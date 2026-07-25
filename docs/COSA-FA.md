# Cosa fa NutriCoach — dettaglio per area

Documento di dettaglio sul comportamento di ogni modulo. Complementare al
[README](../README.md) e alla [PRESENTAZIONE](../PRESENTAZIONE.md).

> Principio architetturale: **single source of truth**. Un solo motore
> (`meal_planner.py` + `nutrition_engine.py`) calcola nutrienti e piani; ogni
> schermata (diario, pianificatore, riepilogo) è una *vista* di quei numeri.
> Non esistono due calcoli indipendenti che possano divergere.

---

## 1. Clienti

- Anagrafica: nome, sesso, data di nascita, altezza, obiettivo (dimagrimento/
  mantenimento/massa), note.
- Ricerca clienti e **confronto** tra due clienti (miscele di profilo + ultima
  antropometria).
- Ogni cliente ha il proprio sotto-albero di misure, diete, BIA, appuntamenti,
  messaggi, acqua, note.

**Endpoint:** `GET /api/clients`, `POST /api/clients`, `GET /api/clients/{id}`,
`POST /api/clients/{id}/compare`.

---

## 2. Dieta da PDF

Flusso:

1. Upload del PDF (`POST /api/clients/{id}/diet/upload`).
2. `diet_parser.py` estrae i **pasti**, con due primitive chiave:
   - **Gruppi alternativa (OR-esclusivi)**: un gruppo contiene N opzioni,
     l'utente ne sceglie *una*; il conteggio considera solo l'opzione scelta
     (non la somma di tutte — bug storico corretto).
   - **Grammature**: ogni alimento porta i grammi previsti.
3. `nutrition_engine.py` calcola **macro/giorno** sommando gli alimenti scelti.
4. `GET /api/clients/{id}/diet/{did}/compute` ritorna macro totali e per pasto.
5. **Spesa** (`GET /api/clients/{id}/diet/{did}/shopping`): aggrega gli
   alimenti per nome e grammi.
6. **Export** HTML (`/export/html`) e PDF (`pdf_export.py`, reportlab).

**Endpoint:** upload, `/compute`, `/shopping`, `/export/html`, `/export/pdf`.

---

## 3. Diario alimentare (builder manuale)

Alternativa all'import PDF: il nutrizionista (o il cliente) compone il diario
voce per voce.

- Ricerca alimenti fuzzy su `~240` alimenti di riferimento
  (`nutrition_db.search_foods`).
- Ogni voce: alimento + grammi + pasto + giorno.
- **Aggregazione automatica** di macro **e micronutrienti** via
  `meal_planner`/`meal_planner.diary_totals` (Calcio, Ferro, VitC, K, Mg).
- Possibilità di alimenti **personalizzati** (`foods_custom`).

**Endpoint:** `POST /api/clients/{id}/diet-item`, `GET /api/clients/{id}/diet-items`,
`GET /api/clients/{id}/diary/totals`, `POST/GET/DELETE /api/foods/custom`.

---

## 4. Pianificatore automatico

`meal_planner.generate_plan(targets)` compone 7 giorni × 5 pasti
(colazione, spuntino, pranzo, spuntino2, cena) bilanciati tra proteina,
carboidrato, verdura, grasso e frutta, avvicinandosi ai target
(kcal / proteine / carboidrati / grassi) del cliente.

- Deterministico (seed fisso) → stesso input → stesso piano.
- Ogni pasto riporta i propri totali; il riepilogo settimanale mostra la media
  kcal/giorno.

**Endpoint:** `POST /api/clients/{id}/plan/generate`.

---

## 5. BIA (bioimpedenziometria)

`bia_parser.parse_bia_text` legge referti InBody/Tanita:

- **Sorgenti**: paste di testo (anche da OCR di PDF scansionato) o upload PDF.
- **Campi**: peso, altezza, BMI, massa grassa, massa magra, acqua totale (TBW),
  angolo di fase (PhA).
- **Robustezza sul testo "sporco"** (verificata con test):
  - decimali `75,2` e `75.2` equivalgono;
  - valori tra parentesi `(75.2)`;
  - PDF a due colonne / testo su unica riga;
  - non confonde `m2` (unità) con il numero `2` di un valore separato.

**Endpoint:** `POST /api/clients/{id}/bia/paste`, `POST /api/clients/{id}/bia/upload`.

---

## 6. Antropometria

`anthropometry.py`:

- **BMR** via Mifflin-St Jeor (1995).
- **% grasso** via Durnin-Womersley (4 pliche).
- **WHR** (waist-to-hip ratio) e sua classificazione.
- **FFMI** (fat-free mass index).
- Classificazione BMI e output pronto per la UI.

**Endpoint:** `GET /api/clients/{id}/anthro`, `POST /api/clients/{id}/measurement`.

---

## 7. Follow-up

### Notifiche
Per cliente: scegli *quali* messaggi inviare (riscontro settimanale, report,
promemoria), su che **canale** (app/WhatsApp/email — hook locali, nessun
invio reale oggi) e con che **frequenza**. `notifications.generate_due`
produce la **coda "da inviare"** in base alle scadenze; il nutrizionista la
vede e la marca inviata.

**Endpoint:** `GET/POST /api/clients/{id}/notif-prefs`,
`POST /api/clients/{id}/notifications/generate`, `PUT /api/notifications/{nid}/sent`.

### Agenda
Calendario mensile (`db.appointments`). Per cliente o generale. Click su un
giorno → pre-compila la data per il nuovo appuntamento. Lista degli aperti con
pulsante "fatto".

**Endpoint:** `POST /api/appointments`, `GET /api/appointments`,
`PUT /api/appointments/{aid}/done`.

### Messaggi
Thread locale per cliente (`db.messages`), direzione nutrizionista↔cliente.
Nessun cloud: è la cronologia delle comunicazioni, pronta per un futuro invio
reale.

**Endpoint:** `POST /api/clients/{id}/message`, `GET /api/clients/{id}/messages`.

---

## 8. Acqua & Progressi

- **Acqua**: log ml per data (`db.water_log`), totale giornaliero.
- **Note di progresso**: testo libero per data (`db.progress_notes`), utile per
  annotare "settimana 3: -1.2 kg, più energia".

**Endpoint:** `POST/GET /api/clients/{id}/water`,
`POST/GET /api/clients/{id}/progress-notes`.

---

## 9. Login & Tema

- **Login locale** (`auth.py`): account nutrizionista con username + password,
  hash **PBKDF2** (mai in chiaro). Reset che cancella solo le credenziali,
  non i clienti.
- **Tema chiaro/scuro**: toggle persistente in `localStorage`; il tema chiaro
  è applicato anche prima del render (niente flash).

**Endpoint:** `/api/auth/status`, `/api/auth/setup`, `/api/auth/login`,
`/api/auth/change`, `/api/auth/reset`.

---

## Scienza Sport (strategie pro → amatoriale)

Tab **🔬 Scienza Sport**: raccoglie approcci documentati nel mondo elite e li
rende applicabili dal nutrizionista su clienti amatoriali/semi-pro. Tutto
ancorato a letteratura 2024-2026 (vedi fonti nel tab), **non è consulenza
medica**.

- **Fuel for the Work Required (FTWR):** periodizzazione dei carboidrati in
  base alla seduta, non "train-low". `sport_science.fueling_daily_targets`
  ritorna g carb/giorno per tipo di giorno (recupero/moderato/alto/gara) e
  `fueling_during_targets` i g/h durante lo sforzo (30/60/90/120 g/h). Il
  bottone "Usa nel pianificatore" imposta carb e kcal nel tab Pianifica.
  - Riferimento pro: Tour de France 2025, fueling 100-120 g/h (fino a 200 in
    fasi severe). Fonte: Outside/Velo, Olympics.com, EF Pro Cycling, Cao 2025.
- **Recovery microcycle:** fondamenta (sonno 7-9h, nutrizione, idratazione)
  prime; adjunct (cooling/compression/attivo/psicologico) sequenziati per
  microciclo. Fonte: Aspetar "Emerging Challenges in Recovery for the Elite
  Football Player" (FIFA World Cup 2026), Ranchordas 2017, Rackard 2025.
- **Chetoni esogeni:** mostrati con **nota UCI 2024** che **sconsiglia** l'uso
  (nessuna evidenza convincente su performance/recovery). Non proposti come
  strategia.

- **Distribuzione proteica (A):** totale giornaliero (1.6-2.2 g/kg) > timing. Calcolatore
  `/api/sport-science/protein`: totale g, g/pasto (4-5 pasti), ~3 g leucina/pasto.
  Nota "mito finestra anabolica 30'" inclusa. Fonti: Lak&Bagheri 2024, Morton 2018,
  Mamerow 2014, Schoenfeld 2013/2017, meta MDPI 2025.
- **Gut training (B):** assorbimento carb trainabile, protocollo 4 settimane
  (30→60→90→120 g/h) con rapporto 2:1 glucosio:fruttosio oltre 60 g/h.
  Fonti: Cao 2025, EF Pro Cycling gut-training 2025, Morton 2026.
- **Periodizzazione a blocchi (C):** fasi (base/costruzione/picco/defaticamento/gara/off)
  con target carb % coerente a FTWR. Calcolatore `/api/sport-science/block`.
  Fonti: Rønnestad block periodization review, Issurin.
- **Creatina (D):** sicura e benefica anche donne/atlete. Calcolatore
  `/api/sport-science/creatine` (loading 0.3 g/kg × 5-7g, mant. 3-5 g/d).
  Fonti: Kreider 2025 (ISSN), Garcia 2025, Tam 2025.
- **Wearable recovery (E):** Oura/WHOOP/Garmin — seguire trend su settimane, non
  giorno singolo; metriche valide RHR/HRV/durata sonno. Fonti: Topalidis 2024,
  Dasari 2024, Khawaja 2024, Schyvens 2025.

**Endpoint:** `/api/sport-science` (bundle), `/api/sport-science/fueling`,
`/api/sport-science/protein`, `/api/sport-science/creatine`, `/api/sport-science/block`.

---

## Privacy & dati

- Tutto in `~/.nutricoach/nutricoach.db` (SQLite). Nessun server, nessuna
  telemetria, nessun account remoto.
- L'installer (NSIS) e il `.dmg` **non toccano** la cartella dati: un
  aggiornamento non cancella clienti né misure.
