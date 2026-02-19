"""
Created by: Yuval Dahan
Date: 29/01/2026
"""

from playwright.sync_api import sync_playwright, expect
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.domain_management import DomainManagement
import time
from Utils.utils import refresh_page
from time import sleep


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

def _open_domain_management(left_panel: LeftPanel):
    """
    Open Domain Management via LeftPanel.
    Expects left_panel.click_domain_management() to return True on success.
    """
    try:
        ok = left_panel.click_domain_management()
    except Exception as e:
        raise AssertionError(
            f"Failed to call left_panel.click_domain_management(). Error: {e}"
        )

    if ok is not True:
        raise AssertionError(
            "left_panel.click_domain_management() returned False "
            "(Domain Management did not become active)."
        )

def test_domain_management(page, left_panel):
    dm = DomainManagement(page)

    # ----------------------------
    # Open Domain Management
    # ----------------------------
    try:
        _open_domain_management(left_panel)
        _ = dm.root().is_visible()
        print("Opened Domain Management ✅")
    except Exception as e:
        print(f"Failed to open Domain Management ❌ | Error: {e}")
        return

    refresh_page(page)
    sleep(10)

    domain_a = f"DM_TEST_UNDER_INVENTORY"
    domain_b = f"DM_TEST_UNDER_SUB_DOMAIN_DEMO"
    domain_a2 = f"{domain_a}_RENAMED"
    domain_b2 = f"{domain_b}_RENAMED"
    move_domain = domain_b
    move_chassis = "Chassis: 8/8"

    # ----------------------------
    # Step 1: add_domain (A + B)
    # ----------------------------
    def step_1():
        dm.add_domain(domain_a, domain_description="auto test domain A", parent_domain_name="Inventory")
        dm.add_domain(domain_b, domain_description="auto test domain B", parent_domain_name="sub-domain-Demo")

    run_step(1, "Domain Management: add_domain (create A + B)", step_1)

    # ----------------------------
    # Step 2: rename_domain (A -> A2)
    # ----------------------------
    chassis_a = "BS-12/12"
    chassis_b = "Chassis: 35/35"
    chassis_a2 = f"RENAMED_BS-12"
    chassis_b2 = f"RENAMED_Chassis: 35"

    def step_2():
        dm.rename_domain(chassis_a, chassis_a2, new_description="renamed by automation")
        dm.rename_domain(chassis_b, chassis_b2, new_description="renamed by automation2")

        dm.rename_domain(chassis_a2, "BS-12", new_description="")
        dm.rename_domain(chassis_b2, "Chassis: 35", new_description="")

    run_step(2, "Domain Management: rename_domain (A -> A2)", step_2)

    # ----------------------------
    # Step 3: move_to_domain (best-effort)
    # ----------------------------
    def step_3():
        dm.move_to_domain(source_item_name=move_domain, target_domain_name="Default")
        dm.move_to_domain(source_item_name=move_chassis, target_domain_name="sub-domain-Demo")

        # dm.move_to_domain(source_item_name=move_chassis, target_domain_name="sub-domain-Demo")
        # dm.move_to_domain(source_item_name=move_domain, target_domain_name=move_domain)

        dm.move_to_domain(source_item_name=move_domain, target_domain_name="sub-domain-Demo")
        dm.move_to_domain(source_item_name=move_chassis, target_domain_name="Default")

    run_step(3, "Domain Management: move_to_domain (A2 -> B) smoke", step_3)

    # ----------------------------
    # Step 4: cleanup remove_domain (best-effort)
    # ----------------------------
    def step_4():
        for name in [domain_a, domain_b]:
                dm.remove_domain(name)

    run_step(4, "Domain Management: remove_domain cleanup (A2 + B)", step_4)

    # ----------------------------
    # Step 5: Change CHASSIS ID (open -> previous -> close)
    # ----------------------------
    def step_5():
        chassis_name_roadm = "PL-1000GRO (10.60.100.30)"   
        chassis_name_transponder = "PL-2000ADS (172.16.30.15)"  
        chassis_name_muxponder = "PL-4000M (10.60.100.100)"
        wrong_parent_chassis_name = "Chassis: 200/200"

        # 1) Open Change Chassis ID modal (NEW mode, but we won't save)
        dm.change_CHASSIS_ID(
            chassis_id=chassis_name_transponder,
            to_mode="existing",
            new_chassis_id=None, 
            existing_chassis_id="BS-12/12",
            parent_chassis="DC-14"
        )
        print("finished change number 1")

        dm.change_CHASSIS_ID(
            chassis_id=chassis_name_transponder,
            to_mode="existing",
            new_chassis_id=None, 
            existing_chassis_id="DC-14",
            parent_chassis="BS-12/12"
        )
        print("finished change number 2")

        dm.change_CHASSIS_ID(
            chassis_id=chassis_name_roadm,
            to_mode="new",
            new_chassis_id="99", 
            existing_chassis_id=None,
            parent_chassis="BS-12/12"
        )
        print("finished change number 3")

        dm.change_CHASSIS_ID(
            chassis_id=chassis_name_roadm,
            to_mode="existing",
            new_chassis_id=None, 
            existing_chassis_id="BS-12/12",
            parent_chassis="Chassis: 99"
        )
        print("finished change number 4")

        dm.remove_chassis("Chassis: 99/99")

        # dm.remove_device("PL-1000GRO (10.60.100.38)", parent_domain_name="Default", parent_chassis="DC-14")

    run_step(5, "Domain Management: Change CHASSIS ID (Previous + Close)", step_5)

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

        test_domain_management(page, left_panel)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")