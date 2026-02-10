"""
Created by: Yuval Dahan
Date: 04/02/2026
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.alarms_and_events import AlarmsAndEvents
import time
from time import sleep
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


def _open_alarms_and_events(left_panel: LeftPanel):
    """
    Open Domain Management via LeftPanel.
    Expects left_panel.click_domain_management() to return True on success.
    """
    try:
        ok = left_panel.click_alarms_and_events()
    except Exception as e:
        raise AssertionError(
            f"Failed to call left_panel.click_alarms_and_events(). Error: {e}"
        )

    if ok is not True:
        raise AssertionError(
            "left_panel.click_alarms_and_events() returned False "
            "(Alarms & Events did not become active)."
        )


def test_alarms_and_events(page, left_panel):
    ae = AlarmsAndEvents(page)

    # ----------------------------
    # Open Alarms & Events
    # ----------------------------
    try:
        _open_alarms_and_events(left_panel)
        # Basic page signal: pagination exists (if the page loads)
        _ = page.locator("div.pagination").first.is_visible()
        print("Opened Alarms & Events ✅")
    except Exception as e:
        print(f"Failed to open Alarms & Events ❌ | Error: {e}")
        return

    # ----------------------------
    # Step 1: Faults type set/get (safe: set to current)
    # ----------------------------
    def step_1():
        cur = ae.get_faults_type()
        print(f"Faults type (current): {cur}")
        if cur:
            ae.set_faults_type(cur)
            after = ae.get_faults_type()
            print(f"Faults type (after): {after}")
        
        events = "Events"
        ae.set_faults_type(events)
        after = ae.get_faults_type()
        if after != events:
            raise AssertionError(f"Expected '{events}', got '{after}'")

    run_step(1, "Faults type: get + set(current) + get", step_1)

    # ----------------------------
    # Step 2: Severity set/get + set_all_severities
    # ----------------------------
    def step_2():
        cur = ae.get_severity()
        print(f"Severity (current): {cur}")

        if cur:
            ae.set_severity(cur)
            after = ae.get_severity()
            print(f"Severity (after set current): {after}")

            severity = "Critical"
            ae.set_severity(severity)
            after = ae.get_severity()
            if after != severity:
                raise AssertionError(f"Expected '{severity}', got '{after}'")

        ae.set_all_severities()
        all_val = ae.get_severity()
        print(f"Severity (after set_all): {all_val}")

    run_step(2, "Severity: get/set + set_all", step_2)

    # ----------------------------
    # Step 3: Category set/get + set_all_categories
    # ----------------------------
    def step_3():
        cur = ae.get_category()
        print(f"Category (current): {cur}")

        if cur:
            ae.set_category(cur)
            after = ae.get_category()
            print(f"Category (after set current): {after}")

            category = "Device"
            ae.set_category(category)
            after = ae.get_category()
            if after != category:
                raise AssertionError(f"Expected '{category}', got '{after}'")

        ae.set_all_categories()
        all_val = ae.get_category()
        print(f"Category (after set_all): {all_val}")

    run_step(3, "Category: get/set + set_all", step_3)

    # ----------------------------
    # Step 4: Filter by set/get (safe: set to current)
    # ----------------------------
    def step_4():
        cur = ae.get_filterBy()
        print(f"Filter by (current): {cur}")
        if cur:
            ae.set_filterBy(cur)
            after = ae.get_filterBy()
            print(f"Filter by (after): {after}")

            filterBy = "Devices"
            ae.set_filterBy(filterBy)
            after = ae.get_filterBy()
            if after != filterBy:
                raise AssertionError(f"Expected '{filterBy}', got '{after}'")

    run_step(4, "Filter by: get + set(current) + get", step_4)

    # ----------------------------
    # Step 5: Filter By Devices (remove_all / set_all / remove one / re-add)
    # ----------------------------
    def step_5():
        ae.set_filterBy("Devices")

        # Clear selections first (best-effort)
        ae.remove_all_devices_filterBy_devices()
        sel0 = ae.get_all_selected_devices_filterBy_devices()
        print(f"Devices selected after remove_all: {len(sel0)} | {sel0[:10]}")

        # Select all across scroll
        ae.set_all_devices_filterBy_devices()
        sel_all = ae.get_all_selected_devices_filterBy_devices()
        print(f"Devices selected after set_all: {len(sel_all)} | {sel_all}")
        if not sel_all:
            raise AssertionError("No devices selected after set_all_devices_filterBy_devices().")

        # Remove one + re-add
        d = sel_all[0]
        ae.remove_device_filterBy_devices(d)
        sel_after_remove = ae.get_all_selected_devices_filterBy_devices()
        print(f"After remove '{d}': {len(sel_after_remove)}")
        if d in sel_after_remove:
            raise AssertionError(f"Device '{d}' still selected after remove_device_filterBy_devices().")

        ae.select_device_filterBy_devices(d)
        sel_after_add = ae.get_all_selected_devices_filterBy_devices()
        print(f"After re-add '{d}': {len(sel_after_add)}")
        if d not in sel_after_add:
            raise AssertionError(f"Device '{d}' not selected after select_device_filterBy_devices().")

    run_step(5, "Filter By Devices: remove_all / set_all / remove one / re-add", step_5)

    # ----------------------------
    # Step 6: Filter By Domain/Chassis (select all + get)
    # ----------------------------
    def step_6():
        ae.set_filterBy("Domain/Chassis")

        ae.select_domain_or_chassis_filterBy_domain_or_chassis("sub-domain-Demo")
        ae.select_all_domains_filterBy_domain_or_chassis()
        ae.select_domain_or_chassis_filterBy_domain_or_chassis("BS-12/12")
        
        selected = ae.get_selected_domain_or_chassis_filterBy_domain_or_chassis()
        print(f"Domain/Chassis selected: {selected}")

        if not selected:
            raise AssertionError("Domain/Chassis selection is empty after select_all_domains_filterBy_domain_or_chassis().")

    run_step(6, "Filter By Domain/Chassis: select all domains + get selected", step_6)

    # ----------------------------
    # Step 7: Date range (from/to) set/get
    # ----------------------------
    def step_7():
        # Use supported input format: 'YYYY-MM-DD HH:MM[:SS]'
        from_dt = "2026-02-01 00:00:00"
        to_dt = "2026-02-04 23:59:00"

        ae.set_from_date(from_dt)
        got_from = ae.get_from_date()
        print(f"From date -> got: {got_from}")
        if not got_from:
            raise AssertionError("From date is empty after set_from_date().")

        ae.set_to_date(to_dt)
        got_to = ae.get_to_date()
        print(f"To date -> got: {got_to}")
        if not got_to:
            raise AssertionError("To date is empty after set_to_date().")

    run_step(7, "Date range: set/get From + set/get To", step_7)

    # ----------------------------
    # Step 8: Message filter + exact match toggle on/off
    # ----------------------------
    def step_8():
        ae.set_message("Ethernet")
        ae.message_check_exact_match_only()
        ae.message_uncheck_exact_match_only()
        ae.set_message("")  # clear

    run_step(8, "Message: set/clear + exact match toggle on/off", step_8)

    # ----------------------------
    # Step 9: Ack checkbox (best-effort: only if at least 1 row exists)
    # ----------------------------
    def step_9():
        rows = page.locator("table tbody tr")
        if rows.count() == 0:
            print("Ack: no rows in table -> skipping Ack checks.")
            return

        # Try check row 0
        ae.check_Ack(0)
        # Try uncheck row 0 (may not be allowed)
        try:
            ae.uncheck_Ack(0)
        except Exception as e:
            print(f"Ack uncheck not allowed / not toggleable (ignored): {e}")

    run_step(9, "Ack: check/uncheck row 0 (best-effort)", step_9)

    # ----------------------------
    # Step 10: Pagination next/previous (best-effort)
    # ----------------------------
    def step_10():
        ae.set_faults_type("Events") 

        # Next a couple times
        for _ in range(10):
            ok = ae.click_next()
            print(f"click_next -> {ok}")
            if not ok:
                break

        # Previous a couple times
        for _ in range(10):
            ok = ae.click_previous()
            print(f"click_previous -> {ok}")
            if not ok:
                break

    run_step(10, "Pagination: next/previous (best-effort)", step_10)

    # ----------------------------
    # Step 11: get_all_events + get_all_alarms
    # ----------------------------
    def step_11():
        # ---- Events ----
        events = ae.get_all_events()
        print(f"Events count: {len(events)}")
        # print(f"Sample event row: {events[0] if events else 'N/A'}")
        # print(f"Events List: {events}")

        if events:
            # Basic structure sanity check on first row
            first = events[0]
            print(f"Sample event row: {events[0] if events else 'N/A'}")
            if not isinstance(first, dict):
                raise AssertionError("get_all_events returned non-dict rows.")
            print(f"Sample event row keys: {list(first.keys())}")
        else:
            print("No events found (table empty) – OK")

        # ---- Alarms ----
        alarms = ae.get_all_alarms()
        print(f"Alarms count: {len(alarms)}")

        if alarms:
            first = alarms[0]
            if not isinstance(first, dict):
                raise AssertionError("get_all_alarms returned non-dict rows.")
            print(f"Sample alarm row keys: {list(first.keys())}")
        else:
            print("No alarms found (table empty) – OK")


    run_step(11, "Alarms & Events: get_all_events + get_all_alarms", step_11)

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

        test_alarms_and_events(page, left_panel)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")
