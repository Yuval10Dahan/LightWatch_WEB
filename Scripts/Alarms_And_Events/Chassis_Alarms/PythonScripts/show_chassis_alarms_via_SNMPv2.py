"""
Created by: Yuval Dahan
Date: 28/04/2026

Comprehensive Alarms Test - Show Chassis Alarms via SNMPv2
=====================================================
Tests the Chassis Alarms using SNMPv2.

*** Runtime: approximately 20 minutes ***
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
from Pages.network_topology import NetworkTopology
from Pages.domain_management import DomainManagement
from Pages.alarms_and_events import AlarmsAndEvents
from Pages.upper_panel import UpperPanel
from PL_Devices.PL_Pages.PL_login_page import PL_LoginPage
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

   DEVICES_LIST = ['172.16.30.13', '172.16.30.15', '172.16.30.16', '172.16.20.126']
   DEVICE_IP_USER = "tech" 
   DEVICE_IP_PASS = "packetlight"

   NEW_CHASSIS_ID = "67"
   DOMAIN_NAME = "ScriptDomain"


# ================================================================
# Values that should not be changed
# ================================================================

BASE_URL = f"http://{LW_SERVER_HOST_IP}/"
WAIT = 30

GOOGLE_SNTP_SERVER = '216.239.35.0'
GMT2 = "GMT+2"

CHASSIS_NAME = "Chassis: 67"

LOGGER_ROOT_DIRECTORY = 'G:\\Python\\PacketLight Automation\\LightWatch_WEB\\Scripts\\Alarms_And_Events\\Chassis_Alarms\\LogFiles'
LOGGER_DIRECTORY_NAME = "show_chassis_alarms_via_SNMPv2"
LOG_FILE_NAME = 'show_chassis_alarms_via_SNMPv2.log'
REPORT_PATH = None



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

def convert_map_chassis_alarms_to_alarms_and_events_chassis_alarms(map_chassis_alarms: list) -> list:
    """
    Convert creation_timestamp and detection_timestamp in map_chassis_alarms
    to be formatted exactly as alarms_and_events_chassis_alarms.
    """
    def format_timestamp(ts: str) -> str:
        if not ts:
            return ts
        try:
            # Try parsing with seconds: "Apr 28, 2026 18:57:56"
            dt = datetime.strptime(ts, "%b %d, %Y %H:%M:%S")
        except ValueError:
            try:
                # Try parsing without seconds: "Apr 28, 2026 11:58"
                dt = datetime.strptime(ts, "%b %d, %Y %H:%M")
            except ValueError:
                return ts
        
        # Return in DD.MM.YYYY, HH:MM:SS format
        return dt.strftime("%d.%m.%Y, %H:%M:%S")

    converted_alarms = []
    for alarm in map_chassis_alarms:
        new_alarm = dict(alarm)
        new_alarm['creation_timestamp'] = format_timestamp(alarm.get('creation_timestamp', ''))
        new_alarm['detection_timestamp'] = format_timestamp(alarm.get('detection_timestamp', ''))
        converted_alarms.append(new_alarm)
        
    return converted_alarms

def compare_map_chassis_alarms_and_alarms_and_events_chassis_alarms(chassis: str, map_alarms: list, lw_alarms: list, section: str | None = None) -> bool:
    """
    Compare map alarms to LW alarms.
    Fields to compare: message, source, category, creation_timestamp, detection_timestamp
    """
    def normalize_time(ts: str) -> str:
        if not ts:
            return ts
        try:
            # Expected format: DD.MM.YYYY, HH:MM:SS (after conversion)
            dt = datetime.strptime(ts, "%d.%m.%Y, %H:%M:%S")
            # Return up to minutes to ignore seconds during comparison
            return dt.strftime("%d.%m.%Y, %H:%M")
        except Exception:
            return ts

    if len(map_alarms) != len(lw_alarms):
        print(f"[{chassis}] Alarms count mismatch: map_chassis_alarms={len(map_alarms)}, alarms_and_events={len(lw_alarms)}")
        return False

    all_matched = True
    
    def sort_key(a):
        return (normalize_time(a.get('creation_timestamp', '')), a.get('message', ''), a.get('source', ''))
        
    sorted_map = sorted(map_alarms, key=sort_key)
    sorted_lw = sorted(lw_alarms, key=sort_key)

    for i in range(len(sorted_map)):
        map_a = sorted_map[i]
        lw_a = sorted_lw[i]

        map_creation = normalize_time(map_a.get('creation_timestamp', ''))
        lw_creation = normalize_time(lw_a.get('creation_timestamp', ''))
        
        map_detection = normalize_time(map_a.get('detection_timestamp', ''))
        lw_detection = normalize_time(lw_a.get('detection_timestamp', ''))

        if not (
            map_a.get('message') == lw_a.get('message') and
            map_a.get('source') == lw_a.get('source') and
            map_a.get('category') == lw_a.get('category') and
            map_creation == lw_creation and
            map_detection == lw_detection
        ):
            if section:
                print(f"[{chassis}] Alarm mismatch at index {i} in {section}:")
            else:
                print(f"[{chassis}] Alarm mismatch at index {i}:")
            print(f"  map_chassis_alarms: message={map_a.get('message')}, source={map_a.get('source')}, category={map_a.get('category')}, creation={map_creation}, detection={map_detection}")
            print(f"  alarms_and_events:  message={lw_a.get('message')}, source={lw_a.get('source')}, category={lw_a.get('category')}, creation={lw_creation}, detection={lw_detection}")
            all_matched = False
            break

    return all_matched

def extract_device_name_and_device_ip(device_str: str) -> tuple:
    """
    Extract device name and IP from string like:
    'PL-1000IL2 (172.16.30.13)' -> ('PL-1000IL2', '172.16.30.13')
    """
    try:
        device_name = device_str.split('(')[0].strip()
        device_ip = device_str.split('(')[-1].split(')')[0].strip()
        return device_name, device_ip
    except:
        return device_str, ""

def adjust_chassis_list(element_list):
    chassis_list = []
    for elem in element_list:
        if "Chassis" in elem:
            chassis_list.append(elem.split('/')[0].strip())
    return chassis_list

def get_elements_per_chassis(element_list):
    elements_per_chassis = {}
    current_chassis = None
    for elem in element_list:
        if "Chassis" in elem:
            current_chassis = elem.split('/')[0].strip()
            elements_per_chassis[current_chassis] = []
        else:
            if current_chassis:
                _, ip = extract_device_name_and_device_ip(elem)
                if ip:
                    elements_per_chassis[current_chassis].append(ip)
    return elements_per_chassis

def test_show_chassis_alarms_via_SNMPv2(page, left_panel: LeftPanel, logger, report):
    domain_management = DomainManagement(page)
    device_discovery = DeviceDiscovery(page)
    alarms_and_events = AlarmsAndEvents(page)
    network_topology = NetworkTopology(page)
    upper_panel = UpperPanel(page)

    results = {}
    global_state = {'chassis_list': [], 'map_chassis_alarms': {}, 'elements_per_chassis': {}}

    ######################## 
    # Step 1 – Add domain. #
    ########################
    def step_1():
        left_panel.click_domain_management()
        domain_management.add_domain("ScriptDomain")
        sleep(0.5)

    results[1] = run_step(1, step_1, logger, report)

    ###################################################
    # Step 2 – Factory default reset for all devices. # 
    ###################################################
    def step_2():
        for ip in DEVICES_LIST:
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
        devices_are_up(DEVICES_LIST, wait_time=WAIT)

    results[2] = run_step(2, step_2, logger, report)

    ################################################################################
    # Step 3 – Login to the GUI of each IP.                                        #
    # Set SNTP server and timezone to synchronize device time with LW server time. #                                   
    ################################################################################
    def step_3():
        for ip in DEVICES_LIST:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            assert ok, f"Login to {ip} GUI failed."

            pl_main_screen = PL_Main_Screen_POM(device_page)
            pl_main_screen.set_chassis_id("")
            pl_main_screen.add_sntp_server(GOOGLE_SNTP_SERVER)
            pl_main_screen.set_sntp_configuration(status="Enabled", gmt=GMT2)
            refresh_page(device_page)
            device_page.close()

    results[3] = run_step(3, step_3, logger, report)

    #############################################################
    # Step 4 – For each IP, set IP and click Start Discovery.   # 
    #############################################################
    def step_4():
        left_panel.click_device_discovery()
        device_discovery.click_SNMPv2()

        for ip in DEVICES_LIST:
           device_discovery.set_ip_address(ip)
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
        for ip in DEVICES_LIST:
            if ip == DEVICES_LIST[0]:
                domain_management.change_CHASSIS_ID(
                    element_name=ip,
                    to_mode="new",
                    new_chassis_id="67",
                    existing_chassis_id=None,
                    parent_chassis=None
                )
            else:
                domain_management.change_CHASSIS_ID(
                   element_name=ip,
                   to_mode="existing",
                   new_chassis_id=None,
                   existing_chassis_id="Chassis: 67",
                   parent_chassis=None
                )
        
        refresh_page(page)
        domain_management.move_to_domain(source_item_name="Chassis: 67/67", target_domain_name="ScriptDomain")

    results[5] = run_step(5, step_5, logger, report)

    # #############################################################################
    # Step 6 - Validate that alarms displayed for each chassis in Management Map. #
    # Match the corresponding alarms shown in Alarms & Events.                    #
    ###############################################################################
    def step_6():
        left_panel.click_network_topology()
        network_topology.show_navigation_info()
        element_list = network_topology.get_navigation_info_elements_list(visible_only=True)
        chassis_list = adjust_chassis_list(element_list)
        global_state['chassis_list'] = chassis_list
        network_topology.hide_navigation_info()

        for chassis in chassis_list:
            network_topology.click_on_element_via_the_map(element_name=chassis)
            network_topology.element_details_click_on_faults()
         
            map_chassis_alarms = network_topology.element_details_faults_get_all_alarms()
            map_chassis_alarms = convert_map_chassis_alarms_to_alarms_and_events_chassis_alarms(map_chassis_alarms)
            global_state['map_chassis_alarms'][chassis] = map_chassis_alarms
         
            network_topology.element_details_faults_view_all_alarms()
            alarms_and_events_chassis_alarms = alarms_and_events.get_all_alarms()
         
            if not compare_map_chassis_alarms_and_alarms_and_events_chassis_alarms(chassis, map_chassis_alarms, alarms_and_events_chassis_alarms):
               raise AssertionError(f"Alarms mismatch for {chassis} in Step 6")

            left_panel.click_network_topology()

    results[6] = run_step(6, step_6, logger, report)

    #######################################################################################
    # Step 7 - Validate chassis alarms using the Domain/Chassis filter in Alarms & Events #
    # and compare them against Management Map chassis alarms for each chassis.            #
    #######################################################################################
    def step_7():
        left_panel.click_network_topology()
        refresh_page(page)
        network_topology.show_navigation_info()
        element_list = network_topology.get_navigation_info_elements_list(visible_only=False)
      
        elements_per_chassis = get_elements_per_chassis(element_list)
        global_state['elements_per_chassis'] = elements_per_chassis

        network_topology.hide_navigation_info()

        chassis_list = global_state['chassis_list']
        chassis_alarms_list = {c: [] for c in chassis_list}

        for chassis in chassis_list:
            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Alarms")
            alarms_and_events.set_filterBy("Domain/Chassis")
            alarms_and_events.select_domain_or_chassis_filterBy_domain_or_chassis(chassis)
               
            alarms = alarms_and_events.get_all_alarms()
            chassis_alarms_list[chassis] = alarms
      
            map_alarms = global_state['map_chassis_alarms'].get(chassis, [])
            if not compare_map_chassis_alarms_and_alarms_and_events_chassis_alarms(chassis, map_alarms, chassis_alarms_list[chassis], section="Step 7"):
                raise AssertionError(f"Alarms mismatch for {chassis} in Step 7")

    results[7] = run_step(7, step_7, logger, report)

    ###############################################################################
    # Step 8 - Select other domain and validate chassis alarms in Alarms & Events #
    # and compare them against Management Map chassis alarms for each chassis.    #
    ###############################################################################
    def step_8():
        domain_name = "ScriptDomain"
        left_panel.click_network_topology()
        upper_panel.select_domain(domain_name)
        
        network_topology.show_navigation_info()
        element_list = network_topology.get_navigation_info_elements_list(visible_only=False)
        elements_per_chassis = get_elements_per_chassis(element_list)
        network_topology.hide_navigation_info()

        chassis = CHASSIS_NAME
        new_domain_chassis_alarms_list = {f'{chassis}': []}

        network_topology.click_on_element_via_the_map(element_name=chassis)
        network_topology.element_details_click_on_faults()
        map_chassis_alarms = network_topology.element_details_faults_get_all_alarms()
        map_chassis_alarms = convert_map_chassis_alarms_to_alarms_and_events_chassis_alarms(map_chassis_alarms)
        
        for ip in elements_per_chassis[chassis]:
            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Alarms")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events_ip_alarms = alarms_and_events.get_all_alarms()
            new_domain_chassis_alarms_list[chassis].extend(alarms_and_events_ip_alarms)
            alarms_and_events.remove_device_filterBy_devices(ip)
            refresh_page(page)
            
        if not compare_map_chassis_alarms_and_alarms_and_events_chassis_alarms(chassis, map_chassis_alarms, new_domain_chassis_alarms_list[chassis]):
            raise AssertionError(f"Alarms mismatch for {chassis} in Step 8")

    results[8] = run_step(8, step_8, logger, report)

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

        test_show_chassis_alarms_via_SNMPv2(page, left_panel, logger, report)

        context.close()
        browser.close()
        close_report(report)

    end_time = time.perf_counter()
    print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
    logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")