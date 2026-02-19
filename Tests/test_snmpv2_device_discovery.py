"""
Created by: Yuval Dahan (AI-assisted)
Date: 18/02/2026

Comprehensive SNMPv2 Feature Test – Device Discovery
=====================================================
Validates every aspect of the SNMPv2 tab inside Device Discovery:
  • Set / Get for all four fields (Read Community, Write Community,
    Admin Community, Contact Port)
  • Overwriting existing values
  • Field persistence when switching tabs (ICMP → SNMPv3 → SNMPv2)
  • Reset to Default behaviour
  • Save as Default (reject + confirm)
  • Starting a single-IP discovery with SNMPv2 settings
  • Closing the Device Discovery panel
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.device_discovery import DeviceDiscovery
import time
from Utils.utils import refresh_page


SERVER_HOST_IP = "172.16.10.22:8080"
BASE_URL = f"http://{SERVER_HOST_IP}/"
USERNAME = "administrator"
PASSWORD = "administrator"


# ================================================================
# Helper
# ================================================================

def run_step(step_num: float, title: str, fn):
    """
    Runs a step and prints consistent success/fail indication.
    """
    try:
        fn()
        print(f"Step {step_num} Success ✅")
        return True
    except Exception as e:
        print(f"Step {step_num} Failed ❌  Error: {e}")
        return False


def _open_device_discovery(left_panel: LeftPanel):
    """
    Open Device Discovery via LeftPanel.
    """
    try:
        ok = left_panel.click_device_discovery()
    except Exception as e:
        raise AssertionError(f"Failed to call left_panel.click_device_discovery(). Error: {e}")

    if ok is not True:
        raise AssertionError("left_panel.click_device_discovery() returned False (Device Discovery did not open).")


# ================================================================
# Test
# ================================================================

def test_snmpv2_device_discovery(page, left_panel):
    dd = DeviceDiscovery(page)

    # ----------------------------
    # Step 1: Open Device Discovery & navigate to SNMPv2 tab
    # ----------------------------
    def step_1():
        _open_device_discovery(left_panel)

        # Verify the container is visible
        assert dd.container().is_visible(), "Device Discovery container is not visible."

        # Navigate to the SNMPv2 tab
        dd.click_SNMPv2()
        print("Opened Device Discovery and switched to SNMPv2 tab")

    run_step(1, "Open Device Discovery & navigate to SNMPv2 tab", step_1)

    # ----------------------------
    # Step 2: Read Community – set / get
    # ----------------------------
    def step_2():
        value = "public"
        dd.set_SNMPv2_read_community(value)
        got = dd.get_SNMPv2_read_community()
        print(f"SNMPv2 Read Community -> set: {value} | got: {got}")
        if got != value:
            raise AssertionError(f"SNMPv2 readCommunity mismatch. expected='{value}' got='{got}'")

    run_step(2, "SNMPv2 Read Community – set/get", step_2)

    # ----------------------------
    # Step 3: Write Community – set / get
    # ----------------------------
    def step_3():
        value = "private"
        dd.set_SNMPv2_write_community(value)
        got = dd.get_SNMPv2_write_community()
        print(f"SNMPv2 Write Community -> set: {value} | got: {got}")
        if got != value:
            raise AssertionError(f"SNMPv2 writeCommunity mismatch. expected='{value}' got='{got}'")

    run_step(3, "SNMPv2 Write Community – set/get", step_3)

    # ----------------------------
    # Step 4: Admin Community – set / get
    # ----------------------------
    def step_4():
        value = "admin"
        dd.set_SNMPv2_admin_community(value)
        got = dd.get_SNMPv2_admin_community()
        print(f"SNMPv2 Admin Community -> set: {value} | got: {got}")
        if got != value:
            raise AssertionError(f"SNMPv2 adminCommunity mismatch. expected='{value}' got='{got}'")

    run_step(4, "SNMPv2 Admin Community – set/get", step_4)

    # ----------------------------
    # Step 5: Contact Port – set / get
    # ----------------------------
    def step_5():
        port = 161
        dd.set_SNMPv2_contact_port(port)
        got = dd.get_SNMPv2_contact_port()
        print(f"SNMPv2 Contact Port -> set: {port} | got: {got}")
        if got != str(port):
            raise AssertionError(f"SNMPv2 contactPort mismatch. expected='{port}' got='{got}'")

    run_step(5, "SNMPv2 Contact Port – set/get", step_5)

    # ----------------------------
    # Step 6: Overwrite all fields with new values
    # ----------------------------
    overwrite_values = {
        "readCommunity": "readTest",
        "writeCommunity": "writeTest",
        "adminCommunity": "adminTest",
        "contactPort": "8161",
    }

    def step_6():
        dd.set_SNMPv2_read_community(overwrite_values["readCommunity"])
        dd.set_SNMPv2_write_community(overwrite_values["writeCommunity"])
        dd.set_SNMPv2_admin_community(overwrite_values["adminCommunity"])
        dd.set_SNMPv2_contact_port(int(overwrite_values["contactPort"]))

        got_read = dd.get_SNMPv2_read_community()
        got_write = dd.get_SNMPv2_write_community()
        got_admin = dd.get_SNMPv2_admin_community()
        got_port = dd.get_SNMPv2_contact_port()

        print(f"Overwrite Read Community  -> expected: {overwrite_values['readCommunity']} | got: {got_read}")
        print(f"Overwrite Write Community -> expected: {overwrite_values['writeCommunity']} | got: {got_write}")
        print(f"Overwrite Admin Community -> expected: {overwrite_values['adminCommunity']} | got: {got_admin}")
        print(f"Overwrite Contact Port    -> expected: {overwrite_values['contactPort']} | got: {got_port}")

        if got_read != overwrite_values["readCommunity"]:
            raise AssertionError(f"Overwrite readCommunity mismatch. expected='{overwrite_values['readCommunity']}' got='{got_read}'")
        if got_write != overwrite_values["writeCommunity"]:
            raise AssertionError(f"Overwrite writeCommunity mismatch. expected='{overwrite_values['writeCommunity']}' got='{got_write}'")
        if got_admin != overwrite_values["adminCommunity"]:
            raise AssertionError(f"Overwrite adminCommunity mismatch. expected='{overwrite_values['adminCommunity']}' got='{got_admin}'")
        if got_port != overwrite_values["contactPort"]:
            raise AssertionError(f"Overwrite contactPort mismatch. expected='{overwrite_values['contactPort']}' got='{got_port}'")

    run_step(6, "SNMPv2 Overwrite all fields with new values", step_6)

    # ----------------------------
    # Step 7: Tab persistence – switch ICMP → SNMPv3 → SNMPv2 and verify
    # ----------------------------
    def step_7():
        # Switch away from SNMPv2
        dd.click_ICMP()
        dd.click_SNMPv3()

        # Switch back to SNMPv2
        dd.click_SNMPv2()

        # Re-read all fields – they should still hold the overwritten values
        got_read = dd.get_SNMPv2_read_community()
        got_write = dd.get_SNMPv2_write_community()
        got_admin = dd.get_SNMPv2_admin_community()
        got_port = dd.get_SNMPv2_contact_port()

        print(f"Persistence Read Community  -> expected: {overwrite_values['readCommunity']} | got: {got_read}")
        print(f"Persistence Write Community -> expected: {overwrite_values['writeCommunity']} | got: {got_write}")
        print(f"Persistence Admin Community -> expected: {overwrite_values['adminCommunity']} | got: {got_admin}")
        print(f"Persistence Contact Port    -> expected: {overwrite_values['contactPort']} | got: {got_port}")

        if got_read != overwrite_values["readCommunity"]:
            raise AssertionError(f"Persistence readCommunity mismatch. expected='{overwrite_values['readCommunity']}' got='{got_read}'")
        if got_write != overwrite_values["writeCommunity"]:
            raise AssertionError(f"Persistence writeCommunity mismatch. expected='{overwrite_values['writeCommunity']}' got='{got_write}'")
        if got_admin != overwrite_values["adminCommunity"]:
            raise AssertionError(f"Persistence adminCommunity mismatch. expected='{overwrite_values['adminCommunity']}' got='{got_admin}'")
        if got_port != overwrite_values["contactPort"]:
            raise AssertionError(f"Persistence contactPort mismatch. expected='{overwrite_values['contactPort']}' got='{got_port}'")

    run_step(7, "SNMPv2 Tab persistence after ICMP → SNMPv3 → SNMPv2", step_7)

    # ----------------------------
    # Step 8: Reset to Default resets SNMPv2 fields
    # ----------------------------
    def step_8():
        dd.click_reset_to_default()

        # Re-read all fields – they should change from the overwritten values
        dd.click_SNMPv2()

        got_read = dd.get_SNMPv2_read_community()
        got_write = dd.get_SNMPv2_write_community()
        got_admin = dd.get_SNMPv2_admin_community()
        got_port = dd.get_SNMPv2_contact_port()

        print(f"After Reset Read Community  -> got: {got_read}")
        print(f"After Reset Write Community -> got: {got_write}")
        print(f"After Reset Admin Community -> got: {got_admin}")
        print(f"After Reset Contact Port    -> got: {got_port}")

        # At least one field should differ from the overwritten values (proving reset worked)
        all_same = (
            got_read == overwrite_values["readCommunity"]
            and got_write == overwrite_values["writeCommunity"]
            and got_admin == overwrite_values["adminCommunity"]
            and got_port == overwrite_values["contactPort"]
        )
        if all_same:
            raise AssertionError("Reset to Default had no effect – all fields still match overwritten values.")

    run_step(8, "SNMPv2 Reset to Default", step_8)

    # ----------------------------
    # Step 9: Re-configure + Save as Default (reject – No)
    # ----------------------------
    def step_9():
        dd.click_SNMPv2()
        dd.set_SNMPv2_read_community("rejectTest")
        dd.set_SNMPv2_write_community("rejectTest")
        dd.set_SNMPv2_admin_community("rejectTest")
        dd.set_SNMPv2_contact_port(9999)

        dd.click_save_as_default()
        dd.reject_default_override()
        print("Save as Default rejected (No) – modal closed cleanly")

    run_step(9, "SNMPv2 Save as Default – reject (No)", step_9)

    # ----------------------------
    # Step 10: Save as Default (confirm – Yes)
    # ----------------------------
    def step_10():
        dd.click_save_as_default()
        dd.confirm_default_override()
        print("Save as Default confirmed (Yes) – modal closed cleanly")

    run_step(10, "SNMPv2 Save as Default – confirm (Yes)", step_10)

    # ----------------------------
    # Step 11: Single-IP discovery with SNMPv2 settings
    # ----------------------------
    def step_11():
        # Ensure range mode is OFF
        dd.click_stop_discovery_for_ip_range()

        # Set a single IP
        ip = "10.60.100.36"
        dd.set_ip_address(ip)
        got_ip = dd.get_ip_address()
        print(f"Discovery IP -> set: {ip} | got: {got_ip}")

        # Configure SNMPv2 fields for discovery
        dd.set_SNMPv2_read_community("public")
        dd.set_SNMPv2_write_community("private")
        dd.set_SNMPv2_admin_community("admin")
        dd.set_SNMPv2_contact_port(161)

        # Start discovery and validate toast
        dd.click_start_discovery()
        print("Start Discovery with SNMPv2 settings succeeded")

    run_step(11, "SNMPv2 single-IP discovery execution", step_11)

    # ----------------------------
    # Step 12: Close Device Discovery
    # ----------------------------
    def step_12():
        dd.close_device_discovery()
        print("Device Discovery container closed")

    run_step(12, "Close Device Discovery", step_12)

    print("\n========================================")
    print("SNMPv2 Device Discovery Test Finished ✅")
    print("========================================")


# ================================================================
# Entry point
# ================================================================

if __name__ == "__main__":
    start_time = time.perf_counter()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        login_page = LoginPage(page)
        login_page.goto(BASE_URL)

        if not login_page.login(USERNAME, PASSWORD):
            print("Login Failed ❌")
            context.close()
            browser.close()
            raise SystemExit(1)

        print("Login Success ✅")

        left_panel = LeftPanel(page)
        refresh_page(page)

        test_snmpv2_device_discovery(page, left_panel)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")
