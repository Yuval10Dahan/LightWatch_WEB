"""
Created by: Yuval Dahan
Date: 13/04/2026

Comprehensive Events Test - Show Device Events via SNMPv3
=====================================================
Tests the Device Events using SNMPv3.

*** Runtime: approximately == minutes ***
=====================================================

Steps to verify before running this script:
--------------------------------------------------------------------------------------------------------------------------
1. Verify that UDP port 162 on the LW server machine is not occupied by the Windows SNMP Trap service (snmptrap.exe).
   - Check via: Resource Monitor → Network tab → Listening Ports.
2. If port 162 is occupied by snmptrap.exe, apply the following workaround:
   Workaround / Temporary Fix:
   ---------------------------
   a. Stop LW Server.
   b. Press Win + R.
   c. Type: services.msc
   d. Locate: SNMP Trap
   e. Right-click → Properties → Click Stop.
   f. Set Startup type → Disabled → Click Apply → OK.
   g. Start LW Server.
3. After applying the fix, verify that port 162 is now occupied by java.exe and not snmptrap.exe.
--------------------------------------------------------------------------------------------------------------------------
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.device_discovery import DeviceDiscovery
from Pages.domain_management import DomainManagement
from Pages.alarms_and_events import AlarmsAndEvents
from PL_Devices.PL_Pages.PL_login_page import PL_LoginPage
from PL_Devices.PL_Pages.PL_security_page import PL_SecurityPage
from PL_Devices.PL_Pages.PL_main_screen_POM import PL_Main_Screen_POM
from Utils.utils import refresh_page, devices_are_up
import time
from time import sleep
from Utils.Logger import create_logger
import sys
from sys import argv
from Utilities.QCreporter import open_report, close_report, step_passed, step_failed
import os
from datetime import datetime
import re
from datetime import timedelta

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

    DUT_IP_NAMES = ["PL-2000ADS (172.16.30.15)", "PL-1000IL2 (172.16.30.13)"]

    NEW_CHASSIS_ID = "67"
    DOMAIN_NAME = "Script_Domain"
    SUB_DOMAIN_NAME = "Script_Sub_Domain"

    CATEGORY_TEST_DEVICE = "172.16.40.31"
    

# ================================================================
# Values that should not be changed
# ================================================================

BASE_URL = f"http://{LW_SERVER_HOST_IP}/"
WAIT = 30

SNMPV3_USERNAME = "admin3"
SNMPV3_PASSWORD = "Admin1234!"
AUTH_TYPE = "SHA1"

SNMPV3_USERNAME = "admin"

CATEGORIES_LIST = ["Device", "Syslog", "System", "Configuration Event", "Inventory",
                    "Discovery", "Provisioning", "Security", "Service", "OTN Service", 
                    "CS Service", "CS Link", "ROADM domain"]

ALL_DEVICES = DEVICES_LIST + [CATEGORY_TEST_DEVICE]

GOOGLE_SNTP_SERVER = '216.239.35.0'
GMT2 = "GMT+2"

LOGGER_ROOT_DIRECTORY = 'G:\\Python\\PacketLight Automation\\LightWatch_WEB\\Scripts\\Alarms_And_Events\\Device_Events\\LogFiles'
LOGGER_DIRECTORY_NAME = "show_device_events_via_SNMPv2"
LOG_FILE_NAME = 'show_device_events_via_SNMPv2.log'
REPORT_PATH = None

DUMMY_MESSAGE = "NonExistentMessageTest123"

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

def convert_lw_events_to_gui_events_format(ip: str, lw_events: list, device_events: list = None) -> list:
    """
    Convert LW events (dict format) into GUI-like table format,
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
        if source.strip() == ip:
            return "System"

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

    for event in lw_events:
        lw_msg = event.get("Message", event.get("message", ""))
        lw_src = normalize_source(event.get("Source", event.get("source", "")))
        lw_sev = event.get("Severity", event.get("severity", ""))
        
        if device_events:
            for dev_event in device_events:
                dev_msg = dev_event[3].replace("System Event :", "").strip()
                dev_msg_lower = dev_msg.lower()
                lw_msg_lower = lw_msg.lower()
                
                # Check for match to map properties
                message_match = (dev_msg_lower in lw_msg_lower) or (lw_msg_lower in dev_msg_lower)
                if not message_match:
                    dev_words = set(dev_msg_lower.split())
                    lw_words = set(lw_msg_lower.split())
                    if len(dev_words.intersection(lw_words)) >= 2:
                        message_match = True
                        
                if message_match:
                    dev_src = dev_event[1].strip()
                    dev_sev = dev_event[2].strip()
                    
                    if dev_src != "System":
                        lw_src = dev_event[1]
                        
                    if dev_sev not in ["Critical", "Major", "Minor"]:
                        lw_sev = dev_event[2]
                    break

        formatted.append([
            convert_timestamp(event.get("Creation Timestamp", event.get("creation_timestamp", ""))),
            lw_src,
            lw_sev,
            lw_msg,
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

def compare_device_and_lw_events(ip: str, device_events: list, lw_events: list, section: str | None = None) -> bool:
    """
    Check if all device events exist in the LW events list.
    LW events list might be larger. Matches are verified by source and message content.
    """
    if not device_events:
        return True
        
    if not lw_events and device_events:
        print(f"[{ip}] Events missing in {section}: Device GUI has {len(device_events)} events, LW is empty.")
        return False

    all_matched = True

    for dev_event in device_events:
        dev_time_str = dev_event[0]
        dev_src = dev_event[1].strip()
        dev_sev = dev_event[2].strip()
        dev_msg = dev_event[3].replace("System Event :", "").strip()

        match_found = False
        for lw_event in lw_events:
            lw_src = lw_event[1].strip()
            lw_sev = lw_event[2].strip()
            lw_msg = lw_event[3].strip()

            dev_msg_lower = dev_msg.lower()
            lw_msg_lower = lw_msg.lower()

            # Message match
            message_match = (dev_msg_lower in lw_msg_lower) or (lw_msg_lower in dev_msg_lower)
            if not message_match:
                dev_words = set(re.sub(r'[^\w\s]', '', dev_msg_lower).split())
                lw_words = set(re.sub(r'[^\w\s]', '', lw_msg_lower).split())
                if len(dev_words.intersection(lw_words)) >= 2:
                    message_match = True

            # Since properties are mapped in convert_lw_events_to_gui_events_format, we can strictly match them
            source_match = (dev_src == lw_src)
            severity_match = (dev_sev == lw_sev)

            if message_match and source_match and severity_match:
                match_found = True
                break
                
        if not match_found:
            if section:
                print(f"[{ip}] Missing event in {section}:")
            else:
                print(f"[{ip}] Missing event:")
            print(f"  Device Event: {dev_event}")
            all_matched = False

    if all_matched:
        if section:
            print(f"[{ip}] All {len(device_events)} {section} device events verified in LW Server. ✅")
        else:
            print(f"[{ip}] All {len(device_events)} device events verified in LW Server. ✅")

    return all_matched

def extract_device_name_and_device_ip(device_str: str) -> tuple:
    """
    Extract device name and IP from string like:
    'PL-1000IL2 (172.16.30.13)' -> ('PL-1000IL2', '172.16.30.13')
    """
    device_name = device_str.split('(')[0].strip()
    device_ip = device_str.split('(')[-1].split(')')[0].strip()
    return device_name, device_ip

def test_show_device_events_via_SNMPv3(page, left_panel: LeftPanel, logger, report):
    domain_management = DomainManagement(page)
    device_discovery = DeviceDiscovery(page)
    alarms_and_events = AlarmsAndEvents(page)

    results = {}
    pl_events_stored = {}
    pl_events_port_1 = {}

    #######################################
    # Step 1 – Add domain and sub-domain. #
    #######################################
    def step_1():
        left_panel.click_domain_management()
        domain_management.add_domain(DOMAIN_NAME)
        sleep(0.5)
        domain_management.add_domain(SUB_DOMAIN_NAME, parent_domain_name=DOMAIN_NAME)
        sleep(0.5)

    results[1] = run_step(1, step_1, logger, report)

    ###################################################
    # Step 2 – Factory default reset for all devices. # 
    ###################################################
    def step_2():
        for ip in ALL_DEVICES:
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
        devices_are_up(ALL_DEVICES, wait_time=WAIT)

    results[2] = run_step(2, step_2, logger, report)

    ################################################################################
    # Step 3 – Login to the GUI of each IP.                                        #
    # Set SNTP server and timezone to synchronize device time with LW server time. #                                   
    ################################################################################
    def step_3():
        for ip in ALL_DEVICES:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")

            ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            assert ok, f"Login to {ip} GUI failed."

            pl_main_screen = PL_Main_Screen_POM(device_page)

            # set chassis id to empty 
            pl_main_screen.set_chassis_id(" ") 

            pl_main_screen.add_sntp_server(GOOGLE_SNTP_SERVER)
            pl_main_screen.set_sntp_configuration(status="Enabled", gmt=GMT2)
            refresh_page(device_page)

            device_page.close()

    results[3] = run_step(3, step_3, logger, report)

    ###################################################
    # Step 4 – Add SNMPv3 user to each IP.            #
    # For each IP, set IP and click Start Discovery.  #                                   
    ###################################################
    def step_4():
        for ip in ALL_DEVICES:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            assert ok, f"Login to {ip} GUI failed."

            pl_security = PL_SecurityPage(device_page)
            pl_security.add_new_user(user_name=SNMPV3_USERNAME, permission="Administrator", password=SNMPV3_PASSWORD,
             verify_password=SNMPV3_PASSWORD, snmpv3_auth=AUTH_TYPE, password_auth=SNMPV3_PASSWORD)

        sleep(5)
        left_panel.click_device_discovery()
        device_discovery.click_SNMPv3()

        for ip in ALL_DEVICES:
            device_discovery.set_ip_address(ip)
            sleep(0.5)
            device_discovery.set_SNMPv3_user_name(SNMPV3_USERNAME)
            sleep(0.5)
            device_discovery.click_start_discovery()
            refresh_page(page)
            sleep(2)

        refresh_page(page)

    results[4] = run_step(4, step_4, logger, report)

    ##########################################################
    # Step 5 – Change chassis ID and move chassis to domain. # 
    ##########################################################
    def step_5():
        left_panel.click_domain_management()

        try:
            domain_management.change_CHASSIS_ID(
                element_name=DUT_IP_NAMES[0],
                to_mode="new",
                new_chassis_id=NEW_CHASSIS_ID, 
                existing_chassis_id=None,
                parent_chassis=None
            )

        except Exception as e:
            print(f"Failed to change chassis id for {DUT_IP_NAMES[0]}: {e}")
            logger.info(f"Failed to change chassis id for {DUT_IP_NAMES[0]}: {e}")
        
        for dut_name in DUT_IP_NAMES:
            if dut_name != DUT_IP_NAMES[0]:
                try:
                    domain_management.change_CHASSIS_ID(
                        element_name=dut_name,
                        to_mode="existing",
                        new_chassis_id=None, 
                        existing_chassis_id=f"Chassis: {NEW_CHASSIS_ID}",
                        parent_chassis=None
                    )

                except Exception as e:
                    print(f"Failed to change chassis id for {dut_name}: {e}")
                    logger.info(f"Failed to change chassis id for {dut_name}: {e}")

        try:
            domain_management.move_to_domain(source_item_name=f"Chassis: {NEW_CHASSIS_ID}/{NEW_CHASSIS_ID}",
             target_domain_name=SUB_DOMAIN_NAME)
        except Exception as e:
            print(f"Failed to move Chassis {NEW_CHASSIS_ID}/{NEW_CHASSIS_ID} to domain {SUB_DOMAIN_NAME}: {e}")
            logger.info(f"Failed to move Chassis {NEW_CHASSIS_ID}/{NEW_CHASSIS_ID} to domain {SUB_DOMAIN_NAME}: {e}")

    results[5] = run_step(5, step_5, logger, report)

    #############################################################
    # Step 6 – Store the events table of the IP via GUI.        # 
    # Go to Alarm & Events on LW server, compare events list.   # 
    #############################################################
    def step_6():
        for ip in DEVICES_LIST:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)
            
            try:
                pl_events_stored[ip] = pl_main.get_events_table("ALL")
                # print(f"Events from {ip} GUI length: {len(pl_events_stored[ip])} \n")
                # print(f"Events from {ip} GUI: {pl_events_stored[ip]} \n")
            except Exception:
                pl_events_stored[ip] = []
 
            device_page.close()

            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Events")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            
            try:
                lw_events = alarms_and_events.get_all_events()
                # print(f"Events from {ip} LW length: {len(lw_events)} \n")
                lw_formatted_events = convert_lw_events_to_gui_events_format(ip, lw_events, pl_events_stored.get(ip, []))
                # print(f"Events from {ip} LW (GUI format) length: {len(lw_formatted_events)} \n")
                # print(f"Events from {ip} LW (GUI format): {lw_formatted_events} \n")
            except Exception:
                lw_events = []
                lw_formatted_events = []
            
            is_match = compare_device_and_lw_events(ip, pl_events_stored[ip], lw_formatted_events)
            if not is_match:
                raise AssertionError(f"Events content mismatch for {ip} between Device GUI and LW.")
            
            refresh_page(page)

    results[6] = run_step(6, step_6, logger, report)

    ###############################################
    # Step 7 – Select Chassis and compare events. # 
    ###############################################
    def step_7():
        left_panel.click_alarms_and_events()
        alarms_and_events.set_faults_type("Events")
        alarms_and_events.set_filterBy("Domain/Chassis")
        alarms_and_events.select_domain_or_chassis_filterBy_domain_or_chassis("Chassis: 67/67")
        
        try:
            lw_events = alarms_and_events.get_all_events()
            # print(f"lw events length: {len(lw_events)}\n")
        except Exception:
            lw_events = []

        all_match = True
        for ip in DEVICES_LIST:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)
            
            try:
                pl_events_stored[ip] = pl_main.get_events_table("ALL")
                # print(f"Events from {ip} GUI length: {len(pl_events_stored[ip])} \n")
                # print(f"Events from {ip} GUI: {pl_events_stored[ip]} \n")
            except Exception:
                pl_events_stored[ip] = []
 
            device_page.close()

            lw_source_events = [a for a in lw_events if ip in a.get('Source', '')]
            # print(f"lw source events for {ip} length: {len(lw_source_events)}\n")
            lw_formatted_events = convert_lw_events_to_gui_events_format(ip, lw_source_events, pl_events_stored.get(ip, []))
            # print(f"lw formatted events for {ip} length: {len(lw_formatted_events)}\n")
            # print(f"pl events stored for {ip} length: {len(pl_events_stored.get(ip, []))}\n")
            
            is_match = compare_device_and_lw_events(ip, pl_events_stored[ip], lw_formatted_events)
            if not is_match:
                all_match = False

        if not all_match:
            raise AssertionError(f"Events content mismatch for ip {ip} between Device GUI and LW Server.")
                
        refresh_page(page)

    results[7] = run_step(7, step_7, logger, report)

    #############################################################
    # Step 8 – Get product name from IP GUI.                    # 
    # In LW Server, filter by Device type and compare events.   # 
    #############################################################
    def step_8():
        for ip in DEVICES_LIST:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)

            try:
                pl_events_stored[ip] = pl_main.get_events_table("ALL")
                # print(f"Events from {ip} GUI length: {len(pl_events_stored[ip])} \n")
                # print(f"Events from {ip} GUI: {pl_events_stored[ip]} \n")
            except Exception:
                pl_events_stored[ip] = []

            try:
                product_name = pl_main.get_system_product_name()
                if product_name == "PL-1000IL":
                    product_name = "PL-1000IL2"

            except Exception:
                for dut_name in DUT_IP_NAMES:
                    product_name_from_list, product_ip_from_list = extract_device_name_and_device_ip(dut_name)
                    if ip == product_ip_from_list:
                        product_name = product_name_from_list
                        break
                else:             
                    raise AssertionError(f"Failed to get product name for {ip} and match it to expected IPs.")

            device_page.close()
            refresh_page(page)

            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Events")
            alarms_and_events.set_filterBy("Device type")
            alarms_and_events.select_devices_type_filterBy_device_type(product_name)
            
            try:
                lw_events_device_type = alarms_and_events.get_all_events()
            except:
                lw_events_device_type = []
                
            lw_source_events = [a for a in lw_events_device_type if ip in a.get('Source', '')]
            lw_formatted_events = convert_lw_events_to_gui_events_format(ip, lw_source_events, pl_events_stored.get(ip, []))
            # print(f"lw formatted events for {ip} length: {len(lw_formatted_events)}\n")
            # print(f"pl events stored for {ip} length: {len(pl_events_stored.get(ip, []))}\n")

            is_match = compare_device_and_lw_events(ip, pl_events_stored[ip], lw_formatted_events)
            if not is_match:
                raise AssertionError(f"Events content mismatch for {ip} between Device GUI and LW Server.")

        refresh_page(page)

    results[8] = run_step(8, step_8, logger, report)

    ###########################################################
    # Step 9 – Set admin up for port on IP GUI, store events. # 
    # Check severity (Critical/Major/Minor) and match.        # 
    ###########################################################
    def step_9():
        refresh_page(page)

        for ip in DEVICES_LIST:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)
            
            try:
                product_name = pl_main.get_system_product_name()
                port_number = PORT_PER_PRODUCT.get(product_name)
                
                pl_main.set_admin_status(port_number=port_number, status="Up")
                pl_events_port_1[ip] = pl_main.get_events_table(button_or_port=port_number)
            except Exception as e:
                print(f"error: {e}")
                pl_events_port_1[ip] = []

            device_page.close()

            try:
                left_panel.click_alarms_and_events()
                alarms_and_events.set_faults_type("Events")
                alarms_and_events.set_filterBy("Devices")
                alarms_and_events.select_device_filterBy_devices(ip)
                lw_events = alarms_and_events.get_all_events()
            except Exception:
                lw_events = []

            # Critical
            alarms_and_events.set_severity("Critical")
            lw_critical_port1 = [
                a for a in lw_events
                if a.get('Severity', a.get('severity')) == 'Critical' and 
                (f"{ip} Port {port_number}" in a.get('Source', '') or
                f"{ip} {port_number}" in a.get('Source', ''))]
            lw_formatted_critical_events = convert_lw_events_to_gui_events_format(ip, lw_critical_port1, pl_events_port_1.get(ip, []))
            pl_critical_port1 = [a for a in pl_events_port_1[ip] if len(a) > 2 and a[2] == 'Critical']
            is_match = compare_device_and_lw_events(ip, pl_critical_port1, lw_formatted_critical_events, section="Critical")
            if not is_match:
                raise AssertionError(f"Critical Events mismatch for {ip}")

            # Major
            alarms_and_events.set_severity("Major")
            lw_major_port1 = [
                a for a in lw_events
                if a.get('Severity', a.get('severity')) == 'Major' and 
                (f"{ip} Port {port_number}" in a.get('Source', '') or
                f"{ip} {port_number}" in a.get('Source', ''))]
            lw_formatted_major_events = convert_lw_events_to_gui_events_format(ip, lw_major_port1, pl_events_port_1.get(ip, []))
            pl_major_port1 = [a for a in pl_events_port_1[ip] if len(a) > 2 and a[2] == 'Major']
            is_match = compare_device_and_lw_events(ip, pl_major_port1, lw_formatted_major_events, section="Major")
            if not is_match:
                raise AssertionError(f"Major Events mismatch for {ip}")

            # Minor
            alarms_and_events.set_severity("Minor")
            lw_minor_port1 = [
                a for a in lw_events
                if a.get('Severity', a.get('severity')) == 'Minor' and 
                (f"{ip} Port {port_number}" in a.get('Source', '') or
                f"{ip} {port_number}" in a.get('Source', ''))]
            lw_formatted_minor_events = convert_lw_events_to_gui_events_format(ip, lw_minor_port1, pl_events_port_1.get(ip, []))
            pl_minor_port1 = [a for a in pl_events_port_1[ip] if len(a) > 2 and a[2] == 'Minor']
            is_match = compare_device_and_lw_events(ip, pl_minor_port1, lw_formatted_minor_events, section="Minor")
            if not is_match:
                raise AssertionError(f"Minor Events mismatch for {ip}")

            alarms_and_events.set_severity("All")
            refresh_page(page)

    results[9] = run_step(9, step_9, logger, report)

    ###########################################################
    # Step 10 – Login to GUI of CATEGORY_TEST_DEVICE.         # 
    # Union all events from all categories and match with LW. # 
    ###########################################################
    def step_10():
        refresh_page(page)
        device_page = page.context.new_page()
        pl_login = PL_LoginPage(device_page)
        pl_login.goto(f"http://{CATEGORY_TEST_DEVICE}/")
        pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
        pl_main = PL_Main_Screen_POM(device_page)

        try:
            pl_events = pl_main.get_events_table("ALL")
        except Exception as e:
            print(f"error: {e}")
            pl_events = []

        device_page.close()

        try:
            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Events")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(CATEGORY_TEST_DEVICE)
            lw_events = alarms_and_events.get_all_events()
        except Exception:
            lw_events = []

        union_lw_events = []
        for category in CATEGORIES_LIST:
            alarms_and_events.set_category(category)
            sleep(0.5)
            lw_category_events = [a for a in lw_events if a.get('category', a.get('Category')) == category]
            lw_formatted_category_events = convert_lw_events_to_gui_events_format(CATEGORY_TEST_DEVICE, lw_category_events, pl_events)
            union_lw_events.extend(lw_formatted_category_events)

        # Normalize time (ignore seconds) for sorting to compare regardless of order
        def normalize_time(ts: str) -> str:
            try:
                dt = datetime.strptime(ts, "%m/%d/%Y %I:%M:%S %p")
                return dt.strftime("%m/%d/%Y %I:%M %p")
            except Exception:
                return ts
                
        def sort_key(event):
            return (normalize_time(event[0]), event[1], event[2], event[3])

        pl_events_sorted = sorted(pl_events, key=sort_key)
        union_lw_events_sorted = sorted(union_lw_events, key=sort_key)

        is_match = compare_device_and_lw_events(CATEGORY_TEST_DEVICE, pl_events_sorted, union_lw_events_sorted, section="Category Union")
        if not is_match:
            raise AssertionError("Events content mismatch for Category Union between Device GUI and LW.")
        
    results[10] = run_step(10, step_10, logger, report)

    #############################################################
    # Step 11 – Test 'From date' and 'To date' filters in LW.   # 
    # Get an existing event and use its timestamp for filtering.# 
    #############################################################
    def step_11():
        for ip in DEVICES_LIST:
            refresh_page(page)
            
            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Events")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            
            try:
                lw_events = alarms_and_events.get_all_events()
            except:
                lw_events = []
                
            if not lw_events:
                print(f"Skipping Date test, No existing events found for {ip} to test Date filters.")
                continue

            target_event = lw_events[-1]
            timestamp_str = target_event.get('Creation Timestamp')
            
            try:
                dt = datetime.strptime(timestamp_str, "%d.%m.%Y, %H:%M:%S")
            except ValueError:
                raise ValueError(f"Failed to parse timestamp: {timestamp_str}")
            
            # 1) Positive Test Range (± 1 hour)
            from_dt_positive = (dt - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
            to_dt_positive = (dt + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

            alarms_and_events.set_from_date(from_dt_positive)
            alarms_and_events.set_to_date(to_dt_positive)
            
            filtered_positive = alarms_and_events.get_all_events()
            found = any(a.get('Message', a.get('message')) == target_event.get('Message', target_event.get('message')) and a.get('Creation Timestamp', a.get('creation_timestamp')) == target_event.get('Creation Timestamp', target_event.get('creation_timestamp')) for a in filtered_positive)
            if not found:
                raise AssertionError(f"Date Filter Positive Test Failed for {ip}: Target event {target_event.get('Message', target_event.get('message'))} was not found in the valid range {from_dt_positive} to {to_dt_positive}.")

            # 2) Negative Test Range (Both Dates set to 2-3 days ago)
            from_dt_negative = (dt - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
            to_dt_negative = (dt - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")

            alarms_and_events.set_from_date(from_dt_negative)
            alarms_and_events.set_to_date(to_dt_negative)
            
            filtered_negative = alarms_and_events.get_all_events()
            found_negative = any(a.get('Message', a.get('message')) == target_event.get('Message', target_event.get('message')) and a.get('Creation Timestamp', a.get('creation_timestamp')) == target_event.get('Creation Timestamp', target_event.get('creation_timestamp')) for a in filtered_negative)
            if found_negative:
                 raise AssertionError(f"Date Filter Negative Test Failed for {ip}: Target event was found outside of its valid date range.")

        refresh_page(page)

    results[11] = run_step(11, step_11, logger, report)

    #############################################################
    # Step 12 – Test 'Message' filter in LW.                    # 
    # Get an existing event and use its message for filtering.  # 
    #############################################################
    def step_12():
        for ip in DEVICES_LIST:
            refresh_page(page)
            
            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Events")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            
            try:
                lw_events = alarms_and_events.get_all_events()
            except:
                lw_events = []
                
            if not lw_events:
                print(f"Skipping Message test, No existing events found for {ip}.\n")
                continue

            target_event = lw_events[0]
            target_msg = target_event.get('Message')
            
            # 1) Positive Test Range (Filter by exact message)
            alarms_and_events.set_message(target_msg)
            sleep(1) 
            
            filtered_positive = alarms_and_events.get_all_events()
            print(f"Filtered events: {filtered_positive}\n")
            found = any(a.get('Message', a.get('message')) == target_msg and a.get('Creation Timestamp', a.get('creation_timestamp')) == target_event.get('Creation Timestamp', target_event.get('creation_timestamp')) for a in filtered_positive)
            if not found:
                raise AssertionError(f"Message Filter Positive Test Failed for {ip}: Target event with message '{target_msg}' was not found after filtering.")

            # 2) Negative Test Range (Filter by dummy message)
            alarms_and_events.set_message(DUMMY_MESSAGE)
            sleep(1) 
            
            try:
                filtered_negative = alarms_and_events.get_all_events()
            except:
                filtered_negative = []
                
            found_negative = any(DUMMY_MESSAGE in a.get('Message', a.get('message', '')) for a in filtered_negative)
            if found_negative or len(filtered_negative) > 0:
                 raise AssertionError(f"Message Filter Negative Test Failed for {ip}: Dummy message '{DUMMY_MESSAGE}' returned {len(filtered_negative)} results, expected 0.")

        refresh_page(page)

    results[12] = run_step(12, step_12, logger, report)

    #############################################################
    # Step 13 – Hide events and show hidden events.             # 
    #############################################################
    def step_13():
        refresh_page(page)

        for ip in DEVICES_LIST: 
            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Events")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events.close_devices_dropdown()
            
            try:
                lw_events = alarms_and_events.get_all_events()
            except:
                lw_events = []
                
            last_5_hidden_events_list = lw_events[-5:] if len(lw_events) >= 5 else lw_events[:]
            
            start_index = len(lw_events) - len(last_5_hidden_events_list)
            for i in range(start_index, len(lw_events)):
                alarms_and_events.hide_event(i)
                sleep(0.5)

            refresh_page(page)
            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Events")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events.close_devices_dropdown()
            
            alarms_and_events.show_hidden_events()
            sleep(1)
            
            try:
                lw_hidden_events = alarms_and_events.get_all_events()
            except:
                lw_hidden_events = []
                
            if lw_hidden_events != last_5_hidden_events_list:
                raise AssertionError(f"IP {ip}: Hidden events retrieved do not match the expected 5 events list.")

    results[13] = run_step(13, step_13, logger, report)

    #############################################################
    # Step 14 – Remove devices from LW.                         # 
    # Apply factory defaults to devices and wait for them.      # 
    #############################################################
    def step_14():
        refresh_page(page)
        left_panel.click_domain_management()

        # Remove devices from LW
        for ip in DEVICES_LIST:
            try:
                domain_management.remove_device(device_name_or_ip=ip, parent_chassis=f"Chassis: {NEW_CHASSIS_ID}", parent_domain_name=SUB_DOMAIN_NAME)
                sleep(1)
                deleted = domain_management.verify_element_deleted(element_name=ip, element_type="device")
                if not deleted:
                    raise AssertionError(f"{ip}: Element not deleted")

            except Exception as e:
                print(f"Remove failed for {ip}: {e}")
                logger.info(f"Remove failed for {ip}: {e}")

        # Reset chassis ID for all devices
        for ip in ALL_DEVICES:
            try:
                device_page = page.context.new_page()
                pl_login = PL_LoginPage(device_page)
                pl_login.goto(f"http://{ip}/")
                pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
                
                pl_main_screen = PL_Main_Screen_POM(device_page)
                pl_main_screen.set_chassis_id("")
                sleep(1)
                device_page.close()
            except Exception as e:
                try:
                    device_page.close()
                except:
                    pass
                print(f"Failed to reset chassis ID for {ip}: {e}")
                logger.info(f"Failed to reset chassis ID for {ip}: {e}")
        
        # Remove category test device
        domain_management.remove_device(device_name_or_ip=CATEGORY_TEST_DEVICE)
        sleep(1)
        deleted = domain_management.verify_element_deleted(element_name=CATEGORY_TEST_DEVICE, element_type="device")
        if not deleted:
            raise AssertionError(f"{CATEGORY_TEST_DEVICE}: Element not deleted")

        # Factory Default
        for ip in ALL_DEVICES:
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
                    raise Exception(f"Factory default failed for {ip}")

                device_page.close()
        
        try:
            devices_are_up(ALL_DEVICES, wait_time=WAIT)
        except:
            raise Exception("Devices are not up after factory default")

    results[14] = run_step(14, step_14, logger, report)

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

        test_show_device_events_via_SNMPv3(page, left_panel, logger, report)

        context.close()
        browser.close()
        close_report(report)

    end_time = time.perf_counter()
    print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
    logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")