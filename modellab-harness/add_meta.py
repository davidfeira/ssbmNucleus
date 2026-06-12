import json

p = r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\storage\metadata.json"
with open(p, encoding="utf-8") as f:
    meta = json.load(f)
skins = meta["characters"]["Fox"]["skins"]
if not any(s.get("id") == "roundtrip-test-plfxrt" for s in skins):
    skins.append({
        "id": "roundtrip-test-plfxrt",
        "color": "plfxrt",
        "costume_code": "PlFxRt",
        "filename": "roundtrip-test-plfxrt.zip",
        "has_csp": True,
        "has_stock": True,
        "csp_source": "imported",
        "stock_source": "imported",
        "date_added": "2026-06-12T00:00:00",
        "slippi_safe": True,
        "slippi_tested": False,
        "slippi_manual_override": None,
    })
    with open(p, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print("added")
else:
    print("already present")
