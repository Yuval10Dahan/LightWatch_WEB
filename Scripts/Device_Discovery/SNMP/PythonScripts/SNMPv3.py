"""
Created by: Yuval Dahan
Date: 26/02/2026

Comprehensive SNMPv3 Test
=====================================================
Tests the SNMPv3 tab inside Device Discovery.


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

    DEVICE_IP_1 = "172.16.30.15"
    DEVICE_IP_2 = "172.16.20.113"
    DEVICE_IP_3 = "172.16.40.21"
    DEVICE_IP_4 = "172.16.20.111"

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

LOGGER_ROOT_DIRECTORY = r'G:\\Python\\PacketLight Automation\\LightWatch_WEB\\Scripts\\Device_Discovery\\SNMP\\LogFiles'
LOGGER_DIRECTORY_NAME = "SNMPv3"
LOG_FILE_NAME = 'SNMPv3.log'
REPORT_PATH = None

def run_step(step_num, step_function, logger, report) -> bool:
    try:
        step_function()
        print(f"Step {step_num} – Pass ✅")
        logger.info(f"Step {step_num} – Pass.")
        if report: step_passed(report, f"Step {step_num} – Pass.")
        return True
    except Exception as e:
        print(f"Step {step_num} – Fail ❌  Error: {e}")
        logger.info(f"Step {step_num} – Fail.")
        logger.info(f"Step {step_num} Error: {e}")
        if report: step_failed(report, f"Step {step_num} – Fail.")
        return False

def open_device_discovery(left_panel: LeftPanel):
    try:
        ok = left_panel.click_device_discovery()
    except Exception as e:
        raise AssertionError(f"Failed to call left_panel.click_device_discovery(). Error: {e}")
    if not ok:
        raise AssertionError("left_panel.click_device_discovery() returned False.")

def test_snmpv3_device_discovery(page, left_panel: LeftPanel, logger, report):
    device_discovery  = DeviceDiscovery(page)
    management_map  = ManagementMap(page)
    domain_management = DomainManagement(page)
    login  = LoginPage(page)

    results = {}
    stored_defaults = {}

    ###################################################
    # Step 1 – Facrory default reset for all devices. #
    # Open Device Discovery.                          #
    ###################################################
    def step_1():
        ips_to_reset = [DEVICE_IP_1, DEVICE_IP_2, DEVICE_IP_3, DEVICE_IP_4]
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

    results[1] = run_step(1, step_1, logger, report)

    #################################################
    # Step 2 – Make sure that default values exist. #
    # Store those values.                           #
    #################################################
    def step_2():
        device_discovery.click_SNMPv3()

        device_discovery.set_SNMPv3_user_name(SNMPv3_DEFAULT_VALUES["userName"]) 
        device_discovery.set_SNMPv3_security_level(SNMPv3_DEFAULT_VALUES["securityLevel"])
        device_discovery.set_SNMPv3_contact_port(SNMPv3_DEFAULT_VALUES["contactPort"])
        device_discovery.click_save_as_default()
        device_discovery.confirm_default_override()
        refresh_page(5)

        stored_defaults["userName"]  = device_discovery.get_SNMPv3_user_name()
        stored_defaults["securityLevel"] = device_discovery.get_SNMPv3_security_level()
        stored_defaults["contactPort"] = device_discovery.get_SNMPv3_contact_port()

    results[2] = run_step(2, step_2, logger, report)

    ###################################
    # Step 3 – Fill new SNMPv3 values #
    ###################################
    def step_3():
        device_discovery.set_ip_address(DEVICE_IP_1)
        device_discovery.set_SNMPv3_user_name("Barca")
        device_discovery.set_SNMPv3_security_level(AUTH_NO_PRIV)
        device_discovery.set_SNMPv3_authentication_protocol("SHA-1")
        device_discovery.set_SNMPv3_authentication_password("1")
        device_discovery.set_SNMPv3_contact_port(TEST_CONTACT_PORT)

        got_ip = device_discovery.get_ip_address()
        got_user = device_discovery.get_SNMPv3_user_name()
        got_sec = device_discovery.get_SNMPv3_security_level()
        got_auth_proto = device_discovery.get_SNMPv3_authentication_protocol()
        got_auth_pass = device_discovery.get_SNMPv3_authentication_password()
        got_port = int(device_discovery.get_SNMPv3_contact_port())

        if got_ip != DEVICE_IP_1 or got_user != "Barca" or got_sec != AUTH_NO_PRIV or \
           got_auth_proto != "SHA-1" or got_auth_pass != "1" or got_port != 1:
            raise AssertionError("Setting new values failed in step 3.")
            
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

        if got_user != stored_defaults.get("userName") or \
           got_sec != stored_defaults.get("securityLevel") or \
           got_port != stored_defaults.get("contactPort"):
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

        if got_user != "Barca" or got_sec != AUTH_NO_PRIV or \
           got_auth_proto != "SHA-1" or got_auth_pass != TEST_AUTHENTICATION_PASSWORD or got_port != TEST_CONTACT_PORT:
            raise AssertionError("Saved defaults did not persist after logout/login.")
            
    results[5] = run_step(5, step_5, logger, report)

    ##################################################################
    # Step 6 – Add the LW server to the DEVICE_IP_1 SNMP Traps table #
    # Start discovery with No Authentication and No Privacy          #
    ##################################################################
    def step_6():
        refresh_page(page)
        device_page = page.context.new_page()

        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(DEVICE_IP_1)
            ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            assert ok, f"Login to {DEVICE_IP_1} GUI failed."

            pl_SNMP = PL_SNMPPage(device_page)
            ok_tab = pl_SNMP.open_SNMP_tab()
            assert ok_tab, f"Failed to open SNMP tab on {DEVICE_IP_1}."

            success, _ = pl_SNMP.Add_Trap_Manager(IP=LW_SERVER_HOST_IP.split(":")[0], SNMP_Version="SNMP v3")
            assert success, (f"Server IP ({LW_SERVER_HOST_IP.split(':')[0]}) was not added")
            refresh_page(page)

        finally:
            device_page.close()


        open_device_discovery(left_panel)
        device_discovery.click_SNMPv3()

        device_discovery.set_ip_address(DEVICE_IP_1)
        device_discovery.set_SNMPv3_user_name("admin")
        device_discovery.set_SNMPv3_security_level(NO_AUTH_NO_PRIV)
        device_discovery.set_SNMPv3_contact_port(CONTACT_PORT)
        
        device_discovery.click_start_discovery()
        countdown_sleep(WAIT, message="Wait for the discovery process to complete")
        refresh_page(page)

    results[6] = run_step(6, step_6, logger, report)

    #################################
    # Step 7 – Check Management Map #
    #################################
    def step_7():
        ok = left_panel.click_management_map()
        assert ok, "Failed to navigate to Management Map."

        management_map.show_navigation_info()
        in_nav = management_map.is_element_exist_on_navigation_info_list(DEVICE_IP_1)
        assert in_nav, f"{DEVICE_IP_1} was not found in the Navigation Info list."
        management_map.navigation_info_open_element_details(DEVICE_IP_1)

    results[7] = run_step(7, step_7, logger, report)

    #############################################
    # Step 8 – Verify LW is still in SNMP Traps #
    #############################################
    def step_8():
        refresh_page(page)
        device_page = page.context.new_page()
        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{DEVICE_IP_1}/")
            ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            assert ok, f"Login to {DEVICE_IP_1} GUI failed."

            pl_SNMP = PL_SNMPPage(device_page)
            ok_tab = pl_SNMP.open_SNMP_tab()
            assert ok_tab, f"Failed to open SNMP tab on {DEVICE_IP_1}."

            found = pl_SNMP.manager_address_added_to_SNMP_traps(LW_SERVER_HOST_IP.split(":")[0])
            assert found, f"Server IP ({LW_SERVER_HOST_IP.split(':')[0]}) was NOT found in SNMP Traps."
        finally:
            device_page.close()

    results[8] = run_step(8, step_8, logger, report)

    ####################################
    # Step 9 – Check SNMPv3 parameters #
    ####################################
    def step_9():
        refresh_page(page)
        device_page = page.context.new_page()
        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{DEVICE_IP_1}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)

            pl_security = PL_SecurityPage(device_page)
            pl_security.open_security_tab()
            pl_security.click_on_users()
            table = pl_security.get_users_table()
            
            params = pl_security.return_user_parameters("admin", table)
            if params is None or len(params) == 0:
                 raise AssertionError("No parameters found for user 'admin'")
            
            row_str = " ".join([str(x) for x in params])
            assert "admin" in row_str, "User Name admin not found in params."
            assert "Administrator" in row_str, "Permission Administrator not found in params."
            assert "No Auth" in row_str, "SNMPv3 Auth 'No Auth' not found in params."
            assert "No Priv" in row_str, "SNMPv3 Priv 'No Priv' not found in params."
        finally:
            device_page.close()

    results[9] = run_step(9, step_9, logger, report)

    ##########################
    # Step 10 – Add new user #
    ##########################
    def step_10():
        device_page = page.context.new_page()
        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{DEVICE_IP_1}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)

            pl_sec = PL_SecurityPage(device_page)
            pl_sec.open_security_tab()
            pl_sec.click_on_users()

            ok = pl_sec.add_new_user(user_name="Yuval", permission="Administrator",
                password=NEW_USER_PASSWORD, verify_password=NEW_USER_PASSWORD,
                snmpv3_auth="SHA1", snmpv3_priv="No Priv")
            
            assert ok, "Failed to add new user Yuval."
        finally:
            device_page.close()

    results[10] = run_step(10, step_10, logger, report)

    #############################################################
    # Step 11 – Discovery with Auth, No Priv using the new user #
    #############################################################
    def step_11():
        refresh_page(page)
        device_page = page.context.new_page()

        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(DEVICE_IP_2)
            ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            assert ok, f"Login to {DEVICE_IP_2} GUI failed."

            pl_SNMP = PL_SNMPPage(device_page)
            ok_tab = pl_SNMP.open_SNMP_tab()
            assert ok_tab, f"Failed to open SNMP tab on {DEVICE_IP_2}."

            success, _ = pl_SNMP.Add_Trap_Manager(IP=LW_SERVER_HOST_IP.split(":")[0], SNMP_Version="SNMP v3")
            assert success, (f"Server IP ({LW_SERVER_HOST_IP.split(':')[0]}) was not added")
            refresh_page(page)

        finally:
            device_page.close()


        open_device_discovery(left_panel)
        device_discovery.click_SNMPv3()

        device_discovery.set_ip_address(DEVICE_IP_2)
        device_discovery.set_SNMPv3_user_name("Yuval")
        device_discovery.set_SNMPv3_security_level(AUTH_NO_PRIV)
        device_discovery.set_SNMPv3_authentication_protocol("SHA-1")
        device_discovery.set_SNMPv3_authentication_password(AUTHENTICATION_PASSWORD)
        device_discovery.set_SNMPv3_contact_port(CONTACT_PORT)
        
        device_discovery.click_start_discovery()
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
        in_nav = management_map.is_element_exist_on_navigation_info_list(DEVICE_IP_2)
        assert in_nav, f"{DEVICE_IP_2} was not found in the Navigation Info list."
        management_map.navigation_info_open_element_details(DEVICE_IP_2)

    results[12] = run_step(12, step_12, logger, report)

    #############################################
    # Step 13 – Verify LW is stillin SNMP Traps #
    #############################################
    def step_13():
        refresh_page(page)
        device_page = page.context.new_page()
        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{DEVICE_IP_2}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)

            pl_SNMP = PL_SNMPPage(device_page)
            pl_SNMP.open_SNMP_tab()

            found = pl_SNMP.manager_address_added_to_SNMP_traps(LW_SERVER_HOST_IP.split(":")[0])
            assert found, f"Server IP not found in SNMP Traps of {DEVICE_IP_2}."
        finally:
            device_page.close()

    results[13] = run_step(13, step_13, logger, report)

    #####################################
    # Step 14 – Check SNMPv3 parameters #
    #####################################
    def step_14():
        refresh_page(page)
        device_page = page.context.new_page()
        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{DEVICE_IP_2}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)

            pl_sec = PL_SecurityPage(device_page)
            pl_sec.open_security_tab()
            pl_sec.click_on_users()
            table = pl_sec.get_users_table()
            
            params = pl_sec.return_user_parameters("Yuval", table)
            if params is None or len(params) == 0:
                 raise AssertionError("No parameters found for user 'Yuval'")
            
            row_str = " ".join([str(x) for x in params])
            assert "Yuval" in row_str, "User Name Yuval not found in params."
            assert "Administrator" in row_str, "Permission Administrator not found in params."
            assert "SHA1" in row_str, "SNMPv3 Auth 'SHA1' not found in params."
            assert "No Priv" in row_str, "SNMPv3 Priv 'No Priv' not found in params."
        finally:
            device_page.close()

    results[14] = run_step(14, step_14, logger, report)

    ##################################
    # Step 15 – Add new user 'Alpha' #
    ##################################
    def step_15():
        device_page = page.context.new_page()
        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{DEVICE_IP_3}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)

            pl_sec = PL_SecurityPage(device_page)
            pl_sec.open_security_tab()
            pl_sec.click_on_users()

            ok = pl_sec.add_new_user(user_name="Alpha", permission="Administrator",
                password=NEW_USER_PASSWORD, verify_password=NEW_USER_PASSWORD,
                snmpv3_auth="SHA1", snmpv3_priv="AES-128")
            
            assert ok, "Failed to add new user Alpha."
        finally:
            device_page.close()

    results[15] = run_step(15, step_15, logger, report)

    ###################################################
    # Step 16 – Discovery with Auth, Priv using Alpha #
    ###################################################
    def step_16():
        refresh_page(page)
        device_page = page.context.new_page()

        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(DEVICE_IP_3)
            ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            assert ok, f"Login to {DEVICE_IP_3} GUI failed."

            pl_SNMP = PL_SNMPPage(device_page)
            ok_tab = pl_SNMP.open_SNMP_tab()
            assert ok_tab, f"Failed to open SNMP tab on {DEVICE_IP_3}."

            success, _ = pl_SNMP.Add_Trap_Manager(IP=LW_SERVER_HOST_IP.split(":")[0], SNMP_Version="SNMP v3")
            assert success, (f"Server IP ({LW_SERVER_HOST_IP.split(':')[0]}) was not added")
            refresh_page(page)

        finally:
            device_page.close()


        open_device_discovery(left_panel)
        device_discovery.click_SNMPv3()

        device_discovery.set_ip_address(DEVICE_IP_3)
        device_discovery.set_SNMPv3_user_name("Alpha")
        device_discovery.set_SNMPv3_security_level(AUTH_PRIV) 
        device_discovery.set_SNMPv3_authentication_protocol("SHA-1")
        device_discovery.set_SNMPv3_authentication_password(AUTHENTICATION_PASSWORD)
        device_discovery.set_SNMPv3_privacy_protocol("AES-128")
        device_discovery.set_SNMPv3_privacy_password(PRIVACY_PASSWORD)
        device_discovery.set_SNMPv3_contact_port(CONTACT_PORT)
        
        device_discovery.click_start_discovery()
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
        in_nav = management_map.is_element_exist_on_navigation_info_list(DEVICE_IP_3)
        assert in_nav, f"{DEVICE_IP_3} was not found in the Navigation Info list."
        management_map.navigation_info_open_element_details(DEVICE_IP_3)

    results[17] = run_step(17, step_17, logger, report)

    ##############################################
    # Step 18 – Verify LW is still in SNMP Traps #
    ##############################################
    def step_18():
        refresh_page(page)
        device_page = page.context.new_page()
        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{DEVICE_IP_3}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)

            pl_SNMP = PL_SNMPPage(device_page)
            pl_SNMP.open_SNMP_tab()

            found = pl_SNMP.manager_address_added_to_SNMP_traps(LW_SERVER_HOST_IP.split(":")[0])
            assert found, f"Server IP not found in SNMP Traps of {DEVICE_IP_3}."
        finally:
            device_page.close()

    results[18] = run_step(18, step_18, logger, report)

    #####################################
    # Step 19 – Check SNMPv3 parameters #
    #####################################
    def step_19():
        refresh_page(page)
        device_page = page.context.new_page()
        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{DEVICE_IP_3}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)

            pl_sec = PL_SecurityPage(device_page)
            pl_sec.open_security_tab()
            pl_sec.click_on_users()
            table = pl_sec.get_users_table()
            
            params = pl_sec.return_user_parameters("Alpha", table)
            if params is None or len(params) == 0:
                 raise AssertionError("No parameters found for user 'Alpha'")
            
            row_str = " ".join([str(x) for x in params])
            assert "Alpha" in row_str, "User Name Alpha not found in params."
            assert "Administrator" in row_str, "Permission Administrator not found in params."
            assert "SHA1" in row_str, "SNMPv3 Auth 'SHA1' not found in params."
            assert "AES-128" in row_str, "SNMPv3 Priv 'AES-128' not found in params."
        finally:
            device_page.close()

    results[19] = run_step(19, step_19, logger, report)

    ##########################################################
    # Step 20 – Remove devices from LW via Domain Management #
    ##########################################################
    def step_20():
        ips_to_remove = [DEVICE_IP_1, DEVICE_IP_2, DEVICE_IP_3, DEVICE_IP_4]
        for ip in ips_to_remove:
            domain_management.remove_device(ip)
            sleep(5)

    results[20] = run_step(20, step_20, logger, report)

    ###############################################
    # Step 21 – Apply factory defaults to devices #
    ###############################################
    def step_21():

        ips_to_reset = [DEVICE_IP_1, DEVICE_IP_2, DEVICE_IP_3, DEVICE_IP_4]
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

    results[21] = run_step(21, step_21, logger, report)

    ##################################################
    # Step 22 – Combinatorics of Auth/Priv Protocols #
    ##################################################
    
    def do_combo_test(target_ip, auth_proto, priv_proto):
        print(f"Authentication Protocol - {auth_proto}, Privacy Protocol - {priv_proto} combination:")

        # Add new user
        device_page = page.context.new_page()
        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{target_ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)

            pl_sec = PL_SecurityPage(device_page)
            pl_sec.open_security_tab()
            pl_sec.click_on_users()

            ok = pl_sec.add_new_user(user_name="Alpha", permission="Administrator",
                password=NEW_USER_PASSWORD, verify_password=NEW_USER_PASSWORD,
                snmpv3_auth=auth_proto.replace('-', ''), # e.g. SHA-256 -> SHA256 in GUI sometimes? Just passing as is.
                snmpv3_priv=priv_proto
            )
            assert ok, f"Failed to add new user Alpha on {target_ip} with {auth_proto}/{priv_proto}"
        finally:
            device_page.close()

        # Discovery
        refresh_page(page)
        device_page = page.context.new_page()

        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(target_ip)
            ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            assert ok, f"Login to {target_ip} GUI failed."

            pl_SNMP = PL_SNMPPage(device_page)
            ok_tab = pl_SNMP.open_SNMP_tab()
            assert ok_tab, f"Failed to open SNMP tab on {target_ip}."

            success, _ = pl_SNMP.Add_Trap_Manager(IP=LW_SERVER_HOST_IP.split(":")[0], SNMP_Version="SNMP v3")
            assert success, (f"Server IP ({LW_SERVER_HOST_IP.split(':')[0]}) was not added")
            refresh_page(page)

        finally:
            device_page.close()


        open_device_discovery(left_panel)
        device_discovery.click_SNMPv3()

        device_discovery.set_ip_address(target_ip)
        device_discovery.set_SNMPv3_user_name("Alpha")
        device_discovery.set_SNMPv3_security_level(AUTH_PRIV)
        device_discovery.set_SNMPv3_authentication_protocol(auth_proto)
        device_discovery.set_SNMPv3_authentication_password(AUTHENTICATION_PASSWORD)
        device_discovery.set_SNMPv3_privacy_protocol(priv_proto)
        device_discovery.set_SNMPv3_privacy_password(PRIVACY_PASSWORD)
        device_discovery.set_SNMPv3_contact_port(CONTACT_PORT)
        
        device_discovery.click_start_discovery()
        countdown_sleep(WAIT, message=f"Wait for discovery of {target_ip}")
        refresh_page(page)

        # Map verify
        ok_map = left_panel.click_management_map()
        assert ok_map, "Failed to navigate to Management Map."
        management_map.show_navigation_info()
        in_nav = management_map.is_element_exist_on_navigation_info_list(target_ip)
        assert in_nav, f"{target_ip} not found in Nav Info."

        # Traps verify
        refresh_page(page)
        device_page2 = page.context.new_page()
        try:
            pl_login = PL_LoginPage(device_page2)
            pl_login.goto(f"http://{target_ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)

            pl_SNMP = PL_SNMPPage(device_page2)
            pl_SNMP.open_SNMP_tab()
            found = pl_SNMP.manager_address_added_to_SNMP_traps(LW_SERVER_HOST_IP.split(":")[0])
            assert found, f"Trap not found for {target_ip}"
        finally:
            device_page2.close()
            
        # Params verify
        refresh_page(page)
        device_page3 = page.context.new_page()
        try:
            pl_login = PL_LoginPage(device_page3)
            pl_login.goto(f"http://{target_ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)

            pl_sec = PL_SecurityPage(device_page3)
            pl_sec.open_security_tab()
            pl_sec.click_on_users()
            table = pl_sec.get_users_table()
            
            params = pl_sec.return_user_parameters("Alpha", table)
            row_str = " ".join([str(x) for x in params])
            assert "Alpha" in row_str, "User Name Alpha not found in params."
            assert "Administrator" in row_str, "Permission Administrator not found in params."
            assert auth_proto in row_str, f"SNMPv3 Auth {auth_proto} not found in params."
            assert priv_proto in row_str, f"SNMPv3 Priv {priv_proto} not found in params."
        finally:
            device_page3.close()

    def step_22():
        auths = ["SHA-1", "SHA-256", "SHA-384", "SHA-512"]
        privs = ["AES-128", "AES-192", "AES-256"]
        combinations = [(a, p) for a in auths for p in privs if not (a == "SHA-1" and p == "AES-128")]
        ips = [DEVICE_IP_1, DEVICE_IP_2, DEVICE_IP_3, DEVICE_IP_4]

        # reps 1-4
        for i in range(4):
            if i < len(combinations):
                do_combo_test(ips[i], combinations[i][0], combinations[i][1])
        step_20() # remove devices from LW
        step_21() # reset devices

        # reps 5-8
        for i in range(4, 8):
            if i < len(combinations):
                do_combo_test(ips[i-4], combinations[i][0], combinations[i][1])
        step_20() # remove devices from LW
        step_21() # reset devices

        # reps 9-11
        for i in range(8, len(combinations)):
            do_combo_test(ips[i-8], combinations[i][0], combinations[i][1])

    results[22] = run_step(22, step_22, logger, report)

    #############################################################
    # Step 23 – Invalid IP Checks
    #############################################################
    def step_23():
        refresh_page(page)
        open_device_discovery(left_panel)
        device_discovery.click_SNMPv3()

        invalid_ips = ["a.1.1.1", "10.@.10.10", "10.10.&.10", "10.10.10.?"]
        
        failed = []
        for bad_ip in invalid_ips:
            device_discovery.set_ip_address(bad_ip)
            is_valid = device_discovery.is_ip_address_field_valid()
            if is_valid:
                failed.append(bad_ip)

        if failed:
            raise AssertionError(f"Expected to be INVALID but were valid: {failed}")

    results[23] = run_step(23, step_23, logger, report)


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

        test_snmpv3_device_discovery(page, left_panel, logger, report)

        context.close()
        browser.close()
        close_report(report)

    end_time = time.perf_counter()
    print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
    logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")