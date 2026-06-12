"""Studiomdl Data (SMD) parser/writer for the model lab rigging pipeline.

SMD is the handoff format between the Python rigger and HSDRawViewer's
headless model import (``--model import``, via IONET's SMDImporter). The
dialect here matches what HSDRawViewer's ``--model export`` emits:

    version 1
    nodes
    <id> "<name>" <parent_id>
    end
    skeleton
    time 0
    <id> <tx> <ty> <tz> <rx> <ry> <rz>
    end
    triangles
    <material_name>
    <parent_bone> <x> <y> <z> <nx> <ny> <nz> <u> <v> <nlinks> [<bone> <weight>]...
    ...x3 vertices
    end

Vertex weight links are the SMD "extended" triangle format; when nlinks is
absent the vertex is rigidly bound to <parent_bone>.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Bone:
    id: int
    name: str
    parent: int  # -1 for root
    # bind pose, local space (translation xyz, rotation xyz in radians)
    pos: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rot: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass
class Vertex:
    pos: tuple[float, float, float]
    normal: tuple[float, float, float]
    uv: tuple[float, float]
    # [(bone_id, weight), ...] — normalized, at least one entry
    weights: list[tuple[int, float]] = field(default_factory=list)
    # SMD vertex parent field. In HSDRawViewer exports this is NOT a weight
    # bone: it is the id of a mesh placeholder node ("Joint_X_Object_Y",
    # parent -1) that IONET uses to group triangles back into per-DObj
    # meshes. Must be preserved or the importer mis-binds the geometry.
    parent: int | None = None


@dataclass
class Triangle:
    material: str
    verts: tuple[Vertex, Vertex, Vertex]


@dataclass
class SMD:
    bones: list[Bone] = field(default_factory=list)
    triangles: list[Triangle] = field(default_factory=list)

    @property
    def materials(self) -> list[str]:
        seen: dict[str, None] = {}
        for t in self.triangles:
            seen.setdefault(t.material)
        return list(seen)


def _parse_vertex(line: str) -> Vertex:
    parts = line.split()
    parent = int(parts[0])
    x, y, z, nx, ny, nz, u, v = (float(p) for p in parts[1:9])
    weights: list[tuple[int, float]] = []
    if len(parts) > 9:
        nlinks = int(parts[9])
        for i in range(nlinks):
            bone = int(parts[10 + i * 2])
            w = float(parts[11 + i * 2])
            weights.append((bone, w))
    if not weights:
        weights = [(parent, 1.0)]
    return Vertex(pos=(x, y, z), normal=(nx, ny, nz), uv=(u, v),
                  weights=weights, parent=parent)


def load(path: str | Path) -> SMD:
    smd = SMD()
    section = None
    material = None
    tri_verts: list[Vertex] = []

    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            if line.startswith("version"):
                continue
            if line in ("nodes", "skeleton", "triangles"):
                section = line
                continue
            if line == "end":
                section = None
                material = None
                tri_verts = []
                continue

            if section == "nodes":
                # <id> "<name>" <parent>
                first_quote = line.index('"')
                last_quote = line.rindex('"')
                bone_id = int(line[:first_quote].strip())
                name = line[first_quote + 1:last_quote]
                parent = int(line[last_quote + 1:].strip())
                smd.bones.append(Bone(id=bone_id, name=name, parent=parent))
            elif section == "skeleton":
                if line.startswith("time"):
                    continue
                parts = line.split()
                bone_id = int(parts[0])
                vals = [float(p) for p in parts[1:7]]
                # bones list is indexed by id in HSDRawViewer exports, but be safe
                bone = next(b for b in smd.bones if b.id == bone_id)
                bone.pos = tuple(vals[0:3])
                bone.rot = tuple(vals[3:6])
            elif section == "triangles":
                # alternating: material-name line, then 3 vertex lines
                if material is None:
                    material = line
                    tri_verts = []
                else:
                    tri_verts.append(_parse_vertex(line))
                    if len(tri_verts) == 3:
                        smd.triangles.append(
                            Triangle(material=material, verts=tuple(tri_verts))
                        )
                        material = None
                        tri_verts = []

    return smd


def _fmt(x: float) -> str:
    # enough precision for float32 round-trip without bloating the file
    return f"{x:.6g}"


def save(smd: SMD, path: str | Path) -> None:
    lines: list[str] = ["version 1", "nodes"]
    for b in smd.bones:
        lines.append(f'{b.id} "{b.name}" {b.parent}')
    lines.append("end")

    lines.append("skeleton")
    lines.append("time 0")
    for b in smd.bones:
        p, r = b.pos, b.rot
        lines.append(
            f"{b.id} {_fmt(p[0])} {_fmt(p[1])} {_fmt(p[2])} "
            f"{_fmt(r[0])} {_fmt(r[1])} {_fmt(r[2])}"
        )
    lines.append("end")

    lines.append("triangles")
    for t in smd.triangles:
        lines.append(t.material)
        for v in t.verts:
            parent = v.parent if v.parent is not None else v.weights[0][0]
            links = " ".join(f"{b} {_fmt(w)}" for b, w in v.weights)
            lines.append(
                f"{parent} {_fmt(v.pos[0])} {_fmt(v.pos[1])} {_fmt(v.pos[2])} "
                f"{_fmt(v.normal[0])} {_fmt(v.normal[1])} {_fmt(v.normal[2])} "
                f"{_fmt(v.uv[0])} {_fmt(v.uv[1])} "
                f"{len(v.weights)} {links}"
            )
    lines.append("end")

    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
