"""NutriCoach — Parser BIA / misure antropometriche da PDF.

Supporta:
- PDF testuale: estrazione regex dei campi noti (peso, altezza, BMI, FM, FFM,
  TBW, ECW, ICW, BCM, SMM, ASMM, PhA, idratazione, ecc.)
- PDF scansionato: render delle pagine in immagini base64 + (opzionale) testo
  OCR incollato dall'utente, che viene ri-passato al parser testuale.

I campi riconosciuti sono flessibili (accetta varianti italiane/inglesi).
"""

import re
import base64
import fitz  # PyMuPDF

# Mappa label normalizzata -> campo
FIELD_PATTERNS = {
    "peso": ["peso", "weight", "body weight", "wt"],
    "altezza": ["altezza", "height", "statura", "ht"],
    "bmi": ["bmi", "imc"],
    "fm": ["massa grassa", "fat mass", "fm ", "f.m."],
    "ffm": ["massa magra", "fat free", "ffm", "f.f.m."],
    "tbw": ["acqua totale", "total body water", "tbw"],
    "ecw": ["acqua extra", "extracellular", "ecw"],
    "icw": ["acqua intra", "intracellular", "icw"],
    "bcm": ["massa cellulare", "body cell", "bcm"],
    "smm": ["massa muscolo", "skeletal muscle", "smm", "mms"],
    "asmm": ["massa muscolare appendicolare", "appendicular", "asmm"],
    "pha": ["angolo di fase", "phase angle", "pha", "ph a"],
    "hydration": ["idratazione", "hydration", "hd"],
    "protein": ["massa proteica", "protein", "proteina"],
    "mineral": ["massa minerale", "mineral"],
    "fmi": ["indice di massa grassa", "fat mass index", "fmi"],
    "ffmi": ["indice di massa magra", "fat free mass index", "ffmi"],
    "bmr": ["metabolismo basale", "basal metabolic", "bmr"],
}

# unità numeriche: cattura numero (anche decimale, virgola o punto)
_NUM = r"(-?\d+(?:[.,]\d+)?)"


def _norm(s: str) -> str:
    import unicodedata
    s = s.lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    # unifica virgola decimale -> punto PRIMA di rimuovere la punteggiatura,
    # altrimenti i decimali (75.2 / 18,3) verrebbero persi
    s = s.replace(",", ".")
    s = re.sub(r"[^a-z0-9 .]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _match_field(label: str):
    n = _norm(label)
    for field, patterns in FIELD_PATTERNS.items():
        for p in patterns:
            if p in n:
                return field
    return None


def _parse_number(token: str):
    m = re.search(_NUM, token.replace(",", "."))
    return float(m.group(1)) if m else None


def parse_bia_text(text: str) -> dict:
    """Estrae i campi BIA da testo (PDF testuale o OCR incollato).

    Robusto a:
    - una o piu righe, anche tutto su un'unica riga (PDF a 2 colonne, copia
      di un blob);
    - valori tra parentesi: "Peso (kg) (75.2)";
    - unita attaccate al numero: "75.2kg";
    - varianti italiane/inglesi delle label.
    """
    out = {"fields": {}, "raw_lines": 0}
    # normalizza: minuscolo, accentati->ascii, virgola decimale->punto
    norm = _norm(text)
    out["raw_lines"] = len([l for l in text.splitlines() if l.strip()])

    # per ogni campo, prova tutte le pattern e prendi il primo numero valido
    for field, patterns in FIELD_PATTERNS.items():
        if field in out["fields"]:
            continue
        for p in patterns:
            # confine di parola; le pattern con spazi interni restano intere
            pat = r"(?<![a-z])" + re.escape(p.strip()) + r"(?![a-z])"
            for m in re.finditer(pat, norm):
                # cerca il numero nei prossimi ~30 char, anche tra parentesi;
                # il numero NON deve essere preceduto da una lettera (es. "m2",
                # "kg", "°" sono parti d'unita', non valori)
                after = norm[m.end(): m.end() + 30]
                nm = re.search(r"\(?\s*(?<![a-z0-9.])(\d+(?:\.\d+)?)", after)
                if nm:
                    val = float(nm.group(1))
                    out["fields"][field] = val
                    break
            if field in out["fields"]:
                break
    return out


def parse_bia_pdf(path: str) -> dict:
    """Estrae BIA da PDF. Se testuale -> parse diretto. Se scansionato ->
    tenta OCR (se Tesseract installato); altrimenti ritorna le immagini per
    OCR/copia manuale esterna."""
    doc = fitz.open(path)
    text = ""
    pages_b64 = []
    for page in doc:
        t = page.get_text()
        if t.strip():
            text += t + "\n"
        # render immagine (per scan o comunque utile come anteprima)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6))
        pages_b64.append(base64.b64encode(pix.tobytes("png")).decode("ascii"))
    doc.close()
    if text.strip():
        parsed = parse_bia_text(text)
        parsed["scanned"] = False
        return parsed
    # PDF scansionato: tenta OCR
    try:
        import ocr
        res = ocr.ocr_pdf(path)
        if res["text"].strip():
            parsed = parse_bia_text(res["text"])
            parsed["scanned"] = False
            parsed["ocr"] = True
            return parsed
        return {"scanned": True, "pages": res.get("pages", pages_b64),
                "fields": {}, "raw_lines": 0, "ocr_available": ocr.tesseract_available()}
    except Exception:
        return {"scanned": True, "pages": pages_b64, "fields": {}, "raw_lines": 0}


def parse_bia_pasted(pasted_text: str) -> dict:
    """Parse di testo OCR incollato (da PDF scansionato)."""
    parsed = parse_bia_text(pasted_text)
    parsed["scanned"] = True
    parsed["from_paste"] = True
    return parsed


if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Siviglino\Desktop\Report utente - F.Q. - 18-06-2026.pdf"
    res = parse_bia_pdf(p)
    print("Scanned:", res.get("scanned"))
    if res.get("scanned"):
        print("Pagine immagine:", len(res.get("pages", [])))
    else:
        print("Campi:", res.get("fields"))
