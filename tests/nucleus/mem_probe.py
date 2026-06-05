"""
mem_probe.py -- proof that we can read Melee's live emulated RAM directly from
the Slippi Dolphin process, with no libmelee and no dependence on Slippi's
network/stream format.

Technique (same as Dolphin Memory Engine): Dolphin maps the GameCube's MEM1
(0x80000000, 24 MiB) into its address space as a 0x2000000-byte MEM_MAPPED
region. We scan the process's memory regions for one whose first 6 bytes are the
Melee game id "GALE01"; that region's base maps GC address 0x80000000. From
there any GC address 0x8xxxxxxx reads at base + (addr - 0x80000000).

This is the read half of a memory-feedback harness (the input half is the
controller pipe in ../dolphin/pipe.js). Run while a Slippi Dolphin is playing
Melee:

    python tests/nucleus/mem_probe.py [--pid <dolphin pid>]

With no --pid it reads the pid from the dolphin harness session file.
"""

import ctypes
import ctypes.wintypes as wt
import json
import os
import sys
import time

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_MAPPED = 0x40000
MEM1_REGION_SIZE = 0x2000000  # 32 MiB region Dolphin maps for GC MEM1
GC_BASE = 0x80000000
GAME_ID = b"GALE01"

SESSION_FILE = os.path.join(
    os.path.dirname(__file__), "..", "artifacts", "dolphin", "live", "session.json"
)

k32 = ctypes.WinDLL("kernel32", use_last_error=True)


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_ulonglong),
        ("AllocationBase", ctypes.c_ulonglong),
        ("AllocationProtect", wt.DWORD),
        ("__alignment1", wt.DWORD),
        ("RegionSize", ctypes.c_ulonglong),
        ("State", wt.DWORD),
        ("Protect", wt.DWORD),
        ("Type", wt.DWORD),
        ("__alignment2", wt.DWORD),
    ]


def open_process(pid):
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        raise OSError(f"OpenProcess({pid}) failed: {ctypes.get_last_error()}")
    return h


def read(h, host_addr, size):
    buf = ctypes.create_string_buffer(size)
    n = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(
        h, ctypes.c_void_p(host_addr), buf, size, ctypes.byref(n)
    )
    if not ok:
        return None
    return buf.raw[: n.value]


def find_mem1_bases(h):
    """Return every mapped region whose start is the Melee game id (MEM1 mirrors)."""
    bases = []
    addr = 0
    mbi = MEMORY_BASIC_INFORMATION()
    max_addr = 0x7FFFFFFFFFFF
    while addr < max_addr:
        ok = k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not ok:
            break
        if mbi.Type == MEM_MAPPED and mbi.RegionSize == MEM1_REGION_SIZE:
            head = read(h, mbi.BaseAddress, len(GAME_ID))
            if head == GAME_ID:
                bases.append(mbi.BaseAddress)
        nxt = mbi.BaseAddress + mbi.RegionSize
        if nxt <= addr:
            break
        addr = nxt
    return bases


class Mem:
    """Reads GameCube addresses from a located MEM1 base."""

    def __init__(self, h, mem1_base):
        self.h = h
        self.base = mem1_base

    def host(self, gc_addr):
        return self.base + (gc_addr - GC_BASE)

    def bytes(self, gc_addr, size):
        return read(self.h, self.host(gc_addr), size)

    def u32(self, gc_addr):
        b = self.bytes(gc_addr, 4)
        return int.from_bytes(b, "big") if b else None


def resolve_pid(argv):
    if "--pid" in argv:
        return int(argv[argv.index("--pid") + 1])
    with open(os.path.abspath(SESSION_FILE), "r", encoding="utf-8") as f:
        return int(json.load(f)["pid"])


def main():
    pid = resolve_pid(sys.argv[1:])
    print(f"attaching to Dolphin pid {pid}")
    h = open_process(pid)

    bases = find_mem1_bases(h)
    if not bases:
        print("FAIL: no MEM1 region found (is Melee running? still booting?)")
        return 1
    base = bases[0]
    print(f"found MEM1: {len(bases)} mirror(s); using base 0x{base:012x}")

    mem = Mem(h, base)
    print(f"game id @0x80000000 = {mem.bytes(GC_BASE, 6)!r}")

    # Prove the read is LIVE: snapshot ALL of MEM1 (24 MiB) twice ~0.5s apart and
    # count changed bytes. Also scan for a u32 that incremented by ~30 (0.5s * 60fps)
    # -- a global frame counter -- which both proves "live" and discovers a useful
    # address for the eventual harness.
    import numpy as np

    size = 0x1800000  # 24 MiB of valid GC MEM1
    b1 = mem.bytes(GC_BASE, size)
    time.sleep(0.5)
    b2 = mem.bytes(GC_BASE, size)
    if not b1 or not b2:
        print("FAIL: could not read MEM1 bulk")
        return 1
    n = min(len(b1), len(b2)) & ~3
    u8a = np.frombuffer(b1, np.uint8, n)
    u8b = np.frombuffer(b2, np.uint8, n)
    changed = int(np.count_nonzero(u8a != u8b))
    print(f"live-state check: {changed:,} of {n:,} bytes changed across MEM1 in 0.5s")

    a1 = np.frombuffer(b1, ">u4", n // 4).astype(np.int64)
    a2 = np.frombuffer(b2, ">u4", n // 4).astype(np.int64)
    d = a2 - a1
    cand = np.where((d >= 25) & (d <= 35) & (a1 > 0) & (a1 < 0x100000))[0]
    if len(cand):
        print("frame-counter candidates (u32 that ticked ~30 frames):")
        for idx in cand[:5]:
            print(f"  0x{GC_BASE + idx * 4:08x}: {int(a1[idx])} -> {int(a2[idx])}")

    print()
    if changed > 1000:
        print("PASS: reading live, changing Melee RAM directly from the Slippi process.")
        print("=> a memory-feedback harness is feasible without libmelee or its stream format.")
        return 0
    print("read OK but little change (game idle?); re-run while in a match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
