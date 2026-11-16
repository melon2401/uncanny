#!/bin/zsh
cd -- "$(dirname -- "$0")" || exit 1
python3 detector/setup_visual.py
read -r "?Press Return to close."
