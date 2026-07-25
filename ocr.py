"""NutriCoach — OCR per PDF scansionati (offline, Best-Effort).

Se il PDF non ha testo selezionabile (scansionato), renderizziamo le pagine
come immagini e, se e' installato Tesseract, ne estraiamo il testo via
pytesseract. Se Tesseract NON e' presente, ritorniamo le immagini (base64)
cosi' il frontend le mostra e l'utente puo' copiare/incollare il testo a mano.

Nessun dato lascia il computer: tutto locale.
"""

import base64
import io

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


def tesseract_available():
    """True se pytesseract importato E il binario tesseract risponde."""
    if not _HAVE_TESS:
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def ocr_pdf(path, dpi=200, lang="ita+eng"):
    """Renderizza un PDF in immagini; se possibile estrae il testo via OCR.

    Ritorna {"text": str, "pages": [base64_png, ...], "ocr": bool}
    """
    doc = fitz.open(path)
    pages = []
    texts = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        b64 = base64.b64encode(pix.tobytes("png")).decode("ascii")
        pages.append(b64)
        if _HAVE_TESS and _HAVE_PIL and tesseract_available():
            try:
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                txt = pytesseract.image_to_string(img, lang=lang)
                texts.append(txt)
            except Exception:
                pass
    doc.close()
    text = "\n".join(t for t in texts if t.strip())
    return {"text": text, "pages": pages, "ocr": bool(text.strip()) and tesseract_available()}
