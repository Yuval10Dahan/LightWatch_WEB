"""
Created by: Yuval Dahan
Date: 23/02/2026
"""

from playwright.sync_api import sync_playwright, expect
from PL_Devices.PL_Pages.PL_login_page import PL_LoginPage
from PL_Devices.PL_Pages.PL_SNMP_page import PL_SNMPPage


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


def test_PL_SNMP_tab(page):
    pl = PL_LoginPage(page)
    snmp = PL_SNMPPage(page)

    # ----------------------------
    # Step 1: goto login page
    # ----------------------------
    def step_1():
        pl.goto(BASE_URL)
        # Strong signal: login form must be visible
        assert pl.login_root.is_visible(), "Login form is not visible after goto()"

    run_step(1, "PL SNMP: goto login page", step_1)

    # ----------------------------
    # Step 2: positive login
    # ----------------------------
    def step_2():
        ok = pl.login(USERNAME, PASSWORD)
        print(f"Login returned: {ok}")
        if ok is not True:
            raise AssertionError("Login failed with valid credentials")

    run_step(2, "PL SNMP: login with valid credentials", step_2)

    # ----------------------------
    # Step 3: Open SNMP tab (main function under test)
    # ----------------------------
    def step_3():
        ok = snmp.open_SNMP_tab(timeout=12_000)
        print(f"open_snmp_tab returned: {ok}")
        if ok is not True:
            raise AssertionError("open_snmp_tab() returned False")

    run_step(3, "PL SNMP: open SNMP tab", step_3)

    # ----------------------------
    # Step 4: t
    # ----------------------------
    def step_4():
        ok = snmp.set_SNMP_protocol_version("v3 only")
        print(f"set_SNMP_protocol_version: {ok}")
        if ok is not True:
            raise AssertionError("set_SNMP_protocol_version() returned False")
        
        ok = snmp.set_SNMP_protocol_version("v1, v2c, v3")
        print(f"set_SNMP_protocol_version: {ok}")
        if ok is not True:
            raise AssertionError("set_SNMP_protocol_version() returned False")

    run_step(4, "PL SNMP: open SNMP tab", step_4)

    # ----------------------------
    # Step 5: Open SNMP tab again (idempotent smoke)
    # ----------------------------
    def step_5():
        snmp_traps_table = snmp.get_SNMP_traps_table()
        # print(f"SNMP Traps table: {snmp_traps_table}")

        ok = snmp.manager_address_added_to_SNMP_traps("172.16.10.22")
        print(f"Address found: {ok}")

    run_step(5, "PL SNMP: open SNMP tab (idempotent)", step_5)

    # ---------------------------------------
    # Step 6: Add SNMP Trap and delete it
    # ---------------------------------------
    def step_6():
        success, last_msg = snmp.Add_Trap_Manager("172.16.10.22", "SNMP v2c")
        print(f"success: {success}, last_msg: {last_msg}")
        is_deleted = snmp.Delete_Trap_Manager_eq_IP("172.16.10.22")
        print(f"Deleted: {is_deleted}")

    run_step(6, "PL SNMP: open SNMP tab (idempotent)", step_6)

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

        test_PL_SNMP_tab(page)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")
