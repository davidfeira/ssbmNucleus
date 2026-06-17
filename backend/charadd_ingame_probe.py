"""
charadd_ingame_probe.py -- functional proof that a BATCH (add-fighters) build is
correct in-game, especially the one file that isn't byte-identical to the sequential
path: PlCo.dat (per-fighter bone lookup tables, read at fighter load). Loads EACH
custom fighter solo into a match; if PlCo were missing/corrupting a fighter's bone
table the fighter would crash on spawn. Healthy = global frame counter keeps
advancing in-match for several seconds.

Run from backend/:  python charadd_ingame_probe.py [slug1 slug2 ...]
  (builds the ISO with add-fighters, then boots once per char)
"""
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH, PROJECT_ROOT  # noqa: E402
from stress_build import run_mexcli, parse_json, TEST_BASE  # noqa: E402
from ingame.boot import DolphinBoot, dolphin_running  # noqa: E402
from ingame.melee_mem import Dolphin  # noqa: E402
from ingame.melee_pipe import Pipe  # noqa: E402
from ingame.melee_css import Cursor  # noqa: E402
from ingame.melee_sss import StageCursor, INTERNAL_STAGE_ID  # noqa: E402
from ingame.observe import wait_in_game, wait_game_frames  # noqa: E402
from ingame import nav, match_setup  # noqa: E402

VAULT = STORAGE_PATH / "custom_characters"
RUNS_ROOT = STORAGE_PATH / "test-runs"
ISO = (PROJECT_ROOT / "output" / "charbatch.iso").resolve()
FRAME_COUNTER = 0x80479D60
DEFAULT_SLUGS = ["wario", "slippy", "toad"]


def log(m):
    print(m, flush=True)


def build_iso(slugs):
    work = (STORAGE_PATH / "test-builds" / "charbatch_proj").resolve()
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(TEST_BASE, work)
    # strip video so the added fighters fit the disc
    for p in (work / "files").rglob("*"):
        if p.is_file() and p.name.lower().startswith("mv"):
            p.unlink()
    proj = str((work / "project.mexproj").resolve())

    entries = []
    for s in slugs:
        cdir = VAULT / s
        zp = cdir / "fighter.zip"
        if not zp.exists():
            log(f"  [skip] {s}: no fighter.zip")
            continue
        e = {"zip": str(zp.resolve())}
        vt = cdir / "victory_theme.hps"
        if vt.exists():
            try:
                entry = json.loads((cdir / "fighter.json").read_text(encoding="utf-8"))
                e["victoryName"] = (entry.get("victoryTheme") or {}).get("name") or f"{s} Victory"
            except Exception:
                e["victoryName"] = f"{s} Victory"
            e["victoryHps"] = str(vt.resolve())
        wav = cdir / "announcer.wav"
        if wav.exists():
            e["announcerWav"] = str(wav.resolve())
        entries.append((s, e))

    man = work / "manifest.json"
    man.write_text(json.dumps({"fighters": [e for _, e in entries]}))
    r = parse_json(run_mexcli(["add-fighters", proj, str(man)], timeout=1800).stdout) or {}
    if not r.get("success"):
        raise SystemExit(f"add-fighters failed: {r}")
    # map slug -> externalId from the result (results are in manifest order)
    chars = []
    for (s, _), res in zip(entries, r.get("fighters", [])):
        if res.get("success"):
            chars.append((res.get("name", s), res.get("externalId")))
    log(f"added {len(chars)} fighters: " + ", ".join(f"{n}=0x{e:02X}" for n, e in chars))

    iso = ISO
    iso.parent.mkdir(parents=True, exist_ok=True)
    cp = run_mexcli(["export", proj, str(iso), "0.5", "false", "false"], timeout=1800)
    res = parse_json(cp.stdout) or {}
    if not res.get("success") or not iso.exists():
        raise SystemExit(f"export failed: {res}")
    log(f"exported {iso.stat().st_size/1024/1024:.0f} MiB -> {iso}")
    shutil.rmtree(work, ignore_errors=True)
    return chars


def probe_char(ckind, name):
    """Boot, solo-load one fighter into a match, verify frames keep advancing."""
    res = {"name": name, "ckind": ckind, "verdict": "ERROR", "note": ""}
    boot = DolphinBoot(str(ISO), None, str(RUNS_ROOT), log=log)
    p = None
    try:
        boot.prepare()
        boot.launch()
        if not boot.wait_for_pipe(timeout=60):
            res["verdict"] = "NO-BOOT"
            return res
        d = Dolphin(boot.pid)
        t0 = time.time()
        while not d.locate() and time.time() - t0 < 25:
            if not d.alive():
                res["verdict"] = "CRASH-BOOT"
                return res
            time.sleep(0.4)
        if d.base is None:
            res["verdict"] = "NO-MEM1"
            return res

        match_setup.patch_one_player(d, log=log)
        p = Pipe(boot.pipe_index)
        if not nav.nav_to_css(d, p, log=log):
            res["verdict"] = "NO-CSS"
            return res
        nav.wait_css_ready(d, Cursor(d, p), log=log)
        match_setup.force_time_infinite(d, log=log)

        match_setup.write_solo_player(d, ckind, 0)
        match_setup.warp_to_stage_select(d)
        sc = StageCursor(d, p)
        if not sc.wait_for_stage_select(timeout=8.0):
            res["verdict"] = "NO-SSS"
            return res
        match_setup.write_solo_player(d, ckind, 0)
        if not sc.force_select(INTERNAL_STAGE_ID["battlefield"]):
            res["verdict"] = "NO-MATCH"
            return res

        if not wait_in_game(d, timeout=20.0):
            res["verdict"] = "NO-INGAME"
            return res
        wait_game_frames(d, 200)  # past READY/GO

        f0 = d.u32(FRAME_COUNTER)
        time.sleep(6.0)
        f1 = d.u32(FRAME_COUNTER)
        if not d.alive():
            res["verdict"] = "CRASHED"
            return res
        adv = (f1 - f0) & 0xFFFFFFFF if (f0 is not None and f1 is not None) else 0
        res["note"] = f"frames advanced {adv} in 6s"
        res["verdict"] = "HEALTHY" if adv > 250 else "HUNG"
        return res
    except Exception as e:  # noqa: BLE001
        res["verdict"] = "EXC"
        res["note"] = f"{type(e).__name__}: {e}"
        return res
    finally:
        try:
            if p:
                p.close()
        except Exception:
            pass
        boot.cleanup()


def main():
    slugs = sys.argv[1:] or DEFAULT_SLUGS
    if dolphin_running():
        log("WARNING: a Dolphin emulator is already open; close it for reliable input.")
    chars = build_iso(slugs)
    results = []
    for name, ckind in chars:
        log(f"\n################ {name} (ckind=0x{ckind:02X}) ################")
        r = probe_char(ckind, name)
        results.append(r)
        log(f"  -> {r['verdict']}  {r['note']}")
        time.sleep(3)

    log("\n==================== SUMMARY ====================")
    for r in results:
        log(f"  {r['name']:<16} ckind=0x{r['ckind']:02X}  {r['verdict']:<10} {r['note']}")
    ok = all(r["verdict"] == "HEALTHY" for r in results) and results
    log(f"\n==> {'PASS - all custom chars load in-game' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
