"""NutriCoach — OCR layer per PDF BIA scansionati.

Estrae immagini dalle pagine dei PDF che non contengono un layer testuale.
Non viene eseguito OCR server-side — le immagini vengono restituite
per essere mostrate al frontend, dove l'utente puo' inserire i valori
manualmente oppure usare un servizio OCR basato su browser.

Dipendenze:
  - PyMuPDF  (fitz)        -> rendering pagine in PNG
"""

import io
import os


def ocr_pdf_text(pdf_bytes: bytes, dpi: int = 220, lang: str = "ita+eng") -> str:
    """Ritorna una stringa vuota — l'OCR e' stato rimosso.

    Le immagini delle pagine vengono restituite dall'endpoint upload
    al frontend, dove l'utente puo' inserire i valori BIA manualmente.
    """
    return ""


def ocr_pdf_images(pdf_bytes: bytes, dpi: int = 200) -> list:
    """Renderizza un PDF in lista di bytes PNG (una per pagina).

    Ritorna una lista di bytes PNG (non base64).
    """
    try:
        import fitz
    except ImportError:
        return []

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        images.append(pix.tobytes("png"))
    doc.close()
    return images
