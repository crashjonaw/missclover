#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  MISS CLOVER — Production Launch Script
#
#  Usage:
#    First time:  chmod +x run_production.sh && ./run_production.sh
#    After that:  ./run_production.sh
#
#  This script will:
#    1. Close idle Terminal windows (macOS)
#    2. Check Python and dependencies
#    3. Generate SECRET_KEY if missing in .env
#    4. Back up the database
#    5. Run db migrations
#    6. Start gunicorn in a labelled Terminal
#    7. Start Cloudflare Tunnel in a labelled Terminal
# ═══════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── Colors ──────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $1"; exit 1; }

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  MISS CLOVER — Production Launcher"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ── 0. Close idle Terminal windows ──────────────────────────────────
info "Closing idle terminal windows..."
osascript -e '
tell application "Terminal"
    set winCount to count of windows
    repeat with i from winCount to 1 by -1
        try
            set w to window i
            set allIdle to true
            repeat with t in (every tab of w)
                if busy of t is true then
                    set allIdle to false
                    exit repeat
                end if
            end repeat
            if allIdle then close w saving no
        end try
    end repeat
end tell
' 2>/dev/null
sleep 1
ok "Idle windows closed"

# ── 1. Check Python ─────────────────────────────────────────────────
info "Checking Python..."
PYTHON=""
for cmd in python3 python; do
  if command -v "$cmd" &>/dev/null; then PYTHON="$cmd"; break; fi
done
[ -z "$PYTHON" ] && fail "Python not found. Install Python 3.10+."
ok "Found $($PYTHON --version 2>&1)"

# ── 2. Dependencies ────────────────────────────────────────────────
info "Installing/updating dependencies..."
if [ ! -d .venv ]; then
  $PYTHON -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
$PYTHON -c "import gunicorn" 2>/dev/null || fail "gunicorn not installed."
ok "Dependencies ready"

# ── 3. .env / SECRET_KEY ────────────────────────────────────────────
info "Checking .env..."
if [ ! -f .env ]; then
  warn ".env not found — generating from template + new SECRET_KEY"
  cp .env.example .env
  SECRET=$($PYTHON -c "import secrets; print(secrets.token_hex(32))")
  # Replace the placeholder
  if grep -q "^SECRET_KEY=" .env; then
    # use a delimiter that won't appear in the secret
    "$PYTHON" - <<PY
import os, re
p = ".env"
with open(p) as f: txt = f.read()
txt = re.sub(r'^SECRET_KEY=.*$', f'SECRET_KEY={"${SECRET}"}', txt, flags=re.M)
with open(p, "w") as f: f.write(txt)
PY
  fi
  warn "→ Edit .env to fill in HITPAY_API_KEY, HITPAY_SALT, and MAIL_* before checkout works."
fi
set -a
# shellcheck disable=SC1091
source .env
set +a
[ -z "$SECRET_KEY" ] && fail "SECRET_KEY is empty in .env."
ok "Environment loaded (SECRET_KEY: ${#SECRET_KEY} chars)"

# ── 4. DB backup ────────────────────────────────────────────────────
info "Database backup..."
mkdir -p backups instance
DB="instance/missclover.db"
if [ -f "$DB" ]; then
  BACKUP="backups/missclover_$(date '+%Y%m%d_%H%M%S').db"
  cp "$DB" "$BACKUP"
  ok "Backed up to $BACKUP"
  ls -t backups/missclover_*.db 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
else
  info "No existing database — will be created on first run"
fi

# ── 5. Migrations + seed ───────────────────────────────────────────
info "Running database migrations..."
export FLASK_APP=app.py
if [ ! -d migrations ]; then
  flask db init
  flask db migrate -m "initial schema" >/dev/null
fi
flask db upgrade
$PYTHON seed.py >/dev/null 2>&1 || warn "Seed step had issues (check manually)"
ok "Database ready"

# ── 6. Sanity check ────────────────────────────────────────────────
info "Sanity check..."
$PYTHON -c "import app; print('  app imported')" || fail "Sanity check failed."
ok "App imports cleanly"

# ── 7. Cleanup old processes on port 5002 ──────────────────────────
info "Cleaning up old MISS CLOVER processes..."
pkill -9 -f "cloudflared.*missclover" 2>/dev/null || true
lsof -ti:5002 | xargs kill -9 2>/dev/null || true
sleep 1
lsof -ti:5002 | xargs kill -9 2>/dev/null || true
sleep 1
if lsof -ti:5002 >/dev/null 2>&1; then
  fail "Port 5002 still in use — cannot start"
fi
ok "Old processes cleaned"

# ── 8. Patch cloudflared config ────────────────────────────────────
CF_CONFIG="$HOME/.cloudflared/config.yml"
if [ -f "$CF_CONFIG" ]; then
  sed -i '' 's/localhost:5002/127.0.0.1:5002/g' "$CF_CONFIG" 2>/dev/null || true
  ok "cloudflared config patched"
else
  info "No cloudflared config found — tunnel step will be skipped"
fi

# ── 9. Launch ──────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "  ${GREEN}Launching MISS CLOVER in production mode${NC}"
echo "  Gunicorn: ${GUNICORN_BIND:-127.0.0.1:5002}"
echo "  Stop with: ./stop_production.sh"
echo "═══════════════════════════════════════════════════════════"
echo ""

export SECRET_KEY

info "Starting Gunicorn..."
osascript -e "
tell app \"Terminal\"
    set w to do script \"cd '$SCRIPT_DIR' && source .venv/bin/activate && set -a && source .env && set +a && gunicorn -c gunicorn.conf.py app:app\"
    set custom title of window 1 to \"MC-Gunicorn\"
end tell"

echo "Waiting for Gunicorn to start..."
sleep 5

if curl -s -o /dev/null -w '' http://127.0.0.1:5002/ 2>/dev/null; then
  ok "Gunicorn is running on 127.0.0.1:5002"
else
  warn "Gunicorn may still be starting — check the MC-Gunicorn terminal"
fi

if [ -f "$CF_CONFIG" ]; then
  info "Starting Cloudflare Tunnel..."
  osascript -e "
tell app \"Terminal\"
    set w to do script \"cloudflared tunnel run --url http://127.0.0.1:5002 missclover\"
    set custom title of window 1 to \"MC-Tunnel\"
end tell"
  sleep 3
  ok "Cloudflare Tunnel launched"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "  ${GREEN}MISS CLOVER is live!${NC}"
echo "  Local:   http://localhost:5002"
echo ""
echo "  Stop by closing the MC-Gunicorn / MC-Tunnel windows"
echo "  or running: ./stop_production.sh"
echo "═══════════════════════════════════════════════════════════"
echo ""
