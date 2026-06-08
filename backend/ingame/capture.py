"""
capture.py -- take a clean in-game SCREENSHOT of a stage with the harness.

Boots a freshly-built ISO in the isolated throwaway Dolphin (boot.py), then poses
everything DIRECTLY via WriteProcessMemory (the same path force_select uses) -- no
Dolphin gecko engine (Slippi ignores user codes) and no fragile cursor/stick
framing:

  * clean-shot RAM patches: invisible fighters, no HUD/shadows/screen-shake;
  * 1-PLAYER start: relax the CSS "Ready to Fight" gate (0x80263064 cmpwi r31,2
    -> r31,1) so we load in ALONE -- nothing can attack/SD/move the camera;
  * Time mode + no time limit so a solo match doesn't instantly end;
  * DEBUG_FREE camera (mode 8) posed by direct writes for a deterministic
    whole-stage frame (mode 8 has no per-frame callback, so the writes stick).

The user's Slippi setup is never touched (throwaway User dir + per-process writes).
The CSS analog for stages: like a CSP for a character, but rendered live.

RE addresses are NTSC 1.02 (doldecomp/melee): the 1-player gate in mncharsel
fn_80262F44; GameRules at 0x8045BF10; the Camera struct at 0x80452C68 +
CameraDebugMode at 0x80453004.
"""

import time

from .boot import DolphinBoot
from .melee_mem import Dolphin
from .melee_pipe import Pipe
from .melee_css import Cursor
from .melee_sss import StageCursor
from . import nav
from . import match_setup
from . import screenshot as _screenshot
from .runner import _lock_vanilla, _ensure_on_sss, _memory_select_to_sss

CKIND_FOX = 0x02   # external char id; the fighter is invisible for the shot anyway


def _noop(*_a, **_k):
    pass


# --- clean-shot RAM patches (gecko "04" codes as plain 32-bit writes) ----------
CODE_PATCHES = [
    (0x80030384, 0x60000000),   # Character Models Invisible [UnclePunch]
    (0x800872F8, 0x38600000),   # No Character Shadows [Altimor]
    (0x800304C4, 0x60000000),   # Disable Camera and Item Spawn Overlay (1)
    (0x8005A634, 0x48000094),   # Disable Camera and Item Spawn Overlay (2)
    (0x802275F8, 0x480000F0),   # Disable DPad Up Camera Changes
    (0x80030E44, 0x4E800020),   # Disable Screen Shake [Achilles1515]
]
HUD_FLAG_ADDR = 0x804D6D58       # 8-bit "remove HUD" flag (re-asserted before shot)

# 1-player start + Time/no-timer come from match_setup (shared with the runner).

# --- camera (Camera 0x80452C68 + CameraDebugMode 0x80453004) -------------------
CAMERA_MODE = 0x80452C6C         # CameraType; 8 = DEBUG_FREE (no per-frame cb)
CAMERA_FARZ = 0x80452C78
CAM_STD_INT = 0x80452C7C         # live STANDARD interest (read for calibration)
CAM_STD_EYE = 0x80452C94         # live STANDARD eye
CAM_STD_FOV = 0x80452CAC
CAM_DBG_INT = 0x80453040         # DEBUG_FREE look-at Vec3
CAM_DBG_EYE = 0x8045304C         # DEBUG_FREE eye Vec3
CAM_DBG_FOV = 0x80453058         # DEBUG_FREE fov (degrees)
CAMERA_DEBUG_FREE = 8

# Per-base-stage camera framing (eye, interest, fov). Calibrated by capture. An
# absent stage falls back to DEFAULT_FRAMING. Keyed by the INTERNAL_STAGE_ID name.
DEFAULT_FRAMING = {"eye": (0.0, 20.0, 450.0), "interest": (0.0, 8.0, 0.0), "fov": 40.0}
STAGE_FRAMING = {}


def _apply_code_patches(d, log=_noop):
    ok = sum(1 for addr, val in CODE_PATCHES if d.write_u32(addr, val))
    log(f"applied {ok}/{len(CODE_PATCHES)} capture patches")
    return ok


def _read_vec3(d, addr):
    return (d.f32(addr), d.f32(addr + 4), d.f32(addr + 8))


def _write_vec3(d, addr, v):
    d.write_f32(addr, float(v[0]))
    d.write_f32(addr + 4, float(v[1]))
    d.write_f32(addr + 8, float(v[2]))


def _set_free_camera(d, eye, interest, fov):
    """Pose the camera deterministically via DEBUG_FREE (mode 8), which reads
    these fields directly with no smoothing/clamping/recompute."""
    d.write_u32(CAMERA_MODE, CAMERA_DEBUG_FREE)
    _write_vec3(d, CAM_DBG_INT, interest)
    _write_vec3(d, CAM_DBG_EYE, eye)
    d.write_f32(CAM_DBG_FOV, float(fov))
    d.write_f32(CAMERA_FARZ, 16384.0)   # avoid clipping the back of the stage


def capture_stage(iso_path, slippi_path, runs_root, internal_id, hold=None,
                  framing_key=None, emit=None, log=None, settle=4.0,
                  hires_textures=False):
    """Boot the ISO, load the stage ALONE in a no-timer Time match (internal_id,
    holding `hold` for a DAS variant), pose the camera, and return
    {"ok": bool, "png": bytes|None, "reason": str}.

    framing_key selects a per-base-stage camera preset (STAGE_FRAMING)."""
    emit = emit or _noop
    log = log or _noop
    result = {"ok": False, "png": None, "reason": ""}

    boot = DolphinBoot(iso_path, slippi_path, runs_root,
                       hires_textures=hires_textures, clean_osd=True, log=log)
    p = None
    try:
        emit("booting", 10, "Preparing an isolated Dolphin (capture mode)…")
        boot.prepare()
        boot.launch()
        emit("booting", 20, "Waiting for the controller pipe…")
        if not boot.wait_for_pipe(timeout=45):
            result["reason"] = "Dolphin never opened its input pipe."
            return result

        emit("booting", 28, "Attaching to emulated memory…")
        d = Dolphin(boot.pid)
        t0 = time.time()
        while not d.locate() and time.time() - t0 < 20:
            if not d.alive():
                result["reason"] = "Dolphin exited during boot."
                return result
            time.sleep(0.4)
        if d.base is None:
            result["reason"] = "Could not read the game's memory after boot."
            return result

        _apply_code_patches(d, log=log)               # clean-shot patches (persist)
        solo = match_setup.patch_one_player(d, log=log)  # load in alone if possible

        p = Pipe(boot.pipe_index)
        cur = Cursor(d, p)
        sc = StageCursor(d, p)

        emit("at_css", 40, "Navigating to the character-select screen…")
        try:
            if not nav.nav_to_css(d, p, log=log):
                result["reason"] = "Could not reach the character-select screen."
                return result
        except nav.OnlineAbort as oa:
            result["reason"] = str(oa)
            return result
        nav.wait_css_ready(d, cur, log=log)
        match_setup.force_time_infinite(d, log=log)   # so a solo match persists

        emit("selecting_stage", 55, "Loading the stage…")
        # Primary: cursor-free memory selection (write a solo Fox + warp CSS->SSS).
        # The fighter is invisible for the shot, so any vanilla fighter works -- this
        # just skips the cursor lock + START. Falls back to the cursor path if we
        # couldn't load solo or the warp didn't land (then we're still on the CSS).
        on_sss = _memory_select_to_sss(d, sc, CKIND_FOX, 0, log) if solo else False
        if not on_sss:
            if not solo:
                nav.add_cpu(d, p, cur=cur, log=log)  # fallback: need a 2nd player
            _lock_vanilla(cur, "fox", 0)
            # Reach the stage-select screen (START from the locked CSS). With the
            # 1-player patch this works solo; otherwise the added CPU satisfies it.
            if not sc.ensure_stage_select():
                if not (not solo and _ensure_on_sss(d, p, sc, cur, log)):
                    result["reason"] = "Could not reach the stage-select screen."
                    return result
        if not sc.force_select(internal_id, hold=hold):
            result["reason"] = "Could not start the match on the stage."
            return result

        emit("framing", 75, "Framing the shot…")
        time.sleep(max(0.0, settle))             # past the GO! intro zoom
        std_eye = _read_vec3(d, CAM_STD_EYE)
        std_int = _read_vec3(d, CAM_STD_INT)
        std_fov = d.f32(CAM_STD_FOV)
        log(f"default cam eye={std_eye} interest={std_int} fov={std_fov}")
        fr = STAGE_FRAMING.get(framing_key, DEFAULT_FRAMING)

        emit("capturing", 90, "Capturing the screenshot…")
        # Settle the pose + clean-shot state, then grab the window's CLIENT area
        # (no title bar). The scene is static (solo, no timer, frozen DEBUG_FREE
        # camera), so the frame is stable; DEBUG_FREE sticks but the HUD flag is
        # re-read each frame, so we keep asserting it right up to the grab.
        for _ in range(15):
            _set_free_camera(d, fr["eye"], fr["interest"], fr["fov"])
            _apply_code_patches(d)
            d.write_u8(HUD_FLAG_ADDR, 0x01)
            time.sleep(0.016)
        if not d.alive():
            result["reason"] = "Dolphin exited before the screenshot."
            return result
        png = _screenshot.capture_png(boot.pid, max_width=960)
        if not png:
            result["reason"] = "Screenshot capture returned no image."
            return result
        result["ok"] = True
        result["png"] = png
        result["reason"] = "captured"
        result["solo"] = solo
        return result
    except Exception as e:
        result["reason"] = f"{type(e).__name__}: {e}"
        return result
    finally:
        try:
            if p is not None:
                p.close()
        except Exception:
            pass
        boot.cleanup()
