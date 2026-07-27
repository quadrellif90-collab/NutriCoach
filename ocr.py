"""NutriCoach — OCR per PDF scansionati (offline, Best-Effort).

Se il PDF non ha testo selezionabile (scansionato), renderizziamo le pagine
come immagini e, se e' disponibile Tesseract (bundlato nell'EXE o installato
nel sistema), ne estraiamo il testo via pytesseract. Se Tesseract NON e'
disponibile, ritorniamo le immagini (base64) cosi' il frontend le mostra e
l'utente puo' copiare/incollare il testo a mano.

Tesseract bundlato: l'EXE include la cartella `tesseract/` (binario +
tessdata). A runtime la rileviamo sia in dev (./tesseract) che nel bundle
PyInstaller (sys._MEIPASS/tesseract). Nessun dato lascia il computer.
"""

import base64
import io
import os
import sys

try:
    import pytesseract
    _HAVE_TESS = True
except Exception:
    _HAVE_TESS = False

try:
    from PIL import Image
    _HAVE_PIL = True
except Exception:
    _HAVE_PIL = False

import fitz  # PyMuPDF


def _candidate_tesseract_dirs():
    """Directory dove cercare il binario Tesseract bundlato O di sistema."""
    dirs = []
    # 1) dentro il bundle PyInstaller
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        dirs.append(os.path.join(base, "tesseract"))
    # 2) directory corrente / sorgente
    here = os.path.dirname(os.path.abspath(__file__))
    dirs.append(os.path.join(here, "tesseract"))
    dirs.append(os.path.join(os.getcwd(), "tesseract"))
    # 3) installazione di sistema (Windows: Program Files; Win/Linux/Mac PATH)
    prog = os.environ.get("ProgramFiles", r"C:\Program Files")
    dirs.append(os.path.join(prog, "Tesseract-OCR"))
    dirs.append(os.path.join(prog + " (x86)", "Tesseract-OCR"))
    # 4) PATH di sistema (pytesseract lo usa da solo se presente)
    return dirs


def _find_tesseract():
    """Ritorna (cmd_path, tessdata_dir) se Tesseract e' disponibile.

    - Se il binario di sistema e' nel PATH, ritorna (None, system_tessdata_dir)
      cosi' pytesseract lo usa ma noi impostiamo TESSDATA_PREFIX corretto.
    - Altrimenti cerca un bundle/installazione in _candidate_tesseract_dirs().
    """
    # 1) bundle / installazione esplicita (anche fuori dal PATH)
    for d in _candidate_tesseract_dirs():
        if not os.path.isdir(d):
            continue
        for name in ("tesseract.exe", "tesseract"):
            cmd = os.path.join(d, name)
            if os.path.isfile(cmd):
                td = os.path.join(d, "tessdata")
                return (cmd, td if os.path.isdir(td) else None)
    # 2) fallback: binario di sistema nel PATH (pytesseract lo usa da solo)
    if _HAVE_TESS:
        try:
            pytesseract.get_tesseract_version()
            # prova a indovinare il tessdata di sistema
            import shutil
            tp = shutil.which("tesseract")
            if tp:
                d = os.path.dirname(tp)
                td = os.path.join(d, "tessdata")
                return (tp, td if os.path.isdir(td) else None)
            return (None, None)
        except Exception:
            pass
    return (None, None)


def _configure_tesseract():
    """Configura pytesseract se troviamo un bundle; ritorna True se utilizzabile."""
    if not _HAVE_TESS or not _HAVE_PIL:
        return False
    cmd, tessdata = _find_tesseract()
    try:
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
        # TESSDATA_PREFIX deve puntare alla CARTELLA GENITORE di tessdata
        # (es. C:\Program Files\Tesseract-OCR  se tessdata sta dentro)
        if tessdata:
            # TESSDATA_PREFIX deve puntare ALLA cartella che contiene i
            # file .traineddata (es. C:\Program Files\Tesseract-OCR\tessdata)
            os.environ["TESSDATA_PREFIX"] = tessdata
        # se non abbiamo un bundle ma tesseract e' nel PATH di sistema,
        # lasciamo che pytesseract lo risolva da solo (il suo default e' ok)
        # verifica che risponda
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


_TESS_OK = None  # cache lazy


def tesseract_available():
    """True se pytesseract+PIL importati e Tesseract (sistema o bundle) risponde."""
    global _TESS_OK
    if _TESS_OK is not None:
        return _TESS_OK
    _TESS_OK = _configure_tesseract()
    return _TESS_OK


def ocr_pdf(path, dpi=200, lang="ita+eng"):
    """Renderizza un PDF in immagini; se possibile estrae il testo via OCR.

    Ritorna {"text": str, "pages": [base64_png, ...], "ocr": bool}
    """
    doc = fitz.open(path)
    pages = []
    texts = []
    have_ocr = tesseract_available()
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        b64 = base64.b64encode(pix.tobytes("png")).decode("ascii")
        pages.append(b64)
        if have_ocr:
            try:
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                txt = pytesseract.image_to_string(img, lang=lang)
                texts.append(txt)
            except Exception:
                pass
    doc.close()
    text = "\n".join(t for t in texts if t.strip())
    return {"text": text, "pages": pages, "ocr": bool(text.strip()) and have_ocr}
