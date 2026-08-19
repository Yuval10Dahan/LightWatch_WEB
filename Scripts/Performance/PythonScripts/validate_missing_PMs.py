"""
Created by: Yuval Dahan
Date: 18/08/2026

PM's Test -
=====================================================
Tests...

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


4. Make sure that in each device you test, at least one interval of data is documented in the PM table of
   both the PL device and the LightWatch server.
--------------------------------------------------------------------------------------------------------------------------
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.device_discovery import DeviceDiscovery
from Pages.network_topology import NetworkTopology
from Pages.domain_management import DomainManagement
from Pages.upper_panel import UpperPanel
from Pages.performance import Performance
from PL_Devices.PL_Pages.PL_login_page import PL_LoginPage
from PL_Devices.PL_Pages.PL_main_screen_POM import PL_Main_Screen_POM
from PL_Devices.PL_Pages.PL_performance_page import PL_PerformancePage
from Utils.utils import refresh_page, devices_are_up, create_page, countdown_sleep
import time
from time import sleep
from Utils.Logger import create_logger
from Utils.utils import CLI_Login, open_connection, close_connection, send_cli_command, send_cli_commands
import sys
from sys import argv
from Utilities.QCreporter import open_report, close_report, step_passed, step_failed
import os
from datetime import datetime, date
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

    CLI_HOST = "172.16.20.2" 
    CLI_PORT = "2001"

    PL_1000D_IP = "" # 172.16.40.133
    PL_1000GD_IP = "" # 172.16.40.134
    PL_1000GIL_IP = "" # 172.16.20.197
    PL_1000GR_IP = "" # 10.30.6.25 (Hardware device)
    PL_1000GRO_IP = "" # 172.16.40.32
    PL_1000GRO_R_IP = "" # 172.16.40.36
    PL_1000IL_IP = "" # 172.16.30.13
    PL_1000R_IP = "" # 10.30.6.158
    PL_1000RO_IP = "" # 172.16.40.131
    PL_1000TE = "" # 
    PL_1000TE_CRYPTO = "" # 172.16.30.22
    PL_1000TN = "" # 172.16.40.12
    PL_2000_IP = "172.16.20.111" # 172.16.20.111
    PL_2000AD_LH_IP = "" # 
    PL_2000_AD_METRO_IP = "" # 
    PL_2000ADS_IP = "" # 172.16.30.15
    PL_2000GA_IP = "" # 172.16.20.123
    PL_2000GM_IP = "" # 172.16.20.126
    PL_2000M_IP = "" # 172.16.20.120
    PL_2000T_IP = "" # 172.16.30.17
    PL_4000G_IP = "" # 172.16.20.23
    PL_4000M_IP = "" # 172.16.40.21
    PL_4000T_IP = "" # 172.16.40.40
    PL_8000G_IP = "" # 172.16.20.117
    PL_8000M_IP = "" # 172.16.30.113

    DEVICE_IP_USER = "tech" 
    DEVICE_IP_PASS = "packetlight"

    DOMAIN_NAME = "PM_domain"


# ================================================================
# Values that should not be changed
# ================================================================

DEVICES_LIST = [PL_1000D_IP, PL_1000GD_IP, PL_1000GIL_IP, PL_1000GR_IP, 
                PL_1000GRO_IP, PL_1000GRO_R_IP, PL_1000IL_IP, PL_1000R_IP, 
                PL_1000RO_IP, PL_1000TE, PL_1000TE_CRYPTO, PL_1000TN, 
                PL_2000_IP, PL_2000AD_LH_IP, PL_2000_AD_METRO_IP, PL_2000ADS_IP, 
                PL_2000GA_IP, PL_2000GM_IP, PL_2000M_IP, PL_2000T_IP, 
                PL_4000G_IP, PL_4000M_IP, PL_4000T_IP, PL_8000G_IP, PL_8000M_IP]

DEVICES_NAMES = ["PL-1000D", "PL-1000GD", "PL-1000GIL", "PL-1000GR", 
                "PL-1000GRO", "PL-1000GRO-R", "PL-1000IL2", "PL-1000R", 
                "PL-1000RO2", "PL-1000TE", "PL-1000TECrypto", "PL-1000TN", 
                "PL-2000", "PL-2000AD_LH", "PL-2000_AD_METRO", "PL-2000ADS", 
                "PL-2000GA", "PL-2000GM", "PL-2000M", "PL-2000T", 
                "PL-4000G", "PL-4000M", "PL-4000T", "PL-8000G", "PL-8000M"]

TECH_USERNAME = "tech" 
TECH_PASSWORD = "packetlight"

BASE_URL = f"http://{LW_SERVER_HOST_IP}/"
WAIT = 5
WAIT_FOR_PM_POLLING = 1000

BACK_TO_START_CLI_COMMANDS = ["..", "..", ".."]
ETH1_DOWN_COMMANDS = ["configure", "interface", "lan 1 down", "Y"]
ETH1_UP_COMMANDS = ["configure", "interface", "lan 1 up", "Y"]

INTERVALS_NUMBER = 32
PM_TYPE_MINUTES = "15 Minutes"
PM_TYPE_DAYS = "Days"

LOGGER_ROOT_DIRECTORY = 'G:\\Python\\PacketLight Automation\\LightWatch_WEB\\Scripts\\Performance\\LogFiles'
LOGGER_DIRECTORY_NAME = "validate_missing_PMs"
LOG_FILE_NAME = 'validate_missing_PMs.log'
REPORT_PATH = None

RESET_NEEDED = False

GOOGLE_SNTP_SERVER = '216.239.35.0'
GMT2 = "GMT+2"

PORT_PER_PRODUCT = {
    "PL-1000IL2": "MC 1",
    "PL-1000IL": "MC 1",
    "PL-1000R": "MC 1",
    "PL-1000D": "MC 1",
    "PL-1000GD": "MC 1",
    "PL-1000GIL": "MC 1",
    "PL-1000GR": "MC 1",
    "PL-1000GRO": "MC 1",
    "PL-1000GRO-R": "MNG 1",
    "PL-1000RO": "MC 1",
    "PL-1000RO2": "MC 1",
    "PL-1000TE Crypto": "1",
    "PL-1000TE_CRYPTO": "1",
    "PL-1000TECrypto": "1",
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
    "PL-8000M": "1"
}

def is_israel_daylight_saving_enabled() -> bool:
    '''
    Determines if Israel is currently observing daylight saving time.
    '''
    today = date.today()
    year = today.year

    dst_start = date(year, 3, 27)
    dst_end = date(year, 10, 25)

    return dst_start <= today < dst_end

def extract_port_name_from_list(device_name, ports_list):
    """
    Look up device_name in ports_list (PORT_PER_PRODUCT) and return its port name.
    """
    port_name = ports_list.get(device_name)
    if port_name is None:
        raise AssertionError(f"No port mapping found for device '{device_name}' in PORT_PER_PRODUCT.")
    return port_name

def strip_current_interval_row(device_pm_table: list) -> list:
    """
    Drop the first row of device_pm_table ("Current" -- e.g. row 0 in
    get_PM_table()'s output). LW's table has no equivalent "Current" row, so
    comparison must start from the device's row 1 onward.
    """
    return device_pm_table[1:] if device_pm_table else []


_INTERVAL_PATTERN = re.compile(r"(\d{2})/(\d{2})/(\d{2});(\d{2}):(\d{2}):\d{2}")
_VALIDITY_WORDS = {"yes", "no", "partial"}


def normalize_header_key(header: str) -> str:
    """
    Normalize a column header for comparison, ignoring case/punctuation/spacing
    differences between the device's and LW's labels for the same column --
    e.g. device "Rx Level dBm" vs LW "Rx Level, dBm" both normalize to
    "rxleveldbm". This is what makes comparison generic across PM Types/products
    that render completely different column sets ("Native Signal": Interval/
    Errors/.../Valid; "Layer 2 PM": Interval/RX Bytes/.../Valid; "Optical Level":
    Interval/Rx Level dBm/.../Max Tx dBm with no Valid column at all).
    """
    return re.sub(r"[^a-z0-9]", "", (header or "").lower())

def _convert_device_interval_to_lw_format(device_interval: str) -> str:
    """
    Convert a device 'Interval' cell (e.g. "1     06/08/26;11:15:01") into LW's
    format (e.g. "11:15 06.08.2026"): strip the leading interval index, drop
    seconds, and reorder DD/MM/YY;HH:MM:SS -> HH:MM DD.MM.YYYY.
    """
    match = _INTERVAL_PATTERN.search(device_interval or "")
    if not match:
        return (device_interval or "").strip()

    day, month, year, hour, minute = match.groups()
    return f"{hour}:{minute} {day}.{month}.20{year}"

_NUMBER_WITH_UNIT_PATTERN = re.compile(r"^(-?\d+(?:\.\d+)?)\s*[A-Za-z%]+$")


def _strip_trailing_unit(value: str) -> str:
    """
    Strip a trailing unit suffix from a bare numeric reading -- e.g. the device
    renders "1.2 dBm" for the same value LW renders as just "1.2". Values that
    aren't a plain "<number><unit>" (e.g. "NA", "PARTIAL; YES") are left as-is.
    """
    match = _NUMBER_WITH_UNIT_PATTERN.match(value)
    return match.group(1) if match else value

def normalize_cell_value(value: str) -> str:
    """
    Normalize a single cell's text for comparison: collapse whitespace,
    title-case Yes/No/Partial-style validity words regardless of source casing
    (device renders "YES"/"NO", LW renders "Yes"/"No"), and strip a trailing
    unit suffix from bare numeric readings (device "1.2 dBm" vs LW "1.2").
    """
    cleaned = re.sub(r"\s+", " ", (value or "").strip())
    cleaned = _strip_trailing_unit(cleaned)
    parts = [p.strip() for p in cleaned.split(";")]
    return "; ".join(p.capitalize() if p.lower() in _VALIDITY_WORDS else p for p in parts)

_IGNORED_COLUMN_KEYS = {"reset"}


def normalize_row_for_comparison(row: dict, is_device_row: bool = False) -> dict:
    """
    Convert a single PM table row (dynamic headers, from either the PL device
    or LW) into a {normalized_header: normalized_value} dict, so rows from
    either source can be compared regardless of differing column names/counts/
    casing for the same PM type. is_device_row=True additionally reformats
    whichever column normalizes to "interval" from the device's raw
    "<index>  DD/MM/YY;HH:MM:SS" text into LW's "HH:MM DD.MM.YYYY" format.

    Columns in _IGNORED_COLUMN_KEYS are dropped entirely -- "Reset" is a
    device-only button column (sometimes rendered with a header, sometimes
    not, always empty-valued) that LW's table never has, so it must never
    participate in the column-set/value comparison on either side.
    """
    normalized = {}
    for header, value in row.items():
        key = normalize_header_key(header)
        if key in _IGNORED_COLUMN_KEYS:
            continue
        if is_device_row and key == "interval":
            value = _convert_device_interval_to_lw_format(value)
        normalized[key] = normalize_cell_value(value)
    return normalized

def convert_device_row_to_lw_format(device_row: dict) -> dict:
    """
    Convert one device PM row (dict, as returned by PL_PerformancePage.get_PM_table,
    with whatever headers the device's current PM Type happens to render) into a
    normalized dict comparable against LW's row for the same PM Type.
    """
    return normalize_row_for_comparison(device_row, is_device_row=True)

def _interval_date_only(value: str) -> str:
    """
    Extract just the DD.MM.YYYY date portion of an "HH:MM DD.MM.YYYY" interval
    value, dropping the clock. Used to compare "interval" columns by date only.
    """
    parts = (value or "").split(" ", 1)
    return parts[1] if len(parts) == 2 else (value or "").strip()

def values_match(key: str, device_value: str, lw_value: str) -> bool:
    """
    Compare one column's values between device and LW. The "interval" column
    only compares the date, never the clock -- LW server time and device time
    can drift by minutes/hours, so comparing hours:minutes would flag false
    mismatches unrelated to actual PM data correctness.
    """
    if key == "interval":
        return _interval_date_only(device_value) == _interval_date_only(lw_value)
    return device_value == lw_value

def compare_pm_tables(device_pm_table: list, lw_pm_table: list) -> bool:
    """
    Verify that every interval LW's PM table has also exists in the PL device's
    PM table, with matching values - LW is checked for CONTAINMENT within the
    device table, not row-for-row/index alignment.

    device_pm_table's "Current" row is dropped before comparing (LW's table has
    no equivalent row).
    """
    device_rows = strip_current_interval_row(device_pm_table)

    if not lw_pm_table:
        return True

    if not device_rows:
        print("PM table mismatch: device table has no non-'Current' rows to check LW's intervals against.")
        return False

    device_norms = [convert_device_row_to_lw_format(row) for row in device_rows]
    lw_norms = [normalize_row_for_comparison(row) for row in lw_pm_table]

    all_matched = True
    for i, lw_row in enumerate(lw_norms):
        lw_keys = set(lw_row)
        lw_interval = lw_row.get("interval", "")

        closest_mismatches = None  # value diffs for a device row with the same interval + column set

        for device_row in device_norms:
            if set(device_row) != lw_keys:
                continue  # different PM type/schema -- not a candidate for this LW row

            if not values_match("interval", device_row.get("interval", ""), lw_interval):
                continue  # not the same interval -- not a candidate

            mismatches = {
                key: (device_row[key], lw_row[key])
                for key in lw_keys
                if not values_match(key, device_row[key], lw_row[key])
            }

            if not mismatches:
                closest_mismatches = {}
                break

            if closest_mismatches is None:
                closest_mismatches = mismatches

        if closest_mismatches is None:
            print(
                f"LW row {i} (interval={lw_interval}): no matching interval found in device table "
                f"(device intervals: {[d.get('interval') for d in device_norms]})"
            )
            all_matched = False
        elif closest_mismatches:
            print(f"LW row {i} (interval={lw_interval}): interval found in device table but values differ: {closest_mismatches}")
            all_matched = False

    return all_matched

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

def test_PM_table(page, left_panel: LeftPanel, logger, report):
    domain_management = DomainManagement(page)
    device_discovery = DeviceDiscovery(page)
    network_topology = NetworkTopology(page)
    upper_panel = UpperPanel(page)
    performance = Performance(page)

    session = open_connection(host=CLI_HOST, port=CLI_PORT, drain_banner=True)
    login_status = CLI_Login(session=session, user=TECH_USERNAME, password=TECH_PASSWORD)
    if not login_status:
        raise AssertionError("Login failed.")

    results = {}

    # ===============
    # Side function 
    # =============== 

    ###################################################
    # Step 1 – (Optional) cold reset for all devices, #
    # then wait for them all to come back up.         #
    ###################################################
    def step_1():
        if RESET_NEEDED:
            for ip in DEVICES_LIST:
                if not ip:
                    continue

                device_page = page.context.new_page()
                try:
                    pl_login = PL_LoginPage(device_page)
                    pl_login.goto(f"http://{ip}/")
                    ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
                    if not ok:
                        raise AssertionError(f"Login to {ip} GUI failed.")

                    pl_main_screen = PL_Main_Screen_POM(device_page)
                    pl_main_screen.device_restart("cold")
                finally:
                    device_page.close()

            configured_devices = [ip for ip in DEVICES_LIST if ip]
            devices_are_up(configured_devices, wait_time=WAIT)

        else:
            print("Reset skipped.")

    results[1] = run_step(1, step_1, logger, report)

    ################################################################################
    # Step 2 – Login to the GUI of each IP.                                        #
    # Set SNTP server and timezone to synchronize device time with LW server time. #                                   
    ################################################################################
    def step_2():
        daylight_save = "Enabled" if is_israel_daylight_saving_enabled() else "Disabled"

        for ip in DEVICES_LIST:
            if not ip:
                continue

            device_page = page.context.new_page()
            pl_login = PL_LoginPage(device_page)
            pl_login.goto(f"http://{ip}/")
            ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
            assert ok, f"Login to {ip} GUI failed."

            pl_main_screen = PL_Main_Screen_POM(device_page)
            pl_main_screen.set_chassis_id("")

            # relevant for devices that only has SNTP configuration option
            if ip == PL_1000D_IP or ip == PL_1000GD_IP or ip == PL_1000R_IP or \
               ip == PL_1000TE_CRYPTO or ip == PL_1000TN or ip == PL_2000_IP:
                pl_main_screen.add_sntp_server(GOOGLE_SNTP_SERVER, skip_protocol_and_key_and_value=True)
            else:
                pl_main_screen.add_sntp_server(GOOGLE_SNTP_SERVER)

            pl_main_screen.set_sntp_configuration(status="Enabled", gmt=GMT2, daylight_save=daylight_save)
            refresh_page(device_page)
            device_page.close()

    results[2] = run_step(2, step_2, logger, report)

    ################################################
    # Step 3 – Configure SNMPv2 and save default.  #
    ################################################
    def step_3():
        left_panel.click_device_discovery()
        device_discovery.click_SNMPv2()
        device_discovery.set_SNMPv2_read_community("read-only")
        device_discovery.set_SNMPv2_write_community("read-write")
        device_discovery.set_SNMPv2_admin_community("admin")
        device_discovery.set_SNMPv2_contact_port(161)
        device_discovery.click_save_as_default()

        try:
            device_discovery.confirm_default_override(timeout=3000)
        except Exception:
            pass

    results[3] = run_step(3, step_3, logger, report)

    ########################################################
    # Step 4 – Discover each device via SNMPv2 by its IP.  #
    ########################################################
    def step_4():
        left_panel.click_device_discovery()

        # for ip in DEVICES_LIST:
        for ip, device_name in zip(DEVICES_LIST, DEVICES_NAMES):
            if not ip:
                continue

            device_discovery.click_SNMPv2()
            device_discovery.set_ip_address(ip)
            device_discovery.click_start_discovery()
            refresh_page(page)

            device_page = page.context.new_page()
            try:
                pl_login = PL_LoginPage(device_page)
                pl_login.goto(f"http://{ip}/")
                ok = pl_login.login(DEVICE_IP_USER, DEVICE_IP_PASS)
                if not ok:
                    raise AssertionError(f"Login to {ip} GUI failed.")

                port1_name = extract_port_name_from_list(device_name, PORT_PER_PRODUCT)
                pl_main_screen = PL_Main_Screen_POM(device_page)
                pl_main_screen.set_admin_status(port_number=port1_name, status="up")
                
            except Exception as e:
                print(f"Failed to set admin status at port {port1_name} for {ip} ({device_name}): {e}")
            finally:
                device_page.close()

        countdown_sleep(WAIT_FOR_PM_POLLING, message=f"Waiting for PM polling to complete, this may take a while")

    results[4] = run_step(4, step_4, logger, report)

    ########################################################################
    # Step 5 – Verify every discovered device appears in Navigation Info. #
    ########################################################################
    def step_5():
        left_panel.click_network_topology()
        network_topology.show_navigation_info()
        nav_elements = network_topology.get_navigation_info_elements_list()

        missing = [ip for ip in DEVICES_LIST if ip and not any(ip in element for element in nav_elements)]

        if missing:
            raise AssertionError(f"Devices missing from Navigation Info list: {missing}")

    results[5] = run_step(5, step_5, logger, report)

    ########################################################################
    # Step 6 – Add PM_domain, select it, and move all devices into it.    #
    ########################################################################
    def step_6():
        left_panel.click_domain_management()
        domain_management.add_domain(DOMAIN_NAME)

        left_panel.click_network_topology()
        upper_panel.select_domain(DOMAIN_NAME)

        left_panel.click_domain_management()
        for ip in DEVICES_LIST:
            if not ip:
                continue

            domain_management.move_to_domain(source_item_name=ip, target_domain_name=DOMAIN_NAME)
            sleep(1)

    results[6] = run_step(6, step_6, logger, report)

    #################
    # Step 7 – pass #
    #################
    def step_7():
        send_cli_command(session, BACK_TO_START_CLI_COMMANDS)
        send_cli_commands(session, ETH1_DOWN_COMMANDS)

    results[7] = run_step(7, step_7, logger, report)

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

        test_PM_table(page, left_panel, logger, report)

        context.close()
        browser.close()
        close_report(report)
        close_connection(session)

    end_time = time.perf_counter()
    print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
    logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")