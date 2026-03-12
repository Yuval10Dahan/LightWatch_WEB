"""
Created by: Yuval Dahan
Date: 04/03/2026

=====================================================
Tests the Start Discovery for IP Range for SNMPv3.

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
from PL_Devices.PL_Pages.PL_security_page import PL_SecurityPage
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
    globals().update(const_dict)
elif 2 < len(argv) < 3:
    directory = argv[1] + ' ' + argv[2]
    const_dict = eval(open(directory, 'r').read())
    globals().update(const_dict)
else:
    LW_SERVER_HOST_IP  = "172.16.10.22:8080"
    LW_USERNAME = "administrator"
    LW_PASSWORD = "administrator"

    DEVICE_IP_USER = "tech"
    DEVICE_IP_PASS = "packetlight"

    # Range devices
    DEVICE_IP_1 = "172.16.30.123"
    DEVICE_IP_2 = "172.16.30.124"

    AUTHENTICATION_PASSWORD = "Z@qqaz$$2"
    PRIVACY_PASSWORD = "Z@qqaz$$2"

CONTACT_PORT = 161
NEW_USER_PASSWORD = "Z@qqaz$$2"

TEST_AUTHENTICATION_PASSWORD = "1"
TEST_PRIVATE_PASSWORD = "1"
TEST_CONTACT_PORT = 1

NO_AUTH_NO_PRIV = "No Authentication, No Privacy"
AUTH_NO_PRIV = "Authentication, No Privacy"
AUTH_PRIV = "Authentication, Privacy"

SNMPv3_DEFAULT_VALUES = {
    "userName": "admin",
    "securityLevel": "No Authentication, No Privacy",
    "contactPort": 161
}

BASE_URL = f"http://{LW_SERVER_HOST_IP}/"
WAIT = 30

LOGGER_ROOT_DIRECTORY = r'G:\Python\PacketLight Automation\LightWatch_WEB\Scripts\Device_Discovery\SNMP\LogFiles'
LOGGER_DIRECTORY_NAME = "discovery_for_ip_range_SNMPv3"
LOG_FILE_NAME = 'discovery_for_ip_range_SNMPv3.log'
REPORT_PATH = None

RANGE_DEVICES = [DEVICE_IP_1, DEVICE_IP_2]


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
        if report:
            step_passed(report, f"Step {step_num} – Pass.")
        return True
    except Exception as e:
        print(f"Step {step_num} – Fail ❌  Error: {e}")
        logger.info(f"Step {step_num} – Fail.")
        logger.info(f"Step {step_num} Error: {e}")
        if report:
            step_failed(report, f"Step {step_num} – Fail.")
        return False

def open_device_discovery(left_panel: LeftPanel):
    """Open Device Discovery via LeftPanel and assert it opened."""
    try:
        ok = left_panel.click_device_discovery()
    except Exception as e:
        raise AssertionError(f"Failed to call left_panel.click_device_discovery(). Error: {e}")

    if ok is not True:
        raise AssertionError(
            "left_panel.click_device_discovery() returned False "
            "(Device Discovery did not open)."
        )

def add_lw_trap_snmpv3(page, device_ip: str):
    """
    Add LW server as SNMPv3 trap manager on a device.
    """
    server_ip = LW_SERVER_HOST_IP.split(":")[0]
    device_page = page.context.new_page()
    try:
        pl_login = PL_LoginPage(device_page)
        pl_login.goto(f"http://{device_ip}/")
        ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
        assert ok, f"Login to {device_ip} GUI failed."

        pl_snmp = PL_SNMPPage(device_page)
        ok_tab = pl_snmp.open_SNMP_tab()
        assert ok_tab, f"Failed to open SNMP tab on {device_ip}."

        success, _ = pl_snmp.Add_Trap_Manager(IP=server_ip, SNMP_Version="SNMP v3")
        assert success, f"Server IP ({server_ip}) was not added to SNMPv3 Traps table on {device_ip}."
        refresh_page(device_page)
    finally:
        device_page.close()

def verify_lw_trap_exists_snmpv3(page, device_ip: str):
    """
    Verify LW server is in SNMP traps on a device.
    """
    server_ip = LW_SERVER_HOST_IP.split(":")[0]
    device_page = page.context.new_page()
    try:
        pl_login = PL_LoginPage(device_page)
        pl_login.goto(f"http://{device_ip}/")
        ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
        assert ok, f"Login to {device_ip} GUI failed."

        pl_snmp = PL_SNMPPage(device_page)
        ok_tab = pl_snmp.open_SNMP_tab()
        assert ok_tab, f"Failed to open SNMP tab on {device_ip}."

        found = pl_snmp.manager_address_added_to_SNMP_traps(server_ip)
        assert found, f"Server IP ({server_ip}) was NOT found in SNMP Traps table of {device_ip}."
    finally:
        device_page.close()

def add_snmpv3_user(page, device_ip: str, user_name: str, snmpv3_auth: str, snmpv3_priv: str):
    """
    Add SNMPv3 user on device.
    """
    device_page = page.context.new_page()
    try:
        pl_login = PL_LoginPage(device_page)
        pl_login.goto(f"http://{device_ip}/")
        ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
        assert ok, f"Login to {device_ip} GUI failed."

        pl_sec = PL_SecurityPage(device_page)
        pl_sec.open_security_tab()
        pl_sec.click_on_users()

        ok_add = pl_sec.add_new_user(
            user_name=user_name,
            permission="Administrator",
            password=NEW_USER_PASSWORD,
            verify_password=NEW_USER_PASSWORD,
            snmpv3_auth=snmpv3_auth,
            snmpv3_priv=snmpv3_priv
        )
        assert ok_add, f"Failed to add new user '{user_name}' on {device_ip}."
    finally:
        device_page.close()

def verify_user_parameters(page, device_ip: str, user_name: str, expected_auth_contains: str, expected_priv_contains: str):
    """
    Verify auth/priv parameters for a given user in device Users table.
    """
    device_page = page.context.new_page()

    try:
        pl_login = PL_LoginPage(device_page)
        pl_login.goto(f"http://{device_ip}/")
        ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
        assert ok, f"Login to {device_ip} GUI failed."

        pl_sec = PL_SecurityPage(device_page)
        pl_sec.open_security_tab()
        pl_sec.click_on_users()
        table = pl_sec.get_users_table()

        params = pl_sec.return_user_parameters(user_name, table)
        if params is None or len(params) == 0:
            raise AssertionError(f"No parameters found for user '{user_name}' on {device_ip}.")

        row_str = " ".join([str(x) for x in params])
        assert user_name in row_str, f"User Name {user_name} not found in params."
        assert "Administrator" in row_str, "Permission Administrator not found in params."
        if expected_auth_contains:
            assert expected_auth_contains in row_str, f"SNMPv3 Auth '{expected_auth_contains}' not found in params."
        if expected_priv_contains:
            assert expected_priv_contains in row_str, f"SNMPv3 Priv '{expected_priv_contains}' not found in params."
    
    finally:
        device_page.close()

def run_snmpv3_range_discovery(device_discovery: DeviceDiscovery, start_ip: str, end_ip: str,
                              user_name: str, security_level: str,
                              auth_protocol: str = None, auth_password: str = None,
                              priv_protocol: str = None, priv_password: str = None,
                              contact_port: int = CONTACT_PORT):
    """
    Start discovery in RANGE mode using SNMPv3 fields.
    """
    device_discovery.click_SNMPv3()
    device_discovery.click_start_discovery_for_ip_range()

    device_discovery.set_range_start_ip(start_ip)
    device_discovery.set_range_end_ip(end_ip)

    device_discovery.set_SNMPv3_user_name(user_name)
    device_discovery.set_SNMPv3_security_level(security_level)

    if auth_protocol is not None:
        device_discovery.set_SNMPv3_authentication_protocol(auth_protocol)
    if auth_password is not None:
        device_discovery.set_SNMPv3_authentication_password(auth_password)

    if priv_protocol is not None:
        device_discovery.set_SNMPv3_privacy_protocol(priv_protocol)
    if priv_password is not None:
        device_discovery.set_SNMPv3_privacy_password(priv_password)

    device_discovery.set_SNMPv3_contact_port(contact_port)

    device_discovery.click_start_discovery()


# ================================================================
# Main test
# ================================================================

def test_discovery_for_ip_range_snmpv3(page, left_panel: LeftPanel, logger, report):
    device_discovery = DeviceDiscovery(page)
    management_map = ManagementMap(page)
    domain_management = DomainManagement(page)
    login = LoginPage(page)

    results = {}
    stored_defaults = {}

    ###################################################
    # Step 1 – Factory default reset for all devices. #
    # Open Device Discovery.                          #
    ###################################################
    def step_1():
        ips_to_reset = [DEVICE_IP_1, DEVICE_IP_2]
        for ip in ips_to_reset:
            device_page = page.context.new_page()
            try:
                pl_login = PL_LoginPage(device_page)
                pl_login.goto(f"http://{ip}/")
                pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
                sleep(1)

                pl_main = PL_Main_Screen_POM(device_page)
                pl_main.device_restart("factory")
                sleep(5)
            finally:
                device_page.close()

        devices_are_up(ips_to_reset, wait_time=WAIT)

        open_device_discovery(left_panel)
        assert device_discovery.container().is_visible(), "Device Discovery container is not visible."
        device_discovery.click_SNMPv3()

    results[1] = run_step(1, step_1, logger, report)

    #################################################
    # Step 2 – Make sure that default values exist. #
    # Store those values.                           #
    #################################################
    def step_2():
        device_discovery.click_SNMPv3()

        # Force-save factory defaults (like SNMPv3.py does)
        device_discovery.set_SNMPv3_user_name(SNMPv3_DEFAULT_VALUES["userName"])
        device_discovery.set_SNMPv3_security_level(SNMPv3_DEFAULT_VALUES["securityLevel"])
        device_discovery.set_SNMPv3_contact_port(SNMPv3_DEFAULT_VALUES["contactPort"])
        device_discovery.click_save_as_default()
        device_discovery.confirm_default_override()
        refresh_page(5)

        stored_defaults["userName"] = device_discovery.get_SNMPv3_user_name()
        stored_defaults["securityLevel"] = device_discovery.get_SNMPv3_security_level()
        stored_defaults["contactPort"] = device_discovery.get_SNMPv3_contact_port()

    results[2] = run_step(2, step_2, logger, report)

    ###################################
    # Step 3 – Fill new SNMPv3 values #
    ###################################
    def step_3():
        device_discovery.click_SNMPv3()
        device_discovery.click_start_discovery_for_ip_range()

        device_discovery.set_range_start_ip(DEVICE_IP_1)
        device_discovery.set_range_end_ip(DEVICE_IP_2)

        device_discovery.set_SNMPv3_user_name("Barca")
        device_discovery.set_SNMPv3_security_level(AUTH_NO_PRIV)
        device_discovery.set_SNMPv3_authentication_protocol("SHA-1")
        device_discovery.set_SNMPv3_authentication_password("1")
        device_discovery.set_SNMPv3_contact_port(TEST_CONTACT_PORT)

        got_start = device_discovery.get_range_start_ip()
        got_end = device_discovery.get_range_end_ip()

        got_user = device_discovery.get_SNMPv3_user_name()
        got_sec = device_discovery.get_SNMPv3_security_level()
        got_auth_proto = device_discovery.get_SNMPv3_authentication_protocol()
        got_auth_pass = device_discovery.get_SNMPv3_authentication_password()
        got_port = int(device_discovery.get_SNMPv3_contact_port())

        if got_start != DEVICE_IP_1 or got_end != DEVICE_IP_2:
            raise AssertionError("Setting Range Start/End IP failed in step 3.")

        if got_user != "Barca" or got_sec != AUTH_NO_PRIV or got_auth_proto != "SHA-1" or got_auth_pass != "1" or got_port != 1:
            raise AssertionError("Setting new SNMPv3 values failed in step 3.")

    results[3] = run_step(3, step_3, logger, report)

    ############################################################
    # Step 4 – Click 'Reset to Default' and verify restoration #
    ############################################################
    def step_4():
        device_discovery.click_reset_to_default()
        refresh_page(page)
        device_discovery.click_SNMPv3()

        got_user = device_discovery.get_SNMPv3_user_name()
        got_sec = device_discovery.get_SNMPv3_security_level()
        got_port = device_discovery.get_SNMPv3_contact_port()

        if got_user != stored_defaults.get("userName") or got_sec != stored_defaults.get("securityLevel") or got_port != stored_defaults.get("contactPort"):
            raise AssertionError("Reset to Default did not restore all SNMPv3 values.")

    results[4] = run_step(4, step_4, logger, report)

    ####################################################################
    # Step 5 – Fill new values, Save as Default and verify persistence #
    ####################################################################
    def step_5():
        refresh_page(page)
        open_device_discovery(left_panel)
        device_discovery.click_SNMPv3()

        device_discovery.set_SNMPv3_user_name("Barca")
        device_discovery.set_SNMPv3_security_level(AUTH_NO_PRIV)
        device_discovery.set_SNMPv3_authentication_protocol("SHA-1")
        device_discovery.set_SNMPv3_authentication_password(TEST_AUTHENTICATION_PASSWORD)
        device_discovery.set_SNMPv3_contact_port(TEST_CONTACT_PORT)

        device_discovery.click_save_as_default()
        device_discovery.confirm_default_override()
        sleep(5)

        ok_logout = login.logout()
        assert ok_logout, "Logout failed after Save as Default."

        ok_login = login.login(LW_USERNAME, LW_PASSWORD)
        assert ok_login, "Login failed after logout (Step 5)."

        open_device_discovery(left_panel)
        device_discovery.click_SNMPv3()

        got_user = device_discovery.get_SNMPv3_user_name()
        got_sec = device_discovery.get_SNMPv3_security_level()
        got_auth_proto = device_discovery.get_SNMPv3_authentication_protocol()
        got_auth_pass = device_discovery.get_SNMPv3_authentication_password()
        got_port = int(device_discovery.get_SNMPv3_contact_port())

        if got_user != "Barca" or got_sec != AUTH_NO_PRIV or got_auth_proto != "SHA-1" or got_auth_pass != TEST_AUTHENTICATION_PASSWORD or got_port != TEST_CONTACT_PORT:
            raise AssertionError("Saved defaults did not persist after logout/login.")

    results[5] = run_step(5, step_5, logger, report)

    ##################################################################
    # Step 6 – Add the LW server to DEVICE_IP_1..DEVICE_IP_2 Traps.  #
    # Start discovery in RANGE mode with No Auth / No Priv.          #
    ##################################################################
    def step_6():
        refresh_page(page)

        for ip in [DEVICE_IP_1, DEVICE_IP_2]:
            add_lw_trap_snmpv3(page, ip)

        open_device_discovery(left_panel)

        run_snmpv3_range_discovery(device_discovery=device_discovery, start_ip=DEVICE_IP_1, end_ip=DEVICE_IP_2, user_name="admin", security_level=NO_AUTH_NO_PRIV,
            contact_port=CONTACT_PORT)

        countdown_sleep(WAIT * 2, message="Wait for the discovery process to complete")
        refresh_page(page)

    results[6] = run_step(6, step_6, logger, report)

    #############################################
    # Step 7 – Check Management Map             #
    #############################################
    def step_7():
        ok = left_panel.click_management_map()
        assert ok, "Failed to navigate to Management Map."

        management_map.show_navigation_info()

        missing = []
        for ip in [DEVICE_IP_1, DEVICE_IP_2]:
            if not management_map.is_element_exist_on_navigation_info_list(ip):
                missing.append(ip)
            else:
                management_map.navigation_info_open_element_details(ip)

        if missing:
            raise AssertionError(f"Devices not found in Navigation Info after range discovery: {missing}")

    results[7] = run_step(7, step_7, logger, report)

    ##############################################
    # Step 8 – Verify LW is still in SNMP Traps  #
    # for devices                                #
    ##############################################
    def step_8():
        for ip in [DEVICE_IP_1, DEVICE_IP_2]:
            verify_lw_trap_exists_snmpv3(page, ip)

    results[8] = run_step(8, step_8, logger, report)

    ####################################
    # Step 9 – Check SNMPv3 parameters #
    ####################################
    def step_9():
        verify_user_parameters(page=page, device_ip=DEVICE_IP_1, user_name="admin", expected_auth_contains="No Auth", expected_priv_contains="No Priv")

    results[9] = run_step(9, step_9, logger, report)

    ##########################
    # Step 10 – Add new user #
    ##########################
    def step_10():
        for ip in [DEVICE_IP_1, DEVICE_IP_2]:
            add_snmpv3_user(page=page, device_ip=ip, user_name="Yuval", snmpv3_auth="SHA1", snmpv3_priv="No Priv")

    results[10] = run_step(10, step_10, logger, report)

    #############################################################
    # Step 11 – Discovery with Auth, No Priv using the new user #
    # (RANGE mode with Start==End == DEVICE_IP_2)               #
    #############################################################
    def step_11():
        refresh_page(page)

        for ip in [DEVICE_IP_1, DEVICE_IP_2]:
            add_lw_trap_snmpv3(page, ip)

        open_device_discovery(left_panel)

        run_snmpv3_range_discovery(
            device_discovery=device_discovery,
            start_ip=DEVICE_IP_1,
            end_ip=DEVICE_IP_2,
            user_name="Yuval",
            security_level=AUTH_NO_PRIV,
            auth_protocol="SHA-1",
            auth_password=AUTHENTICATION_PASSWORD,
            contact_port=CONTACT_PORT,
        )

        countdown_sleep(WAIT, message="Wait for the discovery process")
        refresh_page(page)

    results[11] = run_step(11, step_11, logger, report)

    ##################################
    # Step 12 – Check Management Map #
    ##################################
    def step_12():
        ok = left_panel.click_management_map()
        assert ok, "Failed to navigate to Management Map."

        management_map.show_navigation_info()

        missing = []
        for ip in [DEVICE_IP_1, DEVICE_IP_2]:
            if not management_map.is_element_exist_on_navigation_info_list(ip):
                missing.append(ip)
            else:
                management_map.navigation_info_open_element_details(ip)

        if missing:
            raise AssertionError(f"Devices not found in Navigation Info after range discovery: {missing}")

    results[12] = run_step(12, step_12, logger, report)

    ##############################################
    # Step 13 – Verify LW is still in SNMP Traps #
    ##############################################
    def step_13():
        for ip in [DEVICE_IP_1, DEVICE_IP_2]:
            verify_lw_trap_exists_snmpv3(page, ip)

    results[13] = run_step(13, step_13, logger, report)

    #####################################
    # Step 14 – Check SNMPv3 parameters #
    #####################################
    def step_14():
        for ip in [DEVICE_IP_1, DEVICE_IP_2]:
            verify_user_parameters(
                page=page,
                device_ip=ip,
                user_name="Yuval",
                expected_auth_contains="SHA1",
                expected_priv_contains="No Priv",
            )

    results[14] = run_step(14, step_14, logger, report)

    ##################################
    # Step 15 – Add new user 'Alpha' #
    ##################################
    def step_15():
        for ip in [DEVICE_IP_1, DEVICE_IP_2]:
            add_snmpv3_user(
                page=page,
                device_ip=ip,
                user_name="Alpha",
                snmpv3_auth="SHA1",
                snmpv3_priv="AES-128",
            )

    results[15] = run_step(15, step_15, logger, report)

    ###################################################
    # Step 16 – Discovery with Auth, Priv             #
    ###################################################
    def step_16():
        refresh_page(page)

        for ip in [DEVICE_IP_1, DEVICE_IP_2]:
            add_lw_trap_snmpv3(page, ip)

        open_device_discovery(left_panel)

        run_snmpv3_range_discovery(
            device_discovery=device_discovery,
            start_ip=DEVICE_IP_1,
            end_ip=DEVICE_IP_2,
            user_name="Alpha",
            security_level=AUTH_PRIV,
            auth_protocol="SHA-1",
            auth_password=AUTHENTICATION_PASSWORD,
            priv_protocol="AES-128",
            priv_password=PRIVACY_PASSWORD,
            contact_port=CONTACT_PORT,
        )

        countdown_sleep(WAIT, message="Wait for discovery")
        refresh_page(page)

    results[16] = run_step(16, step_16, logger, report)

    ##################################
    # Step 17 – Check Management Map #
    ##################################
    def step_17():
        ok = left_panel.click_management_map()
        assert ok, "Failed to navigate to Management Map."

        management_map.show_navigation_info()

        for ip in [DEVICE_IP_1, DEVICE_IP_2]:
            in_nav = management_map.is_element_exist_on_navigation_info_list(ip)
            assert in_nav, f"{ip} was not found in the Navigation Info list."
            management_map.navigation_info_open_element_details(ip)

    results[17] = run_step(17, step_17, logger, report)

    ##############################################
    # Step 18 – Verify LW is still in SNMP Traps #
    ##############################################
    def step_18():
        for ip in [DEVICE_IP_1, DEVICE_IP_2]:
            verify_lw_trap_exists_snmpv3(page, ip)

    results[18] = run_step(18, step_18, logger, report)

    #####################################
    # Step 19 – Check SNMPv3 parameters #
    #####################################
    def step_19():
        for ip in [DEVICE_IP_1, DEVICE_IP_2]:
            verify_user_parameters(
                page=page,
                device_ip=ip,
                user_name="Alpha",
                expected_auth_contains="SHA1",
                expected_priv_contains="AES-128",
            )

    results[19] = run_step(19, step_19, logger, report)

    ##########################################################
    # Step 20 – Remove devices from LW via Domain Management #
    ##########################################################
    def step_20():
        ips_to_remove = [DEVICE_IP_1, DEVICE_IP_2]
        for ip in ips_to_remove:
            domain_management.remove_device(ip)
            sleep(5)

    results[20] = run_step(20, step_20, logger, report)

    ###############################################
    # Step 21 – Apply factory defaults to devices #
    ###############################################
    def step_21():
        ips_to_reset = [DEVICE_IP_1, DEVICE_IP_2]
        for ip in ips_to_reset:
            device_page = page.context.new_page()
            try:
                pl_login = PL_LoginPage(device_page)
                pl_login.goto(f"http://{ip}/")
                pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
                sleep(1)

                pl_main = PL_Main_Screen_POM(device_page)
                pl_main.device_restart("factory")
                sleep(5)
            finally:
                device_page.close()

        devices_are_up(ips_to_reset, wait_time=WAIT)

    results[21] = run_step(21, step_21, logger, report)

    ##################################################
    # Step 22 – Combinatorics of Auth/Priv Protocols #
    ##################################################

    def do_combo_test(target_ip, auth_proto, priv_proto):
        # Add user on the target device
        add_snmpv3_user(
            page=page,
            device_ip=target_ip,
            user_name="Alpha",
            snmpv3_auth=auth_proto.replace("-", ""),  # e.g. SHA-256 -> SHA256
            snmpv3_priv=priv_proto,
        )

        # Add LW trap on the target device
        add_lw_trap_snmpv3(page, target_ip)

        # Discovery (RANGE mode with Start == End)
        refresh_page(page)
        open_device_discovery(left_panel)

        run_snmpv3_range_discovery(
            device_discovery=device_discovery,
            start_ip=target_ip,
            end_ip=target_ip,
            user_name="Alpha",
            security_level=AUTH_PRIV,
            auth_protocol=auth_proto,
            auth_password=AUTHENTICATION_PASSWORD,
            priv_protocol=priv_proto,
            priv_password=PRIVACY_PASSWORD,
            contact_port=CONTACT_PORT,
        )

        countdown_sleep(WAIT, message=f"Wait for discovery of {target_ip}")
        refresh_page(page)

        # Verify device appears in Management Map
        ok_map = left_panel.click_management_map()
        assert ok_map, "Failed to navigate to Management Map."

        management_map.show_navigation_info()
        in_nav = management_map.is_element_exist_on_navigation_info_list(target_ip)
        assert in_nav, f"{target_ip} was not found in Navigation Info."

        # Verify LW trap still exists
        verify_lw_trap_exists_snmpv3(page, target_ip)

        # Verify user parameters
        verify_user_parameters(
            page=page,
            device_ip=target_ip,
            user_name="Alpha",
            expected_auth_contains=auth_proto,
            expected_priv_contains=priv_proto,
        )

    def step_22():
        auths = ["SHA-1", "SHA-256", "SHA-384", "SHA-512"]
        privs = ["AES-128", "AES-192", "AES-256"]

        # SHA-1 + AES-128 already covered in earlier steps, so skip it here
        combinations = [
            (auth_proto, priv_proto)
            for auth_proto in auths
            for priv_proto in privs
            if not (auth_proto == "SHA-1" and priv_proto == "AES-128")
        ]

        available_ips = [DEVICE_IP_1, DEVICE_IP_2]
        batch_size = len(available_ips)

        for batch_start in range(0, len(combinations), batch_size):
            batch = combinations[batch_start:batch_start + batch_size]

            for ip, (auth_proto, priv_proto) in zip(available_ips, batch):
                do_combo_test(ip, auth_proto, priv_proto)

            # Cleanup after every batch so the same 2 devices can be reused
            step_20()
            step_21()

    results[22] = run_step(22, step_22, logger, report)

    #############################################################
    # Step 23 – Invalid IP Checks (Range Start/End fields)      #
    #############################################################
    def step_23():
        refresh_page(page)
        open_device_discovery(left_panel)
        device_discovery.click_SNMPv3()
        device_discovery.click_start_discovery_for_ip_range()

        invalid_ips = ["a.1.1.1", "10.@.10.10", "10.10.&.10", "10.10.10.?"]

        failed_start = []
        failed_end = []

        for bad_ip in invalid_ips:
            device_discovery.set_range_start_ip(bad_ip)
            if device_discovery.is_range_start_ip_field_valid():
                failed_start.append(bad_ip)

            device_discovery.set_range_end_ip(bad_ip)
            if device_discovery.is_range_end_ip_field_valid():
                failed_end.append(bad_ip)

        if failed_start or failed_end:
            msg_parts = []
            if failed_start:
                msg_parts.append(f"Start IP field accepted invalid values: {failed_start}")
            if failed_end:
                msg_parts.append(f"End IP field accepted invalid values: {failed_end}")
            raise AssertionError("; ".join(msg_parts))

    results[23] = run_step(23, step_23, logger, report)

    ###################
    # Overall Results #
    ###################
    print("\n" + "=" * 60)
    all_passed = all(results.values())
    failed_steps = [str(k) for k, v in results.items() if not v]
    if all_passed:
        print("TEST PASSED ✅")
        logger.info("TEST PASSED")
    else:
        print(f"TEST FAILED ❌  Failed steps: {', '.join(failed_steps)}")
        logger.info("TEST FAILED")
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

        test_discovery_for_ip_range_snmpv3(page, left_panel, logger, report)

        context.close()
        browser.close()
        close_report(report)

    end_time = time.perf_counter()
    print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
    logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")