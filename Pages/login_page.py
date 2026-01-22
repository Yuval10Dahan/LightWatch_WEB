'''
Created by: Yuval Dahan
Date: 19/01/2026
'''


from playwright.sync_api import expect, TimeoutError, Page


class LoginPage:
    """
    Login page – Handles navigation to the login page, credential validation, authentication,
    logout, and recovery via the Reload button with clear success/failure outcomes.
    """

    LOGIN_PATH = "/logins"

    # ==========================================================
    # Init
    # ==========================================================
    def __init__(self, page: Page):
        self.page = page

        # ---------- Login Page Anchors ----------
        self.login_root = page.locator("div.login-content")
        self.username = page.locator('app-input[formcontrolname="username"] input')
        self.password = page.locator('app-input[formcontrolname="password"] input')
        self.login_btn = page.locator('footer button.btn-primary', has_text="Login")
        self.error_msg = page.locator('.content-row.error-message span', has_text="Login failed: Invalid credentials")

        # ---------- Post-login Anchor ----------
        # Strongest global indicator that user is logged in
        self.post_login_anchor = page.locator("#g-search")

        # ---------- Logout Button ----------
        self.logout_btn = page.locator('li', has_text="Logout")

        # ---------- Reload Button ----------
        self.reload_button = page.locator('button', has_text="Reload")

    # ==========================================================
    # Navigation
    # ==========================================================
    def goto(self, base_url: str) -> None:
        """
        Navigate to login page.
        - Accepts base root or /login
        - Returns early if already logged in
        """

        base_url = base_url.rstrip("/")

        # ---- Guard: already logged in ----
        if self.post_login_anchor.is_visible():
            return

        # Decide where to go
        target_url = (
            base_url if base_url.endswith(self.LOGIN_PATH)
            else f"{base_url}{self.LOGIN_PATH}"
        )

        self.page.goto(target_url, wait_until="domcontentloaded")
        # self.page.goto(base_url, wait_until="domcontentloaded")

        # Ensure login UI is fully rendered
        expect(self.login_root).to_be_visible(timeout=15_000)
        expect(self.username).to_be_visible(timeout=15_000)
        expect(self.password).to_be_visible(timeout=15_000)
        expect(self.login_btn).to_be_visible(timeout=15_000)

    # ==========================================================
    # Login Action
    # ==========================================================
    def login(self, username: str, password: str) -> bool:
        """
        Attempts login and returns result.

        Returns:
            True  -> login succeeded
            False -> validation or authentication failure
        """

        # ---- Guard: already logged in ----
        if self.post_login_anchor.is_visible():
            return True

        # ---- Username validation ----
        self.username.fill(username)
        if len(username) < 8:
            expect(self.login_btn).to_be_disabled()
            print(f"Login failed: Username length too short ❌")
            return False

        # ---- Password validation ----
        self.password.fill(password)
        if len(password) < 8:
            # Angular marks password invalid (red state)
            print(f"Login failed: Password length too short ❌")
            return False

        expect(self.login_btn).to_be_enabled()
        self.login_btn.click()

        try:
            self.post_login_anchor.wait_for(state="visible", timeout=15_000)
            return True

        except TimeoutError:
            if self.error_msg.is_visible():
                print(f"Login failed: Invalid credentials ❌")
                return False

            return False
        
    # ==========================================================
    # Logout Action
    # ==========================================================
    def logout(self) -> bool:
        """
        Attempts to log out the user by clicking the logout button and ensuring login page appears.
        
        Returns:
            True  -> logout succeeded (login screen visible)
            False -> any failure (still on the dashboard)
        """

        # Ensure the logout button is visible and click it
        if self.logout_btn.is_visible():
            self.logout_btn.click()
            self.click_reload_button()

            # Wait for the login screen to appear (post-logout)
            try:
                self.login_root.wait_for(state="visible", timeout=10_000)
                return True
            except TimeoutError as e:
                print(f"Logout failed ❌")
                return False

        return False
    
    # ==========================================================
    # Reload Action
    # ==========================================================
    def click_reload_button(self) -> bool:
        """
        Attempts to click the Reload button on the error page and waits for the page to reload successfully.

        Returns:
            True  -> Reload button clicked and page reloaded successfully.
            False -> Reload button not found or reload failed.
        """
        try:
            # Wait for the reload button to be visible and click it
            self.reload_button.wait_for(state="visible", timeout=15_000)
            self.reload_button.click()

            # After clicking, wait for the page to reload and ensure login elements appear again
            expect(self.page.locator('app-input[formcontrolname="username"]')).to_be_visible(timeout=15_000)
            expect(self.page.locator('app-input[formcontrolname="password"]')).to_be_visible(timeout=15_000)

            return True

        except TimeoutError:
            return False
    