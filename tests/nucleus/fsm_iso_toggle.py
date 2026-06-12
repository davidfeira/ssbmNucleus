"""fsm_iso_toggle.py -- enable/disable the FSM patch inside a built ISO, in
place, for A/B crash isolation. Uses the project's sidecar backup for the
original bytes.

Usage:
  python fsm_iso_toggle.py <iso> off   # restore vanilla hook+region
  python fsm_iso_toggle.py <iso> on    # re-apply from the project main.dol
"""

import struct
import sys
from pathlib import Path

HERE = Path(__file__).parent
BACKEND = HERE.parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

import fsm_patcher as fsm  # noqa: E402

PROJECT_DOL = HERE.parent.parent / "projects" / "harness-test" / "sys" / "main.dol"
SIDECAR = Path(str(PROJECT_DOL) + fsm.SIDECAR_SUFFIX)


def main():
    iso_path, mode = sys.argv[1], sys.argv[2]
    with open(iso_path, "r+b") as f:
        f.seek(0x420)
        dol = struct.unpack(">I", f.read(4))[0]
        print(f"dol @ 0x{dol:X} in {iso_path}")

        if mode == "off":
            data = SIDECAR.read_bytes()
            hook, region = data[:4], data[4:]
            f.seek(dol + fsm.ENGINE_FILE_OFFSET)
            f.write(region)
            f.seek(dol + fsm.HOOK_FILE_OFFSET)
            f.write(hook)
            print("FSM patch REMOVED from ISO (vanilla bytes restored)")
        elif mode == "on":
            with open(PROJECT_DOL, "rb") as src:
                src.seek(fsm.ENGINE_FILE_OFFSET)
                region = src.read(fsm.ENGINE_REGION_SIZE + fsm.TABLE_REGION_SIZE)
                src.seek(fsm.HOOK_FILE_OFFSET)
                hook = src.read(4)
            f.seek(dol + fsm.ENGINE_FILE_OFFSET)
            f.write(region)
            f.seek(dol + fsm.HOOK_FILE_OFFSET)
            f.write(hook)
            print("FSM patch RE-APPLIED to ISO from project main.dol")
        else:
            raise SystemExit("mode must be on|off")

        f.seek(dol + fsm.HOOK_FILE_OFFSET)
        print("hook now:", f.read(4).hex().upper())


if __name__ == "__main__":
    main()
