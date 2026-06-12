"""Copy per-joint JObj flags from a vanilla DAT onto a structurally-identical
round-trip DAT (same joint tree, walked in the same order)."""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ssbmNucleus" / "backend"))
from skinlab.datprobe import DatFile, HEADER_SIZE  # noqa: E402

src_path, dst_path, out_path = sys.argv[1:4]
src = DatFile(src_path)
dst = DatFile(dst_path)

src_root = next(o for n, o in src.roots if n.endswith("_joint") and "matanim" not in n)
dst_root = next(o for n, o in dst.roots if n.endswith("_joint") and "matanim" not in n)

src_jobjs = src._iter_tree(src_root, 0x08, 0x0C)
dst_jobjs = dst._iter_tree(dst_root, 0x08, 0x0C)
assert len(src_jobjs) == len(dst_jobjs), (len(src_jobjs), len(dst_jobjs))

raw = bytearray(dst.raw)
patched = 0
for s_off, d_off in zip(src_jobjs, dst_jobjs):
    flags = src.u32(s_off + 0x04)
    cur = dst.u32(d_off + 0x04)
    if flags != cur:
        struct.pack_into(">I", raw, HEADER_SIZE + d_off + 0x04, flags)
        patched += 1

Path(out_path).write_bytes(raw)
print(f"patched {patched} joint flag words -> {out_path}")
