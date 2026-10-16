#!/bin/bash
# Prepares Claude Code on the web sessions so tests (including Qt GUI tests) and linters run.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# System libraries PySide6 needs to import QtGui/QtWidgets in a headless container
QT_LIBS=(libegl1 libgl1 libxkbcommon0 libfontconfig1 libdbus-1-3)
if ! dpkg -s "${QT_LIBS[@]}" >/dev/null 2>&1; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${QT_LIBS[@]}" >/dev/null
fi

uv sync --quiet

# Run Qt without a display
echo 'export QT_QPA_PLATFORM=offscreen' >> "$CLAUDE_ENV_FILE"
