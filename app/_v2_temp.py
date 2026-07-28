# ─── NOTIFICATIONS ───────────────────────────────────────────────────────

NOTIF_TYPES = {"reminder": "⏰", "message": "💬", "appointment": "📅", "alert": "⚠️"}

def add_notification(patient_id, title, message, notif_type="reminder"):
    con = get_db()
    con.execute("INSERT INTO notifications (patient_id, title, message, type) VALUES (?,?,?,?)",
                (patient_id, title, message, notif_type))
    con.commit()
    return con.execute("SELECT last_insert_rowid()").fetchone()[0]


def get_notifications(limit=50, unread_only=False):
    con = get_db()
    q = "SELECT n.*, p.name as patient_name FROM notifications n LEFT JOIN patients p ON n.patient_id=p.id"
    if unread_only:
        q += " WHERE n.read=0"
    q += " ORDER BY n.created_at DESC LIMIT ?"
    return rows_to_list(con.execute(q, (limit,)).fetchall())


def get_notifications_for_patient(pid, limit=50):
    return rows_to_list(get_db().execute(
        "SELECT * FROM notifications WHERE patient_id=? ORDER BY created_at DESC LIMIT ?", (pid, limit)).fetchall())


def mark_notification_read(nid):
    con = get_db()
    con.execute("UPDATE notifications SET read=1 WHERE id=?", (nid,))
    con.commit()


def mark_all_notifications_read():
    con = get_db()
    con.execute("UPDATE notifications SET read=1 WHERE read=0")
    con.commit()


def count_unread_notifications():
    r = get_db().execute("SELECT COUNT(*) FROM notifications WHERE read=0").fetchone()
    return r[0] if r else 0


def ensure_v2_tables():
    """Crea tabelle mancanti per upgrade (v2.15->v2.17)."""
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
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            title TEXT NOT NULL,
            message TEXT NOT NULL DEFAULT '',
            type TEXT NOT NULL DEFAULT 'reminder',
            read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
    """)
    con.commit()