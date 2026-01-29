"""
Created by: Yuval Dahan
Date: 28/01/2026
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.service_provisioning import ServiceProvisioning
import time
from Utils.utils import refresh_page


SERVER_HOST_IP = "172.16.10.62:8080"
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

    # ----------------------------
    # Step 1: Open modal + Exit
    # ----------------------------
    def step_1():
        open_service_provisioning(left_panel)
        sp.wait_modal_visible()

        sp.click_exit()
        sp.wait_modal_hidden()

    run_step(1, "Provisioning: open modal + Exit closes it", step_1)

    # ----------------------------
    # Step 2: Create ROADM service
    # ----------------------------
    def step_2():
        open_service_provisioning(left_panel)
        sp.create_ROADM_service()

    run_step(2, "Provisioning: create ROADM service", step_2)

    # ----------------------------
    # Step 3: Create OTN service
    # ----------------------------
    def step_3():
        open_service_provisioning(left_panel)
        sp.create_OTN_service()

    run_step(3, "Provisioning: create OTN service", step_3)

    # ----------------------------
    # Step 4: Create CHASSIS service
    # ----------------------------
    def step_4():
        open_service_provisioning(left_panel)
        sp.create_CHASSIS_service()

    run_step(4, "Provisioning: create CHASSIS service", step_4)

    print("Test Finished ✅")


if __name__ == "__main__":
    start_time = time.perf_counter()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

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