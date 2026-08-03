# -*- coding: utf-8 -*-
"""NutriCoach v2 (Dietowin-style) — avvio rapido.

Flag speciale `--zai-browser`:
  processo figlio usato dal browser OCR integrato (pywebview).
  Con questo flag l'app NON avvia uvicorn: apre solo la finestra browser
  e termina. Necessario per PyInstaller onefile (sys.executable == EXE):
  `subprocess.Popen([sys.executable, "--zai-browser", ...])` riavvia l'EXE,
  che entra in questo ramo e NON riapre una nuova sessione NutriCoach.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))

def _main_zai_browser(argv):
    """Apre solo la finestra browser OCR e termina (processo figlio)."""
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
    sys.path.insert(0, HERE)
    try:
        from app.zai_ocr import _run_webview, _run_login_webview
    except Exception as exc:  # pragma: no cover
        sys.stderr.write("zai_ocr import fallito: %s\n" % exc)
        sys.exit(1)
    if token_file:
        _run_login_webview(url, token_file)
    else:
        _run_webview(url, titolo)
    sys.exit(0)


if __name__ == "__main__":
    # Processo figlio del browser OCR: non avviare uvicorn!
    if "--zai-browser" in sys.argv:
        _main_zai_browser(sys.argv)
    sys.path.insert(0, HERE)
    from app.main import app
    import uvicorn
    PORT = int(os.environ.get("NUTRICOACH_PORT", "8400"))
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")
