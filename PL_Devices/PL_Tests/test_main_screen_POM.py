"""
Created by: Yuval Dahan
Date: 01/03/2026
"""

from playwright.sync_api import sync_playwright

from PL_Devices.PL_Pages.PL_login_page import PL_LoginPage
from PL_Devices.PL_Pages.PL_main_screen_POM import PL_Main_Screen_POM

# NOTE: adjust to your device / environment
SERVER_HOST_IP = "172.16.20.113"
BASE_URL = f"http://{SERVER_HOST_IP}/"
USERNAME = "tech"
PASSWORD = "packetlight"


def run_step(step_num: float, title: str, fn):
    """Runs a step and prints consistent success/fail indication."""
    try:
        print(f"\n--- Step {step_num}: {title} ---")
        fn()
        print(f"Step {step_num} Success ✅")
        return True
    except Exception as e:
        print(f"Step {step_num} Failed ❌  Error: {e}")
        return False


def test_main_screen_POM(page):
    pl = PL_LoginPage(page)
    main = PL_Main_Screen_POM(page)

    # ----------------------------
    # Step 1: goto login page
    # ----------------------------
    def step_1():
        pl.goto(BASE_URL)
        assert pl.login_root.is_visible(), "Login form is not visible after goto()"

    run_step(1, "Main Screen: goto login page", step_1)

    # ----------------------------
    # Step 2: positive login
    # ----------------------------
    def step_2():
        ok = pl.login(USERNAME, PASSWORD)
        print(f"Login returned: {ok}")
        if ok is not True:
            raise AssertionError("Login failed with valid credentials")

    run_step(2, "Main Screen: login with valid credentials", step_2)

    # ----------------------------
    # Step 3: (optional) print frames debug
    # ----------------------------
    def step_3():
        # Useful when locators fail due to frame changes
        main.print_frames_debug()

    run_step(3, "Main Screen: print frames debug", step_3)

    # ----------------------------
    # Step 4: Click System button (top menu)
    # ----------------------------
    def step_4():
        ok = main.click_system_btn(timeout=12_000)
        print(f"click_system_btn returned: {ok}")
        if ok is not True:
            raise AssertionError("click_system_btn() returned False")

    run_step(4, "Main Screen: click System button", step_4)

    # ----------------------------
    # Step 5: Click Maintenance (left menu)
    # ----------------------------
    def step_5():
        ok = main.click_maintenance(timeout=20_000)
        print(f"click_maintenance returned: {ok}")
        if ok is not True:
            raise AssertionError("click_maintenance() returned False")

    run_step(5, "Main Screen: click Maintenance", step_5)

    # ----------------------------
    # Step 6: Restart dialog smoke (DISMISS so we don't actually reboot)
    # ----------------------------
    def step_6():
        ok, alert_msg = main.device_restart("factory", action_dismiss=True, timeout=12_000)
        print(f"device_restart returned: ok={ok}, alert='{alert_msg}'")
        if ok is not True:
            raise AssertionError(f"device_restart() returned False. Alert='{alert_msg}'")
        if not alert_msg:
            raise AssertionError("Expected a confirmation dialog message but got empty text")

    run_step(6, "Main Screen: warm restart dialog (dismiss)", step_6)

    # Cleanup: logout (best-effort)
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

        test_main_screen_POM(page)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")
