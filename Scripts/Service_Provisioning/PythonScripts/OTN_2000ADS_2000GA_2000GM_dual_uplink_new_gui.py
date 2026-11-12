"""
Created by: Yuval Dahan
Date: 02/11/2026

Comprehensive OTN Test for 2000ADS, 2000GA and 2000GM devices.
=====================================================

*** Runtime: approximately -- minutes ***
=====================================================

Setup:


                                          (10Gig)       
                                          [T.G_1]      
                                             |            
                                        _____|__________________
                                        | [Port 1]              |
                                        |                       |        
                                        |           A           | 
                            [Uplink 2] /|                       |\ [Uplink 1]
                                      / |_______________________| \
                                     /                             \
                                    /                               \
                                   /                                 \
                                  /                                   \
                                 /                                     \
                                /                                       \
                               /                                         \
                              /                                           \
                             /                                             \
                            /                                               \
                     [Uplink 1]                                          [Uplink 2]
 _______________________                                                      _______________________
|                       |                                                    |                       |
|                       |                                                    |                       |        
|           C           | [Uplink 2]                              [Uplink 1] |           B           | 
|                       |----------------------------------------------------|                       |
|_[Port 2]______________|                                                    |_____[Port 2]_[Port 1]_|
   |    |                                                                              |      |   |
   \____/                                                                              |      \___/  
  (Loopback)                                                                        [T.G_2] (Loopback)
                                                                                    (OTU2)
 


Notes:
1) This script is designed to 2000ADS, 2000GA and 2000GM devices.


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
from Pages.alarms_and_events import AlarmsAndEvents
from Pages.device_discovery import DeviceDiscovery
from Pages.domain_management import DomainManagement
from Pages.help_and_about import HelpAndAbout
from Pages.inventory import Inventory
from Pages.left_panel_page import LeftPanel
from Pages.login_page import LoginPage
from Pages.network_topology import NetworkTopology
from Pages.performance import Performance
from Pages.service_list import ServiceList
from Pages.service_provisioning import ServiceProvisioning
from Pages.system_configuration import SystemConfiguration
from Pages.system_operations import SystemOperationsPage
from Pages.upper_panel import UpperPanel
from Pages.user_management import UserManagement
from Pages.network_topology import NetworkTopology
from PL_Devices.PL_Pages_New_Gui.PL_login_page_new_gui import PL_LoginPage
from PL_Devices.PL_Pages_New_Gui.PL_main_screen_POM_new_gui import PL_Main_Screen_POM
from PL_Devices.PL_Pages_New_Gui.PL_performance_page_new_gui import PL_PerformancePage
from PL_Devices.PL_Pages_New_Gui.PL_security_page_new_gui import PL_SecurityPage
from PL_Devices.PL_Pages_New_Gui.PL_SNMP_page_new_gui import PL_SNMPPage
from PL_Devices.PL_Pages_New_Gui.PL_upper_panel_new_gui import PL_Upper_Panel
from Utils.utils import refresh_page, countdown_sleep, create_page, devices_are_up
from Testing_Equipment.Traffic_Generator.traffic_generator_Basic_Functions import Traffic_Generator
from Testing_Equipment.VIAVI import viavi_Basic_Functions
import re
import time
from time import sleep
import random
from Utils.Logger import create_logger
import sys
from sys import argv
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from collections import Counter
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

    # LW_SERVER_HOST_IP  = "172.16.10.22:8080"
    LW_SERVER_HOST_IP = "172.16.10.22:8443"
    LW_USERNAME = "administrator"
    LW_PASSWORD = "administrator"

    DEVICE_IP_USER = "tech"
    DEVICE_IP_PASS = "packetlight"

    DOMAIN_NAME = "OTN_Domain"

    DEVICES_LIST = ['172.16.40.15', '172.16.40.19', '172.16.40.20'] # Device A needs to be the first in the list, Device B second, Device C third. The order is important.

    TRAFFIC_GENERATOR_IP1 = '172.16.10.101'
    TRAFFIC_GENERATOR_APPLICATION1 = '10GigEth-LAN' # Not supposed to be changed
    TRAFFIC_GENERATOR_SLOT1 = 3
    TRAFFIC_GENERATOR_PORT1 = 2

    TRAFFIC_GENERATOR_IP2 = '172.16.10.101'
    TRAFFIC_GENERATOR_APPLICATION2 = 'OTU2' # Not supposed to be changed
    TRAFFIC_GENERATOR_SLOT2 = 6
    TRAFFIC_GENERATOR_PORT2 = 1

    LW_SERVICE_TYPE1 = '10GbE-LAN'
    LW_SERVICE_TYPE2 = 'OTU2'
    LW_SERVICE_TYPE3 = 'STM64'
    LW_SERVICE_TYPE4 = '8G FC'
    LW_SERVICE_TYPE5 = '16G FC'
    LW_SERVICE_TYPE6 = '12G-SDI'
    LW_SERVICE_TYPE7 = '12G-SDI DUAL'
    LW_SERVICE_TYPE8 = '12G-SDI NTSC'
    LW_SERVICE_TYPE9 = '10GbE-LAN'

    UPLINK_SERVICE_TYPE1 = "OTU4"
    UPLINK_SERVICE_TYPE2 = "OTU4"

    CLIENT_SERVICE_TYPE1 = "10GbE-LAN"
    CLIENT_SERVICE_TYPE2 = "OTU2"
    CLIENT_SERVICE_TYPE3 = "STM-64"
    CLIENT_SERVICE_TYPE4 = "8G FC"
    CLIENT_SERVICE_TYPE5 = "16G FC"
    CLIENT_SERVICE_TYPE6 = "12G-SDI"
    CLIENT_SERVICE_TYPE7 = "12G-SDI DUAL"
    CLIENT_SERVICE_TYPE8 = "12G-SDI NTSC"
    CLIENT_SERVICE_TYPE9 = "10GbE-LAN"


# ================================================================
# Values that should not be changed
# ================================================================

# The LW server answers HTTPS on 8443 and HTTP on 8080
BASE_URL = f"{'https' if LW_SERVER_HOST_IP.endswith(':8443') else 'http'}://{LW_SERVER_HOST_IP}/"
WAIT = 10

# Steps 21-22 compare only the alarms / events raised since the script started
SCRIPT_START_TIME = datetime.now()

SERVICE_NAME1 = "A-TO-B-PORT1-10G"
SERVICE_NAME2 = "B-TO-C-PORT2-OTU2"
SERVICE_NAME3 = "C-TO-A-PORT3-STM64"
SERVICE_NAME4 = "A-TO-B-PORT4-8GFC"
SERVICE_NAME5 = "B-TO-C-PORT5-16GFC"
SERVICE_NAME6 = "C-TO-A-PORT6-12G-SDI"
SERVICE_NAME7 = "A-TO-B-PORT7-12G-SDI_DUAL"
SERVICE_NAME8 = "B-TO-C-PORT8-12G-SDI_NTSC"
SERVICE_NAME9 = "A-TO-B-PORT9-10G"

UPLINK_PORT_1 = 19
UPLINK_PORT_2 = 20
CLIENT_PORT_1 = 1
CLIENT_PORT_2 = 2
CLIENT_PORT_3 = 3
CLIENT_PORT_4 = 4
CLIENT_PORT_5 = 5
CLIENT_PORT_6 = 6
CLIENT_PORT_7 = 7
CLIENT_PORT_8 = 8
CLIENT_PORT_9 = 9

SERVICE1_PATH = "service1_path"
SERVICE2_PATH = "service2_path"
SERVICE3_PATH = "service3_path"
SERVICE4_PATH = "service4_path"
SERVICE5_PATH = "service5_path"
SERVICE6_PATH = "service6_path"
SERVICE7_PATH = "service7_path"
SERVICE8_PATH = "service8_path"
SERVICE9_PATH = "service9_path"


LINKS_TIMEOUT = 180          # seconds to wait for the OTN links to turn positive
NEUTRAL_PORT = 16            # port read on transit devices for the pass-through slots (see verify_service_on_devices)
ALERT_TIMEOUT = 120          # seconds to wait for a service Alert to change

GOOGLE_SNTP_SERVER = '216.239.35.0'
GMT2 = "GMT+2"

LOGGER_ROOT_DIRECTORY = 'G:\\Python\\PacketLight Automation\\LightWatch_WEB\\Scripts\\Service_Provisioning\\LogFiles'
LOGGER_DIRECTORY_NAME = "OTN_2000ADS_2000GA_2000GM"
LOG_FILE_NAME = 'OTN_2000ADS_2000GA_2000GM.log'
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

# ================================================================
# Side functions
# ================================================================

IP_RE = re.compile(r"\((\d{1,3}(?:\.\d{1,3}){3})\)")


def _clean(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()

def _ok(result) -> bool:
    """PL POM setters return (success, dialog_text); tolerate a bare bool too."""
    return bool(result[0]) if isinstance(result, tuple) else bool(result)

def lw_node_label(ip, product_names) -> str:
    """LW node label, e.g. 'PL-2000ADS (172.16.40.15)'."""
    return f"{product_names[ip]} ({ip})"

def lw_port_label(port) -> str:
    """LW port label, e.g. 'Port 1'."""
    return f"Port {port}"

def lw_endpoint_label(ip, port, product_names) -> str:
    """Service List Start/End value, e.g. 'PL-2000ADS (172.16.40.15):Port 1'."""
    return f"{lw_node_label(ip, product_names)}:{lw_port_label(port)}"

def open_device(page, ip):
    """Login to the PL device GUI in a new tab and open Configuration. Returns (device_page, pl_main_screen)."""
    device_page = page.context.new_page()
    pl_login = PL_LoginPage(device_page)
    pl_login.goto(f"http://{ip}/")
    if not pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS):
        device_page.close()
        raise AssertionError(f"Login to {ip} GUI failed.")
    sleep(1)

    pl_main_screen = PL_Main_Screen_POM(device_page)
    if not pl_main_screen.click_Configuration():
        device_page.close()
        raise AssertionError(f"click_Configuration failed on {ip}.")
    return device_page, pl_main_screen

def logout_from_device(device_page, ip):
    """Logout from the PL device GUI."""
    pl_login = PL_LoginPage(device_page)
    if not pl_login.logout():
        raise AssertionError(f"Logout from {ip} GUI failed.")
    sleep(2)

def set_port_service_type(pl_main_screen, ip, port, service_type):
    if not _ok(pl_main_screen.set_service_type(port_number=str(port), service_type_value=service_type)):
        raise AssertionError(f"{ip}: set_service_type(Port {port}, '{service_type}') failed.")

def set_port_admin_up(pl_main_screen, ip, port):
    if not _ok(pl_main_screen.set_admin_status(port_number=str(port), status="Up")):
        raise AssertionError(f"{ip}: set_admin_status(Port {port}, 'Up') failed.")

def configure_client_port(page, ips, port, service_type):
    """Set the client port service type on every device in ips."""
    for ip in ips:
        device_page, pl_main_screen = open_device(page, ip)
        try:
            set_port_service_type(pl_main_screen, ip, port, service_type)
        finally:
            logout_from_device(device_page, ip)
            device_page.close()

def get_path_section(service_path: dict, name: str) -> list:
    """Case-insensitive lookup of the 'Working' / 'Protection' section of the tributary slots table."""
    for key, blocks in (service_path or {}).items():
        if name.lower() in key.lower():
            return blocks or []
    return []

def lw_block_slots(block) -> list:
    """
    Tributary slots LW assigned to one hop.
    LW lists only the slots 'used by service' for each hop and does not mark them with an extra
    class, so get_tributary_slots_table() returns an empty 'selected_slots' - fall back to 'slots'.
    """
    return block.get("selected_slots") or block.get("slots") or []

def path_hops(blocks) -> list:
    """
    Split a tributary slots section into hops: [{"ip": str, "uplink": int, "slots": set[int]}].
    A transit device appears twice (one hop per uplink) - its uplinks are NOT merged, because
    each uplink carries its own slots (e.g. Uplink 1 = 17-24, Uplink 2 = 9-16).
    """
    hops = []
    for block in blocks or []:
        m = IP_RE.search(block.get("device", ""))
        if not m:
            raise AssertionError(f"Could not parse the device IP from '{block.get('device')}'.")
        u = re.search(r"Uplink\s*(\d+)", f"{block.get('uplink', '')} {block.get('label', '')}", re.IGNORECASE)
        if not u:
            raise AssertionError(f"Could not parse the uplink of hop {block}.")
        hops.append({
            "ip": m.group(1),
            "uplink": int(u.group(1)),
            "slots": {int(s) for s in lw_block_slots(block) if str(s).strip().isdigit()},
        })
    return hops

def verify_service_on_devices(page, sections: dict, endpoints: dict, protected: bool, service_name: str) -> list:
    """
    Compare every LW hop (device + uplink + slots) with the device provisioning.

    Workaround for a device limitation: with APS on, a provisioned port's Provisioning tab opens on
    the APS active Rx uplink and blocks the other uplink tab, and it draws both uplinks merged. The page
    still carries the raw per-uplink slot bitmaps (provArray / msi), so get_provisioning_all_uplinks()
    decodes every uplink from them:
        endpoint device -> read from the service port: on every uplink, the slots 'Occupied by this
                           port' must EQUAL the LW slots of that uplink (none when LW uses no slots there)
        transit device  -> read from NEUTRAL_PORT: LW slots must be 'Occupied by Pass-through service'
                           (other services may pass through too, so not an equality)

    sections:  {"Working": [hops], "Protection": [hops]}
    endpoints: {ip: service port} of the A and Z nodes.
    Returns a list of error strings (empty = pass).
    """
    errors = []

    # LW expectation per (ip, uplink) - an endpoint uplink may appear in both sections
    expected = {}
    for section, hops in sections.items():
        for hop in hops:
            entry = expected.setdefault((hop["ip"], hop["uplink"]), {"slots": set(), "sections": []})
            entry["slots"] |= hop["slots"]
            entry["sections"].append(section)
            if not hop["slots"]:
                errors.append(f"[{service_name} / {section}] {hop['ip']} Uplink {hop['uplink']}: LW selected no tributary slots.")

    for ip in dict.fromkeys(k[0] for k in expected):
        service_port = endpoints.get(ip)
        read_port = service_port if service_port is not None else NEUTRAL_PORT

        device_page, pl_main_screen = open_device(page, ip)
        try:
            device = pl_main_screen.get_provisioning_all_uplinks(str(read_port))
        finally:
            logout_from_device(device_page, ip)
            device_page.close()

        if device is None:
            errors.append(f"[{service_name}] {ip}: could not read the Provisioning tab of Port {read_port}.")
            continue
        # print(f"[{service_name}] {ip} Port {read_port}: {device}\n")

        lw_uplinks = {u: e for (hop_ip, u), e in expected.items() if hop_ip == ip}
        for uplink in lw_uplinks:
            if uplink not in device["uplinks"]:
                errors.append(f"[{service_name}] {ip}: LW uses Uplink {uplink}, the device has only "
                              f"uplinks {sorted(device['uplinks'])}.")

        if service_port is not None:
            # Endpoint: exact match on EVERY uplink (catches slots LW did not ask for, too)
            tag = f"[{service_name}] {ip} Port {service_port}"
            for uplink, slots in device["uplinks"].items():
                device_slots = {s["slot"] for s in slots if s["state"] == "this_port"}
                lw_slots = lw_uplinks.get(uplink, {}).get("slots", set())
                if device_slots != lw_slots:
                    sections_txt = "+".join(lw_uplinks[uplink]["sections"]) if uplink in lw_uplinks else "not in LW path"
                    errors.append(f"{tag} Uplink {uplink} ({sections_txt}): LW slots {sorted(lw_slots)} != "
                                  f"device slots occupied by this port {sorted(device_slots)}.")

            facility_protection = device.get("protection") == "Facility"
            if facility_protection != protected:
                state = "active" if protected else "not active"
                errors.append(f"{tag}: Facility Protection should be {state}, device shows protection={device['protection']}.")
        else:
            # Transit: LW slots must be pass-through on each uplink LW uses
            for uplink, entry in lw_uplinks.items():
                slots = device["uplinks"].get(uplink)
                if slots is None:
                    continue
                tag = f"[{service_name} / {'+'.join(entry['sections'])}] {ip} Uplink {uplink}"
                device_slots = {s["slot"] for s in slots if s["state"] == "pass_through"}
                missing = entry["slots"] - device_slots
                if missing:
                    errors.append(f"{tag}: LW slots {sorted(missing)} are not occupied by a pass-through service "
                                  f"(device pass-through slots, read from Port {NEUTRAL_PORT}: {sorted(device_slots)}).")

    return errors

def _create_otn_service(page, left_panel, service_provisioning, product_names, a_node, a_port, lw_service_type,
                        z_node, z_port, service_name, protected: bool, protection_device=None) -> dict:
    """
    Shared body of create_otn_service_protection / create_otn_service_unprotected.

    The LW tributary slots are read on the checkout step, the service is created, and only then each
    device's Provisioning tab is compared with them (the device slots are occupied only after Create).
    Returns the tributary slots table (service path).
    """
    
    left_panel.click_service_provisioning()
    service_provisioning.create_OTN_service()
    refresh_page(page)
    service_provisioning.set_OTN_A_node(lw_node_label(a_node, product_names))
    service_provisioning.set_OTN_A_port(lw_port_label(a_port))
    if protected:
        service_provisioning.enable_OTN_protection()
    service_provisioning.set_OTN_service_type(lw_service_type)
    service_provisioning.OTN_service_click_next()
    service_provisioning.set_OTN_Z_node(lw_node_label(z_node, product_names))
    service_provisioning.set_OTN_Z_port(lw_port_label(z_port))
    service_provisioning.set_OTN_service_name(service_name)
    service_provisioning.enable_OTN_auto_path()
    service_provisioning.OTN_service_click_next()

    service_path = service_provisioning.get_tributary_slots_table()
    # print(f"{service_name} tributary slots: {service_path}\n")

    working = get_path_section(service_path, "Working")
    protection = get_path_section(service_path, "Protection")
    if not working:
        raise AssertionError(f"{service_name}: LW tributary slots table has no 'Working' path.")
    if protected and not protection:
        raise AssertionError(f"{service_name}: protection is enabled but LW shows no 'Protection' path.")
    if not protected and protection:
        raise AssertionError(f"{service_name}: unprotected service but LW shows a 'Protection' path.")

    service_provisioning.OTN_service_create()

    def verify_all() -> list:
        errors = []
        sections = {"Working": path_hops(working)}
        if protected:
            sections["Protection"] = path_hops(protection)
            protection_ips = [hop["ip"] for hop in sections["Protection"]]
            if protection_device not in protection_ips:
                errors.append(f"{service_name}: protection device {protection_device} is not in the LW protection path "
                              f"{list(dict.fromkeys(protection_ips))}.")
        errors += verify_service_on_devices(page, sections, endpoints={a_node: a_port, z_node: z_port},
                                            protected=protected, service_name=service_name)
        return errors

    # The devices may need a few seconds to apply the provisioning - one retry before failing
    errors = verify_all()
    if errors:
        countdown_sleep(WAIT * 2, message=f"{service_name}: device provisioning mismatch, re-checking")
        errors = verify_all()
    if errors:
        raise AssertionError(" | ".join(errors))

    return service_path

def create_otn_service_protection(page, left_panel, service_provisioning, product_names, a_node, a_port,
                                  lw_service_type, z_node, z_port, service_name, protection_device) -> dict:
    return _create_otn_service(page, left_panel, service_provisioning, product_names, a_node, a_port, lw_service_type,
                               z_node, z_port, service_name, protected=True, protection_device=protection_device)

def create_otn_service_unprotected(page, left_panel, service_provisioning, product_names, a_node, a_port,
                                   lw_service_type, z_node, z_port, service_name) -> dict:
    return _create_otn_service(page, left_panel, service_provisioning, product_names, a_node, a_port, lw_service_type,
                               z_node, z_port, service_name, protected=False)

def has_otn_link(links, ip1, uplink1, ip2, uplink2) -> bool:
    """True if links has a positive OTN link between ip1/uplink1 and ip2/uplink2 (either side order)."""
    wanted = {f"{ip1} | {uplink1}", f"{ip2} | {uplink2}"}
    for link in links or []:
        if _clean(link.get("Link_Type")).upper() != "OTN" or _clean(link.get("Severity")).lower() != "positive":
            continue
        if {_clean(link.get("Side_A_Info")), _clean(link.get("Side_B_Info"))} == wanted:
            return True
    return False

def get_service_row(left_panel, service_list, service_name):
    """Service List -> domain -> Service Name filter. Returns the row whose Name matches, or None."""
    left_panel.click_service_list()
    service_list.select_domain_or_chassis(DOMAIN_NAME)
    service_list.set_service_name(service_name)
    sleep(2)
    for row in service_list.get_service_list():
        if _clean(row.get("Name")) == service_name:
            return row
    return None

def check_service_row(left_panel, service_list, expected: dict, retries: int = 3) -> list:
    """
    Compare the Service List row of expected['Name'] with expected (case/whitespace-insensitive).
    Retried a few times since Alert / Consistency settle a moment after creation.
    Returns a list of error strings.
    """
    name = expected["Name"]
    errors = []
    for attempt in range(retries):
        row = get_service_row(left_panel, service_list, name)
        if row is None:
            errors = [f"'{name}' was not found in the Service List."]
        else:
            # print(f"   Service List row: {row}")
            errors = [f"{name}: {key} expected '{value}', got '{_clean(row.get(key))}'."
                      for key, value in expected.items()
                      if _clean(row.get(key)).lower() != _clean(value).lower()]
        if not errors:
            return []
        if attempt < retries - 1:
            countdown_sleep(WAIT, message=f"{name}: Service List mismatch, re-checking")
    return errors

def wait_for_service_alert(left_panel, service_list, service_name, want_ok: bool, timeout_s: int) -> str:
    """Poll the Service List until the service Alert is 'OK' (want_ok) or not 'OK'. Returns the last Alert seen."""
    deadline = time.time() + timeout_s
    alert = ""
    while True:
        row = get_service_row(left_panel, service_list, service_name)
        alert = _clean(row.get("Alert")) if row else ""
        if row and ((alert.upper() == "OK") == want_ok):
            return alert
        if time.time() >= deadline:
            raise AssertionError(f"{service_name}: Alert did not become {'OK' if want_ok else 'not OK'} "
                                 f"within {timeout_s}s (last Alert: '{alert}').")
        sleep(10)

# ---------------- Service alarms / events: device GUI vs LW (steps 21-22) ----------------

FAULT_TIME_TOLERANCE_SEC = 60   # device time vs LW 'Creation Timestamp'
# The LW Events / Alarms list is sorted newest first and keeps growing while it is paged, so a row
# can slide onto a page that was already read and be skipped. When device faults are missing,
# the LW list is read again (merged with the earlier reads) before they count as missing.
LW_FAULTS_REREADS = 2
LW_FAULTS_REREAD_WAIT_SEC = 5
ENDPOINT_RE = re.compile(r"\((\d{1,3}(?:\.\d{1,3}){3})\)\s*:\s*Port\s*(\d+)", re.IGNORECASE)

def parse_device_fault_time(ts: str):
    """Device GUI fault time -> datetime, or None. '10/11/26;17:45:37' (day first) or '3/12/2026 1:42:31 PM'."""
    ts = _clean(ts)
    for fmt in ("%d/%m/%y;%H:%M:%S", "%d/%m/%Y;%H:%M:%S", "%m/%d/%Y %I:%M:%S %p"):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            pass
    return None

def parse_lw_fault_time(ts: str):
    """LW fault time -> datetime, or None. '10.11.2026, 17:45:37'."""
    try:
        return datetime.strptime(_clean(ts), "%d.%m.%Y, %H:%M:%S")
    except ValueError:
        return None

def service_endpoints(row: dict) -> list:
    """Service List row -> [(ip, port), ...] from Start / End, e.g. 'PL-2000ADS (172.16.40.15):Port 1' -> ('172.16.40.15', '1')."""
    endpoints = []
    for key in ("Start", "End"):
        m = ENDPOINT_RE.search(_clean(row.get(key)))
        if not m:
            raise AssertionError(f"{row.get('Name')}: cannot read device/port from {key} '{row.get(key)}'.")
        if m.groups() not in endpoints:
            endpoints.append(m.groups())
    return endpoints

def device_faults_since(rows: list, ip: str, since: datetime) -> list:
    """
    Device GUI alarms/events table rows ([date_time, source, severity, message, note]) raised at or
    after 'since', tagged with the device IP. Placeholder rows ('No Alarms' / 'No Events') are dropped.
    """
    out = []
    for row in rows or []:
        if len(row) < 4:
            continue
        when = parse_device_fault_time(row[0])
        if when and when >= since:
            out.append({"ip": ip, "time": when, "source": _clean(row[1]), "severity": _clean(row[2]),
                        "message": _clean(row[3]), "raw": row})
    return out

def lw_faults_since(rows: list, since: datetime) -> list:
    """
    LW Service List alarms/events dicts with 'Creation Timestamp' at or after 'since'.
    The LW side starts FAULT_TIME_TOLERANCE_SEC earlier, so a device event right at the start
    still finds its LW row when the two clocks differ by a few seconds.
    """
    since = since - timedelta(seconds=FAULT_TIME_TOLERANCE_SEC)
    out = []
    for row in rows or []:
        when = parse_lw_fault_time(row.get("Creation Timestamp", ""))
        if when and when >= since:
            out.append(dict(row, _time=when))
    return out

def merge_lw_fault_reads(rows: list, new_rows: list) -> list:
    """
    Union of two LW list reads that keeps identical rows: LW can show two real events with the same
    values in every column (e.g. two 'APS Switch Over' at the same second - the device tells them apart
    only by its Note 'to Working' / 'to Protecting', which LW does not show). So a row is added only
    for the copies 'new_rows' has beyond those 'rows' already has (per row: the max count of the reads).
    """
    def key(r):
        return tuple(sorted(r.items()))

    have = Counter(key(r) for r in rows)
    merged = list(rows)
    for r in new_rows or []:
        k = key(r)
        if have[k] > 0:
            have[k] -= 1          # this copy is already in 'rows'
        else:
            merged.append(r)      # a copy 'rows' does not have yet
    return merged

def fault_sources_match(ip: str, dev_src: str, lw_src: str) -> bool:
    """
    Device GUI source vs LW source: 'Port 1' vs '172.16.40.15 Port 1', 'System' vs '172.16.40.15',
    'ETH 1 Port' vs '172.16.40.15 Ethernet 1'.
    Same words (ignoring 'port'), numbers equal or missing on either side, and LW must name this device.
    """
    if ip not in lw_src:
        return False

    def parse(src: str):
        tokens = re.findall(r"[a-z]+|\d+", src.lower().replace(ip.lower(), " "))
        words = ["eth" if t == "ethernet" else t for t in tokens if t != "port" and not t.isdigit()]
        return (words or ["system"]), [t for t in tokens if t.isdigit()]

    dev_words, dev_nums = parse(dev_src)
    lw_words, lw_nums = parse(lw_src)
    return dev_words == lw_words and (not dev_nums or not lw_nums or dev_nums == lw_nums)

def fault_severities_match(dev_sev: str, lw_sev: str) -> bool:
    """Device 'Cleared' = LW 'Clear'; a device 'Event' is shown by LW as 'Info' or 'Clear'; Critical/Major/Minor are equal."""
    dev_sev, lw_sev = dev_sev.lower(), lw_sev.lower()
    if dev_sev == "event":
        return lw_sev in ("info", "clear", "event")
    if dev_sev == "cleared":
        return lw_sev in ("clear", "cleared")
    return dev_sev == lw_sev

def fault_messages_match(dev_msg: str, lw_msg: str) -> bool:
    dev_msg = dev_msg.replace("System Event :", "").strip().lower()
    lw_msg = lw_msg.strip().lower()
    return dev_msg == lw_msg or (dev_msg and lw_msg and (dev_msg in lw_msg or lw_msg in dev_msg))

def device_faults_missing_in_lw(device_faults: list, lw_faults: list) -> tuple:
    """
    Every device fault must have its own LW row: same message, severity and source (device + port),
    and LW 'Creation Timestamp' within FAULT_TIME_TOLERANCE_SEC of the device time.
    Each LW row can match one device fault only.
    Returns (device faults that have no LW row, set of indexes of the LW rows that were matched).
    """
    used, missing = set(), []
    for dev in device_faults:
        best, best_delta = None, None
        for i, lw in enumerate(lw_faults):
            if i in used:
                continue
            if not (fault_messages_match(dev["message"], lw.get("Message", ""))
                    and fault_severities_match(dev["severity"], lw.get("Severity", ""))
                    and fault_sources_match(dev["ip"], dev["source"], lw.get("Source", ""))):
                continue
            delta = abs((dev["time"] - lw["_time"]).total_seconds())
            if delta <= FAULT_TIME_TOLERANCE_SEC and (best_delta is None or delta < best_delta):
                best, best_delta = i, delta
        if best is None:
            missing.append(dev)
        else:
            used.add(best)
    return missing, used

def explain_missing_fault(dev: dict, lw_faults: list, used: set) -> str:
    """
    Plain-words reason why a device fault has no LW row. Looks only at LW rows that no other
    device fault took, in this order: right row with another severity, right row from another
    port/device, the LW row exists but already matched an identical device row, right row at
    another time, nothing at all.
    """
    tol = FAULT_TIME_TOLERANCE_SEC
    free = [lw for i, lw in enumerate(lw_faults) if i not in used]

    def delta(lw):
        return int((lw["_time"] - dev["time"]).total_seconds())

    def same_msg(lw):
        return fault_messages_match(dev["message"], lw.get("Message", ""))

    def same_port(lw):
        return fault_sources_match(dev["ip"], dev["source"], lw.get("Source", ""))

    near = [lw for lw in free if same_msg(lw) and abs(delta(lw)) <= tol]

    def is_clear(sev: str) -> bool:
        return _clean(sev).lower() in ("clear", "cleared")

    # 1) same port, same time, other severity
    for lw in sorted((lw for lw in near if same_port(lw)), key=lambda r: abs(delta(r))):
        if is_clear(lw.get("Severity", "")) != is_clear(dev["severity"]):
            # a raise vs its clear (or the other way round) - two different events, not a severity mismatch
            return (f"LW has no '{dev['severity']}' row of it - the nearest LW row is a different event: "
                    f"'{lw.get('Severity')}' at {lw['_time']:%H:%M:%S}.")
        return (f"LW has it at {lw['_time']:%H:%M:%S} but with severity '{lw.get('Severity')}' "
                f"(device: '{dev['severity']}').")

    # 2) same time, but LW shows it from another port / device
    for lw in sorted(near, key=lambda r: abs(delta(r))):
        return f"LW has it at {lw['_time']:%H:%M:%S} but from '{_clean(lw.get('Source'))}' (device: {dev['ip']} {dev['source']})."

    # 3) LW has it, but that row already matched an identical device row
    taken = [lw for i, lw in enumerate(lw_faults) if i in used and same_msg(lw) and same_port(lw)
             and abs(delta(lw)) <= tol and fault_severities_match(dev["severity"], lw.get("Severity", ""))]
    if taken:
        return (f"the device shows this {len(taken) + 1} times around {dev['time']:%H:%M:%S}, "
                f"LW has it only {len(taken)} time(s).")

    # 4) same port, other time
    other_time = [lw for lw in free if same_msg(lw) and same_port(lw)]
    if other_time:
        lw = min(other_time, key=lambda r: abs(delta(r)))
        d = delta(lw)
        return (f"LW has no '{dev['message']}' within {tol} s - the closest unmatched one is at "
                f"{lw['_time']:%H:%M:%S} ({abs(d)} s {'later' if d > 0 else 'earlier'}).")

    # 5) nothing
    if not any(same_port(lw) for lw in lw_faults):
        return f"LW has no events at all from {dev['ip']} {dev['source']} since the script started."
    return f"LW has no (unmatched) '{dev['message']}' from {dev['ip']} {dev['source']} since the script started."

def read_device_port_faults(page, ip: str, port: str, faults_type: str) -> list:
    """Login to the device GUI and return its alarms or events table of Port <port> (raw rows)."""
    device_page, pl_main_screen = open_device(page, ip)
    try:
        if faults_type == "Alarms":
            return pl_main_screen.get_alarms_table(str(port))
        return pl_main_screen.get_events_table(str(port))
    finally:
        try:
            logout_from_device(device_page, ip)
        finally:
            device_page.close()

def print_service_faults_report(name, endpoints, faults_type, device_faults, lw_faults, missing, used):
    """
    Print, per service, what was compared and - in plain words - every problem:
      'On the device, missing in LW'  -> fails the step (with the reason: closest LW row / what differs)
      'In LW, not on the device'      -> information only (LW may keep events the device already rotated out)
    """
    kind = faults_type.lower()
    one = kind[:-1]

    def span(times):
        return f"{min(times):%H:%M:%S} - {max(times):%H:%M:%S}" if times else "none"

    def line(when, ip, source, severity, message):
        return f"{when:%H:%M:%S} | {ip} {source} | {severity} | {message}"

    where = ", ".join(f"{ip} Port {port}" for ip, port in endpoints)
    status = "OK" if not missing else f"{len(missing)} PROBLEM(S)"
    print(f"\n   [{name}] {status}")
    print(f"      Compared: {where}")
    print(f"      Device: {len(device_faults)} {kind} since {SCRIPT_START_TIME:%H:%M:%S} ({span([d['time'] for d in device_faults])})")
    print(f"      LW    : {len(lw_faults)} {kind} since {SCRIPT_START_TIME:%H:%M:%S} ({span([l['_time'] for l in lw_faults])})")

    if missing:
        print(f"      On the device, missing in LW ({len(missing)}):")
        for dev in sorted(missing, key=lambda d: d["time"]):
            print(f"         - {line(dev['time'], dev['ip'], dev['source'], dev['severity'], dev['message'])}")
            print(f"           why: {explain_missing_fault(dev, lw_faults, used)}")

    # LW rows of the compared ports that no device row matched (service rows like 'Service status changed' are skipped)
    port_rows = [(i, lw) for i, lw in enumerate(lw_faults)
                 if any(fault_sources_match(ip, f"Port {port}", lw.get("Source", "")) for ip, port in endpoints)]
    extra = [lw for i, lw in port_rows if i not in used]
    if extra:
        print(f"      In LW, not on the device ({len(extra)}) - information only:")
        for lw in sorted(extra, key=lambda r: r["_time"]):
            print(f"         - {lw['_time']:%H:%M:%S} | {_clean(lw.get('Source'))} | {lw.get('Severity')} | {lw.get('Message')}")

    if not missing and not extra:
        print(f"      Every {one} matches between the devices and LW.")

def verify_service_faults_on_devices(page, left_panel, service_list, faults_type: str) -> list:
    """
    Steps 21 / 22: for every service in the Service List, every alarm / event that the service's
    Start and End devices raised on the service port since the script started (SCRIPT_START_TIME)
    must also be in the service's LW Alarms / Events list. Returns a list of error strings.
    """
    since = SCRIPT_START_TIME
    # LW 'From date' = the start day at 00:00 (fewer pages to read); the exact start time is filtered below
    lw_from_date = datetime.combine(since.date(), datetime.min.time()).strftime("%Y-%m-%d %H:%M:%S")

    refresh_page(page)  # close any open Events / Alarms panel so the full Service List is shown
    left_panel.click_service_list()
    service_list.select_domain_or_chassis(DOMAIN_NAME)
    service_list.set_service_name("")
    services = service_list.get_service_list()
    if not services:
        return [f"No services found in the Service List of '{DOMAIN_NAME}'."]

    errors = []
    for row in services:
        name = _clean(row.get("Name"))
        try:
            endpoints = service_endpoints(row)

            # Devices first: anything they show was already sent to LW when LW is read below
            device_faults = []
            for ip, port in endpoints:
                device_faults += device_faults_since(read_device_port_faults(page, ip, port, faults_type), ip, since)

            refresh_page(page)
            left_panel.click_service_list()
            service_list.select_domain_or_chassis(DOMAIN_NAME)
            service_list.set_service_name(name)
            sleep(2)
            service_list.click_on_service(service_name=name)
            service_list.click_on_events_alarms_button()
            service_list.set_faults_type(faults_type)
            service_list.set_from_date(lw_from_date)
            sleep(2)

            read_lw = service_list.get_alarms_list if faults_type == "Alarms" else service_list.get_events_list
            lw_rows = merge_lw_fault_reads([], read_lw())
            lw_service_faults = lw_faults_since(lw_rows, since)
            missing, used = device_faults_missing_in_lw(device_faults, lw_service_faults)

            # Rows can be skipped while paging a list that is still growing (or arrive late) - read again
            for attempt in range(1, LW_FAULTS_REREADS + 1):
                if not missing:
                    break
                # print(f"   [{name}] {len(missing)} device {faults_type.lower()} not found in LW - "
                #       f"reading the LW list again in {LW_FAULTS_REREAD_WAIT_SEC}s ({attempt}/{LW_FAULTS_REREADS})")
                sleep(LW_FAULTS_REREAD_WAIT_SEC)
                lw_rows = merge_lw_fault_reads(lw_rows, read_lw())
                lw_service_faults = lw_faults_since(lw_rows, since)
                missing, used = device_faults_missing_in_lw(device_faults, lw_service_faults)
            print_service_faults_report(name, endpoints, faults_type, device_faults, lw_service_faults, missing, used)
            for dev in missing:
                errors.append(f"{name}: {dev['ip']} {dev['source']} {faults_type[:-1].lower()} "
                              f"'{dev['message']}' ({dev['severity']}, {dev['time']:%H:%M:%S}) is on the device but not in LW")

        except AssertionError as e:
            errors.append(f"{name}: {e}")

    return errors

# ---------------- Service PMs: device GUI vs LW (step 23) ----------------

PM_PERIOD_TYPES = ["15 Minutes", "Days"]
# Day compared per PM period (days ago): Days -> yesterday's closed day; 15 Minutes -> today's
# intervals (the device keeps only the last 32 = 8 hours), up to the newest one LW has already polled.
PM_COMPARE_DAYS_AGO = {"15 Minutes": 0, "Days": 1}
DEVICE_PM_INTERVAL_RE = re.compile(r"(\d{2})/(\d{2})/(\d{2});(\d{2}):(\d{2}):\d{2}")
PM_VALIDITY_WORDS = {"yes", "no", "partial"}
PM_UNIT_RE = re.compile(r"^(-?\d+(?:\.\d+)?)\s*[A-Za-z%]+$")
PM_IGNORED_COLUMNS = {"reset", "side"}   # device-only Reset button column / LW-only Side column

def pm_column_key(header: str) -> str:
    """'Errored\\nSeconds' / 'Rx Level, dBm' -> 'erroredseconds' / 'rxleveldbm' (same key for device and LW)."""
    return re.sub(r"[^a-z0-9]", "", (header or "").lower())

def pm_cell_value(value: str) -> str:
    """'1.2 dBm' -> '1.2', 'PARTIAL; YES' -> 'Partial; Yes', whitespace collapsed."""
    value = PM_UNIT_RE.sub(r"\1", _clean(value))
    return "; ".join(p.capitalize() if p.lower() in PM_VALIDITY_WORDS else p for p in (s.strip() for s in value.split(";")))

def device_pm_interval(value: str) -> str:
    """Device 'Interval' -> LW format: '3.  10/11/26;11:15:40' / 'Previous Day: 10/11/26;00:00:06' -> '11:15 10.11.2026'."""
    m = DEVICE_PM_INTERVAL_RE.search(value or "")
    if not m:
        return _clean(value)
    day, month, year, hour, minute = m.groups()
    return f"{hour}:{minute} {day}.{month}.20{year}"

def normalize_pm_row(row: dict, from_device: bool) -> dict:
    """PM row (any PM type / column set) -> {column_key: value}, interval in LW format 'HH:MM DD.MM.YYYY'."""
    out = {}
    for header, value in row.items():
        key = pm_column_key(header)
        if not key or key in PM_IGNORED_COLUMNS:
            continue
        out[key] = (device_pm_interval(value) if from_device else _clean(value)) if key == "interval" else pm_cell_value(value)
    return out

def device_pm_rows_of_day(rows: list, day_text: str) -> list:
    """
    Device PM rows of one day ('DD.MM.YYYY'), normalized. The rows that are not a closed interval
    are dropped: 'Current:' (15 min), 'Current Day:' and 'Untimed:' (Days).
    """
    out = []
    for row in rows or []:
        interval_text = _clean(row.get("Interval", ""))
        if re.match(r"^(current|untimed)", interval_text, re.IGNORECASE):
            continue
        norm = normalize_pm_row(row, from_device=True)
        if norm.get("interval", "").endswith(day_text):
            out.append(norm)
    return out

def pm_interval_time(interval: str):
    """LW-format interval 'HH:MM DD.MM.YYYY' -> datetime, or None."""
    try:
        return datetime.strptime(_clean(interval), "%H:%M %d.%m.%Y")
    except ValueError:
        return None

def compare_pm_rows(device_rows: list, lw_rows: list) -> list:
    """
    Every device interval must be in LW with the same values (LW may have more intervals).
    Returns a list of plain-words problems.
    """
    problems = []
    lw_by_interval = {}
    for lw in lw_rows:
        lw_by_interval.setdefault(lw.get("interval", ""), []).append(lw)

    for dev in device_rows:
        interval = dev.get("interval", "")
        candidates = lw_by_interval.get(interval, [])
        if not candidates:
            problems.append(f"interval {interval} is on the device but not in LW")
            continue

        best_diffs = None
        for lw in candidates:
            columns = (set(dev) | set(lw)) - {"interval"}
            diffs = {c: (dev.get(c, "<no column>"), lw.get(c, "<no column>")) for c in sorted(columns) if dev.get(c) != lw.get(c)}
            if best_diffs is None or len(diffs) < len(best_diffs):
                best_diffs = diffs
            if not diffs:
                break
        if best_diffs:
            text = ", ".join(f"{c}: device={d} LW={l}" for c, (d, l) in best_diffs.items())
            problems.append(f"interval {interval} has different values -> {text}")
    return problems

def read_device_port_pms(page, ip: str, port: str) -> dict:
    """Login to the device GUI and read Port <port> PM tables for every PM period and PM type: {(period, type): rows}."""
    device_page = page.context.new_page()
    try:
        pl_login = PL_LoginPage(device_page)
        pl_login.goto(f"http://{ip}/")
        if not pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS):
            raise AssertionError(f"Login to {ip} GUI failed.")
        sleep(1)

        pl_performance = PL_PerformancePage(device_page)
        pm_types = pl_performance.get_device_pm_type_current_dropdown_options(port_number=str(port))
        if not pm_types:
            raise AssertionError(f"{ip}: no PM types found for Port {port}.")

        tables = {}
        for period in PM_PERIOD_TYPES:
            for pm_type in pm_types:
                if not pl_performance.set_PM_Period(port_number=str(port), period=period):
                    raise AssertionError(f"{ip}: set_PM_Period(Port {port}, '{period}') failed.")
                if not pl_performance.set_PM_Type(port_number=str(port), pm_type=pm_type):
                    raise AssertionError(f"{ip}: set_PM_Type(Port {port}, '{pm_type}') failed.")
                if not pl_performance.click_on_Get_PM(port_number=str(port)):
                    raise AssertionError(f"{ip}: click_on_Get_PM(Port {port}) failed.")
                tables[(period, pm_type)] = pl_performance.get_PM_table(port_number=str(port))

        try:
            pl_login.logout()
        except Exception:
            pass
        return tables
    finally:
        device_page.close()

def verify_service_pms_on_devices(page, left_panel, service_list) -> list:
    """
    Step 23: for every service, the PM intervals that the Start (A) and End (Z) devices show on the
    service port - per PM period and PM type - must be in the service's LW Performance table
    (Side A / Side Z) with the same values.
      Days       -> yesterday's day (the 'Previous Day' row).
      15 Minutes -> today's intervals, up to the newest interval LW has already polled for that side
                    (newer device intervals are not in LW yet and are skipped).
    Returns a list of error strings.
    """
    now = datetime.now()
    day_of = {period: (now - timedelta(days=PM_COMPARE_DAYS_AGO[period])).date() for period in PM_PERIOD_TYPES}

    refresh_page(page)
    left_panel.click_service_list()
    service_list.select_domain_or_chassis(DOMAIN_NAME)
    service_list.set_service_name("")
    services = service_list.get_service_list()
    if not services:
        return [f"No services found in the Service List of '{DOMAIN_NAME}'."]

    errors = []
    for row in services:
        name = _clean(row.get("Name"))
        print(f"\n   [{name}] PMs - " + ", ".join(f"{p}: {d:%d.%m.%Y}" for p, d in day_of.items()))
        try:
            # Side A = Start, Side Z = End (same as the LW Performance panel)
            sides = {}
            for side, key in (("A", "Start"), ("Z", "End")):
                m = ENDPOINT_RE.search(_clean(row.get(key)))
                if not m:
                    raise AssertionError(f"cannot read device/port from {key} '{row.get(key)}'.")
                sides[side] = {"node": _clean(row.get(key)).split(":")[0].strip(), "ip": m.group(1), "port": m.group(2)}

            # 1) Devices: every PM period x PM type of the service port
            device_pms = {side: read_device_port_pms(page, s["ip"], s["port"]) for side, s in sides.items()}
            configs = sorted({cfg for tables in device_pms.values() for cfg in tables},
                             key=lambda c: (PM_PERIOD_TYPES.index(c[0]), c[1]))

            # 2) LW: the service Performance panel, same configuration
            refresh_page(page)
            left_panel.click_service_list()
            service_list.select_domain_or_chassis(DOMAIN_NAME)
            service_list.set_service_name(name)
            sleep(2)
            service_list.click_on_service(service_name=name)
            service_list.click_on_performance_button(name)
            service_list.performance_set_device_A(sides["A"]["node"])
            service_list.performance_set_device_Z(sides["Z"]["node"])
            service_list.performance_set_port_A(lw_port_label(sides["A"]["port"]))
            service_list.performance_set_port_Z(lw_port_label(sides["Z"]["port"]))

            period_set = None
            for period, pm_type in configs:
                day = day_of[period]
                day_text = day.strftime("%d.%m.%Y")
                label = f"{period} / {pm_type}"
                device_rows = {side: device_pm_rows_of_day(device_pms[side].get((period, pm_type)), day_text) for side in sides}

                if not any(device_rows.values()):
                    print(f"      {label}: nothing to compare - no device intervals of {day_text}.")
                    continue

                if period_set != day:  # LW Period start / end = that day only (fewer pages to read)
                    service_list.performance_set_period_start(f"{day:%d/%m/%Y} 00:00")
                    service_list.performance_set_period_end(f"{day:%d/%m/%Y} 23:59")
                    period_set = day
                service_list.performance_set_pm_period_type(period)
                service_list.performance_set_pm_type(pm_type)
                sleep(2)
                lw_table = service_list.performance_get_pm_table(all_pages=True)

                for side, s in sides.items():
                    where = f"Side {side} {s['ip']} Port {s['port']}"
                    lw_rows = [normalize_pm_row(r, from_device=False) for r in lw_table
                               if _clean(r.get("Side")).upper() == side]
                    lw_rows = [r for r in lw_rows if r.get("interval", "").endswith(day_text)]
                    dev_rows = device_rows[side]
                    note = ""

                    if period == "15 Minutes":
                        lw_times = [t for t in (pm_interval_time(r.get("interval")) for r in lw_rows) if t]
                        if not lw_times:
                            problem = f"LW has no 15-minute intervals of {day_text} (device has {len(dev_rows)})"
                            print(f"      {label} | {where}: 1 PROBLEM(S)\n         - {problem}")
                            errors.append(f"{name} | {label} | {where}: {problem}")
                            continue
                        newest = max(lw_times)
                        not_polled = [r for r in dev_rows if (pm_interval_time(r.get("interval")) or newest) > newest]
                        dev_rows = [r for r in dev_rows if r not in not_polled]
                        if not_polled:
                            note = f" ({len(not_polled)} newer device intervals skipped - LW polled up to {newest:%H:%M})"

                    problems = compare_pm_rows(dev_rows, lw_rows)
                    status = "OK" if not problems else f"{len(problems)} PROBLEM(S)"
                    print(f"      {label} | {where}: device {len(dev_rows)} intervals, LW {len(lw_rows)}{note} -> {status}")
                    for problem in problems:
                        print(f"         - {problem}")
                        errors.append(f"{name} | {label} | {where}: {problem}")

        except AssertionError as e:
            print(f"      ERROR: {e}")
            errors.append(f"{name}: {e}")

    return errors

# ================================================================
# Main test
# ================================================================

def test_OTN_2000ADS_2000GA_2000GM(page, left_panel: LeftPanel, logger, report):
    device_discovery  = DeviceDiscovery(page)
    domain_management = DomainManagement(page)
    network_topology = NetworkTopology(page)
    service_provisioning = ServiceProvisioning(page)
    service_list = ServiceList(page)
    system_operations = SystemOperationsPage(page)
    upper_panel = UpperPanel(page)

    tgSession1 = viavi_Basic_Functions.Connect_To_Port(TRAFFIC_GENERATOR_IP1, TRAFFIC_GENERATOR_SLOT1, TRAFFIC_GENERATOR_PORT1)
    viavi_Basic_Functions.load_Predefind_Application(tgSession1, TRAFFIC_GENERATOR_APPLICATION1)

    tgSession2 = viavi_Basic_Functions.Connect_To_Port(TRAFFIC_GENERATOR_IP2, TRAFFIC_GENERATOR_SLOT2, TRAFFIC_GENERATOR_PORT2)
    viavi_Basic_Functions.load_Predefind_Application(tgSession2, TRAFFIC_GENERATOR_APPLICATION2)

    # Product name per device (A/B/C are different products) - used to build the LW node labels
    PRODUCT_NAMES = {}
    for ip in DEVICES_LIST:
        device_page = page.context.new_page()
        pl_login = PL_LoginPage(device_page)
        pl_login.goto(f"http://{ip}/")
        pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
        sleep(1)
        pl_main_screen_POM = PL_Main_Screen_POM(device_page)
        PRODUCT_NAMES[ip] = pl_main_screen_POM.get_system_product_name()

        if not pl_login.logout():
            raise AssertionError(f"Logout from {ip} GUI failed.")
        sleep(2)
        device_page.close()
        if not PRODUCT_NAMES[ip]:
            raise SystemExit(f"Could not read the product name of {ip} ❌")
    print(f"Product names: {PRODUCT_NAMES}\n")

    A, B, C = DEVICES_LIST[0], DEVICES_LIST[1], DEVICES_LIST[2]

    # Physical OTN topology (see Setup): A.U1-B.U2, A.U2-C.U1, B.U1-C.U2
    OTN_LINKS = [
        ((A, "Uplink 1"), (B, "Uplink 2")),
        ((A, "Uplink 2"), (C, "Uplink 1")),
        ((B, "Uplink 1"), (C, "Uplink 2")),
    ]

    # Every OTN service of the test: (name, path_key, A-node, port, LW type, client type, Z-node, protected, protection device)
    SERVICES = [
        (SERVICE_NAME1, SERVICE1_PATH, A, CLIENT_PORT_1, LW_SERVICE_TYPE1, CLIENT_SERVICE_TYPE1, B, True,  C),
        (SERVICE_NAME2, SERVICE2_PATH, B, CLIENT_PORT_2, LW_SERVICE_TYPE2, CLIENT_SERVICE_TYPE2, C, False, None),
        (SERVICE_NAME3, SERVICE3_PATH, C, CLIENT_PORT_3, LW_SERVICE_TYPE3, CLIENT_SERVICE_TYPE3, A, True,  B),
        (SERVICE_NAME4, SERVICE4_PATH, A, CLIENT_PORT_4, LW_SERVICE_TYPE4, CLIENT_SERVICE_TYPE4, B, False, None),
        (SERVICE_NAME5, SERVICE5_PATH, B, CLIENT_PORT_5, LW_SERVICE_TYPE5, CLIENT_SERVICE_TYPE5, C, True,  A),
        (SERVICE_NAME6, SERVICE6_PATH, C, CLIENT_PORT_6, LW_SERVICE_TYPE6, CLIENT_SERVICE_TYPE6, A, False, None),
        (SERVICE_NAME7, SERVICE7_PATH, A, CLIENT_PORT_7, LW_SERVICE_TYPE7, CLIENT_SERVICE_TYPE7, B, True,  C),
        (SERVICE_NAME8, SERVICE8_PATH, B, CLIENT_PORT_8, LW_SERVICE_TYPE8, CLIENT_SERVICE_TYPE8, C, False, None),
        (SERVICE_NAME9, SERVICE9_PATH, A, CLIENT_PORT_9, LW_SERVICE_TYPE9, CLIENT_SERVICE_TYPE9, B, False, None),
    ]

    # LW tributary slots table of every created service, keyed by SERVICEn_PATH
    service_paths = {}

    def create_service(spec):
        name, path_key, a_node, port, lw_type, _client_type, z_node, protected, protection_device = spec
        if protected:
            service_paths[path_key] = create_otn_service_protection(
                page, left_panel, service_provisioning, PRODUCT_NAMES,
                a_node, port, lw_type, z_node, port, name, protection_device)
        else:
            service_paths[path_key] = create_otn_service_unprotected(
                page, left_panel, service_provisioning, PRODUCT_NAMES,
                a_node, port, lw_type, z_node, port, name)

    def expected_service_row(spec, check_alert: bool = True) -> dict:
        name, _path_key, a_node, port, lw_type, _client_type, z_node, protected, _protection_device = spec
        expected = {
            "Name": name,
            "Start": lw_endpoint_label(a_node, port, PRODUCT_NAMES),
            "End": lw_endpoint_label(z_node, port, PRODUCT_NAMES),
            "Type": lw_type,
            "Consistency": "Yes",
            "Protection": "1+1" if protected else "No",
        }
        if check_alert:
            expected["Alert"] = "OK"
        return expected

    def open_otn_map():
        left_panel.click_network_topology()
        upper_panel.select_domain(DOMAIN_NAME)

    results = {}

    # ##################################################################
    # # Step 1 – Add domain and Factory default reset for all devices. #
    # ##################################################################
    # def step_1():
    #     left_panel.click_domain_management()
    #     domain_management.add_domain(DOMAIN_NAME)
    #     sleep(0.5) 

    #     for ip in DEVICES_LIST:
    #         device_page = page.context.new_page()
    #         pl_login = PL_LoginPage(device_page)
    #         pl_login.goto(f"http://{ip}/")
    #         pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
    #         sleep(1)

    #         pl_main_screen_POM = PL_Main_Screen_POM(device_page)
    #         pl_main_screen_POM.device_restart("factory")
    #         sleep(5)
    #         device_page.close()

    #     # Wait for devices to come back up after factory default reset
    #     devices_are_up(DEVICES_LIST, wait_time=WAIT)

    # results[1] = run_step(1, step_1, logger, report)

    # ################################################################################
    # # Step 2 – Login to the GUI of each IP.                                        #
    # # Set SNTP server and timezone to synchronize device time with LW server time. #                                   
    # ################################################################################
    # def step_2():
    #     def is_israel_dst():
    #         israel_time = datetime.now(ZoneInfo("Asia/Jerusalem"))
    #         return israel_time.dst() != timedelta(0)

    #     daylight_save = "Enabled" if is_israel_dst() else "Disabled"

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
    #         pl_main_screen.set_sntp_configuration(status="Enabled", gmt=GMT2, daylight_save=daylight_save)
    #         refresh_page(device_page)

    #         if not pl_login.logout():
    #             raise AssertionError(f"Logout from {ip} GUI failed.")
    #         sleep(2)
    #         device_page.close()

    # results[2] = run_step(2, step_2, logger, report)

    # ############################################################
    # # Step 3 – Discover every device in DEVICES_LIST (SNMPv2). #
    # ############################################################
    # def step_3():
    #     left_panel.click_device_discovery()
    #     device_discovery.click_SNMPv2()

    #     for ip in DEVICES_LIST:
    #         device_discovery.set_ip_address(ip)
    #         if not device_discovery.click_start_discovery():
    #             raise AssertionError(f"Start Discovery failed for {ip}.")
    #         sleep(1)

    #     countdown_sleep(WAIT, message="Wait for the discovered devices to be added")

    # results[3] = run_step(3, step_3, logger, report)

    # ##############################################
    # # Step 4 – Move every device to DOMAIN_NAME. #
    # ##############################################
    # def step_4():
    #     refresh_page(page) 
    #     for ip in DEVICES_LIST:
    #         left_panel.click_domain_management()
    #         domain_management.move_to_domain(source_item_name=ip, target_domain_name=DOMAIN_NAME)
    #         sleep(1)

    # results[4] = run_step(4, step_4, logger, report)

    # ########################################################################
    # # Step 5 – Verify every device was added to DOMAIN_NAME (Network Map). #
    # ########################################################################
    # def step_5():
    #     left_panel.click_network_topology()
    #     upper_panel.select_domain(DOMAIN_NAME)

    #     missing = [ip for ip in DEVICES_LIST if not network_topology.is_element_exist_on_navigation_info_list(ip)]
    #     network_topology.hide_navigation_info()

    #     if missing:
    #         raise AssertionError(f"Devices missing from domain '{DOMAIN_NAME}' on the Network Topology: {missing}")

    # results[5] = run_step(5, step_5, logger, report)

    # ##########################################################################
    # # Step 6 – Take OTN ownership of every device (NMS Owned false -> true). #
    # ##########################################################################
    # def step_6():
    #     open_otn_map()
    #     errors = [] 

    #     for ip in DEVICES_LIST:
    #         network_topology.show_navigation_info()
    #         network_topology.navigation_info_open_element_details(ip)
    #         network_topology.element_details_click_on_info()
    #         network_topology.device_element_details_info_click_on_general()

    #         before = _clean(network_topology.device_element_details_info_general_get_NMS_owned()).lower()
    #         if before != "false":
    #             errors.append(f"{ip}: NMS Owned before 'Manage Device OTN Services' is '{before}', expected 'false'.")

    #         network_topology.device_element_details_info_general_manage_device_OTN_services()
    #         sleep(2)

    #         after = _clean(network_topology.device_element_details_info_general_get_NMS_owned()).lower()
    #         if after != "true":
    #             errors.append(f"{ip}: NMS Owned after 'Manage Device OTN Services' is '{after}', expected 'true'.")

    #         # print(f"   {ip}: NMS Owned {before} -> {after}")
    #         network_topology.navigation_info_close_element_details()

    #     if errors:
    #         raise AssertionError(" | ".join(errors))

    # results[6] = run_step(6, step_6, logger, report)

    # ################################################################################
    # # Step 7 – Set the uplinks (service type + admin Up) and client ports 1 and 2. #
    # ################################################################################
    # def step_7():
    #     for ip in DEVICES_LIST:
    #         device_page, pl_main_screen = open_device(page, ip)
    #         try:
    #             set_port_service_type(pl_main_screen, ip, UPLINK_PORT_1, UPLINK_SERVICE_TYPE1)
    #             set_port_admin_up(pl_main_screen, ip, UPLINK_PORT_1)
    #             set_port_service_type(pl_main_screen, ip, UPLINK_PORT_2, UPLINK_SERVICE_TYPE2)
    #             set_port_admin_up(pl_main_screen, ip, UPLINK_PORT_2)
    #         finally:
    #             logout_from_device(device_page, ip)
    #             device_page.close()

    #     for ip in DEVICES_LIST:
    #         device_page, pl_main_screen = open_device(page, ip)
    #         try:
    #             set_port_service_type(pl_main_screen, ip, CLIENT_PORT_1, CLIENT_SERVICE_TYPE1)
    #             set_port_service_type(pl_main_screen, ip, CLIENT_PORT_2, CLIENT_SERVICE_TYPE2)
    #         finally:
    #             logout_from_device(device_page, ip)
    #             device_page.close()

    # results[7] = run_step(7, step_7, logger, report)

    # ##########################################################################################
    # # Step 8 – Service 1 (A->B, 1+1 via C) + Service 2 (B->C, unprotected).                  #
    # # Admin Up the client ports, verify the OTN links on the map and both Service List rows. #
    # ##########################################################################################
    # def step_8():
    #     left_panel.click_network_topology()
    #     upper_panel.select_domain(DOMAIN_NAME)
    #     errors = []

    #     create_service(SERVICES[0])
    #     create_service(SERVICES[1])

    #     admin_up_ports = {A: [CLIENT_PORT_1], B: [CLIENT_PORT_1, CLIENT_PORT_2], C: [CLIENT_PORT_2]}
    #     for ip in DEVICES_LIST:
    #         device_page, pl_main_screen = open_device(page, ip)
    #         try:
    #             for port in admin_up_ports[ip]:
    #                 set_port_admin_up(pl_main_screen, ip, port)
    #         finally:
    #             logout_from_device(device_page, ip)
    #             device_page.close()

    #     # OTN links - polled, the map needs a moment to report them positive
    #     refresh_page(page)
    #     open_otn_map()
    #     network_topology.enable_OTN()

    #     for ip in DEVICES_LIST:
    #         expected_links = [link for link in OTN_LINKS if ip in (link[0][0], link[1][0])]
    #         deadline = time.time() + LINKS_TIMEOUT
    #         while True:
    #             network_topology.show_navigation_info()
    #             network_topology.navigation_info_open_element_details(ip)
    #             ip_links = network_topology.element_details_links_get_links_table()
    #             network_topology.navigation_info_close_element_details()

    #             missing = [link for link in expected_links if not has_otn_link(ip_links, link[0][0], link[0][1], link[1][0], link[1][1])]
    #             if not missing or time.time() >= deadline:
    #                 break
    #             countdown_sleep(WAIT, message=f"{ip}: waiting for the OTN links to turn positive")
    #             refresh_page(page)
    #             open_otn_map()
    #             network_topology.enable_OTN()

    #         # print(f"   {ip} links: {ip_links}")
    #         for (ip1, up1), (ip2, up2) in missing:
    #             errors.append(f"{ip}: no positive OTN link {ip1} {up1} <-> {ip2} {up2}.")

    #     # Service List
    #     for spec in SERVICES[:2]:
    #         errors += check_service_row(left_panel, service_list, expected_service_row(spec))

    #     if errors:
    #         raise AssertionError(" | ".join(errors))

    # results[8] = run_step(8, step_8, logger, report)

    # #############################################################################
    # # Steps 9-15 – Services 3-9: set the client port service type on both ends, #
    # # then create the service and verify the device provisioning.               #
    # #############################################################################
    # def make_service_step(spec):
    #     def step():
    #         left_panel.click_network_topology()
    #         upper_panel.select_domain(DOMAIN_NAME)

    #         name, _path_key, a_node, port, _lw_type, client_type, z_node, _protected, _protection_device = spec
    #         configure_client_port(page, [a_node, z_node], port, client_type)
    #         create_service(spec)
    #     return step

    # for step_num, spec in zip(range(9, 16), SERVICES[2:]):
    #     results[step_num] = run_step(step_num, make_service_step(spec), logger, report)

    # ###############################################################################
    # # Step 16 – Service List audit of all 9 services                              #
    # # (Start / End / Type / Protection / Consistency, Alert only for the services #
    # # that have the traffic generators attached - 1 and 2).                       #
    # ###############################################################################
    # def step_16():
    #     errors = []
    #     for index, spec in enumerate(SERVICES):
    #         errors += check_service_row(left_panel, service_list, expected_service_row(spec, check_alert=index < 2))
    #     if errors:
    #         raise AssertionError(" | ".join(errors))

    # results[16] = run_step(16, step_16, logger, report)

    # ###################################################################################
    # # Step 17 – Tributary slots audit across all services (LW data):                  #
    # # every hop of a service uses the same number of slots, and no two services share #
    # # a tributary slot on the same device uplink.                                     #
    # ###################################################################################
    # def step_17():
    #     errors = []
    #     owners = {}  # (ip, uplink, slot) -> service name

    #     for name, path_key, *_rest in SERVICES:
    #         service_path = service_paths.get(path_key)
    #         if not service_path:
    #             errors.append(f"{name}: no tributary slots table was collected (service creation failed?).")
    #             continue

    #         for section_name in ("Working", "Protection"):
    #             blocks = get_path_section(service_path, section_name)
    #             sizes = {len(lw_block_slots(block)) for block in blocks}
    #             if 0 in sizes:
    #                 errors.append(f"{name} / {section_name}: a hop has no selected tributary slots.")
    #             if len(sizes) > 1:
    #                 errors.append(f"{name} / {section_name}: hops use a different number of slots {sorted(sizes)}.")

    #             for block in blocks:
    #                 m = IP_RE.search(block.get("device", ""))
    #                 ip = m.group(1) if m else block.get("device", "")
    #                 for slot in lw_block_slots(block):
    #                     key = (ip, block.get("uplink", ""), str(slot))
    #                     if key in owners and owners[key] != name:
    #                         errors.append(f"{ip} {key[1]} slot {slot} is used by both '{owners[key]}' and '{name}'.")
    #                     owners.setdefault(key, name)

    #     print(f"   {len(owners)} (device, uplink, slot) allocations checked.")
    #     if errors:
    #         raise AssertionError(" | ".join(errors))

    # results[17] = run_step(17, step_17, logger, report)

    # ############################################################################
    # # Step 18 – Fault propagation, Service 1: T.G_1 laser off -> Alert not OK, #
    # # laser on -> Alert back to OK.                                            #
    # ############################################################################
    # def step_18():
    #     viavi_Basic_Functions.Set_Laser(tgSession1, State='off')
    #     try:
    #         alert = wait_for_service_alert(left_panel, service_list, SERVICE_NAME1, want_ok=False, timeout_s=ALERT_TIMEOUT)
    #         # print(f"   {SERVICE_NAME1}: Alert with T.G_1 laser off = '{alert}'")
    #     finally:
    #         viavi_Basic_Functions.Set_Laser(tgSession1, State='on')

    #     refresh_page(page)
    #     alert = wait_for_service_alert(left_panel, service_list, SERVICE_NAME1, want_ok=True, timeout_s=ALERT_TIMEOUT)
    #     # print(f"   {SERVICE_NAME1}: Alert with T.G_1 laser on = '{alert}'")

    # results[18] = run_step(18, step_18, logger, report)

    # ############################################################################
    # # Step 19 – Fault propagation, Service 2: T.G_2 laser off -> Alert not OK, #
    # # laser on -> Alert back to OK.                                            #
    # ############################################################################
    # def step_19():
    #     viavi_Basic_Functions.Set_Laser(tgSession2, State='off')
    #     try:
    #         alert = wait_for_service_alert(left_panel, service_list, SERVICE_NAME2, want_ok=False, timeout_s=ALERT_TIMEOUT)
    #         # print(f"   {SERVICE_NAME2}: Alert with T.G_2 laser off = '{alert}'")
    #     finally:
    #         viavi_Basic_Functions.Set_Laser(tgSession2, State='on')

    #     alert = wait_for_service_alert(left_panel, service_list, SERVICE_NAME2, want_ok=True, timeout_s=ALERT_TIMEOUT)
    #     # print(f"   {SERVICE_NAME2}: Alert with T.G_2 laser on = '{alert}'")

    # results[19] = run_step(19, step_19, logger, report)

    # ##################################################################################
    # # Step 20 – Negative: LW must not let a second OTN service use an occupied port  #
    # # (A Port 1 already carries Service 1). The wizard must stop before the          #
    # # tributary slots step; the service is never created.                            #
    # ##################################################################################
    # def step_20():
    #     left_panel.click_network_topology()
    #     upper_panel.select_domain(DOMAIN_NAME)
    #     name = "NEGATIVE-OCCUPIED-PORT"
    #     reached_checkout = False
    #     port_stage = False  # failures before choosing the occupied port are real errors, not LW blocking it
    #     try:
    #         left_panel.click_service_provisioning()
    #         service_provisioning.create_OTN_service()
    #         service_provisioning.set_OTN_A_node(lw_node_label(A, PRODUCT_NAMES))
    #         port_stage = True
    #         service_provisioning.set_OTN_A_port(lw_port_label(CLIENT_PORT_1))
    #         service_provisioning.set_OTN_service_type(LW_SERVICE_TYPE1)
    #         service_provisioning.OTN_service_click_next()
    #         service_provisioning.set_OTN_Z_node(lw_node_label(B, PRODUCT_NAMES))
    #         service_provisioning.set_OTN_Z_port(lw_port_label(CLIENT_PORT_1))
    #         service_provisioning.set_OTN_service_name(name)
    #         service_provisioning.enable_OTN_auto_path()
    #         service_provisioning.OTN_service_click_next()
    #         service_provisioning.get_tributary_slots_table(timeout_ms=5000)
    #         reached_checkout = True
    #     except AssertionError as e:
    #         if not port_stage:
    #             raise AssertionError(f"The wizard failed before the occupied port could be tried: {e}")
    #         print(f"LW blocked the occupied port as expected: {e}")
    #     finally:
    #         refresh_page(page)  # leave the wizard without creating anything

    #     if reached_checkout:
    #         raise AssertionError(f"LW offered tributary slots for a second service on the occupied {A} Port {CLIENT_PORT_1}.")

    #     if get_service_row(left_panel, service_list, name) is not None:
    #         raise AssertionError(f"'{name}' was created on an occupied port.")

    # results[20] = run_step(20, step_20, logger, report)

    # #####################################################################################
    # # Step 21 – Alarms: for every service, the alarms the Start / End devices raised   #
    # # on the service port since the script started must all be in its LW Alarms list. #
    # #####################################################################################
    # def step_21():
    #     left_panel.click_network_topology()
    #     upper_panel.select_domain(DOMAIN_NAME)

    #     errors = verify_service_faults_on_devices(page, left_panel, service_list, "Alarms")
    #     if errors:
    #         raise AssertionError(" | ".join(errors))

    # results[21] = run_step(21, step_21, logger, report)

    # #####################################################################################
    # # Step 22 – Events: for every service, the events the Start / End devices raised   #
    # # on the service port since the script started must all be in its LW Events list. #
    # #####################################################################################
    # def step_22():
    #     left_panel.click_network_topology()
    #     upper_panel.select_domain(DOMAIN_NAME)

    #     errors = verify_service_faults_on_devices(page, left_panel, service_list, "Events")
    #     if errors:
    #         raise AssertionError(" | ".join(errors))

    # results[22] = run_step(22, step_22, logger, report)

    #####################################################################################
    # Step 23 – PMs: for every service, the PM intervals of the Start (A) / End (Z)      #
    # devices on the service port - every PM period and PM type - must be in the        #
    # service's LW Performance table with the same values (Days: yesterday,             #
    # 15 Minutes: today's intervals that LW has already polled).                         #
    #####################################################################################
    def step_23():
        errors = verify_service_pms_on_devices(page, left_panel, service_list)
        if errors:
            raise AssertionError(" | ".join(errors))

    results[23] = run_step(23, step_23, logger, report)

    ##################################################################################
    # Step 24 – Delete all: remove every service, release the OTN ownership of every #
    # device (NMS Owned true -> false), remove the devices and the domain.           #
    ##################################################################################
    def step_24():
        errors = []

        # 1) Remove every service of the domain
        refresh_page(page)
        left_panel.click_service_list()
        service_list.select_domain_or_chassis(DOMAIN_NAME)
        service_list.set_service_name("")
        names = [_clean(row.get("Name")) for row in service_list.get_service_list()]
        # print(f"Removing {len(names)} services: {names}")

        for name in names:
            try:
                refresh_page(page)
                service_list.select_domain_or_chassis(DOMAIN_NAME)
                sleep(1)
                service_list.click_on_service(service_name=name)
                sleep(1)
                service_list.remove_service(service_name=name)
                sleep(1)
            except AssertionError as e:
                errors.append(f"remove '{name}' failed: {e}")

        left_panel.click_service_list()
        service_list.select_domain_or_chassis(DOMAIN_NAME)
        service_list.set_service_name("")
        left = [_clean(row.get("Name")) for row in service_list.get_service_list()]
        if left:
            errors.append(f"services still in the Service List after removing: {left}")

        # 2) Release the OTN ownership of every device (NMS Owned true -> false)
        left_panel.click_network_topology()
        upper_panel.select_domain(DOMAIN_NAME)
        for ip in DEVICES_LIST:
            try:
                network_topology.show_navigation_info()
                network_topology.navigation_info_open_element_details(ip)
                network_topology.element_details_click_on_info()
                network_topology.device_element_details_info_click_on_general()

                before = _clean(network_topology.device_element_details_info_general_get_NMS_owned()).lower()
                if before != "true":
                    errors.append(f"{ip}: NMS Owned before 'Release Device OTN Services' is '{before}', expected 'true'.")

                network_topology.device_element_details_info_general_release_device_OTN_services()
                sleep(2)

                after = _clean(network_topology.device_element_details_info_general_get_NMS_owned()).lower()
                if after != "false":
                    errors.append(f"{ip}: NMS Owned after 'Release Device OTN Services' is '{after}', expected 'false'.")

                # print(f"   {ip}: NMS Owned {before} -> {after}")
                network_topology.navigation_info_close_element_details()
            except AssertionError as e:
                errors.append(f"{ip}: release OTN ownership failed: {e}")

        # 3) Remove the devices, then the domain
        left_panel.click_domain_management()
        for ip in DEVICES_LIST:
            try:
                domain_management.remove_device(ip, parent_domain_name=DOMAIN_NAME)
            except AssertionError as e:
                errors.append(f"remove device {ip} failed: {e}")
            refresh_page(page)

        try:
            domain_management.remove_domain(domain_name=DOMAIN_NAME)
        except AssertionError as e:
            errors.append(f"remove domain '{DOMAIN_NAME}' failed: {e}")

        if errors:
            raise AssertionError(" | ".join(errors))

    results[24] = run_step(24, step_24, logger, report)

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

        browser, context, page = create_page(p, max_size=True)

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

        test_OTN_2000ADS_2000GA_2000GM(page, left_panel, logger, report)

        context.close()
        browser.close()
        close_report(report)

    end_time = time.perf_counter()
    print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
    logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")