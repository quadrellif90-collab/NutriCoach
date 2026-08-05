# AUTO MEMORIES INDEX — NutriCoach v2.20.16

> **Generated**: 2026-08-05 | **Branch**: `master` | **Version**: 2.20.16 (app/git tag allineati)
> **Repo**: `quadrellif90-collab/NutriCoach` | **Status**: 🟢 Production-ready — release v2.20.16 pubblicata

---

## 📂 FULL PROJECT TREE

```
NutriCoach/
├── app/                          # FastAPI backend package (V2)
│   ├── main.py                   # 🎯 124 REST endpoints + global exception handler
│   ├── database.py               # SQLite schema + CRUD (24 tables)
│   ├── bia_parser_v2.py          # BIA OCR parsing v2
│   ├── diet_pdf.py               # PDF report generation
│   ├── energy_calc.py            # Calorie/BMR/TDEE (age_from_birth, bmr_mifflin)
│   ├── ocr_engine.py             # Windows OCR + Tesseract fallback (parse_bia_pdf: testo nativo → OCR)
│   ├── ocr_pdf.py                # PDF OCR pipeline
│   ├── zai_ocr.py                # z.ai OCR (import da main)
│   ├── static/
│   │   └── style.css             # SPA stylesheet (breakpoint 1100/900/768, modal fit-content)
│   └── templates/
│       ├── index.html            # 📄 SPA — all UI + JS (1726 lines, vanilla JS, 0 CDN)
│       └── portal.html           # Patient portal
├── tests/
│   └── test_nutricoach.py        # 25 test cases
├── templates/                    # Legacy dashboard.html (v1)
├── assets/                       # icon.ico / .icns / .png / .svg
├── tesseract/                    # Bundled Tesseract + tessdata (ita, eng)
├── .github/workflows/
│   └── build.yml                 # CI: build+release su tag v* (~22min, Windows+macOS, Tesseract bundled)
├── requirements.txt              # fastapi, uvicorn, python-multipart, PyMuPDF, reportlab, pytesseract, Pillow, pywebview, pyinstaller
├── version.py                    # Versione
├── run.py                        # Dev runner (porta 8090)
├── run_v2.py                     # Runner esplicito (porta 8400)
├── launcher.py / launcher_v2.py  # Desktop native window launcher
├── release_validator.sh          # Release validator
├── RELEASE_CERTIFICATE.md        # Certificato release
├── BUG_REPORT_LATEST.md          # Bug report QA
├── MEMORY.md                     # Questo file
├── CHANGELOG.md                  # Changelog completo
└── *.py (root)                   # Moduli legacy (clinical_nutrition, meal_planner, bia_analysis, etc.)
```

---

## ⚙️ CORE ARCHITECTURE

| Aspect | Detail |
|--------|--------|
| **Framework** | FastAPI + uvicorn |
| **Host/Port** | `127.0.0.1:8400` (v2 runner) / `8090` (legacy) |
| **API Base** | `/api/` — **124 route** (GET ~50, POST ~55, PUT, PATCH, DELETE) |
| **Auth** | Auto-login all'avvio (main.py ~1448), niente login richiesto; Setup Wizard silenzioso (cartella predefinita) |
| **Static Mount** | `/static` → `app/static/` |
| **DB** | SQLite in `~/.nutricoach/nutricoach.db` — ⚠️ WAL non checkpointato: si svuota tra riavvii uvicorn se non si fa checkpoint |

### API Route Highlights (v2.20.16)
| Modulo | Route principali |
|--------|------------------|
| **Import BIA** | `POST /api/patients/{pid}/import`, `POST /api/patients/{pid}/import/confirm`, `POST /api/ocr/local/process` (OCR locale: testo nativo → Windows OCR/Tesseract, asyncio.to_thread), `/api/ocr/zai/*` (z.ai cloud) |
| **Plan** | `POST /api/patients/{pid}/plan/generate` (piani su misura, patologie) |
| **BIA/Radar** | `GET /api/patients/{pid}/body-composition`, `/radar`, `/bia-trend`, `/energy-needs` |
| **Dieta** | `/api/patients/{pid}/diet-macros/{day}`, `/diet/pdf`, `/shopping-list`, `/diet-templates` |
| **Foods** | `/api/foods`, `/api/foods/categories`, `/api/foods/{fid}/swaps` |
| **Recipes** | `/api/recipes` CRUD + `/apply` |
| **Portal** | `/portal/{token}`, `/api/portal/{token}/data|pdf`, `POST /api/patients/{pid}/portal-token` |
| **Scale/Wearable/Fitness** | CRUD `/api/patients/{pid}/scale|wearable|fitness` |
| **Export/Backup** | `/api/export/patients`, `/api/export/patient/{pid}`, `/api/import/patient`, `/api/backup`, `/api/backup/auto` |
| **Version** | `GET /api/version` → `{"version":"2.20.16","platform":"win32"}` |

---

## 🗄️ DATABASE SCHEMA (app/database.py)

| Table | Purpose |
|-------|---------|
| `patients` | Profili (name, sex, birth_date, goal, sport, pathologies, language, height) |
| `bia_readings` | Misurazioni BIA (weight, pha, hydration, muscle, bmr, tbw, ecw, icw, ffm, smm, asmm, bcm, bf_pct…) |
| `measurements` | Antropometria (weight_kg, waist_cm, hip_cm, skinfolds) |
| `anthropometry` | Antropometria v2 |
| `diet_plans` / `diet_items` | Piani alimentari + item |
| `diet_templates` | Template preset |
| `food_catalog` | Database alimenti (kcal, protein, fat, carbs, fiber, sugars, salt) |
| `recipes` | Ricettario (ingredients JSON) |
| `appointments` | Appuntamenti |
| `notifications` / `app_notifications` | Notifiche |
| `documents` | File upload (BLOB) |
| `symptoms` / `progress_notes` | Clinico |
| `categories` / `groups_t` / `patient_groups` | Grouping |
| `_app_version` | Version tracker |

---

## 🎨 FRONTEND SPA (app/templates/index.html)

- **1726 righe**, vanilla JS inline (0 CDN), Chart.js NON usato (SVG custom)
- **Functions core**: `qs/qsa/toast/jget/jpost/jdel/jpatch/esc`, `modal/closeModal/showConfirm`
- **UI scale**: `ncApplyZoom` — scala automatica in base alla larghezza finestra (w/1440, clamp 0.8–1.2), resize listener `ncOnResize`; NIENTE zoom manuale a percentuali (rimosso in v2.20.16)
- **Modali**: `width:fit-content` + `max-width:min(94vw,640px)` + `overflow-wrap:anywhere` (auto-size al testo, word-wrap testi lunghi); su ≤768px fullscreen + `min-width:0!important`
- **Sidebar**: divisore trascinabile (`sidebar-resizer`, persistito localStorage)
- **Side panel**: `#side-panel` paziente fisso + toggle (`toggleSidePanel`/`refreshSidePanel`, localStorage `nc-side-panel`)
- **Dashboard widget**: personalizzabili (Ultimi pazienti/Trend/Statistiche)
- **Import OCR locale**: `localOCRSubmit(file)` → POST multipart → anteprima DIRECT (bypass testo intermedio — fix v2.20.16: prima passava da testo→import e perdeva campi)
- **Setup Wizard**: silenzioso (backup dir predefinita, nessuna UI)
- **pccConfirm-style**: `showConfirm` per conferme

---

## 🔌 CRITICAL MODULES (root *.py)

| Module | Purpose |
|--------|---------|
| `clinical_nutrition.py` | Knowledge base condizioni cliniche + raccomandazioni |
| `nutrition_db.py` | DB alimenti italiani |
| `meal_planner.py` | Generatore piani |
| `bia_analysis.py` | Analisi BIA — espone `calculate(d, info)` (dict diretto) e `summarize()` |
| `bia_parser.py` / `app/bia_parser_v2.py` | Parser testo BIA |
| `charts.py` | SVG chart |
| `pdf_export.py` / `pdf_sport_science.py` | PDF report |
| `auth.py` | Auth legacy |
| `ocr.py` / `app/ocr_engine.py` | OCR pipeline |

---

## 🧪 TEST & VERIFICA

| Tipo | Comando | Note |
|------|---------|------|
| Unit | `PYTHONPATH=. pytest tests/ -q` | 25 test (brace balance, node --check JS, parser) |
| JS | `python -c "import re; ...extract <script>..." + node --check` | Estrarre script inline da index.html |
| E2E OCR | POST `/api/ocr/local/process` con PDF Bodygram | 14 campi: peso 71.4, PhA 7.4, TBW 43.0, BF% 20.4 |
| HTTP | `curl -s http://127.0.0.1:8400/api/version` | Health check |

---

## 🔐 SECURITY & CONFORMANCE

- Auth: auto-login (overlay nascosto), SHA-256 hash
- CORS: localhost only
- XSS: `esc()` su tutto l'output utente
- Nessun secret hardcoded
- Dati 100% offline (SQLite locale)

---

## 🏷️ VERSION HISTORY (recenti)

| Tag | Descrizione |
|-----|-------------|
| `v2.20.16` | OCR locale fix (bypass testo intermedio, 14 campi), PDF testo nativo pre-OCR, auto-scale UI, modal fit-content |
| `v2.20.15` | UX fase 2: wizard silenzioso, zoom font (poi rimosso), responsive, modali resize, widget pannello+dashboard |
| `v2.20.14` | Import BIA Bodygram OCR locale + finestra dati mancanti (BMR Mifflin), radar verificato |

---

*Aggiornato: 2026-08-05 — release master v2.20.16*
