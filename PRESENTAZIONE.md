# NutriCoach — Presentazione

## Il problema
Il nutrizionista moderno gestisce decine di clienti: piani alimentari, misure
corporali, esami BIA, follow-up, appuntamenti. I software esistenti sono spesso
a pagamento, basati su cloud, e obbligano a caricare i dati sensibili dei
pazienti su server di terze parti. Per un professionista italiano questo è un
problema di **privacy** (GDPR) oltre che di costo.

## La soluzione
**NutriCoach** è un gestionale **desktop, locale, gratuito e open source** che
fa tutto il lavoro di studio senza mai mandare un byte fuori dal computer.

> "Tutti i tuoi clienti, tutti i loro dati, nel tuo PC. Niente cloud, niente abbonamenti."

---

## Per chi è fatto
- Nutrizionisti e dietisti che vogliono uno strumento proprio, portabile e privato
- Studi che già lavorano con PDF dieta / referti InBody e vogliono digitalizzare
- Professionisti attenti alla privacy dei dati dei pazienti

---

## Cosa lo rende diverso
1. **Single Source of Truth** — un solo motore di calcolo; diario, piano e
   riepilogo sono *viste* coerenti, mai numeri discordanti.
2. **Parsing "sporco"-friendly** — incolli il referto BIA dal PDF e NutriCoach
   riconosce peso, massa grassa, angolo di fase anche se il testo è su una
   colonna sola o pieno di parentesi.
3. **Micronutrienti inclusi** — non solo macro: calcio, ferro, vitamina C,
   potassio e magnesio aggregati automaticamente.
4. **Pianificazione automatica** — dai i target e ottieni una settimana di pasti
   bilanciati, non solo una tabella di numeri.
5. **Tutto offline** — login locale con hash PBKDF2, database SQLite locale.

---

## Demo rapida
1. Avvia `NutriCoach` (release scaricata o `python run.py`)
2. Crea il tuo account nutrizionista
3. Aggiungi un cliente → **Importa** il PDF dieta → vedi spesa e riepilogo
4. Incolla un referto BIA → vedi massa grassa / angolo di fase
5. Vai su **Pianifica** → genera una settimana automatica dai target
6. Usa **Agenda** per appuntamenti, **Messaggi** per il thread, **Notifiche**
   per i follow-up

---

## Roadmap
- [ ] App mobile lato cliente + sync (richiede infrastruttura opzionale)
- [ ] Codici a barre / scansione etichette
- [ ] Integrazione wearable (esportazione/importazione)
- [ ] Calendario appuntamenti con promemoria automatici

*(Le prime tre richiedono componenti cloud/esterne e sono opzionali rispetto
al core locale.)*

---

© 2026 Filippo Siviglia — NutriCoach · Licenza MIT
