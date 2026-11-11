#!/bin/zsh
# Run from Finder or Terminal; keep this window open during analysis.
cd -- "$(dirname -- "$0")" || exit 1
if [[ ! -x .venv/bin/python ]]; then
  print "The local Python environment is missing. Follow the setup in README.md."
  read -r "?Press Return to close."
  exit 1
fi
if lsof -nP -iTCP:8767 -sTCP:LISTEN >/dev/null 2>&1; then
  print "Port 8767 is already in use. Uncanny may already be running."
  read -r "?Press Return to close."
  exit 0
fi
print "Starting Uncanny locally. Keep this window open while analyzing videos."
.venv/bin/python detector/server.py
read -r "?Detector stopped. Press Return to close."
