# 🍏 NutriCoach v2.9.0 — Presentazione

**Il gestionale di nutrizione locale che chiude il loop clinico tra dieta, misure e follow-up.**

> *Dietowin-style, 100% offline, zero abbonamenti, zero cloud.*

---

## 🎯 Perché NutriCoach

I software di dietetica cadono in due limiti:
1. **Cloud obbligatorio** → dati sensibili pazienti fuori GDPR
2. **Fogli di calcolo separati** → i numeri non tornano mai

NutriCoach è l'opposto: **uno strumento tuo, portatile, privato**, con un solo motore di calcolo. Ogni schermata è una *vista* coerente degli stessi numeri.

---

## ✨ Cosa fa (8 capitoli completati)

### 1. 🗄️ Database alimentare professionale (v2.2.0)
- 212 alimenti italiani (fonte INRAN/CREA)
- 11 categorie: latticini, carni, pesce, cereali, legumi, verdure, frutta, frutta secca, olii grassi, bevande, varie
- Valori completi: kcal, proteine, carboidrati, grassi, fibre, zuccheri, sale
- Ricerca autocomplete integrata nel diario

### 2. 📄 Export PDF piano alimentare (v2.3.0)
- Tabella settimanale 7 giorni × 5 pasti con grammature
- Riepilogo macro giornaliero (kcal, P, C, F)
- Sezioni raccomandazioni cliniche e alimenti esclusi
- Font Unicode (Arial/Segoe) per caratteri italiani

### 3. 🔥 Calcolo fabbisogno calorico (v2.4.0)
- Mifflin-St Jeor, Harris-Benedict, Katch-McArdle
- TDEE per livello attività
- Target kcal per obiettivo (dimagrimento/mantenimento/massa/performance)
- Pulsante "Calcola fabbisogno" auto-compila il piano

### 4. 🛒 Lista della spesa automatica (v2.5.0)
- Aggrega grammature per alimento dal piano settimanale
- Raggruppamento per categoria alimentare
- Export PDF con checkbox

### 5. 📊 Grafici evolutivi BIA (v2.6.0)
- 7 metriche: peso, BF%, massa magra, acqua, PhA, muscolo, BMI
- Sparkline SVG interattive + report PDF con grafici a linee

### 6. 🔗 Portale paziente (v2.7.0)
- Link protetto da token (secrets.token_urlsafe)
- Vista read-only mobile-friendly del piano
- Dati sensibili non esposti

### 7. 💾 Backup automatico + export/import (v2.8.0)
- Backup giornaliero idempotente (copia DB + JSON)
- Export CSV pazienti, export/import JSON singolo paziente

### 8. 🎨 Template dieta + UI migliorata (v2.9.0)
- Template dieta personalizzabili e riusabili
- Tema chiaro/scuro (persistito in localStorage)

---

## 🔬 OCR Engine integrato (v2.1.0)

Estrae **14/14 campi BIA** da PDF AKERN/InBody:
- **Windows.Media.Ocr** (API nativa Windows 10/11, italiano) — nessuna dipartenza esterna
- Fallback Tesseract se `winsdk` non disponibile
- TBW derivato da ECW+ICW, PhA e Idratazione catturati

---

## 🏗️ Architettura

| Componente | Modulo |
|------------|--------|
| API server | `app/main.py` (FastAPI) |
| Database | `app/database.py` (SQLite + migrazioni auto) |
| PDF | `app/diet_pdf.py` (fpdf2) |
| Fabbisogno | `app/energy_calc.py` |
| OCR | `app/ocr_engine.py` (Windows.Media.Ocr) |
| Alimenti | `nutrition_db.py` (INRAN/CREA) |
| UI | `app/templates/index.html` + `portal.html` |

---

## 🚀 Quick start

```bash
pip install -r requirements.txt
python run_v2.py 8400
# Apri http://127.0.0.1:8400
```

Build EXE: `python build_exe.py` → `dist/NutriCoach.exe`

---

## 📊 Confronto con i competitor

| Feature | NutriCoach v2.9 | Dietowin 11 | Nutrium |
|---------|----------------|------------|---------|
| Offline / privacy | ✅ 100% | ⚠️ cloud | ❌ cloud |
| DB alimenti integrato | ✅ 212 | ✅ | ✅ |
| OCR BIA integrato | ✅ Windows OCR | ❌ | ❌ |
| Export PDF piano | ✅ | ✅ | ✅ |
| Fabbisogno calorico | ✅ 3 formule | ✅ | ✅ |
| Portale paziente | ✅ | ❌ | ✅ |
| Backup automatico | ✅ | ⚠️ | ❌ |
| Tema scuro | ✅ | ❌ | ✅ |
| **Prezzo** | **Gratuito (MIT)** | **€/anno** | **€/mese** |

---

## 📜 Licenza

MIT — usa, modifica, ridistribuisci liberamente.

**🔗 Repository:** https://github.com/quadrellif90-collab/NutriCoach
