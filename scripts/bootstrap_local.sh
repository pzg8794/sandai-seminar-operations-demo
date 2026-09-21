#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_ROOT="${SCRIPT_DIR:h}"
PYTHON_BIN="${SANDAI_BOOTSTRAP_PYTHON:-/opt/homebrew/bin/python3.12}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Required Python 3.12 was not found at: $PYTHON_BIN" >&2
  echo "Set SANDAI_BOOTSTRAP_PYTHON to another Python 3.12 executable." >&2
  exit 2
fi

if [[ ! -d "$PROJECT_ROOT/.venv" ]]; then
  "$PYTHON_BIN" -m venv "$PROJECT_ROOT/.venv"
fi

"$PROJECT_ROOT/.venv/bin/python" -m pip install --upgrade pip
"$PROJECT_ROOT/.venv/bin/python" -m pip install -r "$PROJECT_ROOT/requirements.in"
"$PROJECT_ROOT/.venv/bin/python" -m pip install -e "$PROJECT_ROOT"
"$PROJECT_ROOT/.venv/bin/python" -m ipykernel install \
  --prefix "$PROJECT_ROOT/.venv" \
  --name sandai-demo \
  --display-name "Python 3.12 (SaNDAI Demo)"

echo "SaNDAI local environment is ready."
echo "Next: run the VS Code task 'SaNDAI: Shared Drive status'."
