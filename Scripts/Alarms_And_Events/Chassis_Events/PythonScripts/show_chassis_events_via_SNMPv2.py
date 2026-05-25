"""
Created by: Yuval Dahan
Date: 04/05/2026

Comprehensive Events Test - Show Chassis Events via SNMPv2
=====================================================
Tests the Chassis Events using SNMPv2.

*** Runtime: approximately 60 minutes ***
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
import re
from datetime import timedelta

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

LOGGER_ROOT_DIRECTORY = 'G:\\Python\\PacketLight Automation\\LightWatch_WEB\\Scripts\\Alarms_And_Events\\Chassis_Events\\LogFiles'
LOGGER_DIRECTORY_NAME = "show_chassis_events_via_SNMPv2"
LOG_FILE_NAME = 'show_chassis_events_via_SNMPv2.log'
REPORT_PATH = None

DEFAULT_DOMAIN_NAME = "Default"

 

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

def convert_map_chassis_events_to_alarms_and_events_chassis_events(map_chassis_events: list) -> list:
   """
   Convert creation_timestamp and detection_timestamp in map_chassis_events
   to be formatted exactly as alarms_and_events_chassis_events.
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

   converted_events = []
   for event in map_chassis_events:
      new_event = dict(event)
      new_event['creation_timestamp'] = format_timestamp(event.get('creation_timestamp', ''))
      new_event['detection_timestamp'] = format_timestamp(event.get('detection_timestamp', ''))
      converted_events.append(new_event)
        
   return converted_events

def validate_map_chassis_events_in_alarms_and_events_chassis_events(chassis: str, map_events: list, lw_events: list,
      section: str | None = None, compare_timestamps: bool = True) -> tuple[bool, dict]:
   """
   Returns True only if every map_event is included in lw_events.
   Returns the missing events in a dict.
   """

   def clean(s) -> str:
      return re.sub(r"\s+", " ", str(s or "").strip())

   def normalize_time(ts: str) -> str:
      ts = clean(ts)
      if not ts:
         return ""

      for fmt in ("%d.%m.%Y, %H:%M:%S", "%d.%m.%Y, %H:%M"):
         try:
            return datetime.strptime(ts, fmt).strftime("%d.%m.%Y, %H:%M")
         except Exception:
            pass

      return ts

   def time_close(t1: str, t2: str, margin_seconds: int = 120) -> bool:
      t1 = normalize_time(t1)
      t2 = normalize_time(t2)

      if not t1 or not t2:
         return t1 == t2

      try:
         dt1 = datetime.strptime(t1, "%d.%m.%Y, %H:%M")
         dt2 = datetime.strptime(t2, "%d.%m.%Y, %H:%M")
         return abs((dt1 - dt2).total_seconds()) <= margin_seconds
      except Exception:
         return t1 == t2

   def category_parts(category: str) -> set[str]:
      return {clean(c) for c in clean(category).split(";") if clean(c)}

   def message_match(map_msg: str, lw_msg: str) -> bool:
      map_msg = clean(map_msg)
      lw_msg = clean(lw_msg)

      return (
         map_msg == lw_msg or
         (map_msg and lw_msg and map_msg in lw_msg) or
         (map_msg and lw_msg and lw_msg in map_msg)
      )

   def source_match(map_source: str, lw_source: str) -> bool:
      map_source = clean(map_source)
      lw_source = clean(lw_source)

      if map_source == lw_source:
         return True

      return (
         map_source and lw_source and
         (
            map_source in lw_source or
            lw_source in map_source
         )
      )

   def category_match(map_cat: str, lw_cat: str) -> bool:
      map_parts = category_parts(map_cat)
      lw_parts = category_parts(lw_cat)

      if not map_parts or not lw_parts:
         return map_parts == lw_parts

      return bool(map_parts & lw_parts)

   def timestamps_match(map_creation, map_detection, lw_creation, lw_detection) -> bool:
      # direct comparison
      direct = (
         time_close(map_creation, lw_creation) and
         time_close(map_detection, lw_detection)
      )

      # swapped comparison (VERY IMPORTANT)
      swapped = (
         time_close(map_creation, lw_detection) and
         time_close(map_detection, lw_creation)
      )

      return direct or swapped

   def normalize_lw_event(lw_e: dict) -> dict:
      return {
         "message": clean(lw_e.get("Message", lw_e.get("message", ""))),
         "source": clean(lw_e.get("Source", lw_e.get("source", ""))),
         "category": clean(lw_e.get("Category", lw_e.get("category", ""))),
         "creation_timestamp": normalize_time(lw_e.get("Creation Timestamp", lw_e.get("creation_timestamp", ""))),
         "detection_timestamp": normalize_time(lw_e.get("Detection Timestamp", lw_e.get("detection_timestamp", ""))),
         "raw": lw_e,
      }

   def normalize_map_event(map_e: dict) -> dict:
      return {
         "message": clean(map_e.get("message", "")),
         "source": clean(map_e.get("source", "")),
         "category": clean(map_e.get("category", "")),
         "creation_timestamp": normalize_time(map_e.get("creation_timestamp", "")),
         "detection_timestamp": normalize_time(map_e.get("detection_timestamp", "")),
         "raw": map_e,
      }

   normalized_lw_events = [normalize_lw_event(e) for e in lw_events]

   missing_events = []

   for map_e in map_events:
      map_norm = normalize_map_event(map_e)
      found = False

      best_reason = "no matching message/source/category/time"
      partial_candidates = []

      for lw_norm in normalized_lw_events:
         msg_ok = message_match(map_norm["message"], lw_norm["message"])
         src_ok = source_match(map_norm["source"], lw_norm["source"])
         cat_ok = category_match(map_norm["category"], lw_norm["category"])

         if compare_timestamps:
            time_ok = timestamps_match(
               map_norm["creation_timestamp"],
               map_norm["detection_timestamp"],
               lw_norm["creation_timestamp"],
               lw_norm["detection_timestamp"]
            )
         else:
            time_ok = True

         if msg_ok and src_ok and cat_ok and time_ok:
            found = True
            break

         if msg_ok and src_ok and cat_ok:
            best_reason = "time mismatch"
            partial_candidates.append(lw_norm)
         elif msg_ok and src_ok:
            best_reason = "category mismatch"
            partial_candidates.append(lw_norm)
         elif msg_ok:
            best_reason = "message matched, but source/category/time did not all match"
            partial_candidates.append(lw_norm)

      if not found:
         missing_events.append((map_norm, best_reason, partial_candidates))

   if missing_events:
      location = f"[{chassis}]"
      if section:
         location += f" [{section}]"

      # print(f"\n{location} Map events validation failed. ❌")
      # print(f"Missing map events: {len(missing_events)}")

      # for map_norm, reason, candidates in missing_events:
      #    print(
      #       f"\nMissing event | reason={reason}\n"
      #       f"  MAP: message={map_norm['message']}, "
      #       f"source={map_norm['source']}, "
      #       f"category={map_norm['category']}, "
      #       f"creation={map_norm['creation_timestamp']}, "
      #       f"detection={map_norm['detection_timestamp']}"
      #    )

      #    if candidates:
      #       print("  Closest LW candidates:")
      #       for lw in candidates:
      #          print(
      #             f"    LW: message={lw['message']}, "
      #             f"source={lw['source']}, "
      #             f"category={lw['category']}, "
      #             f"creation={lw['creation_timestamp']}, "
      #             f"detection={lw['detection_timestamp']}"
      #          )

      return False, missing_events

   location = f"[{chassis}]"
   if section:
      location += f" [{section}]"

   print(f"\n{location} Map events validation passed. ✅")
   return True, []

def validate_missing_map_events_by_direct_search(alarms_and_events, left_panel, chassis: str, missing_events: list,
   from_date: str, compare_timestamps: bool = True) -> bool:
   """
   Returns True only if all missing events are found.
   """

   def clean(s) -> str:
      return re.sub(r"\s+", " ", str(s or "").strip())

   def normalize_time(ts: str) -> str:
      ts = clean(ts)
      if not ts:
         return ""

      for fmt in ("%d.%m.%Y, %H:%M:%S", "%d.%m.%Y, %H:%M"):
         try:
            return datetime.strptime(ts, fmt).strftime("%d.%m.%Y, %H:%M")
         except Exception:
            pass

      return ts

   def time_close(t1: str, t2: str, margin_seconds: int = 120) -> bool:
      t1 = normalize_time(t1)
      t2 = normalize_time(t2)

      if not t1 or not t2:
         return t1 == t2

      try:
         dt1 = datetime.strptime(t1, "%d.%m.%Y, %H:%M")
         dt2 = datetime.strptime(t2, "%d.%m.%Y, %H:%M")
         return abs((dt1 - dt2).total_seconds()) <= margin_seconds
      except Exception:
         return t1 == t2

   def message_match(map_msg: str, lw_msg: str) -> bool:
      map_msg = clean(map_msg)
      lw_msg = clean(lw_msg)

      return (
         map_msg == lw_msg or
         (map_msg and lw_msg and map_msg in lw_msg) or
         (map_msg and lw_msg and lw_msg in map_msg)
      )

   def source_match(map_source: str, lw_source: str) -> bool:
      map_source = clean(map_source)
      lw_source = clean(lw_source)

      return (
         map_source == lw_source or
         (map_source and lw_source and (map_source in lw_source or lw_source in map_source))
      )

   def category_parts(category: str) -> set[str]:
      return {clean(c) for c in clean(category).split(";") if clean(c)}

   def category_match(map_cat: str, lw_cat: str) -> bool:
      map_parts = category_parts(map_cat)
      lw_parts = category_parts(lw_cat)

      if not map_parts or not lw_parts:
         return map_parts == lw_parts

      return bool(map_parts & lw_parts)

   def timestamps_match(map_creation, map_detection, lw_creation, lw_detection) -> bool:
      direct = (
         time_close(map_creation, lw_creation) and
         time_close(map_detection, lw_detection)
      )

      swapped = (
         time_close(map_creation, lw_detection) and
         time_close(map_detection, lw_creation)
      )

      return direct or swapped

   def normalize_lw_event(lw_e: dict) -> dict:
      return {
         "message": clean(lw_e.get("Message", lw_e.get("message", ""))),
         "source": clean(lw_e.get("Source", lw_e.get("source", ""))),
         "category": clean(lw_e.get("Category", lw_e.get("category", ""))),
         "creation_timestamp": normalize_time(lw_e.get("Creation Timestamp", lw_e.get("creation_timestamp", ""))),
         "detection_timestamp": normalize_time(lw_e.get("Detection Timestamp", lw_e.get("detection_timestamp", ""))),
      }

   def is_missing_event_found_in_lw(map_event: dict, lw_events: list) -> bool:
      map_message = clean(map_event.get("message", ""))
      map_source = clean(map_event.get("source", ""))
      map_category = clean(map_event.get("category", ""))
      map_creation = normalize_time(map_event.get("creation_timestamp", ""))
      map_detection = normalize_time(map_event.get("detection_timestamp", ""))

      for lw_e in lw_events:
         lw = normalize_lw_event(lw_e)

         if not message_match(map_message, lw["message"]):
            continue

         if not source_match(map_source, lw["source"]):
            continue

         if not category_match(map_category, lw["category"]):
            continue

         if compare_timestamps:
            if not timestamps_match(
               map_creation,
               map_detection,
               lw["creation_timestamp"],
               lw["detection_timestamp"]
            ):
               continue

         return True

      return False

   all_found = True

   for item in missing_events:
      # Supports both:
      # missing_events = [map_norm, ...]
      # missing_events = [(map_norm, reason, candidates), ...]
      if isinstance(item, tuple):
         map_event = item[0]
         map_event_reason = item[1]
      else:
         map_event = item
         map_event_reason = "Unknown"

      message = clean(map_event.get("message", ""))
      
      refresh_page(page)
      left_panel.click_alarms_and_events()
      alarms_and_events.set_faults_type("Events")
      alarms_and_events.set_filterBy("Domain/Chassis")
      alarms_and_events.select_domain_or_chassis_filterBy_domain_or_chassis(chassis)
      alarms_and_events.set_from_date(from_date_and_time=from_date)

      # Use the missing event message as a focused search.
      alarms_and_events.set_message(message)

      sleep(3)
      filtered_lw_events = alarms_and_events.get_all_events()

      if not is_missing_event_found_in_lw(map_event, filtered_lw_events):
         print(
            f"\n[{chassis}] Missing event was NOT found by direct search ({map_event_reason}):\n"
            f"  message={map_event.get('message')}, "
            f"source={map_event.get('source')}, "
            f"category={map_event.get('category')}, "
            f"creation={map_event.get('creation_timestamp')}, "
            f"detection={map_event.get('detection_timestamp')}"
         )
         all_found = False
      else:
         print(f"[{chassis}] Missing event found by direct search: {message}")

   return all_found

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

def test_show_chassis_events_via_SNMPv2(page, left_panel: LeftPanel, logger, report):
   domain_management = DomainManagement(page)
   device_discovery = DeviceDiscovery(page)
   alarms_and_events = AlarmsAndEvents(page)
   network_topology = NetworkTopology(page)
   upper_panel = UpperPanel(page)

   results = {}
   global_state = {'chassis_list': [], 'map_chassis_events': {}, 'elements_per_chassis': {}}
   from_date_per_chassis = {}

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

   ###############################################################################
   # Step 6 - Validate that events displayed for each chassis in Management Map. #
   # Match the corresponding events shown in Alarms & Events.                    #
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
         
         map_chassis_events = network_topology.element_details_faults_get_all_events()
         map_chassis_events = convert_map_chassis_events_to_alarms_and_events_chassis_events(map_chassis_events)
         global_state['map_chassis_events'][chassis] = map_chassis_events
         
         network_topology.element_details_faults_view_all_events()
         sleep(3)
         from_date = map_chassis_events[0]['detection_timestamp']
         from_date_obj = datetime.strptime(from_date, "%d.%m.%Y, %H:%M:%S") - timedelta(days=1)
         from_date_formatted = from_date_obj.strftime("%Y-%m-%d %H:%M:%S")
         from_date_per_chassis[chassis] = from_date_formatted
         sleep(2)
         alarms_and_events.set_from_date(from_date_and_time=from_date_formatted)
         sleep(10)
         alarms_and_events_chassis_events = alarms_and_events.get_all_events()
         
         ok, missing_events = validate_map_chassis_events_in_alarms_and_events_chassis_events(chassis, map_chassis_events, 
         alarms_and_events_chassis_events, section="Step 6")

         missing_ok = True
         if not ok:
            missing_ok = validate_missing_map_events_by_direct_search(alarms_and_events, left_panel, chassis, missing_events,
            from_date_formatted)

         if not missing_ok:
            raise AssertionError(f"Events mismatch for {chassis} in Step 6")
         
         left_panel.click_network_topology()
         refresh_page(page)

   results[6] = run_step(6, step_6, logger, report)

   #######################################################################################
   # Step 7 - Validate chassis events using the Domain/Chassis filter in Alarms & Events #
   # and compare them against Management Map chassis events for each chassis.            #
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
      chassis_events_list = {c: [] for c in chassis_list}

      for chassis in chassis_list:
         refresh_page(page)
         left_panel.click_alarms_and_events()
         alarms_and_events.set_faults_type("Events")
         alarms_and_events.set_filterBy("Domain/Chassis")
         alarms_and_events.select_domain_or_chassis_filterBy_domain_or_chassis(chassis)
               
         alarms_and_events.set_from_date(from_date_and_time=from_date_per_chassis[chassis])
         sleep(5)
         events = alarms_and_events.get_all_events()
         chassis_events_list[chassis] = events
      
         map_events = global_state['map_chassis_events'].get(chassis, [])

         ok, missing_events = validate_map_chassis_events_in_alarms_and_events_chassis_events(chassis, map_events, 
         chassis_events_list[chassis], section="Step 7")

         missing_ok = True
         if not ok:
            missing_ok = validate_missing_map_events_by_direct_search(alarms_and_events, left_panel, chassis, missing_events,
            from_date_per_chassis[chassis])

         if not missing_ok:
            raise AssertionError(f"Events mismatch for {chassis} in Step 7")

   results[7] = run_step(7, step_7, logger, report)

   ###############################################################################
   # Step 8 - Select other domain and validate chassis events in Alarms & Events #
   # and compare them against Management Map chassis events for each chassis.    #
   ###############################################################################
   def step_8():
      try:
         domain_name = "ScriptDomain"
         left_panel.click_network_topology()
         upper_panel.select_domain(domain_name)
         
         network_topology.show_navigation_info()
         element_list = network_topology.get_navigation_info_elements_list(visible_only=False)
         elements_per_chassis = get_elements_per_chassis(element_list)
         network_topology.hide_navigation_info()

         chassis = CHASSIS_NAME
         new_domain_chassis_events_list = {f'{chassis}': []}

         network_topology.click_on_element_via_the_map(element_name=chassis)
         network_topology.element_details_click_on_faults()
         map_chassis_events = network_topology.element_details_faults_get_all_events()
         map_chassis_events = convert_map_chassis_events_to_alarms_and_events_chassis_events(map_chassis_events)
         global_state['map_chassis_events'][chassis] = map_chassis_events
         from_date = map_chassis_events[0]['detection_timestamp']
         from_date_obj = datetime.strptime(from_date, "%d.%m.%Y, %H:%M:%S") - timedelta(days=1)
         from_date_formatted = from_date_obj.strftime("%Y-%m-%d %H:%M:%S")
         
         for ip in elements_per_chassis[chassis]:
            left_panel.click_alarms_and_events()
            alarms_and_events.set_faults_type("Events")
            alarms_and_events.set_from_date(from_date_and_time=from_date_formatted)
            alarms_and_events.set_filterBy("Devices")
            alarms_and_events.select_device_filterBy_devices(ip)
            alarms_and_events.close_devices_dropdown()

            alarms_and_events_ip_events = alarms_and_events.get_all_events()
            new_domain_chassis_events_list[chassis].extend(alarms_and_events_ip_events)
            alarms_and_events.remove_device_filterBy_devices(ip)
            refresh_page(page)
            
         ok, missing_events = validate_map_chassis_events_in_alarms_and_events_chassis_events(chassis, map_chassis_events, 
         new_domain_chassis_events_list[chassis], section="Step 8")

         missing_ok = True
         if not ok:
            missing_ok = validate_missing_map_events_by_direct_search(alarms_and_events, left_panel, chassis, missing_events,
            from_date_formatted)

         if not missing_ok:
            raise AssertionError(f"Events mismatch for {chassis} in Step 8")

      finally:
         refresh_page(page)
         left_panel.click_network_topology()
         upper_panel.select_domain(DEFAULT_DOMAIN_NAME)


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

      test_show_chassis_events_via_SNMPv2(page, left_panel, logger, report)

      context.close()
      browser.close()
      close_report(report)

   end_time = time.perf_counter()
   print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
   logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")