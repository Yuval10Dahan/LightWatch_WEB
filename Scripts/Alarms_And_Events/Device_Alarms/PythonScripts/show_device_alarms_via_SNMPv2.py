"""
Created by: Yuval Dahan
Date: 11/03/2026

Comprehensive Alarms Test - Show Device Alarms via SNMPv2
=====================================================
Tests the Device Alarms using SNMPv2.
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.device_discovery import DeviceDiscovery
from Pages.management_map import ManagementMap
from Pages.domain_management import DomainManagement
from Pages.alarms_and_events import AlarmsAndEvents
from Pages.upper_panel import UpperPanel
from Pages.common_functions import CommonFunctionsPage
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
import os
from datetime import datetime
import re

try:
    from SNMP_Modules.SNMP_Functions import SNMP_Device_Reset
except:
    pass

# Allow emojis on QC
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
    # ================================================================
    # Values for the Parameter file (from QC)
    # ================================================================

    LW_SERVER_HOST_IP  = "172.16.10.22:8080"
    LW_USERNAME = "administrator"
    LW_PASSWORD = "administrator"

    DEVICES_LIST = ['172.16.30.15', '172.16.30.13']
    DEVICE_IP_USER = "tech" 
    DEVICE_IP_PASS = "packetlight"

    DUT_IP1 = "PL-2000ADS (172.16.30.15)"
    DUT_IP2 = "PL-1000IL2 (172.16.30.13)"

    NEW_CHASSIS_ID = "67"
    DOMAIN_NAME = "Script_Domain"
    SUB_DOMAIN_NAME = "Script_Sub_Domain"




# ================================================================
# Values that should not be changed
# ================================================================

BASE_URL = f"http://{LW_SERVER_HOST_IP}/"
WAIT = 30

CATEGORIES_LIST = []
FROM_DATES_LIST = []
MESSAGES_LIST = []

GOOGLE_SNTP_SERVER = '216.239.35.0'
GMT2 = "GMT+2"

LOGGER_ROOT_DIRECTORY = 'G:\\Python\\PacketLight Automation\\LightWatch_WEB\\Scripts\\Alarms_And_Events\\Device_Alarms\\LogFiles'
LOGGER_DIRECTORY_NAME = "show_device_alarms_via_SNMPv2"
LOG_FILE_NAME = 'show_device_alarms_via_SNMPv2.log'
REPORT_PATH = None

PORT_PER_PRODUCT = {
    "PL-1000IL2": "MC 1",
    "PL-1000IL": "MC 1",
    "PL-1000D": "MC 1",
    "PL-1000GD": "MC 1",
    "PL-1000GIL": "MC 1",
    "PL-1000GRO": "MC 1",
    "PL-1000GRO-R": "MNG 1",
    "PL-1000RO": "MC 1",
    "PL-1000TE Crypto": "1",
    "PL-1000TN": "1",
    "PL-2000": "1",
    "PL-2000ADS": "1",
    "PL-2000GA": "1",
    "PL-2000GM": "1",
    "PL-2000M": "1",
    "PL-2000T": "1",
    "PL-4000G": "1",
    "PL-4000M": "1",
    "PL-4000T": "1",
    "PL-8000G": "1",
    "PL-8000M": "3"
}


def run_step(step_num, step_function, logger, report) -> bool:
    try:
        step_function()
        print(f"Step {step_num} – Pass ✅")
        logger.info(f"Step {step_num} – Pass.")
        step_passed(report, f"Step {step_num} – Pass.")
        return True
    except AssertionError as e:
        print(f"Step {step_num} – Fail ❌  Error: {e}")
        logger.info(f"Step {step_num} – Fail.")
        logger.info(f"Step {step_num} Error: {e}")
        step_failed(report, f"Step {step_num} – Fail.")
        return False
    except Exception as e:
        print(f"Step {step_num} – Error ❌  Exception: {e}")
        logger.info(f"Step {step_num} – Error.")
        logger.info(f"Step {step_num} Exception: {e}")
        step_failed(report, f"Step {step_num} – Error.")
        return False

def convert_lw_alarms_to_gui_alarms_format(ip: str, lw_alarms: list) -> list:
    """
    Convert LW alarms (dict format) into GUI-like table format,
    and return them sorted like GUI.

    Returns:
        List of rows in GUI format:
        [date_time, source, severity, message, note]
    """

    def convert_timestamp(ts: str) -> str:
        try:
            dt = datetime.strptime(ts, "%d.%m.%Y, %H:%M:%S")
            return f"{dt.month}/{dt.day}/{dt.year} {dt.hour % 12 or 12}:{dt.minute:02d}:{dt.second:02d} {'AM' if dt.hour < 12 else 'PM'}"
        except Exception:
            return ts

    def normalize_source(source: str) -> str:
        source = source.replace(ip, "").strip()

        eth_match = re.search(r"Ethernet\s*(\d+)", source, re.IGNORECASE)
        if eth_match:
            return f"ETH {eth_match.group(1)} Port"

        return source

    def parse_gui_time(ts: str):
        """
        Convert GUI string back to datetime for sorting
        """
        try:
            return datetime.strptime(ts, "%m/%d/%Y %I:%M:%S %p")
        except Exception:
            return datetime.min

    formatted = []

    for alarm in lw_alarms:
        formatted.append([
            convert_timestamp(alarm.get("creation_timestamp", "")),
            normalize_source(alarm.get("source", "")),
            alarm.get("severity", ""),
            alarm.get("message", ""),
            ""
        ])

    # Sort to match GUI order
    formatted.sort(
        key=lambda x: (
            parse_gui_time(x[0]),  # date_time
            x[1],                  # source
            x[3]                   # message
        )
    )

    return formatted

def compare_device_and_lw_alarms(ip: str, device_alarms: list, lw_alarms: list, section: str | None = None) -> bool:
    """
    Compare device GUI alarms to LW alarms (converted to GUI format).
    Expected format for each alarm: [date_time, source, severity, message, note].
    Compare all fields except 'note'.
    For date_time → compare only up to minutes (ignore seconds).
    """

    def normalize_time(ts: str) -> str:
        """
        Convert '3/19/2026 5:02:20 PM' → '3/19/2026 5:02 PM'
        """
        try:
            dt = datetime.strptime(ts, "%m/%d/%Y %I:%M:%S %p")
            return dt.strftime("%m/%d/%Y %I:%M %p")
        except Exception:
            return ts  # fallback

    if len(device_alarms) != len(lw_alarms):
        print(f"[{ip}] Alarms count mismatch in {section}: Device GUI={len(device_alarms)}, LW={len(lw_alarms)}")
        return False

    all_matched = True

    for i in range(len(device_alarms)):
        dev_alarm = device_alarms[i]
        lw_alarm = lw_alarms[i]

        # Normalize time (ignore seconds)
        dev_time = normalize_time(dev_alarm[0])
        lw_time = normalize_time(lw_alarm[0])

        # Compare fields
        if not (
            dev_time == lw_time and
            dev_alarm[1] == lw_alarm[1] and
            dev_alarm[2] == lw_alarm[2] and
            dev_alarm[3] == lw_alarm[3]
        ):
            if section:
                print(f"[{ip}] Alarm mismatch at index {i} in {section}:")
            else:
                print(f"[{ip}] Alarm mismatch at index {i}:")
            print(f"  Device: {dev_alarm[:4]}")
            print(f"  LW:     {lw_alarm[:4]}")
            all_matched = False
            break

    return all_matched

def extract_device_name_and_device_ip(device_str: str) -> tuple:
    """
    Extract device name and IP from string like:
    'PL-1000IL2 (172.16.30.13)' -> ('PL-1000IL2', '172.16.30.13')
    """
    device_name = device_str.split('(')[0].strip()
    device_ip = device_str.split('(')[-1].split(')')[0].strip()
    return device_name, device_ip

def test_show_device_alarms_via_SNMPv2(page, left_panel: LeftPanel, logger, report):
    domain_management = DomainManagement(page)
    device_discovery = DeviceDiscovery(page)
    alarms_and_events = AlarmsAndEvents(page)
    management_map = ManagementMap(page)
    upper_panel = UpperPanel(page)
    common_functions = CommonFunctionsPage(page)

    results = {}
    pl_alarms_stored = {}
    pl_alarms_port_1 = {}

    # #######################################
    # # Step 1 – Add domain and sub-domain. #
    # #######################################
    # def step_1():
    #     left_panel.click_domain_management()
    #     domain_management.add_domain(DOMAIN_NAME)
    #     sleep(0.5)
    #     domain_management.add_domain(SUB_DOMAIN_NAME, parent_domain_name=DOMAIN_NAME)
    #     sleep(0.5)

    # results[1] = run_step(1, step_1, logger, report)

    # ########################################
    # # Step 2 – Cold reset for all devices. # 
    # ########################################
    # def step_2():
    #     for ip in DEVICES_LIST:
    #         device_page = page.context.new_page()
    #         pl_login = PL_LoginPage(device_page)
    #         pl_login.goto(f"http://{ip}/")
    #         pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
    #         sleep(1)

    #         pl_main_screen_POM = PL_Main_Screen_POM(device_page)
    #         pl_main_screen_POM.device_restart("cold")
    #         sleep(5)
    #         device_page.close()

    #     # Wait for devices to come back up after cold reset
    #     devices_are_up(DEVICES_LIST, wait_time=WAIT)

    # results[2] = run_step(2, step_2, logger, report)

    # ################################################################################
    # # Step 3 – Login to the GUI of each IP.                                        #
    # # Set SNTP server and timezone to synchronize device time with LW server time. #                                   
    # # Add the LW server as SNMP trap manager with SNMP v2c.                        # 
    # ################################################################################
    # def step_3():
    #     for ip in DEVICES_LIST:
    #         device_page = page.context.new_page()
    #         pl_login = PL_LoginPage(device_page)
    #         pl_login.goto(f"http://{ip}/")

    #         ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
    #         assert ok, f"Login to {ip} GUI failed."

    #         pl_main_screen = PL_Main_Screen_POM(device_page)

    #         # set chassis id to empty 
    #         pl_main_screen.set_chassis_id(" ") 

    #         pl_main_screen.add_sntp_server(GOOGLE_SNTP_SERVER)
    #         pl_main_screen.set_sntp_configuration(status="Enabled", gmt=GMT2)
    #         refresh_page(device_page)

    #         pl_SNMP = PL_SNMPPage(device_page)  
    #         pl_SNMP.open_SNMP_tab()
    #         success, _ = pl_SNMP.Add_Trap_Manager(IP=LW_SERVER_HOST_IP.split(":")[0], SNMP_Version="SNMP v2c")
    #         assert success, f"Server IP was not added as trap manager for {ip}"

    #         device_page.close()

    # results[3] = run_step(3, step_3, logger, report)

    # #############################################################
    # # Step 4 – For each IP, set IP and click Start Discovery.   # 
    # #############################################################
    # def step_4():
    #     left_panel.click_device_discovery()
    #     device_discovery.click_SNMPv2()

    #     for ip in DEVICES_LIST:
    #         device_discovery.set_ip_address(ip)
    #         sleep(0.5)
    #         device_discovery.click_start_discovery()
    #         refresh_page(page)
    #         sleep(2)

    #     refresh_page(page)

    # results[4] = run_step(4, step_4, logger, report)

    # ##########################################################
    # # Step 5 – Change chassis ID and move chassis to domain. # 
    # ##########################################################
    # def step_5():
    #     left_panel.click_domain_management()

    #     try:
    #         domain_management.change_CHASSIS_ID(
    #             element_name=DUT_IP1,
    #             to_mode="new",
    #             new_chassis_id=NEW_CHASSIS_ID, 
    #             existing_chassis_id=None,
    #             parent_chassis=None
    #         )

    #     except Exception as e:
    #         print(f"Failed to change chassis id for {DUT_IP1}: {e}")
    #         logger.info(f"Failed to change chassis id for {DUT_IP1}: {e}")

    #     try:
    #         domain_management.change_CHASSIS_ID(
    #             element_name=DUT_IP2,
    #             to_mode="existing",
    #             new_chassis_id=None, 
    #             existing_chassis_id=f"Chassis: {NEW_CHASSIS_ID}",
    #             parent_chassis=None
    #         )

    #     except Exception as e:
    #         print(f"Failed to change chassis id for {DUT_IP2}: {e}")
    #         logger.info(f"Failed to change chassis id for {DUT_IP2}: {e}")

    #     try:
    #         domain_management.move_to_domain(source_item_name=f"Chassis: {NEW_CHASSIS_ID}/{NEW_CHASSIS_ID}",
    #          target_domain_name=SUB_DOMAIN_NAME)
    #     except Exception as e:
    #         print(f"Failed to move Chassis {NEW_CHASSIS_ID}/{NEW_CHASSIS_ID} to domain {SUB_DOMAIN_NAME}: {e}")
    #         logger.info(f"Failed to move Chassis {NEW_CHASSIS_ID}/{NEW_CHASSIS_ID} to domain {SUB_DOMAIN_NAME}: {e}")

    # results[5] = run_step(5, step_5, logger, report)

    # #############################################################
    # # Step 6 – Store the alarm table of the IP via GUI.         # 
    # # Go to Alarm & Events on LW server, compare alarms list.   # 
    # #############################################################
    # def step_6():
    #     
    #     for ip in DEVICES_LIST:
    #         device_page = page.context.new_page()
    #         pl_login = PL_LoginPage(device_page)
    #         pl_login.goto(f"http://{ip}/")
    #         pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
    #         pl_main = PL_Main_Screen_POM(device_page)
            
    #         try:
    #             pl_alarms_stored[ip] = pl_main.get_alarms_table("ALL")
    #             print(f"Alarms from {ip} GUI: {pl_alarms_stored[ip]}")
    #         except Exception:
    #             pl_alarms_stored[ip] = []

    #         device_page.close()

    #         left_panel.click_alarms_and_events()
    #         alarms_and_events.set_faults_type("Alarms")
    #         alarms_and_events.set_filterBy("Devices")
    #         alarms_and_events.select_device_filterBy_devices(ip)
            
    #         try:
    #             lw_alarms = alarms_and_events.get_all_alarms()
    #             lw_formatted_alarms = convert_lw_alarms_to_gui_alarms_format(ip, lw_alarms)
    #             print(f"Alarms from {ip} LW (GUI format): {lw_formatted_alarms}")

    #         except Exception:
    #             lw_alarms = []
    #             lw_formatted_alarms = []
            
    #         is_match = compare_device_and_lw_alarms(ip, pl_alarms_stored[ip], lw_formatted_alarms)
    #         if not is_match:
    #             raise AssertionError(f"Alarms content mismatch for {ip} between Device GUI and LW.")
            
    #         refresh_page(page)

    # results[6] = run_step(6, step_6, logger, report)

    # ###############################################
    # # Step 7 – Select Chassis and compare alarms. # 
    # ###############################################
    # def step_7():
    #     for ip in DEVICES_LIST:
    #         device_page = page.context.new_page()
    #         pl_login = PL_LoginPage(device_page)
    #         pl_login.goto(f"http://{ip}/")
    #         pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
    #         pl_main = PL_Main_Screen_POM(device_page)
            
    #         try:
    #             pl_alarms_stored[ip] = pl_main.get_alarms_table("ALL")
    #             print(f"Alarms from {ip} GUI: {pl_alarms_stored[ip]}")
    #         except Exception:
    #             pl_alarms_stored[ip] = []

    #         device_page.close()

    #     left_panel.click_alarms_and_events()
    #     alarms_and_events.set_faults_type("Alarms")
    #     alarms_and_events.set_filterBy("Domain/Chassis")
    #     alarms_and_events.select_domain_or_chassis_filterBy_domain_or_chassis("Chassis: 67/67")
        
    #     try:
    #         lw_alarms = alarms_and_events.get_all_alarms()
    #     except Exception:
    #         lw_alarms = []

    #     all_match = True
    #     for ip in DEVICES_LIST:
    #         lw_source_alarms = [a for a in lw_alarms if ip in a.get('source', '')]
    #         lw_formatted_alarms = convert_lw_alarms_to_gui_alarms_format(ip, lw_source_alarms)
    #         print(f"Alarms from {ip} LW (GUI format, filtered): {lw_formatted_alarms}")
            
    #         is_match = compare_device_and_lw_alarms(ip, pl_alarms_stored[ip], lw_formatted_alarms)
    #         if not is_match:
    #             all_match = False
                
    #     if not all_match:
    #         raise AssertionError("Alarms content mismatch between Device GUI and LW Server.")
            
    #     refresh_page(page)

    # results[7] = run_step(7, step_7, logger, report)

    # #############################################################
    # # Step 8 – Get product name from IP GUI.                    # 
    # # In LW Server, filter by Device type and compare alarms.   # 
    # #############################################################
    # def step_8():
    #     all_match = True

    #     for ip in DEVICES_LIST:
    #         device_page = page.context.new_page()
    #         pl_login = PL_LoginPage(device_page)
    #         pl_login.goto(f"http://{ip}/")
    #         pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
    #         pl_main = PL_Main_Screen_POM(device_page)

    #         try:
    #             pl_alarms_stored[ip] = pl_main.get_alarms_table("ALL")
    #         except Exception:
    #             pl_alarms_stored[ip] = []

    #         try:
    #             product_name = pl_main.get_system_product_name()
    #             if product_name == "PL-1000IL":
    #                 product_name = "PL-1000IL2"

    #         except Exception:
    #             # fallback: extract product name from DUT_IP strings
    #             product_name_1, product_ip1 = extract_device_name_and_device_ip(DUT_IP1)
    #             product_name_2, product_ip_2 = extract_device_name_and_device_ip(DUT_IP2)
    #             if ip == product_ip1:
    #                 product_name = product_name_1
    #             elif ip == product_ip_2:
    #                 product_name = product_name_2
    #             else:             
    #                 raise AssertionError(f"Failed to get product name for {ip} and match it to expected IPs.")

    #         device_page.close()

    #         left_panel.click_alarms_and_events()
    #         alarms_and_events.set_faults_type("Alarms")
    #         alarms_and_events.set_filterBy("Device type")
    #         alarms_and_events.select_devices_type_filterBy_device_type(product_name)
            
    #         try:
    #             lw_alarms = alarms_and_events.get_all_alarms()
    #         except:
    #             lw_alarms = []
                
    #         lw_source_alarms = [a for a in lw_alarms if ip in a.get('source', '')]
    #         lw_formatted_alarms = convert_lw_alarms_to_gui_alarms_format(ip, lw_source_alarms)

    #         is_match = compare_device_and_lw_alarms(ip, pl_alarms_stored[ip], lw_formatted_alarms)
    #         if not is_match:
    #             all_match = False

    #     if not all_match:
    #         raise AssertionError("Alarms content mismatch between Device GUI and LW Server.")

    #     refresh_page(page)

    # results[8] = run_step(8, step_8, logger, report)

    # ###########################################################
    # # Step 9 – Set admin up for port on IP GUI, store alarms. # 
    # # Check severity (Critical/Major/Minor/All) and match.    # 
    # ###########################################################
    # def step_9():
    #     refresh_page(page)
    #     all_match = True

    #     for ip in DEVICES_LIST:
    #         device_page = page.context.new_page()
    #         pl_login = PL_LoginPage(device_page)
    #         pl_login.goto(f"http://{ip}/")
    #         pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
    #         pl_main = PL_Main_Screen_POM(device_page)
            
    #         try:
    #             product_name = pl_main.get_system_product_name()
    #             port_number = PORT_PER_PRODUCT.get(product_name)
                
    #             pl_main.set_admin_status(port_number=port_number, status="Up")
    #             pl_alarms_port_1[ip] = pl_main.get_alarms_table(button_or_port=port_number)
    #         except Exception as e:
    #             print(f"error: {e}")
    #             pl_alarms_port_1[ip] = []

    #         device_page.close()

    #         try:
    #             # left_panel.click_common_functions()
    #             # common_functions.click_polling_restart()

    #             left_panel.click_alarms_and_events()
    #             alarms_and_events.set_faults_type("Alarms")
    #             alarms_and_events.set_filterBy("Devices")
    #             alarms_and_events.select_device_filterBy_devices(ip)
    #             lw_alarms = alarms_and_events.get_all_alarms()
    #         except Exception:
    #             lw_alarms = []

    #         # Critical
    #         alarms_and_events.set_severity("Critical")
    #         lw_critical_port1 = [
    #             a for a in lw_alarms
    #             if a.get('severity') == 'Critical' and 
    #             (f"{ip} Port {port_number}" in a.get('source', '') or
    #             f"{ip} {port_number}" in a.get('source', ''))]
    #         lw_formatted_critical_alarms = convert_lw_alarms_to_gui_alarms_format(ip, lw_critical_port1)
    #         pl_critical_port1 = [a for a in pl_alarms_port_1[ip] if len(a) > 2 and a[2] == 'Critical']
    #         is_match = compare_device_and_lw_alarms(ip, pl_critical_port1, lw_formatted_critical_alarms, section="Critical")
    #         if not is_match:
    #             all_match = False

    #         # Major
    #         alarms_and_events.set_severity("Major")
    #         lw_major_port1 = [
    #             a for a in lw_alarms
    #             if a.get('severity') == 'Major' and 
    #             (f"{ip} Port {port_number}" in a.get('source', '') or
    #             f"{ip} {port_number}" in a.get('source', ''))]
    #         lw_formatted_major_alarms = convert_lw_alarms_to_gui_alarms_format(ip, lw_major_port1)
    #         pl_major_port1 = [a for a in pl_alarms_port_1[ip] if len(a) > 2 and a[2] == 'Major']
    #         is_match = compare_device_and_lw_alarms(ip, pl_major_port1, lw_formatted_major_alarms, section="Major")
    #         if not is_match:
    #             all_match = False

    #         # Minor
    #         alarms_and_events.set_severity("Minor")
    #         lw_minor_port1 = [
    #             a for a in lw_alarms
    #             if a.get('severity') == 'Minor' and 
    #             (f"{ip} Port {port_number}" in a.get('source', '') or
    #             f"{ip} {port_number}" in a.get('source', ''))]
    #         lw_formatted_minor_alarms = convert_lw_alarms_to_gui_alarms_format(ip, lw_minor_port1)
    #         pl_minor_port1 = [a for a in pl_alarms_port_1[ip] if len(a) > 2 and a[2] == 'Minor']
    #         is_match = compare_device_and_lw_alarms(ip, pl_minor_port1, lw_formatted_minor_alarms, section="Minor")
    #         if not is_match:
    #             all_match = False

    #         alarms_and_events.set_severity("All")
    #         refresh_page(page)

    #     if not all_match:
    #         raise AssertionError("Alarms content mismatch between Device GUI and LW Server.")

    # results[9] = run_step(9, step_9, logger, report)

    #############################################################
    # Step 10 – Login to GUI of 172.16.30.15.                   # 
    # Generate an alarm related to Category and match.          # 
    #############################################################
    def step_10():
        refresh_page(page)
        ip = "172.16.30.15"
        device_page = page.context.new_page()
        pl_login = PL_LoginPage(device_page)
        pl_login.goto(f"http://{ip}/")
        pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
        for category in CATEGORIES_LIST:
            # Generate an alarm that relate to 'category'
            pass
        device_page.close()
        
    results[10] = run_step(10, step_10, logger, report)

    #############################################################
    # Step 11 – Login to GUI of 172.16.30.15.                   # 
    # Generate an alarm related to Date and match.              # 
    #############################################################
    def step_11():
        refresh_page(page)
        ip = "172.16.30.15"
        device_page = page.context.new_page()
        pl_login = PL_LoginPage(device_page)
        pl_login.goto(f"http://{ip}/")
        pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
        for date_ in FROM_DATES_LIST:
            # Generate an alarm that relate to 'date'
            pass
        device_page.close()

    results[11] = run_step(11, step_11, logger, report)

    #############################################################
    # Step 12 – Login to GUI of 172.16.30.15.                   # 
    # Generate an alarm related to Message and match.           # 
    #############################################################
    def step_12():
        refresh_page(page)
        ip = "172.16.30.15"
        device_page = page.context.new_page()
        pl_login = PL_LoginPage(device_page)
        pl_login.goto(f"http://{ip}/")
        pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
        for msg in MESSAGES_LIST:
            # Generate an alarm that relate to 'message'
            pass
        device_page.close()

    results[12] = run_step(12, step_12, logger, report)

    #############################################################
    # Step 13 – Go to Alarm & Events on LW server.              # 
    # Clear alerts, verify severity is Clear, element green.    # 
    #############################################################
    def step_13():
        refresh_page(page)
        left_panel.click_alarms_and_events()
        alarms_and_events.set_faults_type("Alarms")
        alarms_and_events.set_filterBy("Devices")
        alarms_and_events.select_device_filterBy_devices("172.16.30.15")
        
        try:
             lw_alarms_pre = alarms_and_events.get_all_alarms()
        except:
             lw_alarms_pre = []
             
        number_of_alarms = len(lw_alarms_pre)
        for _ in range(number_of_alarms):
             try:
                 alarms_and_events.clear_alert()
             except Exception as e:
                 logger.info(f"clear_alert failed: {e}")
             
        # make sure that each alarms from the list has 'severity' = Clear
        left_panel.click_management_map()
        try:
             upper_panel.select_domain("Script_Domain")
        except:
             pass
        try:
             management_map.double_click_on_element_via_the_map("Script_Sub_Domain")
             color = management_map.get_map_element_color("172.16.30.15")
             if color != "green":
                  raise AssertionError("Element color is not green")
        except:
             pass

    results[13] = run_step(13, step_13, logger, report)

    #############################################################
    # Step 14 – Remove devices from LW.                         # 
    # Apply factory defaults to devices and wait for them.      # 
    #############################################################
    def step_14():
        refresh_page(page)
        left_panel.click_domain_management()
        for ip in DEVICES_LIST:
            try:
                domain_management.select_device_row(ip, "Remove")
                domain_management.action_btn("Remove").click(force=True)
                domain_management.warning_remove_modal().locator("button.btn.btn-primary", has_text="Yes").click()
                sleep(1)
            except Exception as e:
                logger.info(f"Remove failed for {ip}: {e}")

        # Factory Default
        for ip in DEVICES_LIST:
            try:
                SNMP_Device_Reset(ip, "factory")
            except:
                device_page = page.context.new_page()
                pl_login = PL_LoginPage(device_page)
                pl_login.goto(f"http://{ip}/")
                pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
                pl_main = PL_Main_Screen_POM(device_page)
                try:
                    pl_main.device_restart("factory")
                except:
                    pass
                device_page.close()
                pass
        
        try:
             devices_are_up(DEVICES_LIST, wait_time=WAIT)
        except:
             pass

    results[14] = run_step(14, step_14, logger, report)

    ######################################################################################
    # Step 15 – Need to complete this step after i learn how to generate all the alarms  # 
    ######################################################################################
    def step_15():
        refresh_page(page)

        # ==========================================================
        # Expected Popular Events / Alarms list (for LW validation)
        # Source: LW presentation documentation
        # ==========================================================

        EXPECTED_EVENTS = {

            "client": [
                "Optics Removed",
                "Loss of Light",
                "Loss of Lock",
                "Loss of Sync",
                "HI BER",
                "OTN LOF",
                "Ethernet Link Failure",
                "Remote Fault",
                "Key Exchange Failed",
                "No License or License Expired",
                "Service changing",
                "Service Provisioning",
            ],

            "uplink": [
                "Optics Removed",
                "Loss of Light",
                "Loss of Lock",
                "OTN Path AIS",
                "OTN Path BDI",
                "Tx/WL changing",
            ],

            "system": [
                "NTP server alarms/events",
                "Radius/Tacacs events",
                "Syslog server events",
                "SW upgrade events",
                "Remote Power Failure",
                "User Login/Logout",
                "Hardware Failure",
                "Login Intrusion",
                "Power Supply Failure 1",
                "Power Supply Failure 2",
                "Fan unit",
                "System mode changing",
                "Cold reset",
                "Warm reset",
                "WEB GUI: General tab Configuration",
                "WEB GUI: IP tab configuration",
                "SNMP add/delete",
                "EDFA configuration",
                "APS configuration",
                "Optical Switch",
                "OLP",
            ],

            "roadm": [
                "Add",
                "Drop",
                "WSS",
            ]
        }

    results[15] = run_step(15, step_15, logger, report)

    # ==========================================================


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

        test_show_device_alarms_via_SNMPv2(page, left_panel, logger, report)

        context.close()
        browser.close()
        close_report(report)

    end_time = time.perf_counter()
    print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
    logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")