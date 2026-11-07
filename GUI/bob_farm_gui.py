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

Install:  pip install mss opencv-python numpy pydirectinput
Run:      python bob_farm_gui.py
"""
import os, sys, json, time, ctypes, threading, base64, queue, platform
from ctypes import wintypes

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except ImportError:
    print("tkinter is missing. Reinstall Python and tick the 'tcl/tk and IDLE' option.")
    raise SystemExit(1)

try:
    import cv2, numpy as np, mss, pydirectinput as pdi
except ImportError as _e:
    _r = tk.Tk(); _r.withdraw()
    messagebox.showerror("Missing packages", f"{_e}\n\nInstall them with:\npip install mss opencv-python numpy pydirectinput")
    raise SystemExit(1)

pdi.PAUSE = 0
pdi.FAILSAFE = False

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bob_farm_config.json")
CONFIG_VERSION = 2
MIGRATE_RESET = ("search_spin", "search_speed", "jump_while_walking")   # reset to the new defaults when an older file is loaded
STOP_KEY_VK = 0x77            # F8
WINDOW_TITLE = "Roblox"
START_DELAY = 5               # seconds between pressing Start and the first action
user32 = ctypes.windll.user32 if os.name == "nt" else None
DBG_W = 480                   # width of the debug window in pixels
DBG_WIN = "debug"             # title of the debug window

# ============================== SETTINGS SCHEMA ==============================
# (group, key, kind, default, min, max)
# kinds: int | float | bool | sign | zones
SCHEMA = [
    ("capture", "target_fps",         "int",   30,    5,      120),
    ("capture", "proc_width",         "int",   640,   320,    1920),
    ("capture", "capture_window",     "bool",  True,  None,   None),
    ("capture", "show_preview",       "bool",  True,  None,   None),
    ("capture", "show_debug_window",  "bool",  True,  None,   None),

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
]
DEFAULTS = {key: default for (_, key, _, default, _, _) in SCHEMA}
GROUPS = ["capture", "detect", "camera", "search", "portal"]


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
                for key in MIGRATE_RESET:         # file from an older version: apply the fixed search/jump defaults
                    cfg[key] = DEFAULTS[key]
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
        "title": "BOB Farm",
        "subtitle": "Slap Battles  ·  automatic BOB glove portal farm",
        "lang": "Language",
        "tab.settings": "Settings", "tab.requirements": "Requirements",
        "btn.start": "Start", "btn.stop": "Stop", "btn.save": "Save settings", "btn.reset": "Reset to defaults",
        "btn.choose_config": "Choose config", "btn.export_config": "Export config",
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
        "group.camera": "Camera & movement", "group.search": "Searching & jumping",
        "group.portal": "Entering the portal & reset",
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
        "evt.stopped": "Stopped.", "evt.error": "Error: {err}", "evt.debug_closed": "Debug window closed ('-' key).",
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
        "title": "BOB Farm",
        "subtitle": "Slap Battles  ·  автофарм портала для перчатки BOB",
        "lang": "Язык",
        "tab.settings": "Настройки", "tab.requirements": "Требования",
        "btn.start": "Старт", "btn.stop": "Стоп", "btn.save": "Сохранить настройки", "btn.reset": "Сбросить по умолчанию",
        "btn.choose_config": "Выбрать конфиг", "btn.export_config": "Экспорт конфига",
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
        "group.camera": "Камера и движение", "group.search": "Поиск и прыжки",
        "group.portal": "Вход в портал и ресет",
        "req.title": "Системные требования", "req.note": "Значения примерные. Сам скрипт лёгкий (только процессор, видеокарта не нужна), основная нагрузка идёт от Roblox.",
        "req.col.component": "Компонент", "req.col.min": "Минимум", "req.col.rec": "Рекомендуется",
        "req.os": "Операционная система", "req.os.min": "Windows 10 (64-бит)", "req.os.rec": "Windows 11 (64-бит)",
        "req.python": "Python", "req.python.min": "3.9", "req.python.rec": "3.10 - 3.12 (с tkinter)",
        "req.cpu": "Процессор", "req.cpu.min": "4 потока, 2.5 ГГц", "req.cpu.rec": "8+ потоков, 3.5+ ГГц",
        "req.ram": "Оперативная память", "req.ram.min": "8 ГБ", "req.ram.rec": "16 ГБ",
        "req.gpu": "Видеокарта", "req.gpu.min": "Любая, на которой идёт Roblox (встроенная подойдёт)", "req.gpu.rec": "GTX 1050 / RX 560 или лучше",
        "req.display": "Экран", "req.display.min": "1280x720, оконный режим или окно без рамки", "req.display.rec": "1920x1080, оконный режим или окно без рамки",
        "req.disk": "Свободное место на диске", "req.disk.min": "300 МБ", "req.disk.rec": "500 МБ",
        "req.deps": "Пакеты Python", "req.deps.min": "mss, opencv-python, numpy, pydirectinput", "req.deps.rec": "так же",
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
        "evt.stopped": "Остановлено.", "evt.error": "Ошибка: {err}", "evt.debug_closed": "Окно debug закрыто (клавиша '-').",
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
    """Brings the Roblox window to the front so key presses and mouse moves go to the game."""
    try:
        hwnd = user32.FindWindowW(None, WINDOW_TITLE)
        if hwnd:
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9)            # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


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


# ============================== THE FARM ENGINE ==============================
class Engine:
    """Runs in a background thread. Talks to the window through emit() (log events)
    and set_preview() (PNG bytes of the debug picture)."""

    def __init__(self, cfg, emit, set_preview, stop_event):
        self.c = cfg
        self.emit = emit
        self.set_preview = set_preview
        self.stop = stop_event
        self.low = np.array((cfg["h_min"], cfg["s_min"], cfg["v_min"]), np.uint8)
        self.high = np.array((cfg["h_max"], cfg["s_max"], cfg["v_max"]), np.uint8)
        self.zones = parse_zones(cfg["ignore_zones"])
        self.k3 = np.ones((3, 3), np.uint8)
        self.k7 = np.ones((7, 7), np.uint8)
        self.jump = {"down": False, "t": 0.0, "last": 0.0}
        self.walking = False

    # ---------- helpers ----------
    def stopping(self):
        if key_down(STOP_KEY_VK):
            self.stop.set()
        return self.stop.is_set()

    def sleep(self, sec):
        """Sleep that wakes up immediately when Stop / F8 is pressed. Returns False if stopped."""
        end = time.time() + sec
        while time.time() < end:
            if self.stopping():
                return False
            time.sleep(min(0.05, max(0.0, end - time.time())))
        return not self.stopping()

    def press_key(self, k):
        pdi.keyDown(k)
        self.sleep(self.c["key_hold"])
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

    def press_e_and_reset(self, w_down):
        c = self.c
        self.release_jump()
        if w_down:
            self.release_walk()
        if not self.sleep(c["e_delay"]):
            return
        self.press_key("e")
        if not self.sleep(c["reset_delay"]):
            return
        for k in ("esc", "r"):
            self.press_key(k)
            if not self.sleep(0.15):
                return
        self.press_key("enter")
        self.sleep(c["respawn_wait"])

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

    # ---------- thread entry ----------
    def run(self):
        try:
            self._run()
        except Exception as e:
            self.emit("evt.error", err=f"{type(e).__name__}: {e}")
        finally:
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
        frame_time = 1.0 / c["target_fps"]

        seen, max_ratio, peak_orange = False, 0.0, 0.0
        lost, lost_t = 0, time.time()
        hits, prev_c, lock_pos = 0, None, None
        search_start = time.time()
        last_preview, frame_i = 0.0, 0
        debug_on = c["show_debug_window"]
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
                want_preview = c["show_preview"] and time.time() - last_preview > 0.15
                if debug_on or want_preview:
                    dbg = self._draw_debug(small, mask, det, confirmed, hits, orange_frac, W, H, state)
                    view = cv2.resize(dbg, (DBG_W, int(DBG_W * H / W)))
                    if debug_on:
                        if dbg_hwnd is None:
                            dbg_hwnd = setup_debug_window(view)
                            focus_roblox()                  # the new window must not take the focus from the game
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
                jump_active = False
                if confirmed:
                    cx, cy, w, h = det[:4]
                    seen, lost, lock_pos = True, 0, (cx, cy)
                    max_ratio = max(max_ratio, h / H)
                    search_start = time.time()
                    state = "WALK"

                    offset = (cx - W / 2) / W
                    if abs(offset) > c["deadzone"]:
                        step = max(-c["mouse_max_step"], min(c["mouse_max_step"], offset * c["mouse_gain"]))
                        mouse_move(step * c["mouse_sign"])
                    if abs(offset) <= c["walk_angle"]:           # walk straight to the portal
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
                time.sleep(max(0.0, frame_time - (time.time() - t0)))

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
FONT, FONT_B, FONT_S = ("Segoe UI", 10), ("Segoe UI Semibold", 10), ("Segoe UI", 9)


class App:
    def __init__(self, root, cfg, lang):
        self.root, self.cfg, self.lang = root, cfg, lang
        self.q = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = None
        self.running = False
        self.pending_png = None
        self.has_preview = False
        self.photo = None
        self.i18n = []              # (widget, key, option, kind)
        self.fields = {}            # key -> dict(kind, get, set, widget)
        self.sysinfo = get_system_info()

        root.title("BOB Farm")
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
        self.nb.add(tab_settings, text="Settings")
        self.nb.add(tab_req, text="Requirements")
        self.tab_widgets = [(tab_settings, "tab.settings"), (tab_req, "tab.requirements")]

        bar = tk.Frame(tab_settings, bg=BG)
        bar.pack(side="bottom", fill="x", pady=(10, 0))
        self.button(bar, "btn.save", self.on_save, accent=True).pack(side="left")
        self.button(bar, "btn.reset", self.on_reset).pack(side="left", padx=(10, 0))
        self.button(bar, "btn.choose_config", self.on_choose_config).pack(side="left", padx=(10, 0))
        self.button(bar, "btn.export_config", self.on_export_config).pack(side="left", padx=(10, 0))
        wrap, inner = self.make_scrollable(tab_settings)
        wrap.pack(fill="both", expand=True, pady=(12, 0))
        self.build_settings(inner)

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

        lg, lg_body = self.card(right, "log.title")
        lg.pack(fill="both", expand=True, pady=(12, 0))
        self.log_text = tk.Text(lg_body, height=10, bg=ENTRY_BG, fg=TEXT_C, insertbackground=TEXT_C, relief="flat",
                                font=("Consolas", 9), wrap="word", highlightthickness=1,
                                highlightbackground=BORDER, state="disabled")
        self.log_text.pack(fill="both", expand=True)
        path = tk.Frame(right, bg=BG)
        path.pack(fill="x", pady=(8, 0))
        self.reg(tk.Label(path, bg=BG, fg=MUTED, font=FONT_S), "cfg.path").pack(side="left")
        tk.Label(path, text=CONFIG_PATH, bg=BG, fg=MUTED, font=FONT_S, wraplength=360, justify="left").pack(side="left", padx=(4, 0))

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

    # ---------- requirements tab ----------
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
    def on_save(self):
        cfg, errors = self.collect()
        if errors:
            self.show_errors(errors)
            return False
        self.cfg = cfg
        try:
            save_config(cfg, self.lang)
            self.log("evt.saved", path=CONFIG_PATH)
        except Exception as e:
            self.log("evt.save_failed", err=str(e))
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
            data = {"config_version": CONFIG_VERSION, "language": self.lang, "settings": cfg}
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
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError("The config file must contain a JSON object.")

            saved = data.get("settings", data)
            if not isinstance(saved, dict):
                raise ValueError("The config settings must be a JSON object.")

            cfg = dict(DEFAULTS)
            for (_, key, kind, default, lo, hi) in SCHEMA:
                if key in saved:
                    cfg[key] = parse_value(kind, saved[key], lo, hi)

            errors = cross_check(cfg)
            if errors:
                names = ", ".join(key for key, _ in errors)
                raise ValueError(f"Invalid settings: {names}")

            # Replace the main config with the selected config automatically.
            save_config(cfg, self.lang)
            self.cfg = cfg
            self.fill_fields(cfg)

            self.log("evt.saved", path=CONFIG_PATH)
            messagebox.showinfo(
                self.t("title"),
                "Configuration loaded and saved as the main config."
                if self.lang == "en"
                else "Конфигурация загружена и сохранена как основной конфиг."
            )
        except Exception as e:
            messagebox.showerror(
                self.t("title"),
                ("Could not load configuration:\\n" if self.lang == "en"
                 else "Не удалось загрузить конфигурацию:\\n") + str(e)
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
        self.stop_event.clear()
        self.pending_png, self.has_preview = None, False
        engine = Engine(dict(self.cfg), self.emit, self.set_preview, self.stop_event)
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
        self.root.after(120, self.poll)

    def write_log(self, key, kw):
        line = time.strftime("%H:%M:%S  ") + self.t(key, **(kw or {}))
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def on_engine_stopped(self):
        self.running = False
        self.pending_png, self.has_preview = None, False
        self.set_status("status.idle", MUTED)
        self.set_enabled(self.start_btn, True)
        self.set_enabled(self.stop_btn, False)
        self.preview_label.configure(image="", text=self.t("preview.off"), height=12)

    # ---------- keep this window out of the screen capture ----------
    def exclude_from_capture(self):
        try:
            self.root.update_idletasks()
            hwnd = user32.GetParent(self.root.winfo_id())
            user32.SetWindowDisplayAffinity(hwnd, 0x11)     # WDA_EXCLUDEFROMCAPTURE
        except Exception:
            pass


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


if __name__ == "__main__":
    main()
