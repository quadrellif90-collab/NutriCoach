# -*- coding: utf-8 -*-
"""
zai_ocr.py — Client OCR z.ai + browser integrato (pattern Elite Beach Balancer).

Flusso:
  1) L'utente apre il browser integrato (pywebview in processo separato) su
     https://ocr.z.ai/ e fa login una tantum. Il token OAuth salvato nel
     localStorage del sito (chiave "settings-storage" -> state.token) viene
     catturato e salvato nella configurazione dell'app.
  2) Da lì in poi, caricando una foto/PDF, l'app fa:
       POST {BASE}/tasks/process (multipart "file") -> task_id
       GET  {BASE}/tasks/detail/{task_id} (polling) -> risultato OCR
  3) Il risultato contiene testo (Markdown) e tabelle (HTML) che il parser
     di import converte in record BIA / Antropometria / Piano alimentare.

Nessuna dipendenza esterna obbligatoria: urllib stdlib per l'API, pywebview
opzionale per il browser integrato. Il token è personale e non condiviso.
"""

import os
import sys
import io
import json
import time
import uuid
import mimetypes
import urllib.request
import urllib.error
from urllib import parse as urllib_parse

BASE_URL = "https://ocr.z.ai/api/v1/z-ocr"
OCR_SITE = "https://ocr.z.ai/"

# Chiave nella configurazione dell'app dove salviamo il token.
_CONFIG_KEY_TOKEN = "ocr_zai_token"


class OcrError(Exception):
    """Errore del servizio OCR z.ai (con messaggio leggibile per l'utente)."""


# ----------------------------------------------------------------------------
# Gestione token (salvato in studio_config.json via database.py)
# ----------------------------------------------------------------------------

def _carica_config():
    try:
        import app.database as db
        return db.load_studio_config() or {}
    except Exception:
        return {}


def _salva_config(cfg):
    try:
        import app.database as db
        db.save_studio_config(cfg)
        return True
    except Exception:
        return False


def get_token():
    """Ritorna il token salvato, oppure None se non presente."""
    try:
        return _carica_config().get(_CONFIG_KEY_TOKEN) or None
    except Exception:
        return None


def set_token(token):
    """Salva il token nella configurazione dell'app."""
    try:
        cfg = _carica_config()
        cfg[_CONFIG_KEY_TOKEN] = token or ""
        return _salva_config(cfg)
    except Exception:
        return False


def cancella_token():
    set_token("")


def token_presente():
    return bool(get_token())


# ----------------------------------------------------------------------------
# Browser integrato (pywebview in processo separato, come BBP)
# ----------------------------------------------------------------------------

def browser_interno_ok():
    try:
        import webview  # noqa: F401
        return True
    except Exception:
        return False


def _run_webview(url, titolo):
    """Processo figlio: apre il browser interno (uso manuale)."""
    try:
        import webview
        webview.create_window(titolo, url, width=1100, height=780, resizable=True)
        webview.start()
    except Exception:
        pass


def _avvia_browser_child(url, titolo=None, token_file=None):
    """Lancia run_v2.py --zai-browser in processo separato via subprocess.

    IMPORTANTE: in PyInstaller onefile sys.executable == l'EXE, quindi
    `subprocess.Popen([sys.executable, "--zai-browser", ...])` riavvia l'EXE,
    che entra nel ramo --zai-browser di run_v2.py e apre SOLO la finestra
    browser (non avvia uvicorn). Uso subprocess invece di multiprocessing.spawn
    per evitare il bug "il pulsante OCR riapre una nuova sessione NutriCoach".
    """
    import subprocess
    cmd = [sys.executable, "--zai-browser", "--url", url]
    if titolo:
        cmd += ["--titolo", titolo]
    if token_file:
        cmd += ["--token-file", token_file]
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        kw = {"creationflags": creationflags} if os.name == "nt" else {}
        subprocess.Popen(cmd, shell=False, **kw)
        return True
    except Exception:
        return False


def apri_browser_ocr(url=None, titolo="OCR z.ai — Estrai testo"):
    """Apre ocr.z.ai nel browser interno. Ritorna True se avviato."""
    if not browser_interno_ok():
        return False
    return _avvia_browser_child(url or OCR_SITE, titolo=titolo)


# JS eseguito periodicamente nella pagina: legge il token dallo storage del sito.
_JS_LEGGI_TOKEN = r"""
(function(){
  try {
    var raw = localStorage.getItem('settings-storage');
    if (!raw) {
      for (var i=0;i<localStorage.length;i++){
        var k = localStorage.key(i);
        var v = localStorage.getItem(k) || '';
        if (v.indexOf('"token"') !== -1) { raw = v; break; }
      }
    }
    if (!raw) return '';
    var obj = JSON.parse(raw);
    var st = obj && (obj.state || obj);
    var tok = st && st.token;
    return tok ? String(tok) : '';
  } catch(e) { return ''; }
})();
"""


def _run_login_webview(url, token_file):
    """Processo figlio: apre il login e scrive il token catturato su file."""
    try:
        import webview
    except ImportError:
        return

    stato = {"trovato": False}

    def _monitor(window):
        import time
        for _ in range(300):
            if stato["trovato"]:
                return
            try:
                tok = window.evaluate_js(_JS_LEGGI_TOKEN)
            except Exception:
                tok = None
            if tok:
                stato["trovato"] = True
                try:
                    with open(token_file, "w", encoding="utf-8") as f:
                        json.dump({"token": tok}, f)
                except Exception:
                    pass
                try:
                    window.destroy()
                except Exception:
                    pass
                return
            time.sleep(1.0)

    try:
        window = webview.create_window(
            "Login z.ai — Accedi per abilitare l'OCR automatico",
            url, width=1100, height=800, resizable=True)
        webview.start(_monitor, window)
    except Exception:
        pass


def login_e_cattura_token(timeout=330):
    """Apre il login z.ai e attende la cattura del token.

    Ritorna (ok: bool, token_or_msg). ok=True se il token è stato catturato.
    """
    if not browser_interno_ok():
        return False, ("Browser interno non disponibile. Installa il "
                       "componente 'pywebview' oppure inserisci il token "
                       "manualmente.")
    try:
        import webview  # noqa: F401
    except ImportError:
        return False, "Componente 'pywebview' non installato."

    import tempfile

    fd, token_file = tempfile.mkstemp(prefix="zai_token_", suffix=".json")
    os.close(fd)
    try:
        os.remove(token_file)
    except OSError:
        pass

    if not _avvia_browser_child(OCR_SITE, titolo="Login z.ai — Accedi per abilitare l'OCR automatico",
                                token_file=token_file):
        return False, "Impossibile avviare il browser interno."

    inizio = time.time()
    while time.time() - inizio < timeout:
        if os.path.exists(token_file):
            break
        time.sleep(0.5)

    token = None
    if os.path.exists(token_file):
        for _ in range(10):
            try:
                with open(token_file, "r", encoding="utf-8") as f:
                    token = (json.load(f) or {}).get("token")
                break
            except Exception:
                time.sleep(0.2)

    try:
        if os.path.exists(token_file):
            os.remove(token_file)
    except OSError:
        pass

    if token:
        try:
            set_token(token)
            return True, "Login completato: OCR automatico abilitato ✓"
        except Exception:
            return False, "Token catturato ma salvataggio fallito."
    return False, "Token non rilevato. Completa il login nella finestra aperta."


# ----------------------------------------------------------------------------
# HTTP di basso livello (stdlib)
# ----------------------------------------------------------------------------

def _headers(extra=None):
    h = {
        "Accept": "application/json",
        "User-Agent": "NutriCoach/2.20.8",
    }
    tok = get_token()
    if tok:
        h["Authorization"] = "Bearer " + tok
    if extra:
        h.update(extra)
    return h


def _leggi_risposta(resp):
    raw = resp.read()
    try:
        data = json.loads(raw.decode("utf-8", "replace"))
    except Exception:
        raise OcrError("Risposta non valida dal servizio OCR.")
    if isinstance(data, dict) and "code" in data and data.get("code") != 200:
        msg = data.get("message") or "Richiesta rifiutata dal servizio OCR."
        raise OcrError(msg)
    return data


def _get(path, params=None, timeout=60):
    url = BASE_URL + path
    if params:
        url += "?" + urllib_parse.urlencode(params)
    req = urllib.request.Request(url, headers=_headers(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _leggi_risposta(resp)
    except urllib.error.HTTPError as e:
        _gestisci_http_error(e)
    except urllib.error.URLError as e:
        raise OcrError(f"Connessione fallita: {getattr(e, 'reason', e)}")


def _gestisci_http_error(e):
    if e.code == 401:
        raise OcrError("Sessione z.ai scaduta o assente: esegui di nuovo il "
                       "login a z.ai dalle impostazioni.")
    try:
        body = e.read().decode("utf-8", "replace")
        data = json.loads(body)
        msg = data.get("message") or body
    except Exception:
        msg = f"Errore HTTP {e.code}"
    raise OcrError(msg)


def _post_multipart_file(path, file_path, timeout=180):
    """POST multipart/form-data con un singolo campo 'file'."""
    boundary = "----NutriCoach" + uuid.uuid4().hex
    filename = os.path.basename(file_path)
    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    with open(file_path, "rb") as f:
        contenuto = f.read()

    buf = io.BytesIO()
    def w(s):
        buf.write(s if isinstance(s, bytes) else s.encode("utf-8"))

    w(f"--{boundary}\r\n")
    w(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n')
    w(f"Content-Type: {ctype}\r\n\r\n")
    w(contenuto)
    w(f"\r\n--{boundary}--\r\n")
    body = buf.getvalue()

    headers = _headers({
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
    })
    req = urllib.request.Request(BASE_URL + path, data=body,
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _leggi_risposta(resp)
    except urllib.error.HTTPError as e:
        _gestisci_http_error(e)
    except urllib.error.URLError as e:
        raise OcrError(f"Connessione fallita: {getattr(e, 'reason', e)}")


# ----------------------------------------------------------------------------
# API OCR
# ----------------------------------------------------------------------------

def _estrai_task_id(risposta):
    d = risposta.get("data") if isinstance(risposta, dict) else None
    if isinstance(d, dict):
        for k in ("task_id", "taskId", "id", "task"):
            if d.get(k):
                return str(d[k])
    if isinstance(risposta, dict):
        for k in ("task_id", "taskId", "id"):
            if risposta.get(k):
                return str(risposta[k])
    raise OcrError("Il servizio non ha restituito un identificativo di lavoro.")


def _stato_e_risultato(dettaglio):
    d = dettaglio.get("data") if isinstance(dettaglio, dict) else dettaglio
    if not isinstance(d, dict):
        return None, {}
    stato = str(d.get("status") or d.get("state") or "").lower()
    return stato, d


def carica_e_estrai(file_path, progress_cb=None, timeout_totale=300):
    """Carica un file (immagine/PDF) su z.ai e ritorna il risultato OCR.

    Ritorna il dizionario 'data' del dettaglio task (testo/tabelle).
    Solleva OcrError in caso di problemi.
    """
    if not token_presente():
        raise OcrError("Non hai ancora effettuato il login a z.ai. Aprilo "
                       "dalle impostazioni OCR e riprova.")
    if not os.path.isfile(file_path):
        raise OcrError(f"File non trovato: {file_path}")

    def _log(m):
        if progress_cb:
            try:
                progress_cb(m)
            except Exception:
                pass

    _log("Caricamento del file su z.ai...")
    risp = _post_multipart_file("/tasks/process", file_path)
    task_id = _estrai_task_id(risp)

    _log("Elaborazione OCR in corso...")
    inizio = time.time()
    attesa = 1.5
    while True:
        if time.time() - inizio > timeout_totale:
            raise OcrError("Tempo scaduto durante l'elaborazione OCR.")
        dettaglio = _get(f"/tasks/detail/{task_id}")
        stato, dati = _stato_e_risultato(dettaglio)

        if stato in ("success", "succeeded", "completed", "done", "finish",
                     "finished", "2"):
            _log("Risultato pronto.")
            return dati
        if stato in ("failed", "fail", "error", "3"):
            msg = dati.get("message") or dati.get("error") \
                or "Elaborazione OCR fallita."
            raise OcrError(msg)

        if not stato and (dati.get("markdown") or dati.get("result")
                          or dati.get("content") or dati.get("elements")):
            return dati

        time.sleep(attesa)
        attesa = min(attesa * 1.5, 8)


# ----------------------------------------------------------------------------
# Estrazione testo/tabelle dal risultato z.ai
# ----------------------------------------------------------------------------

def estrai_testo_e_tabelle(dati):
    """Da un risultato OCR z.ai estrae (markdown_testo, lista_tabelle_html).

    Gestisce sia la forma {markdown: ...} sia {elements: [...]} sia
    {result: {...}} con varianti di chiavi usate dal servizio.
    """
    md = dati.get("markdown") or dati.get("text") or dati.get("content") or ""
    tables = []
    for key in ("tables", "html", "table_html", "elements"):
        v = dati.get(key)
        if isinstance(v, str):
            tables.append(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    tables.append(item)
                elif isinstance(item, dict):
                    for k2 in ("html", "table", "markdown", "text", "content"):
                        if item.get(k2):
                            (tables if k2 in ("html", "table") else [md]).append(str(item[k2]))
    return str(md or ""), tables
