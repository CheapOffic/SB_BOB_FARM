"""
BOB glove portal farmer (Slap Battles, Halloween event)

How it works:
  1. Captures the screen and finds the bright orange portal by colour.
  2. Turns the camera with the mouse so the portal is centered, then walks to it with W.
  3. Once you are inside (the orange disappears = teleport), waits E_DELAY, presses E,
     waits RESET_DELAY, then resets the character (Esc -> R -> Enter).

Controls:
  F8  - stop the script
  "-" - close the debug window (it is pinned on top and has no close button)

Requirements:
  pip install mss opencv-python numpy pydirectinput
  Roblox in windowed/borderless mode, first-person view (zoom the camera all the way in).
"""
import time, ctypes
from ctypes import wintypes
import cv2, numpy as np, mss, pydirectinput as pdi

pdi.PAUSE = 0
pdi.FAILSAFE = False

# ======================= SETTINGS =======================
PROC_WIDTH        = 640        # frame width used for processing (colour detection is fast)
TARGET_FPS        = 30
STOP_KEY_VK       = 0x77       # F8 stops the script

# --- portal colour in HSV (OpenCV scale: H 0..180, S 0..255, V 0..255) ---
# Measured from screenshots: orange portal H=21, S=250, V=253.
# The red floor has H~179 and the yellow-green portal has H=31+, so both are excluded.
HSV_LOW           = (12, 170, 200)
HSV_HIGH          = (26, 255, 255)

# --- shape filters (reject other orange things) ---
MIN_AREA_FRAC     = 0.002      # min blob area as a fraction of the frame
MAX_AREA_FRAC     = 0.60       # max blob area (orange over half the screen is not "the portal")
MIN_FILL          = 0.45       # blob area / bounding box area
MIN_SOLIDITY      = 0.75       # blob area / convex hull area
AR_MIN, AR_MAX    = 0.25, 1.40 # bounding box width/height (the portal is ~0.66)
CONFIRM_FRAMES    = 3          # frames in a row the portal must stay in place before walking

# Screen zones to ignore (HUD icons etc.): (x0, y0, x1, y1) as fractions of the screen, 0..1
# Currently: top-right corner (candy icon).
IGNORE_ZONES      = [(0.78, 0.00, 1.00, 0.18)]

# --- camera and movement ---
MOUSE_GAIN        = 500        # camera turn strength (higher = faster)
MOUSE_MAX_STEP    = 120        # max mouse pixels per frame
MOUSE_SIGN        = 1          # camera turns the wrong way -> set to -1
DEADZONE          = 0.015      # centre zone (fraction of width) where no turning is needed
WALK_ANGLE        = 0.12       # walk (W) only if the portal is within 12% of width from centre
SEARCH_SPEED      = 30         # spin speed while searching (mouse pixels per frame)
SEARCH_TIMEOUT    = 8.0        # seconds of searching with no portal -> press E + reset
SEARCH_FAIL_E     = True       # enable the rule above
STUCK_TIME        = 1.5        # portal not getting closer for this many seconds -> jump

# --- entering the portal / reset ---
E_DELAY           = 0.1        # after entering the portal wait this long, then press E
RESET_DELAY       = 0.6        # after pressing E wait this long, then reset
RESPAWN_WAIT      = 4.0        # pause after the reset before searching again
KEY_HOLD          = 0.06       # how long each key is held (too-short taps can be missed by the game)
ENTER_MIN_RATIO   = 0.12       # portal was taller than 12% of the frame -> it was close
LOST_FRAMES       = 6          # frames without the portal before it counts as lost

# "Entered the portal" detection: the orange fills the screen, then suddenly disappears.
ENTER_ORANGE_FRAC = 0.20       # orange covered >= 20% of the screen -> player was right at the portal
ORANGE_GONE_FRAC  = 0.03       # orange dropped below 3% -> teleported, we are inside
ENTER_WAIT_MAX    = 2.5        # if the orange never disappears, treat it as entered after this many seconds

# --- debug window ---
DEBUG             = True
DBG_W             = 480        # debug window width in pixels
# The window is pinned on top and has no close button.
# It can only be closed with the "-" key (works even while Roblox is focused).
# ========================================================

user32 = ctypes.windll.user32
user32.FindWindowW.restype = wintypes.HWND
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.GetSystemMenu.restype = wintypes.HMENU
user32.GetSystemMenu.argtypes = [wintypes.HWND, wintypes.BOOL]
user32.DeleteMenu.argtypes = [wintypes.HMENU, wintypes.UINT, wintypes.UINT]
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, wintypes.UINT]

WIN = "debug"
LOW = np.array(HSV_LOW, np.uint8)
HIGH = np.array(HSV_HIGH, np.uint8)
K3 = np.ones((3, 3), np.uint8)
K7 = np.ones((7, 7), np.uint8)


# ---------- input helpers ----------
def stopped():
    return user32.GetAsyncKeyState(STOP_KEY_VK) & 0x8000


def minus_pressed():
    # 0xBD = "-" on the main keyboard, 0x6D = "-" on the numpad
    return (user32.GetAsyncKeyState(0xBD) & 0x8000) or (user32.GetAsyncKeyState(0x6D) & 0x8000)


def mouse_move(dx):
    user32.mouse_event(0x0001, int(dx), 0, 0, 0)   # relative mouse movement


def press_key(k, hold=KEY_HOLD):
    # Hold the key a little longer, otherwise Roblox may miss the press
    pdi.keyDown(k)
    time.sleep(hold)
    pdi.keyUp(k)


def press_e_and_reset(w_down, e_delay=E_DELAY):
    if w_down:
        pdi.keyUp("w")
    time.sleep(e_delay)                 # wait after entering the portal
    press_key("e")
    time.sleep(RESET_DELAY)             # wait before resetting
    press_key("esc"); time.sleep(0.15)
    press_key("r");   time.sleep(0.15)
    press_key("enter")
    time.sleep(RESPAWN_WAIT)


# ---------- colour-based portal detection ----------
def find_portal(small):
    """Returns (det, mask, area, orange_frac).
    det = (cx, cy, w, h, contour) or None; orange_frac = share of the screen that is portal-orange."""
    H, W = small.shape[:2]
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOW, HIGH)
    for (zx0, zy0, zx1, zy1) in IGNORE_ZONES:
        mask[int(zy0 * H):int(zy1 * H), int(zx0 * W):int(zx1 * W)] = 0
    orange_frac = float(np.count_nonzero(mask)) / (W * H)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, K3)     # remove specks
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, K7)    # fill small holes

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best, best_area = None, 0
    for c in cnts:
        area = cv2.contourArea(c)
        if area < MIN_AREA_FRAC * W * H or area > MAX_AREA_FRAC * W * H:
            continue
        x, y, w, h = cv2.boundingRect(c)
        if w < 4 or h < 4:
            continue
        if area / (w * h) < MIN_FILL:
            continue
        hull = cv2.contourArea(cv2.convexHull(c))
        if hull <= 0 or area / hull < MIN_SOLIDITY:
            continue
        if not (AR_MIN <= w / h <= AR_MAX):
            continue
        if area > best_area:                               # keep the largest valid blob
            best_area = area
            best = (x + w / 2, y + h / 2, float(w), float(h), c)
    return best, mask, best_area, orange_frac


# ---------- debug window ----------
def setup_debug_window(first_frame):
    cv2.namedWindow(WIN, cv2.WINDOW_AUTOSIZE)
    cv2.imshow(WIN, first_frame)
    cv2.waitKey(1)
    cv2.moveWindow(WIN, 0, 0)
    hwnd = user32.FindWindowW(None, WIN)
    if hwnd:
        menu = user32.GetSystemMenu(hwnd, False)
        if menu:
            user32.DeleteMenu(menu, 0xF060, 0)   # remove the close button (SC_CLOSE)
        pin_window(hwnd)
    return hwnd


def pin_window(hwnd):
    # HWND_TOPMOST = -1; flags: SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
    user32.SetWindowPos(hwnd, wintypes.HWND(-1), 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)


# ---------- main loop ----------
def main():
    print("Starting in 5 seconds - click into Roblox (first-person view!).")
    print("F8 = stop the script | '-' = close the debug window")
    time.sleep(5)
    frame_time = 1 / TARGET_FPS

    walking = False
    seen = False              # a confirmed portal has been seen during this run-up
    max_ratio = 0.0           # biggest portal height seen (fraction of frame height)
    peak_orange = 0.0         # biggest orange share of the screen seen
    lost_t = time.time()      # when the portal was last lost
    lost = 0                  # consecutive frames without a confirmed portal
    hits = 0                  # consecutive frames the portal was found in the same place
    prev_c = None
    last_h, last_progress = 0, time.time()
    search_start = time.time()
    fps_t, fps_n = time.time(), 0
    debug_on = DEBUG
    hwnd = None
    minus_prev = False
    last_pin = 0

    with mss.mss() as sct:
        mon = sct.monitors[1]
        while not stopped():
            t0 = time.time()
            img = np.ascontiguousarray(np.array(sct.grab(mon))[:, :, :3])

            # Black out the area under the debug window so the script can't detect itself
            if debug_on:
                dh = int(DBG_W * img.shape[0] / img.shape[1]) + 60
                img[0:dh, 0:DBG_W + 20] = 0

            small = cv2.resize(img, (PROC_WIDTH, int(img.shape[0] * PROC_WIDTH / img.shape[1])),
                               interpolation=cv2.INTER_AREA)
            H, W = small.shape[:2]

            det, mask, area, orange_frac = find_portal(small)

            # --- confirm the portal over several consecutive frames ---
            if det:
                if prev_c is not None and abs(det[0] - prev_c[0]) < 0.2 * W and abs(det[1] - prev_c[1]) < 0.25 * H:
                    hits += 1
                else:
                    hits = 1
                prev_c = (det[0], det[1])
            else:
                hits = 0
                prev_c = None
            confirmed = det is not None and hits >= CONFIRM_FRAMES
            if seen:
                peak_orange = max(peak_orange, orange_frac)

            # --- debug window ---
            if debug_on:
                dbg = small.copy()
                if det:
                    color = (0, 255, 0) if confirmed else (0, 255, 255)   # green = confirmed, yellow = candidate
                    cx, cy, w, h = det[:4]
                    cv2.rectangle(dbg, (int(cx - w / 2), int(cy - h / 2)),
                                  (int(cx + w / 2), int(cy + h / 2)), color, 3)
                    cv2.drawContours(dbg, [det[4]], -1, (255, 0, 255), 1)
                    cv2.circle(dbg, (int(cx), int(cy)), 6, color, -1)
                cv2.line(dbg, (W // 2, 0), (W // 2, H), (0, 0, 255), 1)  # screen centre
                for (zx0, zy0, zx1, zy1) in IGNORE_ZONES:                  # ignored zones (grey)
                    cv2.rectangle(dbg, (int(zx0 * W), int(zy0 * H)), (int(zx1 * W) - 1, int(zy1 * H)),
                                  (128, 128, 128), 1)
                status = "CONFIRMED" if confirmed else ("candidate" if det else "none")
                cv2.putText(dbg, f"{status} hits={hits} or={orange_frac:.2f}", (10, 28),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                # mask thumbnail (what counts as "orange") in the bottom-right corner
                tw = W // 3
                th = int(tw * H / W)
                thumb = cv2.cvtColor(cv2.resize(mask, (tw, th)), cv2.COLOR_GRAY2BGR)
                dbg[H - th:H, W - tw:W] = thumb
                cv2.rectangle(dbg, (W - tw, H - th), (W - 1, H - 1), (255, 255, 255), 1)

                view = cv2.resize(dbg, (DBG_W, int(DBG_W * H / W)))
                if hwnd is None:
                    hwnd = setup_debug_window(view)
                cv2.imshow(WIN, view)
                cv2.waitKey(1)
                if cv2.getWindowProperty(WIN, cv2.WND_PROP_VISIBLE) < 1:
                    hwnd = None                    # window was closed some other way -> recreate it
                if hwnd and time.time() - last_pin > 2:
                    pin_window(hwnd)               # keep it on top
                    last_pin = time.time()

            # --- "-" key closes the debug window ---
            mp = bool(minus_pressed())
            if mp and not minus_prev and debug_on:
                debug_on = False
                cv2.destroyAllWindows()
                print("Debug window closed ('-' key)")
            minus_prev = mp

            # =============== LOGIC ===============
            if confirmed:
                cx, cy, w, h = det[:4]
                ratio = h / H
                seen = True
                lost = 0
                max_ratio = max(max_ratio, ratio)
                search_start = time.time()

                # turn the camera so the portal sits in the centre
                offset = (cx - W / 2) / W
                if abs(offset) > DEADZONE:
                    step = max(-MOUSE_MAX_STEP, min(MOUSE_MAX_STEP, offset * MOUSE_GAIN))
                    mouse_move(step * MOUSE_SIGN)

                # walk forward only when the portal is almost centered
                if abs(offset) <= WALK_ANGLE:
                    if not walking:
                        pdi.keyDown("w"); walking = True
                elif walking:
                    pdi.keyUp("w"); walking = False

                # stuck (portal not getting bigger) -> jump
                if h > last_h * 1.03:
                    last_h, last_progress = h, time.time()
                elif time.time() - last_progress > STUCK_TIME:
                    pdi.press("space")
                    last_progress = time.time()

            elif det is not None and not seen:
                # candidate not confirmed yet: stand still and wait a few frames
                if walking:
                    pdi.keyUp("w"); walking = False
                search_start = time.time()

            else:
                lost += 1
                if lost == 1:
                    lost_t = time.time()
                if seen and lost >= LOST_FRAMES:
                    was_close = max_ratio >= ENTER_MIN_RATIO or peak_orange >= ENTER_ORANGE_FRAC
                    if not was_close:
                        # lost it from far away -> just search again
                        if walking:
                            pdi.keyUp("w"); walking = False
                        seen, max_ratio, peak_orange, lost = False, 0.0, 0.0, 0
                        hits, prev_c = 0, None
                        last_h, last_progress = 0, time.time()
                        search_start = time.time()
                    else:
                        # The portal was right in front of us. Count it as entered ONLY when the
                        # orange has really disappeared (teleport). While orange is still on
                        # screen we keep holding W so the player walks all the way in.
                        gone = orange_frac < ORANGE_GONE_FRAC
                        waited = time.time() - lost_t > ENTER_WAIT_MAX
                        if gone or waited:
                            print("Entered the portal -> E (in %.1f s) -> reset (in %.1f s)"
                                  % (E_DELAY, RESET_DELAY))
                            press_e_and_reset(walking)
                            walking = False
                            seen, max_ratio, peak_orange, lost = False, 0.0, 0.0, 0
                            hits, prev_c = 0, None
                            last_h, last_progress = 0, time.time()
                            search_start = time.time()
                elif not seen:
                    # no portal on screen -> spin and search
                    if walking:
                        pdi.keyUp("w"); walking = False
                    mouse_move(SEARCH_SPEED * MOUSE_SIGN)
                    if SEARCH_FAIL_E and time.time() - search_start > SEARCH_TIMEOUT:
                        print("No portal found -> E + reset")
                        press_e_and_reset(False)
                        search_start = time.time()

            fps_n += 1
            if time.time() - fps_t >= 2:
                print(f"FPS: {fps_n / (time.time() - fps_t):.1f} | blob area={area:.0f} | seen={seen}")
                fps_t, fps_n = time.time(), 0

            time.sleep(max(0, frame_time - (time.time() - t0)))   # cap the loop at TARGET_FPS

    pdi.keyUp("w")
    cv2.destroyAllWindows()
    print("Stopped.")


if __name__ == "__main__":
    main()
