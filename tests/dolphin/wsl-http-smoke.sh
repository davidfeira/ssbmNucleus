#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <iso-path> [build-dir]" >&2
  exit 2
fi

ISO_PATH="$1"
BUILD_DIR="${2:-/mnt/c/Users/david/projects/NucleusDesktop/tests/external/emubench-dolphin/build-wsl}"
ARTIFACT_ROOT="/mnt/c/Users/david/projects/NucleusDesktop/tests/artifacts/wsl/http-smoke"
TEST_USER="$ARTIFACT_ROOT/user"
XVFB_DISPLAY=":99"
LOG_FILE="$ARTIFACT_ROOT/dolphin.log"
XVFB_LOG="$ARTIFACT_ROOT/xvfb.log"

rm -rf "$TEST_USER"
mkdir -p "$TEST_USER"
mkdir -p "$ARTIFACT_ROOT"

Xvfb "$XVFB_DISPLAY" -screen 0 1280x720x24 >"$XVFB_LOG" 2>&1 &
XVFB_PID=$!
DOLPHIN_PID=""

cleanup() {
  if [[ -n "$DOLPHIN_PID" ]]; then
    kill "$DOLPHIN_PID" >/dev/null 2>&1 || true
    wait "$DOLPHIN_PID" >/dev/null 2>&1 || true
  fi
  kill "$XVFB_PID" >/dev/null 2>&1 || true
}

trap cleanup EXIT
sleep 2

export DISPLAY="$XVFB_DISPLAY"
DOLPHIN_EMU_USERPATH="$TEST_USER" timeout 60s \
  "$BUILD_DIR/Binaries/dolphin-emu-nogui" \
  -u "$TEST_USER" \
  -e "$ISO_PATH" \
  >"$LOG_FILE" 2>&1 &
DOLPHIN_PID=$!

for _ in $(seq 1 20); do
  if curl -fsS http://127.0.0.1:8080/; then
    echo
    echo "http server ok"
    exit 0
  fi
  sleep 1
done

tail -n 120 "$LOG_FILE" >&2 || true
exit 1
