"""
melee_mem.py -- read the live emulated GameCube RAM of a Slippi Dolphin process.

Locates MEM1 (GC 0x80000000) inside the Dolphin process the same way Dolphin
Memory Engine does -- find the 0x2000000 MEM_MAPPED region that starts with the
"GALE01" game id -- then exposes typed reads of GC addresses. This is the read
half of the memory-feedback harness (input half: melee_pipe.py). No libmelee,
no Slippi stream format; works on whatever Slippi build is running Melee 1.02.

Ported into the backend from tests/nucleus/melee_mem.py. Identical logic, except
it takes the Dolphin pid explicitly (no session.json file dependency) so it can
be driven by the backend that just launched Dolphin itself. Uses only stdlib
ctypes/kernel32 -- nothing to install.
"""

import ctypes
import ctypes.wintypes as wt
import struct

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_MAPPED = 0x40000
MEM1_REGION_SIZE = 0x2000000
MEM1_VALID = 0x1800000  # 24 MiB of real GC RAM
GC_BASE = 0x80000000
GAME_ID = b"GALE01"

_k32 = ctypes.WinDLL("kernel32", use_last_error=True)


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


class Dolphin:
    """Attach to a Slippi Dolphin process and read Melee's emulated RAM."""

    def __init__(self, pid):
        if not pid:
            raise ValueError("Dolphin(pid) requires the Dolphin process id")
        self.pid = int(pid)
        self.h = _k32.OpenProcess(
            PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, self.pid
        )
        if not self.h:
            raise OSError(f"OpenProcess({self.pid}) failed: {ctypes.get_last_error()}")
        self.base = None
        self.locate()

    def locate(self):
        """(Re)find the MEM1 base. Returns False if Melee RAM isn't present."""
        addr = 0
        mbi = MEMORY_BASIC_INFORMATION()
        while addr < 0x7FFFFFFFFFFF:
            if not _k32.VirtualQueryEx(
                self.h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)
            ):
                break
            if mbi.Type == MEM_MAPPED and mbi.RegionSize == MEM1_REGION_SIZE:
                if self._raw(mbi.BaseAddress, len(GAME_ID)) == GAME_ID:
                    self.base = mbi.BaseAddress
                    return True
            nxt = mbi.BaseAddress + mbi.RegionSize
            if nxt <= addr:
                break
            addr = nxt
        self.base = None
        return False

    def alive(self):
        code = wt.DWORD()
        if not _k32.GetExitCodeProcess(self.h, ctypes.byref(code)):
            return False
        return code.value == 259  # STILL_ACTIVE

    # --- typed reads (big-endian, as the GameCube stores them) ---------------
    def _raw(self, host_addr, size):
        buf = ctypes.create_string_buffer(size)
        n = ctypes.c_size_t(0)
        ok = _k32.ReadProcessMemory(
            self.h, ctypes.c_void_p(host_addr), buf, size, ctypes.byref(n)
        )
        return buf.raw[: n.value] if ok else None

    def host(self, gc_addr):
        return self.base + (gc_addr - GC_BASE)

    def bytes(self, gc_addr, size):
        if self.base is None:
            return None
        return self._raw(self.host(gc_addr), size)

    def snapshot(self, size=MEM1_VALID):
        """Read a contiguous block of MEM1 from the start (for diffing)."""
        return self._raw(self.base, size)

    def u8(self, gc_addr):
        b = self.bytes(gc_addr, 1)
        return b[0] if b else None

    def u16(self, gc_addr):
        b = self.bytes(gc_addr, 2)
        return struct.unpack(">H", b)[0] if b else None

    def u32(self, gc_addr):
        b = self.bytes(gc_addr, 4)
        return struct.unpack(">I", b)[0] if b else None

    def s32(self, gc_addr):
        b = self.bytes(gc_addr, 4)
        return struct.unpack(">i", b)[0] if b else None

    def f32(self, gc_addr):
        b = self.bytes(gc_addr, 4)
        return struct.unpack(">f", b)[0] if b else None

    def deref(self, pointer_addr, offset=0):
        """Follow a GC pointer (a u32 holding a 0x8xxxxxxx address) + offset."""
        p = self.u32(pointer_addr)
        if not p or not (GC_BASE <= p < GC_BASE + MEM1_VALID):
            return None
        return p + offset

    def close(self):
        if getattr(self, "h", None):
            try:
                _k32.CloseHandle(self.h)
            except Exception:
                pass
            self.h = None
