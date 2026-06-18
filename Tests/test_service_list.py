"""
Created by: Yuval Dahan
Date: 21/01/2026
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.service_list import ServiceList
import time
from Utils.utils import refresh_page, create_frame_html, create_page


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

    # ----------------------------
    # Step 1: Search by name
    # ----------------------------
    def step_1():
        
        # create_frame_html(page)
        service_list.set_service_name("Yuval")

    run_step(1, "Service List: search by name", step_1)

    # ----------------------------
    # Step 2: Service Layer Multi-Select
    # ----------------------------
    def step_2():
        service_list.select_service_layer("ROADM")
        service_list.select_service_layer("OTN")
        service_list.select_service_layer("CS")
        service_list.select_service_layer("All")

        service_list.set_all_service_layers()
        selected = service_list.get_all_selected_service_layers()
        print(f"Selected: {selected}")

        service_list.remove_all_service_layers()

        service_list.select_service_layer("ROADM")
        selected2 = service_list.get_all_selected_service_layers()
        print(f"Selected2: {selected2}")

        service_list.remove_service_layer("ROADM")

    run_step(2, "Service Layer Multi-Select", step_2)

    # ----------------------------
    # Step 3: Service Type
    # ----------------------------
    def step_3():
        # create_frame_html(page)

    run_step(3, "Service Type", step_3)

    # ----------------------------
    # Step 4: Protection Type
    # ----------------------------
    def step_4():
        service_list.select_protection_type("Unprotected")
        service_list.select_protection_type("Protected")
        service_list.select_protection_type("Restoration")
        service_list.select_protection_type("All")

        service_list.set_all_protection_types()
        selected_protection_types = service_list.get_all_selected_protection_types()
        print(f"Selected protection types: {selected_protection_types}")
        
        service_list.remove_all_protection_types()
        
        service_list.select_protection_type("Unprotected")
        selected_protection_types2 = service_list.get_all_selected_protection_types()
        print(f"Selected protection types2: {selected_protection_types2}")
        
        service_list.remove_protection_type("Unprotected")

    run_step(4, "Protection Type", step_4)

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
        # create_frame_html(page)

        service_list.select_service_type("50GHZ")
        service_list.remove_service_type("50GHZ")
        service_list.set_all_service_types()
        service_list.remove_all_service_types()
        service_list.close_service_type_dropdown()

        service_list.set_all_service_types()
        services_list = service_list.get_all_selected_service_types()
        print(f"Services list: {services_list}")

    run_step(6, "...", step_6)

    # ----------------------------
    # Step 7: 
    # ----------------------------
    def step_7():
        services = service_list.get_service_list()
        print(f"services: {services}")

        service_list.click_next()
        service_list.click_previous()

        
        # service_list.click_on_service(0)
        service_list.click_on_service(1)
        service_list.click_on_service(2)
        service_list.click_on_service(3)
        # service_list.click_on_service(4)
        # service_list.click_on_service(5)

        service_list.click_on_service(service_name="test1")
        service_list.click_on_service(service_name="test2")
        service_list.click_on_service(service_name="test4")

        # service_list.click_on_service(1, "test1")
        # service_list.click_on_service()
        

        service_list.click_on_events_alarms_button()

        service_list.set_faults_type("Alarms")
        faults_type = service_list.get_faults_type()
        print(f"Faults type: {faults_type}")

        service_list.set_severity("Critical")
        severity = service_list.get_severity()
        print(f"Severity: {severity}")

        service_list.set_from_date("2022-01-01 00:00:00")
        from_date = service_list.get_from_date()
        print(f"From date: {from_date}")

        service_list.set_to_date("2026-06-02 00:00:00")
        to_date = service_list.get_to_date()
        print(f"To date: {to_date}")

        service_list.set_message("add")

        service_list.message_check_exact_match_only()
        service_list.message_uncheck_exact_match_only()

        service_list.set_faults_type("Events")
        service_list.hide_event(0)
        service_list.show_hidden_events(True)
        service_list.show_hidden_events(False)

        service_list.set_faults_type("Alarms")
        service_list.acknowledge_alarm()

    run_step(7, "...", step_7)

    # ----------------------------
    # Step 8: 
    # ----------------------------
    def step_8():
        # service_list.click_on_path(0)
        service_list.click_on_path(1)
        service_list.close_ROADM_service_path_table()
        service_list.click_on_path(2)
        service_list.close_ROADM_service_path_table()
        service_list.click_on_path(3)
        service_list.close_ROADM_service_path_table()

        service_list.click_on_path(service_name="test1")
        service_list.close_ROADM_service_path_table()
        service_list.click_on_path(service_name="test2")
        service_list.close_ROADM_service_path_table()
        service_list.click_on_path(service_name="test4")
        service_list.close_ROADM_service_path_table()
        
        roadm_service_path_table = service_list.get_ROADM_service_path_table(2)
        print(f"ROADM service path table(by index): {roadm_service_path_table}")

        roadm_service_path_table = service_list.get_ROADM_service_path_table(service_name="test2")
        print(f"ROADM service path table(by name): {roadm_service_path_table}")
        
        # service_list.rename_service_cancel_button()
        service_list.rename_service("changed_test_name_by_index", row_index=3)
        service_list.rename_service("changed_test_name_by_name", old_service_name="changed_test_name_by_index")

        # service_list.remove_service_cancel_button()
        service_list.remove_service(row_index=3)
        service_list.remove_service(service_name="test2")

    run_step(8, "...", step_8)

    # ----------------------------
    # Step 9: 
    # ----------------------------
    def step_9():
        # create_frame_html(page)
        service_list.export_CSV(save_dir = r"C:\temp")

    run_step(9, "...", step_9)

    # ----------------------------
    # Step 10: 
    # ----------------------------
    def step_10():
        # create_frame_html(page)
        service_list.performance_set_display()
        service_list.click_on_performance_button(service_name="test1")
        pm_table_true = service_list.performance_get_pm_table(all_pages=True)
        print(f"\n\n pm_table_true: {pm_table_true}")
        pm_table_false = service_list.performance_get_pm_table(all_pages=False)
        print(f"\n\n pm_table_false: {pm_table_false}")

        service_list.performance_set_period_start("06/06/2026 07:53")
    
        performance_get_period_start = service_list.performance_get_period_start()
        print(f"performance_get_period_start: {performance_get_period_start}")
        
        service_list.performance_set_period_end("07/06/2026 23:54")
        performance_get_period_end = service_list.performance_get_period_end()
        print(f"performance_get_period_end: {performance_get_period_end}")

        service_list.performance_set_device_A("PL-1000GRO (172.16.40.118)")
        device_A = service_list.performance_get_device_A()
        print(f"device_A: {device_A}")
        service_list.performance_set_device_Z("PL-1000GRO (172.16.40.119)")
        device_Z = service_list.performance_get_device_Z()
        print(f"device_Z: {device_Z}")

        service_list.performance_set_port_A("MC 2")
        port_A = service_list.performance_get_port_A()
        print(f"port_A: {port_A}")

        service_list.performance_set_port_Z("MC 1")
        port_Z = service_list.performance_get_port_Z()
        print(f"port_Z: {port_Z}")

        service_list.performance_set_pm_period_type("Days")
        service_list.performance_set_pm_type("Optical Level")

        pm_period_type = service_list.performance_get_pm_period_type()
        print(f"pm_period_type: {pm_period_type}")

        pm_type = service_list.performance_get_pm_type()
        print(f"pm_type: {pm_type}")

        pm_table = service_list.performance_get_pm_table(all_pages=True)
        print(f"pm_table (all pages): {pm_table}")
        pm_table = service_list.performance_get_pm_table(all_pages=False)
        print(f"pm_table (single page): {pm_table}")

        service_list.performance_refresh_pm_table()
        

    run_step(10, "...", step_10)

    print("Test Finished ✅")


if __name__ == "__main__":
    start_time = time.perf_counter()

    with sync_playwright() as p:
        browser, context, page = create_page(p, max_size=True)

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