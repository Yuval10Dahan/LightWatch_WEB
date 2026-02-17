'''
Created by: Yuval Dahan
Date: 26/01/2026
'''


from playwright.sync_api import Page, TimeoutError
from time import sleep
import sys


# ✅
def refresh_page(page: Page, timeout: int = 30_000) -> bool:
    """
    Refresh the current page regardless of UI.
    
    Returns:
        True  -> Page reloaded successfully
        False -> Reload failed or timed out
    """
    try:
        page.reload(wait_until="domcontentloaded", timeout=timeout)
        sleep(5)
        return True
    except TimeoutError:
        return False
    
# ✅
def countdown_sleep(total_seconds: int, message: str = "Waiting", update_every: float = 1.0, end_message=""):
    """
    Sleep with a live countdown printed to the terminal.

    Args:
        total_seconds (int): how long to wait (seconds)
        message (str): text shown before the timer
        update_every (float): refresh interval in seconds (default: 1 sec)
        end_message (str): message printed when finished
    """
    try:
        total_seconds = int(total_seconds)
    except Exception:
        raise ValueError("total_seconds must be an integer number of seconds")

    if total_seconds <= 0:
        print(f"{message}: 00:00")
        return

    # Ensure at least one update per second-ish, but allow bigger intervals
    if update_every <= 0:
        update_every = 1.0

    remaining = total_seconds
    last_shown = None

    while remaining > 0:
        mins, secs = divmod(remaining, 60)
        timer_str = f"{mins:02d}:{secs:02d}"

        if timer_str != last_shown:
            sys.stdout.write(f"\r{message}: {timer_str} ")
            sys.stdout.flush()
            last_shown = timer_str

        sleep(update_every)
        remaining -= update_every

        # keep remaining as int-like for nice formatting
        remaining = int(round(remaining))

    sys.stdout.write(f"\r{message}: 00:00 {end_message}\n")
    sys.stdout.flush()