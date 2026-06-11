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
from .observe import wait_in_game, wait_game_frames, FRAME_COUNTER
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

# Per-base-stage camera framing (eye, interest, fov). Calibrated 2026-06-11 via
# _cap_calibrate.py sweeps (one boot per stage, candidates eyeballed). An absent
# stage falls back to DEFAULT_FRAMING. Keyed by the INTERNAL_STAGE_ID name.
DEFAULT_FRAMING = {"eye": (0.0, 20.0, 450.0), "interest": (0.0, 8.0, 0.0), "fov": 40.0}
STAGE_FRAMING = {
    "battlefield": {"eye": (0.0, 35.7, 189.5), "interest": (0.0, 29.7, 0.0), "fov": 40.0},
    "finaldestination": {"eye": (0.0, 14.0, 237.1), "interest": (0.0, 8.0, 0.0), "fov": 40.0},
    "dreamland": {"eye": (0.0, 34.2, 214.1), "interest": (0.0, 28.2, 0.0), "fov": 40.0},
    "yoshisstory": {"eye": (0.0, 29.5, 201.7), "interest": (0.0, 23.5, 0.0), "fov": 40.0},
    "fountainofdreams": {"eye": (0.0, 29.9, 175.3), "interest": (0.0, 23.9, 0.0), "fov": 40.0},
    "pokemonstadium": {"eye": (0.0, 65.0, 310.0), "interest": (0.0, 8.0, 0.0), "fov": 40.0},
}


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
                  hires_textures=False, framing_sweep=None):
    """Boot the ISO, load the stage ALONE in a no-timer Time match (internal_id,
    holding `hold` for a DAS variant), pose the camera, and return
    {"ok": bool, "png": bytes|None, "reason": str}.

    framing_key selects a per-base-stage camera preset (STAGE_FRAMING).
    framing_sweep (calibration): a list of framing dicts -- one boot, one shot
    per framing; returns {"ok", "shots": [{"framing", "png", "reason"}]}."""
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
        p.neutral()                  # start from a clean controller state before the held load
        time.sleep(0.15)
        if not sc.force_select(internal_id, hold=hold):
            result["reason"] = "Could not start the match on the stage."
            return result

        emit("framing", 75, "Waiting for the stage to finish loading…")
        if framing_sweep is not None:
            # calibration mode: one boot, many camera candidates. The camera is
            # deterministic (DEBUG_FREE, no per-frame recompute), so after the
            # first settled shot each new framing only needs a short hold.
            shots = []
            for i, fr in enumerate(framing_sweep):
                emit("capturing", 90, f"Sweep shot {i + 1}/{len(framing_sweep)}…")
                png, reason = _frame_and_shot(boot, d, fr,
                                              settle=settle if i == 0 else 0.7,
                                              log=log)
                shots.append({"framing": fr, "png": png, "reason": reason})
            result["ok"] = any(s["png"] for s in shots)
            result["shots"] = shots
            result["reason"] = "sweep"
            result["solo"] = solo
            return result
        fr = STAGE_FRAMING.get(framing_key, DEFAULT_FRAMING)
        emit("capturing", 90, "Capturing the screenshot…")
        png, reason = _frame_and_shot(boot, d, fr, settle=settle, log=log)
        if not png:
            result["reason"] = reason
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


def _hold_clean_pose(d, fr, frames=12):
    """Re-assert the DEBUG_FREE camera + clean-shot patches + HUD-off flag over
    `frames` real GAME frames right before the grab. DEBUG_FREE has no per-frame
    callback so the camera sticks, but the HUD flag is re-read every frame -- so
    we keep asserting it, counted in GAME frames (not wall-clock) so a slow
    machine can't grab the frame before the HUD-off flag has taken effect."""
    last = d.u32(FRAME_COUNTER)
    advanced = 0
    deadline = time.time() + max(1.5, frames / 10.0 + 1.0)
    while advanced < frames and time.time() < deadline and d.alive():
        _set_free_camera(d, fr["eye"], fr["interest"], fr["fov"])
        _apply_code_patches(d)
        d.write_u8(HUD_FLAG_ADDR, 0x01)
        f = d.u32(FRAME_COUNTER)
        if f is not None and last is not None:
            if f > last:
                advanced += f - last
            last = f
        time.sleep(0.008)


def _frame_and_shot(boot, d, fr, settle=4.0, log=_noop):
    """Wait for the match to actually be IN-GAME (absorbs host-variable stage load
    time), then wait a fixed number of GAME frames past the intro zoom -- both
    read from the game's own RAM, so this is host-SPEED independent (a slow
    Dolphin just takes more wall-clock for the same game frames; the old fixed
    time.sleep() grabbed too early on a slow machine). Then pose the DEBUG_FREE
    camera + re-assert the clean-shot state and grab. The scene is static (solo,
    no timer, frozen camera) so the frame is stable. Returns (png_bytes, reason);
    png_bytes is None on failure."""
    if not wait_in_game(d, timeout=30.0, log=log):
        return None, "stage never finished loading into a match"
    wait_game_frames(d, max(1, round(settle * 60)), log=log)   # past the GO! intro zoom
    log(f"default cam eye={_read_vec3(d, CAM_STD_EYE)} "
        f"interest={_read_vec3(d, CAM_STD_INT)} fov={d.f32(CAM_STD_FOV)}")
    _hold_clean_pose(d, fr)
    if not d.alive():
        return None, "Dolphin exited before the screenshot"

    # Grab the render window's own pixels (PrintWindow) -- clean even though the
    # throwaway Dolphin never takes the foreground. _hold_clean_pose just asserted
    # the DEBUG_FREE camera + HUD-off over the last frames, and the scene is static
    # (solo, no timer, frozen camera), so the grabbed frame is clean and stable.
    png = _screenshot.capture_via_printwindow(boot.pid, max_width=960)
    if not png:  # last resort: desktop grab of the window rect
        png = _screenshot.capture_png(boot.pid, max_width=960)
    if not png:
        return None, "screenshot capture returned no image"
    return png, "captured"


PAUSE_STAGE_INTERNAL_ID = 0x1F   # Battlefield: dark backdrop shows the light pause graphics


def _pause_match(d, p, tries=3, log=_noop):
    """Pause the running match by tapping START. Pausing hands the camera to the
    pause controller, so a CameraType change away from its in-match value is the
    confirmation signal (the global frame counter does NOT freeze on pause).
    Returns True when the switch was observed; the caller may still proceed
    optimistically on False -- a missed read just means we couldn't confirm."""
    m0 = d.u32(CAMERA_MODE)
    for attempt in range(1, tries + 1):
        p.tap("START", hold=0.08)
        deadline = time.time() + 1.2
        while time.time() < deadline and d.alive():
            m = d.u32(CAMERA_MODE)
            if m is not None and m0 is not None and m != m0:
                log(f"paused (camera mode {m0} -> {m}) on tap {attempt}")
                return True
            time.sleep(0.05)
        log(f"pause tap {attempt}: camera mode unchanged ({m0})")
    return False


def capture_pause(iso_path, slippi_path, runs_root, emit=None, log=None, settle=2.0,
                  internal_id=PAUSE_STAGE_INTERNAL_ID):
    """Boot the ISO, load a stage ALONE (invisible fighter, no timer), PAUSE the
    match, and screenshot the pause overlay -- the live preview for a pause
    screen mod. Same clean-shot setup as capture_stage but WITHOUT the HUD-off
    flag or the DEBUG_FREE camera: the pause overlay IS the subject, and pausing
    runs its own camera. Returns {"ok": bool, "png": bytes|None, "reason": str}."""
    emit = emit or _noop
    log = log or _noop
    result = {"ok": False, "png": None, "reason": ""}

    boot = DolphinBoot(iso_path, slippi_path, runs_root, clean_osd=True, log=log)
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

        # NO clean-shot code patches here: the pause preview should look like a
        # real paused game -- visible fighter, shadows, and the in-match HUD
        # behind the overlay. (The stage capture's invisible-fighter/HUD-off
        # patches made the pause shot look empty.)
        solo = match_setup.patch_one_player(d, log=log)

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
        match_setup.force_time_infinite(d, log=log)

        emit("selecting_stage", 55, "Loading the stage…")
        on_sss = _memory_select_to_sss(d, sc, CKIND_FOX, 0, log) if solo else False
        if not on_sss:
            if not solo:
                nav.add_cpu(d, p, cur=cur, log=log)
            _lock_vanilla(cur, "fox", 0)
            if not sc.ensure_stage_select():
                if not (not solo and _ensure_on_sss(d, p, sc, cur, log)):
                    result["reason"] = "Could not reach the stage-select screen."
                    return result
        p.neutral()
        time.sleep(0.15)
        if not sc.force_select(internal_id):
            result["reason"] = "Could not start the match."
            return result

        emit("framing", 75, "Waiting for the stage to finish loading…")
        if not wait_in_game(d, timeout=30.0, log=log):
            result["reason"] = "stage never finished loading into a match"
            return result
        wait_game_frames(d, max(1, round(settle * 60)), log=log)   # past the GO! intro zoom

        emit("capturing", 85, "Pausing the match…")
        paused = _pause_match(d, p, log=log)
        if not paused:
            log("could not confirm the pause via camera mode; capturing anyway")
        time.sleep(1.0)                              # let the overlay fade-in finish
        if not d.alive():
            result["reason"] = "Dolphin exited before the screenshot"
            return result

        emit("capturing", 92, "Capturing the screenshot…")
        png = _screenshot.capture_via_printwindow(boot.pid, max_width=960)
        if not png:
            png = _screenshot.capture_png(boot.pid, max_width=960)
        if not png:
            result["reason"] = "screenshot capture returned no image"
            return result
        result["ok"] = True
        result["png"] = png
        result["reason"] = "captured"
        result["paused_confirmed"] = paused
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


def capture_stage_batch(iso_path, slippi_path, runs_root, variants,
                        emit=None, log=None, settle=4.0, hires_textures=False):
    """Boot ONE ISO and screenshot many DAS variants -- possibly spanning SEVERAL
    base stages -- in a single session. Each variant carries its own stage + hold:
    `variants` = [{"id", "button", "internal_id", "framing_key"}] (as placed by
    build_stage_skin_multibatch_iso; `id` should be globally unique, e.g.
    "<stageCode>:<variantId>"). Build + boot happen once; between shots we quit to
    the CSS, re-enter, force-select that variant's stage holding its button.
    Returns {"ok": bool, "shots": [{"id","button","png"}], "reason": str}."""
    emit = emit or _noop
    log = log or _noop
    result = {"ok": False, "shots": [], "reason": ""}

    boot = DolphinBoot(iso_path, slippi_path, runs_root,
                       hires_textures=hires_textures, clean_osd=True, log=log)
    p = None
    try:
        emit("booting", 8, "Preparing an isolated Dolphin (capture mode)…")
        boot.prepare()
        boot.launch()
        emit("booting", 16, "Waiting for the controller pipe…")
        if not boot.wait_for_pipe(timeout=45):
            result["reason"] = "Dolphin never opened its input pipe."
            return result

        emit("booting", 22, "Attaching to emulated memory…")
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

        _apply_code_patches(d, log=log)
        solo = match_setup.patch_one_player(d, log=log)
        p = Pipe(boot.pipe_index)
        cur = Cursor(d, p)
        sc = StageCursor(d, p)

        emit("at_css", 26, "Navigating to the character-select screen…")
        try:
            if not nav.nav_to_css(d, p, log=log):
                result["reason"] = "Could not reach the character-select screen."
                return result
        except nav.OnlineAbort as oa:
            result["reason"] = str(oa)
            return result
        nav.wait_css_ready(d, cur, log=log)
        match_setup.force_time_infinite(d, log=log)

        n = len(variants)
        for i, v in enumerate(variants):
            vid, button = v["id"], v["button"]
            internal_id = v["internal_id"]
            fr = STAGE_FRAMING.get(v.get("framing_key"), DEFAULT_FRAMING)
            emit("capturing", 30 + int(60 * i / max(1, n)),
                 f"Capturing variant {i + 1}/{n}…")
            if i > 0:
                # Quit the previous match back to the CSS before the next variant.
                if not nav.reset_to_css(d, p, log=log):
                    result["reason"] = "Could not return to the CSS between variants."
                    break
            on_sss = _memory_select_to_sss(d, sc, CKIND_FOX, 0, log) if solo else False
            if not on_sss:  # fallback to the cursor path (stays on CSS if warp missed)
                if not solo:
                    nav.add_cpu(d, p, cur=cur, log=log)
                _lock_vanilla(cur, "fox", 0)
                if not sc.ensure_stage_select():
                    if not (not solo and _ensure_on_sss(d, p, sc, cur, log)):
                        log(f"could not reach the SSS for {vid}; skipping")
                        continue
            p.neutral()              # clear any residual held button from the prior variant
            time.sleep(0.15)
            if not sc.force_select(internal_id, hold=button):
                log(f"could not start the match for {vid} (hold {button}); skipping")
                continue
            png, reason = _frame_and_shot(boot, d, fr, settle=settle, log=log)
            if png:
                result["shots"].append({"id": vid, "button": button, "png": png})
                log(f"captured {vid} (hold {button})")
            else:
                log(f"screenshot failed for {vid}: {reason}")
            if not d.alive():
                result["reason"] = "Dolphin exited mid-batch."
                break

        result["ok"] = len(result["shots"]) > 0
        if not result["reason"]:
            result["reason"] = f"captured {len(result['shots'])}/{n}"
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
