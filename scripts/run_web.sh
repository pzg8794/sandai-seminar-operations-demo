#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python scripts/export_web_data.py
npm --prefix web run build
exec .venv/bin/gunicorn --bind 127.0.0.1:8765 web.server:application
