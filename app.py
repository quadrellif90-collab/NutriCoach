"""NutriCoach — Backend FastAPI (localhost, nessun cloud)."""

import os
import sys
import json
import shutil
import tempfile
import datetime
import subprocess
import urllib.request
import urllib.error
from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# risoluzione percorso risorse: funziona sia da sorgente che da EXE (PyInstaller)
def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)

import db as database
import diet_parser
import bia_parser
import nutrition_engine
import anthropometry as ant
import charts
import pdf_export
import auth
import notifications
import nutrition_db as ndb
import meal_planner
import diet_presets
import sport_science
import pdf_sport_science
import clinical_nutrition
import version

UPLOAD_DIR = os.path.join(database.DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="NutriCoach", version="1.6.8")

app.add_middleware(
    CORSMiddleware,
    # app locale single-user: consenti solo origin localhost (era "*", troppo permissivo
    # con allow_credentials=True)
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

STATIC = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC, exist_ok=True)


# ---------------- UI ----------------
@app.get("/")
def api_root():
    return FileResponse(resource_path(os.path.join("templates", "dashboard.html")))


# ---------------- Alimenti (ricerca + custom) ----------------
@app.get("/api/foods/search")
def api_food_search(q: str = "", limit: int = 25):
    return ndb.search_foods(q, limit)

@app.get("/api/foods/custom")
def api_custom_foods():
    return database.list_custom_foods()

@app.post("/api/foods/custom")
async def api_custom_food_add(request: Request):
    b = await request.json()
    fid = database.add_custom_food(b.get("name", ""), b.get("per_100g", {}))
    return {"ok": True, "id": fid}

@app.delete("/api/foods/custom/{fid}")
def api_custom_food_del(fid: int):
    database.delete_custom_food(fid)
    return {"ok": True}


# ---------------- Diet builder (diario) ----------------
@app.post("/api/clients/{cid}/diet-item")
async def api_diet_item_add(cid: int, request: Request):
    b = await request.json()
    iid = database.add_diet_item(cid, b.get("day", ""), b.get("meal", ""),
                                 b.get("food", ""), b.get("grams", 0),
                                 int(bool(b.get("custom", 0))))
    return {"ok": True, "id": iid}

@app.get("/api/clients/{cid}/diet-items")
def api_diet_items(cid: int, day: str = None):
    return database.list_diet_items(cid, day)

@app.delete("/api/clients/{cid}/diet-item/{iid}")
def api_diet_item_del(cid: int, iid: int):
    database.delete_diet_item(iid)
    return {"ok": True}

@app.get("/api/clients/{cid}/diary/totals")
def api_diary_totals(cid: int, day: str = None):
    return meal_planner.diary_totals(cid, day)

@app.post("/api/clients/{cid}/plan/generate")
async def api_plan_generate(cid: int, request: Request):
    b = await request.json()
    targets = b.get("targets", {})
    options = b.get("options", {})
    # anamnesi + allergie del cliente -> esclusioni cliniche nel piano
    client = database.get_client(cid) or {}
    # SINGLE SOURCE OF TRUTH: parse_pathologies gestisce CSV e JSON
    parsed = clinical_nutrition.parse_pathologies(client.get("pathologies"))
    conditions = parsed["conditions"]
    # allergie da entrambe le fonti: campo cliente + anamnesi JSON
    allergies = client.get("allergies") or ""
    if parsed["allergies"]:
        allergies = (allergies + "," + ",".join(parsed["allergies"])).strip(",")
    excl = meal_planner.excluded_foods(conditions, allergies)
    excl.update(options.get("exclude_foods") or [])
    options["exclude_foods"] = sorted(excl)
    plan = meal_planner.generate_plan(targets, options)
    plan["clinical"] = {
        "conditions": conditions,
        "excluded_foods": sorted(excl),
        "recommendations": clinical_nutrition.get_dietary_recommendations(conditions) if conditions else [],
    }
    # Gap 1: persisti il piano come dieta per renderlo esportabile in PDF
    import datetime as _dt
    title = f"Piano {client.get('name','')} {_dt.date.today().isoformat()}"
    if conditions:
        title += f" [{','.join(conditions)}]"
    did = database.add_diet(cid, plan, title=title, date=_dt.date.today().isoformat())
    plan["diet_id"] = did
    return plan


@app.get("/api/diet-presets")
def api_diet_presets():
    return {"presets": diet_presets.preset_list()}


@app.post("/api/diet-presets/targets")
async def api_diet_preset_targets(request: Request):
    b = await request.json()
    key = b.get("key", "personalizzato")
    kcal = float(b.get("kcal", 2000) or 2000)
    weight_kg = b.get("weight_kg")
    try:
        weight_kg = float(weight_kg) if weight_kg else None
    except Exception:
        weight_kg = None
    return diet_presets.preset_targets(key, kcal, weight_kg)


@app.get("/api/sport-science")
def api_sport_science():
    return sport_science.science_bundle()


@app.post("/api/sport-science/fueling")
async def api_sport_science_fueling(request: Request):
    b = await request.json()
    day_type = b.get("day_type")
    intensity = b.get("intensity")
    weight_kg = b.get("weight_kg")
    try:
        weight_kg = float(weight_kg) if weight_kg else None
    except Exception:
        weight_kg = None
    out = {}
    if day_type:
        out["daily"] = sport_science.fueling_daily_targets(day_type, weight_kg)
    if intensity:
        out["during"] = sport_science.fueling_during_targets(intensity)
    return out


@app.post("/api/sport-science/protein")
async def api_sport_science_protein(request: Request):
    b = await request.json()
    w = b.get("weight_kg")
    gpk = b.get("g_per_kg", 1.8)
    meals = b.get("meals", 4)
    try:
        w = float(w) if w else None
        gpk = float(gpk) if gpk else 1.8
        meals = int(meals) if meals else 4
    except Exception:
        w, gpk, meals = None, 1.8, 4
    return sport_science.protein_dist_targets(w, gpk, meals)


@app.post("/api/sport-science/creatine")
async def api_sport_science_creatine(request: Request):
    b = await request.json()
    w = b.get("weight_kg")
    sex = b.get("sex", "M")
    try:
        w = float(w) if w else None
    except Exception:
        w = None
    return sport_science.creatine_dose(w, sex)


@app.post("/api/sport-science/block")
async def api_sport_science_block(request: Request):
    b = await request.json()
    phase = b.get("phase")
    kcal = b.get("kcal", 2000)
    try:
        kcal = float(kcal) if kcal else 2000
    except Exception:
        kcal = 2000
    if not phase:
        raise HTTPException(400, "phase mancante")
    out = sport_science.block_phase_target(phase, None, kcal)
    if not out:
        raise HTTPException(404, "fase non valida")
    return out


@app.get("/api/clients/{cid}/sport-science-report")
def api_sport_science_report(cid: int, day_type: str = "race", intensity: str = "race", weight_kg: float = None):
    client = database.get_client(cid) or {}
    pdf = pdf_sport_science.build_sport_science_pdf(
        client=client, day_type=day_type, intensity=intensity, weight_kg=weight_kg)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=nutricoach_sport_science_{cid}.pdf"})


# ---------------- Clinical Nutrition (condizioni + anamnesi) ----------------
@app.get("/api/clinical-nutrition/conditions")
def api_clinical_conditions():
    """Lista di tutte le condizioni cliniche disponibili."""
    return {"conditions": clinical_nutrition.get_all_conditions()}

@app.get("/api/clinical-nutrition/conditions/{condition_key}")
def api_clinical_condition(condition_key: str):
    """Dettagli di una condizione clinica."""
    cond = clinical_nutrition.get_condition(condition_key)
    if not cond:
        raise HTTPException(404, "Condizione non trovata")
    return cond

@app.post("/api/clinical-nutrition/recommendations")
async def api_clinical_recommendations(request: Request):
    """Raccomandazioni dietetiche basate sulle condizioni del cliente."""
    b = await request.json()
    conditions = b.get("conditions", [])
    client_info = b.get("client_info", {})
    return clinical_nutrition.generate_anamnesis_report(conditions, client_info)

@app.post("/api/clients/{cid}/anamnesis")
async def api_save_anamnesis(cid: int, request: Request):
    """Salva le condizioni cliniche del cliente (anamnesi) nella colonna pathologies."""
    b = await request.json()
    conditions = b.get("conditions", [])
    notes = b.get("notes", "")
    # salva come JSON nella colonna pathologies (esistente)
    anamnesis_data = {"clinical_conditions": conditions, "anamnesis_notes": notes}
    database.update_client(cid, pathologies=json.dumps(anamnesis_data))
    client = database.get_client(cid) or {}
    recs = clinical_nutrition.generate_anamnesis_report(conditions, {"name": client.get("name", "")})
    return {"ok": True, "recommendations": recs}

@app.get("/api/clients/{cid}/anamnesis")
def api_get_anamnesis(cid: int):
    """Leggi l'anamnesi del cliente."""
    client = database.get_client(cid) or {}
    raw = client.get("pathologies", "") or ""
    try:
        data = json.loads(raw)
    except Exception:
        data = {}
    conditions = data.get("clinical_conditions", []) if isinstance(data, dict) else []
    notes = data.get("anamnesis_notes", "") if isinstance(data, dict) else ""
    recs = clinical_nutrition.generate_anamnesis_report(conditions, {"name": client.get("name", "")})
    return {"conditions": conditions, "notes": notes, "recommendations": recs}

@app.post("/api/clients/{cid}/check-in")
async def api_check_in(cid: int, request: Request):
    """Registra un check-in settimanale del cliente."""
    b = await request.json()
    checkin = {
        "date": b.get("date", datetime.date.today().isoformat()),
        "weight_kg": b.get("weight_kg"),
        "compliance_pct": b.get("compliance_pct"),
        "mood": b.get("mood", ""),
        "symptoms": b.get("symptoms", []),
        "notes": b.get("notes", ""),
        "energy_level": b.get("energy_level", 5),
    }
    database.add_progress_note(cid, checkin["date"], json.dumps(checkin))
    return {"ok": True, "checkin": checkin}

@app.get("/api/clients/{cid}/check-ins")
def api_get_check_ins(cid: int):
    """Leggi tutti i check-in del cliente."""
    notes = database.list_progress_notes(cid)
    checkins = []
    for n in notes:
        try:
            data = json.loads(n.get("text", ""))
            if isinstance(data, dict) and "compliance_pct" in data:
                checkins.append(data)
        except Exception:
            pass
    return {"checkins": checkins}


@app.get("/api/follow-up")
def api_follow_up(cid: int, current_kcal: float = None):
    """Analisi follow-up: trend peso, compliance, consiglio aggiustamento kcal."""
    import followup
    client = database.get_client(cid)
    if not client:
        raise HTTPException(404, "Cliente non trovato")
    checkins = api_get_check_ins(cid)["checkins"]
    checkins.sort(key=lambda c: c.get("date", ""))
    # fallback kcal: TDEE dall'antropometria se non passato
    if not current_kcal:
        anth = database.compute_anthropometry(cid) or {}
        current_kcal = anth.get("tdee")
    return followup.analyze(checkins, client.get("goal", ""), current_kcal)


@app.get("/api/studio/today")
def api_studio_today():
    """Home operativa: per ogni cliente calcola i segnali 'da seguire oggi'.
    Flag: peso mancante (>14gg), diario sintomi da rivedere (>7gg),
    piano assente, check-in settimanale mancante, note non lette."""
    import datetime as _dt
    today = _dt.date.today()
    clients = database.list_clients()
    out = []
    for c in clients:
        cid = c["id"]
        # pesi
        ms = database.list_measurements(cid)
        last_weight = ms[-1]["date"] if ms else None
        # sintomi
        sy = database.list_symptoms(cid, limit=1)
        last_symptom = sy[0]["date"] if sy else None
        # piani
        diets = database.list_diets(cid)
        has_plan = len(diets) > 0
        last_plan = diets[0]["date"] if diets else None
        # check-in (progress notes con compliance_pct)
        checkins = api_get_check_ins(cid)["checkins"]
        last_checkin = checkins[-1]["date"] if checkins else None

        def days_since(d):
            if not d:
                return 999
            try:
                return (today - _dt.date.fromisoformat(d)).days
            except Exception:
                return 999

        flags = []
        if days_since(last_weight) > 14:
            flags.append({"type": "peso", "label": "Peso da aggiornare", "days": days_since(last_weight)})
        if days_since(last_symptom) > 7:
            flags.append({"type": "diario", "label": "Diario da rivedere", "days": days_since(last_symptom)})
        if not has_plan:
            flags.append({"type": "piano", "label": "Nessun piano generato", "days": None})
        if days_since(last_checkin) > 7:
            flags.append({"type": "checkin", "label": "Check-in settimanale mancante", "days": days_since(last_checkin)})
        # R: appuntamento oggi
        todays = [a for a in database.list_appointments(cid) if (a.get("appt_date") or "").startswith(today.isoformat())]
        if todays:
            flags.append({"type": "agenda", "label": f"Appuntamento oggi: {todays[0].get('title','')}", "days": 0})

        out.append({
            "id": cid,
            "name": c.get("name", ""),
            "flags": flags,
            "last_weight": last_weight,
            "last_symptom": last_symptom,
            "last_plan": last_plan,
            "has_plan": has_plan,
            "needs_attention": len(flags) > 0,
        })
    out.sort(key=lambda x: (not x["needs_attention"], -sum(f["days"] or 0 for f in x["flags"])))
    return {"today": out, "count_attention": sum(1 for x in out if x["needs_attention"])}


@app.post("/api/studio/seed-demo")
def api_seed_demo():
    """Crea un cliente di esempio (Marco Demo) con anamnesi IBS+SIBO, una
    misurazione e un piano, per aiutare un nuovo utente a scoprire l'app.
    Idempotente: non crea duplicati se 'Marco Demo' esiste gia'."""
    clients = database.list_clients()
    if any(c.get("name") == "Marco Demo" for c in clients):
        return {"ok": True, "skipped": True, "message": "Cliente demo gia' presente"}
    cid = database.add_client("Marco Demo", sex="M", goal="Mantenimento",
                              age=34, height_cm=178, activity="Moderato",
                              allergies="noci",
                              pathologies=json.dumps({"clinical_conditions": ["ibs", "sibo"], "anamnesis_notes": "Esempio demo"}))
    database.add_measurement(cid, __import__("datetime").date.today().isoformat(), weight_kg=78.5, waist_cm=88)
    # piano demo salvato
    plan = meal_planner.generate_plan({"kcal": 2100, "p": 150, "c": 210, "f": 70}, {})
    database.add_diet(cid, plan, title="Piano Marco Demo (esempio)", date=__import__("datetime").date.today().isoformat())
    return {"ok": True, "client_id": cid, "message": "Cliente demo 'Marco Demo' creato"}


@app.post("/api/clients/{cid}/client-checkin")
async def api_client_checkin(cid: int, request: Request):
    """Check-in lato CLIENTE: peso + compliance + energia + sintomo rapido.
    Il nutrizionista vede chi ha risposto nella Home 'Oggi'."""
    b = await request.json()
    now = __import__("datetime").date.today().isoformat()
    checkin = {
        "date": b.get("date", now),
        "weight_kg": b.get("weight_kg"),
        "compliance_pct": b.get("compliance_pct"),
        "energy_level": b.get("energy_level", 5),
        "mood": b.get("mood", ""),
        "symptoms": b.get("symptoms", []),
        "notes": b.get("notes", ""),
        "source": "cliente",
    }
    database.add_progress_note(cid, checkin["date"], json.dumps(checkin))
    return {"ok": True, "checkin": checkin}


CONFIG_PATH = os.path.join(database.DATA_DIR, "studio_config.json")

def load_studio_config():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_studio_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

@app.get("/api/studio/config")
def api_get_config():
    cfg = load_studio_config()
    # non esporre la password SMTP
    safe = {k: ("" if k == "smtp_password" else v) for k, v in cfg.items()}
    safe["has_smtp_password"] = bool(cfg.get("smtp_password"))
    return safe

@app.post("/api/studio/config")
async def api_set_config(request: Request):
    body = await request.body()
    cfg = json.loads(body.decode() if body else "{}")
    # merge con esistente
    cur = load_studio_config()
    cur.update(cfg)
    save_studio_config(cur)
    return {"ok": True}

@app.post("/api/clients/{cid}/notify")
async def api_notify(cid: int, request: Request):
    """Invia un follow-up via email (SMTP reale se configurato) o whatsapp
    (link wa.me, 0 dipendenze). Registra in notification_log.
    Se l'email non e' configurata/invio fallisce, ritorna comunque il link
    (mailto o wa.me) per invio manuale."""
    b = await request.json()
    client = database.get_client(cid) or {}
    channel = b.get("channel", "email")
    ctype = b.get("type", "piano")
    subject = b.get("subject", f"NutriCoach — {ctype} {client.get('name', 'Cliente')}")
    body = b.get("body", "In allegato/collegato il tuo piano. A presto!")
    email = client.get("email") or ""
    phone = (client.get("phone") or "").strip().replace(" ", "").replace("+", "").replace("-", "")
    result = {"ok": True, "channel": channel, "logged": True, "sent": False}

    if channel == "email":
        if email:
            cfg = load_studio_config()
            if cfg.get("smtp_host") and cfg.get("smtp_user") and cfg.get("smtp_password"):
                try:
                    import smtplib, ssl
                    from email.message import EmailMessage
                    msg = EmailMessage()
                    msg["Subject"] = subject
                    msg["From"] = cfg.get("smtp_from", cfg["smtp_user"])
                    msg["To"] = email
                    msg.set_content(body)
                    ctx = ssl.create_default_context()
                    with smtplib.SMTP(cfg["smtp_host"], int(cfg.get("smtp_port", 587))) as s:
                        if cfg.get("smtp_tls", True):
                            s.starttls(context=ctx)
                        s.login(cfg["smtp_user"], cfg["smtp_password"])
                        s.send_message(msg)
                    result["sent"] = True
                    result["method"] = "smtp"
                except Exception as e:
                    result["smtp_error"] = str(e)
            # fallback mailto
            import urllib.parse
            result["mailto"] = f"mailto:{email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
            result["email"] = email
        else:
            result["email_missing"] = True
    elif channel == "whatsapp":
        if phone:
            import urllib.parse
            result["wa_link"] = f"https://wa.me/{phone}?text={urllib.parse.quote(body)}"
            result["phone"] = phone
        else:
            result["phone_missing"] = True

    database.add_notification_log(cid, ctype, channel, note=subject)
    return result


# ===== Backup / Export / Restore (P) =====
BACKUP_DIR = os.path.join(database.DATA_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

@app.get("/api/studio/export")
def api_export_archive():
    """Esporta l'intero archivio: scarica il DB SQLite + un dump JSON di tutti i clienti."""
    import shutil, io, json as _json
    db_path = database.DB_PATH
    if not os.path.exists(db_path):
        raise HTTPException(404, "DB non trovato")
    # dump JSON di tutti i clienti
    clients = database.list_clients()
    dump = {"exported_at": datetime.datetime.now().isoformat(), "clients": []}
    for c in clients:
        cid = c["id"]
        dump["clients"].append({
            "client": c,
            "measurements": database.list_measurements(cid),
            "diets": database.list_diets(cid),
            "symptoms": database.list_symptoms(cid),
            "supplements": database.list_supplements(cid),
            "diet_phases": database.list_diet_phases(cid),
            "progress_notes": database.list_progress_notes(cid),
        })
    # costruisci uno zip in memoria
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(db_path, "nutricoach.db")
        z.writestr("clients_dump.json", _json.dumps(dump, ensure_ascii=False, indent=2))
    buf.seek(0)
    from fastapi.responses import Response
    return Response(content=buf.getvalue(),
                    media_type="application/zip",
                    headers={"Content-Disposition": "attachment; filename=nutricoach_archivio.zip"})

@app.post("/api/studio/backup-now")
def api_backup_now():
    """Crea subito un backup del DB in ~/.nutricoach/backups/YYYYMMDD-HHMM.db."""
    import shutil, datetime as _dt
    ts = _dt.datetime.now().strftime("%Y%m%d-%H%M")
    dest = os.path.join(BACKUP_DIR, f"nutricoach_{ts}.db")
    shutil.copy2(database.DB_PATH, dest)
    # tieni solo gli ultimi 7
    files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")])
    for old in files[:-7]:
        try: os.remove(os.path.join(BACKUP_DIR, old))
        except Exception: pass
    return {"ok": True, "backup": dest, "kept": len(files[-7:])}

@app.get("/api/studio/backups")
def api_list_backups():
    files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")], reverse=True)
    return {"backups": files, "dir": BACKUP_DIR}

@app.post("/api/studio/restore")
async def api_restore_backup(request: Request):
    """Ripristina un backup: invia il nome file da /api/studio/backups oppure
    upload diretto. SOVRASCRIVE il DB corrente — usare con cautela."""
    import shutil
    b = await request.json()
    name = b.get("name") or ""
    src = os.path.join(BACKUP_DIR, os.path.basename(name))
    if not os.path.exists(src):
        raise HTTPException(404, "Backup non trovato")
    # backup di sicurezza prima di sovrascrivere
    api_backup_now()
    shutil.copy2(src, database.DB_PATH)
    return {"ok": True, "restored": name}


@app.post("/api/clients/{cid}/share-plan")
async def api_share_plan(cid: int, request: Request):
    """Genera un PDF del piano alimentare per condividerlo con il cliente."""
    b = await request.json()
    client = database.get_client(cid) or {}
    diet_id = b.get("diet_id")
    if not diet_id:
        diets = database.list_diets(cid)
        if diets:
            diet_id = diets[0].get("id")
    if not diet_id:
        raise HTTPException(404, "Nessuna dieta trovata per questo cliente")
    diet = database.get_diet(diet_id) or {}
    try:
        import io
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        title_style = ParagraphStyle('Title2', parent=styles['Title'], fontSize=18, spaceAfter=20)
        story.append(Paragraph(f"Piano Alimentare — {client.get('name', 'Cliente')}", title_style))
        story.append(Paragraph(f"Data: {datetime.date.today().strftime('%d/%m/%Y')}", styles['Normal']))
        story.append(Spacer(1, 20))
        diet_data = diet.get("diet", {})
        for day in diet_data.get("days", []):
            story.append(Paragraph(f"<b>Giorno {day.get('day', '')}</b>", styles['Heading2']))
            for meal in day.get("meals", []):
                meal_name = meal.get("meal", "")
                items = meal.get("items", [])
                items_text = ", ".join(f"{i.get('food','')} {i.get('g','')}g" for i in items)
                totals = meal.get("totals", {})
                kcal = round(totals.get("kcal", 0))
                story.append(Paragraph(f"<b>{meal_name}</b>: {items_text} ({kcal} kcal)", styles['Normal']))
            day_totals = day.get("totals", {})
            story.append(Paragraph(
                f"<i>Totale giorno: {round(day_totals.get('kcal',0))} kcal | "
                f"P {round(day_totals.get('protein',0))}g | "
                f"C {round(day_totals.get('carbs',0))}g | "
                f"F {round(day_totals.get('fat',0))}g</i>", styles['Normal']))
            story.append(Spacer(1, 10))
        story.append(Spacer(1, 20))
        # === E: sezione clinica unificata (conflitti + phased + pattern + esclusioni) ===
        conds = clinical_nutrition.parse_pathologies(client.get("pathologies"))["conditions"]
        if conds:
            names = [clinical_nutrition.get_condition(k).get("name", k)
                     for k in conds if clinical_nutrition.get_condition(k)]
            story.append(Paragraph("<b>🩺 Cartella Clinica</b>", styles['Heading2']))
            story.append(Paragraph("Condizioni: " + ", ".join(names), styles['Normal']))
            # conflitti
            if len(conds) > 1:
                conflicts = clinical_nutrition.get_condition_conflicts(conds)
                if conflicts:
                    story.append(Paragraph("<b>Conflitti da gestire:</b>", styles['Normal']))
                    for c in conflicts:
                        story.append(Paragraph("• " + c, styles['Normal']))
            # esclusioni
            avoid = clinical_nutrition.get_foods_to_avoid(conds)
            if avoid:
                story.append(Paragraph("<b>Alimenti da evitare/limitare:</b> " + "; ".join(avoid[:25]), styles['Normal']))
            # pattern dietetici consigliati
            patterns = clinical_nutrition.get_diet_patterns_for_conditions(conds)
            if patterns:
                story.append(Paragraph("<b>Pattern dietetici consigliati:</b> " +
                                       ", ".join(p["name"] for p in patterns[:4]), styles['Normal']))
            # phased protocol (per la prima condizione con protocollo)
            for k in conds:
                proto = clinical_nutrition.get_phased_protocol(k)
                if proto:
                    story.append(Paragraph(f"<b>Protocollo {proto['condition']}:</b> "
                                           f"eliminazione {proto['elimination'].get('duration_weeks','?')} sett, "
                                           f"reintroduzione {proto['reintroduction'].get('duration_weeks','?')} sett",
                                           styles['Normal']))
                    break
            story.append(Spacer(1, 10))
        story.append(Paragraph("Generato da NutriCoach", styles['Normal']))
        doc.build(story)
        return Response(content=buf.getvalue(), media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename=piano_{client.get('name','cliente').replace(' ','_')}.pdf"})
    except Exception as e:
        raise HTTPException(500, f"Errore generazione PDF: {e}")

# ---------------- Messaggi (thread locale) ----------------
@app.post("/api/clients/{cid}/message")
async def api_message_add(cid: int, request: Request):
    b = await request.json()
    mid = database.add_message(cid, b.get("direction", "nutri->client"), b.get("text", ""),
                                b.get("date"))
    return {"ok": True, "id": mid}

@app.get("/api/clients/{cid}/messages")
def api_messages(cid: int):
    return database.list_messages(cid)


# ---------------- Appuntamenti ----------------
@app.post("/api/appointments")
async def api_appt_add(request: Request):
    b = await request.json()
    aid = database.add_appointment(b.get("client_id"), b.get("title", ""),
        b.get("note", ""), b.get("appt_date"), b.get("status","open"), b.get("follow_up",0))
    return {"ok": True, "id": aid}

@app.get("/api/appointments")
def api_appointments(client_id: int = None, status: str = None):
    return database.list_appointments(client_id, status)

@app.put("/api/appointments/{aid}")
async def api_appt_update(aid: int, request: Request):
    b = await request.json()
    database.update_appointment(aid, **b)
    return {"ok": True}

@app.post("/api/appointments/{aid}/done")
async def api_appt_done(aid: int, request: Request):
    b = await request.json()
    database.set_appointment_done(aid, int(b.get("done", 1)))
    return {"ok": True}

@app.get("/api/follow-ups")
def api_follow_ups():
    return database.get_follow_ups()


# ---------------- Acqua ----------------
@app.post("/api/clients/{cid}/water")
async def api_water_add(cid: int, request: Request):
    b = await request.json()
    wid = database.add_water(cid, b.get("date", _today()), b.get("ml", 0))
    return {"ok": True, "id": wid}

@app.get("/api/clients/{cid}/water")
def api_water_get(cid: int, date: str = None):
    if date:
        return {"ml": database.get_water(cid, date)}
    return database.list_water(cid)


# ---------------- Note di progresso ----------------
@app.post("/api/clients/{cid}/progress-note")
async def api_prognote_add(cid: int, request: Request):
    b = await request.json()
    nid = database.add_progress_note(cid, b.get("date", _today()), b.get("text", ""))
    return {"ok": True, "id": nid}

@app.get("/api/clients/{cid}/progress-notes")
def api_prognote_list(cid: int):
    return database.list_progress_notes(cid)

@app.delete("/api/clients/{cid}/progress-note/{nid}")
def api_prognote_del(cid: int, nid: int):
    database.delete_progress_note(nid)
    return {"ok": True}


# ---------------- Clients ----------------
@app.get("/api/clients")
def api_clients():
    return database.list_clients()


@app.post("/api/clients")
async def api_client_create(request: Request):
    body = await request.json()
    cid = database.add_client(
        name=body.get("name", "Senza nome"),
        dob=body.get("dob", ""),
        sex=body.get("sex", ""),
        age=body.get("age"),
        height_cm=body.get("height_cm"),
        activity=body.get("activity", "moderato"),
        athlete=int(bool(body.get("athlete", False))),
        email=body.get("email", ""),
        phone=body.get("phone", ""),
        goal=body.get("goal", ""),
        allergies=body.get("allergies", ""),
        pathologies=body.get("pathologies", ""),
        preferences=body.get("preferences", ""),
        notes=body.get("notes", ""),
    )
    return {"id": cid}


@app.put("/api/clients/{cid}")
async def api_client_update(cid: int, request: Request):
    body = await request.json()
    database.update_client(cid, **body)
    return {"ok": True}


@app.post("/api/clients/{cid}/profile")
async def api_client_profile(cid: int, request: Request):
    """Aggiorna profilo anagrafico + anamnesi + misura antropometrica in un colpo solo."""
    body = await request.json()
    prof = {k: body.get(k) for k in
            ("name", "dob", "sex", "age", "height_cm", "activity", "athlete",
             "email", "phone", "goal", "allergies", "pathologies", "preferences", "notes")}
    prof = {k: v for k, v in prof.items() if v is not None}
    if prof:
        database.update_client(cid, **prof)
    m = body.get("measurement", {})
    if m:
        date = m.pop("date", None) or datetime.date.today().isoformat()
        database.add_measurement(cid, date, **m)
    return {"ok": True}


@app.get("/api/clients/{cid}/anthropometry")
def api_anthropometry(cid: int):
    res = database.compute_anthropometry(cid)
    if not res:
        raise HTTPException(404, "cliente non trovato")
    return res


@app.get("/api/clients/{cid}/charts")
def api_charts(cid: int, metric: str = "weight"):
    """Trend SVG per peso/%grassa/phA. metric: weight|fat|pha|all."""
    ms = database.list_measurements(cid)
    bias = database.list_bia(cid)
    labels = [m.get("date", "") for m in ms]
    weight = [m.get("weight_kg") for m in ms if m.get("weight_kg")]
    # % grassa ricavata da antropometria se hai le pieghe; qui usa BIA se presente
    fat, pha = [], []
    for b in bias:
        d = b.get("data", {})
        if "bodyFat" in d or "fat_pct" in d:
            fat.append(d.get("bodyFat") or d.get("fat_pct"))
        if "pha" in d or "phA" in d:
            pha.append(d.get("pha") or d.get("phA"))
    if metric == "weight":
        return Response(charts.line_chart(weight, labels, title="Peso (kg)", color="#0d9488"), media_type="image/svg+xml")
    if metric == "fat":
        return Response(charts.line_chart(fat, labels, title="% grassa", color="#f59e0b"), media_type="image/svg+xml")
    if metric == "pha":
        return Response(charts.line_chart(pha, labels, title="PhA (°)", color="#6366f1"), media_type="image/svg+xml")
    return Response(charts.trend_block(weight, fat, pha, labels), media_type="image/svg+xml")


@app.get("/api/clients/{cid}/export-pdf")
async def api_export_pdf(cid: int, diet_id: int = None, selections: str = "{}"):
    try:
        sel = json.loads(selections) if isinstance(selections, str) else selections
    except Exception:
        sel = {}
    path = os.path.join(tempfile.gettempdir(), f"report_{cid}.pdf")
    pdf_export.build_report_pdf(cid, diet_id, sel, path)
    return FileResponse(path, media_type="application/pdf", filename=f"report_{database.get_client(cid).get('name','cliente')}.pdf")


@app.post("/api/clients/{cid}/plan/export-pdf")
async def api_plan_export_pdf(cid: int, request: Request = None):
    """Genera e salva il piano filtrato, poi restituisce il PDF clinico unificato."""
    targets = {}
    if request:
        try:
            b = await request.json()
            targets = b.get("targets", {})
        except Exception:
            pass
    if not targets:
        targets = {"kcal": 2000, "p": 150, "c": 200, "f": 67}
    plan = meal_planner.generate_plan(targets, {})
    client = database.get_client(cid) or {}
    parsed = clinical_nutrition.parse_pathologies(client.get("pathologies"))
    conditions = parsed["conditions"]
    excl = meal_planner.excluded_foods(conditions, client.get("allergies") or "")
    plan["clinical"] = {"conditions": conditions, "excluded_foods": sorted(excl),
                         "recommendations": clinical_nutrition.get_dietary_recommendations(conditions) if conditions else []}
    import datetime as _dt
    did = database.add_diet(cid, plan, title=f"Piano {client.get('name','')} {_dt.date.today().isoformat()}", date=_dt.date.today().isoformat())
    path = os.path.join(tempfile.gettempdir(), f"report_{cid}.pdf")
    pdf_export.build_report_pdf(cid, did, {}, path)
    return FileResponse(path, media_type="application/pdf", filename=f"piano_{client.get('name','cliente')}.pdf")


# ---------------- Auth (login nutrizionista, locale) ----------------
@app.get("/api/auth/status")
def api_auth_status():
    return {"has_account": auth.has_account(), "username": auth.get_username()}


@app.post("/api/auth/setup")
async def api_auth_setup(request: Request):
    if auth.has_account():
        raise HTTPException(403, "account gia' creato")
    b = await request.json()
    user = (b.get("username") or "").strip()
    pw = b.get("password", "")
    if len(user) < 2:
        raise HTTPException(400, "username troppo corto (min 2)")
    if len(pw) < 4:
        raise HTTPException(400, "password troppo corta (min 4)")
    auth.set_account(user, pw)
    return {"ok": True}


@app.post("/api/auth/login")
async def api_auth_login(request: Request):
    if not auth.has_account():
        raise HTTPException(400, "crea prima un account")
    b = await request.json()
    if auth.verify_password(b.get("username", ""), b.get("password", "")):
        return {"ok": True}
    raise HTTPException(401, "credenziali errate")


@app.post("/api/auth/change")
async def api_auth_change(request: Request):
    b = await request.json()
    if not auth.verify_password(b.get("current_user", ""), b.get("current", "")):
        raise HTTPException(401, "credenziali attuali errate")
    user = (b.get("username") or "").strip() or auth.get_username()
    pw = b.get("password", "")
    if len(pw) < 4:
        raise HTTPException(400, "password troppo corta (min 4)")
    auth.set_account(user, pw)
    return {"ok": True}


@app.post("/api/auth/reset")
def api_auth_reset():
    """Reset delle credenziali (lascia intatti i dati dei clienti)."""
    auth.clear_account()
    return {"ok": True}


# ---------------- Reminders ----------------
@app.get("/api/reminders")
def api_reminders_list(client_id: int = None):
    return database.list_reminders(client_id)


@app.post("/api/clients/{cid}/reminders")
async def api_reminder_create(cid: int, request: Request):
    b = await request.json()
    rid = database.add_reminder(cid, b.get("title", ""), b.get("note", ""),
                                b.get("due_date"), b.get("channel", "app"))
    return {"id": rid}


@app.put("/api/reminders/{rid}/done")
async def api_reminder_done(rid: int, request: Request):
    b = await request.json()
    database.set_reminder_done(rid, int(b.get("done", 1)))
    return {"ok": True}


@app.delete("/api/reminders/{rid}")
def api_reminder_delete(rid: int):
    database.delete_reminder(rid)
    return {"ok": True}


# ---------------- Notifiche (config per cliente + coda) ----------------
@app.get("/api/clients/{cid}/notification-prefs")
def api_notif_prefs_get(cid: int):
    prefs = database.get_notification_prefs(cid)
    from_db = {p["type"]: p for p in prefs}
    out = []
    for t, label in notifications.TYPES.items():
        if t in from_db:
            p = from_db[t]; p["label"] = label
        else:
            p = {"type": t, "label": label, "enabled": False, "channel": "app", "freq": "weekly"}
        out.append(p)
    return out


@app.post("/api/clients/{cid}/notification-prefs")
async def api_notif_prefs_set(cid: int, request: Request):
    b = await request.json()
    database.set_notification_prefs(cid, b.get("prefs", []))
    return {"ok": True}


@app.post("/api/clients/{cid}/notifications/generate")
def api_notif_generate(cid: int):
    ids = notifications.generate_due(cid, database)
    return {"created": ids, "count": len(ids)}


@app.get("/api/notifications")
def api_notif_list(status: str = "pending", client_id: int = None):
    return database.list_notifications(client_id, status)


@app.put("/api/notifications/{nid}/sent")
async def api_notif_sent(nid: int, request: Request):
    b = await request.json()
    database.set_notification_sent(nid, bool(b.get("sent", True)))
    return {"ok": True}


# ---------------- Confronto clienti ----------------
@app.get("/api/clients/compare")
def api_compare(ids: str = ""):
    """ids = "1,3,5". Ritorna snapshot per confronto."""
    try:
        idlist = [int(x) for x in ids.split(",") if x.strip()]
    except Exception:
        idlist = []
    return database.compare_clients(idlist)


@app.get("/api/diets/{did}/export-diet-pdf")
async def api_export_diet_pdf(did: int, selections: str = "{}"):
    try:
        sel = json.loads(selections) if isinstance(selections, str) else selections
    except Exception:
        sel = {}
    d = database.get_diet(did)
    if not d:
        raise HTTPException(404, "dieta non trovata")
    path = os.path.join(tempfile.gettempdir(), f"dieta_{did}.pdf")
    pdf_export.build_diet_pdf(d["diet"], sel, path)
    return FileResponse(path, media_type="application/pdf", filename=f"dieta_{did}.pdf")


@app.get("/api/clients/{cid}")
def api_client_get(cid: int):
    c = database.get_client(cid)
    if not c:
        raise HTTPException(404, "Cliente non trovato")
    return c


# ---------------- Measurements ----------------
@app.post("/api/clients/{cid}/measurements")
async def api_measurement_add(cid: int, request: Request):
    body = await request.json()
    date = body.pop("date", None) or _today()
    mid = database.add_measurement(cid, date, **body)
    return {"ok": True, "id": mid}


@app.get("/api/clients/{cid}/measurements")
def api_measurements(cid: int):
    return database.list_measurements(cid)


@app.delete("/api/clients/{cid}/measurements/{mid}")
def api_measurement_del(cid: int, mid: int):
    database.delete_measurement(mid)
    return {"ok": True}


# ---------------- BIA ----------------
@app.post("/api/clients/{cid}/bia/upload")
async def api_bia_upload(cid: int, file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, f"bia_{cid}_{_timestamp()}_{file.filename}")
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    res = bia_parser.parse_bia_pdf(path)
    if res.get("scanned"):
        return {"scanned": True, "pages": res.get("pages", []), "file": path}
    # salva direttamente
    bid = database.add_bia(cid, _today(), res["fields"], source=file.filename)
    return {"scanned": False, "bia_id": bid, "fields": res["fields"]}


@app.post("/api/clients/{cid}/bia/paste")
async def api_bia_paste(cid: int, request: Request):
    body = await request.json()
    text = body.get("text", "")
    parsed = bia_parser.parse_bia_pasted(text)
    date = body.get("date", _today())
    bid = database.add_bia(cid, date, parsed["fields"], source="paste-ocr")
    return {"ok": True, "bia_id": bid, "fields": parsed["fields"]}


@app.get("/api/clients/{cid}/bia")
def api_bia_list(cid: int):
    return database.list_bia(cid)


# ---------------- Diets ----------------
@app.post("/api/clients/{cid}/diet/upload")
async def api_diet_upload(cid: int, file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, f"diet_{cid}_{_timestamp()}_{file.filename}")
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    res = diet_parser.parse_diet_pdf(path)
    if res.get("scanned"):
        return {"scanned": True, "text": "", "file": path}
    did = database.add_diet(cid, res["diet"], title=res["diet"].get("title", ""),
                            date=res["diet"].get("date", ""), source_file=file.filename)
    return {"scanned": False, "diet_id": did, "diet": res["diet"]}


@app.post("/api/clients/{cid}/diet/text")
async def api_diet_text(cid: int, request: Request):
    body = await request.json()
    text = body.get("text", "")
    parsed = diet_parser.parse_diet_text(text)
    did = database.add_diet(cid, parsed, title=body.get("title", "Dieta incollata"),
                            date=body.get("date", ""), source_file="paste")
    return {"diet_id": did, "diet": parsed}


@app.get("/api/clients/{cid}/diets")
def api_diets(cid: int):
    return database.list_diets(cid)


@app.get("/api/diets/{did}")
def api_diet_get(did: int):
    d = database.get_diet(did)
    if not d:
        raise HTTPException(404, "Dieta non trovata")
    return d


# ---------------- Computed: piano / spesa / riepilogo ----------------
@app.post("/api/diets/{did}/compute")
async def api_diet_compute(did: int, request: Request):
    d = database.get_diet(did)
    if not d:
        raise HTTPException(404, "Dieta non trovata")
    body = await request.json()
    selections = body.get("selections", {})
    comp = nutrition_engine.compute_diet(d["diet"], selections)
    return comp


@app.post("/api/diets/{did}/shopping-list")
async def api_shopping(did: int, request: Request):
    d = database.get_diet(did)
    if not d:
        raise HTTPException(404, "Dieta non trovata")
    body = await request.json()
    sl = nutrition_engine.build_shopping_list(d["diet"], body.get("selections", {}))
    return {"shopping": sl}


@app.post("/api/diets/{did}/summary")
async def api_summary(did: int, request: Request):
    d = database.get_diet(did)
    if not d:
        raise HTTPException(404, "Dieta non trovata")
    body = await request.json()
    cid = body.get("client_id")
    client = database.get_client(cid) if cid else None
    bia = database.list_bia(cid)[0]["data"] if (cid and database.list_bia(cid)) else None
    summ = nutrition_engine.weekly_summary(d["diet"], body.get("selections", {}), client, bia)
    return summ


@app.post("/api/diets/{did}/plan/save")
async def api_plan_save(did: int, request: Request):
    body = await request.json()
    pid = database.save_plan(body.get("client_id"), body.get("selections", {}),
                             diet_id=did, title=body.get("title", ""), week_start=body.get("week_start", ""))
    return {"plan_id": pid}


# ---------------- Recipes ----------------
@app.get("/api/recipes")
def api_recipes():
    return database.list_recipes()


@app.post("/api/recipes")
async def api_recipe_create(request: Request):
    body = await request.json()
    rid = database.add_recipe(
        title=body.get("title", "Ricetta"),
        description=body.get("description", ""),
        ingredients=body.get("ingredients", []),
        steps=body.get("steps", []),
        nutrients=body.get("nutrients", {}),
        author=body.get("author", "nutrizionista"),
    )
    return {"id": rid}


# ---------------- Export HTML piano cliente ----------------
@app.post("/api/diets/{did}/export-html")
async def api_export_html(did: int, request: Request):
    d = database.get_diet(did)
    if not d:
        raise HTTPException(404, "Dieta non trovata")
    body = await request.json()
    cid = body.get("client_id")
    client = database.get_client(cid) if cid else None
    bia = database.list_bia(cid)[0]["data"] if (cid and database.list_bia(cid)) else None
    html = build_plan_html(d["diet"], client, bia, body.get("selections", {}))
    out = os.path.join(UPLOAD_DIR, f"piano_{cid or did}_{_timestamp()}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    return FileResponse(out, media_type="text/html", filename=os.path.basename(out))


# ---------------- Helpers ----------------
def _today():
    return datetime.date.today().isoformat()


def _timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def build_plan_html(diet, client, bia, selections):
    """Genera HTML responsive del piano nutrizionale cliente."""
    comp = nutrition_engine.compute_diet(diet, selections)
    rows = []
    for day in comp["days"]:
        for meal in day["meals"]:
            opts_html = []
            for gi, grp in enumerate(meal["groups"]):
                for oi, o in enumerate(grp["options"]):
                    active = o.get("active")
                    opts_html.append(
                        f"<li class='{'active' if active else 'opt'}'>"
                        f"<b>{o['food']}</b> {o['grams']:.0f} g "
                        f"<span class='kcal'>{o['kcal']:.0f} kcal</span>"
                        f"{'' if o['matched'] else ' <span class=unmatched>?</span>'}"
                        f"{' ✓' if active else ''}</li>")
            rows.append(f"""
            <div class="meal">
              <h4>{day['day']} — {meal['meal']} <span class="mtot">{meal['totals']['kcal']:.0f} kcal</span></h4>
              <ul>{''.join(opts_html)}</ul>
            </div>""")
    client_html = ""
    if client:
        client_html = f"<p><b>Cliente:</b> {client.get('name')} &nbsp; <b>Obiettivo:</b> {client.get('goal')}</p>"
    bia_html = ""
    if bia:
        bia_html = "<p class='bia'>" + " &nbsp; ".join(f"{k}: {v}" for k, v in bia.items()) + "</p>"
    w = comp["week"]
    return f"""<!DOCTYPE html>
<html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Piano Nutrizionale — {client.get('name') if client else 'Cliente'}</title>
<style>
  *{{box-sizing:border-box}}
  body{{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;background:#f5f7fa;color:#1a2332}}
  .wrap{{max-width:900px;margin:auto;padding:24px}}
  h1{{color:#0d9488}}
  .kpi{{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}}
  .kpi div{{background:#fff;border-left:4px solid #0d9488;padding:10px 16px;border-radius:8px;flex:1;min-width:120px}}
  .kpi b{{display:block;font-size:1.4em;color:#0d9488}}
  .meal{{background:#fff;border-radius:10px;padding:12px 16px;margin:10px 0;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
  .meal h4{{margin:0 0 6px;color:#334155}}
  .mtot{{float:right;color:#f59e0b;font-weight:600}}
  ul{{margin:4px 0;padding-left:18px}}
  li{{margin:2px 0}}
  li.opt{{color:#64748b}}
  li.active{{color:#0f172a;font-weight:600}}
  .kcal{{color:#94a3b8;font-size:.85em}}
  .unmatched{{color:#ef4444}}
  .bia{{background:#fff7ed;padding:8px 12px;border-radius:8px;color:#9a3412;font-size:.9em}}
  @media(max-width:600px){{.kpi div{{min-width:45%}}}}
</style></head>
<body><div class="wrap">
  <h1>Piano Nutrizionale Settimanale</h1>
  {client_html}
  {bia_html}
  <div class="kpi">
    <div><b>{w['avg_day']['kcal']:.0f}</b>kcal/media giorno</div>
    <div><b>{w['avg_day']['p']:.0f} g</b>proteine</div>
    <div><b>{w['avg_day']['c']:.0f} g</b>carboidrati</div>
    <div><b>{w['avg_day']['f']:.0f} g</b>grassi</div>
    <div><b>{w['avg_day']['fib']:.0f} g</b>fibre</div>
  </div>
  {''.join(rows)}
  <p style="margin-top:24px;color:#94a3b8;font-size:.8em">Generato con NutriCoach — valori stimati da database alimenti di riferimento.</p>
</div></body></html>"""


# ---------------- Self-update (GitHub Releases) ----------------
_GITHUB_RELEASES_LATEST = "https://api.github.com/repos/quadrellif90-collab/NutriCoach/releases/latest"
_UPDATE_CACHE = {"ts": 0.0, "data": None}
_UPDATE_TTL = 6 * 3600  # 6h


def _parse_ver(v):
    v = (v or "").lstrip("vV").strip()
    try:
        return tuple(int(x) for x in v.split("."))
    except Exception:
        return (0,)


def _github_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "NutriCoach", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def get_update_info(force=False):
    """Controlla releases/latest e ritorna info aggiornamento (cache 6h)."""
    import time
    now = time.time()
    if not force and _UPDATE_CACHE["data"] and (now - _UPDATE_CACHE["ts"]) < _UPDATE_TTL:
        return _UPDATE_CACHE["data"]
    try:
        rel = _github_get(_GITHUB_RELEASES_LATEST)
    except Exception as e:
        return {"update_available": False, "error": str(e), "current": version.VERSION}
    tag = rel.get("tag_name", "")
    latest = tag.lstrip("vV")
    plat = sys.platform
    # scegli l'asset per piattaforma
    dl = None
    asset_name = None
    for a in rel.get("assets", []):
        n = a.get("name", "")
        if plat == "win32" and n.endswith(".exe") and "Setup" in n:
            dl = a.get("browser_download_url"); asset_name = n; break
        if plat == "darwin" and n.endswith(".dmg"):
            dl = a.get("browser_download_url"); asset_name = n; break
    # fallback: primo exe (Windows) / dmg (Mac) se non trovato quello "Setup"
    if dl is None:
        for a in rel.get("assets", []):
            n = a.get("name", "")
            if plat == "win32" and n.endswith(".exe"):
                dl = a.get("browser_download_url"); asset_name = n; break
            if plat == "darwin" and n.endswith(".dmg"):
                dl = a.get("browser_download_url"); asset_name = n; break
    info = {
        "update_available": _parse_ver(latest) > _parse_ver(version.VERSION),
        "current": version.VERSION,
        "latest": latest,
        "tag": tag,
        "html_url": rel.get("html_url", ""),
        "download_url": dl,
        "asset_name": asset_name,
        "platform": plat,
    }
    _UPDATE_CACHE["ts"] = now
    _UPDATE_CACHE["data"] = info
    return info


@app.get("/api/version")
def api_version():
    return {"version": version.VERSION, "platform": sys.platform}


@app.get("/api/self-update/check")
def api_self_update_check():
    return get_update_info(force=True)


@app.post("/api/self-update/apply")
def api_self_update_apply():
    """Scarica l'installer della release latest e lo lancia (silenzioso su Win).
    Ritorna prima di completare: l'app deve liberare i file (si chiude)."""
    info = get_update_info(force=True)
    dl = info.get("download_url")
    if not dl:
        return JSONResponse(status_code=400,
                            content={"ok": False, "error": "Nessun asset scaricabile per questa piattaforma"})
    plat = sys.platform
    try:
        td = tempfile.mkdtemp(prefix="nutricoach-update-")
        fname = info.get("asset_name") or ("NutriCoach-Setup.exe" if plat == "win32" else "NutriCoach.dmg")
        dest = os.path.join(td, fname)
        req = urllib.request.Request(dl, headers={"User-Agent": "NutriCoach"})
        with urllib.request.urlopen(req, timeout=300) as r:
            with open(dest, "wb") as f:
                f.write(r.read())
        if plat == "win32" and fname.lower().endswith(".exe"):
            subprocess.Popen([dest, "/S"], shell=False)
            return {"ok": True, "launched": True, "mode": "windows-installer",
                    "msg": "Installer avviato. L'app si chiudera' per aggiornarsi."}
        elif plat == "darwin" and fname.lower().endswith(".dmg"):
            subprocess.Popen(["open", dest])
            return {"ok": True, "launched": True, "mode": "macos-dmg",
                    "msg": "DMG aperta: trascina NutriCoach in Applicazioni per aggiornare."}
        else:
            import webbrowser
            webbrowser.open(info.get("html_url") or dl)
            return {"ok": True, "launched": True, "mode": "manual",
                    "msg": "Aperta la pagina della release."}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


# ─── Symptom Log (diario sintomi GI) ─────────────────────────────────
@app.post("/api/clients/{cid}/symptoms")
async def api_add_symptom(cid: int, request: Request):
    """Registra un evento sintomatologico per un cliente."""
    b = await request.json()
    sid = database.add_symptom(
        cid, b.get("date", ""), b.get("time"),
        b.get("bloating", 0), b.get("pain", 0), b.get("gas", 0),
        b.get("nausea", 0), b.get("heartburn", 0),
        b.get("constipation", 0), b.get("diarrhea", 0),
        b.get("brain_fog", 0), b.get("fatigue", 0),
        b.get("bristol_scale"), b.get("meal_context"),
        b.get("foods_eaten"), b.get("diet_compliance"), b.get("notes"))
    return {"id": sid, "ok": True}


@app.get("/api/clients/{cid}/symptoms")
def api_list_symptoms(cid: int, date_from: str = None, date_to: str = None, limit: int = 100):
    return {"symptoms": database.list_symptoms(cid, date_from, date_to, limit)}


@app.get("/api/clients/{cid}/symptoms/summary")
def api_symptom_summary(cid: int, days: int = 30):
    return database.symptom_summary(cid, days)


@app.delete("/api/symptoms/{sid}")
def api_delete_symptom(sid: int):
    database.delete_symptom(sid)
    return {"ok": True}


# ─── Supplement Log ──────────────────────────────────────────────────
@app.post("/api/clients/{cid}/supplements")
async def api_add_supplement(cid: int, request: Request):
    b = await request.json()
    sid = database.add_supplement(cid, b.get("date", ""), b["name"],
                           b.get("dose"), b.get("taken", 1), b.get("notes"))
    return {"id": sid, "ok": True}


@app.get("/api/clients/{cid}/supplements")
def api_list_supplements(cid: int, date_from: str = None):
    return {"supplements": database.list_supplements(cid, date_from)}


# ─── Diet Phase (eliminazione/reintroduzione/mantenimento) ──────────
@app.post("/api/clients/{cid}/diet-phase")
async def api_set_diet_phase(cid: int, request: Request):
    b = await request.json()
    database.set_diet_phase(cid, b["condition_key"], b["phase"],
                     b.get("start_date"), b.get("notes"))
    return {"ok": True}


@app.get("/api/clients/{cid}/diet-phases")
def api_get_diet_phases(cid: int):
    return {"phases": database.get_diet_phases(cid)}


# ─── Cartella Clinica unificata (aggrega tutto per cliente) ──────────
@app.get("/api/clients/{cid}/clinical-summary")
def api_clinical_summary(cid: int, days: int = 30):
    """Aggrega in un'unica risposta: condizioni, conflitti, esclusioni,
    integratori, fase dieta, sintomi (summary), trend peso, note progresso."""
    client = database.get_client(cid) or {}
    parsed = clinical_nutrition.parse_pathologies(client.get("pathologies"))
    conditions = parsed["conditions"]
    out = {
        "client_name": client.get("name", ""),
        "conditions": conditions,
        "conflicts": clinical_nutrition.get_condition_conflicts(conditions) if len(conditions) > 1 else [],
        "foods_to_avoid": clinical_nutrition.get_foods_to_avoid(conditions) if conditions else [],
        "foods_safe": clinical_nutrition.get_foods_safe(conditions) if conditions else [],
        "supplements": database.list_supplements(cid)[:30],
        "diet_phases": database.get_diet_phases(cid),
        "symptom_summary": database.symptom_summary(cid, days) if conditions else {},
        "measurements": database.list_measurements(cid)[-10:],
        "progress_notes": database.list_progress_notes(cid)[-10:],
    }
    # arricchisce con dettagli condizione
    out["condition_details"] = [
        {"key": k, "name": clinical_nutrition.get_condition(k).get("name", k),
         "evidence_level": clinical_nutrition.get_condition(k).get("evidence_level", "")}
        for k in conditions if clinical_nutrition.get_condition(k)
    ]
    return out


# ─── C: AI pattern detection dal diario + reintroduzione FODMAP guidata ──
@app.get("/api/clients/{cid}/symptom-patterns")
def api_symptom_patterns(cid: int, days: int = 30):
    """Rileva pattern dai log sintomi del cliente (loop chiuso piano→diario→piano)."""
    symptoms = database.list_symptoms(cid, limit=500)
    if days:
        from datetime import datetime, timedelta
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        symptoms = [s for s in symptoms if s.get("date", "") >= cutoff]
    return {"patterns": clinical_nutrition.detect_symptom_patterns(symptoms)}


@app.get("/api/clients/{cid}/fodmap-reintroduction")
def api_fodmap_reintroduction(cid: int):
    """Suggerisce il prossimo passo di reintroduzione FODMAP guidata (ordine Monash)."""
    phases = database.get_diet_phases(cid)
    symptoms = database.list_symptoms(cid, limit=200)
    return clinical_nutrition.suggest_next_reintroduction(phases, symptoms)


# ─── Clinical: conflitti multi-condizione + integratori + phased ────
@app.post("/api/clinical-nutrition/conflicts")
async def api_condition_conflicts(request: Request):
    """Ritorna avvisi di conflitto quando un cliente ha più condizioni."""
    b = await request.json()
    conditions = b.get("conditions", [])
    return {"conflicts": clinical_nutrition.get_condition_conflicts(conditions)}


@app.post("/api/clinical-nutrition/supplements")
async def api_condition_supplements(request: Request):
    """Ritorna gli integratori raccomandati per le condizioni del cliente."""
    b = await request.json()
    conditions = b.get("conditions", [])
    return {"supplements": clinical_nutrition.get_supplements(conditions)}


@app.get("/api/clinical-nutrition/phased/{condition_key}")
def api_phased_protocol(condition_key: str):
    """Ritorna il protocollo phased per una condizione."""
    protocol = clinical_nutrition.get_phased_protocol(condition_key)
    if not protocol:
        raise HTTPException(404, "Protocollo phased non disponibile per questa condizione")
    return {"condition": condition_key, "protocol": protocol}


# ─── Clinical: pattern dietetici evidence-based (Mediterranea, DASH, MIND...) ──
@app.get("/api/clinical-nutrition/diet-patterns")
def api_all_diet_patterns():
    """Ritorna l'elenco di tutti i pattern dietetici evidence-based."""
    return {"patterns": clinical_nutrition.get_all_diet_patterns()}


@app.get("/api/clinical-nutrition/diet-patterns/{pattern_key}")
def api_diet_pattern(pattern_key: str):
    """Ritorna il dettaglio completo di un pattern dietetico."""
    pattern = clinical_nutrition.get_diet_pattern(pattern_key)
    if not pattern:
        raise HTTPException(404, "Pattern dietetico non trovato")
    return {"key": pattern_key, "pattern": pattern}


@app.post("/api/clinical-nutrition/diet-patterns/suggest")
async def api_suggest_diet_patterns(request: Request):
    """Suggerisce i pattern dietetici rilevanti per le condizioni del cliente."""
    b = await request.json()
    conditions = b.get("conditions", [])
    return {"suggestions": clinical_nutrition.get_diet_patterns_for_conditions(conditions)}


# ─── FODMAP analysis ────────────────────────────────────────────────
@app.post("/api/clients/{cid}/fodmap-analysis")
async def api_fodmap_analysis(cid: int, request: Request):
    """Analisi del carico FODMAP del diario del cliente per un giorno."""
    b = await request.json()
    day = b.get("day", "")
    items = database.list_diet_items(cid, day)
    if not items:
        return {"fodmap_load": 0, "by_group": {}, "flagged_items": [], "message": "Nessun alimento per questo giorno"}
    food_items = [(it["food"], it["grams"]) for it in items]
    result = clinical_nutrition.calculate_fodmap_load(food_items)
    return result


@app.get("/api/clinical-nutrition/food-analysis/{food_name}")
def api_food_analysis(food_name: str):
    """Analisi completa di un alimento: FODMAP, istamina, ossalati, salicilati, lectine."""
    import nutrition_db as ndb
    key = ndb._norm(food_name)
    if not key:
        return {"found": False, "name": food_name}
    return {
        "found": True, "name": key,
        "fodmap": ndb.food_fodmap(key),
        "histamine": ndb.food_histamine_level(key),
        "oxalate": ndb.food_oxalate_level(key),
        "salicylate": ndb.food_salicylate_level(key),
        "lectin": ndb.food_lectin_level(key),
        "nutrition": ndb.nutrition_for(key, 100),
    }


# ================ NUOVI ENDPOINT 1.6 (Dietowin) ================

# --- Client delete + categoria ---
@app.delete("/api/clients/{cid}")
def api_client_delete(cid: int):
    if not database.delete_client(cid):
        raise HTTPException(status_code=404, detail="Client not found")
    return {"ok": True}


@app.get("/api/categories")
def api_categories():
    return database.list_categories()


@app.post("/api/categories")
def api_category_add(body: dict):
    cid = database.add_category(body.get("name",""), body.get("color","#6366f1"), body.get("description",""))
    return {"id": cid, "ok": True}


@app.delete("/api/categories/{cid}")
def api_category_delete(cid: int):
    database.delete_category(cid)
    return {"ok": True}


# --- Groups ---
@app.get("/api/groups")
def api_groups():
    return database.list_groups()


@app.post("/api/groups")
def api_group_add(body: dict):
    gid = database.add_group(body.get("name",""), body.get("description",""))
    return {"id": gid, "ok": True}


@app.delete("/api/groups/{gid}")
def api_group_delete(gid: int):
    database.delete_group(gid)
    return {"ok": True}


@app.post("/api/groups/{gid}/members")
def api_group_add_member(gid: int, body: dict):
    database.add_client_to_group(body["client_id"], gid)
    return {"ok": True}


@app.delete("/api/groups/{gid}/members/{cid}")
def api_group_remove_member(gid: int, cid: int):
    database.remove_client_from_group(cid, gid)
    return {"ok": True}


@app.get("/api/groups/{gid}/members")
def api_group_members(gid: int):
    return database.get_group_members(gid)


@app.get("/api/clients/{cid}/groups")
def api_client_groups(cid: int):
    return database.get_client_groups(cid)


# --- BIA Readings (nuovo strutturato) ---
@app.post("/api/clients/{cid}/bia-reading")
def api_bia_reading_add(cid: int, body: dict):
    bid = database.add_bia_reading(cid, body.get("date", _today()), pdf_path=body.get("pdf_path",""),
        pdf_name=body.get("pdf_name",""), weight_kg=body.get("weight_kg"),
        bf_pct=body.get("bf_pct"), mm_pct=body.get("mm_pct"), pha=body.get("pha"),
        bmr_kcal=body.get("bmr_kcal"), tbw_l=body.get("tbw_l"),
        bmi=body.get("bmi"), bf_kg=body.get("bf_kg"), ffm_kg=body.get("ffm_kg"),
        bcm_kg=body.get("bcm_kg"), smm_kg=body.get("smm_kg"),
        ecw_l=body.get("ecw_l"), icw_l=body.get("icw_l"), ecw_ratio=body.get("ecw_ratio"),
        visceral_fat_level=body.get("visceral_fat_level"),
        source=body.get("source","manual"), notes=body.get("notes"),
        raw_json=body.get("raw_json"))
    return {"id": bid, "ok": True}


@app.get("/api/clients/{cid}/bia-readings")
def api_bia_readings(cid: int):
    return database.list_bia_readings(cid)


@app.get("/api/bia-readings/{bid}")
def api_bia_reading_get(bid: int):
    r = database.get_bia_reading(bid)
    if not r:
        raise HTTPException(404, "BIA non trovata")
    return r


@app.delete("/api/bia-readings/{bid}")
def api_bia_reading_delete(bid: int):
    database.delete_bia_reading(bid)
    return {"ok": True}


@app.get("/api/clients/{cid}/bia-trend")
def api_bia_trend(cid: int, field: str = "weight_kg", days: int = 365):
    return database.get_bia_trend(cid, field, days)


@app.post("/api/clients/{cid}/bia-reading/upload")
async def api_bia_reading_upload(cid: int, file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, f"bia_{cid}_{_timestamp()}_{file.filename}")
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    parsed = bia_parser.parse_bia_pdf(path) if os.path.getsize(path) > 0 else {"scanned": True}
    fields = parsed.get("fields", {}) if not parsed.get("scanned") else {}
    bid = database.add_bia_reading(cid, _today(), pdf_path=path, pdf_name=file.filename,
        source="upload", weight_kg=fields.get("peso"),
        bf_pct=fields.get("fm"), bf_kg=fields.get("fat_kg"),
        mm_pct=fields.get("ffm"), pha=fields.get("pha"),
        bmi=fields.get("bmi"), tbw_l=fields.get("tbw"),
        bmr_kcal=fields.get("bmr"),
        raw_json=json.dumps(fields))
    return {"bia_id": bid, "parsed": fields, "pdf_path": path}


@app.get("/api/files/{filepath:path}")
def api_serve_file(filepath: str):
    full = os.path.join(UPLOAD_DIR, filepath)
    if not os.path.exists(full):
        raise HTTPException(404, "File non trovato")
    return FileResponse(full)


# --- Documents ---
@app.post("/api/documents")
async def api_doc_upload(cid: int = Form(None), title: str = Form(""), doc_type: str = Form("altro"),
                          file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, f"doc_{_timestamp()}_{file.filename}")
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    did = database.add_document(cid, title, doc_type, path, original_name=file.filename, date=_today())
    return {"id": did, "path": path}


@app.get("/api/documents")
def api_docs(cid: int = None, doc_type: str = None):
    return database.list_documents(cid, doc_type)


@app.delete("/api/documents/{did}")
def api_doc_delete(did: int):
    database.delete_document(did)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8090)
