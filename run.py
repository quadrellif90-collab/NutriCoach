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

# Quando l'app è un EXE one-file (console=False), sys.stdin può essere None.
# uvicorn.DefaultFormatter chiama sys.stdin.isatty() -> crash. Lo rendiamo robusto.
class _SafeStream:
    """Wrapper che simula un terminale non interattivo se stdin/out/err mancano."""
    def __init__(self, stream):
        self._s = stream
    def isatty(self):
        return False
    def write(self, s):
        if self._s is not None:
            try:
                self._s.write(s)
            except Exception:
                pass
    def flush(self):
        if self._s is not None:
            try:
                self._s.flush()
            except Exception:
                pass
    def read(self, *a):
        if self._s is not None:
            return self._s.read(*a)
        return ""
    def readline(self, *a):
        if self._s is not None:
            return self._s.readline(*a)
        return ""

if sys.stdin is None:
    sys.stdin = _SafeStream(None)
if sys.stdout is None:
    sys.stdout = _SafeStream(None)
if sys.stderr is None:
    sys.stderr = _SafeStream(None)

LOG_DIR = os.path.join(os.path.expanduser("~"), ".nutricoach")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "nutricoach.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")],
)
log = logging.getLogger("nutricoach")

# Config logging per uvicorn SENZA DefaultFormatter (che usa sys.stdin.isatty()):
# in EXE console=False sys.stdin e' None e crasha. Usiamo logging.Formatter standard.
UVICORN_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"class": "logging.Formatter", "fmt": "%(levelname)s: %(message)s"},
        "access": {
            "class": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelname)s: %(client_addr)s - "%(request_line)s" %(status_code)s',
        },
    },
    "handlers": {
        "default": {"formatter": "default", "class": "logging.StreamHandler", "stream": "ext://sys.stderr"},
        "access": {"formatter": "access", "class": "logging.StreamHandler", "stream": "ext://sys.stdout"},
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}

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
    # check aggiornamenti non bloccante (logga se disponibile; la UI lo mostra)
    def _boot_update_check():
        try:
            info = app_module.get_update_info(force=False)
            if info.get("update_available"):
                log.info("Aggiornamento disponibile: v%s (attuale v%s) — %s",
                          info.get("latest"), info.get("current"), info.get("html_url"))
        except Exception as e:  # pragma: no cover
            log.debug("check aggiornamenti non disponibile: %s", e)
    threading.Thread(target=_boot_update_check, daemon=True).start()
    if not os.environ.get("NUTRICOACH_NOBROWSE"):
        threading.Thread(target=open_browser, daemon=True).start()
    try:
        uvicorn.run(app_module.app, host="127.0.0.1", port=PORT,
                    log_level="info", log_config=UVICORN_LOG_CONFIG)
    except Exception as e:  # pragma: no cover
        log.exception("Errore di avvio: %s", e)
        # In EXE console=False sys.stdin puo' essere None -> input() crasha.
        try:
            input("Errore di avvio. Premi Invio per chiudere. (vedi ~/.nutricoach/nutricoach.log)")
        except Exception:
            time.sleep(5)
