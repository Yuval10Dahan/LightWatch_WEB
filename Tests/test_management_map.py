"""
Created by: Yuval Dahan
Date: 21/01/2026
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.management_map import ManagementMap
import time


SERVER_HOST_IP = "172.16.10.62:8080"
BASE_URL = f"http://{SERVER_HOST_IP}/"
USERNAME = "administrator"
PASSWORD = "administrator"


def run_step(step_num: int, title: str, fn):
    """
    Runs a step and prints consistent success/fail indication.
    """
    try:
        fn()
        print(f"Step {step_num} Success ✅  |  {title}")
        return True
    except Exception as e:
        print(f"Step {step_num} Failed ❌  |  {title}  |  Error: {e}")
        return False


def test_management_map(page, left_panel):
    # ----------------------------
    # Open page + init POM
    # ----------------------------
    try:
        left_panel.click_management_map()
        management_map = ManagementMap(page)
        print("Opened Management Map ✅")
    except Exception as e:
        print(f"Failed to open Management Map ❌ | Error: {e}")
        return

    # ----------------------------
    # Step 1: Alarms visibility
    # ----------------------------
    def step_1():
        management_map.show_alarms()
        if management_map.get_alarms_status() != "shown":
            raise AssertionError("Alarms expected to be 'shown' after show_alarms()")

        management_map.hide_alarms()
        if management_map.get_alarms_status() != "hidden":
            raise AssertionError("Alarms expected to be 'hidden' after hide_alarms()")

    run_step(1, "Alarms visibility (show/hide)", step_1)

    # ----------------------------
    # Step 2: Severity filters
    # ----------------------------
    def step_2():
        management_map.hide_critical_major()
        management_map.show_critical_major()

        management_map.hide_minor()
        management_map.show_minor()

        management_map.hide_cleared()
        management_map.show_cleared()

    run_step(2, "Severity filters (Critical/Minor/Cleared)", step_2)

    # ----------------------------
    # Step 3: Navigation Info panel
    # ----------------------------
    def step_3():
        management_map.show_navigation_info()
        management_map.hide_navigation_info()

        management_map.show_navigation_info()

        management_map.navigation_info_double_click_on_element("DR-13/13")

    run_step(3, "Navigation Info (show/hide)", step_3)

    # ----------------------------
    # Step 4: Map edit flow
    # ----------------------------
    def step_4():
        management_map.enable_drag()
        management_map.save_and_lock()

        management_map.enable_drag()
        management_map.discard_and_lock()

    run_step(
        4,
        "Map edit flow (Enable drag → Save&Lock → Enable drag → Discard&Lock)",
        step_4
    )

    # ----------------------------
    # Step 5: Layer toggles
    # ----------------------------
    def step_5():
        management_map.enable_chassis()
        management_map.enable_OTN()
        management_map.enable_ROADM()
        management_map.enable_manage()

    run_step(5, "Layer toggles (Chassis/OTN/ROADM/Manage)", step_5)

    # management_map.refresh_page()

    # ----------------------------
    # Step 6: Zoom controls
    # ----------------------------
    def step_6():
        management_map.map_zoom_in()
        management_map.map_zoom_in()
        management_map.map_zoom_in()

        management_map.map_zoom_out()
        management_map.map_zoom_out()

        # Expected to display "Zoom out is not possible anymore - got to the max zoom-out range. (Continue with the script)" 4 times.
        management_map.map_zoom_out()
        management_map.map_zoom_out()
        management_map.map_zoom_out()
        management_map.map_zoom_out()

        management_map.map_zoom_in()
        management_map.map_zoom_out()
        management_map.map_zoom_in()
        management_map.map_zoom_out()

    run_step(6, "Zoom controls (Zoom in/out)", step_6)

    print("Test Finished ✅")


if __name__ == "__main__":
    start_time = time.perf_counter()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        login_page = LoginPage(page)
        login_page.goto(BASE_URL)

        if login_page.login(USERNAME, PASSWORD):
            print("Login Success ✅")
        else:
            print("Login Failed ❌")
            context.close()
            browser.close()
            raise SystemExit(1)

        left_panel = LeftPanel(page)

        # Run the test
        test_management_map(page, left_panel)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")