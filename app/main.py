"""
NutriCoach v2 — App principale FastAPI (modulare, Dietowin-style).
"""
import os, sys, json, asyncio, re, html as htmlmod, datetime as dt, hashlib
import asyncio
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import app.database as db
from app import energy_calc
import clinical_nutrition, meal_planner, bia_parser, diet_presets, anthropometry, ocr, bia_analysis

app = FastAPI(title="NutriCoach v2 — Dietowin", version="2.20.15")

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

# Global exception handler — converts unhandled errors to clean JSON responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"ok": False, "error": exc.detail})
    return JSONResponse(
        status_code=400,
        content={"ok": False, "error": "Richiesta non valida", "detail": str(exc)[:200]}
    )

# Servi file statici (CSS)
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

UPLOAD_DIR = os.path.join(db.DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _today():
    return dt.date.today().isoformat()

def _timestamp():
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")

# ─── UI ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    return open(os.path.join(os.path.dirname(__file__), "templates", "index.html"), encoding="utf-8").read()

# ─── ANAMNESI CLINICA (condizioni + raccomandazioni) ──────────────────────

@app.get("/api/clinical-conditions")
def api_clinical_conditions():
    return {"conditions": clinical_nutrition.get_all_conditions()}

@app.post("/api/patients/{pid}/anamnesis")
async def api_save_anamnesis(pid: int, request: Request):
    b = await request.json()
    conditions = b.get("conditions", [])
    notes = b.get("notes", "")
    data = {"clinical_conditions": conditions, "anamnesis_notes": notes}
    db.update_patient(pid, pathologies=json.dumps(data))
    p = db.get_patient(pid)
    recs = clinical_nutrition.generate_anamnesis_report(conditions, {"name": (p or {}).get("name","")})
    return {"ok": True, "recommendations": recs}

@app.get("/api/patients/{pid}/anamnesis")
def api_get_anamnesis(pid: int):
    p = db.get_patient(pid)
    raw = (p or {}).get("pathologies", "{}")
    try:
        data = json.loads(raw) if isinstance(raw, str) else {}
    except Exception:
        data = {}
    conditions = data.get("clinical_conditions", []) if isinstance(data, dict) else []
    notes = data.get("anamnesis_notes", "") if isinstance(data, dict) else ""
    p_info = {"name": (p or {}).get("name","")}
    recs = clinical_nutrition.generate_anamnesis_report(conditions, p_info) if conditions else []
    return {"conditions": conditions, "notes": notes, "recommendations": recs}

# ─── PRESET DIETA ──────────────────────────────────────────────────────────

@app.get("/api/diet-presets")
def api_presets():
    return {"presets": diet_presets.preset_list()}

@app.post("/api/diet-presets/targets")
async def api_preset_targets(request: Request):
    b = await request.json()
    return diet_presets.preset_targets(b.get("key","personalizzato"), float(b.get("kcal",2000) or 2000), b.get("weight_kg"))


@app.post("/api/presets/check-compatibility")
async def api_check_preset_compatibility(request: Request):
    """Verifica se un preset è incompatibile con le condizioni cliniche del paziente."""
    b = await request.json()
    conditions = b.get("conditions", [])
    preset_key = b.get("preset", "")
    result = clinical_nutrition.check_preset_compatibility(conditions, preset_key)
    return result


# ─── PIANO ALIMENTARE ─────────────────────────────────────────────────────

@app.post("/api/patients/{pid}/plan/generate")
async def api_generate_plan(pid: int, request: Request):
    b = await request.json()
    targets = b.get("targets", {}) or {}
    options = b.get("options", {}) or {}
    preset = b.get("preset") or options.get("preset")
    client = db.get_patient(pid) or {}
    parsed = clinical_nutrition.parse_pathologies(client.get("pathologies"))
    conditions = list(parsed["conditions"])
    req_conds = options.get("conditions") or []
    if isinstance(req_conds, list):
        for c in req_conds:
            if c and c not in conditions:
                conditions.append(c)
    allergies = client.get("allergies", "")
    if parsed["allergies"]:
        allergies = (allergies + "," + ",".join(parsed["allergies"])).strip(",")
    if preset and preset not in ("personalizzato", "none", ""):
        kcal = float(targets.get("kcal", 2000))
        w = client.get("weight_kg")
        w = float(w) if w else None
        pt = diet_presets.preset_targets(preset, kcal, w)
        targets = {"kcal": int(kcal), "protein_pct": pt["p_pct"], "carb_pct": pt["c_pct"], "fat_pct": pt["f_pct"]}
        options["preset"] = preset
    excl = meal_planner.excluded_foods(conditions, allergies)
    excl.update(options.get("exclude_foods") or [])
    options["exclude_foods"] = sorted(excl)
    # Converti days da int a lista di nomi giorni se necessario
    all_days = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
    raw_days = options.get("days", 7)
    if isinstance(raw_days, int):
        options["days"] = all_days[:raw_days]
    elif not isinstance(raw_days, list):
        options["days"] = all_days
    plan = meal_planner.generate_plan(targets, options)
    plan["clinical"] = {"conditions": conditions, "excluded_foods": sorted(excl), "preset": preset,
                        "recommendations": clinical_nutrition.get_dietary_recommendations(conditions) if conditions else []}
    title = f"Piano {client.get('name','')} {_today()}"
    if preset:
        title += f" [{diet_presets.PRESETS.get(preset,{}).get('label', preset)}]"
    if conditions:
        title += f" [{','.join(conditions)}]"
    kcal = targets.get("kcal", 0)
    p = targets.get("protein_pct", 0)
    c = targets.get("carb_pct", 0)
    f = targets.get("fat_pct", 0)
    did = db.add_diet_plan(pid, title, preset or "", conditions, int(kcal), int(p), int(c), int(f), plan)
    plan["diet_id"] = did
    return plan


# ─── SMART IMPORT ───────────────────────────────────────────────────

def _parse_import_text(text: str, _depth: int = 0) -> dict:
    """Rileva il tipo di contenuto incollato e restituisce {type, data, confidence}.
    Tipi supportati: 'bia', 'anthropometry', 'diet_plan', 'foods', 'json', 'unknown'.
    """
    text = text.strip()
    if not text:
        return {"type": "unknown", "data": {}, "confidence": 0.0}

    # 1. Prova JSON
    try:
        j = json.loads(text)
        if isinstance(j, dict):
            # Heuristica per tipo
            keys = set(j.keys())
            if any(k in keys for k in ("weight_kg", "bf_pct", "tbw_l", "ecw_l", "icw_l", "pha", "bf_kg", "mm_kg", "smm_kg", "bcm_kg")):
                return {"type": "bia", "data": j, "confidence": 0.9}
            if any(k in keys for k in ("skinfold_tricipite", "skinfold_bicipite", "skinfold_sottoscapolare", "skinfold_sovrailiaca", "waist_cm", "hip_cm")):
                return {"type": "anthropometry", "data": j, "confidence": 0.9}
            if any(k in keys for k in ("targets", "options", "preset", "meals_per_day")):
                return {"type": "diet_plan", "data": j, "confidence": 0.8}
            if any(k in keys for k in ("foods", "items", "catalog")) and isinstance(j.get("foods") or j.get("items"), list):
                return {"type": "foods", "data": j, "confidence": 0.7}
            if "md_results" in keys or "layout_details" in keys:
                # Risposta completa OCR z.ai: lascia passare al branch 2c
                pass
            else:
                return {"type": "json", "data": j, "confidence": 0.5}
        elif isinstance(j, list):
            return {"type": "json", "data": {"items": j}, "confidence": 0.4}
    except Exception:
        pass

    # 2. Markdown / YAML frontmatter
    if text.startswith("---"):
        # YAML frontmatter semplice
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                import yaml
                fm = yaml.safe_load(parts[1])
                if isinstance(fm, dict):
                    return {"type": "json", "data": fm, "confidence": 0.6, "body": parts[2].strip()}
            except Exception:
                pass

    # 2b. HTML / tabelle (formato export z.ai OCR)
    # NB: salta le risposte COMPLETE z.ai (JSON con md_results/layout_details):
    #     contengono "<table" dentro le stringhe ma il feed dell'intero blob
    #     produrrebbe righe spurie e perderebbe il markdown -> va al 2c.
    _zai_resp = "md_results" in text or "layout_details" in text
    if not _zai_resp and ("<table" in text.lower() or "<td" in text.lower() or "<tr" in text.lower()):
        try:
            import io as _io
            from html.parser import HTMLParser as _HP

            class _TabParser(_HP):
                def __init__(self):
                    super().__init__()
                    self.rows = []
                    self.cur = None
                    self.cell = None
                def handle_starttag(self, tag, attrs):
                    if tag == "tr":
                        self.cur = []
                    elif tag in ("td", "th") and self.cur is not None:
                        self.cell = []
                def handle_data(self, data):
                    if self.cell is not None:
                        self.cell.append(data)
                def handle_endtag(self, tag):
                    if tag in ("td", "th") and self.cell is not None:
                        self.cur.append("".join(self.cell).strip())
                        self.cell = None
                    elif tag == "tr" and self.cur is not None:
                        if any(self.cur):
                            self.rows.append(self.cur)
                        self.cur = None

            p = _TabParser()
            p.feed(text)
            if p.rows:
                data = {}
                anthro = {}

                def norm(s):
                    return str(s or "").lower().strip()

                def num(v):
                    if v is None:
                        return None
                    s = norm(v).replace(",", ".")
                    m = re.search(r"(\d+[.,]?\d*)", s)
                    try:
                        return float(m.group(1)) if m else None
                    except Exception:
                        return None

                def _contiene(row0, keys):
                    """Match per sottostringa; chiavi corte (<=2 char) con match esatto
                    ('mm' non deve matchare dentro 'grammi')."""
                    r = norm(row0)
                    for k in keys:
                        if len(k) <= 2:
                            if r == k:
                                return True
                        elif k in r:
                            return True
                    return False

                # Layout verticale: ogni riga "Parametro | Valore"
                # Sinonimi estesi al report BIA italiano (Biavector/Bodygram export z.ai)
                vend = [
                    (("peso", "weight", "massa corporea", "body weight"), "weight_kg"),
                    (("bf",), "bf_mixed"),
                    (("massa grassa", "body fat", "grasso corporeo", "grasso", "masse grasse", "fat mass"), "bf_mixed"),
                    (("mm",), "mm_mixed"),
                    (("massa muscolare scheletrica", "massa muscolo-scheletrica",
                      "massa muscolo scheletrica", "skeletal muscle", "smm"), "smm_kg"),
                    (("massa muscolare appendicolare", "massa muscolare appendicol",
                      "appendicular", "asmm"), "asmm_kg"),
                    (("massa muscolare", "muscle mass"), "mm_mixed"),
                    (("angolo di fase", "phase angle", "pha"), "pha"),
                    (("acqua totale", "total body water", "tbw"), "tbw_l"),
                    (("acqua extra cellulare", "acqua extracellulare", "extracellular water", "extracellulare", "ecw"), "ecw_l"),
                    (("acqua intra cellulare", "acqua intracellulare", "intracellular water", "intracellulare", "icw"), "icw_l"),
                    (("metabolismo basale", "basal metabolism", "basal metabolic", "bmr"), "bmr_kcal"),
                    (("massa magra", "fat free mass", "lean body", "ffm"), "ffm_kg"),
                    (("massa cellulare", "body cell mass", "bcm"), "bcm_kg"),
                ]
                v_anthro = [
                    (("vita", "waist", "circ. vita"), "waist_cm"),
                    (("fianchi", "hip", "circ. fianchi"), "hip_cm"),
                    (("braccio", "arm"), "arm_cm"),
                    (("coscia", "thigh"), "thigh_cm"),
                    (("tricip", "triceps"), "skinfold_tricipite"),
                    (("bicip", "biceps"), "skinfold_bicipite"),
                    (("sottoscap", "subscapular"), "skinfold_sottoscapolare"),
                    (("sovrailiaca", "suprailiac", "sovrailiaca"), "skinfold_sovrailiaca"),
                ]

                def _unita(row1):
                    """Ritorna 'kg', 'pct', o None in base al testo del valore."""
                    r = norm(row1)
                    if "%" in r or "\u00b0" in r:
                        return "pct"
                    if "kg" in r:
                        return "kg"
                    return None

                def _salva(target, value):
                    if value is not None:
                        data[target] = value

                for keys, target in vend:
                    for row in p.rows:
                        if len(row) >= 2 and _contiene(row[0], keys):
                            v = num(row[1])
                            if target == "bf_mixed":
                                u = _unita(row[1])
                                _salva("bf_pct" if u == "pct" else "bf_kg" if u == "kg" else "bf_pct", v)
                            elif target == "mm_mixed":
                                # Escludi righe SMM/ASMM (Massa Muscolare Appendicolare/Scheletrica)
                                _r0 = norm(row[0])
                                if any(x in _r0 for x in ("appendicol", "scheletric", "smm", "asmm", "skeletal")):
                                    continue
                                u = _unita(row[1])
                                _salva("mm_pct" if u == "pct" else "mm_kg" if u == "kg" else "mm_pct", v)
                            else:
                                _salva(target, v)
                            break
                for keys, target in v_anthro:
                    for row in p.rows:
                        if len(row) >= 2 and _contiene(row[0], keys):
                            anthro[target] = num(row[1])
                            break

                # BIA valida solo se c'è almeno un campo specifico (non solo peso+altezza)
                bia_specific = {"bf_pct", "bf_kg", "mm_pct", "mm_kg", "pha", "tbw_l",
                                "ecw_l", "icw_l", "bmr_kcal", "ffm_kg", "smm_kg", "asmm_kg", "bcm_kg"}
                if len(data) >= 2 and (set(data) & bia_specific):
                    # Il testo fuori tabella (peso, altezza, BMI, data esame) non e'
                    # nelle righe HTML: unisci il parsing testuale (branch 3) per
                    # raccogliere TUTTI i campi (markdown + tabella).
                    try:
                        import html as _html_mod
                        _plain = re.sub(r"<[^>]+>", " ", text)
                        _plain = re.sub(r"@url:`[^`]*`", " ", _plain)
                        _plain = _html_mod.unescape(_plain)
                        _rows_txt = "\n".join(f"{r[0]}: {r[1]}" for r in p.rows if len(r) >= 2)
                        sub = _parse_import_text(_plain + "\n" + _rows_txt, _depth + 1)
                        if sub["type"] == "bia" and len(sub.get("data", {})) >= len(data):
                            return sub
                    except Exception:
                        pass
                    return {"type": "bia", "data": data, "confidence": 0.88}
                if len(anthro) >= 2:
                    return {"type": "anthropometry", "data": anthro, "confidence": 0.88}
        except Exception:
            pass

    # 2c. Risposta completa OCR z.ai (md_results / layout_details)
    # Formato: dump della risposta API contenente il markdown ("md_results")
    # e gli elementi per pagina ("layout_details" con "content": testo e tabelle HTML).
    # Le tabelle vengono CONVERTITE in righe "chiave: valore" così il parsing
    # testuale successivo raccoglie TUTTI i campi (markdown + tabelle).
    if _depth < 3 and ("md_results" in text or "layout_details" in text or '"content"' in text):
        _zai_md = ""
        _zai_rows = []  # righe di testo chiave: valore
        _zai_txt = []
        try:
            jz = json.loads(text)
            if isinstance(jz, dict) and ("md_results" in jz or "layout_details" in jz):
                _md = jz.get("md_results")
                if isinstance(_md, str):
                    _zai_md = _md
                _ld = jz.get("layout_details")
                if isinstance(_ld, list):
                    for page in _ld:
                        if not isinstance(page, list):
                            continue
                        for elem in page:
                            if not isinstance(elem, dict) or not isinstance(elem.get("content"), str):
                                continue
                            c = elem["content"]
                            if "<table" in c.lower() or "<td" in c.lower() or "<tr" in c.lower():
                                _zai_rows.append(c)
                            else:
                                _zai_txt.append(c)
                _jz_ok = True
            else:
                _jz_ok = False
        except Exception:
            _jz_ok = False

        if not _jz_ok:
            # Non-JSON: separa markdown/table da text in base al contenuto
            for m in re.finditer(r'"(?:md_results|content)"\s*:\s*"((?:[^"\\]|\\.)*)"', text):
                raw = m.group(1)
                try:
                    c = json.loads('"' + raw + '"')
                except Exception:
                    c = raw
                if "<table" in c.lower() or "<td" in c.lower() or "<tr" in c.lower():
                    _zai_rows.append(c)
                else:
                    _zai_txt.append(c)

        # Converte le tabelle HTML in righe "Parametro: Valore"
        if _zai_rows:
            try:
                import io as _io2
                from html.parser import HTMLParser as _HP2

                class _TabParser2(_HP2):
                    def __init__(self):
                        super().__init__()
                        self.rows = []
                        self.cur = None
                        self.cell = None
                    def handle_starttag(self, tag, attrs):
                        if tag == "tr":
                            self.cur = []
                        elif tag in ("td", "th") and self.cur is not None:
                            self.cell = []
                    def handle_data(self, data):
                        if self.cell is not None:
                            self.cell.append(data)
                    def handle_endtag(self, tag):
                        if tag in ("td", "th") and self.cell is not None:
                            self.cur.append("".join(self.cell).strip())
                            self.cell = None
                        elif tag == "tr" and self.cur is not None:
                            if any(self.cur):
                                self.rows.append(self.cur)
                            self.cur = None

                for html_tab in _zai_rows:
                    tp = _TabParser2()
                    tp.feed(html_tab)
                    for row in tp.rows:
                        if len(row) >= 2 and row[0] and row[0].lower() not in ("parametro", "parameter", "valore", "value", "indicatore", "indicator", ""):
                            _zai_txt.append(f"{row[0]}: {row[1]}")
                        elif len(row) >= 2:
                            _zai_txt.append(f"{row[0]}: {row[1]}")
            except Exception:
                pass

        _zai_testo = "\n".join([_zai_md] + _zai_txt)
        if _zai_testo.strip():
            sub = _parse_import_text(_zai_testo, _depth + 1)
            if sub["type"] != "unknown" and sub.get("confidence", 0) >= 0.5:
                return sub

    # 3. Testo strutturato - pattern comuni BIA
    # Separatore permissivo tra etichetta e valore (attraversa " (FM): " ecc.)
    SEP = r"[\s:=]*(?:\([^)\d]*\)[\s:=]*)?(?:[A-Za-zÀ-ÿ°]+[\s:=]*){0,1}"
    bia_patterns = [
        (r"(?:peso|weight|massa corporea)" + SEP + r"(\d+[.,]?\d*)", "weight_kg"),
        (r"(?:altezza|height|stature)" + SEP + r"(\d+[.,]?\d*)", "height_cm"),
        (r"(?:bmi|indice di massa corporea|body mass index)" + SEP + r"(\d+[.,]?\d*)", "bmi"),
        (r"(?:massa grassa|body fat|grasso corporeo|masse grasse|fat mass)" + SEP + r"(\d+[.,]?\d*)\s*%", "bf_pct"),
        (r"(?:massa grassa|body fat|grasso corporeo|masse grasse|fat mass)" + SEP + r"(\d+[.,]?\d*)\s*kg\b", "bf_kg"),
        (r"\bbf\s*[:%]?\s*(?:%|percento)?\s*[:=]?\s*(\d+[.,]?\d*)", "bf_pct"),
        (r"(?:massa muscolare(?!\s*(?:appendicolare|scheletrica|scheletrico))|muscle mass(?!\s*(?:appendicular|skeletal)))" + SEP + r"(\d+[.,]?\d*)\s*%", "mm_pct"),
        (r"(?:massa muscolare(?!\s*(?:appendicolare|scheletrica|scheletrico))|muscle mass(?!\s*(?:appendicular|skeletal)))" + SEP + r"(\d+[.,]?\d*)\s*kg\b", "mm_kg"),
        (r"\bmm\s*[:%]?\s*(?:%|percento)?\s*[:=]?\s*(\d+[.,]?\d*)", "mm_pct"),
        (r"(?:angolo di fase|phase angle|\bpha\b)" + SEP + r"(\d+[.,]?\d*)", "pha"),
        (r"(?:acqua totale|total body water|\btbw\b)" + SEP + r"(\d+[.,]?\d*)", "tbw_l"),
        (r"(?:acqua extra cellulare|acqua extracellulare|extracellular water|\becw\b)" + SEP + r"(\d+[.,]?\d*)", "ecw_l"),
        (r"(?:acqua intra cellulare|acqua intracellulare|intracellular water|\bicw\b)" + SEP + r"(\d+[.,]?\d*)", "icw_l"),
        (r"(?:metabolismo basale|basal metastasis|basal metabolic rate|\bbmr\b)" + SEP + r"(\d+[.,]?\d*)", "bmr_kcal"),
        (r"(?:massa magra|fat free mass|\bffm\b)" + SEP + r"(\d+[.,]?\d*)", "ffm_kg"),
        (r"(?:massa muscolare appendicolare|appendicular skeletal mass|\basmm\b)" + SEP + r"(\d+[.,]?\d*)", "asmm_kg"),
        (r"(?:massa muscolare scheletrica|massa muscolo-scheletrica|skeletal muscle mass|\bsmm\b)" + SEP + r"(\d+[.,]?\d*)", "smm_kg"),
        (r"(?:massa cellulare|body cell mass|\bbcm\b)" + SEP + r"(\d+[.,]?\d*)", "bcm_kg"),
    ]
    anthro_patterns = [
        (r"(?:vita|waist)[\s:]*(\d+[.,]?\d*)", "waist_cm"),
        (r"(?:fianchi|hip)[\s:]*(\d+[.,]?\d*)", "hip_cm"),
        (r"(?:braccio|arm)[\s:]*(\d+[.,]?\d*)", "arm_cm"),
        (r"(?:coscia|thigh)[\s:]*(\d+[.,]?\d*)", "thigh_cm"),
        (r"(?:tricipite|triceps)[\s:]*(\d+[.,]?\d*)", "skinfold_tricipite"),
        (r"(?:bicipite|biceps)[\s:]*(\d+[.,]?\d*)", "skinfold_bicipite"),
        (r"(?:sottoscapolare|subscapular)[\s:]*(\d+[.,]?\d*)", "skinfold_sottoscapolare"),
        (r"(?:sovrailiaca|suprailiac)[\s:]*(\d+[.,]?\d*)", "skinfold_sovrailiaca"),
    ]

    def extract(patterns, text):
        out = {}
        for pat, key in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    out[key] = float(m.group(1).replace(",", "."))
                except Exception:
                    pass
        return out

    bia_data = extract(bia_patterns, text)
    # Derivazioni: bmi da peso+altezza, bf_pct da bf_kg, tbw da ecw+icw
    if "bmi" not in bia_data and "weight_kg" in bia_data and "height_cm" in bia_data:
        try:
            bia_data["bmi"] = round(bia_data["weight_kg"] / ((bia_data["height_cm"] / 100) ** 2), 1)
        except Exception:
            pass
    if "bf_pct" not in bia_data and "bf_kg" in bia_data and "weight_kg" in bia_data:
        try:
            bia_data["bf_pct"] = round(bia_data["bf_kg"] / bia_data["weight_kg"] * 100, 1)
        except Exception:
            pass
    if "tbw_l" not in bia_data and "ecw_l" in bia_data and "icw_l" in bia_data:
        bia_data["tbw_l"] = round(bia_data["ecw_l"] + bia_data["icw_l"], 1)
    anthro_data = extract(anthro_patterns, text)

    if bia_data and len(bia_data) >= 2:
        return {"type": "bia", "data": bia_data, "confidence": min(0.85, 0.4 + len(bia_data) * 0.08)}
    if anthro_data and len(anthro_data) >= 2:
        return {"type": "anthropometry", "data": anthro_data, "confidence": min(0.85, 0.4 + len(anthro_data) * 0.08)}

        # 3b. Piano alimentare da testo libero (es. export z.ai markdown)
    diet_patterns = [
        (r"(?:kcal|calor(?:ie|iche)|energy)[\s:]*([\d.,]+)", "kcal"),
        (r"(?:proteine?|protein)\s*[:%]?\s*(\d+[.,]?\d*)", "protein"),
        (r"(?:carboidrati|carbs?|carb)\s*[:%]?\s*(\d+[.,]?\d*)", "carbs"),
        (r"(?:grassi?|fat)\s*[:%]?\s*(\d+[.,]?\d*)", "fat"),
        (r"(?:pasti|meals?)\s*[:]?\s*(\d+)", "meals"),
    ]
    diet_data = {}
    for pat, key in diet_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                diet_data[key] = float(m.group(1).replace(",", "."))
            except Exception:
                pass
    if "kcal" in diet_data and ("carbs" in diet_data or "protein" in diet_data or "fat" in diet_data):
        targets = {"kcal": diet_data.get("kcal")}
        for k, t in (("protein", "protein_pct"), ("carbs", "carb_pct"), ("fat", "fat_pct")):
            if k in diet_data:
                targets[t] = diet_data[k]
        fields = {"targets": targets, "options": {"meals": int(diet_data.get("meals", 5)), "days": 7}}
        return {"type": "diet_plan", "data": fields, "confidence": 0.7}

    return {"type": "unknown", "data": {"raw": text}, "confidence": 0.1}


@app.post("/api/patients/{pid}/import")
async def api_smart_import(pid: int, request: Request):
    """Import intelligente: accetta JSON, Markdown, o testo libero.
    Rileva automaticamente il tipo (BIA, Antropometria, Dieta, Alimenti) e restituisce
    l'anteprima mappata per conferma utente.
    """
    b = await request.json()
    text = b.get("text", "")
    if not text or not text.strip():
        raise HTTPException(400, "Testo vuoto")

    parsed = _parse_import_text(text)

    # Se bassa confidenza o unknown, restituisci per review manuale
    if parsed["type"] in ("unknown", "json") and parsed.get("confidence", 0) < 0.6:
        return {
            "ok": True,
            "needs_review": True,
            "detected_type": parsed["type"],
            "confidence": parsed.get("confidence", 0),
            "raw_text": text[:500],
            "suggestion": "Incolla JSON strutturato o testo con etichette esplicite (es. 'Peso: 70', 'BF%: 18')"
        }

    # Mappa campi noti per conferma
    field_labels = {
        "bia": {
            "weight_kg": "Peso (kg)", "height_cm": "Altezza (cm)", "bf_pct": "BF%", "mm_pct": "MM%",
            "pha": "PhA", "tbw_l": "TBW (L)", "ecw_l": "ECW (L)", "icw_l": "ICW (L)",
            "bmr_kcal": "BMR (kcal)", "bf_kg": "BF (kg)", "mm_kg": "MM (kg)",
            "ffm_kg": "FFM (kg)", "smm_kg": "SMM (kg)", "asmm_kg": "ASMM (kg)", "bcm_kg": "BCM (kg)"
        },
        "anthropometry": {
            "weight_kg": "Peso (kg)", "height_cm": "Altezza (cm)", "waist_cm": "Vita (cm)",
            "hip_cm": "Fianchi (cm)", "arm_cm": "Braccio (cm)", "thigh_cm": "Coscia (cm)",
            "skinfold_tricipite": "Tricipitale (mm)", "skinfold_bicipite": "Bicipitale (mm)",
            "skinfold_sottoscapolare": "Sottoscapolare (mm)", "skinfold_sovrailiaca": "Sovrailiaca (mm)"
        }
    }

    # Campi BIA consigliati (per la finestra "dati mancanti" dopo l'import)
    missing_fields = []
    derived_fields = {}
    if parsed["type"] == "bia":
        rec = ["bmr_kcal", "mm_pct", "bf_pct", "tbw_l", "pha", "ffm_kg", "smm_kg"]
        for k in rec:
            if k not in parsed["data"]:
                missing_fields.append(k)
        # Deriva BMR con Mifflin-St Jeor dal paziente (se peso+altezza presenti)
        if "bmr_kcal" not in parsed["data"] and "weight_kg" in parsed["data"] and "height_cm" in parsed["data"]:
            try:
                pat = db.get_patient(pid) or {}
                age = energy_calc.age_from_birth(pat.get("birth_date")) or 30
                w = float(parsed["data"]["weight_kg"]); h = float(parsed["data"]["height_cm"])
                derived_fields["bmr_kcal"] = energy_calc.bmr_mifflin(w, h, age, str(pat.get("sex") or "M"))
            except Exception:
                pass

    return {
        "ok": True,
        "needs_review": False,
        "detected_type": parsed["type"],
        "confidence": parsed.get("confidence", 0),
        "mapped_fields": parsed["data"],
        "field_labels": field_labels.get(parsed["type"], {}),
        "missing_fields": missing_fields,
        "derived_fields": derived_fields,
        "suggested_endpoint": f"/api/patients/{pid}/bia" if parsed["type"] == "bia" else f"/api/patients/{pid}/anthropometry"
    }


@app.post("/api/patients/{pid}/import/confirm")
async def api_smart_import_confirm(pid: int, request: Request):
    """Conferma e salva i dati importati (dopo anteprima)."""
    b = await request.json()
    itype = b.get("type")
    fields = b.get("fields", {})
    date = b.get("date") or dt.date.today().isoformat()

    if itype == "bia":
        bid = db.add_bia(pid, fields, date, source="import")
        return {"ok": True, "id": bid, "message": "BIA importata ✓"}
    elif itype == "anthropometry":
        fields["date"] = date
        aid = db.add_anthropometry(pid, fields)
        return {"ok": True, "id": aid, "message": "Antropometria importata ✓"}
    elif itype == "diet_plan":
        # Genera il piano dai target importati e lo salva
        targets = fields.get("targets") or {}
        options = fields.get("options") or {}
        preset = fields.get("preset") or options.get("preset") or ""
        client = db.get_patient(pid) or {}
        parsed = clinical_nutrition.parse_pathologies(client.get("pathologies"))
        conditions = list(parsed["conditions"])
        for c in (options.get("conditions") or []):
            if c and c not in conditions:
                conditions.append(c)
        allergies = client.get("allergies", "")
        if parsed["allergies"]:
            allergies = (allergies + "," + ",".join(parsed["allergies"])).strip(",")
        excl = meal_planner.excluded_foods(conditions, allergies)
        excl.update(options.get("exclude_foods") or [])
        options["exclude_foods"] = sorted(excl)
        if not targets.get("kcal"):
            bia = db.list_bia(pid, limit=1)
            if bia and bia[0].get("weight_kg"):
                w = float(bia[0]["weight_kg"])
                h = float(bia[0].get("height_cm") or 170)
                age = 35
                targets["kcal"] = int(24 * w * (1.3 if not client.get("sex") == "F" else 1.2))
        # Normalizza days: int -> lista nomi giorni
        all_days = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
        raw_days = options.get("days", all_days)
        if isinstance(raw_days, int):
            options["days"] = all_days[:raw_days]
        elif not isinstance(raw_days, list):
            options["days"] = all_days
        # Normalizza targets: percentuali -> grammi (come fa api_generate_plan)
        kcal = int(targets.get("kcal") or 2000)
        gp = float(targets.get("protein_pct") or targets.get("p_pct") or 0)
        gc = float(targets.get("carb_pct") or targets.get("c_pct") or 0)
        gf = float(targets.get("fat_pct") or targets.get("f_pct") or 0)
        if gp and gc and gf and not targets.get("p"):
            p_grams = round(kcal * gp / 100 / 4, 1)
            c_grams = round(kcal * gc / 100 / 4, 1)
            f_grams = round(kcal * gf / 100 / 9, 1)
        else:
            p_grams = float(targets.get("p") or targets.get("protein") or 0)
            c_grams = float(targets.get("c") or targets.get("carbs") or 0)
            f_grams = float(targets.get("f") or targets.get("fat") or 0)
        if not p_grams: p_grams = round(kcal * 0.30 / 4, 1)
        if not c_grams: c_grams = round(kcal * 0.45 / 4, 1)
        if not f_grams: f_grams = round(kcal * 0.25 / 9, 1)
        gen_targets = {"kcal": kcal, "p": p_grams, "c": c_grams, "f": f_grams}
        plan = meal_planner.generate_plan(gen_targets, options)
        p = int(round(p_grams * 4 / kcal * 100)) if kcal else 30
        c = int(round(c_grams * 4 / kcal * 100)) if kcal else 45
        f = int(round(f_grams * 9 / kcal * 100)) if kcal else 25
        title = f"Piano importato {client.get('name','')} {_today()}"
        if preset:
            title += f" [{diet_presets.PRESETS.get(preset,{}).get('label', preset)}]"
        did = db.add_diet_plan(pid, title, preset, conditions, kcal, p, c, f, plan)
        return {"ok": True, "id": did, "message": "Piano alimentare importato ✓"}
    else:
        raise HTTPException(400, f"Tipo non supportato per conferma: {itype}")


# ─── OCR z.ai (browser integrato + client) ──────────────────────────────

@app.get("/api/ocr/zai/status")
def api_zai_status():
    """Stato token z.ai: True se il login OCR è già stato fatto."""
    try:
        from app import zai_ocr
        return {"ok": True, "logged_in": zai_ocr.token_presente(),
                "browser_available": zai_ocr.browser_interno_ok()}
    except Exception as e:
        return {"ok": False, "logged_in": False, "error": str(e)}


@app.post("/api/ocr/zai/open")
async def api_zai_open():
    """Apre ocr.z.ai nel browser integrato (pywebview, processo separato)."""
    try:
        from app import zai_ocr
        ok = zai_ocr.apri_browser_ocr()
        return {"ok": ok, "message": "Browser OCR aperto ✓" if ok else "Browser non disponibile (pywebview mancante)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/ocr/zai/login")
async def api_zai_login():
    """Apre il login z.ai e cattura il token per l'OCR automatico."""
    try:
        from app import zai_ocr
        ok, msg = zai_ocr.login_e_cattura_token()
        return {"ok": bool(ok), "message": msg}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/ocr/zai/logout")
async def api_zai_logout():
    """Rimuove il token z.ai salvato."""
    try:
        from app import zai_ocr
        zai_ocr.cancella_token()
        return {"ok": True, "message": "Token rimosso"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/ocr/zai/process")
async def api_zai_process(pid: int, file: UploadFile = File(...)):
    """Carica un file (immagine/PDF) su z.ai, esegue l'OCR e restituisce il
    testo (Markdown) e le tabelle (HTML) estratti per l'anteprima di import."""
    try:
        from app import zai_ocr
        if not zai_ocr.token_presente():
            return {"ok": False, "error": "Login z.ai non effettuato. Aprilo dal bottone OCR e accedi.", "needs_login": True}
        # Salva il file temporaneo
        fname = f"zai_{_timestamp()}_{file.filename or 'upload'}"
        path = os.path.join(UPLOAD_DIR, fname)
        total = 0
        with open(path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPLOAD_SIZE:
                    raise HTTPException(413, "File troppo grande (max 10 MB)")
                out.write(chunk)
        dati = zai_ocr.carica_e_estrai(path)
        md, tables = zai_ocr.estrai_testo_e_tabelle(dati)
        return {"ok": True, "markdown": (md or "")[:20000], "tables": tables[:5],
                "note": "Copia il testo/tabelle e incollalo nel modale di import, oppure usa 'Importa direttamente'."}
    except HTTPException:
        raise
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/ocr/local/process")
async def api_ocr_local_process(pid: int, file: UploadFile = File(...)):
    """OCR locale (nessun servizio esterno): rasterizza PDF/immagine e
    estrae i campi BIA con Windows OCR / Tesseract (gia' bundled).

    Ritorna i campi mappati (stesso formato di /api/import) per
    l'anteprima di conferma. Se il file ha gia' testo estraibile
    (PDF nativo), usa direttamente quello.
    """
    try:
        from app.ocr_engine import parse_bia_pdf
        fname = f"local_{_timestamp()}_{file.filename or 'upload'}"
        path = os.path.join(UPLOAD_DIR, fname)
        total = 0
        with open(path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPLOAD_SIZE:
                    raise HTTPException(413, "File troppo grande (max 10 MB)")
                out.write(chunk)
        with open(path, "rb") as f:
            _pre_bytes = f.read()
        # Windows OCR usa asyncio.run(): esegui in un thread fuori dall'event loop
        data = await asyncio.to_thread(parse_bia_pdf, _pre_bytes)
        if not data:
            return {"ok": False, "error": "Nessun dato BIA riconosciuto dal file. Riprova con un'immagine piu' nitida."}
        # Mappa per compatibilita' con l'anteprima import
        compat = {"phase_angle": "pha", "weight_kg": "weight_kg", "height_cm": "height_cm",
                  "fat_mass_kg": "bf_kg", "fat_free_mass_kg": "ffm_kg", "fat_mass_pct": "bf_pct"}
        out = {}
        for k, v in data.items():
            key = compat.get(k, k)
            if isinstance(v, (int, float)):
                out[key] = v
        return {"ok": True, "detected_type": "bia", "mapped_fields": out,
                "confidence": 0.8, "note": "OCR locale completato — verifica i valori in anteprima"}
    except HTTPException:
        raise
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─── FOOD CATALOG ──────────────────────────────────────────────────

@app.get("/api/foods")
def api_foods_search(q: str = "", cat: str = "", limit: int = 30):
    return db.search_food_catalog(query=q, category=cat, limit=limit)


@app.get("/api/foods/categories")
def api_food_categories():
    return db.get_food_categories()


@app.get("/api/foods/{fid}")
def api_get_food(fid: int):
    f = db.get_food(fid)
    if not f:
        raise HTTPException(404, "Alimento non trovato")
    return f


@app.get("/api/foods/{fid}/swaps")
def api_food_swaps(fid: int, limit: int = 5):
    """Sostituzioni nutriente-equivalenti per un alimento."""
    return {"swaps": db.get_food_swaps(fid, limit=limit)}


# ─── BODY COMPOSITION API (FFMI, FMI, WHR, BMI, radar) ───────────────────

@app.get("/api/patients/{pid}/body-composition")
def api_body_comp(pid: int):
    """Calcola FFMI, FMI, WHR, BMI per il paziente."""
    results = db.get_body_composition_data(pid)
    if not results:
        raise HTTPException(404, "Dati insufficienti (servono peso + altezza + BF%)")
    return results


@app.get("/api/patients/{pid}/radar")
def api_radar(pid: int):
    """Dati per radar chart confronto metriche BIA (valore, min, max)."""
    comp = db.get_body_composition_data(pid)
    if not comp:
        raise HTTPException(404, "Dati insufficienti")
    radar = {
        "metrics": [],
        "patient_name": comp.get("name", ""),
    }
    # Ranges di riferimento (normalizzati 0-100)
    refs = {
        "ffmi": {"label": "FFMI", "min": 14, "max": 26, "unit": "kg/m²"},
        "fmi": {"label": "FMI", "min": 2, "max": 12, "unit": "kg/m²"},
        "bmi": {"label": "BMI", "min": 16, "max": 35, "unit": "kg/m²"},
        "bf_pct": {"label": "BF%", "min": 5, "max": 40, "unit": "%"},
        "mm_pct": {"label": "MM%", "min": 20, "max": 50, "unit": "%"},
        "pha": {"label": "PhA", "min": 3, "max": 12, "unit": "°"},
    }
    for key, ref in refs.items():
        val = comp.get(key)
        if val is not None:
            # normalizza 0-100
            norm = max(0, min(100, (val - ref["min"]) / (ref["max"] - ref["min"]) * 100))
            radar["metrics"].append({
                "key": key, "label": ref["label"],
                "value": val, "normalized": round(norm, 1),
                "min": ref["min"], "max": ref["max"], "unit": ref["unit"]
            })
    return radar


# ─── ADHERENCE REPORT ────────────────────────────────────────────────────

@app.get("/api/patients/{pid}/adherence")
def api_adherence(pid: int, days_back: int = 7):
    """Report aderenza dieta: macro target vs effettivi per giorno."""
    from datetime import datetime, timedelta
    plan = db.get_latest_diet_plan(pid)
    if not plan:
        return {"adherence": [], "message": "Nessun piano attivo"}
    # calcola target giornalieri dal piano
    plan_data = (plan.get("plan_json") or plan.get("plan") or "{}")
    import json
    try: plan_data = json.loads(plan_data) if isinstance(plan_data, str) else plan_data
    except: plan_data = {}
    targets = {"kcal": plan.get("kcal") or 0, "pct_p": (plan.get("p") or 30) / 100,
               "pct_c": (plan.get("c") or 45) / 100, "pct_f": (plan.get("f") or 25) / 100}
    days_of_week = ["lun","mar","mer","gio","ven","sab","dom"]
    labels = {"lun":"Lunedì","mar":"Martedì","mer":"Mercoledì","gio":"Giovedì",
              "ven":"Venerdì","sab":"Sabato","dom":"Domenica"}
    adherence = []
    for d in days_of_week:
        items = db.list_diet_items(pid, day=d)
        macros = db.compute_meal_macros(items)
        current = {k: macros.get(k, 0) for k in ["kcal","protein_g","carbs_g","fat_g"]}
        target_kcal = targets.get("kcal") or 2000
        target_p = round(target_kcal * targets.get("pct_p", 0.3) / 4, 1)
        target_c = round(target_kcal * targets.get("pct_c", 0.45) / 4, 1)
        target_f = round(target_kcal * targets.get("pct_f", 0.25) / 9, 1)
        pct = round((current["kcal"] / max(target_kcal, 1)) * 100, 1)
        adherence.append({
            "day": d, "label": labels.get(d, d),
            "target_kcal": target_kcal, "actual_kcal": current["kcal"],
            "target_p": target_p, "actual_p": current.get("protein_g", 0),
            "target_c": target_c, "actual_c": current.get("carbs_g", 0),
            "target_f": target_f, "actual_f": current.get("fat_g", 0),
            "completion_pct": pct
        })
    return {"adherence": adherence, "patient_id": pid}


# ─── RECIPES API ─────────────────────────────────────────────────────────

@app.get("/api/recipes")
def api_list_recipes(category: str = "", q: str = "", limit: int = 20, offset: int = 0):
    items = db.list_recipes(category=category, q=q, limit=limit, offset=offset)
    total = db.count_recipes(category=category, q=q)
    return {"recipes": items, "total": total, "limit": limit, "offset": offset}


@app.get("/api/recipes/{rid}")
def api_get_recipe(rid: int):
    r = db.get_recipe(rid)
    if not r:
        raise HTTPException(404, "Ricetta non trovata")
    return r


@app.post("/api/recipes")
async def api_create_recipe(request: Request):
    b = await request.json()
    rid = db.create_recipe(
        b.get("name", "Ricetta"), b.get("ingredients", []),
        b.get("instructions", ""), b.get("servings", 4),
        b.get("category", ""), b.get("macros")
    )
    return {"ok": True, "id": rid}


@app.delete("/api/recipes/{rid}")
def api_delete_recipe(rid: int):
    db.delete_recipe(rid)
    return {"ok": True}


@app.post("/api/recipes/{rid}/apply")
async def api_apply_recipe(rid: int, request: Request):
    """Applica una ricetta come pasti per un paziente."""
    b = await request.json()
    pid = b.get("patient_id")
    day = b.get("day", "lun")
    meal = b.get("meal", "pranzo")
    recipe = db.get_recipe(rid)
    if not recipe:
        raise HTTPException(404, "Ricetta non trovata")
    ingredients = recipe.get("ingredients") or []
    if isinstance(ingredients, str):
        ingredients = []
    count = 0
    for ing in ingredients:
        if not isinstance(ing, dict):
            continue
        food_id = ing.get("food_id")
        grams = ing.get("grams", 100)
        if food_id:
            db.add_diet_item(
                pid=pid, plan_id=None, day=day, meal=meal,
                food=ing.get("name", ""), grams=grams, food_id=food_id
            )
            count += 1
    return {"ok": True, "items_added": count}


# ─── PATIENTS CRUD ────────────────────────────────────────────────────────

@app.get("/api/patients/{pid}/diet-macros/{day}")
def api_diet_macros(pid: int, day: str):
    """Calcola macro totali per un giorno specifico."""
    items = db.list_diet_items(pid, day=day)
    return db.compute_meal_macros(items)


@app.get("/api/patients/{pid}/diet/pdf")
def api_diet_pdf(pid: int):
    """Esporta il diario alimentare del paziente in PDF professionale."""
    from app.diet_pdf import generate_diet_pdf
    patient = db.get_patient(pid)
    if not patient:
        raise HTTPException(404, "Paziente non trovato")
    items = db.list_diet_items(pid)
    days_data = {}
    for it in items:
        d = it.get("day"); m = it.get("meal")
        days_data.setdefault(d, {}).setdefault(m, []).append(it)
    macros = {}
    for d in ["lun","mar","mer","gio","ven","sab","dom"]:
        macros[d] = db.compute_meal_macros(days_data.get(d, {}).get("colazione", []) +
                                           days_data.get(d, {}).get("spuntino", []) +
                                           days_data.get(d, {}).get("pranzo", []) +
                                           days_data.get(d, {}).get("spuntino2", []) +
                                           days_data.get(d, {}).get("cena", []))
    # Targets dall'ultimo piano
    plans = db.list_diet_plans(pid, limit=100)
    targets = {"kcal": 2000, "protein_pct": 30, "carb_pct": 45, "fat_pct": 25}
    if plans:
        p0 = plans[0]
        targets = {"kcal": p0.get("kcal_target") or 2000, "protein_pct": 30, "carb_pct": 45,
                   "fat_pct": 25, "preset": p0.get("preset") or ""}
    pdf_bytes = bytes(generate_diet_pdf(patient, targets, days_data, macros, brand=db.get_user_by_id(1)))
    fname = f"piano_{patient['name'].replace(' ','_')}_{_today()}.pdf"
    out_path = os.path.join(UPLOAD_DIR, fname)
    with open(out_path, "wb") as f:
        f.write(pdf_bytes)
    return FileResponse(out_path, media_type="application/pdf", filename=fname)


# ─── BIA TREND ───────────────────────────────────────────────────────────

@app.get("/api/patients/{pid}/bia-trend")
def api_bia_trend(pid: int):
    """Serie temporale delle misurazioni BIA per grafici multi-metrica."""
    rows = db.list_bia(pid)
    metrics = ["weight_kg", "bf_pct", "ffm_kg", "tbw_l", "pha", "mm_kg", "bmi"]
    series = {m: [] for m in metrics}
    dates = []
    for r in sorted(rows, key=lambda x: x.get("date", "")):
        dates.append(r.get("date"))
        for m in metrics:
            v = r.get(m)
            series[m].append(round(v, 2) if v is not None else None)
    return {"dates": dates, "series": series, "metrics": metrics}


@app.get("/api/patients/{pid}/bia-trend/pdf")
def api_bia_trend_pdf(pid: int):
    """Report PDF con grafici evolutivi."""
    from app.diet_pdf import generate_bia_report_pdf
    trend = api_bia_trend(pid)  # dict direct call (not async)
    p = db.get_patient(pid)
    pdf = bytes(generate_bia_report_pdf(p or {"name": f"P{pid}"}, trend, brand=db.get_user_by_id(1)))
    fname = f"report_bia_{p['name'].replace(' ','_') if p else pid}_{_today()}.pdf"
    out = os.path.join(UPLOAD_DIR, fname)
    with open(out, "wb") as f: f.write(pdf)
    return FileResponse(out, media_type="application/pdf", filename=fname)


# ─── FABBISOGNO ENERGETICO ─────────────────────────────────────────────────

@app.get("/api/patients/{pid}/energy-needs")
def api_energy_needs(pid: int, activity: str = "moderato", goal: str = "mantenimento"):
    """Calcola BMR/TDEE/target kcal dai dati del paziente (ultima BIA)."""
    from app import energy_calc
    p = db.get_patient(pid)
    if not p:
        raise HTTPException(404, "Paziente non trovato")
    bia = db.list_bia(pid, limit=1)
    b = bia[0] if bia else {}
    weight = b.get("weight_kg")
    height = b.get("height_cm")
    bf = b.get("bf_pct")
    age = energy_calc.age_from_birth(p.get("birth_date")) or 35
    if not weight:
        raise HTTPException(400, "Nessuna misurazione BIA con peso: inserire prima una BIA")
    if not height:
        height = 170
    return energy_calc.energy_needs(weight, height, age, p.get("sex", "M"),
                                    activity=activity, goal=goal, bf_pct=bf)


# ─── SHOPPING LIST ───────────────────────────────────────────────────────

@app.get("/api/patients/{pid}/shopping-list")
def api_shopping_list(pid: int):
    """Genera lista della spesa aggregata dal piano alimentare settimanale."""
    items = db.list_diet_items(pid)
    agg = {}
    for it in items:
        food = it.get("food", "—")
        grams = float(it.get("grams", 100) or 100)
        agg[food] = agg.get(food, 0) + grams
    # Ordina per categoria
    foods = db.get_db().execute(
        "SELECT name, category FROM food_catalog WHERE name IN (%s)" % ",".join("?" * len(agg)) or "''",
        tuple(agg.keys())).fetchall()
    cat_map = {r[0]: r[1] for r in foods}
    by_cat = {}
    for food, g in agg.items():
        cat = cat_map.get(food, "varie")
        by_cat.setdefault(cat, []).append({"food": food, "grams": round(g, 0)})
    by_cat = {k: sorted(v, key=lambda x: x["food"]) for k, v in by_cat.items()}
    return {"total_items": len(agg), "by_category": by_cat}


@app.get("/api/patients/{pid}/shopping-list/pdf")
def api_shopping_list_pdf(pid: int):
    """Export lista spesa in PDF."""
    from app.diet_pdf import generate_shopping_pdf
    data = api_shopping_list(pid)
    p = db.get_patient(pid)
    pdf = bytes(generate_shopping_pdf(p or {"name": f"P{pid}"}, data["by_category"], brand=db.get_user_by_id(1)))
    fname = f"spesa_{p['name'].replace(' ','_') if p else pid}_{_today()}.pdf"
    out = os.path.join(UPLOAD_DIR, fname)
    with open(out, "wb") as f: f.write(pdf)
    return FileResponse(out, media_type="application/pdf", filename=fname)


# ─── PATIENT PORTAL (read-only public) ──────────────────────────────────

@app.get("/portal/{token}")
def api_portal(token: str):
    p = db.get_db().execute("SELECT id FROM patients WHERE portal_token=?", (token,)).fetchone()
    if not p:
        raise HTTPException(404, "Token non valido")
    return FileResponse(str(__import__("pathlib").Path(__file__).parent / "templates" / "portal.html"))


@app.get("/api/portal/{token}/data")
def api_portal_data(token: str):
    """Dati JSON del portale paziente (separato dall'HTML)."""
    p = db.get_db().execute("SELECT id FROM patients WHERE portal_token=?", (token,)).fetchone()
    if not p:
        raise HTTPException(404, "Token non valido")
    pid = p["id"]
    patient = db.get_patient(pid)
    safe = {k: v for k, v in patient.items() if k not in ("portal_token",)}
    items = db.list_diet_items(pid)
    days_data = {}
    for it in items:
        d = it.get("day"); m = it.get("meal")
        days_data.setdefault(d, {}).setdefault(m, []).append({"food": it.get("food"), "grams": it.get("grams")})
    macros = {}
    for d in ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]:
        ms = days_data.get(d, {})
        macros[d] = db.compute_meal_macros(sum(ms.values(), []))
    bia = db.list_bia(pid, limit=1)
    return {"patient": safe, "plan": days_data, "macros": macros, "last_bia": bia[0] if bia else None}


@app.get("/api/portal/{token}/pdf")
def api_portal_pdf(token: str):
    """PDF del piano dal portale paziente."""
    p = db.get_db().execute("SELECT id FROM patients WHERE portal_token=?", (token,)).fetchone()
    if not p:
        raise HTTPException(404, "Token non valido")
    pid = p["id"]
    from app.diet_pdf import generate_diet_pdf
    patient = db.get_patient(pid)
    items = db.list_diet_items(pid)
    days_data = {}; macros = {}
    for it in items:
        d = it.get("day"); m = it.get("meal")
        days_data.setdefault(d, {}).setdefault(m, []).append(it)
    for d in ["lun","mar","mer","gio","ven","sab","dom"]:
        ms = days_data.get(d, {})
        macros[d] = db.compute_meal_macros(sum(ms.values(), []))
    plans = db.list_diet_plans(pid, limit=100)
    targets = {"kcal":2000,"protein_pct":30,"carb_pct":45,"fat_pct":25,"preset":""}
    if plans:
        p0 = plans[0]
        targets = {"kcal":p0.get("kcal_target") or 2000,"protein_pct":30,"carb_pct":45,"fat_pct":25,"preset":p0.get("preset") or ""}
    pdf_bytes = bytes(generate_diet_pdf(patient, targets, days_data, macros, brand=db.get_user_by_id(1)))
    out = os.path.join(UPLOAD_DIR, f"portal_{pid}_{_today()}.pdf")
    with open(out, "wb") as f: f.write(pdf_bytes)
    return FileResponse(out, media_type="application/pdf", filename=f"piano_{patient['name'].replace(' ','_')}.pdf")


@app.post("/api/patients/{pid}/portal-token")
def api_gen_portal_token(pid: int):
    """Genera/rigenera token per il portale paziente."""
    import secrets
    token = secrets.token_urlsafe(16)
    con = db.get_db()
    con.execute("UPDATE patients SET portal_token=? WHERE id=?", (token, pid))
    con.commit()
    return {"token": token, "url": f"/portal/{token}"}


# ─── SCALE MEASUREMENTS API ────────────────────────────────────────────

@app.get("/api/patients/{pid}/scale")
def api_list_scale(pid: int):
    return db.list_scale_measurements(pid)


@app.post("/api/patients/{pid}/scale")
async def api_add_scale(pid: int, request: Request):
    b = await request.json()
    sid = db.add_scale_measurement(pid,
        weight_kg=b.get("weight_kg"), bf_pct=b.get("bf_pct"),
        muscle_kg=b.get("muscle_kg"), tbw_kg=b.get("tbw_kg"),
        bone_kg=b.get("bone_kg"), visceral_fat=b.get("visceral_fat"),
        bmr=b.get("bmr"), metabolic_age=b.get("metabolic_age"),
        date=b.get("date"), source=b.get("source","manual"), notes=b.get("notes",""))
    return {"id": sid, "ok": True}


@app.delete("/api/scale/{sid}")
def api_delete_scale(sid: int):
    db.delete_scale_measurement(sid)
    return {"ok": True}


# ─── WEARABLE DATA API ─────────────────────────────────────────────────

@app.get("/api/patients/{pid}/wearable")
def api_list_wearable(pid: int):
    return db.list_wearable_data(pid)


@app.post("/api/patients/{pid}/wearable")
async def api_add_wearable(pid: int, request: Request):
    b = await request.json()
    wid = db.add_wearable_entry(pid, b.get("source","garmin"),
        date=b.get("date"), steps=b.get("steps",0),
        heart_rate_avg=b.get("heart_rate_avg"), heart_rate_rest=b.get("heart_rate_rest"),
        calories_active=b.get("calories_active",0), sleep_hours=b.get("sleep_hours"),
        stress_avg=b.get("stress_avg"), raw_data=json.dumps(b.get("raw_data",{})))
    return {"id": wid, "ok": True}


@app.delete("/api/wearable/{wid}")
def api_delete_wearable(wid: int):
    db.delete_wearable_entry(wid)
    return {"ok": True}


# ─── FITNESS IMPORTS API ───────────────────────────────────────────────

@app.get("/api/patients/{pid}/fitness")
def api_list_fitness(pid: int):
    return db.list_fitness_imports(pid)


@app.post("/api/patients/{pid}/fitness")
async def api_add_fitness(pid: int, request: Request):
    b = await request.json()
    fid = db.add_fitness_import(pid, b.get("source","strava"), b.get("activity_type",""),
        date=b.get("date"), duration_min=b.get("duration_min"),
        distance_km=b.get("distance_km"), elevation_m=b.get("elevation_m"),
        calories=b.get("calories"), avg_hr=b.get("avg_hr"),
        notes=b.get("notes",""), raw_data=json.dumps(b.get("raw_data",{})))
    return {"id": fid, "ok": True}


@app.delete("/api/fitness/{fid}")
def api_delete_fitness(fid: int):
    db.delete_fitness_import(fid)
    return {"ok": True}


    # ─── DIET TEMPLATES API ──────────────────────────────────────────────────

@app.get("/api/diet-templates")
def api_list_diet_templates():
    return {"templates": db.list_diet_templates()}


@app.post("/api/diet-templates")
async def api_create_diet_template(request: Request):
    b = await request.json()
    tid = db.create_diet_template(b.get("name", "Template"), b.get("targets", {}))
    return {"ok": True, "id": tid}


@app.delete("/api/diet-templates/{tid}")
def api_delete_diet_template(tid: int):
    db.delete_diet_template(tid)
    return {"ok": True}


# ─── BACKUP / EXPORT / IMPORT ───────────────────────────────────────────

@app.post("/api/backup")
def api_backup():
    """Crea backup del DB (copia file + dump JSON)."""
    import shutil
    src = db.DB_PATH
    ts = _today()
    backup_dir = os.path.join(os.path.dirname(src), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    # Copia file DB
    db_copy = os.path.join(backup_dir, f"nutricoach_{ts}.db")
    shutil.copy2(src, db_copy)
    # Dump JSON completo
    json_path = os.path.join(backup_dir, f"nutricoach_{ts}.json")
    data = db.export_all_json()
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"ok": True, "db": db_copy, "json": json_path, "timestamp": ts}


@app.get("/api/backup/auto")
def api_backup_auto():
    """Backup automatico giornaliero (idempotente: 1 al giorno)."""
    backup_dir = os.path.join(os.path.dirname(db.DB_PATH), "backups")
    today_file = os.path.join(backup_dir, f"nutricoach_{_today()}.db")
    if os.path.isfile(today_file):
        return {"ok": True, "skipped": True, "db": today_file}
    return api_backup()


@app.get("/api/export/patients")
def api_export_patients():
    """Export CSV di tutti i pazienti."""
    import csv, io
    patients = db.list_patients(limit=10000, offset=0)
    out = io.StringIO()
    if patients:
        w = csv.DictWriter(out, fieldnames=list(patients[0].keys()))
        w.writeheader()
        for p in patients:
            w.writerow(p)
    return Response(content=out.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=patients.csv"})


@app.get("/api/export/patient/{pid}")
def api_export_patient(pid: int):
    """Export JSON completo di un singolo paziente (BIA, dieta, appuntamenti, documenti)."""
    data = db.export_patient_json(pid)
    if not data:
        raise HTTPException(404, "Paziente non trovato")
    return Response(content=json.dumps(data, ensure_ascii=False, indent=2),
                    media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename=patient_{pid}.json"})


@app.post("/api/import/patient")
async def api_import_patient(request: Request):
    """Import paziente da JSON export."""
    data = await request.json()
    new_id = db.import_patient_json(data)
    return {"ok": True, "id": new_id}


# ─── PATIENTS CRUD ────────────────────────────────────────────────────────

@app.get("/api/patients")
def api_list_patients(cat_id: int = None, limit: int = 20, offset: int = 0):
    items = db.list_patients(cat_id, limit=limit, offset=offset)
    total = db.count_patients(cat_id)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@app.get("/api/patients/compare")
def api_compare(ids: str):
    idlist = [int(x.strip()) for x in ids.split(",") if x.strip()]
    return db.compare_patients(idlist)


@app.get("/api/patients/{pid}")
def api_get_patient(pid: int):
    p = db.get_patient(pid)
    if not p:
        raise HTTPException(404, "Paziente non trovato")
    return p

@app.post("/api/patients")
async def api_create_patient(request: Request):
    b = await request.json()
    name = (b.get("name") or "").strip()
    if not name:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Il nome del paziente e richiesto")
    if len(name) > 200:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Il nome del paziente non puo superare 200 caratteri")
    pid = db.add_patient(name, b.get("sex","M"), b.get("phone",""), b.get("email",""),
                         b.get("goal",""), b.get("sport",""), b.get("notes",""), b.get("allergies",""),
                         b.get("category_id"))
    # language can be updated separately
    lang = b.get("language")
    if lang:
        db.update_patient(pid, language=lang)
    # meals_per_day can be updated separately
    mpd = b.get("meals_per_day")
    if mpd is not None:
        db.update_patient(pid, meals_per_day=int(mpd))
    return {"ok": True, "id": pid}
@app.put("/api/patients/{pid}")
async def api_update_patient(pid: int, request: Request):
    b = await request.json()
    allowed = {"name","sex","phone","email","goal","sport","notes","allergies","category_id","birth_date","language","meals_per_day"}
    kw = {k: v for k, v in b.items() if k in allowed}
    if kw:
        db.update_patient(pid, **kw)
    return {"ok": True}


# ─── ALLERGENS ───────────────────────────────────────────────────────────

@app.get("/api/allergens")
def api_allergens():
    """Restituisce lista di allergeni noti e alimenti che li contengono."""
    foods = db.get_all_foods() if hasattr(db, 'get_all_foods') else db.search_food_catalog(query="", limit=500)
    known_allergens = {
        "glutine": ["grano","farro","orzo","segale","avena","cracker","pane","pasta","semolino","cous cous","bulgur"],
        "lattosio": ["latte","yogurt","formaggio","ricotta","mozzarella","parmigiano","panna","burro","crema di latte","latti","gelato"],
        "uova": ["uovo","uova","frittata","maionese","pasta all'uovo"],
        "soia": ["soia","tofu","tempeh","edamame","salsa di soia"],
        "arachidi": ["arachidi","burro d'arachidi","olio d'arachidi"],
        "frutta secca": ["mandorle","noci","nocciole","pistacchi","anacardi","noci pecan","macadamia"],
        "crostacei": ["gamberi","gamberetti","aragosta","scampi","mazzancolle"],
        "pesce": ["salmone","tonno","merluzzo","sogliola","orata","branzino","trota","sgombro","acciughe"],
        "sedano": ["sedano","sedano rapa"],
        "senape": ["senape","semi di senape"],
        "sesamo": ["sesamo","olio di sesamo","pasta di sesamo","tahini"],
    }
    results = {}
    for allergen, keywords in known_allergens.items():
        matches = []
        for kw in keywords:
            for f in foods:
                if kw.lower() in f.get("name","").lower() and f not in matches:
                    matches.append(f)
                    if len(matches) >= 10:
                        break
            if len(matches) >= 10:
                break
        if matches:
            results[allergen] = [{"id": m["id"], "name": m["name"], "category": m["category"]} for m in matches]
    return results


# ─── AUTH ─────────────────────────────────────────────────────────────────

@app.post("/api/login")
async def api_login(request: Request):
    b = await request.json()
    username = b.get("username", "")
    password = b.get("password", "")
    user = db.get_user(username)
    if not user or user["password_hash"] != hashlib.sha256(password.encode()).hexdigest():
        raise HTTPException(401, "Credenziali non valide")
    token = db.create_session(user["id"])
    return {"ok": True, "token": token, "user": {"id": user["id"], "username": user["username"],
                                                  "role": user["role"], "clinic_name": user["clinic_name"],
                                                  "logo_url": user["logo_url"], "theme_color": user["theme_color"]}}


@app.get("/api/auto-login")
def api_auto_login():
    """Auto-login with default admin user — no credentials needed."""
    user = db.get_user("admin")
    if not user:
        raise HTTPException(500, "Admin user not found")
    token = db.create_session(user["id"])
    return {"ok": True, "token": token, "user": {"id": user["id"], "username": user["username"],
                                                  "role": user["role"], "clinic_name": user["clinic_name"],
                                                  "logo_url": user["logo_url"], "theme_color": user["theme_color"]}}


@app.post("/api/logout")
async def api_logout(request: Request):
    b = await request.json()
    db.delete_session(b.get("token", ""))
    return {"ok": True}


@app.get("/api/session")
def api_get_session(token: str = ""):
    s = db.get_session(token)
    if not s:
        raise HTTPException(401, "Sessione non valida")
    return s


@app.get("/api/settings")
def api_get_settings(token: str = ""):
    s = db.get_session(token)
    if not s:
        raise HTTPException(401, "Non autenticato")
    return {"clinic_name": s["clinic_name"], "logo_url": s["logo_url"], "theme_color": s["theme_color"],
            "username": s["username"], "role": s["role"]}


@app.post("/api/settings")
async def api_save_settings(request: Request):
    b = await request.json()
    s = db.get_session(b.get("token", ""))
    if not s:
        raise HTTPException(401, "Non autenticato")
    db.update_user_settings(s["user_id"],
                            clinic_name=b.get("clinic_name"),
                            logo_url=b.get("logo_url"),
                            theme_color=b.get("theme_color"))
    return {"ok": True}


@app.post("/api/setup-wizard")
async def api_setup_wizard(request: Request):
    b = await request.json()
    token = b.get("token", "")
    s = db.get_session(token)
    if not s:
        raise HTTPException(401, "Non autenticato")
    folder = b.get("backup_folder", "")
    db.set_backup_folder(s["user_id"], folder)
    return {"ok": True, "backup_folder": folder}


@app.get("/api/setup-wizard")
def api_get_setup_wizard(token: str = ""):
    s = db.get_session(token)
    if not s:
        raise HTTPException(401, "Non autenticato")
    folder = db.get_backup_folder(s["user_id"])
    return {"backup_folder": folder, "has_folder": bool(folder)}


# ─── STATISTICS ──────────────────────────────────────────────────────────

@app.get("/api/stats")
def api_stats():
    return db.get_studio_stats()


@app.on_event("startup")
async def _ensure_tables():
    db.ensure_v2_tables()


# ─── DIARY CHECK PASTI ───────────────────────────────────────────────────

@app.get("/api/patients/{pid}/diary")
def api_diary(pid: int, date: str = ""):
    if date:
        return db.get_diary_entries(pid, date)
    return db.get_diary_entries(pid)


@app.post("/api/patients/{pid}/diary")
async def api_save_diary(pid: int, request: Request):
    b = await request.json()
    eid = db.save_diary_entry(pid, b.get("date", ""), b.get("meal", ""), b.get("food_id"),
                               b.get("food_name", ""), b.get("consumed", 0), b.get("notes", ""),
                               b.get("plan_id"))
    return {"id": eid, "ok": True}


@app.patch("/api/diary/{eid}")
async def api_update_diary(eid: int, request: Request):
    b = await request.json()
    db.update_diary_entry(eid, b.get("consumed"), b.get("notes"))
    return {"ok": True}


# ─── CHAT ────────────────────────────────────────────────────────────────

@app.get("/api/patients/{pid}/messages")
def api_messages(pid: int):
    return db.get_messages(pid)


@app.post("/api/patients/{pid}/messages")
async def api_send_message(pid: int, request: Request):
    b = await request.json()
    mid = db.send_message(pid, b.get("text", ""), b.get("sender", "nutritionist"))
    if b.get("sender") == "patient":
        p = db.get_patient(pid)
        db.add_app_notification(pid, f"💬 Messaggio da {p['name']}",
                                b.get("text","")[:80], "message")
    return {"id": mid, "ok": True}


@app.post("/api/patients/{pid}/messages/read")
def api_mark_read(pid: int):
    db.mark_messages_read(pid)
    return {"ok": True}


@app.get("/api/patients/{pid}/messages/unread")
def api_unread(pid: int):
    return {"count": db.count_unread(pid)}


# ─── NOTIFICATIONS (IN-APP) ──────────────────────────────────────────────

NOTIF_ICONS = {"message":"💬","appointment":"📅","reminder":"⏰","alert":"⚠️"}

@app.get("/api/notifications")
def api_notifications(unread: bool = False):
    return db.get_app_notifications(unread_only=unread)


@app.get("/api/notifications/unread")
def api_notif_unread():
    return {"count": db.count_app_unread()}


@app.post("/api/notifications/{nid}/read")
def api_notif_read(nid: int):
    db.mark_app_read(nid)
    return {"ok": True}


@app.post("/api/notifications/read-all")
def api_notif_read_all():
    db.mark_all_app_read()
    return {"ok": True}


@app.post("/api/notifications")
async def api_create_notif(request: Request):
    b = await request.json()
    nid = db.add_app_notification(b.get("patient_id"), b.get("title",""), b.get("message",""), b.get("type","reminder"))
    return {"id": nid, "ok": True}


# ─── PATIENTS ─────────────────────────────────────────────────────────────

# ─── CATEGORIES ────────────────────────────────────────────────────────────

@app.delete("/api/patients/{pid}")
def api_delete_patient(pid: int, token: str = ""):
    # App single-user ad auto-login: nessuna autenticazione richiesta.
    # Il token è accettato per compatibilità ma non è obbligatorio.
    db.delete_patient(pid)
    return {"ok": True}


# ─── DRUG-NUTRIENT INTERACTIONS ─────────────────────────────────────────

@app.get("/api/drugs")
def api_search_drugs(q: str = "", limit: int = 20):
    return {"drugs": db.search_drugs(query=q, limit=limit)}


@app.get("/api/drugs/all")
def api_all_drugs():
    return db.search_drugs(limit=500)


# ─── QUESTIONNAIRES ──────────────────────────────────────────────────────

@app.get("/api/questionnaires")
def api_list_questionnaires():
    """Restituisce la lista dei questionari disponibili con le domande."""
    return {"questionnaires": {k: {"name": v["name"], "description": v["description"],
                                   "max_score": v["max_score"], "questions": v["questions"]}
                               for k, v in db.QUESTIONNAIRES.items()}}


@app.post("/api/patients/{pid}/questionnaires")
async def api_save_questionnaire(pid: int, request: Request):
    try:
        b = await request.json()
    except Exception:
        b = {}
    if not b.get("questionnaire"):
        raise HTTPException(400, "Campo obbligatorio: questionnaire")
    qid = db.save_questionnaire_result(
        pid, b["questionnaire"], b.get("score", 0),
        b.get("answers", []), b.get("notes", ""))
    return {"ok": True, "id": qid}


@app.get("/api/patients/{pid}/questionnaires")
def api_list_patient_questionnaires(pid: int, questionnaire: str = ""):
    q = questionnaire if questionnaire else None
    return {"results": db.list_questionnaire_results(pid, questionnaire=q)}


# ─── CATEGORIES ────────────────────────────────────────────────────────────

@app.get("/api/categories")
def api_list_categories():
    return db.list_categories()

@app.post("/api/categories")
async def api_create_category(request: Request):
    try:
        b = await request.json()
    except Exception:
        b = {}
    if not b.get("name"):
        raise HTTPException(400, "Campo obbligatorio: name")
    cid = db.add_category(b["name"], b.get("color","#6366f1"))
    return {"id": cid}

@app.delete("/api/categories/{cid}")
def api_delete_category(cid: int):
    db.delete_category(cid)
    return {"ok": True}

# ─── BIA ──────────────────────────────────────────────────────────────────

@app.get("/api/patients/{pid}/bia")
def api_bia_list(pid: int):
    return db.list_bia(pid)

@app.get("/api/patients/{pid}/bia-analysis")
def api_bia_analysis(pid: int):
    """Analisi BIA avanzata: indici derivati + riassunto clinico in italiano."""
    bia = db.list_bia(pid)
    if not bia:
        return {"ok": True, "has_data": False, "calculations": {}, "flags": [], "summary": ""}
    latest = bia[0]  # list_bia ordina per data DESC
    patient = db.get_patient(pid) or {}
    anthro = db.list_anthropometry(pid)
    anthro_latest = anthro[0] if anthro else None
    r = bia_analysis.summarize(latest, patient, anthro_latest)
    r["has_data"] = True
    r["latest_date"] = latest.get("date")
    r["patient_name"] = patient.get("name", "")
    r["sex"] = patient.get("sex", "")
    return {"ok": True, **r}

@app.post("/api/patients/{pid}/bia")
async def api_add_bia(pid: int, request: Request):
    b = await request.json()
    bid = db.add_bia(pid, b, b.get("date"))
    return {"ok": True, "id": bid}

@app.post("/api/patients/{pid}/bia/upload")
async def api_bia_upload(pid: int, file: UploadFile = File(...)):
    # --- Size limit check (10 MB) ---
    total_size = 0
    chunk_size = 1024 * 1024  # 1 MB chunks
    content_chunks = []
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File troppo grande (max 10 MB)")
        content_chunks.append(chunk)

    file_bytes = b"".join(content_chunks)

    # Store the file on disk
    path = os.path.join(UPLOAD_DIR, f"bia_{pid}_{_timestamp()}_{file.filename}")
    with open(path, "wb") as f:
        f.write(file_bytes)

    # No server-side OCR — just store the file.
    # The frontend will display the PDF/image so the user can enter BIA values manually
    # (or use a browser-based OCR service like zai.qwen.ai).
    return {"ok": True, "path": path,
            "note": "File caricato. Inserire i valori BIA manualmente."}

@app.delete("/api/bia/{bid}")
def api_delete_bia(bid: int):
    db.delete_bia(bid)
    return {"ok": True}


# ─── ANTHROPOMETRY ────────────────────────────────────────────────────────

@app.get("/api/patients/{pid}/anthropometry")
def api_list_anthropometry(pid: int):
    return db.list_anthropometry(pid)


@app.post("/api/patients/{pid}/anthropometry")
async def api_add_anthropometry(pid: int, request: Request):
    b = await request.json()
    # Auto-calculate BMI, WHR, fat% if provided
    weight = b.get("weight_kg")
    height = b.get("height_cm")
    waist = b.get("waist_cm")
    hip = b.get("hip_cm")
    if weight and height:
        h = height / 100.0
        b["bmi"] = round(weight / (h * h), 1)
    if waist and hip:
        b["whr"] = round(waist / hip, 2)
    skinfolds = {}
    for k in ("tricipite", "bicipite", "sottoscapolare", "sovrailiaca"):
        sk_key = f"skinfold_{k}"
        # DB column is skinfold_sovraiaca (historical typo); map UI key to it
        if b.get(sk_key) is not None:
            skinfolds[k] = b[sk_key]
            if k == "sovrailiaca" and not b.get("skinfold_sovraiaca"):
                b["skinfold_sovraiaca"] = b[sk_key]
        elif b.get("skinfold_sovraiaca") is not None and k == "sovrailiaca":
            skinfolds[k] = b["skinfold_sovraiaca"]
    if len(skinfolds) == 4:
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from anthropometry import fat_percent_durnin
            # Get patient sex and age for Durnin calculation
            p = db.get_patient(pid)
            sex = p.get("sex", "M") if p else "M"
            age = 35  # default
            if p and p.get("birth_date"):
                try:
                    from datetime import date as _d
                    bd = _d.fromisoformat(p["birth_date"])
                    age = (_d.today() - bd).days // 365
                except Exception:
                    pass
            _, fat_pct = fat_percent_durnin(skinfolds, age, sex)
            if fat_pct is not None:
                b["fat_pct_durnin"] = fat_pct
        except Exception:
            pass
    aid = db.add_anthropometry(pid, b, b.get("date"))
    return {"ok": True, "id": aid}


@app.delete("/api/patients/{pid}/anthropometry/{aid}")
def api_delete_anthropometry(pid: int, aid: int):
    db.delete_anthropometry(aid)
    return {"ok": True}

# ─── MISURE ───────────────────────────────────────────────────────────────

@app.get("/api/patients/{pid}/measurements")
def api_list_measurements(pid: int):
    return db.list_measurements(pid) if hasattr(db, 'list_measurements') else []

@app.post("/api/patients/{pid}/measurements")
async def api_add_measurement(pid: int, request: Request):
    b = await request.json()
    # measurement handling...
    return {"ok": True}

# ─── DIET ──────────────────────────────────────────────────────────────────

@app.get("/api/patients/{pid}/diet-plans")
def api_list_diet_plans(pid: int, limit: int = 10, offset: int = 0):
    items = db.list_diet_plans(pid, limit=limit, offset=offset)
    total = db.count_diet_plans(pid)
    return {"items": items, "total": total, "limit": limit, "offset": offset}

@app.get("/api/patients/{pid}/diet-items")
def api_list_diet_items(pid: int, day: str = None):
    return db.list_diet_items(pid, day)

@app.post("/api/patients/{pid}/diet-items")
async def api_add_diet_item(pid: int, request: Request):
    b = await request.json()
    diid = db.add_diet_item(pid, b.get("plan_id"), b.get("day"), b.get("meal"), b.get("food"), b.get("grams", 100), b.get("alternative",""))
    return {"ok": True, "id": diid}

@app.delete("/api/diet-items/{iid}")
def api_delete_diet_item(iid: int):
    db.delete_diet_item(iid)
    return {"ok": True}

@app.post("/api/patients/{pid}/diet/clear")
def api_clear_diet(pid: int):
    db.clear_diet_items(pid)
    return {"ok": True}

# ─── APPOINTMENTS ─────────────────────────────────────────────────────────

@app.get("/api/appointments")
def api_list_appointments(pid: int = None, from_date: str = None, limit: int = 50, offset: int = 0):
    items = db.list_appointments(pid, from_date, limit=limit, offset=offset)
    total = db.count_appointments(pid, from_date)
    return {"items": items, "total": total, "limit": limit, "offset": offset}

@app.post("/api/appointments")
async def api_create_appointment(request: Request):
    try:
        b = await request.json()
    except Exception:
        b = {}
    if not b.get("patient_id") or not b.get("title") or not b.get("appt_date"):
        raise HTTPException(400, "Campi obbligatori: patient_id, title, appt_date")
    aid = db.add_appointment(b["patient_id"], b["title"], b["appt_date"], b.get("appt_time",""),
                             b.get("status","open"), b.get("follow_up",0), b.get("outcome",""), b.get("notes",""))
    return {"ok": True, "id": aid}

# ─── NOTIFICATIONS (EMAIL) ────────────────────────────────────────────────

@app.get("/api/email-notifications")
def api_list_email_notifications(pid: int = None, pending: bool = False):
    return db.list_notifications(pid, pending)

@app.post("/api/email-notifications")
async def api_create_email_notification(request: Request):
    b = await request.json()
    nid = db.add_notification(b.get("patient_id", 0), b.get("type","email"), b.get("subject",""), b.get("message",""), b.get("bulk_id"))
    return {"ok": True, "id": nid}

@app.post("/api/email-notifications/{nid}/sent")
def api_mark_sent(nid: int):
    db.mark_sent(nid)
    return {"ok": True}

# ─── DOCUMENTS ────────────────────────────────────────────────────────────

@app.get("/api/documents")
def api_list_documents(pid: int = None, limit: int = 50, offset: int = 0):
    items = db.list_documents(pid, limit=limit, offset=offset)
    total = db.count_documents(pid)
    return {"items": items, "total": total, "limit": limit, "offset": offset}

@app.post("/api/documents")
async def api_create_document(request: Request):
    try:
        b = await request.json()
    except Exception:
        b = {}
    if not b.get("patient_id"):
        raise HTTPException(400, "Campo obbligatorio: patient_id")
    did = db.add_document(b["patient_id"], b.get("title",""), b.get("doc_type",""), b.get("file_path",""))
    return {"ok": True, "id": did}

# ─── SYMPTOMS ─────────────────────────────────────────────────────────────

@app.get("/api/patients/{pid}/symptoms")
def api_list_symptoms(pid: int):
    return {"symptoms": db.list_symptoms(pid)}

@app.post("/api/patients/{pid}/symptoms")
async def api_add_symptom(pid: int, request: Request):
    b = await request.json()
    sid = db.add_symptom(pid, b.get("date",_today()), b.get("time",""),
                         bloating=b.get("bloating",0), pain=b.get("pain",0), gas=b.get("gas",0),
                         nausea=b.get("nausea",0), heartburn=b.get("heartburn",0),
                         constipation=b.get("constipation",0), diarrhea=b.get("diarrhea",0),
                         bristol=b.get("bristol",0), urgency=b.get("urgency",0), incomplete=b.get("incomplete",0),
                         foods=b.get("foods",""), notes=b.get("notes",""))
    return {"ok": True, "id": sid}

@app.delete("/api/symptoms/{sid}")
def api_delete_symptom(sid: int):
    db.get_db().execute("DELETE FROM symptoms WHERE id=?", (sid,)).connection.commit()
    return {"ok": True}

@app.get("/api/patients/{pid}/symptoms/summary")
def api_symptom_summary(pid: int, days: int = 30):
    con = db.get_db()
    rows = con.execute("""
        SELECT COUNT(*) as cnt,
               AVG(bloating) as avg_bloating, AVG(pain) as avg_pain,
               AVG(gas) as avg_gas, AVG(nausea) as avg_nausea,
               AVG(heartburn) as avg_heartburn, AVG(constipation) as avg_constipation,
               AVG(diarrhea) as avg_diarrhea
        FROM symptoms WHERE patient_id=? AND date>=date('now','-{} days')
    """.format(days), (pid,)).fetchone()
    return dict(rows) if rows else {}

# ─── PROGRESS NOTES ────────────────────────────────────────────────────────

@app.get("/api/patients/{pid}/progress-notes")
def api_list_progress(pid: int):
    return db.list_progress_notes(pid)

@app.post("/api/patients/{pid}/progress-notes")
async def api_add_progress(pid: int, request: Request):
    b = await request.json()
    nid = db.add_progress_note(pid, b.get("note",""), b.get("date"))
    return {"ok": True, "id": nid}

@app.delete("/api/progress-notes/{nid}")
def api_delete_progress(nid: int):
    db.delete_progress_note(nid)
    return {"ok": True}

# ─── VERSION ──────────────────────────────────────────────────────────────

@app.get("/api/version")
def api_version():
    _, V = os.path.dirname(__file__), "2.20.15"
    return {"version": V, "platform": sys.platform}

# ─── UPDATE CHECK (GitHub Releases) ──────────────────────────────────────
_GITHUB_REPO = "quadrellif90-collab/NutriCoach"
_GITHUB_RELEASES_URL = f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest"
_UPDATE_CACHE_TTL_S = 6 * 3600  # 6 hours
_UPDATE_CACHE_PATH = os.path.join(db.DATA_DIR, "update_cache.json")

def _read_update_cache():
    try:
        return json.loads(open(_UPDATE_CACHE_PATH, encoding="utf-8").read())
    except Exception:
        return None

def _write_update_cache(data):
    try:
        with open(_UPDATE_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def _cache_fresh(cache):
    if not cache:
        return False
    if cache.get("current") != "2.20.15":
        return False
    try:
        from datetime import datetime, timezone
        ts = datetime.strptime(cache["checked_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - ts).total_seconds() < _UPDATE_CACHE_TTL_S
    except Exception:
        return False

@app.get("/api/update/check")
def api_update_check(force: int = 0):
    """Check GitHub releases for updates. Returns {current, latest, update_available, ...}"""
    import sys as _sys
    from datetime import datetime, timezone

    plat = _sys.platform
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cache = _read_update_cache()

    if not force and _cache_fresh(cache):
        cache["cached"] = True
        cache["current"] = "2.20.15"
        cache["update_available"] = cache.get("latest", "0") > "2.20.15"
        return cache

    try:
        import urllib.request
        req = urllib.request.Request(_GITHUB_RELEASES_URL, headers={"User-Agent": "NutriCoach"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            rel = json.loads(resp.read().decode())

        tag = (rel.get("tag_name") or "").lstrip("v").strip()
        if not tag:
            raise RuntimeError("release missing tag_name")

        # Select platform asset
        download_url, asset_name = None, None
        for asset in (rel.get("assets") or []):
            name = (asset.get("name") or "").lower()
            if plat == "win32" and name.endswith(".exe"):
                download_url = asset.get("browser_download_url")
                asset_name = asset.get("name")
                break
            elif plat == "darwin" and name.endswith(".dmg"):
                download_url = asset.get("browser_download_url")
                asset_name = asset.get("name")
                break

        payload = {
            "current": "2.20.15",
            "latest": tag,
            "update_available": "2.20.15" < tag,
            "release_url": rel.get("html_url", ""),
            "download_url": download_url,
            "asset_name": asset_name,
            "platform": plat,
            "checked_at": now,
            "cached": False,
            "error": None,
            "release_body": (rel.get("body") or "")[:2000],
        }
        _write_update_cache(payload)
        return payload

    except Exception as e:
        if cache:
            cache["cached"] = True
            cache["error"] = str(e)
            cache["current"] = "2.20.15"
            cache["update_available"] = cache.get("latest", "0") > "2.20.15"
            return cache
        return {"current": "2.20.15", "latest": None, "update_available": False,
                "release_url": None, "download_url": None, "asset_name": None,
                "platform": plat, "checked_at": now, "cached": False,
                "error": str(e), "release_body": None}

@app.get("/api/update/download")
def api_update_download():
    """Download the latest release and restart the app."""
    import urllib.request, subprocess, sys as _sys, time

    cache = _read_update_cache()
    if not cache or not cache.get("download_url"):
        return {"ok": False, "error": "Nessun aggiornamento disponibile. Fai prima un /api/update/check"}

    url = cache["download_url"]
    asset = cache.get("asset_name", "NutriCoach-Setup.exe")
    dest = os.path.join(db.DATA_DIR, asset)

    try:
        # Download
        req = urllib.request.Request(url, headers={"User-Agent": "NutriCoach"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)

        print(f"[NutriCoach Update] Download completato: {dest}")

        # Launch installer and restart app
        if _sys.platform == "win32":
            # Start installer silently with ELEVATION (UAC).
            # Senza "runas" un installer NSIS con requireAdministrator fallisce
            # con ERROR_ELEVATION_REQUIRED (WinError 740) se l'app gira in
            # Program Files senza privilegi admin.
            import ctypes
            launched = False
            try:
                res = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", dest, "/S", None, 1)
                # >32 => successo; 740 (ERROR_ELEVATION_REQUIRED) o altri => errore
                if res > 32:
                    launched = True
            except Exception:
                launched = False
            if not launched:
                # Fallback: tentativo normale; se fallisce, istruisci l'utente
                try:
                    subprocess.Popen([dest, "/S"], shell=False)
                    launched = True
                except Exception:
                    launched = False
            # Give installer time to start, then exit
            time.sleep(2)
            # Restart: launch new exe and exit current
            exe_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "NutriCoach.exe")
            if os.path.exists(exe_path):
                try:
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "open", exe_path, "", None, 1)
                except Exception:
                    subprocess.Popen([exe_path])
            os._exit(0)
        else:
            return {"ok": True, "downloaded": dest, "action": "manual_install"}

        return {"ok": True, "downloaded": dest}

    except Exception as e:
        return {"ok": False, "error": str(e)}

# ─── INIT ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    db.init_db()
    # Crea utente admin predefinito se non esiste
    pw_hash = hashlib.sha256("admin123".encode()).hexdigest()
    user = db.get_user("admin")
    if not user:
        uid = db.create_user("admin", pw_hash, "nutritionist", "NutriCoach Studio")
        if uid:
            print("[NutriCoach] Utente admin creato (admin / admin123)")
        else:
            print("[NutriCoach] ATTENZIONE: impossibile creare utente admin")
    elif user.get("password_hash") != pw_hash:
        # Aggiorna la password se diversa
        con = db.get_db()
        con.execute("UPDATE users SET password_hash=? WHERE username=?", (pw_hash, "admin"))
        con.commit()
        print("[NutriCoach] Password admin aggiornata (admin / admin123)")
    try:
        api_backup_auto()
    except Exception as e:
        print(f"[NutriCoach] backup auto saltato: {e}")
    print(f"[NutriCoach v2] DB={db.DB_PATH} pronto")

# ─── MAIN ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8400)