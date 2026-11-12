"""
Created by: Yuval Dahan
Date: 29/10/2026

Comprehensive Inventory Test
=====================================================
Tests the Inventory tab: Filter By (Default / Device / Chassis), Quick filter, Whole word,
Expand / Expand All / Collapse All and Refresh, and verifies that the inventory LW shows
for each device matches the inventory on the device's own GUI.

*** Runtime: approximately -- minutes ***
=====================================================

Notes:
---------------------------------------------------------------------------------------------------------------------
1. Every device in DEVICES_LIST must be reachable via SNMPv2 and via its web GUI (DEVICE_IP_USER / DEVICE_IP_PASS).
2. Step 7 assigns the chassis IDs 1999, 1998, ... (one per device) - make sure they are not in use on the LW server.
3. The last step removes the devices, chassis and domain from LW and clears the chassis ID on the devices.
---------------------------------------------------------------------------------------------------------------------
"""

from playwright.sync_api import sync_playwright

from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.upper_panel import UpperPanel
from Pages.device_discovery import DeviceDiscovery
from Pages.network_topology import NetworkTopology
from Pages.inventory import Inventory
from Pages.domain_management import DomainManagement
from Pages.system_operations import SystemOperationsPage
from PL_Devices.PL_Pages_New_Gui.PL_login_page_new_gui import PL_LoginPage
from PL_Devices.PL_Pages_New_Gui.PL_main_screen_POM_new_gui import PL_Main_Screen_POM
from Utils.utils import refresh_page, countdown_sleep, create_page, devices_are_up
import time
from time import sleep
import random
import re
from collections import Counter
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

    # LW_SERVER_HOST_IP  = "172.16.10.22:8080"
    LW_SERVER_HOST_IP = "172.16.10.22:8443"
    LW_USERNAME = "administrator"
    LW_PASSWORD = "administrator"

    DEVICE_IP_USER = "tech"
    DEVICE_IP_PASS = "packetlight"

    DOMAIN_NAME = "Inventory_Domain"

    DEVICES_LIST = ['172.16.20.125', '172.16.40.30', '172.16.20.101', '172.16.30.118']



# ================================================================
# Values that should not be changed
# ================================================================

# The LW server answers HTTPS on 8443 and HTTP on 8080
BASE_URL = f"{'https' if LW_SERVER_HOST_IP.endswith(':8443') else 'http'}://{LW_SERVER_HOST_IP}/"
WAIT = 10
FILTER_WAIT = 2  # seconds for the table to re-render after a filter change

FILTERS_LIST = ['Default', 'Device', 'Chassis']
FIRST_CHASSIS_ID = 1999
NON_EXISTING_FILTER = "NoSuchInventoryEntity_12345"

LOGGER_ROOT_DIRECTORY = 'G:\\Python\\PacketLight Automation\\LightWatch_WEB\\Scripts\\Inventory\\LogFiles'
LOGGER_DIRECTORY_NAME = "Inventory"
LOG_FILE_NAME = 'Inventory.log'
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

def open_inventory(left_panel: LeftPanel):
    """
    Open Inventory via LeftPanel and assert it opened.
    """
    try:
        ok = left_panel.click_inventory()
    except Exception as e:
        raise AssertionError(f"Failed to call left_panel.click_inventory(). Error: {e}")

    if ok is not True:
        raise AssertionError(
            "left_panel.click_inventory() returned False "
            "(Inventory did not open).")

def extract_device_name_and_device_ip(device_str: str) -> tuple:
    """
    'PL-2000GM (172.16.20.125)' -> ('PL-2000GM', '172.16.20.125')
    """
    m = re.match(r"^\s*(.*?)\s*\(\s*([\d.]+)\s*\)\s*$", device_str or "")
    if not m:
        return (device_str or "").strip(), ""
    return m.group(1), m.group(2)

def get_device_types_occurrences(devices_list: list) -> dict:
    """
    ['PL-2000GM (172.16.20.125)', 'PL-4000G (172.16.30.51)', 'PL-4000G (172.16.30.52)']
    -> {'PL-2000GM': 1, 'PL-4000G': 2}
    """
    return dict(Counter(extract_device_name_and_device_ip(d)[0] for d in devices_list))

def expected_quick_filter_count(device_type: str, occurrences: dict) -> int:
    """
    The Quick filter is a case-insensitive "contains" match, so 'PL-1000G' also matches 'PL-1000GIL'.
    Expected number of devices = occurrences of every type that contains `device_type`.
    For types that are not a substring of another type this equals occurrences[device_type].
    """
    needle = device_type.lower()
    return sum(n for t, n in occurrences.items() if needle in t.lower())

def get_domain_devices_list(left_panel: LeftPanel, domain_management: DomainManagement) -> list:
    """
    Open Domain Management and return the devices under DOMAIN_NAME ('NAME (IP)' strings).
    """
    left_panel.click_domain_management()
    devices_list = domain_management.get_devices_list_per_domain(DOMAIN_NAME)
    if not devices_list:
        raise AssertionError(f"No devices found under domain '{DOMAIN_NAME}'.")
    return devices_list

def set_filter_by(inventory: Inventory, filter_name: str):
    if not inventory.set_filterBy(filter_name):
        raise AssertionError(f"Failed to set Filter By to '{filter_name}'.")
    sleep(FILTER_WAIT)

def set_quick_filter(inventory: Inventory, value: str):
    if not inventory.set_quick_filter(value):
        raise AssertionError(f"Failed to set Quick filter to '{value}'.")
    sleep(FILTER_WAIT)

def count_devices(inventory: Inventory) -> int:
    count = inventory.get_number_of_devices_on_inventory_list()
    if count < 0:
        raise AssertionError("Failed to read the number of devices on the inventory list.")
    return count

def listed_device_ips(inventory: Inventory) -> list:
    """IP addresses of the entity (chassis) rows currently in the table."""
    return [r["ip_address"] for r in inventory.get_all_inventory_list() if not r["is_child"]]

def _norm(value) -> str:
    value = " ".join(str(value or "").split())
    # An unprogrammed EEPROM field reads back as all 0xFF bytes ('ff:ff:ff:...'): LW shows it
    # as-is (that's what the MIB returns) while the device GUI shows it empty - treat it as empty
    if re.fullmatch(r"(?i)f+(?:[:\-\s]f+)*", value):
        return ""
    return "" if value in ("--", "-", "N/A", "NA") else value

# Device GUI inventory column -> LW inventory column
INVENTORY_FIELDS_MAP = {
    "Name": "entity",
    "Description": "description",
    "Serial Number": "serial_no",
    "Hardware Rev": "hw_ver",
    "Part Number": "part_number",
    "Manufacturer": "manufacturer",
}

def compare_inventory_lists(ip: str, device_inventory: list, lw_inventory: list) -> list:
    """
    Match every row of the device's own inventory to an LW row (by serial number, else by name)
    and compare the shared fields. LW child rows must all exist on the device too; the LW chassis
    row is allowed to be missing from the device table.
    Returns a list of mismatch descriptions (empty when the lists match).
    """
    errors = []
    unmatched_lw = list(lw_inventory)

    def lw_key(row):
        return _norm(row.get("serial_no")) or _norm(row.get("entity"))

    for dev_row in device_inventory:
        key = _norm(dev_row.get("Serial Number")) or _norm(dev_row.get("Name"))
        lw_row = next((r for r in unmatched_lw if lw_key(r) == key), None)
        if lw_row is None:
            # Serial numbers differ - pair by name so the difference is reported as a field mismatch
            name = _norm(dev_row.get("Name"))
            lw_row = next((r for r in unmatched_lw if _norm(r.get("entity")) == name), None)
        if lw_row is None:
            errors.append(f"[{ip}] '{dev_row.get('Name')}' (S/N '{dev_row.get('Serial Number')}') "
                          f"is on the device but missing on LW.")
            continue
        unmatched_lw.remove(lw_row)

        for dev_field, lw_field in INVENTORY_FIELDS_MAP.items():
            dev_val, lw_val = _norm(dev_row.get(dev_field)), _norm(lw_row.get(lw_field))
            if dev_val != lw_val:
                errors.append(f"[{ip}] '{dev_row.get('Name')}' {dev_field} mismatch: "
                              f"device='{dev_val}', LW='{lw_val}'.")

    for lw_row in unmatched_lw:
        if lw_row.get("is_child"):
            errors.append(f"[{ip}] '{lw_row.get('entity')}' (S/N '{lw_row.get('serial_no')}') "
                          f"is on LW but missing on the device.")

    return errors

def match_inventory_lists(page, inventory: Inventory, ip: str, device_inventory_cache: dict):
    """
    Compare the inventory of `ip` on LW (current Inventory filter) to the device's own GUI inventory.
    The device inventory is read once per IP (login to the device GUI) and cached.
    Raises AssertionError on mismatch.
    """
    if ip not in device_inventory_cache:
        device_page = page.context.new_page()
        try:
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            if not pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS):
                raise AssertionError(f"Login to {ip} GUI failed.")
            device_inventory = PL_Main_Screen_POM(device_page).get_inventory_list()
            if not device_inventory:
                raise AssertionError(f"Failed to read the inventory list from the {ip} GUI.")
            device_inventory_cache[ip] = device_inventory
        finally:
            device_page.close()

    lw_inventory = inventory.get_entity_inventory_list(ip)
    if not lw_inventory:
        raise AssertionError(f"Failed to read the inventory of {ip} on LW.")

    errors = compare_inventory_lists(ip, device_inventory_cache[ip], lw_inventory)
    if errors:
        raise AssertionError("Inventory mismatch between LW and device:\n  " + "\n  ".join(errors))
    print(f"   {ip}: LW inventory matches the device ({len(device_inventory_cache[ip])} entries) ✅")

def find_chassis_of_device_type(inventory: Inventory, device_type: str, state: dict) -> str:
    """
    Return a chassis (as shown in the Chassis dropdown) that holds a device of `device_type`.
    Filter By must already be 'Chassis'.
    """
    for ip, chassis in state['chassis_by_ip'].items():
        if any(extract_device_name_and_device_ip(d) == (device_type, ip) for d in state['domain_devices']):
            return chassis

    for chassis in inventory.get_chassis_list():
        if not inventory.set_chassis(chassis):
            continue
        set_quick_filter(inventory, device_type)
        if count_devices(inventory) > 0:
            return chassis
    raise AssertionError(f"No chassis with a '{device_type}' device was found.")

def select_filter_scope(inventory: Inventory, filter_name: str, device_type: str, state: dict) -> str:
    """
    Set Filter By to `filter_name`. For 'Device' / 'Chassis' also select a device / chassis
    that contains a device of `device_type`. Returns a description of the selected scope.
    """
    set_filter_by(inventory, filter_name)

    if filter_name == FILTERS_LIST[1]:
        ip = next(ip for d in state['domain_devices']
                  for name, ip in [extract_device_name_and_device_ip(d)] if name == device_type)
        if not inventory.set_devices(ip):
            raise AssertionError(f"Failed to select device '{ip}'.")
        sleep(FILTER_WAIT)
        return f"Device {ip}"

    if filter_name == FILTERS_LIST[2]:
        chassis = find_chassis_of_device_type(inventory, device_type, state)
        if not inventory.set_chassis(chassis):
            raise AssertionError(f"Failed to select chassis '{chassis}'.")
        sleep(FILTER_WAIT)
        return chassis

    return filter_name

# ================================================================
# Main test
# ================================================================

def test_inventory(page, left_panel: LeftPanel, logger, report):
    device_discovery  = DeviceDiscovery(page)
    inventory  = Inventory(page)
    domain_management = DomainManagement(page)
    network_topology = NetworkTopology(page)
    system_operations = SystemOperationsPage(page)
    upper_panel = UpperPanel(page)

    results = {}
    state = {
        'device_inventory_cache': {},   # ip -> inventory read from the device GUI
        'chassis_by_ip': {},            # ip -> 'Chassis: <id>' assigned in step 7
        'domain_devices': [],           # 'NAME (IP)' strings under DOMAIN_NAME
        'random_element_type': None,
    }

    def refresh_domain_devices():
        state['domain_devices'] = get_domain_devices_list(left_panel, domain_management)
        return get_device_types_occurrences(state['domain_devices'])

    def pick_random_element_type(occurrences: dict) -> str:
        if not state['random_element_type'] or state['random_element_type'] not in occurrences:
            state['random_element_type'] = random.choice(list(occurrences))
        print(f"   random_element_type = '{state['random_element_type']}'")
        return state['random_element_type']

    ##################################################################
    # Step 1 – Add domain and Factory default reset for all devices. #
    ##################################################################
    def step_1():
        left_panel.click_domain_management()
        domain_management.add_domain(DOMAIN_NAME)
        sleep(0.5) 

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

    results[1] = run_step(1, step_1, logger, report)

    ############################################################
    # Step 2 – Discover every device in DEVICES_LIST (SNMPv2). #
    ############################################################
    def step_2():
        left_panel.click_device_discovery()
        device_discovery.click_SNMPv2()

        for ip in DEVICES_LIST:
            device_discovery.set_ip_address(ip)
            if not device_discovery.click_start_discovery():
                raise AssertionError(f"Start Discovery failed for {ip}.")
            sleep(1)

        left_panel.click_system_operations()
        system_operations.click_synchronize_inventory()

        countdown_sleep(WAIT, message="Wait for the discovered devices to be added")

    results[2] = run_step(2, step_2, logger, report)

    ##############################################
    # Step 3 – Move every device to DOMAIN_NAME. #
    ##############################################
    def step_3():
        refresh_page(page)
        for ip in DEVICES_LIST:
            left_panel.click_domain_management()
            domain_management.move_to_domain(source_item_name=ip, target_domain_name=DOMAIN_NAME)
            sleep(1)

    results[3] = run_step(3, step_3, logger, report)

    ########################################################################
    # Step 4 – Verify every device was added to DOMAIN_NAME (Network Map). #
    ########################################################################
    def step_4():
        left_panel.click_network_topology()
        upper_panel.select_domain(DOMAIN_NAME)

        missing = [ip for ip in DEVICES_LIST if not network_topology.is_element_exist_on_navigation_info_list(ip)]
        network_topology.hide_navigation_info()

        if missing:
            raise AssertionError(f"Devices missing from domain '{DOMAIN_NAME}' on the Network Topology: {missing}")

    results[4] = run_step(4, step_4, logger, report)

    #######################################################################
    # Step 5 – Filter By Default: device count, IP list, and inventory    #
    #          of each device matches the device's own GUI.               #
    #######################################################################
    def step_5():
        left_panel.click_system_operations()
        system_operations.click_synchronize_inventory()
        refresh_page(page)

        upper_panel.select_domain(DOMAIN_NAME)
        open_inventory(left_panel)
        sleep(WAIT)
        set_filter_by(inventory, FILTERS_LIST[0])

        count = count_devices(inventory)
        if count != len(DEVICES_LIST):
            raise AssertionError(f"Number of devices on the inventory list is {count}, expected {len(DEVICES_LIST)}.")

        listed_ips = listed_device_ips(inventory)
        if sorted(listed_ips) != sorted(DEVICES_LIST):
            raise AssertionError(f"Inventory list IPs {sorted(listed_ips)} do not match DEVICES_LIST {sorted(DEVICES_LIST)}.")

        for ip in DEVICES_LIST:
            match_inventory_lists(page, inventory, ip, state['device_inventory_cache'])

    results[5] = run_step(5, step_5, logger, report)

    ##################################################################
    # Step 6 – Filter By Device: inventory of each device matches    #
    #          the device's own GUI.                                 #
    ##################################################################
    def step_6():
        upper_panel.select_domain(DOMAIN_NAME)
        open_inventory(left_panel)
        errors = []
        for ip in DEVICES_LIST:
            set_filter_by(inventory, FILTERS_LIST[1])
            if not inventory.set_devices(ip):
                errors.append(f"Failed to select device '{ip}'.")
                continue
            sleep(FILTER_WAIT)
            try:
                match_inventory_lists(page, inventory, ip, state['device_inventory_cache'])
            except AssertionError as e:
                errors.append(str(e))

        if errors:
            raise AssertionError("\n".join(errors))

    results[6] = run_step(6, step_6, logger, report)

    ##############################################################################
    # Step 7 – Give every device its own chassis ID (1999, 1998, ...), then      #
    #          Filter By Chassis: each chassis lists its device, and the device  #
    #          inventory matches the device's own GUI.                           #
    ##############################################################################
    def step_7():
        upper_panel.select_domain(DOMAIN_NAME)
        devices_in_domain = get_domain_devices_list(left_panel, domain_management)
        if len(devices_in_domain) != len(DEVICES_LIST):
            raise AssertionError(f"Domain '{DOMAIN_NAME}' holds {len(devices_in_domain)} devices, expected {len(DEVICES_LIST)}.")

        number_of_chassis = FIRST_CHASSIS_ID
        for ip in DEVICES_LIST:
            domain_management.change_CHASSIS_ID(element_name=ip, to_mode="new", new_chassis_id=number_of_chassis)
            state['chassis_by_ip'][ip] = f"Chassis: {number_of_chassis}"
            number_of_chassis -= 1

        open_inventory(left_panel)
        set_filter_by(inventory, FILTERS_LIST[2])
        chassis_list_values = inventory.get_chassis_list()
        print(f"   chassis_list_values = {chassis_list_values}")

        missing = [c for c in state['chassis_by_ip'].values() if c not in chassis_list_values]
        if missing:
            raise AssertionError(f"Chassis missing from the Chassis dropdown: {missing}")

        errors = []
        for chassis in chassis_list_values:
            if not inventory.set_chassis(chassis):
                errors.append(f"Failed to select chassis '{chassis}'.")
                continue
            sleep(FILTER_WAIT)

            listed_ips = listed_device_ips(inventory)
            expected_ips = [ip for ip, c in state['chassis_by_ip'].items() if c == chassis]
            if expected_ips and sorted(listed_ips) != sorted(expected_ips):
                errors.append(f"{chassis} lists {listed_ips}, expected {expected_ips}.")

            for ip in listed_ips:
                if ip not in DEVICES_LIST:
                    continue
                try:
                    match_inventory_lists(page, inventory, ip, state['device_inventory_cache'])
                except AssertionError as e:
                    errors.append(str(e))

        if errors:
            raise AssertionError("\n".join(errors))

    results[7] = run_step(7, step_7, logger, report)

    ##############################################################################
    # Step 8 – Filter By Default + Quick filter by device type (as-is and lower  #
    #          case): the number of devices matches the occurrences in domain.   #
    ##############################################################################
    def step_8():
        occurrences = refresh_domain_devices()
        print(f"   device types = {occurrences}")

        upper_panel.select_domain(DOMAIN_NAME)
        open_inventory(left_panel)
        inventory.uncheck_whole_word()
        set_filter_by(inventory, FILTERS_LIST[0])

        errors = []
        for device_type in occurrences:
            expected = expected_quick_filter_count(device_type, occurrences)
            for value in (device_type, device_type.lower()):
                set_quick_filter(inventory, value)
                count = count_devices(inventory)
                if count != expected:
                    errors.append(f"Quick filter '{value}': {count} devices, expected {expected}.")

        set_quick_filter(inventory, "")
        if errors:
            raise AssertionError("\n".join(errors))

    results[8] = run_step(8, step_8, logger, report)

    ##########################################################################
    # Step 9 – Filter By Device: exactly one device is listed per device.    #
    ##########################################################################
    def step_9():
        upper_panel.select_domain(DOMAIN_NAME)
        open_inventory(left_panel)
        errors = []
        for ip in DEVICES_LIST:
            set_filter_by(inventory, FILTERS_LIST[1])
            if not inventory.set_devices(ip):
                errors.append(f"Failed to select device '{ip}'.")
                continue
            sleep(FILTER_WAIT)

            count = count_devices(inventory)
            if count != 1:
                errors.append(f"Device '{ip}': {count} devices listed, expected 1.")
            elif listed_device_ips(inventory) != [ip]:
                errors.append(f"Device '{ip}': listed {listed_device_ips(inventory)}.")

        if errors:
            raise AssertionError("\n".join(errors))

    results[9] = run_step(9, step_9, logger, report)

    ##############################################################################
    # Step 10 – Filter By Chassis + Quick filter by device type (as-is and lower #
    #           case): summed over the chassis, the number of devices matches    #
    #           the occurrences in the domain.                                   #
    ##############################################################################
    def step_10():
        occurrences = refresh_domain_devices()

        upper_panel.select_domain(DOMAIN_NAME)
        open_inventory(left_panel)
        inventory.uncheck_whole_word()
        set_filter_by(inventory, FILTERS_LIST[2])

        # Only one chassis is shown at a time - sum the matches over the domain's chassis
        chassis_list = list(dict.fromkeys(state['chassis_by_ip'].values())) or inventory.get_chassis_list()
        if not chassis_list:
            raise AssertionError("Chassis list is empty.")

        errors = []
        for device_type in occurrences:
            expected = expected_quick_filter_count(device_type, occurrences)
            for value in (device_type, device_type.lower()):
                total = 0
                for chassis in chassis_list:
                    if not inventory.set_chassis(chassis):
                        raise AssertionError(f"Failed to select chassis '{chassis}'.")
                    set_quick_filter(inventory, value)
                    total += count_devices(inventory)
                if total != expected:
                    errors.append(f"Quick filter '{value}': {total} devices over {chassis_list}, expected {expected}.")

        set_quick_filter(inventory, "")
        if errors:
            raise AssertionError("\n".join(errors))

    results[10] = run_step(10, step_10, logger, report)

    #################################################################
    # Step 11 – For each Filter By + Quick filter of a random type: #
    #           expanding the first row works.                      #
    #################################################################
    def step_11():
        occurrences = refresh_domain_devices()
        random_element_type = pick_random_element_type(occurrences)

        upper_panel.select_domain(DOMAIN_NAME)
        open_inventory(left_panel)
        inventory.uncheck_whole_word()
        errors = []
        for filter_name in FILTERS_LIST:
            scope = select_filter_scope(inventory, filter_name, random_element_type, state)
            set_quick_filter(inventory, random_element_type)
            if not inventory.expand_by_row(1):
                errors.append(f"[{scope}] Failed to expand the first row with Quick filter '{random_element_type}'.")
            refresh_page(page)

        if errors:
            raise AssertionError("\n".join(errors))

    results[11] = run_step(11, step_11, logger, report)

    #####################################################################
    # Step 12 – For each Filter By + Quick filter of a random type:     #
    #           Expand All expands every listed row.                    #
    #####################################################################
    def step_12():
        occurrences = refresh_domain_devices()
        random_element_type = pick_random_element_type(occurrences)

        upper_panel.select_domain(DOMAIN_NAME)
        open_inventory(left_panel)
        inventory.uncheck_whole_word()
        errors = []
        for filter_name in FILTERS_LIST:
            scope = select_filter_scope(inventory, filter_name, random_element_type, state)
            set_quick_filter(inventory, random_element_type)
            if not inventory.expand_all():
                errors.append(f"[{scope}] Failed to click Expand All.")
            elif not inventory.is_expanded_all():
                errors.append(f"[{scope}] Expand All did not expand all the rows with Quick filter '{random_element_type}'.")
            refresh_page(page)

        if errors:
            raise AssertionError("\n".join(errors))

    results[12] = run_step(12, step_12, logger, report)

    ###########################################################################
    # Step 13 – Whole word: a partial type matches less devices than the full #
    #           type, and the full type keeps its count.                      #
    ###########################################################################
    def step_13():
        if not state['random_element_type']:
            pick_random_element_type(refresh_domain_devices())
        random_element_type = state['random_element_type']

        upper_panel.select_domain(DOMAIN_NAME)
        open_inventory(left_panel)
        inventory.uncheck_whole_word()
        set_filter_by(inventory, FILTERS_LIST[0])
        set_quick_filter(inventory, random_element_type)
        number_of_device_type = count_devices(inventory)

        random_element_type_changed = random_element_type[:-1]
        set_quick_filter(inventory, random_element_type_changed)
        if not inventory.check_whole_word():
            raise AssertionError("Failed to check Whole word.")
        sleep(FILTER_WAIT)
        count_changed = count_devices(inventory)
        if count_changed == number_of_device_type:
            raise AssertionError(f"Whole word + '{random_element_type_changed}' lists {count_changed} devices, "
                                 f"same as '{random_element_type}' - Whole word did not filter.")

        refresh_page(page)
        set_quick_filter(inventory, random_element_type)
        if not inventory.check_whole_word():
            raise AssertionError("Failed to check Whole word.")
        sleep(FILTER_WAIT)
        count_full = count_devices(inventory)
        if count_full != number_of_device_type:
            raise AssertionError(f"Whole word + '{random_element_type}' lists {count_full} devices, "
                                 f"expected {number_of_device_type}.")

    results[13] = run_step(13, step_13, logger, report)

    ##############################################################################
    # Step 14 – Quick filter with a non-existing value lists no devices, and     #
    #           clearing it brings every device back.                            #
    ##############################################################################
    def step_14():
        refresh_page(page)
        upper_panel.select_domain(DOMAIN_NAME)
        open_inventory(left_panel)
        inventory.uncheck_whole_word()
        set_filter_by(inventory, FILTERS_LIST[0])

        set_quick_filter(inventory, NON_EXISTING_FILTER)
        count = count_devices(inventory)
        if count != 0:
            raise AssertionError(f"Quick filter '{NON_EXISTING_FILTER}' lists {count} devices, expected 0.")

        set_quick_filter(inventory, "")
        count = count_devices(inventory)
        if count != len(DEVICES_LIST):
            raise AssertionError(f"After clearing the Quick filter {count} devices are listed, expected {len(DEVICES_LIST)}.")

    results[14] = run_step(14, step_14, logger, report)

    ##############################################################################
    # Step 15 – Quick filter by IP address and by chassis serial number lists    #
    #           exactly the matching device.                                     #
    ##############################################################################
    def step_15():
        upper_panel.select_domain(DOMAIN_NAME)
        open_inventory(left_panel)
        inventory.uncheck_whole_word()
        set_filter_by(inventory, FILTERS_LIST[0])
        set_quick_filter(inventory, "")

        serial_by_ip = {r["ip_address"]: r["serial_no"] for r in inventory.get_all_inventory_list() if not r["is_child"]}

        errors = []
        for ip in DEVICES_LIST:
            # '172.16.30.11' is also contained in '172.16.30.118'
            expected_ips = sorted(d for d in DEVICES_LIST if ip in d)
            set_quick_filter(inventory, ip)
            listed = sorted(listed_device_ips(inventory))
            if listed != expected_ips:
                errors.append(f"Quick filter '{ip}' lists {listed}, expected {expected_ips}.")

            serial = serial_by_ip.get(ip)
            if not serial:
                errors.append(f"No serial number found for {ip}.")
                continue
            set_quick_filter(inventory, serial)
            listed = listed_device_ips(inventory)
            if ip not in listed:
                errors.append(f"Quick filter by serial number '{serial}' lists {listed}, expected {ip}.")

        set_quick_filter(inventory, "")
        if errors:
            raise AssertionError("\n".join(errors))

    results[15] = run_step(15, step_15, logger, report)

    ##############################################################################
    # Step 16 – Expand All then Collapse All: every row collapses back and the   #
    #           number of devices does not change.                               #
    ##############################################################################
    def step_16():
        upper_panel.select_domain(DOMAIN_NAME)
        open_inventory(left_panel)
        set_filter_by(inventory, FILTERS_LIST[0])
        set_quick_filter(inventory, "")
        count_before = count_devices(inventory)

        if not inventory.expand_all():
            raise AssertionError("Failed to click Expand All.")
        if not inventory.is_expanded_all():
            raise AssertionError("Expand All did not expand all the rows.")

        if not inventory.collapse_all():
            raise AssertionError("Failed to click Collapse All.")
        sleep(FILTER_WAIT)
        child_rows = [r for r in inventory.get_all_inventory_list() if r["is_child"]]
        if child_rows:
            raise AssertionError(f"{len(child_rows)} child rows still shown after Collapse All.")

        count_after = count_devices(inventory)
        if count_after != count_before:
            raise AssertionError(f"Expand All / Collapse All changed the number of devices: {count_before} -> {count_after}.")

    results[16] = run_step(16, step_16, logger, report)

    ##########################################################################
    # Step 17 – Filter By Device + Expand All: every listed row (chassis and #
    #           all its modules) belongs to the selected device only.        #
    ##########################################################################
    def step_17():
        upper_panel.select_domain(DOMAIN_NAME)
        open_inventory(left_panel)
        errors = []
        for ip in DEVICES_LIST:
            set_filter_by(inventory, FILTERS_LIST[1])
            if not inventory.set_devices(ip):
                errors.append(f"Failed to select device '{ip}'.")
                continue
            sleep(FILTER_WAIT)
            if not inventory.expand_all():
                errors.append(f"[{ip}] Failed to click Expand All.")
                continue
            sleep(FILTER_WAIT)

            foreign = {r["ip_address"] for r in inventory.get_all_inventory_list()} - {ip}
            if foreign:
                errors.append(f"[{ip}] rows of other devices are listed: {sorted(foreign)}.")
            refresh_page(page)

        if errors:
            raise AssertionError("\n".join(errors))

    results[17] = run_step(17, step_17, logger, report)

    ##########################################################################
    # Step 18 – Refresh button: the same devices are listed after a refresh. #
    ##########################################################################
    def step_18():
        upper_panel.select_domain(DOMAIN_NAME)
        open_inventory(left_panel)
        set_filter_by(inventory, FILTERS_LIST[0])
        set_quick_filter(inventory, "")
        ips_before = sorted(listed_device_ips(inventory))

        if not inventory.refresh():
            raise AssertionError("Failed to click Refresh.")
        sleep(FILTER_WAIT)

        ips_after = sorted(listed_device_ips(inventory))
        if ips_after != ips_before:
            raise AssertionError(f"Devices changed after Refresh: {ips_before} -> {ips_after}.")

    results[18] = run_step(18, step_18, logger, report)

    #################################################################
    # Step 19 – Cleanup: remove the devices, chassis and domain     #
    #           from LW, and clear the chassis ID on the devices.   #
    #################################################################
    def step_19():
        upper_panel.select_domain(DOMAIN_NAME)
        left_panel.click_domain_management()
        for ip in DEVICES_LIST:
            domain_management.remove_device(ip, parent_domain_name=DOMAIN_NAME, parent_chassis=state['chassis_by_ip'].get(ip))
            refresh_page(page)

        for chassis in dict.fromkeys(state['chassis_by_ip'].values()):
            domain_management.remove_chassis(chassis_name=chassis, parent_domain_name=DOMAIN_NAME)

        refresh_page(page)
        sleep(WAIT * 10)
        domain_management.remove_domain(domain_name=DOMAIN_NAME)

        for ip in DEVICES_LIST:
            device_page = page.context.new_page()
            try:
                pl_login = PL_LoginPage(device_page)
                pl_login.goto(f"http://{ip}/")
                if not pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS):
                    raise AssertionError(f"Login to {ip} GUI failed.")
                PL_Main_Screen_POM(device_page).set_chassis_id("")
            finally:
                device_page.close()

    results[19] = run_step(19, step_19, logger, report)


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

        test_inventory(page, left_panel, logger, report)

        context.close()
        browser.close()
        close_report(report)

    end_time = time.perf_counter()
    print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
    logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")