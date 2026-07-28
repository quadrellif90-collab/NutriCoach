# Changelog

## v2.20.0 (2026-07-28) — 🏁 Completo! Tutte 22/22 feature

### Nuove feature
- **⚖️ Bilance impedenziometriche** — tabella `scale_measurements`, CRUD, form manuale, trend (peso, BF%, muscolo, acqua, VF, BMR, età metabolica)
- **⌚ Wearable Garmin/Fitbit** — tabella `wearable_data`, CRUD, 8 metriche (passi, FC media/riposo, sonno, stress, calorie attive)
- **🏃 Fitness import (Strava/TrainingPeaks)** — tabella `fitness_imports`, CRUD, 8 categorie attività (corsa, bici, nuoto, camminata...)
- **🎓 Onboarding tour** — overlay interattivo 3 passi al primo login (localStorage `onboarding_done`)
- **💡 Tooltip** — 10 `title` informativi su nav e bottoni (Dashboard, Pazienti, Dieta, Ricettario, Notifiche, Tema...)
- **🏷️ Brand nel PDF** — tutti i PDF includono logo studio, nome clinica e colore tema (letti dalle impostazioni utente)
- **📄 Export piano dal portale paziente** — nuovo endpoint `/api/portal/{token}/pdf` + bottone "📄 Scarica PDF"

### Miglioramenti
- `ensure_v2_tables()` aggiornata con tutte le 3 nuove tabelle per upgrade automatico
- Gestione fallback colore tema nei PDF (anche con `#000` o valori vuoti)
- UI paziente: 19 tab (aggiunti ⚖️ Bilancia, ⌚ Wearable, 🏃 Fitness)

### Dettaglio file
- `app/main.py` — 6 nuovi endpoint (scale, wearable, fitness CRUD + portal PDF) + versione 2.20.0
- `app/database.py` — 9 nuove funzioni CRUD + tabelle in `ensure_v2_tables()`
- `app/diet_pdf.py` — brand (logo, nome, colore) in tutti i PDF
- `app/templates/index.html` — 3 tab, onboarding, tooltip, int/float helper
- `app/templates/portal.html` — bottone export PDF

---

## v2.17.0 (2026-07-27) — 🔔 Notifiche in-app + Desktop

### Nuove feature
- **🔔 Notifiche in-app** — tabella `app_notifications` con CRUD, API REST
- **🖥️ Notifiche desktop native** — campanella 🔔 nella nav con badge unread, dropdown notifiche, polling ogni 15s
- **🤖 Auto-notifica** — notifica automatica generata su nuovo messaggio paziente in chat

### Dettaglio
- `app/database.py`: tabella `app_notifications`, funzioni add/list/mark/count
- `app/main.py`: 4 endpoint notifiche, hook su messaggio
- `app/templates/index.html`: campanella, badge, dropdown, notifiche desktop API, polling

---

## v2.16.0 (2026-07-27) — 📝 Check pasti + Self-report + Chat

### Nuove feature
- **✅ Check pasti consumati** — tabella `meal_diary`, API CRUD, UI tab 📝 con pulsanti consumato/non consumato
- **📊 Self-reporting** — mood, fame, soddisfazione per ogni pasto (emoji picker)
- **💬 Chat paziente** — tabella `messages`, API messaggi con invio/ricezione, UI stile bubble chat
- **📅 Appuntamenti** — full CRUD (tabella, API, UI)

### Dettaglio
- `app/database.py`: tabelle `meal_diary`, `messages`, funzioni CRUD
- `app/main.py`: endpoint check pasti, self-report, messaggi, appuntamenti
- `app/templates/index.html`: tab Diario con past tracker, tab Chat con bubble

---

## v2.15.0 (2026-07-26) — 💊 Farmaci + Questionari

### Nuove feature
- **💊 Gestione farmaci** — tabella `medications`, API CRUD, interazioni farmaco-nutriente
- **📋 Questionari clinici** — tabella `quiz_questions` + `quiz_answers`, admin edit, compilazione paziente
- **🔄 Auto-migrazione** — `ensure_v2_tables()` aggiornata per upgrade automatico

---

## v2.14.0 (2026-07-26) — 🌐 Multi-lingua + Allergeni

### Nuove feature
- **🌐 Traduzioni** — piano alimentare in lingua del paziente (italiano/inglese)
- **⚠️ Allergeni** — gestione allergie/intolleranze nel profilo paziente, avvisi visivi
- **🏷️ Etichette HFSS** — alert su alimenti ad alto contenuto di grassi/zuccheri/sale

---

## v2.13.0 (2026-07-25) — 📈 Dashboard + Aderenza

### Nuove feature
- **📊 Dashboard aderenza** — percentuale pasti consumati, heatmap settimanale
- **📈 Trend visuali** — evoluzione peso/BF/PhA nel tempo con grafici SVG
- **🎯 Obiettivi paziente** — target calorici adattivi

---

## v2.12.0 (2026-07-24) — 📊 Radar chart + Performance

### Nuove feature
- **🕸️ Radar chart** — confronto FFMI/FMI/BFM/Hydration/SMM
- **📊 Dashboard performance** — panoramica paziente con metriche chiave
- **📈 Confronto multi-tempo** — ultima BIA vs media storica

---

## v2.11.0 (2026-07-23) — 📖 Ricettario + Swap

### Nuove feature
- **📖 Ricettario personale** — tabella `recipes`, CRUD, ingredienti con grammatura, ricerca
- **🔄 Swap automatico alimenti** — API `/api/foods/{fid}/swaps`, equivalenze nutrizionali
- **📄 Lista spesa** — aggregata per ricetta con grammatura totale

---

## v2.10.0 (2026-07-22) — 🗂️ Backup automatico

### Nuove feature
- **💾 Backup giornaliero automatico** all'avvio in `~/.nutricoach/backups/`
- **📤 Export CSV** di tutti i pazienti
- **📥 Import paziente** da JSON (BIA, dieta, appuntamenti, documenti)
- **📋 Statistics studio** — endpoint `/api/stats`

---

## v2.9.0 (2026-07-21) — 📐 Template + Tema

### Nuove feature
- **📐 Template dieta** — tabella `diet_templates`, 5 preset (mediterraneo, zona, chetogenico, vegano, CKD)
- **🌗 Tema chiaro/scuro** — toggle in navbar, persistito in localStorage
- **🎨 CSS completo** — `style.css` con variabili CSS per tema

---

## v2.8.0 (2026-07-20) — 🔐 Backup + Export

### Nuove feature
- **🗄️ Backup manuale** via endpoint API
- **📄 Export/Import JSON** paziente completo
- **📊 Export CSV** lista pazienti

---

## v2.7.0 (2026-07-19) — 🌍 Portale Paziente

### Nuove feature
- **🔗 Portale paziente** — vista read-only via link protetto (`secrets.token_urlsafe`)
- **📱 Mobile-friendly** — template `portal.html` responsive
- **🛡️ Zero esposizione dati sensibili** — solo piano alimentare visibile

---

## v2.6.0 (2026-07-18) — 📊 Grafici BIA + Report PDF

### Nuove feature
- **📈 Grafici evolutivi** — 7 metriche BIA (peso, BF%, MM%, TBW, ECW/ICW, PhA, SMM)
- **📄 Report PDF BIA** — `generate_bia_report_pdf()` con sparkline SVG
- **📊 Confronto multi-misurazione** — overlay dati storici

---

## v2.5.0 (2026-07-17) — 🛒 Lista Spesa

### Nuove feature
- **🛒 Lista spesa automatica** — aggregata dal piano alimentare
- **📁 Raggruppamento per categoria** alimenti
- **📄 Export PDF lista spesa** — `generate_shopping_pdf()`

---

## v2.4.0 (2026-07-16) — ⚡ Fabbisogno Calorico

### Nuove feature
- **⚡ Calcolo BMR** con 3 formule: Mifflin-St Jeor, Harris-Benedict, Katch-McArdle
- **📊 TDEE** con 5 livelli di attività
- **🎯 Target kcal** per obiettivo (dimagrimento −15%, massa +10%, performance +5%)
- **🧮 Endpoint** `POST /api/diet-presets/targets`

---

## v2.3.0 (2026-07-15) — 📄 Export PDF Piano

### Nuove feature
- **📄 PDF professionale** — `DietPDF` class con header, tabella 7×5, macro giornalieri
- **📋 Raccomandazioni** — sezione personalizzata nel PDF
- **🚫 Alimenti esclusi** — lista alimenti da evitare
- **📊 Tabella nutrizionale** — kcal totali, distribuzione %, micronutrienti

---

## v2.2.0 (2026-07-14) — 🥗 Database Alimenti

### Nuove feature
- **🥗 Database alimenti** — 212 prodotti italiani (INRAN/CREA)
- **🏷️ Categorie** — 11 categorie (latticini, carni, pesce, cereali, legumi, verdure, frutta, frutta secca, grassi, bevande, varie)
- **🔍 Ricerca** — endpoint `/api/foods`, autocomplete, filtri per categoria
- **📊 Valori completi** — kcal, proteine, grassi, carboidrati, fibre, zuccheri, sale per 100g

---

## v2.1.0 (2026-07-13) — 🔍 OCR Engine

### Nuove feature
- **🔍 OCR BIA** — `app/ocr_engine.py` con Windows.Media.Ocr (API nativa Windows 10/11)
- **📄 Estrazione 14 campi** da PDF AKERN: peso, altezza, BMI, FM, BF%, FFM, TBW, ECW, ICW, BCM, SMM, ASMM, PhA, Idratazione
- **🔄 Fallback Tesseract** — se `winsdk` non disponibile
- **📤 Upload PDF** — endpoint `POST /api/patients/{pid}/bia-ocr`

---

## v2.0.0 (2026-07-12) — 🎉 Versione Iniziale

### Nuove feature
- **🏗️ Architettura FastAPI** con SQLite
- **👥 CRUD pazienti** con anamnesi
- **📐 Modello Dietowin-style** — data aggregator pattern
- **🔐 Login amministratore** con sessione e hash SHA-256
- **📦 Base UI index.html** con template Jinja2