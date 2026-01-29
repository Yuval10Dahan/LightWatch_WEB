'''
Created by: Yuval Dahan
Date: 21/01/2026
'''

from playwright.sync_api import Page, expect
from typing import Callable, List, Optional
import time
import re
from time import sleep
from datetime import datetime


MAX_SCROLL_PAGES = 60


class ServiceList:
    """
    Service List page – handles filters, ordering, navigation,
    and table-level operations for Events / Alarms.
    """

    def __init__(self, page: Page):
        self.page = page

    # ==========================================================
    # Internal small helpers 
    # ==========================================================
    def wait_until(self, condition: Callable[[], bool], timeout_ms: int = 10000, interval_ms: int = 200):
        """
        Polls condition() until it returns True or timeout.
        Raises AssertionError on timeout.
        """
        end_time = time.time() + (timeout_ms / 1000.0)
        last_exc = None

        while time.time() < end_time:
            try:
                if condition():
                    return
                last_exc = None
            except Exception as e:
                last_exc = e

            time.sleep(interval_ms / 1000.0)

        if last_exc:
            raise AssertionError(f"Condition not met within {timeout_ms}ms. Last error: {last_exc}")
        raise AssertionError(f"Condition not met within {timeout_ms}ms.")

    @staticmethod
    def _clean(s: str) -> str:
        """
        Normalize whitespace in a string and strip leading/trailing spaces.
        """
        return re.sub(r"\s+", " ", (s or "").strip())

    def filters_root(self):
        """
        Return the root locator for the Service List filters section.
        Used as a base for locating filter controls.
        """
        return self.page.locator(".service-filters").first

    def dropdown(self, label: str):
        """
        Locate a dropdown component by its label text.
        """
        root = self.filters_root()
        dropdown = root.locator(f"app-dropdown[label='{label}']").first
        expect(dropdown).to_be_visible(timeout=5000)
        return dropdown

    def dropdown_selected_text(self, label: str) -> str:
        """
        Return the currently selected value of a labeled dropdown.
        """
        dropdown = self.dropdown(label)
        selected = dropdown.locator(".selected-view span").first
        expect(selected).to_be_visible(timeout=5000)
        return self._clean(selected.inner_text())

    def open_dropdown(self, label: str):
        """
        Open a labeled dropdown by clicking its toggle button.
        """
        dropdown = self.dropdown(label)
        btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
        expect(btn).to_be_visible(timeout=5000)
        btn.click(force=True)

    def dropdown_pick(self, label: str, value: str, timeout: int = 8000):
        """
        Select a value from a labeled dropdown.
        """
        before = self.dropdown_selected_text(label)

        # Open dropdown
        dropdown = self.dropdown(label)
        btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
        expect(btn).to_be_visible(timeout=timeout)

        btn.click(force=True)

        # Target the correct menu for this dropdown
        menu = dropdown.locator(f"div.dropdown-menu[data-label='{label}']").first
        expect(menu).to_be_visible(timeout=timeout)

        # Pick exact item (use exact-text match)
        # Using regex ^\s*VALUE\s*$ avoids "All" matching "All Something"
        item = menu.locator("li.dropdown-item", has_text=re.compile(rf"^\s*{re.escape(value)}\s*$", re.IGNORECASE)).first

        # If not found, give a useful error with available options
        if item.count() == 0:
            options = menu.locator("li.dropdown-item").all_inner_texts()
            options = [self._clean(x) for x in options if self._clean(x)]
            raise AssertionError(f"Value '{value}' not found in dropdown '{label}'. Available: {options}")

        item.scroll_into_view_if_needed()
        item.click(force=True)

        # Wait for selected value to update 
        target = value.strip().lower()

        def changed():
            try:
                return self.dropdown_selected_text(label).strip().lower() == target
            except Exception:
                return False

        self.wait_until(changed, timeout_ms=timeout, interval_ms=150)

        after = self.dropdown_selected_text(label)
        if after.strip().lower() != target:
            # Ensure it changed
            if after == before:
                raise AssertionError(f"Dropdown '{label}' selection did not change (still '{after}').")

    def filter_by_container(self):
        """
        Return the 'Filter by' container.
        """
        root = self.filters_root()
        radio_btn = root.locator("app-radio-button[label='Filter by']").first
        expect(radio_btn).to_be_visible(timeout=5000)
        return radio_btn

    def date_input_field(self):
        """
        Return the date range input field.
        """
        root = self.filters_root()
        date_inp = root.locator("input[formcontrolname='dateRange']").first
        expect(date_inp).to_be_visible(timeout=5000)
        return date_inp

    def message_input_field(self):
        """
        Return the Message filter input field.
        """
        root = self.filters_root()
        inp = root.locator("app-input[label='Message'] input[type='text']").first
        expect(inp).to_be_visible(timeout=5000)
        return inp

    def descending_checkbox(self):
        """
        Return the Descending order checkbox.
        """
        root = self.filters_root()
        cb = root.locator("app-checkbox[label='Descending']").first
        expect(cb).to_be_visible(timeout=5000)
        return cb

    def read_all_pages_from_table(self, table_locator, timeout: int = 12_000) -> list:
        """
        Read all rows from a paginated simple-table and return them as list of dicts.
        """
        expect(table_locator).to_be_visible(timeout=timeout)

        def pager_active_page_text() -> str:
            pager = self.page.locator("div.pagination ngb-pagination ul.pagination").first
            if pager.count() == 0:
                return ""
            active = pager.locator("li.page-item.active a.page-link").first
            if active.count() == 0:
                return ""
            return self._clean(active.inner_text())

        def first_row_fingerprint() -> str:
            first_row = table_locator.locator("tbody tr").first
            if first_row.count() == 0:
                return ""
            return self._clean(first_row.inner_text())

        all_rows = []
        seen = set()

        while True:
            # Read current page
            page_rows = self.read_table_as_dicts(table_locator)

            for row in page_rows:
                key = tuple((k, self._clean(str(v))) for k, v in row.items())
                if key not in seen:
                    seen.add(key)
                    all_rows.append(row)

            # No pager -> only one page
            pager = self.page.locator("div.pagination ngb-pagination ul.pagination").first
            if pager.count() == 0:
                break

            before_page = pager_active_page_text()
            before_fp = first_row_fingerprint()

            clicked = self.click_next(timeout=timeout)
            if not clicked:
                break

            # Wait for page to actually change
            self.wait_until(
                lambda: (
                    (pager_active_page_text() and pager_active_page_text() != before_page)
                    or (first_row_fingerprint() and first_row_fingerprint() != before_fp)
                ),
                timeout_ms=timeout,
                interval_ms=200,
            )

            # Ensure table is still visible after re-render
            expect(table_locator).to_be_visible(timeout=timeout)

        return all_rows
    
    def day_suffix(self, day: int) -> str:
        if 11 <= day <= 13:
            return "th"
        return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    def format_for_picker(self, dt: datetime) -> str:
        # Example: January 27th 2026, 11:14:39 am
        month = dt.strftime("%B")
        day = dt.day
        suffix = self.day_suffix(day)
        year = dt.year

        hour_12 = dt.strftime("%I").lstrip("0") or "12"
        minute = dt.strftime("%M")
        second = dt.strftime("%S")
        ampm = dt.strftime("%p").lower()

        return f"{month} {day}{suffix} {year}, {hour_12}:{minute}:{second} {ampm}"
    # =========================
    # Severity
    # =========================
    def get_severity(self):
        """
        Get the currently selected Severity filter value.
        """
        return self.dropdown_selected_text("Severity")

    def set_severity(self, severity: str):
        """
        Set the Severity filter to the given value.
        """
        self.dropdown_pick("Severity", severity)
        sleep(1)

    # =========================
    # Category
    # =========================
    def get_category(self):
        """
        Get the currently selected Category filter value.
        Returns the visible dropdown text.
        """
        return self.dropdown_selected_text("Category")

    def set_category(self, category: str):
        """
        Set the Category filter to the given value.
        """
        self.dropdown_pick("Category", category)
        sleep(1)

    # =========================
    # Filter By (general)
    # =========================
    def get_filter_by(self):
        """
        Return the currently selected 'Filter by' mode.
        Returns one of: 'Devices' / 'Domain/Chassis' / 'Device type'.
        """
        rb = self.filter_by_container()

        options = ["Devices", "Domain/Chassis", "Device type"]
        for opt in options:
            label = rb.locator(f"label:has-text('{opt}')").first
            if label.count() == 0:
                continue
            try:
                checked_svg = label.locator("svg.checked").first
                if checked_svg.count() > 0 and checked_svg.is_visible():
                    return opt
            except Exception:
                continue

        return ""  # unknown

    def set_filter_by(self, filter_by: str):
        """
        Select a 'Filter by' option by label text.
        """
        rb = self.filter_by_container()
        label = rb.locator(f"label:has-text('{filter_by}')").first
        if label.count() == 0:
            raise AssertionError(f"Filter by option '{filter_by}' not found.")
        label.click(force=True)

        # Best-effort wait that it becomes selected
        def selected():
            try:
                chk = label.locator("svg.checked").first
                return chk.count() > 0 and chk.is_visible()
            except Exception:
                return False

        try:
            self.wait_until(selected, timeout_ms=5000, interval_ms=200)
        except Exception:
            # Some DOMs don't render svg.checked; don't hard-fail
            pass

        sleep(1)

    # =========================
    # Filter By → Devices
    # =========================
    def devices_dropdown(self):
        """
        Return the app-dropdown for Devices.
        """
        root = self.filters_root()
        dropdown = root.locator("section.section-devices app-dropdown[label='Devices']").first
        if dropdown.count() == 0:
            raise AssertionError("Devices dropdown not found.")
        return dropdown

    def _try_open_devices_dropdown(self, timeout: int = 8000):
        """
        Best-effort open for Devices dropdown.
        Returns the menu locator if visible, otherwise returns None (no exception).
        """
        dropdown = self.devices_dropdown()
        btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
        expect(btn).to_be_visible(timeout=timeout)

        menu = dropdown.locator("div.dropdown-menu[data-label='Devices']").first

        # Try a few ways to open (some builds toggle weirdly)
        attempts = [
            lambda: btn.click(force=True),
            lambda: btn.click(force=True),  # sometimes first click focuses, second opens
            lambda: btn.press("Enter"),
            lambda: btn.press("Space"),
            lambda: btn.press("ArrowDown"),
        ]

        for act in attempts:
            try:
                act()
            except Exception:
                pass

            try:
                # poll visibility without hard failing
                self.wait_until(lambda: menu.is_visible(), timeout_ms=min(timeout, 1500), interval_ms=150)
                if menu.is_visible():
                    return menu
            except Exception:
                pass

        return None

    def open_devices_dropdown(self, timeout: int = 8000):
        """
        Open the Devices dropdown and return its menu locator.
        Raises AssertionError if it cannot be opened.
        """
        menu = self._try_open_devices_dropdown(timeout=timeout)
        if menu is None:
            raise AssertionError("Devices dropdown menu did not open (menu stayed hidden).")
        return menu

    def is_device_checked(self, device_li) -> bool:
        """
        Return True if the device checkbox is selected.
        """
        return device_li.locator("svg.unchecked").count() == 0

    def device_text(self, device_li) -> str:
        """
        Extract the device label text from the li (ignoring checkbox).
        """
        txt = self._clean(device_li.inner_text())
        return txt.split()[0] if txt else ""

    def set_all_devices_filterBy_devices(self, timeout: int = 10000):
        """
        Select all devices in the Devices filter by selecting each device row.
        Scrolls through the list and clicks any unchecked device until all are checked.
        """
        self.set_filter_by("Devices")
        menu = self.open_devices_dropdown(timeout=timeout)

        scroller = menu.locator("div.simplebar-content-wrapper").first
        expect(scroller).to_be_visible(timeout=timeout)

        def click_all_visible_unchecked() -> bool:
            """
            Click every unchecked device currently rendered (skip the 'All' row at index 0).
            Returns True if any click was performed.
            """
            clicked_any = False
            rows = menu.locator("li.dropdown-item.multiple")
            n = rows.count()
            for i in range(1, n):
                r = rows.nth(i)
                if not self.is_device_checked(r):
                    r.scroll_into_view_if_needed()
                    r.click(force=True)
                    clicked_any = True
            return clicked_any

        def any_unchecked_visible() -> bool:
            rows = menu.locator("li.dropdown-item.multiple")
            n = rows.count()
            for i in range(1, n):
                r = rows.nth(i)
                if not self.is_device_checked(r):
                    return True
            return False

        def scroll_to_top():
            scroller.evaluate("el => { el.scrollTop = 0; }")

        def scroll_page_down():
            scroller.evaluate("el => { el.scrollTop = el.scrollTop + el.clientHeight; }")

        def get_scroll_state():
            return (
                scroller.evaluate("el => el.scrollTop"),
                scroller.evaluate("el => el.scrollHeight"),
                scroller.evaluate("el => el.clientHeight"),
            )

        def all_selected_across_scroll() -> bool:
            """
            Two-pass strategy (handles virtualization):
            - Pass 1: scroll down, clicking any unchecked visible device rows.
            - Pass 2: scroll down again and verify none remain unchecked.
            """
            try:
                # -------- Pass 1: select everything we can see while scrolling down
                scroll_to_top()
                last_scroll_top = -1
                for _ in range(MAX_SCROLL_PAGES):
                    click_all_visible_unchecked()

                    scroll_top, scroll_h, client_h = get_scroll_state()
                    if scroll_top + client_h >= scroll_h - 2:
                        break

                    if scroll_top == last_scroll_top:
                        break
                    last_scroll_top = scroll_top

                    scroll_page_down()

                # -------- Pass 2: verify (no unchecked anywhere while scrolling)
                scroll_to_top()
                last_scroll_top = -1
                for _ in range(MAX_SCROLL_PAGES):
                    if any_unchecked_visible():
                        return False

                    scroll_top, scroll_h, client_h = get_scroll_state()
                    if scroll_top + client_h >= scroll_h - 2:
                        return not any_unchecked_visible()

                    if scroll_top == last_scroll_top:
                        return not any_unchecked_visible()
                    last_scroll_top = scroll_top

                    scroll_page_down()

                return True
            except Exception:
                return False

        self.wait_until(all_selected_across_scroll, timeout_ms=timeout, interval_ms=250)

    def get_all_selected_devices_filterBy_devices(self, timeout: int = 8000) -> list:
        """
        Return a list of selected devices in the Devices filter.
        Scrolls the list and collects checked device names.
        """
        self.set_filter_by("Devices")

        menu = self._try_open_devices_dropdown(timeout=timeout)
        if menu is None:
            print("Devices dropdown did not open (likely no selected devices). Returning [].")
            return []

        scroller = menu.locator("div.simplebar-content-wrapper").first
        # scroller might not exist if list is very small
        if scroller.count() == 0:
            scroller = menu

        def scroll_to_top():
            try:
                scroller.evaluate("el => { el.scrollTop = 0; }")
            except Exception:
                pass

        def scroll_page_down():
            try:
                scroller.evaluate("el => { el.scrollTop = el.scrollTop + el.clientHeight; }")
            except Exception:
                pass

        def get_scroll_state():
            try:
                return (
                    scroller.evaluate("el => el.scrollTop"),
                    scroller.evaluate("el => el.scrollHeight"),
                    scroller.evaluate("el => el.clientHeight"),
                )
            except Exception:
                return (0, 0, 0)

        seen = set()
        out = []

        scroll_to_top()
        last_scroll_top = -1

        for _ in range(MAX_SCROLL_PAGES):
            rows = menu.locator("li.dropdown-item.multiple")
            n = rows.count()

            for i in range(1, n):  # skip "All"
                r = rows.nth(i)
                if self.is_device_checked(r):
                    name = self.device_text(r)
                    if name and name not in seen:
                        seen.add(name)
                        out.append(name)

            scroll_top, scroll_h, client_h = get_scroll_state()
            if scroll_h == 0 or client_h == 0:
                break
            if scroll_top + client_h >= scroll_h - 2:
                break
            if scroll_top == last_scroll_top:
                break

            last_scroll_top = scroll_top
            scroll_page_down()

        if not out:
            print("No devices are selected in Devices filter.")
        return out

    def select_device_filterBy_devices(self, device_name: str, timeout: int = 10000):
        """
        Select a specific device in the Devices filter.
        Scrolls until the device is found, then selects it if not already selected.
        """
        self.set_filter_by("Devices")
        menu = self.open_devices_dropdown(timeout=timeout)

        scroller = menu.locator("div.simplebar-content-wrapper").first
        expect(scroller).to_be_visible(timeout=timeout)

        def scroll_to_top():
            scroller.evaluate("el => { el.scrollTop = 0; }")

        def scroll_page_down():
            scroller.evaluate("el => { el.scrollTop = el.scrollTop + el.clientHeight; }")

        def get_scroll_state():
            return (
                scroller.evaluate("el => el.scrollTop"),
                scroller.evaluate("el => el.scrollHeight"),
                scroller.evaluate("el => el.clientHeight"),
            )

        scroll_to_top()
        last_scroll_top = -1
        for _ in range(MAX_SCROLL_PAGES):
            row = menu.locator("li.dropdown-item.multiple", has_text=re.compile(rf"^\s*{re.escape(device_name)}\s*$")).first

            if row.count() > 0:
                row.scroll_into_view_if_needed()
                if not self.is_device_checked(row):
                    row.click(force=True)
                    self.wait_until(lambda: self.is_device_checked(row), timeout_ms=timeout, interval_ms=200)
                return

            scroll_top, scroll_h, client_h = get_scroll_state()
            if scroll_top + client_h >= scroll_h - 2:
                break
            if scroll_top == last_scroll_top:
                break
            last_scroll_top = scroll_top
            scroll_page_down()

        raise AssertionError(f"Device '{device_name}' not found in Devices dropdown (even after scrolling).")

    def remove_device_filterBy_devices(self, device_name: str, timeout: int = 10000):
        """
        Unselect a specific device in the Devices filter.
        Scrolls until the device is found, then unselects it if selected.
        """
        self.set_filter_by("Devices")
        menu = self.open_devices_dropdown(timeout=timeout)

        scroller = menu.locator("div.simplebar-content-wrapper").first
        expect(scroller).to_be_visible(timeout=timeout)

        def scroll_to_top():
            scroller.evaluate("el => { el.scrollTop = 0; }")

        def scroll_page_down():
            scroller.evaluate("el => { el.scrollTop = el.scrollTop + el.clientHeight; }")

        def get_scroll_state():
            return (
                scroller.evaluate("el => el.scrollTop"),
                scroller.evaluate("el => el.scrollHeight"),
                scroller.evaluate("el => el.clientHeight"),
            )

        scroll_to_top()
        last_scroll_top = -1
        for _ in range(MAX_SCROLL_PAGES):
            row = menu.locator("li.dropdown-item.multiple", has_text=re.compile(rf"^\s*{re.escape(device_name)}\s*$")).first

            if row.count() > 0:
                row.scroll_into_view_if_needed()
                if self.is_device_checked(row):
                    row.click(force=True)
                    self.wait_until(lambda: not self.is_device_checked(row), timeout_ms=timeout, interval_ms=200)
                return

            scroll_top, scroll_h, client_h = get_scroll_state()
            if scroll_top + client_h >= scroll_h - 2:
                break
            if scroll_top == last_scroll_top:
                break
            last_scroll_top = scroll_top
            scroll_page_down()

        raise AssertionError(f"Device '{device_name}' not found in Devices dropdown (even after scrolling).")

    def remove_all_devices_filterBy_devices(self, timeout: int = 10000):
        """
        Unselect all devices by clicking the 'All' control (it clears all selections in this UI).
        """
        self.set_filter_by("Devices")
        menu = self.open_devices_dropdown(timeout=timeout)

        all_row = menu.locator("li.dropdown-item.multiple", has_text=re.compile(r"^\s*All\s*$")).first
        expect(all_row).to_be_visible(timeout=timeout)
        all_row.click(force=True)

        # Best-effort verify: no checked devices remain in the visible viewport
        def none_checked_visible():
            rows = menu.locator("li.dropdown-item.multiple")
            n = rows.count()
            for i in range(1, n):
                if self.is_device_checked(rows.nth(i)):
                    return False
            return True

        try:
            self.wait_until(none_checked_visible, timeout_ms=timeout, interval_ms=250)
        except Exception:
            pass

    # =========================
    # Filter By → Domain / Chassis
    # =========================
    def click_on_inventory_tree_icon(self, timeout: int = 5000):
        """
        Click the inventory-tree icon next to the Domain field to open the Domain/Chassis picker modal.
        """
        root = self.filters_root()

        # Inventory tree icon lives inside the Domain section
        icon = root.locator("section.section-domain app-icon[name='inventory-tree']").first
        expect(icon).to_be_visible(timeout=timeout)
        icon.click(force=True)

        # Assert the picker modal opens
        modal = self.page.locator("div.modal-dialog:has-text('Select group to filter')").first
        expect(modal).to_be_visible(timeout=timeout)
        return modal

    def get_selected_domain_or_chassis_filterBy_domain_or_chassis(self) -> str:
        """
        Return the currently selected Domain/Chassis value.
        """
        root = self.filters_root()
        domain_section = root.locator("section.section-domain").first
        if domain_section.count() == 0:
            return ""

        # Input is disabled per HTML, so value may be empty
        inp = domain_section.locator("app-input[label='Domain'] input").first
        if inp.count() > 0:
            try:
                v = self._clean(inp.input_value())
                if v:
                    return v
            except Exception:
                pass

            try:
                v = self._clean(inp.get_attribute("value") or "")
                if v:
                    return v
            except Exception:
                pass

        # Fallback: read the visible text for the whole Domain control
        try:
            return self._clean(domain_section.locator("app-input[label='Domain']").inner_text())
        except Exception:
            return ""

    def reset_domain_or_chassis_filterBy_domain_or_chassis(self, timeout: int = 8000):
        """
        Reset the Domain/Chassis filter using the picker modal (click icon -> Reset -> Ok).
        """
        self.set_filter_by("Domain/Chassis")

        root = self.filters_root()
        domain_section = root.locator("section.section-domain").first
        if domain_section.count() == 0:
            raise AssertionError("Domain section not found.")

        modal = self.click_on_inventory_tree_icon(timeout=timeout)

        reset_btn = modal.locator("footer button:has-text('Reset')").first
        expect(reset_btn).to_be_visible(timeout=timeout)
        reset_btn.click(force=True)

        ok_btn = modal.locator("footer button:has-text('Ok')").first
        expect(ok_btn).to_be_visible(timeout=timeout)
        ok_btn.click(force=True)

        expect(modal).to_be_hidden(timeout=timeout)

        # Optional: wait until something is reflected in the UI 
        def updated():
            return self.get_selected_domain_or_chassis_filterBy_domain_or_chassis().strip() != ""

        try:
            self.wait_until(updated, timeout_ms=timeout, interval_ms=200)
        except Exception:
            pass

    def select_domain_or_chassis_filterBy_domain_or_chassis(self, value: str, timeout: int = 10000):
        """
        Select a Domain/Chassis group from the inventory-tree modal and confirm with Ok.
        """
        self.set_filter_by("Domain/Chassis")

        root = self.filters_root()
        domain_section = root.locator("section.section-domain").first
        if domain_section.count() == 0:
            raise AssertionError("Domain section not found.")

        modal = self.click_on_inventory_tree_icon(timeout=timeout)

        node = modal.locator("app-inventory-tree span", has_text=re.compile(rf"^\s*{re.escape(value)}\s*$")).first

        if node.count() == 0:
            labels = modal.locator("app-inventory-tree span").all_inner_texts()
            labels = [self._clean(x) for x in labels if self._clean(x)]
            raise AssertionError(f"Domain/Chassis '{value}' not found in inventory tree. Visible: {labels}")

        node.scroll_into_view_if_needed()
        node.click(force=True)

        ok_btn = modal.locator("footer button:has-text('Ok')").first
        expect(ok_btn).to_be_visible(timeout=timeout)
        ok_btn.click(force=True)

        expect(modal).to_be_hidden(timeout=timeout)

        def updated():
            sleep(2)
            v = self.get_selected_domain_or_chassis_filterBy_domain_or_chassis()
            return v.strip() != "" and value.strip().lower() in v.strip().lower()

        try:
            self.wait_until(updated, timeout_ms=timeout, interval_ms=200)
        except Exception:
            # Some builds may not echo the selection into the disabled field text.
            pass

    # =========================
    # Filter By → Device Type
    # =========================
    def set_all_devices_filterBy_device_type(self):
        """
        Select 'All' in the Device Type filter.
        """
        pass

    def get_all_selected_devices_filterBy_device_type(self):
        """
        Return a list with the selected device type.
        Returns [] if 'All' is selected.
        """
        pass

    def select_device_type_filterBy_device_type(self, device_type: str):
        """
        Select a specific device type in the filter.
        """
        pass

    def remove_device_type_filterBy_device_type(self, device_type: str):
        """
        Remove a selected device type by resetting to 'All'.
        """
        pass

    def remove_all_devices_filterBy_device_type(self):
        """
        Reset Device Type filter to 'All'.
        """
        pass

    # =========================
    # Date
    # =========================
    def get_date(self):
        """
        Return the currently selected date range string.
        """
        inp = self.date_input_field()
        try:
            return self._clean(inp.input_value())
        except Exception:
            return self._clean(inp.get_attribute("value") or "")

    def set_date(self, from_date_and_time: str, to_date_and_time: str, timeout: int = 10000):
        """
        Set date range using easy inputs like 'YEAR-MONTH-DAY HOUR:MINUTES' or 'YEAR-MONTH-DAY HOUR:MINUTES:SECONDS'
        Example: '2026-01-27 11:14' or '2026-01-27 11:14:39'.
        """
        # Allow 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD HH:MM:SS'
        def parse(s: str) -> datetime:
            s = s.strip()
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    pass
            raise ValueError(f"Unsupported datetime format: '{s}'. Use 'YYYY-MM-DD HH:MM[:SS]'")

        from_dt = parse(from_date_and_time)
        to_dt = parse(to_date_and_time)

        target = f"{self.format_for_picker(from_dt)} - {self.format_for_picker(to_dt)}"

        inp = self.date_input_field()
        expect(inp).to_be_visible(timeout=timeout)
        inp.click(force=True)
        inp.fill("")
        inp.type(target, delay=5)
        inp.press("Enter")

        # close picker if open 
        picker = self.page.locator("bs-daterangepicker-container[role='dialog']").first
        if picker.count() > 0:
            try:
                if picker.is_visible():
                    self.page.keyboard.press("Escape")
            except Exception:
                pass

        sleep(2)
        self.wait_until(lambda: (self.get_date() or "").strip() != "", timeout_ms=timeout, interval_ms=200)

    # =========================
    # Message
    # =========================
    def set_message(self, message: str):
        """
        Set the Message filter text.
        Overwrites any existing value in the input field.
        """
        inp = self.message_input_field()
        inp.fill(message)

        sleep(1)

    # =========================
    # Ordering / Sorting
    # =========================
    def get_order_by(self):
        """
        Return the currently selected Order By value.
        """
        return self.dropdown_selected_text("Order by")

    def set_order_by(self, column_name: str):
        """
        Set the Order By dropdown to a specific column.
        """
        self.dropdown_pick("Order by", column_name)
        sleep(1)

    def set_order_by_all(self):
        """
        Set the Order By dropdown to 'All'.
        """
        self.dropdown_pick("Order by", "All")
        sleep(1)

    def enable_descending_order(self):
        """
        Enable descending sort order if it is not already enabled.
        """
        cb = self.descending_checkbox()
        label = cb.locator("label.checkbox-container").first
        expect(label).to_be_visible(timeout=5000)

        def is_checked():
            cls = (label.get_attribute("class") or "")
            return "checked" in cls.split()

        if is_checked():
            return

        label.click(force=True)
        self.wait_until(is_checked, timeout_ms=5000, interval_ms=200)

    def disable_descending_order(self):
        """
        Disable descending sort order if it is currently enabled.
        """
        cb = self.descending_checkbox()
        label = cb.locator("label.checkbox-container").first
        expect(label).to_be_visible(timeout=5000)

        def is_checked():
            cls = (label.get_attribute("class") or "")
            return "checked" in cls.split()

        if not is_checked():
            return

        label.click(force=True)
        self.wait_until(lambda: not is_checked(), timeout_ms=5000, interval_ms=200)

    # =========================
    # Pagination
    # =========================
    def click_previous(self, timeout: int = 5000) -> bool:
        """
        Click the Previous page button.
        Returns True if clicked, False if disabled/not clickable.
        """
        pager = self.page.locator("div.pagination ngb-pagination ul.pagination").first
        expect(pager).to_be_visible(timeout=timeout)

        prev_li = pager.locator("li.page-item:has(a[aria-label='Previous'])").first
        expect(prev_li).to_be_visible(timeout=timeout)

        cls = (prev_li.get_attribute("class") or "")
        if "disabled" in cls.split():
            return False

        prev_a = prev_li.locator("a[aria-label='Previous']").first
        expect(prev_a).to_be_visible(timeout=timeout)
        prev_a.click(force=True)
        return True

    def click_next(self, timeout: int = 5000) -> bool:
        """
        Click the Next page button.
        Returns True if clicked, False if disabled/not clickable.
        """
        pager = self.page.locator("div.pagination ngb-pagination ul.pagination").first
        expect(pager).to_be_visible(timeout=timeout)

        next_li = pager.locator("li.page-item:has(a[aria-label='Next'])").first
        expect(next_li).to_be_visible(timeout=timeout)

        cls = (next_li.get_attribute("class") or "")
        if "disabled" in cls.split():
            return False

        next_a = next_li.locator("a[aria-label='Next']").first
        expect(next_a).to_be_visible(timeout=timeout)
        next_a.click(force=True)
        return True

    # =========================
    # Events / Alarms Panel
    # =========================
    def events_tabset(self):
        """Return the Events/Alarms tabset container."""
        tabset = self.page.locator("tabset.tab-container").first
        if tabset.count() == 0:
            raise AssertionError("Events/Alarms tabset not found (tabset.tab-container).")
        return tabset

    def click_events_tab(self, tab_name: str, timeout: int = 12000):
        """Click a tab by its name (Events history / Alarms / Alarms summary)."""
        tabset = self.events_tabset()

        tab_btn = tabset.locator(
            "ul.nav.nav-tabs a.nav-link",
            has_text=re.compile(rf"^\s*{re.escape(tab_name)}\s*$")
        ).first

        expect(tab_btn).to_be_visible(timeout=timeout)
        tab_btn.click(force=True)

        # Wait until tab is marked active
        expect(tab_btn).to_have_class(re.compile(r"\bactive\b"), timeout=timeout)

    def active_tab_table(self, timeout: int = 12000):
        """
        Return the simple-table <table> inside the ACTIVE tab-pane.

        IMPORTANT: active pane is <tab class="active tab-pane"> (same element),
        so selector is: tab.active.tab-pane  (NOT 'tab.active tab-pane').
        """
        tabset = self.events_tabset()
        table = tabset.locator("div.tab-content tab.active.tab-pane app-simple-table table").first
        expect(table).to_be_visible(timeout=timeout)
        return table

    def extract_headers(self, table) -> list:
        """
        Extract table headers robustly.
        Tries 'th .name' first, then falls back to 'th' inner text.
        """
        headers = [self._clean(x) for x in table.locator("thead th .name").all_inner_texts()]
        headers = [h for h in headers if h]

        if not headers:
            headers = [self._clean(x) for x in table.locator("thead th").all_inner_texts()]
            headers = [h for h in headers if h]

        return headers

    def read_table_as_dicts(self, table) -> list:
        """Read an HTML table into a list[dict] using header names as keys."""
        headers = self.extract_headers(table)

        rows = table.locator("tbody tr")
        out = []

        # If there are no <tr>, return [] (OK)
        for i in range(rows.count()):
            r = rows.nth(i)

            # td texts
            cells = [self._clean(x) for x in r.locator("td").all_inner_texts()]

            # map only up to headers length (ignore action/expand columns)
            row_dict = {}
            for c_idx, h in enumerate(headers):
                row_dict[h] = cells[c_idx] if c_idx < len(cells) else ""
            out.append(row_dict)

        return out
    
    def click_on_events_history(self, timeout: int = 12000):
        """
        Switch to 'Events history' tab in Events/Alarms panel.
        Ensures the panel is open before clicking.
        """
        # Ensure panel is open
        try:
            self.events_tabset()
        except Exception:
            self.open_events_alarms(timeout=timeout)

        self.click_events_tab("Events history", timeout=timeout)

        try:
            self.active_tab_table(timeout=timeout)
        except Exception:
            # Some builds may render empty/no table – don't hard fail here
            pass

    def click_on_alarms(self, timeout: int = 12000):
        """
        Switch to 'Alarms' tab in Events/Alarms panel.
        """
        # Ensure panel is open
        try:
            self.events_tabset()
        except Exception:
            self.open_events_alarms(timeout=timeout)

        self.click_events_tab("Alarms", timeout=timeout)

    def click_on_alarms_summary(self, timeout: int = 12000):
        """
        Switch to 'Alarms summary' tab in Events/Alarms panel.
        """
        # Ensure panel is open
        try:
            self.events_tabset()
        except Exception:
            self.open_events_alarms(timeout=timeout)

        self.click_events_tab("Alarms summary", timeout=timeout)

    def open_events_alarms(self, timeout: int = 12000):
        """
        Open the Events/Alarms inside panel.
        Clicks the corresponding action button and waits for the tabset to appear.
        """
        btn = self.page.locator("button:has-text('Events/Alarms')").first
        expect(btn).to_be_visible(timeout=timeout)
        btn.click(force=True)
        expect(self.page.locator("tabset.tab-container").first).to_be_visible(timeout=timeout)

    def get_all_events_history(self, timeout: int = 12_000) -> list:
        """
        Return all Events history records across all pagination pages.
        """
        try:
            self.events_tabset()
        except Exception:
            self.open_events_alarms(timeout=timeout)

        self.click_on_events_history(timeout=timeout)
        table = self.active_tab_table(timeout=timeout)  
        return self.read_all_pages_from_table(table, timeout=timeout)
    
    def get_all_alarms(self, timeout: int = 12_000) -> list:
        """
        Return all Alarms records across all pagination pages.
        """
        try:
            self.events_tabset()
        except Exception:
            self.open_events_alarms(timeout=timeout)

        self.click_on_alarms(timeout=timeout)
        table = self.page.locator("section.faults-enabled app-simple-table table").first  
        return self.read_all_pages_from_table(table, timeout=timeout)

    def get_alarms_summary(self, timeout: int = 12_000) -> list:
        """
        Read ALL 'Alarms summary' rows across pagination pages.
        Returns list[dict] where keys are headers.
        """
        # Ensure panel is open
        try:
            self.events_tabset()
        except Exception:
            self.open_events_alarms(timeout=timeout)

        # Switch to Alarms summary tab
        self.click_on_alarms_summary(timeout=timeout)

        table = self.page.locator("section.faults-enabled app-simple-table table").first
        return self.read_all_pages_from_table(table, timeout=timeout)
        
    def close_events_alarms(self, timeout: int = 5000):
        """
        Close (hide) the Events/Alarms panel if it's currently open.
        """
        tabset = self.page.locator("tabset.tab-container").first

        # If already closed -> nothing to do
        if tabset.count() == 0:
            return

        try:
            # If exists but not visible -> treat as closed
            if not tabset.is_visible():
                return
        except Exception:
            return

        # Click the same toggle button used to open it
        btn = self.page.locator("div.service-actionWrapper-footer button:has(app-icon[name='alarm-events'])").first

        if btn.count() == 0:
            # fallback by text (if icon selector changes)
            btn = self.page.locator("div.service-actionWrapper-footer button:has-text('Events/Alarms')").first

        expect(btn).to_be_visible(timeout=timeout)
        btn.click(force=True)

        try:
            # Wait until the panel is gone/hidden
            expect(tabset).to_be_hidden(timeout=timeout)
        except TimeoutError:
            self.wait_until(lambda: tabset.count() == 0, timeout_ms=timeout, interval_ms=200)

    # =========================
    # Column Editing
    # =========================
    def click_edit_columns(self):
        """
        Clicks the Edit Columns button.
        """
        btn = self.page.locator("button:has-text('Edit columns')").first
        expect(btn).to_be_visible(timeout=5000)
        btn.click()

    def click_save_changes(self, timeout: int = 5000):
        """
        Click 'Save changes' in the Edit Columns footer.
        """
        footer = self.page.locator("div.service-actionWrapper-footer").first
        expect(footer).to_be_visible(timeout=timeout)

        btn = footer.locator("button:has-text('Save changes')").first
        expect(btn).to_be_visible(timeout=timeout)
        btn.click(force=True)

        # Wait until edit mode exits (buttons disappear or footer changes)
        self.wait_until(lambda: footer.locator("button:has-text('Save changes')").count() == 0, timeout_ms=timeout, interval_ms=200)

    def click_revert_changes(self, timeout: int = 5000):
        """
        Click 'Revert changes' in the Edit Columns footer.
        """
        footer = self.page.locator("div.service-actionWrapper-footer").first
        expect(footer).to_be_visible(timeout=timeout)

        btn = footer.locator("button:has-text('Revert changes')").first
        expect(btn).to_be_visible(timeout=timeout)
        btn.click(force=True)

        # Wait until edit mode exits
        self.wait_until(lambda: footer.locator("button:has-text('Revert changes')").count() == 0, timeout_ms=timeout, interval_ms=200)