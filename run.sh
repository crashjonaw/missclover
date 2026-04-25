#!/usr/bin/env bash
# MISS CLOVER — local development server
# Spins up a Flask dev server on http://127.0.0.1:5002 with hot-reload.

set -e
cd "$(dirname "$0")"

echo "====================================="
echo "  MISS CLOVER — local dev"
echo "====================================="

# venv (create on first run)
if [ ! -d .venv ]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# deps
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# env (create from template on first run)
if [ ! -f .env ]; then
  echo "First run — creating .env from .env.example"
  cp .env.example .env
  python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env.tmp 2>/dev/null || true
  echo "→ Edit .env to fill in HITPAY_API_KEY and (optionally) MAIL_* before checkout works."
fi

# migrations + seed (idempotent)
export FLASK_APP=app.py
if [ ! -d migrations ]; then
  echo "Initialising migrations..."
  flask db init
  flask db migrate -m "initial schema" >/dev/null
fi
flask db upgrade

echo "Seeding products..."
python seed.py

# free port 5002 if held by a previous run
lsof -ti:5002 | xargs kill -9 2>/dev/null || true

echo ""
echo "→ http://127.0.0.1:5002"
echo ""
exec flask --app app.py run --host=127.0.0.1 --port=5002 --debug
