#!/usr/bin/env python3
"""NutriCoach v2 Launcher — entry point EXE per Dietowin-style app.
Avvia il server FastAPI IN-PROCESS (thread), poi apre finestra nativa pywebview.
Ricade su browser classico se pywebview non disponibile.

Flag speciale `--zai-browser`: processo figlio usato dal browser OCR integrato.
In PyInstaller onefile sys.executable == l'EXE, quindi
`subprocess.Popen([sys.executable, "--zai-browser", ...])` rilancia questo
entry point: se il flag è presente, NON si avvia uvicorn: si apre SOLO la
finestra di login/OCR pywebview e si termina. Necessario per evitare il bug
\"il pulsante OCR riapre una nuova sessione NutriCoach\".
"""
import os, sys, threading, time, webbrowser, logging, socket

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _main_zai_browser(argv):
    """Processo figlio: apre solo la finestra browser OCR e termina."""
    url = "https://ocr.z.ai/"
    titolo = "OCR z.ai — Estrai testo"
    token_file = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--url" and i + 1 < len(argv):
            url = argv[i + 1]; i += 2; continue
        if a == "--titolo" and i + 1 < len(argv):
            titolo = argv[i + 1]; i += 2; continue
        if a == "--token-file" and i + 1 < len(argv):
            token_file = argv[i + 1]; i += 2; continue
        i += 1
    try:
        from app.zai_ocr import _run_webview, _run_login_webview
    except Exception as exc:
        sys.stderr.write("zai_ocr import fallito: %s\n" % exc)
        sys.exit(1)
    if token_file:
        _run_login_webview(url, token_file)
    else:
        _run_webview(url, titolo)
    sys.exit(0)


LOG_DIR = os.path.join(os.path.expanduser("~"), ".nutricoach")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "nutricoach_v2.log")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")])
log = logging.getLogger("nutricoach_v2")

PORT = int(os.environ.get("NUTRICOACH_PORT", "8400"))

def _port_free(p):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", p)); return True
    except OSError: return False
    finally: s.close()

def open_browser():
    time.sleep(1.5)
    try: webbrowser.open(f"http://127.0.0.1:{PORT}/")
    except Exception as e: log.warning("browser: %s", e)

if __name__ == "__main__":
    # Processo figlio del browser OCR: NON avviare uvicorn!
    if "--zai-browser" in sys.argv:
        _main_zai_browser(sys.argv)

    from app import main as app_module
    from app.database import DATA_DIR as _DATA_DIR, DB_PATH

    # supporto pywebview (finestra nativa) — opzionale
    _HAVE_WEBVIEW = False
    try:
        import webview
        _HAVE_WEBVIEW = True
    except ImportError: pass

    log.info("NutriCoach v2 avvio su porta %d (DB=%s)", PORT, DB_PATH)

    used_port = PORT
    for cand in range(PORT, PORT + 10):
        if _port_free(cand): used_port = cand; break
    if used_port != PORT:
        log.warning("Porta %d occupata, uso porta %d", PORT, used_port)
        PORT = used_port

    # non bloccare: avvia uvicorn in thread
    import uvicorn
    from uvicorn.config import Config
    from uvicorn.server import Server

    config = Config(app_module.app, host="127.0.0.1", port=PORT, log_level="info",
                    log_config={
                        "version":1,"disable_existing_loggers":False,
                        "formatters":{"default":{"()":"uvicorn.logging.DefaultFormatter","fmt":"%(levelname)s: %(message)s"}},
                        "handlers":{"default":{"formatter":"default","class":"logging.StreamHandler","stream":"ext://sys.stderr"}},
                        "loggers":{"uvicorn":{"handlers":["default"],"level":"INFO","propagate":False}},
                    })
    server = Server(config=config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(1.5)

    # finestra nativa o browser
    if _HAVE_WEBVIEW:
        try:
            import webview
            ico_path = os.path.join(HERE, "assets", "icon.ico")
            # Il supporto icona dipende dalla piattaforma: Windows .ico
            wargs = {"title": "NutriCoach v2 — Dietowin",
                     "url": f"http://127.0.0.1:{PORT}/",
                     "width": 1200, "height": 800, "resizable": True, "min_size": (800,600)}
            if os.path.isfile(ico_path):
                wargs["icon"] = ico_path
            webview.create_window(**wargs)
            webview.start()
        except Exception as e:
            log.warning("webview fallito: %s -> browser", e)
            open_browser()
            t.join()
    else:
        open_browser()
        t.join()