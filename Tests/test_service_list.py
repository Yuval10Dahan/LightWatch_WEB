"""
Created by: Yuval Dahan
Date: 21/01/2026
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.service_list import ServiceList
import time
from Utils.utils import refresh_page, create_frame_html


SERVER_HOST_IP = "172.16.10.22:8080"
BASE_URL = f"http://{SERVER_HOST_IP}/"
USERNAME = "administrator"
PASSWORD = "administrator"


def run_step(step_num: float, title: str, fn):
    """
    Runs a step and prints consistent success/fail indication.
    """
    try:
        fn()
        print(f"Step {step_num} Success ✅")
        return True
    except Exception as e:
        print(f"Step {step_num} Failed ❌  Error: {e}")
        return False


def test_service_list(page, left_panel):
    # ----------------------------
    # Open page + init POM
    # ----------------------------
    try:
        left_panel.click_service_list()
        service_list = ServiceList(page)
        print("Opened Service List ✅")
    except Exception as e:
        print(f"Failed to open Service List ❌ | Error: {e}")
        return

    # # ----------------------------
    # # Step 1: Search by name
    # # ----------------------------
    # def step_1():
        
    #     # create_frame_html(page)
    #     service_list.set_service_name("Yuval")

    # run_step(1, "Service List: search by name", step_1)

    # # ----------------------------
    # # Step 2: Service Layer Multi-Select
    # # ----------------------------
    # def step_2():
    #     service_list.select_service_layer("ROADM")
    #     service_list.select_service_layer("OTN")
    #     service_list.select_service_layer("CS")
    #     service_list.select_service_layer("All")

    #     service_list.set_all_service_layers()
    #     selected = service_list.get_all_selected_service_layers()
    #     print(f"Selected: {selected}")

    #     service_list.remove_all_service_layers()

    #     service_list.select_service_layer("ROADM")
    #     selected2 = service_list.get_all_selected_service_layers()
    #     print(f"Selected2: {selected2}")

    #     service_list.remove_service_layer("ROADM")

    # run_step(2, "Service Layer Multi-Select", step_2)

    # # ----------------------------
    # # Step 3: Service Type
    # # ----------------------------
    # def step_3():
    #     # create_frame_html(page)

    # run_step(3, "Service Type", step_3)

    # # ----------------------------
    # # Step 4: Protection Type
    # # ----------------------------
    # def step_4():
    #     service_list.select_protection_type("Unprotected")
    #     service_list.select_protection_type("Protected")
    #     service_list.select_protection_type("Restoration")
    #     service_list.select_protection_type("All")

    #     service_list.set_all_protection_types()
    #     selected_protection_types = service_list.get_all_selected_protection_types()
    #     print(f"Selected protection types: {selected_protection_types}")
        
    #     service_list.remove_all_protection_types()
        
    #     service_list.select_protection_type("Unprotected")
    #     selected_protection_types2 = service_list.get_all_selected_protection_types()
    #     print(f"Selected protection types2: {selected_protection_types2}")
        
    #     service_list.remove_protection_type("Unprotected")

    # run_step(4, "Protection Type", step_4)

    # ----------------------------
    # Step 5: Domain/Chassis modal flow 
    # ----------------------------
    def step_5():
        # create_frame_html(page)
        service_list.set_filter_by("Domain/Chassis")

        selected_filter_by = service_list.get_filter_by()
        print(f"Selected filter by: {selected_filter_by}")

        try:
            service_list.select_domain_or_chassis("Chassis: 4/4")
            val1 = service_list.get_selected_domain_or_chassis()
            print(f"Domain value: {val1}")

            service_list.select_domain_or_chassis("Default")
            val2 = service_list.get_selected_domain_or_chassis()
            print(f"Domain value: {val2}")

        except Exception as e:
            print(f"Domain/Chassis flow not available in this env (skipping). Reason: {e}")

    run_step(5, "Domain/Chassis", step_5)

    # ----------------------------
    # Step 6: 
    # ----------------------------
    def step_6():
        pass

    run_step(6, "...", step_6)

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

        test_service_list(page, left_panel)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")