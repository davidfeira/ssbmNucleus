"""verify_fsm_ram.py -- check the FSM engine patch in live Dolphin RAM.

Attaches to the running Slippi Dolphin (session.json pid) and dumps the three
FSM regions baked into main.dol by backend/fsm_patcher.py:
  hook   @ 0x80073338  expect 48398578 (b -> engine)   [vanilla: BB610014]
  engine @ 0x8040B8B0  expect 7F63DB78... (Magus420 FSM engine)
  table  @ 0x8040B9B0  8-byte entries, byte 0 = external char id
"""

import struct
import sys

from melee_mem import Dolphin

HOOK = 0x80073338
ENGINE = 0x8040B8B0
TABLE = 0x8040B9B0


def main():
    d = Dolphin()
    hook = d.bytes(HOOK, 4)
    engine = d.bytes(ENGINE, 8)
    print(f"hook   @ {HOOK:08X}: {hook.hex().upper()}  "
          f"({'PATCHED' if hook == bytes.fromhex('48398578') else 'vanilla' if hook == bytes.fromhex('BB610014') else 'UNKNOWN'})")
    print(f"engine @ {ENGINE:08X}: {engine.hex().upper()}  "
          f"({'present' if engine.startswith(bytes.fromhex('7F63DB78')) else 'MISSING'})")

    print(f"table  @ {TABLE:08X}:")
    n = 0
    for i in range(150):
        e = d.bytes(TABLE + i * 8, 8)
        if e[:4] == b"\x00\x00\x00\x00":
            break
        mult = struct.unpack(">f", e[4:8])[0]
        print(f"  [{i:3d}] char=0x{e[0]:02X} frame={e[1]:3d} "
              f"flags=0x{e[2]:02X} subaction={e[3]:3d} x{mult:g}")
        n += 1
    print(f"{n} entries")
    return 0 if n > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
