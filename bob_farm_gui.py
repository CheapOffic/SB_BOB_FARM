"""
BOB Farm - GUI version (Slap Battles, Halloween event, BOB glove portal farm)

- Every setting can be edited in the window.
- Settings are saved to  bob_farm_config.json  (next to this script) and loaded on start.
- Language: English (default) or Russian.
- "Requirements" tab shows what a PC needs and what yours has.

While the portal is not visible the character jumps and slowly turns the camera until it is found.
When the portal is found, jumping stops and the character walks straight to it, enters it,
presses E, waits and resets the character (Esc -> R -> Enter).

Debug window: the same pinned always-on-top window as in the console version
(close it with the "-" key; it has no close button).

Stop: the Stop button or F8 (works while Roblox is focused).

Install:  pip install mss opencv-python numpy pydirectinput pillow pytesseract
Automatic disconnect-dialog recovery checks all Roblox disconnect error codes every 20 seconds. Tesseract OCR is required to detect dialog text.
Run:      python bob_farm_gui.py
"""
import os, sys, json, time, ctypes, threading, base64, queue, platform, urllib.request, urllib.error, urllib.parse, hashlib, re, tempfile, secrets, random, ast, importlib.util, inspect, asyncio, pathlib, shutil, subprocess, io
from ctypes import wintypes

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except ImportError:
    print("tkinter is missing. Reinstall Python and tick the 'tcl/tk and IDLE' option.")
    raise SystemExit(1)

try:
    import cv2, numpy as np, mss, pydirectinput as pdi
    from PIL import Image, ImageDraw, ImageFont
except ImportError as _e:
    _r = tk.Tk(); _r.withdraw()
    messagebox.showerror("Missing packages", f"{_e}\n\nInstall them with:\npip install mss opencv-python numpy pydirectinput pillow pytesseract")
    raise SystemExit(1)

pdi.PAUSE = 0
pdi.FAILSAFE = False

try:
    import pytesseract
    # pytesseract is only a Python wrapper; the Tesseract executable is also required.
    _tesseract_candidates = [
        shutil.which("tesseract"),
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Tesseract-OCR", "tesseract.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Tesseract-OCR", "tesseract.exe"),
    ]
    for _candidate in _tesseract_candidates:
        if _candidate and os.path.isfile(_candidate):
            pytesseract.pytesseract.tesseract_cmd = _candidate
            break
except Exception:
    pytesseract = None

OCR_AVAILABLE = False
if pytesseract is not None:
    try:
        pytesseract.get_tesseract_version()
        OCR_AVAILABLE = True
    except Exception:
        OCR_AVAILABLE = False

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bob_farm_config.json")
CONFIG_VERSION = 3
APP_VERSION = "V1.5.6"
SLAP_BATTLES_PLACE_ID = 6403373529
GITHUB_API_CONFIGS = "https://api.github.com/repos/CheapOffic/SB_BOB_FARM/contents/CONFIGS?ref=main"
GITHUB_GUI_RAW = "https://raw.githubusercontent.com/CheapOffic/SB_BOB_FARM/main/GUI/bob_farm_gui.py"
GIT_CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GIT_CONFIGS")
GIT_CONFIG_STATE = os.path.join(GIT_CONFIG_DIR, ".download_state.json")
THEME_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bob_farm_theme.json")
TELEGRAM_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bob_farm_telegram.json")
TELEGRAM_ACCESS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bob_farm_telegram_access.json")
TELEGRAM_FEATURES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bob_farm_telegram_features.json")
STATS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bob_farm_stats.json")
PLUGIN_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bob_farm_plugin_settings.json")
PROFILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Profiles")
MASTERIES_API_URL = "https://api.github.com/repos/CheapOffic/SB_BOB_FARM/contents/Masteries?ref=main"
MASTERIES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Masteries")
MASTERIES_STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bob_farm_masteries.json")
MASTERIES_MAX_BYTES = 1024 * 1024
MIGRATE_RESET = ("search_spin", "search_speed", "jump_while_walking")   # reset to the new defaults when an older file is loaded
STOP_KEY_VK = 0x77            # F8
WINDOW_TITLE = "Roblox"
PLUGIN_WAIT_MAX = 60.0         # seconds the main bot waits for a plugin after entering the portal
START_DELAY = 5               # seconds between pressing Start and the first action
user32 = ctypes.windll.user32 if os.name == "nt" else None
DBG_W = 480                   # width of the debug window in pixels
DBG_WIN = "debug"             # title of the debug window

# ============================== SETTINGS SCHEMA ==============================
# (group, key, kind, default, min, max)
# kinds: int | float | bool | sign | zones
SCHEMA = [
    ("features", "builtin_farm",     "bool",  True,  None,   None),
    ("features", "feat_aim",         "bool",  True,  None,   None),
    ("features", "feat_walk",        "bool",  True,  None,   None),
    ("features", "feat_press_e",     "bool",  True,  None,   None),
    ("features", "feat_reset",       "bool",  True,  None,   None),
    ("features", "feat_plugins",     "bool",  True,  None,   None),

    ("capture", "target_fps",         "int",   30,    5,      120),
    ("capture", "proc_width",         "int",   640,   320,    1920),
    ("capture", "capture_window",     "bool",  True,  None,   None),
    ("capture", "show_preview",       "bool",  True,  None,   None),
    ("capture", "show_debug_window",  "bool",  True,  None,   None),
    ("capture", "debug_fps",          "int",   30,    1,      120),

    ("detect",  "h_min",              "int",   14,    0,      180),
    ("detect",  "h_max",              "int",   26,    0,      180),
    ("detect",  "s_min",              "int",   200,   0,      255),
    ("detect",  "s_max",              "int",   255,   0,      255),
    ("detect",  "v_min",              "int",   225,   0,      255),
    ("detect",  "v_max",              "int",   255,   0,      255),
    ("detect",  "min_area_frac",      "float", 0.002, 0.0001, 0.5),
    ("detect",  "max_area_frac",      "float", 0.60,  0.01,   1.0),
    ("detect",  "min_fill",           "float", 0.45,  0.0,    1.0),
    ("detect",  "min_solidity",       "float", 0.75,  0.0,    1.0),
    ("detect",  "ar_min",             "float", 0.25,  0.05,   5.0),
    ("detect",  "ar_max",             "float", 1.40,  0.05,   10.0),
    ("detect",  "max_red_frac",       "float", 0.12,  0.0,    1.0),
    ("detect",  "confirm_frames",     "int",   3,     1,      30),
    ("detect",  "ignore_zones",       "zones", "0.78,0.00,1.00,0.18", None, None),

    ("camera",  "mouse_gain",         "float", 500.0, 1.0,    5000.0),
    ("camera",  "mouse_max_step",     "int",   120,   1,      2000),
    ("camera",  "mouse_sign",         "sign",  1,     None,   None),
    ("camera",  "first_person_on_spawn", "bool", True, None, None),
    ("camera",  "deadzone",           "float", 0.015, 0.0,    0.5),
    ("camera",  "walk_angle",         "float", 0.12,  0.0,    1.0),

    ("search",  "search_jump",        "bool",  True,  None,   None),
    ("search",  "search_spin",        "bool",  True,  None,   None),
    ("search",  "search_speed",       "int",   15,    1,      500),
    ("search",  "jump_interval",      "float", 0.45,  0.1,    5.0),
    ("search",  "jump_hold",          "float", 0.05,  0.01,   1.0),
    ("search",  "jump_while_walking", "bool",  False, None,   None),
    ("search",  "search_timeout",     "float", 8.0,   1.0,    120.0),
    ("search",  "search_fail_e",      "bool",  True,  None,   None),

    ("portal",  "enter_min_ratio",    "float", 0.12,  0.01,   1.0),
    ("portal",  "lost_frames",        "int",   6,     1,      60),
    ("portal",  "enter_orange_frac",  "float", 0.20,  0.01,   1.0),
    ("portal",  "orange_gone_frac",   "float", 0.03,  0.0,    0.5),
    ("portal",  "enter_wait_max",     "float", 2.5,   0.2,    30.0),
    ("portal",  "e_delay",            "float", 0.1,   0.0,    5.0),
    ("portal",  "reset_delay",        "float", 0.6,   0.0,    10.0),
    ("portal",  "respawn_wait",       "float", 4.0,   0.0,    60.0),
    ("portal",  "key_hold",           "float", 0.06,  0.01,   1.0),

    ("recovery", "auto_reconnect",    "bool",  True,  None,   None),
    ("recovery", "reconnect_retry",   "int",   20,    5,      180),
    ("recovery", "stall_watchdog",    "bool",  False, None,   None),
    ("recovery", "stall_minutes",     "int",   1,     1,      60),
    ("recovery", "stall_action_hop",  "bool",  True,  None,   None),
    ("recovery", "hop_after_portals", "bool",  False, None,   None),
    ("recovery", "hop_portal_count",  "int",   10,    1,      1000),
]
DEFAULTS = {key: default for (_, key, _, default, _, _) in SCHEMA}
GROUPS = ["features", "capture", "detect", "camera", "search", "portal", "recovery"]


class FieldError(Exception):
    def __init__(self, code, **kw):
        super().__init__(code)
        self.code, self.kw = code, kw


def fmt_num(v):
    return f"{v:g}" if isinstance(v, float) else str(v)


def parse_zones(text):
    """'0.78,0.00,1.00,0.18; 0,0,0.2,0.1'  ->  [(0.78, 0.0, 1.0, 0.18), (0, 0, 0.2, 0.1)]"""
    zones = []
    for part in str(text).replace("\n", ";").split(";"):
        part = part.strip()
        if not part:
            continue
        try:
            nums = [float(x) for x in part.split(",")]
        except ValueError:
            raise FieldError("err.zones")
        if len(nums) != 4 or any(n < 0 or n > 1 for n in nums) or nums[0] >= nums[2] or nums[1] >= nums[3]:
            raise FieldError("err.zones")
        zones.append(tuple(nums))
    return zones


def parse_value(kind, raw, lo, hi):
    if kind == "bool":
        return bool(raw)
    if kind == "sign":
        s = str(raw).strip()
        if s not in ("1", "-1"):
            raise FieldError("err.number")
        return int(s)
    if kind == "zones":
        text = str(raw).strip()
        parse_zones(text)                       # validates
        return text
    s = str(raw).strip().replace(",", ".")
    if kind == "int":
        try:
            val = int(s)
        except ValueError:
            raise FieldError("err.int")
    else:
        try:
            val = float(s)
        except ValueError:
            raise FieldError("err.number")
    if (lo is not None and val < lo) or (hi is not None and val > hi):
        raise FieldError("err.range", lo=fmt_num(lo), hi=fmt_num(hi))
    return val


def cross_check(cfg):
    """Returns a list of (key, error_code) for settings that conflict with each other."""
    bad = []
    if cfg["h_min"] > cfg["h_max"]:
        bad.append(("h_min", "err.minmax"))
    if cfg["s_min"] > cfg["s_max"]:
        bad.append(("s_min", "err.minmax"))
    if cfg["v_min"] > cfg["v_max"]:
        bad.append(("v_min", "err.minmax"))
    if cfg["ar_min"] >= cfg["ar_max"]:
        bad.append(("ar_min", "err.minmax"))
    if cfg["min_area_frac"] >= cfg["max_area_frac"]:
        bad.append(("min_area_frac", "err.minmax"))
    return bad


# ============================== CONFIG FILE (.json) ==============================
def load_config():
    """Loads bob_farm_config.json. Creates it with defaults if it does not exist."""
    cfg, lang = dict(DEFAULTS), "en"
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            lang = data.get("language", "en") if data.get("language") in ("en", "ru") else "en"
            saved = data.get("settings", {})
            for (_, key, kind, default, lo, hi) in SCHEMA:
                if key in saved:
                    try:
                        cfg[key] = parse_value(kind, saved[key], lo, hi)
                    except FieldError:
                        pass                      # bad value in the file -> keep the default
            if data.get("config_version", 1) < CONFIG_VERSION:
                # Backward-compatible migration: saved keys remain untouched; only missing
                # keys keep their current defaults from dict(DEFAULTS).
                try:
                    save_config(cfg, lang)
                except Exception:
                    pass
        except Exception:
            pass                                  # unreadable file -> defaults
    else:
        save_config(cfg, lang)
    return cfg, lang


def save_config(cfg, lang):
    data = {"config_version": CONFIG_VERSION, "language": lang, "settings": cfg}
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CONFIG_PATH)


# ============================== TEXTS (English / Russian) ==============================
TEXT = {
    "en": {
        "title": "BOB Farm", "theme": "Theme",
        "subtitle": "Slap Battles  ·  automatic BOB glove portal farm",
        "lang": "Language",
        "tab.settings": "Settings", "tab.requirements": "Requirements",
        "tab.dashboard": "Dashboard", "tab.console": "Live Console",
        "tab.reports": "Reports", "tab.connect": "Connect", "tab.masteries": "Masteries",
        "report.title": "Session report", "report.refresh": "Refresh report",
        "report.empty": "Events will appear here during a session", "report.activity": "EVENT ACTIVITY",
        "report.portals": "Portals", "report.resets": "Resets", "report.errors": "Errors",
        "report.start": "Start", "report.latest": "Latest",
        "report.summary": "Status: {status}    Duration: {duration}    Portals: {portals}    No-portal resets: {resets}    Errors: {errors}",
        "dash.title": "Session dashboard", "dash.status": "Farm status", "dash.elapsed": "Session time",
        "dash.portals": "Portals entered", "dash.noportal": "No-portal resets", "dash.errors": "Errors",
        "dash.last": "Last event", "dash.waiting": "No events yet", "console.clear": "Clear console",
        "btn.start": "Start", "btn.stop": "Stop", "btn.save": "Save settings", "btn.profiles": "Profiles",
        "btn.choose_config": "Choose config", "btn.export_config": "Export config",
        "btn.git_config": "SET CONFIG FROM GIT", "btn.check_updates": "CHECK FOR UPDATES",
        "btn.profiles": "Profiles", "btn.plugin_settings": "Plugin settings", "btn.calibrate": "Calibrate portal color",
        "status.idle": "Idle", "status.starting": "Starting - click into Roblox", "status.running": "Running",
        "status.stopping": "Stopping...",
        "preview.title": "Live preview", "preview.off": "Preview is off", "preview.wait": "Waiting for the first frame...",
        "log.title": "Log", "hotkey": "F8 = stop  |  '-' = close the debug window (both work while Roblox is focused)",
        "cfg.path": "Config file:",
        "msg.invalid.title": "Invalid settings", "msg.invalid.head": "Please fix these fields:",
        "err.number": "must be a number", "err.int": "must be a whole number",
        "err.range": "must be between {lo} and {hi}",
        "err.zones": "format: x0,y0,x1,y1 with values 0..1 (several zones separated by ';')",
        "err.minmax": "min must be lower than max",
        "group.capture": "Capture & performance", "group.detect": "Portal detection",
        "group.features": "Features (on / off)", "group.camera": "Camera & movement", "group.search": "Searching & jumping",
        "group.portal": "Entering the portal & reset", "group.recovery": "Recovery & automatic server hopping",
        "auto_reconnect": ("Reconnect after disconnect", "Every 20 seconds, detect any Roblox Disconnected dialog (any error code) or a closed Roblox process and try to reconnect. Requires Tesseract OCR."),
        "reconnect_retry": ("Reconnect wait (s)", "How long to wait after pressing Reconnect before opening a fresh server."),
        "stall_watchdog": ("Enable stuck protection", "If no portal is entered for the selected time, perform the chosen recovery action."),
        "stall_minutes": ("No-portal timeout (min)", "How many minutes without a portal before the watchdog acts."),
        "stall_action_hop": ("Server hop when stuck", "When enabled, join another public server. When disabled, only log the warning."),
        "hop_after_portals": ("Hop after N portals", "Automatically change to another public server after the selected number of portal entries."),
        "hop_portal_count": ("Portal count before hop", "Number of successful portal entries between automatic server hops."),
        "req.title": "System requirements", "req.note": "Approximate values. The script itself is light (CPU only, no GPU needed); most of the load comes from Roblox.",
        "req.col.component": "Component", "req.col.min": "Minimum", "req.col.rec": "Recommended",
        "req.os": "Operating system", "req.os.min": "Windows 10 (64-bit)", "req.os.rec": "Windows 11 (64-bit)",
        "req.python": "Python", "req.python.min": "3.9", "req.python.rec": "3.10 - 3.12 (with tkinter)",
        "req.cpu": "Processor", "req.cpu.min": "4 threads, 2.5 GHz", "req.cpu.rec": "8+ threads, 3.5+ GHz",
        "req.ram": "Memory (RAM)", "req.ram.min": "8 GB", "req.ram.rec": "16 GB",
        "req.gpu": "Graphics card", "req.gpu.min": "Any GPU that runs Roblox (integrated is fine)", "req.gpu.rec": "GTX 1050 / RX 560 or better",
        "req.display": "Screen", "req.display.min": "1280x720, windowed or borderless", "req.display.rec": "1920x1080, windowed or borderless",
        "req.disk": "Free disk space", "req.disk.min": "300 MB", "req.disk.rec": "500 MB",
        "req.deps": "Python packages", "req.deps.min": "mss, opencv-python, numpy, pydirectinput", "req.deps.rec": "same",
        "req.game": "Roblox", "req.game.min": "First-person view (zoom in all the way)", "req.game.rec": "same",
        "req.usage": "The script uses about 0.2-0.3 GB of RAM and one CPU core. It does not use the GPU.",
        "pc.title": "Your PC", "pc.cpu": "Processor", "pc.cores": "CPU threads", "pc.ram": "RAM (total / free)",
        "pc.gpu": "Graphics card", "pc.screen": "Screen", "pc.python": "Python", "pc.os": "System",
        "pc.unknown": "unknown",
        "pc.verdict.rec": "Your PC meets the recommended requirements.",
        "pc.verdict.min": "Your PC meets the minimum requirements. Lower the FPS or the processing width if it lags.",
        "pc.verdict.low": "Your PC is below the minimum requirements. Expect low FPS and lag.",
        "evt.starting": "Starting in {sec} seconds - Roblox is brought to the front automatically (click into the game if nothing happens).",
        "evt.capture_window": "Capturing the Roblox window: {w}x{h} at ({l}, {t})",
        "evt.capture_monitor": "Roblox window not found - capturing the whole monitor: {w}x{h}",
        "evt.capture_changed": "Capture area changed: {w}x{h} at ({l}, {t})",
        "evt.entered": "Entered the portal -> E in {e} s -> reset in {r} s",
        "evt.noportal": "No portal found -> E + reset",
        "evt.server_hop": "Server hop: joining a new server.", "evt.plugin_start": "Plugin loaded: {name}", "evt.plugin_cycle": "Plugin pass completed: {name}",
        "evt.plugin_log": "[{name}] {msg}", "evt.plugin_error": "Plugin {name} failed: {err}",
        "evt.plugins_none": "No plugin could be loaded.",
        "evt.stopped": "Stopped.", "evt.error": "Error: {err}", "evt.warning": "Warning: {msg}", "evt.first_person": "Camera zoomed to first-person.", "evt.debug_closed": "Debug window closed ('-' key).",
        "evt.settings": "Search: jumping {jump}, turning the camera {spin} (speed {speed}); jumping while walking {jww}.",
        "evt.state.SEARCH": "Searching for the portal...", "evt.state.CANDIDATE": "Something orange spotted - checking it...",
        "evt.state.WALK": "Portal confirmed - walking to it.", "evt.state.ENTER": "Right at the portal - waiting for the teleport.",
        "evt.saved": "Settings saved to {path}", "evt.reset": "Defaults restored (not saved yet).",
        "evt.save_failed": "Could not save the config: {err}",
        "target_fps": ("Target FPS", "How many frames per second the script processes."),
        "proc_width": ("Processing width (px)", "Frame width used for detection. Lower is faster, higher sees farther."),
        "capture_window": ("Capture only the Roblox window", "Ignores everything else on the screen. Recommended."),
        "show_preview": ("Show live preview", "Shows what the script sees inside this window."),
        "show_debug_window": ("Show debug window", "Pinned always-on-top window with the detection boxes and the colour mask. Close it with the '-' key."),
        "h_min": ("Hue min (H)", "Portal colour range in HSV, OpenCV scale: H 0-180, S and V 0-255. The portal core is H 21, S 250, V 253."),
        "h_max": ("Hue max (H)", "Raise it if the portal is not detected, lower it to exclude yellow things."),
        "s_min": ("Saturation min (S)", "Lower it if the portal looks washed out."),
        "s_max": ("Saturation max (S)", "Normally 255."),
        "v_min": ("Brightness min (V)", "Lower it in dark areas."),
        "v_max": ("Brightness max (V)", "Normally 255."),
        "min_area_frac": ("Min blob area", "Smallest orange blob (share of the frame) that can be the portal."),
        "max_area_frac": ("Max blob area", "Orange covering more than this share of the frame is not the portal."),
        "min_fill": ("Min fill", "Blob area divided by its bounding box area."),
        "min_solidity": ("Min solidity", "Blob area divided by its convex hull area. Rejects ragged shapes."),
        "ar_min": ("Min width / height", "The portal is about 0.66 wide-to-tall."),
        "ar_max": ("Max width / height", "Upper limit of the same ratio."),
        "max_red_frac": ("Max red share", "Rejects blobs whose box contains this much bright pure red (the red glove glow)."),
        "confirm_frames": ("Confirm frames", "Frames in a row the portal must stay in place before the script walks to it."),
        "ignore_zones": ("Ignore zones", "Screen areas to ignore as x0,y0,x1,y1 from 0 to 1. Separate several zones with ';'."),
        "mouse_gain": ("Camera gain", "Camera turn strength. Higher turns faster but may overshoot."),
        "mouse_max_step": ("Max camera step", "Maximum mouse pixels per frame."),
        "mouse_sign": ("Camera direction", "Set to -1 if the camera turns the wrong way."),
        "first_person_on_spawn": ("Auto first-person on spawn", "Click Roblox at the current mouse position, then scroll the wheel up after startup and every respawn to zoom fully in. Disable this if you prefer third-person."),
        "deadzone": ("Centre dead zone", "No turning while the portal is this close to the screen centre (fraction of width)."),
        "walk_angle": ("Walk angle", "Walk forward only if the portal is within this distance from the centre (fraction of width)."),
        "search_jump": ("Jump while searching", "No portal on screen: jump in place again and again until it is found."),
        "search_spin": ("Turn while searching", "Slowly turn the camera while searching so the portal can come into view. Off = jump in place only (it will never find a portal that is not in front of you)."),
        "search_speed": ("Search turn speed", "Mouse pixels per frame. Only used when turning while searching is on."),
        "jump_interval": ("Jump interval (s)", "Seconds between jumps."),
        "jump_hold": ("Jump key hold (s)", "How long the jump key is held."),
        "jump_while_walking": ("Jump while walking", "Keep jumping while walking to the portal. Off = jumping stops when the portal is found and the character walks normally."),
        "search_timeout": ("Search timeout (s)", "No portal for this long: press E and reset."),
        "search_fail_e": ("Reset when no portal", "Enable the timeout rule above."),
        "debug_fps": ("Debug window FPS", "How many times per second the debug window is redrawn (lower = less load)."),
        "builtin_farm": ("Built-in portal farm", "Main bot: find the portal, walk to it, enter it. Turn it off to run only Masteries plugins."),
        "feat_aim": ("Turn the camera to the portal", "Aim the camera at the portal while walking to it."),
        "feat_walk": ("Walk to the portal", "Hold W and walk straight to the portal once it is in front of you."),
        "feat_press_e": ("Press E inside", "Press E after entering the portal."),
        "feat_reset": ("Reset the character", "Esc -> R -> Enter after the portal (and after the no-portal timeout)."),
        "feat_plugins": ("Run Masteries plugins", "Run the plugins ticked in the Masteries tab when you press Start."),
        "enter_min_ratio": ("Close-portal height", "A portal taller than this share of the frame counts as close."),
        "lost_frames": ("Lost frames", "Frames without the portal before it counts as lost."),
        "enter_orange_frac": ("Close-portal orange share", "Orange covered this share of the screen: the player was right at the portal."),
        "orange_gone_frac": ("Teleport orange share", "Orange dropped below this: teleported, we are inside."),
        "enter_wait_max": ("Max wait for teleport (s)", "If the orange never disappears, treat it as entered after this long."),
        "e_delay": ("E delay (s)", "Wait after entering the portal, then press E."),
        "reset_delay": ("Reset delay (s)", "Wait after pressing E, then reset the character."),
        "respawn_wait": ("Respawn wait (s)", "Pause after the reset before searching again."),
        "key_hold": ("Key hold (s)", "How long each key is held. Very short taps can be missed by the game."),
    },
    "ru": {
        "title": "BOB Farm", "theme": "Тема",
        "subtitle": "Slap Battles  ·  автофарм портала для перчатки BOB",
        "lang": "Язык",
        "tab.settings": "Настройки", "tab.requirements": "Требования",
        "tab.dashboard": "Панель", "tab.console": "Журнал событий",
        "tab.reports": "Отчёты", "tab.connect": "Связь", "tab.masteries": "Мастерии",
        "report.title": "Отчёт сессии", "report.refresh": "Обновить отчёт",
        "report.empty": "События появятся здесь во время сессии", "report.activity": "АКТИВНОСТЬ СОБЫТИЙ",
        "report.portals": "Порталы", "report.resets": "Ресеты", "report.errors": "Ошибки",
        "report.start": "Начало", "report.latest": "Последнее",
        "report.summary": "Статус: {status}    Время: {duration}    Порталы: {portals}    Ресеты без портала: {resets}    Ошибки: {errors}",
        "dash.title": "Статистика сессии", "dash.status": "Статус фарма", "dash.elapsed": "Время сессии",
        "dash.portals": "Входов в портал", "dash.noportal": "Ресетов без портала", "dash.errors": "Ошибок",
        "dash.last": "Последнее событие", "dash.waiting": "Событий пока нет", "console.clear": "Очистить журнал",
        "btn.start": "Старт", "btn.stop": "Стоп", "btn.save": "Сохранить настройки", "btn.profiles": "Профили",
        "btn.choose_config": "Выбрать конфиг", "btn.export_config": "Экспорт конфига",
        "btn.git_config": "SET CONFIG FROM GIT", "btn.check_updates": "CHECK FOR UPDATES",
        "btn.profiles": "Профили", "btn.plugin_settings": "Настройки плагина", "btn.calibrate": "Калибровать цвет портала",
        "status.idle": "Ожидание", "status.starting": "Запуск - кликни в окно Roblox", "status.running": "Работает",
        "status.stopping": "Останавливаю...",
        "preview.title": "Превью", "preview.off": "Превью выключено", "preview.wait": "Жду первый кадр...",
        "log.title": "Журнал", "hotkey": "F8 = стоп  |  '-' = закрыть окно debug (работают, когда активен Roblox)",
        "cfg.path": "Файл настроек:",
        "msg.invalid.title": "Неверные настройки", "msg.invalid.head": "Исправь эти поля:",
        "err.number": "должно быть числом", "err.int": "должно быть целым числом",
        "err.range": "должно быть от {lo} до {hi}",
        "err.zones": "формат: x0,y0,x1,y1 со значениями 0..1 (несколько зон через ';')",
        "err.minmax": "минимум должен быть меньше максимума",
        "group.capture": "Захват и производительность", "group.detect": "Детект портала",
        "group.features": "Функции (вкл / выкл)", "group.camera": "Камера и движение", "group.search": "Поиск и прыжки",
        "group.portal": "Вход в портал и ресет", "group.recovery": "Восстановление и автоматическая смена серверов",
        "auto_reconnect": ("Перезаход после отключения", "Каждые 20 секунд проверяет любое окно Roblox Disconnected (любой код ошибки) или закрытие Roblox и пытается переподключиться. Нужен Tesseract OCR."),
        "reconnect_retry": ("Ожидание перезахода (с)", "Сколько ждать после нажатия Reconnect, прежде чем открывать новый сервер."),
        "stall_watchdog": ("Включить защиту от зависания", "Если портал не найден за указанное время, выполнить выбранное действие восстановления."),
        "stall_minutes": ("Тайм-аут без портала (мин)", "Сколько минут без входа в портал ждать до действия защиты."),
        "stall_action_hop": ("Менять сервер при зависании", "Если включено — зайти на другой публичный сервер. Если выключено — только записать предупреждение."),
        "hop_after_portals": ("Менять сервер после N порталов", "Автоматически переходить на другой публичный сервер после указанного числа входов в портал."),
        "hop_portal_count": ("Число порталов до смены", "Сколько успешных входов в портал сделать перед автоматической сменой сервера."),
        "req.title": "Системные требования", "req.note": "Значения примерные. Сам скрипт лёгкий (только процессор, видеокарта не нужна), основная нагрузка идёт от Roblox.",
        "req.col.component": "Компонент", "req.col.min": "Минимум", "req.col.rec": "Рекомендуется",
        "req.os": "Операционная система", "req.os.min": "Windows 10 (64-бит)", "req.os.rec": "Windows 11 (64-бит)",
        "req.python": "Python", "req.python.min": "3.9", "req.python.rec": "3.10 - 3.12 (с tkinter)",
        "req.cpu": "Процессор", "req.cpu.min": "4 потока, 2.5 ГГц", "req.cpu.rec": "8+ потоков, 3.5+ ГГц",
        "req.ram": "Оперативная память", "req.ram.min": "8 ГБ", "req.ram.rec": "16 ГБ",
        "req.gpu": "Видеокарта", "req.gpu.min": "Любая, на которой идёт Roblox (встроенная подойдёт)", "req.gpu.rec": "GTX 1050 / RX 560 или лучше",
        "req.display": "Экран", "req.display.min": "1280x720, оконный режим или окно без рамки", "req.display.rec": "1920x1080, оконный режим или окно без рамки",
        "req.disk": "Свободное место на диске", "req.disk.min": "300 МБ", "req.disk.rec": "500 МБ",
        "req.deps": "Пакеты Python", "req.deps.min": "mss, opencv-python, numpy, pydirectinput, pillow; pytesseract + Tesseract OCR для автоперезахода", "req.deps.rec": "так же",
        "req.game": "Roblox", "req.game.min": "Вид от первого лица (камера приближена до упора)", "req.game.rec": "так же",
        "req.usage": "Скрипт использует около 0.2-0.3 ГБ оперативной памяти и одно ядро процессора. Видеокарту он не использует.",
        "pc.title": "Твой ПК", "pc.cpu": "Процессор", "pc.cores": "Потоков процессора", "pc.ram": "ОЗУ (всего / свободно)",
        "pc.gpu": "Видеокарта", "pc.screen": "Экран", "pc.python": "Python", "pc.os": "Система",
        "pc.unknown": "неизвестно",
        "pc.verdict.rec": "Твой ПК соответствует рекомендуемым требованиям.",
        "pc.verdict.min": "Твой ПК соответствует минимальным требованиям. Если лагает, уменьши FPS или ширину обработки.",
        "pc.verdict.low": "Твой ПК слабее минимальных требований. Жди низкий FPS и лаги.",
        "evt.starting": "Запуск через {sec} сек - Roblox выводится на передний план автоматически (если ничего не происходит, кликни в игру).",
        "evt.capture_window": "Захват окна Roblox: {w}x{h} в точке ({l}, {t})",
        "evt.capture_monitor": "Окно Roblox не найдено - захват всего монитора: {w}x{h}",
        "evt.capture_changed": "Область захвата изменилась: {w}x{h} в точке ({l}, {t})",
        "evt.entered": "Зашёл в портал -> E через {e} сек -> ресет через {r} сек",
        "evt.noportal": "Портал не найден -> E + ресет",
        "evt.server_hop": "Смена сервера: захожу на новый сервер.", "evt.plugin_start": "Плагин загружен: {name}", "evt.plugin_cycle": "Плагин выполнил проход: {name}",
        "evt.plugin_log": "[{name}] {msg}", "evt.plugin_error": "Ошибка плагина {name}: {err}",
        "evt.plugins_none": "Ни один плагин не удалось загрузить.",
        "evt.stopped": "Остановлено.", "evt.error": "Ошибка: {err}", "evt.warning": "Предупреждение: {msg}", "evt.first_person": "Камера приближена до первого лица.", "evt.debug_closed": "Окно debug закрыто (клавиша '-').",
        "evt.settings": "Поиск: прыжки {jump}, вращение камеры {spin} (скорость {speed}); прыжки при ходьбе {jww}.",
        "evt.state.SEARCH": "Ищу портал...", "evt.state.CANDIDATE": "Заметил что-то оранжевое - проверяю...",
        "evt.state.WALK": "Портал подтверждён - иду к нему.", "evt.state.ENTER": "Вплотную к порталу - жду телепорт.",
        "evt.saved": "Настройки сохранены в {path}", "evt.reset": "Значения по умолчанию восстановлены (ещё не сохранены).",
        "evt.save_failed": "Не удалось сохранить файл настроек: {err}",
        "target_fps": ("Целевой FPS", "Сколько кадров в секунду обрабатывает скрипт."),
        "proc_width": ("Ширина обработки (px)", "Ширина кадра для детекта. Меньше значит быстрее, больше значит видит дальше."),
        "capture_window": ("Захват только окна Roblox", "Всё остальное на экране игнорируется. Рекомендуется."),
        "show_preview": ("Показывать превью", "Показывает, что видит скрипт, прямо в этом окне."),
        "show_debug_window": ("Показывать окно debug", "Закреплённое поверх всех окон окно с рамками детекта и цветовой маской. Закрывается клавишей '-'."),
        "h_min": ("Оттенок мин (H)", "Диапазон цвета портала в HSV, шкала OpenCV: H 0-180, S и V 0-255. Ядро портала: H 21, S 250, V 253."),
        "h_max": ("Оттенок макс (H)", "Увеличь, если портал не находится, уменьши, чтобы исключить жёлтые объекты."),
        "s_min": ("Насыщенность мин (S)", "Уменьши, если портал выглядит блёклым."),
        "s_max": ("Насыщенность макс (S)", "Обычно 255."),
        "v_min": ("Яркость мин (V)", "Уменьши в тёмных местах."),
        "v_max": ("Яркость макс (V)", "Обычно 255."),
        "min_area_frac": ("Мин. площадь пятна", "Наименьшее оранжевое пятно (доля кадра), которое может быть порталом."),
        "max_area_frac": ("Макс. площадь пятна", "Оранжевое, занимающее больше этой доли кадра, порталом не считается."),
        "min_fill": ("Мин. заполнение", "Площадь пятна, делённая на площадь его рамки."),
        "min_solidity": ("Мин. плотность формы", "Площадь пятна, делённая на площадь его выпуклой оболочки. Отсекает рваные формы."),
        "ar_min": ("Мин. ширина / высота", "У портала примерно 0.66."),
        "ar_max": ("Макс. ширина / высота", "Верхний предел того же отношения."),
        "max_red_frac": ("Макс. доля красного", "Отсекает пятна, в рамке которых много яркого чистого красного (свечение красной перчатки)."),
        "confirm_frames": ("Кадров подтверждения", "Сколько кадров подряд портал должен стоять на месте, прежде чем скрипт пойдёт к нему."),
        "ignore_zones": ("Игнорируемые зоны", "Области экрана, которые игнорируются, в виде x0,y0,x1,y1 от 0 до 1. Несколько зон разделяй символом ';'."),
        "mouse_gain": ("Сила поворота камеры", "Чем больше, тем быстрее камера поворачивается, но может перелетать."),
        "mouse_max_step": ("Макс. шаг камеры", "Максимум пикселей мыши за кадр."),
        "mouse_sign": ("Направление камеры", "Поставь -1, если камера крутится не в ту сторону."),
        "first_person_on_spawn": ("Авто-вид от первого лица при спавне", "При переключении на Roblox нажимать в текущей позиции курсора и прокручивать колесо вверх после запуска и каждого респавна. Отключи, если предпочитаешь вид от третьего лица."),
        "deadzone": ("Мёртвая зона по центру", "Пока портал так близко к центру экрана, камера не поворачивается (доля ширины)."),
        "walk_angle": ("Угол для ходьбы", "Идти вперёд, только если портал не дальше этого расстояния от центра (доля ширины)."),
        "search_jump": ("Прыгать при поиске", "Портала нет на экране: прыгать на месте снова и снова, пока он не найдётся."),
        "search_spin": ("Вращаться при поиске", "Медленно крутить камеру при поиске, чтобы портал попал в кадр. Выключено значит только прыгать на месте (портал, которого нет перед тобой, так не найдётся)."),
        "search_speed": ("Скорость вращения при поиске", "Пикселей мыши за кадр. Работает, только если включено вращение при поиске."),
        "jump_interval": ("Интервал прыжков (с)", "Секунд между прыжками."),
        "jump_hold": ("Удержание прыжка (с)", "Сколько держать клавишу прыжка."),
        "jump_while_walking": ("Прыгать при ходьбе", "Продолжать прыгать, пока идёшь к порталу. Выключено значит прыжки прекращаются, когда портал найден, и персонаж идёт обычным шагом."),
        "search_timeout": ("Тайм-аут поиска (с)", "Портала нет так долго: нажать E и сделать ресет."),
        "search_fail_e": ("Ресет, если портала нет", "Включить правило тайм-аута выше."),
        "debug_fps": ("FPS окна debug", "Сколько раз в секунду окно debug перерисовывается (меньше = меньше нагрузка)."),
        "builtin_farm": ("Встроенный фарм портала", "Основной бот: найти портал, дойти и зайти. Выключи, чтобы работали только плагины Masteries."),
        "feat_aim": ("Поворачивать камеру на портал", "Наводить камеру на портал, пока идёшь к нему."),
        "feat_walk": ("Идти к порталу", "Зажимать W и идти прямо к порталу, когда он перед тобой."),
        "feat_press_e": ("Нажимать E внутри", "Нажимать E после входа в портал."),
        "feat_reset": ("Ресет персонажа", "Esc -> R -> Enter после портала (и после тайм-аута без портала)."),
        "feat_plugins": ("Запускать плагины Masteries", "При нажатии Старт запускать плагины, отмеченные во вкладке Masteries."),
        "enter_min_ratio": ("Высота «близкого» портала", "Портал выше этой доли кадра считается близким."),
        "lost_frames": ("Кадров потери", "Сколько кадров без портала нужно, чтобы считать его потерянным."),
        "enter_orange_frac": ("Доля оранжевого «вплотную»", "Оранжевое занимало эту долю экрана: игрок был вплотную к порталу."),
        "orange_gone_frac": ("Доля оранжевого после телепорта", "Оранжевого стало меньше этого: телепортировало, мы внутри."),
        "enter_wait_max": ("Макс. ожидание телепорта (с)", "Если оранжевое не пропадает, через столько секунд считать, что зашли."),
        "e_delay": ("Задержка E (с)", "Пауза после входа в портал, потом нажимается E."),
        "reset_delay": ("Задержка ресета (с)", "Пауза после нажатия E, потом ресет персонажа."),
        "respawn_wait": ("Ожидание респавна (с)", "Пауза после ресета перед новым поиском."),
        "key_hold": ("Удержание клавиши (с)", "Сколько держится каждая клавиша. Слишком короткие нажатия игра может не заметить."),
    },
}


def tr(lang, key, **kw):
    s = TEXT.get(lang, TEXT["en"]).get(key) or TEXT["en"].get(key) or key
    return s.format(**kw) if kw and isinstance(s, str) else s


# ============================== SYSTEM INFO ==============================
def get_system_info():
    """CPU / RAM / GPU / screen of this PC. Every value falls back to None if it cannot be read."""
    info = {"cpu": None, "threads": os.cpu_count(), "ram_total": None, "ram_free": None,
            "gpu": None, "screen": None, "python": platform.python_version(),
            "os": f"{platform.system()} {platform.release()} ({platform.machine()})"}
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
            info["cpu"] = str(winreg.QueryValueEx(k, "ProcessorNameString")[0]).strip()
    except Exception:
        info["cpu"] = platform.processor() or None
    try:
        class MEMSTAT(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        ms = MEMSTAT()
        ms.dwLength = ctypes.sizeof(MEMSTAT)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
        info["ram_total"], info["ram_free"] = ms.ullTotalPhys / 1024 ** 3, ms.ullAvailPhys / 1024 ** 3
    except Exception:
        try:
            pages, size = os.sysconf("SC_PHYS_PAGES"), os.sysconf("SC_PAGE_SIZE")
            info["ram_total"] = pages * size / 1024 ** 3
            info["ram_free"] = os.sysconf("SC_AVPHYS_PAGES") * size / 1024 ** 3
        except Exception:
            pass
    try:
        import winreg
        names = []
        base = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base) as k:
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(k, i)
                except OSError:
                    break
                i += 1
                if not sub.isdigit():
                    continue
                try:
                    with winreg.OpenKey(k, sub) as sk:
                        n = str(winreg.QueryValueEx(sk, "DriverDesc")[0]).strip()
                        if n and n not in names:
                            names.append(n)
                except OSError:
                    pass
        info["gpu"] = ", ".join(names) or None
    except Exception:
        pass
    try:
        info["screen"] = f"{user32.GetSystemMetrics(0)}x{user32.GetSystemMetrics(1)}"
    except Exception:
        pass
    return info


def pc_verdict(info):
    """'rec' / 'min' / 'low' / None (unknown)."""
    threads, ram = info.get("threads"), info.get("ram_total")
    if not threads or not ram:
        return None
    if threads >= 8 and ram >= 15.0:
        return "rec"
    if threads >= 4 and ram >= 7.5:
        return "min"
    return "low"


# ============================== WINDOWS HELPERS ==============================
def key_down(vk):
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def mouse_move(dx):
    user32.mouse_event(0x0001, int(dx), 0, 0, 0)        # relative mouse movement


def _find_roblox_hwnd():
    """Find the visible Roblox game window, including titles with extra text."""
    if os.name != "nt" or user32 is None:
        return None
    hwnd = user32.FindWindowW(None, WINDOW_TITLE)
    if hwnd and user32.IsWindowVisible(hwnd):
        return hwnd
    found = []
    enum_cb_type = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def enum_cb(candidate, _):
        if user32.IsWindowVisible(candidate):
            length = user32.GetWindowTextLengthW(candidate)
            if length:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(candidate, buff, length + 1)
                if "roblox" in buff.value.lower():
                    found.append(candidate)
                    return False
        return True
    user32.EnumWindows(enum_cb_type(enum_cb), 0)
    return found[0] if found else None


def _roblox_is_foreground(hwnd):
    if not hwnd:
        return False
    fg = user32.GetForegroundWindow()
    return fg == hwnd or user32.GetAncestor(fg, 2) == hwnd


def mouse_click_and_zoom(ticks=50):
    """Click the center of the Roblox client and zoom only after it owns focus."""
    if os.name != "nt" or user32 is None:
        return False
    try:
        hwnd = _find_roblox_hwnd()
        if not hwnd:
            return False
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        # SetForegroundWindow can be denied by Windows; never send input to another app.
        for _ in range(20):
            if _roblox_is_foreground(hwnd):
                break
            time.sleep(0.05)
        if not _roblox_is_foreground(hwnd):
            return False

        rect = wintypes.RECT()
        if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
            return False
        point = wintypes.POINT((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2)
        if not user32.ClientToScreen(hwnd, ctypes.byref(point)):
            return False
        user32.SetCursorPos(point.x, point.y)
        time.sleep(0.08)
        # Click once to give the game mouse capture, then zoom fully in.
        user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.04)
        user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(0.12)
        ticks = max(1, min(60, int(ticks)))
        for _ in range(ticks):
            if not _roblox_is_foreground(hwnd):
                return False
            user32.mouse_event(0x0800, 0, 0, 120, 0)
            time.sleep(0.02)
        return True
    except Exception:
        return False

def mouse_wheel_up(ticks=32):
    """Send wheel-up input to the focused Roblox window."""
    if os.name != "nt" or user32 is None:
        return False
    ticks = max(1, min(60, int(ticks)))
    for _ in range(ticks):
        user32.mouse_event(0x0800, 0, 0, 120, 0)
        time.sleep(0.025)
    return True


def minus_pressed():
    # 0xBD = "-" on the main keyboard, 0x6D = "-" on the numpad
    return key_down(0xBD) or key_down(0x6D)


def pin_window(hwnd):
    # HWND_TOPMOST = -1; flags: SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
    user32.SetWindowPos(hwnd, wintypes.HWND(-1), 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)


def setup_debug_window(first_frame):
    """Opens the debug window in the top-left corner, pinned on top, without a close button."""
    cv2.namedWindow(DBG_WIN, cv2.WINDOW_AUTOSIZE)
    cv2.imshow(DBG_WIN, first_frame)
    cv2.waitKey(1)
    cv2.moveWindow(DBG_WIN, 0, 0)
    hwnd = user32.FindWindowW(None, DBG_WIN)
    if hwnd:
        menu = user32.GetSystemMenu(hwnd, False)
        if menu:
            user32.DeleteMenu(menu, 0xF060, 0)      # remove the close button (SC_CLOSE)
        pin_window(hwnd)
    return hwnd if hwnd else 0


def focus_roblox():
    """Bring Roblox to the foreground and verify that it actually received focus."""
    if os.name != "nt" or user32 is None:
        return False
    try:
        hwnd = _find_roblox_hwnd()
        if not hwnd:
            return False
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        for _ in range(30):
            if _roblox_is_foreground(hwnd):
                return True
            time.sleep(0.05)
        return False
    except Exception:
        return False

def get_roblox_region():
    """Screen rectangle of the Roblox window's client area, or None if it is not found."""
    hwnd = user32.FindWindowW(None, WINDOW_TITLE)
    if not hwnd or user32.IsIconic(hwnd):
        return None
    rc = wintypes.RECT()
    pt = wintypes.POINT(0, 0)
    user32.GetClientRect(hwnd, ctypes.byref(rc))
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    w, h = rc.right - rc.left, rc.bottom - rc.top
    if w < 200 or h < 200:
        return None
    return {"left": int(pt.x), "top": int(pt.y), "width": int(w), "height": int(h)}


# ============================== MASTERIES (PLUGINS) ==============================
def load_masteries_state():
    """Names of the plugin files the user has ticked (in the order they were ticked)."""
    try:
        with open(MASTERIES_STATE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [n for n in data.get("enabled", []) if isinstance(n, str)]
    except Exception:
        return []


def save_masteries_state(enabled):
    try:
        tmp = MASTERIES_STATE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"enabled": list(enabled)}, f, indent=2, ensure_ascii=False)
        os.replace(tmp, MASTERIES_STATE)
    except Exception:
        pass



def plugin_info(path):
    """Inspect plugin metadata without executing its Python code."""
    info = {
        "name": os.path.splitext(os.path.basename(path))[0],
        "description": "",
        "ok": False,
        "reason": "",
        "entry": "",
    }
    try:
        with open(path, "r", encoding="utf-8-sig") as file:
            tree = ast.parse(file.read(), filename=os.path.basename(path))

        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                key = node.targets[0].id
                if key in ("NAME", "DESCRIPTION"):
                    try:
                        info[key.lower()] = str(ast.literal_eval(node.value))
                    except Exception:
                        pass

        functions = {
            node.name: node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for candidate in ("run", "main", "start"):
            if candidate in functions:
                info["ok"] = True
                info["entry"] = candidate
                break

        if not info["ok"] and "setup" in functions:
            info["ok"] = True
            info["entry"] = "setup"
        if not info["ok"]:
            info["reason"] = "No supported entry point: define run(ctx), main(ctx), start(ctx), or setup(ctx)."
    except Exception as exc:
        info["reason"] = f"{type(exc).__name__}: {exc}"
        info["description"] = f"({type(exc).__name__})"
    return info




def load_plugin(path):
    path = os.path.abspath(path)
    root = os.path.abspath(MASTERIES_DIR)
    try:
        if os.path.commonpath([root, path]) != root:
            raise RuntimeError("plugin is outside the Masteries folder")
    except ValueError:
        raise RuntimeError("plugin is outside the Masteries folder")

    stem = re.sub(r"\W", "_", os.path.splitext(os.path.basename(path))[0])
    module_name = "bob_mastery_" + stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not create a Python module loader")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(module_name, None)
        raise

    if not any(callable(getattr(mod, name, None)) for name in ("run", "main", "start", "setup")):
        sys.modules.pop(module_name, None)
        raise RuntimeError("plugin must define run(ctx), main(ctx), start(ctx), or setup(ctx)")
    return mod



class PluginStop(Exception):
    """Raised inside a plugin when Stop / F8 is pressed. Plugins do not need to catch it."""


class PluginContext:
    """The `ctx` object a Masteries plugin receives.

    A plugin file may define (all optional, but at least one of setup / run):
      NAME = "..."   DESCRIPTION = "..."   RUN_ONCE = True/False
      def setup(ctx):  called ONCE when the bot starts (change settings, replace functions)
      def run(ctx):    ONE pass of the macro; called again and again until Stop

    Timing / control
      ctx.sleep(sec)                    wait (stops instantly on Stop / F8)
      ctx.wait_until(fn, timeout=10)    wait until fn() is true -> True, or False on timeout
      ctx.stopped                       True after Stop / F8
      ctx.log(text)                     write a line to the Live Console
    Settings (live, only for this run; the config file is not changed)
      ctx.get("key")                    read any setting, e.g. ctx.get("target_fps")
      ctx.set("key", value)             change any setting from the Settings tab, e.g.
                                        ctx.set("show_debug_window", False), ctx.set("debug_fps", 10),
                                        ctx.set("h_min", 100)  (what to detect), ctx.set("target_fps", 20) ...
      ctx.cfg                           the live settings dict (read it; change it with ctx.set)
    Replace / extend any function of the bot
      ctx.override(name, fn)            replace Engine method `name` (find_portal, press_e_and_reset,
                                        jump_tick, _draw_debug, press_key, ...). fn(original, *args, **kw)
                                        gets the original method first, so it can call it or ignore it.
                                        find_portal must return (det, mask, area, orange_frac) like the original.
      ctx.restore(name=None)            put back one replaced function (or all)
      ctx.engine                        the raw Engine object (full access)
    Keyboard / mouse
      ctx.press(key, hold=None)         tap a key, e.g. ctx.press("e")
      ctx.hold(key) / ctx.release(key)  hold / release a key (released automatically on Stop)
      ctx.walk(True/False)              hold / release W
      ctx.jump()                        tap SPACE
      ctx.turn(dx)                      turn the camera (+ = right, uses the mouse_sign setting)
      ctx.focus_game()                  bring Roblox to the front
    Screen / detection (all positions are 0..1 fractions of the game window)
      ctx.grab()                        BGR frame (numpy array) of the game window
      ctx.find_color(low_hsv, high_hsv, min_area=0.002)  -> {"x","y","w","h","area"} or None
      ctx.find_portal()                 the portal detector, same result format
    Actions
      ctx.reset_character()             Esc -> R -> Enter, then waits respawn_wait seconds
    """

    def __init__(self, eng):
        self._e = eng
        self._held = set()
        self._sct = None
        self.cfg = eng.c                 # live dict: the bot reads it every frame
        self.engine = eng
        self.name = ""
        self.plugin_settings = _safe_json_read(PLUGIN_SETTINGS_PATH, {})

    @property
    def settings(self):
        return self.plugin_settings

    def get_setting(self, key, default=None):
        return self.plugin_settings.get(self.name, {}).get(key, default)

    # ----- control -----
    def _chk(self):
        if self._e.stopping() or not self._e.wait_if_paused():
            raise PluginStop()

    @property
    def stopped(self):
        return self._e.stopping()

    def log(self, msg):
        self._e.emit("evt.plugin_log", name=self.name, msg=str(msg))

    def sleep(self, sec):
        if not self._e.sleep(sec):
            raise PluginStop()

    def wait_until(self, cond, timeout=10.0, step=0.05):
        end = time.time() + timeout
        while time.time() < end:
            self._chk()
            if cond():
                return True
            self.sleep(step)
        return False

    # ----- settings / replacing functions -----
    def get(self, key):
        return self._e.c[key]

    def set(self, key, value):
        spec = next((r for r in SCHEMA if r[1] == key), None)
        if spec is None:
            raise KeyError(f"unknown setting: {key}")
        _grp, _key, kind, _default, lo, hi = spec
        if kind == "int" and isinstance(value, float) and value.is_integer():
            value = int(value)
        try:
            self._e.c[key] = parse_value(kind, value, lo, hi)
        except FieldError as e:
            raise ValueError(f"bad value for {key}: {e.code} {e.kw}")
        self._e.refresh_settings()

    def override(self, name, fn):
        eng = self._e
        if name.startswith("__") or name in ("run", "_run", "_plugin_loop", "_start_plugins") or not callable(getattr(eng, name, None)):
            raise ValueError(f"cannot override '{name}'")
        orig = eng._orig.setdefault(name, getattr(eng, name))     # the first original is kept: no stacking
        setattr(eng, name, lambda *a, **k: fn(orig, *a, **k))

    def restore(self, name=None):
        eng = self._e
        for n in ([name] if name else list(eng._orig)):
            if n in eng._orig:
                try:
                    delattr(eng, n)                                # falls back to the class method
                except AttributeError:
                    pass
                eng._orig.pop(n, None)

    # ----- keyboard / mouse -----
    def press(self, key, hold=None):
        self._chk()
        self._e.press_key(key, hold)
        self._chk()

    def hold(self, key):
        self._chk()
        pdi.keyDown(key)
        self._held.add(key)

    def release(self, key):
        pdi.keyUp(key)
        self._held.discard(key)

    def release_all(self):
        for k in list(self._held):
            try:
                pdi.keyUp(k)
            except Exception:
                pass
        self._held.clear()

    def walk(self, on=True):
        (self.hold if on else self.release)("w")

    def jump(self):
        self.press("space", self._e.c["jump_hold"])

    def turn(self, dx):
        self._chk()
        mouse_move(dx * self._e.c["mouse_sign"])

    def focus_game(self):
        focus_roblox()

    # ----- screen -----
    def grab(self):
        self._chk()
        mon, _ = self._e.pick_region(self._sct)
        return np.ascontiguousarray(np.array(self._sct.grab(mon))[:, :, :3])

    def _small(self, img):
        pw = min(self._e.c["proc_width"], img.shape[1])
        if pw == img.shape[1]:
            return img
        return cv2.resize(img, (pw, int(img.shape[0] * pw / img.shape[1])), interpolation=cv2.INTER_AREA)

    def find_color(self, low_hsv, high_hsv, min_area=0.002, frame=None):
        small = self._small(self.grab() if frame is None else frame)
        H, W = small.shape[:2]
        mask = cv2.inRange(cv2.cvtColor(small, cv2.COLOR_BGR2HSV),
                           np.array(low_hsv, np.uint8), np.array(high_hsv, np.uint8))
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best = max(cnts, key=cv2.contourArea, default=None)
        if best is None or cv2.contourArea(best) < min_area * W * H:
            return None
        x, y, w, h = cv2.boundingRect(best)
        return {"x": (x + w / 2) / W, "y": (y + h / 2) / H, "w": w / W, "h": h / H,
                "area": cv2.contourArea(best) / (W * H)}

    def find_portal(self, frame=None):
        small = self._small(self.grab() if frame is None else frame)
        H, W = small.shape[:2]
        det, _mask, area, _orange = self._e.find_portal(small)
        if det is None:
            return None
        cx, cy, w, h = det[:4]
        return {"x": cx / W, "y": cy / H, "w": w / W, "h": h / H, "area": area / (W * H)}

    # ----- actions -----
    def reset_character(self):
        for k in ("esc", "r"):
            self.press(k)
            self.sleep(0.15)
        self.press("enter")
        if self.sleep(self._e.c["respawn_wait"]):
            self._e.ensure_first_person()


# ============================== THE FARM ENGINE ==============================
class Engine:
    """Runs in a background thread. Talks to the window through emit() (log events)
    and set_preview() (PNG bytes of the debug picture)."""

    def __init__(self, cfg, emit, set_preview, stop_event, plugins=None):
        self.c = cfg
        self.plugins = list(plugins or [])
        self.plugin_thread = None
        self._orig = {}                 # functions replaced by plugins
        self.plugin_pass_end = 0.0      # time when a plugin last finished one run(ctx)
        self.emit = emit
        self.set_preview = set_preview
        self.stop = stop_event
        self.pause_event = cfg.get("_pause_event")
        self.low = np.array((cfg["h_min"], cfg["s_min"], cfg["v_min"]), np.uint8)
        self.high = np.array((cfg["h_max"], cfg["s_max"], cfg["v_max"]), np.uint8)
        self.zones = parse_zones(cfg["ignore_zones"])
        self.k3 = np.ones((3, 3), np.uint8)
        self.k7 = np.ones((7, 7), np.uint8)
        self.jump = {"down": False, "t": 0.0, "last": 0.0}
        self.walking = False
        self.plugin_trigger = threading.Event()
        self.plugin_ready = threading.Event()
        self.plugin_cycle_done = threading.Event()
        self.plugin_cycle_lock = threading.Lock()
        self.plugin_busy = threading.Event()
        self.plugin_last_error = ""

    # ---------- helpers ----------
    def refresh_settings(self):
        """Re-reads the settings that are cached (colour range, ignored zones). Called after ctx.set()."""
        c = self.c
        self.low = np.array((c["h_min"], c["s_min"], c["v_min"]), np.uint8)
        self.high = np.array((c["h_max"], c["s_max"], c["v_max"]), np.uint8)
        self.zones = parse_zones(c["ignore_zones"])

    def stopping(self):
        if key_down(STOP_KEY_VK):
            self.stop.set()
        return self.stop.is_set()

    def wait_if_paused(self):
        """Freeze farm actions during a Roblox disconnect without ending the engine."""
        if self.pause_event is None:
            return not self.stopping()
        if self.pause_event.is_set():
            self.release_jump()
            self.release_walk()
            try:
                plugin_ctx = getattr(self, "plugin_ctx", None)
                if plugin_ctx is not None:
                    plugin_ctx.release_all()
            except Exception:
                pass
            for key in ("w", "space", "e", "esc", "r", "enter"):
                try:
                    pdi.keyUp(key)
                except Exception:
                    pass
        while self.pause_event.is_set() and not self.stopping():
            time.sleep(0.1)
        return not self.stopping()

    def sleep(self, sec):
        """Sleep that wakes up on Stop / F8 and remains frozen during reconnect."""
        end = time.time() + sec
        while time.time() < end:
            if self.stopping() or not self.wait_if_paused():
                return False
            time.sleep(min(0.05, max(0.0, end - time.time())))
        return not self.stopping()

    def press_key(self, k, hold=None):
        pdi.keyDown(k)
        self.sleep(self.c["key_hold"] if hold is None else hold)
        pdi.keyUp(k)

    def jump_tick(self, active):
        """Non-blocking jumping: press SPACE every jump_interval while `active`."""
        now = time.time()
        if self.jump["down"] and now - self.jump["t"] >= self.c["jump_hold"]:
            pdi.keyUp("space")
            self.jump["down"] = False
        if active and not self.jump["down"] and now - self.jump["last"] >= self.c["jump_interval"]:
            pdi.keyDown("space")
            self.jump.update(down=True, t=now, last=now)

    def release_jump(self):
        if self.jump["down"]:
            pdi.keyUp("space")
            self.jump["down"] = False

    def release_walk(self):
        if self.walking:
            pdi.keyUp("w")
            self.walking = False

    def ensure_first_person(self):
        """Wait for Roblox to become the foreground window, then click and zoom."""
        if not self.c.get("first_person_on_spawn", True) or self.stopping():
            return
        try:
            # Roblox may still be loading or Windows may delay foreground activation.
            # Retry for up to 30 seconds, but never send mouse input to another window.
            deadline = time.time() + 30.0
            while time.time() < deadline and not self.stopping():
                if focus_roblox():
                    if mouse_click_and_zoom(50):
                        self.emit("evt.first_person")
                        return
                if not self.sleep(1.0):
                    return
            self.emit("evt.warning", msg="Roblox window did not accept focus; first-person zoom skipped.")
        except Exception as e:
            self.emit("evt.warning", msg=f"First-person zoom: {type(e).__name__}: {e}")

    def press_e_and_reset(self, w_down):
        c = self.c
        self.release_jump()
        if w_down:
            self.release_walk()
        if not self.sleep(c["e_delay"]):
            return
        if c["feat_press_e"]:
            self.press_key("e")
        if not self.sleep(c["reset_delay"]):
            return
        if c["feat_reset"]:
            for k in ("esc", "r"):
                self.press_key(k)
                if not self.sleep(0.15):
                    return
            self.press_key("enter")
            if self.sleep(c["respawn_wait"]):
                self.ensure_first_person()

    def pick_region(self, sct):
        if self.c["capture_window"]:
            r = get_roblox_region()
            if r:
                return r, True
        return sct.monitors[1], False

    # ---------- portal detection ----------
    def find_portal(self, small, prefer=None):
        """Returns (det, mask, area, orange_frac). det = (cx, cy, w, h, contour) or None."""
        c = self.c
        H, W = small.shape[:2]
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.low, self.high)
        for (zx0, zy0, zx1, zy1) in self.zones:
            mask[int(zy0 * H):int(zy1 * H), int(zx0 * W):int(zx1 * W)] = 0
        orange_frac = float(np.count_nonzero(mask)) / (W * H)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.k3)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.k7)

        hh, ss, vv = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
        red = (((hh <= 10) | (hh >= 170)) & (ss >= 180) & (vv >= 200)).astype(np.uint8)

        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cands = []
        for cnt in cnts:
            area = cv2.contourArea(cnt)
            if area < c["min_area_frac"] * W * H or area > c["max_area_frac"] * W * H:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            if w < 4 or h < 4 or area / (w * h) < c["min_fill"]:
                continue
            hull = cv2.contourArea(cv2.convexHull(cnt))
            if hull <= 0 or area / hull < c["min_solidity"]:
                continue
            if not (c["ar_min"] <= w / h <= c["ar_max"]):
                continue
            if np.count_nonzero(red[y:y + h, x:x + w]) / float(w * h) > c["max_red_frac"]:
                continue
            cands.append((x + w / 2, y + h / 2, float(w), float(h), cnt, area))
        if not cands:
            return None, mask, 0, orange_frac
        best = None
        if prefer is not None:
            near = [t for t in cands if abs(t[0] - prefer[0]) < 0.25 * W and abs(t[1] - prefer[1]) < 0.30 * H]
            if near:
                best = min(near, key=lambda t: abs(t[0] - prefer[0]) + abs(t[1] - prefer[1]))
        if best is None:
            best = max(cands, key=lambda t: t[5])
        return best[:5], mask, best[5], orange_frac

    # ---------- Masteries plugins ----------
    def _start_plugins(self):
        if self.plugins:
            self.plugin_thread = threading.Thread(target=self._plugin_loop, daemon=True)
            self.plugin_thread.start()


    def _call_plugin_function(self, fn, ctx):
        """Call a supported plugin function with ctx when it accepts an argument."""
        try:
            signature = inspect.signature(fn)
            positional = [
                p for p in signature.parameters.values()
                if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            accepts_args = bool(positional) or any(
                p.kind == inspect.Parameter.VAR_POSITIONAL
                for p in signature.parameters.values()
            )
        except (TypeError, ValueError):
            accepts_args = True

        result = fn(ctx) if accepts_args else fn()
        if inspect.isawaitable(result):
            return asyncio.run(result)
        return result

    def _plugin_loop(self):
        """Load plugins once; run one plugin pass per portal, or continuously in plugin-only mode."""
        mods = []
        ctx = PluginContext(self)
        self.plugin_ctx = ctx
        try:
            for path in self.plugins:
                filename = os.path.basename(path)
                try:
                    mod = load_plugin(path)
                    mods.append((filename, mod))
                    self.emit("evt.plugin_start", name=getattr(mod, "NAME", filename))
                except Exception as exc:
                    self.plugin_last_error = f"{type(exc).__name__}: {exc}"
                    self.emit("evt.plugin_error", name=filename, err=self.plugin_last_error)

            if not mods:
                self.emit("evt.plugins_none")
                return

            with mss.mss() as sct:
                ctx._sct = sct

                # setup(ctx) is initialization only; it is not treated as the repeated run pass.
                for item in list(mods):
                    filename, mod = item
                    ctx.name = str(getattr(mod, "NAME", filename))
                    setup_fn = getattr(mod, "setup", None)
                    if callable(setup_fn):
                        try:
                            self._call_plugin_function(setup_fn, ctx)
                        except PluginStop:
                            return
                        except Exception as exc:
                            self.plugin_last_error = f"{type(exc).__name__}: {exc}"
                            self.emit("evt.plugin_error", name=filename, err=self.plugin_last_error)
                            mods.remove(item)
                            continue
                    if not any(callable(getattr(mod, entry_name, None)) for entry_name in ("run", "main", "start")):
                        mods.remove(item)  # setup-only plugin: initialization has completed

                self.plugin_ready.set()
                if not mods:
                    return

                # If the built-in farm is enabled, wait until the portal has been entered.
                # If it is disabled, plugins run by themselves in a loop.
                while mods and not self.stopping():
                    if self.c.get("builtin_farm", True):
                        if not self.plugin_trigger.wait(0.1):
                            continue
                        self.plugin_trigger.clear()
                        self.plugin_cycle_done.clear()

                    self.plugin_busy.set()
                    for item in list(mods):
                        filename, mod = item
                        if self.stopping():
                            break
                        ctx.name = str(getattr(mod, "NAME", filename))
                        entry = next(
                            (getattr(mod, name, None) for name in ("run", "main", "start")
                             if callable(getattr(mod, name, None))),
                            None
                        )
                        try:
                            if entry is not None:
                                self._call_plugin_function(entry, ctx)
                                self.plugin_pass_end = time.time()
                                self.emit("evt.plugin_cycle", name=ctx.name)
                            elif callable(getattr(mod, "setup", None)):
                                # setup-only plugins are allowed, but only initialize once.
                                self.plugin_pass_end = time.time()
                        except PluginStop:
                            break
                        except Exception as exc:
                            self.plugin_last_error = f"{type(exc).__name__}: {exc}"
                            self.emit("evt.plugin_error", name=filename, err=self.plugin_last_error)
                            mods.remove(item)
                            ctx.release_all()
                            continue

                        if getattr(mod, "RUN_ONCE", False):
                            mods.remove(item)

                    self.plugin_busy.clear()
                    if self.c.get("builtin_farm", True):
                        self.plugin_cycle_done.set()
                    elif mods:
                        if not self.sleep(0.05):
                            break

        except Exception as exc:
            self.plugin_last_error = f"{type(exc).__name__}: {exc}"
            self.emit("evt.error", err=self.plugin_last_error)
        finally:
            self.plugin_busy.clear()
            self.plugin_ready.set()
            self.plugin_cycle_done.set()
            ctx.release_all()

    def trigger_plugins_and_wait(self, timeout=PLUGIN_WAIT_MAX):
        """Trigger plugins without blocking the capture/debug loop."""
        if self.plugin_thread is None or not self.plugin_thread.is_alive():
            return
        if not self.plugin_ready.wait(timeout=2):
            self.emit("evt.plugin_error", name="Masteries", err="Plugin loader is still initializing; it will run on the next portal.")
            return
        if not self.plugin_thread.is_alive():
            return
        self.plugin_cycle_done.clear()
        self.plugin_trigger.set()

    def _run_idle(self):
        """Built-in farm is off: only the plugins work. Ends when they all finished or on Stop."""
        self.emit("evt.starting", sec=START_DELAY)
        if not self.sleep(START_DELAY):
            return
        with mss.mss() as sct:
            mon, is_window = self.pick_region(sct)
        if is_window:
            self.emit("evt.capture_window", w=mon["width"], h=mon["height"], l=mon["left"], t=mon["top"])
        else:
            self.emit("evt.capture_monitor", w=mon["width"], h=mon["height"])
        while not self.stopping():
            if self.plugin_thread is None or not self.plugin_thread.is_alive():
                break
            time.sleep(0.1)

    # ---------- thread entry ----------
    def run(self):
        try:
            self._start_plugins()
            if self.c["builtin_farm"]:
                self._run()
            else:
                self._run_idle()
        except Exception as e:
            self.emit("evt.error", err=f"{type(e).__name__}: {e}")
        finally:
            self.stop.set()                                  # also stops the plugin thread
            if self.plugin_thread is not None:
                self.plugin_thread.join(timeout=5)
            try:
                self.release_jump()
                self.release_walk()
            except Exception:
                pass
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
            self.emit("evt.stopped")

    def _run(self):
        c = self.c
        self.emit("evt.starting", sec=START_DELAY)
        if not self.sleep(START_DELAY):
            return
        # Apply the same camera zoom on the first spawn as after later resets.
        self.ensure_first_person()
        frame_time = 1.0 / c["target_fps"]

        seen, max_ratio, peak_orange = False, 0.0, 0.0
        lost, lost_t = 0, time.time()
        hits, prev_c, lock_pos = 0, None, None
        search_start = time.time()
        last_preview, frame_i, last_dbg = 0.0, 0, 0.0
        debug_on = c["show_debug_window"]
        dbg_cfg = debug_on
        dbg_hwnd, minus_prev, last_pin = None, False, 0.0
        miss, cand_frames = 0, 0           # frames without / with a portal candidate in a row
        state, shown_state, shown_t = "", "", 0.0
        onoff = lambda b: "ON" if b else "OFF"

        with mss.mss() as sct:
            mon, is_window = self.pick_region(sct)
            if is_window:
                self.emit("evt.capture_window", w=mon["width"], h=mon["height"], l=mon["left"], t=mon["top"])
            else:
                self.emit("evt.capture_monitor", w=mon["width"], h=mon["height"])
            self.emit("evt.settings", jump=onoff(c["search_jump"]), spin=onoff(c["search_spin"]),
                      speed=c["search_speed"], jww=onoff(c["jump_while_walking"]))

            while not self.stopping():
                if not self.wait_if_paused():
                    break
                t0 = time.time()
                if frame_i % 60 == 0 and frame_i > 0:          # re-check the window position every ~2 s
                    new_mon, new_is_window = self.pick_region(sct)
                    key = lambda m: (m["left"], m["top"], m["width"], m["height"])
                    if key(new_mon) != key(mon):
                        mon = new_mon
                        self.emit("evt.capture_changed", w=mon["width"], h=mon["height"], l=mon["left"], t=mon["top"])
                frame_i += 1

                img = np.ascontiguousarray(np.array(sct.grab(mon))[:, :, :3])
                if debug_on:                    # black out the area under the debug window (no self-detection)
                    dh = int(DBG_W * img.shape[0] / img.shape[1]) + 60
                    bx, by = max(0, DBG_W + 20 - mon["left"]), max(0, dh - mon["top"])
                    if bx > 0 and by > 0:
                        img[0:by, 0:bx] = 0
                pw = min(c["proc_width"], img.shape[1])
                small = cv2.resize(img, (pw, int(img.shape[0] * pw / img.shape[1])),
                                   interpolation=cv2.INTER_AREA) if pw != img.shape[1] else img
                H, W = small.shape[:2]

                # stay on the SAME blob frame after frame: the locked portal, or else the last candidate
                det, mask, area, orange_frac = self.find_portal(small, lock_pos or prev_c)

                if det:
                    cand_frames += 1
                    miss = 0
                    if prev_c is not None and abs(det[0] - prev_c[0]) < 0.2 * W and abs(det[1] - prev_c[1]) < 0.25 * H:
                        hits += 1
                    else:
                        hits = 1
                    prev_c = (det[0], det[1])
                else:
                    cand_frames = 0
                    miss += 1
                    hits = max(0, hits - 1)              # a flicker lowers the count instead of wiping it
                    if miss > 4:
                        hits, prev_c = 0, None
                # confirmed after a few frames on the same blob; a steady candidate is accepted after ~20 frames
                confirmed = det is not None and (hits >= c["confirm_frames"] or cand_frames >= 20)
                if seen:
                    peak_orange = max(peak_orange, orange_frac)

                # ---------- debug picture: pinned debug window + preview inside this window ----------
                if c["show_debug_window"] != dbg_cfg:               # a plugin / setting turned the debug window on or off
                    dbg_cfg = c["show_debug_window"]
                    debug_on = dbg_cfg
                    if not dbg_cfg:
                        try:
                            cv2.destroyAllWindows()
                        except Exception:
                            pass
                        dbg_hwnd = None
                want_preview = c["show_preview"] and time.time() - last_preview > 0.15
                dbg_due = debug_on and time.time() - last_dbg >= 1.0 / c["debug_fps"]
                if dbg_due or want_preview:
                    dbg = self._draw_debug(small, mask, det, confirmed, hits, orange_frac, W, H, state)
                    view = cv2.resize(dbg, (DBG_W, int(DBG_W * H / W)))
                    if dbg_due:
                        last_dbg = time.time()
                        if dbg_hwnd is None:
                            dbg_hwnd = setup_debug_window(view)
                            focus_roblox()                  # the new window must not take the focus from the game
                            # Re-apply first-person after the debug window is created.
                            # The wheel events are sent only after Roblox is focused.
                            self.ensure_first_person()
                        cv2.imshow(DBG_WIN, view)
                        cv2.waitKey(1)
                        if cv2.getWindowProperty(DBG_WIN, cv2.WND_PROP_VISIBLE) < 1:
                            dbg_hwnd = None                 # closed some other way -> recreate it
                        if dbg_hwnd and time.time() - last_pin > 2:
                            pin_window(dbg_hwnd)            # keep it on top
                            last_pin = time.time()
                    if want_preview:
                        last_preview = time.time()
                        ok, buf = cv2.imencode(".png", view)
                        if ok:
                            self.set_preview(buf.tobytes())

                # the "-" key closes the debug window
                mp = bool(minus_pressed())
                if mp and not minus_prev and debug_on:
                    debug_on = False
                    cv2.destroyAllWindows()
                    self.emit("evt.debug_closed")
                minus_prev = mp

                # ---------- logic ----------
                # A plugin pass may take a while. Keep capturing/updating the debug view,
                # but do not let the built-in farm fight the plugin for keyboard/mouse.
                if self.plugin_busy.is_set():
                    self.release_jump()
                    self.release_walk()
                    state = "PLUGIN"
                    if state != shown_state and time.time() - shown_t > 0.4:
                        shown_state, shown_t = state, time.time()
                        self.emit("evt.state.PLUGIN")
                    time.sleep(max(0.0, 1.0 / c["target_fps"] - (time.time() - t0)))
                    continue
                jump_active = False
                if confirmed:
                    cx, cy, w, h = det[:4]
                    seen, lost, lock_pos = True, 0, (cx, cy)
                    max_ratio = max(max_ratio, h / H)
                    search_start = time.time()
                    state = "WALK"

                    offset = (cx - W / 2) / W
                    if c["feat_aim"] and abs(offset) > c["deadzone"]:
                        step = max(-c["mouse_max_step"], min(c["mouse_max_step"], offset * c["mouse_gain"]))
                        mouse_move(step * c["mouse_sign"])
                    if c["feat_walk"] and abs(offset) <= c["walk_angle"]:   # walk straight to the portal
                        if not self.walking:
                            pdi.keyDown("w")
                            self.walking = True
                    else:
                        self.release_walk()

                    jump_active = c["jump_while_walking"]      # off by default: walk normally once found

                elif det is not None and not seen:
                    self.release_walk()
                    search_start = time.time()
                    jump_active = c["search_jump"]
                    state = "CANDIDATE"

                else:
                    lost += 1
                    if lost == 1:
                        lost_t = time.time()
                    if seen and lost >= c["lost_frames"]:
                        was_close = max_ratio >= c["enter_min_ratio"] or peak_orange >= c["enter_orange_frac"]
                        if not was_close:
                            self.release_walk()
                            seen, max_ratio, peak_orange, lost = False, 0.0, 0.0, 0
                            hits, prev_c, lock_pos = 0, None, None
                            search_start = time.time()
                        else:
                            jump_active = c["jump_while_walking"]
                            state = "ENTER"
                            gone = orange_frac < c["orange_gone_frac"]
                            waited = time.time() - lost_t > c["enter_wait_max"]
                            if gone or waited:                     # teleported -> we are inside
                                self.emit("evt.entered", e=c["e_delay"], r=c["reset_delay"])
                                self.press_e_and_reset(self.walking)
                                self.trigger_plugins_and_wait()    # run enabled plugins after entering the portal
                                seen, max_ratio, peak_orange, lost = False, 0.0, 0.0, 0
                                hits, prev_c, lock_pos = 0, None, None
                                search_start = time.time()
                                jump_active = False
                    elif seen:
                        jump_active = c["jump_while_walking"]
                    else:
                        self.release_walk()
                        jump_active = c["search_jump"]            # jump (and turn) until the portal is found
                        state = "SEARCH"
                        if c["search_spin"]:
                            mouse_move(c["search_speed"] * c["mouse_sign"])
                        if c["search_fail_e"] and time.time() - search_start > c["search_timeout"]:
                            self.emit("evt.noportal")
                            self.press_e_and_reset(False)
                            search_start = time.time()
                            jump_active = False

                self.jump_tick(jump_active)
                if state and state != shown_state and time.time() - shown_t > 0.4:
                    shown_state, shown_t = state, time.time()
                    self.emit(f"evt.state.{state}")
                time.sleep(max(0.0, 1.0 / c["target_fps"] - (time.time() - t0)))

    def _draw_debug(self, small, mask, det, confirmed, hits, orange_frac, W, H, state=""):
        """Draws the debug picture (portal box, centre line, ignored zones, colour mask thumbnail)."""
        dbg = small.copy()
        ctr = (W // 2, H // 2)
        cv2.line(dbg, (W // 2, 0), (W // 2, H), (0, 0, 255), 1)       # screen centre
        cv2.circle(dbg, ctr, 5, (0, 0, 255), -1)
        if det:
            col = (0, 255, 0) if confirmed else (0, 165, 255)
            cx, cy, w, h = det[:4]
            cv2.rectangle(dbg, (int(cx - w / 2), int(cy - h / 2)), (int(cx + w / 2), int(cy + h / 2)), col, 3)
            cv2.line(dbg, ctr, (int(cx), int(cy)), col, 2)
            cv2.drawContours(dbg, [det[4]], -1, (255, 0, 255), 1)
        for (zx0, zy0, zx1, zy1) in self.zones:
            cv2.rectangle(dbg, (int(zx0 * W), int(zy0 * H)), (int(zx1 * W) - 1, int(zy1 * H)), (128, 128, 128), 1)
        status = "CONFIRMED" if confirmed else ("candidate" if det else "none")
        cv2.putText(dbg, f"{state} {status} hits={hits} or={orange_frac:.2f}", (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        tw = W // 3
        th = int(tw * H / W)
        thumb = cv2.cvtColor(cv2.resize(mask, (tw, th)), cv2.COLOR_GRAY2BGR)
        dbg[H - th:H, W - tw:W] = thumb
        cv2.rectangle(dbg, (W - tw, H - th), (W - 1, H - 1), (255, 255, 255), 1)
        return dbg


# ============================== THE WINDOW ==============================
BG, PANEL, CARD, BORDER = "#12141a", "#181b23", "#1f232d", "#2c3240"
TEXT_C, MUTED, ACCENT, ACCENT_D = "#e9ecf4", "#8d95a8", "#ff8a1f", "#e5700a"
GREEN, RED, ENTRY_BG = "#3ecf8e", "#ff5d6c", "#14171f"

# Built-in themes. Custom themes can be included in any config JSON under the "theme" key.
THEMES = {
    "Midnight Orange": {"bg":"#12141a","panel":"#181b23","card":"#1f232d","border":"#2c3240","text":"#e9ecf4","muted":"#8d95a8","accent":"#ff8a1f","accent_dark":"#e5700a","entry":"#14171f"},
    "Ocean Blue": {"bg":"#0b1420","panel":"#102235","card":"#163047","border":"#24506a","text":"#e5f5ff","muted":"#91b5c9","accent":"#28b8ff","accent_dark":"#1389c4","entry":"#0c1d2b"},
    "Purple Haze": {"bg":"#171020","panel":"#21152f","card":"#2c1d40","border":"#49305f","text":"#f4eaff","muted":"#b9a2cc","accent":"#bd79ff","accent_dark":"#9254d1","entry":"#1d1428"},
    "Crimson": {"bg":"#1b1014","panel":"#29151c","card":"#381c26","border":"#63303e","text":"#ffeef1","muted":"#c49aa5","accent":"#ff4968","accent_dark":"#d52d4b","entry":"#211319"},
    "Emerald": {"bg":"#0d1915","panel":"#14251e","card":"#1b3329","border":"#315b48","text":"#e8fff3","muted":"#9bbdab","accent":"#35d69a","accent_dark":"#1ca978","entry":"#102019"},
    "Gold": {"bg":"#19160d","panel":"#282212","card":"#393019","border":"#62512a","text":"#fff8e5","muted":"#c6b98f","accent":"#ffc94a","accent_dark":"#d99d20","entry":"#211b0e"},
    "Rose": {"bg":"#1c1118","panel":"#2a1823","card":"#3a2130","border":"#634056","text":"#fff0f7","muted":"#c8a4b7","accent":"#ff83bd","accent_dark":"#d85b98","entry":"#24151e"},
    "Cyberpunk": {"bg":"#100f1d","panel":"#19172b","card":"#24213d","border":"#45406f","text":"#f4f0ff","muted":"#aaa4d1","accent":"#e84dff","accent_dark":"#b52bd0","entry":"#171426"},
    "Arctic": {"bg":"#eaf2f7","panel":"#dce8f0","card":"#ffffff","border":"#b9cbd8","text":"#182b38","muted":"#607887","accent":"#168bc4","accent_dark":"#096b9b","entry":"#f5f9fc"},
    "Paper": {"bg":"#f1eee7","panel":"#e5e0d5","card":"#fffdf7","border":"#c9c1b1","text":"#29261f","muted":"#777064","accent":"#d56b27","accent_dark":"#a94d16","entry":"#fffaf0"},
    "Forest": {"bg":"#101812","panel":"#19251b","card":"#233326","border":"#405b43","text":"#eff8ed","muted":"#a8b9a4","accent":"#a6d65c","accent_dark":"#7ca638","entry":"#172119"},
    "Neon Mint": {"bg":"#0c1718","panel":"#102526","card":"#163334","border":"#28605c","text":"#eafffc","muted":"#91c4be","accent":"#46f0cf","accent_dark":"#21bda4","entry":"#102021"},
    "Slate": {"bg":"#171a1f","panel":"#20252c","card":"#2a3039","border":"#414b58","text":"#edf1f5","muted":"#a2adba","accent":"#9db4ce","accent_dark":"#718ba8","entry":"#1b2027"},
    "Sunset": {"bg":"#1b1218","panel":"#2b1a20","card":"#3a2428","border":"#68403b","text":"#fff1e8","muted":"#c7a69a","accent":"#ff9b59","accent_dark":"#df6d39","entry":"#24171b"},
}
THEME_KEYS = ("bg", "panel", "card", "border", "text", "muted", "accent", "accent_dark", "entry")
FONT, FONT_B, FONT_S = ("Segoe UI", 10), ("Segoe UI Semibold", 10), ("Segoe UI", 9)


class App:
    def __init__(self, root, cfg, lang):
        self.root, self.cfg, self.lang = root, cfg, lang
        self._server_list_cache = []
        self._server_list_cache_at = 0.0
        self._server_page_cache = {}
        self._server_api_last_request_at = 0.0
        self._server_api_cooldown_until = 0.0
        self._server_api_lock = threading.Lock()
        self.q = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = None
        self.engine_instance = None
        self.running = False
        self.pending_png = None
        self.has_preview = False
        self.photo = None
        self.session_started = None
        self.session_finished = None
        self.session_portals = 0
        self.session_noportal = 0
        self.session_errors = 0
        self.last_event_text = self.t("dash.waiting")
        self.log_line_count = 0
        self.log_limit = 300
        self.event_history = []          # lightweight report data, capped at 500 events
        self.telegram_thread = None
        self.telegram_stop = threading.Event()
        self.telegram_offset = 0
        self.server_hop_after_id = None
        self.server_hop_enabled = False
        self.server_hop_minutes = tk.StringVar(value="5")
        self.server_hop_auto_var = tk.BooleanVar(value=False)
        self.server_hop_busy = threading.Event()
        self._last_server_id = None
        self.masteries_enabled = load_masteries_state()
        self.masteries_vars = {}
        self.masteries_texts = []
        self.telegram_features = self.load_telegram_features()
        self.telegram_feature_vars = {}
        self.telegram_cfg = self.load_telegram_config()
        self.telegram_access = self.load_telegram_access()
        self._last_dash_refresh = 0.0
        self.i18n = []              # (widget, key, option, kind)
        self.fields = {}            # key -> dict(kind, get, set, widget)
        self.sysinfo = get_system_info()
        self.theme_name, self.theme_colors = self.load_theme()
        global BG, PANEL, CARD, BORDER, TEXT_C, MUTED, ACCENT, ACCENT_D, ENTRY_BG
        BG, PANEL, CARD, BORDER = (self.theme_colors[k] for k in ("bg", "panel", "card", "border"))
        TEXT_C, MUTED, ACCENT, ACCENT_D, ENTRY_BG = (self.theme_colors[k] for k in ("text", "muted", "accent", "accent_dark", "entry"))
        self.theme_color_map = {}

        root.title("BOB Farm V2")
        root.configure(bg=BG)
        root.geometry("1240x800")
        root.minsize(1060, 700)
        self.setup_style()
        self.build_header()
        self.build_body()
        self.apply_language()
        self.exclude_from_capture()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.after(100, self.poll)
        if self.telegram_cfg.get("auto_start"):
            root.after(1200, self._auto_start_telegram)

    # ---------- small helpers ----------
    def t(self, key, **kw):
        return tr(self.lang, key, **kw)

    def reg(self, widget, key, option="text", fmt=None):
        self.i18n.append((widget, key, option, fmt))
        return widget

    def setup_style(self):
        st = ttk.Style(self.root)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure(".", background=BG, foreground=TEXT_C, font=FONT)
        st.configure("TNotebook", background=BG, borderwidth=0)
        st.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(20, 9), borderwidth=0, font=FONT_B)
        st.map("TNotebook.Tab", background=[("selected", CARD)], foreground=[("selected", ACCENT)])
        st.configure("Dark.TCheckbutton", background=CARD, foreground=TEXT_C, focuscolor=CARD, font=FONT)
        st.map("Dark.TCheckbutton", background=[("active", CARD)],
               indicatorcolor=[("selected", ACCENT), ("!selected", ENTRY_BG)])
        st.configure("TCombobox", fieldbackground=ENTRY_BG, background=PANEL, foreground=TEXT_C,
                     arrowcolor=ACCENT, bordercolor=BORDER, lightcolor=ENTRY_BG, darkcolor=ENTRY_BG)
        st.map("TCombobox", fieldbackground=[("readonly", ENTRY_BG)], foreground=[("readonly", TEXT_C)],
               selectbackground=[("readonly", ENTRY_BG)], selectforeground=[("readonly", TEXT_C)])
        st.configure("Vertical.TScrollbar", background=BORDER, troughcolor=BG, bordercolor=BG,
                     arrowcolor=MUTED, lightcolor=BORDER, darkcolor=BORDER)
        self.root.option_add("*TCombobox*Listbox.background", ENTRY_BG)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT_C)
        self.root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#000000")

    def button(self, parent, key, command, accent=False):
        bg, fg = (ACCENT, "#1a1205") if accent else (CARD, TEXT_C)
        hover = ACCENT_D if accent else BORDER
        b = tk.Button(parent, bg=bg, fg=fg, activebackground=hover, activeforeground=fg, disabledforeground=MUTED,
                      relief="flat", bd=0, font=FONT_B, padx=18, pady=9, cursor="hand2", command=command,
                      highlightthickness=0)
        b._colors = (bg, fg, hover)

        def enter(_e):
            if str(b.cget("state")) == "normal":
                b.configure(bg=b._colors[2])

        def leave(_e):
            if str(b.cget("state")) == "normal":
                b.configure(bg=b._colors[0])
        b.bind("<Enter>", enter)
        b.bind("<Leave>", leave)
        self.reg(b, key)
        return b

    def set_enabled(self, b, enabled):
        bg, fg, _hover = b._colors
        if enabled:
            b.configure(state="normal", bg=bg, fg=fg, cursor="hand2")
        else:
            b.configure(state="disabled", bg=CARD, fg=MUTED, cursor="arrow")

    def make_scrollable(self, parent):
        wrap = tk.Frame(parent, bg=BG)
        canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def wheel(e):
            canvas.yview_scroll(int(-e.delta / 120), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        return wrap, inner

    def card(self, parent, title_key):
        outer = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        head = tk.Frame(outer, bg=CARD)
        head.pack(fill="x", padx=16, pady=(14, 6))
        tk.Frame(head, bg=ACCENT, width=4, height=18).pack(side="left", padx=(0, 10))
        self.reg(tk.Label(head, bg=CARD, fg=TEXT_C, font=("Segoe UI Semibold", 12)), title_key).pack(side="left")
        body = tk.Frame(outer, bg=CARD)
        body.pack(fill="x", padx=16, pady=(0, 14))
        return outer, body

    # ---------- header ----------
    def build_header(self):
        h = tk.Frame(self.root, bg=BG)
        h.pack(fill="x", padx=22, pady=(18, 8))
        tk.Frame(h, bg=ACCENT, width=6, height=46).pack(side="left", padx=(0, 14))
        titles = tk.Frame(h, bg=BG)
        titles.pack(side="left")
        self.reg(tk.Label(titles, bg=BG, fg=TEXT_C, font=("Segoe UI Semibold", 22)), "title").pack(anchor="w")
        self.reg(tk.Label(titles, bg=BG, fg=MUTED, font=FONT), "subtitle").pack(anchor="w")
        right = tk.Frame(h, bg=BG)
        right.pack(side="right")
        self.reg(tk.Label(right, bg=BG, fg=MUTED, font=FONT), "theme").pack(side="left", padx=(0, 6))
        self.theme_box = ttk.Combobox(right, values=list(THEMES.keys()) + ["Custom"], state="readonly", width=15, font=FONT)
        self.theme_box.set(self.theme_name)
        self.theme_box.pack(side="left", padx=(0, 16))
        self.theme_box.bind("<<ComboboxSelected>>", self.on_theme_selected)
        self.reg(tk.Label(right, bg=BG, fg=MUTED, font=FONT), "lang").pack(side="left", padx=(0, 8))
        self.lang_box = ttk.Combobox(right, values=["English", "Русский"], state="readonly", width=11, font=FONT)
        self.lang_box.set("English" if self.lang == "en" else "Русский")
        self.lang_box.pack(side="left")
        self.lang_box.bind("<<ComboboxSelected>>", self.on_language)

    # ---------- body ----------
    def build_body(self):
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=22, pady=(4, 18))
        body.grid_columnconfigure(0, weight=3, uniform="c")
        body.grid_columnconfigure(1, weight=2, uniform="c")
        body.grid_rowconfigure(0, weight=1)

        # ----- left: tabs -----
        self.nb = ttk.Notebook(body)
        self.nb.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        tab_settings = tk.Frame(self.nb, bg=BG)
        tab_req = tk.Frame(self.nb, bg=BG)
        self.reports_tab = tk.Frame(self.nb, bg=BG)
        self.connect_tab = tk.Frame(self.nb, bg=BG)
        self.masteries_tab = tk.Frame(self.nb, bg=BG)
        self.nb.add(tab_settings, text="Settings")
        self.nb.add(self.reports_tab, text=self.t("tab.reports"))
        self.nb.add(self.connect_tab, text=self.t("tab.connect"))
        self.nb.add(self.masteries_tab, text=self.t("tab.masteries"))
        self.nb.add(tab_req, text=self.t("tab.requirements"))
        self.tab_widgets = [
            (tab_settings, "tab.settings"),
            (self.reports_tab, "tab.reports"),
            (self.connect_tab, "tab.connect"),
            (self.masteries_tab, "tab.masteries"),
            (tab_req, "tab.requirements"),
        ]
        self.build_reports_tab()
        self.build_connect_tab()
        self.build_masteries_tab()

        bar = tk.Frame(tab_settings, bg=BG)
        self.settings_toolbar = bar
        bar.pack(side="bottom", fill="x", pady=(10, 0))
        self.button(bar, "btn.save", self.on_save, accent=True).pack(side="left")
        self.button(bar, "btn.profiles", self.open_profiles_dialog).pack(side="left", padx=(10, 0))
        self.button(bar, "btn.choose_config", self.on_choose_config).pack(side="left", padx=(10, 0))
        self.button(bar, "btn.export_config", self.on_export_config).pack(side="left", padx=(10, 0))
        cloud_bar = tk.Frame(tab_settings, bg=BG)
        cloud_bar.pack(side="bottom", fill="x", pady=(8, 0))
        self.button(cloud_bar, "btn.git_config", self.on_git_configs, accent=True).pack(side="left")
        self.button(cloud_bar, "btn.check_updates", self.on_check_updates).pack(side="left", padx=(10, 0))
        wrap, inner = self.make_scrollable(tab_settings)
        wrap.pack(fill="both", expand=True, pady=(12, 0))

        hop_card = tk.Frame(inner, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        hop_card.pack(fill="x", pady=(0, 12))
        hop_head = tk.Frame(hop_card, bg=CARD)
        hop_head.pack(fill="x", padx=14, pady=(12, 6))
        tk.Frame(hop_head, bg=ACCENT, width=4, height=18).pack(side="left", padx=(0, 10))
        self.server_hop_title = tk.Label(hop_head, text="", bg=CARD, fg=TEXT_C,
                                         font=("Segoe UI Semibold", 12))
        self.server_hop_title.pack(side="left")
        hop_row = tk.Frame(hop_card, bg=CARD)
        hop_row.pack(fill="x", padx=14, pady=(2, 12))
        self.server_hop_interval_label = tk.Label(hop_row, text="", bg=CARD, fg=MUTED, font=FONT)
        self.server_hop_interval_label.pack(side="left")
        self.server_hop_entry = tk.Entry(hop_row, textvariable=self.server_hop_minutes, width=6,
                                         bg=ENTRY_BG, fg=TEXT_C, insertbackground=TEXT_C, relief="flat")
        self.server_hop_entry.pack(side="left", padx=(8, 12), ipady=4)
        self.server_hop_start_btn = tk.Button(hop_row, text="", command=self.start_server_hop,
                                               bg=ACCENT, fg="#1a1205", relief="flat", padx=12, pady=7)
        self.server_hop_start_btn.pack(side="left")
        self.server_hop_stop_btn = tk.Button(hop_row, text="", command=self.stop_server_hop,
                                              bg=CARD, fg=TEXT_C, relief="flat", padx=12, pady=7,
                                              state="disabled")
        self.server_hop_stop_btn.pack(side="left", padx=(8, 0))
        self.server_hop_now_btn = tk.Button(hop_row, text="", command=self.rejoin_random_server,
                                             bg=CARD, fg=TEXT_C, relief="flat", padx=12, pady=7)
        self.server_hop_now_btn.pack(side="left", padx=(8, 0))
        self.server_hop_auto_check = ttk.Checkbutton(
            hop_card, text="", variable=self.server_hop_auto_var,
            command=self.on_server_hop_checkbox, style="Dark.TCheckbutton"
        )
        self.server_hop_auto_check.pack(anchor="w", padx=14, pady=(0, 6))
        self.server_hop_status = tk.Label(hop_card, text="", bg=CARD, fg=MUTED, font=FONT)
        self.server_hop_status.pack(anchor="w", padx=14, pady=(0, 10))

        self.build_settings(inner)
        self.apply_server_hop_language()

        wrap2, inner2 = self.make_scrollable(tab_req)
        wrap2.pack(fill="both", expand=True, pady=(12, 0))
        self.build_requirements(inner2)

        # ----- right: preview, controls, log -----
        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        pv, pv_body = self.card(right, "preview.title")
        pv.pack(fill="x")
        self.preview_label = tk.Label(pv_body, bg="#0b0c10", fg=MUTED, font=FONT, height=12)
        self.preview_label.pack(fill="x")

        ctl = tk.Frame(right, bg=BG)
        ctl.pack(fill="x", pady=(12, 0))
        self.start_btn = self.button(ctl, "btn.start", self.on_start, accent=True)
        self.start_btn.pack(side="left")
        self.stop_btn = self.button(ctl, "btn.stop", self.on_stop)
        self.stop_btn.pack(side="left", padx=(10, 0))
        self.set_enabled(self.stop_btn, False)
        status = tk.Frame(ctl, bg=BG)
        status.pack(side="right")
        self.dot = tk.Label(status, text="●", bg=BG, fg=MUTED, font=("Segoe UI", 14))
        self.dot.pack(side="left")
        self.status_label = tk.Label(status, bg=BG, fg=TEXT_C, font=FONT_B)
        self.status_label.pack(side="left", padx=(4, 0))
        self.status_key = "status.idle"

        self.reg(tk.Label(right, bg=BG, fg=MUTED, font=FONT_S), "hotkey").pack(anchor="w", pady=(6, 0))

        self.right_tabs = ttk.Notebook(right)
        self.right_tabs.pack(fill="both", expand=True, pady=(12, 0))
        self.dashboard_tab = tk.Frame(self.right_tabs, bg=BG)
        self.console_tab = tk.Frame(self.right_tabs, bg=BG)
        self.right_tabs.add(self.dashboard_tab, text=self.t("tab.dashboard"))
        self.right_tabs.add(self.console_tab, text=self.t("tab.console"))
        dash_card, dash_body = self.card(self.dashboard_tab, "dash.title")
        dash_card.pack(fill="both", expand=True)
        self.dash_labels = {}
        self.dash_caption_labels = {}
        stats = tk.Frame(dash_body, bg=CARD)
        stats.pack(fill="x")
        stat_defs = [
            ("status", "dash.status"), ("elapsed", "dash.elapsed"),
            ("portals", "dash.portals"), ("noportal", "dash.noportal"),
            ("errors", "dash.errors")
        ]
        for idx, (key, title_key) in enumerate(stat_defs):
            cell = tk.Frame(stats, bg=ENTRY_BG, highlightbackground=BORDER, highlightthickness=1)
            cell.grid(row=idx // 2, column=idx % 2, sticky="nsew", padx=4, pady=4)
            stats.grid_columnconfigure(idx % 2, weight=1)
            caption = tk.Label(cell, text=self.t(title_key), bg=ENTRY_BG, fg=MUTED, font=FONT_S)
            caption.pack(anchor="w", padx=10, pady=(8, 2))
            self.dash_caption_labels[key] = (caption, title_key)
            value = tk.Label(cell, text=(self.t("status.idle") if key == "status" else "00:00:00" if key == "elapsed" else "0"),
                             bg=ENTRY_BG, fg=ACCENT if key == "status" else TEXT_C, font=("Segoe UI Semibold", 17))
            value.pack(anchor="w", padx=10, pady=(0, 8))
            self.dash_labels[key] = value
        last_box = tk.Frame(dash_body, bg=CARD)
        last_box.pack(fill="x", padx=4, pady=(10, 2))
        last_caption = tk.Label(last_box, text=self.t("dash.last"), bg=CARD, fg=MUTED, font=FONT_S)
        last_caption.pack(anchor="w")
        self.dash_caption_labels["last"] = (last_caption, "dash.last")
        self.dash_labels["last"] = tk.Label(last_box, text=self.last_event_text, bg=CARD, fg=TEXT_C,
                                              font=FONT, anchor="w", justify="left", wraplength=420)
        self.dash_labels["last"].pack(fill="x", anchor="w", pady=(3, 0))

        console_head = tk.Frame(self.console_tab, bg=BG)
        console_head.pack(fill="x", pady=(0, 6))
        self.button(console_head, "console.clear", self.clear_console).pack(side="right")
        console_card = tk.Frame(self.console_tab, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        console_card.pack(fill="both", expand=True)
        self.log_text = tk.Text(console_card, height=10, bg=ENTRY_BG, fg=TEXT_C, insertbackground=TEXT_C, relief="flat",
                                font=("Consolas", 9), wrap="word", highlightthickness=0,
                                state="disabled", padx=8, pady=8)
        log_scroll = ttk.Scrollbar(console_card, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")
        path = tk.Frame(right, bg=BG)
        path.pack(fill="x", pady=(8, 0))
        self.reg(tk.Label(path, bg=BG, fg=MUTED, font=FONT_S), "cfg.path").pack(side="left")
        tk.Label(path, text=CONFIG_PATH, bg=BG, fg=MUTED, font=FONT_S, wraplength=360, justify="left").pack(side="left", padx=(4, 0))


    # ---------- reports ----------
    def build_reports_tab(self):
        head = tk.Frame(self.reports_tab, bg=BG)
        head.pack(fill="x", padx=12, pady=12)
        self.report_title_label = tk.Label(head, text="", bg=BG, fg=TEXT_C,
                                           font=("Segoe UI Semibold", 16))
        self.report_title_label.pack(side="left")
        self.report_refresh_button = tk.Button(
            head, text="", command=self.refresh_report,
            bg=ACCENT, fg="#1a1205", relief="flat", padx=12, pady=7
        )
        self.report_refresh_button.pack(side="right")
        self.report_summary = tk.Label(self.reports_tab, text="",
                                       bg=BG, fg=MUTED, font=FONT, justify="left", anchor="w")
        self.report_summary.pack(fill="x", padx=14, pady=(0, 8))
        chart_box = tk.Frame(self.reports_tab, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        chart_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.report_canvas = tk.Canvas(chart_box, bg=ENTRY_BG, highlightthickness=0, height=340)
        self.report_canvas.pack(fill="both", expand=True, padx=8, pady=8)
        self.report_canvas.bind("<Configure>", lambda _e: self.refresh_report())
        self.refresh_report()

    def refresh_report(self):
        if not hasattr(self, "report_canvas"):
            return
        c = self.report_canvas
        c.delete("all")
        w = max(c.winfo_width(), 320)
        h = max(c.winfo_height(), 240)
        pad_l, pad_r, pad_t, pad_b = 48, 18, 24, 38
        x0, y0, x1, y1 = pad_l, pad_t, w-pad_r, h-pad_b
        c.create_text(x0, 8, text=self.t("report.activity"), fill=MUTED, anchor="nw", font=("Segoe UI", 9, "bold"))
        for i in range(5):
            y = y1 - (y1-y0)*i/4
            c.create_line(x0, y, x1, y, fill=BORDER)
            c.create_text(x0-8, y, text=str(i), fill=MUTED, anchor="e", font=("Segoe UI", 8))
        c.create_line(x0, y0, x0, y1, fill=MUTED)
        c.create_line(x0, y1, x1, y1, fill=MUTED)
        hist = self.event_history[-200:]
        if len(hist) < 2:
            c.create_text((x0+x1)//2, (y0+y1)//2, text=self.t("report.empty"),
                          fill=MUTED, font=FONT)
        else:
            start = hist[0]["time"]
            span = max(hist[-1]["time"]-start, 1.0)
            series = {"portals": [], "resets": [], "errors": []}
            totals = {"portals": 0, "resets": 0, "errors": 0}
            for item in hist:
                key = item["key"]
                if key == "evt.entered": totals["portals"] += 1
                elif key == "evt.noportal": totals["resets"] += 1
                elif key == "evt.error": totals["errors"] += 1
                for name in series: series[name].append((item["time"], totals[name]))
            max_count = max(1, max(v for values in series.values() for _,v in values))
            colors = {"portals": "#39c879", "resets": "#f0ad45", "errors": "#ee5b61"}
            for name, values in series.items():
                pts = [(x0+(ts-start)/span*(x1-x0), y1-val/max_count*(y1-y0)) for ts,val in values]
                for a,b in zip(pts, pts[1:]):
                    c.create_line(a[0],a[1],b[0],b[1], fill=colors[name], width=2)
            c.create_text(x0+8, y0+8, text=self.t("report.portals").upper(), fill=colors["portals"], anchor="nw", font=("Segoe UI",8,"bold"))
            c.create_text(x0+82, y0+8, text=self.t("report.resets").upper(), fill=colors["resets"], anchor="nw", font=("Segoe UI",8,"bold"))
            c.create_text(x0+150, y0+8, text=self.t("report.errors").upper(), fill=colors["errors"], anchor="nw", font=("Segoe UI",8,"bold"))
            c.create_text(x0, y1+18, text=self.t("report.start").upper(), fill=MUTED, anchor="w", font=("Segoe UI",8))
            c.create_text(x1, y1+18, text=self.t("report.latest").upper(), fill=MUTED, anchor="e", font=("Segoe UI",8))
        self.report_summary.configure(
            text=self.t("report.summary",
                        status=self.t("status.running" if self.running else "status.idle"),
                        duration=self._session_duration_text(),
                        portals=self.session_portals,
                        resets=self.session_noportal,
                        errors=self.session_errors)
        )

    def _session_duration_text(self):
        if not self.session_started:
            return "00:00:00"
        end = self.session_finished if self.session_finished is not None else time.monotonic()
        sec = max(0, int(end-self.session_started))
        hh, rem = divmod(sec,3600); mm, ss = divmod(rem,60)
        return f"{hh:02d}:{mm:02d}:{ss:02d}"

    def build_report_png(self):
        # OpenCV-only chart renderer: no matplotlib dependency and low memory use.
        width, height = 1200, 620
        img = np.full((height,width,3), (35,35,35), dtype=np.uint8)
        cv2.putText(img, "BOB FARM - SESSION REPORT", (35,48), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (245,245,245), 2, cv2.LINE_AA)
        duration = self._session_duration_text()
        lines = [
            f"Duration: {duration}",
            f"Portals entered: {self.session_portals}",
            f"No-portal resets: {self.session_noportal}",
            f"Errors: {self.session_errors}",
            f"Status: {'RUNNING' if self.running else 'IDLE'}"
        ]
        for i, line in enumerate(lines):
            cv2.putText(img, line, (40,95+i*34), cv2.FONT_HERSHEY_SIMPLEX, .68, (220,220,220), 1, cv2.LINE_AA)
        left,right,top,bottom = 65,1160,300,555
        for i in range(5):
            y = bottom-i*(bottom-top)//4
            cv2.line(img,(left,y),(right,y),(75,75,75),1)
        cv2.putText(img,"EVENT ACTIVITY",(left,top-18),cv2.FONT_HERSHEY_SIMPLEX,.55,(180,180,180),1,cv2.LINE_AA)
        hist = self.event_history[-200:]
        if len(hist)>1:
            start=hist[0]["time"]; span=max(hist[-1]["time"]-start,1)
            totals={"evt.entered":0,"evt.noportal":0,"evt.error":0}
            series={k:[] for k in totals}
            for item in hist:
                if item["key"] in totals: totals[item["key"]]+=1
                for key in series:
                    x=left+int((item["time"]-start)/span*(right-left))
                    y=bottom-int(totals[key]/max(1,len(hist))*(bottom-top))
                    series[key].append((x,y))
            for key,color in (("evt.entered",(55,200,110)),("evt.noportal",(70,170,245)),("evt.error",(90,90,235))):
                for a,b in zip(series[key],series[key][1:]): cv2.line(img,a,b,color,2,cv2.LINE_AA)
            cv2.putText(img,"GREEN: PORTALS   ORANGE: RESETS   RED: ERRORS",(left,top+22),
                        cv2.FONT_HERSHEY_SIMPLEX,.48,(205,205,205),1,cv2.LINE_AA)
        cv2.putText(img,time.strftime("%Y-%m-%d %H:%M:%S"),(40,595),cv2.FONT_HERSHEY_SIMPLEX,.45,(150,150,150),1,cv2.LINE_AA)
        ok, encoded = cv2.imencode(".png", img)
        return encoded.tobytes() if ok else None

    # ---------- public server rejoin / automatic server hopping ----------
    def apply_server_hop_language(self):
        if not hasattr(self, "server_hop_title"):
            return
        ru = self.lang == "ru"
        self.server_hop_title.configure(text="Смена серверов" if ru else "Server hopping")
        self.server_hop_interval_label.configure(text="Интервал (мин.):" if ru else "Interval (min):")
        self.server_hop_start_btn.configure(text="ЗАПУСТИТЬ" if ru else "START")
        self.server_hop_stop_btn.configure(text="ОСТАНОВИТЬ" if ru else "STOP")
        self.server_hop_now_btn.configure(text="СМЕНИТЬ СЕЙЧАС" if ru else "HOP NOW")
        self.server_hop_auto_check.configure(
            text="Автосмена включена (по желанию)" if ru else "Enable automatic hopping (optional)"
        )
        if not self.server_hop_enabled:
            self.server_hop_status.configure(text="Автосмена выключена" if ru else "Automatic hopping is off")

    def on_server_hop_checkbox(self):
        if self.server_hop_auto_var.get():
            self.start_server_hop()
            if not self.server_hop_enabled:
                self.server_hop_auto_var.set(False)
        else:
            self.stop_server_hop()

    def _fetch_public_server_page(self, cursor=None, sort_order="Desc"):
        """Load one public-server page using the same URL/pagination pattern as Server Browser."""
        params = {"sortOrder": sort_order or "Desc", "limit": "100"}
        if cursor:
            params["cursor"] = cursor
        url = (
            f"https://games.roblox.com/v1/games/{SLAP_BATTLES_PLACE_ID}/servers/Public?"
            f"{urllib.parse.urlencode(params)}"
        )
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        )

        # Retry the exact same cursor page on rate limit; never advance the cursor
        # until Roblox actually returns a valid page.
        last_error = None
        for attempt in range(6):
            try:
                with urllib.request.urlopen(request, timeout=25) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
                    raise RuntimeError("Roblox returned an invalid server-list response.")
                return payload["data"], payload.get("nextPageCursor")
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code == 429 and attempt < 5:
                    wait_seconds = 3 * (attempt + 1)
                    self.log("evt.warning", msg=f"Roblox HTTP 429; retrying same page in {wait_seconds}s")
                    time.sleep(wait_seconds)
                    continue
                if exc.code == 429:
                    raise RuntimeError(
                        "Roblox API rate-limited the server search after 6 attempts. "
                        "Wait before trying again."
                    ) from exc
                raise RuntimeError(f"Roblox API HTTP {exc.code}: {exc.reason}") from exc
            except urllib.error.URLError as exc:
                raise RuntimeError(f"Network error while loading Roblox servers: {exc}") from exc
        raise RuntimeError(f"Could not load Roblox servers: {last_error}")

    def _get_random_public_server(self, target_players=None):
        """Load up to 200 Slap Battles servers; accept 11–13 players only and ping <70 ms."""
        candidates = []
        seen = set()
        cursor = None
        loaded = 0
        page_count = 0

        # Keep pagination atomic so manual hop, auto-hop and Telegram /rejoin
        # cannot issue overlapping requests or mix cursors.
        with self._server_api_lock:
            while loaded < 200 and page_count < 2:
                batch, next_cursor = self._fetch_public_server_page(
                    cursor=cursor, sort_order="Desc"
                )
                page_count += 1
                loaded += len(batch)

                for server in batch:
                    try:
                        server_id = str(server.get("id") or "")
                        if not server_id or server_id in seen:
                            continue
                        seen.add(server_id)

                        players = int(server.get("playing", 0))
                        maximum = int(server.get("maxPlayers", 0))
                        raw_ping = server.get("ping")
                        ping = float(raw_ping) if raw_ping is not None else None

                        if maximum <= 0 or players >= maximum:
                            continue
                        # User's requested population: 11–13 players only.
                        # Never select a server with 14+ players.
                        if players < 11 or players > 13:
                            continue
                        if ping is None or ping < 0 or ping >= 70:
                            continue

                        candidates.append((server_id, players, maximum, ping))
                    except (TypeError, ValueError, AttributeError):
                        continue

                self.log(
                    "evt.warning",
                    msg=(f"Slap Battles server search: page {page_count}, "
                         f"loaded {loaded}/200, suitable {len(candidates)}"),
                )

                if loaded >= 200 or not next_cursor or not batch:
                    break
                cursor = next_cursor
                time.sleep(0.3)

        if not candidates:
            raise RuntimeError(
                f"Scanned {loaded} servers, but none matched: 11–13 players "
                "and Roblox-reported ping below 70 ms."
            )

        # Lowest ping wins. If pings tie, prefer the server with more players.
        last_id = getattr(self, "_last_server_id", None)
        fresh = [item for item in candidates if item[0] != last_id] or candidates
        server_id, players, maximum, ping = min(
            fresh, key=lambda item: (item[3], -item[1])
        )
        self._last_server_id = server_id
        ping_label = f"{ping:.0f} ms (Roblox API)"
        self.log(
            "evt.warning",
            msg=(f"Selected server: {players}/{maximum} players, "
                 f"ping {ping_label}; checked {loaded} servers"),
        )
        return server_id, players, maximum, ping, players, ping_label

    def _launch_roblox_server(self, server_id):
        if os.name != "nt":
            raise RuntimeError("Joining a Roblox server through the app protocol is supported on Windows only.")
        if server_id:
            join_uri = f"roblox://experiences/start?placeId={SLAP_BATTLES_PLACE_ID}&gameInstanceId={server_id}"
        else:                                           # no server list: let Roblox pick a server itself
            join_uri = f"roblox://placeId={SLAP_BATTLES_PLACE_ID}"
        os.startfile(join_uri)

    def rejoin_random_server(self, notify_chat_id=None, target_players=None):
        if self.server_hop_busy.is_set():
            if notify_chat_id is not None:
                self._tg_send_text(notify_chat_id,
                    "A server join is already in progress." if self.lang != "ru" else "Переход на сервер уже выполняется.")
            return
        self.server_hop_busy.set()
        if hasattr(self, "server_hop_status"):
            status_text = "Finding a public server..." if self.lang != "ru" else "Поиск публичного сервера..."
            try:
                self.root.after(0, lambda msg=status_text: self.server_hop_status.configure(text=msg))
            except Exception:
                pass

        def worker():
            try:
                server_id, playing, maximum, ping, target, ping_label = self._get_random_public_server(target_players)
                self._launch_roblox_server(server_id)
                result = (f"Joining Slap Battles server: {playing}/{maximum} players; ping {ping_label}."
                          if self.lang != "ru" else
                          f"Подключаю к серверу Slap Battles: {playing}/{maximum} игроков; пинг {ping_label}.")
                self.root.after(0, lambda msg=result: self.server_hop_status.configure(text=msg)
                                if hasattr(self, "server_hop_status") else None)
                if notify_chat_id is not None:
                    self._tg_send_text(notify_chat_id, result)
                self.emit("evt.server_hop")
            except Exception as exc:
                error = (f"Server join failed: {exc}" if self.lang != "ru" else
                         f"Не удалось перейти на сервер: {exc}")
                try:
                    self.root.after(0, lambda msg=error: self.server_hop_status.configure(text=msg)
                                    if hasattr(self, "server_hop_status") else None)
                except Exception:
                    pass
                if notify_chat_id is not None:
                    self._tg_send_text(notify_chat_id, error[:3500])
            finally:
                self.server_hop_busy.clear()
        threading.Thread(target=worker, daemon=True).start()

    def start_server_hop(self):
        try:
            minutes = float(self.server_hop_minutes.get().strip())
            if not 1 <= minutes <= 1440:
                raise ValueError
        except Exception:
            messagebox.showerror("Server hopping",
                                 "Enter an interval from 1 to 1440 minutes." if self.lang != "ru"
                                 else "Укажи интервал от 1 до 1440 минут.")
            return
        self.server_hop_enabled = True
        self.server_hop_auto_var.set(True)
        self.server_hop_stop_btn.configure(state="normal")
        self.server_hop_start_btn.configure(state="disabled")
        self.server_hop_entry.configure(state="disabled")
        self.server_hop_status.configure(
            text=(f"Automatic hopping every {minutes:g} minute(s)." if self.lang != "ru"
                  else f"Автосмена серверов каждые {minutes:g} мин.")
        )
        self._schedule_server_hop(int(minutes * 60 * 1000))

    def _schedule_server_hop(self, delay_ms):
        if not self.server_hop_enabled:
            return
        if self.server_hop_after_id:
            self.root.after_cancel(self.server_hop_after_id)
        self.server_hop_after_id = self.root.after(delay_ms, self._server_hop_tick)

    def _server_hop_tick(self):
        self.server_hop_after_id = None
        if not self.server_hop_enabled:
            return
        self.rejoin_random_server()
        try:
            minutes = float(self.server_hop_minutes.get().strip())
        except Exception:
            minutes = 5
        self._schedule_server_hop(int(minutes * 60 * 1000))

    def stop_server_hop(self):
        self.server_hop_enabled = False
        if hasattr(self, "server_hop_auto_var"):
            self.server_hop_auto_var.set(False)
        if self.server_hop_after_id:
            try:
                self.root.after_cancel(self.server_hop_after_id)
            except Exception:
                pass
            self.server_hop_after_id = None
        if hasattr(self, "server_hop_start_btn"):
            self.server_hop_start_btn.configure(state="normal")
            self.server_hop_stop_btn.configure(state="disabled")
            self.server_hop_entry.configure(state="normal")
            self.server_hop_status.configure(
                text="Automatic hopping stopped." if self.lang != "ru" else "Автосмена серверов остановлена."
            )

    # ---------- Telegram connection / access control ----------
    def load_telegram_features(self):
        defaults = {"start": True, "capture": True, "rejoin": True, "stats": True, "settings": True}
        try:
            with open(TELEGRAM_FEATURES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                defaults.update({k: bool(data.get(k, v)) for k, v in defaults.items()})
        except Exception:
            pass
        return defaults

    def save_telegram_features(self):
        data = {key: bool(var.get()) for key, var in self.telegram_feature_vars.items()}
        tmp = TELEGRAM_FEATURES_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, TELEGRAM_FEATURES_PATH)
        self.telegram_features = data
        messagebox.showinfo("Telegram", "Bot feature settings saved." if self.lang != "ru" else "Настройки функций бота сохранены.")

    def load_telegram_config(self):
        try:
            with open(TELEGRAM_CONFIG_PATH,"r",encoding="utf-8") as f:
                d=json.load(f)
            return {"token":str(d.get("token","")).strip(), "allowed_ids":str(d.get("allowed_ids","")),
                    "password_free_ids":str(d.get("password_free_ids","")), "auto_start":bool(d.get("auto_start",False))}
        except Exception:
            return {"token":"","allowed_ids":"","password_free_ids":"","auto_start":False}

    def load_telegram_access(self):
        try:
            with open(TELEGRAM_ACCESS_PATH,"r",encoding="utf-8") as f: return json.load(f)
        except Exception:
            return {"salt":"","password_hash":""}

    def save_telegram_config(self):
        token=self.tg_token_entry.get().strip()
        allowed=self.tg_allowed_entry.get().strip()
        free=self.tg_free_entry.get().strip()
        password=self.tg_password_entry.get()
        ids=[x.strip() for x in re.split(r"[,;\s]+",allowed) if x.strip()]
        free_ids=[x.strip() for x in re.split(r"[,;\s]+",free) if x.strip()]
        if any(not x.isdigit() for x in ids+free_ids):
            messagebox.showerror("Telegram","Telegram IDs must contain digits only.")
            return False
        if any(x not in ids for x in free_ids):
            messagebox.showerror("Telegram","Password-free IDs must also be in the allowed IDs list.")
            return False
        ids=list(dict.fromkeys(ids))
        free_ids=list(dict.fromkeys(free_ids))
        if any(x not in free_ids for x in ids) and not password and not self.telegram_access.get("password_hash"):
            messagebox.showerror("Telegram","Set an access password or add every allowed ID to the password-free list.")
            return False
        if password and len(password) < 6:
            messagebox.showerror("Telegram","Use an access password with at least 6 characters.")
            return False
        if password:
            salt=secrets.token_hex(16)
            digest=hashlib.pbkdf2_hmac("sha256",password.encode("utf-8"),bytes.fromhex(salt),200000).hex()
            self.telegram_access={"salt":salt,"password_hash":digest}
            self._tg_authenticated=set()
            try:
                with open(TELEGRAM_ACCESS_PATH,"w",encoding="utf-8") as f: json.dump(self.telegram_access,f,indent=2)
            except OSError as e:
                messagebox.showerror("Telegram",f"Could not save password database: {e}")
                return False
        self.telegram_cfg={"token":token,"allowed_ids":",".join(ids),"password_free_ids":",".join(free_ids),"auto_start":bool(getattr(self,"tg_auto_start_var",tk.BooleanVar(value=False)).get())}
        try:
            with open(TELEGRAM_CONFIG_PATH,"w",encoding="utf-8") as f: json.dump(self.telegram_cfg,f,indent=2)
        except OSError as e:
            messagebox.showerror("Telegram",f"Could not save Telegram settings: {e}")
            return False
        self._tg_authenticated=set()
        messagebox.showinfo("Telegram","Settings saved. Start the bot to connect.")
        return True

    def build_connect_tab(self):
        wrap, inner = self.make_scrollable(self.connect_tab)
        wrap.pack(fill="both", expand=True, padx=12, pady=12)

        self.connect_title_label = tk.Label(inner, text="", bg=BG, fg=TEXT_C,
                                             font=("Segoe UI Semibold", 15))
        self.connect_title_label.pack(anchor="w", pady=(0, 10))

        self.tg_token_label = tk.Label(inner, text="", bg=BG, fg=MUTED, font=FONT)
        self.tg_token_label.pack(anchor="w")
        self.tg_token_entry = tk.Entry(inner, bg=ENTRY_BG, fg=TEXT_C, insertbackground=TEXT_C,
                                       relief="flat", show="•")
        self.tg_token_entry.pack(fill="x", pady=(3, 10), ipady=7)
        self.tg_token_entry.insert(0, self.telegram_cfg["token"])

        self.tg_allowed_label = tk.Label(inner, text="", bg=BG, fg=MUTED, font=FONT)
        self.tg_allowed_label.pack(anchor="w")
        self.tg_allowed_entry = tk.Entry(inner, bg=ENTRY_BG, fg=TEXT_C, insertbackground=TEXT_C, relief="flat")
        self.tg_allowed_entry.pack(fill="x", pady=(3, 10), ipady=7)
        self.tg_allowed_entry.insert(0, self.telegram_cfg["allowed_ids"])

        self.tg_free_label = tk.Label(inner, text="", bg=BG, fg=MUTED, font=FONT)
        self.tg_free_label.pack(anchor="w")
        self.tg_free_entry = tk.Entry(inner, bg=ENTRY_BG, fg=TEXT_C, insertbackground=TEXT_C, relief="flat")
        self.tg_free_entry.pack(fill="x", pady=(3, 10), ipady=7)
        self.tg_free_entry.insert(0, self.telegram_cfg["password_free_ids"])

        self.tg_password_label = tk.Label(inner, text="", bg=BG, fg=MUTED, font=FONT)
        self.tg_password_label.pack(anchor="w")
        self.tg_password_entry = tk.Entry(inner, bg=ENTRY_BG, fg=TEXT_C, insertbackground=TEXT_C,
                                           relief="flat", show="•")
        self.tg_password_entry.pack(fill="x", pady=(3, 10), ipady=7)

        row = tk.Frame(inner, bg=BG)
        row.pack(fill="x", pady=5)
        self.tg_save_btn = tk.Button(row, text="", command=self.save_telegram_config,
                                     bg=ACCENT, fg="#1a1205", relief="flat", padx=12, pady=8)
        self.tg_save_btn.pack(side="left")
        self.tg_start_btn = tk.Button(row, text="", command=self.start_telegram_bot,
                                      bg=CARD, fg=TEXT_C, relief="flat", padx=12, pady=8)
        self.tg_start_btn.pack(side="left", padx=8)
        self.tg_stop_btn = tk.Button(row, text="", command=self.stop_telegram_bot,
                                     bg=CARD, fg=TEXT_C, relief="flat", padx=12, pady=8, state="disabled")
        self.tg_stop_btn.pack(side="left")

        self.tg_auto_start_var = tk.BooleanVar(value=bool(self.telegram_cfg.get("auto_start", False)))
        self.tg_auto_start_check = ttk.Checkbutton(
            inner, text=("Подключать при старте" if self.lang == "ru" else "Connect on startup"),
            variable=self.tg_auto_start_var, style="Dark.TCheckbutton",
            command=self.save_auto_start_preference)
        self.tg_auto_start_check.pack(anchor="w", pady=(4, 6))

        self.tg_status = tk.Label(inner, text="", bg=BG, fg=MUTED, font=FONT)
        self.tg_status.pack(anchor="w", pady=(8, 4))
        self.tg_help_label = tk.Label(inner, text="", bg=BG, fg=MUTED, font=FONT,
                                      justify="left", wraplength=600)
        self.tg_help_label.pack(anchor="w", pady=8)
        feature_box = tk.LabelFrame(inner, text="Bot features" if self.lang != "ru" else "Функции бота",
                                    bg=BG, fg=TEXT_C, padx=10, pady=8)
        feature_box.pack(fill="x", pady=(8, 4))
        self.telegram_feature_vars = {}
        self.telegram_feature_checks = {}
        for key, en, ru in (("start", "Respond to /start", "Отвечать на /start"),
                            ("capture", "Allow /capture (screenshots + report)", "Разрешить /capture (скриншот + отчёт)"),
                            ("rejoin", "Allow /rejoin (filtered server)", "Разрешить /rejoin (сервер по фильтрам)")):
            var = tk.BooleanVar(value=self.telegram_features.get(key, True))
            self.telegram_feature_vars[key] = var
            check = ttk.Checkbutton(feature_box, text=ru if self.lang == "ru" else en,
                                    variable=var, style="Dark.TCheckbutton")
            check.pack(anchor="w", pady=2)
            self.telegram_feature_checks[key] = (check, en, ru)
        self.tg_features_save_btn = tk.Button(feature_box, text="Сохранить функции" if self.lang == "ru" else "SAVE FEATURES",
                                              command=self.save_telegram_features,
                                              bg=CARD, fg=TEXT_C, relief="flat", padx=12, pady=7)
        self.tg_features_save_btn.pack(anchor="w", pady=(7, 0))
        self._tg_authenticated = set()
        self.apply_connect_language()

    def apply_connect_language(self):
        if not hasattr(self, "connect_title_label"):
            return
        ru = self.lang == "ru"
        values = {
            "title": "СВЯЗЬ С TELEGRAM" if ru else "TELEGRAM CONNECTION",
            "token": "Токен API бота" if ru else "Bot API token",
            "allowed": "Разрешённые Telegram ID (через запятую)" if ru else "Allowed Telegram user IDs (comma separated)",
            "free": "ID без пароля (также должны быть в списке разрешённых)" if ru else "IDs that do NOT need a password (must also be allowed)",
            "password": "Пароль доступа (оставь пустым, чтобы сохранить текущий)" if ru else "Access password (leave blank to keep existing password)",
            "save": "СОХРАНИТЬ НАСТРОЙКИ" if ru else "SAVE SETTINGS",
            "start": "ЗАПУСТИТЬ БОТА" if ru else "START BOT",
            "stop": "ОСТАНОВИТЬ БОТА" if ru else "STOP BOT",
            "status": ("Бот: работает" if self.telegram_thread and self.telegram_thread.is_alive() else "Бот: не подключён") if ru
                      else ("Bot: online" if self.telegram_thread and self.telegram_thread.is_alive() else "Bot: offline"),
            "help": ("Команды: /start — инструкция, /password ПАРОЛЬ — вход, /capture — скриншот и отчёт, /rejoin — перейти на сервер, /restart — перезапуск фарма с минимум 20 игроками и пингом ниже 70 мс.\\n"
                     "Отвечает только ID из списка разрешённых.")
                    if ru else
                    ("Commands: /start — instructions, /password PASSWORD — login, /capture — screenshot and report, /rejoin — join a server, /restart — restart farm with 11–13 players and ping below 70 ms.\\n"
                     "Only IDs in the allowlist receive replies.")
        }
        self.connect_title_label.configure(text=values["title"])
        self.tg_token_label.configure(text=values["token"])
        self.tg_allowed_label.configure(text=values["allowed"])
        self.tg_free_label.configure(text=values["free"])
        self.tg_password_label.configure(text=values["password"])
        self.tg_save_btn.configure(text=values["save"])
        self.tg_start_btn.configure(text=values["start"])
        self.tg_stop_btn.configure(text=values["stop"])
        self.tg_status.configure(text=values["status"])
        self.tg_help_label.configure(text=values["help"])
        if hasattr(self, "tg_auto_start_check"):
            self.tg_auto_start_check.configure(text="Подключать при старте" if ru else "Connect on startup")
        if hasattr(self, "telegram_feature_checks"):
            for _key, (check, en, ru_text) in self.telegram_feature_checks.items():
                check.configure(text=ru_text if ru else en)
            self.tg_features_save_btn.configure(text="СОХРАНИТЬ ФУНКЦИИ" if ru else "SAVE FEATURES")

    def _tg_api(self, method, payload=None, timeout=25):
        token=self.telegram_cfg.get("token","")
        if not token: raise RuntimeError("Telegram bot token is empty")
        data=json.dumps(payload or {}).encode("utf-8")
        req=urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}",data=data,
                                   headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=timeout) as response:
            result=json.loads(response.read().decode("utf-8"))
        if not result.get("ok"): raise RuntimeError(result.get("description","Telegram API error"))
        return result.get("result")

    def _tg_send_text(self, chat_id, text):
        self._tg_api("sendMessage",{"chat_id":chat_id,"text":text})

    def _tg_send_photo(self, chat_id, photo_bytes, filename, caption):
        token=self.telegram_cfg.get("token","")
        boundary="----BOBFarm"+secrets.token_hex(12)
        parts=[]
        def field(name,value):
            parts.append((f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n").encode())
        field("chat_id",str(chat_id))
        field("caption",caption)
        parts.append((f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{filename}\"\r\nContent-Type: image/png\r\n\r\n").encode()+photo_bytes+b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        req=urllib.request.Request(f"https://api.telegram.org/bot{token}/sendPhoto",data=b"".join(parts),
                                   headers={"Content-Type":f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req,timeout=45) as response:
            result=json.loads(response.read().decode("utf-8"))
        if not result.get("ok"): raise RuntimeError(result.get("description","sendPhoto failed"))

    def save_auto_start_preference(self):
        self.telegram_cfg["auto_start"] = bool(self.tg_auto_start_var.get())
        try:
            with open(TELEGRAM_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.telegram_cfg, f, ensure_ascii=False, indent=2)
            if self.telegram_cfg["auto_start"] and hasattr(self, "tg_token_entry") and self.tg_token_entry.get().strip():
                self.save_telegram_config()
        except Exception as exc:
            self.log("ERROR", f"Could not save auto-connect preference: {exc}")

    def _auto_start_telegram(self):
        if not self.telegram_cfg.get("auto_start"):
            return
        if not self.telegram_cfg.get("token"):
            self.log("ERROR", "Auto-connect is enabled, but Telegram token is empty.")
            return
        try:
            self.start_telegram_bot()
        except Exception as exc:
            self.log("ERROR", f"Telegram auto-connect failed: {exc}")

    def _telegram_restart_farm(self, chat_id):
        # Telegram thread only schedules GUI work; Tk widgets are touched on the main thread.
        def begin():
            if self.running:
                self.on_stop()
            deadline = time.monotonic() + 20.0
            def wait_until_stopped():
                if not self.running:
                    try:
                        self.on_start()
                        self._tg_send_text(chat_id, "Фарм перезапущен." if self.lang == "ru" else "Farm restarted.")
                    except Exception as exc:
                        self._tg_send_text(chat_id, ("Не удалось перезапустить фарм: " if self.lang == "ru" else "Farm restart failed: ") + str(exc)[:2500])
                    return
                if time.monotonic() >= deadline:
                    self._tg_send_text(chat_id, "Не удалось дождаться остановки фарма. Повторный запуск отменён." if self.lang == "ru" else "Farm did not stop in time; restart cancelled.")
                    return
                self.root.after(250, wait_until_stopped)
            self.root.after(250, wait_until_stopped)
        self.root.after(0, begin)

    def start_telegram_bot(self):
        if not self.save_telegram_config():
            return
        if self.telegram_thread and self.telegram_thread.is_alive(): return
        if not self.telegram_cfg.get("token"):
            messagebox.showwarning("Telegram", "Enter a bot token first." if self.lang != "ru" else "Сначала введи токен бота."); return
        self.telegram_stop.clear()
        self.telegram_thread=threading.Thread(target=self._telegram_poll_loop,daemon=True)
        self.telegram_thread.start()
        self.tg_status.configure(text=("Bot: connecting..." if self.lang != "ru" else "Бот: подключение..."),fg=ACCENT)
        self.tg_start_btn.configure(state="disabled"); self.tg_stop_btn.configure(state="normal")

    def stop_telegram_bot(self):
        self.telegram_stop.set()
        if hasattr(self,"tg_status"): self.tg_status.configure(text=("Bot: stopping..." if self.lang != "ru" else "Бот: остановка..."),fg=MUTED)
        if hasattr(self,"tg_start_btn"): self.tg_start_btn.configure(state="normal")
        if hasattr(self,"tg_stop_btn"): self.tg_stop_btn.configure(state="disabled")

    def _telegram_poll_loop(self):
        try:
            # Clear any pending updates to avoid replaying old commands.
            try:
                updates=self._tg_api("getUpdates",{"timeout":0,"offset":-1},timeout=8)
                if updates: self.telegram_offset=updates[-1]["update_id"]+1
            except Exception: pass
            self.root.after(0,lambda:self.tg_status.configure(text=("Bot: online" if self.lang != "ru" else "Бот: в сети"),fg=GREEN))
            while not self.telegram_stop.is_set():
                try:
                    updates=self._tg_api("getUpdates",{"timeout":20,"offset":self.telegram_offset},timeout=25)
                    for update in updates:
                        self.telegram_offset=update["update_id"]+1
                        msg=update.get("message") or update.get("edited_message")
                        if msg: self._handle_telegram_message(msg)
                except Exception as e:
                    if not self.telegram_stop.is_set():
                        self.root.after(0,lambda err=str(e): self.tg_status.configure(text=(f"Bot: error - {err[:100]}" if self.lang != "ru" else f"Ошибка бота: {err[:100]}"),fg="#ff6969"))
                        time.sleep(3)
        finally:
            self.root.after(0,lambda: (self.tg_status.configure(text=("Bot: offline" if self.lang != "ru" else "Бот: не подключён"),fg=MUTED),
                                       self.tg_start_btn.configure(state="normal"),
                                       self.tg_stop_btn.configure(state="disabled")))

    def _handle_telegram_message(self,msg):
        sender=msg.get("from",{})
        uid=str(sender.get("id",""))
        chat_id=msg.get("chat",{}).get("id")
        text=str(msg.get("text","")).strip()
        allowed={x.strip() for x in self.telegram_cfg.get("allowed_ids","").split(",") if x.strip()}
        free={x.strip() for x in self.telegram_cfg.get("password_free_ids","").split(",") if x.strip()}
        if uid not in allowed: return  # do not respond to strangers
        lang = self.lang  # Telegram replies always follow the GUI language setting
        def say(en,ru): self._tg_send_text(chat_id,ru if lang=="ru" else en)
        command = text.split()[0].split("@")[0] if text else ""
        if command == "/start":
            if self.telegram_features.get("start", True):
                say("BOB Farm connected. Commands: /capture and /rejoin (if enabled).",
                    "BOB Farm подключён. Команды: /capture и /rejoin (если включены).")
            return
        if command == "/password":
            supplied=text.partition(" ")[2].strip()
            access=self.telegram_access
            if not supplied or not access.get("password_hash"):
                say("Password is not configured.","Пароль не настроен.")
                return
            digest=hashlib.pbkdf2_hmac("sha256",supplied.encode("utf-8"),bytes.fromhex(access["salt"]),200000).hex()
            if secrets.compare_digest(digest,access["password_hash"]):
                self._tg_authenticated.add(uid)
                say("Access granted.","Доступ разрешён.")
            else:
                say("Incorrect password.","Неверный пароль.")
            return
        if command == "/rejoin":
            if not self.telegram_features.get("rejoin", True):
                say("The /rejoin command is disabled by the app owner.", "Команда /rejoin отключена владельцем программы.")
                return
            if uid not in free and uid not in self._tg_authenticated:
                say("Send /password YOUR_PASSWORD first.","Сначала отправь /password ТВОЙ_ПАРОЛЬ.")
                return
            say("Searching for a server with 11–13 players and ping below 70 ms...", "Ищу сервер на 11–13 игроков с пингом ниже 70 мс...")
            self.rejoin_random_server(chat_id)
            return
        if command == "/capture":
            if not self.telegram_features.get("capture", True):
                say("The /capture command is disabled by the app owner.", "Команда /capture отключена владельцем программы.")
                return
            if uid not in free and uid not in self._tg_authenticated:
                say("Send /password YOUR_PASSWORD first.","Сначала отправь /password ТВОЙ_ПАРОЛЬ.")
                return
            try:
                with mss.mss() as sct:
                    mon=sct.monitors[0]
                    shot=sct.grab(mon)
                    screen_bytes=cv2.imencode(".png",np.asarray(shot)[:,:,:3])[1].tobytes()
                self._tg_send_photo(chat_id,screen_bytes,"screen.png",
                    "BOB Farm screen capture" if lang!="ru" else "Скриншот экрана BOB Farm")
                report=self.build_report_png()
                if report:
                    self._tg_send_photo(chat_id,report,"report.png",
                        f"BOB Farm report | Portals: {self.session_portals} | Resets: {self.session_noportal} | Errors: {self.session_errors}" if lang!="ru"
                        else f"Отчёт BOB Farm | Порталы: {self.session_portals} | Ресеты: {self.session_noportal} | Ошибки: {self.session_errors}")
            except Exception as e:
                self._tg_send_text(chat_id,("Capture failed: "+str(e))[:3500] if lang!="ru" else ("Ошибка создания отчёта: "+str(e))[:3500])

    # ---------- settings tab ----------
    def build_settings(self, parent):
        for g in GROUPS:
            outer, body = self.card(parent, f"group.{g}")
            outer.pack(fill="x", pady=(0, 12))
            body.grid_columnconfigure(0, weight=1)
            row = 0
            for (grp, key, kind, default, lo, hi) in SCHEMA:
                if grp != g:
                    continue
                cell = tk.Frame(body, bg=CARD)
                cell.grid(row=row, column=0, sticky="ew", pady=5)
                cell.grid_columnconfigure(0, weight=1)
                texts = tk.Frame(cell, bg=CARD)
                texts.grid(row=0, column=0, sticky="w")
                self.reg(tk.Label(texts, bg=CARD, fg=TEXT_C, font=FONT, anchor="w", justify="left"), key, fmt=0).pack(anchor="w")
                self.reg(tk.Label(texts, bg=CARD, fg=MUTED, font=FONT_S, anchor="w", justify="left", wraplength=470), key, fmt=1).pack(anchor="w")
                value = self.cfg.get(key, default)
                if kind == "bool":
                    var = tk.BooleanVar(value=bool(value))
                    w = ttk.Checkbutton(cell, variable=var, style="Dark.TCheckbutton")
                    self.fields[key] = dict(kind=kind, widget=w, get=var.get, set=var.set, lo=lo, hi=hi)
                elif kind == "sign":
                    w = ttk.Combobox(cell, values=["1", "-1"], state="readonly", width=8, font=FONT)
                    w.set(str(value))
                    self.fields[key] = dict(kind=kind, widget=w, get=w.get, set=w.set, lo=lo, hi=hi)
                else:
                    var = tk.StringVar(value=fmt_num(value))
                    width = 30 if kind == "zones" else 12
                    w = tk.Entry(cell, textvariable=var, width=width, bg=ENTRY_BG, fg=TEXT_C, insertbackground=TEXT_C,
                                 relief="flat", font=FONT, highlightthickness=1, highlightbackground=BORDER,
                                 highlightcolor=ACCENT)
                    var.trace_add("write", lambda *a, wd=w: wd.configure(highlightbackground=BORDER))
                    self.fields[key] = dict(kind=kind, widget=w, get=var.get, set=var.set, lo=lo, hi=hi)
                w.grid(row=0, column=1, sticky="e", padx=(14, 0), ipady=3)
                row += 1

    def collect(self):
        """Reads every field. Returns (cfg, errors) where errors = [(key, text)]."""
        cfg, errors = {}, []
        for (grp, key, kind, default, lo, hi) in SCHEMA:
            self.mark(key, False)
        for (grp, key, kind, default, lo, hi) in SCHEMA:
            f = self.fields[key]
            try:
                cfg[key] = parse_value(kind, f["get"](), lo, hi)
            except FieldError as e:
                errors.append((key, self.t(e.code, **e.kw)))
                self.mark(key, True)
        if not errors:
            for key, code in cross_check(cfg):
                errors.append((key, self.t(code)))
                self.mark(key, True)
        return cfg, errors

    def mark(self, key, bad):
        w = self.fields[key]["widget"]
        if self.fields[key]["kind"] in ("int", "float", "zones"):
            w.configure(highlightbackground=RED if bad else BORDER)

    def fill_fields(self, cfg):
        for (grp, key, kind, default, lo, hi) in SCHEMA:
            v = cfg.get(key, default)
            self.fields[key]["set"](bool(v) if kind == "bool" else (str(v) if kind == "sign" else fmt_num(v)))
            self.mark(key, False)

    # ---------- Masteries plugins (download / tick / run) ----------

    # ---------- Masteries plugins (download / tick / run) ----------
    def mtext(self, widget, en, ru, option="text"):
        self.masteries_texts.append((widget, option, en, ru))
        widget.configure(**{option: ru if self.lang == "ru" else en})
        return widget

    def apply_masteries_language(self):
        for widget, option, en, ru in self.masteries_texts:
            try:
                widget.configure(**{option: ru if self.lang == "ru" else en})
            except tk.TclError:
                pass
        self.refresh_masteries_local()

    def build_masteries_tab(self):
        wrap, inner = self.make_scrollable(self.masteries_tab)
        wrap.pack(fill="both", expand=True, padx=12, pady=12)

        self.mtext(
            tk.Label(inner, bg=BG, fg=TEXT_C, font=("Segoe UI Semibold", 15)),
            "MASTERIES PLUGINS", "ПЛАГИНЫ MASTERIES"
        ).pack(anchor="w", pady=(0, 6))
        self.mtext(
            tk.Label(inner, bg=BG, fg=MUTED, wraplength=700, justify="left"),
            "Choose plugins from GitHub, install them, then tick the installed plugins you want to run. "
            "With Built-in portal farm enabled, plugins run after each portal entry. With it disabled, "
            "plugins run on their own. Python plugins can access your PC, so enable only trusted files.",
            "Выбирай плагины с GitHub, устанавливай их, затем отмечай установленные плагины. "
            "При включённом встроенном фарме плагины запускаются после каждого входа в портал. "
            "При выключенном — работают самостоятельно. Python-плагины имеют доступ к ПК, "
            "поэтому включай только файлы, которым доверяешь."
        ).pack(anchor="w", pady=(0, 12))

        cards = tk.Frame(inner, bg=BG)
        cards.pack(fill="both", expand=True)
        cards.grid_columnconfigure(0, weight=1, uniform="masteries")
        cards.grid_columnconfigure(1, weight=1, uniform="masteries")

        left_card = tk.Frame(cards, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        right_card = tk.Frame(cards, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.mtext(tk.Label(left_card, bg=CARD, fg=TEXT_C, font=FONT_B),
                   "Available on GitHub", "Доступно на GitHub").pack(anchor="w", padx=12, pady=(10, 6))
        self.masteries_remote_list = tk.Listbox(
            left_card, height=13, selectmode="extended", bg=ENTRY_BG, fg=TEXT_C,
            selectbackground=ACCENT, relief="flat", exportselection=False,
            highlightthickness=0, activestyle="none"
        )
        self.masteries_remote_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.mtext(tk.Label(right_card, bg=CARD, fg=TEXT_C, font=FONT_B),
                   "Installed plugins — tick to enable", "Установленные плагины — отметь для включения").pack(
                       anchor="w", padx=12, pady=(10, 6))

        local_wrap = tk.Frame(right_card, bg=ENTRY_BG)
        local_wrap.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        local_canvas = tk.Canvas(local_wrap, bg=ENTRY_BG, highlightthickness=0, bd=0)
        local_scroll = ttk.Scrollbar(local_wrap, orient="vertical", command=local_canvas.yview)
        self.masteries_local_frame = tk.Frame(local_canvas, bg=ENTRY_BG)
        self.masteries_local_frame.bind(
            "<Configure>", lambda _e: local_canvas.configure(scrollregion=local_canvas.bbox("all"))
        )
        local_window = local_canvas.create_window((0, 0), window=self.masteries_local_frame, anchor="nw")
        local_canvas.bind("<Configure>", lambda e: local_canvas.itemconfigure(local_window, width=e.width))
        local_canvas.configure(yscrollcommand=local_scroll.set)
        local_canvas.pack(side="left", fill="both", expand=True)
        local_scroll.pack(side="right", fill="y")

        def local_wheel(event):
            local_canvas.yview_scroll(int(-event.delta / 120), "units")
        local_canvas.bind("<Enter>", lambda _e: local_canvas.bind_all("<MouseWheel>", local_wheel))
        local_canvas.bind("<Leave>", lambda _e: local_canvas.unbind_all("<MouseWheel>"))

        buttons = tk.Frame(inner, bg=BG)
        buttons.pack(fill="x", pady=(10, 4))

        def add_button(en, ru, command, accent=False):
            button = tk.Button(
                buttons, command=command, relief="flat", bd=0, padx=12, pady=8,
                cursor="hand2", font=FONT_B,
                bg=ACCENT if accent else CARD,
                fg="#1a1205" if accent else TEXT_C,
                activebackground=ACCENT_D if accent else BORDER,
                activeforeground="#1a1205" if accent else TEXT_C
            )
            self.mtext(button, en, ru)
            button.pack(side="left", padx=(0, 8))
            return button

        add_button("REFRESH GITHUB", "ОБНОВИТЬ GITHUB", self.refresh_masteries_remote)
        add_button("INSTALL SELECTED", "УСТАНОВИТЬ ВЫБРАННОЕ", self.download_masteries_selected, True)
        add_button("INSTALL ALL", "УСТАНОВИТЬ ВСЕ", self.download_masteries_all)
        add_button("IMPORT .PY", "ИМПОРТ .PY", self.import_mastery)
        add_button("OPEN FOLDER", "ОТКРЫТЬ ПАПКУ", self.open_masteries_folder)

        self.masteries_status = tk.Label(inner, text="", bg=BG, fg=MUTED, anchor="w",
                                         justify="left", wraplength=700)
        self.masteries_status.pack(anchor="w", pady=5)
        self.masteries_remote_items = []
        os.makedirs(MASTERIES_DIR, exist_ok=True)
        self.refresh_masteries_local()
        self.root.after(700, self.refresh_masteries_remote)

    def mstatus(self, en, ru):
        if hasattr(self, "masteries_status"):
            self.masteries_status.configure(text=ru if self.lang == "ru" else en)

    def refresh_masteries_local(self):
        frame = getattr(self, "masteries_local_frame", None)
        if frame is None:
            return
        for child in frame.winfo_children():
            child.destroy()

        self.masteries_vars = {}
        os.makedirs(MASTERIES_DIR, exist_ok=True)
        ru = self.lang == "ru"
        names = [
            name for name in sorted(os.listdir(MASTERIES_DIR), key=str.lower)
            if name.lower().endswith(".py") and os.path.isfile(os.path.join(MASTERIES_DIR, name))
        ]

        if not names:
            tk.Label(
                frame, bg=ENTRY_BG, fg=MUTED,
                text="No plugins installed yet." if not ru else "Плагины ещё не установлены.",
                font=FONT
            ).pack(anchor="w", padx=10, pady=10)
            return

        for name in names:
            path = os.path.join(MASTERIES_DIR, name)
            info = plugin_info(path)
            enabled = name in self.masteries_enabled and info["ok"]
            var = tk.BooleanVar(value=enabled)
            self.masteries_vars[name] = var

            item = tk.Frame(frame, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
            item.pack(fill="x", padx=5, pady=4)
            top = tk.Frame(item, bg=CARD)
            top.pack(fill="x", padx=8, pady=(6, 2))

            check = ttk.Checkbutton(
                top, text=info["name"], variable=var, style="Dark.TCheckbutton",
                command=lambda filename=name: self.on_mastery_toggle(filename)
            )
            if not info["ok"]:
                check.state(["disabled"])
            check.pack(side="left", anchor="w")

            remove_text = "REMOVE" if not ru else "УДАЛИТЬ"
            tk.Button(
                top, text=remove_text, command=lambda filename=name: self.remove_mastery(filename),
                bg=CARD, fg=MUTED, activebackground=BORDER, activeforeground=TEXT_C,
                relief="flat", bd=0, cursor="hand2", font=FONT_S
            ).pack(side="right")

            description = info["description"] or name
            if not info["ok"]:
                description = (
                    "Invalid plugin: " + info.get("reason", "unsupported entry point")
                    if not ru else
                    "Плагин не поддерживается: " + info.get("reason", "не найдена функция запуска")
                )
            tk.Label(
                item, text=description, bg=CARD, fg=MUTED if info["ok"] else RED,
                font=FONT_S, anchor="w", justify="left", wraplength=300
            ).pack(fill="x", padx=30, pady=(0, 7))

        frame.update_idletasks()

    def on_mastery_toggle(self, filename):
        var = self.masteries_vars.get(filename)
        if var is None:
            return
        if var.get():
            ru = self.lang == "ru"
            question = (
                f"'{filename}' is Python code and will run on your PC when you press Start. "
                "Only enable plugins you trust. Enable it?"
                if not ru else
                f"'{filename}' — это код Python, который будет выполняться на ПК после нажатия Старт. "
                "Включай только плагины, которым доверяешь. Включить?"
            )
            if not messagebox.askyesno("Masteries", question):
                var.set(False)
                return
            if filename not in self.masteries_enabled:
                self.masteries_enabled.append(filename)
        elif filename in self.masteries_enabled:
            self.masteries_enabled.remove(filename)
        save_masteries_state(self.masteries_enabled)
        count = len(self.enabled_plugin_paths())
        self.mstatus(
            f"Enabled plugins: {count}. They will run when you press Start.",
            f"Включено плагинов: {count}. Они запустятся после нажатия Старт."
        )

    def enabled_plugin_paths(self):
        valid = []
        for filename in list(self.masteries_enabled):
            path = os.path.abspath(os.path.join(MASTERIES_DIR, filename))
            try:
                if os.path.commonpath([os.path.abspath(MASTERIES_DIR), path]) != os.path.abspath(MASTERIES_DIR):
                    continue
            except ValueError:
                continue
            if filename.lower().endswith(".py") and os.path.isfile(path) and plugin_info(path)["ok"]:
                valid.append(path)
        return valid

    def import_mastery(self):
        ru = self.lang == "ru"
        files = filedialog.askopenfilenames(
            title="Choose plugin file(s)" if not ru else "Выбери файл(ы) плагина",
            filetypes=[("Python plugin", "*.py"), ("All files", "*.*")]
        )
        if not files:
            return
        installed, failed = [], []
        os.makedirs(MASTERIES_DIR, exist_ok=True)
        for source_file in files:
            filename = os.path.basename(source_file)
            try:
                if not re.fullmatch(r"[\w .-]+\.py", filename, flags=re.UNICODE):
                    raise RuntimeError("invalid filename")
                if os.path.getsize(source_file) > MASTERIES_MAX_BYTES:
                    raise RuntimeError("file is larger than 1 MB")
                content = pathlib.Path(source_file).read_bytes()
                text = content.decode("utf-8-sig")
                ast.parse(text, filename=filename)
                destination = os.path.join(MASTERIES_DIR, filename)
                if os.path.exists(destination) and not messagebox.askyesno(
                    "Masteries",
                    f"'{filename}' already exists. Replace it?" if not ru else f"'{filename}' уже существует. Заменить?"
                ):
                    continue
                temporary = destination + ".tmp"
                with open(temporary, "wb") as file:
                    file.write(content)
                os.replace(temporary, destination)
                installed.append(filename)
            except Exception as exc:
                failed.append(f"{filename}: {type(exc).__name__}: {exc}")
        self.refresh_masteries_local()
        if failed:
            self.masteries_status.configure(
                text=(f"Installed: {len(installed)}. Failed: " if not ru else
                      f"Установлено: {len(installed)}. Ошибки: ") + "; ".join(failed)
            )
        elif installed:
            self.mstatus(
                f"Installed: {', '.join(installed)}",
                f"Установлено: {', '.join(installed)}"
            )

    def open_masteries_folder(self):
        try:
            os.makedirs(MASTERIES_DIR, exist_ok=True)
            os.startfile(MASTERIES_DIR)
        except Exception as exc:
            self.masteries_status.configure(text=str(exc))

    def refresh_masteries_remote(self):
        self.mstatus("Loading GitHub plugin list...", "Загружаю список плагинов GitHub...")
        def worker():
            try:
                request = urllib.request.Request(
                    MASTERIES_API_URL,
                    headers={"User-Agent": "BOB-Farm/1.4", "Accept": "application/vnd.github+json"}
                )
                with urllib.request.urlopen(request, timeout=25) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                if not isinstance(payload, list):
                    raise ValueError("GitHub returned an invalid folder listing")
                items = [
                    item for item in payload
                    if isinstance(item, dict) and item.get("type") == "file"
                    and str(item.get("name", "")).lower().endswith(".py")
                    and item.get("download_url")
                ]
                items.sort(key=lambda item: str(item.get("name", "")).lower())
                def update():
                    if not self.masteries_remote_list.winfo_exists():
                        return
                    self.masteries_remote_items = items
                    self.masteries_remote_list.delete(0, "end")
                    for item in items:
                        self.masteries_remote_list.insert("end", item["name"])
                    self.mstatus(
                        f"GitHub: {len(items)} plugin file(s) found.",
                        f"GitHub: найдено файлов плагинов: {len(items)}."
                    )
                self.root.after(0, update)
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                self.root.after(0, lambda msg=message: self.mstatus(
                    "GitHub error: " + msg, "Ошибка GitHub: " + msg
                ))
        threading.Thread(target=worker, daemon=True).start()

    def download_masteries_selected(self):
        indices = self.masteries_remote_list.curselection()
        items = [self.masteries_remote_items[i] for i in indices if i < len(self.masteries_remote_items)]
        if not items:
            messagebox.showwarning(
                "Masteries",
                "Select one or more GitHub plugins first." if self.lang != "ru" else
                "Сначала выбери один или несколько плагинов GitHub."
            )
            return
        self.download_masteries(items)

    def download_masteries_all(self):
        if not self.masteries_remote_items:
            messagebox.showwarning(
                "Masteries",
                "Refresh the GitHub list first." if self.lang != "ru" else
                "Сначала обнови список GitHub."
            )
            return
        self.download_masteries(list(self.masteries_remote_items))

    def download_masteries(self, items):
        self.mstatus("Installing plugins...", "Устанавливаю плагины...")
        def worker():
            installed, failed = [], []
            for item in items:
                filename = os.path.basename(str(item.get("name", "")))
                temporary = None
                try:
                    url = str(item.get("download_url", ""))
                    if not re.fullmatch(r"[\w .-]+\.py", filename, flags=re.UNICODE):
                        raise RuntimeError("invalid filename")
                    parsed = urllib.parse.urlparse(url)
                    if parsed.scheme != "https" or parsed.hostname != "raw.githubusercontent.com":
                        raise RuntimeError("download URL is not a trusted GitHub raw URL")
                    request = urllib.request.Request(url, headers={"User-Agent": "BOB-Farm/1.4"})
                    with urllib.request.urlopen(request, timeout=30) as response:
                        content = response.read(MASTERIES_MAX_BYTES + 1)
                    if len(content) > MASTERIES_MAX_BYTES:
                        raise RuntimeError("file is larger than 1 MB")
                    decoded = content.decode("utf-8-sig")
                    ast.parse(decoded, filename=filename)
                    destination = os.path.join(MASTERIES_DIR, filename)
                    os.makedirs(MASTERIES_DIR, exist_ok=True)
                    temporary = destination + ".download"
                    with open(temporary, "wb") as file:
                        file.write(content)
                    os.replace(temporary, destination)
                    installed.append(filename)
                except Exception as exc:
                    if temporary and os.path.exists(temporary):
                        try:
                            os.remove(temporary)
                        except OSError:
                            pass
                    failed.append(f"{filename}: {type(exc).__name__}: {exc}")

            def finish():
                self.refresh_masteries_local()
                if failed:
                    self.masteries_status.configure(
                        text=(f"Installed: {len(installed)}. Failed: " if self.lang != "ru" else
                              f"Установлено: {len(installed)}. Ошибки: ") + "; ".join(failed)
                    )
                else:
                    self.mstatus(
                        f"Installed: {', '.join(installed)}",
                        f"Установлено: {', '.join(installed)}"
                    )
            self.root.after(0, finish)
        threading.Thread(target=worker, daemon=True).start()

    def remove_mastery(self, filename):
        path = os.path.abspath(os.path.join(MASTERIES_DIR, filename))
        root = os.path.abspath(MASTERIES_DIR)
        try:
            if os.path.commonpath([root, path]) != root:
                raise RuntimeError("plugin path is outside the Masteries folder")
            if os.path.isfile(path):
                os.remove(path)
            if filename in self.masteries_enabled:
                self.masteries_enabled.remove(filename)
                save_masteries_state(self.masteries_enabled)
            self.refresh_masteries_local()
            self.mstatus("Plugin removed.", "Плагин удалён.")
        except Exception as exc:
            self.masteries_status.configure(text=str(exc))

    def build_requirements(self, parent):
        outer, body = self.card(parent, "req.title")
        outer.pack(fill="x", pady=(0, 12))
        self.reg(tk.Label(body, bg=CARD, fg=MUTED, font=FONT_S, wraplength=560, justify="left", anchor="w"),
                 "req.note").pack(anchor="w", pady=(0, 8))
        table = tk.Frame(body, bg=CARD)
        table.pack(fill="x")
        table.grid_columnconfigure(0, weight=2, uniform="r")
        table.grid_columnconfigure(1, weight=3, uniform="r")
        table.grid_columnconfigure(2, weight=3, uniform="r")
        for col, key in enumerate(("req.col.component", "req.col.min", "req.col.rec")):
            self.reg(tk.Label(table, bg=CARD, fg=ACCENT, font=FONT_B, anchor="w"), key).grid(row=0, column=col, sticky="w", pady=(0, 6), padx=(0, 10))
        for r, name in enumerate(("os", "python", "cpu", "ram", "gpu", "display", "disk", "deps", "game"), start=1):
            self.reg(tk.Label(table, bg=CARD, fg=TEXT_C, font=FONT_B, anchor="w", justify="left", wraplength=150), f"req.{name}").grid(row=r, column=0, sticky="nw", pady=4, padx=(0, 10))
            self.reg(tk.Label(table, bg=CARD, fg=TEXT_C, font=FONT, anchor="w", justify="left", wraplength=190), f"req.{name}.min").grid(row=r, column=1, sticky="nw", pady=4, padx=(0, 10))
            self.reg(tk.Label(table, bg=CARD, fg=TEXT_C, font=FONT, anchor="w", justify="left", wraplength=190), f"req.{name}.rec").grid(row=r, column=2, sticky="nw", pady=4, padx=(0, 10))
        self.reg(tk.Label(body, bg=CARD, fg=MUTED, font=FONT_S, wraplength=560, justify="left", anchor="w"),
                 "req.usage").pack(anchor="w", pady=(10, 0))

        outer2, body2 = self.card(parent, "pc.title")
        outer2.pack(fill="x", pady=(0, 12))
        info = self.sysinfo
        unk = lambda: self.t("pc.unknown")
        rows = [
            ("pc.cpu", lambda: info["cpu"] or unk()),
            ("pc.cores", lambda: str(info["threads"]) if info["threads"] else unk()),
            ("pc.ram", lambda: f"{info['ram_total']:.1f} GB / {info['ram_free']:.1f} GB" if info["ram_total"] else unk()),
            ("pc.gpu", lambda: info["gpu"] or unk()),
            ("pc.screen", lambda: info["screen"] or unk()),
            ("pc.python", lambda: info["python"]),
            ("pc.os", lambda: info["os"]),
        ]
        grid = tk.Frame(body2, bg=CARD)
        grid.pack(fill="x")
        grid.grid_columnconfigure(1, weight=1)
        self.pc_value_labels = []
        for r, (key, getter) in enumerate(rows):
            self.reg(tk.Label(grid, bg=CARD, fg=MUTED, font=FONT, anchor="w"), key).grid(row=r, column=0, sticky="nw", pady=3, padx=(0, 16))
            val = tk.Label(grid, bg=CARD, fg=TEXT_C, font=FONT, anchor="w", justify="left", wraplength=380)
            val.grid(row=r, column=1, sticky="nw", pady=3)
            self.pc_value_labels.append((val, getter))
        self.verdict_label = tk.Label(body2, bg=CARD, font=FONT_B, anchor="w", justify="left", wraplength=560)
        self.verdict_label.pack(anchor="w", pady=(12, 0))

    def refresh_pc_texts(self):
        for lbl, getter in self.pc_value_labels:
            lbl.configure(text=getter())
        v = pc_verdict(self.sysinfo)
        if v is None:
            self.verdict_label.configure(text="")
        else:
            color = {"rec": GREEN, "min": ACCENT, "low": RED}[v]
            self.verdict_label.configure(text=self.t(f"pc.verdict.{v}"), fg=color)

    # ---------- language ----------
    def apply_language(self):
        for widget, key, option, fmt in self.i18n:
            val = self.t(key)
            if fmt is not None:
                val = val[fmt]
            widget.configure(**{option: val})
        for i, (tab, key) in enumerate(self.tab_widgets):
            self.nb.tab(i, text=self.t(key))
        if hasattr(self, "reports_tab"):
            self.nb.tab(1, text=self.t("tab.reports"))
            self.nb.tab(2, text=self.t("tab.connect"))
            self.nb.tab(3, text=self.t("tab.masteries"))
            self.nb.tab(4, text=self.t("tab.requirements"))
        if hasattr(self, "report_title_label"):
            self.report_title_label.configure(text=self.t("report.title"))
            self.report_refresh_button.configure(text=self.t("report.refresh"))
            self.refresh_report()
        self.apply_connect_language()
        self.apply_server_hop_language()
        self.apply_masteries_language()
        if hasattr(self, "right_tabs"):
            self.right_tabs.tab(0, text=self.t("tab.dashboard"))
            self.right_tabs.tab(1, text=self.t("tab.console"))
            for _key, (caption, title_key) in self.dash_caption_labels.items():
                caption.configure(text=self.t(title_key))
        self.status_label.configure(text=self.t(self.status_key))
        if not self.has_preview:
            self.preview_label.configure(text=self.t("preview.wait" if self.running else "preview.off"), image="")
        self.refresh_pc_texts()

    def on_language(self, _event=None):
        self.lang = "en" if self.lang_box.get() == "English" else "ru"
        self.apply_language()
        try:
            save_config(self.cfg, self.lang)
        except Exception as e:
            self.log("evt.save_failed", err=str(e))

    # ---------- actions ----------
    def _apply_live_config(self, cfg):
        """Apply saved settings to the active engine without restarting the farm."""
        engine = getattr(self, "engine_instance", None)
        if not self.running or engine is None or self.stop_event.is_set():
            return
        # Keep the engine's existing dictionary (it also contains internal runtime keys).
        # Update only public settings, then rebuild cached detector values.
        for key, value in cfg.items():
            engine.c[key] = value
        engine.refresh_settings()
        self.log("evt.settings_live_applied")

    def on_save(self):
        cfg, errors = self.collect()
        if errors:
            self.show_errors(errors)
            return False
        self.cfg = cfg
        try:
            save_config(cfg, self.lang)
            self._apply_live_config(cfg)
            self.log("evt.saved", path=CONFIG_PATH)
        except Exception as e:
            self.log("evt.save_failed", err=str(e))
            return False
        return True

    def on_export_config(self):
        """Export the current settings as a standalone JSON file for sharing."""
        cfg, errors = self.collect()
        if errors:
            self.show_errors(errors)
            return

        path = filedialog.asksaveasfilename(
            title="Export configuration" if self.lang == "en" else "Экспорт конфигурации",
            defaultextension=".json",
            initialfile="bob_farm_config.json",
            filetypes=[("JSON config", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            data = {"config_version": CONFIG_VERSION, "language": self.lang, "settings": cfg, "theme_name": self.theme_name, "theme": self.current_theme_payload()}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.cfg = cfg
            self.log("evt.saved", path=path)
            messagebox.showinfo(
                self.t("title"),
                ("Configuration exported successfully. You can send this JSON file to your friend."
                 if self.lang == "en" else
                 "Конфигурация успешно экспортирована. Теперь можешь отправить этот JSON-файл другу.")
            )
        except Exception as e:
            messagebox.showerror(
                self.t("title"),
                ("Could not export configuration:\n" if self.lang == "en" else
                 "Не удалось экспортировать конфигурацию:\n") + str(e)
            )

    def load_theme(self):
        try:
            with open(THEME_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("name", "Midnight Orange")
            colors = data.get("colors", {})
            if isinstance(colors, dict) and all(k in colors for k in THEME_KEYS):
                return name, {k: str(colors[k]) for k in THEME_KEYS}
            if name in THEMES:
                return name, dict(THEMES[name])
        except Exception:
            pass
        return "Midnight Orange", dict(THEMES["Midnight Orange"])

    def current_theme_payload(self):
        return dict(self.theme_colors)

    def save_theme(self):
        tmp = THEME_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"name": self.theme_name, "colors": self.theme_colors}, f, indent=2, ensure_ascii=False)
        os.replace(tmp, THEME_PATH)

    def on_theme_selected(self, _event=None):
        name = self.theme_box.get()
        if name in THEMES:
            self.apply_theme(name)

    def apply_theme(self, name):
        if name not in THEMES:
            return
        self.theme_name = name
        self.apply_custom_theme(THEMES[name], name)

    def apply_custom_theme(self, colors, name="Custom"):
        global BG, PANEL, CARD, BORDER, TEXT_C, MUTED, ACCENT, ACCENT_D, ENTRY_BG
        if not isinstance(colors, dict) or not all(k in colors for k in THEME_KEYS):
            raise ValueError("Theme must define: " + ", ".join(THEME_KEYS))
        # Validate color strings before applying them to Tk.
        for key in THEME_KEYS:
            value = str(colors[key])
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
                raise ValueError(f"Invalid theme color for {key}: {value}")
        old = {"bg":BG,"panel":PANEL,"card":CARD,"border":BORDER,"text":TEXT_C,"muted":MUTED,
               "accent":ACCENT,"accent_dark":ACCENT_D,"entry":ENTRY_BG}
        new = {k:str(colors[k]) for k in THEME_KEYS}
        mapping = dict(zip(old.values(), new.values()))
        BG, PANEL, CARD, BORDER = new["bg"], new["panel"], new["card"], new["border"]
        TEXT_C, MUTED, ACCENT, ACCENT_D, ENTRY_BG = new["text"], new["muted"], new["accent"], new["accent_dark"], new["entry"]
        self.theme_name, self.theme_colors = name, new
        def recolor(widget):
            for option in ("bg", "background", "fg", "foreground", "activebackground", "activeforeground",
                           "highlightbackground", "insertbackground", "selectbackground", "troughcolor"):
                try:
                    value = widget.cget(option)
                    if value in mapping:
                        widget.configure(**{option:mapping[value]})
                except Exception:
                    pass
            try:
                if hasattr(widget, "_colors"):
                    widget._colors = tuple(mapping.get(v, v) for v in widget._colors)
            except Exception:
                pass
            for child in widget.winfo_children():
                recolor(child)
        recolor(self.root)
        st = ttk.Style(self.root)
        st.configure(".", background=BG, foreground=TEXT_C, font=FONT)
        st.configure("TNotebook", background=BG, borderwidth=0)
        st.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(20, 9), borderwidth=0, font=FONT_B)
        st.map("TNotebook.Tab", background=[("selected", CARD)], foreground=[("selected", ACCENT)])
        st.configure("Dark.TCheckbutton", background=CARD, foreground=TEXT_C, focuscolor=CARD, font=FONT)
        st.configure("TCombobox", fieldbackground=ENTRY_BG, background=PANEL, foreground=TEXT_C, arrowcolor=ACCENT)
        self.root.option_add("*TCombobox*Listbox.background", ENTRY_BG)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT_C)
        self.root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", TEXT_C)
        try:
            self.theme_box.set(name if name in THEMES else "Custom")
            self.save_theme()
        except Exception:
            pass

    def _github_request(self, url, timeout=25):
        req = urllib.request.Request(url, headers={
            "User-Agent": "BOB-Farm-GUI",
            "Accept": "application/vnd.github+json"
        })
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read()

    def _read_git_state(self):
        try:
            with open(GIT_CONFIG_STATE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_git_state(self, data):
        os.makedirs(GIT_CONFIG_DIR, exist_ok=True)
        tmp = GIT_CONFIG_STATE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, GIT_CONFIG_STATE)

    def on_git_configs(self):
        """Show GitHub configs as scrollable rows with an individual SET button."""
        if self.running:
            messagebox.showwarning(self.t("title"),
                "Stop the farm before changing the configuration." if self.lang == "en"
                else "Останови фарм перед сменой конфигурации.")
            return

        win = tk.Toplevel(self.root)
        win.title("GitHub configs" if self.lang == "en" else "GitHub конфиги")
        win.configure(bg=BG)
        win.geometry("620x520")
        win.minsize(480, 360)
        win.transient(self.root)

        heading = "GitHub configurations" if self.lang == "en" else "Конфигурации GitHub"
        tk.Label(win, text=heading, bg=BG, fg=TEXT_C, font=FONT_B).pack(anchor="w", padx=18, pady=(16, 8))
        hint = ("INSTALLED means this exact version is already saved on your PC. Press SET to apply it."
                if self.lang == "en" else
                "INSTALLED означает, что эта версия уже скачана. Нажми SET, чтобы применить её.")
        tk.Label(win, text=hint, bg=BG, fg=MUTED, font=FONT, wraplength=570, justify="left").pack(anchor="w", padx=18, pady=(0, 10))

        list_wrap = tk.Frame(win, bg=BG)
        list_wrap.pack(fill="both", expand=True, padx=18, pady=4)
        canvas = tk.Canvas(list_wrap, bg=BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(list_wrap, orient="vertical", command=canvas.yview)
        rows_frame = tk.Frame(canvas, bg=BG)
        rows_frame.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        window_id = canvas.create_window((0, 0), window=rows_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def wheel(event):
            canvas.yview_scroll(int(-event.delta / 120), "units")
        canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", wheel))
        canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))

        status = tk.Label(win, text=("Loading configs from GitHub..." if self.lang == "en" else "Загружаю конфиги с GitHub..."),
                          bg=BG, fg=MUTED, font=FONT, anchor="w")
        status.pack(fill="x", padx=18, pady=(8, 2))
        progress = ttk.Progressbar(win, mode="indeterminate", length=200)
        progress.pack(fill="x", padx=18, pady=(0, 10))
        progress.start(12)
        footer = tk.Frame(win, bg=BG)
        footer.pack(fill="x", padx=18, pady=(0, 16))
        tk.Button(footer, text=("REFRESH" if self.lang == "en" else "ОБНОВИТЬ СПИСОК"), command=lambda: refresh(),
                  bg=CARD, fg=TEXT_C, relief="flat", padx=14, pady=8).pack(side="left")
        tk.Button(footer, text=("CLOSE" if self.lang == "en" else "ЗАКРЫТЬ"), command=win.destroy,
                  bg=CARD, fg=TEXT_C, relief="flat", padx=14, pady=8).pack(side="right")

        def set_status(message):
            if win.winfo_exists():
                status.configure(text=message)

        def apply_local(path, name):
            try:
                self._apply_config_file(path)
                set_status((f"SET: {name} — configuration applied." if self.lang == "en" else f"SET: {name} — конфигурация применена."))
            except Exception as exc:
                messagebox.showerror("GitHub configs", ("Could not apply config:\n" if self.lang == "en" else "Не удалось применить конфиг:\n") + str(exc), parent=win)

        def download_or_set(item, button):
            name = item["name"]
            sha = item.get("sha", "")
            url = item.get("download_url")
            if not url:
                messagebox.showerror("GitHub configs", "No download URL was provided by GitHub.", parent=win)
                return
            os.makedirs(GIT_CONFIG_DIR, exist_ok=True)
            target = os.path.join(GIT_CONFIG_DIR, os.path.basename(name))
            state = self._read_git_state()
            old = state.get(name, {}) if isinstance(state.get(name, {}), dict) else {}
            already_current = os.path.isfile(target) and old.get("sha") == sha
            if already_current:
                apply_local(target, name)
                return
            if os.path.isfile(target) and old.get("sha") and old.get("sha") != sha:
                question = (f"{name} has a newer version on GitHub. Download the update?" if self.lang == "en"
                            else f"Для {name} на GitHub есть новая версия. Скачать обновление?")
                if not messagebox.askyesno("Config update", question, parent=win):
                    return

            button.configure(state="disabled", text=("DOWNLOADING..." if self.lang == "en" else "ЗАГРУЗКА..."))
            progress.stop()
            progress.configure(mode="indeterminate")
            progress.start(12)
            set_status((f"Downloading {name}..." if self.lang == "en" else f"Скачиваю {name}..."))

            def worker():
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "BOB-Farm-GUI"})
                    with urllib.request.urlopen(req, timeout=35) as response:
                        content = response.read()
                    parsed = json.loads(content.decode("utf-8-sig"))
                    if not isinstance(parsed, dict):
                        raise ValueError("JSON config must contain an object.")
                    # Validate before replacing the existing downloaded file.
                    saved = parsed.get("settings", parsed)
                    if not isinstance(saved, dict):
                        raise ValueError("Config settings must be a JSON object.")
                    candidate = dict(DEFAULTS)
                    for (_group, key, kind, _default, lo, hi) in SCHEMA:
                        if key in saved:
                            candidate[key] = parse_value(kind, saved[key], lo, hi)
                    errors = cross_check(candidate)
                    if errors:
                        raise ValueError("Invalid settings: " + ", ".join(key for key, _ in errors))
                    tmp = target + ".download"
                    with open(tmp, "wb") as file:
                        file.write(content)
                    os.replace(tmp, target)
                    state = self._read_git_state()
                    state[name] = {"sha": sha, "downloaded_at": int(time.time())}
                    self._write_git_state(state)
                    self.root.after(0, lambda: finish_download(target, name, button))
                except Exception as exc:
                    self.root.after(0, lambda err=str(exc): download_failed(button, err))
            threading.Thread(target=worker, daemon=True).start()

        def finish_download(path, name, button):
            if not win.winfo_exists():
                return
            progress.stop()
            progress.configure(mode="determinate", value=100)
            button.configure(state="normal", text=("SET" if self.lang == "en" else "ПРИМЕНИТЬ"))
            set_status((f"DOWNLOADED: {name}" if self.lang == "en" else f"СКАЧАНО: {name}"))
            apply_local(path, name)
            # Refresh badges so the downloaded item immediately shows INSTALLED.
            refresh()

        def download_failed(button, error):
            if not win.winfo_exists():
                return
            progress.stop()
            button.configure(state="normal", text=("SET" if self.lang == "en" else "ПРИМЕНИТЬ"))
            set_status(("Download failed: " if self.lang == "en" else "Ошибка загрузки: ") + error)

        def refresh():
            for child in rows_frame.winfo_children():
                child.destroy()
            progress.configure(mode="indeterminate")
            progress.start(12)
            set_status("Loading configs from GitHub..." if self.lang == "en" else "Загружаю конфиги с GitHub...")

            def worker():
                try:
                    raw = self._github_request(GITHUB_API_CONFIGS, timeout=30)
                    data = json.loads(raw.decode("utf-8"))
                    if not isinstance(data, list):
                        raise ValueError("GitHub returned an invalid folder listing.")
                    files = [x for x in data if isinstance(x, dict) and x.get("type") == "file"
                             and str(x.get("name", "")).lower().endswith(".json") and x.get("download_url")]
                    files.sort(key=lambda x: x.get("name", "").lower())
                    self.root.after(0, lambda: populate(files))
                except Exception as exc:
                    self.root.after(0, lambda err=str(exc): (progress.stop(), set_status(("Could not load configs: " if self.lang == "en" else "Не удалось загрузить конфиги: ") + err)))
            threading.Thread(target=worker, daemon=True).start()

        def populate(files):
            if not win.winfo_exists():
                return
            progress.stop()
            state = self._read_git_state()
            for item in files:
                name, sha = item.get("name", "config.json"), item.get("sha", "")
                local_path = os.path.join(GIT_CONFIG_DIR, os.path.basename(name))
                old = state.get(name, {}) if isinstance(state.get(name, {}), dict) else {}
                installed = os.path.isfile(local_path) and old.get("sha") == sha
                row = tk.Frame(rows_frame, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
                row.pack(fill="x", pady=4)
                tk.Label(row, text=name, bg=CARD, fg=TEXT_C, font=FONT_B, anchor="w").pack(side="left", fill="x", expand=True, padx=12, pady=11)
                badge_text = (("INSTALLED" if installed else ("UPDATE AVAILABLE" if os.path.isfile(local_path) else "NOT INSTALLED")) if self.lang == "en" else ("УСТАНОВЛЕНО" if installed else ("ЕСТЬ ОБНОВЛЕНИЕ" if os.path.isfile(local_path) else "НЕ УСТАНОВЛЕНО")))
                badge_color = ACCENT if installed else MUTED
                tk.Label(row, text=badge_text, bg=CARD, fg=badge_color, font=FONT_B).pack(side="left", padx=8)
                btn = tk.Button(row, text=("SET" if self.lang == "en" else "ПРИМЕНИТЬ"), bg=ACCENT, fg="#17120a", activebackground=ACCENT_D,
                                relief="flat", padx=18, pady=7, cursor="hand2")
                btn.configure(command=lambda data=item, b=btn: download_or_set(data, b))
                btn.pack(side="right", padx=10, pady=7)
            if not files:
                tk.Label(rows_frame, text=("No .json files found in CONFIGS." if self.lang == "en" else "В CONFIGS не найдено .json файлов."),
                         bg=BG, fg=MUTED, font=FONT).pack(anchor="w", pady=12)
            set_status((f"{len(files)} JSON config(s) found." if self.lang == "en" else f"Найдено JSON-конфигов: {len(files)}"))

        refresh()

    def _git_download_complete(self, win, path, name, status, progress, buttons):
        # Kept for compatibility with older calls; the current GitHub window uses row actions.
        progress.configure(value=100)
        status.configure(text=(f"DOWNLOADED: {name}" if self.lang == "en" else f"СКАЧАНО: {name}"))
        self._apply_config_file(path)

    def _apply_config_file(self, path):
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        if not isinstance(data, dict): raise ValueError("The config file must contain a JSON object.")
        saved = data.get("settings", data)
        if not isinstance(saved, dict): raise ValueError("The config settings must be a JSON object.")
        cfg = dict(DEFAULTS)
        for (_, key, kind, default, lo, hi) in SCHEMA:
            if key in saved: cfg[key] = parse_value(kind, saved[key], lo, hi)
        errors = cross_check(cfg)
        if errors: raise ValueError("Invalid settings: " + ", ".join(key for key, _ in errors))
        save_config(cfg, self.lang)
        self.cfg = cfg
        self.fill_fields(cfg)
        self._apply_live_config(cfg)
        theme_data = data.get("theme")
        if isinstance(theme_data, dict):
            theme_colors = theme_data.get("colors", theme_data)
            theme_name = theme_data.get("name", data.get("theme_name", "Custom"))
            self.apply_custom_theme(theme_colors, theme_name)
        elif isinstance(theme_data, str) and theme_data in THEMES:
            self.apply_theme(theme_data)
        self.log("evt.saved", path=CONFIG_PATH)

    def on_check_updates(self):
        win = tk.Toplevel(self.root)
        win.title("BOB Farm updates" if self.lang == "en" else "Обновления BOB Farm")
        win.configure(bg=BG)
        win.geometry("520x250")
        win.minsize(460, 220)
        win.transient(self.root)

        tk.Label(win, text=("BOB Farm — Software updates" if self.lang == "en" else "BOB Farm — обновления программы"), bg=BG, fg=TEXT_C, font=("Segoe UI Semibold", 15)).pack(pady=(20, 5))
        tk.Label(win, text=(f"Installed version: {APP_VERSION}" if self.lang == "en" else f"Установленная версия: {APP_VERSION}"), bg=BG, fg=MUTED, font=FONT).pack(pady=(0, 12))
        status = tk.Label(win, text=("Checking GitHub for a new version..." if self.lang == "en" else "Проверяю GitHub на наличие новой версии..."),
                          bg=BG, fg=TEXT_C, font=FONT, wraplength=470, justify="center")
        status.pack(fill="x", padx=20, pady=8)
        progress = ttk.Progressbar(win, mode="indeterminate", length=400)
        progress.pack(fill="x", padx=35, pady=8)
        progress.start(12)
        actions = tk.Frame(win, bg=BG)
        actions.pack(fill="x", padx=20, pady=(12, 18))
        close_btn = tk.Button(actions, text=("CLOSE" if self.lang == "en" else "ЗАКРЫТЬ"), command=win.destroy,
                              bg=CARD, fg=TEXT_C, relief="flat", padx=18, pady=9)
        close_btn.pack(side="right")

        def worker():
            try:
                remote = self._github_request(GITHUB_GUI_RAW, timeout=35).decode("utf-8-sig")
                match = re.search(r'^APP_VERSION\s*=\s*[\"\']([^\"\']+)[\"\']', remote, re.MULTILINE)
                if not match:
                    raise ValueError('APP_VERSION was not found in GUI/bob_farm_gui.py.')
                remote_version = match.group(1).strip()
                self.root.after(0, lambda: finish_check(remote, remote_version))
            except Exception as exc:
                self.root.after(0, lambda err=str(exc): (progress.stop(), status.configure(text=("Could not check for updates: " if self.lang == "en" else "Не удалось проверить обновления: ") + err)))

        def finish_check(remote_source, remote_version):
            if not win.winfo_exists():
                return
            progress.stop()
            if remote_version == APP_VERSION:
                status.configure(text=(f"You're up to date. Version {APP_VERSION} is installed." if self.lang == "en" else f"Обновлений нет. Установлена версия {APP_VERSION}."))
                return
            status.configure(text=(f"New version available: {APP_VERSION}  →  {remote_version}" if self.lang == "en" else f"Доступна новая версия: {APP_VERSION}  →  {remote_version}"))
            update_btn = tk.Button(actions, text=("DOWNLOAD UPDATE" if self.lang == "en" else "СКАЧАТЬ ОБНОВЛЕНИЕ"),
                                   bg=ACCENT, fg="#17120a", activebackground=ACCENT_D, relief="flat", padx=16, pady=9)
            update_btn.pack(side="left")

            def install_update():
                try:
                    compile(remote_source, "bob_farm_gui.py", "exec")
                    current_file = os.path.abspath(__file__)
                    tmp = current_file + ".update.tmp"
                    with open(tmp, "w", encoding="utf-8") as file:
                        file.write(remote_source)
                    os.replace(tmp, current_file)
                    status.configure(text=(f"Update {remote_version} downloaded successfully. Restart BOB Farm to use it." if self.lang == "en"
                                           else f"Обновление {remote_version} скачано. Перезапусти BOB Farm."))
                    update_btn.configure(state="disabled", text=("UPDATED" if self.lang == "en" else "ОБНОВЛЕНО"))
                except Exception as exc:
                    status.configure(text=("Update failed: " if self.lang == "en" else "Ошибка обновления: ") + str(exc))
            update_btn.configure(command=install_update)

        threading.Thread(target=worker, daemon=True).start()

    def on_choose_config(self):
        if self.running:
            messagebox.showwarning(
                self.t("title"),
                "Stop the farm before changing the configuration." if self.lang == "en"
                else "Останови фарм перед сменой конфигурации."
            )
            return

        path = filedialog.askopenfilename(
            title="Choose configuration" if self.lang == "en" else "Выбери конфигурацию",
            filetypes=[
                ("JSON config", "*.json"),
                ("All files", "*.*")
            ]
        )
        if not path:
            return

        try:
            self._apply_config_file(path)
            messagebox.showinfo(
                self.t("title"),
                "Configuration loaded and saved as the main config."
                if self.lang == "en"
                else "Конфигурация загружена и сохранена как основной конфиг."
            )
        except Exception as e:
            messagebox.showerror(
                self.t("title"),
                ("Could not load configuration:\n" if self.lang == "en"
                 else "Не удалось загрузить конфигурацию:\n") + str(e)
            )

    def on_reset(self):
        self.fill_fields(DEFAULTS)
        self.log("evt.reset")

    def show_errors(self, errors):
        lines = []
        for key, text in errors:
            lines.append(f"- {self.t(key)[0]}: {text}")
        messagebox.showerror(self.t("msg.invalid.title"), self.t("msg.invalid.head") + "\n\n" + "\n".join(lines))

    def on_start(self):
        if self.running:
            return
        if not self.on_save():
            return
        # OCR is optional. The farm itself must never stop or ask for Tesseract at startup.
        # Error-277 OCR monitoring is skipped automatically when Tesseract is unavailable.
        plugin_paths = self.enabled_plugin_paths() if self.cfg["feat_plugins"] else []
        if self.masteries_enabled and not self.cfg["feat_plugins"]:
            question = (
                "Plugins are ticked in Masteries, but 'Run Masteries plugins' is OFF in Settings. "
                "Enable plugins for this session?"
                if self.lang == "en" else
                "В Masteries отмечены плагины, но в Настройках выключено «Запускать плагины Masteries». "
                "Включить плагины для этой сессии?"
            )
            if messagebox.askyesno("Masteries", question):
                plugin_paths = self.enabled_plugin_paths()
        if not self.cfg["builtin_farm"] and not plugin_paths:
            messagebox.showwarning("BOB Farm",
                                   "Включи 'Встроенный фарм портала' или отметь плагин во вкладке Masteries." if self.lang == "ru"
                                   else "Turn on 'Built-in portal farm' or tick a plugin in the Masteries tab.")
            return
        run_cfg = dict(self.cfg)
        self._disconnect_pause = threading.Event()
        run_cfg["_pause_event"] = self._disconnect_pause
        if plugin_paths:
            names = "\n".join("  - " + plugin_info(p)["name"] for p in plugin_paths)
            if self.lang == "ru":
                text = f"Обнаружены включённые плагины:\n{names}\n\nВы хотите продолжить?"
            else:
                text = f"Enabled plugins detected:\n{names}\n\nDo you want to continue?"
            if not messagebox.askyesno("Masteries", text):
                return
            # the plugins do their own actions: the built-in E / reset are skipped (settings file is not changed)
            run_cfg["feat_press_e"] = False
            run_cfg["feat_reset"] = False
        self.stop_event.clear()
        self.pending_png, self.has_preview = None, False
        self.session_started = time.monotonic()
        self.session_finished = None
        if hasattr(self, "_last_portal_event"):
            self._last_portal_event = time.time()
        self.session_portals = self.session_noportal = self.session_errors = 0
        self.event_history = []
        self.last_event_text = self.t("dash.waiting")
        self.update_dashboard()
        engine = Engine(run_cfg, self.emit, self.set_preview, self.stop_event, plugin_paths)
        self.engine_instance = engine
        self.thread = threading.Thread(target=engine.run, daemon=True)
        self.thread.start()
        focus_roblox()                                   # bring Roblox to the front right away
        self.running = True
        self.set_status("status.starting", ACCENT)
        self.set_enabled(self.start_btn, False)
        self.set_enabled(self.stop_btn, True)
        self.preview_label.configure(text=self.t("preview.wait" if self.cfg["show_preview"] else "preview.off"), image="")

    def on_stop(self):
        if self.running:
            self.stop_event.set()
            self.set_status("status.stopping", ACCENT)

    def on_close(self):
        self.stop_event.set()
        self.telegram_stop.set()
        self.stop_server_hop()
        try:
            cfg, errors = self.collect()
            if not errors:
                save_config(cfg, self.lang)
        except Exception:
            pass
        self.root.destroy()

    def set_status(self, key, color):
        self.status_key = key
        self.status_label.configure(text=self.t(key))
        self.dot.configure(fg=color)
        if hasattr(self, "dash_labels"):
            self.dash_labels["status"].configure(text=self.t(key), fg=color)

    # ---------- thread-safe messaging ----------
    def emit(self, key, **kw):
        self.q.put(("evt", key, kw))

    def set_preview(self, png):
        self.q.put(("preview", png, None))

    def log(self, key, **kw):
        self.q.put(("evt", key, kw))

    def poll(self):
        try:
            while True:
                kind, a, b = self.q.get_nowait()
                if kind == "evt":
                    self.write_log(a, b)
                    if a == "evt.capture_window" or a == "evt.capture_monitor":
                        self.set_status("status.running", GREEN)
                    elif a == "evt.stopped":
                        self.on_engine_stopped()
                elif kind == "preview":
                    self.pending_png = a
        except queue.Empty:
            pass
        if self.pending_png is not None and self.running:
            try:
                self.photo = tk.PhotoImage(data=base64.b64encode(self.pending_png))
                self.preview_label.configure(image=self.photo, text="", height=self.photo.height())
                self.has_preview = True
            except tk.TclError:
                pass
        self.pending_png = None
        now = time.monotonic()
        if now - self._last_dash_refresh >= 1.0:
            self.update_dashboard()
            self.refresh_report()
            self._last_dash_refresh = now
        self.root.after(120, self.poll)

    def clear_console(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.log_line_count = 0

    def update_dashboard(self):
        if not hasattr(self, "dash_labels"):
            return
        end_time = self.session_finished if self.session_finished is not None else time.monotonic()
        elapsed = int(end_time - self.session_started) if self.session_started else 0
        hours, rem = divmod(elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        self.dash_labels["elapsed"].configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.dash_labels["portals"].configure(text=str(self.session_portals))
        self.dash_labels["noportal"].configure(text=str(self.session_noportal))
        self.dash_labels["errors"].configure(text=str(self.session_errors))
        self.dash_labels["last"].configure(text=self.last_event_text)

    def write_log(self, key, kw):
        line = time.strftime("%H:%M:%S  ") + self.t(key, **(kw or {}))
        self.last_event_text = line
        self.event_history.append({"time": time.time(), "key": key})
        if len(self.event_history) > 500:
            del self.event_history[:len(self.event_history) - 500]
        if key == "evt.entered":
            self.session_portals += 1
        elif key == "evt.noportal":
            self.session_noportal += 1
        elif key == "evt.error":
            self.session_errors += 1
        self.update_dashboard()
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line + "\n")
        self.log_line_count += 1
        if self.log_line_count > self.log_limit:
            self.log_text.delete("1.0", "2.0")
            self.log_line_count -= 1
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def on_engine_stopped(self):
        self.running = False
        self.engine_instance = None
        if self.session_started is not None and self.session_finished is None:
            self.session_finished = time.monotonic()
        self.pending_png, self.has_preview = None, False
        self.set_status("status.idle", MUTED)
        self.set_enabled(self.start_btn, True)
        self.set_enabled(self.stop_btn, False)
        self.preview_label.configure(image="", text=self.t("preview.off"), height=12)

    # ---------- allow screenshots / screen recording ----------
    def exclude_from_capture(self):
        # WDA_NONE (0) explicitly allows Windows screenshots and screen capture.
        try:
            self.root.update_idletasks()
            hwnd = user32.GetParent(self.root.winfo_id())
            user32.SetWindowDisplayAffinity(hwnd, 0)
        except Exception:
            pass



# ============================== V1.5 RECOVERY / PROFILES / TELEGRAM STATS ==============================
def _safe_json_read(path, fallback):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else fallback
    except Exception:
        return fallback


def _save_json_atomic(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _app_stats_init(self):
    self.stats_data = _safe_json_read(STATS_PATH, {"total": 0, "started_at": time.time(), "events": []})
    self.stats_data.setdefault("total", 0)
    self.stats_data.setdefault("events", [])
    self.stats_data.setdefault("started_at", time.time())
    self.stats_data.setdefault("daily", {})
    self.stats_data.setdefault("session_started_at", time.time())
    if not self.stats_data["daily"]:
        for event in self.stats_data.get("events", []):
            if event.get("k") == "evt.entered":
                try:
                    day=time.strftime("%Y-%m-%d",time.localtime(float(event.get("t",0))))
                    self.stats_data["daily"][day]=int(self.stats_data["daily"].get(day,0))+1
                except Exception:
                    pass
    self._stats_lock = threading.Lock()
    self._last_portal_event = time.time()
    self._last_watchdog_action = 0.0
    self._reconnect_thread = None
    self._reconnect_stop = threading.Event()
    self._reconnect_busy = threading.Event()
    self._disconnect_pause = threading.Event()
    self._disconnect_last_seen = 0.0
    self._roblox_process_seen = False
    self._roblox_missing_since = None
    self._active_profile = "Default"


def _stats_record(self, key):
    now = time.time()
    with self._stats_lock:
        events = self.stats_data.setdefault("events", [])
        if key == "evt.entered":
            self.stats_data["total"] = int(self.stats_data.get("total", 0)) + 1
            self._last_portal_event = now
            day = time.strftime("%Y-%m-%d", time.localtime(now))
            daily = self.stats_data.setdefault("daily", {})
            daily[day] = int(daily.get(day, 0)) + 1
        events.append({"t": now, "k": key})
        # Retain 90 days of detailed events for short-term rates; lifetime totals and
        # daily aggregates remain saved indefinitely for the long-term chart.
        cutoff = now - 90 * 24 * 3600
        self.stats_data["events"] = [e for e in events if float(e.get("t", 0)) >= cutoff][-100000:]
        self.stats_data["updated_at"] = now
        try:
            _save_json_atomic(STATS_PATH, self.stats_data)
        except Exception:
            pass


def _stats_snapshot(self):
    now = time.time()
    with self._stats_lock:
        events = list(self.stats_data.get("events", []))
        total = int(self.stats_data.get("total", 0))
    def count_since(seconds):
        return sum(1 for e in events if e.get("k") == "evt.entered" and now - float(e.get("t", 0)) <= seconds)
    return total, count_since(600), count_since(3600), events


def _stats_png(self, lang=None):
    lang = lang or self.lang
    total, ten, hour, _ = self._stats_snapshot()
    with self._stats_lock:
        daily = dict(self.stats_data.get("daily", {}))
    width, height = 1100, 650
    img = Image.new("RGB", (width, height), (28, 30, 36))
    draw = ImageDraw.Draw(img)
    font_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    def get_font(size, bold=False):
        names = (["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"])
        for name in names:
            path = os.path.join(font_dir, name)
            try:
                if os.path.isfile(path): return ImageFont.truetype(path, size)
            except Exception:
                pass
        try: return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
        except Exception: return ImageFont.load_default()
    title_font, metric_font, small_font = get_font(29, True), get_font(22, True), get_font(16)
    white, green, muted, grid = (245,245,245), (70,210,130), (165,170,180), (65,68,76)
    if lang == "ru":
        title = "BOB FARM — СТАТИСТИКА ПОРТАЛОВ"
        labels = [(f"ВСЕГО: {total}", 40), (f"ЗА 10 МИН: {ten}", 390), (f"ЗА ЧАС: {hour}", 760)]
        caption = "ВХОДЫ В ПОРТАЛ ПО ДНЯМ (СОХРАНЁННАЯ ИСТОРИЯ)"
        empty = "Пока нет записанных порталов"
        footer = "TOTAL сохраняется между запусками программы"
    else:
        title = "BOB FARM — PORTAL STATISTICS"
        labels = [(f"TOTAL: {total}", 40), (f"LAST 10 MIN: {ten}", 390), (f"LAST 1 HOUR: {hour}", 760)]
        caption = "PORTAL ENTRIES BY DAY (SAVED HISTORY)"
        empty = "No portal events recorded yet"
        footer = "Lifetime total is saved between app restarts"
    draw.text((35, 25), title, font=title_font, fill=white)
    for label, x in labels:
        draw.text((x, 90), label, font=metric_font, fill=green)
    left, right, top, bottom = 70, 1040, 230, 550
    for i in range(5):
        y = bottom - i*(bottom-top)//4
        draw.line((left,y,right,y), fill=grid, width=1)
    days = sorted(daily.items())[-60:]
    if days:
        values = [max(0,int(v)) for _,v in days]
        peak = max(1, max(values))
        step = (right-left)/max(1,len(values))
        bar_w = max(2, int(step*0.65))
        for i, value in enumerate(values):
            x = left + int(i*step)
            y = bottom - int(value/peak*(bottom-top))
            draw.rectangle((x,y,min(right,x+bar_w),bottom), fill=green)
        draw.text((left,top-30), caption, font=small_font, fill=muted)
        draw.text((left,bottom+12), f"{days[0][0]}  —  {days[-1][0]}", font=small_font, fill=muted)
    else:
        draw.text((left,390), empty, font=metric_font, fill=muted)
    draw.text((35,615), footer, font=small_font, fill=muted)
    output=io.BytesIO()
    img.save(output,format="PNG")
    return output.getvalue()


def _stats_text(self, lang=None):
    lang = lang or self.lang
    total, ten, hour, _ = self._stats_snapshot()
    if lang == "ru":
        return (f"📊 СТАТИСТИКА BOB FARM\n\n"
                f"TOTAL за всё время: {total}\n"
                f"За последние 10 минут: {ten}\n"
                f"За последний час: {hour}\n"
                f"Сессия: {self._session_duration_text()}\n"
                f"Порталов в час (текущий час): {hour}")
    return (f"📊 BOB FARM STATISTICS\n\n"
            f"TOTAL all time: {total}\n"
            f"Last 10 minutes: {ten}\n"
            f"Last hour: {hour}\n"
            f"Session: {self._session_duration_text()}\n"
            f"Portals per hour (current hour): {hour}")


def _profile_save(self, name):
    name = re.sub(r"[^A-Za-zА-Яа-яЁё0-9 _.-]", "", str(name)).strip()[:40]
    if not name:
        raise ValueError("Profile name is empty")
    os.makedirs(PROFILES_DIR, exist_ok=True)
    cfg, errors = self.collect()
    if errors:
        raise ValueError("Fix invalid settings before saving a profile")
    payload = {"version": 1, "settings": cfg, "plugins": sorted(self.masteries_enabled)}
    _save_json_atomic(os.path.join(PROFILES_DIR, name + ".json"), payload)
    self._active_profile = name
    return name


def _profile_load(self, name):
    path = os.path.join(PROFILES_DIR, os.path.basename(str(name)) + ".json")
    if not path.lower().endswith(".json") or not os.path.isfile(path):
        raise FileNotFoundError(path)
    data = _safe_json_read(path, {})
    saved = data.get("settings", {})
    if not isinstance(saved, dict):
        raise ValueError("Invalid profile settings")
    merged = dict(self.cfg)
    # Only values explicitly stored in this profile are applied. Missing keys keep their current values.
    for _, key, kind, default, lo, hi in SCHEMA:
        if key in saved:
            merged[key] = parse_value(kind, saved[key], lo, hi)
    errors = cross_check(merged)
    if errors:
        raise ValueError("Profile contains conflicting settings")
    self.cfg = merged
    self.fill_fields(merged)
    self.on_save()
    plugin_names = data.get("plugins")
    if isinstance(plugin_names, list):
        available = {os.path.basename(p) for p in self._plugin_paths()}
        self.masteries_enabled = {x for x in plugin_names if x in available}
        save_masteries_state(self.masteries_enabled)
        self.refresh_masteries_local()
    self._active_profile = os.path.splitext(os.path.basename(path))[0]
    return self._active_profile


def _plugin_paths(self):
    os.makedirs(MASTERIES_DIR, exist_ok=True)
    return [os.path.join(MASTERIES_DIR, f) for f in os.listdir(MASTERIES_DIR) if f.lower().endswith(".py")]


def _profiles_dialog(self):
    ru = self.lang == "ru"
    win = tk.Toplevel(self.root)
    win.title("Profiles" if not ru else "Профили")
    win.configure(bg=BG)
    win.geometry("700x520")
    win.minsize(620, 460)
    win.transient(self.root)
    win.grab_set()

    title = "Profiles" if not ru else "Профили"
    subtitle = ("Save complete setups and switch between them instantly." if not ru
                else "Сохраняй полные наборы настроек и переключайся между ними в один клик.")
    tk.Label(win, text=title, bg=BG, fg=TEXT_C, font=("Segoe UI Semibold", 22)).pack(anchor="w", padx=24, pady=(20, 2))
    tk.Label(win, text=subtitle, bg=BG, fg=MUTED, font=FONT).pack(anchor="w", padx=26, pady=(0, 16))

    content = tk.Frame(win, bg=BG)
    content.pack(fill="both", expand=True, padx=22, pady=(0, 14))
    left = tk.Frame(content, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    left.pack(side="left", fill="both", expand=True, padx=(0, 10))
    right = tk.Frame(content, bg=CARD, highlightbackground=BORDER, highlightthickness=1, width=245)
    right.pack(side="right", fill="y")
    right.pack_propagate(False)

    tk.Label(left, text=("SAVED PROFILES" if not ru else "СОХРАНЁННЫЕ ПРОФИЛИ"), bg=CARD, fg=MUTED,
             font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=16, pady=(15, 8))
    listing = tk.Listbox(left, bg=ENTRY_BG, fg=TEXT_C, selectbackground=ACCENT,
                         selectforeground="#111318", activestyle="none", relief="flat",
                         borderwidth=0, highlightthickness=0, font=("Segoe UI Semibold", 11),
                         height=12)
    listing.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    tk.Label(right, text=("PROFILE DETAILS" if not ru else "ДЕЙСТВИЯ С ПРОФИЛЕМ"), bg=CARD, fg=MUTED,
             font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=15, pady=(15, 8))
    name_var = tk.StringVar(value="")
    tk.Label(right, text=("Profile name" if not ru else "Название профиля"), bg=CARD, fg=TEXT_C, font=FONT_B).pack(anchor="w", padx=15, pady=(4, 5))
    entry = tk.Entry(right, textvariable=name_var, bg=ENTRY_BG, fg=TEXT_C, insertbackground=TEXT_C,
                     relief="flat", font=FONT, highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=ACCENT)
    entry.pack(fill="x", padx=15, ipady=8)
    detail = tk.Label(right, text=("Choose a profile or enter a new name." if not ru
                                   else "Выбери профиль или введи новое название."),
                      bg=CARD, fg=MUTED, font=FONT_S, justify="left", wraplength=205)
    detail.pack(anchor="w", padx=15, pady=(10, 12))

    def refresh(select_name=None):
        listing.delete(0, "end")
        os.makedirs(PROFILES_DIR, exist_ok=True)
        names = sorted(os.path.splitext(f)[0] for f in os.listdir(PROFILES_DIR) if f.lower().endswith(".json"))
        for name in names:
            listing.insert("end", ("◆  " if name == self._active_profile else "   ") + name)
        if select_name in names:
            idx = names.index(select_name)
            listing.selection_set(idx)
            listing.activate(idx)
            name_var.set(select_name)
        elif names and not name_var.get():
            listing.selection_set(0)
            listing.activate(0)
            name_var.set(names[0])
        if not names:
            detail.configure(text=("No profiles saved yet." if not ru else "Пока нет сохранённых профилей."))
        return names

    def selected_name():
        sel = listing.curselection()
        if not sel: return None
        raw = listing.get(sel[0]).strip()
        return raw[1:].strip() if raw.startswith("◆") else raw.strip()

    def choose(_=None):
        value = selected_name()
        if value:
            name_var.set(value)
            path = os.path.join(PROFILES_DIR, value + ".json")
            data = _safe_json_read(path, {})
            count = len(data.get("settings", {})) if isinstance(data.get("settings", {}), dict) else 0
            plugins = len(data.get("plugins", [])) if isinstance(data.get("plugins", []), list) else 0
            detail.configure(text=(f"{count} settings · {plugins} plugins" if not ru else f"Настроек: {count} · Плагинов: {plugins}"))
    listing.bind("<<ListboxSelect>>", choose)

    def action_button(text, command, primary=False, danger=False):
        bg = ACCENT if primary else ("#48242a" if danger else ENTRY_BG)
        fg = "#111318" if primary else ("#ff8792" if danger else TEXT_C)
        b = tk.Button(right, text=text, command=command, bg=bg, fg=fg, activebackground=bg,
                      activeforeground=fg, relief="flat", bd=0, cursor="hand2",
                      font=("Segoe UI Semibold", 9), padx=12, pady=9)
        b.pack(fill="x", padx=15, pady=4)
        return b

    def save_profile():
        try:
            value = self._profile_save(name_var.get())
            refresh(value)
            detail.configure(text=("Profile saved successfully." if not ru else "Профиль успешно сохранён."))
        except Exception as exc:
            messagebox.showerror(title, str(exc), parent=win)

    def load_profile():
        value = name_var.get().strip() or selected_name()
        if not value:
            messagebox.showwarning(title, ("Select a profile first." if not ru else "Сначала выбери профиль."), parent=win)
            return
        try:
            self._profile_load(value)
            refresh(value)
            detail.configure(text=("This profile is now active." if not ru else "Этот профиль теперь активен."))
        except Exception as exc:
            messagebox.showerror(title, str(exc), parent=win)

    def delete_profile():
        value = selected_name() or name_var.get().strip()
        if not value: return
        ask = (f"Delete profile '{value}'?" if not ru else f"Удалить профиль «{value}»?")
        if not messagebox.askyesno(title, ask, parent=win): return
        path = os.path.join(PROFILES_DIR, os.path.basename(value) + ".json")
        try:
            if os.path.isfile(path): os.remove(path)
            refresh()
            detail.configure(text=("Profile deleted." if not ru else "Профиль удалён."))
        except Exception as exc:
            messagebox.showerror(title, str(exc), parent=win)

    action_button(("SAVE CURRENT" if not ru else "СОХРАНИТЬ ТЕКУЩИЕ"), save_profile, primary=True)
    action_button(("LOAD PROFILE" if not ru else "ЗАГРУЗИТЬ ПРОФИЛЬ"), load_profile)
    action_button(("DELETE PROFILE" if not ru else "УДАЛИТЬ ПРОФИЛЬ"), delete_profile, danger=True)
    tk.Frame(right, bg=BORDER, height=1).pack(fill="x", padx=15, pady=12)
    tk.Label(right, text=("The profile stores your settings and enabled Masteries plugins. Missing settings in an older profile are left unchanged." if not ru
                          else "Профиль хранит настройки и включённые плагины Masteries. Отсутствующие параметры старого профиля не изменяются."),
             bg=CARD, fg=MUTED, font=FONT_S, wraplength=210, justify="left").pack(anchor="w", padx=15, pady=(0, 10))
    action_button(("CLOSE" if not ru else "ЗАКРЫТЬ"), win.destroy)
    refresh(self._active_profile if self._active_profile != "Default" else None)


def _tg_settings_keyboard(self, chat_id, lang=None):
    lang = lang or self.lang
    features = [
        ("capture", "📷 Capture", "📷 Скриншот"),
        ("rejoin", "🔁 Rejoin", "🔁 Перезаход"),
        ("stats", "📊 Stats", "📊 Статистика"),
        ("settings", "⚙️ Settings", "⚙️ Настройки"),
    ]
    rows=[]
    for key,en,ru in features:
        enabled = bool(self.telegram_features.get(key, True))
        label = ru if lang=="ru" else en
        rows.append([{"text": f"{'✅' if enabled else '⬜'} {label}", "callback_data": f"tg_toggle:{key}"}])
    for key,en,ru in [
        ("auto_reconnect","Auto reconnect","Автоперезаход"),
        ("stall_watchdog","Stuck watchdog","Защита от зависания"),
        ("hop_after_portals","Hop after N portals","Хоп после N порталов"),
    ]:
        enabled=bool(self.cfg.get(key,False))
        rows.append([{"text":f"{'✅' if enabled else '⬜'} {(ru if lang=='ru' else en)}","callback_data":f"cfg_toggle:{key}"}])
    rows.append([{"text": "✖️ Close" if lang=="en" else "✖️ Закрыть", "callback_data":"tg_close"}])
    self._tg_api("sendMessage", {"chat_id":chat_id,
        "text":"⚙️ Настройки бота" if lang=="ru" else "⚙️ Bot settings",
        "reply_markup":{"inline_keyboard":rows}})


def _tg_send_stats(self, chat_id, lang=None):
    lang = lang or self.lang
    self._tg_send_text(chat_id, self._stats_text(lang))
    png = self._stats_png(lang)
    if png:
        self._tg_send_photo(chat_id, png, "bob_farm_stats.png",
            "График порталов за всё время" if lang=="ru" else "Portal history chart")


def _tg_settings_callback(self, query):
    uid=str((query.get("from") or {}).get("id",""))
    allowed={x.strip() for x in self.telegram_cfg.get("allowed_ids","").split(",") if x.strip()}
    if uid not in allowed: return
    free={x.strip() for x in self.telegram_cfg.get("password_free_ids","").split(",") if x.strip()}
    if uid not in free and uid not in getattr(self,"_tg_authenticated",set()):
        try: self._tg_api("answerCallbackQuery",{"callback_query_id":query.get("id"),"text":"Authenticate first / Сначала авторизуйся"})
        except Exception: pass
        return
    data=str(query.get("data",""))
    sender=query.get("from") or {}
    code=str(sender.get("language_code", "")).lower()
    lang="ru" if code.startswith("ru") else ("en" if code.startswith("en") else self.lang)
    chat_id=(query.get("message") or {}).get("chat",{}).get("id")
    try:
        if data.startswith("tg_toggle:"):
            key=data.split(":",1)[1]
            self.telegram_features[key]=not bool(self.telegram_features.get(key,True))
            _save_json_atomic(TELEGRAM_FEATURES_PATH,self.telegram_features)
            self._tg_api("answerCallbackQuery",{"callback_query_id":query.get("id"),"text":"OK"})
            if chat_id: self._tg_settings_keyboard(chat_id,lang)
        elif data.startswith("cfg_toggle:"):
            key=data.split(":",1)[1]
            if key in self.cfg:
                self.cfg[key]=not bool(self.cfg[key])
                save_config(self.cfg,self.lang)
            self._tg_api("answerCallbackQuery",{"callback_query_id":query.get("id"),"text":"OK"})
            if chat_id: self._tg_settings_keyboard(chat_id,lang)
        elif data=="tg_close":
            self._tg_api("answerCallbackQuery",{"callback_query_id":query.get("id")})
    except Exception:
        pass


def _tg_poll_loop_v15(self):
    try:
        try:
            updates=self._tg_api("getUpdates",{"timeout":0,"offset":-1},timeout=8)
            if updates: self.telegram_offset=updates[-1]["update_id"]+1
        except Exception: pass
        self.root.after(0,lambda:self.tg_status.configure(text=("Bot: online" if self.lang!="ru" else "Бот: в сети"),fg=GREEN))
        while not self.telegram_stop.is_set():
            try:
                updates=self._tg_api("getUpdates",{"timeout":20,"offset":self.telegram_offset},timeout=25)
                for update in updates:
                    self.telegram_offset=update["update_id"]+1
                    if update.get("callback_query"):
                        self._tg_settings_callback(update["callback_query"])
                    msg=update.get("message") or update.get("edited_message")
                    if msg: self._handle_telegram_message(msg)
            except Exception as e:
                if not self.telegram_stop.is_set():
                    err=str(e)
                    self.root.after(0,lambda msg=err:self.tg_status.configure(text=(f"Bot: error - {msg[:100]}" if self.lang!="ru" else f"Ошибка бота: {msg[:100]}"),fg="#ff6969"))
                    time.sleep(3)
    finally:
        self.root.after(0,lambda: (self.tg_status.configure(text=("Bot: offline" if self.lang!="ru" else "Бот: не подключён"),fg=MUTED),
                                   self.tg_start_btn.configure(state="normal"),self.tg_stop_btn.configure(state="disabled")))


def _handle_tg_v15(self, msg):
    text=str(msg.get("text","")).strip()
    command=text.split()[0].split("@")[0] if text else ""
    sender=msg.get("from") or {}
    uid=str(sender.get("id",""))
    allowed={x.strip() for x in self.telegram_cfg.get("allowed_ids","").split(",") if x.strip()}
    free={x.strip() for x in self.telegram_cfg.get("password_free_ids","").split(",") if x.strip()}
    chat_id=(msg.get("chat") or {}).get("id")
    if uid not in allowed: return
    # Telegram language is selected per user; app language is only the fallback.
    code=str(sender.get("language_code", "")).lower()
    lang="ru" if code.startswith("ru") else ("en" if code.startswith("en") else self.lang)
    if command in ("/settings", "/stats") and uid not in free and uid not in getattr(self,"_tg_authenticated",set()):
        self._tg_send_text(chat_id,"Сначала авторизуйся через /password." if lang=="ru" else "Authenticate with /password first.")
        return
    if command=="/settings":
        if self.telegram_features.get("settings",True): self._tg_settings_keyboard(chat_id,lang)
        else: self._tg_send_text(chat_id,"Настройки отключены." if lang=="ru" else "Settings are disabled.")
        return
    if command=="/stats":
        if self.telegram_features.get("stats",True): self._tg_send_stats(chat_id,lang)
        else: self._tg_send_text(chat_id,"Команда /stats отключена." if lang=="ru" else "The /stats command is disabled.")
        return
    if command in ("/status","/stop"):
        if uid not in free and uid not in getattr(self,"_tg_authenticated",set()):
            self._tg_send_text(chat_id,"Сначала авторизуйся через /password." if lang=="ru" else "Authenticate with /password first.")
            return
        if command=="/status":
            self._tg_send_text(chat_id,self._stats_text(lang))
        else:
            self.on_stop()
            self._tg_send_text(chat_id,"Остановка запрошена." if lang=="ru" else "Stop requested.")
        return
    # Preserve the original auth and command implementation, but use this user's locale.
    old_lang=self.lang
    try:
        self.lang=lang
        if command in ("/start","/password","/rejoin","/capture"):
            return _ORIGINAL_TG_HANDLER(self,msg)
    finally:
        self.lang=old_lang



def _plugin_settings_open(self, plugin_path):
    try:
        info=plugin_info(plugin_path)
        with open(plugin_path,"r",encoding="utf-8-sig") as f: source=f.read()
        tree=ast.parse(source)
        settings={}
        for node in tree.body:
            if isinstance(node,(ast.Assign,ast.AnnAssign)):
                targets=node.targets if isinstance(node,ast.Assign) else [node.target]
                if any(isinstance(t,ast.Name) and t.id=="SETTINGS" for t in targets):
                    settings=ast.literal_eval(node.value)
                    break
        if not isinstance(settings,dict) or not settings:
            messagebox.showinfo("Masteries", "This plugin does not declare SETTINGS." if self.lang=="en" else "Этот плагин не объявляет SETTINGS.")
            return
        saved=_safe_json_read(PLUGIN_SETTINGS_PATH,{})
        plugin_key=str(info.get("name") or os.path.basename(plugin_path))
        values=saved.get(plugin_key, saved.get(os.path.basename(plugin_path),{}))
        win=tk.Toplevel(self.root); win.title(info.get("name",os.path.basename(plugin_path)))
        win.configure(bg=BG); win.geometry("440x480")
        tk.Label(win,text=info.get("name","Plugin settings"),bg=BG,fg=TEXT_C,font=("Segoe UI Semibold",14)).pack(pady=12)
        form=tk.Frame(win,bg=BG); form.pack(fill="both",expand=True,padx=16)
        vars={}
        for key,spec in settings.items():
            if isinstance(spec,dict):
                default=spec.get("default",spec.get("value",""))
                label=spec.get("label",key)
                kind=spec.get("type","text")
            else:
                default=spec; label=key; kind="text"
            value=values.get(key,default)
            row=tk.Frame(form,bg=CARD); row.pack(fill="x",pady=4)
            tk.Label(row,text=str(label),bg=CARD,fg=TEXT_C,anchor="w").pack(side="left",padx=8,pady=8)
            if isinstance(default,bool) or kind=="bool":
                var=tk.BooleanVar(value=bool(value))
                ttk.Checkbutton(row,variable=var).pack(side="right",padx=8)
            else:
                var=tk.StringVar(value=str(value))
                tk.Entry(row,textvariable=var,bg=ENTRY_BG,fg=TEXT_C,insertbackground=TEXT_C,relief="flat",width=18).pack(side="right",padx=8,pady=6)
            vars[key]=var
        def save():
            data=_safe_json_read(PLUGIN_SETTINGS_PATH,{})
            typed={}
            for key,var in vars.items():
                raw=var.get()
                spec=settings[key]
                default=spec.get("default",spec.get("value","")) if isinstance(spec,dict) else spec
                kind=spec.get("type", "text") if isinstance(spec,dict) else "text"
                if isinstance(default,bool) or kind=="bool":
                    typed[key]=bool(raw)
                elif isinstance(default,int) and not isinstance(default,bool) or kind=="int":
                    typed[key]=int(str(raw).strip())
                elif isinstance(default,float) or kind=="float":
                    typed[key]=float(str(raw).strip().replace(",", "."))
                else:
                    typed[key]=str(raw)
            data[plugin_key]=typed
            _save_json_atomic(PLUGIN_SETTINGS_PATH,data)
            messagebox.showinfo("Masteries","Saved." if self.lang=="en" else "Сохранено.",parent=win)
        tk.Button(win,text=("SAVE" if self.lang=="en" else "СОХРАНИТЬ"),command=save,bg=ACCENT,fg="#111",relief="flat").pack(pady=12)
    except Exception as exc:
        messagebox.showerror("Masteries",str(exc))



def _open_selected_plugin_settings(self):
    try:
        selected = self.masteries_local_frame.winfo_children()
        candidates = self._plugin_paths()
        if not candidates:
            return
        # Prefer the first checked plugin; its settings are the most likely target.
        chosen = next((p for p in candidates if os.path.basename(p) in self.masteries_enabled), candidates[0])
        self._plugin_settings_open(chosen)
    except Exception as exc:
        messagebox.showerror("Masteries",str(exc))


def _calibrate_portal_color(self):
    if os.name != "nt":
        messagebox.showerror("Calibration", "Windows is required." if self.lang=="en" else "Нужна Windows.")
        return
    if getattr(self, "_calibration_active", False):
        return
    self._calibration_active=True
    lang=self.lang
    messagebox.showinfo("Portal color" if lang=="en" else "Цвет портала",
        "Switch to Roblox and left-click the CENTER of the orange portal once. The bot will sample its color."
        if lang=="en" else "Переключись в Roblox и один раз нажми ЛКМ по ЦЕНТРУ оранжевого портала. Бот определит цвет.")
    def worker():
        try:
            was_down=False
            deadline=time.time()+45
            while time.time()<deadline and not getattr(self,"_v15_stop",threading.Event()).is_set():
                down=bool(user32.GetAsyncKeyState(0x01) & 0x8000)
                if down and not was_down:
                    pt=wintypes.POINT()
                    if not user32.GetCursorPos(ctypes.byref(pt)):
                        raise RuntimeError("Could not read cursor position")
                    with mss.mss() as sct:
                        mon=sct.monitors[0]
                        x,y=pt.x-mon["left"],pt.y-mon["top"]
                        if x<0 or y<0 or x>=mon["width"] or y>=mon["height"]:
                            raise RuntimeError("Cursor is outside the captured screen")
                        frame=np.asarray(sct.grab(mon))[:,:,:3]
                    hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
                    x0,x1=max(0,x-7),min(hsv.shape[1],x+8)
                    y0,y1=max(0,y-7),min(hsv.shape[0],y+8)
                    patch=hsv[y0:y1,x0:x1]
                    pixels=patch.reshape(-1,3)
                    # Ignore nearly gray/dark pixels around the cursor; use the median of saturated pixels.
                    useful=pixels[(pixels[:,1]>=70)&(pixels[:,2]>=70)]
                    if len(useful)<5:
                        raise RuntimeError("The sampled area is too dark or has no clear color. Try clicking the portal center.")
                    h,sat,val=[int(v) for v in np.median(useful,axis=0)]
                    self.cfg["h_min"]=max(0,h-9); self.cfg["h_max"]=min(180,h+9)
                    self.cfg["s_min"]=max(40,sat-75); self.cfg["s_max"]=255
                    self.cfg["v_min"]=max(40,val-75); self.cfg["v_max"]=255
                    def apply():
                        try:
                            self.fill_fields(self.cfg)
                            self.on_save()
                            messagebox.showinfo("Portal color" if self.lang=="en" else "Цвет портала",
                                f"HSV updated: H {self.cfg['h_min']}-{self.cfg['h_max']}, S ≥ {self.cfg['s_min']}, V ≥ {self.cfg['v_min']}"
                                if self.lang=="en" else f"HSV обновлён: H {self.cfg['h_min']}-{self.cfg['h_max']}, S ≥ {self.cfg['s_min']}, V ≥ {self.cfg['v_min']}")
                        finally:
                            self._calibration_active=False
                    self.root.after(0,apply)
                    return
                was_down=down
                time.sleep(0.03)
            self.root.after(0,lambda: (setattr(self,"_calibration_active",False),
                messagebox.showwarning("Calibration" if self.lang=="en" else "Калибровка",
                "No click detected within 45 seconds." if self.lang=="en" else "Клик не обнаружен за 45 секунд.")))
        except Exception as exc:
            self.root.after(0,lambda err=str(exc): (setattr(self,"_calibration_active",False),
                messagebox.showerror("Calibration" if self.lang=="en" else "Калибровка",err)))
    threading.Thread(target=worker,daemon=True).start()


def _apply_v15(self):
    self._v15_stop=threading.Event()
    _app_stats_init(self)
    # New optional features have separate config settings and are persisted by the existing config saver.
    self.recovery_vars = {}
    try:
        btn_parent = self.masteries_local_frame.master.master
        self.button(btn_parent,"btn.plugin_settings",self._open_selected_plugin_settings).pack(fill="x",padx=10,pady=(0,8))
        self.button(btn_parent,"btn.calibrate",self.calibrate_portal_color).pack(fill="x",padx=10,pady=(0,8))
    except Exception:
        pass
    self._watchdog_thread = threading.Thread(target=self._watchdog_loop,daemon=True)
    self._watchdog_thread.start()


def _watchdog_loop(self):
    # Portal-stall watchdog remains lightweight; disconnect detection is deliberately
    # rate-limited to one check every 20 seconds to avoid unnecessary screen captures/OCR.
    last_disconnect_check = 0.0
    while not getattr(self, "_v15_stop", threading.Event()).is_set():
        try:
            if self.running and self.cfg.get("stall_watchdog", False):
                threshold = int(self.cfg.get("stall_minutes", 1)) * 60
                idle = time.time() - getattr(self, "_last_portal_event", time.time())
                if idle >= threshold and time.time() - getattr(self, "_last_watchdog_action", 0) > max(60, threshold * 2):
                    self._last_watchdog_action = time.time()
                    if self.cfg.get("stall_action_hop", True):
                        self.rejoin_random_server()
                        self.emit("evt.error", err="Watchdog: no portal event; server hop requested.")
                    else:
                        self.emit("evt.error", err="Watchdog: no portal event detected.")
            now = time.monotonic()
            if self.running and self.cfg.get("auto_reconnect", True) and now - last_disconnect_check >= 20.0:
                last_disconnect_check = now
                self._check_roblox_process()
                self._check_disconnected_window()
        except Exception as exc:
            try:
                self.emit("evt.error", err=("Recovery monitor: " if self.lang != "ru" else "Монитор переподключения: ") + str(exc)[:180])
            except Exception:
                pass
        time.sleep(1)


def _check_roblox_process(self):
    """Detect RobloxPlayerBeta.exe closing after it was seen at least once."""
    if os.name != "nt" or self._reconnect_busy.is_set():
        return
    try:
        result=subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq RobloxPlayerBeta.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=4,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        present="robloxplayerbeta.exe" in (result.stdout or "").lower()
        now=time.time()
        if present:
            self._roblox_process_seen=True
            self._roblox_missing_since=None
            return
        # Do not launch Roblox if it was never running; this avoids surprise launches.
        if not self._roblox_process_seen:
            return
        if self._roblox_missing_since is None:
            self._roblox_missing_since=now
            return
        if now-self._roblox_missing_since < 8:
            return
        if not self.running or self.stop_event.is_set() or self._reconnect_busy.is_set():
            return
        self._reconnect_busy.set()
        self._tg_notify_localized(
            "Roblox closed. Rejoining a public server..." if self.lang!="ru"
            else "Roblox закрылся. Повторно захожу на публичный сервер..."
        )
        def worker():
            try:
                self.rejoin_random_server()
                deadline=time.time()+60
                while time.time()<deadline and self.running and not self.stop_event.is_set():
                    time.sleep(2)
                    check=subprocess.run(
                        ["tasklist", "/FI", "IMAGENAME eq RobloxPlayerBeta.exe", "/FO", "CSV", "/NH"],
                        capture_output=True, text=True, timeout=4,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    )
                    if "robloxplayerbeta.exe" in (check.stdout or "").lower():
                        self._roblox_process_seen=True
                        self._roblox_missing_since=None
                        try:
                            self.root.after(1200, focus_roblox)
                        except Exception:
                            pass
                        return
                self._tg_notify_localized(
                    "Roblox did not reopen automatically. Check the Roblox app and internet connection."
                    if self.lang!="ru" else
                    "Roblox не запустился автоматически. Проверь приложение Roblox и подключение к интернету."
                )
            except Exception as exc:
                self._tg_notify_localized(
                    ("Reconnect failed: " if self.lang!="ru" else "Ошибка перезахода: ")+str(exc)[:250]
                )
            finally:
                self._reconnect_busy.clear()
        threading.Thread(target=worker,daemon=True).start()
    except Exception:
        # A failed tasklist query must not crash the farm or trigger a false reconnect.
        return


def _check_disconnected_window(self):
    """Detect any Roblox Disconnected dialog, regardless of its error code."""
    if not OCR_AVAILABLE or self._reconnect_busy.is_set() or not self.running:
        return
    try:
        with mss.mss() as sct:
            screen_mon = sct.monitors[0]
            shot = np.asarray(sct.grab(screen_mon))[:, :, :3]
        rgb = cv2.cvtColor(shot, cv2.COLOR_BGR2RGB)
        raw = pytesseract.image_to_string(rgb, config="--psm 11").lower()
        compact = re.sub(r"\s+", " ", raw).strip()
        # Do not whitelist error numbers: Roblox may show 273 or any future code.
        # Requiring both dialog heading and its action avoids matching unrelated text.
        if "disconnected" not in compact or "reconnect" not in compact:
            return
        now = time.time()
        if now - getattr(self, "_disconnect_last_seen", 0.0) < 20:
            return
        self._disconnect_last_seen = now
        self._reconnect_busy.set()
        pause_event = getattr(self, "_disconnect_pause", None)
        if pause_event is not None:
            pause_event.set()
        self._tg_notify_localized(
            "Roblox disconnect dialog detected. Farm paused; clicking Reconnect..." if self.lang == "en"
            else "Обнаружено окно отключения Roblox. Фарм на паузе; нажимаю Reconnect..."
        )

        # Locate the actual Reconnect button on the captured desktop, not fixed coordinates.
        reconnect_xy = None
        try:
            data = pytesseract.image_to_data(rgb, output_type=pytesseract.Output.DICT, config="--psm 11")
            for i, word in enumerate(data.get("text", [])):
                if "reconnect" in str(word).lower():
                    reconnect_xy = (
                        int(screen_mon["left"] + data["left"][i] + data["width"][i] / 2),
                        int(screen_mon["top"] + data["top"][i] + data["height"][i] / 2),
                    )
                    break
        except Exception:
            pass

        def worker():
            recovered = False
            try:
                if reconnect_xy:
                    try:
                        user32.SetCursorPos(int(reconnect_xy[0]), int(reconnect_xy[1]))
                        time.sleep(0.15)
                        pdi.click(int(reconnect_xy[0]), int(reconnect_xy[1]))
                    except Exception as exc:
                        self._tg_notify_localized(("Reconnect click failed: " if self.lang == "en" else "Не удалось нажать Reconnect: ") + str(exc)[:120])
                else:
                    self._tg_notify_localized(
                        "Could not locate the Reconnect button; will try joining a fresh server." if self.lang == "en"
                        else "Не удалось найти кнопку Reconnect; попробую зайти на новый сервер."
                    )

                # Wait up to 60 seconds. Any remaining Disconnected dialog means recovery failed.
                deadline = time.time() + 60
                while time.time() < deadline and self.running and not self.stop_event.is_set():
                    time.sleep(3)
                    try:
                        with mss.mss() as sct2:
                            frame = np.asarray(sct2.grab(sct2.monitors[0]))[:, :, :3]
                        txt = pytesseract.image_to_string(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), config="--psm 11").lower()
                        txt = re.sub(r"\s+", " ", txt)
                        if "disconnected" not in txt or "reconnect" not in txt:
                            time.sleep(1.5)
                            with mss.mss() as sct3:
                                frame2 = np.asarray(sct3.grab(sct3.monitors[0]))[:, :, :3]
                            txt2 = pytesseract.image_to_string(cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB), config="--psm 11").lower()
                            if "disconnected" not in re.sub(r"\s+", " ", txt2):
                                recovered = True
                                break
                    except Exception:
                        continue

                if not recovered and self.running and not self.stop_event.is_set():
                    self._tg_notify_localized(
                        "Reconnect did not clear the dialog. Trying a fresh server..." if self.lang == "en"
                        else "Окно отключения не исчезло. Пробую перейти на новый сервер..."
                    )
                    try:
                        self.rejoin_random_server()
                        deadline = time.time() + 75
                        while time.time() < deadline and self.running and not self.stop_event.is_set():
                            time.sleep(3)
                            with mss.mss() as sct4:
                                frame = np.asarray(sct4.grab(sct4.monitors[0]))[:, :, :3]
                            txt = pytesseract.image_to_string(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), config="--psm 11").lower()
                            if "disconnected" not in re.sub(r"\s+", " ", txt):
                                recovered = True
                                break
                    except Exception as exc:
                        self._tg_notify_localized(("Server rejoin failed: " if self.lang == "en" else "Ошибка перехода на сервер: ") + str(exc)[:180])

                if recovered:
                    self._roblox_process_seen = True
                    self._roblox_missing_since = None
                    self._tg_notify_localized(
                        "Roblox connection restored. Farm resumed." if self.lang == "en"
                        else "Соединение Roblox восстановлено. Фарм продолжен."
                    )
                    if pause_event is not None:
                        pause_event.clear()
                elif self.running and not self.stop_event.is_set():
                    self._tg_notify_localized(
                        "Roblox is still disconnected. Farm remains paused; check Roblox or press Stop." if self.lang == "en"
                        else "Roblox всё ещё отключён. Фарм остаётся на паузе; проверь Roblox или нажми Stop."
                    )
            finally:
                # Never resume blindly: only confirmed recovery clears the pause.
                self._reconnect_busy.clear()

        threading.Thread(target=worker, daemon=True).start()
    except Exception as exc:
        self._reconnect_busy.clear()
        try:
            self.emit("evt.error", err=("Disconnect detection failed: " if self.lang == "en" else "Ошибка обнаружения отключения: ") + str(exc)[:180])
        except Exception:
            pass


def _tg_notify_localized(self, message):
    try:
        for uid in self.telegram_cfg.get("allowed_ids","").split(","):
            uid=uid.strip()
            if uid:
                self._tg_send_text(uid,message)
    except Exception:
        pass


def _write_log_v15(self,key,kw):
    _ORIGINAL_WRITE_LOG(self,key,kw)
    if key in ("evt.entered","evt.noportal","evt.error"):
        self._stats_record(key)
    if key == "evt.entered" and self.cfg.get("hop_after_portals", False):
        count = int(self.cfg.get("hop_portal_count", 10))
        if self.session_portals and self.session_portals % max(1, count) == 0:
            self.rejoin_random_server()


def _on_close_v15(self):
    self._v15_stop.set() if hasattr(self, "_v15_stop") else None
    try:
        _save_json_atomic(STATS_PATH,self.stats_data)
    except Exception: pass
    return _ORIGINAL_ON_CLOSE(self)


_ORIGINAL_TG_HANDLER = App._handle_telegram_message
_ORIGINAL_TG_POLL = App._telegram_poll_loop
_ORIGINAL_WRITE_LOG = App.write_log
_ORIGINAL_ON_CLOSE = App.on_close
App._handle_telegram_message = _handle_tg_v15
App._telegram_poll_loop = _tg_poll_loop_v15
App.write_log = _write_log_v15
App.on_close = _on_close_v15
App.open_profiles_dialog = _profiles_dialog
App._profile_save = _profile_save
App._profile_load = _profile_load
App._plugin_paths = _plugin_paths
App._stats_record = _stats_record
App._stats_snapshot = _stats_snapshot
App._stats_png = _stats_png
App._stats_text = _stats_text
App._tg_settings_keyboard = _tg_settings_keyboard
App._tg_send_stats = _tg_send_stats
App._tg_settings_callback = _tg_settings_callback
App._watchdog_loop = _watchdog_loop
App._check_disconnected_window = _check_disconnected_window
App._tg_notify_localized = _tg_notify_localized
App._apply_v15 = _apply_v15
App.calibrate_portal_color = _calibrate_portal_color
App._plugin_settings_open = _plugin_settings_open
App._open_selected_plugin_settings = _open_selected_plugin_settings

# Wrap App initialization without changing the existing UI construction order.
_ORIGINAL_APP_INIT = App.__init__
def _app_init_v15(self,*args,**kwargs):
    _ORIGINAL_APP_INIT(self,*args,**kwargs)
    self._apply_v15()
App.__init__ = _app_init_v15

def main():
    if os.name != "nt":
        print("BOB Farm works on Windows only.")
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass
    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
    user32.FindWindowW.restype = wintypes.HWND
    user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.GetSystemMenu.restype = wintypes.HMENU
    user32.GetSystemMenu.argtypes = [wintypes.HWND, wintypes.BOOL]
    user32.DeleteMenu.argtypes = [wintypes.HMENU, wintypes.UINT, wintypes.UINT]
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                    ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.GetParent.restype = wintypes.HWND
    user32.GetParent.argtypes = [wintypes.HWND]
    user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
    cfg, lang = load_config()
    root = tk.Tk()
    App(root, cfg, lang)
    root.mainloop()


# ============================== TELEGRAM LANGUAGE + COMPLETE HELP FIX ==============================
TG_LANGUAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bob_farm_telegram_languages.json")

def _tg_load_languages(self):
    try:
        data = _safe_json_read(TG_LANGUAGE_PATH, {})
        return {str(k): ("ru" if str(v).lower().startswith("ru") else "en")
                for k, v in data.items() if str(v).lower() in ("ru", "en")}
    except Exception:
        return {}

def _tg_language_for(self, sender):
    uid = str((sender or {}).get("id", ""))
    saved = getattr(self, "_tg_user_languages", {}).get(uid)
    if saved in ("ru", "en"):
        return saved
    code = str((sender or {}).get("language_code", "")).lower()
    if code.startswith("ru"):
        return "ru"
    if code.startswith("en"):
        return "en"
    return "ru" if getattr(self, "lang", "en") == "ru" else "en"

def _tg_save_user_language(self, uid, lang):
    if lang not in ("ru", "en"):
        return
    if not hasattr(self, "_tg_user_languages"):
        self._tg_user_languages = _tg_load_languages(self)
    self._tg_user_languages[str(uid)] = lang
    _save_json_atomic(TG_LANGUAGE_PATH, self._tg_user_languages)

def _tg_set_chat_commands(self, chat_id, lang):
    if lang == "ru":
        commands = [
            {"command":"start", "description":"Запуск и полный список команд"},
            {"command":"help", "description":"Показать все доступные команды"},
            {"command":"password", "description":"Войти: /password ПАРОЛЬ"},
            {"command":"settings", "description":"Настройки бота"},
            {"command":"stats", "description":"Статистика и график порталов"},
            {"command":"status", "description":"Текущий статус и статистика"},
            {"command":"capture", "description":"Скриншот и отчёт"},
            {"command":"rejoin", "description":"Перейти на сервер по фильтрам"},
            {"command":"restart", "description":"Перезапустить фарм"},
            {"command":"stop", "description":"Остановить фарм"},
        ]
    else:
        commands = [
            {"command":"start", "description":"Start and show all commands"},
            {"command":"help", "description":"Show all available commands"},
            {"command":"password", "description":"Log in: /password PASSWORD"},
            {"command":"settings", "description":"Bot settings"},
            {"command":"stats", "description":"Portal statistics and chart"},
            {"command":"status", "description":"Current status and statistics"},
            {"command":"capture", "description":"Screenshot and report"},
            {"command":"rejoin", "description":"Join a suitable server with 11–13 players"},
            {"command":"stop", "description":"Stop the farm"},
        ]
    try:
        self._tg_api("setMyCommands", {"commands": commands, "scope": {"type":"chat", "chat_id": chat_id}})
    except Exception:
        # The textual /help list remains available if Telegram rejects chat-scoped commands.
        pass

def _tg_help_text(self, lang):
    if lang == "ru":
        return (
            "🤖 BOB Farm — доступные команды\n\n"
            "/start — запуск и краткая инструкция\n"
            "/help — полный список команд\n"
            "Язык Telegram-бота автоматически совпадает с языком интерфейса программы.\n"
            "/password ПАРОЛЬ — авторизация (если требуется)\n"
            "/settings — настройки и переключатели функций\n"
            "/stats — TOTAL, за 10 минут, за час и график порталов\n"
            "/status — текущая статистика\n"
            "/capture — скриншот экрана и отчёт\n"
            "/rejoin — сервер на 11–13 игроков, пинг ниже 70 мс\n"
            "/stop — остановить фарм\n"
            "/restart — перезапустить фарм\n\n"
            "Часть команд может быть отключена владельцем программы. Команды /capture, /rejoin, /settings, /stats, /status и /stop требуют авторизации, если твой ID не добавлен в список без пароля."
        )
    return (
        "🤖 BOB Farm — available commands\n\n"
        "/start — start and quick instructions\n"
        "/help — complete command list\n"
        "The Telegram bot automatically uses the language selected in the app interface.\n"
        "/password PASSWORD — authenticate (if required)\n"
        "/settings — settings and feature toggles\n"
        "/stats — TOTAL, last 10 minutes, last hour and portal chart\n"
        "/status — current statistics\n"
        "/capture — screen capture and report\n"
        "/rejoin — server with 11–13 players, ping below 70 ms\n"
        "/stop — stop the farm\n"
        "/restart — restart the farm\n\n"
        "Some commands may be disabled by the app owner. /capture, /rejoin, /settings, /stats, /status and /stop require authentication unless your ID is password-free."
    )

def _tg_language_keyboard(self, chat_id, lang):
    rows = [[{"text":"🇷🇺 Русский", "callback_data":"tg_lang:ru"}],
            [{"text":"🇬🇧 English", "callback_data":"tg_lang:en"}]]
    self._tg_api("sendMessage", {"chat_id":chat_id,
        "text":"Выбери язык ответов бота:" if lang=="ru" else "Choose the bot reply language:",
        "reply_markup":{"inline_keyboard":rows}})

def _handle_tg_v153(self, msg):
    text = str(msg.get("text", "")).strip()
    command = text.split()[0].split("@")[0].lower() if text else ""
    sender = msg.get("from") or {}
    uid = str(sender.get("id", ""))
    chat_id = (msg.get("chat") or {}).get("id")
    allowed = {x.strip() for x in self.telegram_cfg.get("allowed_ids", "").split(",") if x.strip()}
    free = {x.strip() for x in self.telegram_cfg.get("password_free_ids", "").split(",") if x.strip()}
    if uid not in allowed:
        return
    # One language source of truth: the language selected in the desktop app UI.
    lang = "ru" if getattr(self, "lang", "en") == "ru" else "en"
    if chat_id is not None and command in ("/start", "/help"):
        _tg_set_chat_commands(self, chat_id, lang)
    if command in ("/start", "/help"):
        if command == "/start" and not self.telegram_features.get("start", True):
            self._tg_send_text(chat_id, "Команда /start отключена." if lang=="ru" else "The /start command is disabled.")
            return
        self._tg_send_text(chat_id, _tg_help_text(self, lang))
        return
    if command == "/language":
        self._tg_send_text(chat_id, "Язык бота автоматически берётся из языка интерфейса программы. Измени язык в главном окне BOB Farm." if lang=="ru" else "The bot language follows the app interface language. Change it in the main BOB Farm window.")
        return
    if command == "/restart":
        if uid not in free and uid not in getattr(self, "_tg_authenticated", set()):
            self._tg_send_text(chat_id, "Сначала авторизуйся: /password ТВОЙ_ПАРОЛЬ" if lang=="ru" else "Authenticate first: /password YOUR_PASSWORD")
            return
        self._tg_send_text(chat_id, "Перезапускаю фарм: остановка, затем запуск..." if lang=="ru" else "Restarting farm: stopping, then starting...")
        self._telegram_restart_farm(chat_id)
        return
    if command in ("/settings", "/stats", "/status", "/stop", "/capture", "/rejoin"):
        if uid not in free and uid not in getattr(self, "_tg_authenticated", set()):
            self._tg_send_text(chat_id, "Сначала авторизуйся: /password ТВОЙ_ПАРОЛЬ" if lang=="ru" else "Authenticate first: /password YOUR_PASSWORD")
            return
    if command == "/settings":
        if self.telegram_features.get("settings", True): self._tg_settings_keyboard(chat_id, lang)
        else: self._tg_send_text(chat_id, "Настройки отключены." if lang=="ru" else "Settings are disabled.")
        return
    if command == "/stats":
        if self.telegram_features.get("stats", True): self._tg_send_stats(chat_id, lang)
        else: self._tg_send_text(chat_id, "Команда /stats отключена." if lang=="ru" else "The /stats command is disabled.")
        return
    if command == "/status":
        self._tg_send_text(chat_id, self._stats_text(lang))
        return
    if command == "/stop":
        self.on_stop()
        self._tg_send_text(chat_id, "Остановка фарма запрошена." if lang=="ru" else "Farm stop requested.")
        return
    # Preserve the established implementations of authentication, capture and rejoin.
    old_lang = self.lang
    try:
        self.lang = lang
        return _ORIGINAL_TG_HANDLER(self, msg)
    finally:
        self.lang = old_lang

def _tg_callback_v153(self, query):
    # Inline Telegram settings must use the desktop application's selected language.
    sender = dict((query or {}).get("from") or {})
    sender["language_code"] = "ru" if getattr(self, "lang", "en") == "ru" else "en"
    patched = dict(query or {})
    patched["from"] = sender
    # Old per-user language records are intentionally ignored: GUI language is authoritative.
    return _ORIGINAL_TG_SETTINGS_CALLBACK(self, patched)

def _tg_poll_v153(self):
    try:
        # Do not discard pending messages: users may send /start just before the bot connects.
        while not self.telegram_stop.is_set():
            try:
                updates = self._tg_api("getUpdates", {"timeout":20, "offset":self.telegram_offset}, timeout=25)
                for update in updates:
                    self.telegram_offset = update["update_id"] + 1
                    if update.get("callback_query"):
                        self._tg_settings_callback(update["callback_query"])
                    msg = update.get("message") or update.get("edited_message")
                    if msg:
                        self._handle_telegram_message(msg)
            except Exception as exc:
                if not self.telegram_stop.is_set():
                    err = str(exc)
                    try:
                        self.root.after(0, lambda e=err: self.tg_status.configure(
                            text=(f"Ошибка Telegram: {e[:120]}" if self.lang=="ru" else f"Telegram error: {e[:120]}"), fg="#ff6969"))
                    except Exception: pass
                    time.sleep(3)
    finally:
        try:
            self.root.after(0, lambda: (self.tg_status.configure(
                text=("Бот: не подключён" if self.lang=="ru" else "Bot: offline"), fg=MUTED),
                self.tg_start_btn.configure(state="normal"), self.tg_stop_btn.configure(state="disabled")))
        except Exception: pass

_ORIGINAL_TG_SETTINGS_CALLBACK = App._tg_settings_callback
App._handle_telegram_message = _handle_tg_v153
App._tg_settings_callback = _tg_callback_v153
App._telegram_poll_loop = _tg_poll_v153


# ============================== PERSISTENT ANALYTICS ==============================
# Analytics-only patch: preserve counters and durations across application restarts.
_ORIG_STATS_INIT_ANALYTICS = App._stats_record.__self__ if False else None
_ORIG_STATS_RECORD_ANALYTICS = App._stats_record if hasattr(App, "_stats_record") else None
_ORIG_REFRESH_REPORT_ANALYTICS = App.refresh_report
_ORIG_STATS_TEXT_ANALYTICS = App._stats_text
_ORIG_START_ANALYTICS = App.on_start
_ORIG_STOP_ANALYTICS = App.on_stop
_ORIG_CLOSE_ANALYTICS = App.on_close


def _analytics_read_data(self):
    data = getattr(self, "stats_data", {})
    events = list(data.get("events", []))
    now = time.time()
    day_start = time.localtime(now)
    day_key = time.strftime("%Y-%m-%d", day_start)
    week_start = now - 7 * 86400
    day_count = sum(1 for e in events if e.get("k") == "evt.entered" and time.strftime("%Y-%m-%d", time.localtime(float(e.get("t", 0)))) == day_key)
    week_count = sum(1 for e in events if e.get("k") == "evt.entered" and float(e.get("t", 0)) >= week_start)
    active_run_start = float(getattr(self, "_analytics_run_started", 0) or 0)
    last_run_start = float(getattr(self, "_analytics_last_run_started", 0) or 0)
    run_start = active_run_start or last_run_start
    run_count = sum(1 for e in events if e.get("k") == "evt.entered" and run_start and float(e.get("t", 0)) >= run_start)
    app_started = float(data.get("app_started_at", now) or now)
    app_seconds = float(data.get("app_seconds", 0)) + max(0, now - app_started)
    farm_total_seconds = float(data.get("run_seconds", 0))
    current_run_seconds = float(getattr(self, "_analytics_last_run_duration", 0) or 0)
    if active_run_start and getattr(self, "running", False):
        elapsed = max(0, now - active_run_start)
        farm_total_seconds += elapsed
        current_run_seconds = elapsed
    current_app_seconds = max(0, now - app_started)
    return day_count, week_count, run_count, int(current_run_seconds), int(current_app_seconds), int(app_seconds), int(farm_total_seconds)


def _analytics_format_duration(seconds):
    seconds = max(0, int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return (f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}" if days else f"{hours:02d}:{minutes:02d}:{seconds:02d}")


def _analytics_update_summary(self):
    try:
        day, week, run, run_seconds, current_app_seconds, app_seconds, farm_total_seconds = _analytics_read_data(self)
        lang = self.lang
        if lang == "ru":
            extra = (f"\nСегодня: {day}    За 7 дней: {week}    Текущий запуск фарма: {run}"
                     f"\nВремя фарма (текущий запуск): {_analytics_format_duration(run_seconds)}"
                     f"    Текущий запуск программы: {_analytics_format_duration(current_app_seconds)}"
                     f"\nВсего программа работала: {_analytics_format_duration(app_seconds)}"
                     f"\nВсего фарм работал: {_analytics_format_duration(farm_total_seconds)}")
        else:
            extra = (f"\nToday: {day}    Last 7 days: {week}    Current farm run: {run}"
                     f"\nFarm runtime (current run): {_analytics_format_duration(run_seconds)}"
                     f"    Current app launch: {_analytics_format_duration(current_app_seconds)}"
                     f"\nTotal app runtime: {_analytics_format_duration(app_seconds)}"
                     f"\nTotal farm runtime: {_analytics_format_duration(farm_total_seconds)}")
        self.report_summary.configure(text=self.report_summary.cget("text") + extra)
    except Exception:
        pass


def _analytics_refresh_report(self):
    _ORIG_REFRESH_REPORT_ANALYTICS(self)
    _analytics_update_summary(self)



def _analytics_stats_text(self, lang=None):
    lang = lang or self.lang
    base = _ORIG_STATS_TEXT_ANALYTICS(self, lang)
    day, week, run, run_seconds, current_app_seconds, app_seconds, farm_total_seconds = _analytics_read_data(self)
    if lang == "ru":
        extra = (f"\n\n📅 Сегодня: {day}\n📆 За последние 7 дней: {week}"
                 f"\n▶️ Текущий запуск фарма: {run}\n⏱ Время фарма этого запуска: {_analytics_format_duration(run_seconds)}"
                 f"\n🖥 Время с момента запуска программы: {_analytics_format_duration(current_app_seconds)}"
                 f"\nВсего времени работы программы: {_analytics_format_duration(app_seconds)}"
                 f"\nОбщее время фарма: {_analytics_format_duration(farm_total_seconds)}")
    else:
        extra = (f"\n\n📅 Today: {day}\n📆 Last 7 days: {week}"
                 f"\n▶️ Current farm run: {run}\n⏱ Farm runtime this run: {_analytics_format_duration(run_seconds)}"
                 f"\n🖥 Current app launch runtime: {_analytics_format_duration(current_app_seconds)}"
                 f"\nTotal app runtime: {_analytics_format_duration(app_seconds)}"
                     f"\nTotal farm runtime: {_analytics_format_duration(farm_total_seconds)}")
    return base + extra


def _analytics_wrap_start(self):
    was_running = bool(getattr(self, "running", False))
    result = _ORIG_START_ANALYTICS(self)
    if not was_running and getattr(self, "running", False):
        now = time.time()
        self._analytics_run_started = now
        self._analytics_last_run_started = now
        self._analytics_last_run_duration = 0.0
        self.stats_data["run_started_at"] = now
        self.stats_data.setdefault("run_seconds", 0)
        try: _save_json_atomic(STATS_PATH, self.stats_data)
        except Exception: pass
    return result



def _analytics_wrap_stop(self):
    was_running = bool(getattr(self, "running", False))
    now = time.time()
    if was_running and getattr(self, "_analytics_run_started", None):
        start = float(self._analytics_run_started)
        elapsed = max(0, now - start)
        self.stats_data["run_seconds"] = float(self.stats_data.get("run_seconds", 0)) + elapsed
        self.stats_data["last_run_started_at"] = start
        self.stats_data["last_run_duration"] = elapsed
        self.stats_data["run_started_at"] = None
        self._analytics_last_run_started = start
        self._analytics_last_run_duration = elapsed
        self._analytics_run_started = None
        try: _save_json_atomic(STATS_PATH, self.stats_data)
        except Exception: pass
    return _ORIG_STOP_ANALYTICS(self)



def _analytics_wrap_close(self):
    now = time.time()
    app_start = float(self.stats_data.get("app_started_at", now))
    self.stats_data["app_seconds"] = float(self.stats_data.get("app_seconds", 0)) + max(0, now - app_start)
    self.stats_data["app_started_at"] = None
    # If app is closed while farming, finalize that run's elapsed time too.
    if getattr(self, "running", False) and getattr(self, "_analytics_run_started", None):
        self.stats_data["run_seconds"] = float(self.stats_data.get("run_seconds", 0)) + max(0, now - float(self._analytics_run_started))
        self.stats_data["run_started_at"] = None
        self._analytics_run_started = None
    try: _save_json_atomic(STATS_PATH, self.stats_data)
    except Exception: pass
    result = _ORIG_CLOSE_ANALYTICS(self)
    return result



# Initialize persistent runtime clock when the stats structure is initialized.
_ORIG_APP_STATS_INIT_ANALYTICS = _app_stats_init

def _analytics_stats_init(self):
    _ORIG_APP_STATS_INIT_ANALYTICS(self)
    data = self.stats_data
    now = time.time()
    data.setdefault("app_seconds", 0.0)
    old_app_start = data.get("app_started_at")
    if old_app_start:
        try:
            data["app_seconds"] = float(data.get("app_seconds", 0)) + max(0, now - float(old_app_start))
        except Exception:
            pass
    # Resume a farm-run duration left active when the app was closed unexpectedly.
    previous_run_start = data.get("run_started_at")
    if previous_run_start:
        try:
            data["run_seconds"] = float(data.get("run_seconds", 0)) + max(0, now - float(previous_run_start))
        except Exception:
            pass
    data.setdefault("run_seconds", 0.0)
    data["run_started_at"] = None
    data["app_started_at"] = now
    self._analytics_run_started = None
    self._analytics_last_run_started = float(data.get("last_run_started_at", 0) or 0)
    self._analytics_last_run_duration = float(data.get("last_run_duration", 0) or 0)
    try: _save_json_atomic(STATS_PATH, data)
    except Exception: pass



App._stats_text = _analytics_stats_text
App.refresh_report = _analytics_refresh_report
App.on_start = _analytics_wrap_start
App.on_stop = _analytics_wrap_stop
App.on_close = _analytics_wrap_close
_app_stats_init = _analytics_stats_init

if __name__ == "__main__":
    main()
