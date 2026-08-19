"""
Created by: Yuval Dahan
Date: 06/03/2026
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.performance import Performance
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
        left_panel.click_performance()
        performance = Performance(page)
        print("Opened Performance ✅")
    except Exception as e:
        print(f"Failed to open Performance ❌ | Error: {e}")
        return

    # ----------------------------
    # Step 1: 
    # ----------------------------
    def step_1():
        # create_frame_html(page)

        pm_type_options = performance.get_pm_type_current_dropdown_options()
        print(f"PM type options: {pm_type_options}")

        performance.export_CSV()
        performance.click_next()
        performance.click_previous()
        

    run_step(1, "...", step_1)

    # # ----------------------------
    # # Step 2: 
    # # ----------------------------
    # def step_2():
    #     # create_frame_html(page) 
    #     performance.set_period_start("06/06/2026 07:53")
    #     performance.set_period_start("07/06/2026 21:53")
    #     period_start = performance.get_period_start()
    #     print(f"Period start: {period_start}")

    #     performance.set_period_end("08/06/2026 07:53")
    #     performance.set_period_end("07/06/2026 23:54")
    #     period_end = performance.get_period_end()
    #     print(f"Period end: {period_end}")

    # run_step(2, "...", step_2)

    # # ----------------------------
    # # Step 3: 
    # # ----------------------------
    # def step_3():
    #     # create_frame_html(page)
    #     performance.set_device("PL-4000M (172.16.30.124)")
    #     device = performance.get_device()
    #     print(f"Device: {device}")

    # run_step(3, "...", step_3)

    # # ----------------------------
    # # Step 4: 
    # # ----------------------------
    # def step_4():
    #     # create_frame_html(page)
    #     performance.set_port("MC 3")
    #     port = performance.get_port()
    #     print(f"Port: {port}")

    #     performance.set_port("COM #1/W")
    #     port = performance.get_port()
    #     print(f"Port: {port}")

    # run_step(4, "...", step_4)

    # # ----------------------------
    # # Step 5: 
    # # ----------------------------
    # def step_5():
    #     # create_frame_html(page)
    #     performance.set_pm_period_type("Days")
    #     period_type = performance.get_pm_period_type()
    #     print(f"PM period type: {period_type}")

    #     performance.set_pm_period_type("15 Minutes")
    #     period_type = performance.get_pm_period_type()
    #     print(f"PM period type: {period_type}")

    # run_step(5, "...", step_5)

    # # ----------------------------
    # # Step 6: 
    # # ----------------------------
    # def step_6():
    #     # create_frame_html(page)
    #     performance.set_device("PL-1000TECrypto (172.16.40.24)")
    #     performance.set_pm_type("Optical Level")
    #     pm_type = performance.get_pm_type()
    #     print(f"PM type: {pm_type}")

    # run_step(6, "...", step_6)

    # # ----------------------------
    # # Step 7: 
    # # ----------------------------
    # def step_7():
    #     # create_frame_html(page)
    #     performance.refresh_pm_table()
    #     performance.refresh_pm_table()
    #     performance.refresh_pm_table()
    #     performance.refresh_pm_table()
    #     performance.refresh_pm_table()

    # run_step(7, "...", step_7)

    # ----------------------------
    # Step 8: 
    # ----------------------------
    def step_8():
        # # create_frame_html(page)
        performance.set_device("PL-1000IL2 (172.16.30.13)")
        pm_table_3_fields = performance.get_pm_table(all_pages=False)
        print(f"PM TABLE 3 FIELDS FIRST PAGE: \n\n{pm_table_3_fields}\n\n")
        pm_table_3_fields = performance.get_pm_table(all_pages=True)
        print(f"PM TABLE 3 FIELDS ALL PAGES: \n\n{pm_table_3_fields}\n\n")

        pm_table_32_intervals = performance.get_pm_table_number_of_intervals(32)
        print(f"PM TABLE 3 FIELDS FIRST 32 INTERVALS: \n\n{pm_table_32_intervals}\n\n")
        pm_table_32_intervals_length = len(pm_table_32_intervals)
        print(f"PM TABLE 3 FIELDS FIRST 32 INTERVALS LENGTH: \n\n{pm_table_32_intervals_length}\n\n")

        performance.set_device("PL-4000M (172.16.30.124)")
        pm_table_6_fields = performance.get_pm_table(all_pages=False)
        print(f"PM TABLE 6 FIELDS FIRST PAGE: \n\n{pm_table_6_fields}\n\n")
        pm_table_6_fields = performance.get_pm_table(all_pages=True)
        print(f"PM TABLE 6 FIELDS ALL PAGES: \n\n{pm_table_6_fields}\n\n")
        print(f"\n\n PM TABLE 6 Last row: \n\n{pm_table_6_fields[-1]}\n\n")

        performance.set_device("PL-8000M (172.16.30.114)")
        pm_table_12_fields = performance.get_pm_table(all_pages=False)
        print(f"PM TABLE 12 FIELDS FIRST PAGE: \n\n{pm_table_12_fields}\n\n")
        pm_table_12_fields = performance.get_pm_table(all_pages=True)
        print(f"PM TABLE 12 FIELDS ALL PAGES: \n\n{pm_table_12_fields}\n\n")
        print(f"\n\n PM TABLE 12 Last row: \n\n{pm_table_12_fields[-1]}\n\n")

    run_step(8, "...", step_8)

    # # ----------------------------
    # # Step 9: 
    # # ----------------------------
    # def step_9():
    #     create_frame_html(page)

    # run_step(9, "...", step_9)

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