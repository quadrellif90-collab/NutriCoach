"""NutriCoach — OCR per PDF scansionati (offline, Best-Effort).

Se il PDF non ha testo selezionabile (scansionato), renderizziamo le pagine
come immagini. Non viene eseguito OCR server-side — il frontend mostra le
immagini e l'utente puo' copiare/incollare il testo a mano (oppure usare
un servizio OCR basato su browser come zai.qwen.ai).
"""

import base64
import io
import os

try:
    from PIL import Image
    _HAVE_PIL = True
except Exception:
    _HAVE_PIL = False

import fitz  # PyMuPDF


def ocr_pdf(path, dpi=200):
    """Renderizza un PDF in immagini base64.

    Non esegue OCR — restituisce solo le immagini delle pagine.

    Ritorna {"text": str, "pages": [base64_png, ...], "ocr": bool}
    """
    doc = fitz.open(path)
    pages = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        b64 = base64.b64encode(pix.tobytes("png")).decode("ascii")
        pages.append(b64)
    doc.close()
    return {"text": "", "pages": pages, "ocr": False}
