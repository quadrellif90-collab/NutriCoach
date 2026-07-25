# NutriCoach — Presentazione

![NutriCoach](assets/icon.png)

> **Gestionale di nutrizione per nutrizionisti. 100% locale, nessun cloud, nessun abbonamento.** — Versione **1.1.0**

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
| Gestione clienti | Anagrafica, ricerca, confronto tra due clienti; sesso M/F + obiettivo come selettori |
| Dieta da PDF | Import con alternative + grammi; **OCR su scansioni** (Tesseract bundlato); spesa, riepilogo, export HTML/PDF |
| Diario alimentare | Builder manuale + ricerca alimenti + micro automatici |
| Pianificazione | Settimana bilanciata dai target (kcal/P/C/F) + **preset dieto** (Mediterranea, Zona, CKD, Carb Cycling, Alto Proteico, Vegano, Keto, Personalizzato) |
| Scienza Sport | Tab con strategie pro→amatoriali (proteina, gut training, blocchi, creatina, wearable) + report PDF |
| BIA | Referti InBody/Tanita da paste o PDF (anche scansionati/OCR), parsing robusto |
| Antropometria | BMR, % grasso, WHR, FFMI |
| Follow-up | Notifiche configurabili, agenda, messaggi, acqua, progressi |
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
4. **Micronutrienti inclusi** — non solo macro: calcio, ferro, vitamina C,
   potassio e magnesio aggregati automaticamente.
5. **Pianificazione automatica + preset** — dai i target o scegli un tipo di
   dieta; ottieni una settimana di pasti bilanciati, non solo una tabella.
6. **Scienza Sport documentata** — strategie del mondo elite (WorldTour,
   calcio pro) con calcolatori e fonti 2024-2026, adattate ad amatoriale/semi-pro.
7. **Tutto offline + auto-update** — login locale PBKDF2, SQLite locale, e
   aggiornamenti automatici dalla release GitHub senza perdere i dati.

---

## Demo rapida
1. Avvia `NutriCoach` (release scaricata o `python run.py`)
2. Crea il tuo account nutrizionista
3. Aggiungi un cliente (sesso + obiettivo) → **Importa** il PDF dieta → vedi spesa e riepilogo
4. Incolla un referto BIA (o carica un PDF scansionato: OCR automatico) → massa grassa / angolo di fase
5. Vai su **Pianifica** → scegli un preset dieta o i target → settimana automatica
6. Apri **Scienza Sport** → calcola distribuzione proteica / gut training / blocchi / creatina
7. Usa **Agenda** per appuntamenti, **Messaggi** per il thread, **Notifiche** per i follow-up

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
- [ ] Invio notifiche reale (WhatsApp/Email) via client locali
- [ ] Integrazione wearable (import HRV/sonno da export Oura/WHOOP)
- [ ] App mobile lato cliente + sync opzionale (richiede infrastruttura esterna)
- [ ] Codici a barre / scansione etichette

*(Le voci che richiedono cloud/esterne sono opzionali rispetto al core locale.)*

---

© 2026 Filippo Siviglia — NutriCoach · Licenza MIT
