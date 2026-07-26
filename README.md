![NutriCoach](assets/icon.png)

# NutriCoach — Gestione Nutrizione per Nutrizionisti

**Gestionale di nutrizione per nutrizionisti, locale, che chiude il loop tra piano alimentare, misure del corpo (BIA/antropometria) e follow-up del cliente — con diario, pianificazione automatica, appuntamenti e notifiche. Tutto offline.**

![Python](https://img.shields.io/badge/Python-3.11-blue) ![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-green) ![Version](https://img.shields.io/badge/Version-v1.4.3-brightgreen) ![License](https://img.shields.io/badge/License-MIT-blue)

Latest: **[v1.4.3 — Clinical Nutrition (23 condizioni), Pattern Dietetici, Cartella Clinica unificata, Workflow A–E + fix](https://github.com/quadrellif90-collab/NutriCoach/releases/tag/v1.4.3)**

> 🔒 **100% offline.** Nessun dato lascia la macchina. Nessun account remoto. Nessuna sottoscrizione. I dati dei tuoi clienti vivono solo in `~/.nutricoach/` sul tuo computer.

---

**Indice:** [TL;DR](#tldr) · [Perché esiste](#perché-esiste) · [Cosa fa l'app (per area)](#cosa-fa-lapp-per-area) · [Avvio rapido](#avvio-rapido) · [Motore nutrizionale (single source of truth)](#motore-nutrizionale-single-source-of-truth) · [Dieta da PDF & OCR](#dieta-da-pdf--ocr) · [BIA & Antropometria](#bia--antropometria) · [Scienza Sport](#scienza-sport) · [Diario & Pianificatore](#diario--pianificatore) · [Follow-up (Notifiche/Agenda/Messaggi)](#follow-up-notificheagendamessaggi) · [Auto-aggiornamento](#auto-aggiornamento) · [Architettura](#architettura) · [Installer & Release](#installer--release) · [Licenza](#licenza)

> Approfondimento su cosa fa nel dettaglio: [**docs/COSA-FA.md**](docs/COSA-FA.md). Presentazione per clienti/stakeholder: [**PRESENTAZIONE.md**](PRESENTAZIONE.md). Come si fa una release / come funziona l'update: [**docs/AGGIORNAMENTO.md**](docs/AGGIORNAMENTO.md). Changelog: [**CHANGELOG.md**](CHANGELOG.md).

---

## TL;DR

NutriCoach è un gestionale **localhost-only** che:

- Gestisce **clienti** con anagrafica, ricerca e **confronto** tra due clienti (sesso M/F + obiettivo come selettori);
- Importa **diete da PDF** (con gruppi ad alternative + grammature, riconoscimento testo reale; **OCR su PDF scansionati** grazie a Tesseract bundlato), calcola macro/giorno, genera **spesa** e **riepilogo**, esporta in **HTML/PDF**;
- Ha un **diario alimentare** con ricerca alimenti e **aggregazione automatica di macro + micronutrienti** (Calcio, Ferro, Vitamina C, Potassio, Magnesio);
- **Pianifica settimane** bilanciate partendo dai tuoi target (kcal / proteine / carboidrati / grassi) — con **preset dieto configurabili** (Mediterranea, Zona, CKD, Carb Cycling, Alto Proteico, Vegano, Keto, Personalizzato);
- **Tab Scienza Sport** con strategie pro → amatoriali documentate (distribuzione proteica, gut training, periodizzazione a blocchi, creatina, wearable recovery, FTWR, recovery microcycle);
- Importa referti **BIA** (InBody/Tanita) anche da testo incollato "sporco" o PDF scansionato (OCR);
- Calcola **antropometria** (BMR Mifflin-St Jeor, % grasso Durnin-Womersley, WHR, FFMI);
- Tiene **appuntamenti** (calendario), **messaggi** (thread), **acqua** e **note di progresso**;
- Invia **notifiche** configurabili per cliente (riscontro, report, promemoria) con il nutrizionista che riceve una coda "da inviare";
- Ha **login locale** (username + password, hash PBKDF2) e **tema chiaro/scuro**;
- **Si aggiorna da solo** da GitHub Releases (banner + auto-install su Windows).
- **Chiude il loop clinico**: il piano si **filtra automaticamente** per le condizioni del cliente (esclusioni FODMAP/istamina/integratori), la **Cartella Clinica** unifica tutto in un tab, e il **diario** alimenta pattern AI + reintroduzione FODMAP guidata.

Tutti i calcoli derivano da **un solo motore** (`meal_planner.py` / `nutrition_engine.py`): diario, piano e riepilogo sono *viste* coerenti, mai numeri discordanti. Le condizioni cliniche (23) sono la **single source of truth** del filtraggio: da esse derivano esclusioni, integratori e pattern dietetici.

---

## Perché esiste

I software di dietetica in circolazione cadono spesso in due limiti:

- **Cloud obbligatorio**: i dati sensibili dei pazienti finiscono su server di terzi (problema GDPR per il nutrizionista);
- **Fogli di calcolo separati**: dieta, misure e follow-up vivono in file diversi, i numeri non tornano mai tra loro.

NutriCoach nasce per essere l'opposto: **uno strumento proprio, portatile, privato**, dove il motore di calcolo è uno solo e ogni schermata è una vista di quei numeri. Il nutrizionista importa la dieta del cliente, registra le misure, pianifica, e il follow-up (notifiche/appuntamenti) gli ricorda cosa fare — tutto sul suo PC.

---

## Cosa fa l'app (per area)

| Area | Cosa fa | Dove (modulo) |
|------|---------|---------------|
| **Clienti** | Anagrafica, ricerca, confronto tra due clienti, sesso M/F + obiettivo | `db.py`, `app.py` |
| **Clinical Nutrition** | **23 condizioni** (IBS/FODMAP, SIBO, IBD, GERD, celiachia, NCGS, allergie IgE, EoE, lattosio, dispepsia, obesità, T2D, ipertensione, osteoporosi, endometriosi, MASLD, PCOS, istamina…) con strategie evidence-based 2024-2026; **conflitti** tra condizioni, **integratori** e **protocolli phased** (es. FODMAP 3 fasi) | `clinical_nutrition.py`, `app.py` |
| **Pattern Dietetici** | 7 pattern evidence-based (Mediterranea, DASH, MIND, Portfolio, basso IG, RPAH/FAILSAFE, Supporto Barriera) con suggerimento per condizione | `clinical_nutrition.py` (DIET_PATTERNS) |
| **Cartella Clinica** | Vista unificata per cliente: condizioni → conflitti → esclusioni → integratori → fase dieta → sintomi → trend peso | `/api/clients/{cid}/clinical-summary` |
| **Dieta da PDF** | Import con gruppi alternativa + grammature; **OCR su scansioni**; calcolo macro/giorno; spesa; riepilogo; export HTML/PDF | `diet_parser.py`, `ocr.py`, `pdf_export.py`, `nutrition_engine.py` |
| **Diario** | Builder manuale voce-per-voce, ricerca alimenti, **aggregazione automatica macro + micro**; **AI pattern** + **reintroduzione FODMAP guidata** (ordine Monash) | `meal_planner.py`, `nutrition_db.py`, `clinical_nutrition.py` |
| **Pianificatore** | Settimana bilanciata generata dai target (kcal/P/C/F) **filtra automaticamente le esclusioni cliniche** + **preset dieto** + export PDF clinico | `meal_planner.py`, `diet_presets.py`, `pdf_export.py` |
| **BIA** | Parsing referti InBody/Tanita (paste o PDF, anche scansionati/OCR), riconoscimento robusto su testo "sporco" | `bia_parser.py`, `ocr.py` |
| **Antropometria** | BMR (Mifflin-St Jeor), % grasso (Durnin-Womersley), WHR, FFMI, classificazione | `anthropometry.py` |
| **Scienza Sport** | Strategie pro→amatoriali con calcolatori (proteina, gut training, blocchi, creatina, wearable) + report PDF | `sport_science.py`, `pdf_sport_science.py` |
| **Onboarding** | **Wizard anamnesi 3-step** (patologie → allergie → conflitti) che popola il cliente | UI + `/api/clients/{cid}/anamnesis` |
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
makensis /DVERSION=1.3.0 installer.nsi     # -> NutriCoach-Setup-1.4.3.exe

# Build desktop (macOS .dmg) — richiede macOS
pyinstaller NutriCoach.spec --clean --noconfirm
# impacchetta dist/NutriCoach in .app + hdiutil -> NutriCoach-1.4.3.dmg
```

Nessun `.exe` necessario per la modalità web: il backend FastAPI gira e l'interfaccia è HTML nel browser. I dati utente restano in `~/.nutricoach/`.

---

## Motore nutrizionale (single source of truth)

Modulo [`meal_planner.py`](meal_planner.py) + [`nutrition_db.py`](nutrition_db.py) + [`nutrition_engine.py`](nutrition_engine.py). **Un solo motore calcola, gli altri moduli sono viste di quei numeri:**

- **Ricerca alimenti** su ~240 alimenti di riferimento (fonti INRAN/LARN) con match fuzzy (sinonimi, singolare/plurale).
- **Micronutrienti**: ogni alimento porta Calcio, Ferro, Vitamina C, Potassio, Magnesio oltre a macro (kcal, P, C, F, fibra, zuccheri, sale).
- **Aggregazione**: `diary_totals()` somma macro+micro di tutte le voci del diario — niente doppi calcoli.
- **Pianificazione**: `generate_plan(targets)` compone 7 giorni × 5 pasti bilanciati (proteina/carb/verdura/grasso/frutta) vicino ai target.
- **Preset dieto**: `diet_presets.py` espone target macro per tipo di dieta (Mediterranea, Zona, CKD, Carb Cycling, Alto Proteico, Vegano, Keto, Personalizzato).

Tutte le funzioni hanno test (`tests/test_nutricoach.py`).

---

## Dieta da PDF & OCR

[`diet_parser.py`](diet_parser.py) importa piani alimentari. Supporta i **gruppi con alternative** (OR-exclusivi: scegli *un* alimento per gruppo) e le **grammature** per alimento. Da lì: calcolo **macro/giorno**, **lista spesa**, **riepilogo** ed **export** in HTML e PDF.

**OCR reale per PDF scansionati:** se il PDF non ha testo selezionabile, [`ocr.py`](ocr.py) renderizza le pagine e le passa a **Tesseract**, che è **bundlato dentro l'EXE/dmg** (installato in CI via `choco`/`brew`). Se il binario non è disponibile, l'app mostra comunque le immagini per copia manuale.

---

## BIA & Antropometria

[`bia_parser.py`](bia_parser.py) importa misurazioni da referti di bioimpedenziometria:

- **Paste di testo** (anche da PDF scansionato/OCR) o upload PDF nativo;
- estrazione: peso, BMI, massa grassa/magra, acqua totale (TBW), **angolo di fase** (PhA);
- **robusto sul testo "sporco"**: decimali (`75,2` o `75.2`), valori tra parentesi `(75.2)`, PDF a due colonne, numeri confusi con le unità (`m2` non catturato come `2`).

[`anthropometry.py`](anthropometry.py) calcola BMR (Mifflin-St Jeor), % grasso (Durnin-Womersley), WHR, FFMI e li classifica. Test: `tests/test_nutricoach.py` (incluso il parser BIA su casi problematici).

---

## Scienza Sport

Tab **🔬 Scienza Sport**: approcci documentati nel mondo elite (WorldTour ciclismo, calcio pro) resi applicabili ad amatoriale/semi-pro, con calcolatori reali e fonti 2024-2026 citate:

- **A Distribuzione proteica**: 1.6–2.2 g/kg, 4–5 pasti, ~3 g leucina; nota "mito finestra anabolica 30'".
- **B Gut training**: protocollo 4 settimane (30→120 g/h), 2:1 glucosio:fruttosio.
- **C Periodizzazione a blocchi**: fasi → target carb % coerente a FTWR.
- **D Creatina**: loading 0.3 g/kg × 5–7g, mant. 3–5 g/d (anche donne).
- **E Wearable recovery**: Oura/WHOOP/Garmin, trend su settimane.
- FTWR fueling, recovery microcycle (calcio pro), nota chetoni UCI.

Report PDF esportabile per cliente (endpoint `/api/clients/{cid}/sport-science-report`).

---

## Diario & Pianificatore

- **Diario**: aggiungi voci (alimento + grammi) e il motore aggrega macro + micro in tempo reale. Puoi usare gli alimenti di riferimento o aggiungerne di personalizzati (`foods_custom`).
- **Pianificatore**: inserisci i target (kcal / P / C / F) o scegli un **preset dieto**; ottieni una settimana di pasti bilanciati, pronta da mostrare o adattare al cliente.

---

## Follow-up (Notifiche/Agenda/Messaggi)

- **Notifiche**: per ogni cliente scegli *quali* messaggi inviare (riscontro settimanale, promemoria report, ecc.), su che canale e con che frequenza. Il nutrizionista vede una **coda "da inviare"** generata automaticamente dalle scadenze. (L'invio reale via WhatsApp/Email è futuro: oggi sono hook locali, nessun dato esce.)
- **Agenda**: calendario mensile degli appuntamenti, per cliente o generale; click su un giorno per aggiungerne uno.
- **Messaggi**: thread locale per cliente (simula la conversazione; nessun cloud).

---

## Architettura

- `app.py` — backend FastAPI (tutti gli endpoint REST, inclusi `/api/self-update/*`)
- `run.py` — entrypoint (uvicorn, apre il browser, log su file, check update all'avvio)
- `db.py` — SQLite (`~/.nutricoach/nutricoach.db`): clienti, misure, diete, BIA, appuntamenti, messaggi, acqua, note
- `nutrition_db.py` — database alimenti di riferimento (macro + micro)
- `nutrition_engine.py` — calcolo nutrienti / pasti
- `meal_planner.py` — **motore unico**: aggrega macro+micro, genera piani
- `diet_parser.py` / `bia_parser.py` — import referti (+ `ocr.py` per scansioni)
- `diet_presets.py` — preset dieto configurabili
- `sport_science.py` / `pdf_sport_science.py` — strategie pro + report PDF
- `anthropometry.py` — BMR, %grasso, WHR, FFMI
- `charts.py` — grafici SVG offline
- `pdf_export.py` — export PDF (reportlab)
- `notifications.py` — motore notifiche
- `auth.py` — login locale (PBKDF2)
- `version.py` — versione app (auto-update)
- `templates/dashboard.html` — UI (italiano, tema chiaro/scuro)
- `assets/icon.png` + `icon.ico` + `icon.icns` — branding
- `.github/workflows/build.yml` — CI: build Win (exe + installer NSIS, Tesseract bundlato) e Mac (.dmg) su tag

Dati in `~/.nutricoach/`; **nessun cloud**.

---

## Auto-aggiornamento

NutriCoach verifica all'avvio l'ultima release su GitHub (`releases/latest`) e, se è più nuova di `version.py`, mostra un banner "Aggiornamento disponibile". Su **Windows** l'installer si lancia in silenzioso (`/S`) e l'app si riavvia; su **Mac** il banner segnala la novità e l'utente trascina il `.app` nel dmg. I dati in `~/.nutricoach/` **non vengono mai toccati**. Dettagli per sviluppatori in [**docs/AGGIORNAMENTO.md**](docs/AGGIORNAMENTO.md).

---

## Installer & Release

| Piattaforma | Asset | Note |
|---|---|---|
| Windows | `NutriCoach-Setup-<ver>.exe` (installer NSIS) | doppio click → Program Files + scorciatoie + icona |
| Windows | `NutriCoach.exe` (portatile) | estrai e avvia, nessuna installazione |
| macOS | `NutriCoach-<ver>.dmg` | apri e trascina in Applicazioni |

Vedi [**Releases**](https://github.com/quadrellif90-collab/NutriCoach/releases).

> **macOS**: l'app non è firmata/notarizzata da Apple. Al primo avvio, se compare "app non può essere aperta", fai click destro → **Apri**, oppure da Terminale: `xattr -dr com.apple.quarantine /Applications/NutriCoach.app`.

---

## Licenza

MIT — vedi [`LICENSE`](LICENSE).

© 2026 Filippo Siviglia — NutriCoach. Costruito localmente, per nutrizionisti che vogliono i propri dati sul proprio computer.
