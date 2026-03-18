"""
Created by: Yuval Dahan
Date: 01/03/2026
"""

from playwright.sync_api import sync_playwright

from PL_Devices.PL_Pages.PL_login_page import PL_LoginPage
from PL_Devices.PL_Pages.PL_main_screen_POM import PL_Main_Screen_POM
from PL_Devices.PL_Pages.PL_upper_panel import PL_Upper_Panel

# NOTE: adjust to your device / environment
SERVER_HOST_IP = "172.16.30.17"
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


def test_main_screen_POM(page):
    pl = PL_LoginPage(page)
    main = PL_Main_Screen_POM(page)
    upper_panel = PL_Upper_Panel(page)

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
    # Step 3: Click Fault
    # ----------------------------
    def step_3():
        ok = main.click_Fault(timeout=20_000)
        print(f"click_Fault returned: {ok}")
        if ok is not True:
            raise AssertionError("click_Fault() returned False")

    run_step(3, "Main Screen: click Fault", step_3)

    # ----------------------------
    # Step 4: Click Configuration
    # ----------------------------
    def step_4():
        ok = main.click_Configuration(timeout=20_000)
        print(f"click_Configuration returned: {ok}")
        if ok is not True:
            raise AssertionError("click_Configuration() returned False")

    run_step(4, "Main Screen: click Configuration", step_4)

    # ----------------------------
    # Step 5: Click Performance
    # ----------------------------
    def step_5():
        ok = main.click_Performance(timeout=20_000)
        print(f"click_Performance returned: {ok}")
        if ok is not True:
            raise AssertionError("click_Performance() returned False")

    run_step(5, "Main Screen: click Performance", step_5)

    # ----------------------------
    # Step 6: Click Security
    # ----------------------------
    def step_6():
        ok = main.click_Security(timeout=20_000)
        print(f"click_Security returned: {ok}")
        if ok is not True:
            raise AssertionError("click_Security() returned False")

    run_step(6, "Main Screen: click Security", step_6)

    # ----------------------------
    # Step 7: Click Maintenance
    # ----------------------------
    def step_7():
        ok = main.click_maintenance(timeout=20_000)
        print(f"click_maintenance returned: {ok}")
        if ok is not True:
            raise AssertionError("click_maintenance() returned False")

    run_step(7, "Main Screen: click Maintenance", step_7)

    # ----------------------------
    # Step 8: Click Alarms tab
    # ----------------------------
    def step_8():
        ok = main.click_Alarms(timeout=20_000)
        print(f"click_Alarms returned: {ok}")
        if ok is not True:
            raise AssertionError("click_Alarms() returned False")

    run_step(8, "Main Screen: click Alarms tab", step_8)

    # ----------------------------
    # Step 9: Click Events tab
    # ----------------------------
    def step_9():
        ok = main.click_Events(timeout=20_000)
        print(f"click_Events returned: {ok}")
        if ok is not True:
            raise AssertionError("click_Events() returned False")

    run_step(9, "Main Screen: click Events tab", step_9)

    # ----------------------------
    # Step 10: Click Configuration Changes tab
    # ----------------------------
    def step_10():
        ok = main.click_Configuration_Changes(timeout=20_000)
        print(f"click_Configuration_Changes returned: {ok}")
        if ok is not True:
            raise AssertionError("click_Configuration_Changes() returned False")

    run_step(10, "Main Screen: click Configuration Changes tab", step_10)

    # ----------------------------
    # Step 11: Read alarms table
    # ----------------------------
    def step_11():
        table = main.alarms_table(timeout=20_000)
        print(f"alarms_table returned {len(table)} rows")
        print(f"table: {table}")
        if not isinstance(table, list):
            raise AssertionError("alarms_table() did not return a list")

    run_step(11, "Main Screen: get alarms table", step_11)

    # ----------------------------
    # Step 12: Get alarms table after clicking System
    # ----------------------------
    def step_12():
        table = main.get_alarms_table("System", timeout=20_000)
        print(f"table: {table}")
        table = main.get_alarms_table("ALL", timeout=20_000)
        print(f"table: {table}")
        table = main.get_alarms_table("4", timeout=20_000)
        print(f"table: {table}")  
        table = main.get_alarms_table("ETH 2", timeout=20_000)
        print(f"table: {table}")  

        if not isinstance(table, list):
            raise AssertionError("get_alarms_table('System') did not return a list")

    run_step(12, "Main Screen: get alarms table for System", step_12)

    # ----------------------------
    # Step 13: Set admin status of a port
    # ----------------------------
    def step_13():
        port = "1"
        status = "up"
        ok, dialog_text = main.set_admin_status(port, status, timeout=20_000)
        print(f"set_admin_status returned: ok={ok}, dialog_text='{dialog_text}'")
        if ok is not True:
            raise AssertionError(f"set_admin_status() returned False. Dialog text: '{dialog_text}'")
        if not dialog_text:
            raise AssertionError("Expected a confirmation dialog message but got empty text")
        
        ok, dialog_text = main.set_admin_status(port, "down", timeout=20_000)

    run_step(13, "Main Screen: set admin status of a port", step_13)

    # ----------------------------
    # Step 14: get product name
    # ----------------------------
    def step_14():
        product_name = main.get_system_product_name()
        print(f"get_system_product_name returned: '{product_name}'")
        if not product_name:
            raise AssertionError("get_system_product_name() returned empty string")

    run_step(14, "Main Screen: get system product name", step_14)

    # # ----------------------------
    # # Step 13: Restart dialog smoke (DISMISS so we don't actually reboot)
    # # ----------------------------
    # def step_13():
    #     ok, alert_msg = main.device_restart("factory", action_dismiss=True, timeout=12_000)
    #     print(f"device_restart returned: ok={ok}, alert='{alert_msg}'")
    #     if ok is not True:
    #         raise AssertionError(f"device_restart() returned False. Alert='{alert_msg}'")
    #     if not alert_msg:
    #         raise AssertionError("Expected a confirmation dialog message but got empty text")

    # run_step(13, "Main Screen: factory restart dialog (dismiss)", step_13)

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