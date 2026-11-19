import time

NAME = "Portal: E -> wait 10 s -> reset"
DESCRIPTION = "After the character enters the portal: press E, wait 10 seconds, reset the character (Esc, R, Enter)."

WAIT_AFTER_E = 10.0   # seconds to wait after pressing E
E_DELAY = 0.1         # pause before pressing E


def run(ctx):
    c = ctx.cfg
    low = (c["h_min"], c["s_min"], c["v_min"])
    high = (c["h_max"], c["s_max"], c["v_max"])

    peak_h, peak_orange = 0.0, 0.0   # how close / how orange the portal got
    lost, lost_t = 0, 0.0            # frames without the portal, and when that started

    while True:                      # waits for "entered the portal", then does the macro once
        ctx.sleep(0.03)
        frame = ctx.grab()
        portal = ctx.find_portal(frame)
        orange = ctx.find_color(low, high, min_area=0, frame=frame)
        frac = orange["area"] if orange else 0.0

        if portal:
            peak_h = max(peak_h, portal["h"])
            peak_orange = max(peak_orange, frac)
            lost = 0
            continue

        lost += 1
        if lost == 1:
            lost_t = time.time()
        if lost < c["lost_frames"]:
            continue

        was_close = peak_h >= c["enter_min_ratio"] or peak_orange >= c["enter_orange_frac"]
        if not was_close:            # portal was far away and disappeared: it was not an entry
            peak_h, peak_orange, lost = 0.0, 0.0, 0
            continue

        gone = frac < c["orange_gone_frac"]
        waited = time.time() - lost_t > c["enter_wait_max"]
        if gone or waited:           # portal vanished up close -> we are inside
            break

    ctx.log("Entered the portal")
    ctx.sleep(E_DELAY)
    ctx.press("e")
    ctx.log(f"E pressed, waiting {WAIT_AFTER_E:g} s")
    ctx.sleep(WAIT_AFTER_E)
    ctx.log("Resetting the character")
    ctx.reset_character()
