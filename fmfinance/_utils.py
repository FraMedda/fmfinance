import time

DEFAULT_COOLDOWN = 1.2

def apply_cooldown(seconds=DEFAULT_COOLDOWN):
    time.sleep(seconds)