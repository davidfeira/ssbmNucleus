"""
embed.py -- show the throwaway test Dolphin's render window INSIDE the app UI.

Not a true embed (cross-process SetParent is an input-queue minefield): the
frontend renders a placeholder and posts its physical-pixel screen rect here;
we find the active test Dolphin's render window, strip its title bar / sizing
frame, and SetWindowPos it over the placeholder -- always-on-top, never
activated -- so the game appears to play inside the app. Same trick the
HSDRawViewer model viewer uses (EmbeddedServer.cs), done from the OUTSIDE since
we don't build Dolphin: with `-b` (batch) the render window is Dolphin's only
window, so nothing is left floating.

boot.py registers the active DolphinBoot pid here; window discovery reuses
screenshot.py's render-window heuristics and is re-run on every call because
the render window only exists once the game starts booting (and Dolphin
recreates it if its video backend restarts).
"""

import os
import threading

_lock = threading.Lock()
_active_pid = None

if os.name == "nt":
    import ctypes
    from ctypes import wintypes as wt

    _u32 = ctypes.WinDLL("user32", use_last_error=True)
    _u32.GetWindowLongW.argtypes = [wt.HWND, ctypes.c_int]
    _u32.GetWindowLongW.restype = ctypes.c_long
    _u32.SetWindowLongW.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_long]
    _u32.SetWindowLongW.restype = ctypes.c_long
    _u32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int,
                                  ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    _u32.SetWindowPos.restype = wt.BOOL

GWL_STYLE = -16
WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000
WS_SYSMENU = 0x00080000
_CHROME = WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU

HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
SWP_SHOWWINDOW = 0x0040
SWP_NOMOVE = 0x0002


def set_active(pid):
    """Called by DolphinBoot.launch(): this pid's render window is the one the
    frontend may embed."""
    global _active_pid
    with _lock:
        _active_pid = pid


def clear_active(pid=None):
    """Forget the active pid (on terminate/cleanup). With a pid, only clears if
    it still matches -- a stale cleanup must not unregister a newer boot."""
    global _active_pid
    with _lock:
        if pid is None or _active_pid == pid:
            _active_pid = None


def get_active():
    with _lock:
        return _active_pid


def _render_hwnd(pid):
    from . import screenshot as _ss
    _ss._ensure_dpi_aware()
    cands = _ss._render_candidates(pid)
    return cands[0] if cands else None


def _strip_chrome(hwnd):
    style = _u32.GetWindowLongW(hwnd, GWL_STYLE)
    bare = style & ~_CHROME
    if bare != style:
        _u32.SetWindowLongW(hwnd, GWL_STYLE, bare)
        _u32.SetWindowPos(hwnd, None, 0, 0, 0, 0,
                          SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE
                          | SWP_NOZORDER | SWP_NOACTIVATE)


def position(x, y, width, height):
    """Pin the active test Dolphin's render window to the given PHYSICAL-pixel
    screen rect, borderless, above the app, without activating it. Returns
    {"found": bool} -- False until the render window exists (the frontend keeps
    polling while the build/boot is still in progress)."""
    if os.name != "nt":
        return {"found": False}
    pid = get_active()
    if not pid:
        return {"found": False}
    hwnd = _render_hwnd(pid)
    if not hwnd:
        return {"found": False}
    _strip_chrome(hwnd)
    _u32.SetWindowPos(hwnd, HWND_TOPMOST, int(x), int(y), int(width), int(height),
                      SWP_NOACTIVATE | SWP_SHOWWINDOW)
    return {"found": True}


def park(pid=None):
    """Move a test Dolphin's render window offscreen (placeholder hidden /
    panel unmounted / about to be terminated -- a dying GL window flashes
    black wherever it sits, so boot.py parks before killing). Stays
    visible-but-offscreen so PrintWindow screenshots keep working. Defaults
    to the active pid."""
    if os.name != "nt":
        return {"found": False}
    if pid is None:
        pid = get_active()
    if not pid:
        return {"found": False}
    hwnd = _render_hwnd(pid)
    if not hwnd:
        return {"found": False}
    _u32.SetWindowPos(hwnd, HWND_NOTOPMOST, -32000, -32000, 0, 0,
                      SWP_NOSIZE | SWP_NOACTIVATE)
    return {"found": True}
