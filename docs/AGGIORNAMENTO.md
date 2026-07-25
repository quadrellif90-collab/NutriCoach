# Aggiornamento e Release — NutriCoach

Guida operativa per pubblicare una nuova versione e per capire come funziona
l'auto-aggiornamento lato utente.

## 1. Per l'utente (auto-aggiornamento)

NutriCoach si aggiorna **da solo** quando esce una nuova release su GitHub:

1. All'avvio l'app chiama `GET /api/self-update/check` che legge
   `https://api.github.com/repos/quadrellif90-collab/NutriCoach/releases/latest`.
2. Confronta la versione remota con `version.py` (`VERSION`).
3. Se c'è una versione più nuova, compare il **banner "Aggiornamento disponibile"**
   con il bottone **Aggiorna**.
4. Cliccando, l'app scarica l'asset corretto per il sistema operativo e, su
   **Windows**, lancia l'installer in silenzioso (`/S`) — i dati in
   `~/.nutricoach/` **non vengono toccati**.
5. L'app si riavvia sulla nuova versione.

> **Mac**: il `.dmg` non supporta l'install silenziosa. L'utente deve trascinare
> `NutriCoach.app` in Applicazioni (il banner segnala comunque la novità).

> Limite di rate GitHub: ~60 richieste/h per IP anonimo; sufficiente per il
> check all'avvio. Nessun account né token richiesto.

## 2. Per lo sviluppatore (fare una release)

Tutto è automatizzato da GitHub Actions al push di un **tag `vX.Y.Z`**.

### Passi
1. Fai le modifiche e committa su `master`.
2. **Bumpa la versione** in `version.py` (`VERSION = "X.Y.Z"`) — deve combaciare
   col tag. Questo è l'unico punto critico: se `version.py` e il tag divergono,
   l'auto-update non si attiva (o si attiva sempre).
3. Pusha:
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
4. La CI (`Build NutriCoach (Windows + macOS)`) parte automaticamente:
   - Installa Tesseract (Windows `choco`, Mac `brew`) e lo **bundla** nell'EXE/dmg.
   - Builda l'EXE one-file (PyInstaller, `console=False`, icona inclusa).
   - Windows: NSIS genera `NutriCoach-Setup-vX.Y.Z.exe`.
   - Mac: `.app` + `hdiutil` genera `NutriCoach-vX.Y.Z.dmg`.
   - Crea la **GitHub Release** `vX.Y.Z` e allega i 3 asset.
5. Verifica su GitHub che la release esista e che gli asset siano 3.

### Asset della release
| File | Piattaforma | Note |
|------|-----------|------|
| `NutriCoach-Setup-vX.Y.Z.exe` | Windows | Installer NSIS, `/S` silenzioso per auto-update |
| `NutriCoach.exe` | Windows | Portabile, estrai e avvia |
| `NutriCoach-vX.Y.Z.dmg` | macOS | Trascina in Applicazioni |

### Convenzioni di versione
- `MAJOR`: cambi non retrocompatibili o restyling.
- `MINOR`: nuove funzionalà (es. 1.0.0 → 1.1.0: OCR + Scienza Sport).
- `PATCH`: bug fix.

### Rollback / hotfix
Se una release è difettosa:
- Puoi eliminare il tag (`git tag -d vX.Y.Z && git push :refs/tags/vX.Y.Z`),
  correggere, e ricrearlo. La CI ricostruisce e sovrascrive la release.
- Gli utenti già aggiornati a una versione rotta torneranno a vedere il banner
  solo quando uscirà una versione **superiore**.

## 3. File coinvolti

| File | Ruolo |
|------|-------|
| `version.py` | Versione corrente (sorgente di verità per l'auto-update) |
| `app.py` | Endpoint `/api/self-update/check`, `/api/self-update/apply` |
| `run.py` | Check all'avvio (thread non bloccante) + log |
| `templates/dashboard.html` | Banner `#update-banner`, `checkUpdate()`/`applyUpdate()` |
| `.github/workflows/build.yml` | Build Win+Mac, bundling Tesseract, release |
| `installer.nsi` | Installer Windows (icona, `/S`) |
| `NutriCoach.spec` | Config PyInstaller (icona, hiddenimports, tesseract datas) |
| `CHANGELOG.md` | Registro versioni |

## 4. Dati utente
L'installer e l'auto-update **non cancellano** `%USERPROFILE%\.nutricoach\`
(Windows) / `~/.nutricoach/` (Mac). Un aggiornamento non fa perdere clienti né
misure. Backup consigliato prima di grossi cambi: copia della cartella `.nutricoach`.
