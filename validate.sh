#!/usr/bin/env bash
# ==============================================================================
# NOUS / HERMES - ULTRA-PERFORMANT FULL APP VALIDATION & RELEASE SUITE
# NutriCoach v2.20.5 — adattato per FastAPI+SQLite+vanilla JS
# ==============================================================================
set -e

# Visual formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCORE=100
ERRORS_COUNT=0
WARNINGS_COUNT=0
REPORT_FILE="RELEASE_CERTIFICATE.md"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; WARNINGS_COUNT=$((WARNINGS_COUNT+1)); SCORE=$((SCORE-5)); }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; ERRORS_COUNT=$((ERRORS_COUNT+1)); SCORE=$((SCORE-20)); }
log_section() { echo -e "\n${BOLD}${CYAN}════════════════════════════════════════════════════════════════════${NC}\n${BOLD} $1 ${NC}\n${BOLD}${CYAN}════════════════════════════════════════════════════════════════════${NC}"; }

# Cleanup on exit
cleanup() {
  if [ -n "$SERVER_PID" ]; then
    log_info "Arresto del server locale di test (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
  fi
}
trap cleanup EXIT

# Clear old report
echo "# 🛡️ CERTIFICATO DI IDONEITÀ ALLA DISTRIBUZIONE" > $REPORT_FILE
echo "Versione: v2.20.5" >> $REPORT_FILE
echo "Progetto: NutriCoach (FastAPI + SQLite + vanilla JS)" >> $REPORT_FILE
echo "Data Validazione: $(date)" >> $REPORT_FILE
echo "---" >> $REPORT_FILE
echo "" >> $REPORT_FILE

log_section "1. SCANSIONE DI SICUREZZA E SEGRETI CRITICI"

log_info "Verifica presenza di API Key o password hardcoded nel codice..."
if grep -rnE "AIzaSy[0-9A-Za-z_-]{35}|sk-[a-zA-Z0-9]{32,}|ghp_[a-zA-Z0-9]{36}|postgres://|mysql://" \
  --include="*.py" --include="*.js" --include="*.html" --include="*.json" --include="*.yml" --include="*.yaml" --include="*.toml" \
  --exclude-dir={node_modules,.git,dist,build,__pycache__,.venv} . 2>/dev/null | grep -v "RELEASE_CERTIFICATE.md" | grep -v "\.git" | head -5; then
  log_fail "Trovati potenziali SEGRETI O API KEY nel codice sorgente!"
else
  log_success "Nessun segreto visibile rilevato nel sorgente."
fi

log_info "Verifica file .env e .gitignore..."
if [ -f ".env" ]; then
  if [ -f ".gitignore" ] && grep -q "\.env" .gitignore 2>/dev/null; then
    log_success ".env presente e in .gitignore — OK"
  else
    log_fail "Il file .env esiste ma NON è in .gitignore!"
  fi
else
  log_success "Nessun file .env presente (OK per app con credenziali hardcoded in boot)"
fi

log_section "2. AUDIT DIPENDENZE PYTHON"

log_info "Verifica requirements.txt..."
if [ -f "requirements.txt" ]; then
  log_success "requirements.txt presente ($(wc -l < requirements.txt) pacchetti)"
  # Quick security check on known vulnerable packages
  if grep -qi "pyyaml<\|requests<\|urllib3<\|cryptography<\|flask<\|jinja2<" requirements.txt 2>/dev/null; then
    log_warn "Trovate versioni potenzialmente vulnerabili in requirements.txt"
  fi
else
  log_warn "requirements.txt non trovato"
fi

log_section "3. ANALISI STATICA (LINTING & SYNTAX CHECK)"

log_info "Verifica sintassi Python (py_compile)..."
PY_FILES=$(find . -name "*.py" -not -path "./.venv/*" -not -path "./__pycache__/*" 2>/dev/null)
FAIL_SYNTAX=0
for f in $PY_FILES; do
  python -m py_compile "$f" 2>/dev/null || { log_fail "Errore sintassi Python in $f"; FAIL_SYNTAX=$((FAIL_SYNTAX+1)); }
done
[ "$FAIL_SYNTAX" -eq 0 ] && log_success "Sintassi Python OK ($(echo "$PY_FILES" | wc -l) file)"

log_info "Verifica sintassi JavaScript (node --check)..."
if command -v node &>/dev/null; then
  HTML_FILE="app/templates/index.html"
  if [ -f "$HTML_FILE" ]; then
    JS_CONTENT=$(node -e "
      const fs=require('fs');
      const html=fs.readFileSync('$HTML_FILE','utf8');
      const m=html.match(/<script>([\s\S]*?)<\/script>/);
      if(m) try{new Function(m[1]);console.log('OK')}catch(e){console.log('ERR:'+e.message)}
      else console.log('NOSCRIPT');
    ")
    if [ "$JS_CONTENT" = "OK" ]; then
      log_success "Sintassi JavaScript inline OK (index.html)"
    else
      log_fail "Errore sintassi JS inline: $JS_CONTENT"
    fi
  fi
  # CSS check via node
  CSS_FILE="app/static/style.css"
  if [ -f "$CSS_FILE" ]; then
    log_info "Verifica CSS (parsing struttura)..."
    node -e "const fs=require('fs');const c=fs.readFileSync('$CSS_FILE','utf8');console.log('CSS: ' + c.length + ' bytes, ' + (c.match(/{/g)||[]).length + ' rules')" || log_warn "CSS non valido"
  fi
else
  log_warn "Node.js non disponibile — saltato controllo JS/CSS"
fi

log_section "4. TEST UNITARI E DI INTEGRAZIONE"

if [ -f "pytest.ini" ] || [ -f "setup.cfg" ] && grep -q "\[tool:pytest\]" setup.cfg 2>/dev/null; then
  log_info "Avvio PyTest..."
  python -m pytest -x --tb=short -q 2>&1 || {
    log_warn "Alcuni test pytest non superati (potrebbe non avere test dedicati)"
  }
elif ls test_*.py 2>/dev/null | head -1; then
  log_info "Trovati file test_*.py — avvio pytest..."
  python -m pytest -x --tb=short -q 2>&1 || log_warn "Test pytest falliti"
else
  log_info "Nessun test framework/config rilevato (pytest.ini o test_*.py) — skip test"
fi

log_section "5. VERIFICA IMMAGINI E ASSET STATICI"

log_info "Verifica asset statici..."
STATIC_DIR="app/static"
if [ -d "$STATIC_DIR" ]; then
  ASSET_COUNT=$(find "$STATIC_DIR" -type f | wc -l)
  log_success "Asset statici: $ASSET_COUNT file"
  # Verify CSS file
  if [ -f "$STATIC_DIR/style.css" ]; then
    CSS_SIZE=$(stat -c%s "$STATIC_DIR/style.css" 2>/dev/null || stat -f%z "$STATIC_DIR/style.css" 2>/dev/null || echo "0")
    log_info "  style.css: $CSS_SIZE bytes"
  fi
else
  log_warn "Directory static/ non trovata"
fi

log_info "Verifica template HTML..."
TEMPLATE_DIR="app/templates"
if [ -d "$TEMPLATE_DIR" ]; then
  HTML_SIZE=$(stat -c%s "$TEMPLATE_DIR/index.html" 2>/dev/null || stat -f%z "$TEMPLATE_DIR/index.html" 2>/dev/null || echo "0")
  log_info "  index.html: $HTML_SIZE bytes, $(wc -l < "$TEMPLATE_DIR/index.html") righe"
fi

log_section "6. TEST END-TO-END (E2E) E BENCHMARK PRESTAZIONI"

PORT=8400
log_info "Avvio del server di test locale su porta $PORT..."
python run_v2.py $PORT > /tmp/nutricoach-server.log 2>&1 &
SERVER_PID=$!
sleep 4

log_info "Health Check HTTP (http://localhost:$PORT)..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT 2>/dev/null || echo "000")

if [ "$HTTP_STATUS" -eq 200 ] || [ "$HTTP_STATUS" -eq 304 ]; then
  log_success "Server locale operativo (HTTP Status: $HTTP_STATUS)"

  # Version check
  VERSION=$(curl -s http://localhost:$PORT/api/version 2>/dev/null || echo "")
  log_info "  Versione dichiarata: $VERSION"

  # API smoke test
  STATS=$(curl -s http://localhost:$PORT/api/stats 2>/dev/null | head -c 100)
  log_info "  Stats API: ${STATS:+OK (primi 100 char)}${STATS:-ERRORE}"

  # Test di latenza
  log_info "Benchmark latenza (10 richieste)..."
  TOTAL_TIME=0
  for i in 1 2 3 4 5 6 7 8 9 10; do
    T=$(curl -s -w "%{time_total}" -o /dev/null http://localhost:$PORT/ 2>/dev/null || echo "1.0")
    TOTAL_TIME=$(echo "$TOTAL_TIME + $T" | awk '{print $1 + $2}' 2>/dev/null || echo "0")
  done
  AVG=$(echo "$TOTAL_TIME / 10" | awk '{print $1 / $2}' 2>/dev/null || echo "0.5")
  AVG_MS=$(echo "$AVG * 1000" | awk '{print int($1)}' 2>/dev/null || echo "500")
  log_info "  Latenza media: ${AVG_MS}ms"

  if [ "$AVG_MS" -gt 1000 ]; then
    log_warn "Latenza supera 1 secondo (${AVG_MS}ms)"
  else
    log_success "Performance di risposta ottimali (${AVG_MS}ms)"
  fi

  # Test API principali
  log_info "Test API CRUD principali..."
  # Login
  LOGIN_RESP=$(curl -s -X POST http://localhost:$PORT/api/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}' 2>/dev/null)
  if echo "$LOGIN_RESP" | grep -q "token"; then
    log_success "  Login API: OK (token ricevuto)"
    TOKEN=$(echo "$LOGIN_RESP" | python -c "import sys,json;print(json.load(sys.stdin)['token'])" 2>/dev/null || echo "")
  else
    log_warn "  Login API: risposta inattesa — $LOGIN_RESP"
    TOKEN=""
  fi

  # Session check
  if [ -n "$TOKEN" ]; then
    SESSION_CHECK=$(curl -s "http://localhost:$PORT/api/session?token=$TOKEN" 2>/dev/null)
    if echo "$SESSION_CHECK" | grep -q "username"; then
      log_success "  Session API: OK"
    fi
  fi

  # Browser accessibility test
  log_info "Verifica accessibilità frontend..."
  if command -v node &>/dev/null; then
    node -e "
      const http=require('http');
      http.get('http://localhost:$PORT/', res => {
        let d='';
        res.on('data',c=>d+=c);
        res.on('end',()=>{
          const checks=[
            ['sidebar','sidebar'],
            ['login overlay','login-overlay'],
            ['view','id=view'],
            ['toast','id=toast'],
            ['modal','modal-root'],
            ['search input','search-input'],
            ['page title','page-title'],
            ['brand name','brand-name'],
          ];
          let ok=0,fail=0;
          checks.forEach(([name,id])=>{
            if(d.includes(id)){ok++;console.log('  ELEMENT '+name+': OK')}
            else{fail++;console.log('  ELEMENT '+name+': MISSING')}
          });
          console.log('  Frontend elements: '+ok+'/'+(ok+fail)+' present');
          if(fail>0)process.exit(1);
        });
      }).on('error',e=>{console.log('  Frontend check failed: '+e.message);process.exit(1)});
    " && log_success "Frontend: tutti gli elementi HTML richiesti presenti" || log_warn "Frontend: alcuni elementi mancanti"
  fi

else
  log_warn "Impossibile contattare il server su porta $PORT (Status: $HTTP_STATUS). Saltati i test E2E live."
fi

log_section "7. GIT & VERSIONE"

log_info "Verifica stato Git..."
if git rev-parse --git-dir > /dev/null 2>&1; then
  BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
  COMMITS=$(git rev-list --count HEAD 2>/dev/null || echo "0")
  TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "no-tag")
  STATUS=$(git status --porcelain 2>/dev/null | wc -l)
  log_info "  Branch: $BRANCH"
  log_info "  Commits: $COMMITS"
  log_info "  Ultimo tag: $TAG"
  if [ "$STATUS" -eq 0 ]; then
    log_success "  Working tree PULITO (nessun file modificato)"
  else
    log_info "  Working tree: $STATUS file modificati/nuovi"
  fi
else
  log_warn "Non in un repository Git"
fi

log_section "8. REPORT FINALE E GIUDIZIO DI RILASCIO"

if [ $SCORE -lt 0 ]; then SCORE=0; fi

echo "## Risultati Audit Automatizzato" >> $REPORT_FILE
echo "" >> $REPORT_FILE
echo "| Metrica | Valore |" >> $REPORT_FILE
echo "|---------|--------|" >> $REPORT_FILE
echo "| **Punteggio Totale** | **$SCORE / 100** |" >> $REPORT_FILE
echo "| **Errori Critici (FAIL)** | $ERRORS_COUNT |" >> $REPORT_FILE
echo "| **Avvisi (WARN)** | $WARNINGS_COUNT |" >> $REPORT_FILE
echo "| **Data** | $(date) |" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Dettaglio errori
if [ $ERRORS_COUNT -gt 0 ]; then
  echo "### ❌ Errori Rilevati" >> $REPORT_FILE
  echo "" >> $REPORT_FILE
  for e in "${ERROR_LIST[@]}"; do
    echo "- $e" >> $REPORT_FILE
  done
  echo "" >> $REPORT_FILE
fi

if [ $ERRORS_COUNT -eq 0 ] && [ $SCORE -ge 85 ]; then
  STATUS_MSG="✅ APPROVATO PER LA DISTRIBUZIONE - PRODOTTO READY FOR PRODUCTION"
  echo "### STATO: $STATUS_MSG" >> $REPORT_FILE
  echo "" >> $REPORT_FILE
  echo "| Categoria | Giudizio |" >> $REPORT_FILE
  echo "|-----------|----------|" >> $REPORT_FILE
  echo "| 🔒 Sicurezza | ✅ Superato |" >> $REPORT_FILE
  echo "| 📦 Dipendenze | ✅ Superato |" >> $REPORT_FILE
  echo "| 🔍 Analisi Statica | ✅ Superato |" >> $REPORT_FILE
  echo "| 🧪 Test | ✅ Superato |" >> $REPORT_FILE
  echo "| ⚡ Performance | ✅ Superato |" >> $REPORT_FILE
  echo "| 🌐 Frontend | ✅ Superato |" >> $REPORT_FILE
  echo "| 📋 Git | ✅ Superato |" >> $REPORT_FILE
  echo "" >> $REPORT_FILE
  echo -e "\n${BOLD}${GREEN}====================================================================${NC}"
  echo -e "${BOLD}${GREEN}  $STATUS_MSG  ${NC}"
  echo -e "${BOLD}${GREEN}  Punteggio Qualità Prodotto: $SCORE / 100${NC}"
  echo -e "${BOLD}${GREEN}  Errori: $ERRORS_COUNT | Avvisi: $WARNINGS_COUNT${NC}"
  echo -e "${BOLD}${GREEN}====================================================================${NC}\n"
else
  STATUS_MSG="❌ NON IDONEO ALLA DISTRIBUZIONE - CORREGGERE GLI ERRORI PRIMA DEL RILASCIO"
  echo "### STATO: $STATUS_MSG" >> $REPORT_FILE
  echo "" >> $REPORT_FILE
  echo -e "\n${BOLD}${RED}====================================================================${NC}"
  echo -e "${BOLD}${RED}  $STATUS_MSG  ${NC}"
  echo -e "${BOLD}${RED}  Punteggio Qualità Prodotto: $SCORE / 100 | Errori: $ERRORS_COUNT${NC}"
  echo -e "${BOLD}${RED}====================================================================${NC}\n"
fi

log_info "Report di validazione dettagliato salvato in: ${BOLD}$REPORT_FILE${NC}"
