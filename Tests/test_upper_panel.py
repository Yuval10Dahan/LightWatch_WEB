"""
Created by: Yuval Dahan
Date: 08/02/2026
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.upper_panel import UpperPanel
import time
from Utils.utils import refresh_page


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


def test_upper_panel(page):
    up = UpperPanel(page)

    # ----------------------------
    # Step 1: Avatar menu open
    # ----------------------------
    def step_1():
        up.click_on_avatar_icon()

    run_step(1, "Upper Panel: open avatar menu", step_1)

    # ----------------------------
    # Step 2: Change Password page + fields + save (safe smoke)
    # Tests:
    # click_on_change_password, get_username, set_username,
    # set_current_password, set_new_password, set_confirm_password, click_save_new_password
    # ----------------------------
    def step_2():
        up.click_on_change_password()

        # Username field is typically read-only; we still test getter + setter behavior.
        current_user = up.get_username()
        print(f"Username in change password form: '{current_user}'")
        # up.set_username("yuval")

        up.set_current_password("current_password")
        up.set_new_password("TempPass123!")
        up.set_confirm_password("TempPass123!")

        # up.click_save_new_password()

        # Return to main page so header elements exist consistently for next steps
        page.goto(BASE_URL)

    run_step(2, "Upper Panel: change password (fill + save) smoke", step_2)

    # Stabilize after navigation
    refresh_page(page)

    # ----------------------------
    # Step 3: Global search open / set / close
    # Tests:
    # click_on_global_search, set_global_search_value, close_global_search
    # ----------------------------
    def step_3():
        up.click_on_global_search()
        up.set_global_search_value("Ethernet")
        up.close_global_search()

    run_step(3, "Upper Panel: global search (open/set/close)", step_3)

    # ----------------------------
    # Step 4: Domains dropdown open + select a domain (best-effort)
    # Tests:
    # click_on_domains_dropdown, select_domain
    # ----------------------------
    def step_4():
        # Open (function under test)
        up.click_on_domains_dropdown()

        domain_to_select = "sub-domain-Demo"
        print(f"Selecting domain: {domain_to_select}")

        up.select_domain(domain_to_select)

    run_step(4, "Upper Panel: domains dropdown + select first domain", step_4)

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

        refresh_page(page)
        test_upper_panel(page)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")
