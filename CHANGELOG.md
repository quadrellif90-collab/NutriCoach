# Changelog — NutriCoach

Tutte le versioni significative del progetto. Formato basato su
[Keep a Changelog](https://keepachangelog.com/).

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
