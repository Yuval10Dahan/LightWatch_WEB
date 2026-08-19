"""
Created by: Ron Shuster
Date: 02/08/2026

Comprehensive Main Screen Test – Search Tool
=====================================================
Tests the "Search tool" actions on the main screen (Global Search):
    - Search device by IP
    - Search device by name
    - Click on the device name to locate the device on the map
    - Click on the service list icon from the search to open the services
      list filtered by the device
    - Click on the device name from the search, then "View All Alarms" to
      open the alarms list filtered by the device
    - Search for a device that does not exist (negative test)


*** Runtime: approximately 5 minutes ***
"""

from playwright.sync_api import sync_playwright, expect

from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.upper_panel import UpperPanel
from Pages.network_topology import NetworkTopology
from Pages.service_list import ServiceList
from Pages.alarms_and_events import AlarmsAndEvents
from Utils.utils import refresh_page, create_page
import time
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

    # Device already discovered and present in the system - used for both
    # IP-based and name-based Global Search.
    DEVICE_IP = "172.16.20.126"
    DEVICE_NAME = "PL-2000GM"

    # A search term that must not match any real device - used only by the
    # "no results" negative test.
    NON_EXISTENT_SEARCH_TERM = "testNonExistentDevice_Automation"



# ================================================================
# Values that should not be changed
# ================================================================

BASE_URL = f"http://{LW_SERVER_HOST_IP}/"

LOGGER_ROOT_DIRECTORY = 'G:\\Python\\PacketLight Automation\\LightWatch_WEB\\Scripts\\Domain_Management'
LOGGER_DIRECTORY_NAME = "search_tool_actions"
LOG_FILE_NAME = 'search_tool_actions.log'
REPORT_PATH = None

# ================================================================
# Helper – step runner
# ================================================================

def run_step(step_num, step_function, logger, report, page=None) -> bool:
    """
    Runs a step - prints consistent success / fail line.
    Returns True on success, False on failure.
    On failure, if `page` is given, saves a screenshot + the Global Search
    dropdown HTML (when present) next to the log file for debugging.
    """
    try:
        step_function()
        print(f"Step {step_num} – Pass ✅")
        logger.info(f"Step {step_num} – Pass.")
        step_passed(report, f"Step {step_num} – Pass.")
        return True
    except Exception as e:
        print(f"Step {step_num} – Fail ❌  Error: {e}")
        logger.info(f"Step {step_num} – Fail.")
        logger.info(f"Step {step_num} Error: {e}")
        step_failed(report, f"Step {step_num} – Fail.")

        if page is not None:
            debug_dir = os.path.join(LOGGER_ROOT_DIRECTORY, "debug")
            try:
                os.makedirs(debug_dir, exist_ok=True)
                screenshot_path = os.path.join(debug_dir, f"step_{step_num}_failure.png")
                page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"Step {step_num} – Saved failure screenshot: {screenshot_path}")

                search = page.locator("app-global-search").first
                if search.count() > 0:
                    html_path = os.path.join(debug_dir, f"step_{step_num}_global_search.html")
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(search.inner_html())
                    logger.info(f"Step {step_num} – Saved Global Search DOM: {html_path}")
            except Exception as debug_e:
                logger.info(f"Step {step_num} – Failed to save debug artifacts: {debug_e}")

        return False

def click_on_device_via_global_search_with_retry(upper_panel: UpperPanel, device_text: str, attempts: int = 3, timeout: int = 12000):
    """
    Retry wrapper around upper_panel.click_on_device_via_global_search().

    upper_panel.click_on_device_service_list_tab_via_global_search() and
    ..._performance_tab_via_global_search() both call refresh_page() before
    opening Global Search; click_on_device_via_global_search() does not.
    Reopening Global Search without that refresh - e.g. right after a prior
    in-app navigation - has been observed to leave stale widget state that
    collapses the results dropdown before Playwright's wait completes.
    Refreshing first mirrors the reliable calls. Page Objects (Pages/*.py)
    are treated as read-only from test scripts, so this stays local instead
    of changing upper_panel.py.
    """
    last_exc = None
    for attempt in range(1, attempts + 1):
        refresh_page(upper_panel.page)
        try:
            upper_panel.click_on_device_via_global_search(device_text, timeout=timeout)
            return
        except Exception as e:
            last_exc = e
    raise last_exc

def get_global_search_result_count(upper_panel: UpperPanel, timeout: int = 8000) -> int:
    """
    Return how many result rows are currently shown in Global Search.
    """
    search = upper_panel.page.locator("app-global-search").first
    expect(search).to_be_visible(timeout=timeout)

    return search.locator("li", has=search.locator(".global-search-content-row-label")).count()

def assert_device_in_devices_filter(alarms_and_events: AlarmsAndEvents, device_ip: str, device_name: str):
    """
    Assert the Alarms & Events "Devices" filter is scoped to our device.

    Checks both the filter mode ("Devices" - the literal used throughout
    Pages/alarms_and_events.py, e.g. set_filterBy("Devices")) and that the
    device is one of the selected chips - a chip can render as an IP, a
    name, or "name (ip)" depending on the view, so both identifiers are
    accepted.
    """
    filter_mode = alarms_and_events.get_filterBy()
    assert filter_mode.strip().lower() == "devices", (
        f"Expected the Alarms & Events 'Filter by' to be 'Devices', got '{filter_mode}'.")

    selected_devices = alarms_and_events.get_all_selected_devices_filterBy_devices()
    assert any(device_ip in d or device_name in d for d in selected_devices), (
        f"Expected the Devices filter to include '{device_ip}' / '{device_name}', found: {selected_devices}.")

# ================================================================
# Main test
# ================================================================

def test_search_tool_actions(page, left_panel: LeftPanel, logger, report):
    upper_panel = UpperPanel(page)
    network_topology = NetworkTopology(page)
    service_list = ServiceList(page)
    alarms_and_events = AlarmsAndEvents(page)

    results = {}

    #########################################################################
    # Step 1 – Search device by IP, then click on the device name.         #
    # Verify the device is located on the map (Network Topology).          #
    #########################################################################
    def step_1():
        click_on_device_via_global_search_with_retry(upper_panel, DEVICE_IP)

        network_topology.get_map_element_color(element_ip=DEVICE_IP)

    results[1] = run_step(1, step_1, logger, report, page=page)

    #########################################################################
    # Step 2 – Search device by IP, then click the service list icon.      #
    # Verify the Service List opens filtered by that device.               #
    #########################################################################
    def step_2():
        upper_panel.click_on_device_service_list_tab_via_global_search(DEVICE_IP)

        filter_mode = service_list.get_filter_by()
        assert filter_mode.strip().lower() == "device", (
            f"Expected the Service List 'Filter by' to be 'Device' after opening it from Global "
            f"Search for '{DEVICE_IP}', got '{filter_mode}'.")

    results[2] = run_step(2, step_2, logger, report, page=page)

    #########################################################################
    # Step 3 – Search device by IP, click the device name, then "View All  #
    # Alarms". Verify Alarms & Events opens filtered by that device.       #
    #########################################################################
    def step_3():
        click_on_device_via_global_search_with_retry(upper_panel, DEVICE_IP)
        network_topology.element_details_faults_view_all_alarms()

        assert_device_in_devices_filter(alarms_and_events, DEVICE_IP, DEVICE_NAME)

    results[3] = run_step(3, step_3, logger, report, page=page)

    #########################################################################
    # Step 4 – Search device by name, then click on the device name.       #
    # Verify the device is located on the map (Network Topology).          #
    #########################################################################
    def step_4():
        click_on_device_via_global_search_with_retry(upper_panel, DEVICE_NAME)

        network_topology.get_map_element_color(element_name=DEVICE_NAME)

    results[4] = run_step(4, step_4, logger, report, page=page)

    #########################################################################
    # Step 5 – Search device by name, then click the service list icon.    #
    # Verify the Service List opens filtered by that device.               #
    #########################################################################
    def step_5():
        upper_panel.click_on_device_service_list_tab_via_global_search(DEVICE_NAME)

        filter_mode = service_list.get_filter_by()
        assert filter_mode.strip().lower() == "device", (
            f"Expected the Service List 'Filter by' to be 'Device' after opening it from Global "
            f"Search for '{DEVICE_NAME}', got '{filter_mode}'.")

    results[5] = run_step(5, step_5, logger, report, page=page)

    #########################################################################
    # Step 6 – Search device by name, click the device name, then "View    #
    # All Alarms". Verify Alarms & Events opens filtered by that device.   #
    #########################################################################
    def step_6():
        click_on_device_via_global_search_with_retry(upper_panel, DEVICE_NAME)
        network_topology.element_details_faults_view_all_alarms()

        assert_device_in_devices_filter(alarms_and_events, DEVICE_IP, DEVICE_NAME)

    results[6] = run_step(6, step_6, logger, report, page=page)

    #########################################################################
    # Step 7 – Search for a device that does not exist (negative test).    #
    # Verify Global Search returns no results.                             #
    #########################################################################
    def step_7():
        upper_panel.set_global_search_value(NON_EXISTENT_SEARCH_TERM)

        result_count = get_global_search_result_count(upper_panel)
        assert result_count == 0, (
            f"Searching for '{NON_EXISTENT_SEARCH_TERM}' (expected to match no device) returned "
            f"{result_count} result(s) in Global Search.")

        upper_panel.close_global_search()

    results[7] = run_step(7, step_7, logger, report, page=page)

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

        test_search_tool_actions(page, left_panel, logger, report)

        context.close()
        browser.close()
        close_report(report)

    end_time = time.perf_counter()
    print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
    logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")