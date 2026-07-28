"""
NutriCoach v2 — App principale FastAPI (modulare, Dietowin-style).
"""
import os, sys, json, asyncio, datetime as dt
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
from app import ocr_engine  # OCR integrato: Windows OCR + fallback Tesseract

app = FastAPI(title="NutriCoach v2 — Dietowin", version="2.7.0")

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
    plans = db.list_diet_plans(pid)
    targets = {"kcal": 2000, "protein_pct": 30, "carb_pct": 45, "fat_pct": 25}
    if plans:
        p0 = plans[0]
        targets = {"kcal": p0.get("kcal_target") or 2000, "protein_pct": 30, "carb_pct": 45,
                   "fat_pct": 25, "preset": p0.get("preset") or ""}
    pdf_bytes = bytes(generate_diet_pdf(patient, targets, days_data, macros))
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
    metrics = ["weight_kg", "bf_pct", "ffm_kg", "tbw_kg", "phase_angle", "muscle_kg", "bmi"]
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
    pdf = bytes(generate_bia_report_pdf(p or {"name": f"P{pid}"}, trend))
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
    pdf = bytes(generate_shopping_pdf(p or {"name": f"P{pid}"}, data["by_category"]))
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


@app.post("/api/patients/{pid}/portal-token")
def api_gen_portal_token(pid: int):
    """Genera/rigenera token per il portale paziente."""
    import secrets
    token = secrets.token_urlsafe(16)
    con = db.get_db()
    con.execute("UPDATE patients SET portal_token=? WHERE id=?", (token, pid))
    con.commit()
    return {"token": token, "url": f"/portal/{token}"}


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
    path = os.path.join(UPLOAD_DIR, f"bia_{pid}_{_timestamp()}_{file.filename}")
    with open(path, "wb") as f:
        import shutil
        shutil.copyfileobj(file.file, f)

    # OCR Engine: Windows OCR primario, Tesseract fallback
    with open(path, "rb") as f:
        pdf_bytes = f.read()
    fields = await asyncio.to_thread(ocr_engine.parse_bia_pdf, pdf_bytes)

    if not fields:
        return {"ok": False, "error": "Nessun dato BIA estratto dal PDF"}

    # Mappa campi -> colonne DB (ocr_engine già produce bf_kg, ffm_kg, etc.)
    bid = db.add_bia(pid, fields, source=file.filename)
    return {"ok": True, "bia_id": bid, "fields": fields,
            "note": "OCR engine: Windows.Media.Ocr"}

@app.delete("/api/bia/{bid}")
def api_delete_bia(bid: int):
    db.delete_bia(bid)
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