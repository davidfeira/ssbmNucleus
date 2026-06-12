"""Character mapping campaign for the model lab: export every character's rig
kit and audit it — joint/DObj counts, body surface stats, stable-bone sets —
so the rigger's rules can be validated per character (the model-lab analog of
the AI studio's region-mapping campaign)."""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from modellab import smd  # noqa: E402
from modellab.rig import joint_world_positions, sane_surface  # noqa: E402

import numpy as np  # noqa: E402

EXE = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\utility\tools\HSDLib\HSDRawViewer\bin\Release\net6.0-windows\HSDRawViewer.exe")
FILES = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\storage\test-base\files")
OUT = Path(r"C:\Users\david\projects\ssbmNucleus-master\modellab\rigkits")

CODES = {
    'PlCa': 'Captain Falcon', 'PlCl': 'Young Link', 'PlDk': 'Donkey Kong',
    'PlDr': 'Dr. Mario', 'PlFc': 'Falco', 'PlFe': 'Roy', 'PlFx': 'Fox',
    'PlGn': 'Ganondorf', 'PlGw': 'Mr. Game & Watch', 'PlKb': 'Kirby',
    'PlKp': 'Bowser', 'PlLg': 'Luigi', 'PlLk': 'Link', 'PlMr': 'Mario',
    'PlMs': 'Marth', 'PlMt': 'Mewtwo', 'PlNn': 'Nana', 'PlNs': 'Ness',
    'PlPc': 'Pichu', 'PlPe': 'Peach', 'PlPk': 'Pikachu', 'PlPp': 'Popo (ICs)',
    'PlPr': 'Jigglypuff', 'PlSk': 'Sheik', 'PlSs': 'Samus', 'PlYs': 'Yoshi',
    'PlZd': 'Zelda',
}


def joint_symbol(dat_path):
    raw = Path(dat_path).read_bytes()
    for m in re.findall(rb'[\x20-\x7e]{8,}', raw):
        s = m.decode('ascii', 'replace')
        if s.endswith('_joint') and 'matanim' not in s:
            return s
    return None


results = []
for code, name in sorted(CODES.items()):
    dat = FILES / f"{code}Nr.dat"
    if not dat.exists():
        results.append({"code": code, "name": name, "status": "no PlXxNr.dat"})
        continue

    slug = name.replace(' ', '_').replace('.', '').replace('(', '').replace(')', '').lower()
    kit_dir = OUT / slug
    kit_dir.mkdir(parents=True, exist_ok=True)
    kit = kit_dir / f"{slug}_vanilla.smd"

    sym = joint_symbol(dat)
    if not sym:
        results.append({"code": code, "name": name, "status": "no joint symbol"})
        continue

    if not kit.exists():
        r = subprocess.run([str(EXE), '--model', 'export', str(dat), sym, str(kit)],
                           capture_output=True, text=True, timeout=600)
        if 'SUCCESS' not in (r.stdout or ''):
            results.append({"code": code, "name": name,
                            "status": f"export failed: {(r.stdout or '')[-120:]}"})
            continue

    try:
        m = smd.load(kit)
        joints = [b for b in m.bones if b.name.startswith('JOBJ_')]
        mesh_nodes = [b for b in m.bones if not b.name.startswith('JOBJ_')]
        surf = sane_surface(m)
        pts_all = np.array([v.pos for t in m.triangles for v in t.verts])
        pts_surf = np.array([v.pos for t in surf for v in t.verts])

        mass = {}
        for t in surf:
            for v in t.verts:
                for bone, w in v.weights:
                    mass[bone] = mass.get(bone, 0.0) + w
        total = sum(mass.values()) or 1.0
        stable = sorted(b for b, mw in mass.items() if mw / total >= 0.02)

        results.append({
            "code": code, "name": name, "status": "ok",
            "symbol": sym,
            "joints": len(joints), "dobjs": len(mesh_nodes),
            "tris": len(m.triangles), "surface_tris": len(surf),
            "height_all": round(float(pts_all[:, 1].max() - pts_all[:, 1].min()), 1),
            "height_body": round(float(pts_surf[:, 1].max() - pts_surf[:, 1].min()), 1),
            "bones_used": len(mass), "stable_bones": stable,
        })
        print(f"{name:>18}: {len(joints)} joints, {len(mesh_nodes)} dobjs, "
              f"{len(m.triangles)} tris (surface {len(surf)}), "
              f"body h {results[-1]['height_body']}, "
              f"{len(stable)} stable bones")
    except Exception as e:
        results.append({"code": code, "name": name, "status": f"audit failed: {e}"})
        print(f"{name:>18}: AUDIT FAILED {e}")

out_json = Path(r"C:\Users\david\projects\ssbmNucleus-master\modellab\character_map.json")
out_json.write_text(json.dumps(results, indent=2))
ok = sum(1 for r in results if r.get("status") == "ok")
print(f"\n{ok}/{len(results)} characters mapped -> {out_json}")
