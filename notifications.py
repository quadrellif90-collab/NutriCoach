"""NutriCoach — Motore notifiche configurabili per cliente.

Il nutrizionista imposta, per ogni cliente, QUALI notifiche mandare al
cliente (riscontro/check-in, invio report, follow-up, promemoria pesata,
promemoria misurazioni), su QUALE canale (app/WhatsApp/Email) e con quale
FREQUENZA (giornaliera/settimanale/quindicinale/mensile).

Il motore genera le notifiche "dovute" in una coda (notification_log).
Lato nutrizionista: la coda mostra cosa inviare (ricordarsi di mandare il
report a Tizio). L'invio reale via WhatsApp/Email sara' attivato in seguito
con i client installati sul PC del nutrizionista; per ora la notifica e'
generata e marcata come da inviare / inviata.

Tipi di notifica:
- riscontro : chiede al cliente un check-in ("come sta andando?")
- report     : invio report / dieta aggiornata
- followup   : follow-up peso & misurazioni
- peso       : promemoria per pesarsi
- misura     : promemoria per misurazioni

Frequenze (giorni):
- daily 1, weekly 7, biweekly 14, monthly 30
"""

from datetime import date, timedelta

TYPES = {
    "riscontro": "Check-in / riscontro",
    "report":    "Invio report / dieta",
    "followup":  "Follow-up peso & misurazioni",
    "peso":      "Promemoria pesata",
    "misura":    "Promemoria misurazioni",
}
CHANNELS = ["app", "whatsapp", "email"]
FREQ_DAYS = {"daily": 1, "weekly": 7, "biweekly": 14, "monthly": 30}

DEFAULT_PREFS = [
    {"type": "riscontro", "channel": "whatsapp", "freq": "weekly",   "enabled": True},
    {"type": "report",    "channel": "email",    "freq": "monthly",  "enabled": True},
    {"type": "followup",  "channel": "app",      "freq": "biweekly", "enabled": False},
    {"type": "peso",      "channel": "app",      "freq": "weekly",   "enabled": False},
    {"type": "misura",    "channel": "whatsapp", "freq": "monthly",  "enabled": False},
]


def _iso(d):
    return d.isoformat()


def generate_due(cid, db, today=None):
    """Crea nella coda le notifiche dovute per il cliente.

    Ritorna la lista delle notifiche appena create.
    `db` e' il modulo db (per evitare import circolare).
    """
    today = today or date.today()
    prefs = db.get_notification_prefs(cid) or []
    # ultima inviata per tipo
    last = {}
    for row in db.list_notifications(cid, status="all"):
        t = row["type"]
        if t not in last or (row.get("sent_at") or row.get("created_at") or "") > last[t]:
            last[t] = row.get("sent_at") or row.get("created_at") or ""
    created = []
    for p in prefs:
        if not p.get("enabled"):
            continue
        t = p["type"]
        freq_days = FREQ_DAYS.get(p.get("freq", "weekly"), 7)
        anchor = last.get(t)
        if anchor:
            try:
                base = date.fromisoformat(anchor[:10])
            except Exception:
                base = today
            next_due = base + timedelta(days=freq_days)
        else:
            # mai inviata: e' dovuta da oggi
            next_due = today
        if next_due <= today:
            # evita duplicati pending per lo stesso tipo
            pending = [n for n in db.list_notifications(cid, status="pending") if n["type"] == t]
            if pending:
                continue
            nid = db.add_notification_log(
                cid, t, p.get("channel", "app"),
                due_date=_iso(next_due),
                note=f"{TYPES.get(t, t)} ({p.get('freq')})")
            created.append(nid)
    return created


def build_message(type_, client_name):
    """Testo predefinito della notifica verso il cliente."""
    msgs = {
        "riscontro": f"Ciao {client_name}, come sta andando la dieta questa settimana? Fammi sapere pesi ed eventuali difficolta'.",
        "report":    f"Ciao {client_name}, ti ho preparato il report aggiornato con fabbisogno e piano. Lo trovi in allegato.",
        "followup":  f"Ciao {client_name}, e' il momento del follow-up: pesati e, se puoi, fai le misurazioni.",
        "peso":      f"Ciao {client_name}, promemoria per la pesata settimanale. Inserisci il peso su NutriCoach.",
        "misura":    f"Ciao {client_name}, promemoria per le misurazioni (pieghe/addome/fianchi) questo mese.",
    }
    return msgs.get(type_, f"Promemoria {type_} per {client_name}.")
