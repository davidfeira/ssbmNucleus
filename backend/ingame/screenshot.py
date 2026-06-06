"""
screenshot.py -- capture the Dolphin window as a PNG, using only stdlib ctypes
(to find the window rectangle for a pid) + Pillow's ImageGrab (already bundled).

This replaces the old harness path, which shelled out to `node control.js shot`
-> a PowerShell window-capture helper. The packaged backend can't depend on Node
or PowerShell, so we locate the target process's top-level window via user32 and
grab just its rectangle with PIL. Falls back to a full-screen grab if the window
can't be found, and returns the PNG as raw bytes (the caller base64-encodes it
into the SocketIO result, so no file/route plumbing is needed).
"""

import ctypes
import ctypes.wintypes as wt
import io

try:
    from PIL import ImageGrab  # bundled with the backend (Pillow)
except Exception:  # pragma: no cover - PIL is expected to be present
    ImageGrab = None

_u32 = ctypes.WinDLL("user32", use_last_error=True)

_EnumWindowsProc = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


def _window_rect_for_pid(pid):
    """Return (left, top, right, bottom) of the largest visible top-level window
    owned by `pid`, or None. Dolphin's render window is the big one; the small
    helper/config windows lose the area comparison."""
    best = {"area": 0, "rect": None}

    def _cb(hwnd, _lparam):
        if not _u32.IsWindowVisible(hwnd):
            return True
        wpid = wt.DWORD(0)
        _u32.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
        if wpid.value != pid:
            return True
        r = wt.RECT()
        if not _u32.GetWindowRect(hwnd, ctypes.byref(r)):
            return True
        w = r.right - r.left
        h = r.bottom - r.top
        if w <= 0 or h <= 0:
            return True
        area = w * h
        if area > best["area"]:
            best["area"] = area
            best["rect"] = (r.left, r.top, r.right, r.bottom)
        return True

    _u32.EnumWindows(_EnumWindowsProc(_cb), 0)
    return best["rect"]


def _foreground(pid):
    """Best-effort: bring the Dolphin window forward so the grab isn't of
    whatever is occluding it. Harmless if it fails."""
    try:
        rect = None

        def _cb(hwnd, _lparam):
            nonlocal rect
            wpid = wt.DWORD(0)
            _u32.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
            if wpid.value == pid and _u32.IsWindowVisible(hwnd):
                _u32.SetForegroundWindow(hwnd)
                rect = True
                return False
            return True

        _u32.EnumWindows(_EnumWindowsProc(_cb), 0)
    except Exception:
        pass


def capture_png(pid=None, max_width=640):
    """Capture the Dolphin window (by pid) and return PNG bytes, downscaled to
    max_width so it travels cheaply over the websocket. Returns None if capture
    isn't possible (no PIL / headless)."""
    if ImageGrab is None:
        return None
    bbox = _window_rect_for_pid(pid) if pid else None
    if bbox:
        _foreground(pid)
    try:
        img = ImageGrab.grab(bbox=bbox) if bbox else ImageGrab.grab()
    except Exception:
        try:
            img = ImageGrab.grab()
        except Exception:
            return None
    if img.width > max_width:
        h = int(img.height * (max_width / img.width))
        img = img.resize((max_width, max(1, h)))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()
