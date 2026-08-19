"""
Created by: Yuval Dahan
Date: 03/08/2026
"""

from playwright.sync_api import sync_playwright
from PL_Devices.PL_Pages_New_Gui.PL_login_page_new_gui import PL_LoginPage
from PL_Devices.PL_Pages_New_Gui.PL_performance_page_new_gui import PL_PerformancePage
from Utils.utils import create_page, create_frame_html

# NOTE: adjust to your device / environment
SERVER_HOST_IP = "172.16.20.212"
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


def test_PL_performance_tab(page):
    pl = PL_LoginPage(page)
    perf = PL_PerformancePage(page)

    PORT = "1"

    # ----------------------------
    # Step 1: goto login page
    # ----------------------------
    def step_1():
        pl.goto(BASE_URL)
        # Strong signal: login form must be visible
        assert pl.login_root.is_visible(), "Login form is not visible after goto()"

    run_step(1, "PL Performance: goto login page", step_1)

    # ----------------------------
    # Step 2: positive login
    # ----------------------------
    def step_2():
        ok = pl.login(USERNAME, PASSWORD)
        print(f"Login returned: {ok}")
        if ok is not True:
            raise AssertionError("Login failed with valid credentials")

    run_step(2, "PL Performance: login with valid credentials", step_2)

    # ----------------------------
    # Step 3: Open Performance tab (main function under test)
    # ----------------------------
    def step_3():
        perf.open_performance_tab()

    run_step(3, "PL Performance: open Performance tab", step_3)

    # ----------------------------
    # Step 4: Set PM Period for a port
    # ----------------------------
    def step_4():
        ok = perf.set_PM_Period(PORT, "15 Minutes", timeout=12_000)
        print(f"set_PM_Period returned: {ok}")
        if ok is not True:
            raise AssertionError("set_PM_Period() returned False")

        ok = perf.set_PM_Period(PORT, "Days", timeout=12_000)
        print(f"set_PM_Period returned: {ok}")
        if ok is not True:
            raise AssertionError("set_PM_Period() returned False")

    run_step(4, "PL Performance: set PM Period", step_4)

    # ----------------------------
    # Step 5: Set PM Type for a port
    # ----------------------------
    def step_5():
        # create_frame_html(page)
        ok = perf.set_PM_Type(PORT, "Egress PM", timeout=12_000)
        print(f"set_PM_Type returned: {ok}")
        if ok is not True:
            raise AssertionError("set_PM_Type() returned False")

    run_step(5, "PL Performance: set PM Type", step_5)

    # ----------------------------
    # Step 6: Click Get PM
    # ----------------------------
    def step_6():
        ok = perf.click_on_Get_PM(PORT, timeout=12_000)
        print(f"click_on_Get_PM returned: {ok}")
        if ok is not True:
            raise AssertionError("click_on_Get_PM() returned False")

    run_step(6, "PL Performance: click Get PM", step_6)

    # ----------------------------
    # Step 7: Read PM table
    # ----------------------------
    def step_7():
        table = perf.get_PM_table(PORT, timeout=12_000)
        print(f"PM table rows: {len(table)}")
        for row in table:
            # {header: value}, e.g. {"Interval": ..., "Errors": ..., ..., "Valid": ...}
            print(row)

        if not isinstance(table, list):
            raise AssertionError("get_PM_table() did not return a list")

    run_step(7, "PL Performance: get PM table", step_7)

    # ----------------------------
    # Step 8: Reset a single interval row (destructive, clears PM data)
    # ----------------------------
    def step_8():
        perf.set_PM_Type(PORT, "Egress PM", timeout=12_000)
        perf.set_PM_Period(PORT, "Days", timeout=12_000)
        perf.click_on_Get_PM(PORT, timeout=12_000)
        # create_frame_html(page)
        ok, dialog_text = perf.click_reset_on_interval(PORT, 2, timeout=12_000)
        # print(f"click_reset_on_interval returned: ok={ok}, dialog_text='{dialog_text}'")
        if ok is not True:
            raise AssertionError(f"click_reset_on_interval() returned False. Dialog text: '{dialog_text}'")

    run_step(8, "PL Performance: reset a single interval", step_8)

    # ----------------------------
    # Step 9: Reset Port PM (destructive, clears the port's PM data)
    # ----------------------------
    def step_9():
        ok, dialog_text = perf.reset_port_PM(PORT, timeout=12_000)
        # print(f"reset_port_PM returned: ok={ok}, dialog_text='{dialog_text}'")
        if ok is not True:
            raise AssertionError(f"reset_port_PM() returned False. Dialog text: '{dialog_text}'")

    run_step(9, "PL Performance: reset port PM", step_9)

    # ----------------------------
    # Step 10: Reset All Ports PM (destructive, clears PM data on every port)
    # ----------------------------
    def step_10():
        ok, dialog_text = perf.reset_all_ports_PM(PORT, timeout=12_000)
        # print(f"reset_all_ports_PM returned: ok={ok}, dialog_text='{dialog_text}'")
        if ok is not True:
            raise AssertionError(f"reset_all_ports_PM() returned False. Dialog text: '{dialog_text}'")

    run_step(10, "PL Performance: reset all ports PM", step_10)

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
        browser, context, page = create_page(p, max_size=True)

        test_PL_performance_tab(page)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")
