![NutriCoach](assets/icon.svg)

# NutriCoach — Gestione Nutrizione per Nutrizionisti

**Gestionale di nutrizione per nutrizionisti, locale, che chiude il loop tra piano alimentare, misure del corpo (BIA/antropometria) e follow-up del cliente — con diario, pianificazione automatica, appuntamenti e notifiche. Tutto offline.**

![Python](https://img.shields.io/badge/Python-3.11-blue) ![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-green) ![Version](https://img.shields.io/badge/Version-v1.0.0-brightgreen) ![License](https://img.shields.io/badge/License-MIT-blue)

Latest: **[v1.0.0 — Diario+micro, Pianificatore, Agenda, Notifiche, installer Win/Mac](https://github.com/quadrellif90-collab/NutriCoach/releases/tag/v1.0.0)**

> 🔒 **100% offline.** Nessun dato lascia la macchina. Nessun account remoto. Nessuna sottoscrizione. I dati dei tuoi clienti vivono solo in `~/.nutricoach/` sul tuo computer.

---

**Indice:** [TL;DR](#tldr) · [Perché esiste](#perché-esiste) · [Cosa fa l'app (per area)](#cosa-fa-lapp-per-area) · [Avvio rapido](#avvio-rapido) · [Motore nutrizionale (single source of truth)](#motore-nutrizionale-single-source-of-truth) · [Dieta da PDF](#dieta-da-pdf) · [BIA & Antropometria](#bia--antropometria) · [Diario & Pianificatore](#diario--pianificatore) · [Follow-up (Notifiche/Agenda/Messaggi)](#follow-up-notificheagendamessaggi) · [Architettura](#architettura) · [Installer & Release](#installer--release) · [Licenza](#licenza)

> Approfondimento su cosa fa nel dettaglio: [**docs/COSA-FA.md**](docs/COSA-FA.md). Presentazione per clienti/stakeholder: [**PRESENTAZIONE.md**](PRESENTAZIONE.md).

---

## TL;DR

NutriCoach è un gestionale **localhost-only** che:

- Gestisce **clienti** con anagrafica, ricerca e **confronto** tra due clienti;
- Importa **diete da PDF** (con gruppi ad alternative + grammature), calcola macro/giorno, genera **spesa** e **riepilogo**, esporta in **HTML/PDF**;
- Ha un **diario alimentare** con ricerca alimenti e **aggregazione automatica di macro + micronutrienti** (Calcio, Ferro, Vitamina C, Potassio, Magnesio);
- **Pianifica settimane** bilanciate partendo dai tuoi target (kcal / proteine / carboidrati / grassi) — stile "auto meal generator";
- Importa referti **BIA** (InBody/Tanita) anche da testo incollato "sporco" (decimali, parentesi, due colonne);
- Calcola **antropometria** (BMR Mifflin-St Jeor, % grasso Durnin-Womersley, WHR, FFMI);
- Tiene **appuntamenti** (calendario), **messaggi** (thread), **acqua** e **note di progresso**;
- Invia **notifiche** configurabili per cliente (riscontro, report, promemoria) con il nutrizionista che riceve una coda "da inviare";
- Ha **login locale** (username + password, hash PBKDF2) e **tema chiaro/scuro**.

Tutti i calcoli derivano da **un solo motore** (`meal_planner.py` / `nutrition_engine.py`): diario, piano e riepilogo sono *viste* coerenti, mai numeri discordanti.

---

## Perché esiste

I software di dietetica in circolazione cadono spesso in due limiti:

- **Cloud obbligatorio**: i dati sensibili dei pazienti finiscono su server di terzi (problema GDPR per il nutrizionista);
- **Fogli di calcolo separati**: dieta, misure e follow-up vivono in file diversi, i numeri non tornano mai tra loro.

NutriCoach nasce per essere l'opposto: **uno strumento proprio, portabile, privato**, dove il motore di calcolo è uno solo e ogni schermata è una vista di quei numeri. Il nutrizionista importa la dieta del cliente, registra le misure, pianifica, e il follow-up (notifiche/appuntamenti) gli ricorda cosa fare — tutto sul suo PC.

---

## Cosa fa l'app (per area)

| Area | Cosa fa | Dove (modulo) |
|------|---------|---------------|
| **Clienti** | Anagrafica, ricerca, confronto tra due clienti | `db.py`, `app.py` |
| **Dieta da PDF** | Import con gruppi alternativa + grammature; calcolo macro/giorno; spesa; riepilogo; export HTML/PDF | `diet_parser.py`, `pdf_export.py`, `nutrition_engine.py` |
| **Diario** | Builder manuale voce-per-voce, ricerca alimenti, **aggregazione automatica macro + micro** | `meal_planner.py`, `nutrition_db.py` |
| **Pianificatore** | Settimana bilanciata generata dai target (kcal/P/C/F) | `meal_planner.py` |
| **BIA** | Parsing referti InBody/Tanita (paste o PDF), riconoscimento robusto anche su testo "sporco" | `bia_parser.py` |
| **Antropometria** | BMR (Mifflin-St Jeor), % grasso (Durnin-Womersley), WHR, FFMI, classificazione | `anthropometry.py` |
| **Notifiche** | Configurabili per cliente (riscontro/report/promemoria) con frequenza e canale; coda "da inviare" | `notifications.py` |
| **Messaggi** | Thread locale per cliente | `db.py` |
| **Agenda** | Calendario mensile appuntamenti (per cliente o generale) | `db.py`, UI |
| **Acqua & Progressi** | Log idratazione e note di avanzamento | `db.py` |
| **Login / Tema** | Account nutrizionista (PBKDF2), toggle chiaro/scuro persistente | `auth.py`, UI |

Il dettaglio di ogni area (flusso, formule, endpoint) è in [**docs/COSA-FA.md**](docs/COSA-FA.md).

---

## Avvio rapido

```bash
# Sviluppo / web app
pip install -r requirements.txt
python run.py                 # apre http://127.0.0.1:8090 nel browser

# Build desktop (EXE Windows) + installer NSIS
pyinstaller NutriCoach.spec --clean --noconfirm
makensis /DVERSION=1.0.0 installer.nsi     # -> NutriCoach-Setup-1.0.0.exe

# Build desktop (macOS .dmg) — richiede macOS
pyinstaller NutriCoach.spec --clean --noconfirm
# impacchetta dist/NutriCoach in .app + hdiutil -> NutriCoach-1.0.0.dmg
```

Nessun `.exe` necessario per la modalità web: il backend FastAPI gira e l'interfaccia è HTML nel browser. I dati utente restano in `~/.nutricoach/`.

---

## Motore nutrizionale (single source of truth)

Modulo [`meal_planner.py`](meal_planner.py) + [`nutrition_db.py`](nutrition_db.py) + [`nutrition_engine.py`](nutrition_engine.py). **Un solo motore calcola, gli altri moduli sono viste di quei numeri:**

- **Ricerca alimenti** su ~240 alimenti di riferimento (fonti INRAN/LARN) con match fuzzy (sinonimi, singolare/plurale).
- **Micronutrienti**: ogni alimento porta Calcio, Ferro, Vitamina C, Potassio, Magnesio oltre a macro (kcal, P, C, F, fibra, zuccheri, sale).
- **Aggregazione**: `diary_totals()` somma macro+micro di tutte le voci del diario — niente doppi calcoli.
- **Pianificazione**: `generate_plan(targets)` compone 7 giorni × 5 pasti bilanciati (proteina/carb/verdura/grasso/frutta) vicino ai target.

Tutte le funzioni hanno test (`tests/test_nutricoach.py`).

---

## Dieta da PDF

[`diet_parser.py`](diet_parser.py) importa piani alimentari. Supporta i **gruppi con alternative** (OR-exclusivi: scegli *un* alimento per gruppo, e il conteggio tiene conto di una sola opzione) e le **grammature** per alimento. Da lì:

- calcolo **macro/giorno** (`nutrition_engine.py`);
- **lista spesa** aggregata;
- **riepilogo** e **export** in HTML e PDF (`pdf_export.py`, reportlab).

---

## BIA & Antropometria

[`bia_parser.py`](bia_parser.py) importa misurazioni da referti di bioimpedenziometria:

- **Paste di testo** (anche da PDF scansionato/OCR) o upload PDF nativo;
- estrazione: peso, BMI, massa grassa/magra, acqua totale (TBW), **angolo di fase** (PhA);
- **robusto sul testo "sporco"**: decimali (`75,2` o `75.2`), valori tra parentesi `(75.2)`, PDF a due colonne, numeri confusi con le unità (`m2` non catturato come `2`).

[`anthropometry.py`](anthropometry.py) calcola BMR (Mifflin-St Jeor), % grasso (Durnin-Womersley), WHR, FFMI e li classifica. Test: `tests/test_nutricoach.py` (incluso il parser BIA su casi problematici).

---

## Diario & Pianificatore

- **Diario**: aggiungi voci (alimento + grammi) e il motore aggrega macro + micro in tempo reale. Puoi usare gli alimenti di riferimento o aggiungerne di personalizzati (`foods_custom`).
- **Pianificatore**: inserisci i target (kcal / P / C / F) e ottieni una settimana di pasti bilanciati, pronta da mostrare o adattare al cliente.

---

## Follow-up (Notifiche/Agenda/Messaggi)

- **Notifiche**: per ogni cliente scegli *quali* messaggi inviare (riscontro settimanale, promemoria report, ecc.), su che canale e con che frequenza. Il nutrizionista vede una **coda "da inviare"** generata automaticamente dalle scadenze. (L'invio reale via WhatsApp/Email è futuro: oggi sono hook locali, nessun dato esce.)
- **Agenda**: calendario mensile degli appuntamenti, per cliente o generale; click su un giorno per aggiungerne uno.
- **Messaggi**: thread locale per cliente (simula la conversazione; nessun cloud).

---

## Architettura

- `app.py` — backend FastAPI (tutti gli endpoint REST)
- `run.py` — entrypoint (uvicorn, apre il browser, log su file)
- `db.py` — SQLite (`~/.nutricoach/nutricoach.db`): clienti, misure, diete, BIA, appuntamenti, messaggi, acqua, note
- `nutrition_db.py` — database alimenti di riferimento (macro + micro)
- `nutrition_engine.py` — calcolo nutrienti / pasti
- `meal_planner.py` — **motore unico**: aggrega macro+micro, genera piani
- `bia_parser.py` / `diet_parser.py` — import referti
- `anthropometry.py` — BMR, %grasso, WHR, FFMI
- `charts.py` — grafici SVG offline
- `pdf_export.py` — export PDF (reportlab)
- `notifications.py` — motore notifiche
- `auth.py` — login locale (PBKDF2)
- `templates/dashboard.html` — UI (italiano, tema chiaro/scuro)
- `.github/workflows/build.yml` — CI: build Win (exe + installer NSIS) e Mac (.dmg) su tag

Dati in `~/.nutricoach/`; **nessun cloud**.

---

## Installer & Release

| Piattaforma | Asset | Note |
|---|---|---|
| Windows | `NutriCoach-Setup-<ver>.exe` (installer NSIS) | doppio click → Program Files + scorciatoie |
| Windows | `NutriCoach.exe` (portatile) | estrai e avvia, nessuna installazione |
| macOS | `NutriCoach-<ver>.dmg` | apri e trascina in Applicazioni |

Vedi [**Releases**](https://github.com/quadrellif90-collab/NutriCoach/releases).

> **macOS**: l'app non è firmata/notarizzata da Apple. Al primo avvio, se compare "app non può essere aperta", fai click destro → **Apri**, oppure da Terminale: `xattr -dr com.apple.quarantine /Applications/NutriCoach.app`.

---

## Licenza

MIT — vedi [`LICENSE`](LICENSE).

© 2026 Filippo Siviglia — NutriCoach. Costruito localmente, per nutrizionisti che vogliono i propri dati sul proprio computer.
