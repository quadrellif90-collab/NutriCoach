
## [1.6.5] — 2026-07-27

### Tab Sintomi + Progressi (completamento scheda paziente)
- **Tab Sintomi** (🩺 diario GI): indice benessere 30gg, medie 9 sintomi, form inserimento (Bristol, ora, cibi), eliminazione
- **Tab Progressi** (📈): trend peso SVG unificato (misure + BIA), note di progresso, eliminazione
- **Helper** `trendSVG()` per grafici SVG riusabili
- **Endpoint**: `DELETE /api/clients/{cid}/progress-note/{nid}`, `delete_progress_note()` in db.py
- **Bug fixati**: endpoint `/symptoms` ritorna `{"symptoms":[]}` (dict) → `.symptoms||[]`; summary usa `avg_*` non campo diretto; spread `...syms` non `**syms`

## [1.6.4] — 2026-07-27

### Notifiche + Tab Misure (2 feature richieste)
- **Tab Misure** (scheda paziente): storico tabelle (peso, altezza, circonferenze, pliche), form inserimento, eliminazione
- **Endpoint**: `POST /api/clients/{cid}/measurements` ritorna `id`, `DELETE /api/clients/{cid}/measurements/{mid}`, `delete_measurement()` in db.py
- **Pagina Notifiche** (sidebar 📨): coda notifiche, generazione dovute, invio singolo (wa.me/mailto), invio bulk per gruppo
- **Helpers frontend**: `jput`, `jdel`, `setActiveNav`
- **Bug critico fixato**: `openPatient()` non apriva la scheda (chiamava `switchNav('dashboard')` che sovrascriveva `#view`); ora usa `setActiveNav` senza ricaricare
- **Bug fixato**: endpoint POST misure non ritornava `id` → frontend diceva "Errore salvataggio"

## [1.6.3] — 2026-07-27

### Cleanup duplicazioni (post-1.6.2)
- Rimosso `delete_client` duplicato in `db.py` (rimasta solo la versione con controllo esistenza + return 0)
- Rimosso `api_client_delete` duplicato in `app.py` (rimasta solo la versione con 404 su inesistente)
- Verifica ad-hoc 26/26 passata

## [1.6.2] — 2026-07-27

### Fix test autonomo post-1.6.1 (4 bug risolti)
- **`DELETE /api/clients/{cid}`**: ora ritorna `404` se il paziente non esiste (prima `200` silenzioso)
- **Chiusura appuntamento**: endpoint `/api/appointments/{aid}/done` cambiato da `PUT` → `POST` (il client usa `jpost` che fa POST)
- **`saveAppt` in modifica**: rimossa doppia chiamata spuria (POST inutile + PUT reale)
- **Duplicazioni rimosse**: due `delete_client` in `db.py` e due `api_client_delete` in `app.py` (conflitto router)

## [1.6.1] — 2026-07-27

### Agenda completa con stato, follow-up, outcome
- **DB**: colonne `status` (open/closed/cancelled), `follow_up`, `outcome` su appointments
- **Backend**: `PUT /api/appointments/{aid}` per modifica, `GET /api/follow-ups` per follow-up attivi
- **UI Agenda** (7-card): statistiche oggi/programmati/completati/follow-up + lista oggi + prossimi + follow-up attivi
- **Tab Appuntamenti** (scheda paziente): creazione/chiusura/modifica con stato, follow-up, outcome
- **Modale appuntamento**: seleziona paziente, titolo, data, note, flag follow-up, chiusura
- Migrazione automatica dei dati esistenti (vecchi appuntamenti con `done=0` → `status='open'`)

## [1.6.0] — 2026-07-27

### Refactoring Dietowin-style: BIA hub + categorie + gruppi
- **Nuove tabelle DB**: `bia_readings` (campi strutturati + pdf_path), `documents` (archivio), `categories` (categorie colore), `groups_`/`client_groups` (gruppi bulk)
- **BIA Hub** (sidebar 🔬): upload PDF, storico con trend SVG, form inserimento completo (Peso, BF%, MM%, PhA, TBW, ECW/ICW, BMR, grasso viscerale), elimina
- **Pazienti**: elimina cliente (`DELETE /api/clients/{cid}`), categorie con colore, gruppi per invii bulk
- **Archivio documenti**: upload, lista per paziente/tipo, visualizzazione inline
- **Sidebar 7 voci**: Dashboard · Pazienti · BIA · Agenda · Notifiche · Archivio · Dieta
- **Scheda paziente** (8 tab): Anamnesi · Misure · Dieta · Referti · Appuntamenti · Sintomi · Gruppi · Progressi

## [1.5.5] — 2026-07-27

### Fix wizard anamnesi (condizioni cliniche)
- **Bug critico**: `loadConditions` assumeva un array, ma `/api/clinical-nutrition/conditions` ritorna un **dict** `{key:{name,...}}` → lo step 3 (Clinica) crashava e restava vuoto. Ora converte il dict in array (`Object.entries` → `{key,label}`).
- `openNewClient` ora ha `.catch(()=>showWizard())` per robustezza se l'endpoint fallisce.
- `renderWizardStep` (step 2) usa `(_CONDITIONS||[])` guard.
- Verificato live: wizard 4-step completo (Anagrafica → Obiettivi → Clinica con 23 condizioni → Conferma → salvataggio cliente+anamnesi OK).
- Verificato live: scheda paziente (8 tab), tab Dieta → `calcWeeks()` auto-calcola N settimane da data inizio/fine, `generatePlan` crea il piano (`/plan/generate` → diet_id).

## [1.5.4] — 2026-07-27

### Riscrittura UI — stile Nutrium + funzioni Dietowin
- **Dashboard pulita**: sidebar a 3 voci (Dashboard, Pazienti, Agenda) + card statistiche + lista pazienti + promemoria
- **Scheda paziente a sezioni** (8 tab): Anamnesi · Misure · Dieta · Referti · Appuntamenti · Sintomi · Integratori · Progressi
- **Wizard anamnesi** modale a 4 step (anagrafica → obiettivi → clinica → conferma)
- **Pianifica per data**: selettore data inizio + data fine → N settimane auto → `plan/generate`
- **Fix bug**: `loadAnamnesi` crashava su `recommendations` dict (non array); `renderDashboard` leggeva campi inesistenti; appuntamenti per-client via `?client_id=`
- **Bridge pywebview preservato**: Email/WhatsApp (`ncOpenExternal`) + PDF (`ncDownload`)

## [1.5.3] — 2026-07-27

### Fix backend + OCR nota
- **Notify /api/clients/{cid}/notify**: email (SMTP + fallback mailto) e WhatsApp (wa.me) testate OK
- **PDF export /api/clients/{cid}/plan/export-pdf**: genera PDF clinico valido (ReportLab)
- **Clinical summary /api/clients/{cid}/clinical-summary**: risponde 200 con dati completi
- **Reminders / Agenda / Messaggi**: endpoint funzionanti (liste vuote = nessun dato, non errore)
- **OCR BIA/Dieta**: nota — Tesseract OCR è dipendenza di **sistema** (non bundlabile in Python). Per PDF scansionati serve installare Tesseract su Windows; l'app rileva PDF senza testo e richiede incolla OCR manuale.

## [1.5.2] — 2026-07-27

### Overhaul UI — sidebar semplificata (6 voci) + fix tab
- **Fix critico tab**: rimossa la guardia che bloccava il click sulle tab
  senza cliente selezionato ("Entra in un cliente prima" su tutto).
  Ora le 6 voci della sidebar funzionano sempre.
- **Fix critico ID**: le sezioni Oggi/Cartella/Pattern avevano id `sec-*`
  diversi dal `data-tab` → il click non mostrava nulla. Aggiunta mappatura.
- **Sidebar ridisegnata**: solo 6 voci fisse — 🏠 Oggi, 👥 Clienti,
  🔔 Promemoria, 📅 Agenda, 📨 Notifiche, 💬 Messaggi.
- **Submenu cliente**: le 14 schede cliniche (Cartella, Antropometria,
  Piano, Pianifica, Diario, Spesa, Riepilogo, Progressi, Scienza Sport,
  Salute Intestinale, Sintomi, Integratori, Pattern, Importa) appaiono
  solo quando entri in un cliente e spariscono quando esci.
- **Rimosse** 🍲 Ricette e 💧 Acqua dalla navigazione.

## [1.5.1] — 2026-07-26

### Fix launcher (finestra nativa)
- **Port-guard**: se la porta 8090 è già occupata (es. un'altra istanza
  di NutriCoach già aperta), il launcher esce con errore esplicito invece
  di aprire la finestra sull'istanza sbagliata (che mostrerebbe dati o
  versione diversi — es. "non vedo le tab" perché apre la vecchia istanza).
- Messaggio di errore chiaro: chiudi NutriCoach già aperto e riprova.

## [1.5.0] — 2026-07-26

### Finestra nativa desktop (come PCC — niente più pagina browser)
- **`launcher.py`**: avvia il server FastAPI in background e apre l'app in
  una **finestra nativa** via `pywebview` (EdgeChromium su Windows, Cocoa su
  Mac, GTK/WebKit su Linux) — NON più un tab nel browser.
- **Fallback automatico**: se `pywebview` non è installato, ricade sul
  browser classico (`webbrowser.open`) — nessun regressione in dev.
- **Bridge JS↔Python** (`window.pywebview.api`):
  - `open_external(url)` — mailto / WhatsApp (`wa.me`) / link esterni si
    aprono nel browser di sistema, fuori dalla finestra.
  - `download(filename, b64)` — i download (PDF piano, archivio zip) usano
    il dialogo "Salva con nome" nativo (necessario su macOS WKWebView che
    ignora `<a download>`). Su Windows funziona anche il metodo nativo.
- **`NutriCoach.spec`** ora builda da `launcher.py` e include `pywebview`
  negli hidden imports; `requirements.txt` aggiunge `pywebview>=6.0.0`.

## [1.4.4] — 2026-07-26

### Invio automatico Email / WhatsApp (cliente finale)
- **✉️ Email reale via SMTP**: il nutrizionista configura il proprio server
  SMTP (Gmail/Outlook) nel pannello "⚙️ Config email" (Home Oggi).
  La "📧 Email" del piano / check-in invia davvero il messaggio.
  Se non configurato → fallback `mailto:` (client locale).
  Endpoint `/api/studio/config` (GET/POST) + SMTP in `/api/clients/{cid}/notify`.
- **📱 WhatsApp via `wa.me`**: la "📱 WhatsApp" apre la chat col cliente
  con il messaggio precompilato (0 dipendenze, nessuna API a pagamento).
- **Check-in**: nel modale ora ci sono anche "✉️ Email" e "📱 WhatsApp"
  per sollecitare il paziente direttamente.
- **Coda notifiche**: invio reale + log (non solo bottone "Inviato").

## [1.4.3] — 2026-07-26

### Bug fix (audit contratti frontend↔backend)
- **Card Home "Oggi" ora aprono il cliente**: le card usavano
  `selectClient()` (funzione inesistente → click morto). Corretto in
  `enterClient(${c.id})` (verificato: click apre scheda cliente).
- Audit automatico di tutti gli `onclick`/chiamate API/`getElementById`:
  **0 orphan** rimasti dopo il fix (le altre segnalazioni erano falsi positivi
  da stringhe template o elementi creati dinamicamente).

## [1.4.2] — 2026-07-26

### Sicurezza dati & chiusura loop (cliente finale)
- **💾 Backup/Export archivio**: nella Home "Oggi" pannello "I tuoi dati" —
  scarica `nutricoach_archivio.zip` (DB SQLite + dump JSON di tutti i clienti).
  Endpoint `/api/studio/export`.
- **📌 Backup ora + 📥 Ripristina**: crea/ripristina backup in
  `~/.nutricoach/backups/` (keep ultimi 7). Il ripristino chiede conferma
  esplicita e fa un backup di sicurezza prima di sovrascrivere.
  Endpoint `/api/studio/backup-now`, `/api/studio/backups`, `/api/studio/restore`.
- **🔄 Auto-backup silenzioso al login**: ogni accesso copia il DB nei backup.
- **📅 Agenda → Oggi**: la Home "Oggi" segnala gli appuntamenti di oggi
  (collega agenda e priorità giornaliera). Endpoint `/api/studio/today`
  ora include flag `agenda` per appuntamenti del giorno corrente.

## [1.4.1] — 2026-07-26

### UX quotidiana (cliente finale)
- **📱 Sidebar responsive**: su schermi stretti (<900px) i 22 tab diventano
  una barra orizzontale scrollabile (niente più colonna illeggibile su
  laptop 13" / tablet).
- **🖨️ Print CSS**: stampando da browser (Cartella Clinica, Diario, Piano)
  l'UI scompare e resta solo il contenuto pulito, pagina per pagina.
- **🔍 Ricerca clienti**: campo filtro live nella lista clienti (per nome).
- **📈 Mini-grafico trend peso**: Canvas nativo (0 dipendenze) nella Cartella
  Clinica che disegna l'andamento peso sulle ultime misurazioni.

## [1.4.0] — 2026-07-26

### Workflow & UX (cliente finale)
- **🏠 Home "Oggi"**: nuova tab operativa che mostra i clienti che richiedono
  attenzione (peso da aggiornare >14gg, diario da rivedere >7gg, piano assente,
  check-in settimanale mancante). Ordinati per urgenza. Endpoint `/api/studio/today`.
- **⚡ Check-in rapido lato cliente**: modale per registrare peso + compliance %
  + energia dal lato nutrizionista (simula l'invio del cliente). Endpoint
  `/api/clients/{cid}/client-checkin`. Il nutrizionista vede chi ha risposto
  nella Home "Oggi".
- **📧 Invio piano via email**: pulsante nel tab Pianifica che registra l'invio
  in `notification_log` e apre il client email locale (`mailto:`, 0 dipendenze).
  Endpoint `/api/clients/{cid}/notify`.
- **✨ Seed dati esempio**: pulsante "Carica cliente di esempio (Marco Demo)"
  nella Home quando non ci sono clienti — crea un caso IBS+SIBO con piano
  filtrato per esplorare l'app. Endpoint `/api/studio/seed-demo` (idempotente).
- **⚡ Diario "Salva ORA"**: compila data/ora automaticamente; slider sintomi
  mostrano il valore live.
- **📄 Prompt PDF post-generazione**: dopo "Genera settimana" appare il
  pulsante "Esporta PDF clinico" per chiudere il loop piano→PDF.

## [1.3.1] — 2026-07-26

### Fix (audit aggressivo post-release)
- **`parse_pathologies` ora estrae anche le `allergies` dal JSON anamnesi**
  (`{"clinical_conditions":[...], "allergies":[...]}`). Prima le allergie
  salvate via anamnesi JSON venivano **perse** → il piano filtrava le
  condizioni ma NON le allergie quando l'anamnesi era in formato JSON.
  Ora `api_plan_generate` unisce entrambe le fonti (campo `allergies`
  del cliente + `allergies` dall'anamnesi JSON) nelle esclusioni.
- Aggiunto `_normalize_allergies` (lowercase, gestione stringa/lista).
- `parse_pathologies` gestisce anche input `dict`/`list` diretti (non solo
  stringa) e non crasha mai.

## [1.3.0] — 2026-07-26

### Aggiunto (raffinamento scientifico + workflow)
- **Modulo Clinical Nutrition ampliato a 23 condizioni** con strategie
  evidence-based aggiornate alle fonti 2024-2026:
  - Nuove condizioni: **IBD** (Crohn/colite, ECCO 2023), **Endometriosi**
    (Pattern anti-infiammatorio, Endometriosis Foundation 2023),
    **MASLD/NAFLD** (dieta Mediterranea + riduzione fruttosio, AASLD 2023),
    **PCOS** (bassa GI + inositolo, guideline 2023), **EOE** (6FED/4FED),
    **SIBO** (procinetici + protocollo eradicazione), **intolleranza istamina**
    (DAO suina 4.2 mg, integrazione vitamina C).
  - Corretta la logica SIBO: **procinetici obbligatori** (Prucalopride/LDN 62%
    meno recidive, Iberogast), DAOsuina 4.2 mg come gold standard; **rimossa
    la zonulina** (test non validato, Nutrients 2023).
- **7 Pattern Dietetici evidence-based** (`DIET_PATTERNS`): Mediterranea, DASH,
  MIND, Portfolio, basso indice glicemico, RPAH/FAILSAFE (basso chimico, 88%
  migliora J Hum Nutr Diet 2024), Supporto Barriera Intestinale. Tab **🥗 Pattern
  Dietetici** + endpoint `/api/clinical-nutrition/diet-patterns/*` e `/suggest`.
- **Cartella Clinica unificata** (tab **🗂️**): endpoint
  `/api/clients/{cid}/clinical-summary` fonde condizioni → conflitti →
  esclusioni → integratori → fase dieta → sintomi → trend peso in un'unica vista.
- **Loop diario → AI pattern + reintroduzione FODMAP guidata** (tab Diario):
  - `detect_symptom_patterns()` rileva sintomi ricorrenti dai log.
  - `fodmap_reintroduction_plan()` (ordine Monash 2025) + `suggest_next_reintroduction()`.
  - Endpoint `/api/clients/{cid}/symptom-patterns` e `/fodmap-reintroduction`.
- **Wizard Onboarding Anamnesi** (pulsante 🧭): 3 step (patologie → allergie/note
  → conflitti rilevati) che popola anamnesi + allergie del cliente.
- **PDF piano clinico unificato**: `plan/generate` ora **salva la dieta** nel DB
  e l'endpoint `/api/clients/{cid}/plan/export-pdf` genera il report con
  condizioni, conflitti, esclusioni, pattern consigliati e phased protocol.

### Fix
- **Bug fondamentale formato `pathologies`**: il campo arrivava come CSV
  (`"sibo, ibs"`) dal form ma come JSON (`{"clinical_conditions":[...]}`) da
  anamnesis; `parse_pathologies()` è ora la **single source of truth** (gestisce
  entrambi). Prima `json.loads` falliva silenziosamente → condizioni `[]` →
  esclusioni cliniche **mai applicate** al piano.
- `import json` mancante in `clinical_nutrition.py` (crash silenzioso su JSON).
- Endpoint sintomi/integratori/fase-dieta usavano `db.` inesistente → corretti a
  `database.` (erano già rotti nel sistema).
- `fodmap-analysis` chiamava `meal_planner._fodmap_load` inesistente → ora
  `clinical_nutrition.calculate_fodmap_load`.
- `pdf_export.build_report_pdf` gestisce entrambe le strutture piano (planner
  `meal.items` e import `meal.groups`) senza `KeyError`.

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
