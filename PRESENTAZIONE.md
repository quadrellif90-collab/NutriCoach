# 🥗 NutriCoach v2.20.0

## Gestionale di Nutrizione Professionale — 100% Offline

> **Un unico strumento per l'intero flusso di lavoro del nutrizionista:**
> dall'acquisizione dei dati BIA, alla generazione del piano alimentare,
> al follow-up del paziente, fino all'analisi dei risultati.

---

## 🎯 Il Problema

I nutrizionisti oggi usano **3-4 strumenti diversi**:
1. Un software per i piani alimentari (Dietowin, Nutrium)
2. Un foglio di calcolo per BIA e trend
3. Un CRM per pazienti e appuntamenti
4. WhatsApp/email per il follow-up

**Risultato:** dati sparsi, lavoro duplicato, nessuna coerenza.

## ✅ La Soluzione

NutriCoach **unifica tutto** in un'unica applicazione locale:

| Funzione | NutriCoach | Alternativa |
|----------|-----------|-------------|
| Database alimenti | ✅ 212 prodotti INRAN/CREA | Dietowin (a pagamento) |
| Piani alimentari | ✅ 5 template + personalizzabili | Nutrium ($50/mese) |
| BIA + OCR | ✅ Integrato (Windows.Media.Ocr) | Lettura manuale |
| Grafici trend | ✅ 7 metriche + radar chart | Excel |
| Portale paziente | ✅ Token protetto | Abbonamento cloud |
| Chat | ✅ Messaggistica integrata | WhatsApp |
| Wearable | ✅ Garmin, Fitbit, Strava | — |
| Backup | ✅ Automatico giornaliero | — |
| **Prezzo** | **💰 Gratuito, 100% offline** | **€30-100/mese** |

---

## 🏗️ Architettura — Dietowin Pro Model

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA AGGREGATOR                          │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────────┐ │
│  │ BIA  │  │  DB  │  │ Trend│  │ PDF  │  │ Categorie    │ │
│  │ OCR  │  │ Alim │  │ Chart│  │ Rep  │  │ Gruppi       │ │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────────────┘ │
│                      │                                      │
│               ┌──────┴──────┐                               │
│               │   Paziente  │                               │
│               └──────┬──────┘                               │
│                      │                                      │
│  ┌───────────────────┼────────────────────┐                 │
│  │   Agenda FollowUp │  Notifiche Bulk    │                 │
│  │   Archivio Doc    │  WhatsApp / Email  │                 │
│  └───────────────────┴────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          │  DIET GENERATOR       │
          │  (secondario)         │
          └───────────────────────┘
```

**Principio base:** ogni feature segue il pattern **Create → View → Trend → Compare → Delete**.

---

## 📊 Le 22 Feature Complete

### 1️⃣ Database Alimentare Professionale ⭐ #1
| Sotto-feature | Stato |
|---------------|-------|
| Ricerca alimenti con valori nutrizionali completi | ✅ |
| 11 categorie (cereali, legumi, verdure, frutta, proteine...) | ✅ |
| 212 prodotti italiani — fonte INRAN / CREA | ✅ |
| Sostituzione automatica (swap nutriente-equivalente) | ✅ |
| Liste della spesa automatiche dal piano alimentare | ✅ |

### 2️⃣ Piani Alimentari Professionali ⭐ #2
| Sotto-feature | Stato |
|---------------|-------|
| Export PDF con logo studio, intestazione brandizzata | ✅ |
| Analisi nutrizionale completa (kcal, distribuzione %, micro) | ✅ |
| Grammatura automatica basata sul fabbisogno | ✅ |
| Ricettario personale / biblioteca ricette | ✅ |
| Piano in lingua del paziente (italiano, inglese) | ✅ |
| Template dieta (mediterraneo, keto, vegano, zona, CKD, carb cycling) | ✅ |

### 3️⃣ App Paziente / Portale ⭐ #3
| Sotto-feature | Stato |
|---------------|-------|
| Leva paziente per visualizzare piano alimentare | ✅ |
| Check pasti consumati e aderenza | ✅ |
| Diario alimentare self-reporting (mood, fame, soddisfazione) | ✅ |
| Chat paziente-nutrizionista | ✅ |
| Notifiche push/desktop native (campanella, polling, badge) | ✅ |
| Export piano in PDF dal portale | ✅ |

### 4️⃣ Analytics e Reportistica ⭐ #4
| Sotto-feature | Stato |
|---------------|-------|
| Grafici evolutivi (peso, BF%, MM%, PhA, TBW, ECW/ICW, SMM) | ✅ |
| Report di progresso in PDF (BIA trend multi-metrica) | ✅ |
| Radar chart confronto (FFMI, FMI, BFM, Hydration, SMM) | ✅ |
| Dashboard aderenza al piano | ✅ |

### 5️⃣ Funzionalità Cliniche
| Sotto-feature | Stato |
|---------------|-------|
| Calcolo fabbisogno (Mifflin / Harris / Katch-McArdle) + TDEE | ✅ |
| FFMI / FMI / WHR (indici composizione corporea) | ✅ |
| Allergie e intolleranze nel profilo paziente | ✅ |
| Interazioni farmaci-nutrienti | ✅ |
| Questionari clinici (anamnesi, sintomi, follow-up) | ✅ |

### 6️⃣ Amministrazione Studio
| Sotto-feature | Stato |
|---------------|-------|
| Backup automatico giornaliero | ✅ |
| Export CSV/JSON + import pazienti | ✅ |
| Multi-utente con login e sessioni | ✅ |
| Brand personalizzato (logo, nome studio, colore tema) | ✅ |
| Statistiche studio (pazienti, piani, aderenza) | ✅ |

### 7️⃣ Integrazione Dispositivi
| Sotto-feature | Stato |
|---------------|-------|
| Bilance impedenziometriche (peso, BF%, muscolo, TBW, VF, BMR) | ✅ |
| Wearable Garmin / Fitbit (passi, FC, sonno, stress) | ✅ |
| Import attività Strava / TrainingPeaks (corsa, bici, nuoto) | ✅ |

### 8️⃣ Esperienza Utente
| Sotto-feature | Stato |
|---------------|-------|
| Tema chiaro/scuro | ✅ |
| UI reattiva e mobile-friendly | ✅ |
| Tour onboarding interattivo al primo accesso | ✅ |
| Tooltip informativi su ogni sezione | ✅ |
| Notifiche desktop native real-time | ✅ |

---

## 🔧 Specifiche Tecniche

| Componente | Tecnologia |
|------------|-----------|
| **Backend** | Python 3.11 + FastAPI |
| **Database** | SQLite (`~/.nutricoach/nutricoach.db`) — 20+ tabelle |
| **Frontend** | Vanilla JS + CSS (nessun framework) |
| **PDF** | FPDF2 con font Unicode |
| **OCR** | Windows.Media.Ocr (primario) + Tesseract (fallback) |
| **Auth** | Sessioni con hash SHA-256 |
| **Avvio** | `run_v2.py` (uvicorn) o `NutriCoach.exe` (PyInstaller) |

---

## 🚀 Avvio

```bash
git clone https://github.com/quadrellif90-collab/NutriCoach.git
cd NutriCoach
pip install -r requirements.txt
python run_v2.py
# Apri http://127.0.0.1:8400
```

**Login:** `admin` / `admin123`

---

## 📈 Roadmap Completata

```
v2.1.0  ████████████████████████████████░░  OCR BIA
v2.2.0  ████████████████████████████████░░  Database Alimenti
v2.3.0  ████████████████████████████████░░  Export PDF
v2.4.0  ████████████████████████████████░░  Fabbisogno
v2.5.0  ████████████████████████████████░░  Lista Spesa
v2.6.0  ████████████████████████████████░░  Grafici
v2.7.0  ████████████████████████████████░░  Portale
v2.8.0  ████████████████████████████████░░  Backup
v2.9.0  ████████████████████████████████░░  Template + Tema
v2.10.0 ████████████████████████████████░░  Backup auto + Stats
v2.11.0 ████████████████████████████████░░  Ricettario + Swap
v2.12.0 ████████████████████████████████░░  Radar + Performance
v2.13.0 ████████████████████████████████░░  Dashboard Aderenza
v2.14.0 ████████████████████████████████░░  Multi-lingua + Allergeni
v2.15.0 ████████████████████████████████░░  Farmaci + Questionari
v2.16.0 ████████████████████████████████░░  Check pasti + Chat
v2.17.0 ████████████████████████████████░░  Notifiche
v2.20.0 ████████████████████████████████░░  Bilanci, Wearable, Fitness
        ████████████████████████████████  22/22 ✅
```

---

## 📦 Database — 20+ Tabelle

```
patients
├── bia_measurements
├── scale_measurements    ← Nuovo v2.20
├── wearable_data          ← Nuovo v2.20
├── fitness_imports        ← Nuovo v2.20
├── diet_plans
│   ├── meals
│   └── meal_diary
├── messages
├── app_notifications
├── appointments
├── recipes
├── documents
├── medications
├── quiz_questions
│   └── quiz_answers
├── food_catalog
├── food_category
├── diet_templates
└── users / user_settings
```

---

## 🏁 Conclusione

NutriCoach v2.20.0 è **completo** — tutte le 22 feature sono state implementate, testate e rilasciate.

Non ci sono abbonamenti. Non ci sono server cloud. I dati dei tuoi pazienti sono **solo tuoi**, sul **tuo computer**, con **backup automatici** giornalieri.

> **Un solo strumento. Zero canoni. Massimo controllo.**

---

<p align="center">
  <a href="https://github.com/quadrellif90-collab/NutriCoach">github.com/quadrellif90-collab/NutriCoach</a><br>
  <strong>NutriCoach v2.20.0</strong> — 🥗 by quadrellif90
</p>