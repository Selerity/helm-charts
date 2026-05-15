#!/bin/bash
# Cron script to run Viya 4 Home Directory Builder
# Add to crontab with: 0,15,30,45 * * * * /path/to/run_cron.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.json"
PYTHON_SCRIPT="$SCRIPT_DIR/viya4_home_dir_builder.py"
LOG_FILE="$SCRIPT_DIR/viya4_home_dir_builder.log"

# Ensure Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH" >> "$LOG_FILE"
    exit 1
fi

# Run the script with logging
python3 "$PYTHON_SCRIPT" --config "$CONFIG_FILE" >> "$LOG_FILE" 2>&1