# Piano NutriCoach 1.5.0 — Prossima build (studiato, NON implementato)

**Decisione utente (2026-07-26):** fermarsi a 1.4.4. Le feature sotto sono
rimandate alla 1.5.0. Questo file è la roadmap pronta per la prossima sessione.

**Vincolo architetturale da NON violare:** NutriCoach è **100% locale**
(DB SQLite in `~/.nutricoach/`, nessun cloud). Qualsiasi feature 1.5.0 deve
restare offline-first. Niente account remoti, niente sync server a pagamento.

---

## Candidate (valutate per impatto/effort/sicurezza)

### A. Portale cliente reale (login paziente + diario lato loro)
- **Effort:** ALTO
- **Valore:** ALTO — chiude il loop "nutrizionista↔paziente" dentro l'app
- **Approccio locale:** secondo utente (ruolo `client`) nello stesso DB,
  login separato, vede solo i propri dati (diario, peso, check-in).
  Il nutrizionista "invita" il paziente generando un token/credenziali locali.
- **Rischio:** aumenta superficie (auth dua ruoli). Da fare SOLO se l'utente
  vuole davvero il portale; altrimenti il `wa.me`/`mailto` di 1.4.4 basta.

### B. Template piano riutilizzabili
- **Effort:** BASSO-MEDIO
- **Valore:** MEDIO — risparmio tempo per nutrizionisti con protocolli fissi
- **Approccio:** salva un piano generato come "template" (nome + JSON),
  ricarica su nuovo cliente (riapplica filtri condizioni).
- **Sicurezza:** niente nuovo rischio, solo lettura/scrittura DB locale.

### C. Sync multi-dispositivo (stesso utente, 2 PC)
- **Effort:** ALTO / MEDIO se via "copia archivio"
- **Valore:** MEDIO — ma viola il local-first se fatto con cloud
- **Approccio consigliato:** usare l'export/restore ZIP di 1.4.2 come
  "trasporto" manuale. Sync automatico = fuori scope (servirebbe server).

### D. Invio automatico reale WhatsApp (non solo wa.me)
- **Effort:** MEDIO (richiede API WhatsApp Business o libreria come
  `pywhatkit`/`whatsapp-web` — dipendenze pesanti, instabili)
- **Valore:** BASSO rispetto a `wa.me` (già funzionante in 1.4.4)
- **Decisione:** **SCARTATO** — `wa.me` è zero-dipendenze e fa già il lavoro.
  Non vale la complessità/rischio.

### E. Promemoria automatici (ricordi che scattano da soli)
- **Effort:** MEDIO
- **Valore:** MEDIO — oggi i reminders sono una coda statica
- **Approccio:** al login, genera reminder basati su regole
  (es. "paziente X senza check-in >7gg" → già in Home Oggi 1.4.0;
  estendere a "appuntamento tra 3gg" → già in Agenda→Oggi 1.4.2).
  Quindi **quasi già fatto**; rimane solo un toast all'apertura.

### F. Report PDF periodico (es. resoconto mensile cliente)
- **Effort:** BASSO (riusa `exportPlanPdf` / reportlab)
- **Valore:** MEDIO — utile per il paziente
- **Approccio:** bottone "Genera resoconto 30gg" nella Cartella Clinica.

---

## Raccomandazione per 1.5.0 (ordine proposto)
1. **B** Template piano (basso effort, alto risparmio tempo) — START
2. **F** Report PDF periodico (basso effort, riusa codice esistente)
3. **E** Promemoria automatici al login (quasi gratis, chiude loop)
4. **A** Portale cliente — SOLO se l'utente lo richiede esplicitamente
   (altrimenti wa.me/mailto bastano)

**Da SCARTARE:** D (WhatsApp auto), C (sync cloud).

## Verifica attesa per 1.5.0
- Ad-hoc script per ogni nuova funzione (come fatto in 1.4.x)
- Audit contratti frontend↔backend (0 orphan) prima del tag
- CI build + asset su GitHub Releases

## Come riprendere la prossima volta
1. Leggere questo file
2. Chiedere all'utente quale delle candidate (A-F) vuole → implementare
3. Bump 1.5.0, doc, commit, push, tag, CI, verifica
