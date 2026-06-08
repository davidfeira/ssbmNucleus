"""
match_setup.py -- direct-memory match setup shared by the in-game harness.

Two small WriteProcessMemory pokes that let the harness load a match ALONE (one
player, no CPU): relax the CSS "Ready to Fight" gate so a solo roster can start,
and force Time mode with no time limit so a one-player match doesn't instantly
end. Used by both the crash-test runner (runner.py) and the stage screenshot
capture (capture.py) -- loading solo is simpler and faster (no add-CPU cursor
sweep) and nothing can attack/SD/move the camera.

NTSC 1.02 addresses (doldecomp/melee):
  * CSS start gate: mncharsel fn_80262F44 +0x120 == 0x80263064, originally
    `cmpwi r4, 2` (r4 = valid player count); patch to `cmpwi r4, 1`.
  * GameRules (persistent menu rules the CSS reads) at 0x8045BF10: mode byte +0x02
    (0=Time), time-limit byte +0x03 (0 = no time / infinite).
Always RPM-read the gate first and only patch the exact expected opcode.
"""

import time

HOOK_1P = 0x80263064
HOOK_1P_ORIG = 0x2C040002        # cmpwi r4, 2  (require >= 2 players)
HOOK_1P_PATCH = 0x2C040001       # cmpwi r4, 1  (allow a solo start)

GAMERULES = 0x8045BF10
RULES_MODE = GAMERULES + 0x02    # 0 = Time, 1 = Stock, 2 = Coin
RULES_TIME = GAMERULES + 0x03    # minutes; 0 = no time / infinite

# --- cursor-free selection (write the match directly, then warp CSS->SSS) -------
# The CSS cursor is just an input method; the match loads whatever the per-port
# player block holds. So we write a solo player block and routing-poke the CSS
# straight to the stage-select screen -- no cursor lock, no add-CPU, no START
# "ready player" gate. The caller then force_selects the stage (the engine's own
# start, which finalizes rules so the solo match sustains).
CSS_PLAYERS = 0x80480820         # CSS-embedded StartMeleeData players, stride 0x24
VSDATA_PTR = 0x804D3EE0          # *(this)+0x5F8 = persistent VsModeData players
VS_PLAYERS_OFF = 0x5F8
PLAYER_STRIDE = 0x24
# PlayerInitData: c_kind +0x00, slot_type +0x01 (0=human,1=cpu,3=NA), stocks +0x02,
#                 color/costume +0x03, port +0x04, controller +0x07, team +0x09.
PENDING_SCENE = 0x80479D35       # next minor scene (target_minor + 1); SSS = 0x02
LOOP_BREAK = 0x80479D64          # break the current scene loop so the next loads


def _noop(*_a, **_k):
    pass


def patch_one_player(d, log=_noop, retries=15):
    """Relax the CSS start gate to allow a SOLO match. Returns True if 1-player
    starts are enabled (patched now or already), False if the hook never read as
    expected (caller should fall back to adding a 2nd player).

    Retries the read: right after attaching, that memory can momentarily read as
    0 / garbage, and a single bad read would silently drop us onto the slower
    cursor+CPU path. We re-check for a few seconds until the opcode appears."""
    last = None
    for _ in range(max(1, retries)):
        cur = d.u32(HOOK_1P)
        last = cur
        if cur == HOOK_1P_PATCH:
            return True
        if cur == HOOK_1P_ORIG:
            d.write_u32(HOOK_1P, HOOK_1P_PATCH)
            if d.u32(HOOK_1P) == HOOK_1P_PATCH:
                log("1-player start enabled (patched 0x80263064 cmpwi r4,2 -> r4,1)")
                return True
        time.sleep(0.2)
    log(f"1-player hook never settled at 0x80263064 (last 0x{(last or 0):08X}); "
        f"falling back to a 2nd player")
    return False


def force_time_infinite(d, log=_noop):
    """Time mode + no time limit, so a solo match doesn't instantly end."""
    d.write_u8(RULES_MODE, 0)
    d.write_u8(RULES_TIME, 0)
    log("VS rules set to Time / no time limit")


def write_solo_player(d, ckind, color=0):
    """Write a solo human match -- port 0 = `ckind`/`color`, ports 1-5 NA -- into
    BOTH the CSS-embedded StartMeleeData AND the persistent VsModeData, so a
    CSS->SSS memory warp (which skips CSS_Exit's panel->match copy) still starts a
    valid 1-player match as the chosen fighter. `ckind` is the EXTERNAL char id."""
    bases = [CSS_PLAYERS]
    container = d.u32(VSDATA_PTR)
    if container and 0x80000000 <= container < 0x81800000:
        bases.append(container + VS_PLAYERS_OFF)
    for base in bases:
        d.write_u8(base + 0x00, ckind & 0xFF)   # c_kind (external char id)
        d.write_u8(base + 0x01, 0)              # slot type: human
        d.write_u8(base + 0x02, 4)              # stocks
        d.write_u8(base + 0x03, color & 0xFF)  # costume / color slot
        d.write_u8(base + 0x04, 0)             # port
        d.write_u8(base + 0x07, 0)             # controller index
        d.write_u8(base + 0x09, 0)             # team
        d.write_u8(base + 0x0A, 0x78)          # nametag: none
        for port in range(1, 6):
            d.write_u8(base + port * PLAYER_STRIDE + 0x01, 3)  # NA (solo)


def warp_to_stage_select(d):
    """Routing poke: break the CSS frame loop with the SSS minor pending, so the VS
    major re-inits onto the stage-select screen -- skipping the cursor lock and the
    START 'ready player' gate. Only valid once on the vanilla CSS (the Slippi menu
    doesn't run the vanilla scene engine)."""
    d.write_u8(PENDING_SCENE, 0x02)   # SSS minor (0x01) + 1
    d.write_u8(LOOP_BREAK, 1)
