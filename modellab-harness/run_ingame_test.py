"""Drive the in-app in-game costume test (solo load + forced stage) directly,
bypassing Flask — same code path as /api/mex/test-in-game/costume."""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

BACKEND = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from test_build import build_single_costume_iso  # noqa: E402
from ingame.runner import run_test  # noqa: E402

STORAGE = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\storage")
VANILLA = r"C:\Users\david\projects\melee\working\melee-vanilla-v1.02-working.iso"
SLIPPI = os.path.join(os.environ["APPDATA"], "Slippi Launcher", "netplay")

character = sys.argv[1] if len(sys.argv) > 1 else "Fox"
skin_id = sys.argv[2] if len(sys.argv) > 2 else "roundtrip-test-plfxrt"

skin_zip = STORAGE / character / f"{skin_id}.zip"
assert skin_zip.exists(), skin_zip

runs_root = STORAGE / "test-runs"
build_dir = STORAGE / "test-builds"
runs_root.mkdir(parents=True, exist_ok=True)
build_dir.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
out_iso = build_dir / f"modellab_{stamp}.iso"

print(f"building one-costume ISO for {character} / {skin_id} ...")
index = build_single_costume_iso(
    vanilla_iso=VANILLA, character=character, skin_zip=str(skin_zip),
    out_iso=str(out_iso),
    progress_cb=lambda p, m: print(f"  build {p}% {m}"),
    log=lambda m: print(f"  {m}"),
)
print(f"built {out_iso} (costume index {index})")

manifest = {"costume": {"fighter": character, "colorIndex": index, "name": skin_id}}
result = run_test(
    iso_path=str(out_iso), slippi_path=SLIPPI, runs_root=str(runs_root),
    manifest=manifest,
    emit=lambda stage, pct, msg: print(f"  [{stage} {pct}%] {msg}"),
    log=lambda m: print(f"  {m}"),
    observe_seconds=9,
)

print("verdict:", result.get("verdict"), "| pass:", result.get("pass"), "|", result.get("reason"))

# save the screenshot data-uri to a png
shot = result.get("screenshot")
if shot and shot.startswith("data:image"):
    import base64
    b64 = shot.split(",", 1)[1]
    out_png = Path(r"C:\Users\david\projects\ssbmNucleus-master\modellab\out\falco_on_fox\ingame.png")
    out_png.write_bytes(base64.b64decode(b64))
    print("screenshot ->", out_png)
for c in result.get("checks", []):
    print("  check:", json.dumps({k: c.get(k) for k in ("label", "verdict", "reason")}))
    s = c.get("screenshot")
    if s and s.startswith("data:image"):
        import base64
        p = Path(rf"C:\Users\david\projects\ssbmNucleus-master\modellab\out\falco_on_fox\ingame_{c.get('label', 'check').replace(' ', '_')}.png")
        p.write_bytes(base64.b64decode(s.split(",", 1)[1]))
        print("  ->", p)

try:
    out_iso.unlink()
except OSError:
    pass
