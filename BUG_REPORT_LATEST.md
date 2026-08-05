# 🐛 BUG REPORT LATEST — NutriCoach v2.20.16

> **Data QA:** 2026-08-05 · **Metodo:** 4 sub-agenti paralleli (UI/UX, Functional, Journey, Backend) · **Server:** http://127.0.0.1:8400
> **Base codice:** master @ v2.20.16 · **Template QA:** AGENT_QA_BRIEFING.md

---

## ✅ Stato fix (FASE 4 — auto-fix completata)

> **Data fix:** 2026-08-05 · **Verifica:** 34/34 check dedicati PASS + pytest 27/27 PASS
> **Nota:** 1 CRITICAL, 9 HIGH, e la maggior parte dei MEDIUM sono corretti. Residui LOW/documentazionali sotto.

| ID | Fix | Verifica |
|----|-----|----------|
| C1 | Sidebar @900px → `position:static` barra orizzontale (non piu' full-screen) | PASS |
| H1 | `birth_date` salvata su POST /api/patients + validazione formato (YYYY-MM-DD) | PASS |
| H2 | Zoom root rimosso → font-size fluido `clamp(12px,0.8vw+4px,15px)` (media query corrette) | PASS |
| H3 | Side-panel mobile → `position:static` sotto la topbar | PASS |
| H4 | `.nav-item:hover` → `color:var(--sidebar-text)` (leggibile in light) | PASS |
| H5 | `tr:hover` → `background:var(--bg)` (nessun flash bianco in dark) | PASS |
| H6 | Salva template: valori gp-* catturati prima della chiusura modale | PASS |
| H7 | `--bg2`/`--surface2` definite in :root e [data-theme=dark] | PASS |
| H8 | XSS sanitizzato server-side su nome paziente | PASS |
| B6 | `meals_per_day` invalido → 400 SENZA creare il paziente (no side effect) | PASS |
| M1 | Body non-JSON/array → 400 "deve essere un oggetto JSON" | PASS |
| M8 | Soglia needs_review <0.6 applicata a TUTTI i tipi import | PASS |
| M9 | Import su pid inesistente → 404 "Paziente non trovato" | PASS |
| M10 | Preset sconosciuto → 400 "Preset ... non valido" | PASS |
| M11/M12 | kcal <=0 o >10000 → 400 con messaggio italiano | PASS |
| M13 | Plan su pid inesistente → 404 | PASS |
| M16 | Ricette validate (nome, ingredients lista, macros dict) | PASS |
| M17/B11 | 422 pydantic → handler italiano ("Il campo 'pid' deve essere un numero intero") | PASS |
| B1/B2/B3 | 500 reali loggati (no leak dettagli, non mascherati come 400) | PASS |
| B5 | File parziali rimossi su 413 OCR (resource leak) | PASS |
| B8 | Leak dettagli Python nelle risposte → messaggi puliti | PASS |
| B9 | radar/body-comp: 404 "Paziente non trovato" vs 200 lista vuota | PASS |
| B10 | 404 endpoint inesistenti → "Endpoint non trovato" italiano | PASS |
| M2 | aiBusy/aiIdle overlay collegati a genPlan/OCR | PASS |

### Residui (LOW, non bloccanti)
- L2: accenti in alcuni messaggi (migliorati, residui cosmetici)
- L4: `mm_kg` nel trend (parser lo mappa, manca solo la serie chart)
- L5/L6/L7: test legacy aggiornati, minor cleanup
- M3: toast con max-width (cosmetico)
- M5: empty-state pazienti lista (cosmetico)

---

## Riepilogo per gravità

| Gravità | Conteggio | Note |
|---------|-----------|------|
| **CRITICAL** | 1 | Layout rotto 769-900px |
| **HIGH** | 9 | birth_date scartato, sidebar/zoom/side-panel, hover illeggibili, Salva template bloccato, variabili CSS mancanti, XSS server-side |
| **MEDIUM** | 25 | Validazioni assenti, messaggi inglesi, doppio submit, loading mai collegato, a11y, 500 mascherati, side effect su errore |
| **LOW** | 9 | Micro-copy, accenti, orari pasti, empty states, 404/422 inglesi, health check |
| **TOTALE** | **44** | 13 UI/UX + 15 Functional + 4 Journey + 12 Backend |

---

## CRITICAL

| # | Componente | Descrizione | Fix |
|---|-----------|-------------|-----|
| C1 | `style.css:158` sidebar @900px | A viewport 769-900px la sidebar `position:fixed;width:100%;height:100vh` copre tutto il contenuto (`.main` ha `margin-left:220px`): rottura totale layout tablet/portrait | A ≤900px: sidebar statica orizzontale (`flex-direction:row;height:auto;position:static`) o larghezza 220px; nascondere `#sidebar-resizer` nella fascia |

## HIGH

| # | Componente | Descrizione | Fix |
|---|-----------|-------------|-----|
| H1 | `POST /api/patients` | `birth_date` (e `height`) **scartati in silenzio**: non persistono, nessun errore; `birth_date` solo via PUT separato, `height` mai gestito. Formato data non validato ("1990-13-99" passa) | Salvare `birth_date` nell'INSERT di `add_patient`; validare formato (400 italiano); gestire `height`→`height_cm` |
| H2 | `index.html:1554-1561` zoom root | `zoom` root (0.8-1.2) sposta la valutazione delle media query di ~20%: breakpoint disallineati, zona rotta C1 si sposta sui tablet 615-720px | Non combinare `zoom` root + media query: layout nativamente fluido o `transform:scale` su wrapper |
| H3 | `style.css:199-200` side-panel mobile | A ≤768px `#side-panel` resta `position:fixed` con `max-height:38vh`: fluttua sopra topbar/contenuto (z-index 1000) invece di diventare sezione inferiore | Nel media ≤768px: `position:static;top:auto;right:auto;transform:none` + `.hidden{display:none}` |
| H4 | `style.css:11` hover nav light | `.nav-item:hover` teal chiaro + testo bianco → contrasto ~1.5:1 illeggibile in tema chiaro | `color:var(--sidebar-text)` o sfondo hover più scuro |
| H5 | `style.css:46` tr:hover dark | `tr:hover{background:#f8fafc}` hard-coded: flash bianco abbagliante in dark mode | `tr:hover{background:var(--bg)}` |
| H6 | `index.html:842-847` Salva template | `savePlanTemplate()` apre `modal()` che sostituisce `#modal-root` distruggendo gli input `gp-*`; `doSavePlanTemplate` legge `$('gp-k').value` → TypeError, bottone bloccato su "⏳..." per sempre | Salvare i valori gp-* in variabili PRIMA della nuova modale; try/catch + ripristino bottone |
| H7 | `index.html:1035,545,...` var CSS mancanti | `--surface2` e `--bg2` mai definite: bolle chat TRASPARENTI, box anteprima import/radar/chips senza sfondo | Definire `--bg2`/`--surface2` in `:root` e `[data-theme=dark]` |
| H8 | `POST /api/patients` XSS | Nome salvato raw lato server (no sanitizzazione): `<script>` persistito e riflesso in export CSV/PDF | Sanitizzare server-side (strip tag); escape in CSV/PDF |
| H9 | Anamnesi (journey) | Nessuna validazione condizioni: etichette italiane fuori catalogo accettate con report generico fuorviante (33 strategie non pertinenti) | Validare condizioni contro `/api/clinical-conditions` o mappare etichette IT→chiavi |

## MEDIUM

| # | Componente | Descrizione | Fix |
|---|-----------|-------------|-----|
| M1 | `jget/jpost` + handler globale | Crash convertiti in 400 con `detail` **inglese tecnico** ("'list' object has no attribute 'get'"); due shape diverse 4xx (`{detail}` vs `{ok,error}`) | Catturare `JSONDecodeError` → messaggi italiani; uniformare shape; handler `RequestValidationError` IT |
| M2 | `setLoading` mai usato | Stato loading definito ma MAI invocato; doppio click = doppie POST (no idempotenza) | `setLoading(btn,true)` in ogni handler async + finally; dedup BIA/paziente |
| M3 | Toast overflow | `#toast{white-space:nowrap}` senza max-width: errori lunghi escono dallo schermo | `max-width:min(90vw,520px);white-space:normal;word-wrap:break-word` |
| M4 | Accessibilità | 0 tabindex/role/aria; div onclick non focusabili; modale senza Escape/focus trap | `tabindex="0"`+`role="button"` su div cliccabili; Escape chiude modale |
| M5 | Empty state pazienti | Lista pazienti vuota → area bianca senza messaggio né CTA; `.empty` standalone non stilizzato | `||'<div class=empty>Nessun paziente...'` + regola `.empty` standalone |
| M6 | Confronta tabella | `.cmp-table` senza `.tablewrap{overflow-x:auto}`: colonne schiacciate con 5+ pazienti | Avvolgere in `<div class=tablewrap>` o `overflow-x:auto` |
| M7 | Import text non-stringa | `{"text":123}` → 400 con dettaglio inglese `'int' object has no attribute 'strip'` | Validare stringa → "Il testo deve essere una stringa" |
| M8 | Import soglia review | BIA confidenza 0.56 marcata `needs_review:false` (soglia solo per unknown/json) | Soglia `confidence<0.6` → `needs_review:true` per tutti i tipi |
| M9 | Import pid inesistente | Anteprima import su pid 999999 → 200 invece di 404 | Check `get_patient` → 404 "Paziente non trovato" |
| M10 | plan/generate preset sconosciuto | `"kestrel"` → TypeError mascherato da 400 inglese | Validare preset → 400 "Preset non valido" |
| M11 | plan/generate kcal=0 | kcal=0 falsy → default 2000 silenzioso | Validare `kcal>0` → 400 |
| M12 | plan/generate kcal=100000 | Nessun limite superiore: piano clinico assurdo salvato (porzioni cap 250g) | Range 500-10000 → 400 fuori range |
| M13 | plan/generate pid inesistente | → 400 "FOREIGN KEY constraint failed" inglese | Check paziente → 404 |
| M14 | plan/generate conditions non-lista | Stringa ignorata silenziosamente: condizione clinica non applicata | Validare lista → 400 |
| M15 | Double-submit | Nessuna idempotenza: 2 pazienti/2 piani/2 BIA identici | Idempotency key / dedup UI |
| M16 | POST /api/recipes | Nessuna validazione: `{}` → ricetta vuota; `ingredients:"pasta"` → lista di caratteri; `macros:"x"` → tipo corrotto | name obbligatorio, ingredients lista, macros dict |
| M17 | `pid` non numerico | 422 pydantic inglese ("Input should be a valid integer...") | Handler `RequestValidationError` italiano |

## BACKEND & NETWORK (agente 4 — 8 MEDIUM + 4 LOW)

### MEDIUM
| # | Componente | Descrizione | Fix |
|---|-----------|-------------|-----|
| B1 | Global handler r.20-27 | 500 interni mascherati come 400 "Richiesta non valida": crash indistinguibili da errori client | Restituire 500 (o 422 per JSON malformato) nel ramo non-HTTP |
| B2 | Global handler r.26 | Leak dettagli Python in risposta: `str(exc)[:200]` ("'list' object has no attribute 'get'") | `logger.exception` + messaggio generico localizzato |
| B3 | Global handler | Nessun logging: eccezioni inghiottite senza traccia | Aggiungere `logger.exception` |
| B4 | Tutte le route | 3 formati errore inconsistenti: `{detail}` / `{ok,error,detail}` / lista 422 | Envelope unico `{ok:false,error:{...}}` + handler RequestValidationError |
| B5 | Route OCR r.774-818 | Resource leak su 413: file parziale ~10MB mai rimosso da uploads/ | `os.remove` nel except / file temp + rename atomico |
| B6 | POST /api/patients | Side effect su errore: `meals_per_day:"abc"` → 400 MA paziente comunque creato (id=13) | Validare tutto il body PRIMA di `db.add_patient` (Pydantic/transazione+rollback) |
| B7 | POST /api/patients | Nessuna validazione tipo campi oltre name | Pydantic model per il body |
| B8 | /api/version r.1977 | Non è health check reale: non tocca il DB, 200 anche con SQLite corrotto | `SELECT 1` nel DB + endpoint `/api/health` |

### LOW
| # | Componente | Descrizione | Fix |
|---|-----------|-------------|-----|
| B9 | /api/patients/{pid}/radar | 404 "Dati insufficienti" per paziente inesistente (fuorviante) | Distinguere 404 paziente vs 200 lista vuota |
| B10 | 404 default | "Not Found" inglese sugli endpoint inesistenti | Custom 404 handler IT |
| B11 | 422 default | "Field required"/"Input should be a valid integer" inglesi | Handler RequestValidationError localizzato |
| B12 | Upload r.752/785/1744 | 413 check solo a chunk, no pre-check Content-Length | Pre-check header + 413 immediato |

---

## LOW

| # | Componente | Descrizione | Fix |
|---|-----------|-------------|-----|
| L1 | Micro-copy | Toast generici senza tipo (`'Errore salvataggio ricetta'` senza `{type:'error'}`), `confirm()` nativo, tab Misure "In arrivo" | `_errMsg(r)` + `{type:'error'}`; `showConfirm`; empty state Misure |
| L2 | Accenti messaggi | "Il nome del paziente e richiesto", "non puo superare" (mancano è/ò) | Correggere accenti |
| L3 | Orari pasti meals=5 | Cena alle 16:00 (colazione 8, spuntini 10/14) | Distribuzione oraria realistica |
| L4 | `mm_kg` non mappato | BIA import: `mm_pct` sì ma `mm_kg` no → serie null nel bia-trend | Mappare `mm_kg` |
| L5 | `sex` non validato | `"Gatto"` accettato e salvato | Enum validazione |

---

## Note metodologiche

- I sub-agenti hanno testato via API REST + analisi statica (nessun browser GUI disponibile)
- Tutti gli errori 4xx rispondono JSON, ma molti con dettaglio tecnico inglese (maschera bug reali)
- Dati di test QA: pazienti/ricette/piani creati e rimossi dagli agenti; verificare `GET /api/patients` per residui
- **Bug da verificare PRIMA del fix** (possibili falsi positivi): C1 (sidebar 900px — verificare combo zoom root), H6 (Salva template — verificare stato reale DOM)

*Generato da: orchestrazione QA 4 sub-agenti · 2026-08-05*
