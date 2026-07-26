
## [1.2.0] — 2026-07-25

### Aggiunto
- **Modulo Clinical Nutrition** (`clinical_nutrition.py`): database di 11 condizioni cliniche
  con strategie dietetiche evidence-based (fonti 2024-2026):
  - IBS/FODMAP (3 fasi, 70% responder, umbrella review PMC 2025)
  - GERD/reflusso (dieta anti-reflusso, dieta Mediterranea)
  - Intolleranza lattosio (eliminazione, sostituti, enzimi lattasi)
  - Celiachia (GFD per tutta la vita, ESSCD 2025 guidelines)
  - Sensibilità glutine non celiaca (NCGS)
  - Allergie alimentari IgE-mediate (14 allergeni EU, EAACI 2022)
  - Esofagite Eosinofila (dieta 4FED, ASCIA 2023)
  - Dispepsia funzionale
  - Obesità/sovrappeso
  - Diabete tipo 2
  - Ipertensione (dieta DASH)
  - Osteoporosi
- **Anamnesi cliente**: salva/leggi condizioni cliniche + note
  (`/api/clients/{cid}/anamnesis` GET/POST)
- **Raccomandazioni dietetiche**: genera report personalizzato
  in base alle condizioni del cliente
  (`/api/clinical-nutrition/recommendations`)
- **Check-in settimanale**: peso, compliance, umore, sintomi, energia
  (`/api/clients/{cid}/check-in` GET/POST)
- **Condivisione piano**: PDF esportabile del piano alimentare
  (`/api/clients/{cid}/share-plan`)
- **Endpoint elenco condizioni**: `/api/clinical-nutrition/conditions`
- **Dettaglio condizione**: `/api/clinical-nutrition/conditions/{key}`
# Changelog — NutriCoach

Tutte le versioni significative del progetto. Formato basato su
[Keep a Changelog](https://keepachangelog.com/).

## [1.1.3] — 2026-07-25

### Fix (avvio EXE)
- **EXE che "non parte" se la porta è occupata** (es. vecchia istanza ancora
  aperta): `run.py` ora verifica la porta e, se occupata, prova le porte
  successive (8090→8099) invece di morire silenziosamente.
- **Errori di avvio ora visibili**: in caso di fallimento mostra un
  `messagebox` (TK) invece di chiudersi senza messaggio.
- **Spec PyInstaller robusto**: rimossa la tupla `datas` vuota `('', '')`
  (causa di build fallito in locale) — `tesseract/` è aggiunto solo se esiste.

## [1.1.2] — 2026-07-25

### Fix (critico avvio EXE)
- **Crash all'avvio dell'EXE** (`console=False`): `uvicorn.DefaultFormatter`
  chiamava `sys.stdin.isatty()` ma in EXE `sys.stdin` è `None` →
  `AttributeError` + `ValueError: Unable to configure formatter 'default'`,
  seguito da `RuntimeError: input(): lost sys.stdin`.
  Risolto in `run.py`: wrapper `_SafeStream` che rende `sys.stdin/out/err`
  robusti a `None`, e `UVICORN_LOG_CONFIG` con `logging.Formatter` standard
  (senza `DefaultFormatter`). Verificato: server parte con stdin `/dev/null`
  e risponde HTTP 200.

## [1.1.1] — 2026-07-25

### Fix
- **Deep scan**: `meal_planner.generate_plan` robusto a chiavi target mancanti
  (prima `KeyError 'p'` → HTTP 500 su `/api/clients/{cid}/plan/generate` quando
  il payload era parziale). Ora normalizza `kcal/p/c/f` (accetta anche
  `protein/carbs/fat`) e applica default. Verificato: 47/47 endpoint OK.

## [1.1.0] — 2026-07-25

### Aggiunto
- **OCR reale per PDF scansionati** (dieta + BIA): Tesseract bundlato dentro
  l'EXE/dmg via CI (Windows `choco` + Mac `brew`), con fallback a immagini se
  il binario non è disponibile. Modulo `ocr.py`.
- **Tab "🔬 Scienza Sport"** con strategie pro → amatoriali documentate e
  applicabili (fonti 2024-2026 reali):
  - **A** Distribuzione proteica (1.6–2.2 g/kg, 4–5 pasti, ~3 g leucina; nota
    "mito finestra anabolica 30'").
  - **B** Gut training (protocollo 4 settimane 30→120 g/h, 2:1 glucosio:fruttosio).
  - **C** Periodizzazione a blocchi (fasi → target carb % coerente a FTWR).
  - **D** Creatina (loading 0.3 g/kg × 5–7g, mant. 3–5 g/d; anche donne).
  - **E** Wearable recovery (Oura/WHOOP/Garmin: trend su settimane).
  - FTWR fueling, recovery microcycle (calcio pro), nota chetoni UCI.
- **Report PDF strategie pro** esportabile per cliente (`pdf_sport_science.py`,
  endpoint `/api/clients/{cid}/sport-science-report`).
- **Preset dieto configurabili** nel pianificatore: Mediterranea, Zona 40-30-30,
  CKD, Carb Cycling, Alto Proteico, Vegano, Keto, Personalizzato (macro custom).
- **Selettori Maschio/Femmina + Obiettivo** (`<select>`) in creazione cliente.
- **Riconoscimento testo dieta** corretto (renderer usava `m.items`, ora
  `m.groups`/`m.options` — single source of truth).

### Branding
- Icona app reale (PNG/ICO/ICNS) generata e applicata a EXE, installer NSIS,
  `.app`/`.dmg` e favicon.
- Nome uniformato: **NutriCoach**.

### Tecnico
- `version.py` → `1.1.0`; auto-aggiornamento verifica `releases/latest`.

## [1.0.0] — 2026-07-24

- Rilascio iniziale: dashboard nutrizionista locale (SQLite), import dieta PDF,
  parametri BIA, notifiche/promemoria, login, pianificatore automatico,
  installer Windows (NSIS) + `.dmg` Mac, auto-aggiornamento da GitHub Releases.
