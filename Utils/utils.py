'''
Created by: Yuval Dahan
Date: 26/01/2026
'''


from playwright.sync_api import Page, TimeoutError
from time import sleep
import sys
from playwright.sync_api import expect
from typing import Tuple, Optional
from ipaddress import ip_address
from datetime import timedelta
from time import perf_counter
import time, requests
from concurrent.futures import ThreadPoolExecutor, as_completed


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

def click_system_btn(self, retries: int = 5, timeout: int = 10_000) -> bool:
    """
    Playwright version of Click_System_Btn of PacketLight GUI.
    """
    def accept_any_dialog_once() -> None:
        try:
            self.page.once("dialog", lambda d: d.accept())
        except Exception:
            pass

    for attempt in range(retries):
        try:
            accept_any_dialog_once()

            # 1) outer frame: horizontal_menu_frame
            h_fl = self.page.frame_locator("iframe[name='horizontal_menu_frame'], frame[name='horizontal_menu_frame']")
            # 2) inner frame: box_menu
            box_fl = h_fl.frame_locator("iframe[name='box_menu'], frame[name='box_menu']")

            # 3) System button
            # In LW old UI it can be <input name="System"> or <a name="System"> etc.
            sys_btn = box_fl.locator("[name='System']").first

            expect(sys_btn).to_be_visible(timeout=timeout)
            sys_btn.scroll_into_view_if_needed()
            sys_btn.click(force=True, timeout=timeout)

            return True

        except Exception as e:
            print(f"System btn not found at the {attempt + 1} attempt: {e}")
            try:
                self.page.reload(wait_until="domcontentloaded")
            except Exception:
                pass

    return False

def click_maintenance(self, retries: int = 3, timeout: int = 20_000) -> bool:
    """
    Playwright version of Click_Maintenance of PacketLight GUI.

    Returns:
        True on success, False otherwise.
    """

    def accept_any_dialog_once() -> None:
        try:
            self.page.once("dialog", lambda d: d.accept())
        except Exception:
            pass

    for attempt in range(retries):
        try:
            accept_any_dialog_once()

            # Left menu frame
            left_fl = self.page.frame_locator("iframe[name='vertical_menu_frame'], frame[name='vertical_menu_frame']")

            maint_btn = left_fl.locator("#Maintenance").first
            expect(maint_btn).to_be_visible(timeout=timeout)

            # If it's not already active, click it
            cls = (maint_btn.get_attribute("class") or "").strip()
            if cls != "vertical_button vertical_button_active":
                maint_btn.scroll_into_view_if_needed()
                maint_btn.click(force=True, timeout=timeout)

            return True

        except Exception as e:
            print(f"maintenance btn fail (attempt {attempt + 1}): {e}")
            try:
                self.page.wait_for_timeout(3000)  # replace selenium sleep(3)
                self.page.reload(wait_until="domcontentloaded")
            except Exception:
                pass

    return False

def device_restart(self, restart_type: str, action_dismiss: bool = False, retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
    """
    Playwright version of Device_Restart of PacketLight GUI.

    Purpose:
        Activate a restart action (cold / warm / factory / shutdown) from:
            System -> Maintenance -> Restart tab

    Args:
        restart_type: 'cold' | 'warm' | 'factory' | 'shutdown'
        action_dismiss: if True -> dismiss dialog (Cancel). If False -> accept dialog (OK)
        retries: retries for navigation/click stability
        timeout: playwright timeout in ms

    Returns:
        (success, alert_message)
            success=True when dialog was handled (accepted/dismissed) as expected
            alert_message is the dialog text (or '' if none)
    """
    PRIV_WARN = "Not enough privileges"
    SERVICE_LOCK_DETECTED = "System restore to factory default is forbidden."

    rt = (restart_type or "").strip().lower()
    if rt == "cold":
        reset_type_id = "cold_restart"
    elif rt == "warm":
        reset_type_id = "warm_restart"
    elif rt == "factory":
        reset_type_id = "restart_factory"
    elif rt == "shutdown":
        reset_type_id = "shutdown"
    else:
        return False, ""

    def main_page_fl():
        return self.page.frame_locator("iframe[name='main_page'], iframe#main_body")

    def maint_sys_fl():
        # maintenance inner iframe (selenium: name='maint_sys')
        return main_page_fl().frame_locator("iframe[name='maint_sys'], iframe#maint_sys")

    def arm_dialog_capture_once() -> dict:
        """
        Capture a single dialog text and accept/dismiss it once.
        Returns holder {'text': Optional[str]}
        """
        holder = {"text": None}

        def _handler(d):
            holder["text"] = (d.message or "").strip()
            try:
                if holder["text"] == PRIV_WARN:
                    d.accept()
                elif action_dismiss:
                    d.dismiss()
                else:
                    d.accept()
            except Exception:
                # best effort
                try:
                    d.accept()
                except Exception:
                    pass

        try:
            self.page.once("dialog", _handler)
        except Exception:
            pass
        return holder

    def wait_for_dialog_text(holder: dict, ms: int = 4000) -> Optional[str]:
        step = 50
        loops = max(1, ms // step)
        for _ in range(loops):
            if holder.get("text") is not None:
                return holder["text"]
            try:
                self.page.wait_for_timeout(step)
            except Exception:
                break
        return holder.get("text")

    success = False
    actual_alert_message = ""

    for attempt in range(retries):
        try:
            # Navigate: System -> Maintenance
            # Keep your existing helpers (same as selenium code)
            click_system_btn(self)
            click_maintenance(self)

            # Restart tab is in main_page frame
            tab_restart = main_page_fl().locator("#tab_restart").first
            expect(tab_restart).to_be_visible(timeout=timeout)
            tab_restart.click()

            # Verify tab active
            expect(tab_restart).to_have_attribute("class", "tab tabactive", timeout=timeout)

            # Inner maintenance frame
            reset_btn = maint_sys_fl().locator(f"#{reset_type_id}").first
            expect(reset_btn).to_be_visible(timeout=timeout)
            expect(reset_btn).to_be_enabled(timeout=timeout)

            # Arm dialog handler BEFORE clicking
            dlg_holder = arm_dialog_capture_once()

            reset_btn.click(force=True)

            # Wait for dialog text (captured by handler)
            actual_alert_message = wait_for_dialog_text(dlg_holder, ms=5000) or ""

            if actual_alert_message == "":
                # In Selenium this would raise because they expected an alert
                # We'll treat it as failure to keep parity with old behavior
                raise AssertionError("No dialog appeared after clicking restart button")

            # Service lock text may appear in page body (not a dialog)
            try:
                # check in maint frame first
                if maint_sys_fl().locator(f"body:has-text('{SERVICE_LOCK_DETECTED}')").first.is_visible(timeout=1500):
                    try:
                        self.Refresh_Screen()
                    except Exception:
                        pass
                    return False, SERVICE_LOCK_DETECTED
            except Exception:
                pass

            if actual_alert_message == PRIV_WARN:
                return False, actual_alert_message

            # If we reached here, dialog was accepted/dismissed as requested
            success = True
            break

        except Exception:
            try:
                self.Point_General_System_Configuration()
            except Exception:
                pass
            print(f"{attempt + 1} attempt, for Device Restart, failed")
            continue

    return success, actual_alert_message

def normalize_url_for_device(url: str) -> str:
    """
    - Ensures scheme exists (defaults to http://)
    - Wraps IPv6 host in [brackets] if needed
    """
    if "http://" not in url and "https://" not in url:
        url = "http://" + url

    host = url.split("://", 1)[1]

    # If it's already [ipv6], keep it
    try:
        if host and host[0] == "[" and host[-1] == "]":
            return url
    except Exception:
        return url

    # Otherwise, if host is IPv6, wrap it
    try:
        if ip_address(host).version == 6:
            url = url.replace(host, f"[{host}]", 1)
    except Exception:
        pass

    return url

def countdown_timer(
    page: Page,
    *,
    seconds: Optional[float] = None,
    minutes: Optional[float] = None,
    hours: Optional[float] = None,
    new_line: bool = True,
    msg: Optional[str] = None,
    silent: bool = False,
) -> None:
    """
    Playwright-based countdown (uses page.wait_for_timeout).
    """
    if seconds is None and minutes is None and hours is None:
        return

    total_seconds = 0
    if hours:
        total_seconds += int(hours * 60 * 60)
    if minutes:
        total_seconds += int(minutes * 60)
    if seconds:
        total_seconds += int(seconds)

    while total_seconds > 0:
        if not silent:
            if msg:
                print(f"{msg} {timedelta(seconds=total_seconds)} ", end="\r")
            else:
                print(f"{timedelta(seconds=total_seconds)} ", end="\r")

        page.wait_for_timeout(1000)
        total_seconds -= 1

    if not silent:
        if new_line:
            print(" " * 79)
        else:
            print(" " * 79, end="\r")

def http_ping(page: Page, url: str, timeout_ms: int = 2000) -> bool:
    """
    Playwright equivalent of HTTP_Ping:
    Sends an HTTP GET using page.request.

    Returns True if we got a response with any body (or even empty body but OK),
    False on errors/timeouts.
    """
    try:
        # Your old code did URL.replace("s","") (forcing http).
        # We'll mimic that behavior to avoid https-only issues:
        ping_url = url.replace("https://", "http://", 1)

        resp = page.request.get(ping_url, timeout=timeout_ms)
        # Consider "reachable" if we got a response at all (even 401/403 is still "up")
        # If you want strict success only, replace with: if not resp.ok: return False
        _ = resp.body()  # read body to mimic "read() != ''" behavior (and force IO)
        return True
    except Exception:
        return False

def devices_are_up(ips, wait_time):
    def wait_device_http(ip, timeout_s=600, interval_s=2):
            url = f"http://{ip}/"
            start = time.perf_counter()
            while time.perf_counter() - start < timeout_s:
                try:
                    r = requests.get(url, timeout=3)
                    if r.status_code < 600:  # any real response means "up enough"
                        return ip, (time.perf_counter() - start)
                except Exception:
                    pass
                time.sleep(interval_s)
            raise TimeoutError(f"{ip} did not come up within {timeout_s}s")
        
    print(f"Waiting for devices to come back up after reset: {ips}")
    sleep(wait_time)
    with ThreadPoolExecutor(max_workers=len(ips)) as ex:
        futures = [ex.submit(wait_device_http, ip) for ip in ips]
        for f in as_completed(futures):
            ip, restart_time = f.result()
            print(f"{ip}: device is UP after {restart_time:.1f} seconds")

def Device_Is_Up(
    page: Page,
    URL: str,
    waitBefore: int = 0,
    extra_delay: int = 0,
    wait4ever: bool = False,
    silent: bool = False,
):
    """
    Playwright version of Device_Is_Up.

    Behavior:
    - waits waitBefore (countdown)
    - polls with ~2s interval using HTTP ping (Playwright request)
    - if wait4ever=False: fails after RETRY_LIMIT (50) -> raises TimeoutError
    - if wait4ever=True: loops until reachable and returns recovery_time (seconds)
    - then waits extra_delay (countdown)
    """
    URL = normalize_url_for_device(URL)

    RETRY_LIMIT = 50
    if wait4ever:
        RETRY_LIMIT = 10_000_000
        start = perf_counter()

    countdown_timer(page, seconds=waitBefore, new_line=False, silent=silent)

    retry = 0
    while True:
        retry += 1

        if http_ping(page, URL, timeout_ms=2000):
            break

        # wait ~2 seconds between retries (like your code)
        page.wait_for_timeout(2000)

        if retry > RETRY_LIMIT:
            # old code printed and exit(); better for automation is raising:
            raise TimeoutError(f"Device is not reachable: {URL}")

    countdown_timer(page, seconds=extra_delay, new_line=False, silent=silent)

    if wait4ever:
        end = perf_counter()
        return end - start

    return True