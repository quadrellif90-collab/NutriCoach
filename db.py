"""NutriCoach — Database clienti (SQLite, locale, nessun cloud).

Schema:
- clients: anagrafica + obiettivo
- measurements: misure antropometriche (peso, altezza, circonferenze, pieghe, ecc.)
- bia: bioimpedenziometria (storage storico, uno per data)
- diets: piano alimentare importato da PDF (JSON)
- recipes: ricette create dal nutrizionista
- plans: piano settimanale selezionato (con alternative scelte) per cliente

Tutto in un solo file DB nella data dir dell'app.
"""

import os
import sqlite3
import json
import datetime

DATA_DIR = os.path.join(os.path.expanduser("~"), ".nutricoach")
DB_PATH = os.path.join(DATA_DIR, "nutricoach.db")


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")  # attiva ON DELETE CASCADE
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        dob TEXT,
        age INTEGER,
        sex TEXT,
        height_cm REAL,
        activity TEXT DEFAULT 'moderato',
        athlete INTEGER DEFAULT 0,
        email TEXT,
        phone TEXT,
        goal TEXT,
        allergies TEXT,
        pathologies TEXT,
        preferences TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        weight_kg REAL,
        height_cm REAL,
        waist_cm REAL,
        hip_cm REAL,
        chest_cm REAL,
        arm_cm REAL,
        thigh_cm REAL,
        calf_cm REAL,
        skinfold_triceps REAL,
        skinfold_biceps REAL,
        skinfold_subscapular REAL,
        skinfold_suprailiac REAL,
        note TEXT,
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS bia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        data_json TEXT,
        source TEXT,
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS diets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        title TEXT,
        date TEXT,
        diet_json TEXT,
        source_file TEXT,
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        author TEXT DEFAULT 'nutrizionista',
        title TEXT NOT NULL,
        description TEXT,
        ingredients_json TEXT,
        steps_json TEXT,
        nutrients_json TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        diet_id INTEGER,
        title TEXT,
        week_start TEXT,
        selections_json TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        title TEXT NOT NULL,
        note TEXT,
        due_date TEXT,
        done INTEGER DEFAULT 0,
        channel TEXT DEFAULT 'app',
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS foods_custom (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        author TEXT DEFAULT 'nutrizionista',
        name TEXT NOT NULL,
        per_100g TEXT,   -- JSON dei nutrienti per 100g
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS diet_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        day TEXT,            -- lun/mar/... o data
        meal TEXT,           -- colazione/pranzo/...
        food TEXT,
        grams REAL,
        custom INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        direction TEXT,      -- 'nutri->client' | 'client->nutri'
        text TEXT,
        date TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        title TEXT,
        note TEXT,
        appt_date TEXT,
        done INTEGER DEFAULT 0,
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS water_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        ml INTEGER DEFAULT 0,
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS progress_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        text TEXT,
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    );
    """
    )
    # --- migrazione schema (column-add idempotente) ---
    existing = {r[1] for r in cur.execute("PRAGMA table_info(clients)").fetchall()}
    for col, ctype in [
        ("dob", "TEXT"), ("age", "INTEGER"), ("height_cm", "REAL"), ("activity", "TEXT DEFAULT 'moderato'"),
        ("athlete", "INTEGER DEFAULT 0"), ("allergies", "TEXT"), ("pathologies", "TEXT"),
        ("preferences", "TEXT"),
    ]:
        if col not in existing:
            try:
                cur.execute(f"ALTER TABLE clients ADD COLUMN {col} {ctype}")
            except Exception:
                pass
    existing_m = {r[1] for r in cur.execute("PRAGMA table_info(measurements)").fetchall()}
    for col in ["skinfold_biceps", "skinfold_subscapular"]:
        if col not in existing_m:
            try:
                cur.execute(f"ALTER TABLE measurements ADD COLUMN {col} REAL")
            except Exception:
                pass
    cur.execute("""CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        title TEXT NOT NULL,
        note TEXT,
        due_date TEXT,
        done INTEGER DEFAULT 0,
        channel TEXT DEFAULT 'app',
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    )""")
    # tabella prefs notifiche (per cliente)
    cur.execute("""CREATE TABLE IF NOT EXISTS notification_prefs (
        client_id INTEGER,
        type TEXT,
        enabled INTEGER DEFAULT 0,
        channel TEXT DEFAULT 'app',
        freq TEXT DEFAULT 'weekly',
        PRIMARY KEY(client_id, type),
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    )""")
    # coda invii notifiche
    cur.execute("""CREATE TABLE IF NOT EXISTS notification_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        type TEXT,
        channel TEXT DEFAULT 'app',
        due_date TEXT,
        status TEXT DEFAULT 'pending',
        note TEXT,
        sent_at TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    )""")
    # ── Diario sintomi GI (IBS, SIBO, IST, MCAS) ──────────────────────
    cur.execute("""CREATE TABLE IF NOT EXISTS symptom_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        time TEXT,
        -- Scala 0-4 (0=nessuno, 1=lieve, 2=moderato, 3=forte, 4=severo)
        bloating INTEGER DEFAULT 0,
        pain INTEGER DEFAULT 0,
        gas INTEGER DEFAULT 0,
        nausea INTEGER DEFAULT 0,
        heartburn INTEGER DEFAULT 0,
        constipation INTEGER DEFAULT 0,
        diarrhea INTEGER DEFAULT 0,
        brain_fog INTEGER DEFAULT 0,
        fatigue INTEGER DEFAULT 0,
        -- Bristol Stool Scale 1-7
        bristol_scale INTEGER,
        -- Correlazione pasto
        meal_context TEXT,       -- colazione/pranzo/cena/spuntino
        foods_eaten TEXT,        -- testo libero o JSON alimenti
        -- Compliance
        diet_compliance TEXT,    -- 'full'/'partial'/'none'
        -- Note aggiuntive
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    )""")
    # ── Log integratori ────────────────────────────────────────────────
    cur.execute("""CREATE TABLE IF NOT EXISTS supplement_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        supplement_name TEXT NOT NULL,
        dose TEXT,
        taken INTEGER DEFAULT 1,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    )""")
    # ── Fase dieta corrente (eliminazione/reintroduzione/mantenimento) ──
    cur.execute("""CREATE TABLE IF NOT EXISTS diet_phase (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        condition_key TEXT NOT NULL,
        phase TEXT NOT NULL DEFAULT 'elimination',
        start_date TEXT,
        notes TEXT,
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    )""")
    # ── Nuove tabelle 1.6 (Dietowin-style) ──
    cur.execute("""CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        color TEXT DEFAULT '#6366f1',
        description TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS groups_ (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS client_groups (
        client_id INTEGER NOT NULL,
        group_id INTEGER NOT NULL,
        PRIMARY KEY(client_id,group_id),
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE,
        FOREIGN KEY(group_id) REFERENCES groups_(id) ON DELETE CASCADE
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS bia_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        pdf_path TEXT,
        pdf_name TEXT,
        weight_kg REAL, height_cm REAL, bmi REAL,
        bf_pct REAL, bf_kg REAL, mm_pct REAL, mm_kg REAL, ffm_kg REAL,
        tbw_l REAL, tbw_pct REAL, ecw_l REAL, icw_l REAL, ecw_ratio REAL,
        pha REAL, bcm_kg REAL, smm_kg REAL, asmm_kg REAL,
        bmr_kcal REAL, visceral_fat_level REAL, metabolic_age REAL,
        segment_analysis TEXT,
        raw_json TEXT, source TEXT DEFAULT 'upload', notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        title TEXT,
        doc_type TEXT DEFAULT 'altro',
        file_path TEXT NOT NULL,
        original_name TEXT,
        date TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    )""")
    # migrazione: aggiungi category_id a clients
    cols = {r[1] for r in cur.execute("PRAGMA table_info(clients)")}
    if "category_id" not in cols:
        try:
            cur.execute("ALTER TABLE clients ADD COLUMN category_id INTEGER REFERENCES categories(id)")
        except:
            pass
    # migrazione: estendi appointments con status/follow_up/outcome
    appt_cols = {r[1] for r in cur.execute("PRAGMA table_info(appointments)")}
    for col, ctype in [("status","TEXT DEFAULT 'open'"),("follow_up","INTEGER DEFAULT 0"),("outcome","TEXT")]:
        if col not in appt_cols:
            try:
                cur.execute(f"ALTER TABLE appointments ADD COLUMN {col} {ctype}")
            except:
                pass
    conn.commit()
    return conn


# ---------------- Clients ----------------
def add_client(name, dob="", sex="", age=None, height_cm=None, activity="moderato",
               athlete=0, email="", phone="", goal="", allergies="", pathologies="",
               preferences="", notes=""):
    conn = _ensure()
    cur = conn.cursor()
    cur.execute("""INSERT INTO clients
        (name,dob,sex,age,height_cm,activity,athlete,email,phone,goal,allergies,pathologies,preferences,notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (name, dob, sex, age, height_cm, activity, athlete, email, phone, goal,
         allergies, pathologies, preferences, notes))
    cid = cur.lastrowid
    conn.commit(); conn.close()
    return cid


def list_clients():
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT * FROM clients ORDER BY name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows


def get_client(cid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT * FROM clients WHERE id=?", (cid,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_client(cid, **fields):
    allowed = {"name","dob","sex","age","height_cm","activity","athlete","email","phone",
               "goal","allergies","pathologies","preferences","notes","category_id"}
    f = {k: v for k, v in fields.items() if k in allowed}
    if not f:
        return
    conn = _ensure(); cur = conn.cursor()
    cur.execute("UPDATE clients SET " + ",".join(f"{k}=?" for k in f) + " WHERE id=?",
                tuple(f.values()) + (cid,))
    conn.commit(); conn.close()


# ---------------- Measurements ----------------
def add_measurement(cid, date, **vals):
    conn = _ensure(); cur = conn.cursor()
    cols = ["weight_kg","height_cm","waist_cm","hip_cm","chest_cm","arm_cm","thigh_cm","calf_cm",
            "skinfold_triceps","skinfold_biceps","skinfold_subscapular","skinfold_suprailiac","note"]
    keys = [c for c in cols if c in vals]
    if not keys:
        conn.close(); return None
    q = ",".join(["client_id","date"] + keys)
    ph = ",".join(["?"] * (len(keys) + 2))
    cur.execute(f"INSERT INTO measurements ({q}) VALUES ({ph})",
                (cid, date) + tuple(vals[k] for k in keys))
    mid = cur.lastrowid
    conn.commit(); conn.close()
    return mid


def list_measurements(cid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT * FROM measurements WHERE client_id=? ORDER BY date DESC", (cid,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows


def latest_measurement(cid):
    rows = list_measurements(cid)
    return rows[0] if rows else {}

def delete_measurement(mid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("DELETE FROM measurements WHERE id=?", (mid,))
    conn.commit(); conn.close()

def compute_anthropometry(cid):
    """Unisce profilo cliente + ultima misura e ritorna i calcoli antropometrici."""
    import anthropometry as ant
    c = get_client(cid)
    if not c:
        return None
    m = latest_measurement(cid)
    profile = {"sex": c.get("sex"), "age": c.get("age"), "height_cm": c.get("height_cm"),
               "activity": c.get("activity") or "moderato", "athlete": bool(c.get("athlete"))}
    skinfolds = {
        "tricipite": m.get("skinfold_triceps"),
        "bicipite": m.get("skinfold_biceps"),
        "sottoscapolare": m.get("skinfold_subscapular"),
        "sovrailiaca": m.get("skinfold_suprailiac"),
    }
    measurement = {"weight_kg": m.get("weight_kg"), "waist_cm": m.get("waist_cm"),
                   "hip_cm": m.get("hip_cm"), "skinfolds": skinfolds}
    res = ant.compute_all(profile, measurement)
    res["client"] = c
    res["measurement"] = m
    return res


# ---------------- BIA ----------------
def add_bia(cid, date, data_json, source=""):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO bia (client_id,date,data_json,source) VALUES (?,?,?,?)",
                (cid, date, json.dumps(data_json, ensure_ascii=False), source))
    bid = cur.lastrowid
    conn.commit(); conn.close()
    return bid


def list_bia(cid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT * FROM bia WHERE client_id=? ORDER BY date DESC", (cid,))
    rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        try: r["data"] = json.loads(r["data_json"])
        except (json.JSONDecodeError, ValueError): r["data"] = {}
    conn.close(); return rows


# ---------------- Diets ----------------
def add_diet(cid, diet_json, title="", date="", source_file=""):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO diets (client_id,title,date,diet_json,source_file) VALUES (?,?,?,?,?)",
                (cid, title, date, json.dumps(diet_json, ensure_ascii=False), source_file))
    did = cur.lastrowid
    conn.commit(); conn.close()
    return did


def list_diets(cid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT id,client_id,title,date,source_file FROM diets WHERE client_id=? ORDER BY date DESC", (cid,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows


def get_diet(did):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT * FROM diets WHERE id=?", (did,))
    row = cur.fetchone()
    if not row:
        conn.close(); return None
    d = dict(row)
    try: d["diet"] = json.loads(d["diet_json"])
    except (json.JSONDecodeError, ValueError): d["diet"] = {}
    conn.close(); return d


# ---------------- Recipes ----------------
def add_recipe(title, description="", ingredients=None, steps=None, nutrients=None, author="nutrizionista"):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO recipes (author,title,description,ingredients_json,steps_json,nutrients_json) VALUES (?,?,?,?,?,?)",
                (author, title, description, json.dumps(ingredients or [], ensure_ascii=False),
                 json.dumps(steps or [], ensure_ascii=False), json.dumps(nutrients or {}, ensure_ascii=False)))
    rid = cur.lastrowid
    conn.commit(); conn.close()
    return rid


def list_recipes():
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT id,title,description,author FROM recipes ORDER BY title")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows


def get_recipe(rid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT * FROM recipes WHERE id=?", (rid,))
    row = cur.fetchone()
    if not row:
        conn.close(); return None
    d = dict(row)
    for k in ("ingredients_json","steps_json","nutrients_json"):
        try: d[k[:-5]] = json.loads(d[k])
        except (json.JSONDecodeError, ValueError): d[k[:-5]] = {}
    conn.close(); return d


# ---------------- Reminders ----------------
def add_reminder(client_id, title, note="", due_date=None, channel="app"):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO reminders (client_id,title,note,due_date,channel) VALUES (?,?,?,?,?)",
                (client_id, title, note, due_date, channel))
    rid = cur.lastrowid
    conn.commit(); conn.close()
    return rid


def list_reminders(client_id=None, only_open=True):
    conn = _ensure(); cur = conn.cursor()
    q = "SELECT * FROM reminders"
    args = []
    where = []
    if client_id is not None:
        where.append("client_id=?")
        args.append(client_id)
    if only_open:
        where.append("done=0")
    if where:
        q += " WHERE " + " AND ".join(where)
    q += " ORDER BY due_date IS NULL, due_date ASC"
    cur.execute(q, args)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows


def set_reminder_done(rid, done=1):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("UPDATE reminders SET done=? WHERE id=?", (done, rid))
    conn.commit(); conn.close()


def delete_reminder(rid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("DELETE FROM reminders WHERE id=?", (rid,))
    conn.commit(); conn.close()


# ---------------- Confronto clienti ----------------
def compare_clients(ids):
    """Ritorna lista di snapshot (profilo + ultima antropometria) per confronto."""
    out = []
    for cid in ids:
        c = get_client(cid)
        if not c:
            continue
        anth = compute_anthropometry(cid) or {}
        m = anth.get("measurement", {})
        out.append({
            "id": cid,
            "name": c.get("name"),
            "sex": c.get("sex"),
            "age": c.get("age"),
            "goal": c.get("goal"),
            "weight_kg": m.get("weight_kg"),
            "bmi": anth.get("bmi"),
            "fat_pct": anth.get("fat_pct"),
            "tdee": anth.get("tdee"),
            "ffmi": anth.get("ffmi"),
            "whr": anth.get("whr"),
            "lean_mass_kg": anth.get("lean_mass_kg"),
            "protein_g": anth.get("protein_g"),
        })
    return out


# ---------------- Notifiche ----------------
def set_notification_prefs(cid, prefs):
    """prefs = [{'type','enabled','channel','freq'}, ...]."""
    conn = _ensure(); cur = conn.cursor()
    for p in prefs:
        cur.execute("""INSERT INTO notification_prefs (client_id,type,enabled,channel,freq)
            VALUES(?,?,?,?,?)
            ON CONFLICT(client_id,type) DO UPDATE SET
              enabled=excluded.enabled, channel=excluded.channel, freq=excluded.freq""",
            (cid, p["type"], int(bool(p.get("enabled"))), p.get("channel", "app"), p.get("freq", "weekly")))
    conn.commit(); conn.close()

def get_notification_prefs(cid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT type,enabled,channel,freq FROM notification_prefs WHERE client_id=?", (cid,))
    rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        r["enabled"] = bool(r["enabled"])
    conn.close(); return rows


def add_notification_log(cid, type_, channel, due_date=None, note=""):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO notification_log (client_id,type,channel,due_date,note) VALUES(?,?,?,?,?)",
                (cid, type_, channel, due_date, note))
    nid = cur.lastrowid
    conn.commit(); conn.close(); return nid


def list_notifications(cid=None, status="pending"):
    """status: 'pending' | 'sent' | 'all'."""
    conn = _ensure(); cur = conn.cursor()
    q = "SELECT * FROM notification_log"
    args = []; where = []
    if cid is not None:
        where.append("client_id=?")
        args.append(cid)
    if status != "all":
        where.append("status=?")
        args.append(status)
    if where:
        q += " WHERE " + " AND ".join(where)
    q += " ORDER BY created_at DESC"
    cur.execute(q, args)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows


def set_notification_sent(nid, sent=True):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("UPDATE notification_log SET status=?, sent_at=datetime('now') WHERE id=?",
                ("sent" if sent else "pending", nid))
    conn.commit(); conn.close()


# ---------------- Plans ----------------
def save_plan(cid, selections_json, diet_id=None, title="", week_start=""):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO plans (client_id,diet_id,title,week_start,selections_json) VALUES (?,?,?,?,?)",
                (cid, diet_id, title, week_start, json.dumps(selections_json, ensure_ascii=False)))
    pid = cur.lastrowid
    conn.commit(); conn.close()
    return pid


def list_plans(cid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT id,title,week_start,created_at FROM plans WHERE client_id=? ORDER BY created_at DESC", (cid,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows


# ---------------- Alimenti personalizzati ----------------
def add_custom_food(name, per_100g, author="nutrizionista"):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO foods_custom (author,name,per_100g) VALUES (?,?,?)",
                (author, name, json.dumps(per_100g, ensure_ascii=False)))
    fid = cur.lastrowid
    conn.commit(); conn.close(); return fid

def list_custom_foods():
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT id,name,per_100g FROM foods_custom ORDER BY name")
    rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        try: r["per_100g"] = json.loads(r["per_100g"])
        except (json.JSONDecodeError, ValueError): r["per_100g"] = {}
    conn.close(); return rows

def delete_custom_food(fid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("DELETE FROM foods_custom WHERE id=?", (fid,))
    conn.commit(); conn.close()


# ---------------- Diet builder (diario alimentare manuale) ----------------
def add_diet_item(cid, day, meal, food, grams, custom=0, alts=None):
    conn = _ensure(); cur = conn.cursor()
    # colonna alts (alternative per cibo, stile Dietowin) aggiunta in 1.7.0
    try:
        cur.execute("ALTER TABLE diet_items ADD COLUMN alts TEXT")
    except Exception:
        pass
    alts_json = json.dumps(alts, ensure_ascii=False) if alts else None
    cur.execute("INSERT INTO diet_items (client_id,day,meal,food,grams,custom,alts) VALUES (?,?,?,?,?,?,?)",
                (cid, day, meal, food, float(grams or 0), int(bool(custom)), alts_json))
    iid = cur.lastrowid
    conn.commit(); conn.close(); return iid

def list_diet_items(cid, day=None):
    conn = _ensure(); cur = conn.cursor()
    q = "SELECT * FROM diet_items WHERE client_id=?"
    args = [cid]
    if day:
        q += " AND day=?"
        args.append(day)
    q += " ORDER BY day, meal"
    cur.execute(q, args)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows

def delete_diet_item(iid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("DELETE FROM diet_items WHERE id=?", (iid,))
    conn.commit(); conn.close()


# ---------------- Messaggi (thread locale) ----------------
def add_message(cid, direction, text, date=None):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO messages (client_id,direction,text,date) VALUES (?,?,?,COALESCE(?,datetime('now')))",
                (cid, direction, text, date))
    mid = cur.lastrowid
    conn.commit(); conn.close(); return mid

def list_messages(cid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT * FROM messages WHERE client_id=? ORDER BY date ASC", (cid,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows


# ---------------- Appuntamenti ----------------
def add_appointment(client_id, title, note="", appt_date=None, status="open", follow_up=0):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO appointments (client_id,title,note,appt_date,status,follow_up) VALUES (?,?,?,?,?,?)",
                (client_id, title, note, appt_date, status, follow_up))
    aid = cur.lastrowid
    conn.commit(); conn.close(); return aid

def list_appointments(client_id=None, status_filter=None):
    conn = _ensure(); cur = conn.cursor()
    q = "SELECT a.*, c.name AS client_name FROM appointments a LEFT JOIN clients c ON a.client_id=c.id"
    where = []; args = []
    if client_id is not None:
        where.append("a.client_id=?"); args.append(client_id)
    if status_filter:
        if status_filter == "open":
            where.append("a.status='open'")
        elif status_filter == "closed":
            where.append("a.status='closed'")
        elif status_filter == "cancelled":
            where.append("a.status='cancelled'")
    if where:
        q += " WHERE " + " AND ".join(where)
    q += " ORDER BY a.appt_date IS NULL, a.appt_date ASC"
    cur.execute(q, args)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows

def update_appointment(aid, **kw):
    allowed = {"title","note","appt_date","status","follow_up","outcome"}
    f = {k:v for k,v in kw.items() if k in allowed and v is not None}
    if not f: return
    conn = _ensure(); cur = conn.cursor()
    q = "UPDATE appointments SET " + ",".join(f"{k}=?" for k in f) + " WHERE id=?"
    cur.execute(q, list(f.values()) + [aid])
    conn.commit(); conn.close()

def get_follow_ups():
    conn = _ensure(); cur = conn.cursor()
    cur.execute("""SELECT a.*, c.name AS client_name FROM appointments a 
        JOIN clients c ON a.client_id=c.id 
        WHERE a.follow_up=1 AND a.status='open' 
        ORDER BY a.appt_date ASC""")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows

def set_appointment_done(aid, done=1):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("UPDATE appointments SET status=? WHERE id=?", ("closed" if done else "open", aid))
    conn.commit(); conn.close()


# ---------------- Acqua ----------------
def add_water(cid, date, ml):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO water_log (client_id,date,ml) VALUES (?,?,?)", (cid, date, int(ml or 0)))
    wid = cur.lastrowid
    conn.commit(); conn.close(); return wid

def get_water(cid, date):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(ml),0) AS tot FROM water_log WHERE client_id=? AND date=?", (cid, date))
    row = cur.fetchone()
    conn.close(); return int(row["tot"]) if row else 0

def list_water(cid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT date, COALESCE(SUM(ml),0) AS ml FROM water_log WHERE client_id=? GROUP BY date ORDER BY date DESC", (cid,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows


# ---------------- Note di progresso ----------------
def add_progress_note(cid, date, text):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO progress_notes (client_id,date,text) VALUES (?,?,?)", (cid, date, text))
    nid = cur.lastrowid
    conn.commit(); conn.close(); return nid

def list_progress_notes(cid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT * FROM progress_notes WHERE client_id=? ORDER BY date DESC", (cid,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows


def delete_progress_note(nid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("DELETE FROM progress_notes WHERE id=?", (nid,))
    conn.commit(); conn.close()


# ---------------- Symptom Log (diario sintomi GI) ----------------
def add_symptom(cid, date, time=None, bloating=0, pain=0, gas=0, nausea=0,
                heartburn=0, constipation=0, diarrhea=0, brain_fog=0, fatigue=0,
                bristol_scale=None, meal_context=None, foods_eaten=None,
                diet_compliance=None, notes=None):
    """Registra un evento sintomatologico."""
    conn = _ensure(); cur = conn.cursor()
    cur.execute("""INSERT INTO symptom_log
        (client_id,date,time,bloating,pain,gas,nausea,heartburn,
         constipation,diarrhea,brain_fog,fatigue,bristol_scale,
         meal_context,foods_eaten,diet_compliance,notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (cid, date, time, bloating, pain, gas, nausea, heartburn,
         constipation, diarrhea, brain_fog, fatigue, bristol_scale,
         meal_context, foods_eaten, diet_compliance, notes))
    sid = cur.lastrowid
    conn.commit(); conn.close(); return sid


def list_symptoms(cid, date_from=None, date_to=None, limit=100):
    """Lista i log sintomi di un cliente, ordinate per data/ora."""
    conn = _ensure(); cur = conn.cursor()
    q = "SELECT * FROM symptom_log WHERE client_id=?"
    args = [cid]
    if date_from:
        q += " AND date>=?"; args.append(date_from)
    if date_to:
        q += " AND date<=?"; args.append(date_to)
    q += " ORDER BY date DESC, time DESC LIMIT ?"
    args.append(limit)
    cur.execute(q, args)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows


def symptom_summary(cid, days=30):
    """Riepilogo sintomi degli ultimi N giorni (medie per scala 0-4)."""
    conn = _ensure(); cur = conn.cursor()
    cur.execute("""SELECT
        ROUND(AVG(bloating),1) AS avg_bloating,
        ROUND(AVG(pain),1) AS avg_pain,
        ROUND(AVG(gas),1) AS avg_gas,
        ROUND(AVG(nausea),1) AS avg_nausea,
        ROUND(AVG(heartburn),1) AS avg_heartburn,
        ROUND(AVG(constipation),1) AS avg_constipation,
        ROUND(AVG(diarrhea),1) AS avg_diarrhea,
        ROUND(AVG(brain_fog),1) AS avg_brain_fog,
        ROUND(AVG(fatigue),1) AS avg_fatigue,
        ROUND(AVG(bristol_scale),1) AS avg_bristol,
        COUNT(*) AS total_entries
        FROM symptom_log
        WHERE client_id=? AND date >= date('now', ?)""",
        (cid, f'-{days} days'))
    row = cur.fetchone()
    conn.close(); return dict(row) if row else {}


def delete_symptom(sid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("DELETE FROM symptom_log WHERE id=?", (sid,))
    conn.commit(); conn.close()


# ---------------- Client CRUD (nuovo) ----------------
def delete_client(cid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT id FROM clients WHERE id=?", (cid,))
    if not cur.fetchone():
        conn.close()
        return 0
    cur.execute("DELETE FROM clients WHERE id=?", (cid,))
    n = cur.rowcount
    conn.commit(); conn.close()
    return n


def add_category(name, color="#6366f1", desc=""):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO categories (name,color,description) VALUES (?,?,?)",
                (name, color, desc))
    cid = cur.lastrowid
    conn.commit(); conn.close()
    return cid


def list_categories():
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT * FROM categories ORDER BY name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def delete_category(cid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("UPDATE clients SET category_id=NULL WHERE category_id=?", (cid,))
    cur.execute("DELETE FROM categories WHERE id=?", (cid,))
    conn.commit(); conn.close()


# ---------------- Groups ----------------
def add_group(name, desc=""):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO groups_ (name,description) VALUES (?,?)", (name, desc))
    gid = cur.lastrowid
    conn.commit(); conn.close()
    return gid


def list_groups():
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT g.*, (SELECT COUNT(*) FROM client_groups cg WHERE cg.group_id=g.id) AS member_count FROM groups_ g ORDER BY g.name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def delete_group(gid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("DELETE FROM client_groups WHERE group_id=?", (gid,))
    cur.execute("DELETE FROM groups_ WHERE id=?", (gid,))
    conn.commit(); conn.close()


def add_client_to_group(cid, gid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO client_groups (client_id,group_id) VALUES (?,?)", (cid, gid))
    conn.commit(); conn.close()


def remove_client_from_group(cid, gid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("DELETE FROM client_groups WHERE client_id=? AND group_id=?", (cid, gid))
    conn.commit(); conn.close()


def get_client_groups(cid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT g.* FROM groups_ g JOIN client_groups cg ON g.id=cg.group_id WHERE cg.client_id=? ORDER BY g.name", (cid,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_group_members(gid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT c.* FROM clients c JOIN client_groups cg ON c.id=cg.client_id WHERE cg.group_id=? ORDER BY c.name", (gid,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ---------------- BIA Readings (strutturato) ----------------
def add_bia_reading(cid, date, pdf_path="", pdf_name="", **kw):
    conn = _ensure(); cur = conn.cursor()
    fields = ["client_id","date","pdf_path","pdf_name",
              "weight_kg","height_cm","bmi",
              "bf_pct","bf_kg","mm_pct","mm_kg","ffm_kg",
              "tbw_l","tbw_pct","ecw_l","icw_l","ecw_ratio",
              "pha","bcm_kg","smm_kg","asmm_kg",
              "bmr_kcal","visceral_fat_level","metabolic_age",
              "segment_analysis","raw_json","source","notes"]
    vals = [cid, date, pdf_path, pdf_name]
    for f in fields[4:]:
        vals.append(kw.get(f))
    ph = ",".join(["?"]*len(fields))
    q = f"INSERT INTO bia_readings ({','.join(fields)}) VALUES ({ph})"
    cur.execute(q, vals)
    bid = cur.lastrowid
    conn.commit(); conn.close()
    return bid


def list_bia_readings(cid, limit=50):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT * FROM bia_readings WHERE client_id=? ORDER BY date DESC LIMIT ?", (cid, limit))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_bia_reading(bid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT * FROM bia_readings WHERE id=?", (bid,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_bia_reading(bid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT pdf_path FROM bia_readings WHERE id=?", (bid,))
    row = cur.fetchone()
    pdf_path = row["pdf_path"] if row else None
    cur.execute("DELETE FROM bia_readings WHERE id=?", (bid,))
    conn.commit(); conn.close()
    if pdf_path and os.path.exists(pdf_path):
        try: os.remove(pdf_path)
        except: pass


def get_bia_trend(cid, field="weight_kg", days=365):
    conn = _ensure(); cur = conn.cursor()
    cur.execute(f"SELECT date, {field} FROM bia_readings WHERE client_id=? AND date>=date('now',?) AND {field} IS NOT NULL ORDER BY date",
                (cid, f'-{days} days'))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ---------------- Documents ----------------
def add_document(cid, title, doc_type, file_path, original_name="", date="", notes=""):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO documents (client_id,title,doc_type,file_path,original_name,date,notes) VALUES (?,?,?,?,?,?,?)",
                (cid, title, doc_type, file_path, original_name, date, notes))
    did = cur.lastrowid
    conn.commit(); conn.close()
    return did


def list_documents(cid=None, doc_type=None):
    conn = _ensure(); cur = conn.cursor()
    q = "SELECT d.*, c.name AS client_name FROM documents d LEFT JOIN clients c ON d.client_id=c.id"
    params = []
    wheres = []
    if cid is not None:
        wheres.append("d.client_id=?")
        params.append(cid)
    if doc_type:
        wheres.append("d.doc_type=?")
        params.append(doc_type)
    if wheres:
        q += " WHERE " + " AND ".join(wheres)
    q += " ORDER BY d.created_at DESC"
    cur.execute(q, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def delete_document(did):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT file_path FROM documents WHERE id=?", (did,))
    row = cur.fetchone()
    fp = row["file_path"] if row else None
    cur.execute("DELETE FROM documents WHERE id=?", (did,))
    conn.commit(); conn.close()
    if fp and os.path.exists(fp):
        try: os.remove(fp)
        except: pass


# ---------------- Supplement Log ----------------
def add_supplement(cid, date, name, dose=None, taken=1, notes=None):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO supplement_log (client_id,date,supplement_name,dose,taken,notes) VALUES (?,?,?,?,?,?)",
                (cid, date, name, dose, taken, notes))
    sid = cur.lastrowid
    conn.commit(); conn.close(); return sid


def list_supplements(cid, date_from=None, limit=100):
    conn = _ensure(); cur = conn.cursor()
    q = "SELECT * FROM supplement_log WHERE client_id=?"
    args = [cid]
    if date_from:
        q += " AND date>=?"; args.append(date_from)
    q += " ORDER BY date DESC LIMIT ?"
    args.append(limit)
    cur.execute(q, args)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows


# ---------------- Diet Phase ----------------
def set_diet_phase(cid, condition_key, phase, start_date=None, notes=None):
    """Impiazza la fase corrente di una dieta clinica per un cliente."""
    conn = _ensure(); cur = conn.cursor()
    # upsert: se esiste già per quella condizione, aggiorna
    cur.execute("SELECT id FROM diet_phase WHERE client_id=? AND condition_key=?",
                (cid, condition_key))
    existing = cur.fetchone()
    if existing:
        cur.execute("UPDATE diet_phase SET phase=?, start_date=COALESCE(?,start_date), notes=COALESCE(?,notes) WHERE id=?",
                    (phase, start_date, notes, existing["id"]))
    else:
        cur.execute("INSERT INTO diet_phase (client_id,condition_key,phase,start_date,notes) VALUES (?,?,?,?,?)",
                    (cid, condition_key, phase, start_date, notes))
    conn.commit(); conn.close()


def get_diet_phases(cid):
    """Ritorna tutte le fasi dieta attive per un cliente."""
    conn = _ensure(); cur = conn.cursor()
    cur.execute("SELECT * FROM diet_phase WHERE client_id=?", (cid,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows


if __name__ == "__main__":
    cid = add_client("Test Cliente", dob="1990-01-01", sex="M", goal="Dimagrimento")
    add_measurement(cid, "2026-07-01", weight_kg=75, height_cm=180, waist_cm=85)
    add_bia(cid, "2026-07-01", {"weight":75,"bodyFat":20,"phaseAngle":7.0}, source="manual")
    print("Client creato:", cid, "| DB:", DB_PATH)
