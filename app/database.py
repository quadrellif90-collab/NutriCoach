"""
NutriCoach v2 — Database schema Dietowin-style.
Single source of truth per tutte le tabelle e le operazioni CRUD.
"""
import sqlite3, os, json, datetime as dt

DATA_DIR = os.path.join(os.path.expanduser("~"), ".nutricoach")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.environ.get("NUTRICOACH_DB") or os.path.join(DATA_DIR, "nutricoach.db")

def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con

def init_db():
    con = get_db()
    cur = con.cursor()
    # Droppa tabelle v1 (vecchia app) che hanno colonne diverse:
    # client_id -> patient_id, ecc.
    for old in ("clients","groups","diet","diet_presets"):
        cur.execute(f"DROP TABLE IF EXISTS {old}")
    # Per le tabelle condivise, verifica colonna patient_id; se manca droppa
    v2_tables = ["bia_readings","measurements","diet_plans","diet_items",
                 "appointments","notifications","documents","symptoms","progress_notes"]
    for tbl in v2_tables:
        try:
            cur.execute(f"SELECT patient_id FROM {tbl} LIMIT 1")
        except Exception:
            cur.execute(f"DROP TABLE IF EXISTS {tbl}")
    # Ora crea tutte le tabelle v2 da zero
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sex TEXT DEFAULT 'M',
            birth_date TEXT,
            phone TEXT,
            email TEXT,
            goal TEXT DEFAULT '',
            sport TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            allergies TEXT DEFAULT '',
            language TEXT DEFAULT 'it',
            pathologies TEXT DEFAULT '{}',
            category_id INTEGER,
            created TEXT DEFAULT (date('now')),
            updated TEXT DEFAULT (date('now'))
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            color TEXT DEFAULT '#6366f1'
        );
        CREATE TABLE IF NOT EXISTS groups_t (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS patient_groups (
            patient_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            PRIMARY KEY (patient_id, group_id),
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (group_id) REFERENCES groups_t(id)
        );
        CREATE TABLE IF NOT EXISTS bia_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            date TEXT NOT NULL DEFAULT (date('now')),
            source TEXT DEFAULT 'manual',
            weight_kg REAL, height_cm REAL, bmi REAL,
            bf_pct REAL, bf_kg REAL,
            mm_pct REAL, mm_kg REAL,
            ffm_kg REAL,
            tbw_l REAL, ecw_l REAL, icw_l REAL,
            pha REAL, bmr_kcal REAL,
            smm_kg REAL, asmm_kg REAL, bcm_kg REAL,
            visceral_fat_level REAL,
            protein_kg REAL, mineral_kg REAL,
            fmi REAL, ffmi REAL,
            hydration_pct REAL,
            notes TEXT DEFAULT '',
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            date TEXT NOT NULL DEFAULT (date('now')),
            weight_kg REAL, height_cm REAL,
            waist_cm REAL, hip_cm REAL,
            arm_cm REAL, thigh_cm REAL, calf_cm REAL,
            chest_cm REAL,
            notes TEXT DEFAULT '',
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        CREATE TABLE IF NOT EXISTS diet_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            title TEXT DEFAULT '',
            date TEXT NOT NULL DEFAULT (date('now')),
            preset TEXT DEFAULT '',
            conditions TEXT DEFAULT '[]',
            kcal_target INTEGER DEFAULT 0,
            p_target INTEGER DEFAULT 0,
            c_target INTEGER DEFAULT 0,
            f_target INTEGER DEFAULT 0,
            plan_json TEXT DEFAULT '{}',
            created TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        CREATE TABLE IF NOT EXISTS diet_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            plan_id INTEGER,
            date TEXT NOT NULL DEFAULT (date('now')),
            day TEXT NOT NULL,
            meal TEXT NOT NULL,
            food TEXT NOT NULL,
            grams REAL DEFAULT 100,
            alternative TEXT DEFAULT '',
            food_id INTEGER DEFAULT NULL,
            kcal REAL DEFAULT NULL,
            protein_g REAL DEFAULT NULL,
            carbs_g REAL DEFAULT NULL,
            fat_g REAL DEFAULT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            appt_date TEXT NOT NULL,
            appt_time TEXT DEFAULT '',
            status TEXT DEFAULT 'open',
            follow_up INTEGER DEFAULT 0,
            outcome TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            type TEXT DEFAULT 'email',
            subject TEXT DEFAULT '',
            message TEXT DEFAULT '',
            sent INTEGER DEFAULT 0,
            sent_date TEXT,
            bulk_id TEXT,
            created TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            title TEXT DEFAULT '',
            doc_type TEXT DEFAULT '',
            file_path TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            date TEXT NOT NULL DEFAULT (date('now')),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        CREATE TABLE IF NOT EXISTS symptoms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            date TEXT NOT NULL DEFAULT (date('now')),
            time TEXT DEFAULT '',
            bloating INTEGER DEFAULT 0,
            pain INTEGER DEFAULT 0,
            gas INTEGER DEFAULT 0,
            nausea INTEGER DEFAULT 0,
            heartburn INTEGER DEFAULT 0,
            constipation INTEGER DEFAULT 0,
            diarrhea INTEGER DEFAULT 0,
            bristol INTEGER DEFAULT 0,
            urgency INTEGER DEFAULT 0,
            incomplete INTEGER DEFAULT 0,
            foods TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        CREATE TABLE IF NOT EXISTS progress_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            date TEXT NOT NULL DEFAULT (date('now')),
            note TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        CREATE TABLE IF NOT EXISTS food_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT DEFAULT '',
            kcal REAL DEFAULT 0,
            protein_g REAL DEFAULT 0,
            carbs_g REAL DEFAULT 0,
            fat_g REAL DEFAULT 0,
            fiber_g REAL DEFAULT 0,
            sugar_g REAL DEFAULT 0,
            salt_g REAL DEFAULT 0
        );
    """)
    con.commit()
    seed_food_catalog()
    return con

# ─── HELPER ──────────────────────────────────────────────────────────────

def row_to_dict(row):
    if row is None:
        return None
    return dict(row)

def rows_to_list(rows):
    return [dict(r) for r in rows]

# ─── PATIENTS ─────────────────────────────────────────────────────────────

def add_patient(name, sex="M", phone="", email="", goal="", sport="", notes="", allergies="", category_id=None):
    con = get_db()
    cur = con.execute("INSERT INTO patients (name,sex,phone,email,goal,sport,notes,allergies,category_id) VALUES (?,?,?,?,?,?,?,?,?)",
                      (name, sex, phone, email, goal, sport, notes, allergies, category_id))
    con.commit()
    return cur.lastrowid

def update_patient(pid, **kw):
    if not kw:
        return
    sets = ", ".join(f"{k}=?" for k in kw)
    vals = list(kw.values()) + [pid]
    con = get_db()
    con.execute(f"UPDATE patients SET {sets}, updated=date('now') WHERE id=?", vals)
    con.commit()

def get_patient(pid):
    con = get_db()
    r = con.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
    return row_to_dict(r)

def list_patients(category_id=None):
    con = get_db()
    q = "SELECT * FROM patients"
    p = []
    if category_id:
        q += " WHERE category_id=?"
        p = [category_id]
    q += " ORDER BY name"
    return rows_to_list(con.execute(q, p).fetchall())

def delete_patient(pid):
    con = get_db()
    for t in ["diet_items","diet_plans","bia_readings","measurements","appointments","notifications","documents","symptoms","progress_notes","patient_groups"]:
        con.execute(f"DELETE FROM {t} WHERE patient_id=?", (pid,))
    con.execute("DELETE FROM patients WHERE id=?", (pid,))
    con.commit()

# ─── CATEGORIES ────────────────────────────────────────────────────────────

def add_category(name, color):
    con = get_db()
    con.execute("INSERT INTO categories (name,color) VALUES (?,?)", (name, color))
    con.commit()
    return con.execute("SELECT last_insert_rowid()").fetchone()[0]

def list_categories():
    return rows_to_list(get_db().execute("SELECT * FROM categories ORDER BY name").fetchall())

def delete_category(cid):
    get_db().execute("DELETE FROM categories WHERE id=?", (cid,)).connection.commit()

# ─── BIA ──────────────────────────────────────────────────────────────────

def add_bia(pid, fields, date=None, source="manual"):
    con = get_db()
    date = date or dt.date.today().isoformat()
    cols = ["patient_id","date","source"]
    vals = [pid, date, source]
    for k in ("weight_kg","height_cm","bmi","bf_pct","bf_kg","mm_pct","mm_kg","ffm_kg",
              "tbw_l","ecw_l","icw_l","pha","bmr_kcal","smm_kg","asmm_kg","bcm_kg",
              "visceral_fat_level","protein_kg","mineral_kg","fmi","ffmi","hydration_pct"):
        if k in fields:
            cols.append(k); vals.append(fields[k])
    ph = ",".join("?" for _ in vals)
    con.execute(f"INSERT INTO bia_readings ({','.join(cols)}) VALUES ({ph})", vals)
    con.commit()
    return con.execute("SELECT last_insert_rowid()").fetchone()[0]

def list_bia(pid, limit=50):
    return rows_to_list(get_db().execute(
        "SELECT * FROM bia_readings WHERE patient_id=? ORDER BY date DESC LIMIT ?", (pid, limit)).fetchall())

def delete_bia(bid):
    get_db().execute("DELETE FROM bia_readings WHERE id=?", (bid,)).connection.commit()

def bia_trend(pid, field="weight_kg", days=365):
    con = get_db()
    return rows_to_list(con.execute(
        f"SELECT date,{field} FROM bia_readings WHERE patient_id=? AND date>=date('now','-{days} days') ORDER BY date", (pid,)).fetchall())

# ─── DIET ─────────────────────────────────────────────────────────────────

def add_diet_plan(pid, title, preset, conditions, kcal, p, c, f, plan_json):
    con = get_db()
    con.execute("INSERT INTO diet_plans (patient_id,title,preset,conditions,kcal_target,p_target,c_target,f_target,plan_json) VALUES (?,?,?,?,?,?,?,?,?)",
                (pid, title, preset, json.dumps(conditions), kcal, p, c, f, json.dumps(plan_json)))
    con.commit()
    return con.execute("SELECT last_insert_rowid()").fetchone()[0]

def list_diet_plans(pid):
    return rows_to_list(get_db().execute("SELECT id,title,date,preset,kcal_target FROM diet_plans WHERE patient_id=? ORDER BY date DESC", (pid,)).fetchall())


def get_latest_diet_plan(pid):
    """Ritorna il piano alimentare più recente con tutti i dati (kcal, p, c, f)."""
    row = get_db().execute("SELECT * FROM diet_plans WHERE patient_id=? ORDER BY date DESC LIMIT 1", (pid,)).fetchone()
    return row_to_dict(row) if row else None


def add_diet_item(pid, plan_id, day, meal, food, grams=100, alternative="", food_id=None, kcal=None, protein_g=None, carbs_g=None, fat_g=None):
    con = get_db()
    date = dt.date.today().isoformat()
    con.execute("INSERT INTO diet_items (patient_id,plan_id,date,day,meal,food,grams,alternative,food_id,kcal,protein_g,carbs_g,fat_g) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (pid, plan_id, date, day, meal, food, grams, alternative, food_id, kcal, protein_g, carbs_g, fat_g))
    con.commit()
    return con.execute("SELECT last_insert_rowid()").fetchone()[0]

def list_diet_items(pid, day=None):
    con = get_db()
    if day:
        return rows_to_list(con.execute("SELECT * FROM diet_items WHERE patient_id=? AND day=? ORDER BY meal", (pid, day)).fetchall())
    return rows_to_list(con.execute("SELECT * FROM diet_items WHERE patient_id=? ORDER BY day,meal", (pid,)).fetchall())

def delete_diet_item(iid):
    get_db().execute("DELETE FROM diet_items WHERE id=?", (iid,)).connection.commit()

def clear_diet_items(pid):
    get_db().execute("DELETE FROM diet_items WHERE patient_id=?", (pid,)).connection.commit()

# ─── APPOINTMENTS ─────────────────────────────────────────────────────────

def add_appointment(pid, title, appt_date, appt_time="", status="open", follow_up=0, outcome="", notes=""):
    con = get_db()
    con.execute("INSERT INTO appointments (patient_id,title,appt_date,appt_time,status,follow_up,outcome,notes) VALUES (?,?,?,?,?,?,?,?)",
                (pid, title, appt_date, appt_time, status, follow_up, outcome, notes))
    con.commit()
    return con.execute("SELECT last_insert_rowid()").fetchone()[0]

def list_appointments(pid=None, date_from=None):
    con = get_db()
    q = "SELECT a.*, p.name as patient_name FROM appointments a JOIN patients p ON a.patient_id=p.id"
    params = []
    wheres = []
    if pid:
        wheres.append("a.patient_id=?"); params.append(pid)
    if date_from:
        wheres.append("a.appt_date>=?"); params.append(date_from)
    if wheres:
        q += " WHERE " + " AND ".join(wheres)
    q += " ORDER BY a.appt_date DESC"
    return rows_to_list(con.execute(q, params).fetchall())

# ─── NOTIFICATIONS ────────────────────────────────────────────────────────

def add_notification(pid, type, subject, message, bulk_id=None):
    con = get_db()
    con.execute("INSERT INTO notifications (patient_id,type,subject,message,bulk_id) VALUES (?,?,?,?,?)",
                (pid, type, subject, message, bulk_id))
    con.commit()
    return con.execute("SELECT last_insert_rowid()").fetchone()[0]

def list_notifications(pid=None, pending=False):
    con = get_db()
    q = "SELECT n.*, p.name as patient_name FROM notifications n JOIN patients p ON n.patient_id=p.id"
    params = []
    wheres = []
    if pid:
        wheres.append("n.patient_id=?"); params.append(pid)
    if pending:
        wheres.append("n.sent=0")
    if wheres:
        q += " WHERE " + " AND ".join(wheres)
    q += " ORDER BY n.created DESC"
    return rows_to_list(con.execute(q, params).fetchall())

def mark_sent(nid):
    get_db().execute("UPDATE notifications SET sent=1, sent_date=date('now') WHERE id=?", (nid,)).connection.commit()

# ─── DOCUMENTS ────────────────────────────────────────────────────────────

def add_document(pid, title, doc_type, file_path):
    con = get_db()
    con.execute("INSERT INTO documents (patient_id,title,doc_type,file_path) VALUES (?,?,?,?)",
                (pid, title, doc_type, file_path))
    con.commit()
    return con.execute("SELECT last_insert_rowid()").fetchone()[0]

def list_documents(pid=None):
    con = get_db()
    if pid:
        return rows_to_list(con.execute("SELECT * FROM documents WHERE patient_id=? ORDER BY date DESC", (pid,)).fetchall())
    return rows_to_list(con.execute("SELECT d.*, p.name as patient_name FROM documents d JOIN patients p ON d.patient_id=p.id ORDER BY d.date DESC").fetchall())

# ─── SYMPTOMS ─────────────────────────────────────────────────────────────

def add_symptom(pid, date, time, **kw):
    fields = ["patient_id","date","time"]
    vals = [pid, date, time]
    for k in ("bloating","pain","gas","nausea","heartburn","constipation","diarrhea","bristol","urgency","incomplete","foods","notes"):
        if k in kw:
            fields.append(k); vals.append(kw[k])
    ph = ",".join("?" for _ in vals)
    get_db().execute(f"INSERT INTO symptoms ({','.join(fields)}) VALUES ({ph})", vals).connection.commit()
    return get_db().execute("SELECT last_insert_rowid()").fetchone()[0]

def list_symptoms(pid, limit=50):
    return rows_to_list(get_db().execute("SELECT * FROM symptoms WHERE patient_id=? ORDER BY date DESC LIMIT ?", (pid, limit)).fetchall())

# ─── PROGRESS NOTES ──────────────────────────────────────────────────────

def add_progress_note(pid, note, date=None):
    date = date or dt.date.today().isoformat()
    get_db().execute("INSERT INTO progress_notes (patient_id,date,note) VALUES (?,?,?)", (pid, date, note)).connection.commit()
    return get_db().execute("SELECT last_insert_rowid()").fetchone()[0]

def list_progress_notes(pid):
    return rows_to_list(get_db().execute("SELECT * FROM progress_notes WHERE patient_id=? ORDER BY date DESC", (pid,)).fetchall())

def delete_progress_note(nid):
    get_db().execute("DELETE FROM progress_notes WHERE id=?", (nid,)).connection.commit()

# ─── PATIENT COMPARE ──────────────────────────────────────────────────────

def compare_patients(ids):
    """Ritorna snapshot antropometrico per confronto multiplo pazienti."""
    results = []
    for pid in ids:
        comp = get_body_composition_data(pid)
        if comp:
            results.append(comp)
    return results


def get_body_composition_data(pid):
    """Ritorna BMI, FFMI, FMI, WHR, BF%, MM%, PhA per un paziente."""
    p = get_patient(pid)
    if not p:
        return None
    con = get_db()
    bia = con.execute("SELECT * FROM bia_readings WHERE patient_id=? ORDER BY date DESC LIMIT 1", (pid,)).fetchone()
    meas = con.execute("SELECT * FROM measurements WHERE patient_id=? ORDER BY date DESC LIMIT 1", (pid,)).fetchone()
    bia_d = row_to_dict(bia) or {}
    meas_d = row_to_dict(meas) or {}
    weight = bia_d.get("weight_kg") or meas_d.get("weight_kg") or p.get("weight_kg")
    height = bia_d.get("height_cm") or meas_d.get("height_cm")
    bf = bia_d.get("bf_pct")
    mm = bia_d.get("mm_pct")
    pha = bia_d.get("pha")
    tbw = bia_d.get("tbw_l")
    bmr = bia_d.get("bmr_kcal")
    bmi = round(weight / ((height/100)**2), 1) if weight and height else None
    ffmi = round((weight * (1 - (bf or 0)/100)) / ((height/100)**2), 1) if weight and height and bf is not None else None
    fmi = round((weight * ((bf or 0)/100)) / ((height/100)**2), 1) if weight and height and bf is not None else None
    whr = round(meas_d.get("waist_cm",0) / meas_d.get("hip_cm",1), 2) if meas_d.get("waist_cm") and meas_d.get("hip_cm") else None
    return {
        "id": pid, "name": p.get("name"), "sex": p.get("sex"),
        "weight_kg": weight, "height_cm": height, "bmi": bmi,
        "bf_pct": bf, "mm_pct": mm, "pha": pha,
        "tbw_l": tbw, "bmr_kcal": bmr,
        "ffmi": ffmi, "fmi": fmi, "whr": whr,
    }


# ─── FOOD CATALOG ─────────────────────────────────────

def seed_food_catalog():
    """Popola food_catalog da nutrition_db se vuoto."""
    con = get_db()
    # Migrazioni per DB preesistente (v2.2.0+)
    for tbl, cols in [
        ("food_catalog", ["id INTEGER PRIMARY KEY AUTOINCREMENT", "name TEXT NOT NULL UNIQUE",
                          "category TEXT DEFAULT ''", "kcal REAL DEFAULT 0", "protein_g REAL DEFAULT 0",
                          "carbs_g REAL DEFAULT 0", "fat_g REAL DEFAULT 0", "fiber_g REAL DEFAULT 0",
                          "sugar_g REAL DEFAULT 0", "salt_g REAL DEFAULT 0"]),
    ]:
        con.execute(f"CREATE TABLE IF NOT EXISTS {tbl} ({','.join(cols)})")
    # Crea diet_templates
    con.execute("""CREATE TABLE IF NOT EXISTS diet_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        targets TEXT DEFAULT '{}',
        owner_id INTEGER DEFAULT NULL
    )""")
    # Crea recipes
    con.execute("""CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ingredients TEXT DEFAULT '[]',
        instructions TEXT DEFAULT '',
        servings INTEGER DEFAULT 4,
        category TEXT DEFAULT '',
        macros TEXT DEFAULT '{}'
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS drug_interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drug TEXT NOT NULL,
        category TEXT DEFAULT '',
        effect TEXT DEFAULT '',
        recommendation TEXT DEFAULT '',
        severity TEXT DEFAULT 'media'
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS questionnaire_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        questionnaire TEXT NOT NULL,
        score REAL DEFAULT 0,
        answers TEXT DEFAULT '[]',
        date TEXT NOT NULL DEFAULT (date('now')),
        notes TEXT DEFAULT '',
        FOREIGN KEY (patient_id) REFERENCES patients(id)
            )""")
    con.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'nutritionist',
        clinic_name TEXT DEFAULT '',
        logo_url TEXT DEFAULT '',
        theme_color TEXT DEFAULT '#6366f1',
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""")
    # Migra colonne patients
    for col in ["portal_token TEXT DEFAULT NULL", "birth_date TEXT DEFAULT NULL", "language TEXT DEFAULT 'it'", "user_id INTEGER DEFAULT 1"]:
        try:
            con.execute(f"ALTER TABLE patients ADD COLUMN {col}")
        except Exception:
            pass
    con.commit()
    cnt = con.execute("SELECT COUNT(*) FROM food_catalog").fetchone()[0]
    if cnt > 0:
        return cnt  # già popolato
    try:
        import sys as _sys
        _nutri_root = os.path.dirname(os.path.dirname(__file__))
        if _nutri_root not in _sys.path:
            _sys.path.insert(0, _nutri_root)
        import nutrition_db as ndb
        cat_map = {
            "latticini": ["latte", "yogurt", "formaggio", "ricotta", "mozzarella", "parmigiano",
                          "grana", "pecorino", "burro", "stracchino", "philadelphia", "fiordilatte",
                          "uova", "albumi", "tuorlo", "kefir", "panna", "latteria", "certosa",
                          "galbanino", "crema"],
            "carni": ["pollo", "tacchino", "manzo", "vitello", "maiale", "coniglio", "agnello",
                      "bresaola", "prosciutto", "salame", "mortadella", "carpaccio", "salsiccia",
                      "hamburger", "speck", "wurstel", "cotechino", "zampone"],
            "pesce": ["salmone", "tonno", "sgombro", "merluzzo", "orata", "branzino", "trota",
                      "acciughe", "sarde", "sogliola", "cernia", "polpo", "seppia", "calamari",
                      "gamberi", "code", "moscardini", "nasello", "palombo", "rombo",
                      "spigola", "pesce spada"],
            "cereali": ["pasta", "riso", "farro", "orzo", "cous cous", "cuscus", "quinoa",
                        "bulgur", "grano saraceno", "avena", "fiocchi", "semolino", "miglio",
                        "amaranto", "pane", "cracker", "grissini", "fette"],
            "legumi": ["lenticchie", "ceci", "fagioli", "piselli", "soia", "fave", "cicerchie",
                       "hummus", "edamame"],
            "verdure": ["zucchine", "melanzane", "peperoni", "pomodori", "spinaci", "bietole",
                        "cavolfiore", "broccoli", "cavolo", "insalata", "lattuga", "rucola",
                        "valeriana", "carote", "sedano", "finocchi", "cipolla", "aglio",
                        "asparagi", "carciofi", "funghi", "radicchio", "zucca", "patate",
                        "patata", "verza", "scarola", "indivia", "porro", "barbabietola",
                        "sedano rapa", "cetriolo", "ravanelli"],
            "frutta": ["mela", "pera", "banana", "arancia", "kiwi", "fragole", "mirtilli",
                       "lamponi", "ciliegie", "pesca", "albicocca", "susina", "prugna",
                       "uva", "melone", "anguria", "cocco", "ananas", "mango", "papaya",
                       "fichi", "cachi", "mandarino", "pompelmo", "limone", "avocado",
                       "ribes", "more"],
            "olii grassi": ["olio", "oliva", "semi", "lino", "cocco olio", "avocado olio"],
            "frutta secca": ["mandorle", "noci", "nocciole", "arachidi", "pistacchi",
                             "pinoli", "anacardi", "macadamia", "noci pecan"],
            "semi": ["semi", "chia", "lino semi", "sesamo", "girasole", "zucca", "papavero"],
            "bevande": ["caffè", "te", "camomilla", "tisana", "acqua", "vino", "birra",
                        "succo", "spremuta", "centrifugato", "estratto", "smoothie"]
        }
        for name, info in ndb.FOODS.items():
            kcal, prot, car, fat, fib, sug, sal = info
            cat = "varie"
            for cname, keywords in cat_map.items():
                if any(k in name.lower() for k in keywords):
                    cat = cname; break
            if "latte" in name and "cocco" not in name and "mandorla" not in name and "avena" not in name and "soia" not in name:
                cat = "latticini"
            try:
                con.execute("INSERT OR IGNORE INTO food_catalog (name,category,kcal,protein_g,carbs_g,fat_g,fiber_g,sugar_g,salt_g) VALUES (?,?,?,?,?,?,?,?,?)",
                          (name, cat, kcal, prot, car, fat, fib, sug, sal))
            except:
                pass
        con.commit()
        cnt = con.execute("SELECT COUNT(*) FROM food_catalog").fetchone()[0]
        return cnt
    except ImportError:
        return 0

def search_food_catalog(query="", category="", limit=30):
    """Cerca alimenti per nome o categoria."""
    con = get_db()
    if query:
        q = f"%{query}%"
        if category:
            return rows_to_list(con.execute(
                "SELECT * FROM food_catalog WHERE (name LIKE ? OR name LIKE ?) AND category=? ORDER BY name LIMIT ?",
                (q, f"%{query}%", category, limit)).fetchall())
        return rows_to_list(con.execute(
            "SELECT * FROM food_catalog WHERE name LIKE ? OR name LIKE ? ORDER BY CASE WHEN name LIKE ? THEN 0 ELSE 1 END, name LIMIT ?",
            (q, f"%{query}%", f"{query}%", limit)).fetchall())
    if category:
        return rows_to_list(con.execute(
            "SELECT * FROM food_catalog WHERE category=? ORDER BY name LIMIT ?", (category, limit)).fetchall())
    return rows_to_list(con.execute(
        "SELECT * FROM food_catalog ORDER BY name LIMIT ?", (limit,)).fetchall())

def get_food_categories():
    return [r["category"] for r in rows_to_list(
        get_db().execute("SELECT DISTINCT category FROM food_catalog ORDER BY category").fetchall()) if r["category"]]


def get_all_foods():
    """Ritorna tutti gli alimenti."""
    return rows_to_list(get_db().execute("SELECT * FROM food_catalog ORDER BY name").fetchall())


def get_food(fid):
    return row_to_dict(get_db().execute("SELECT * FROM food_catalog WHERE id=?", (fid,)).fetchone())


def compute_meal_macros(items):
    """Calcola totali kcal/P/C/F per una lista di item dieta (food_id o macro salvati)."""
    total = {"kcal": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0}
    for item in items:
        fid = item.get("food_id")
        grams = float(item.get("grams", 100) or 100)
        if fid:
            f = get_food(fid)
            if f:
                ratio = grams / 100.0
                total["kcal"] += f["kcal"] * ratio
                total["protein_g"] += f["protein_g"] * ratio
                total["carbs_g"] += f["carbs_g"] * ratio
                total["fat_g"] += f["fat_g"] * ratio
                total["fiber_g"] += f["fiber_g"] * ratio
                continue
        # fallback: macro salvati direttamente nell'item
        if item.get("kcal"):
            total["kcal"] += float(item.get("kcal") or 0)
            total["protein_g"] += float(item.get("protein_g") or 0)
            total["carbs_g"] += float(item.get("carbs_g") or 0)
            total["fat_g"] += float(item.get("fat_g") or 0)
        else:
            # fallback 2: lookup per nome in food_catalog
            f = get_db().execute("SELECT * FROM food_catalog WHERE name=? COLLATE NOCASE", (item.get("food",""),)).fetchone()
            if f:
                f = dict(f); ratio = grams / 100.0
                total["kcal"] += f["kcal"] * ratio
                total["protein_g"] += f["protein_g"] * ratio
                total["carbs_g"] += f["carbs_g"] * ratio
                total["fat_g"] += f["fat_g"] * ratio
                total["fiber_g"] += f["fiber_g"] * ratio
    return {k: round(v, 1) for k, v in total.items()}


# ─── FOOD SWAPS (sostituzione nutriente-equivalente) ─────────────────────

def get_food_swaps(food_id, limit=5):
    """Trova alimenti nella stessa categoria con profilo nutrizionale simile."""
    import math
    con = get_db()
    food = con.execute("SELECT * FROM food_catalog WHERE id=?", (food_id,)).fetchone()
    if not food:
        return []
    food = dict(food)
    cat = food["category"]
    if not cat:
        candidates = con.execute("SELECT * FROM food_catalog WHERE id != ?", (food_id,)).fetchall()
    else:
        candidates = con.execute("SELECT * FROM food_catalog WHERE category=? AND id != ?", (cat, food_id)).fetchall()
    target = {k: food.get(k, 0) for k in ["kcal", "protein_g", "carbs_g", "fat_g"]}
    scored = []
    for c in candidates:
        c = dict(c)
        cur = {"kcal": c["kcal"], "protein_g": c["protein_g"], "carbs_g": c["carbs_g"], "fat_g": c["fat_g"]}
        dist = math.sqrt(
            ((cur["kcal"] - target["kcal"]) / max(target["kcal"], 1)) ** 2 +
            ((cur["protein_g"] - target["protein_g"]) / max(target["protein_g"], 1)) ** 2 +
            ((cur["carbs_g"] - target["carbs_g"]) / max(target["carbs_g"], 1)) ** 2 +
            ((cur["fat_g"] - target["fat_g"]) / max(target["fat_g"], 1)) ** 2
        )
        scored.append((dist, c))
    scored.sort(key=lambda x: x[0])
    return [s[1] for s in scored[:limit]]


# ─── RECIPES (ricettario personale) ──────────────────────────────────────

def create_recipe(name, ingredients, instructions, servings=4, category="", macros=None):
    """Crea ricetta. ingredients = lista dict (food_id o name, grams)."""
    con = get_db()
    import json
    cur = con.execute(
        "INSERT INTO recipes (name, ingredients, instructions, servings, category, macros) VALUES (?,?,?,?,?,?)",
        (name, json.dumps(ingredients), instructions, servings, category, json.dumps(macros or {}))
    )
    con.commit()
    return cur.lastrowid


def get_recipe(rid):
    import json
    con = get_db()
    r = con.execute("SELECT * FROM recipes WHERE id=?", (rid,)).fetchone()
    if not r: return None
    d = dict(r)
    try: d["ingredients"] = json.loads(d["ingredients"]) if isinstance(d["ingredients"], str) else d["ingredients"]
    except: d["ingredients"] = []
    try: d["macros"] = json.loads(d["macros"]) if isinstance(d["macros"], str) else d["macros"]
    except: d["macros"] = {}
    return d


def list_recipes(category="", q=""):
    import json
    con = get_db()
    q = f"%{q}%"
    if category:
        rows = con.execute(
            "SELECT * FROM recipes WHERE category=? AND (name LIKE ? OR instructions LIKE ?) ORDER BY name",
            (category, q, q)).fetchall()
    else:
        rows = con.execute(
            "SELECT * FROM recipes WHERE name LIKE ? OR instructions LIKE ? ORDER BY name",
            (q, q)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        try: d["ingredients"] = json.loads(d["ingredients"]) if isinstance(d["ingredients"], str) else d["ingredients"]
        except: d["ingredients"] = []
        try: d["macros"] = json.loads(d["macros"]) if isinstance(d["macros"], str) else d["macros"]
        except: d["macros"] = {}
        out.append(d)
    return out


def delete_recipe(rid):
    con = get_db()
    con.execute("DELETE FROM recipes WHERE id=?", (rid,))
    con.commit()


def export_all_json():
    """Esporta tutto il DB in un dict JSON-serializzabile."""
    con = get_db()
    tables = ["patients", "categories", "bia_readings", "diet_plans", "diet_items",
              "appointments", "notifications", "documents", "progress_notes",
              "anamnesis", "measurements", "clinical_conditions", "food_catalog"]
    out = {}
    for t in tables:
        try:
            rows = con.execute(f"SELECT * FROM {t}").fetchall()
            out[t] = [dict(r) for r in rows]
        except Exception:
            out[t] = []
    return out


def export_patient_json(pid):
    """Export completo di un paziente (tutte le tabelle correlate)."""
    con = get_db()
    p = con.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
    if not p:
        return None
    data = {"patient": dict(p)}
    for t, fk in [("bia_readings", "patient_id"), ("diet_plans", "patient_id"),
                  ("diet_items", "patient_id"), ("appointments", "patient_id"),
                  ("progress_notes", "patient_id"), ("anamnesis", "patient_id"),
                  ("measurements", "patient_id"), ("documents", "patient_id")]:
        try:
            rows = con.execute(f"SELECT * FROM {t} WHERE {fk}=?", (pid,)).fetchall()
            data[t] = [dict(r) for r in rows]
        except Exception:
            data[t] = []
    return data


def import_patient_json(data):
    """Importa paziente da dict export. Ritorna nuovo id."""
    con = get_db()
    p = data.get("patient", {})
    pid = add_patient(p.get("name", "Importato"), p.get("sex"), p.get("goal"),
                     p.get("sport"), p.get("phone"), p.get("email"), p.get("notes"))
    # Tabelle correlate
    for t, fk in [("bia_readings", "patient_id"), ("diet_plans", "patient_id"),
                  ("diet_items", "patient_id"), ("appointments", "patient_id"),
                  ("progress_notes", "patient_id"), ("anamnesis", "patient_id"),
                  ("measurements", "patient_id"), ("documents", "patient_id")]:
        for row in data.get(t, []):
            cols = [c for c in row.keys() if c != "id" and c != fk]
            vals = [row[c] for c in cols]
            # Normalizza date/created
            cols.append(fk); vals.append(pid)
            placeholders = ",".join("?" * len(cols))
            con.execute(f"INSERT INTO {t} ({','.join(cols)}) VALUES ({placeholders})", vals)
    con.commit()
    return pid


# ─── DIET TEMPLATES (personalizzabili) ───────────────────────────────────

def create_diet_template(name, targets, owner_id=None):
    """Salva un template di dieta riusabile."""
    con = get_db()
    cur = con.execute("INSERT INTO diet_templates (name, targets, owner_id) VALUES (?,?,?)",
                     (name, json.dumps(targets), owner_id))
    con.commit()
    return cur.lastrowid


def list_diet_templates(owner_id=None):
    con = get_db()
    if owner_id:
        rows = con.execute("SELECT * FROM diet_templates WHERE owner_id=? OR owner_id IS NULL ORDER BY name", (owner_id,)).fetchall()
    else:
        rows = con.execute("SELECT * FROM diet_templates ORDER BY name").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        try: d["targets"] = json.loads(d["targets"]) if d["targets"] else {}
        except Exception: d["targets"] = {}
        out.append(d)
    return out


def delete_diet_template(tid):
    con = get_db()
    con.execute("DELETE FROM diet_templates WHERE id=?", (tid,))
    con.commit()


# ─── DRUG-NUTRIENT INTERACTIONS ─────────────────────────────────────────

DRUG_INTERACTIONS = [
    {"drug": "ACE-inibitori (enalapril, ramipril)", "category": "cardiovascolare",
     "effect": "Aumentano potassio (iperkaliemia), riducono zinco",
     "recommendation": "Evitare integratori di K+. Monitorare zinco. Consumare frutta secca, semi.",
     "severity": "alta"},
    {"drug": "Anticoagulanti (warfarin)", "category": "cardiovascolare",
     "effect": "Interazione con vitamina K (verdure a foglia verde)",
     "recommendation": "Mantenere assunzione costante di vit. K (non eliminare). Monitorare INR.",
     "severity": "alta"},
    {"drug": "Metformina", "category": "diabete",
     "effect": "Riduce B12, folati. Possibile malassorbimento.",
     "recommendation": "Integrare B12 (500-1000 mcg/giorno) e acido folico. Controllo annuale.",
     "severity": "alta"},
    {"drug": "Corticosteroidi (prednisone)", "category": "antinfiammatorio",
     "effect": "Ritenzione Na, perdita K, Ca, Mg. Osteoporosi indotta.",
     "recommendation": "Dieta iposodica. Integrare Ca (1000mg) + vit. D (2000UI) + Mg.",
     "severity": "alta"},
    {"drug": "Diuretici tiazidici", "category": "cardiovascolare",
     "effect": "Perdita K, Mg, Ca. Iperglicemia lieve.",
     "recommendation": "Integrare K, Mg. Limitare zuccheri semplici.",
     "severity": "media"},
    {"drug": "Diuretici ansa (furosemide)", "category": "cardiovascolare",
     "effect": "Forti perdite K, Mg, Ca",
     "recommendation": "Integrare K (alimenti ricchi: banane, spinaci, patate). Integrare Mg.",
     "severity": "alta"},
    {"drug": "Diuretici K-sparing (spironolattone)", "category": "cardiovascolare",
     "effect": "Aumentano K, perdita Ca",
     "recommendation": "Evitare alimenti ricchi di K in eccesso. Mantenere Ca adeguato.",
     "severity": "media"},
    {"drug": "Inibitori pompa protonica (omeprazolo)", "category": "gastroenterologico",
     "effect": "Riducono B12, Ca, Mg, Fe. Aumento rischio osteoporosi.",
     "recommendation": "Monitorare B12, ferritina. Integrare Ca, Mg, vit. D. Uso cronico da limitare.",
     "severity": "alta"},
    {"drug": "Statine (atorvastatina, rosuvastatina)", "category": "cardiovascolare",
     "effect": "Interazione con pompelmo. Riduzione CoQ10. Aumento CPK.",
     "recommendation": "Evitare pompelmo/succo. Integrare CoQ10 (100-200mg). Monitorare CPK.",
     "severity": "alta"},
    {"drug": "Farmaci tiroidei (levotiroxina)", "category": "endocrinologico",
     "effect": "Ca e Fe riducono assorbimento. Interazione con fibre, soia, noce.",
     "recommendation": "Assumere a digiuno 30-60min prima colazione. Separare 4h da Ca/Fe.",
     "severity": "alta"},
    {"drug": "Antidepressivi MAOI", "category": "psichiatrico",
     "effect": "Interazione pericolosa con tiramina (crisi ipertensiva)",
     "recommendation": "Evitare: formaggi stagionati, salumi, crauti, soia, birra, vino rosso.",
     "severity": "alta"},
    {"drug": "Contraccettivi orali", "category": "ormonale",
     "effect": "Riducono B6, B12, folati. Aumento ritenzione idrica.",
     "recommendation": "Integrare B6 (25-50mg), folati (400mcg), B12. Dieta ricca di frutta e verdura.",
     "severity": "media"},
    {"drug": "Antiepilettici (fenitoina, valproato)", "category": "neurologico",
     "effect": "Riducono B9, B12, D, K. Valproato: aumento ammonio, rischio obesità.",
     "recommendation": "Integrare B9, vit. D. Monitorare ammonio per valproato. Dieta iperproteica?",
     "severity": "alta"},
    {"drug": "Metotrexato", "category": "antireumatico",
     "effect": "Antagonista folati. Riduce B12, B9.",
     "recommendation": "Integrare acido folico (5mg/settimana post-dose). Monitorare B12.",
     "severity": "alta"},
    {"drug": "Bifosfonati (alendronato)", "category": "osso",
     "effect": "Ca, Fe, Mg riducono assorbimento. Rischio esofagite.",
     "recommendation": "Assumere a digiuno con acqua. Attendere 30-60min prima di cibo/Ca.",
     "severity": "media"},
]


def seed_drug_interactions():
    """Popola drug_interactions se vuoto."""
    con = get_db()
    cnt = con.execute("SELECT COUNT(*) FROM drug_interactions").fetchone()[0]
    if cnt > 0:
        return cnt
    for d in DRUG_INTERACTIONS:
        con.execute("INSERT INTO drug_interactions (drug, category, effect, recommendation, severity) VALUES (?,?,?,?,?)",
                    (d["drug"], d["category"], d["effect"], d["recommendation"], d["severity"]))
    con.commit()
    return len(DRUG_INTERACTIONS)


def search_drugs(query="", limit=20):
    """Cerca farmaci per nome."""
    con = get_db()
    if query:
        return rows_to_list(con.execute(
            "SELECT * FROM drug_interactions WHERE drug LIKE ? ORDER BY severity DESC, drug LIMIT ?",
            (f"%{query}%", limit)).fetchall())
    return rows_to_list(con.execute(
        "SELECT * FROM drug_interactions ORDER BY severity DESC, drug LIMIT ?", (limit,)).fetchall())


# ─── QUESTIONNAIRES ──────────────────────────────────────────────────────

QUESTIONNAIRES = {
    "medas": {
        "name": "MEDAS — Adesione Dieta Mediterranea",
        "description": "Questionario di 14 item sull'aderenza alla dieta mediterranea (punteggio 0-14)",
        "max_score": 14,
        "questions": [
            "Usa olio d'oliva come principale grasso da condimento?",
            "Quanto olio d'oliva consuma al giorno? (≥4 cucchiai = 1 punto)",
            "Quante porzioni di verdura consuma al giorno? (≥2 porzioni/die = 1 punto)",
            "Quanta frutta consuma al giorno? (≥3 porzioni/die = 1 punto)",
            "Quanta carne rossa/processata consuma al giorno? (<1 porzione/die = 1 punto)",
            "Quanto burro/margarina/panna consuma al giorno? (<1/die = 1 punto)",
            "Beve bevande zuccherate? (<1/die = 1 punto)",
            "Quanto vino rosso beve al giorno? (1-2 bicchieri/die = 1 punto)",
            "Quanti legumi consuma a settimana? (≥3 porzioni/sett = 1 punto)",
            "Quanto pesce consuma a settimana? (≥3 porzioni/sett = 1 punto)",
            "Quanta frutta secca consuma a settimana? (≥3 porzioni/sett = 1 punto)",
            "Consuma più pollo/tacchino che carne rossa? (Sì = 1 punto)",
            "Quante volte a settimana mangia pasta/riso/cereali? (≥3/sett = 1 punto)",
            "Usa salsa di pomodoro o condimenti a base di pomodoro? (≥2/sett = 1 punto)",
        ]
    },
    "scoff": {
        "name": "SCOFF — Screening Disturbi Alimentari",
        "description": "5 domande per screening disturbi alimentari (≥2 positivo)",
        "max_score": 5,
        "questions": [
            "Si è mai sentito/a così pieno/a da star male? (Sì = 1 punto)",
            "Le capita di non riuscire a smettere di mangiare? (Sì = 1 punto)",
            "Ha perso più di 6 kg in 3 mesi? (Sì = 1 punto)",
            "Si considera grasso/a quando gli altri dicono che è troppo magro/a? (Sì = 1 punto)",
            "Il cibo domina la sua vita? (Sì = 1 punto)",
        ]
    },
    "vas": {
        "name": "VAS — Scala Analogica Visiva",
        "description": "Scala 0-10 per sintomi soggettivi (fame, dolore, gonfiore, energia, stress)",
        "max_score": 10,
        "questions": [
            "Fame (0=none, 10=molta fame)",
            "Dolore (0=nessuno, 10=molto dolore)",
            "Gonfiore addominale (0=nessuno, 10=molto gonfiore)",
            "Energia (0=nessuna, 10=molta energia)",
            "Stress (0=nessuno, 10=motto stress)",
        ]
    }
}


def save_questionnaire_result(pid, questionnaire, score, answers, notes=""):
    """Salva risultato questionario."""
    con = get_db()
    con.execute("INSERT INTO questionnaire_results (patient_id, questionnaire, score, answers, notes) VALUES (?,?,?,?,?)",
                (pid, questionnaire, score, json.dumps(answers), notes))
    con.commit()
    return con.execute("SELECT last_insert_rowid()").fetchone()[0]


def list_questionnaire_results(pid, questionnaire=None):
    """Lista risultati questionari per paziente."""
    con = get_db()
    if questionnaire:
        return rows_to_list(con.execute(
            "SELECT * FROM questionnaire_results WHERE patient_id=? AND questionnaire=? ORDER BY date DESC",
            (pid, questionnaire)).fetchall())
    return rows_to_list(con.execute(
        "SELECT * FROM questionnaire_results WHERE patient_id=? ORDER BY date DESC", (pid,)).fetchall())


# ─── USER MANAGEMENT ────────────────────────────────────────────────────

def create_user(username, password_hash, role="nutritionist", clinic_name="", logo_url="", theme_color="#6366f1"):
    """Crea un nuovo utente. Ritorna l'id o None se username esiste."""
    con = get_db()
    try:
        con.execute("INSERT INTO users (username, password_hash, role, clinic_name, logo_url, theme_color) VALUES (?,?,?,?,?,?)",
                    (username, password_hash, role, clinic_name, logo_url, theme_color))
        con.commit()
        return con.execute("SELECT last_insert_rowid()").fetchone()[0]
    except Exception:
        return None


def get_user(username):
    """Cerca utente per username."""
    return row_to_dict(get_db().execute("SELECT * FROM users WHERE username=?", (username,)).fetchone())


def get_user_by_id(uid):
    """Cerca utente per id."""
    return row_to_dict(get_db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone())


def create_session(user_id):
    """Crea sessione token per utente. Ritorna il token."""
    import secrets
    token = secrets.token_hex(32)
    con = get_db()
    # Delete old sessions for user
    con.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
    con.execute("INSERT INTO sessions (token, user_id) VALUES (?,?)", (token, user_id))
    con.commit()
    return token


def get_session(token):
    """Recupera sessione per token."""
    return row_to_dict(get_db().execute("SELECT s.*, u.username, u.role, u.clinic_name, u.logo_url, u.theme_color "
                                        "FROM sessions s JOIN users u ON s.user_id=u.id WHERE s.token=?",
                                        (token,)).fetchone())


def delete_session(token):
    con = get_db()
    con.execute("DELETE FROM sessions WHERE token=?", (token,))
    con.commit()


def update_user_settings(uid, clinic_name=None, logo_url=None, theme_color=None):
    con = get_db()
    fields = []
    vals = []
    if clinic_name is not None:
        fields.append("clinic_name=?")
        vals.append(clinic_name)
    if logo_url is not None:
        fields.append("logo_url=?")
        vals.append(logo_url)
    if theme_color is not None:
        fields.append("theme_color=?")
        vals.append(theme_color)
    if fields:
        vals.append(uid)
        con.execute(f"UPDATE users SET {','.join(fields)} WHERE id=?", tuple(vals))
        con.commit()


# ─── STATISTICS ──────────────────────────────────────────────────────────

def get_studio_stats():
    """Ritorna statistiche aggregate dello studio."""
    con = get_db()
    total_patients = con.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    # Per categoria
    cats = rows_to_list(con.execute(
        "SELECT c.name, COUNT(p.id) as cnt FROM patients p LEFT JOIN categories c ON p.category_id=c.id GROUP BY c.id ORDER BY cnt DESC").fetchall())

    # Per sesso
    gender = rows_to_list(con.execute(
        "SELECT sex, COUNT(*) as cnt FROM patients GROUP BY sex").fetchall())

    # Età media
    age_stats = con.execute(
        "SELECT AVG(CAST(strftime('%Y','now') AS INTEGER) - CAST(birth_date AS INTEGER)) FROM patients WHERE birth_date IS NOT NULL AND birth_date!=''").fetchone()[0]

    # Ultimi pazienti
    recent = rows_to_list(con.execute(
        "SELECT id, name, created FROM patients ORDER BY created DESC LIMIT 5").fetchall())

    # BIA medie (ultima lettura per paziente)
    bia_avg = row_to_dict(con.execute(
        "SELECT AVG(weight_kg) as avg_weight, AVG(bmi) as avg_bmi, AVG(bf_pct) as avg_bf, "
        "AVG(mm_pct) as avg_mm, AVG(tbw_l) as avg_tbw, AVG(ecw_l) as avg_ecw, AVG(pha) as avg_pha "
        "FROM bia_readings WHERE id IN (SELECT MAX(id) FROM bia_readings GROUP BY patient_id)").fetchone()) or {}

    return {
        "total_patients": total_patients,
        "categories": cats,
        "gender": gender,
        "avg_age": round(age_stats, 1) if age_stats else 0,
        "recent_patients": recent,
        "bia_averages": bia_avg,
    }


# ─── INIT ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print(f"DB: {DB_PATH} — tabelle create/verificate")# ─── MEAL DIARY CRUD ─────────────────────────────────────────────────────

def save_diary_entry(pid, date, meal, food_id, food_name, consumed=0, notes="", plan_id=None):
    con = get_db()
    con.execute("INSERT INTO meal_diary (patient_id, plan_id, date, meal, food_id, food_name, consumed, notes) VALUES (?,?,?,?,?,?,?,?)",
                (pid, plan_id, date, meal, food_id, food_name, consumed, notes))
    con.commit()
    return con.execute("SELECT last_insert_rowid()").fetchone()[0]


def get_diary_entries(pid, date=None):
    con = get_db()
    if date:
        return rows_to_list(con.execute(
            "SELECT * FROM meal_diary WHERE patient_id=? AND date=? ORDER BY id", (pid, date)).fetchall())
    return rows_to_list(con.execute(
        "SELECT * FROM meal_diary WHERE patient_id=? ORDER BY date DESC, id", (pid,)).fetchall())


def update_diary_entry(eid, consumed=None, notes=None):
    con = get_db()
    fields = []
    vals = []
    if consumed is not None:
        fields.append("consumed=?")
        vals.append(1 if consumed else 0)
    if notes is not None:
        fields.append("notes=?")
        vals.append(notes)
    if fields:
        vals.append(eid)
        con.execute(f"UPDATE meal_diary SET {','.join(fields)} WHERE id=?", tuple(vals))
        con.commit()


# ─── MESSAGES CRUD ───────────────────────────────────────────────────────

def send_message(pid, text, sender="nutritionist"):
    con = get_db()
    con.execute("INSERT INTO messages (patient_id, sender, text) VALUES (?,?,?)", (pid, sender, text))
    con.commit()
    return con.execute("SELECT last_insert_rowid()").fetchone()[0]


def get_messages(pid, limit=50):
    return rows_to_list(get_db().execute(
        "SELECT * FROM messages WHERE patient_id=? ORDER BY created_at DESC LIMIT ?", (pid, limit)).fetchall())


def mark_messages_read(pid):
    con = get_db()
    con.execute("UPDATE messages SET read=1 WHERE patient_id=? AND sender='patient'", (pid,))
    con.commit()


def count_unread(pid):
    r = get_db().execute("SELECT COUNT(*) FROM messages WHERE patient_id=? AND read=0 AND sender='patient'", (pid,)).fetchone()
    return r[0] if r else 0


def ensure_v2_tables():
    """Crea meal_diary e messages se non esistono (per upgrade v2.15->v2.16)."""
    con = get_db()
    con.executescript("""
        CREATE TABLE IF NOT EXISTS meal_diary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            plan_id INTEGER,
            date TEXT NOT NULL,
            meal TEXT NOT NULL DEFAULT '',
            food_id INTEGER,
            food_name TEXT DEFAULT '',
            consumed INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            sender TEXT NOT NULL DEFAULT 'nutritionist',
            text TEXT NOT NULL,
            read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
    """)
    con.commit()