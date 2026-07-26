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
               "goal","allergies","pathologies","preferences","notes"}
    f = {k: v for k, v in fields.items() if k in allowed}
    if not f:
        return
    conn = _ensure(); cur = conn.cursor()
    cur.execute("UPDATE clients SET " + ",".join(f"{k}=?" for k in f) + " WHERE id=?",
                tuple(f.values()) + (cid,))
    conn.commit(); conn.close()


def delete_client(cid):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("DELETE FROM clients WHERE id=?", (cid,))
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
def add_diet_item(cid, day, meal, food, grams, custom=0):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO diet_items (client_id,day,meal,food,grams,custom) VALUES (?,?,?,?,?,?)",
                (cid, day, meal, food, float(grams or 0), int(bool(custom))))
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
def add_appointment(client_id, title, note="", appt_date=None):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("INSERT INTO appointments (client_id,title,note,appt_date) VALUES (?,?,?,?)",
                (client_id, title, note, appt_date))
    aid = cur.lastrowid
    conn.commit(); conn.close(); return aid

def list_appointments(client_id=None, only_open=True):
    conn = _ensure(); cur = conn.cursor()
    q = "SELECT * FROM appointments"
    where = []; args = []
    if client_id is not None:
        where.append("client_id=?"); args.append(client_id)
    if only_open:
        where.append("done=0")
    if where:
        q += " WHERE " + " AND ".join(where)
    q += " ORDER BY appt_date IS NULL, appt_date ASC"
    cur.execute(q, args)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows

def set_appointment_done(aid, done=1):
    conn = _ensure(); cur = conn.cursor()
    cur.execute("UPDATE appointments SET done=? WHERE id=?", (done, aid))
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


if __name__ == "__main__":
    cid = add_client("Test Cliente", dob="1990-01-01", sex="M", goal="Dimagrimento")
    add_measurement(cid, "2026-07-01", weight_kg=75, height_cm=180, waist_cm=85)
    add_bia(cid, "2026-07-01", {"weight":75,"bodyFat":20,"phaseAngle":7.0}, source="manual")
    print("Client creato:", cid, "| DB:", DB_PATH)
