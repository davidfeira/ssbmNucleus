"""verify_ingame.py -- boot the final duel ISO and capture each legal stage's
hold-X DAS variant in-game, using the app's solo capture engine (backend/ingame).

Each capture boots an isolated Dolphin, reaches the CSS, loads the stage ALONE
holding X (so the DAS X-variant = the Porcelain & Ink stage loads), poses the
clean DEBUG_FREE camera, and grabs the render window. A successful capture also
proves boot -> CSS -> match works (boot-health gate).

Run from the repo root:  venv/Scripts/python.exe duel/claude/verify_ingame.py
"""
import json
import sys
from pathlib import Path

DUEL = Path(__file__).resolve().parent
REPO = DUEL.parents[1]
sys.path.insert(0, str(REPO / "backend"))

from core.config import STORAGE_PATH  # noqa: E402
from ingame.capture import capture_stage  # noqa: E402
from ingame.melee_sss import INTERNAL_STAGE_ID  # noqa: E402

ISO = DUEL / "exports" / "final.iso"
RUNS = STORAGE_PATH / "test-runs"

# duel stage code -> capture engine framing/internal key
STAGES = [
    ("GrNBa", "battlefield"),
    ("GrNLa", "finaldestination"),
    ("GrSt", "yoshisstory"),
    ("GrOp", "dreamland"),
    ("GrPs", "pokemonstadium"),
    ("GrIz", "fountainofdreams"),
]


def log(m):
    print(m, flush=True)


def main():
    if not ISO.exists():
        raise SystemExit(f"final ISO missing: {ISO}")
    RUNS.mkdir(parents=True, exist_ok=True)
    results = {}
    for code, key in STAGES:
        log(f"[verify] capturing {code} ({key}) holding X ...")
        try:
            r = capture_stage(str(ISO), None, str(RUNS), INTERNAL_STAGE_ID[key],
                              hold="X", framing_key=key, log=log)
        except Exception as e:
            r = {"ok": False, "png": None, "reason": f"{type(e).__name__}: {e}"}
        ok = bool(r.get("ok") and r.get("png"))
        if ok:
            out = DUEL / "previews" / "stages" / f"{code}_capture.png"
            out.write_bytes(r["png"])
            log(f"[verify] {code} OK -> {out.name} ({len(r['png'])} bytes)")
        else:
            log(f"[verify] {code} FAIL: {r.get('reason')}")
        results[code] = ok
    log("VERIFY_RESULTS " + json.dumps(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
