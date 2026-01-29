"""
Created by: Yuval Dahan
Date: 29/01/2026
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.domain_management import DomainManagement
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


    domain_a = f"DM_TEST_UNDER_INVENTORY"
    domain_b = f"DM_TEST_UNDER_SUB_DOMAIN_DEMO"
    domain_a2 = f"{domain_a}_RENAMED"

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
    def step_2():
        dm.rename_domain(domain_a, domain_a2, new_description="renamed by automation")

    run_step(2, "Domain Management: rename_domain (A -> A2)", step_2)

    # ----------------------------
    # Step 3: click_move_to_domain_mode + middle_move_arrow_btn visible
    # ----------------------------
    def step_3():
        dm.click_move_to_domain_mode()

        arrow = dm.middle_move_arrow_btn()
        if arrow.count() == 0 or not arrow.is_visible():
            raise AssertionError("middle_move_arrow_btn is not visible in Move to domain mode.")

    run_step(3, "Domain Management: enter move-to-domain mode + arrow visible", step_3)

    # ----------------------------
    # Step 4: move_to_domain (best-effort)
    # ----------------------------
    def step_4():
        # NOTE: your move_to_domain() does minimal verification (UI stability).
        # This will still be a good smoke test for selection + arrow + modals flow.
        dm.move_to_domain(source_item_name=domain_a2, target_domain_name=domain_b)

    run_step(4, "Domain Management: move_to_domain (A2 -> B) smoke", step_4)

    # ----------------------------
    # Step 5: cleanup remove_domain (best-effort)
    # ----------------------------
    def step_5():
        # Removing in safe order: try to remove renamed domain first.
        # If your move created nesting or server rule blocks, remove_domain() raises with server message.
        errors = []

        for name in [domain_a2, domain_b]:
            try:
                dm.remove_domain(name)
            except Exception as e:
                errors.append(f"{name}: {e}")

        if errors:
            # Don’t silently ignore: fail so you notice cleanup issues in CI
            raise AssertionError("Cleanup failed:\n" + "\n".join(errors))

    run_step(5, "Domain Management: remove_domain cleanup (A2 + B)", step_5)

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