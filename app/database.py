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
    from anthropometry import compute_anthropometry
    results = []
    for pid in ids:
        p = get_patient(pid)
        if not p:
            continue
        # ultima BIA + misure per dati recenti
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
        whr = round(meas_d.get("waist_cm",0) / meas_d.get("hip_cm",1), 2) if meas_d.get("waist_cm") and meas_d.get("hip_cm") else None
        results.append({
            "id": pid, "name": p.get("name"), "sex": p.get("sex"),
            "age": p.get("birth_date"), "goal": p.get("goal"), "sport": p.get("sport"),
            "weight_kg": weight, "height_cm": height, "bmi": bmi,
            "bf_pct": bf, "mm_pct": mm, "pha": pha,
            "tbw_l": tbw, "bmr_kcal": bmr,
            "ffmi": ffmi, "whr": whr,
        })
    return results

# ─── FOOD CATALOG ──────────────────────────────────────────────────

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
    # Migra colonne diet_items
    for col in ["food_id INTEGER DEFAULT NULL", "kcal REAL DEFAULT NULL",
                "protein_g REAL DEFAULT NULL", "carbs_g REAL DEFAULT NULL", "fat_g REAL DEFAULT NULL"]:
        try:
            con.execute(f"ALTER TABLE diet_items ADD COLUMN {col}")
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
        get_db().execute("SELECT DISTINCT category FROM food_catalog WHERE category!='' ORDER BY category").fetchall())]

def get_food(fid):
    return row_to_dict(get_db().execute("SELECT * FROM food_catalog WHERE id=?", (fid,)).fetchone())

def compute_meal_macros(items):
    """Calcola totali kcal/P/C/F per una lista di item dieta con food_id."""
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
    return {k: round(v, 1) for k, v in total.items()}

# ─── INIT ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print(f"DB: {DB_PATH} — tabelle create/verificate")