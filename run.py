"""NutriCoach — Avvio app (localhost, nessun cloud).

Uso:
    pip install -r requirements.txt
    python run.py            # apre http://127.0.0.1:8090

Env opzionali:
    NUTRICOACH_DB    path del database SQLite (default ~/.nutricoach/nutricoach.db)
    NUTRICOACH_PORT  porta (default 8090)
    NUTRICOACH_NOBROWSE  se impostato, non apre il browser automaticamente
"""

import os
import sys
import webbrowser
import uvicorn
import threading
import time
import logging

# Cartella log in base al sistema (fuori dalla cartella del programma)
if getattr(sys, "frozen", False):
    _base = os.path.dirname(sys.executable)
else:
    _base = os.path.dirname(os.path.abspath(__file__))

LOG_DIR = os.path.join(os.path.expanduser("~"), ".nutricoach")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "nutricoach.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")],
)
log = logging.getLogger("nutricoach")

# import diretto dell'app (funziona da sorgente e da EXE PyInstaller)
import app as app_module

DB_ENV = os.environ.get("NUTRICOACH_DB")
PORT = int(os.environ.get("NUTRICOACH_PORT", "8090"))

if DB_ENV:
    import db as _db
    _db.DB_PATH = DB_ENV


def open_browser():
    time.sleep(1.5)
    try:
        webbrowser.open(f"http://127.0.0.1:{PORT}/")
    except Exception as e:  # pragma: no cover
        log.warning("Impossibile aprire il browser: %s", e)


if __name__ == "__main__":
    log.info("NutriCoach avvio su porta %s (DB=%s)", PORT, DB_ENV or "default")
    if not os.environ.get("NUTRICOACH_NOBROWSE"):
        threading.Thread(target=open_browser, daemon=True).start()
    try:
        uvicorn.run(app_module.app, host="127.0.0.1", port=PORT, log_level="info")
    except Exception as e:  # pragma: no cover
        log.exception("Errore di avvio: %s", e)
        input("Errore di avvio. Premi Invio per chiudere. (vedi ~/.nutricoach/nutricoach.log)")
