# NutriCoach

**Gestionale di nutrizione per nutrizionisti — 100% locale, nessun cloud.**

NutriCoach è un'applicazione desktop che permette a un nutrizionista di gestire
i propri clienti, importare piani alimentari (PDF), registrare misure
antropometriche e BIA (bioimpedenziometria), pianificare diete automaticamente
e tenere traccia dei progressi — il tutto **offline**, con i dati salvati
esclusivamente sul proprio computer (SQLite in `~/.nutricoach/`).

> Nessun dato lascia la macchina. Nessun account remoto. Nessuna sottoscrizione.

---

## Funzionalità

| Area | Cosa fa |
|------|---------|
| **Clienti** | Anagrafica, ricerca, confronto tra clienti |
| **Diete da PDF** | Import di piani alimentari (gruppi con alternative + grammature), calcolo macro/giorno, spesa, riepilogo, export HTML/PDF |
| **Diario alimentare** | Builder manuale voce-per-voce con ricerca alimenti e **aggregazione automatica di macro + micronutrienti** (motore unico) |
| **Pianificatore** | Genera una settimana bilanciata partendo dai target (kcal / proteine / carboidrati / grassi) — stile "auto meal generator" |
| **BIA** | Parsing robusto di referti InBody/Tanita (paste o PDF), riconoscimento peso, massa grassa/magra, angolo di fase, TBW, BMI anche su testo incollato "sporco" |
| **Antropometria** | BMR (Mifflin-St Jeor), % grasso (Durnin-Womersley), WHR, FFMI, classificazione |
| **Notifiche** | Configurabili per cliente (riscontro, report, promemoria) con frequenza e canale; il nutrizionista riceve una coda "da inviare" |
| **Messaggi** | Thread locale per cliente |
| **Agenda** | Calendario mensile degli appuntamenti (per cliente o generale) |
| **Acqua & Progressi** | Log idratazione e note di avanzamento |
| **Tema chiaro/scuro** | Toggle persistente |
| **Login locale** | Account nutrizionista (username + password, hash PBKDF2) — nessun server |

Tutti i calcoli derivano da **un solo motore** (`meal_planner.py` / `nutrition_engine.py`):
le viste (diario, piano, riepilogo) sono coerenti tra loro per costruzione.

---

## Installazione

### Opzione A — Scarica la Release (consigliato)
Vai su **Releases** e scarica:
- `NutriCoach-Windows.exe` per Windows
- `NutriCoach-macOS` (o `.zip`) per macOS

Avvia il file: il database viene creato automaticamente in `~/.nutricoach/`.

### Opzione B — Da sorgente (Python 3.11+)
```bash
git clone https://github.com/quadrellif90-collab/NutriCoach.git
cd NutriCoach
pip install -r requirements.txt
python run.py
# apri http://127.0.0.1:8090
```

Al primo avvio imposta il tuo account nutrizionista (username + password) dalla
schermata di login.

---

## Build (sviluppatori)

Il file `NutriCoach.spec` è la configurazione PyInstaller (one-file).
La CI compila automaticamente i binari per Windows e macOS a ogni tag.

```bash
pip install pyinstaller
pyinstaller NutriCoach.spec
# -> dist/NutriCoach.exe (Windows) / dist/NutriCoach (macOS)
```

---

## Struttura

```
app.py              FastAPI + endpoint REST
run.py              entrypoint (uvicorn)
db.py               SQLite (clienti, misure, diete, BIA, appuntamenti...)
nutrition_db.py     database alimenti di riferimento (macro + micro)
nutrition_engine.py calcolo nutrienti / pasti
meal_planner.py     motore unico: aggrega macro+micro, genera piani
bia_parser.py       parsing referti BIA
diet_parser.py      parsing PDF dieta
anthropometry.py    BMR, %grasso, WHR, FFMI
charts.py           grafici SVG offline
pdf_export.py       export PDF (reportlab)
notifications.py    motore notifiche
templates/          dashboard.html (UI)
tests/              pytest
```

---

## Privacy & Licenza

- **100% offline**: nessun invio di dati a server esterni.
- Licenza **MIT** — vedi `LICENSE`.

© 2026 Filippo Siviglia — NutriCoach
