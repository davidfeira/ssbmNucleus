#!/usr/bin/env bash
# One compression-sweep data point: re-export the kept project at compression C
# (no re-install), then boot + online-CSS test. Prints "C=<C> -> HEALTHY|CRASHED".
# Usage: sweep_point.sh <C> [projectName]
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 2
C="${1:?usage: sweep_point.sh <C> [project]}"
PROJ="${2:-harness-stress}"
node tests/dolphin/control.js kill >/dev/null 2>&1
node tests/nucleus/build-modded-iso.js --type stress --name "$PROJ" --keep-project --export-only --compression "$C" > tests/artifacts/nucleus/_sweep.log 2>&1
if ! grep -q "export complete" tests/artifacts/nucleus/_sweep.log; then
  echo "C=$C -> BUILD_FAILED"; tail -3 tests/artifacts/nucleus/_sweep.log; exit 1
fi
ISO=$(grep -oE "output[\\/].*\.iso" tests/artifacts/nucleus/_sweep.log | head -1 | tr '\\' '/')
RES=$(bash tests/nucleus/online_test_iso.sh "output/${PROJ}.iso" | sed 's/ONLINE-CSS: //')
echo "C=$C -> $RES"
