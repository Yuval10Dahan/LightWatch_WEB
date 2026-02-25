"""
Created by: Yuval Dahan
Date: 22/02/2026
"""

from playwright.sync_api import sync_playwright
from PL_Devices.PL_Pages.PL_login_page import PL_LoginPage
from PL_Devices.PL_Pages.PL_SNMP_page import click_on_SNMP_tab

# NOTE: adjust to your device / environment
SERVER_HOST_IP = "172.16.30.15"
BASE_URL = f"http://{SERVER_HOST_IP}/"
USERNAME = "tech"
PASSWORD = "packetlight"


def run_step(step_num: float, title: str, fn):
    """Runs a step and prints consistent success/fail indication."""
    try:
        fn()
        print(f"Step {step_num} Success ✅")
        return True
    except Exception as e:
        print(f"Step {step_num} Failed ❌  Error: {e}")
        return False


def test_PL_functions(page):
    pl = PL_LoginPage(page)

    # ----------------------------
    # Step 1: goto login page
    # ----------------------------
    def step_1():
        pl.goto(BASE_URL)
        # Strong signal: login form must be visible
        assert pl.login_root.is_visible(), "Login form is not visible after goto()"

    run_step(1, "PL Login: goto login page", step_1)

    # ----------------------------
    # Step 2: positive login
    # ----------------------------
    def step_2():
        ok = pl.login(USERNAME, PASSWORD)
        print(f"Login returned: {ok}")
        if ok is not True:
            raise AssertionError("Login failed with valid credentials")

    run_step(2, "PL Login: login with valid credentials", step_2)

    # ----------------------------
    # Step 3: logout
    # ----------------------------
    def step_3():
        ok = pl.logout()
        print(f"Logout returned: {ok}")
        if ok is not True:
            raise AssertionError("Logout failed")
        assert pl.login_root.is_visible(), "Expected login form after logout()"

    run_step(3, "PL Login: logout returns to login screen", step_3)

    # ----------------------------
    # Step 4: Reload/Retry button (best-effort)
    # ----------------------------
    def step_4():
        # This button typically appears only on some error pages.
        # We just exercise the method and do not hard-fail if it's not present.
        pl.login(USERNAME, PASSWORD)
        clicked = pl.click_reload_button()
        print(f"click_reload_button -> {clicked}")

    run_step(4, "PL Login: reload button (best-effort)", step_4)

    # Cleanup: log out (best-effort)
    try:
        pl.logout()
    except Exception:
        pass

    print("Test Finished ✅")


if __name__ == "__main__":
    import time

    start_time = time.perf_counter()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Run the test
        test_PL_functions(page)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")