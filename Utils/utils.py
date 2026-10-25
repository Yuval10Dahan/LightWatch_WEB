'''
Created by: Yuval Dahan
Date: 26/01/2026
'''


from playwright.sync_api import Page, TimeoutError
from time import sleep
import sys
from playwright.sync_api import expect
from typing import Tuple, Optional, Sequence, List
from ipaddress import ip_address
from datetime import timedelta
from time import perf_counter
import time, requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import builtins



_CLI_PRIV_WARNING = "Not enough privileges"
_CLI_LOGIN_DENIED = "Login denied"
_CLI_PASSWORD_EXPIRED = "Password expired. Set new password:"
_CLI_LOGIN_FAILED_MARKERS = ("Failed", "Login denied", "Login incorrect")
# CLI root ">>" and vxWorks shell "-> " prompts for this product line.
_CLI_DEFAULT_PROMPTS = (">>", "-> ")

# ✅
def create_page(playwright_object, max_size=True) -> Page:
    """
    Create a new page with optional maximized window size.
    The best values are: Width: 1920 , Height: 937, Force Scale Factor: 1
    
    Args:
        playwright_object: The playwright object (p)
        max_size (bool): Whether to maximize the window (default: True)
        
    Returns:
        Page: The new page
    """

    if max_size:
        browser = playwright_object.chromium.launch(channel="chrome", headless=False, args=["--window-size=1920,937", "--force-device-scale-factor=1"])
        context = browser.new_context(viewport={"width": 1920, "height": 937}, device_scale_factor=1, ignore_https_errors=True)

    else:
        browser = playwright_object.chromium.launch(channel="chrome", headless=False)
        context = browser.new_context(ignore_https_errors=True)

    page = context.new_page()

    return browser, context, page

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
def create_frame_html(page: Page):
    """
    Create html files for each frame in the page.
    """
    os.makedirs("frames_dump", exist_ok=True)

    for i, fr in enumerate(page.frames):
        try:
            name = fr.name or f"frame_{i}"
            safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
            with open(f"frames_dump/{i}_{safe_name}.html", "w", encoding="utf-8") as f:
                f.write(fr.content())
            print(f"Saved: {i}_{safe_name}.html | url={fr.url}")
        except Exception as e:
            print(f"Failed frame {i}: {e}")

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

# ✅
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

# ✅
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

# ✅
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

# ✅
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

# ✅
def countdown_timer(page: Page, *, seconds: Optional[float] = None, minutes: Optional[float] = None, hours: Optional[float] = None,
    new_line: bool = True, msg: Optional[str] = None, silent: bool = False) -> None:
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

# ✅
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

# ✅
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

# ✅
def Device_Is_Up(page: Page, URL: str, waitBefore: int = 0, extra_delay: int = 0, wait4ever: bool = False, silent: bool = False):
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

# ✅
def _cli_drain(session, idle_timeout: float = 0.4, idle_rounds: int = 2, max_wait: float = 5.0,
               stop_markers: Optional[Sequence[str]] = None) -> str:
    """
    telnetlib3 replacement for the legacy telnetlib `session.read_very_eager()`:
    keeps reading whatever the device has already sent until the session
    has gone quiet for `idle_rounds` consecutive reads (instead of a blind
    sleep(N) followed by a single non-blocking read).

    Args:
        stop_markers: optional strings (e.g. a CLI prompt) that end the
            read as soon as any of them shows up, instead of waiting out
            the full quiet period or `max_wait`.
    """
    chunks = []
    misses = 0
    start = perf_counter()
    while perf_counter() - start < max_wait:
        try:
            chunk = session.read_some(timeout=idle_timeout)
            sleep(1.5)
        except builtins.TimeoutError:
            # NOTE: this module imports `TimeoutError` from playwright.sync_api,
            # which shadows the builtin -- telnetlib3 raises the real builtin
            # one, so it must be caught via `builtins.TimeoutError` here.
            misses += 1
            if misses >= idle_rounds:
                break
            continue
        except EOFError:
            # Peer closed the session -- whatever we already have is final.
            break
        if not chunk:
            break
        chunks.append(chunk)
        misses = 0
        # Check the whole buffer, not just this chunk -- a marker can land
        # split across two reads.
        if stop_markers and any(marker in "".join(chunks) for marker in stop_markers):
            break
    return "".join(chunks)

# ✅
def CLI_Login(session, user: str, password: str, verify: bool = False, new_password: Optional[str] = None,
              retries: int = 3, admin_fallback_password: str = "Admin123!") -> bool:
    """
    Log in to a PL device's CLI over an already-open telnet session.

    Args:
        session: an already-connected telnetlib3 sync telnet session.

        user: CLI username.

        password: CLI password.

        verify: probe-only mode -- checks whether the credentials are
            accepted without performing the "password expired" reset flow.

        new_password: when the device reports "Password expired. Set new
            password:", send this value. Falls back to
            `admin_fallback_password` for the default admin account when
            not given.

        retries: number of times to retry the full login exchange if the
            device rejects it (e.g. a transient "Login incorrect").

        admin_fallback_password: password to retry with when the device
            denies the default admin account's own password (mirrors the
            legacy helper's hardcoded 'Admin123!' recovery path).

    Returns:
        True on a confirmed successful login (or verified-good credentials
        under verify=True), False otherwise.
    """
    is_admin = user.strip().lower() == "admin"

    for attempt in range(1, max(retries, 1) + 1):
        try:
            # Some devices only show the "User:" prompt after a bare "login"
            # (the legacy code looped on this forever -- bounded here instead).
            banner = ""
            for _ in range(6):
                banner += _cli_drain(session, max_wait=5.0)
                if "User:" in banner:
                    break
                session.write("login\n")
                sleep(1)
            else:
                print(f"CLI_Login (attempt {attempt}/{retries}): 'User:' prompt never appeared")
                continue

            session.write(f"{user}\n")
            sleep(1)
            session.write(f"{password}\n")
            sleep(1)
            session.write("\n")
            response = _cli_drain(session, max_wait=5.0)

            if _CLI_PRIV_WARNING in response and is_admin:
                # Device arbitrarily didn't recognize the admin user -- retry once.
                session.write("login\n")
                sleep(1)
                session.write(f"{user}\n")
                sleep(1)
                session.write(f"{password}\n")
                sleep(1)
                session.write("\n")
                response = _cli_drain(session, max_wait=8.0)

            if _CLI_LOGIN_DENIED in response and is_admin:
                session.write(f"{user}\n")
                sleep(1)
                session.write(f"{admin_fallback_password}\n")
                sleep(1)
                session.write("\n")
                response = _cli_drain(session, max_wait=8.0)

            if verify:
                if any(marker in response for marker in _CLI_LOGIN_FAILED_MARKERS):
                    sleep(10)  # let a delayed "Login timed out" message land
                    return False
                return True

            effective_new_password = new_password
            if _CLI_PASSWORD_EXPIRED in response and is_admin and not effective_new_password:
                effective_new_password = admin_fallback_password

            if _CLI_PASSWORD_EXPIRED in response and effective_new_password:
                session.write(f"{effective_new_password}\n")
                sleep(1)
                session.write(f"{effective_new_password}\n")
                sleep(1)
                session.write("Y\n")
                sleep(1)
                session.write("\n")
                _cli_drain(session, max_wait=5.0)
                return True

            if any(marker in response for marker in _CLI_LOGIN_FAILED_MARKERS):
                print(f"CLI_Login (attempt {attempt}/{retries}): login rejected -> {response!r}")
                continue

            return True

        except Exception as e:
            print(f"CLI_Login (attempt {attempt}/{retries}) raised: {e}")

    return False

# ✅
def open_connection(host: str, port: int, timeout: float = 5, retries: int = 5, retry_delay: float = 2.0,
                     drain_banner: bool = True):
    """
    Open a telnet connection to a device's CLI.

    Args:
        host: device IP/hostname.

        port: telnet port (23 for direct telnet).

        timeout: seconds to wait for the TCP connection itself.

        retries: number of connection attempts before giving up.
        
        retry_delay: seconds to wait between failed attempts.

        drain_banner: read and discard whatever banner the device sends
            right after connecting.

    Returns:
        A connected `TelnetConnection`, or None if every attempt failed.
    """
    try:
        from telnetlib3.sync import TelnetConnection
    except ImportError:
        print("open_connection: telnetlib3 is not installed in this environment")
        return None

    for attempt in range(1, max(retries, 1) + 1):
        try:
            conn = TelnetConnection(host, port, timeout=timeout)
            conn.connect()

            if drain_banner:
                _cli_drain(conn, max_wait=3.0)

            return conn

        except Exception as e:
            print(f"open_connection: failed at attempt {attempt}/{retries}: {e}")
            if attempt < retries:
                sleep(retry_delay)

    return None

# ✅
def close_connection(session) -> bool:
    """
    Close a telnet session opened by `open_connection`.

    Args:
        session: the telnetlib3 sync session to close. Safe to call with
            None (e.g. when `open_connection` already returned None) --
            it's a no-op in that case.

    Returns:
        True if the session was already closed or is now closed cleanly,
        False if `close()` itself raised.
    """
    if session is None:
        return True

    try:
        session.close()
        return True
    except Exception as e:
        print(f"close_connection: failed to close cleanly: {e}")
        return False

# ✅
def send_cli_command(session, command: str, timeout: float = 10.0,
                      prompts: Sequence[str] = _CLI_DEFAULT_PROMPTS, strip_echo: bool = True) -> str:
    """
    Send a single CLI command over an already logged-in telnet session
    (see `CLI_Login`) and return the device's response text.

    Args:
        session: an already-connected, already logged-in telnetlib3 sync
            telnet session.

        command: the CLI command to send (no trailing newline needed).

        timeout: max seconds to wait for the response before giving up on
            it (falls back to this if no prompt marker ever shows up).

        prompts: prompt markers that end the read as soon as any of them
            appears, instead of always waiting out the full `timeout` like
            a blind sleep would. Defaults to this product line's CLI root
            (">>") and vxWorks shell ("-> ") prompts.

        strip_echo: most devices echo the command line back before its
            output; when True (default) that leading echoed line, and a
            trailing prompt marker, are removed from the returned text.

    Returns:
        The command's output, with the echoed command line, trailing
        prompt, and surrounding whitespace stripped by default.
    """
    sleep(1)
    session.write(f"{command}\n")
    response = _cli_drain(session, max_wait=timeout, stop_markers=prompts)

    if strip_echo:
        lines = response.splitlines()
        if lines and command.strip() in lines[0]:
            lines = lines[1:]

        # The trailing prompt (e.g. "PL-2000:172.16.20.111>debug>memory>>")
        # is echoed back on its own line -- drop that whole line, not just
        # the marker characters at its end.
        if lines and any(lines[-1].rstrip().endswith(marker) for marker in prompts):
            lines = lines[:-1]

        response = "\n".join(lines)

    return response.strip()

# ✅
def send_cli_commands(session, commands: List[str], timeout: float = 10.0,
                       prompts: Sequence[str] = _CLI_DEFAULT_PROMPTS, strip_echo: bool = True,
                       stop_on_error: bool = False) -> List[str]:
    """
    Send multiple CLI commands in sequence over the same session -- same as
    calling `send_cli_command` once per command, in order.

    Args:
        session, timeout, prompts, strip_echo: see `send_cli_command`.

        stop_on_error: if True, re-raise as soon as one command's send/read
            fails (e.g. the session dropped) instead of continuing
            best-effort through the rest of the list.

    Returns:
        A list of response strings, one per command, in the same order as
        `commands`. When `stop_on_error` is False, a command that raised
        gets an "<error: ...>" placeholder in its slot instead of aborting
        the remaining commands.
    """
    responses = []
    for command in commands:
        try:
            responses.append(
                send_cli_command(session, command, timeout=timeout, prompts=prompts, strip_echo=strip_echo)
            )
        except Exception as e:
            print(f"send_cli_commands: '{command}' failed: {e}")
            if stop_on_error:
                raise
            responses.append(f"<error: {e}>")

    return responses