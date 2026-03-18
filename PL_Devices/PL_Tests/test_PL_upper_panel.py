"""
Created by: Yuval Dahan
Date: 15/03/2026
"""

from playwright.sync_api import sync_playwright

from PL_Devices.PL_Pages.PL_login_page import PL_LoginPage
from PL_Devices.PL_Pages.PL_upper_panel import PL_Upper_Panel

# NOTE: adjust to your device / environment
SERVER_HOST_IP = "172.16.20.113"
BASE_URL = f"http://{SERVER_HOST_IP}/"
USERNAME = "tech"
PASSWORD = "packetlight"


def run_step(step_num: float, title: str, fn):
    """Runs a step and prints consistent success/fail indication."""
    try:
        # print(f"\n--- Step {step_num}: {title} ---")
        fn()
        print(f"Step {step_num} Success ✅")
        return True
    except Exception as e:
        print(f"Step {step_num} Failed ❌  Error: {e}")
        return False


def test_PL_upper_panel(page):
    pl = PL_LoginPage(page)
    upper_panel = PL_Upper_Panel(page)

    # ----------------------------
    # Step 1: goto login page
    # ----------------------------
    def step_1():
        pl.goto(BASE_URL)
        assert pl.login_root.is_visible(), "Login form is not visible after goto()"

    run_step(1, "Upper Panel: goto login page", step_1)

    # ----------------------------
    # Step 2: positive login
    # ----------------------------
    def step_2():
        ok = pl.login(USERNAME, PASSWORD)
        print(f"Login returned: {ok}")
        if ok is not True:
            raise AssertionError("Login failed with valid credentials")

    run_step(2, "Upper Panel: login with valid credentials", step_2)

    # ----------------------------
    # Step 3: click System button
    # ----------------------------
    def step_3():
        ok = upper_panel.click_system(timeout=12_000)
        print(f"click_system returned: {ok}")
        if ok is not True:
            raise AssertionError("click_system() returned False")

    run_step(3, "Upper Panel: click System button", step_3)

    # ----------------------------
    # Step 4: click ALL button
    # ----------------------------
    def step_4():
        ok = upper_panel.click_all(timeout=12_000)
        print(f"click_all returned: {ok}")
        if ok is not True:
            raise AssertionError("click_all() returned False")

    run_step(4, "Upper Panel: click ALL button", step_4)

    # ----------------------------
    # Step 5: click Port-1 button
    # ----------------------------
    def step_5():
        ok = upper_panel.click_port(1, timeout=12_000)
        print(f"click_port(1) returned: {ok}")
        if ok is not True:
            raise AssertionError("click_port(1) returned False")
        
        upper_panel.click_port(19, timeout=12_000)
        upper_panel.click_port("MNG 1", timeout=12_000)
        upper_panel.click_port("ETH 2", timeout=12_000)

    run_step(5, "Upper Panel: click Port-1 button", step_5)

    # Cleanup: logout (best-effort)
    try:
        upper_panel.upper_panel_logout()
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

        test_PL_upper_panel(page)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")