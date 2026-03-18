"""
Created by: Yuval Dahan
Date: 24/02/2026

Comprehensive SNMPv2 Test
=====================================================
Tests the SNMPv2 tab inside Device Discovery.


*** Runtime: approximately 10 minutes ***
"""

from playwright.sync_api import sync_playwright

from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.device_discovery import DeviceDiscovery
from Pages.management_map import ManagementMap
from PL_Devices.PL_Pages.PL_login_page import PL_LoginPage
from PL_Devices.PL_Pages.PL_SNMP_page import PL_SNMPPage
from PL_Devices.PL_Pages.PL_main_screen_POM import PL_Main_Screen_POM
from Utils.utils import refresh_page, countdown_sleep, devices_are_up
import time
from time import sleep
from Utils.Logger import create_logger
import sys
from sys import argv
from Utilities.QCreporter import open_report, close_report, step_passed, step_failed



# Allow emojis on QC
import os
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass



# ================================================================
# Configuration
# ================================================================

if len(argv) == 2:
    directory = argv[1]
    const_dict = eval(open(directory, 'r').read())
    # print(path)
    globals().update(const_dict)
elif 2 < len(argv) < 3:
    directory = argv[1] + ' ' + argv[2]
    # print(path)
    const_dict = eval(open(directory, 'r').read())

    globals().update(const_dict)
else:
    # ================================================================
    # Values for the Parameter file (from QC)
    # ================================================================
    
    LW_SERVER_HOST_IP  = "172.16.10.22:8080"
    LW_USERNAME = "administrator"
    LW_PASSWORD = "administrator"

    DEVICE_IP = "172.16.20.113"
    DEVICE_IP_USER = "tech"
    DEVICE_IP_PASS = "packetlight"

    BLOCKED_DEVICE_IP = "172.16.40.11"
    TEST_DEVICE_IP = "172.16.30.15"
    
    INVALID_IP_ADDRESS = "256.1.1.1"

    READ_COMMUNITY = "read-only"
    WRITE_COMMUNITY = "read-write"
    ADMIN_COMMUNITY = "admin"



# ================================================================
# Values that should not be changed
# ================================================================

BASE_URL = f"http://{LW_SERVER_HOST_IP}/"
DEVICE_IP_URL = f"http://{DEVICE_IP}/"
BLOCKED_DEVICE_URL = f"http://{BLOCKED_DEVICE_IP}/"
CONTACT_PORT = 161
WAIT = 30

LOGGER_ROOT_DIRECTORY = 'G:\\Python\\PacketLight Automation\\LightWatch_WEB\\Scripts\\Device_Discovery\\SNMP\\LogFiles'
LOGGER_DIRECTORY_NAME = "SNMPv2"
LOG_FILE_NAME = 'SNMPv2.log'
REPORT_PATH = None

# ================================================================
# Helper – step runner
# ================================================================

def run_step(step_num, step_function, logger, report) -> bool:
    """
    Runs a step - prints consistent success / fail line.
    Returns True on success, False on failure.
    """
    try:
        step_function()
        print(f"Step {step_num} – Pass ✅")
        logger.info(f"Step {step_num} – Pass.")
        step_passed(report, f"Step {step_num} – Pass.")
        return True
    except Exception as e:
        print(f"Step {step_num} – Fail ❌  Error: {e}")
        logger.info(f"Step {step_num} – Fail.")
        logger.info(f"Step {step_num} Error: {e}")
        step_failed(report, f"Step {step_num} – Fail.")
        return False

def open_device_discovery(left_panel: LeftPanel):
    """
    Open Device Discovery via LeftPanel and assert it opened.
    """
    try:
        ok = left_panel.click_device_discovery()
    except Exception as e:
        raise AssertionError(f"Failed to call left_panel.click_device_discovery(). Error: {e}")
    
    if ok is not True:
        raise AssertionError(
            "left_panel.click_device_discovery() returned False "
            "(Device Discovery did not open).")

# ================================================================
# Main test
# ================================================================

def test_snmpv2_device_discovery(page, left_panel: LeftPanel, logger, report):
    device_discovery  = DeviceDiscovery(page)
    management_map  = ManagementMap(page)
    login  = LoginPage(page)

    results = {}

    #############################################################
    # Step 1 – Facrory default reset for all devices.           # 
    # Open Device Discovery and navigate to SNMPv2 tab.         # 
    #############################################################
    def step_1():
        ips_to_reset = [DEVICE_IP, BLOCKED_DEVICE_IP, TEST_DEVICE_IP]
        for ip in ips_to_reset:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            sleep(1)

            pl_main_screen_POM = PL_Main_Screen_POM(device_page)
            pl_main_screen_POM.device_restart("factory")
            sleep(5)
            device_page.close()

        # Wait for devices to come back up after factory default reset
        devices_are_up(ips_to_reset, wait_time=WAIT)

        open_device_discovery(left_panel)
        assert device_discovery.container().is_visible(), "Device Discovery container is not visible."
        device_discovery.click_SNMPv2()

    results[1] = run_step(1, step_1, logger, report)

    #######################################################
    # Step 2 – Read & store current SNMPv2 default values # 
    #######################################################

    stored_defaults = {}

    def step_2():
        stored_defaults["readCommunity"]  = device_discovery.get_SNMPv2_read_community()
        stored_defaults["writeCommunity"] = device_discovery.get_SNMPv2_write_community()
        stored_defaults["adminCommunity"] = device_discovery.get_SNMPv2_admin_community()
        stored_defaults["contactPort"]    = device_discovery.get_SNMPv2_contact_port()

        expected_defaults = {
            "readCommunity":  "admin",
            "writeCommunity": "admin",
            "adminCommunity": "admin",
            "contactPort":    "161",
        }

        errors = []

        for key, expected_value in expected_defaults.items():
            actual_value = str(stored_defaults.get(key)).strip()

            if actual_value != expected_value:
                errors.append(f"{key} mismatch: expected='{expected_value}', got='{actual_value}'")

        if errors:
            raise AssertionError("SNMPv2 default values are NOT factory defaults:\n  " + "\n  ".join(errors))

    results[2] = run_step(2, step_2, logger, report)

    ############################
    # Step 3 – Fill new values # 
    ############################

    community_value = "1"
    contact_port_value = 1

    def step_3():
        device_discovery.set_ip_address(DEVICE_IP)
        device_discovery.set_SNMPv2_read_community(community_value)
        device_discovery.set_SNMPv2_write_community(community_value)
        device_discovery.set_SNMPv2_admin_community(community_value)
        device_discovery.set_SNMPv2_contact_port(contact_port_value)

        got_ip_address = device_discovery.get_ip_address()
        got_read  = device_discovery.get_SNMPv2_read_community()
        got_write = device_discovery.get_SNMPv2_write_community()
        got_admin = device_discovery.get_SNMPv2_admin_community()
        got_port  = int(device_discovery.get_SNMPv2_contact_port())

        if (got_ip_address != DEVICE_IP) or (got_read != community_value) or \
            (got_write != community_value) or (got_admin != community_value) or (got_port != contact_port_value):
            raise AssertionError("Setting new values failed.")
            
    results[3] = run_step(3, step_3, logger, report)

    ###################################
    # Step 4 – Click Reset to Default #
    # Verify original values restored #
    ###################################
    def step_4():
        device_discovery.click_reset_to_default()

        device_discovery.click_SNMPv2()

        got_read  = device_discovery.get_SNMPv2_read_community()
        got_write = device_discovery.get_SNMPv2_write_community()
        got_admin = device_discovery.get_SNMPv2_admin_community()
        got_port  = device_discovery.get_SNMPv2_contact_port()

        errors = []
        if got_read != stored_defaults.get("readCommunity", ""):
            errors.append(f"readCommunity mismatch: expected='{stored_defaults.get('readCommunity')}' got='{got_read}'")

        if got_write != stored_defaults.get("writeCommunity", ""):
            errors.append(f"writeCommunity mismatch: expected='{stored_defaults.get('writeCommunity')}' got='{got_write}'")

        if got_admin != stored_defaults.get("adminCommunity", ""):
            errors.append(f"adminCommunity mismatch: expected='{stored_defaults.get('adminCommunity')}' got='{got_admin}'")

        if got_port != stored_defaults.get("contactPort", ""):
            errors.append(f"contactPort mismatch: expected='{stored_defaults.get('contactPort')}' got='{got_port}'")

        if errors:
            raise AssertionError("Reset to Default did not restore all values:\n  " + "\n  ".join(errors))

    results[4] = run_step(4, step_4, logger, report)

    ###############################################
    # Step 5 – Set new values and save as Default #
    # Verify saved values persisted               #
    ###############################################

    step5_expected = {
        "readCommunity":  "read-only",
        "writeCommunity": "read-write",
        "adminCommunity": "admin",
        "contactPort":    "161",
    }

    def step_5():
        refresh_page(page)

        open_device_discovery(left_panel)
        device_discovery.click_SNMPv2()

        device_discovery.set_SNMPv2_read_community(step5_expected["readCommunity"])
        device_discovery.set_SNMPv2_write_community(step5_expected["writeCommunity"])
        device_discovery.set_SNMPv2_admin_community(step5_expected["adminCommunity"])
        device_discovery.set_SNMPv2_contact_port(int(step5_expected["contactPort"]))

        device_discovery.click_save_as_default()
        device_discovery.confirm_default_override()
        sleep(5)

        # Logout
        ok_logout = login.logout()
        assert ok_logout, "Logout failed after Save as Default."

        # Login again
        ok_login = login.login(LW_USERNAME, LW_PASSWORD)
        assert ok_login, "Login failed after logout (Step 5)."

        open_device_discovery(left_panel)
        device_discovery.click_SNMPv2()

        got_read  = device_discovery.get_SNMPv2_read_community()
        got_write = device_discovery.get_SNMPv2_write_community()
        got_admin = device_discovery.get_SNMPv2_admin_community()
        got_port  = device_discovery.get_SNMPv2_contact_port()

        errors = []
        if got_read != step5_expected["readCommunity"]:
            errors.append(f"readCommunity: expected='{step5_expected['readCommunity']}' got='{got_read}'")

        if got_write != step5_expected["writeCommunity"]:
            errors.append(f"writeCommunity: expected='{step5_expected['writeCommunity']}' got='{got_write}'")

        if got_admin != step5_expected["adminCommunity"]:
            errors.append(f"adminCommunity: expected='{step5_expected['adminCommunity']}' got='{got_admin}'")

        if got_port != step5_expected["contactPort"]:
            errors.append(f"contactPort: expected='{step5_expected['contactPort']}' got='{got_port}'")

        if errors:
            raise AssertionError("Saved defaults did not persist after logout/login:\n  " + "\n  ".join(errors))

    results[5] = run_step(5, step_5, logger, report)

    ################################################################
    # Step 6 – Add the LW server to the DEVICE_IP SNMP Traps table #
    # Start Discovery                                              #
    ################################################################

    def step_6():
        refresh_page(page)
        device_page = page.context.new_page()

        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(DEVICE_IP_URL)
            ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            assert ok, f"Login to {DEVICE_IP} GUI failed."

            pl_SNMP = PL_SNMPPage(device_page)
            ok_tab = pl_SNMP.open_SNMP_tab()
            assert ok_tab, f"Failed to open SNMP tab on {DEVICE_IP}."

            success, _ = pl_SNMP.Add_Trap_Manager(IP=LW_SERVER_HOST_IP.split(":")[0], SNMP_Version="SNMP v2c")
            assert success, (f"Server IP ({LW_SERVER_HOST_IP.split(':')[0]}) was not added")
            refresh_page(page)

        finally:
            device_page.close()


        open_device_discovery(left_panel)
        device_discovery.click_SNMPv2()

        device_discovery.set_ip_address(DEVICE_IP)
        device_discovery.click_start_discovery()

        countdown_sleep(WAIT * 2, message="Wait for the discovery process to complete")
        refresh_page(page)

    results[6] = run_step(6, step_6, logger, report)

    ###################################################################
    # Step 7 – Verify that DEVICE_IP displaying on LW navigation info #
    ###################################################################

    def step_7():
        ok = left_panel.click_management_map()
        assert ok, "Failed to navigate to Management Map."

        management_map.show_navigation_info()

        in_nav = management_map.is_element_exist_on_navigation_info_list(DEVICE_IP)
        assert in_nav, (
            f"{DEVICE_IP} was not found in the Navigation Info list. "
            f"Discovery may not have completed yet.")

        management_map.navigation_info_open_element_details(DEVICE_IP)

    results[7] = run_step(7, step_7, logger, report)


    ############################################################
    # Step 8 – Login to DEVICE_IP GUI.                         #
    # Verify that the device is still in the SNMP Traps table. #
    ############################################################

    def step_8():
        # We need a second page for the PL device GUI.
        device_page = page.context.new_page()

        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(DEVICE_IP_URL)
            ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            assert ok, f"Login to {DEVICE_IP} GUI failed."

            pl_SNMP = PL_SNMPPage(device_page)
            ok_tab = pl_SNMP.open_SNMP_tab()
            assert ok_tab, f"Failed to open SNMP tab on {DEVICE_IP}."

            found = pl_SNMP.manager_address_added_to_SNMP_traps(LW_SERVER_HOST_IP.split(":")[0])
            assert found, (
                f"Server IP ({LW_SERVER_HOST_IP.split(':')[0]}) was NOT found "
                f"in the SNMP Traps table of {DEVICE_IP}.")

        finally:
            # Remove the LW server from the device
            is_deleted = pl_SNMP.Delete_Trap_Manager_eq_IP(IP=LW_SERVER_HOST_IP.split(":")[0])
            assert is_deleted, (f"Server IP ({LW_SERVER_HOST_IP.split(':')[0]}) was not deleted")
            refresh_page(page)

            device_page.close()

    results[8] = run_step(8, step_8, logger, report)

    #####################################
    # Step 9 – Fill invalid IP address. #
    # Verify field is INVALID.          #
    #####################################

    def step_9():
        refresh_page(page)

        open_device_discovery(left_panel)

        device_discovery.set_ip_address(INVALID_IP_ADDRESS)

        is_valid = device_discovery.is_ip_address_field_valid()
        if is_valid:
            raise AssertionError(f"IP field was expected to be INVALID for '{INVALID_IP_ADDRESS}', but it was reported as valid.")

    results[9] = run_step(9, step_9, logger, report)

    #########################################################
    # Step 10 – Verify multiple invalid IP strings rejected #
    #########################################################

    INVALID_IPS = [
        "a.1.1.1",
        "10.@.10.10",
        "10.10.&.10",
        "10.10.10.?"
    ]

    def step_10():
        refresh_page(page)

        open_device_discovery(left_panel)

        failed_ips = []
        for bad_ip in INVALID_IPS:
            device_discovery.set_ip_address(bad_ip)
            is_valid = device_discovery.is_ip_address_field_valid()
            if is_valid:
                failed_ips.append(bad_ip)

        if failed_ips:
            raise AssertionError(f"The following IPs were expected to be INVALID but were reported as valid: {failed_ips}")

    results[10] = run_step(10, step_10, logger, report)

    ##############################################
    # Step 11 – Fill special-char communities.   #
    # Verify Start Discovery button is DISABLED. #
    ##############################################

    SPECIAL_CHARS = "! @  # $ % ^ &  *  (  )  +  = < > ? : \" ; '"

    def step_11():
        refresh_page(page)

        open_device_discovery(left_panel)
        device_discovery.click_SNMPv2()

        device_discovery.set_ip_address(TEST_DEVICE_IP)
        device_discovery.set_SNMPv2_read_community(SPECIAL_CHARS)
        device_discovery.set_SNMPv2_write_community(SPECIAL_CHARS)
        device_discovery.set_SNMPv2_admin_community(SPECIAL_CHARS)
        device_discovery.set_SNMPv2_contact_port(CONTACT_PORT)

        is_enabled = device_discovery.is_start_discovery_btn_enabled()
        if is_enabled:
            raise AssertionError(
                "Start Discovery button was expected to be DISABLED when special characters "
                "are used in community strings, but it is enabled."
            )

    results[11] = run_step(11, step_11, logger, report)

    ###############################################
    # Step 12 – Fill invalid contact port values. #
    # Verify fiels is indeed invalid.             #
    ###############################################

    INVALID_CONTACT_PORT_VALUES = [
        -1,
        65536
    ]

    def step_12():
        refresh_page(page)

        open_device_discovery(left_panel)
        device_discovery.click_SNMPv2()

        failed_contact_ports = []
        for invalid_port in INVALID_CONTACT_PORT_VALUES:
            device_discovery.set_SNMPv2_contact_port(invalid_port)
            sleep(1)
            is_valid_port = device_discovery.is_contact_port_field_valid(SNMP_type="SNMPv2")
            if is_valid_port:
                failed_contact_ports.append(invalid_port)

            sleep(2)

        if failed_contact_ports:
            raise AssertionError(f"The following ports were expected to be INVALID but were reported as valid: {failed_contact_ports}")

    results[12] = run_step(12, step_12, logger, report)

    ###########################################################################
    # Step 13 – Set a device to SNMPv3 only.                                  #
    # Add the LW server to the BLOCKED_DEVICE SNMP Traps table                #
    # Start Discovery.                                                        #
    # Verify that the device was not added to the LW server                   #
    ###########################################################################

    def step_13():
        refresh_page(page)
        blocked_device_page = page.context.new_page()

        # Set device SNMP protocol to 'v3 only'
        try:
            pl_login_blocked_device = PL_LoginPage(blocked_device_page)
            pl_login_blocked_device.goto(BLOCKED_DEVICE_URL)
            ok = pl_login_blocked_device.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            assert ok, f"Login to {BLOCKED_DEVICE_IP} GUI failed."

            pl_SNMP_blocked_device = PL_SNMPPage(blocked_device_page)
            ok_version = pl_SNMP_blocked_device.set_SNMP_protocol_version("v3 only")
            assert ok_version, (f"set_SNMP_protocol_version('v3 only') returned False for {BLOCKED_DEVICE_IP}.")

            success, _ = pl_SNMP_blocked_device.Add_Trap_Manager(IP=LW_SERVER_HOST_IP.split(":")[0], SNMP_Version="SNMP v3")
            assert success, (f"Server IP ({LW_SERVER_HOST_IP.split(':')[0]}) was not added")
            refresh_page(blocked_device_page)

        finally:
            blocked_device_page.close()

        # Run SNMPv2 discovery against device with SNMPv3
        open_device_discovery(left_panel)
        device_discovery.click_SNMPv2()

        device_discovery.set_ip_address(BLOCKED_DEVICE_IP)
        device_discovery.set_SNMPv2_read_community(READ_COMMUNITY)
        device_discovery.set_SNMPv2_write_community(WRITE_COMMUNITY)
        device_discovery.set_SNMPv2_admin_community(ADMIN_COMMUNITY)
        device_discovery.set_SNMPv2_contact_port(CONTACT_PORT)

        device_discovery.click_start_discovery()

        countdown_sleep(WAIT, message="Wait for the discovery process to complete")
        refresh_page(page)

        # Verify device did NOT add the server to its SNMP Traps
        blocked_device_page2 = page.context.new_page()

        try:
            pl_login_blocked_device2 = PL_LoginPage(blocked_device_page2)
            pl_login_blocked_device2.goto(BLOCKED_DEVICE_URL)
            ok = pl_login_blocked_device2.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            assert ok, f"Login to {BLOCKED_DEVICE_IP} GUI failed (verification step)."

            pl_SNMP_blocked_device2 = PL_SNMPPage(blocked_device_page2)
            pl_SNMP_blocked_device2.open_SNMP_tab()
            
            # Verify that BLOCKED_DEVICE_URL is not displaying on LW navigation info
            ok = left_panel.click_management_map()
            assert ok, "Failed to navigate to Management Map."

            management_map.show_navigation_info()

            in_nav = management_map.is_element_exist_on_navigation_info_list(BLOCKED_DEVICE_IP)
            assert not in_nav, (
                f"{BLOCKED_DEVICE_IP} was found in the Navigation Info list. "
                f"It should not be there.")

        finally:
            # Remove the LW server from the device
            is_deleted = pl_SNMP_blocked_device2.Delete_Trap_Manager_eq_IP(IP=LW_SERVER_HOST_IP.split(":")[0])
            assert is_deleted, (f"Server IP ({LW_SERVER_HOST_IP.split(':')[0]}) was not deleted")
            refresh_page(page)

            blocked_device_page2.close()

    results[13] = run_step(13, step_13, logger, report)

    ######################################################
    # Step 14 – Reset SNMPv2 fields to default values.   #
    ######################################################

    def step_14():
        refresh_page(page)

        open_device_discovery(left_panel)
        device_discovery.click_SNMPv2()

        device_discovery.set_SNMPv2_read_community(ADMIN_COMMUNITY)
        device_discovery.set_SNMPv2_write_community(ADMIN_COMMUNITY)
        device_discovery.set_SNMPv2_admin_community(ADMIN_COMMUNITY)
        device_discovery.set_SNMPv2_contact_port(CONTACT_PORT)

        device_discovery.click_save_as_default()
        device_discovery.confirm_default_override()
        sleep(5)

        # Logout
        ok_logout = login.logout()
        assert ok_logout, "Logout failed after Save as Default."

        # Login again
        ok_login = login.login(LW_USERNAME, LW_PASSWORD)
        assert ok_login, "Login failed after logout (Step 14)."

        open_device_discovery(left_panel)
        device_discovery.click_SNMPv2()

        got_read  = device_discovery.get_SNMPv2_read_community()
        got_write = device_discovery.get_SNMPv2_write_community()
        got_admin = device_discovery.get_SNMPv2_admin_community()
        got_port  = int(device_discovery.get_SNMPv2_contact_port())

        errors = []
        if got_read != ADMIN_COMMUNITY:
            errors.append(f"readCommunity: expected='{ADMIN_COMMUNITY}' got='{got_read}'")

        if got_write != ADMIN_COMMUNITY:
            errors.append(f"writeCommunity: expected='{ADMIN_COMMUNITY}' got='{got_write}'")

        if got_admin != ADMIN_COMMUNITY:
            errors.append(f"adminCommunity: expected='{ADMIN_COMMUNITY}' got='{got_admin}'")

        if got_port != CONTACT_PORT:
            errors.append(f"contactPort: expected='{CONTACT_PORT}' got='{got_port}'")

        if errors:
            raise AssertionError("Saved defaults did not persist after logout/login:\n  " + "\n  ".join(errors))

    results[14] = run_step(14, step_14, logger, report)

    ###################
    # Overall Results #
    ###################
    print("\n" + "=" * 60)
    all_passed = all(results.values())
    failed_steps = [str(k) for k, v in results.items() if not v]
    if all_passed:
        print("TEST PASSED ✅")
        logger.info(f"TEST PASSED")
    else:
        print(f"TEST FAILED ❌  Failed steps: {', '.join(failed_steps)}")
        logger.info(f"TEST FAILED")
    print("=" * 60)


# ================================================================
# Main 
# ================================================================

if __name__ == "__main__":
    start_time = time.perf_counter()

    with sync_playwright() as p:
        logger = create_logger(LOGGER_ROOT_DIRECTORY, LOG_FILE_NAME, directory_name=LOGGER_DIRECTORY_NAME)
        report = open_report(path=REPORT_PATH)

        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        login_page = LoginPage(page)
        login_page.goto(BASE_URL)

        if not login_page.login(LW_USERNAME, LW_PASSWORD):
            print("Login Failed ❌")
            context.close()
            browser.close()
            raise SystemExit(1)

        print("Login Success ✅\n")

        left_panel = LeftPanel(page)
        refresh_page(page)

        test_snmpv2_device_discovery(page, left_panel, logger, report)

        context.close()
        browser.close()
        close_report(report)

    end_time = time.perf_counter()
    print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
    logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")