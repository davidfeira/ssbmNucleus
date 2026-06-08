"""
screenshot.py -- capture Dolphin's render output as a PNG.

PRIMARY path: PrintWindow(PW_RENDERFULLCONTENT) on Dolphin's render window. This
asks Windows/DWM for the window's own pixels, so it captures the actual emulated
frame even when the window is OCCLUDED, in the BACKGROUND, or not focused -- the
exact failure mode of a plain desktop grab, and the reason the throwaway test
Dolphin (which never takes the foreground) used to screenshot whatever was on top
of it. Pure stdlib ctypes (user32 + gdi32) + Pillow; no Node/PowerShell/ffmpeg.

FALLBACK path: a desktop-region grab of the window's client rect via PIL
ImageGrab (the old behaviour) -- only if PrintWindow comes back empty/black.

Dolphin's own "Take Screenshot" hotkey and "Dump Frames" were both evaluated and
rejected: on this Ishiiruka/Slippi build hotkeys don't fire over the input pipe
(they need real window focus) and frame dumps need a runtime menu toggle + AVI
decoding -- PrintWindow needs neither.
"""

import ctypes
import ctypes.wintypes as wt
import io
import time

try:
    from PIL import ImageGrab, Image  # bundled with the backend (Pillow)
except Exception:  # pragma: no cover - PIL is expected to be present
    ImageGrab = None
    Image = None

_u32 = ctypes.WinDLL("user32", use_last_error=True)
_gdi = ctypes.WinDLL("gdi32", use_last_error=True)

_dpi_aware = False


def _ensure_dpi_aware():
    """Make this process DPI-aware so GetClientRect returns the window's TRUE
    physical pixel size. Without this, on a scaled display (e.g. 150%/200%) the
    DPI-virtualised client rect is smaller than the render, and PrintWindow -- which
    copies 1:1 -- captures only the top-left corner. Best-effort, set once; safe in
    the headless backend (no windows of our own)."""
    global _dpi_aware
    if _dpi_aware:
        return
    _dpi_aware = True
    for attempt in (
        lambda: _u32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)),  # PER_MONITOR_V2
        lambda: ctypes.WinDLL("shcore").SetProcessDpiAwareness(2),        # PER_MONITOR
        lambda: _u32.SetProcessDPIAware(),                                # system-DPI
    ):
        try:
            if attempt():
                return
        except Exception:
            continue

_EnumWindowsProc = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

PW_CLIENTONLY = 0x00000001        # client area only (no title bar / borders)
PW_RENDERFULLCONTENT = 0x00000002  # force a real render of GPU-composited content
# Both together give a clean client-area grab of Dolphin's render window. Either
# alone is wrong here: RENDERFULLCONTENT alone includes the title bar; CLIENTONLY
# alone returns an all-black frame for the GPU surface.
PW_FLAGS = PW_CLIENTONLY | PW_RENDERFULLCONTENT


class _POINT(ctypes.Structure):
    _fields_ = [("x", wt.LONG), ("y", wt.LONG)]


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
                ("biPlanes", wt.WORD), ("biBitCount", wt.WORD),
                ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG),
                ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD)]


def _client_rect_for_pid(pid):
    """Screen-space (left, top, right, bottom) of the CLIENT area (no title bar /
    borders) of the largest visible top-level window owned by `pid`, or None."""
    best = {"area": 0, "hwnd": None}

    def _cb(hwnd, _lparam):
        if not _u32.IsWindowVisible(hwnd):
            return True
        wpid = wt.DWORD(0)
        _u32.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
        if wpid.value != pid:
            return True
        r = wt.RECT()
        if not _u32.GetClientRect(hwnd, ctypes.byref(r)):
            return True
        w, h = r.right - r.left, r.bottom - r.top
        if w <= 0 or h <= 0:
            return True
        if w * h > best["area"]:
            best["area"] = w * h
            best["hwnd"] = hwnd
        return True

    _u32.EnumWindows(_EnumWindowsProc(_cb), 0)
    hwnd = best["hwnd"]
    if not hwnd:
        return None
    r = wt.RECT()
    _u32.GetClientRect(hwnd, ctypes.byref(r))
    tl, br = _POINT(0, 0), _POINT(r.right, r.bottom)
    _u32.ClientToScreen(hwnd, ctypes.byref(tl))
    _u32.ClientToScreen(hwnd, ctypes.byref(br))
    return (tl.x, tl.y, br.x, br.y)


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
    _ensure_dpi_aware()
    # Prefer the client area (no title bar / borders); fall back to the whole window.
    bbox = (_client_rect_for_pid(pid) or _window_rect_for_pid(pid)) if pid else None
    if bbox:
        _foreground(pid)
    try:
        img = ImageGrab.grab(bbox=bbox) if bbox else ImageGrab.grab()
    except Exception:
        try:
            img = ImageGrab.grab()
        except Exception:
            return None
    return _encode_png(img, max_width)


def _encode_png(img, max_width):
    """Downscale to max_width (if wider) and return PNG bytes."""
    if img.width > max_width:
        h = int(img.height * (max_width / img.width))
        img = img.resize((max_width, max(1, h)))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


def _pid_windows(pid):
    """All visible top-level windows owned by `pid` with a non-empty client area,
    as (hwnd, title, width, height)."""
    out = []

    def _cb(hwnd, _lparam):
        if not _u32.IsWindowVisible(hwnd):
            return True
        wpid = wt.DWORD(0)
        _u32.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
        if wpid.value != pid:
            return True
        r = wt.RECT()
        if not _u32.GetClientRect(hwnd, ctypes.byref(r)):
            return True
        w, h = r.right - r.left, r.bottom - r.top
        if w <= 0 or h <= 0:
            return True
        n = _u32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        _u32.GetWindowTextW(hwnd, buf, n + 1)
        out.append((hwnd, buf.value, w, h))
        return True

    _u32.EnumWindows(_EnumWindowsProc(_cb), 0)
    return out


def _render_candidates(pid):
    """Dolphin's RENDER window owned by `pid`, best candidate first. The render
    window is titled exactly 'Dolphin' (the GUI/main window is 'Faster Melee -
    Slippi ...' / 'Dolphin X.Y - ...'); we prefer that, then any non-GUI window,
    largest first, so PrintWindow grabs the game frame and not the menu bar."""
    wins = _pid_windows(pid)
    exact = [w for w in wins if w[1].strip().lower() == "dolphin"]
    if exact:
        exact.sort(key=lambda w: w[2] * w[3], reverse=True)
        return [w[0] for w in exact]

    def _is_gui(title):
        t = title.lower()
        return ("faster melee" in t) or ("slippi" in t) or (" - " in t)

    others = [w for w in wins if not _is_gui(w[1])] or wins
    others.sort(key=lambda w: w[2] * w[3], reverse=True)
    return [w[0] for w in others]


def _printwindow_grab(hwnd):
    """PrintWindow(PW_RENDERFULLCONTENT) the window's client area into a PIL image,
    or None. Returns None for an all-black grab (PrintWindow occasionally yields a
    black frame for a GPU surface -- the caller then tries the next window / the
    desktop fallback)."""
    r = wt.RECT()
    if not _u32.GetClientRect(hwnd, ctypes.byref(r)):
        return None
    w, h = r.right - r.left, r.bottom - r.top
    if w <= 0 or h <= 0:
        return None
    hdc = _u32.GetDC(hwnd)
    mdc = _gdi.CreateCompatibleDC(hdc)
    bmp = _gdi.CreateCompatibleBitmap(hdc, w, h)
    try:
        _gdi.SelectObject(mdc, bmp)
        if not _u32.PrintWindow(hwnd, mdc, PW_FLAGS):
            return None
        bmi = _BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        bmi.biWidth, bmi.biHeight = w, -h   # top-down
        bmi.biPlanes, bmi.biBitCount, bmi.biCompression = 1, 32, 0
        buf = ctypes.create_string_buffer(w * h * 4)
        if not _gdi.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bmi), 0):
            return None
        img = Image.frombuffer("RGB", (w, h), buf.raw, "raw", "BGRX", 0, 1)
        if img.convert("L").getextrema()[1] == 0:   # all black -> reject
            return None
        return img
    finally:
        _gdi.DeleteObject(bmp)
        _gdi.DeleteDC(mdc)
        _u32.ReleaseDC(hwnd, hdc)


def capture_via_printwindow(pid, max_width=960, tries=10):
    """Capture Dolphin's render output via PrintWindow -- the window's OWN pixels,
    so it works while the window is occluded / backgrounded / unfocused. Returns
    PNG bytes (downscaled to max_width), or None if it couldn't get a non-black
    frame (caller falls back to the desktop grab).

    Retries because PrintWindow on an occluded GPU (flip-model) window often
    returns a BLACK frame on the first call(s) until DWM re-composites it -- a
    short retry reliably lands a real frame without needing to steal focus."""
    if Image is None or not pid:
        return None
    _ensure_dpi_aware()
    for _ in range(max(1, tries)):
        for hwnd in _render_candidates(pid):
            try:
                img = _printwindow_grab(hwnd)   # returns None for an all-black grab
            except Exception:
                img = None
            if img is not None:
                return _encode_png(img, max_width)
        time.sleep(0.06)
    return None
