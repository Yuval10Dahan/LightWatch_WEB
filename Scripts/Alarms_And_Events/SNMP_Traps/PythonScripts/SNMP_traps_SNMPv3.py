"""
Created by: Yuval Dahan
Date: 16/04/2026

SNMP Traps via SNMPv3 Test Script
=====================================================
The Alarms being tested:

Client:
1. Optics Removed
2. Unequipped / Unprovisioned
3. Muxponder Path AIS
4. Optics Loss Propagation
5. Provisioning Mismatch
6. Ethernet Link Failure
7. License Expired or No License Applied
8. Optics Bit Rate Mismatch
9. Optics Loss of Light
10. FarLCS (Far-end Loss of Client Signal)
11. Signal Loss of Lock
12. High BER (Signal Fail)
13. Remote Fault
14. Loss of Synchronization
15. Optical Switch Loss of Signal

Uplink:
1. Optics Removed

*** Runtime: approximately 40 minutes ***
=====================================================

Setup:
 1) 3 devices: 
    - 2x PL2000ADS
    - 1x PL1000IL
    - T.G with 10GigEth-LAN application

 2) Note: The PL1000IL is independent (not connected to the 2 PL2000ADS)

    [Traffic Generator]
        Tx  |  Rx
            |
        Rx  |  Tx
     -----------------------------------------------                     -----------------------------------------------
    |    [Client]                                   |                   |                                               |
    |                 **PL2000ADS**                 |                   |                **PL1000IL**                   |
    |                                   [Uplink]    |                   |                                               |
     -----------------------------------------------                     -----------------------------------------------
                                        Tx  |  Rx
                                            |
                                            |
                                            |
                                        Rx  |  Tx
     -----------------------------------------------
    |                                   [Uplink]    |
    |                 **PL2000ADS**                 |
    |    [Client]                                   |
     -----------------------------------------------
        Tx |   | Rx
           |___|

           (loop)

"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.device_discovery import DeviceDiscovery
from Pages.domain_management import DomainManagement
from Pages.alarms_and_events import AlarmsAndEvents
from PL_Devices.PL_Pages.PL_login_page import PL_LoginPage
from PL_Devices.PL_Pages.PL_main_screen_POM import PL_Main_Screen_POM
from Utils.utils import refresh_page, devices_are_up
from Testing_Equipment.Traffic_Generator.traffic_generator_Basic_Functions import Traffic_Generator
from Testing_Equipment.VIAVI import viavi_Basic_Functions
import time
from time import sleep
from Utils.Logger import create_logger
import sys
from sys import argv
from Utilities.QCreporter import open_report, close_report, step_passed, step_failed
import os
from datetime import datetime, timedelta
import re
from zoneinfo import ZoneInfo


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
    LW_SERVER_HOST_IP  = "172.16.10.22:8080"
    LW_USERNAME = "administrator"
    LW_PASSWORD = "administrator"

    PL2000ADS_IP1 = "172.16.30.15"
    PL2000ADS_IP2 = "172.16.30.16"
    PL1000IL_IP = "172.16.30.13"

    DUT_IP1_NAME = "PL-2000ADS (172.16.30.15)"
    DUT_IP2_NAME = "PL-2000ADS (172.16.30.16)"
    DUT_IP3_NAME = "PL-1000IL2 (172.16.30.13)"

    DEVICE_IP_USER = "tech" 
    DEVICE_IP_PASS = "packetlight"

    NEW_CHASSIS_ID = "67"
    DOMAIN_NAME = "Script_Domain"
    SUB_DOMAIN_NAME = "Script_Sub_Domain" 

    TRAFFIC_GENERATOR_IP = '172.16.10.101'
    TRAFFIC_GENERATOR_APPLICATION = '10GigEth-LAN'
    TRAFFIC_GENERATOR_SLOT = 4
    TRAFFIC_GENERATOR_PORT = 1

    UPLINK_PORT_1 = 19
    UPLINK_PORT_2 = 20
    CLIENT_PORT_1 = 1
    CLIENT_PORT_2 = 2
    


DEVICES_LIST = [PL2000ADS_IP1, PL2000ADS_IP2, PL1000IL_IP]
BASE_URL = f"http://{LW_SERVER_HOST_IP}/"
WAIT = 30
SNMPV3_USERNAME = "admin"
GOOGLE_SNTP_SERVER = '216.239.35.0'
GMT2 = "GMT+2"
WAIT_FOR_ALARM = 15

LOGGER_ROOT_DIRECTORY = 'G:\\Python\\PacketLight Automation\\LightWatch_WEB\\Scripts\\Alarms_And_Events\\SNMP_Traps\\LogFiles'
LOGGER_DIRECTORY_NAME = "SNMP_traps_SNMPv3"
LOG_FILE_NAME = 'SNMP_traps_SNMPv3.log'
REPORT_PATH = None

APPLICATION_LOSS_OF_SYNC = '8GFC'
UPLINK_TYPE_1 = 1
UPLINK_TYPE_2 = 2



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
        
        # Normalize COM ports (e.g., "COM Port #1" -> "COM #1")
        source = re.sub(r"COM\s*Port\s*#(\d+)", r"COM #\1", source, flags=re.IGNORECASE)
        
        return source

    def parse_gui_time(ts: str):
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
    formatted.sort(
        key=lambda x: (
            parse_gui_time(x[0]),
            x[1],
            x[3]
        )
    )
    return formatted

def find_alarm(alarms_list, message, source):
    for a in alarms_list:
        if len(a) >= 4 and a[3] == message and a[1] == source:
            return a
    return None

def compare_alarms(alarm1, alarm2, margin_seconds=30):
    if not alarm1 or not alarm2:
        print(f"Device alarm: {alarm1}")
        print(f"Lightwatch alarm: {alarm2}")
        return False
    
    if len(alarm1) < 4 or len(alarm2) < 4:
        print(f"Device alarm: {alarm1}")
        print(f"Lightwatch alarm: {alarm2}")
        return alarm1 == alarm2

    # Normalize COM ports (e.g., "COM Port #1" -> "COM #1")
    source1 = re.sub(r"COM\s*Port\s*#(\d+)", r"COM #\1", alarm1[1], flags=re.IGNORECASE)
    source2 = re.sub(r"COM\s*Port\s*#(\d+)", r"COM #\1", alarm2[1], flags=re.IGNORECASE)

    if source1 != source2 or alarm1[2] != alarm2[2] or alarm1[3] != alarm2[3]:
        print(f"Device alarm: {alarm1}")
        print(f"Lightwatch alarm: {alarm2}")
        return False
        
    try:
        time1 = datetime.strptime(alarm1[0], "%m/%d/%Y %I:%M:%S %p")
        time2 = datetime.strptime(alarm2[0], "%m/%d/%Y %I:%M:%S %p")
        if abs((time1 - time2).total_seconds()) > margin_seconds:
            print(f"Device alarm: {alarm1}")
            print(f"Lightwatch alarm: {alarm2}")
            return False
    except Exception:
        if alarm1[0] != alarm2[0]:
            print(f"Device alarm: {alarm1}")
            print(f"Lightwatch alarm: {alarm2}")
            return False
            
    return True

def test_SNMP_traps_SNMPv3(page, left_panel: LeftPanel, logger, report):
    domain_management = DomainManagement(page)
    device_discovery = DeviceDiscovery(page)
    alarms_and_events = AlarmsAndEvents(page)
    # tgSession = Traffic_Generator(TRAFFIC_GENERATOR_IP, TRAFFIC_GENERATOR_APPLICATION, TRAFFIC_GENERATOR_SLOT, TRAFFIC_GENERATOR_PORT)
    tgSession = viavi_Basic_Functions.Connect_To_Port(TRAFFIC_GENERATOR_IP, TRAFFIC_GENERATOR_SLOT, TRAFFIC_GENERATOR_PORT)
    viavi_Basic_Functions.load_Predefind_Application(tgSession, TRAFFIC_GENERATOR_APPLICATION)

    results = {}
    saved_alarms = {}

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
        def is_israel_dst():
            israel_time = datetime.now(ZoneInfo("Asia/Jerusalem"))
            return israel_time.dst() != timedelta(0)

        daylight_save = "Enabled" if is_israel_dst() else "Disabled"

        for ip in DEVICES_LIST:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")

            ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            assert ok, f"Login to {ip} GUI failed."

            pl_main_screen = PL_Main_Screen_POM(device_page)

            # set chassis id to empty 
            pl_main_screen.set_chassis_id(" ") 

            pl_main_screen.add_sntp_server(GOOGLE_SNTP_SERVER)
            pl_main_screen.set_sntp_configuration(status="Enabled", gmt=GMT2, daylight_save=daylight_save)
            refresh_page(device_page)

            device_page.close()

    results[3] = run_step(3, step_3, logger, report)

    ############################################################################
    # Step 4 – For each IP, set IP, SNMPv3 username and click Start Discovery. # 
    ############################################################################
    def step_4():
        left_panel.click_device_discovery()
        device_discovery.click_SNMPv3()

        for ip in DEVICES_LIST:
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
                element_name=DUT_IP1_NAME,
                to_mode="new",
                new_chassis_id=NEW_CHASSIS_ID, 
                existing_chassis_id=None,
                parent_chassis=None
            )

        except Exception as e:
            print(f"Failed to change chassis id for {DUT_IP1_NAME}: {e}")
            logger.info(f"Failed to change chassis id for {DUT_IP1_NAME}: {e}")

        try:
            domain_management.change_CHASSIS_ID(
                element_name=DUT_IP2_NAME,
                to_mode="existing",
                new_chassis_id=None, 
                existing_chassis_id=f"Chassis: {NEW_CHASSIS_ID}",
                parent_chassis=None
            )

        except Exception as e:
            print(f"Failed to change chassis id for {DUT_IP2_NAME}: {e}")
            logger.info(f"Failed to change chassis id for {DUT_IP2_NAME}: {e}")

        try:
            domain_management.change_CHASSIS_ID(
                element_name=DUT_IP3_NAME,
                to_mode="existing",
                new_chassis_id=None, 
                existing_chassis_id=f"Chassis: {NEW_CHASSIS_ID}",
                parent_chassis=None
            )

        except Exception as e:
            print(f"Failed to change chassis id for {DUT_IP3_NAME}: {e}")
            logger.info(f"Failed to change chassis id for {DUT_IP3_NAME}: {e}")

        try:
            domain_management.move_to_domain(source_item_name=f"Chassis: {NEW_CHASSIS_ID}/{NEW_CHASSIS_ID}",
             target_domain_name=SUB_DOMAIN_NAME)
        except Exception as e:
            print(f"Failed to move Chassis {NEW_CHASSIS_ID}/{NEW_CHASSIS_ID} to domain {SUB_DOMAIN_NAME}: {e}")
            logger.info(f"Failed to move Chassis {NEW_CHASSIS_ID}/{NEW_CHASSIS_ID} to domain {SUB_DOMAIN_NAME}: {e}")

    results[5] = run_step(5, step_5, logger, report)

    ###########################################################
    # Step 6 – Configure Uplink 1 and Port 1 for each device. # 
    ###########################################################
    def step_6():
        for ip in DEVICES_LIST:
            if ip != "172.16.30.13":
                device_page = page.context.new_page()
                pl_login = PL_LoginPage(device_page)
                pl_login.goto(f"http://{ip}/")
                pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
                pl_main = PL_Main_Screen_POM(device_page)
                
                pl_main.set_admin_status(port_number=str(UPLINK_PORT_1), status="Up")
                pl_main.set_service_type(port_number=str(CLIENT_PORT_1), service_type_value="10GbE-LAN")
                pl_main.set_provisioning(port_number=str(CLIENT_PORT_1), uplink_number=UPLINK_TYPE_1)
                pl_main.set_admin_status(port_number=str(CLIENT_PORT_1), status="Up")
                
                device_page.close()

    results[6] = run_step(6, step_6, logger, report)

    #################################
    # Step 7 – Optics Removed Alarm # 
    #################################
    def step_7():
        refresh_page(page)
        ip = DEVICES_LIST[0]
        device_page = page.context.new_page()
        pl_login = PL_LoginPage(device_page)
        pl_login.goto(f"http://{ip}/")
        pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
        pl_main = PL_Main_Screen_POM(device_page)

        pl_main.set_admin_status(port_number=str(CLIENT_PORT_2), status="Up")
        sleep(WAIT_FOR_ALARM)
        alarms_port_2 = pl_main.get_alarms_table(str(CLIENT_PORT_2))
        saved_alarms['step_7_port_2'] = alarms_port_2
        
        optics_removed_port2_alarm = find_alarm(alarms_port_2, "Optics Removed", "Port 2")
        if not optics_removed_port2_alarm:
            device_page.close()
            raise AssertionError("Alarm 'Optics Removed' on Port 2 doesn't exist on device.")

        saved_alarms['optics_removed_port2_alarm'] = optics_removed_port2_alarm
        # print(f"Optics Removed alarm: {optics_removed_port2_alarm} \n")
        device_page.close()

        left_panel.click_alarms_and_events()
        alarms_and_events.set_faults_type("Alarms")
        alarms_and_events.set_filterBy("Devices")
        alarms_and_events.select_device_filterBy_devices(ip)
        alarms_and_events.close_devices_dropdown()
        
        lw_alarms = alarms_and_events.get_all_alarms()
        lw_formatted = convert_lw_alarms_to_gui_alarms_format(ip, lw_alarms)
        
        lw_optics_removed = find_alarm(lw_formatted, "Optics Removed", "Port 2")
        # print(f"LW Formatted Optics Removed Alarm: {lw_optics_removed} \n")
        if not lw_optics_removed:
            raise AssertionError("Alarm 'Optics Removed' on Port 2 doesn't exist on LW Server.")
            
        if not compare_alarms(saved_alarms['optics_removed_port2_alarm'], lw_optics_removed):
            raise AssertionError("Alarm mismatch between device and LW Server for 'Optics Removed'.")

    results[7] = run_step(7, step_7, logger, report)

    #############################################
    # Step 8 – Unequipped / Unprovisioned Alarm # 
    #############################################
    def step_8():
        try:
            refresh_page(page)
            ip = DEVICES_LIST[0]
            
            alarms_port_2 = saved_alarms.get('step_7_port_2', [])
            unprovisioned_alarm = find_alarm(alarms_port_2, "Unequipped / Unprovisioned", "Port 2")
            if not unprovisioned_alarm:
                raise AssertionError("Alarm 'Unequipped / Unprovisioned' on Port 2 doesn't exist on device.")

            saved_alarms['unprovisioned_port2_alarm'] = unprovisioned_alarm

            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Alarms")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events.close_devices_dropdown()
            
            lw_alarms = alarms_and_events.get_all_alarms()
            lw_formatted = convert_lw_alarms_to_gui_alarms_format(ip, lw_alarms)
            
            lw_unprovisioned = find_alarm(lw_formatted, "Unequipped / Unprovisioned", "Port 2")
            if not lw_unprovisioned:
                raise AssertionError("Alarm 'Unequipped / Unprovisioned' on Port 2 doesn't exist on LW Server.")
                
            if not compare_alarms(saved_alarms['unprovisioned_port2_alarm'], lw_unprovisioned):
                raise AssertionError("Alarm mismatch between device and LW Server for 'Unequipped / Unprovisioned'.")
        
        finally:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)
            pl_main.set_admin_status(port_number=str(CLIENT_PORT_2), status="Down")
            device_page.close()

    results[8] = run_step(8, step_8, logger, report)

    ########################################################################################
    # Step 9 – Muxponder Path AIS + Optics Loss Propagation + Provisioning Mismatch Alarms #
    ########################################################################################
    def step_9():
        try:
            refresh_page(page)
            ip = DEVICES_LIST[0]
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)

            pl_main.set_service_type(port_number=str(CLIENT_PORT_2), service_type_value="10GbE-LAN")
            pl_main.set_provisioning(port_number=CLIENT_PORT_2, uplink_number=UPLINK_TYPE_1)
            pl_main.set_admin_status(port_number=str(CLIENT_PORT_2), status="Up")
            sleep(WAIT_FOR_ALARM)
            alarms_port_2 = pl_main.get_alarms_table(str(CLIENT_PORT_2))

            ais_alarm = find_alarm(alarms_port_2, "Muxponder Path AIS", "Port 2")
            if not ais_alarm:
                device_page.close()
                raise AssertionError("Alarm 'Muxponder Path AIS' on Port 2 doesn't exist on device.")
            saved_alarms['muxponder_path_ais_port2_alarm'] = ais_alarm
            
            loss_alarm = find_alarm(alarms_port_2, "Optics Loss Propagation", "Port 2")
            if not loss_alarm:
                device_page.close()
                raise AssertionError("Alarm 'Optics Loss Propagation' on Port 2 doesn't exist on device.")
            saved_alarms['optics_loss_propagation_port2_alarm'] = loss_alarm
            
            mismatch_alarm = find_alarm(alarms_port_2, "Provisioning Mismatch", "Port 2")
            if not mismatch_alarm:
                device_page.close()
                raise AssertionError("Alarm 'Provisioning Mismatch' on Port 2 doesn't exist on device.")
            saved_alarms['provisioning_mismatch_port2_alarm'] = mismatch_alarm
            device_page.close()

            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Alarms")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events.close_devices_dropdown()
            
            lw_alarms = alarms_and_events.get_all_alarms()
            lw_formatted = convert_lw_alarms_to_gui_alarms_format(ip, lw_alarms)

            lw_ais = find_alarm(lw_formatted, "Muxponder Path AIS", "Port 2")
            if not compare_alarms(saved_alarms['muxponder_path_ais_port2_alarm'], lw_ais):
                raise AssertionError("Alarm mismatch for 'Muxponder Path AIS'.")
                
            lw_loss = find_alarm(lw_formatted, "Optics Loss Propagation", "Port 2")
            if not compare_alarms(saved_alarms['optics_loss_propagation_port2_alarm'], lw_loss):
                raise AssertionError("Alarm mismatch for 'Optics Loss Propagation'.")
                
            lw_mismatch = find_alarm(lw_formatted, "Provisioning Mismatch", "Port 2")
            if not compare_alarms(saved_alarms['provisioning_mismatch_port2_alarm'], lw_mismatch):
                raise AssertionError("Alarm mismatch for 'Provisioning Mismatch'.")

        finally:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)
            pl_main.set_admin_status(port_number=str(CLIENT_PORT_2), status="Down")
            pl_main.remove_provisioning(port_number=str(CLIENT_PORT_2))
            device_page.close()

    results[9] = run_step(9, step_9, logger, report)

    #########################################
    # Step 10 – Ethernet Link Failure Alarm # 
    #########################################
    def step_10():
        try:
            refresh_page(page)
            ip = DEVICES_LIST[0]
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)

            pl_main.set_admin_status(port_number="ETH 2", status="Up")
            sleep(WAIT_FOR_ALARM)
            alarms_eth2 = pl_main.get_alarms_table("ETH 2")
            
            eth_fail_alarm = find_alarm(alarms_eth2, "Ethernet Link Failure", "ETH 2 Port")
            if not eth_fail_alarm:
                device_page.close()
                raise AssertionError("Alarm 'Ethernet Link Failure' doesn't exist on device.")

            saved_alarms['ethernet_link_failure_eth2_alarm'] = eth_fail_alarm
            device_page.close()

            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Alarms")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events.close_devices_dropdown()
            
            lw_alarms = alarms_and_events.get_all_alarms()
            lw_formatted = convert_lw_alarms_to_gui_alarms_format(ip, lw_alarms)
            
            lw_eth_fail = find_alarm(lw_formatted, "Ethernet Link Failure", "ETH 2 Port")
            if not compare_alarms(saved_alarms['ethernet_link_failure_eth2_alarm'], lw_eth_fail):
                raise AssertionError("Alarm mismatch for 'Ethernet Link Failure'.")
        
        finally:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)
            pl_main.set_admin_status(port_number="ETH 2", status="Down")
            device_page.close()

    results[10] = run_step(10, step_10, logger, report)

    #########################################################
    # Step 11 – License Expired or No License Applied Alarm # 
    #########################################################
    def step_11():
        try:
            refresh_page(page)
            ip = DEVICES_LIST[0]
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)

            pl_main.set_service_type(port_number=str(CLIENT_PORT_2), service_type_value="Encrypted 10GbE-LAN")
            sleep(2)
            pl_main.set_admin_status(port_number=str(CLIENT_PORT_2), status="Up")
            sleep(WAIT_FOR_ALARM)
            alarms_port_2 = pl_main.get_alarms_table(str(CLIENT_PORT_2))

            license_alarm = find_alarm(alarms_port_2, "License Expired or No License Applied", "Port 2")
            if not license_alarm:
                device_page.close()
                raise AssertionError("Alarm 'License Expired or No License Applied' doesn't exist on device.")

            saved_alarms['license_expired_port2_alarm'] = license_alarm
            device_page.close()

            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Alarms")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events.close_devices_dropdown()
            
            lw_alarms = alarms_and_events.get_all_alarms()
            lw_formatted = convert_lw_alarms_to_gui_alarms_format(ip, lw_alarms)

            lw_license = find_alarm(lw_formatted, "License Expired or No License Applied", "Port 2")
            if not compare_alarms(saved_alarms['license_expired_port2_alarm'], lw_license):
                raise AssertionError("Alarm mismatch for 'License Expired or No License Applied'.")
        
        finally:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)
            pl_main.set_admin_status(port_number=str(CLIENT_PORT_2), status="Down")
            device_page.close()

    results[11] = run_step(11, step_11, logger, report)

    ############################################
    # Step 12 – Optics Bit Rate Mismatch Alarm # 
    ############################################
    def step_12():
        try:
            refresh_page(page)
            ip = DEVICES_LIST[0]
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)

            pl_main.set_admin_status(port_number=str(CLIENT_PORT_1), status="Down")
            pl_main.remove_provisioning(port_number=str(CLIENT_PORT_1))
            pl_main.set_service_type(port_number=str(CLIENT_PORT_1), service_type_value="16G FC")
            pl_main.set_admin_status(port_number=str(CLIENT_PORT_1), status="Up")
            sleep(WAIT_FOR_ALARM)
            
            alarms_port_1 = pl_main.get_alarms_table(str(CLIENT_PORT_1))
            bit_rate_alarm = find_alarm(alarms_port_1, "Optics Bit Rate Mismatch", "Port 1")
            if not bit_rate_alarm:
                device_page.close()
                raise AssertionError("Alarm 'Optics Bit Rate Mismatch' doesn't exist on device.")

            saved_alarms['optics_bit_rate_mismatch_port1_alarm'] = bit_rate_alarm
            device_page.close()

            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Alarms")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events.close_devices_dropdown()
            
            lw_alarms = alarms_and_events.get_all_alarms()
            lw_formatted = convert_lw_alarms_to_gui_alarms_format(ip, lw_alarms)

            lw_bit_rate = find_alarm(lw_formatted, "Optics Bit Rate Mismatch", "Port 1")
            if not compare_alarms(saved_alarms['optics_bit_rate_mismatch_port1_alarm'], lw_bit_rate):
                raise AssertionError("Alarm mismatch for 'Optics Bit Rate Mismatch'.")
        
        finally:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)
            pl_main.set_admin_status(port_number=str(CLIENT_PORT_1), status="Down")
            pl_main.set_service_type(port_number=str(CLIENT_PORT_1), service_type_value="10GbE-LAN")
            pl_main.set_provisioning(port_number=str(CLIENT_PORT_1), uplink_number=UPLINK_TYPE_1)
            pl_main.set_admin_status(port_number=str(CLIENT_PORT_1), status="Up")
            device_page.close()

    results[12] = run_step(12, step_12, logger, report)

    # ##################################################
    # # Step 13 – Optics Loss of Light + FarLCS Alarms #
    # ##################################################
    def step_13():
        try:
            refresh_page(page)
            for ip in DEVICES_LIST:
                if ip != "172.16.30.13":
                    device_page = page.context.new_page()
                    pl_login = PL_LoginPage(device_page)
                    pl_login.goto(f"http://{ip}/")
                    pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
                    pl_main = PL_Main_Screen_POM(device_page)
                    
                    pl_main.set_admin_status(port_number=str(UPLINK_PORT_1), status="Up")
                    pl_main.set_service_type(port_number=str(CLIENT_PORT_1), service_type_value="10GbE-LAN")
                    pl_main.set_provisioning(port_number=str(CLIENT_PORT_1), uplink_number=UPLINK_TYPE_1)
                    pl_main.set_admin_status(port_number=str(CLIENT_PORT_1), status="Up")
                    
                    device_page.close()

            viavi_Basic_Functions.Set_Laser(tgSession, State='off')
            sleep(WAIT_FOR_ALARM)

            ip = DEVICES_LIST[0]
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)

            alarms_port_1 = pl_main.get_alarms_table(str(CLIENT_PORT_1))
            optics_loss_of_light_port1_alarm = find_alarm(alarms_port_1, "Optics Loss of Light", "Port 1")
            farLCS_port1_alarm = find_alarm(alarms_port_1, "FarLCS (Far-end Loss of Client Signal)", "Port 1")
            
            if not optics_loss_of_light_port1_alarm:
                device_page.close()
                raise AssertionError("Alarm 'Optics Loss of Light' on Port 1 doesn't exist on device.")

            if not farLCS_port1_alarm:
                device_page.close()
                raise AssertionError("Alarm 'FarLCS (Far-end Loss of Client Signal)' on Port 1 doesn't exist on device.")
                
            saved_alarms['optics_loss_of_light_port1_alarm'] = optics_loss_of_light_port1_alarm
            saved_alarms['farLCS_port1_alarm'] = farLCS_port1_alarm
            device_page.close()

            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Alarms")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events.close_devices_dropdown()
            
            lw_alarms = alarms_and_events.get_all_alarms()
            lw_formatted = convert_lw_alarms_to_gui_alarms_format(ip, lw_alarms)
            
            lw_optics_loss = find_alarm(lw_formatted, "Optics Loss of Light", "Port 1")
            if not lw_optics_loss:
                raise AssertionError("Alarm 'Optics Loss of Light' on Port 1 doesn't exist on LW Server.")
            lw_farLCS = find_alarm(lw_formatted, "FarLCS (Far-end Loss of Client Signal)", "Port 1")
            if not lw_farLCS:
                raise AssertionError("Alarm 'FarLCS (Far-end Loss of Client Signal)' on Port 1 doesn't exist on LW Server.")
                
            if not compare_alarms(saved_alarms['optics_loss_of_light_port1_alarm'], lw_optics_loss):
                raise AssertionError("Alarm mismatch between device and LW Server for 'Optics Loss of Light'.")
            if not compare_alarms(saved_alarms['farLCS_port1_alarm'], lw_farLCS):
                raise AssertionError("Alarm mismatch between device and LW Server for 'FarLCS (Far-end Loss of Client Signal)'.")
        
        finally:
            viavi_Basic_Functions.Set_Laser(tgSession, State='on')
            sleep(WAIT_FOR_ALARM)

    results[13] = run_step(13, step_13, logger, report)

    # #######################################
    # # Step 14 – Signal Loss of Lock Alarm #
    # #######################################
    def step_14():
        try:
            refresh_page(page)
            viavi_Basic_Functions.insert_PCS_Alarm(tgSession, Alarm_Type='Loss of Lock')
            sleep(WAIT_FOR_ALARM)

            ip = DEVICES_LIST[0]
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)

            alarms_port_1 = pl_main.get_alarms_table(str(CLIENT_PORT_1))
            signal_loss_of_lock_port1_alarm = find_alarm(alarms_port_1, "Signal Loss of Lock", "Port 1")
            
            if not signal_loss_of_lock_port1_alarm:
                device_page.close()
                raise AssertionError("Alarm 'Signal Loss of Lock' on Port 1 doesn't exist on device.")
                
            saved_alarms['signal_loss_of_lock_port1_alarm'] = signal_loss_of_lock_port1_alarm
            device_page.close()

            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Alarms")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events.close_devices_dropdown()
            
            lw_alarms = alarms_and_events.get_all_alarms()
            lw_formatted = convert_lw_alarms_to_gui_alarms_format(ip, lw_alarms)
            
            lw_signal_loss = find_alarm(lw_formatted, "Signal Loss of Lock", "Port 1")
            if not lw_signal_loss:
                raise AssertionError("Alarm 'Signal Loss of Lock' on Port 1 doesn't exist on LW Server.")
                
            if not compare_alarms(saved_alarms['signal_loss_of_lock_port1_alarm'], lw_signal_loss):
                raise AssertionError("Alarm mismatch between device and LW Server for 'Signal Loss of Lock'.")
        
        finally:
            viavi_Basic_Functions.stop_PCS_Alarm(tgSession)

    results[14] = run_step(14, step_14, logger, report)

    # ############################
    # # Step 15 – High BER Alarm #
    # ############################
    def step_15():
        try:
            refresh_page(page)
            viavi_Basic_Functions.insert_PCS_Alarm(tgSession, Alarm_Type='HIBER')
            sleep(WAIT_FOR_ALARM)
            
            ip = DEVICES_LIST[0]
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)

            alarms_port_1 = pl_main.get_alarms_table(str(CLIENT_PORT_1))
            high_ber_port1_alarm = find_alarm(alarms_port_1, "High BER (Signal Fail)", "Port 1")
            
            if not high_ber_port1_alarm:
                device_page.close()
                raise AssertionError("Alarm 'High BER (Signal Fail)' on Port 1 doesn't exist on device.")
                
            saved_alarms['high_ber_port1_alarm'] = high_ber_port1_alarm
            device_page.close()

            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Alarms")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events.close_devices_dropdown()
            
            lw_alarms = alarms_and_events.get_all_alarms()
            lw_formatted = convert_lw_alarms_to_gui_alarms_format(ip, lw_alarms)
            
            lw_high_ber = find_alarm(lw_formatted, "High BER (Signal Fail)", "Port 1")
            if not lw_high_ber:
                raise AssertionError("Alarm 'High BER (Signal Fail)' on Port 1 doesn't exist on LW Server.")
                
            if not compare_alarms(saved_alarms['high_ber_port1_alarm'], lw_high_ber):
                raise AssertionError("Alarm mismatch between device and LW Server for 'High BER (Signal Fail)'.")
        
        finally:
            viavi_Basic_Functions.stop_PCS_Alarm(tgSession)

    results[15] = run_step(15, step_15, logger, report)

    # #################################
    # # Step 16 – Remote Fault Alarm  #
    # #################################
    def step_16():
        try:
            refresh_page(page)
            viavi_Basic_Functions.insert_100GbE_PCS_Alarm(tgSession, Alarm_Type='Remote Fault')
            sleep(WAIT_FOR_ALARM)
            
            ip = DEVICES_LIST[0]
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)

            alarms_port_1 = pl_main.get_alarms_table(str(CLIENT_PORT_1))
            remote_fault_port1_alarm = find_alarm(alarms_port_1, "Remote Fault", "Port 1")
            
            if not remote_fault_port1_alarm:
                device_page.close()
                raise AssertionError("Alarm 'Remote Fault' on Port 1 doesn't exist on device.")
                
            saved_alarms['remote_fault_port1_alarm'] = remote_fault_port1_alarm
            device_page.close()

            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Alarms")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events.close_devices_dropdown()
            
            lw_alarms = alarms_and_events.get_all_alarms()
            lw_formatted = convert_lw_alarms_to_gui_alarms_format(ip, lw_alarms)
            
            lw_remote_fault = find_alarm(lw_formatted, "Remote Fault", "Port 1")
            if not lw_remote_fault:
                raise AssertionError("Alarm 'Remote Fault' on Port 1 doesn't exist on LW Server.")
                
            if not compare_alarms(saved_alarms['remote_fault_port1_alarm'], lw_remote_fault):
                raise AssertionError("Alarm mismatch between device and LW Server for 'Remote Fault'.")
        
        finally:
            viavi_Basic_Functions.stop_PCS_Alarm(tgSession)

    results[16] = run_step(16, step_16, logger, report)

    # ###########################################
    # # Step 17 – Loss of Synchronization Alarm #
    # ###########################################
    def step_17():
        try:
            refresh_page(page)
            viavi_Basic_Functions.load_Predefind_Application(tgSession, APPLICATION_LOSS_OF_SYNC)
            sleep(WAIT_FOR_ALARM)
            
            ip = DEVICES_LIST[0]
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)

            alarms_port_1 = pl_main.get_alarms_table(str(CLIENT_PORT_1))
            loss_of_sync_port1_alarm = find_alarm(alarms_port_1, "Loss of Synchronization", "Port 1")
            
            if not loss_of_sync_port1_alarm:
                device_page.close()
                raise AssertionError("Alarm 'Loss of Synchronization' on Port 1 doesn't exist on device.")
                
            saved_alarms['loss_of_sync_port1_alarm'] = loss_of_sync_port1_alarm
            device_page.close()

            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Alarms")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events.close_devices_dropdown()
            
            lw_alarms = alarms_and_events.get_all_alarms()
            lw_formatted = convert_lw_alarms_to_gui_alarms_format(ip, lw_alarms)
            
            lw_loss_of_sync = find_alarm(lw_formatted, "Loss of Synchronization", "Port 1")
            if not lw_loss_of_sync:
                raise AssertionError("Alarm 'Loss of Synchronization' on Port 1 doesn't exist on LW Server.")
                
            if not compare_alarms(saved_alarms['loss_of_sync_port1_alarm'], lw_loss_of_sync):
                raise AssertionError("Alarm mismatch between device and LW Server for 'Loss of Synchronization'.")
        
        finally:
            viavi_Basic_Functions.load_Predefind_Application(tgSession, TRAFFIC_GENERATOR_APPLICATION)
            sleep(WAIT_FOR_ALARM)

    results[17] = run_step(17, step_17, logger, report)

    # ###############################################
    # # Step 18 – Optical Switch Loss of Signal     #
    # ###############################################
    def step_18():
        try:
            refresh_page(page)
            
            ip = DEVICES_LIST[2]
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)

            pl_main.set_admin_status(port_number="COM", status="Up")
            sleep(WAIT_FOR_ALARM)

            alarms_com = pl_main.get_alarms_table("COM")
            optical_switch_COM_alarm = find_alarm(alarms_com, "Optical Switch Loss of Signal", "COM Port #1")
            
            if not optical_switch_COM_alarm:
                device_page.close()
                raise AssertionError("Alarm 'Optical Switch Loss of Signal' on COM Port #1 doesn't exist on device.")
                
            saved_alarms['optical_switch_COM_alarm'] = optical_switch_COM_alarm
            device_page.close()

            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Alarms")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events.close_devices_dropdown()
            
            lw_alarms = alarms_and_events.get_all_alarms()
            lw_formatted = convert_lw_alarms_to_gui_alarms_format(ip, lw_alarms)
            
            lw_optical_switch = find_alarm(lw_formatted, "Optical Switch Loss of Signal", f"{ip} COM #1")
            if not lw_optical_switch:
                lw_optical_switch = find_alarm(lw_formatted, "Optical Switch Loss of Signal", "COM #1")
                
            if not lw_optical_switch:
                raise AssertionError("Alarm 'Optical Switch Loss of Signal' doesn't exist on LW Server.")
                
            if not compare_alarms(saved_alarms['optical_switch_COM_alarm'], lw_optical_switch):
                raise AssertionError("Alarm mismatch between device and LW Server for 'Optical Switch Loss of Signal'.")
        
        finally:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)
            pl_main.set_admin_status(port_number="COM", status="Down")
            device_page.close()

    results[18] = run_step(18, step_18, logger, report)

    # ###########################################
    # # Step 19 – Uplink check - Optics Removed #
    # ###########################################
    def step_19():
        try:
            refresh_page(page)
            
            ip = DEVICES_LIST[0]
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)

            pl_main.set_admin_status(port_number=UPLINK_PORT_2, status="Up")
            sleep(WAIT_FOR_ALARM)

            alarms_uplink_2 = pl_main.get_alarms_table(str(UPLINK_PORT_2))
            optics_removed_uplink_alarm = find_alarm(alarms_uplink_2, "Optics Removed", f"Uplink {UPLINK_TYPE_2}")
            
            if not optics_removed_uplink_alarm:
                device_page.close()
                raise AssertionError("Alarm 'Optics Removed' on Uplink 2 doesn't exist on device.")
                
            saved_alarms['optics_removed_uplink_alarm'] = optics_removed_uplink_alarm
            device_page.close()

            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Alarms")
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events.close_devices_dropdown()
            
            lw_alarms = alarms_and_events.get_all_alarms()
            lw_formatted = convert_lw_alarms_to_gui_alarms_format(ip, lw_alarms)
            
            lw_optics_removed = find_alarm(lw_formatted, "Optics Removed", "Uplink 2")
                
            if not lw_optics_removed:
                raise AssertionError("Alarm 'Optics Removed' on Uplink 2 doesn't exist on LW Server.")
                
            if not compare_alarms(saved_alarms['optics_removed_uplink_alarm'], lw_optics_removed):
                raise AssertionError("Alarm mismatch between device and LW Server for 'Optics Removed'.")
        
        finally:
            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            pl_main = PL_Main_Screen_POM(device_page)
            pl_main.set_admin_status(port_number=UPLINK_PORT_2, status="Down")
            device_page.close()

    results[19] = run_step(19, step_19, logger, report)

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
    logger = None
    report = None
    
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

        test_SNMP_traps_SNMPv3(page, left_panel, logger, report)

        context.close()
        browser.close()
        close_report(report)

    end_time = time.perf_counter()
    print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
    logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
