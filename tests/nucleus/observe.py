"""
observe.py -- watch a running Slippi Melee for crashes/hangs while a mod is
loaded, reading live state from RAM. This is the payoff for the mod harness:
boot a modded ISO, get into a match, and have observe.py tell you objectively
whether the mod ran or crashed, and capture diagnostics if it didn't.

Crash/hang signals (most reliable first):
  - process death            -> CRASH (Dolphin closed / crashed to desktop)
  - MEM1 / GALE01 gone        -> CRASH (emulation stopped)
  - frame counter frozen      -> HANG  (game frozen but process alive)
  - left in-game unexpectedly -> ENDED (match exited / soft crash to menu)

Scene state (Melee 1.02): major scene 0x80479D30 == 0x02 in VS mode; the
in-match substate 0x80479D33 == 0x02 in-game (0x00 on the character-select
screen). Global frame counter 0x80479D60.

    python observe.py [--seconds N] [--pid P] [--label name]
"""

import json
import os
import subprocess
import sys
import time

from melee_mem import Dolphin

SCENE_MAJOR = 0x80479D30
SCENE_SUBSTATE = 0x80479D33
FRAME_COUNTER = 0x80479D60

HERE = os.path.dirname(os.path.abspath(__file__))
CONTROL_JS = os.path.join(HERE, "..", "dolphin", "control.js")
REPORT_DIR = os.path.join(HERE, "..", "artifacts", "nucleus", "crash-reports")


class Observer:
    def __init__(self, dolphin):
        self.d = dolphin

    def status(self):
        """One snapshot of liveness + scene. Returns None if RAM is unreadable
        (process gone or emulation stopped)."""
        if not self.d.alive():
            return {"alive": False}
        if self.d.base is None and not self.d.locate():
            return {"alive": True, "mem": False}
        frame = self.d.u32(FRAME_COUNTER)
        if frame is None:
            # base may be stale (e.g. game reloaded); try to re-locate once
            if not self.d.locate():
                return {"alive": True, "mem": False}
            frame = self.d.u32(FRAME_COUNTER)
        major = self.d.u8(SCENE_MAJOR)
        sub = self.d.u8(SCENE_SUBSTATE)
        return {
            "alive": True,
            "mem": frame is not None,
            "frame": frame,
            "major": major,
            "sub": sub,
            "in_game": major == 0x02 and sub == 0x02,
        }

    def watch(self, seconds=20.0, freeze_secs=2.0, min_ingame=4.0, log=None, require_ingame=True):
        """Poll until the watch window elapses or a crash/hang is detected.
        Returns (verdict, reason, last_status). verdict in
        {healthy, crashed, hung, ended, never_started}. A mod that loads and
        runs past min_ingame seconds is a PASS even if the match then ends
        (e.g. an idle character gets KO'd) -- only a *quick* exit from in-game
        is treated as a possible soft crash."""
        start = time.time()
        last_frame = None
        last_frame_change = start
        reached_ingame = False
        ingame_start = None
        prev_scene = None

        def emit(event, **kw):
            rec = {"t": round(time.time() - start, 2), "event": event, **kw}
            if log:
                log.write(json.dumps(rec) + "\n")
                log.flush()
            return rec

        emit("watch_start", seconds=seconds)
        while time.time() - start < seconds:
            st = self.status()
            if st is None or not st.get("alive"):
                return "crashed", "dolphin process exited", st
            if not st.get("mem"):
                # emulation stopped (GALE01 gone) -- treat as crash if we were in-game
                if reached_ingame:
                    return "crashed", "emulated RAM became unreadable", st
                time.sleep(0.2)
                continue

            scene = (st["major"], st["sub"])
            if scene != prev_scene:
                emit("scene", major=st["major"], sub=st["sub"], in_game=st["in_game"])
                prev_scene = scene

            if st["in_game"]:
                if not reached_ingame:
                    reached_ingame = True
                    ingame_start = time.time()
                    emit("reached_ingame", frame=st["frame"])
                # freeze detection (only meaningful in-game)
                if st["frame"] != last_frame:
                    last_frame = st["frame"]
                    last_frame_change = time.time()
                elif time.time() - last_frame_change > freeze_secs:
                    emit("frame_frozen", frame=st["frame"])
                    return "hung", f"frame counter frozen at {st['frame']} for >{freeze_secs}s", st
            elif reached_ingame:
                # we were in-game and the scene changed away from it
                dur = time.time() - ingame_start
                emit("left_ingame", major=st["major"], sub=st["sub"], ingame_secs=round(dur, 1))
                if dur < min_ingame:
                    return "ended", f"left in-game after only {dur:.1f}s (possible soft crash)", st
                return "healthy", f"loaded and ran {dur:.1f}s in-game before the match ended", st

            time.sleep(0.2)

        last = self.status()
        if require_ingame and not reached_ingame:
            return "never_started", "never reached in-game during the watch window", last
        return "healthy", "ran to end of watch window without crash/hang", last


def capture_diagnostics(label, verdict, reason, last_status):
    os.makedirs(REPORT_DIR, exist_ok=True)
    stamp = label or "run"
    report = {"label": label, "verdict": verdict, "reason": reason, "last_status": last_status}
    base = os.path.join(REPORT_DIR, f"{stamp}_{verdict}")
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    # best-effort screenshot of whatever is on screen at failure
    try:
        subprocess.run(["node", CONTROL_JS, "shot", "--label", f"crash-{stamp}"],
                       cwd=os.path.join(HERE, "..", "dolphin"),
                       capture_output=True, shell=True, timeout=20)
    except Exception:
        pass
    return base + ".json"


def main():
    args = sys.argv[1:]
    seconds = float(args[args.index("--seconds") + 1]) if "--seconds" in args else 20.0
    pid = int(args[args.index("--pid") + 1]) if "--pid" in args else None
    label = args[args.index("--label") + 1] if "--label" in args else "observe"

    d = Dolphin(pid)
    obs = Observer(d)
    print(f"observing pid {d.pid} for {seconds:.0f}s...")
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(os.path.join(REPORT_DIR, f"{label}.jsonl"), "w", encoding="utf-8") as logf:
        verdict, reason, last = obs.watch(seconds=seconds, log=logf)
    print(f"VERDICT: {verdict} -- {reason}")
    print(f"last status: {last}")
    if verdict in ("crashed", "hung", "ended", "never_started"):
        path = capture_diagnostics(label, verdict, reason, last)
        print(f"diagnostics: {path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
