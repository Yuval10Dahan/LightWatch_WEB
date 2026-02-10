"""
Created by: Yuval Dahan
Date: 21/01/2026
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.service_list import ServiceList
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


def test_service_list(page, left_panel):
    # ----------------------------
    # Open page + init POM
    # ----------------------------
    try:
        left_panel.click_service_list()
        service_list = ServiceList(page)
        print("Opened Service List ✅")
    except Exception as e:
        print(f"Failed to open Service List ❌ | Error: {e}")
        return

    # ----------------------------
    # Step 1: Basic visibility / read current filters
    # ----------------------------
    def step_1():
        root = service_list.filters_root()
        _ = root.is_visible()

        sev = service_list.get_severity()
        cat = service_list.get_category()
        order_by = service_list.get_order_by()
        fb = service_list.get_filter_by()

        # ---- Date filter (NEW: correct usage) ----
        from_date_and_time = "2026-01-02 11:14"
        to_date_and_time = "2026-01-24 08:14"

        date_val1 = service_list.get_date()
        service_list.set_date(from_date_and_time, to_date_and_time)
        date_val2 = service_list.get_date()

        print(f"Severity: {sev}")
        print(f"Category: {cat}")
        print(f"Order by: {order_by}")
        print(f"Date: {date_val1}")
        print(f"Date: {date_val2}")
        print(f"Filter By: {fb}")

    run_step(1, "Service List: page is loaded + read filters", step_1)

    # ----------------------------
    # Step 2: Dropdowns basic set (safe values)
    # ----------------------------
    def step_2():
        # Adjust if your environment differs
        service_list.set_severity("Info")
        service_list.set_category("Syslog")

        current_order = service_list.get_order_by()
        if current_order:
            service_list.set_order_by(current_order)

        # Try a common option (if exists)
        try:
            service_list.set_order_by("Source")
        except Exception as e:
            print(f"Order by 'Source' not available (skipping). Reason: {e}")

        print(
            f"After set: Severity={service_list.get_severity()}, "
            f"Category={service_list.get_category()}, "
            f"OrderBy={service_list.get_order_by()}"
        )

        service_list.set_order_by_all()

    run_step(2, "Dropdowns: set Severity/Category + try set Order by", step_2)

    # ----------------------------
    # Step 3: Descending toggle
    # ----------------------------
    def step_3():
        service_list.enable_descending_order()
        service_list.disable_descending_order()
        service_list.enable_descending_order()

    run_step(3, "Sorting: Descending enable/disable/enable", step_3)

    # ----------------------------
    # Step 4: Filter-by switch
    # ----------------------------
    def step_4():
        service_list.set_filter_by("Devices")
        service_list.set_filter_by("Domain/Chassis")
        service_list.set_filter_by("Device type")

        current = service_list.get_filter_by()
        print(f"Filter By current (best-effort): {current}")

    run_step(4, "Filter By: switch modes (Devices / Domain/Chassis / Device type)", step_4)

    # ----------------------------
    # Step 5: Domain/Chassis modal flow (best-effort)
    # ----------------------------
    def step_5():
        service_list.set_filter_by("Domain/Chassis")

        try:
            service_list.select_domain_or_chassis_filterBy_domain_or_chassis("sub-domain-Demo")
            val1 = service_list.get_selected_domain_or_chassis_filterBy_domain_or_chassis()
            print(f"Domain value: {val1}")

            service_list.select_domain_or_chassis_filterBy_domain_or_chassis("sub-sub-domain")
            val2 = service_list.get_selected_domain_or_chassis_filterBy_domain_or_chassis()
            print(f"Domain value: {val2}")

            service_list.reset_domain_or_chassis_filterBy_domain_or_chassis()
            val3 = service_list.get_selected_domain_or_chassis_filterBy_domain_or_chassis()
            print(f"Domain value: {val3}")

        except Exception as e:
            print(f"Domain/Chassis flow not available in this env (skipping). Reason: {e}")

    run_step(5, "Domain/Chassis: try select/reset (if enabled)", step_5)

    # ----------------------------
    # Step 6: Filter By → Devices (virtualized list support)
    # ----------------------------
    def step_6():
        service_list.set_filter_by("Devices")

        # 1) Clear everything first (best-effort)
        service_list.remove_all_devices_filterBy_devices()
        selected0 = service_list.get_all_selected_devices_filterBy_devices()
        print(f"After remove_all, selected count: {len(selected0)} | {selected0[:10]}")

        # 2) Select all devices across scroll/virtualization
        service_list.set_all_devices_filterBy_devices()
        selected_all = service_list.get_all_selected_devices_filterBy_devices()
        print(f"After set_all, selected count: {len(selected_all)} | {selected_all[:10]}")

        if not selected_all:
            raise AssertionError("No devices selected after set_all_devices_filterBy_devices()")

        # 3) Remove ONE device
        device = selected_all[0]
        service_list.remove_device_filterBy_devices(device)

        selected_after_remove = service_list.get_all_selected_devices_filterBy_devices()
        print(f"After remove '{device}', selected count: {len(selected_after_remove)} | {selected_after_remove[:10]}")

        if device in selected_after_remove:
            raise AssertionError(f"Device '{device}' is still selected after remove_device_filterBy_devices()")

        # 4) Re-add it
        service_list.select_device_filterBy_devices(device)

        selected_after_add = service_list.get_all_selected_devices_filterBy_devices()
        print(f"After re-add '{device}', selected count: {len(selected_after_add)} | {selected_after_add[:10]}")

        if device not in selected_after_add:
            raise AssertionError(f"Device '{device}' was not re-selected after select_device_filterBy_devices()")

    run_step(6, "Filter By Devices: remove_all / set_all (scroll) / remove one / re-add", step_6)

    # ----------------------------
    # Step 7: Filter By → Device type (NEW additions)
    # ----------------------------
    def step_7():
        service_list.set_filter_by("Device type")

        # Reset to All first
        service_list.remove_all_devices_filterBy_device_type()
        sel0 = service_list.get_all_selected_devices_filterBy_device_type()
        print(f"After remove_all_device_type: {sel0}")
        if sel0:
            raise AssertionError(f"Expected [] when 'All' is selected, got: {sel0}")

        # Try selecting a concrete device type (environment dependent)
        candidate_types = ["PL-1000G", "PL-2000M", "PL-4000", "Muxponder", "All"]  # adjust freely
        picked = None

        for t in candidate_types:
            try:
                if t == "All":
                    continue
                service_list.select_device_type_filterBy_device_type(t)
                picked = t
                break
            except Exception:
                continue

        if picked is None:
            print("No candidate device type matched this environment (skipping select/remove checks).")
            # still validate that 'All' path works:
            service_list.set_all_devices_filterBy_device_type()
            sel_all = service_list.get_all_selected_devices_filterBy_device_type()
            if sel_all:
                raise AssertionError(f"Expected [] when 'All' is selected, got: {sel_all}")
            return

        sel1 = service_list.get_all_selected_devices_filterBy_device_type()
        print(f"After selecting '{picked}': {sel1}")
        if sel1 != [picked]:
            raise AssertionError(f"Expected [{picked}], got: {sel1}")

        # Remove it (reset to All)
        service_list.remove_device_type_filterBy_device_type(picked)
        sel2 = service_list.get_all_selected_devices_filterBy_device_type()
        print(f"After remove '{picked}' -> All: {sel2}")
        if sel2:
            raise AssertionError(f"Expected [] after reset to All, got: {sel2}")

        # Set all explicitly
        service_list.set_all_devices_filterBy_device_type()
        sel3 = service_list.get_all_selected_devices_filterBy_device_type()
        print(f"After set_all_device_type (All): {sel3}")
        if sel3:
            raise AssertionError(f"Expected [] when 'All' is selected, got: {sel3}")

    run_step(7, "Filter By Device type: select type / remove -> All / set_all", step_7)

    # ----------------------------
    # Step 8: Message filter
    # ----------------------------
    def step_8():
        service_list.set_message("Ethernet")
        service_list.set_message("")

    run_step(8, "Message: set and clear", step_8)

    # ----------------------------
    # Step 9: Pagination (best-effort)
    # ----------------------------
    def step_9():
        try:
            service_list.click_next()
            service_list.click_next()
            service_list.click_next()
        except Exception as e:
            print(f"Next not clickable (maybe disabled / single page). Reason: {e}")

        try:
            service_list.click_previous()
            service_list.click_previous()
            service_list.click_previous()
        except Exception as e:
            print(f"Previous not clickable (maybe disabled / first page). Reason: {e}")

    run_step(9, "Pagination: click next/previous (best-effort)", step_9)

    # ----------------------------
    # Step 10: Events/Alarms panel + tabs (Events history / Alarms / Alarms summary)
    # ----------------------------
    def step_10():
        service_list.open_events_alarms()

        try:
            # =========================
            # Events history
            # =========================
            service_list.click_on_events_history()
            events_data = service_list.get_all_events_history()
            print(f"Events history: {events_data}")

            # headers = events_data.get("headers", [])
            # rows = events_data.get("rows", [])
            # row_count = events_data.get("row_count", len(rows))
            # print(f"Events history -> headers: {len(headers)} | rows: {row_count}")
            # if headers:
            #     print(f"Events history headers: {headers}")
            # if rows:
            #     print(f"Events history first row: {rows[0]}")

            # =========================
            # Alarms
            # =========================
            service_list.click_on_alarms()
            alarms = service_list.get_all_alarms()

            print(f"Alarms -> rows: {len(alarms)}")
            if alarms:
                print(f"Alarms first row: {alarms[0]}")
                print("")
                print(f"Alarms: {alarms}")

            # =========================
            # Alarms summary
            # =========================
            service_list.click_on_alarms_summary()
            summary = service_list.get_alarms_summary()

            print(f"Alarms summary -> rows: {len(summary)}")
            if summary:
                print(f"Alarms summary first row: {summary[0]}")

        finally:
            # Always attempt to close the panel even if one of the reads fails
            try:
                service_list.close_events_alarms()
            except Exception as e:
                print(f"close_events_alarms failed (ignored): {e}")

        # Smoke: Columns modal (not part of the Events/Alarms panel)
        service_list.click_edit_columns()
        service_list.click_revert_changes()
        service_list.click_edit_columns()
        service_list.click_save_changes()


    run_step(10, "Events/Alarms panel: Events history + Alarms + Alarms summary + close + Edit Columns", step_10)

    print("Test Finished ✅")


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