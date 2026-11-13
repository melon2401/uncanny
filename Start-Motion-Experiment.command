#!/bin/zsh
cd -- "$(dirname -- "$0")" || exit 1
export HF_HUB_OFFLINE=1
print "Starting experimental motion analysis. Keep this window open."
/opt/anaconda3/bin/python3 detector/motion_server.py
read -r "?Motion service stopped. Press Return to close."
