'''
Created by: Yuval Dahan
Date: 20/01/2026
'''



from playwright.sync_api import sync_playwright, expect
from Pages.left_panel_page import LeftPanel
from Pages.login_page import LoginPage
from Pages.common_functions import CommonFunctionsPage
import time

# Initialize constants
SERVER_HOST_IP = "172.16.10.22:8080"  # Your base URL here
BASE_URL = f"http://{SERVER_HOST_IP}/"  # Complete URL with trailing slash
USERNAME = "administrator"
PASSWORD = "administrator"

def test_navigation_left_panel(page):
    try:
        # Initialize the LeftPanel class
        left_panel = LeftPanel(page)

        # Test navigation for each section in the left panel

        # Click on "Service List" and verify it's visible
        left_panel.click_service_list()

        # Click on "Management Map" and verify it's visible
        left_panel.click_management_map()

        # Click again on "Management Map" and verify it's handle correctly
        left_panel.click_management_map()

        # Click on "Service Provisioning" and verify it's visible
        left_panel.click_service_provisioning()

        # Click on "Performance" and verify it's visible
        left_panel.click_performance()

        # Click on "Device Discovery" and verify it's visible
        left_panel.click_device_discovery()

        # Click on "Domain Management" and verify it's visible
        left_panel.click_domain_management()

        # Click on "Inventory" and verify it's visible
        left_panel.click_inventory()

        # Click on "Alarms & Events" and verify it's visible
        left_panel.click_alarms_and_events()

        # Click on "Common Functions" and verify it's visible
        left_panel.click_common_functions()
        common_functions = CommonFunctionsPage(page)
        common_functions.click_exit()

        # Click on "User Management" and verify it's visible
        left_panel.click_user_management()

        # Click on "Task Manager" and verify it's visible
        left_panel.click_task_manager()

        # Click on "System Configuration" and verify it's visible
        left_panel.click_system_configuration()

        # Finally, test logout
        left_panel.click_logout()

        print("Test Success ✅")
    
    except:
        print("Test Failed ❌")


def run_tests():
    with sync_playwright() as p:
        # Launch browser and context
        browser = p.chromium.launch(headless=False)  # Set headless=False for debugging
        context = browser.new_context()
        page = context.new_page()

        login_page = LoginPage(page)
        login_page.goto(BASE_URL)
        if login_page.login(USERNAME, PASSWORD):
            print("Login Success ✅")
        else:
            print("Login Failed ❌")

        # Run the test
        test_navigation_left_panel(page)

        # Close the browser context and browser
        context.close()
        browser.close()

if __name__ == "__main__":
    start_time = time.perf_counter()
    run_tests()
    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")