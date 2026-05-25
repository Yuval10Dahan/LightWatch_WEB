"""
Created by: Yuval Dahan
Date: 21/01/2026
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
# from Pages.management_map import ManagementMap
from Pages.network_topology import NetworkTopology
import time
from Utils.utils import refresh_page


SERVER_HOST_IP = "172.16.10.22:8080"
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


def test_network_topology(page, left_panel):
    # ----------------------------
    # Open page + init POM
    # ----------------------------
    try:
        left_panel.click_network_topology()
        network_topology = NetworkTopology(page)
        print("Opened Network Topology ✅")
    except Exception as e:
        print(f"Failed to open Network Topology ❌ | Error: {e}")
        return

    # ----------------------------
    # Step 1: Alarms visibility
    # ----------------------------
    def step_1():
        network_topology.hide_alarms()
        if network_topology.get_alarms_status() != "hidden":
            raise AssertionError("Alarms expected to be 'hidden' after hide_alarms()")

        network_topology.show_alarms()
        if network_topology.get_alarms_status() != "shown":
            raise AssertionError("Alarms expected to be 'shown' after show_alarms()")

        network_topology.hide_alarms()
        if network_topology.get_alarms_status() != "hidden":
            raise AssertionError("Alarms expected to be 'hidden' after hide_alarms()")

    run_step(1, "Alarms visibility (show/hide)", step_1)

    # ----------------------------
    # Step 2: Severity filters
    # ----------------------------
    def step_2():
        network_topology.hide_critical_major()
        network_topology.show_critical_major()

        network_topology.hide_minor()
        network_topology.show_minor()

        network_topology.hide_cleared()
        network_topology.show_cleared()

    run_step(2, "Severity filters (Critical/Minor/Cleared)", step_2)

    # ----------------------------
    # Step 3: Navigation Info panel
    # ----------------------------
    def step_3():
        network_topology.show_navigation_info()

        elements_list1 = network_topology.get_navigation_info_elements_list(visible_only=True)
        print(f"elements_list1: {elements_list1}")
        elements_list2 = network_topology.get_navigation_info_elements_list(visible_only=False)
        print(f"elements_list2: {elements_list2}")

        element_exist = network_topology.is_element_exist_on_navigation_info_list("PL-8000M (172.16.30.114)")
        # element_exist = network_topology.is_element_exist_on_navigation_info_list("PL-2000ADS (172.16.30.19)")
        print(f"element exist: {element_exist}")
        if element_exist == False:
            raise Exception("Element is not exist")

        network_topology.hide_navigation_info()

        network_topology.show_navigation_info()

        network_topology.navigation_info_double_click_on_element("Chassis: 4/4")

        network_topology.navigation_info_open_element_details("Chassis: 4/4")

        network_topology.element_details_click_on_chassis()
        network_topology.element_details_click_on_services()
        network_topology.element_details_click_on_info()
        network_topology.element_details_click_on_faults()

        network_topology.element_details_faults_click_on_events()
        events_list = network_topology.element_details_faults_get_all_events()
        print(f"Events List:\n{events_list}")
        # network_topology.element_details_faults_view_all_events()

        network_topology.element_details_faults_click_on_alarms()
        alarms_list = network_topology.element_details_faults_get_all_alarms()
        print(f"Alarms List:\n{alarms_list}")
        # network_topology.element_details_faults_view_all_alarms()

        network_topology.navigation_info_close_element_details()

        network_topology.navigation_info_expand_element_byClick_on_arrow("Chassis: 4/4")
        network_topology.navigation_info_open_element_details("PL-1000TECrypto (172.16.30.22)")
        network_topology.navigation_info_close_element_details()
        network_topology.navigation_info_shrink_element_byClick_on_arrow("Chassis: 4/4")
        network_topology.hide_navigation_info()

    run_step(3, "Navigation Info (show/hide)", step_3)

    # ----------------------------
    # Step 4: Map edit flow + Map interactions (NEW)
    # ----------------------------
    def step_4():
        refresh_page(page)
        state, color = network_topology.get_map_element_color(element_ip="172.16.30.124")
        print(f"device color state: {state}, color: {color}") 

        state, color = network_topology.get_map_element_color(element_name="Chassis: 4")
        print(f"Chassis color state: {state}, color: {color}") 

        network_topology.click_on_element_via_the_map(element_ip="172.16.30.124") 
        network_topology.navigation_info_close_element_details()
        network_topology.click_on_element_via_the_map(element_name="Chassis: 4") 
        network_topology.navigation_info_close_element_details()

        network_topology.double_click_on_element_via_the_map(element_name="Chassis: 4") 
        network_topology.click_on_element_via_the_map(element_ip="172.16.30.22") 
        network_topology.navigation_info_close_element_details()
        refresh_page(page)

        network_topology.click_on_element_via_the_map_by_data_id(element_data_id="10") # Chassis: 4
        network_topology.navigation_info_close_element_details()
        network_topology.click_on_element_via_the_map_by_data_id(element_data_id="246") # 172.16.30.124
        network_topology.navigation_info_close_element_details()
        refresh_page(page)

        network_topology.double_click_on_element_via_the_map_by_data_id(element_data_id="10") # Chassis: 4
        network_topology.click_on_element_via_the_map_by_data_id(element_data_id="245") # 172.16.30.22
        network_topology.navigation_info_close_element_details()
        refresh_page(page)

        number_of_elements = network_topology.get_number_of_elements_inside_chassis("14")
        print(f"Number of Elements: {number_of_elements}") # Chassis: 2 --> 2
        number_of_elements = network_topology.get_number_of_elements_inside_chassis("10")
        print(f"Number of Elements: {number_of_elements}") # Chassis: 4 --> 1

        # ---- Existing: Map edit flow ----
        network_topology.unlock_map()
        network_topology.save_and_lock()

        network_topology.unlock_map()
        network_topology.discard_and_lock()

    run_step(4, "Map interactions + edit flow (click/double-click → Enable drag → Save&Lock → Enable drag → Discard&Lock)", step_4)


    # ----------------------------
    # Step 5: Layer toggles
    # ----------------------------
    def step_5():
        network_topology.enable_chassis()
        network_topology.enable_OTN()
        network_topology.enable_ROADM()
        network_topology.enable_manage()

    run_step(5, "Layer toggles (Chassis/OTN/ROADM/Manage)", step_5)

    # network_topology.refresh_page()

    # ----------------------------
    # Step 6: Zoom controls
    # ----------------------------
    def step_6():
        network_topology.map_zoom_in()
        network_topology.map_zoom_in()
        network_topology.map_zoom_in()

        network_topology.map_zoom_out()
        network_topology.map_zoom_out()

        # Expected to display "Zoom out is not possible anymore - current zoom is 118%." 4 times.
        network_topology.map_zoom_out()
        network_topology.map_zoom_out()
        network_topology.map_zoom_out()
        network_topology.map_zoom_out()

        network_topology.map_zoom_in()
        network_topology.map_zoom_out()
        network_topology.map_zoom_in()
        network_topology.map_zoom_out()
        network_topology.map_zoom_in()
        network_topology.reset_zoom_percentage()
        

    run_step(6, "Zoom controls (Zoom in/out)", step_6)

    # ----------------------------
    # Step 7: 
    # ----------------------------
    def step_7():
        pass
        

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
        refresh_page(page)

        # Run the test
        test_network_topology(page, left_panel)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")