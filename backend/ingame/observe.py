"""
observe.py -- watch a running Slippi Melee for crashes/hangs while a mod is
loaded, reading live state from RAM. Boot a modded ISO, get into a match, and
have the Observer tell you objectively whether the mod ran or crashed.

Ported from tests/nucleus/observe.py: the Observer class is identical (the
crash/hang verdict logic is the validated core). The dev CLI main() and
capture_diagnostics (which shelled out to `node control.js shot`) are dropped --
screenshots are taken by the runner via screenshot.py (stdlib ctypes + PIL).

Crash/hang signals (most reliable first):
  - process death            -> CRASH
  - MEM1 / GALE01 gone        -> CRASH
  - frame counter frozen      -> HANG
  - left in-game unexpectedly -> ENDED (soft crash to menu)

Scene state (Melee 1.02): major 0x80479D30 == 0x02 in VS mode; in-match substate
0x80479D33 == 0x02 in-game (0x00 = character select). Frame counter 0x80479D60.
"""

import json
import time

SCENE_MAJOR = 0x80479D30
SCENE_SUBSTATE = 0x80479D33
FRAME_COUNTER = 0x80479D60


class Observer:
    def __init__(self, dolphin):
        self.d = dolphin

    def status(self):
        """One snapshot of liveness + scene. Returns None-ish dicts if RAM is
        unreadable (process gone or emulation stopped)."""
        if not self.d.alive():
            return {"alive": False}
        if self.d.base is None and not self.d.locate():
            return {"alive": True, "mem": False}
        frame = self.d.u32(FRAME_COUNTER)
        if frame is None:
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

    def watch_health(self, seconds=20.0, freeze_secs=3.0, log=None):
        """Watch process + frame-counter health on ANY screen (boot/menu/game).
        Catches boot- and load-time crashes without needing to select the mod --
        the global frame counter advances on every screen, so a freeze or
        process death is a crash/hang regardless of where we are."""
        start = time.time()
        last_frame = None
        last_change = start

        def emit(event, **kw):
            if log:
                log(json.dumps({"t": round(time.time() - start, 2), "event": event, **kw}))

        emit("health_watch_start", seconds=seconds)
        while time.time() - start < seconds:
            st = self.status()
            if st is None or not st.get("alive"):
                return "crashed", "dolphin process exited", st
            if not st.get("mem"):
                return "crashed", "emulated RAM unreadable", st
            f = st.get("frame")
            if f != last_frame:
                last_frame = f
                last_change = time.time()
            elif time.time() - last_change > freeze_secs:
                emit("frame_frozen", frame=f, major=st.get("major"), sub=st.get("sub"))
                return "hung", f"frame counter frozen at {f} for >{freeze_secs}s", st
            time.sleep(0.2)
        return "healthy", f"alive and advancing for {seconds:.0f}s", self.status()

    def watch(self, seconds=20.0, freeze_secs=2.0, min_ingame=4.0, log=None, require_ingame=True):
        """Poll until the watch window elapses or a crash/hang is detected.
        Returns (verdict, reason, last_status). verdict in
        {healthy, crashed, hung, ended, never_started}. A mod that loads and
        runs past min_ingame seconds is a PASS even if the match then ends."""
        start = time.time()
        last_frame = None
        last_frame_change = start
        reached_ingame = False
        ingame_start = None
        prev_scene = None

        def emit(event, **kw):
            if log:
                log(json.dumps({"t": round(time.time() - start, 2), "event": event, **kw}))

        emit("watch_start", seconds=seconds)
        while time.time() - start < seconds:
            st = self.status()
            if st is None or not st.get("alive"):
                return "crashed", "dolphin process exited", st
            if not st.get("mem"):
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
                if st["frame"] != last_frame:
                    last_frame = st["frame"]
                    last_frame_change = time.time()
                elif time.time() - last_frame_change > freeze_secs:
                    emit("frame_frozen", frame=st["frame"])
                    return "hung", f"frame counter frozen at {st['frame']} for >{freeze_secs}s", st
            elif reached_ingame:
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
