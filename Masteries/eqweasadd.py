NAME = "Reset right after E"
DESCRIPTION = "The bot presses E inside the portal and the character is reset immediately after it (Esc, R, Enter)."

RESET_DELAY = 0.0   # seconds between pressing E and the reset (0 = right away)


def setup(ctx):
    eng = ctx.engine
    ctx.set("feat_press_e", True)    # the bot itself presses E (plugins switch it off by default)
    ctx.set("feat_reset", False)     # the reset is done by this plugin, not by the bot

    def press_key(original, key, hold=None):
        original(key, hold)                          # the normal key press
        if key == "e" and not eng.stopping():        # E was just pressed -> reset
            eng.sleep(RESET_DELAY)
            for k in ("esc", "r"):
                original(k)
                eng.sleep(0.15)
            original("enter")
            eng.sleep(eng.c["respawn_wait"])

    ctx.override("press_key", press_key)
