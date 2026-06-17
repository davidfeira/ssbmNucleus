"""
proj_diff.py -- compare two built project dirs file-by-file (presence + size + md5)
to find which generated files differ. Used to locate what the BATCH import path
corrupts vs sequential (the CSS-critical files: MnSlChr/IfAll/MxDt/PlCo...).

Run from backend/:  python proj_diff.py <projA_dir> <projB_dir>
"""
import hashlib
import sys
from pathlib import Path


def index(root):
    out = {}
    for p in root.rglob("*"):
        if p.is_file():
            rel = str(p.relative_to(root)).replace("\\", "/")
            sz = p.stat().st_size
            h = hashlib.md5(p.read_bytes()).hexdigest() if sz < 80_000_000 else f"big:{sz}"
            out[rel] = (sz, h)
    return out


def main():
    A, B = Path(sys.argv[1]), Path(sys.argv[2])
    ia, ib = index(A), index(B)
    onlyA = sorted(set(ia) - set(ib))
    onlyB = sorted(set(ib) - set(ia))
    diff = sorted(k for k in set(ia) & set(ib) if ia[k] != ib[k])

    print(f"A = {A}")
    print(f"B = {B}")
    print(f"\nonly in A ({len(onlyA)}):")
    for k in onlyA[:40]:
        print(f"  - {k}  ({ia[k][0]} B)")
    print(f"\nonly in B ({len(onlyB)}):")
    for k in onlyB[:40]:
        print(f"  + {k}  ({ib[k][0]} B)")
    print(f"\ndiffering content ({len(diff)}):")
    for k in diff[:60]:
        a, b = ia[k], ib[k]
        tag = f"size {a[0]} vs {b[0]}" if a[0] != b[0] else f"same size {a[0]}, content differs"
        print(f"  ~ {k}   [{tag}]")
    if not (onlyA or onlyB or diff):
        print("  (projects are byte-identical)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
