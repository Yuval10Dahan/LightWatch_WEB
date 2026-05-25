"""
Created by: Yuval Dahan
Date: 07/05/2026

Comprehensive Non PacketLight Devices Test - ICMP/SNMPv2/SNMPv3
=====================================================
Tests the Non-PacketLight Devices (such as Computers, Switches) using ICMP/SNMPv2/SNMPv3.

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
from Pages.network_topology import NetworkTopology
from Pages.domain_management import DomainManagement
from Pages.alarms_and_events import AlarmsAndEvents
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
from datetime import datetime, timedelta


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

   DEVICE_IP_USER = "tech" 
   DEVICE_IP_PASS = "packetlight"



BASE_URL = f"http://{LW_SERVER_HOST_IP}/"
WAIT = 30

NON_PL_DEVICE_SNMPV2 = "172.16.10.22"
NON_PL_DEVICE_SNMPV3 = "172.16.30.253"
NON_PL_DEVICE_PC = "172.16.10.13"
NON_PL_DEVICE_SWITCH = "172.16.30.253"
NON_PL_DEVICE_WEBSITE = "172.16.10.101"
PL_DEVICE_ICMP = "172.16.30.111" 

LOGGER_ROOT_DIRECTORY = 'G:\\Python\\PacketLight Automation\\LightWatch_WEB\\Scripts\\Alarms_And_Events\\Non_PacketLight_Devices\\LogFiles'
LOGGER_DIRECTORY_NAME = "non_pl_devices"
LOG_FILE_NAME = 'non_pl_devices.log'
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

def test_non_pl_devices(page, left_panel: LeftPanel, logger, report):
   domain_management = DomainManagement(page)
   device_discovery = DeviceDiscovery(page)
   alarms_and_events = AlarmsAndEvents(page)
   network_topology = NetworkTopology(page)

   results = {}

   def verify_element_added(element_name):
      left_panel.click_network_topology()
      network_topology.show_navigation_info()
      element_list = network_topology.get_navigation_info_elements_list(visible_only=True)
      if element_name in element_list:
         return True
      return False

   def verify_events_created(element_ip, expected_events):
      left_panel.click_alarms_and_events()
      alarms_and_events.set_faults_type("Events")
      alarms_and_events.set_filterBy("Devices")
      alarms_and_events.select_device_filterBy_devices(element_ip)
      to_date_str = alarms_and_events.get_to_date()

      def parse_date(date_string):
         for fmt in ("%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%d/%m/%Y %I:%M:%S %p", "%m/%d/%Y %I:%M:%S %p", "%Y-%m-%d %H:%M:%S"):
            try:
               return datetime.strptime(date_string, fmt), fmt
            except ValueError:
               pass
         raise ValueError(f"Could not parse date {date_string}")
        
      try:
         to_dt, fmt = parse_date(to_date_str)
         from_dt = to_dt - timedelta(minutes=10)
         alarms_and_events.set_from_date(from_dt.strftime("%Y-%m-%d %H:%M:%S"))
      except Exception as e:
         print(f"Could not parse or set date: {e}")
            
      element_events = alarms_and_events.get_all_events()
      actual_messages = [event.get('message', event.get('Message', '')) for event in element_events]
      for exp in expected_events:
         if not any(exp in msg for msg in actual_messages):
            print(f"Event not found: {exp}")
            return False
      return True

   def verify_element_is_green(element_name: str | None = None, element_ip: str | None = None, logger=logger):
      left_panel.click_network_topology()
      if element_name:
         state, color = network_topology.get_map_element_color(element_name=element_name)
         if state != "positive" or color != "green":
            print(f"IP {element_name}: Element color is not green: {color}")
            logger.info(f"IP {element_name}: Element color is not green: {color}")
            return False
      if element_ip:
         state, color = network_topology.get_map_element_color(element_ip=element_ip)
         if state != "positive" or color != "green":
            print(f"IP {element_ip}: Element color is not green: {color}")
            logger.info(f"IP {element_ip}: Element color is not green: {color}")
            return False
      return True

   #############################################################
   # Step 1 – Discovering a non-PacketLight device with SNMPv2 # 
   #############################################################
   def step_1():
      expected_events = [f"Discovery for ({NON_PL_DEVICE_SNMPV2}) started", 
      f"New SNMP device is detected {NON_PL_DEVICE_SNMPV2}", f"Device is reachable {NON_PL_DEVICE_SNMPV2}", 
      f"Discovery for ({NON_PL_DEVICE_SNMPV2}) completed"]

      element_name = f"NOT A PACKETLIGHT DEVICE({NON_PL_DEVICE_SNMPV2})"
      
      left_panel.click_device_discovery()
      device_discovery.click_SNMPv2()
      device_discovery.set_ip_address(NON_PL_DEVICE_SNMPV2)
      device_discovery.set_SNMPv2_read_community("public")
      device_discovery.set_SNMPv2_write_community("public")
      device_discovery.set_SNMPv2_admin_community("public")
      device_discovery.click_start_discovery()
      refresh_page(page)
        
      if not verify_element_added(element_name):
         raise AssertionError(f"{element_name} not added")
        
      if not verify_events_created(NON_PL_DEVICE_SNMPV2, expected_events):
         raise AssertionError(f"Expected events not found for {NON_PL_DEVICE_SNMPV2}")
            
      if not verify_element_is_green(element_name=element_name, logger=logger):
         raise AssertionError(f"{element_name} is not green")

   results[1] = run_step(1, step_1, logger, report)
   
   ################################################################
   # Step 2 – Discovering a non-PacketLight device with ICMP - PC #
   # Trying to discovery the same device again.                   # 
   ################################################################
   def step_2():
      expected_events = [f"New SNMP device is detected {NON_PL_DEVICE_PC}", f"Device is reachable {NON_PL_DEVICE_PC}"]
      element_name = NON_PL_DEVICE_PC
      left_panel.click_device_discovery()
      device_discovery.click_ICMP()
      device_discovery.set_ip_address(NON_PL_DEVICE_PC)
      device_discovery.click_start_discovery(is_icmp=True)
      refresh_page(page)
        
      if not verify_element_added(element_name):
         raise AssertionError(f"{element_name} not added")
        
      if not verify_events_created(NON_PL_DEVICE_PC, expected_events):
         raise AssertionError(f"Expected events not found for {NON_PL_DEVICE_PC}")
            
      if not verify_element_is_green(element_ip=NON_PL_DEVICE_PC, logger=logger):
         raise AssertionError(f"{element_name} is not green")

      # Trying to discovery the same device again
      left_panel.click_device_discovery()
      device_discovery.click_ICMP()
      device_discovery.set_ip_address(NON_PL_DEVICE_PC)
      device_discovery.click_start_discovery(is_icmp=True)
      refresh_page(page)

      expected_event_after_discovery_again = [f"Discovery failed for {NON_PL_DEVICE_PC} - device with the same IP exist"]
      if not verify_events_created(NON_PL_DEVICE_PC, expected_event_after_discovery_again):
         raise AssertionError(f"Expected event not found for {NON_PL_DEVICE_PC} after trying to discovery it again.")

   results[2] = run_step(2, step_2, logger, report)
   
   ####################################################################
   # Step 3 – Discovering a non-PacketLight device with ICMP - Switch # 
   ####################################################################
   def step_3():
      expected_events = [f"New SNMP device is detected {NON_PL_DEVICE_SWITCH}", f"Device is reachable {NON_PL_DEVICE_SWITCH}"]
      element_name = NON_PL_DEVICE_SWITCH
      left_panel.click_device_discovery()
      device_discovery.click_ICMP()
      device_discovery.set_ip_address(NON_PL_DEVICE_SWITCH)
      device_discovery.click_start_discovery(is_icmp=True)
      refresh_page(page)
        
      if not verify_element_added(element_name):
         raise AssertionError(f"{element_name} not added")
        
      if not verify_events_created(NON_PL_DEVICE_SWITCH, expected_events):
         raise AssertionError(f"Expected events not found for {NON_PL_DEVICE_SWITCH}")
            
      if not verify_element_is_green(element_ip=element_name, logger=logger):
         raise AssertionError(f"{element_name} is not green")

      left_panel.click_domain_management()
      domain_management.remove_device(element_name, parent_domain_name="Default")

   results[3] = run_step(3, step_3, logger, report)
   
   #####################################################################
   # Step 4 – Discovering a non-PacketLight device with ICMP - Website # 
   #####################################################################
   def step_4():
      expected_events = [f"New SNMP device is detected {NON_PL_DEVICE_WEBSITE}", f"Device is reachable {NON_PL_DEVICE_WEBSITE}"]
      element_name = NON_PL_DEVICE_WEBSITE
      left_panel.click_device_discovery()
      device_discovery.click_ICMP()
      device_discovery.set_ip_address(NON_PL_DEVICE_WEBSITE)
      device_discovery.click_start_discovery(is_icmp=True)
      refresh_page(page)
        
      if not verify_element_added(element_name):
         raise AssertionError(f"{element_name} not added")
        
      if not verify_events_created(NON_PL_DEVICE_WEBSITE, expected_events):
         raise AssertionError(f"Expected events not found for {NON_PL_DEVICE_WEBSITE}")
            
      if not verify_element_is_green(element_ip=element_name, logger=logger):
         raise AssertionError(f"{element_name} is not green")

   results[4] = run_step(4, step_4, logger, report)
   
   ######################################################################
   # Step 5 – Discovering a non-PacketLight device with SNMPv3 - Switch # 
   ######################################################################
   def step_5():
      expected_events = [f"Device is reachable {NON_PL_DEVICE_SNMPV3}", 
      f"New SNMPv3 device is detected {NON_PL_DEVICE_SNMPV3}",
      "PM protocol set: SNMP"]
      element_name = NON_PL_DEVICE_SNMPV3
      left_panel.click_device_discovery()
      device_discovery.click_SNMPv3()
      device_discovery.set_ip_address(NON_PL_DEVICE_SNMPV3)
      device_discovery.set_SNMPv3_user_name("test")
      device_discovery.set_SNMPv3_security_level("Authentication, Privacy")
      device_discovery.set_SNMPv3_authentication_protocol("SHA-1")
      device_discovery.set_SNMPv3_authentication_password("Z@qqaz$$")
      device_discovery.set_SNMPv3_privacy_protocol("AES-128")
      device_discovery.set_SNMPv3_privacy_password("Z@qqaz$$")
      device_discovery.click_start_discovery()
      refresh_page(page)
        
      if not verify_element_added(element_name):
         raise AssertionError(f"{element_name} not added")
        
      if not verify_events_created(NON_PL_DEVICE_SNMPV3, expected_events):
         raise AssertionError(f"Expected events not found for {NON_PL_DEVICE_SNMPV3}")
            
      if not verify_element_is_green(element_ip=NON_PL_DEVICE_SNMPV3, logger=logger):
         raise AssertionError(f"{element_name} is not green")

   results[5] = run_step(5, step_5, logger, report)
   
   #######################################################
   # Step 6 – Discovering a PacketLight device with ICMP # 
   #######################################################
   def step_6():
      expected_events = [f"New SNMP device is detected {PL_DEVICE_ICMP}", f"Device is reachable {PL_DEVICE_ICMP}"]
      element_name = PL_DEVICE_ICMP
      left_panel.click_device_discovery()
      device_discovery.click_ICMP()
      device_discovery.set_ip_address(PL_DEVICE_ICMP)
      device_discovery.click_start_discovery(is_icmp=True)
      refresh_page(page)
        
      if not verify_element_added(element_name):
         raise AssertionError(f"{element_name} not added")
        
      if not verify_events_created(PL_DEVICE_ICMP, expected_events):
         raise AssertionError(f"Expected events not found for {PL_DEVICE_ICMP}")
            
      if not verify_element_is_green(element_ip=element_name, logger=logger):
         raise AssertionError(f"{element_name} is not green")
            
      left_panel.click_domain_management()
      domain_management.remove_device(device_name_or_ip=element_name)

   results[6] = run_step(6, step_6, logger, report)
   
   ###############################################################
   # Step 7 – Verify ICMP discovery failure while device is down # 
   ###############################################################
   def step_7():
      expected_events = [f"Discovery failed for {PL_DEVICE_ICMP} - ICMP ping failed"]
      element_name = PL_DEVICE_ICMP
        
      device_page = page.context.new_page()
      pl_login = PL_LoginPage(device_page)
      pl_login.goto(f"http://{PL_DEVICE_ICMP}/")
      pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
      pl_main = PL_Main_Screen_POM(device_page)
      pl_main.device_restart("factory")
      device_page.close()
        
      sleep(45)
        
      left_panel.click_device_discovery()
      device_discovery.click_ICMP()
      device_discovery.set_ip_address(PL_DEVICE_ICMP)
      device_discovery.click_start_discovery(is_icmp=True)
      refresh_page(page)
        
      if verify_element_added(element_name):
         raise AssertionError(f"{element_name} was added but it should not be")
            
      devices_are_up([PL_DEVICE_ICMP], wait_time=WAIT)
        
      left_panel.click_device_discovery()
      device_discovery.click_ICMP()
      device_discovery.set_ip_address(PL_DEVICE_ICMP)
      device_discovery.click_start_discovery(is_icmp=True)
      refresh_page(page)
        
      if not verify_events_created(PL_DEVICE_ICMP, expected_events):
         raise AssertionError(f"Expected events not found for {PL_DEVICE_ICMP}")

   results[7] = run_step(7, step_7, logger, report)

   print("\n" + "=" * 60)
   all_passed = all(results.values())
   failed_steps = [str(k) for k, v in results.items() if not v]
   if all_passed:
      print("TEST PASSED \u2705")
      logger.info(f"TEST PASSED")
   else:
      print(f"TEST FAILED \u274c  Failed steps: {', '.join(failed_steps)}")
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

      test_non_pl_devices(page, left_panel, logger, report)

      context.close()
      browser.close()
      close_report(report)

   end_time = time.perf_counter()
   print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
   logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")