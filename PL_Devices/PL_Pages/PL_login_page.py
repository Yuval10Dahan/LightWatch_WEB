'''
Created by: Yuval Dahan
Date: 22/02/2026
'''

from __future__ import annotations
from playwright.sync_api import Page, expect
from time import sleep


class PL_LoginPage:
    """Login page for PL-Devices using Playwright (PacketLight GUI)."""

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
        self.login_btn = page.locator("#login_but, input[type='submit'][value='Login'], input.log_but").first
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
    def horizontal_menu_frame(self):
        return self.page.frame_locator("iframe[name='horizontal_menu_frame'], frame[name='horizontal_menu_frame']")

    # ✅
    def upper_panel_frame(self):
        return self.horizontal_menu_frame().frame_locator("iframe[name='box_menu'], frame[name='box_menu']")

    # ✅
    def logout(self, retries: int = 5, timeout: int = 10_000) -> bool: 
        """
        Logout from PacketLight GUI.

        Returns:
            True  -> logout succeeded
            False -> logout failed
        """

        for attempt in range(retries):
            try:
                logout_btn = self.upper_panel_frame().locator("#Logout").first
                sleep(3)
                expect(logout_btn).to_be_visible(timeout=timeout)
                logout_btn.scroll_into_view_if_needed()
                self.click_reload_button()  # Ensure we're on the latest page state before clicking logout
                logout_btn.click(force=True, timeout=timeout)
                return True

            except Exception as e:
                print(f"Logout button not found/clickable at attempt {attempt + 1}: {e}")
                try:
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

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

        # Preferred: box_menu frame
        try:
            box_menu = self.page.frame(name="box_menu")

            if box_menu is not None:
                refresh = refresh_locator(box_menu)

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