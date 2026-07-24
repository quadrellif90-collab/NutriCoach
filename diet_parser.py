"""NutriCoach — Parser dieta da PDF (stile "Filippo estate.pdf").

Estrae la struttura: Giorno -> Pasto -> lista alimenti (nome, grammi) con
eventuali ALTERNATIVE (righe che iniziano con "o "). I pasti possono essere
invertiti/modificati a piacimento (il PDF lo dice esplicitamente), quindi il
parser mantiene l'ordine ma NON impone vincoli.

Formato tipico (verificato su Filippo estate.pdf / Alice Lamanna.pdf):
  Lunedì
  Colazione Salata
  Quantità
  Avocado           30 g
  Pane comune       50 g
  o Pane di segale  62 g      <-- alternativa
  Uova di gallina  100 g
  ...
  Pranzo
  Quantità
  Riso Basmati      80 g
  o Riso brillato   84 g
  ...

Il parser gestisce anche PDF senza tabelle (testo flow) e salva la struttura
in un dict serializzabile. Per PDF scansionati (0 testo) si usa
`parse_diet_text` dopo aver incollato il testo OCR esterno.
"""

import re
import fitz  # PyMuPDF

DAYS = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
# Pasti riconosciuti (case-insensitive, substring)
MEAL_KEYWORDS = ["colazione", "pranzo", "cena", "spuntino", "merenda", "breakfast", "lunch", "dinner", "snack"]


def _is_day(line: str):
    low = line.strip().lower()
    for d in DAYS:
        if low == d or low.startswith(d):
            return d.capitalize()
    return None


def _is_meal_header(line: str):
    low = line.strip().lower()
    for kw in MEAL_KEYWORDS:
        if kw in low:
            return line.strip().title()
    return None


def _parse_qty(token: str):
    """Estrae grammi da un token tipo '30 g', '30g', '1.5 kg'."""
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(g|gr|grammi|kg|ml|cc)?", token.lower())
    if not m:
        return None
    val = float(m.group(1).replace(",", "."))
    unit = (m.group(2) or "g").lower()
    if unit in ("kg",):
        val *= 1000
    elif unit in ("ml", "cc"):
        val = val  # trattiamo come g approssimativi (liquidi densità ~1)
    return round(val, 1)


def parse_diet_text(text: str) -> dict:
    """Parse del testo estratto (o incollato) in struttura dieta.

    STRUTTURA ALTERNATIVE: nel PDF dieta, ogni alimento che NON inizia con
    "o " è una scelta BASE; le righe successive che iniziano con "o " sono
    ALTERNATIVE MUTUAMENTE ESCLUSIVE dello stesso gruppo (es. "Pane comune
    50g" + "o Pane di segale 62g" => scegli UNO). Il parser raggruppa quindi
    in `groups`: ogni gruppo ha `options` (la base + le altre). I conteggi
    usano UNA sola opzione per gruppo (default la base, o la selezione).
    """
    lines = [l.rstrip() for l in text.splitlines()]
    diet = {"title": "", "client": "", "date": "", "days": []}
    current_day_ref = None
    current_meal_ref = None

    def new_day(name):
        d = {"day": name, "meals": []}
        diet["days"].append(d)
        return d

    def new_meal(name):
        m = {"meal": name, "groups": []}
        current_day_ref["meals"].append(m)
        return m

    def add_option(food, grams, is_alt):
        """Aggiunge un'opzione al gruppo corrente del pasto."""
        if not current_meal_ref["groups"]:
            current_meal_ref["groups"].append({"options": []})
        grp = current_meal_ref["groups"][-1]
        opt = {"food": food.strip(), "grams": grams}
        if not is_alt:
            opt["default"] = True
            # una nuova base chiude il gruppo precedente e ne apre uno nuovo
            if grp["options"]:
                current_meal_ref["groups"].append({"options": []})
                grp = current_meal_ref["groups"][-1]
        grp["options"].append(opt)

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        dm = re.match(r"(\d{1,2}[/\\-]\d{1,2}[/\\-]\d{2,4})", line)
        if dm:
            if not diet["date"]:
                diet["date"] = dm.group(1)
            continue
        if re.match(r"pagina\s+\d+", line.lower()):
            continue
        day = _is_day(line)
        if day:
            current_day_ref = new_day(day)
            current_meal_ref = None
            continue
        meal = _is_meal_header(line)
        if meal and current_day_ref is not None:
            current_meal_ref = new_meal(meal)
            continue
        if line.lower().startswith("quant") or line.lower() in ("qtà", "qta"):
            continue
        if current_meal_ref is not None:
            is_alt = False
            content = line
            if content.lower().startswith("o "):
                is_alt = True
                content = content[2:].strip()
            qty = _parse_qty(content)
            name = content
            if qty is not None:
                name = re.sub(r"\s*\d+(?:[.,]\d+)?\s*(g|gr|grammi|kg|ml|cc)?\s*$", "", content, flags=re.I).strip()
            # riga SOLO quantità -> accoda all'ultima opzione del gruppo corrente
            if qty is not None and not name:
                if current_meal_ref["groups"] and current_meal_ref["groups"][-1]["options"]:
                    current_meal_ref["groups"][-1]["options"][-1]["grams"] = qty
                continue
            if name:
                add_option(name, qty, is_alt)
                continue
        if not diet["title"] and len(line) > 3 and not line.lower().startswith(("ho inserito", "frutta", "verdure", "ricorda")):
            if current_day_ref is None and current_meal_ref is None and len(diet["days"]) == 0:
                diet["title"] = line

    diet["days"] = [d for d in diet["days"] if d["meals"]]
    for d in diet["days"]:
        d["meals"] = [m for m in d["meals"] if m["groups"]]
    return diet


def parse_diet_pdf(path: str) -> dict:
    """Estrae testo dal PDF e parse. Se 0 testo -> ritorna flagged scanned."""
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    if not text.strip():
        return {"scanned": True, "text": "", "diet": None}
    diet = parse_diet_text(text)
    diet["scanned"] = False
    return {"scanned": False, "text": text, "diet": diet}


if __name__ == "__main__":
    import json, sys
    p = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Siviglino\Desktop\Filippo estate.pdf"
    res = parse_diet_pdf(p)
    if res["scanned"]:
        print("PDF SCANSIONATO (0 testo) — serve OCR incolla-testo")
    else:
        d = res["diet"]
        print(f"Titolo: {d.get('title')} | Data: {d.get('date')} | Giorni: {len(d['days'])}")
        for day in d["days"][:2]:
            print(f"  {day['day']}:")
            for meal in day["meals"]:
                items = ", ".join(f"{i['food']} {i['grams']}g{' (alt)' if i['alt'] else ''}" for i in meal["items"][:4])
                print(f"    {meal['meal']}: {items}")
