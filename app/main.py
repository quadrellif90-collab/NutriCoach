"""
NutriCoach v2 — App principale FastAPI (modulare, Dietowin-style).
"""
import os, sys, json, datetime as dt
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Tesseract OCR per BIA: imposta TESSDATA_PREFIX se non gia' in env
if not os.environ.get("TESSDATA_PREFIX"):
    for p in [r"C:\Program Files\Tesseract-OCR\tessdata",
              r"C:\Program Files\Tesseract-OCR\tessdata",
              "/usr/share/tesseract-ocr/4.00/tessdata",
              "/usr/local/share/tessdata"]:
        if os.path.isdir(p):
            os.environ["TESSDATA_PREFIX"] = p
            break

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import app.database as db
import clinical_nutrition, meal_planner, bia_parser, diet_presets, anthropometry, ocr
from app import bia_parser_v2

app = FastAPI(title="NutriCoach v2 — Dietowin", version="2.0.0")

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

# ─── PATIENTS CRUD ────────────────────────────────────────────────────────

@app.get("/api/patients")
def api_list_patients(cat_id: int = None):
    return db.list_patients(cat_id)

@app.get("/api/patients/{pid}")
def api_get_patient(pid: int):
    p = db.get_patient(pid)
    if not p:
        raise HTTPException(404, "Paziente non trovato")
    return p

@app.post("/api/patients")
async def api_create_patient(request: Request):
    b = await request.json()
    pid = db.add_patient(b.get("name",""), b.get("sex","M"), b.get("phone",""), b.get("email",""),
                         b.get("goal",""), b.get("sport",""), b.get("notes",""), b.get("allergies",""),
                         b.get("category_id"))
    return {"ok": True, "id": pid}

@app.put("/api/patients/{pid}")
async def api_update_patient(pid: int, request: Request):
    b = await request.json()
    allowed = {"name","sex","phone","email","goal","sport","notes","allergies","category_id","birth_date"}
    kw = {k: v for k, v in b.items() if k in allowed}
    if kw:
        db.update_patient(pid, **kw)
    return {"ok": True}

@app.delete("/api/patients/{pid}")
def api_delete_patient(pid: int):
    db.delete_patient(pid)
    return {"ok": True}

# ─── CATEGORIES ────────────────────────────────────────────────────────────

@app.get("/api/categories")
def api_list_categories():
    return db.list_categories()

@app.post("/api/categories")
async def api_create_category(request: Request):
    b = await request.json()
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

@app.post("/api/patients/{pid}/bia")
async def api_add_bia(pid: int, request: Request):
    b = await request.json()
    bid = db.add_bia(pid, b, b.get("date"))
    return {"ok": True, "id": bid}

@app.post("/api/patients/{pid}/bia/upload")
async def api_bia_upload(pid: int, file: UploadFile = File(...)):
    import asyncio
    path = os.path.join(UPLOAD_DIR, f"bia_{pid}_{_timestamp()}_{file.filename}")
    with open(path, "wb") as f:
        import shutil
        shutil.copyfileobj(file.file, f)
    # Usa il parser PCC (range fisiologici + decimal restoration + OCR robusto)
    res = await asyncio.to_thread(bia_parser_v2.parse_bia_file, path)
    if res.get("scanned"):
        return {"scanned": True, "pages": res.get("pages",[]), "file": path,
                "note": res.get("note","PDF scansionato non leggibile")}
    reading = res.get("reading", {})
    # Mappa campi PCC -> colonne DB
    mapping = {
        "weight_kg":"weight_kg","height_cm":"height_cm","bmi":"bmi",
        "fat_mass_pct":"bf_pct","fat_mass_kg":"bf_kg","fat_free_mass_kg":"ffm_kg",
        "tbw_l":"tbw_l","ecw_l":"ecw_l","icw_l":"icw_l",
        "phase_angle":"pha",
        "bcm_kg":"bcm_kg","smm_kg":"smm_kg","asmm_kg":"asmm_kg",
        "protein_kg":"protein_kg","protein_pct":"protein_pct",
        "visceral_fat":"visceral_fat_level","hydration_pct":"hydration_pct",
        "bone_kg":"mineral_kg","muscle_mass_kg":"mm_kg",
    }
    db_fields = {}
    for k, v in reading.items():
        if v is not None and k in mapping:
            db_fields[mapping[k]] = v
    # Se non c'e' bf_pct ma c'e' fat_mass_pct, usalo
    if "bf_pct" not in db_fields and reading.get("fat_mass_pct") is not None:
        db_fields["bf_pct"] = reading["fat_mass_pct"]
    bid = db.add_bia(pid, db_fields, source=file.filename)
    return {"ok": True, "bia_id": bid, "fields": db_fields,
            "note": res.get("note"), "restored": res.get("restored_fields")}

@app.delete("/api/bia/{bid}")
def api_delete_bia(bid: int):
    db.delete_bia(bid)
    return {"ok": True}

@app.get("/api/patients/{pid}/bia-trend")
def api_bia_trend(pid: int, field: str = "weight_kg", days: int = 365):
    return db.bia_trend(pid, field, days)

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
def api_list_diet_plans(pid: int):
    return db.list_diet_plans(pid)

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
def api_list_appointments(pid: int = None, from_date: str = None):
    return db.list_appointments(pid, from_date)

@app.post("/api/appointments")
async def api_create_appointment(request: Request):
    b = await request.json()
    aid = db.add_appointment(b["patient_id"], b["title"], b["appt_date"], b.get("appt_time",""),
                             b.get("status","open"), b.get("follow_up",0), b.get("outcome",""), b.get("notes",""))
    return {"ok": True, "id": aid}

# ─── NOTIFICATIONS ────────────────────────────────────────────────────────

@app.get("/api/notifications")
def api_list_notifications(pid: int = None, pending: bool = False):
    return db.list_notifications(pid, pending)

@app.post("/api/notifications")
async def api_create_notification(request: Request):
    b = await request.json()
    nid = db.add_notification(b["patient_id"], b.get("type","email"), b.get("subject",""), b.get("message",""), b.get("bulk_id"))
    return {"ok": True, "id": nid}

@app.post("/api/notifications/{nid}/sent")
def api_mark_sent(nid: int):
    db.mark_sent(nid)
    return {"ok": True}

# ─── DOCUMENTS ────────────────────────────────────────────────────────────

@app.get("/api/documents")
def api_list_documents(pid: int = None):
    return db.list_documents(pid)

@app.post("/api/documents")
async def api_create_document(request: Request):
    b = await request.json()
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
        FROM symptoms WHERE patient_id=? AND date>=date('now','-? days')
    """, (pid, days)).fetchone()
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

# ─── COMPARE ──────────────────────────────────────────────────────────────

@app.get("/api/patients/compare")
def api_compare(ids: str):
    idlist = [int(x.strip()) for x in ids.split(",") if x.strip()]
    return db.compare_patients(idlist)

# ─── VERSION ──────────────────────────────────────────────────────────────

@app.get("/api/version")
def api_version():
    _, V = os.path.dirname(__file__), "2.0.0"
    return {"version": V, "platform": sys.platform}

# ─── INIT ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    db.init_db()
    print(f"[NutriCoach v2] DB={db.DB_PATH} pronto")

# ─── MAIN ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8400)