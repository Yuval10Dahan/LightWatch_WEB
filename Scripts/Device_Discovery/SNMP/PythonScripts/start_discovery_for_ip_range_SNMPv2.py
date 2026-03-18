"""
Created by: Yuval Dahan
Date: 03/03/2026

=====================================================
Tests the start discovery for IP range for SNMPv2.


*** Runtime: approximately == minutes ***
"""

from playwright.sync_api import sync_playwright

from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.device_discovery import DeviceDiscovery
from Pages.management_map import ManagementMap
from Pages.domain_management import DomainManagement
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

    DEVICE_IP1 = "172.16.30.123"
    DEVICE_IP2 = "172.16.30.124"
    DEVICE_IP_USER = "tech"
    DEVICE_IP_PASS = "packetlight"

    INVALID_START_IP_ADDRESS = "256.1.1.1"
    INVALID_END_IP_ADDRESS = "256.1.1.2"

    READ_COMMUNITY = "read-only"
    WRITE_COMMUNITY = "read-write"
    ADMIN_COMMUNITY = "admin"



# ================================================================
# Values that should not be changed
# ================================================================

BASE_URL = f"http://{LW_SERVER_HOST_IP}/"
DEVICE_IP_URL1 = f"http://{DEVICE_IP1}/"
DEVICE_IP_URL2 = f"http://{DEVICE_IP2}/"
DEVICE_IPS_RANGE_LIST = [DEVICE_IP1, DEVICE_IP2]
CONTACT_PORT = 161
WAIT = 30

LOGGER_ROOT_DIRECTORY = 'G:\\Python\\PacketLight Automation\\LightWatch_WEB\\Scripts\\Device_Discovery\\SNMP\\LogFiles'
LOGGER_DIRECTORY_NAME = "discovery_for_ip_range_SNMPv2"
LOG_FILE_NAME = 'discovery_for_ip_range_SNMPv2.log'
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

def test_discovery_for_ip_range_snmpv2(page, left_panel: LeftPanel, logger, report):
    device_discovery  = DeviceDiscovery(page)
    management_map  = ManagementMap(page)
    login  = LoginPage(page)

    results = {}

    #############################################################
    # Step 1 – Facrory default reset for all devices.           # 
    # Open Device Discovery and navigate to SNMPv2 tab.         # 
    #############################################################
    def step_1():
        ips_to_reset = [DEVICE_IP1, DEVICE_IP2]
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
        device_discovery.click_start_discovery_for_ip_range()
        device_discovery.set_range_start_ip(DEVICE_IP1)
        device_discovery.set_range_end_ip(DEVICE_IP2)

        device_discovery.set_SNMPv2_read_community(community_value)
        device_discovery.set_SNMPv2_write_community(community_value)
        device_discovery.set_SNMPv2_admin_community(community_value)
        device_discovery.set_SNMPv2_contact_port(contact_port_value)

        got_range_start_ip = device_discovery.get_range_start_ip()
        got_range_end_ip = device_discovery.get_range_end_ip()
        got_read  = device_discovery.get_SNMPv2_read_community()
        got_write = device_discovery.get_SNMPv2_write_community()
        got_admin = device_discovery.get_SNMPv2_admin_community()
        got_port  = int(device_discovery.get_SNMPv2_contact_port())

        if (got_range_start_ip != DEVICE_IP1) or (got_range_end_ip != DEVICE_IP2) or (got_read != community_value) or \
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

        for ip in DEVICE_IPS_RANGE_LIST:
            device_page = page.context.new_page()

            try:
                pl_login = PL_LoginPage(device_page)
                pl_login.goto(f"http://{ip}/")
                ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
                assert ok, f"Login to {ip} GUI failed."

                pl_SNMP = PL_SNMPPage(device_page)
                ok_tab = pl_SNMP.open_SNMP_tab()
                assert ok_tab, f"Failed to open SNMP tab on {ip}."

                success, _ = pl_SNMP.Add_Trap_Manager(IP=LW_SERVER_HOST_IP.split(":")[0], SNMP_Version="SNMP v2c")
                assert success, (f"Server IP ({LW_SERVER_HOST_IP.split(':')[0]}) was not added")
                refresh_page(page)

            finally:
                device_page.close()


        open_device_discovery(left_panel)
        device_discovery.click_SNMPv2()
        device_discovery.click_start_discovery_for_ip_range()

        device_discovery.set_range_start_ip(DEVICE_IP1)
        device_discovery.set_range_end_ip(DEVICE_IP2)
        device_discovery.click_start_discovery()

        countdown_sleep(WAIT * 2, message="Wait for the discovery process to complete")
        refresh_page(page)

    results[6] = run_step(6, step_6, logger, report)

    ########################################################################################
    # Step 7 – Verify that all devices in the IP range are displayed on LW navigation info #
    ########################################################################################

    def step_7():
        ok = left_panel.click_management_map()
        assert ok, "Failed to navigate to Management Map."

        management_map.show_navigation_info()

        missing_devices = []

        for ip in DEVICE_IPS_RANGE_LIST:
            in_nav = management_map.is_element_exist_on_navigation_info_list(ip)
            if not in_nav:
                missing_devices.append(ip)
            else:
                # Optional: open details only if found
                management_map.navigation_info_open_element_details(ip)

        if missing_devices:
            raise AssertionError(
                f"The following devices were not found in the Navigation Info list: {missing_devices}. "
                f"Discovery may not have completed yet."
            )

    results[7] = run_step(7, step_7, logger, report)


    #############################################################
    # Step 8 – Login to each device GUI in the IP range.        #
    # Verify that the LW server is still in the SNMP Traps      #
    # table for each device.                                    #
    #############################################################

    def step_8():
        server_ip = LW_SERVER_HOST_IP.split(":")[0]
        failed_devices = []

        for ip in DEVICE_IPS_RANGE_LIST:
            device_page = page.context.new_page()
            pl_SNMP = None  # so finally won't crash if init fails

            try:
                pl_login = PL_LoginPage(device_page)
                pl_login.goto(f"http://{ip}/")

                ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
                assert ok, f"Login to {ip} GUI failed."

                pl_SNMP = PL_SNMPPage(device_page)
                ok_tab = pl_SNMP.open_SNMP_tab()
                assert ok_tab, f"Failed to open SNMP tab on {ip}."

                found = pl_SNMP.manager_address_added_to_SNMP_traps(server_ip)
                assert found, (f"Server IP ({server_ip}) was NOT found in the SNMP Traps table of {ip}.")

            except Exception as e:
                failed_devices.append(f"{ip} -> {e}")

            finally:
                # Cleanup: remove LW server from the device 
                try:
                    if pl_SNMP is not None:
                        is_deleted = pl_SNMP.Delete_Trap_Manager_eq_IP(IP=server_ip)
                        assert is_deleted, f"Server IP ({server_ip}) was not deleted from {ip}"
                finally:
                    device_page.close()

        if failed_devices:
            raise AssertionError("Step 8 failures:\n  " + "\n  ".join(failed_devices))

    results[8] = run_step(8, step_8, logger, report)

    ###############################################
    # Step 9 – Fill invalid IP address in range.  #
    # Verify range Start/End fields are INVALID.  #
    ###############################################

    def step_9():
        refresh_page(page)

        open_device_discovery(left_panel)
        device_discovery.click_SNMPv2()
        device_discovery.click_start_discovery_for_ip_range()

        # Start IP invalid
        device_discovery.set_range_start_ip(INVALID_START_IP_ADDRESS)
        start_valid = device_discovery.is_range_start_ip_field_valid()
        if start_valid:
            raise AssertionError(
                f"Range Start IP field was expected to be INVALID for '{INVALID_START_IP_ADDRESS}', "
                f"but it was reported as valid."
            )

        # End IP invalid
        device_discovery.set_range_end_ip(INVALID_END_IP_ADDRESS)
        end_valid = device_discovery.is_range_end_ip_field_valid()
        if end_valid:
            raise AssertionError(
                f"Range End IP field was expected to be INVALID for '{INVALID_END_IP_ADDRESS}', "
                f"but it was reported as valid."
            )

    results[9] = run_step(9, step_9, logger, report)

    #########################################################
    # Step 10 – Verify multiple invalid IP strings rejected #
    # in Range Start/End IP fields.                         #
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
        device_discovery.click_SNMPv2()
        device_discovery.click_start_discovery_for_ip_range()

        failed_start_ips = []
        failed_end_ips = []

        for bad_ip in INVALID_IPS:
            # Validate Start IP
            device_discovery.set_range_start_ip(bad_ip)
            start_valid = device_discovery.is_range_start_ip_field_valid()
            if start_valid:
                failed_start_ips.append(bad_ip)

            # Validate End IP
            device_discovery.set_range_end_ip(bad_ip)
            end_valid = device_discovery.is_range_end_ip_field_valid()
            if end_valid:
                failed_end_ips.append(bad_ip)

        errors = []
        if failed_start_ips:
            errors.append(f"Start IP field accepted invalid values: {failed_start_ips}")
        if failed_end_ips:
            errors.append(f"End IP field accepted invalid values: {failed_end_ips}")

        if errors:
            raise AssertionError(";\n".join(errors))

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
        device_discovery.click_start_discovery_for_ip_range()

        device_discovery.set_range_start_ip(DEVICE_IP1)
        device_discovery.set_range_end_ip(DEVICE_IP2)

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
        device_discovery.click_start_discovery_for_ip_range()

        device_discovery.set_range_start_ip(DEVICE_IP1)
        device_discovery.set_range_end_ip(DEVICE_IP2)

        failed_contact_ports = []

        for invalid_port in INVALID_CONTACT_PORT_VALUES:
            device_discovery.set_SNMPv2_contact_port(invalid_port)

            is_valid_port = device_discovery.is_contact_port_field_valid(SNMP_type="SNMPv2")

            if is_valid_port:
                failed_contact_ports.append(invalid_port)

        if failed_contact_ports:
            raise AssertionError(f"The following ports were expected to be INVALID but were reported as valid: {failed_contact_ports}")

    results[12] = run_step(12, step_12, logger, report)

    ############################################################################
    # Step 13 – Blocked range devices (SNMPv3 only) should NOT be discovered.  #
    # - Delete LW trap from DEVICE_IP1/DEVICE_IP2                              #
    # - Remove devices from LW.                                                #
    # - Set both devices to "v3 only"                                          #
    # - Run SNMPv2 discovery in RANGE mode (DEVICE_IP1..DEVICE_IP2)            #
    # - Verify both NOT in LW Navigation Info                                  #
    ############################################################################

    def step_13():
        refresh_page(page)
        server_ip = LW_SERVER_HOST_IP.split(":")[0]
        blocked_devices = [DEVICE_IP1, DEVICE_IP2]

        # Helper: delete LW trap on device (best-effort)
        def delete_lw_trap_from_device(device_ip: str):
            device_url = f"http://{device_ip}/"
            device_page = page.context.new_page()
            pl_SNMP = None

            try:
                pl_login = PL_LoginPage(device_page)
                pl_login.goto(device_url)

                ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
                assert ok, f"Login to {device_ip} GUI failed."

                pl_SNMP = PL_SNMPPage(device_page)
                ok_tab = pl_SNMP.open_SNMP_tab()
                assert ok_tab, f"Failed to open SNMP tab on {device_ip}."

                # If not found, it might return False.
                # We don't want Step to fail here if it simply doesn't exist.
                try:
                    pl_SNMP.Delete_Trap_Manager_eq_IP(IP=server_ip)
                except Exception:
                    pass

            finally:
                device_page.close()


        # Helper: set SNMP protocol to v3 only
        def set_device_v3_only(device_ip: str):
            device_url = f"http://{device_ip}/"
            device_page = page.context.new_page()

            try:
                pl_login = PL_LoginPage(device_page)
                pl_login.goto(device_url)

                ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
                assert ok, f"Login to {device_ip} GUI failed."

                pl_SNMP = PL_SNMPPage(device_page)
                ok_version = pl_SNMP.set_SNMP_protocol_version("v3 only")
                assert ok_version, f"set_SNMP_protocol_version('v3 only') returned False for {device_ip}."

                refresh_page(device_page)

            finally:
                device_page.close()


        # Delete LW trap from each device
        for ip in blocked_devices:
            delete_lw_trap_from_device(ip)

        ok = left_panel.click_domain_management()
        assert ok, "Failed to navigate to Domain Management."

        # Remove each device from LW server 
        domain_management = DomainManagement(page)
        for ip in blocked_devices:
            domain_management.remove_device(ip)
          
        refresh_page(page)

        # Configure both devices to SNMPv3 only
        for ip in blocked_devices:
            set_device_v3_only(ip)

        # Run SNMPv2 discovery in RANGE mode 
        open_device_discovery(left_panel)
        device_discovery.click_SNMPv2()
        device_discovery.click_start_discovery_for_ip_range()
        device_discovery.set_range_start_ip(DEVICE_IP1)
        device_discovery.set_range_end_ip(DEVICE_IP2)

        device_discovery.set_SNMPv2_read_community(READ_COMMUNITY)
        device_discovery.set_SNMPv2_write_community(WRITE_COMMUNITY)
        device_discovery.set_SNMPv2_admin_community(ADMIN_COMMUNITY)
        device_discovery.set_SNMPv2_contact_port(CONTACT_PORT)

        device_discovery.click_start_discovery()

        countdown_sleep(WAIT, message="Wait for the discovery process to complete")
        refresh_page(page)

        # Verify blocked devices NOT added to LW Navigation Info
        ok = left_panel.click_management_map()
        assert ok, "Failed to navigate to Management Map."

        management_map.show_navigation_info()

        found_in_nav = []
        for ip in blocked_devices:
            if management_map.is_element_exist_on_navigation_info_list(ip):
                found_in_nav.append(ip)

        if found_in_nav:
            raise AssertionError(f"Blocked devices were found in Navigation Info but should NOT be discovered via SNMPv2: {found_in_nav}")
        
        # Remove LW server trap again from both blocked devices
        for ip in blocked_devices:
            delete_lw_trap_from_device(ip)

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

        test_discovery_for_ip_range_snmpv2(page, left_panel, logger, report)

        context.close()
        browser.close()
        close_report(report)

    end_time = time.perf_counter()
    print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
    logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")