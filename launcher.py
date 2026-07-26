#!/usr/bin/env python3
"""NutriCoach Launcher — entry point per l'app desktop (finestra nativa).

Avvia il server FastAPI IN-PROCESS (in un thread, per evitare problemi di
fork con PyInstaller), poi apre una FINESTRA NATIVA con pywebview invece di
una pagina nel browser (comportamento PCC).

Se pywebview non e' disponibile, ricade sul browser classico (webbrowser).

Funziona sia in dev (python launcher.py) che frozen (PyInstaller exe).
"""

import os
import sys
import threading
import time
import webbrowser

# PyInstaller frozen: stdout/stderr possono essere None (console=False)
if getattr(sys, "frozen", False):
    for _n in ("stdout", "stderr"):
        if getattr(sys, _n, None) is None:
            try:
                setattr(sys, _n, open(os.devnull, "w", encoding="utf-8"))
            except Exception:
                pass

PORT = int(os.environ.get("NUTRICOACH_PORT", "8090"))
URL = f"http://127.0.0.1:{PORT}"

_server_error = None
_server_traceback = None


def get_app_dir():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def start_server():
    """Avvia FastAPI in un thread di background."""
    app_dir = get_app_dir()
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    os.chdir(app_dir)

    def _run():
        global _server_error, _server_traceback
        try:
            import uvicorn
            from app import app
            config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning")
            server = uvicorn.Server(config)
            server.run()
        except Exception as e:
            import traceback
            _server_error = e
            _server_traceback = traceback.format_exc()
            try:
                import log_config  # noqa
            except Exception:
                traceback.print_exc()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


def wait_for_server(timeout=30):
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        if _server_error is not None:
            return False
        try:
            urllib.request.urlopen(URL, timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


class JsApi:
    """Bridge esposto a JS come window.pywebview.api.

    - open_external(url): apre link esterni (mailto:, https://wa.me, siti)
      nel browser di sistema, fuori dalla webview.
    - download(filename, b64): salva un file tramite dialog nativo
      (necessario su macOS WKWebView che ignora <a download>).
    """

    def open_external(self, url: str) -> dict:
        try:
            webbrowser.open(url)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def download(self, filename: str, b64: str) -> dict:
        try:
            import base64
            import webview
            if not webview.windows:
                return {"ok": False, "error": "no window"}
            window = webview.windows[0]
            result = window.create_file_dialog(
                webview.SAVE_DIALOG, save_filename=filename
            )
            if not result:
                return {"ok": False, "error": "cancelled"}
            path = result if isinstance(result, str) else result[0]
            with open(path, "wb") as f:
                f.write(base64.b64decode(b64))
            return {"ok": True, "path": path}
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def _fallback_to_browser(reason=""):
    print(f"[NutriCoach] Finestra nativa non disponibile ({reason}) → browser.")
    webbrowser.open(URL)
    # keep-alive
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass


def main():
    print(f"Starting NutriCoach on {URL}...")
    start_server()
    if not wait_for_server():
        if _server_error is not None:
            print(f"ERRORE: server crash: {type(_server_error).__name__}: {_server_error}")
            if _server_traceback:
                print(_server_traceback)
        else:
            print("Warning: server timeout.")
        sys.exit(1)
    print(f"Server ready → {URL}")

    try:
        import webview
        webview.create_window(
            "NutriCoach", URL,
            width=1400, height=900, min_size=(1000, 600),
            js_api=JsApi(),
        )
        webview.start()  # blocca fino alla chiusura della finestra
        print("Finestra chiusa — arresto.")
    except ImportError:
        _fallback_to_browser("pywebview non installato")
    except Exception as e:
        _fallback_to_browser(f"pywebview: {e}")


if __name__ == "__main__":
    main()
