"""
boot.py -- launch a freshly-built ISO in an ISOLATED, throwaway Slippi Dolphin,
configured to be driven over the named pipe and read from RAM -- WITHOUT touching
the user's own Slippi setup.

Ported from the boot half of tests/dolphin/driver.js. The key property: we never
launch the user's real User dir. We make a temp copy of their Config/ + Slippi/
login, patch it (pipe controller on port 1, windowed, no confirm-stop), and boot
Dolphin with `-u <temp dir>`. The user's Slippi config is read-only-copied and
otherwise untouched, so their netplay setup keeps working.

No PowerShell, no Node -- just shutil + subprocess.Popen + a tiny INI writer.
"""

import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

from .melee_pipe import pipe_in_use, pipe_open

_k32_creationflags = 0
if os.name == "nt":
    _k32_creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)


# --------------------------------------------------------------------------- #
# Locate the user's Slippi Dolphin exe + template User dir from the path the    #
# frontend already stores (localStorage 'slippi_dolphin_path', verified by      #
# /api/mex/settings/slippi-path/verify to contain User/Config/Dolphin.ini).     #
# --------------------------------------------------------------------------- #
DOLPHIN_EXE_NAMES = ["Slippi Dolphin.exe", "Dolphin.exe", "DolphinWx.exe"]


def _appdata_fallbacks():
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        return []
    return [
        os.path.join(appdata, "Slippi Launcher", "netplay", "Slippi Dolphin.exe"),
        os.path.join(appdata, "Slippi Launcher", "playback", "Slippi Dolphin.exe"),
    ]


def resolve_dolphin(slippi_path):
    """Return (dolphin_exe, template_user_dir) from the configured Slippi path.

    `slippi_path` may be the Slippi install folder (containing the exe + User/)
    or the exe itself. Falls back to the Slippi Launcher install under APPDATA.
    Raises if no Dolphin executable can be found."""
    candidates_exe = []
    template_user = None

    if slippi_path:
        p = Path(slippi_path)
        if p.is_file() and p.suffix.lower() == ".exe":
            candidates_exe.append(str(p))
            template_user = p.parent / "User"
        elif p.is_dir():
            for name in DOLPHIN_EXE_NAMES:
                cand = p / name
                if cand.exists():
                    candidates_exe.append(str(cand))
            if (p / "User").is_dir():
                template_user = p / "User"
            # Some installs nest the exe one level down.
            if not candidates_exe:
                for sub in p.iterdir() if p.exists() else []:
                    if sub.is_dir():
                        for name in DOLPHIN_EXE_NAMES:
                            cand = sub / name
                            if cand.exists():
                                candidates_exe.append(str(cand))
                                if (sub / "User").is_dir():
                                    template_user = sub / "User"

    for fb in _appdata_fallbacks():
        if os.path.exists(fb):
            candidates_exe.append(fb)
            if template_user is None:
                tu = Path(fb).parent / "User"
                if tu.is_dir():
                    template_user = tu

    exe = next((c for c in candidates_exe if os.path.exists(c)), None)
    if not exe:
        raise FileNotFoundError(
            "Could not find a Slippi Dolphin executable. Set the Slippi path in "
            "Settings (it should point to the folder with 'Slippi Dolphin.exe')."
        )
    if template_user and not Path(template_user).is_dir():
        template_user = None
    return exe, (str(template_user) if template_user else None)


def iso_dir_from_slippi(slippi_path):
    """Return the user's Dolphin ISO directory -- the folder Slippi scans for
    games -- from User/Config/Dolphin.ini (ISOPath0..9 or DefaultISO's parent).
    Falls back to <slippi>/User/Games (created if needed)."""
    import configparser
    ini_path = os.path.join(slippi_path, "User", "Config", "Dolphin.ini")
    try:
        cfg = configparser.ConfigParser()
        cfg.read(ini_path, encoding="utf-8")
        if "General" in cfg:
            g = cfg["General"]
            for i in range(10):
                key = f"ISOPath{i}"
                if key in g and g[key] and Path(g[key]).is_dir():
                    return g[key]
            if "DefaultISO" in g and g["DefaultISO"]:
                parent = str(Path(g["DefaultISO"]).parent)
                if Path(parent).is_dir():
                    return parent
    except Exception:
        pass
    fallback = os.path.join(slippi_path, "User", "Games")
    os.makedirs(fallback, exist_ok=True)
    return fallback


def launch_real(slippi_path, iso_path):
    """Launch the user's REAL Slippi Dolphin booting `iso_path` for normal play:
    their own User dir / config / controllers, a visible window, and NO pipe
    controller (unlike DolphinBoot, which is the isolated test harness). Detached
    so the game keeps running independently of the backend. Returns the exe used."""
    exe, _ = resolve_dolphin(slippi_path)
    args = [str(exe), "-e", str(iso_path)]
    creationflags = 0
    if os.name == "nt":
        # Detach from the backend so the game survives backend churn, but keep
        # the Dolphin window visible -- do NOT use CREATE_NO_WINDOW here.
        creationflags = getattr(subprocess, "DETACHED_PROCESS", 0)
    subprocess.Popen(args, cwd=str(Path(exe).parent), creationflags=creationflags)
    return exe


# --------------------------------------------------------------------------- #
# Tiny Dolphin-INI reader/writer (section -> ordered key/value), matching       #
# driver.js's writeIni semantics: parse, upsert keys, re-stringify.             #
# --------------------------------------------------------------------------- #
def _parse_ini(text):
    sections = {"": {}}
    order = [""]
    current = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(";") or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            if current not in sections:
                sections[current] = {}
                order.append(current)
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            sections[current][k.strip()] = v.strip()
    return sections, order


def _write_ini(path, mutate):
    text = ""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    sections, order = _parse_ini(text)

    def upsert(section, key, value):
        if section not in sections:
            sections[section] = {}
            order.append(section)
        sections[section][key] = str(value)

    def replace_section(section, kv):
        if section not in sections:
            order.append(section)
        sections[section] = dict(kv)

    mutate(upsert, replace_section)

    lines = []
    first = True
    for name in order:
        if name == "" and not sections.get("", {}):
            continue
        if name != "":
            if not first:
                lines.append("")
            lines.append(f"[{name}]")
            first = False
        for k, v in sections[name].items():
            lines.append(f"{k} = {v}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _patch_dolphin_ini(user_dir, pipe_name):
    path = os.path.join(user_dir, "Config", "Dolphin.ini")

    def mutate(upsert, replace_section):
        upsert("Input", "BackgroundInput", "True")       # accept input unfocused
        upsert("Interface", "ConfirmStop", "False")      # no "are you sure" on stop
        upsert("Interface", "PauseOnFocusLost", "False")
        upsert("Display", "Fullscreen", "False")
        upsert("Display", "RenderWindowAutoSize", "False")
        upsert("Display", "RenderWindowWidth", "1280")
        upsert("Display", "RenderWindowHeight", "960")
        upsert("Core", "SIDevice0", "6")  # port 1 = Standard Controller (pipe)
        upsert("Core", "SIDevice1", "0")
        upsert("Core", "SIDevice2", "0")
        upsert("Core", "SIDevice3", "0")

    _write_ini(path, mutate)

    gc_path = os.path.join(user_dir, "Config", "GCPadNew.ini")

    def mutate_gc(upsert, replace_section):
        p = "GCPad1"
        replace_section(p, {})  # wipe inherited keyboard mapping
        upsert(p, "Device", f"Pipe/0/{pipe_name}")
        for btn in ["A", "B", "X", "Y", "Z", "L", "R"]:
            upsert(p, f"Buttons/{btn}", f"Button {btn}")
        upsert(p, "Buttons/Start", "Button START")
        upsert(p, "Buttons/Threshold", "50.0")
        upsert(p, "Main Stick/Up", "Axis MAIN Y +")
        upsert(p, "Main Stick/Down", "Axis MAIN Y -")
        upsert(p, "Main Stick/Left", "Axis MAIN X -")
        upsert(p, "Main Stick/Right", "Axis MAIN X +")
        upsert(p, "Main Stick/Radius", "100.0")
        upsert(p, "D-Pad/Up", "Button D_UP")
        upsert(p, "D-Pad/Down", "Button D_DOWN")
        upsert(p, "D-Pad/Left", "Button D_LEFT")
        upsert(p, "D-Pad/Right", "Button D_RIGHT")
        upsert(p, "C-Stick/Up", "Axis C Y +")
        upsert(p, "C-Stick/Down", "Axis C Y -")
        upsert(p, "C-Stick/Left", "Axis C X -")
        upsert(p, "C-Stick/Right", "Axis C X +")
        upsert(p, "C-Stick/Radius", "100.0")
        upsert(p, "Triggers/L", "Button L")
        upsert(p, "Triggers/R", "Button R")
        upsert(p, "Triggers/L-Analog", "Axis L -+")
        upsert(p, "Triggers/R-Analog", "Axis R -+")
        upsert(p, "Triggers/Threshold", "90.0")
        replace_section("GCPad3", {})  # drop inherited port-3 keyboard cursor

    _write_ini(gc_path, mutate_gc)


def _patch_clean_osd(user_dir):
    """Turn off the emulator OSD overlays for a clean screenshot: Dolphin's FPS
    counter and Slippi's on-screen ping ("Delay: N"). Keys are written lowercase
    to match how Slippi writes GFX.ini (Dolphin reads them case-insensitively)."""
    path = os.path.join(user_dir, "Config", "GFX.ini")

    def mutate(upsert, _replace):
        upsert("Settings", "showfps", "False")
        upsert("Settings", "shownetplayping", "False")
        upsert("Settings", "shownetplaymessages", "False")

    _write_ini(path, mutate)

    # General OSD messages ("Wrote memory card A contents to ...") are a
    # Dolphin.ini Interface setting, not GFX.ini -- they photobomb captures
    # whenever the game touches the memory card near the shot.
    dolphin_ini = os.path.join(user_dir, "Config", "Dolphin.ini")

    def mutate_iface(upsert, _replace):
        upsert("Interface", "OnScreenDisplayMessages", "False")

    _write_ini(dolphin_ini, mutate_iface)


def _patch_gfx_textures(user_dir, dump=False, hires=True):
    path = os.path.join(user_dir, "Config", "GFX.ini")

    def mutate(upsert, _replace):
        upsert("Settings", "DumpTextures", "True" if dump else "False")
        upsert("Settings", "HiresTextures", "True" if hires else "False")

    _write_ini(path, mutate)


def dolphin_running():
    """Return the pids of any already-running Dolphin EMULATOR process (the user's
    own Slippi window). The in-game harness launches and drives its OWN throwaway
    Dolphin, so a second one open at the same time steals the foreground -- the test
    then just sits on the menu, never pressing a button. Windows-only; returns []
    elsewhere or on error. Note: the Slippi LAUNCHER ("Slippi Launcher.exe") is a
    different process and is intentionally NOT matched."""
    if os.name != "nt":
        return []
    pids = []
    for name in DOLPHIN_EXE_NAMES:  # "Slippi Dolphin.exe", "Dolphin.exe", "DolphinWx.exe"
        try:
            out = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {name}", "/FO", "CSV", "/NH"],
                capture_output=True, text=True,
                creationflags=_k32_creationflags, timeout=10,
            ).stdout or ""
        except Exception:
            continue
        for line in out.splitlines():
            line = line.strip()
            if not line or line.upper().startswith("INFO:"):
                continue
            cells = [c.strip().strip('"') for c in line.split('","')]
            if cells and cells[0].lower() == name.lower() and len(cells) > 1:
                pids.append(cells[1])
    return pids


def pick_pipe_index(max_index=8):
    """Pick a slippibot<N> pipe index NOT currently in use, so we never collide
    with a Slippi instance the user already has open."""
    for n in range(1, max_index + 1):
        if not pipe_in_use(n):
            return n
    return 1


class DolphinBoot:
    """Owns the isolated run dir + the launched Dolphin process. Use as a
    context manager so the temp User dir and the process are always cleaned up
    (the user's real Slippi config is never written)."""

    def __init__(self, iso_path, slippi_path, runs_root, pipe_index=None,
                 hires_textures=False, load_seed=None, clean_osd=False,
                 log=lambda m: None):
        self.iso_path = iso_path
        self.slippi_path = slippi_path
        self.runs_root = Path(runs_root)
        self.log = log
        self.pipe_index = pipe_index
        self.hires_textures = hires_textures
        self.load_seed = load_seed  # optional path to a Load/Textures dir to pre-seed
        self.clean_osd = clean_osd  # turn off FPS/ping OSD overlays (capture mode)
        self.run_dir = None
        self.user_dir = None
        self.exe = None
        self.proc = None

    def prepare(self):
        self.exe, template_user = resolve_dolphin(self.slippi_path)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = self.runs_root / f"test-{stamp}"
        self.user_dir = self.run_dir / "User"
        (self.user_dir / "Config").mkdir(parents=True, exist_ok=True)

        # Copy the user's Config + Slippi login into the throwaway User dir.
        if template_user:
            src_cfg = Path(template_user) / "Config"
            if src_cfg.is_dir():
                shutil.copytree(src_cfg, self.user_dir / "Config", dirs_exist_ok=True)
            src_slippi = Path(template_user) / "Slippi"
            if src_slippi.is_dir():
                shutil.copytree(src_slippi, self.user_dir / "Slippi", dirs_exist_ok=True)

        if self.pipe_index is None:
            self.pipe_index = pick_pipe_index()
        _patch_dolphin_ini(str(self.user_dir), f"slippibot{self.pipe_index}")

        if self.clean_osd:
            _patch_clean_osd(str(self.user_dir))

        if self.hires_textures:
            _patch_gfx_textures(str(self.user_dir), dump=False, hires=True)
            # Pre-seed the HD textures before boot (CacheHiresTextures indexes the
            # Load folder once at startup; injecting after boot wouldn't be seen).
            if self.load_seed and Path(self.load_seed).is_dir():
                dst = self.user_dir / "Load" / "Textures"
                dst.mkdir(parents=True, exist_ok=True)
                shutil.copytree(self.load_seed, dst, dirs_exist_ok=True)

        self.log(f"isolated User dir: {self.user_dir}")
        self.log(f"Dolphin exe: {self.exe}  (pipe slippibot{self.pipe_index})")
        return self

    def launch(self):
        args = [self.exe, "-u", str(self.user_dir), "-b", "-e", self.iso_path]
        self.log(f"launching: {args}")
        self.proc = subprocess.Popen(
            args, cwd=os.path.dirname(self.exe),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        # Register as the embeddable Dolphin so the frontend's "test in game"
        # panel can pin our render window inside the app (ingame/embed.py).
        try:
            from . import embed
            embed.set_active(self.proc.pid)
        except Exception:
            pass
        return self.proc

    @property
    def pid(self):
        return self.proc.pid if self.proc else None

    def wait_for_pipe(self, timeout=45.0):
        r"""Dolphin only creates \\.\pipe\slippibot<N> once its input plugin
        initialises (~when the game starts booting); a fixed sleep races it.
        Probe the pipe until it opens."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.proc.poll() is not None:
                return False  # Dolphin exited during boot
            h = pipe_open(self.pipe_index)
            if h is not None:
                from .melee_pipe import _k32
                _k32.CloseHandle(h)
                return True
            time.sleep(0.6)
        return False

    def terminate(self):
        if self.proc:
            try:
                from . import embed
                # Park the render window offscreen BEFORE killing the process:
                # a dying GL window flashes black wherever it sits (very visible
                # when it's pinned topmost over the app by the embed).
                if self.proc.poll() is None:
                    embed.park(self.proc.pid)
                embed.clear_active(self.proc.pid)
            except Exception:
                pass
        if self.proc and self.proc.poll() is None:
            pid = self.proc.pid
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                pass
            if self.proc.poll() is None and os.name == "nt":
                # Tree-kill any stragglers (taskkill.exe is a plain system exe,
                # not PowerShell).
                try:
                    subprocess.run(
                        ["taskkill", "/PID", str(pid), "/T", "/F"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        creationflags=_k32_creationflags, timeout=10,
                    )
                except Exception:
                    pass

    def cleanup(self):
        self.terminate()
        if self.run_dir and self.run_dir.exists():
            shutil.rmtree(self.run_dir, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.cleanup()
        return False
