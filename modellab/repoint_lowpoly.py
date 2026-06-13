"""Repoint a character's empty LowPoly DObj slots at its HIGH-poly model so the
off-screen magnifier + projected shadow render (the m-ex 'no low-poly version
-> use the high-poly mesh index in the low-poly table' fix).

In-place, SAME-LENGTH byte overwrite of the ftData costume visibility table:
each LowPoly lookup entry's index bytes are replaced with the highest-geometry
HighPoly DObj indices (most triangles = best silhouette coverage). No
reallocation, no relocation/offset changes, the model is byte-untouched, and it
is trivially reversible (restore the ftData). Operates on a COPY -> out path.

usage: repoint_lowpoly.py <ftData.dat> <costume.smd> <out.dat>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from skinlab.datprobe import DatFile  # noqa: E402
from modellab import smd as S  # noqa: E402

HEADER = 0x20


def dobj_tri_counts(smd_path):
    """Per-DObj-index triangle count from an exported costume SMD (mesh-node
    order == DObj index)."""
    m = S.load(smd_path)
    nodes = [b.id for b in m.bones if b.parent == -1 and "_Object_" in b.name]
    idx = {b: i for i, b in enumerate(nodes)}
    from collections import Counter
    tr = Counter()
    for t in m.triangles:
        p = t.verts[0].parent
        if p in idx:
            tr[idx[p]] += 1
    return tr, len(nodes)


def repoint(ft_path, smd_path, out_path, log=print):
    ft_path, smd_path, out_path = map(Path, (ft_path, smd_path, out_path))
    raw = bytearray(ft_path.read_bytes())
    d = DatFile(ft_path)                       # read-only structural probe

    def u32(off):
        return int.from_bytes(raw[HEADER + off:HEADER + off + 4], "big")

    def rptr(off):
        v = u32(off)
        return v if (v != 0 or off in d.relocs) else None

    def read_table(base, off):
        """list[list[int]] of DObj-index groups for a HighPoly/LowPoly table,
        plus the (file_offset, length) of each entry's byte array."""
        tbl = rptr(base + off)
        if tbl is None:
            return None, []
        cnt = u32(tbl + 0x00)
        arr = rptr(tbl + 0x04)
        if arr is None or cnt > 64:
            return None, []
        groups, spans = [], []
        for i in range(cnt):
            le = arr + i * 0x08
            n = u32(le + 0x00)
            data = rptr(le + 0x04)
            if data is not None and n <= 256:
                fo = HEADER + data
                groups.append(list(raw[fo:fo + n]))
                spans.append((fo, n))
            else:
                groups.append([])
                spans.append((None, 0))
        return groups, spans

    tri, n_dobj = dobj_tri_counts(smd_path)
    ft = next(o for n, o in d.roots if n.startswith("ftData"))
    lookups = d.ptr(ft + 0x08)
    vis_len = u32(lookups + 0x00)
    vis_arr = rptr(lookups + 0x04)

    edited = 0
    for c in range(vis_len):
        entry = vis_arr + c * 0x10
        high_groups, _ = read_table(entry, 0x00)
        low_groups, low_spans = read_table(entry, 0x04)
        if not high_groups or not low_groups:
            continue
        high_idx = sorted({i for g in high_groups for i in g})
        if not high_idx:
            continue
        # rank high DObjs by triangle mass (best shadow/magnifier coverage)
        ranked = sorted(high_idx, key=lambda i: -tri.get(i, 0))
        for (fo, n) in low_spans:
            if fo is None or n == 0:
                continue
            pick = ranked[:n]                  # same length -> in-place
            covered = sum(tri.get(i, 0) for i in pick)
            total = sum(tri.get(i, 0) for i in high_idx)
            raw[fo:fo + n] = bytes(pick)
            edited += 1
            log(f"  costume {c}: low entry ({n} slots) -> high {pick[:6]}"
                f"{'...' if n > 6 else ''}  coverage {covered}/{total} tris "
                f"({covered / max(total, 1):.0%})")

    if not edited:
        log("  no LowPoly entries to repoint")
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(bytes(raw))
    log(f"  repointed {edited} low entr{'y' if edited == 1 else 'ies'} "
        f"-> {out_path.name} ({len(raw)} bytes, same size as input: "
        f"{len(raw) == ft_path.stat().st_size})")
    return True


if __name__ == "__main__":
    ok = repoint(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.exit(0 if ok else 1)
