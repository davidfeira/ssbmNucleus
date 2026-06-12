"""Validate the BM-derived visibility tables against vanilla rig-kit DObj
counts: a table is vanilla-faithful only if its max DObj index + 1 equals the
vanilla costume's group count (BM didn't restructure that character's model)."""
import json
from pathlib import Path

ML = Path(r"C:\Users\david\projects\ssbmNucleus-master\modellab")
BK = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")

vis = json.load(open(BK / "modellab" / "visibility_tables.json"))
cmap = json.load(open(ML / "character_map.json"))

by_code = {}
for c in (cmap if isinstance(cmap, list) else cmap.get("characters", [])):
    if isinstance(c, dict) and c.get("code"):
        by_code[c["code"]] = c

print(f"{'code':<6}{'bm_max+1':>9}{'vanilla':>9}  verdict")
for code, v in sorted(vis.items()):
    if "error" in v:
        print(f"{code:<6}{'-':>9}{'-':>9}  BM-ERROR: {v['error'][:48]}")
        continue
    c0 = v["costumes"][0]
    hi = {i for e in (c0["high"] or []) for i in e}
    lo = {i for e in (c0["low"] or []) for i in e}
    mx = max(hi | lo) + 1 if (hi or lo) else 0
    van = by_code.get(code, {})
    n = None
    for key in ("dobjs", "groups", "mesh_nodes", "group_count", "n_groups"):
        if key in van:
            n = van[key]
            break
    if n is None:
        print(f"{code:<6}{mx:>9}{'?':>9}  no vanilla count in map "
              f"(keys: {sorted(van.keys())[:8]})")
        continue
    verdict = "MATCH" if n == mx else f"MISMATCH (vanilla {n})"
    print(f"{code:<6}{mx:>9}{n:>9}  {verdict}")
