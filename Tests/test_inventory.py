'''
Created by: Yuval Dahan
Date: 28/10/2026
'''


from Utils.utils import create_page
from playwright.sync_api import sync_playwright
from Pages.inventory import Inventory
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
import time


# SERVER_HOST_IP = "172.16.10.22:8080"  # Your base URL here
SERVER_HOST_IP = "172.16.10.22:8443"
BASE_URL = f"https://{SERVER_HOST_IP}/"  # Complete URL with trailing slash
USERNAME = "administrator"
PASSWORD = "administrator"

# Inventory test values (must exist in the inventory of the server under test)
ENTITY_ROW = 1                      # row number (Expand column) of the entity below
ENTITY_IP = "10.60.100.29"
OTHER_ENTITY_IP = "10.60.100.32"    # a second entity, expanded by IP address
PARTIAL_FILTER = "10.60.100.2"      # matches ENTITY_IP (and others) as a substring only
FILTER_BY_OPTIONS = ["Device", "Default"]

# Set to False to skip the Save All Inventory click (it writes the inventory on the server)
SAVE_INVENTORY = True


def run_step(step_num: int, title: str, fn):
    """
    Runs a step and prints consistent success/fail indication.
    A step fails if it raises, or if it returns False / an empty string.
    """
    try:
        result = fn()
        if result is False or result == "":
            raise AssertionError("step returned a failure result")
        print(f"Step {step_num} Success ✅  |  {title}")
        return True
    except Exception as e:
        print(f"Step {step_num} Failed ❌  |  {title}  |  Error: {e}")
        return False

def printed_rows(label: str, rows: list) -> list:
    """Print a short summary of inventory rows and return them."""
    children = sum(1 for r in rows if r["is_child"])
    print(f"    {label}: {len(rows)} row(s) ({len(rows) - children} entity, {children} child)\n")
    print(rows)
    return rows

def test_inventory(page, left_panel):
    left_panel.click_inventory()
    inv = Inventory(page)
    results = []

    def step(title, fn):
        results.append(run_step(len(results) + 1, title, fn))

    def settle(ms: int = 1000):
        page.wait_for_timeout(ms)

    # Start from a known state: everything collapsed, no filters
    if inv.collapse_all_button.is_visible():
        inv.collapse_all()
    inv.uncheck_whole_word()
    inv.set_quick_filter("")
    settle()

    # ---- Refresh / full table ----
    step("Refresh", inv.refresh)
    settle(2000)
    step("Get all inventory (collapsed): entities only",
         lambda: (lambda rows: len(rows) > 0 and not any(r["is_child"] for r in rows))(
             printed_rows("All inventory", inv.get_all_inventory_list())))

    # ---- Expand / collapse ----
    step("Expand all", inv.expand_all)
    is_expanded = inv.is_expanded_all()
    print(f"is expanded: {is_expanded}")
    settle()
    step("Get all inventory (expanded): child rows are listed",
         lambda: any(r["is_child"] for r in inv.get_all_inventory_list()))
    print(inv.get_all_inventory_list())
    step("Collapse all", inv.collapse_all)
    settle()
    step("Get all inventory (collapsed again): entities only",
         lambda: not any(r["is_child"] for r in inv.get_all_inventory_list()))

    step(f"Expand row {ENTITY_ROW}", lambda: inv.expand_by_row(ENTITY_ROW))
    step(f"Row {ENTITY_ROW} shows child rows",
         lambda: inv.get_all_inventory_list()[1]["is_child"])
    step(f"Expand row {ENTITY_ROW} again (no-op, stays expanded)", lambda: inv.expand_by_row(ENTITY_ROW))
    step(f"Expand by IP address {OTHER_ENTITY_IP}",
         lambda: inv.expand_by_ip_address_or_system_name(OTHER_ENTITY_IP))

    # ---- Per-entity inventory ----
    def check_entity(ip):
        rows = printed_rows(f"Inventory of {ip}", inv.get_entity_inventory_list(ip))
        if len(rows) < 2:
            raise AssertionError("expected the chassis row plus at least one child row")
        if rows[0]["is_child"] or rows[0]["class"] != "chassis":
            raise AssertionError("first row is not the chassis row")
        if not all(r["ip_address"] == ip for r in rows):
            raise AssertionError("rows of another entity were returned")
        return True

    step(f"Get entity inventory {ENTITY_IP}", lambda: check_entity(ENTITY_IP))
    step(f"Get entity inventory {OTHER_ENTITY_IP}", lambda: check_entity(OTHER_ENTITY_IP))
    # step("Get entity inventory of an unknown IP returns an empty list",
    #      lambda: inv.get_entity_inventory_list("1.2.3.4", timeout=2000) == [])

    # ---- Filters ----
    for option in FILTER_BY_OPTIONS:
        step(f"Set Filter By '{option}'", lambda o=option: inv.set_filterBy(o))

    # inv.set_filterBy("Device")
    # inv.set_devices("PL-4000M (10.60.100.103)")

    # inv.set_filterBy("Chassis")
    # inv.set_chassis("ALB-15")

    step(f"Quick filter '{ENTITY_IP}'", lambda: inv.set_quick_filter(ENTITY_IP))
    settle()
    step(f"Only entities matching '{ENTITY_IP}' are listed",
         lambda: (lambda rows: len(rows) > 0 and all(r["ip_address"] == ENTITY_IP for r in rows))(
             printed_rows("Filtered inventory", inv.get_all_inventory_list())))

    step(f"Quick filter partial '{PARTIAL_FILTER}'", lambda: inv.set_quick_filter(PARTIAL_FILTER))
    settle()
    partial_count = len(inv.get_all_inventory_list())
    step("Partial filter lists entities", lambda: partial_count > 0)

    step("Check Whole word", inv.check_whole_word)
    settle()
    step("Whole word: partial filter matches fewer rows",
         lambda: len(inv.get_all_inventory_list()) < partial_count)
    step("Uncheck Whole word", inv.uncheck_whole_word)
    settle()
    step("Unchecking Whole word restores the partial matches",
         lambda: len(inv.get_all_inventory_list()) == partial_count)

    step("Clear quick filter", lambda: inv.set_quick_filter(""))
    settle()
    step("Full inventory is listed again", lambda: len(inv.get_all_inventory_list()) > partial_count)

    # ---- Save ----
    if SAVE_INVENTORY:
        step("Save all inventory", inv.save_all_inventory)
    else:
        print("    SAVE_INVENTORY is False - save step skipped")

    if all(results):
        print("Test Success ✅")
    else:
        print(f"Test Failed ❌  |  {results.count(False)} of {len(results)} steps failed")


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

        left_panel = LeftPanel(page)

        # Run the test
        test_inventory(page, left_panel)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")
