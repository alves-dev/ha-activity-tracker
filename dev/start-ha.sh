#!/bin/sh
# Start the local Home Assistant instance used to test Activity Tracker.

set -eu

readonly HA_CORE_DIR="/home/alves-dev/projects/others/core"
readonly HA_CONFIG_DIR="$HA_CORE_DIR/config"
readonly PID_FILE="/tmp/ha-activity-tracker-home-assistant.pid"
readonly LOG_FILE="/tmp/ha-activity-tracker-home-assistant.log"

is_home_assistant_process() {
  process_args="$(ps -p "$1" -o args= 2>/dev/null || true)"
  case "$process_args" in
    *homeassistant*"$HA_CONFIG_DIR"*) return 0 ;;
    *) return 1 ;;
  esac
}

if [ ! -d "$HA_CORE_DIR" ] || [ ! -d "$HA_CONFIG_DIR" ]; then
  echo "Home Assistant core/config directory was not found." >&2
  exit 1
fi

if [ -r "$PID_FILE" ]; then
  pid="$(cat "$PID_FILE")"
  case "$pid" in
    *[!0-9]*|'') valid_pid=false ;;
    *) valid_pid=true ;;
  esac
  if [ "$valid_pid" = true ] && is_home_assistant_process "$pid"; then
    echo "Home Assistant is already running (PID $pid)."
    exit 0
  fi
  rm -f "$PID_FILE"
fi

cd "$HA_CORE_DIR"
nohup uv run --project . python -m homeassistant --config "$HA_CONFIG_DIR" \
  >"$LOG_FILE" 2>&1 &
pid=$!
echo "$pid" >"$PID_FILE"

sleep 1
if ! kill -0 "$pid" 2>/dev/null; then
  rm -f "$PID_FILE"
  echo "Home Assistant stopped during startup. See $LOG_FILE." >&2
  exit 1
fi

echo "Home Assistant started (PID $pid)."
echo "Log: $LOG_FILE"
