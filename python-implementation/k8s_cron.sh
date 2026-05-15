#!/bin/bash
# Usage: k8s_cron.sh [namespace] [viya_url] [home_path]
# Add to crontab: 0,15,30,45 * * * * /path/to/k8s_cron.sh viya https://viya.company.com /home

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE=${1:-viya}
VIYA_URL=${2:-https://viya.company.com}
HOME_PATH=${3:-/home}

sudo -E python3 "$SCRIPT_DIR/k8s_viya_home_builder.py" "$NAMESPACE" "$VIYA_URL" "$HOME_PATH" >> "$SCRIPT_DIR/k8s_home_builder.log" 2>&1