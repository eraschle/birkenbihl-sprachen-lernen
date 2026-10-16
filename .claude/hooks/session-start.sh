#!/bin/bash
# Prepares Claude Code on the web sessions so tests (including Qt GUI tests) and linters run.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# System libraries PySide6 needs for QtGui/QtWidgets and QtMultimedia (audio) in a headless container
QT_LIBS=(libegl1 libgl1 libxkbcommon0 libfontconfig1 libdbus-1-3 libpulse0)
installed() { dpkg-query -W -f='${Status}' "$1" 2>/dev/null | grep -q "install ok installed"; }
missing=()
for lib in "${QT_LIBS[@]}"; do installed "$lib" || missing+=("$lib"); done
if [ ${#missing[@]} -gt 0 ]; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${missing[@]}" >/dev/null
fi

uv sync --quiet

# Run Qt without a display
echo 'export QT_QPA_PLATFORM=offscreen' >> "$CLAUDE_ENV_FILE"
