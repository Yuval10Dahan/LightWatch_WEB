"""
Created by: Yuval Dahan
Date: 28/01/2026
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.service_provisioning import ServiceProvisioning
from Pages.upper_panel import UpperPanel
import time
from Utils.utils import refresh_page, create_frame_html, create_page


SERVER_HOST_IP = "172.16.10.22:8080"
# SERVER_HOST_IP = "10.30.2.20:8080"
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


def open_service_provisioning(left_panel: LeftPanel):
    """
    Open Service Provisioning modal.
    Adjust this if your LeftPanel method name changes.
    """
    left_panel.click_service_provisioning()


def test_service_provisioning(page, left_panel):
    sp = ServiceProvisioning(page)
    up = UpperPanel(page)

    # # ----------------------------
    # # Step 1: Open modal + Exit
    # # ----------------------------
    # def step_1():
    #     open_service_provisioning(left_panel)
    #     sp.wait_modal_visible()

    #     sp.click_exit()
    #     sp.wait_modal_hidden()

    # run_step(1, "Provisioning: open modal + Exit closes it", step_1)

    # # ----------------------------
    # # Step 2: Create ROADM service
    # # ----------------------------
    # def step_2():
    #     up.select_domain("roadm_domain")

    #     open_service_provisioning(left_panel)
    #     sp.create_ROADM_service()
    #     sp.set_ROADM_mode("Chassis to chassis")
    #     sp.set_ROADM_protection("Protected")
    #     sp.set_ROADM_A_chassis("Chassis: 65")
    #     sp.set_ROADM_Z_chassis("Chassis: 67")
    #     sp.set_ROADM_provisioning_type("Fixed Grid")
    #     sp.set_ROADM_bandwidth("50GHz (m = 4)")
    #     sp.set_ROADM_service_name("Yuval-Test-ROADM")
    #     sp.enable_ROADM_path_restriction()
    #     sp.disable_ROADM_path_restriction()
    #     sp.ROADM_service_click_next()

    #     sp.set_ROADM_path2_A_device("172.16.40.118 (Flex-Grid WSS)")
    #     sp.set_ROADM_path2_A_port("Port 3 (Fixed Grid)")
    #     sp.set_ROADM_path2_Z_device("172.16.40.119 (Flex-Grid WSS)")
    #     sp.set_ROADM_path2_Z_port("Port 5 (Flex Grid)")
    #     sp.ROADM_service_click_back()
    #     sp.set_ROADM_protection("Unprotected")
    #     sp.ROADM_service_click_next()

    #     sp.set_ROADM_path1_A_device("172.16.40.118 (Flex-Grid WSS)")
    #     sp.set_ROADM_path1_A_port("Port 2 (Fixed Grid)")
    #     sp.set_ROADM_path1_Z_device("172.16.40.119 (Flex-Grid WSS)")
    #     sp.set_ROADM_path1_Z_port("Port 2 (Fixed Grid)")
    #     sp.ROADM_service_click_next()

    #     table_path1 = sp.get_ROADM_path1_routes_table()
    #     print(f"table path 1: {table_path1}")
    #     sp.ROADM_path1_click_on_route(0)
    #     sp.ROADM_service_click_next()

    #     sp.set_ROADM_path1_channel("# 14")
    #     sp.ROADM_service_create()

    #     # create_frame_html(page)

    # run_step(2, "Provisioning: create ROADM service", step_2)

    # # ----------------------------
    # # Step 3: Create OTN service
    # # ----------------------------
    # def step_3():
    #     open_service_provisioning(left_panel)
    #     sp.create_OTN_service()
    #     # sp.set_OTN_A_node()
    #     # sp.set_OTN_A_port()
    #     sp.OTN_service_refresh()
    #     sp.enable_OTN_protection()
    #     sp.disable_OTN_protection()
    #     # sp.set_OTN_service_type()

    #     sp.enable_OTN_rate_limit()
    #     sp.disable_OTN_rate_limit()
    #     sp.enable_OTN_rate_limit()

    #     sp.set_OTN_limit_to("ODU2")      

    # run_step(3, "Provisioning: create OTN service", step_3)

    # # ----------------------------
    # # Step 4: Create CHASSIS service
    # # ----------------------------
    # def step_4():
    #     open_service_provisioning(left_panel)
    #     sp.create_CHASSIS_service()

    # run_step(4, "Provisioning: create CHASSIS service", step_4)

    # # ----------------------------
    # # Step 5: 
    # # ----------------------------
    # def step_5():
    #     open_service_provisioning(left_panel)
    #     sp.create_OTN_service()
    #     # create_frame_html(page)
    #     # sp.set_OTN_A_node("PL-2000M (172.16.40.17)")
    #     sp.set_OTN_A_node("PL-4000M (10.60.100.103)")
    #     sp.set_OTN_A_port("Port 29")
    #     sp.set_OTN_service_type("GBE10LAN")
    #     sp.set_OTN_limit_to("6")

    # run_step(5, "...", step_5)

    # ----------------------------
    # Step 5: 
    # ----------------------------
    def step_5():
        open_service_provisioning(left_panel)
        sp.create_OTN_service()
        # create_frame_html(page)
        sp.set_OTN_service_name("Yuval test ROADM service 1")
        sp.enable_OTN_auto_path()
        sp.disable_OTN_auto_path()

    run_step(5, "...", step_5)

    print("Test Finished ✅") 


if __name__ == "__main__":

    start_time = time.perf_counter()

    with sync_playwright() as p:
        browser, context, page = create_page(p, max_size=True)

        login_page = LoginPage(page)
        login_page.goto(BASE_URL)

        if not login_page.login(USERNAME, PASSWORD):
            print("Login Failed ❌")
            context.close()
            browser.close()
            raise SystemExit(1)

        print("Login Success ✅")

        left_panel = LeftPanel(page)
        refresh_page(page)

        test_service_provisioning(page, left_panel)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")