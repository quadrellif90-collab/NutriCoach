# NutriCoach

**Gestionale di nutrizione professionale per nutrizionisti** — locale, offline, completo.

![Version](https://img.shields.io/badge/Version-2.20.0-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-green)
![License](https://img.shields.io/badge/License-MIT-blue)

> 🔒 **100% offline.** Nessun dato lascia il tuo computer. I dati dei pazienti vivono solo in `~/.nutricoach/nutricoach.db`.

---

## 📋 Panoramica

NutriCoach v2 è un gestionale **localhost-only** stile Dietowin/Nutrium che copre l'intero flusso di lavoro del nutrizionista:

| Fase | Cosa fa |
|------|---------|
| **📥 Acquisizione** | Import BIA da PDF (OCR automatico), anamnesi, questionari, dati wearable |
| **📊 Analisi** | Fabbisogno calorico, FFMI/FMI, metabolismo, trend, radar chart |
| **🍽️ Piano** | Generazione automatica, template personalizzabili, grammatura, swap alimenti, ricettario |
| **📄 Consegna** | PDF professionale brandizzato, portale paziente, lista spesa |
| **📱 Follow-up** | Chat, diario pasti, self-report, notifiche push/desktop, appuntamenti |
| **⚙️ Studio** | Multi-utente, brand personalizzato, statistiche, backup automatici |

---

## 🚀 Novità v2.20.0 — Completo!

Aggiornamento finale che completa tutte le **22 feature** previste:

| Versione | Novità |
|----------|--------|
| **v2.20.0** | 🏁 **Completamento!** Bilance, wearable, fitness import, onboarding tour, tooltip, brand PDF, export portale |
| **v2.19.0** | 🔄 Unificato in v2.20.0 |
| **v2.18.0** | 🔄 Unificato in v2.20.0 |
| **v2.17.0** | 🔔 Notifiche in-app + desktop native (polling, badge, auto-notifica) |
| **v2.16.0** | ✅ Check pasti consumati, diario self-reporting, chat paziente |
| **v2.15.0** | 🏥 Farmaci-nutrienti, questionari clinici |
| **v2.14.0** | 🌐 Multi-lingua, allergeni, etichette HFSS |
| **v2.13.0** | 🧮 Dashboard aderenza, trend visuali |
| **v2.12.0** | 📈 Radar chart (FFMI/FMI/BFM), dashboard performance |
| **v2.11.0** | 📖 Ricettario personale, swap automatico alimenti |
| **v2.10.0** | 🗂️ Backup automatico giornaliero, export/import |
| **v2.9.0** | 📐 Template dieta personalizzabili, tema chiaro/scuro |
| **v2.8.0** | 🔐 Backup + export CSV/JSON |
| **v2.7.0** | 🌍 Portale paziente (link protetto, mobile) |
| **v2.6.0** | 📊 Grafici evolutivi BIA, report PDF |
| **v2.5.0** | 🛒 Lista spesa automatica |
| **v2.4.0** | ⚡ Calcolo fabbisogno (Mifflin/Harris/Katch) |
| **v2.3.0** | 📄 Export PDF piano alimentare |
| **v2.2.0** | 🥗 Database alimenti INRAN/CREA (212 prodotti) |
| **v2.1.0** | 🔍 OCR BIA da PDF AKERN |

Vedi [CHANGELOG.md](CHANGELOG.md) per il dettaglio completo.

---

## 🔧 Le 22 Feature Complete

### 1️⃣ Database Alimentare Professionale
- ✅ Ricerca alimenti con valori nutrizionali completi (kcal, proteine, grassi, carboidrati, fibre, zuccheri, sale)
- ✅ 11 categorie alimenti (latticini, carni, pesce, cereali, legumi, verdure, frutta, frutta secca, grassi, bevande, varie)
- ✅ 212 prodotti italiani (fonte INRAN/CREA)
- ✅ Sostituzione automatica (swap nutriente-equivalente)
- ✅ Liste della spesa automatiche

### 2️⃣ Piani Alimentari Professionali
- ✅ Export PDF professionale (logo studio, intestazione, colore tema, ricette)
- ✅ Analisi nutrizionale completa (kcal totali, distribuzione %, micronutrienti)
- ✅ Grammatura automatica basata sul fabbisogno
- ✅ Ricettario personale / biblioteca ricette
- ✅ Piano alimentare nella lingua del paziente (italiano, inglese, ecc.)
- ✅ Template dieta personalizzabili (mediterraneo, low-carb, chetogenico, vegano, zona, CKD, carb cycling)

### 3️⃣ App Paziente / Portale
- ✅ Portale paziente protetto da token per visualizzare il piano
- ✅ Check pasti consumati e aderenza
- ✅ Diario alimentare self-reporting (umore, fame, soddisfazione)
- ✅ Chat paziente-nutrizionista
- ✅ Notifiche push promemoria + notifiche desktop native
- ✅ Export piano in PDF direttamente dal portale

### 4️⃣ Analytics e Reportistica
- ✅ Grafici evolutivi (peso, BF%, MM%, PhA, TBW nel tempo)
- ✅ Report di progresso esportabile in PDF (BIA trend multi-metrica)
- ✅ Radar chart confronto (FFMI, FMI, BFM, Hydration, SMM)
- ✅ Dashboard trend e aderenza al piano

### 5️⃣ Funzionalità Cliniche
- ✅ Calcolo fabbisogno energetico (3 formule: Mifflin, Harris, Katch-McArdle)
- ✅ FFMI / FMI / WHR / rapporto vita-fianchi
- ✅ Gestione allergie e intolleranze
- ✅ Interazioni farmaci-nutrienti
- ✅ Questionari clinici (anamnesi, sintomi, follow-up)

### 6️⃣ Amministrazione Studio
- ✅ Backup automatico giornaliero all'avvio
- ✅ Export CSV/JSON di backup e import pazienti
- ✅ Multi-utente (login admin con sessioni)
- ✅ Brand personalizzato (logo, nome studio, colore tema)
- ✅ Statistiche studio (pazienti, piani, aderenza, appuntamenti)

### 7️⃣ Integrazione Dispositivi & Fitness
- ✅ Bilance impedenziometriche — inserimento manuale (peso, BF%, muscolo, acqua, VF, BMR, età)
- ✅ Wearable (Garmin, Fitbit) — passi, FC, sonno, stress, calorie
- ✅ Import attività fitness (Strava, TrainingPeaks) — corsa, bici, nuoto e altro

### 8️⃣ Esperienza Utente
- ✅ Tema chiaro/scuro
- ✅ UI reattiva e mobile-friendly
- ✅ Tour onboarding interattivo al primo accesso
- ✅ Tooltip informativi su ogni sezione
- ✅ Notifiche desktop native real-time

---

## 🖥️ Screenshot

```
┌──────────────────────────────────────────────────────────────┐
│  📊 Dashboard    👥 Pazienti    🥗 Dieta    📖 Ricettario   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📋 Anamnesi  🏥 BIA  📏 Misure  🥗 Dieta  📄 Referti     │
│  📅 Appuntamenti  😷 Sintomi  📋 Questionari  📈 Progressi  │
│  📝 Diario  💬 Chat  ⚖️ Bilancia  ⌚ Wearable  🏃 Fitness   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚀 Avvio rapido

```bash
# Clona e installa
git clone https://github.com/quadrellif90-collab/NutriCoach.git
cd NutriCoach
pip install -r requirements.txt

# Avvia (predefinito: porta 8400)
python run_v2.py

# Porta personalizzata
python run_v2.py 8400
```

Apri `http://127.0.0.1:8400` nel browser.

**Login predefinito:** `admin` / `admin123` (modificabile nelle impostazioni)

**Build EXE:** `python build_exe.py` → `dist/NutriCoach.exe`

---

## 📁 Struttura del progetto

```
NutriCoach/
├── app/
│   ├── main.py              # FastAPI app + tutte le route API
│   ├── database.py          # SQLite, migrazioni automatiche
│   ├── diet_pdf.py          # Generazione PDF (piano, spesa, report BIA)
│   ├── diet_presets.py      # Protocolli dietetici (10 template)
│   ├── energy_calc.py       # Motore fabbisogno calorico (3 formule)
│   ├── ocr_engine.py        # OCR Windows.Media.Ocr + fallback Tesseract
│   ├── templates/
│   │   ├── index.html       # UI principale (19 tab, onboarding, tooltip)
│   │   └── portal.html      # Portale paziente (con export PDF)
│   ├── static/
│   │   └── style.css        # Tema chiaro/scuro, responsive
│   └── ...                  # Altre utility
├── nutrition_db.py          # Database alimenti INRAN/CREA (212 prodotti)
├── run_v2.py                # Avvio server
├── build_exe.py             # Build PyInstaller
├── CHANGELOG.md             # Storico versioni completo
├── requirements.txt         # Dipendenze Python
└── ...
```

---

## 📊 Database

SQLite locale in `~/.nutricoach/nutricoach.db` con **20+ tabelle**:

| Tabella | Descrizione |
|---------|-------------|
| `patients` | Anagrafica pazienti, allergie, sport, obiettivi |
| `food_catalog` | 212 alimenti con valori nutrizionali |
| `food_category` | 11 categorie alimenti |
| `diet_plans` | Piani alimentari generati |
| `diet_templates` | Template dieta personalizzabili |
| `meal_diary` | Diario pasti consumati |
| `recipes` | Ricettario personale |
| `appointments` | Appuntamenti follow-up |
| `bia_measurements` | BIA e antropometria |
| `scale_measurements` | Dati bilance impedenziometriche |
| `wearable_data` | Dati wearable (Garmin/Fitbit) |
| `fitness_imports` | Attività importate (Strava/TP) |
| `messages` | Chat paziente-nutrizionista |
| `app_notifications` | Notifiche in-app e desktop |
| `documents` | Documenti allegati (referti, PDF) |
| `quiz_questions` + `quiz_answers` | Questionari clinici |
| `medications` | Farmaci e interazioni |
| `user_settings` | Impostazioni studio (brand) |

---

## 🔐 Privacy & Sicurezza

- ✅ **100% offline** — nessun dato inviato a server esterni
- ✅ Nessun account remoto, nessuna sottoscrizione
- ✅ Portale paziente protetto da token crittografico
- ✅ Password hashate (SHA-256)
- ✅ Backup automatici giornalieri nel profilo utente

---

## 📄 Licenza

MIT — vedi [LICENSE](LICENSE).

---

<p align="center">
  <strong>NutriCoach v2.20.0</strong> — Completamente offline. Completamente tuo.
</p>