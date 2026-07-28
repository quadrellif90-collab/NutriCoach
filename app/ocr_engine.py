"""
Motore OCR integrato per NutriCoach v2.
Usa Windows.Media.Ocr (built-in Windows 10/11) come primario,
Tesseract come fallback per sistemi senza winsdk.

Windows OCR restituisce coordinate XY di ogni parola → permette
estrazione intelligente da tabelle (es. AKERN BODYGRAM dove i
valori del paziente sono nella colonna a x≈1410, i riferimenti a x≥2150).
"""

import os, re, logging, io
from typing import Optional
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

# ── data model ──────────────────────────────────────────────
@dataclass
class OcrWord:
    text: str
    x: float
    y: float
    w: float
    h: float

@dataclass
class OcrResult:
    lines: list  # [(y_center, [OcrWord, ...])]
    raw_text: str
    source: str = "windows_ocr"  # o "tesseract"

# ── Windows OCR engine ──────────────────────────────────────
_HAVE_WINSDK = False
try:
    import asyncio
    from winsdk.windows.media.ocr import OcrEngine
    from winsdk.windows.graphics.imaging import (BitmapDecoder, BitmapPixelFormat,
                                                  BitmapAlphaMode)
    from winsdk.windows.storage import StorageFile
    from winsdk.windows.globalization import Language
    _HAVE_WINSDK = True
except ImportError:
    pass

async def _run_windows_ocr(image_path: str) -> OcrResult:
    """Esegue OCR via Windows.Media.Ocr su una singola immagine."""
    from winsdk.windows.media.ocr import OcrEngine
    from winsdk.windows.graphics.imaging import (BitmapDecoder, BitmapPixelFormat,
                                                  BitmapAlphaMode)
    from winsdk.windows.storage import StorageFile
    from winsdk.windows.globalization import Language

    # Prova italiano, fallback sistema
    ocr = OcrEngine.try_create_from_language(Language("it-IT"))
    if ocr is None:
        ocr = OcrEngine.try_create_from_user_profile_languages()

    file = await StorageFile.get_file_from_path_async(image_path)
    stream = await file.open_read_async()
    decoder = await BitmapDecoder.create_async(stream)
    sb = await decoder.get_software_bitmap_async(BitmapPixelFormat.BGRA8,
                                                  BitmapAlphaMode.PREMULTIPLIED)

    result = await ocr.recognize_async(sb)

    # Costruisce strutture dati
    all_lines = []
    words_list = []
    for line in result.lines:
        line_words = []
        for word in line.words:
            wr = word.bounding_rect
            ow = OcrWord(text=word.text, x=wr.x, y=wr.y, w=wr.width, h=wr.height)
            line_words.append(ow)
            words_list.append(ow)
        if line_words:
            y_center = sum(w.y for w in line_words) / len(line_words)
            all_lines.append((y_center, line_words))

    all_lines.sort(key=lambda t: t[0])  # ordina per Y
    raw_text = result.text
    return OcrResult(lines=all_lines, raw_text=raw_text, source="windows_ocr")

def _run_windows_ocr_sync(image_path: str) -> OcrResult:
    """Wrapper sincrono per Windows OCR."""
    return asyncio.run(_run_windows_ocr(image_path))

# ── Tesseract fallback ──────────────────────────────────────
_HAVE_TESSERACT = False
try:
    import pytesseract
    _HAVE_TESSERACT = True
except ImportError:
    try:
        from app import ocr_pdf as tess_fallback
        _HAVE_TESSERACT = True
    except ImportError:
        pass

def _run_tesseract_ocr(image_path: str) -> OcrResult:
    """OCR via Tesseract (fallback senza coordinate)."""
    try:
        import pytesseract
        text = pytesseract.image_to_string(image_path, lang="ita+eng")
    except Exception:
        text = ""
    # Tesseract non dà coordinate → lines simulate
    lines = [(i*50, [OcrWord(text=ln.strip(), x=0, y=i*50, w=0, h=0)])
             for i, ln in enumerate(text.split("\n")) if ln.strip()]
    return OcrResult(lines=lines, raw_text=text, source="tesseract")

# ── PDF rendering ───────────────────────────────────────────
def _render_pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> list:
    """Converte PDF in PNG temporanei e restituisce i path."""
    import fitz
    import tempfile

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    paths = []
    tmpdir = tempfile.mkdtemp(prefix="nc_ocr_")
    for i in range(doc.page_count):
        page = doc[i]
        pix = page.get_pixmap(dpi=dpi)
        out = os.path.join(tmpdir, f"page_{i+1}.png")
        pix.save(out)
        paths.append(out)
    return paths

def _merge_close_lines(lines: list, y_threshold: float = 50) -> list:
    """
    Fonde linee con Y molto vicina (stessa riga di tabella).
    Windows OCR splitta i valori della tabella su linee separate
    a causa dei grandi gap orizzontali (label a x=68, valore a x=1410).
    """
    if not lines:
        return []
    sorted_lines = sorted(lines, key=lambda t: t[0])
    merged = []
    cur_y = sorted_lines[0][0]
    cur_words = list(sorted_lines[0][1])

    for y, words in sorted_lines[1:]:
        if abs(y - cur_y) <= y_threshold:
            # Stessa riga di tabella
            cur_words.extend(words)
            # Aggiorna Y media
            cur_y = (cur_y + y) / 2
        else:
            merged.append((cur_y, sorted(cur_words, key=lambda w: w.x)))
            cur_y = y
            cur_words = list(words)
    if cur_words:
        merged.append((cur_y, sorted(cur_words, key=lambda w: w.x)))
    return merged
# Colonne della tabella AKERN BODYGRAM (valori misurati dal Windows OCR)
# La colonna VALORE del paziente è a x ≈ 1400-1500 (a 200 DPI)
# La colonna INDICE (kg/m) è a x ≈ 1780-1850
# Le colonne RIFERIMENTO partono da x ≈ 2150
_VALUE_COL_X_MIN = 1250
_VALUE_COL_X_MAX = 1650

# Etichette BIA riconosciute (lowercase, senza primo carattere perché Windows
# OCR spesso perde la prima lettera nelle celle di tabella)
_LABEL_MAP = {
    "ngolo di fase (pha)": "phase_angle",
    "angolo di fase (pha)": "phase_angle",
    "cqua totale (tbw)": "tbw_l",
    "acqua totale (tbw)": "tbw_l",
    "cqua extra cellulare (ecw)": "ecw_l",
    "acqua extra cellulare (ecw)": "ecw_l",
    "cqua intra cellulare (icw)": "icw_l",
    "acqua intra cellulare (icw)": "icw_l",
    "massa cellulare (bcm)": "bcm_kg",
    "massa magra (ffm)": "fat_free_mass_kg",
    "massa muscolo-scheletrica (smm)": "smm_kg",
    "massa muscolare appendicolare (asmm)": "asmm_kg",
    "massa grassa (fm)": "fat_mass_kg",
}

# Etichette nel testo libero (fuori tabella)
_FREE_LABELS = {
    "peso:": "weight_kg",
    "altezza:": "height_cm",
    "bmi:": "bmi",
    "idratazione tissutale": "hydration_pct",
    "indice nutrizionale": "chi_value",
}

def _extract_table_value(text: str) -> dict:
    """
    Estrae i valori BIA dal testo Windows OCR.
    La tabella AKERN ha i valori in sequenza sotto "Risultati":
      "Risultati 7.4 0 17.7 L 25.3 L 29.3 kg 56.8 kg 32.2 kg 24.5 kg 14.6 kg"
    Ogni valore corrisponde a una riga della tabella in ordine.
    """
    found = {}

    # Trova la riga "Risultati" con i valori in sequenza
    m = re.search(r'Risultati\s+(.+)', text, re.IGNORECASE)
    if not m:
        return found

    values_str = m.group(1).strip()

    # Estrarre numeri validi (con unità opzionale) dalla sequenza
    # Pattern: numero + (unità opzionale) ripetuto
    # Es: "7.4 0 17.7 L 25.3 L 29.3 kg 56.8 kg 32.2 kg 24.5 kg 14.6 kg"
    # Estrarre valori: 7.4, -skip 0-, 17.7, 25.3, 29.3, 56.8, 32.2, 24.5, 14.6
    
    # Estrai tutti i numeri dalla stringa
    all_nums = re.findall(r'(\d+(?:[.,]\d+)?)\s*(°|L|l|kg|%|0)?', values_str)
    
    if not all_nums:
        return found

    # Filtra: salta "0" solitari (è il delta sign dopo PhA)
    cleaned = []
    for num, unit in all_nums:
        val = float(num.replace(",", "."))
        if val == 0:
            continue  # salta il delta sign "0" dopo 7.4
        # Salva il tipo di unità per aiutare l'assegnazione
        u = unit.strip() if unit else ""
        cleaned.append((val, u))

    # Ordine della tabella AKERN (saltando TBW che manca dalla riga Risultati)
    # La tabella Windows OCR non ha TBW nella riga valori
    table_order = [
        ("phase_angle", None),       # 7.4°
        ("ecw_l", ["L", "l"]),       # 17.7 L
        ("icw_l", ["L", "l"]),       # 25.3 L
        ("bcm_kg", ["kg"]),          # 29.3 kg
        ("fat_free_mass_kg", ["kg"]),# 56.8 kg
        ("smm_kg", ["kg"]),          # 32.2 kg
        ("asmm_kg", ["kg"]),         # 24.5 kg
        ("fat_mass_kg", ["kg"]),     # 14.6 kg
    ]

    for (field_name, expected_units), (val, unit) in zip(table_order, cleaned):
        if expected_units and unit not in expected_units:
            # Se l'unità non corrisponde, skip (parsing fallito)
            continue
        found[field_name] = val

    return found

def _extract_free_text(text: str) -> dict:
    """Estrae valori dal testo libero (fuori tabella)."""
    found = {}
    low = text.lower()

    for label, field in _FREE_LABELS.items():
        m = re.search(re.escape(label) + r"\s*[:\s]*\s*(\d+(?:[.,]\d+)?)", low)
        if m:
            try:
                val = float(m.group(1).replace(",", "."))
                found[field] = val
            except ValueError:
                pass

    # Idratazione speciale (valore su riga separata)
    if "idratazione" in low:
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*%\s*\(tbw/ffm\)", low)
        if m:
            try:
                found["hydration_pct"] = float(m.group(1).replace(",", "."))
            except ValueError:
                pass

    return found

def _cleanup_tmpdir(paths: list):
    """Elimina la directory temporanea che contiene i file PNG."""
    import shutil
    if paths:
        d = os.path.dirname(paths[0])
        if d and os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)

# ── API pubblica ────────────────────────────────────────────
def ocr_pdf(pdf_bytes: bytes) -> OcrResult:
    """
    Esegue OCR su un PDF usando Windows OCR (primario) o Tesseract (fallback).
    Restituisce un OcrResult con linee, parole e coordinate XY.
    """
    paths = _render_pdf_to_images(pdf_bytes, dpi=200)

    if _HAVE_WINSDK:
        log.info("OCR engine: Windows.Media.Ocr (it-IT)")
        result = OcrResult(lines=[], raw_text="", source="windows_ocr")
        for p in paths:
            try:
                page_result = _run_windows_ocr_sync(p)
                result.lines.extend(page_result.lines)
                result.raw_text += page_result.raw_text + "\n"
            except Exception as e:
                log.warning("Windows OCR page failed: %s", e)
        # Cleanup
        _cleanup_tmpdir(paths)
        return result

    # Fallback Tesseract
    log.info("OCR engine: Tesseract fallback")
    if _HAVE_TESSERACT:
        try:
            from app.ocr_pdf import ocr_pdf_text
            text = ocr_pdf_text(pdf_bytes)
        except Exception as e:
            log.warning("Tesseract fallback failed: %s", e)
            text = ""
    else:
        text = ""

    for p in paths:
        try:
            os.unlink(p)
        except OSError:
            pass

    lines = [(i*50, [OcrWord(text=ln.strip(), x=0, y=i*50, w=0, h=0)])
             for i, ln in enumerate(text.split("\n")) if ln.strip()]
    return OcrResult(lines=lines, raw_text=text, source="tesseract")


def parse_bia_ocr(ocr_result: OcrResult) -> dict:
    """Analizza un OcrResult e restituisce i campi BIA estratti."""
    found = {}

    # Estrai valori dalla tabella (Risultati... sequenza ordinata)
    found.update(_extract_table_value(ocr_result.raw_text))

    # Estrai valori dal testo libero
    found.update(_extract_free_text(ocr_result.raw_text))

    # Deriva BF% se non presente
    if "fat_mass_kg" in found and "weight_kg" in found:
        if "fat_mass_pct" not in found:
            found["fat_mass_pct"] = round(found["fat_mass_kg"] / found["weight_kg"] * 100, 1)

    # Deriva TBW da ECW+ICW (Windows OCR spesso perde TBW nella tabella)
    if "tbw_l" not in found and "ecw_l" in found and "icw_l" in found:
        found["tbw_l"] = round(found["ecw_l"] + found["icw_l"], 1)

    # Mappa per compatibilità con DB
    compat = {"fat_mass_kg": "bf_kg", "fat_free_mass_kg": "ffm_kg",
              "fat_mass_pct": "bf_pct"}
    for src, dst in compat.items():
        if src in found and dst not in found:
            found[dst] = found[src]

    return found


def parse_bia_pdf(pdf_bytes: bytes) -> dict:
    """
    Entry point principale: carica PDF, esegue OCR, estrae campi BIA.
    Restituisce dict con campi BIA (stessa interfaccia di bia_parser_v2.parse_bia_text).
    """
    try:
        ocr_result = ocr_pdf(pdf_bytes)
        found = parse_bia_ocr(ocr_result)
        return found
    except Exception as e:
        log.error("OCR engine error: %s", e)
        return {}