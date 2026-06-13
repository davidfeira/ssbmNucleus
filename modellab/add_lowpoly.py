"""Add a real LOW-POLY model to an EXISTING costume DAT whose LowPoly DObj
slots are empty (so the off-screen magnifier shows nothing and the projected
shadow is broken). Decimates the high-poly body, fills the FIRST empty LowPoly
slot with it (weights carried from the nearest high vertex), and re-imports.

Key safety property: we fill an ALREADY-PRESENT empty slot — the DObj count is
unchanged and the high/eye DObjs are byte-untouched in the SMD, so the matanim
(eye blink) re-binds without --strip-matanim. The high model is re-encoded by
the importer (same proven round-trip as every costume import), not modified.

usage: add_lowpoly.py <costume.dat> <ftData.dat> <out.dat> [--strip-matanim]
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
EXE = ROOT / ("utility/tools/HSDLib/HSDRawViewer/bin/Release/"
              "net6.0-windows/HSDRawViewer.exe")

import numpy as np  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

from modellab import smd as S  # noqa: E402
from modellab.rig import ForeignMesh, decimate, recompute_normals  # noqa: E402
from skinlab.datprobe import DatFile  # noqa: E402


def joint_symbol(dat_path):
    for m in re.findall(rb"[\x20-\x7e]{8,}", Path(dat_path).read_bytes()):
        s = m.decode("ascii", "replace")
        if s.endswith("_joint") and "matanim" not in s.lower():
            return s
    raise RuntimeError(f"no joint symbol in {dat_path}")


def low_indices(ft_path):
    """LowPoly DObj indices from a fighter ftData's costume-0 visibility table
    (reloc-aware: vanilla/custom dats store the table at data offset 0)."""
    d = DatFile(str(ft_path))
    ft = next(o for n, o in d.roots if n.startswith("ftData"))
    lk = d.ptr(ft + 0x08)

    def rptr(o):
        return d.u32(o) if o in d.relocs else None

    table = rptr(rptr(lk + 0x04) + 0x04)        # costume0.LowPoly table ptr
    if table is None:
        return []
    cnt = d.u32(table)
    arr = rptr(table + 0x04)
    idx = set()
    for i in range(cnt):
        le = arr + i * 8
        n = d.u32(le)
        data = rptr(le + 0x04)
        if data is not None and n <= 256:
            idx.update(d.raw[0x20 + data:0x20 + data + n])
    return sorted(idx)


def add_lowpoly_to_smd(smd_path, low_idx, out_smd, log=print):
    """Fill the first empty low DObj of an exported costume SMD with a decimated
    copy of its high-poly geometry (weights from the nearest high vertex)."""
    m = S.load(smd_path)
    mesh_nodes = [b for b in m.bones if b.parent == -1 and "_Object_" in b.name]
    idx_by_node = {b.id: i for i, b in enumerate(mesh_nodes)}
    low_set = set(low_idx)
    if low_idx[0] >= len(mesh_nodes):
        log(f"  low index {low_idx[0]} >= {len(mesh_nodes)} mesh nodes; skip")
        return False
    low_node_id = mesh_nodes[low_idx[0]].id

    high = [t for t in m.triangles
            if idx_by_node.get(t.verts[0].parent) not in low_set
            and idx_by_node.get(t.verts[0].parent) is not None]
    if len(high) < 24:
        log(f"  only {len(high)} high tris; skip")
        return False

    tri_pos = np.array([[v.pos for v in t.verts] for t in high], float)
    tri_norm = np.array([[v.normal for v in t.verts] for t in high], float)
    tri_uv = np.array([[v.uv for v in t.verts] for t in high], float)
    tri_mat = [t.material for t in high]
    corner_w = [v.weights for t in high for v in t.verts]

    target = max(120, min(700, len(high) // 12))
    fm = ForeignMesh(tri_pos, tri_norm, tri_uv, tri_mat, {}, ["hi"] * len(high))
    lf = decimate(fm, target) if len(high) > target else fm
    recompute_normals(lf)

    _, nn = cKDTree(tri_pos.reshape(-1, 3)).query(
        lf.tri_pos.reshape(-1, 3), workers=-1)

    new = []
    for t in range(len(lf.tri_pos)):
        verts = []
        for c in range(3):
            verts.append(S.Vertex(
                pos=tuple(lf.tri_pos[t][c]), normal=tuple(lf.tri_norm[t][c]),
                uv=tuple(lf.tri_uv[t][c]), weights=corner_w[nn[t * 3 + c]],
                parent=low_node_id))
        new.append(S.Triangle(material=lf.tri_mat[t], verts=tuple(verts)))
    m.triangles.extend(new)
    S.save(m, out_smd)

    sidecar = Path(str(smd_path) + ".textures.json")
    if sidecar.exists():
        Path(str(out_smd) + ".textures.json").write_text(sidecar.read_text())
    log(f"  low-poly: {len(new)} tris (from {len(high)}) -> DObj {low_idx[0]}")
    return True


def add_lowpoly(costume_dat, ft_dat, out_dat, strip_matanim=False, log=print):
    costume_dat, ft_dat, out_dat = map(Path, (costume_dat, ft_dat, out_dat))
    work = out_dat.parent
    work.mkdir(parents=True, exist_ok=True)
    jsym = joint_symbol(costume_dat)
    low_idx = low_indices(ft_dat)
    log(f"{costume_dat.name}: joint {jsym}, low slots {low_idx}")
    if not low_idx:
        log("  no low slots in the table; nothing to do")
        return False

    base_smd = work / (costume_dat.stem + "_exp.smd")
    r = subprocess.run([str(EXE), "--model", "export", str(costume_dat), jsym,
                        str(base_smd)], capture_output=True, text=True, timeout=300)
    if not base_smd.exists():
        log(f"  export failed:\n{r.stdout[-400:]}\n{r.stderr[-400:]}")
        return False

    low_smd = work / (costume_dat.stem + "_lp.smd")
    if not add_lowpoly_to_smd(base_smd, low_idx, low_smd, log=log):
        return False

    cmd = [str(EXE), "--model", "import", str(costume_dat), jsym,
           str(low_smd), str(out_dat)]
    if strip_matanim:
        cmd.append("--strip-matanim")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if not out_dat.exists():
        log(f"  import failed:\n{r.stdout[-600:]}\n{r.stderr[-500:]}")
        return False
    log(f"  imported {out_dat.name} ({out_dat.stat().st_size} bytes)")
    return True


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ok = add_lowpoly(args[0], args[1], args[2],
                     strip_matanim="--strip-matanim" in sys.argv)
    sys.exit(0 if ok else 1)
