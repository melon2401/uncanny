#!/bin/zsh
cd -- "$(dirname -- "$0")" || exit 1
print "Starting Uncanny's local detectors…"
.venv/bin/python detector/launch.py
read -r "?Press Return to close."
