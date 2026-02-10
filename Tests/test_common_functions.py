'''
Created by: Yuval Dahan
Date: 20/01/2026
'''



from playwright.sync_api import sync_playwright
from Pages.common_functions import CommonFunctionsPage
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
import time


SERVER_HOST_IP = "172.16.10.22:8080"  # Your base URL here
BASE_URL = f"http://{SERVER_HOST_IP}/"  # Complete URL with trailing slash
USERNAME = "administrator"
PASSWORD = "administrator"

def test_common_functions(page, left_panel):
    try:
        left_panel.click_common_functions()
        common_functions = CommonFunctionsPage(page)
        
        # First, ensure the page is visible
        common_functions.is_common_functions_page_visible()

        # Click on the desired function and assert visibility of confirmation text
        common_functions.click_polling_restart()
        common_functions.click_deleting_OTN_inconsistent_services()
        common_functions.click_synchronizing_OTN_services()
        common_functions.click_deleting_ROADM_inconsistent_services()
        common_functions.click_synchronizing_ROADM_services()

        # Click Exit and ensure the page disappears
        common_functions.click_exit()

        print("Test Success ✅")
    
    except:
        print("Test Failed ❌")

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

        left_panel = LeftPanel(page)

        # Run the test
        test_common_functions(page, left_panel)

        context.close()
        browser.close()
    
    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")
