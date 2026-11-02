import os, time, ctypes
from ctypes import wintypes
import cv2, numpy as np, mss, pydirectinput as pdi

pdi.PAUSE = 0
pdi.FAILSAFE = False

# ================= НАСТРОЙКИ =================
PROC_WIDTH       = 640        # ширина кадра для обработки (цветовой детект быстрый, хватает с запасом)

# --- цвет портала в HSV (OpenCV: H 0..180, S 0..255, V 0..255) ---
# Замерено по твоему скриншоту: портал H=21, S=250, V=253 (ярко-оранжевый).
# Красный пол имеет H~179, так что в диапазон не попадает.
HSV_LOW          = (12, 170, 200)
HSV_HIGH         = (26, 255, 255)   # верхняя граница H=26: жёлто-зелёный портал (H=31+) игнорируется

# --- фильтры формы (отсекают лишнее оранжевое) ---
MIN_AREA_FRAC    = 0.002      # мин. площадь пятна в долях кадра
# Зоны, которые игнорируются (интерфейс игры, иконки): (x0, y0, x1, y1) в долях экрана 0..1
# Сейчас: правый верхний угол (иконка конфеты и т.п.)
IGNORE_ZONES     = [(0.78, 0.00, 1.00, 0.18)]
MAX_AREA_FRAC    = 0.60       # макс. (если оранжевое на пол-экрана, это не портал)
MIN_FILL         = 0.45       # площадь пятна / площадь его рамки
MIN_SOLIDITY     = 0.75       # площадь пятна / площадь выпуклой оболочки
AR_MIN, AR_MAX   = 0.25, 1.40 # ширина/высота рамки (у портала ~0.66)
CONFIRM_FRAMES   = 3          # сколько кадров подряд портал должен быть на месте

# --- камера и движение ---
MOUSE_GAIN       = 500        # сила доворота мышью
MOUSE_MAX_STEP   = 120        # макс. пикселей мыши за кадр
MOUSE_SIGN       = 1          # если крутит в обратную сторону -> -1
DEADZONE         = 0.015      # зона по центру, где поворот не нужен
WALK_ANGLE       = 0.12       # идти на W только если портал ближе к центру, чем 12% ширины
SEARCH_SPEED     = 30         # скорость вращения при поиске (пикселей/кадр)
SEARCH_TIMEOUT   = 8.0        # сек поиска без портала -> E + ресет
SEARCH_FAIL_E    = True

# --- вход в портал / ресет ---
ENTER_MIN_RATIO  = 0.12       # портал был крупнее 12% высоты кадра и пропал -> зашли
LOST_FRAMES      = 6          # кадров без портала, чтобы считать его пропавшим
STUCK_TIME       = 1.5        # не приближается столько сек -> прыжок
E_DELAY          = 0.1        # после входа в портал ждём 0.1 сек и жмём E
RESET_DELAY      = 0.6        # после E ждём 0.6 сек и делаем ресет
KEY_HOLD         = 0.06       # сколько держать клавишу (слишком короткое нажатие игра может не заметить)
# --- определение "зашли в портал": оранжевое заполнило экран и резко исчезло ---
ENTER_ORANGE_FRAC = 0.20      # оранжевого на экране было >= 20% -> игрок вплотную к порталу
ORANGE_GONE_FRAC  = 0.03      # оранжевого стало < 3% -> телепортировало, мы внутри
ENTER_WAIT_MAX    = 2.5       # если оранжевое не пропадает столько сек - всё равно считаем входом
RESPAWN_WAIT     = 4.0
TARGET_FPS       = 30
STOP_KEY_VK      = 0x77       # F8 - остановка скрипта

# --- окно debug ---
DEBUG            = True
DBG_W            = 480        # ширина окна debug
# Окно закреплено поверх всех окон, крестик убран.
# Закрыть можно только клавишей "-" (работает и когда активен Roblox).
# ==============================================

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


def stopped():
    return user32.GetAsyncKeyState(STOP_KEY_VK) & 0x8000


def minus_pressed():
    # 0xBD = "-" на основной клавиатуре, 0x6D = "-" на цифровой
    return (user32.GetAsyncKeyState(0xBD) & 0x8000) or (user32.GetAsyncKeyState(0x6D) & 0x8000)


def mouse_move(dx):
    user32.mouse_event(0x0001, int(dx), 0, 0, 0)


# ---------- детект по цвету ----------
def find_portal(small):
    """Возвращает (det, mask, area, orange_frac). det = (cx, cy, w, h, contour) или None."""
    H, W = small.shape[:2]
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOW, HIGH)
    for (zx0, zy0, zx1, zy1) in IGNORE_ZONES:
        mask[int(zy0 * H):int(zy1 * H), int(zx0 * W):int(zx1 * W)] = 0
    orange_frac = float(np.count_nonzero(mask)) / (W * H)   # доля оранжевого на экране
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, K3)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, K7)

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
        if area > best_area:
            best_area = area
            best = (x + w / 2, y + h / 2, float(w), float(h), c)
    return best, mask, best_area, orange_frac


# ---------- окно debug ----------
def setup_debug_window(first_frame):
    cv2.namedWindow(WIN, cv2.WINDOW_AUTOSIZE)
    cv2.imshow(WIN, first_frame)
    cv2.waitKey(1)
    cv2.moveWindow(WIN, 0, 0)
    hwnd = user32.FindWindowW(None, WIN)
    if hwnd:
        menu = user32.GetSystemMenu(hwnd, False)
        if menu:
            user32.DeleteMenu(menu, 0xF060, 0)   # убрать крестик (SC_CLOSE)
        pin_window(hwnd)
    return hwnd


def pin_window(hwnd):
    # HWND_TOPMOST = -1; SWP_NOSIZE|SWP_NOMOVE|SWP_NOACTIVATE
    user32.SetWindowPos(hwnd, wintypes.HWND(-1), 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)


# ---------- действия ----------
def press_key(k, hold=KEY_HOLD):
    # держим клавишу чуть дольше, иначе Roblox может не заметить нажатие
    pdi.keyDown(k)
    time.sleep(hold)
    pdi.keyUp(k)


def press_e_and_reset(w_down, e_delay=E_DELAY):
    if w_down:
        pdi.keyUp("w")
    time.sleep(e_delay)                 # 0.1 сек после входа в портал
    press_key("e")
    time.sleep(RESET_DELAY)             # 0.6 сек до ресета
    press_key("esc"); time.sleep(0.15)
    press_key("r");   time.sleep(0.15)
    press_key("enter")
    time.sleep(RESPAWN_WAIT)


def main():
    print("Старт через 5 сек, кликни в Roblox (первое лицо!).")
    print("F8 - остановка скрипта | '-' - закрыть окно debug")
    time.sleep(5)
    frame_time = 1 / TARGET_FPS

    walking = False
    seen = False
    max_ratio = 0.0
    peak_orange = 0.0
    lost_t = time.time()
    lost = 0
    hits = 0
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

            # закрасить область окна debug, чтобы скрипт не детектил сам себя
            if debug_on:
                dh = int(DBG_W * img.shape[0] / img.shape[1]) + 60
                img[0:dh, 0:DBG_W + 20] = 0

            small = cv2.resize(img, (PROC_WIDTH, int(img.shape[0] * PROC_WIDTH / img.shape[1])),
                               interpolation=cv2.INTER_AREA)
            H, W = small.shape[:2]

            det, mask, area, orange_frac = find_portal(small)

            # --- подтверждение по нескольким кадрам подряд ---
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

            # --- debug окно ---
            if debug_on:
                dbg = small.copy()
                if det:
                    color = (0, 255, 0) if confirmed else (0, 255, 255)
                    cx, cy, w, h = det[:4]
                    cv2.rectangle(dbg, (int(cx - w / 2), int(cy - h / 2)),
                                  (int(cx + w / 2), int(cy + h / 2)), color, 3)
                    cv2.drawContours(dbg, [det[4]], -1, (255, 0, 255), 1)
                    cv2.circle(dbg, (int(cx), int(cy)), 6, color, -1)
                cv2.line(dbg, (W // 2, 0), (W // 2, H), (0, 0, 255), 1)
                for (zx0, zy0, zx1, zy1) in IGNORE_ZONES:
                    cv2.rectangle(dbg, (int(zx0 * W), int(zy0 * H)), (int(zx1 * W) - 1, int(zy1 * H)),
                                  (128, 128, 128), 1)
                status = "CONFIRMED" if confirmed else ("candidate" if det else "none")
                cv2.putText(dbg, f"{status} hits={hits} or={orange_frac:.2f}", (10, 28),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                # миниатюра маски (что именно считается "оранжевым") в правом нижнем углу
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
                    hwnd = None
                if hwnd and time.time() - last_pin > 2:
                    pin_window(hwnd)
                    last_pin = time.time()

            # --- клавиша "-" закрывает debug ---
            mp = bool(minus_pressed())
            if mp and not minus_prev and debug_on:
                debug_on = False
                cv2.destroyAllWindows()
                print("Окно debug закрыто (клавиша '-')")
            minus_prev = mp

            # =============== ЛОГИКА ===============
            if confirmed:
                cx, cy, w, h = det[:4]
                ratio = h / H
                seen = True
                lost = 0
                max_ratio = max(max_ratio, ratio)
                search_start = time.time()

                offset = (cx - W / 2) / W
                if abs(offset) > DEADZONE:
                    step = max(-MOUSE_MAX_STEP, min(MOUSE_MAX_STEP, offset * MOUSE_GAIN))
                    mouse_move(step * MOUSE_SIGN)

                # идём вперёд только когда портал почти по центру
                if abs(offset) <= WALK_ANGLE:
                    if not walking:
                        pdi.keyDown("w"); walking = True
                elif walking:
                    pdi.keyUp("w"); walking = False

                # застрял -> прыжок
                if h > last_h * 1.03:
                    last_h, last_progress = h, time.time()
                elif time.time() - last_progress > STUCK_TIME:
                    pdi.press("space")
                    last_progress = time.time()

            elif det is not None and not seen:
                # кандидат ещё не подтверждён: стоим и ждём пару кадров
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
                        # потеряли издалека -> просто ищем заново
                        if walking:
                            pdi.keyUp("w"); walking = False
                        seen, max_ratio, peak_orange, lost = False, 0.0, 0.0, 0
                        hits, prev_c = 0, None
                        last_h, last_progress = 0, time.time()
                        search_start = time.time()
                    else:
                        # портал был вплотную. Заходим ТОЛЬКО когда оранжевое реально пропало
                        # (телепорт). Пока оранжевое ещё на экране, продолжаем держать W.
                        gone = orange_frac < ORANGE_GONE_FRAC
                        waited = time.time() - lost_t > ENTER_WAIT_MAX
                        if gone or waited:
                            print("Зашли в портал -> E (через %.1f сек) -> ресет (через %.1f сек)"
                                  % (E_DELAY, RESET_DELAY))
                            press_e_and_reset(walking)
                            walking = False
                            seen, max_ratio, peak_orange, lost = False, 0.0, 0.0, 0
                            hits, prev_c = 0, None
                            last_h, last_progress = 0, time.time()
                            search_start = time.time()
                elif not seen:
                    # портала нет -> крутимся и ищем
                    if walking:
                        pdi.keyUp("w"); walking = False
                    mouse_move(SEARCH_SPEED * MOUSE_SIGN)
                    if SEARCH_FAIL_E and time.time() - search_start > SEARCH_TIMEOUT:
                        print("Портала нет на экране -> E + ресет")
                        press_e_and_reset(False)
                        search_start = time.time()

            fps_n += 1
            if time.time() - fps_t >= 2:
                print(f"FPS: {fps_n / (time.time() - fps_t):.1f} | area={area:.0f} | seen={seen}")
                fps_t, fps_n = time.time(), 0

            time.sleep(max(0, frame_time - (time.time() - t0)))

    pdi.keyUp("w")
    cv2.destroyAllWindows()
    print("Остановлено.")


if __name__ == "__main__":
    main()
