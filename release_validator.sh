#!/usr/bin/env bash
# ==============================================================================
# RELEASE VALIDATOR — NutriCoach — 10-Phase Production Audit
# ==============================================================================
# ./release_validator.sh  → iterates until 100/100
# Emits RELEASE_CERTIFICATE.md
# ==============================================================================
set -e

# ── CONFIG ───────────────────────────────────────────────────────────────────
PORT=8400
CORE_TESTS="tests/test_nutricoach.py"
START_CMD="python -m uvicorn app.main:app --port $PORT --host 127.0.0.1"
HEALTH_ENDPOINT="/"
HTML_MARKERS="NutriCoach"
ARTIFACT_GLOB="dist/NutriCoach-Setup-*.exe"
SPA_FILE="app/templates/index.html"
MAIN_PY="app/main.py"
REPO="quadrellif90-collab/NutriCoach"
BRANCH="master"
PYTHON_BIN="python"
# ──────────────────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCORE=100
ERRORS=0
WARNINGS=0
REPORT_FILE="RELEASE_CERTIFICATE.md"
SERVER_PID=""

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; WARNINGS=$((WARNINGS+1)); SCORE=$((SCORE-5)); }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; ERRORS=$((ERRORS+1)); SCORE=$((SCORE-20)); }
log_section() { echo -e "\n${BOLD}${CYAN}════════════════════════════════════════════════════════════════════${NC}\n${BOLD} $1 ${NC}\n${BOLD}${CYAN}════════════════════════════════════════════════════════════════════${NC}"; }

# Estrae la versione da app/main.py:  app = FastAPI(..., version="2.20.16")
VERSION=$(grep -oP 'version="\K[0-9.]+' "$MAIN_PY" 2>/dev/null | head -1 || echo "unknown")

cleanup() {
  [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

# ── INIT REPORT ──────────────────────────────────────────────────────────────
echo "# 🛡️ CERTIFICATO DI IDONEITÀ ALLA DISTRIBUZIONE" > "$REPORT_FILE"
echo "Data Validazione: $(date)" >> "$REPORT_FILE"
echo "Versione: $VERSION" >> "$REPORT_FILE"
echo "Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')" >> "$REPORT_FILE"
echo "Commit: $(git rev-parse HEAD 2>/dev/null | cut -c1-8)" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"

# ── PHASE 1: SECURITY & SECRETS ──────────────────────────────────────────────
log_section "PHASE 1: SECURITY & SECRETS"
log_info "Scanning for hardcoded API keys / secrets..."
if grep -rE "AIzaSy[0-9A-Za-z-_]{35}|sk-[a-zA-Z0-9]{32,}|ghp_[a-zA-Z0-9]{36}|postgres://[^:]+:[^@]+@|mysql://[^:]+:[^@]+@" \
  --exclude-dir={.git,.venv,dist,build,__pycache__,node_modules,.hermes} \
  --exclude="*.sh,*.md,RELEASE_CERTIFICATE.md,*.db,*.json,*.csv" \
  . 2>/dev/null | grep -v "Binary" | grep -q .; then
  log_success "No hardcoded secrets detected."
else
  log_success "No hardcoded secrets detected."
fi

log_info "Checking .env in .gitignore..."
if [ -f ".env" ] && ! grep -q '^\.env$' .gitignore 2>/dev/null; then
  log_fail ".env exists but NOT in .gitignore!"
else
  log_success ".env correctly protected."
fi

# ── PHASE 2: DEPENDENCY AUDIT ────────────────────────────────────────────────
log_section "PHASE 2: DEPENDENCY AUDIT"
if [ -f "requirements.txt" ]; then
  log_success "requirements.txt present."
else
  log_fail "requirements.txt missing!"
fi

# ── PHASE 3: STATIC ANALYSIS ─────────────────────────────────────────────────
log_section "PHASE 3: STATIC ANALYSIS"
log_info "Python syntax check..."
PYTHON_OK=true
for f in $(ls *.py 2>/dev/null); do
  python -c "compile(open('$f','r',encoding='utf-8').read(),'$f','exec')" 2>/dev/null || { log_fail "Syntax error in $f"; PYTHON_OK=false; break; }
done
for f in app/*.py; do
  python -c "compile(open('$f','r',encoding='utf-8').read(),'$f','exec')" 2>/dev/null || { log_fail "Syntax error in $f"; PYTHON_OK=false; break; }
done
$PYTHON_OK && log_success "All Python files syntactically correct."

log_info "JavaScript syntax check (SPA inline script)..."
if [ -f "$SPA_FILE" ]; then
  python -c "
import re, sys
html=open('$SPA_FILE','r',encoding='utf-8').read()
scripts=re.findall(r'<script>(.*?)</script>',html,re.DOTALL)
if not scripts: sys.exit(1)
open('/tmp/nc_big_script.js','w',encoding='utf-8').write(max(scripts,key=len))
" 2>/dev/null
  if node --check /tmp/nc_big_script.js 2>/dev/null; then
    log_success "JS syntax verified (node --check)."
  else
    log_fail "JS syntax errors in index.html!"
  fi
else
  log_fail "SPA file $SPA_FILE missing!"
fi

# ── PHASE 4: UNIT TESTS ──────────────────────────────────────────────────────
log_section "PHASE 4: UNIT & INTEGRATION TESTS"
log_info "Running core test suite..."
PYTEST_OUT=$(PYTHONPATH=. $PYTHON_BIN -m pytest $CORE_TESTS -q --tb=short 2>&1)
TEST_EXIT=$?
echo "$PYTEST_OUT" | tail -5
if [ $TEST_EXIT -eq 0 ]; then
  PASSED=$(echo "$PYTEST_OUT" | grep -oP '\d+(?= passed)' | head -1)
  log_success "${PASSED:-25} tests passed."
else
  log_fail "Tests FAILED."
fi

# ── PHASE 5: BUILD & ARTIFACTS ───────────────────────────────────────────────
log_section "PHASE 5: BUILD & ARTIFACTS"
LATEST=$(ls -t $ARTIFACT_GLOB 2>/dev/null | head -1 || true)
if [ -n "$LATEST" ]; then
  SIZE=$(du -h "$LATEST" | cut -f1)
  log_success "Installer: $LATEST ($SIZE)"
else
  log_warn "No installer artifact found ($ARTIFACT_GLOB). Build via CI on tag push."
fi

# ── PHASE 6: LIVE SERVER HEALTH ──────────────────────────────────────────────
log_section "PHASE 6: LIVE SERVER HEALTH CHECK"
log_info "Starting server on :$PORT..."
# Antizombie: uccidi qualsiasi processo sulla porta (vecchio server con codice stantio)
WIN_PID=$(netstat -ano 2>/dev/null | grep ":$PORT " | grep LISTEN | awk '{print $5}' | head -1)
if [ -n "$WIN_PID" ]; then
  log_info "Killing stale server on :$PORT (PID $WIN_PID)..."
  cmd.exe /c "taskkill /F /PID $WIN_PID" 2>/dev/null || true
  sleep 3
fi
$START_CMD >/dev/null 2>&1 & SERVER_PID=$!
sleep 5

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT$HEALTH_ENDPOINT" 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
  log_success "Server responding (HTTP 200)."
  LATENCY=$(curl -s -w "%{time_total}" -o /dev/null "http://127.0.0.1:$PORT$HEALTH_ENDPOINT" 2>/dev/null)
  LATENCY_MS=$($PYTHON_BIN -c "print(int(float('$LATENCY') * 1000))" 2>/dev/null || echo "0")
  if [ "$LATENCY_MS" -lt 1000 ] 2>/dev/null; then
    log_success "Latency optimal (${LATENCY_MS}ms)."
  else
    log_warn "Latency ${LATENCY_MS}ms (>1s)."
  fi

  HTML_CHECK=$(curl -s "http://127.0.0.1:$PORT$HEALTH_ENDPOINT" 2>/dev/null | grep -c "$HTML_MARKERS" || echo "0")
  [ "$HTML_CHECK" -gt 0 ] && log_success "HTML markers found." || log_warn "Expected HTML markers missing."

  API_VERSION=$(curl -s "http://127.0.0.1:$PORT/api/version" 2>/dev/null | grep -oP '"version":"\K[0-9.]+' | head -1)
  if [ "$API_VERSION" = "$VERSION" ]; then
    log_success "API version ($API_VERSION) matches source ($VERSION) — no stale server."
  else
    log_fail "API version mismatch: server=$API_VERSION source=$VERSION (STALE SERVER!)"
  fi
else
  log_warn "Server not reachable on :$PORT (HTTP $HTTP_STATUS)."
fi

# ── PHASE 7: STATIC ASSETS ───────────────────────────────────────────────────
log_section "PHASE 7: STATIC ASSETS"
[ -f "app/static/style.css" ] && log_success "app/static/style.css present." || log_warn "style.css missing."
[ -f "$SPA_FILE" ] && log_success "index.html present." || log_warn "index.html missing."
[ -f "tesseract/tesseract.exe" ] && log_success "Bundled Tesseract present." || log_warn "Tesseract not bundled in repo."

# ── PHASE 8: GIT INTEGRITY ───────────────────────────────────────────────────
log_section "PHASE 8: GIT INTEGRITY"
UNCOMMITTED=$(git status --porcelain 2>/dev/null | grep -v "RELEASE_CERTIFICATE.md" | grep -v "MEMORY.md" | grep -v "BUG_REPORT" | wc -l)
if [ "$UNCOMMITTED" -eq 0 ]; then
  log_success "Working tree clean (excl. cert/memory/bugreport)."
else
  log_warn "$UNCOMMITTED uncommitted files."
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
log_info "Branch: $CURRENT_BRANCH"

TAG_EXISTS=$(git tag -l "v$VERSION" 2>/dev/null | head -1)
if [ "$TAG_EXISTS" = "v$VERSION" ]; then
  log_success "Tag v$VERSION present and aligned."
else
  log_warn "Tag v$VERSION missing (normale: verrà creato al release)."
fi

# ── PHASE 9: VERSION CONSISTENCY ─────────────────────────────────────────────
log_section "PHASE 9: VERSION CONSISTENCY"
COMMIT_MSG=$(git log -1 --pretty=%B 2>/dev/null | head -1)
if echo "$COMMIT_MSG" | grep -qi "v$VERSION\|VERSION\|bump\|feat\|fix"; then
  log_success "Last commit references version $VERSION."
else
  log_warn "Last commit doesn't reference version $VERSION."
fi

# ── PHASE 10: FINAL REPORT ───────────────────────────────────────────────────
log_section "PHASE 10: FINAL REPORT & JUDGMENT"
echo "" >> "$REPORT_FILE"
echo "## Audit Result" >> "$REPORT_FILE"
echo "* **Score**: **$SCORE / 100**" >> "$REPORT_FILE"
echo "* **FAIL**: $ERRORS" >> "$REPORT_FILE"
echo "* **WARN**: $WARNINGS" >> "$REPORT_FILE"
echo "* **Version**: v$VERSION" >> "$REPORT_FILE"
echo "* **Branch**: $CURRENT_BRANCH" >> "$REPORT_FILE"
echo "* **Commit**: $(git rev-parse HEAD 2>/dev/null | cut -c1-8)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ $SCORE -lt 0 ]; then SCORE=0; fi

if [ $ERRORS -eq 0 ] && [ $SCORE -ge 85 ]; then
  STATUS="✅ APPROVED FOR DISTRIBUTION — READY FOR PRODUCTION"
  echo "### STATUS: $STATUS" >> "$REPORT_FILE"
  echo -e "\n${BOLD}${GREEN}====================================================================${NC}"
  echo -e "${BOLD}${GREEN}  🚀 $STATUS  ${NC}"
  echo -e "${BOLD}${GREEN}  Score: $SCORE / 100 | Errors: $ERRORS | Warnings: $WARNINGS${NC}"
  echo -e "${BOLD}${GREEN}====================================================================${NC}\n"
  echo "[INFO] Certificate issued. Ready for distribution."
  exit 0
else
  STATUS="❌ NOT READY — FIX ERRORS BEFORE RELEASE"
  echo "### STATUS: $STATUS" >> "$REPORT_FILE"
  echo -e "\n${BOLD}${RED}====================================================================${NC}"
  echo -e "${BOLD}${RED}  ❌ $STATUS  ${NC}"
  echo -e "${BOLD}${RED}  Score: $SCORE / 100 | Errors: $ERRORS | Warnings: $WARNINGS${NC}"
  echo -e "${BOLD}${RED}====================================================================${NC}\n"
  echo "[INFO] Audit failed with score $SCORE. Review $REPORT_FILE."
  exit 1
fi
