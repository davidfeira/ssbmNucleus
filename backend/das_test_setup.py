"""
das_test_setup.py -- build a test ISO with N DAS variants on one stage, to:
  (a) confirm NO-BUTTON selection randomly picks from the WHOLE pool (not just the
      6 button-mapped slots), and
  (b) find how many variants a stage can hold before it breaks (stage-lookup table
      / ISO size / loader).

Replicates backend/blueprints/das.py's install layout WITHOUT the Flask app:
  files/<code>/vanilla.dat   (original stage copied in)
  files/<code>/<name>.dat    (each variant; optional "(X)" button suffix)
  files/<code>.dat           (the DAS loader, replaces the stage file)

Run from backend/ (when no other mexcli build is running):
  python das_test_setup.py --stage dreamland --count 52 --buttons X,Y,Z \
      --out ../output/das-dreamland-52.iso --keep
"""
import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH, BASE_PATH  # noqa: E402
from stress_build import run_mexcli, parse_json  # noqa: E402

TEST_BASE = STORAGE_PATH / "test-base"
DAS = {  # stage -> (code, vault_folder, root_ext)
    "dreamland": ("GrOp", "dreamland", ".dat"),
    "battlefield": ("GrNBa", "battlefield", ".dat"),
    "finaldestination": ("GrNLa", "final_destination", ".dat"),
    "yoshisstory": ("GrSt", "yoshis_story", ".dat"),
    "fountainofdreams": ("GrIz", "fountain_of_dreams", ".dat"),
    "pokemonstadium": ("GrPs", "pokemon_stadium", ".usd"),
}


def log(m):
    print(m, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="dreamland")
    ap.add_argument("--count", type=int, default=52, help="how many variant files to place")
    ap.add_argument("--buttons", default="X,Y,Z", help="assign these buttons to the first variants")
    ap.add_argument("--out", required=True)
    ap.add_argument("--projname", default="dastest")
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    if args.stage not in DAS:
        raise SystemExit(f"unknown stage '{args.stage}'; known: {', '.join(DAS)}")
    code, folder, ext = DAS[args.stage]
    vault = STORAGE_PATH / "das" / folder
    zips = sorted(vault.glob("*.zip"))
    if not zips:
        raise SystemExit(f"no DAS zips in {vault}")
    out_iso = Path(args.out).resolve()
    out_iso.parent.mkdir(parents=True, exist_ok=True)
    buttons = [b.strip() for b in args.buttons.split(",") if b.strip()]

    work = (STORAGE_PATH / "test-builds" / f"{args.projname}_proj").resolve()
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    log(f"copying base -> {work}")
    shutil.copytree(TEST_BASE, work)
    files = work / "files"
    proj = str((work / "project.mexproj").resolve())

    stage_folder = files / code
    stage_folder.mkdir(exist_ok=True)
    original = files / f"{code}{ext}"
    loader = BASE_PATH / "utility" / "DynamicAlternateStages" / f"{code}{ext}"
    if original.exists():
        shutil.copy2(original, stage_folder / "vanilla.dat")  # vanilla variant

    placed = 0
    btn_assigned = []
    for i in range(args.count):
        z = zips[i % len(zips)]              # cycle (rename copies) if count > available
        try:
            with zipfile.ZipFile(z) as zf:
                # Match das.py's import filter: stadium variants are packaged as
                # .usd, other stages as .dat (the live import accepts both).
                dats = [n for n in zf.namelist()
                        if n.lower().endswith(".dat") or n.lower().endswith(".usd")]
                if not dats:
                    continue
                data = zf.read(dats[0])
        except Exception as e:
            log(f"  skip {z.name}: {e}")
            continue
        name = f"var{i:03d}"
        if i < len(buttons):
            name = f"{name}({buttons[i]})"   # button-mapped variant
            btn_assigned.append((buttons[i], name))
        (stage_folder / f"{name}.dat").write_bytes(data)
        placed += 1

    if loader.exists():
        shutil.copy2(loader, original)       # loader replaces the stage file
    else:
        raise SystemExit(f"DAS loader missing: {loader}")

    folder_dats = sorted(p.name for p in stage_folder.glob("*.dat"))
    log(f"placed {placed} variants; files/{code}/ has {len(folder_dats)} .dat "
        f"(incl vanilla); button-mapped={btn_assigned}")

    log(f"exporting -> {out_iso} ...")
    cp = run_mexcli(["export", proj, str(out_iso), "1.0", "false", "false"], timeout=1800)
    res = parse_json(cp.stdout) or {}
    log(f"export success={res.get('success')} status={res.get('status')} {res.get('error') or ''}")
    if cp.returncode != 0 and not res.get("success"):
        log(f"  stderr: {cp.stderr[:400]}")
    if out_iso.exists():
        log(f"ISO: {out_iso} size={out_iso.stat().st_size/1024/1024:.1f} MB")
    else:
        log("ISO NOT PRODUCED")

    log("SUMMARY " + json.dumps({
        "stage": args.stage, "code": code, "variants_placed": placed,
        "folder_dat_count": len(folder_dats), "buttons": btn_assigned,
        "iso": str(out_iso),
        "iso_mb": round(out_iso.stat().st_size / 1024 / 1024, 1) if out_iso.exists() else None,
        "export_success": bool(res.get("success")),
    }))
    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)
    return 0 if out_iso.exists() else 1


if __name__ == "__main__":
    raise SystemExit(main())
