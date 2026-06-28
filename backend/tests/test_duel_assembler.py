import json
import sys
import zipfile
from pathlib import Path


BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import duel_assembler as duel  # noqa: E402


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _full_manifest_and_metadata(tmp_path):
    manifest = {
        "agent": "codex",
        "theme": "test theme",
        "local_image_generation": {
            "required": True,
            "provider": "local",
            "models": ["test-local-model"],
        },
        "characters": {},
        "ice_climbers_pairs": [],
        "stages": {},
    }
    metadata = {"characters": {}, "stages": {}}

    for slot in duel.required_character_slots():
        skin_id = f"{slot.character}-{slot.costume_code}".replace(" ", "_")
        filename = f"{slot.costume_code}.zip"
        metadata["characters"].setdefault(slot.character, {"skins": []})["skins"].append(
            {"id": skin_id, "filename": filename}
        )
        manifest["characters"].setdefault(slot.character, []).append(
            {
                "slot": slot.slot,
                "costumeCode": slot.costume_code,
                "skinName": skin_id,
                "vaultSkinId": skin_id,
                "plan": f"plans/characters/{slot.character}/{slot.costume_code}.json",
                "preview": f"previews/characters/{slot.character}/{slot.costume_code}_review.jpg",
            }
        )

    nana_suffixes = duel.VANILLA_CSS_COLOR_ORDER["Nana"]
    popo_suffixes = duel.VANILLA_CSS_COLOR_ORDER["Ice Climbers"]
    metadata["characters"]["Nana"] = {"skins": []}
    for idx, (popo_suffix, nana_suffix) in enumerate(zip(popo_suffixes, nana_suffixes)):
        popo_code = f"Pl{duel.CHAR_PREFIXES['Ice Climbers']}{popo_suffix}"
        nana_code = f"Pl{duel.NANA_PREFIX}{nana_suffix}"
        nana_id = f"Nana-{nana_code}"
        metadata["characters"]["Nana"]["skins"].append({"id": nana_id, "filename": f"{nana_code}.zip"})
        manifest["ice_climbers_pairs"].append(
            {
                "slot": idx,
                "popoCode": popo_code,
                "nanaCode": nana_code,
                "popoVaultSkinId": manifest["characters"]["Ice Climbers"][idx]["vaultSkinId"],
                "nanaVaultSkinId": nana_id,
            }
        )

    for code, stage_info in duel.LEGAL_STAGES.items():
        variant_id = f"{code}-variant"
        metadata["stages"].setdefault(stage_info["folder"], {"variants": []})["variants"].append(
            {"id": variant_id, "filename": f"{variant_id}.zip"}
        )
        manifest["stages"][code] = {
            "stage": stage_info["stage"],
            "skinName": f"{stage_info['stage']} Skin",
            "mode": "das",
            "button": "X",
            "vaultVariantId": variant_id,
            "plan": f"plans/stages/{code}.json",
            "preview": f"previews/stages/{code}_capture.png",
        }

    storage = tmp_path / "storage"
    _write_json(storage / "metadata.json", metadata)
    manifest_path = tmp_path / "duel" / "codex" / "manifest.json"
    _write_json(manifest_path, manifest)
    return manifest_path, manifest, storage


def test_required_slots_match_duel_scope():
    slots = duel.required_character_slots()

    assert len(slots) == 119
    assert {slot.character for slot in slots}.isdisjoint({"Mr. Game & Watch", "Nana"})
    assert sum(1 for slot in slots if slot.character == "Ice Climbers") == 4
    assert len(slots) + len(duel.VANILLA_CSS_COLOR_ORDER["Nana"]) == 123


def test_validate_manifest_builds_canonical_import_and_remove_manifests(tmp_path):
    manifest_path, manifest, storage = _full_manifest_and_metadata(tmp_path)

    result = duel.validate_manifest(manifest, manifest_path, check_files=False, storage_path=storage)

    assert result.ok
    assert result.visible_slots == 119
    assert result.generated_costume_dats == 123
    assert Path(result.imports["Fox"][0]).name == "PlFxNr.zip"
    assert Path(result.imports["Fox"][1]).name == "PlFxOr.zip"
    assert Path(result.imports["Fox"][2]).name == "PlFxLa.zip"
    assert Path(result.imports["Fox"][3]).name == "PlFxGr.zip"
    assert Path(result.imports["Nana"][0]).name == "PlNnNr.zip"
    assert result.removals["Fox"] == [3, 2, 1, 0]
    assert result.removals["Nana"] == [3, 2, 1, 0]
    assert "Mr. Game & Watch" not in result.removals
    assert all(job.mode == "das" and job.button == "X" for job in result.stage_jobs)

    payload = duel.harness_payload(result)
    assert len(payload["importItems"]) == 123
    assert payload["importItems"][0]["fighter"] == "Bowser"
    assert Path(payload["importItems"][0]["costumePath"]).name == "PlKpNr.zip"
    assert payload["removeItems"][0] == {"fighter": "Bowser", "costumeIndex": 3}
    assert Path(payload["stageItems"][0]["variantPath"]).name == "GrNBa-variant.zip"


def test_validate_manifest_reports_missing_required_slot(tmp_path):
    manifest_path, manifest, storage = _full_manifest_and_metadata(tmp_path)
    manifest["characters"]["Fox"] = [
        entry for entry in manifest["characters"]["Fox"] if entry["slot"] != 2
    ]

    result = duel.validate_manifest(manifest, manifest_path, check_files=False, storage_path=storage)

    assert not result.ok
    assert any("Fox: expected 4 slots, found 3" in error for error in result.errors)
    assert any("Fox: missing slot 2 (PlFxLa)" in error for error in result.errors)


def test_install_stage_job_places_default_and_das_files(tmp_path):
    project_path = tmp_path / "project" / "project.mexproj"
    (project_path.parent / "files").mkdir(parents=True)
    project_path.write_text("fake", encoding="utf-8")
    variant_zip = tmp_path / "variant.zip"
    with zipfile.ZipFile(variant_zip, "w") as zf:
        zf.writestr("stage.dat", b"stage data")

    default_target = duel.install_stage_job(
        project_path,
        duel.StageJob("GrPs", "default-replacement", variant_zip, "Pokemon Skin"),
    )
    das_target = duel.install_stage_job(
        project_path,
        duel.StageJob("GrNBa", "das", variant_zip, "Cosmic Rift", "X"),
    )

    assert (project_path.parent / "files" / "GrPs.usd").read_bytes() == b"stage data"
    assert (project_path.parent / "files" / "GrNBa" / "CosmicRift(X).dat").read_bytes() == b"stage data"
    assert default_target.endswith("GrPs.usd")
    assert das_target.endswith("CosmicRift(X).dat")
