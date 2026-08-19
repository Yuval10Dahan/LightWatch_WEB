'''
Created by: Yuval Dahan
Date: 03/08/2026
'''

from __future__ import annotations
from playwright.sync_api import Page, expect
from time import sleep, monotonic


class PL_LoginPage:
    """Login page for PL-Devices New GUI using Playwright (PacketLight GUI)."""

    LOGIN_PATHS = ("/", "/index.html", "/login.html", "/logins")

    # ==========================================================
    # Init
    # ==========================================================
    def __init__(self, page: Page):
        self.page = page

        # ---------- Login Page Anchors ----------
        self.login_root = page.locator('form[name="login_form"]').first
        self.username = page.locator("#u_name_box, input[name='username']").first
        self.password = page.locator("#u_pass_box, input[name='password']").first
        self.login_btn = page.locator("#login_but, button[type='submit'], input.log_but").first
        self.error_msg = page.locator("p.denied:has-text('Access Denied'), text=Access Denied!").first
        self.device_text = page.get_by_text("Device")
        self.inventory_text = page.get_by_text("Inventory")

        # ---------- Post-login Anchor ----------
        # Strongest global indicator that user is logged in
        self.post_login_anchor = page.locator(
            ",".join([
                "a:has-text('Logout')",
                "a[href*='logout']",
                "#logout",
                "input[value='Logout']",
                "frame[name*='main']",
                "#mainFrame",
                "#menuFrame",
                "#contentFrame"
            ])
        ).first

        # ---------- Logout Button ----------
        self.logout_form = page.locator("form[name='logout_form']").first
        self.logout_btn = page.locator("form[name='logout_form'] input#Logout").first

        # ---------- Reload Button ----------
        self.reload_button = page.locator("button:has-text('Reload'), button:has-text('Retry'), input[value='Reload']").first

    # ==========================================================
    # Navigation
    # ==========================================================
    
    # ✅
    def goto(self, base_url: str) -> None:
        """
        Navigate to login page.
        - Accepts base root or a direct login path
        - Returns early if already logged in
        """

        base_url = (base_url or "").rstrip("/")
        if not base_url:
            raise ValueError("base_url is empty")

        # ---- Guard: already logged in ----
        if self.post_login_anchor.is_visible():
            return

        # If caller already provided a specific path, just go there.
        # Otherwise, try a few common PacketLight login endpoints until the form appears.
        candidates = []
        if any(base_url.endswith(p.rstrip("/")) for p in self.LOGIN_PATHS if p != "/"):
            candidates = [base_url]
        else:
            for p in self.LOGIN_PATHS:
                target = base_url if p == "/" else f"{base_url}{p}"
                candidates.append(target)

        last_err = None
        for url in candidates:
            try:
                self.page.goto(url, wait_until="domcontentloaded")
                # Ensure login UI is fully rendered
                expect(self.login_root).to_be_visible(timeout=8_000)
                expect(self.username).to_be_visible(timeout=8_000)
                expect(self.password).to_be_visible(timeout=8_000)
                expect(self.login_btn).to_be_visible(timeout=8_000)
                return
            except Exception as e:
                last_err = e

        raise AssertionError(f"Could not load PacketLight login form from: {candidates}. Last error: {last_err}")

    # ==========================================================
    # Login Action
    # ==========================================================

    # ✅
    def login(self, username: str, password: str) -> bool:
        """
        Attempts login and returns result.

        Returns:
            True  -> login succeeded
            False -> authentication failure (Access Denied / stays on login)
        """

        def is_logged_in() -> bool:
            try:
                if self.logout_btn.count() > 0 and self.logout_btn.first.is_visible():
                    return True
            except Exception:
                pass

            try:
                for frame_name in ("mainFrame", "menuFrame", "contentFrame"):
                    if self.page.frame(name=frame_name) is not None:
                        return True
            except Exception:
                pass

            try:
                if self.page.get_by_text("Device", exact=False).first.is_visible():
                    return True
            except Exception:
                pass
            try:
                if self.page.get_by_text("Inventory", exact=False).first.is_visible():
                    return True
            except Exception:
                pass

            return False

        # ---- Guard: already logged in ----
        if is_logged_in():
            return True

        # Defensive: make sure we are on the login UI
        try:
            expect(self.login_root).to_be_visible(timeout=8_000)
        except Exception:
            # attempt to recover if a device served an error page
            self.page.wait_for_load_state("domcontentloaded")
            if not self.login_root.is_visible():
                return False

        # Fill credentials
        self.username.fill(username or "")
        self.password.fill(password or "")

        self.login_btn.click()

        # Give the device time to redirect / build frames
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=12_000)
        except Exception:
            pass

        # Explicit failure
        try:
            if self.error_msg.count() > 0 and self.error_msg.is_visible():
                print("Login failed: Access Denied! ❌")
                return False
        except Exception:
            pass

        # Success signals
        if is_logged_in():
            return True

        # If login form is gone, we likely logged in even if our anchors didn't match yet
        try:
            if not self.login_root.is_visible():
                return True
        except Exception:
            pass

        # Otherwise: still on login screen and no success signal
        return False

    # ==========================================================
    # Logout Action
    # ==========================================================

    # ✅
    def logo_frame(self):
        return self.page.frame_locator("iframe[name='logo'], frame[name='logo']")

    # ✅
    def is_logged_out(self) -> bool:
        """True when the browser is on the login screen or on the 'Logged Out.' page."""
        try:
            if self.login_root.count() > 0 and self.login_root.is_visible():
                return True
        except Exception:
            pass
        try:
            if "logout.asp" in (self.page.url or ""):
                return True
        except Exception:
            pass
        return False

    # ✅
    def wait_for_logged_out(self, timeout: int = 10_000) -> bool:
        """
        Wait for the top-level document that replaces the frameset after logout.

        Clicking #Logout runs the GUI's Logout() (Scripts/defs.js), which assigns
        top.location.href — '/login.asp?u=&p=' for direct browser access, or
        '/logout.asp' ("Logged Out. Please close the browser window.") when the GUI
        was launched from LightWatch with a wlUserLabel query param. Either way the
        whole frameset is torn down, so locators must not be probed until the new
        document has loaded.

        Returns False as soon as the frameset is seen to come back, so the caller can
        click again rather than waiting out the whole timeout — see logout().
        """
        deadline = monotonic() + timeout / 1000.0
        bounce_grace = monotonic() + 2.0   # let the top-level navigation commit first

        while monotonic() < deadline:
            url = self.page.url or ""

            # LightWatch-launched flow ends on logout.asp — no login form to wait for.
            if "logout.asp" in url:
                return True

            try:
                if self.login_root.count() > 0 and self.login_root.is_visible():
                    return True
            except Exception:
                pass    # document is being swapped under us — just poll again

            # The GUI races its own formLogout POST (302 -> /login.asp) against
            # Logout()'s top.location assignment; the loser is ERR_ABORTED. When the
            # POST wins, login.asp is aborted and the frameset comes back still
            # logged in. Report failure now so logout() can re-click immediately.
            if "main_frames.asp" in url and monotonic() > bounce_grace:
                return False

            self.page.wait_for_timeout(200)

        return self.is_logged_out()

    # ✅
    def logout(self, retries: int = 3, timeout: int = 10_000) -> bool:
        """
        Logout from PacketLight GUI.

        Returns True only once the logged-out page is actually up — returning
        straight after click() left callers racing the top-level navigation, so an
        immediate `login_root.is_visible()` check would intermittently see the
        outgoing frameset instead of the login form.

        Returns:
            True  -> logout succeeded
            False -> logout failed
        """

        for attempt in range(retries):
            # ---- Guard: already logged out ----
            if self.is_logged_out():
                return True

            try:
                logout_btn = self.logo_frame().locator("#Logout").first
                expect(logout_btn).to_be_visible(timeout=timeout)
                logout_btn.scroll_into_view_if_needed()
                logout_btn.click(force=True, timeout=timeout)

                if self.wait_for_logged_out(timeout=timeout):
                    return True

                # print(f"Logout clicked but logged-out page did not appear at attempt {attempt + 1}")

            except Exception as e:
                print(f"Logout button not found/clickable at attempt {attempt + 1}: {e}")

            # NOTE: deliberately no page.reload() here. main_frames.asp registers a
            # beforeunload handler that, unless Logout() already set refreshPressed,
            # posts formLogout and then stalls with `for(i=0;i<1000000;i++)
            # document.write(i)` — reloading the frameset to "recover" costs minutes.

        return False

    # ==========================================================
    # Reload Action
    # ==========================================================

    # ✅
    def click_reload_button(self) -> bool:
        """
        Click PacketLight Refresh button.

        Returns:
            True  -> refresh triggered
            False -> refresh control not found
        """

        def refresh_locator(frame):
            return frame.locator("img#refresh").first

        # Preferred: logo frame (Refresh moved here in the new GUI)
        try:
            logo_frame = self.page.frame(name="logo")

            if logo_frame is not None:
                refresh = refresh_locator(logo_frame)

                if refresh.count() > 0 and refresh.is_visible():
                    refresh.click(force=True)

                    # wait for main frame reload
                    try:
                        self.page.wait_for_load_state("domcontentloaded", timeout=10_000)
                    except Exception:
                        pass

                    return True
        except Exception:
            return False

    # ✅
    def refresh(self, timeout: int = 30_000) -> bool:
        """
        Reload the current browser page.

        Returns:
            True  -> Page reloaded successfully
            False -> Reload failed
        """
        try:
            self.page.reload(wait_until="domcontentloaded", timeout=timeout)
            sleep(5)
            return True
        except Exception:
            return False
