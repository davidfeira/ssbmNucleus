"""
sideb_probe.py -- SOLO (no CPU, no cursor) in-game crash probe for a fighter's
side-B (or any special). Built for the Metal-Mario cape crash, but reusable.

Uses the backend/ingame engine: memory-load the match ALONE (relaxed Ready-to-
Fight gate + direct player-block write), then spam the special and watch the
global frame counter for a freeze (m-ex's `assertion "0" failed ... item not
initialized` halts the game = frame freeze) or a hard process death.

This is the canonical "test a move in-game" recipe -- see backend/ingame/README.md.
Do NOT use the CSS-cursor + CPU path (tests/dolphin + cl_match): a CPU attacking
you ruins the repro, and it's slower.

    cd backend && python sideb_probe.py --iso <path> [--ckind 0x1A]
                  [--stage battlefield] [--move sideb|neutralb|upb|downb] [--reps 24]

ckind = external CSS fighter id; the FIRST added m-ex fighter = 0x1A. Exit 0 if
the move ran with the game alive + advancing, 1 on crash/hang.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.config import STORAGE_PATH, PROJECT_ROOT  # noqa: E402
from ingame.boot import DolphinBoot  # noqa: E402
from ingame.melee_mem import Dolphin  # noqa: E402
from ingame.melee_pipe import Pipe  # noqa: E402
from ingame.melee_css import Cursor  # noqa: E402
from ingame.melee_sss import StageCursor, INTERNAL_STAGE_ID  # noqa: E402
from ingame.observe import wait_in_game, wait_game_frames  # noqa: E402
from ingame import nav, match_setup  # noqa: E402

RUNS_ROOT = STORAGE_PATH / "test-runs"
FRAME_COUNTER = 0x80479D60
STATIC_PLAYER = 0x80453080
STATIC_STRIDE = 0xE90

# m-ex live item-table read (to see why RuntimeIndex[cape] is null).
RTOC = 0x804DF9E0          # r2 (rtoc) for this m-ex build (from DOL __start)
OFST_ITEMS_ADDED = 0x88    # m-ex Header.s: OFST_ItemsAdded(rtoc)
ITEMSADDED_CUSTOM = 0x10   # Arch_ItemsAdded_Custom  (MEXItems fn table, 0x3C stride)
ITEMSADDED_RTINDEX = 0x14  # Arch_ItemsAdded_RuntimeIndex (article DATA ptrs, 4 stride)


def _mem_ptr(v):
    return v is not None and 0x80000000 <= v < 0x81800000


def parse_ranges(spec):
    """'1,3-200' -> [1,3,4,...,200]."""
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return out


def dump_item_tables(d, ft, log):
    """Print the live m-ex custom-item tables: RuntimeIndex (article DATA ptrs,
    the field Create Item null-checks) and Custom (fn tables). A null cape slot
    means onLoad's MEX_IndexFighterItem never stored it."""
    internal = d.u8(ft + 0x4) if ft else None
    hook = d.u32(0x800E12C0)   # our C2 patches this to a branch; orig = 0x38810014
    log(f"  [hook] code@0x800E12C0 = 0x{(hook or 0):08X} "
        f"({'BRANCH (C2 applied)' if hook and (hook >> 26) == 0x12 else 'orig (C2 NOT applied)'})")
    ftdata = d.u32(ft + 0x10C) if ft else None     # FighterData->ftData
    if _mem_ptr(ftdata):
        items = d.u32(ftdata + 0x48)               # ftData->items (article table)
        log(f"  [ftData] ftData=0x{ftdata:08X} items=0x{(items or 0):08X}")
        if _mem_ptr(items):
            arts = [d.u32(items + i * 4) for i in range(4)]
            log(f"  [ftData] items[0..3]={['0x%08X' % (a or 0) for a in arts]}")
            # Find the REAL FighterRuntime table the cape reads: array with
            # items[0] (fireball=48) at slot 5 and items[2] (cape=83) at slot 40.
            i0, i2 = arts[0], arts[2]
            if _mem_ptr(i0) and _mem_ptr(i2):
                import struct as _st
                blob = d.bytes(0x80700000, 0x300000) or b""
                tgt = _st.pack(">I", i2)
                fb = _st.pack(">I", i0)
                hits, pos = [], -1
                while True:
                    pos = blob.find(tgt, pos + 1)
                    if pos < 0:
                        break
                    tbl = pos - 160
                    if tbl >= 20 and blob[tbl + 20:tbl + 24] == fb:
                        hits.append(0x80700000 + tbl)
                log(f"  [REAL fighter-tab] table(s) w/ fireball@5 & cape@40: "
                    f"{[hex(h) for h in hits]}")
    R13 = 0x804DB6A0
    ftab = d.u32(R13 - 0x4968)                # Fighter-item runtime DATA table
    if _mem_ptr(ftab):
        fr = [d.u32(ftab + s * 4) for s in range(38, 43)]
        log(f"  [fighter-tab] FighterRuntime=0x{ftab:08X} [38..42(cape=40)]="
            f"{['0x%08X' % (x or 0) for x in fr]}")
    sa = d.u32(ft + 0x2D4) if ft else None    # FighterData->special_attributes
    if _mem_ptr(sa):
        ck = d.u32(sa + 0x14)                 # MarioAttr.cape_item_kind
        log(f"  [cape] special_attributes=0x{sa:08X}  cape_item_kind(+0x14)={ck} (0x{ck:X})")
    items = d.u32(RTOC + OFST_ITEMS_ADDED)
    log(f"  [items] internal_kind=0x{(internal or 0):X}  ItemsAdded=0x{(items or 0):08X}")
    if not _mem_ptr(items):
        log("  [items] ItemsAdded ptr invalid (rtoc guess off); skipping table dump")
        return
    custom = d.u32(items + ITEMSADDED_CUSTOM)
    runtime = d.u32(items + ITEMSADDED_RTINDEX)
    log(f"  [items] Custom=0x{(custom or 0):08X}  RuntimeIndex=0x{(runtime or 0):08X}")
    if _mem_ptr(runtime):
        s = [d.u32(runtime + i * 4) for i in range(82)]
        log(f"  [items] RuntimeIndex[0..4]={['0x%08X' % (x or 0) for x in s[0:5]]}")
        log(f"  [items] RuntimeIndex[74..81]={['0x%08X' % (x or 0) for x in s[74:82]]}")
    if _mem_ptr(custom):
        c = [d.u32(custom + i * 0x3C) for i in range(82)]
        log(f"  [items] Custom.w0[0..4]={['0x%08X' % (x or 0) for x in c[0:5]]}")
        log(f"  [items] Custom.w0[74..81]={['0x%08X' % (x or 0) for x in c[74:82]]}")
    # Find mexData (rtoc slot P with u32(P+0x1C)==ItemsAdded) -> live MEXItemLookup.
    mexdata = None
    for off in range(0, 0x800, 4):
        v = d.u32(RTOC + off)
        if _mem_ptr(v) and d.u32(v + 0x1C) == items:
            mexdata = v
            break
    if mexdata:
        af = d.u32(mexdata + 0x8)                          # Arch_Fighter
        lk = d.u32(af + 0x4C) if _mem_ptr(af) else None    # +0x4C MEXItemLookup
        log(f"  [lk] mexData=0x{mexdata:08X} lookup=0x{(lk or 0):08X}")
        if _mem_ptr(lk):
            for fid in range(0, 60):
                cnt = d.u32(lk + fid * 8)
                ep = d.u32(lk + fid * 8 + 4)
                if cnt and 0 < cnt < 16 and _mem_ptr(ep):
                    ents = [(d.u8(ep + k * 2) << 8) | d.u8(ep + k * 2 + 1)
                            for k in range(cnt)]
                    log(f"  [lk] lookup[{fid}] Count={cnt} Entries={ents}")

# stick directions for the special: x,y (0.5 center, x=1 right, y=1 down)
MOVE_DIR = {"sideb": (1.0, 0.5), "neutralb": (0.5, 0.5),
            "upb": (0.5, 0.0), "downb": (0.5, 1.0)}


def log(m):
    print(m, flush=True)


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def ft_data(d, port=0):
    gobj = d.u32(STATIC_PLAYER + STATIC_STRIDE * port + 0xB0)
    return d.u32(gobj + 0x2C) if gobj else None


def do_move(p, move):
    x, y = MOVE_DIR[move]
    if move == "neutralb":
        p.tap("B", 0.05)
        return
    p.main(x, y)          # hold the direction (persistent pipe)
    time.sleep(0.03)
    p.tap("B", 0.05)      # special in that direction
    p.center()


def health(d, last):
    """Return (ok, frame, msg). ok=False => crash/hang."""
    if not d.alive():
        return False, None, "process exited (CRASH)"
    frame = d.u32(FRAME_COUNTER)
    if frame is None:
        time.sleep(0.2)
        frame = d.u32(FRAME_COUNTER)
        if frame is None:
            return False, None, "MEM1 unreadable (CRASH)"
    return True, frame, f"frame={frame}"


def main():
    iso = Path(arg("--iso", str(PROJECT_ROOT / "output" / "harness-test.iso")))
    if not iso.exists():
        raise SystemExit(f"ISO missing: {iso}")
    ckind = int(arg("--ckind", "0x1A"), 0)
    stage = arg("--stage", "battlefield")
    move = arg("--move", "sideb")
    reps = int(arg("--reps", "24"))
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)

    boot = DolphinBoot(str(iso), None, str(RUNS_ROOT), log=log)
    p = None
    try:
        boot.prepare()
        boot.launch()
        if not boot.wait_for_pipe(timeout=45):
            raise SystemExit("input pipe never appeared")
        d = Dolphin(boot.pid)
        t0 = time.time()
        while not d.locate() and time.time() - t0 < 20:
            if not d.alive():
                raise SystemExit("Dolphin died during boot")
            time.sleep(0.4)
        if d.base is None:
            raise SystemExit("could not locate MEM1")

        match_setup.patch_one_player(d, log=log)
        p = Pipe(boot.pipe_index)
        # A fresh isolated User dir has no memory card, so Melee shows a "create
        # save data?" prompt that blocks the menu (scene stays 0x00 / boot). Tap
        # A a few times during boot to dismiss it, stopping once the menu (0x01)
        # or a CSS scene appears.
        for _ in range(6):
            maj = d.u8(nav.SCENE_MAJOR)
            if maj in (nav.MENU_MAJOR, nav.VS_MAJOR, nav.ONLINE_CSS):
                break
            log(f"boot prompt dismiss: tapping A (scene major=0x{(maj or 0):02X})")
            p.tap("A", 0.08)
            time.sleep(1.2)
        if not nav.nav_to_css(d, p, log=log):
            raise SystemExit("never reached the offline CSS")
        nav.wait_css_ready(d, Cursor(d, p), log=log)
        match_setup.force_time_infinite(d, log=log)

        log(f"memory-select ckind=0x{ckind:02X} solo, stage={stage}...")
        match_setup.write_solo_player(d, ckind, 0)
        match_setup.warp_to_stage_select(d)
        sc = StageCursor(d, p)
        if not sc.wait_for_stage_select(timeout=8.0):
            raise SystemExit("CSS->SSS warp did not land")
        match_setup.write_solo_player(d, ckind, 0)
        if stage not in INTERNAL_STAGE_ID:
            raise SystemExit(f"unknown stage {stage}; have {list(INTERNAL_STAGE_ID)}")
        if not sc.force_select(INTERNAL_STAGE_ID[stage]):
            raise SystemExit("match never started")

        wait_in_game(d, timeout=20.0)
        wait_game_frames(d, 200)  # past READY/GO!
        ft = ft_data(d)
        log(f"in-game; p1 ftData=0x{(ft or 0):08X}; spamming {move} x{reps}")
        dump_item_tables(d, ft, log)
        ftab40 = (d.u32(0x804DB6A0 - 0x4968) or 0) + 40 * 4  # FighterRuntime[cape=40]
        frt40 = set()

        # Diagnostic: fill chosen RuntimeIndex slots with the cape's data ptr
        # (RuntimeIndex[2]) to discover which slot the cape spawn reads. If the
        # crash stops, the cape reads one of the filled slots.
        fill = arg("--fill-range")
        if fill:
            items = d.u32(RTOC + OFST_ITEMS_ADDED)
            runtime = d.u32(items + ITEMSADDED_RTINDEX) if _mem_ptr(items) else None
            cape = d.u32(runtime + 2 * 4) if _mem_ptr(runtime) else None
            if _mem_ptr(runtime) and _mem_ptr(cape):
                slots = parse_ranges(fill)
                for s in slots:
                    d.write_u32(runtime + s * 4, cape)
                # verify the write took
                rb = [d.u32(runtime + s * 4) for s in slots[:3]]
                log(f"FILLED RuntimeIndex slots {fill} with cape data 0x{cape:08X} "
                    f"({len(slots)} slots); readback[:3]={['0x%08X' % (x or 0) for x in rb]}")
            else:
                log(f"fill skipped: runtime=0x{(runtime or 0):08X} cape=0x{(cape or 0):08X}")
        if "--poison-f40" in sys.argv:
            ftp = d.u32(0x804DB6A0 - 0x4968)
            if _mem_ptr(ftp):
                pre = d.u32(ftp + 40 * 4)
                d.write_u32(ftp + 40 * 4, 0xDEADBEEF)
                log(f"POISONED FighterRuntime[40]@0x{ftp + 160:08X} (was "
                    f"0x{(pre or 0):08X}) -> 0xDEADBEEF")
        # Zero chosen Custom RuntimeIndex slots (to find which the cape reads).
        zc = arg("--zero-custom")
        if zc:
            items = d.u32(RTOC + OFST_ITEMS_ADDED)
            runtime = d.u32(items + ITEMSADDED_RTINDEX) if _mem_ptr(items) else None
            if _mem_ptr(runtime):
                pre = {s: d.u32(runtime + s * 4) for s in parse_ranges(zc)}
                for s in parse_ranges(zc):
                    d.write_u32(runtime + s * 4, 0)
                log(f"ZEROED RuntimeIndex slots {zc}; pre="
                    f"{ {s: '0x%08X' % (v or 0) for s, v in pre.items()} }")
        # Fill the FIGHTER-category runtime table (u32(r13-0x4968)); cape_item_kind=83
        # is a Fighter item -> Create Item reads FighterRuntime[83-43=40].
        fillf = arg("--fill-fighter")
        if fillf:
            R13 = 0x804DB6A0
            ftab = d.u32(R13 - 0x4968)
            items = d.u32(RTOC + OFST_ITEMS_ADDED)
            runtime = d.u32(items + ITEMSADDED_RTINDEX) if _mem_ptr(items) else None
            cape = d.u32(runtime + 2 * 4) if _mem_ptr(runtime) else None
            log(f"  [fighter-tab] FighterRuntime=0x{(ftab or 0):08X}")
            if _mem_ptr(ftab) and _mem_ptr(cape):
                pre = [d.u32(ftab + s * 4) for s in (39, 40, 41)]
                log(f"  [fighter-tab] pre [39,40,41]={['0x%08X' % (x or 0) for x in pre]}")
                for s in parse_ranges(fillf):
                    d.write_u32(ftab + s * 4, cape)
                log(f"FILLED FighterRuntime[{fillf}] with cape 0x{cape:08X}")
            else:
                log(f"fill-fighter skipped: ftab=0x{(ftab or 0):08X} cape=0x{(cape or 0):08X}")

        # Track frame ADVANCEMENT globally (a freeze can straddle reps). A hang
        # (e.g. m-ex's "item not initialized" assert) leaves the process alive
        # but the global frame counter stuck -- and it corrupts the scene bytes,
        # so DON'T treat "left in-game" as a clean pass unless frames advance.
        last_adv = d.u32(FRAME_COUNTER)
        last_adv_t = time.time()
        last_state = None
        seen_states = set()
        cape_kinds = set()
        for i in range(reps):
            do_move(p, move)
            t_end = time.time() + 0.6
            while time.time() < t_end:
                if not d.alive():
                    log(f"  {move} #{i+1}: CRASH (process exited) at state "
                        f"0x{(d.u32(ft + 0x10) if ft else 0):X}")
                    return 1
                frame = d.u32(FRAME_COUNTER)
                if frame is None:
                    log(f"  {move} #{i+1}: CRASH (MEM1 unreadable)")
                    return 1
                stp = d.u32(ft + 0x10) if ft else None
                if stp is not None:
                    seen_states.add(stp)
                ftp = d.u32(0x804DB6A0 - 0x4968)   # re-read table ptr fresh (may relocate)
                if _mem_ptr(ftp):
                    frt40.add(d.u32(ftp + 40 * 4))
                # Read MarioCharVar.item_cape (fighter_var 0x222C + 0x10) -> cape gobj
                # -> ItemData.kind (the global item id the cape spawned with).
                for capeoff in (0x223C, 0x1984):   # item_cape, then item_held_spec
                    ig = d.u32(ft + capeoff) if ft else None
                    if _mem_ptr(ig):
                        idata = d.u32(ig + 0x2C)
                        if _mem_ptr(idata):
                            kk = d.u32(idata + 0x10)        # ItemData.kind
                            fn = d.u32(idata + 0xB8)        # item fn table (Create Item)
                            dp = d.u32(idata + 0xC4)        # item data ptr (Create Item)
                            if kk is not None:
                                cape_kinds.add((kk, fn, dp))
                if frame != last_adv:
                    last_adv, last_adv_t = frame, time.time()
                elif time.time() - last_adv_t > 2.5:
                    st = d.u32(ft + 0x10) if ft else None
                    log(f"  {move} #{i+1}: HANG -- frame frozen at {frame}, "
                        f"state=0x{(st or 0):X} (m-ex assert / cape crash)")
                    log(f"  cape (kind,fn,data) before hang: {sorted('kind=%d fn=0x%08X data=0x%08X' % (k, f or 0, dp or 0) for k, f, dp in cape_kinds)}")
                    log(f"  FighterRuntime[40] seen before hang: "
                        f"{sorted('0x%08X' % v for v in frt40 if v is not None)}")
                    return 1
                time.sleep(0.01)
            st = d.u32(ft + 0x10) if ft else None
            if st != last_state:
                last_state = st
                log(f"  {move} #{i+1}: frame={d.u32(FRAME_COUNTER)} state=0x{(st or 0):X}")

        # Final verdict: must be alive AND still advancing frames.
        f1 = d.u32(FRAME_COUNTER)
        time.sleep(1.2)
        f2 = d.u32(FRAME_COUNTER)
        if not d.alive() or f1 is None or f2 is None:
            log("FINAL FAIL: process/MEM1 gone (CRASH)")
            return 1
        if f1 == f2:
            st = d.u32(ft + 0x10) if ft else None
            log(f"FINAL FAIL: frame frozen at {f2}, state=0x{(st or 0):X} (HANG)")
            return 1
        log(f"states seen during {move}: "
            f"{sorted('0x%X' % s for s in seen_states if s is not None)}")
        log(f"cape spawned (kind,fnTab,dataPtr): {sorted('kind=%d fn=0x%08X data=0x%08X' % (k, f or 0, dp or 0) for k, f, dp in cape_kinds)}")
        log(f"FighterRuntime[40] values seen during {move}: "
            f"{sorted('0x%08X' % v for v in frt40 if v is not None)}")
        log(f"SpecialS (0x159) entered (cape actually fired): "
            f"{'YES' if 0x159 in seen_states else 'NO -- cape did not fire!'}")
        log(f"FINAL OK: alive + advancing ({f1}->{f2})")
        return 0
    finally:
        try:
            if p:
                p.close()
        except Exception:
            pass
        boot.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
