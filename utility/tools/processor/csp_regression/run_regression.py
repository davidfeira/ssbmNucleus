#!/usr/bin/env python3
"""
CSP renderer regression suite.

Guards every CSP-renderer fix we've made (see MANIFEST) against future
regressions in the headless HSDRawViewer `--csp` path. For each case it
(1) renders the costume DAT through the real generate_csp pipeline,
(2) compares the result to a stored golden PNG (the known-good output), and
(3) runs cheap health assertions (geometry present, body not flat white/black).

Usage:
    python run_regression.py                 # render + compare + assert
    python run_regression.py --update-goldens # regenerate goldens (after an
                                              # intentional, reviewed change)
    python run_regression.py --exe <dir>     # use a specific HSDRawViewer build
                                              # dir (default: the repo bin/Release)

A case named *_OPEN is a known-still-broken case: its golden is captured as the
CURRENT (broken) output and the run only warns on drift, so the suite stays green
until that fix lands (then update its golden + drop the _OPEN suffix).
"""
import os, sys, argparse, shutil
import numpy as np
from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, "cases")
GOLDENS = os.path.join(HERE, "goldens")
PROCESSOR = os.path.dirname(HERE)
sys.path.insert(0, PROCESSOR)
import generate_csp  # noqa: E402

# name -> {desc, fix, checks}. checks run on the rendered RGBA image.
MANIFEST = {
    "vanilla_fox":                  dict(fix="baseline", checks=["not_blank", "body_textured"]),
    "vanilla_marth":                dict(fix="baseline", checks=["not_blank", "body_textured"]),
    "wario_eyes_frameskip":         dict(fix="TexAnim same-dim frame skip (eyes)", checks=["not_blank", "body_textured"]),
    "sonic_eyes_stub_dfall_lowpoly":dict(fix="transparent-stub skip + DF_ALL + low-poly suppress (eyes/body)", checks=["not_blank", "body_textured"]),
    "mario_blue_eyes_stub":         dict(fix="transparent-stub skip (eyes)", checks=["not_blank", "body_textured"]),
    "ryu_falcon_causeG_white":      dict(fix="cause-G hasTEX RenderMode gating (white body)", checks=["not_blank", "body_textured"]),
    "marth_causeG":                 dict(fix="cause-G (white/black body)", checks=["not_blank", "body_textured"]),
    "slippy_va_null_geometry":      dict(fix="POBJ GX_VA_NULL terminator (geometry)", checks=["not_blank"]),
    "luigi_pink_va_null":           dict(fix="POBJ GX_VA_NULL terminator (geometry)", checks=["not_blank"]),
    "jiggly_nursehat_accessory":    dict(fix="mexCostume accessory bone-relative follow (nurse hat on head)", checks=["not_blank"]),
    "falco_hair_accessory":         dict(fix="mexCostume accessory bone-relative follow (hair on head)", checks=["not_blank"]),
    "pichu_bandana_accessory":      dict(fix="mexCostume accessory follow (bandana)", checks=["not_blank"]),
    "sheik_mask_accessory":         dict(fix="mexCostume accessory follow (mask)", checks=["not_blank"]),
}

GOLDEN_MAX_CHANGED_PX = 60   # allow tiny render jitter; eye/body breakage is 100s-1000s px


def render(dat, scale=1):
    p = generate_csp.generate_csp(dat, scale=scale)
    return p if (p and os.path.exists(p)) else None


def check_not_blank(arr):
    n = int((arr[:, :, 3] > 10).sum())
    return (n > 3000, f"non-transparent px={n} (want >3000 = geometry renders)")


def check_body_textured(arr):
    # central body region must not be near-uniform white or black (cause-G).
    h, w = arr.shape[:2]
    reg = arr[int(h*0.45):int(h*0.80), int(w*0.30):int(w*0.70), :3].astype(int)
    a = arr[int(h*0.45):int(h*0.80), int(w*0.30):int(w*0.70), 3]
    vis = a > 10
    if vis.sum() < 200:
        return (False, "body region nearly empty")
    px = reg[vis]
    near_white = ((px > 245).all(1)).mean()
    near_black = ((px < 12).all(1)).mean()
    var = float(px.std())
    ok = near_white < 0.85 and near_black < 0.85 and var > 6
    return (ok, f"body white%={near_white:.2f} black%={near_black:.2f} std={var:.1f}")


CHECKS = {"not_blank": check_not_blank, "body_textured": check_body_textured}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update-goldens", action="store_true")
    ap.add_argument("--exe", help="HSDRawViewer build dir (with HSDRawViewer.exe)")
    ap.add_argument("--pool", type=int, default=0, metavar="N",
                    help="render via a CspRenderPool of N persistent --csp-server "
                         "workers (validates the pooled batch path == one-shot)")
    args = ap.parse_args()
    if args.exe:
        generate_csp.HSDRAW_PATH = args.exe
        generate_csp.HSDRAW_EXE = os.path.join(args.exe, "HSDRawViewer.exe")
    os.makedirs(GOLDENS, exist_ok=True)
    work = os.path.join(HERE, "_out"); os.makedirs(work, exist_ok=True)

    pool = None
    if args.pool:
        sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "backend"))
        from skinlab.csp_pool import CspRenderPool
        pool = CspRenderPool(generate_csp.HSDRAW_EXE, workers=args.pool)
        generate_csp.set_active_pool(pool)
        print(f"[pool] rendering via {pool.size} persistent --csp-server worker(s)")

    passed = failed = warned = 0
    for name, spec in MANIFEST.items():
        dat = os.path.join(CASES, name + ".dat")
        if not os.path.exists(dat):
            print(f"SKIP  {name}: no DAT"); continue
        out = render(dat)
        if not out:
            print(f"FAIL  {name}: render produced no output"); failed += 1; continue
        cur = os.path.join(work, name + ".png"); shutil.copy(out, cur)
        arr = np.asarray(Image.open(cur).convert("RGBA"))
        is_open = name.endswith("_OPEN")
        msgs = []
        ok = True
        # health checks
        for c in spec.get("checks", []):
            cok, m = CHECKS[c](arr); msgs.append(f"{c}:{'ok' if cok else 'FAIL'}({m})")
            if not cok and not is_open:
                ok = False
        # golden compare
        golden = os.path.join(GOLDENS, name + ".png")
        if args.update_goldens or not os.path.exists(golden):
            shutil.copy(cur, golden); msgs.append("golden:created")
        else:
            ga = Image.open(golden).convert("RGB"); ca = Image.open(cur).convert("RGB")
            if ga.size != ca.size:
                msgs.append(f"golden:SIZE {ga.size}!={ca.size}");
                if not is_open: ok = False
            else:
                d = np.asarray(ImageChops.difference(ga, ca)); chg = int((d.sum(2) > 16).sum())
                if chg > GOLDEN_MAX_CHANGED_PX:
                    msgs.append(f"golden:DRIFT {chg}px")
                    if is_open: warned += 1
                    else: ok = False
                else:
                    msgs.append(f"golden:ok({chg}px)")
        status = "PASS " if ok else "FAIL "
        if ok: passed += 1
        else: failed += 1
        print(f"{status} {name}  [{spec['fix']}]  {' '.join(msgs)}")

    if pool is not None:
        generate_csp.set_active_pool(None)
        pool.close()

    print(f"\n=== {passed} passed, {failed} failed, {warned} open-warnings ===")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
