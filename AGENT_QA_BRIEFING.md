# AGENT QA BRIEFING — NutriCoach v2.20.16

## Target
- Base URL: `http://127.0.0.1:8400`
- App: NutriCoach (gestionale nutrizionisti) — FastAPI + SQLite + vanilla JS SPA
- Autenticazione: **auto-login** — nessun login richiesto all'avvio
- Lingua UI: **italiano**
- Server attivo: verificare con `curl -s http://127.0.0.1:8400/api/version` → deve dare `{"version":"2.20.16"}`

## Come testare (senza browser: via HTTP/curl/Python)
La SPA è single-page: tutta l'interfaccia vive in `app/templates/index.html` (JS inline),
gli endpoint API in `app/main.py` (124 route). I sub-agenti NON hanno browser GUI: testate
via `curl`, `python` (urllib) e analisi statica dei file.

### Sezioni principali (nav sidebar)
- Dashboard (`/` → `loadDashboard`)
- Pazienti (creazione/ricerca/CRUD via `/api/patients`)
- BIA (import testo/PDF → `/api/patients/{pid}/import`, `/api/ocr/local/process`)
- Dieta (generazione piano → `/api/patients/{pid}/plan/generate`)
- Ricettario (`/api/recipes`), Diario, Chat, Questionari, Agenda, Notifiche
- Impostazioni, Statistiche

### Endpoint utili per test funzionali
```
GET  /api/version
GET  /api/patients?limit=10
POST /api/patients  {"name":"Test QA","sex":"Maschile","birth_date":"1990-12-04","height":168}
POST /api/patients/{pid}/plan/generate  {"targets":{"kcal":2000,"protein_pct":20,"carb_pct":55,"fat_pct":25},"options":{"meals":5,"days":["lun","mar","mer","gio","ven","sab","dom"],"conditions":[]},"preset":""}
POST /api/patients/{pid}/import  {"text":"Peso: 71.4 kg\nAltezza: 168.0 cm\nBMI: 25.3\nPhA: 7.4"}
POST /api/patients/{pid}/import/confirm
GET  /api/recipes
POST /api/recipes  {"name":"Test","ingredients":[],"instructions":"x"}
GET  /api/patients/{pid}/bia-trend
GET  /api/patients/{pid}/radar
POST /api/backup
GET  /api/export/patients
```

## Ruoli dei 4 sub-agenti
1. **UI/UX Pixel-Perfect**: layout responsive, margini/overflow, stati hover/active/disabled/loading visibili, accessibilità
2. **Functional & Edge-Case**: click di ogni azione via API, input estremi (vuoti, negativi, HTML injection, double-submit), modali
3. **Real User Journey**: flusso completo utente (dashboard → crea paziente → BIA → piano → ricetta → backup)
4. **Backend & Network Chaos**: latenza, errori 4xx/5xx, payload malformati, endpoint mancanti, messaggi d'errore

## Consegna
Ogni sub-agente scrive il proprio report in `%TEMP%/qa_agent_<n>.md` con tabella bug:
component | gravità (CRITICAL/HIGH/MEDIUM/LOW) | descrizione | passi per riprodurre | fix suggerito

## Regole
- NON modificare alcun file del progetto (solo report in %TEMP%)
- NON riavviare il server
- Verificare ogni bug con una chiamata reale prima di riportarlo
- Segnalare anche gli stati UX mancanti (no loading, no disabled, no hover) e i messaggi d'errore oscuri
