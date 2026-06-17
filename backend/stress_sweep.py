"""
stress_sweep.py -- run stress_probe.py once per costume id (fresh Dolphin each,
for crash isolation) and tabulate the verdict + the runtime costume read-back
(ft+0x619). Lets us see, across a range of ids, which load as themselves vs clamp
to 0 vs crash -- i.e. where the per-character costume limit actually bites.

Run from backend/:
  python stress_sweep.py --iso ../output/stress-fox-255.iso --ckind 2 \
      --colors 0,4,32,63,64,100,200,253,254
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
PY = sys.executable


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", required=True)
    ap.add_argument("--ckind", default="2")
    ap.add_argument("--colors", required=True, help="comma list, e.g. 0,63,64,254")
    ap.add_argument("--stage", default="battlefield")
    ap.add_argument("--watch", default="8")
    args = ap.parse_args()

    colors = [int(c, 0) for c in args.colors.split(",") if c.strip() != ""]
    rows = []
    for c in colors:
        cp = subprocess.run(
            [PY, str(HERE / "stress_probe.py"), "--iso", args.iso, "--ckind",
             str(args.ckind), "--color", str(c), "--stage", args.stage,
             "--watch", str(args.watch)],
            capture_output=True, text=True, timeout=300,
        )
        res = None
        for line in cp.stdout.splitlines():
            if line.startswith("RESULT "):
                try:
                    res = json.loads(line[len("RESULT "):])
                except Exception:
                    pass
        if res is None:
            rows.append({"color": c, "verdict": "NO_RESULT", "read": None,
                         "tail": cp.stdout.strip().splitlines()[-3:]})
        else:
            cr = res.get("costume_read") or {}
            rows.append({"color": c, "verdict": res.get("verdict"),
                         "ft+0x619": cr.get("ft+0x619"), "css+0x03": cr.get("css+0x03")})
        print(f"  color {c:>3}: {rows[-1].get('verdict')} "
              f"ft+0x619={rows[-1].get('ft+0x619')} css={rows[-1].get('css+0x03')}",
              flush=True)

    print("\n=== SWEEP TABLE ===")
    print(f"{'color':>6} {'verdict':>12} {'ft+0x619':>9} {'css+0x03':>9} {'loaded_as_self':>15}")
    for r in rows:
        same = (r.get("ft+0x619") == r["color"])
        print(f"{r['color']:>6} {str(r.get('verdict')):>12} "
              f"{str(r.get('ft+0x619')):>9} {str(r.get('css+0x03')):>9} {str(same):>15}")
    print("\nSWEEP_JSON " + json.dumps(rows))


if __name__ == "__main__":
    raise SystemExit(main())
