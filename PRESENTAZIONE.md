# NutriCoach — Presentazione

![NutriCoach](assets/icon.png)

> **Gestionale di nutrizione per nutrizionisti. 100% locale, nessun cloud, nessun abbonamento.** — Versione **1.5.4**

---

## Il problema
Il nutrizionista moderno gestisce decine di clienti: piani alimentari, misure
corporali, esami BIA, follow-up, appuntamenti. I software esistenti sono spesso
a pagamento, basati su cloud, e obbligano a caricare i dati sensibili dei
pazienti su server di terze parti. Per un professionista italiano questo è un
problema di **privacy** (GDPR) oltre che di costo.

## La soluzione
**NutriCoach** è un gestionale **desktop, locale, gratuito e open source** che
fa tutto il lavoro di studio senza mai mandare un byte fuori dal computer. E si
**aggiorna da solo** da GitHub Releases.

> *"Tutti i tuoi clienti, tutti i loro dati, nel tuo PC. Niente cloud, niente abbonamenti."*

---

## Per chi è fatto
- Nutrizionisti e dietisti che vogliono uno strumento proprio, portatile e privato
- Studi che già lavorano con PDF dieta / referti InBody e vogliono digitalizzare
- Professionisti attenti alla privacy dei dati dei pazienti
- Atleti / amatoriali che vogliono strategie pro adattate (vedi Scienza Sport)

---

## Cosa fa — mappa rapida

| Cosa | Come |
|------|------|
| Gestione clienti | Dashboard stile Nutrium: statistiche studio + lista pazienti; scheda paziente a 8 sezioni (Anamnesi, Misure, Dieta, Referti, Appuntamenti, Sintomi, Integratori, Progressi) |
| **Clinical Nutrition** | **23 condizioni** cliniche (IBS/FODMAP, SIBO, IBD, GERD, celiachia, NCGS, allergie IgE, EoE, lattosio, endometriosi, MASLD, PCOS, istamina…) con strategie evidence-based 2024-2026, conflitti tra condizioni, integratori e protocolli phased |
| **Pattern Dietetici** | 7 pattern evidence-based (Mediterranea, DASH, MIND, Portfolio, basso IG, RPAH/FAILSAFE, Supporto Barriera) con suggerimento automatico per condizione |
| **Cartella Clinica** | Tab unico per cliente: condizioni → conflitti → esclusioni → integratori → fase dieta → sintomi → trend peso, tutto in un colpo d'occhio |
| Dieta da PDF | Import con alternative + grammi; **OCR su scansioni** (Tesseract bundlato); spesa, riepilogo, export HTML/PDF |
| Diario alimentare | Builder manuale + ricerca alimenti + micro automatici; **AI pattern** + **reintroduzione FODMAP guidata** (ordine Monash) |
| Pianificazione | Settimana bilanciata dai target (kcal/P/C/F) che **filtra automaticamente le esclusioni cliniche** + **preset dieto** + export PDF clinico |
| Scienza Sport | Tab con strategie pro→amatoriali (proteina, gut training, blocchi, creatina, wearable) + report PDF |
| BIA | Referti InBody/Tanita da paste o PDF (anche scansionati/OCR), parsing robusto |
| Antropometria | BMR, % grasso, WHR, FFMI |
| Onboarding | **Wizard anamnesi 4-step** (anagrafica → obiettivi → clinica → conferma) che crea il cliente e popola l'anamnesi |
| Follow-up | Notifiche configurabili, agenda, messaggi, progressi; **invio reale Email/WhatsApp** dalla finestra nativa |
| Sicurezza | Login locale PBKDF2, dati solo su `~/.nutricoach/` |
| Auto-aggiornamento | Banner all'avvio + install silenzioso su Windows da GitHub Releases |

---

## Cosa lo rende diverso
1. **Single Source of Truth** — un solo motore di calcolo; diario, piano e
   riepilogo sono *viste* coerenti, mai numeri discordanti.
2. **Parsing "sporco"-friendly** — incolli il referto BIA dal PDF e NutriCoach
   riconosce peso, massa grassa, angolo di fase anche se il testo è su una
   colonna sola o pieno di parentesi.
3. **OCR reale** — i PDF scansionati vengono letti con Tesseract, bundlato
   dentro l'EXE/dmg (nessuna installazione separata).
3b. **Clinical Nutrition pronta all'uso** — 23 condizioni con strategie
   evidence-based 2024-2026; il piano si **filtra da solo** per le esclusioni
   del cliente (FODMAP, istamina, allergie, integratori) senza errori manuali.
3c. **Cartella Clinica unificata** — condizioni, conflitti, esclusioni,
   integratori, fase dieta e trend in un unico tab per cliente.
3d. **AI pattern + reintroduzione FODMAP guidata** — dal diario emerge il
   pattern sintomi e il prossimo passo di reintroduzione (ordine Monash 2025).
4. **Micronutrienti inclusi** — non solo macro: calcio, ferro, vitamina C,
   potassio e magnesio aggregati automaticamente.
5. **Pianificazione automatica + preset** — dai i target o scegli un tipo di
   dieta; ottieni una settimana di pasti bilanciati (già filtrata clinicamente),
   non solo una tabella.
6. **Scienza Sport documentata** — strategie del mondo elite (WorldTour,
   calcio pro) con calcolatori e fonti 2024-2026, adattate ad amatoriale/semi-pro.
7. **Tutto offline + auto-update** — login locale PBKDF2, SQLite locale, e
   aggiornamenti automatici dalla release GitHub senza perdere i dati.

---

## Demo rapida
1. Avvia `NutriCoach` (release scaricata o `python run.py`)
2. Crea il tuo account nutrizionista
3. Clicca **+ Nuovo paziente** → compila il **Wizard anamnesi 4-step** (anagrafica → obiettivi → condizioni cliniche/allergie → conferma) → il cliente è creato con l'anamnesi popolata
4. Dalla **Dashboard** clicca un paziente → si apre la **scheda a 8 sezioni**
5. Tab **Misure**: registra peso/BIA o importa un referto PDF (OCR su scansioni)
6. Tab **Dieta → Pianifica per periodo**: scegli *data inizio* + *data fine* → il numero di settimane è calcolato automaticamente → **Genera piano** (già filtrato per le esclusioni cliniche del cliente)
7. Tab **Referti**: carica un PDF BIA / incolla il testo OCR
8. Tab **Appuntamenti**: aggiungi un controllo; da **Agenda** (sidebar) vedi tutti quelli aperti
9. Dalla scheda paziente clicca **✉️ Email** o **💬 WhatsApp** per contattare il cliente (parte dal tuo PC via bridge nativo)

---

## Installazione & piattaforme
- **Windows**: `NutriCoach-Setup-x.y.z.exe` (installer) oppure `NutriCoach.exe` portatile
- **macOS**: `NutriCoach-x.y.z.dmg` → trascina in Applicazioni
- **Sorgente**: `pip install -r requirements.txt && python run.py`

Tutte le piattaforme salvano i dati in `~/.nutricoach/` (rispettivamente
`%USERPROFILE%\.nutricoach\` su Windows, `~/Library`/home su Mac). L'auto-aggiornamento
**non cancella** i dati utente.

---

## Roadmap
- [x] Invio notifiche reale (WhatsApp/Email) via client locali / bridge pywebview
- [ ] Integrazione wearable (import HRV/sonno da export Oura/WHOOP)
- [ ] App mobile lato cliente + sync opzionale (richiede infrastruttura esterna)
- [ ] Codici a barre / scansione etichette

*(Le voci che richiedono cloud/esterne sono opzionali rispetto al core locale.)*

---

© 2026 Filippo Siviglia — NutriCoach · Licenza MIT
