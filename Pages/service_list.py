'''
Created by: Yuval Dahan
Date: 21/01/2026
'''

from playwright.sync_api import Page, expect
from typing import Callable
import time
import re
from time import sleep
from datetime import datetime
from pathlib import Path
from Pages.alarms_and_events import AlarmsAndEvents
from Pages.performance import Performance
from Utils.utils import create_frame_html


MAX_SCROLL_PAGES = 200
SLEEP = 0.2


class ServiceList:
    """
    Service List page – handles filters, ordering, navigation,
    and table-level operations for Events / Alarms.
    """

    def __init__(self, page: Page):
        self.page = page
        self.alarms_and_events = AlarmsAndEvents(page)
        self.performance = Performance(page)

    # ==========================================================
    # Internal small helpers 
    # ==========================================================

    # ✅
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

    # ✅
    @staticmethod
    def _clean(s: str) -> str:
        """
        Normalize whitespace in a string and strip leading/trailing spaces.
        """
        return re.sub(r"\s+", " ", (s or "").strip())

    # ✅
    def filters_root_old(self):
        """
        Return the root locator for the Service List filters section.
        Used as a base for locating filter controls.
        """
        return self.page.locator(".service-filters").first

    # ✅
    def filters_root(self):
        root = self.page.locator(
            ".service-filters, "
            ".service-filtersHost, "
            ".faults-actionWrapper-filters, "
            ".faults-filters"
        ).first
        expect(root).to_be_visible(timeout=5000)
        return root

    # ✅
    def dropdown(self, label: str):
        """
        Locate a dropdown component by its label text.
        """
        root = self.filters_root()
        dropdown = root.locator(f"app-dropdown[label='{label}']").first
        expect(dropdown).to_be_visible(timeout=5000)
        return dropdown

    # ✅
    def dropdown_selected_text(self, label: str) -> str:
        """
        Return the currently selected value of a labeled dropdown.
        """
        dropdown = self.dropdown(label)
        selected = dropdown.locator(".selected-view span").first
        expect(selected).to_be_visible(timeout=5000)
        return self._clean(selected.inner_text())

    # ✅
    def open_dropdown(self, label: str):
        """
        Open a labeled dropdown by clicking its toggle button.
        """
        dropdown = self.dropdown(label)
        btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
        expect(btn).to_be_visible(timeout=5000)
        btn.click(force=True)

    # ✅
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

    # ✅
    def filter_by_container(self):
        """
        Return the 'Filter by' container.
        """
        root = self.filters_root()
        radio_btn = root.locator("app-radio-button[label='Filter by']").first
        expect(radio_btn).to_be_visible(timeout=5000)
        return radio_btn

    # ✅
    def date_input_field(self):
        """
        Return the date range input field.
        """
        root = self.filters_root()
        date_inp = root.locator("input[formcontrolname='dateRange']").first
        expect(date_inp).to_be_visible(timeout=5000)
        return date_inp

    # ✅
    def message_input_field(self):
        """
        Return the Message filter input field.
        """
        root = self.filters_root()
        inp = root.locator("app-input[label='Message'] input[type='text']").first
        expect(inp).to_be_visible(timeout=5000)
        return inp

    # ✅
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
    
    # ✅
    def day_suffix(self, day: int) -> str:
        if 11 <= day <= 13:
            return "th"
        return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    # ✅
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
    # Service Name
    # =========================

    # ✅
    def set_service_name(self, service_name: str, timeout: int = 8000):
        """
        Set the Service Name filter.
        """

        try:
            service_name = (service_name or "").strip()

            root = self.filters_root()
            inp = root.locator("app-input[label='Service Name'] input[type='text']").first
            sleep(SLEEP)

            expect(inp).to_be_visible(timeout=timeout)
            expect(inp).to_be_enabled(timeout=timeout)

            current_value = (inp.input_value() or "").strip()

            if current_value == service_name:
                return True

            inp.click(force=True)
            inp.fill(service_name)

            self.wait_until(lambda: (inp.input_value() or "").strip() == service_name, timeout_ms=timeout, interval_ms=150)

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"set_service_name('{service_name}') failed. Problem: {e}")

    # =========================
    # Service Layer
    # =========================

    # ✅
    def select_service_layer(self, service_layer: str, timeout: int = 8000):
        """
        Select one Service Layer from the multi-select dropdown.

        Examples: "ROADM", "OTN", "CS".
        """

        try:
            service_layer = (service_layer or "").strip()
            if not service_layer:
                raise ValueError("service_layer is empty")

            dropdown = self.dropdown("Service Layer")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
            sleep(SLEEP)
            expect(btn).to_be_visible(timeout=timeout)
            btn.click(force=True)

            menu = dropdown.locator("div.dropdown-menu[data-label='Service Layer']").first
            sleep(SLEEP)
            expect(menu).to_be_visible(timeout=timeout)

            item = menu.locator("li.dropdown-item", has_text=re.compile(rf"^\s*{re.escape(service_layer)}\s*$", re.IGNORECASE)).first
            sleep(SLEEP)

            if item.count() == 0:
                options = [
                    self._clean(x)
                    for x in menu.locator("li.dropdown-item").all_inner_texts()
                    if self._clean(x)
                ]
                sleep(SLEEP)

                raise AssertionError(
                    f"Service Layer '{service_layer}' not found. Available: {options}"
                )

            item.scroll_into_view_if_needed()

            # If already selected, do not click again.
            checkbox = item.locator("app-checkbox").first
            sleep(SLEEP)

            if checkbox.count() > 0:
                checked = checkbox.locator("svg.checked").first
                sleep(SLEEP)
                if checked.count() > 0 and checked.is_visible():
                    return True

            item.click(force=True)

            if service_layer != "All":
                self.wait_until(lambda: item.locator("app-checkbox svg.checked").count() > 0, timeout_ms=timeout, interval_ms=150)

            self.close_service_layer_dropdown()

            return True

        except Exception as e:
            raise AssertionError(f"select_service_layer('{service_layer}') failed. Problem: {e}")

    # ✅
    def set_all_service_layers(self, timeout: int = 8000):
        """
        Select all real Service Layer options.
        """

        try:
            dropdown = self.dropdown("Service Layer")
            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
            sleep(SLEEP)

            expect(btn).to_be_visible(timeout=timeout)
            btn.click(force=True)

            menu = dropdown.locator("div.dropdown-menu[data-label='Service Layer']").first
            sleep(SLEEP)
            expect(menu).to_be_visible(timeout=timeout)

            rows = menu.locator("li.dropdown-item.multiple")
            sleep(SLEEP)
            expect(rows.first).to_be_visible(timeout=timeout)

            def is_checked(row) -> bool:
                locator = row.locator("svg.unchecked")
                sleep(SLEEP)
                return locator.count() == 0

            def all_real_layers_selected() -> bool:
                count = rows.count()

                # Start from 1 to skip "All"
                for i in range(1, count):
                    row = rows.nth(i)

                    if not is_checked(row):
                        row.scroll_into_view_if_needed()
                        row.click(force=True)
                        sleep(SLEEP)

                # Verify again
                for i in range(1, count):
                    row = rows.nth(i)

                    if not is_checked(row):
                        return False

                return True

            self.wait_until(all_real_layers_selected, timeout_ms=timeout, interval_ms=200)
            sleep(SLEEP)
            self.close_service_layer_dropdown()

            return True

        except Exception as e:
            raise AssertionError(f"set_all_service_layers failed. Problem: {e}")

    # ✅
    def get_all_selected_service_layers(self, timeout: int = 8000) -> list[str]:
        """
        Return all selected Service Layer values.
        """

        try:
            dropdown = self.dropdown("Service Layer")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
            sleep(SLEEP)
            expect(btn).to_be_visible(timeout=timeout)

            # 1) First try to read selected chips from the closed dropdown button
            chip_texts = [
                self._clean(t)
                for t in btn.locator("div.selected-view.multiple span").all_inner_texts()
            ]
            sleep(SLEEP)

            has_plus = any(re.fullmatch(r"\+\s*\d+", t) for t in chip_texts)

            if chip_texts and not has_plus:
                out = []
                seen = set()

                for text in chip_texts:
                    if not text or text.lower() == "all":
                        continue

                    if text not in seen:
                        seen.add(text)
                        out.append(text)

                return out

            # 2) If chips are compressed / not available, scan the dropdown menu
            menu = dropdown.locator("div.dropdown-menu[data-label='Service Layer']").first
            sleep(SLEEP)

            if menu.count() == 0 or not menu.is_visible():
                btn.click(force=True)
                self.wait_until(lambda: menu.count() > 0 and menu.is_visible(), timeout_ms=timeout, interval_ms=150)

            expect(menu).to_be_visible(timeout=timeout)

            rows = menu.locator("li.dropdown-item.multiple")
            sleep(SLEEP)

            selected_layers = []
            seen = set()

            for i in range(rows.count()):
                row = rows.nth(i)
                text = self._clean(row.inner_text())

                if not text or text.lower() == "all":
                    continue

                # Selected rows do NOT have svg.unchecked
                is_selected = row.locator("svg.unchecked").count() == 0
                sleep(SLEEP)

                if is_selected and text not in seen:
                    seen.add(text)
                    selected_layers.append(text)

            sleep(SLEEP)
            self.close_service_layer_dropdown()

            return selected_layers

        except Exception as e:
            raise AssertionError(f"get_all_selected_service_layers failed. Problem: {e}")

    # ✅
    def close_service_layer_dropdown(self, timeout: int = 5000):
        """
        Close the Service Layer dropdown if it is open.
        """

        try:
            dropdown = self.dropdown("Service Layer")

            if dropdown.count() == 0:
                return

            container = dropdown.locator("div.dropdown-container").first
            sleep(SLEEP)

            menu = dropdown.locator("div.dropdown-menu[data-label='Service Layer']").first
            sleep(SLEEP)

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
            sleep(SLEEP)

            def is_open() -> bool:
                try:
                    container_cls = container.get_attribute("class") or ""
                    menu_cls = menu.get_attribute("class") or ""

                    return (
                        ("open" in container_cls and "show" in container_cls)
                        or ("show" in menu_cls)
                    )

                except Exception:
                    return False

            # Already closed
            if not is_open():
                return

            expect(btn).to_be_visible(timeout=timeout)

            btn.scroll_into_view_if_needed()
            sleep(SLEEP)

            # Click dropdown button to close
            btn.click(force=True)

            self.wait_until(lambda: not is_open(), timeout_ms=timeout, interval_ms=150)

        except Exception as e:
            raise AssertionError(f"close_service_layer_dropdown failed. Problem: {e}")

    # ✅
    def remove_service_layer(self, service_layer: str, timeout: int = 8000):
        """
        Unselect one Service Layer from the multi-select dropdown.
        """

        try:
            service_layer = (service_layer or "").strip()
            if not service_layer:
                raise ValueError("service_layer is empty")

            dropdown = self.dropdown("Service Layer")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
            sleep(SLEEP)
            expect(btn).to_be_visible(timeout=timeout)

            menu = dropdown.locator("div.dropdown-menu[data-label='Service Layer']").first
            sleep(SLEEP)

            if menu.count() == 0 or not menu.is_visible():
                btn.click(force=True)
                self.wait_until(
                    lambda: menu.count() > 0 and menu.is_visible(),
                    timeout_ms=timeout,
                    interval_ms=150
                )

            expect(menu).to_be_visible(timeout=timeout)

            row = menu.locator("li.dropdown-item.multiple", has_text=re.compile(rf"^\s*{re.escape(service_layer)}\s*$", re.IGNORECASE)).first
            sleep(SLEEP)

            if row.count() == 0:
                options = [
                    self._clean(x)
                    for x in menu.locator("li.dropdown-item.multiple").all_inner_texts()
                    if self._clean(x)
                ]
                
                sleep(SLEEP)
                raise AssertionError(
                    f"Service Layer '{service_layer}' not found. Available: {options}"
                )

            row.scroll_into_view_if_needed()

            def is_checked() -> bool:
                locator = row.locator("svg.unchecked")
                sleep(SLEEP)
                return locator.count() == 0

            # Already unselected
            if not is_checked():
                return True

            row.click(force=True)

            self.wait_until(lambda: not is_checked(), timeout_ms=timeout, interval_ms=150)
            sleep(SLEEP)
            self.close_service_layer_dropdown()

            return True

        except Exception as e:
            raise AssertionError(f"remove_service_layer('{service_layer}') failed. Problem: {e}")

    # ✅
    def remove_all_service_layers(self, timeout: int = 8000):
        """
        Clear all selected Service Layer values by clicking 'All'.
        """

        try:
            dropdown = self.dropdown("Service Layer")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
            sleep(SLEEP)

            expect(btn).to_be_visible(timeout=timeout)

            menu = dropdown.locator("div.dropdown-menu[data-label='Service Layer']").first
            sleep(SLEEP)

            # Open only if needed
            if menu.count() == 0 or not menu.is_visible():
                btn.click(force=True)

                self.wait_until(
                    lambda: menu.count() > 0 and menu.is_visible(),
                    timeout_ms=timeout,
                    interval_ms=150
                )

            expect(menu).to_be_visible(timeout=timeout)

            all_row = menu.locator("li.dropdown-item.multiple", has_text=re.compile(r"^\s*All\s*$", re.IGNORECASE)).first
            sleep(SLEEP)

            expect(all_row).to_be_visible(timeout=timeout)

            # If nothing selected already -> done
            checked_rows = menu.locator("li.dropdown-item.multiple:not(:has(svg.unchecked))")
            sleep(SLEEP)

            # subtract "All"
            checked_count = max(0, checked_rows.count() - 1)

            if checked_count == 0:
                return True

            all_row.scroll_into_view_if_needed()
            all_row.click(force=True)

            # Wait until all real layers become unchecked
            self.wait_until(
                lambda: (
                    menu.locator(
                        "li.dropdown-item.multiple:not(:has(svg.unchecked))"
                    ).count() <= 1  # only "All" may remain checked
                ),
                timeout_ms=timeout,
                interval_ms=200
            )

            sleep(SLEEP)
            self.close_service_layer_dropdown()

            return True

        except Exception as e:
            raise AssertionError(f"remove_all_service_layers failed. Problem: {e}")
    
    # =========================
    # Service Type
    # =========================

    # ✅
    def select_service_type(self, service_type: str, timeout: int = 8000):
        """
        Select one Service Type from the multi-select dropdown.

        Examples:
            select_service_type("100GHZ")
            select_service_type("50GHZ")
            select_service_type("75GHZ")
        """

        try:
            service_type = (service_type or "").strip()
            if not service_type:
                raise ValueError("service_type is empty")

            dropdown = self.dropdown("Service Type")

            btn = dropdown.locator(
                "button.dropdown-button, button[dropdowntoggle]"
            ).first

            sleep(SLEEP)
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)

            menu = dropdown.locator(
                "div.dropdown-menu[data-label='Service Type']"
            ).first

            if menu.count() == 0 or not menu.is_visible():
                btn.click(force=True)

                self.wait_until(
                    lambda: menu.count() > 0 and menu.is_visible(),
                    timeout_ms=timeout,
                    interval_ms=150
                )

            expect(menu).to_be_visible(timeout=timeout)

            item = menu.locator(
                "li.dropdown-item",
                has_text=re.compile(
                    rf"^\s*{re.escape(service_type)}\s*$",
                    re.IGNORECASE
                )
            ).first

            if item.count() == 0:
                options = [
                    self._clean(x)
                    for x in menu.locator("li.dropdown-item").all_inner_texts()
                    if self._clean(x)
                ]

                raise AssertionError(
                    f"Service Type '{service_type}' not found. Available: {options}"
                )

            item.scroll_into_view_if_needed()

            def is_checked() -> bool:
                return item.locator("svg.unchecked").count() == 0

            if is_checked():
                self.close_service_type_dropdown()
                return True

            item.click(force=True)

            self.wait_until(
                is_checked,
                timeout_ms=timeout,
                interval_ms=150
            )

            sleep(SLEEP)
            self.close_service_type_dropdown()

            return True

        except Exception as e:
            raise AssertionError(
                f"select_service_type('{service_type}') failed. Problem: {e}"
            )

    # ✅
    def set_all_service_types(self, timeout: int = 8000):
        """
        Select all real Service Type options.
        """

        try:
            dropdown = self.dropdown("Service Type")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            sleep(SLEEP)
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)

            btn.click(force=True)

            menu = dropdown.locator("div.dropdown-menu[data-label='Service Type']").first

            sleep(SLEEP)
            expect(menu).to_be_visible(timeout=timeout)

            rows = menu.locator("li.dropdown-item.multiple")
            expect(rows.first).to_be_visible(timeout=timeout)

            def is_checked(row) -> bool:
                return row.locator("svg.unchecked").count() == 0

            def all_real_service_types_selected() -> bool:
                count = rows.count()

                # skip "All"
                for i in range(1, count):
                    row = rows.nth(i)

                    if not is_checked(row):
                        row.scroll_into_view_if_needed()
                        row.click(force=True)
                        sleep(SLEEP)

                for i in range(1, count):
                    if not is_checked(rows.nth(i)):
                        return False

                return True

            self.wait_until(
                all_real_service_types_selected,
                timeout_ms=timeout,
                interval_ms=200
            )

            sleep(SLEEP)
            self.close_service_type_dropdown()

            return True

        except Exception as e:
            raise AssertionError(f"set_all_service_types failed. Problem: {e}")

    # ✅
    def get_all_selected_service_types(self, timeout: int = 8000) -> list[str]:
        """
        Return all selected Service Type values.
        """

        try:
            dropdown = self.dropdown("Service Type")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            sleep(SLEEP)
            expect(btn).to_be_visible(timeout=timeout)

            # First try reading selected chips from the closed dropdown
            chip_texts = [
                self._clean(t)
                for t in btn.locator(
                    "div.selected-view.multiple span"
                ).all_inner_texts()
            ]

            has_plus = any(
                re.fullmatch(r"\+\s*\d+", t)
                for t in chip_texts
            )

            if chip_texts and not has_plus:
                out = []
                seen = set()

                for text in chip_texts:
                    if not text or text.lower() == "all":
                        continue

                    if text not in seen:
                        seen.add(text)
                        out.append(text)

                return out

            # Open dropdown if needed and inspect menu
            menu = dropdown.locator("div.dropdown-menu[data-label='Service Type']").first

            if menu.count() == 0 or not menu.is_visible():
                btn.click(force=True)

                self.wait_until(
                    lambda: menu.count() > 0 and menu.is_visible(),
                    timeout_ms=timeout,
                    interval_ms=150
                )

            expect(menu).to_be_visible(timeout=timeout)

            rows = menu.locator("li.dropdown-item.multiple")

            selected_types = []
            seen = set()

            for i in range(rows.count()):
                row = rows.nth(i)

                text = self._clean(row.inner_text())

                if not text or text.lower() == "all":
                    continue

                # Selected rows do NOT contain svg.unchecked
                is_selected = row.locator("svg.unchecked").count() == 0

                if is_selected and text not in seen:
                    seen.add(text)
                    selected_types.append(text)

            self.close_service_type_dropdown()

            return selected_types

        except Exception as e:
            raise AssertionError(f"get_all_selected_service_types failed. Problem: {e}")

    # ✅
    def close_service_type_dropdown(self, timeout: int = 5000):
        """
        Close the Service Type dropdown if it is open.
        """

        try:
            dropdown = self.dropdown("Service Type")

            if dropdown.count() == 0:
                return

            container = dropdown.locator("div.dropdown-container").first

            menu = dropdown.locator("div.dropdown-menu[data-label='Service Type']").first

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            def is_open() -> bool:
                try:
                    container_cls = container.get_attribute("class") or ""
                    menu_cls = menu.get_attribute("class") or ""

                    return (
                        ("open" in container_cls and "show" in container_cls)
                        or ("show" in menu_cls)
                    )

                except Exception:
                    return False

            # Already closed
            if not is_open():
                return

            expect(btn).to_be_visible(timeout=timeout)

            btn.scroll_into_view_if_needed()
            sleep(SLEEP)

            btn.click(force=True)

            self.wait_until(
                lambda: not is_open(),
                timeout_ms=timeout,
                interval_ms=150
            )

            sleep(SLEEP)

        except Exception as e:
            raise AssertionError(f"close_service_type_dropdown failed. Problem: {e}")

    # ✅
    def remove_service_type(self, service_type: str, timeout: int = 8000):
        """
        Unselect one Service Type from the multi-select dropdown.
        """

        try:
            service_type = (service_type or "").strip()
            if not service_type:
                raise ValueError("service_type is empty")

            dropdown = self.dropdown("Service Type")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            sleep(SLEEP)
            expect(btn).to_be_visible(timeout=timeout)

            menu = dropdown.locator("div.dropdown-menu[data-label='Service Type']").first

            if menu.count() == 0 or not menu.is_visible():
                btn.click(force=True)

                self.wait_until(
                    lambda: menu.count() > 0 and menu.is_visible(),
                    timeout_ms=timeout,
                    interval_ms=150
                )

            expect(menu).to_be_visible(timeout=timeout)

            row = menu.locator(
                "li.dropdown-item.multiple",
                has_text=re.compile(
                    rf"^\s*{re.escape(service_type)}\s*$",
                    re.IGNORECASE
                )
            ).first

            if row.count() == 0:
                options = [
                    self._clean(x)
                    for x in menu.locator(
                        "li.dropdown-item.multiple"
                    ).all_inner_texts()
                    if self._clean(x)
                ]

                raise AssertionError(
                    f"Service Type '{service_type}' not found. Available: {options}"
                )

            row.scroll_into_view_if_needed()

            def is_checked() -> bool:
                return row.locator("svg.unchecked").count() == 0

            # Already unselected
            if not is_checked():
                self.close_service_type_dropdown()
                return True

            row.click(force=True)

            self.wait_until(
                lambda: not is_checked(),
                timeout_ms=timeout,
                interval_ms=150
            )

            sleep(SLEEP)
            self.close_service_type_dropdown()

            return True

        except Exception as e:
            raise AssertionError(f"remove_service_type('{service_type}') failed. Problem: {e}")

    # ✅
    def remove_all_service_types(self, timeout: int = 8000):
        """
        Clear all selected Service Type values by clicking 'All'.
        """

        try:
            dropdown = self.dropdown("Service Type")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            sleep(SLEEP)
            expect(btn).to_be_visible(timeout=timeout)

            menu = dropdown.locator("div.dropdown-menu[data-label='Service Type']").first

            if menu.count() == 0 or not menu.is_visible():
                btn.click(force=True)

                self.wait_until(
                    lambda: menu.count() > 0 and menu.is_visible(),
                    timeout_ms=timeout,
                    interval_ms=150
                )

            expect(menu).to_be_visible(timeout=timeout)

            all_row = menu.locator("li.dropdown-item.multiple", has_text=re.compile(r"^\s*All\s*$", re.IGNORECASE)).first

            expect(all_row).to_be_visible(timeout=timeout)

            checked_rows = menu.locator("li.dropdown-item.multiple:not(:has(svg.unchecked))")

            checked_count = max(0, checked_rows.count() - 1)

            if checked_count == 0:
                self.close_service_type_dropdown()
                return True

            all_row.scroll_into_view_if_needed()
            all_row.click(force=True)

            self.wait_until(
                lambda: (
                    menu.locator(
                        "li.dropdown-item.multiple:not(:has(svg.unchecked))"
                    ).count() <= 1
                ),
                timeout_ms=timeout,
                interval_ms=200
            )

            sleep(SLEEP)
            self.close_service_type_dropdown()

            return True

        except Exception as e:
            raise AssertionError(f"remove_all_service_types failed. Problem: {e}")

    # =========================
    # Protection Type
    # =========================

    # ✅
    def select_protection_type(self, protection_type: str, timeout: int = 8000):
        """
        Select one Protection Type from the multi-select dropdown.

        Examples: "Unprotected", "Protected", "Restoration".
        """

        try:
            protection_type = (protection_type or "").strip()
            if not protection_type:
                raise ValueError("protection_type is empty")

            dropdown = self.dropdown("Protection Type")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
            sleep(SLEEP)
            expect(btn).to_be_visible(timeout=timeout)
            btn.click(force=True)

            menu = dropdown.locator("div.dropdown-menu[data-label='Protection Type']").first
            sleep(SLEEP)
            expect(menu).to_be_visible(timeout=timeout)

            item = menu.locator("li.dropdown-item",has_text=re.compile(rf"^\s*{re.escape(protection_type)}\s*$", re.IGNORECASE)).first

            if item.count() == 0:
                options = [
                    self._clean(x)
                    for x in menu.locator("li.dropdown-item").all_inner_texts()
                    if self._clean(x)
                ]
                raise AssertionError(
                    f"Protection Type '{protection_type}' not found. Available: {options}"
                )

            item.scroll_into_view_if_needed()

            checkbox = item.locator("app-checkbox").first
            sleep(SLEEP)
            if checkbox.count() > 0:
                checked = checkbox.locator("svg.checked").first
                sleep(SLEEP)
                if checked.count() > 0 and checked.is_visible():
                    self.close_protection_type_dropdown()
                    return True

            item.click(force=True)

            if protection_type.lower() != "all":
                self.wait_until(
                    lambda: item.locator("app-checkbox svg.checked").count() > 0,
                    timeout_ms=timeout,
                    interval_ms=150
                )

            self.close_protection_type_dropdown()
            return True

        except Exception as e:
            raise AssertionError(f"select_protection_type('{protection_type}') failed. Problem: {e}")
    
    # ✅
    def set_all_protection_types(self, timeout: int = 8000):
        """
        Select all real Protection Type options.
        """

        try:
            dropdown = self.dropdown("Protection Type")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            sleep(SLEEP)
            expect(btn).to_be_visible(timeout=timeout)
            btn.click(force=True)

            menu = dropdown.locator("div.dropdown-menu[data-label='Protection Type']").first
            sleep(SLEEP)
            expect(menu).to_be_visible(timeout=timeout)

            rows = menu.locator("li.dropdown-item.multiple")
            sleep(SLEEP)
            expect(rows.first).to_be_visible(timeout=timeout)

            def is_checked(row) -> bool:
                locator = row.locator("svg.unchecked")
                sleep(SLEEP)
                return locator.count() == 0

            def all_real_protection_types_selected() -> bool:
                count = rows.count()

                # Start from 1 to skip "All"
                for i in range(1, count):
                    row = rows.nth(i)

                    if not is_checked(row):
                        row.scroll_into_view_if_needed()
                        row.click(force=True)
                        sleep(SLEEP)

                # Verify again
                for i in range(1, count):
                    if not is_checked(rows.nth(i)):
                        return False

                return True

            self.wait_until(
                all_real_protection_types_selected,
                timeout_ms=timeout,
                interval_ms=200
            )

            sleep(SLEEP)
            self.close_protection_type_dropdown()

            return True

        except Exception as e:
            raise AssertionError(f"set_all_protection_types failed. Problem: {e}")

    # ✅
    def get_all_selected_protection_types(self, timeout: int = 8000) -> list[str]:
        """
        Return all selected Protection Type values.
        """

        try:
            dropdown = self.dropdown("Protection Type")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            sleep(SLEEP)
            expect(btn).to_be_visible(timeout=timeout)

            # 1) First try to read selected chips from the closed dropdown button
            chip_texts = [
                self._clean(t)
                for t in btn.locator(
                    "div.selected-view.multiple span"
                ).all_inner_texts()
            ]

            sleep(SLEEP)

            has_plus = any(
                re.fullmatch(r"\+\s*\d+", t)
                for t in chip_texts
            )

            if chip_texts and not has_plus:
                out = []
                seen = set()

                for text in chip_texts:
                    if not text or text.lower() == "all":
                        continue

                    if text not in seen:
                        seen.add(text)
                        out.append(text)

                return out

            # 2) If chips are compressed / not available, scan dropdown
            menu = dropdown.locator("div.dropdown-menu[data-label='Protection Type']").first
            sleep(SLEEP)

            if menu.count() == 0 or not menu.is_visible():
                btn.click(force=True)

                self.wait_until(
                    lambda: menu.count() > 0 and menu.is_visible(),
                    timeout_ms=timeout,
                    interval_ms=150
                )

            expect(menu).to_be_visible(timeout=timeout)

            rows = menu.locator("li.dropdown-item.multiple")
            sleep(SLEEP)

            selected_types = []
            seen = set()

            for i in range(rows.count()):
                row = rows.nth(i)

                text = self._clean(row.inner_text())

                if not text or text.lower() == "all":
                    continue

                # Selected rows do NOT have svg.unchecked
                is_selected = (
                    row.locator("svg.unchecked").count() == 0
                )

                sleep(SLEEP)

                if is_selected and text not in seen:
                    seen.add(text)
                    selected_types.append(text)

            sleep(SLEEP)

            self.close_protection_type_dropdown()

            return selected_types

        except Exception as e:
            raise AssertionError(f"get_all_selected_protection_types failed. Problem: {e}")

    # ✅
    def close_protection_type_dropdown(self, timeout: int = 5000):
        """
        Close the Protection Type dropdown if it is open.
        """

        try:
            dropdown = self.dropdown("Protection Type")

            if dropdown.count() == 0:
                return

            container = dropdown.locator("div.dropdown-container").first
            sleep(SLEEP)

            menu = dropdown.locator("div.dropdown-menu[data-label='Protection Type']").first
            sleep(SLEEP)

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
            sleep(SLEEP)

            def is_open() -> bool:
                try:
                    container_cls = container.get_attribute("class") or ""
                    menu_cls = menu.get_attribute("class") or ""

                    return (
                        ("open" in container_cls and "show" in container_cls)
                        or ("show" in menu_cls)
                    )

                except Exception:
                    return False

            # Already closed
            if not is_open():
                return

            expect(btn).to_be_visible(timeout=timeout)

            btn.scroll_into_view_if_needed()
            sleep(SLEEP)

            # Click dropdown button to close
            btn.click(force=True)

            self.wait_until(
                lambda: not is_open(),
                timeout_ms=timeout,
                interval_ms=150
            )

        except Exception as e:
            raise AssertionError(f"close_protection_type_dropdown failed. Problem: {e}")

    # ✅
    def remove_protection_type(self, protection_type: str, timeout: int = 8000):
        """
        Unselect one Protection Type from the multi-select dropdown.
        """

        try:
            protection_type = (protection_type or "").strip()
            if not protection_type:
                raise ValueError("protection_type is empty")

            dropdown = self.dropdown("Protection Type")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            sleep(SLEEP)
            expect(btn).to_be_visible(timeout=timeout)

            menu = dropdown.locator("div.dropdown-menu[data-label='Protection Type']").first
            sleep(SLEEP)

            if menu.count() == 0 or not menu.is_visible():
                btn.click(force=True)

                self.wait_until(
                    lambda: menu.count() > 0 and menu.is_visible(),
                    timeout_ms=timeout,
                    interval_ms=150
                )

            expect(menu).to_be_visible(timeout=timeout)

            row = menu.locator(
                "li.dropdown-item.multiple",
                has_text=re.compile(
                    rf"^\s*{re.escape(protection_type)}\s*$",
                    re.IGNORECASE
                )
            ).first

            sleep(SLEEP)

            if row.count() == 0:
                options = [
                    self._clean(x)
                    for x in menu.locator("li.dropdown-item.multiple").all_inner_texts()
                    if self._clean(x)
                ]

                sleep(SLEEP)
                raise AssertionError(
                    f"Protection Type '{protection_type}' not found. Available: {options}"
                )

            row.scroll_into_view_if_needed()

            def is_checked() -> bool:
                return row.locator("svg.unchecked").count() == 0

            # Already unselected
            if not is_checked():
                self.close_protection_type_dropdown()
                return True

            row.click(force=True)

            self.wait_until(
                lambda: not is_checked(),
                timeout_ms=timeout,
                interval_ms=150
            )

            sleep(SLEEP)
            self.close_protection_type_dropdown()

            return True

        except Exception as e:
            raise AssertionError(f"remove_protection_type('{protection_type}') failed. Problem: {e}")

    # ✅
    def remove_all_protection_types(self, timeout: int = 8000):
        """
        Clear all selected Protection Type values by clicking 'All'.
        """

        try:
            dropdown = self.dropdown("Protection Type")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            sleep(SLEEP)
            expect(btn).to_be_visible(timeout=timeout)

            menu = dropdown.locator("div.dropdown-menu[data-label='Protection Type']").first
            sleep(SLEEP)

            # Open only if needed
            if menu.count() == 0 or not menu.is_visible():
                btn.click(force=True)

                self.wait_until(
                    lambda: menu.count() > 0 and menu.is_visible(),
                    timeout_ms=timeout,
                    interval_ms=150
                )

            expect(menu).to_be_visible(timeout=timeout)

            all_row = menu.locator("li.dropdown-item.multiple", has_text=re.compile(r"^\s*All\s*$", re.IGNORECASE)).first
            sleep(SLEEP)
            expect(all_row).to_be_visible(timeout=timeout)

            checked_rows = menu.locator("li.dropdown-item.multiple:not(:has(svg.unchecked))")
            sleep(SLEEP)

            # subtract "All"
            checked_count = max(0, checked_rows.count() - 1)

            if checked_count == 0:
                self.close_protection_type_dropdown()
                return True

            all_row.scroll_into_view_if_needed()
            all_row.click(force=True)

            self.wait_until(
                lambda: (
                    menu.locator(
                        "li.dropdown-item.multiple:not(:has(svg.unchecked))"
                    ).count() <= 1
                ),
                timeout_ms=timeout,
                interval_ms=200
            )

            sleep(SLEEP)
            self.close_protection_type_dropdown()

            return True

        except Exception as e:
            raise AssertionError(f"remove_all_protection_types failed. Problem: {e}")

    # =========================
    # Filter By ( / "Domain/Chassis" / )
    # =========================

    # ✅
    def get_filter_by(self, timeout: int = 8000) -> str:
        """
        Return the currently selected 'Filter by' dropdown value.
        """

        try:
            return self.dropdown_selected_text("Filter by")

        except Exception as e:
            raise AssertionError(f"get_filter_by failed. Problem: {e}")
    
    # ✅
    def set_filter_by(self, filter_by: str, timeout: int = 8000):
        """
        Select the 'Filter by' dropdown value.
        """

        try:
            filter_by = (filter_by or "").strip()
            if not filter_by:
                raise ValueError("filter_by is empty")

            dropdown = self.dropdown("Filter by")

            current_value = self.dropdown_selected_text("Filter by")
            if current_value.lower() == filter_by.lower():
                return True

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            sleep(SLEEP)
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)

            btn.click(force=True)

            menu = dropdown.locator("div.dropdown-menu[data-label='Filter by']").first

            sleep(SLEEP)
            expect(menu).to_be_visible(timeout=timeout)

            item = menu.locator(
                "li.dropdown-item",
                has_text=re.compile(
                    rf"^\s*{re.escape(filter_by)}\s*$",
                    re.IGNORECASE
                )
            ).first
            sleep(SLEEP)

            if item.count() == 0:
                options = [
                    self._clean(x)
                    for x in menu.locator("li.dropdown-item").all_inner_texts()
                    if self._clean(x)
                ]

                sleep(SLEEP)
                raise AssertionError(
                    f"Filter by value '{filter_by}' not found. Available: {options}"
                )

            item.scroll_into_view_if_needed()
            item.click(force=True)

            self.wait_until(
                lambda: self.dropdown_selected_text("Filter by").lower() == filter_by.lower(),
                timeout_ms=timeout,
                interval_ms=150
            )

            return True

        except Exception as e:
            raise AssertionError(f"set_filter_by('{filter_by}') failed. Problem: {e}")

    # =========================
    # Filter By → Devices
    # =========================


    # =========================
    # Filter By → Domain / Chassis
    # =========================
 
    # ✅
    def get_selected_domain_or_chassis(self, timeout: int = 8000) -> str:
        """
        Return the currently selected Domain/Chassis value.
        """

        try:
            dd = self.page.locator("app-dropdown-inventory-tree").filter(
                has=self.page.locator(
                    "div.label",
                    has_text=re.compile(r"^\s*Domain/Chassis\s*$", re.IGNORECASE)
                )
            ).first

            sleep(SLEEP)

            expect(dd).to_be_visible(timeout=timeout)

            btn_span = dd.locator("button.dropdown-inventory-tree-button span").first
            sleep(SLEEP)

            expect(btn_span).to_be_visible(timeout=timeout)

            return self._clean(btn_span.inner_text())

        except Exception as e:
            raise AssertionError(f"get_selected_domain_or_chassis failed. Problem: {e}")
    
    # ✅
    def select_domain_or_chassis(self, name: str, timeout: int = 8000):
        """
        Select Domain/Chassis filter value.
        """

        try:
            name = (name or "").strip()
            if not name:
                raise ValueError("name is empty")

            wants_all = name.lower() in ("all", "all domains")
            expected_text = "All" if wants_all else name.split("/", 1)[0].strip()
            expected_rx = re.compile(rf"\b{re.escape(expected_text)}\b", re.IGNORECASE)

            dd = self.page.locator("app-dropdown-inventory-tree").filter(
                has=self.page.locator(
                    "div.label",
                    has_text=re.compile(r"^\s*Domain/Chassis\s*$", re.IGNORECASE)
                )
            ).first

            sleep(SLEEP)

            expect(dd).to_be_visible(timeout=timeout)

            btn = dd.locator("button.dropdown-inventory-tree-button").first
            sleep(SLEEP)
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)

            current_text = self._clean(btn.inner_text())
            if expected_rx.search(current_text):
                return True

            btn.click(force=True)

            modal = self.page.locator("div.modal-dialog").first
            sleep(SLEEP)
            expect(modal).to_be_visible(timeout=timeout)

            if wants_all:
                default_item = modal.locator(
                    "section.dropdown-inventory-tree-default-item",
                    has_text=re.compile(r"\bAll Domains\b|\bAll\b", re.IGNORECASE)
                ).first
                sleep(SLEEP)

                expect(default_item).to_be_visible(timeout=timeout)
                default_item.click(force=True)

            else:
                tree = modal.locator("app-inventory-tree").first
                sleep(SLEEP)
                expect(tree).to_be_visible(timeout=timeout)

                row = tree.locator(
                    "div.inventory-tree-level-title[type='DOMAIN'], "
                    "div.inventory-tree-level-title[type='CHASSIS']"
                ).filter(
                    has_text=re.compile(rf"^\s*{re.escape(name)}\s*$", re.IGNORECASE)
                ).first

                sleep(SLEEP)

                if row.count() == 0:
                    row = tree.locator(
                        "div.inventory-tree-level-title[type='DOMAIN'], "
                        "div.inventory-tree-level-title[type='CHASSIS']"
                    ).filter(
                        has_text=re.compile(re.escape(name), re.IGNORECASE)
                    ).first

                    sleep(SLEEP)

                if row.count() == 0:
                    raise AssertionError(f"Domain/Chassis '{name}' not found in tree.")

                row.scroll_into_view_if_needed()
                expect(row).to_be_visible(timeout=timeout)
                row.click(force=True)

            btn_span = dd.locator("button.dropdown-inventory-tree-button span").first
            sleep(SLEEP)
            expect(btn_span).to_be_visible(timeout=timeout)

            self.wait_until(
                lambda: expected_rx.search(self._clean(btn_span.inner_text())) is not None,
                timeout_ms=timeout,
                interval_ms=150
            )

            try:
                if modal.is_visible():
                    self.page.keyboard.press("Escape")
            except Exception:
                pass

            return True

        except Exception as e:
            raise AssertionError(f"select_domain_or_chassis('{name}') failed. Problem: {e}")

    # =========================
    # Filter By → Device Type
    # =========================

    # =========================
    # Pagination
    # =========================

    # ✅
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

    # ✅
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
    # Service List table
    # =========================

    # ✅
    def click_on_service(self, row_index: int | str | None = None, service_name: str | None = None, timeout: int = 8000) -> bool:
        """
        Click a service row by GLOBAL row index across all pages OR by service name.

        row_index:
            1 = first service across all pages
            2 = second service across all pages

        service_name:
            exact service name to search across all pages
        """

        try:
            # Supports click_on_service("test1")
            if isinstance(row_index, str) and service_name is None:
                service_name = row_index
                row_index = None

            if row_index is None and not service_name:
                raise ValueError("Either row_index or service_name must be provided")

            if row_index is not None and service_name:
                raise ValueError("Provide either row_index or service_name, not both")

            if row_index is not None:
                if not isinstance(row_index, int):
                    raise ValueError("row_index must be an int")
                if row_index <= 0:
                    raise ValueError("row_index must be >= 1")

            service_name = self._clean(service_name) if service_name else None

            table = self.page.locator(
                "app-service-list table, "
                ".service-list table, "
                ".service-list-table table, "
                "table"
            ).first

            expect(table).to_be_visible(timeout=timeout)

            # ✅ NEW: if requested service is already selected, do nothing
            selected_row = table.locator("tbody tr.selected").first

            if selected_row.count() > 0:
                cells = selected_row.locator("td")

                selected_index = self._clean(cells.nth(0).inner_text()) if cells.count() > 0 else ""
                selected_name = self._clean(cells.nth(1).inner_text()) if cells.count() > 1 else ""

                if service_name and selected_name.lower() == service_name.lower():
                    return True

                if row_index is not None and selected_index == str(row_index):
                    return True

            pagination = self.page.locator(
                "div.simple-table-footer ul.pagination, "
                "ngb-pagination ul.pagination, "
                "ul.pagination"
            ).first

            def get_rows():
                expect(table).to_be_visible(timeout=timeout)
                return table.locator("tbody tr")

            def current_page_number() -> int | None:
                try:
                    active = self.page.locator("ul.pagination li.page-item.active a.page-link").first
                    if active.count() == 0:
                        return None

                    txt = self._clean(active.inner_text())
                    return int(txt) if txt.isdigit() else None

                except Exception:
                    return None

            def next_btn():
                if pagination.count() == 0:
                    return None

                btn = pagination.locator("a.page-link[aria-label='Next']").first
                if btn.count() == 0:
                    btn = pagination.locator(
                        "a.page-link",
                        has_text=re.compile(r"^\s*Next\s*$", re.IGNORECASE)
                    ).first

                return btn

            def prev_btn():
                if pagination.count() == 0:
                    return None

                btn = pagination.locator("a.page-link[aria-label='Previous']").first
                if btn.count() == 0:
                    btn = pagination.locator(
                        "a.page-link",
                        has_text=re.compile(r"^\s*Previous\s*$", re.IGNORECASE)
                    ).first

                return btn

            def is_disabled(btn) -> bool:
                if btn is None or btn.count() == 0:
                    return True

                try:
                    li = btn.locator("xpath=ancestor::li[1]").first
                    cls = (li.get_attribute("class") or "").lower()
                    aria = (btn.get_attribute("aria-disabled") or "").lower()
                    return ("disabled" in cls) or (aria == "true")

                except Exception:
                    try:
                        return btn.is_disabled()
                    except Exception:
                        return False

            def first_row_fingerprint() -> str:
                try:
                    rows = get_rows()
                    if rows.count() == 0:
                        return ""
                    return self._clean(rows.first.inner_text())
                except Exception:
                    return ""

            def wait_for_page_change(before_page: int | None, before_fp: str):
                self.wait_until(
                    lambda: (
                        (
                            before_page is not None
                            and current_page_number() is not None
                            and current_page_number() != before_page
                        )
                        or first_row_fingerprint() != before_fp
                    ),
                    timeout_ms=timeout,
                    interval_ms=150
                )

            def goto_first_page():
                if pagination.count() == 0:
                    return

                for _ in range(MAX_SCROLL_PAGES):
                    p = prev_btn()

                    if p is None or p.count() == 0 or is_disabled(p):
                        break

                    before_page = current_page_number()
                    before_fp = first_row_fingerprint()

                    p.click(force=True)

                    self.wait_until(
                        lambda: (
                            is_disabled(prev_btn())
                            or (
                                before_page is not None
                                and current_page_number() is not None
                                and current_page_number() != before_page
                            )
                            or first_row_fingerprint() != before_fp
                        ),
                        timeout_ms=min(timeout, 4000),
                        interval_ms=150
                    )

            def row_service_name(row) -> str:
                cells = row.locator("td")
                if cells.count() > 1:
                    return self._clean(cells.nth(1).inner_text())
                return self._clean(row.inner_text())

            def find_service_on_current_page():
                rows = get_rows()

                for i in range(rows.count()):
                    row = rows.nth(i)
                    name = row_service_name(row)

                    if name.lower() == service_name.lower():
                        return row

                for i in range(rows.count()):
                    row = rows.nth(i)
                    row_text = self._clean(row.inner_text())

                    if service_name.lower() in row_text.lower():
                        return row

                return None

            goto_first_page()

            target_row = None

            if service_name:
                for _ in range(MAX_SCROLL_PAGES):
                    target_row = find_service_on_current_page()

                    if target_row is not None:
                        break

                    n = next_btn()
                    if n is None or n.count() == 0 or is_disabled(n):
                        break

                    before_page = current_page_number()
                    before_fp = first_row_fingerprint()

                    n.click(force=True)
                    wait_for_page_change(before_page, before_fp)

                if target_row is None:
                    raise AssertionError(f"Service '{service_name}' was not found across all pages.")

            else:
                idx = row_index - 1

                for _ in range(MAX_SCROLL_PAGES):
                    rows = get_rows()
                    count = rows.count()

                    if count == 0:
                        raise AssertionError("Current page contains 0 service rows.")

                    if idx < count:
                        target_row = rows.nth(idx)
                        break

                    idx -= count

                    n = next_btn()
                    if n is None or n.count() == 0 or is_disabled(n):
                        break

                    before_page = current_page_number()
                    before_fp = first_row_fingerprint()

                    n.click(force=True)
                    wait_for_page_change(before_page, before_fp)

                if target_row is None:
                    raise AssertionError(f"row_index={row_index} out of range across pages.")

            target_row.scroll_into_view_if_needed()
            expect(target_row).to_be_visible(timeout=timeout)

            target_row.click(force=True)
            sleep(SLEEP)

            self.wait_until(
                lambda: "selected" in ((target_row.get_attribute("class") or "").lower()),
                timeout_ms=timeout,
                interval_ms=150
            )

            return True

        except Exception as e:
            raise AssertionError(f"click_on_service(row_index={row_index}, service_name={service_name}) failed. Problem: {e}")

    # ✅
    def get_service_list(self, timeout: int = 8000) -> list[dict]:
        """
        Read all services from the Service List table across all pages.
        """

        try:
            table = self.page.locator(
                "app-service-list table, "
                ".service-list table, "
                ".service-list-table table, "
                "table"
            ).first

            expect(table).to_be_visible(timeout=timeout)

            pagination = self.page.locator(
                "div.simple-table-footer ul.pagination, "
                "ngb-pagination ul.pagination, "
                "ul.pagination"
            ).first

            def get_rows():
                expect(table).to_be_visible(timeout=timeout)
                return table.locator("tbody tr")

            def get_headers() -> list[str]:
                ths = table.locator("thead th")
                headers = []

                for i in range(ths.count()):
                    txt = self._clean(ths.nth(i).inner_text())

                    # Ignore action/icon columns
                    if not txt or txt in ("↔", "⊞"):
                        headers.append("")
                    else:
                        headers.append(txt)

                return headers

            def parse_row(row, headers: list[str]) -> dict:
                tds = row.locator("td")
                data = {}

                for i in range(min(tds.count(), len(headers))):
                    key = headers[i]
                    if not key:
                        continue

                    value = self._clean(tds.nth(i).inner_text())
                    data[key] = value

                return data

            def first_row_fingerprint() -> str:
                try:
                    rows = get_rows()
                    if rows.count() == 0:
                        return ""
                    return self._clean(rows.first.inner_text())
                except Exception:
                    return ""

            def current_page_number() -> int | None:
                try:
                    active = self.page.locator("ul.pagination li.page-item.active a.page-link").first

                    if active.count() == 0:
                        return None

                    txt = self._clean(active.inner_text())
                    return int(txt) if txt.isdigit() else None

                except Exception:
                    return None

            def next_btn():
                if pagination.count() == 0:
                    return None

                btn = pagination.locator("a.page-link[aria-label='Next']").first

                if btn.count() == 0:
                    btn = pagination.locator("a.page-link", has_text=re.compile(r"^\s*Next\s*$", re.IGNORECASE)).first

                return btn

            def prev_btn():
                if pagination.count() == 0:
                    return None

                btn = pagination.locator("a.page-link[aria-label='Previous']").first

                if btn.count() == 0:
                    btn = pagination.locator("a.page-link", has_text=re.compile(r"^\s*Previous\s*$", re.IGNORECASE)).first

                return btn

            def is_disabled(btn) -> bool:
                if btn is None or btn.count() == 0:
                    return True

                try:
                    li = btn.locator("xpath=ancestor::li[1]").first
                    cls = (li.get_attribute("class") or "").lower()
                    aria = (btn.get_attribute("aria-disabled") or "").lower()

                    return ("disabled" in cls) or (aria == "true")

                except Exception:
                    try:
                        return btn.is_disabled()
                    except Exception:
                        return False

            def goto_first_page():
                if pagination.count() == 0:
                    return

                for _ in range(MAX_SCROLL_PAGES):
                    p = prev_btn()

                    if p is None or p.count() == 0 or is_disabled(p):
                        break

                    before_page = current_page_number()
                    before_fp = first_row_fingerprint()

                    p.click(force=True)

                    self.wait_until(
                        lambda: (
                            is_disabled(prev_btn())
                            or (
                                before_page is not None
                                and current_page_number() is not None
                                and current_page_number() != before_page
                            )
                            or first_row_fingerprint() != before_fp
                        ),
                        timeout_ms=min(timeout, 4000),
                        interval_ms=150
                    )

            goto_first_page()

            headers = get_headers()
            services = []
            seen = set()

            for _ in range(MAX_SCROLL_PAGES):
                rows = get_rows()

                for i in range(rows.count()):
                    row_data = parse_row(rows.nth(i), headers)

                    if not row_data:
                        continue

                    key = tuple((k, self._clean(str(v))) for k, v in row_data.items())

                    if key not in seen:
                        seen.add(key)
                        services.append(row_data)

                if pagination.count() == 0:
                    break

                n = next_btn()

                if n is None or n.count() == 0 or is_disabled(n):
                    break

                before_page = current_page_number()
                before_fp = first_row_fingerprint()

                n.click(force=True)

                self.wait_until(
                    lambda: (
                        (
                            before_page is not None
                            and current_page_number() is not None
                            and current_page_number() != before_page
                        )
                        or first_row_fingerprint() != before_fp
                    ),
                    timeout_ms=timeout,
                    interval_ms=150
                )

            return services

        except Exception as e:
            raise AssertionError(f"get_service_list failed. Problem: {e}")

    # =========================
    # Events / Alarms 
    # =========================

    # ✅
    def click_on_events_alarms_button(self, timeout: int = 8000) -> bool:
        """
        Click the Events / Alarms button in the Service List footer.

        Usually requires a service row to be selected first.
        """

        try:
            footer = self.page.locator(
                "div.service-actionWrapper-footer, "
                ".service-actionWrapper-footer, "
                "footer"
            ).first

            expect(footer).to_be_visible(timeout=timeout)

            btn = footer.locator("button", has_text=re.compile(r"^\s*Events\s*/\s*Alarms\s*$", re.IGNORECASE)).first

            if btn.count() == 0:
                btn = self.page.locator("button", has_text=re.compile(r"^\s*Events\s*/\s*Alarms\s*$", re.IGNORECASE)).first

            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)

            btn.click(force=True)
            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(f"click_on_events_alarms_button failed. Problem: {e}")

    # ✅
    def set_faults_type(self, faults_type: str):
        self.alarms_and_events.set_faults_type(faults_type)

    # ✅
    def get_faults_type(self, timeout: int = 8000) -> str:
        """
        Return the currently selected Faults type from the Events / Alarms section.
        """

        try:
            dropdown = self.page.locator("app-dropdown[label='Faults type']").first

            sleep(SLEEP)
            expect(dropdown).to_be_visible(timeout=timeout)

            selected = dropdown.locator(".selected-view span").first

            expect(selected).to_be_visible(timeout=timeout)

            return self._clean(selected.inner_text())

        except Exception as e:
            raise AssertionError(f"get_faults_type failed. Problem: {e}")

    # ✅
    def set_severity(self, severity: str):
        self.alarms_and_events.set_severity(severity)

    # ✅
    def get_severity(self, timeout: int = 8000) -> str:
        """
        Return the currently selected Severity.
        """

        try:
            dropdown = self.page.locator("app-dropdown[label='Severity']").first

            sleep(SLEEP)
            expect(dropdown).to_be_visible(timeout=timeout)

            selected = dropdown.locator(".selected-view span").first

            expect(selected).to_be_visible(timeout=timeout)

            return self._clean(selected.inner_text())

        except Exception as e:
            raise AssertionError(f"get_severity failed. Problem: {e}")

    # ✅
    def set_from_date(self, from_date_and_time: str):
        self.alarms_and_events.set_from_date(from_date_and_time)

    # ✅
    def get_from_date(self, timeout: int = 8000) -> str:
        """
        Return the current value of the From date filter.
        """

        try:
            date_input = self.page.locator(
                "app-faults-filter #datepickerFrom input[name='dateRangeFrom'], "
                "app-faults-filter #datepickerFrom input[formcontrolname='dateRangeFrom'], "
                "#datepickerFrom input[name='dateRangeFrom'], "
                "#datepickerFrom input[formcontrolname='dateRangeFrom']"
            ).first

            sleep(SLEEP)
            expect(date_input).to_be_visible(timeout=timeout)

            return self._clean(date_input.input_value())

        except Exception as e:
            raise AssertionError(f"get_from_date failed. Problem: {e}")

    # ✅
    def set_to_date(self, to_date_and_time: str):
        self.alarms_and_events.set_to_date(to_date_and_time)

    # ✅
    def get_to_date(self, timeout: int = 8000) -> str:
        """
        Return the current value of the To date filter.
        """

        try:
            date_input = self.page.locator(
                "app-faults-filter #datepickerTo input[name='dateRangeTo'], "
                "app-faults-filter #datepickerTo input[formcontrolname='dateRangeTo'], "
                "#datepickerTo input[name='dateRangeTo'], "
                "#datepickerTo input[formcontrolname='dateRangeTo']"
            ).first

            sleep(SLEEP)
            expect(date_input).to_be_visible(timeout=timeout)

            return self._clean(date_input.input_value())

        except Exception as e:
            raise AssertionError(f"get_to_date failed. Problem: {e}")

    # ✅
    def set_message(self, message: str):
        self.alarms_and_events.set_message(message)

    # ✅
    def message_check_exact_match_only(self):
        self.alarms_and_events.message_check_exact_match_only()
    
    # ✅
    def message_uncheck_exact_match_only(self):
        self.alarms_and_events.message_uncheck_exact_match_only()

    # ✅
    def hide_event(self, row_index: int | None = None, timeout: int = 8000) -> bool:
        """
        Hide an event from the Service List Events / Alarms panel.
        row_index is GLOBAL across all pages.
        """

        try:
            if row_index is None:
                raise ValueError("row_index must be provided")

            if row_index < 0:
                raise ValueError("row_index must be >= 0")

            self.set_faults_type("Events")

            table = self.page.locator("app-faults-table app-simple-table div.simple-table-container table").first
            expect(table).to_be_visible(timeout=timeout)

            pagination = self.page.locator("app-faults-table app-simple-table ngb-pagination ul.pagination").first

            def get_rows():
                expect(table).to_be_visible(timeout=timeout)
                return table.locator("tbody tr")

            def current_page_number():
                active = pagination.locator("li.page-item.active a.page-link").first
                if active.count() == 0:
                    return None

                txt = self._clean(active.inner_text())
                return int(txt) if txt.isdigit() else None

            def next_btn():
                if pagination.count() == 0:
                    return None

                return pagination.locator(
                    "a.page-link[aria-label='Next'], "
                    "li.page-item a.page-link",
                    has_text=re.compile(r"^\s*Next\s*$", re.IGNORECASE)
                ).first

            def prev_btn():
                if pagination.count() == 0:
                    return None

                return pagination.locator(
                    "a.page-link[aria-label='Previous'], "
                    "li.page-item a.page-link",
                    has_text=re.compile(r"^\s*Previous\s*$", re.IGNORECASE)
                ).first

            def is_disabled(btn) -> bool:
                if btn is None or btn.count() == 0:
                    return True

                li = btn.locator("xpath=ancestor::li[1]").first
                cls = (li.get_attribute("class") or "").lower()
                aria = (btn.get_attribute("aria-disabled") or "").lower()

                return "disabled" in cls or aria == "true"

            def wait_for_page_change(before_page):
                self.wait_until(
                    lambda: (
                        before_page is not None
                        and current_page_number() is not None
                        and current_page_number() != before_page
                    ),
                    timeout_ms=timeout,
                    interval_ms=150
                )

            def goto_first_page():
                if pagination.count() == 0:
                    return

                for _ in range(MAX_SCROLL_PAGES):
                    p = prev_btn()

                    if p is None or p.count() == 0 or is_disabled(p):
                        break

                    before_page = current_page_number()
                    p.click(force=True)

                    self.wait_until(
                        lambda: (
                            is_disabled(prev_btn())
                            or (
                                before_page is not None
                                and current_page_number() is not None
                                and current_page_number() != before_page
                            )
                        ),
                        timeout_ms=min(timeout, 4000),
                        interval_ms=150
                    )

            goto_first_page()

            idx = row_index
            target_row = None

            for _ in range(MAX_SCROLL_PAGES):
                rows = get_rows()
                row_count = rows.count()

                if row_count == 0:
                    raise AssertionError("No event rows found.")

                if idx < row_count:
                    target_row = rows.nth(idx)
                    break

                idx -= row_count

                n = next_btn()
                if n is None or n.count() == 0 or is_disabled(n):
                    break

                before_page = current_page_number()
                n.click(force=True)
                wait_for_page_change(before_page)

            if target_row is None:
                raise AssertionError(f"row_index={row_index} out of range across pages.")

            # Save signature before hiding
            tds = target_row.locator("td")
            target_message = self._clean(tds.nth(0).inner_text() if tds.count() > 0 else "")
            target_source = self._clean(tds.nth(5).inner_text() if tds.count() > 5 else "")
            target_creation = self._clean(tds.nth(7).inner_text() if tds.count() > 7 else "")

            target_row.scroll_into_view_if_needed()
            target_row.click(force=True)
            sleep(SLEEP)

            hide_btn = self.page.locator("div.service-actionWrapper-footer button", has_text=re.compile(r"^\s*Hide\s*$", re.IGNORECASE)).first

            expect(hide_btn).to_be_visible(timeout=timeout)
            self.wait_until(lambda: hide_btn.is_enabled(), timeout_ms=timeout, interval_ms=150)

            hide_btn.click(force=True)
            sleep(1)

            # Make sure "Show hidden events" is unchecked
            try:
                show_hidden_cb = self.page.locator("app-faults-filter app-checkbox", has_text=re.compile(r"Show hidden events", re.IGNORECASE)).first

                if show_hidden_cb.count() > 0:
                    checked_icon = show_hidden_cb.locator("svg.checked").first
                    if checked_icon.count() > 0 and checked_icon.is_visible():
                        show_hidden_cb.locator("label.checkbox-container").first.click(force=True)
                        sleep(SLEEP)

            except Exception:
                pass

            def row_still_visible() -> bool:
                rows = get_rows()

                for i in range(rows.count()):
                    row = rows.nth(i)
                    cells = row.locator("td")

                    msg = self._clean(cells.nth(0).inner_text() if cells.count() > 0 else "")
                    src = self._clean(cells.nth(5).inner_text() if cells.count() > 5 else "")
                    cre = self._clean(cells.nth(7).inner_text() if cells.count() > 7 else "")

                    if msg == target_message and src == target_source and cre == target_creation:
                        return True

                return False

            self.wait_until(
                lambda: not row_still_visible(),
                timeout_ms=timeout,
                interval_ms=200
            )

            return True

        except Exception as e:
            raise AssertionError(f"hide_event failed. Problem: {e}")

    # ✅
    def show_hidden_events(self, show: bool = True):
        self.alarms_and_events.show_hidden_events(show)
    
    # ✅
    def acknowledge_alarm(self, row_index: int | None = None, timeout: int = 8000) -> bool:
        """
        Acknowledge an alarm from the Service List Events / Alarms panel.
        row_index is GLOBAL across all pages.
        """

        try:
            if row_index is None:
                raise ValueError("row_index must be provided")

            if row_index < 0:
                raise ValueError("row_index must be >= 0")

            self.set_faults_type("Alarms")

            table = self.page.locator("app-faults-table app-simple-table div.simple-table-container table").first
            expect(table).to_be_visible(timeout=timeout)

            pagination = self.page.locator("app-faults-table app-simple-table ngb-pagination ul.pagination").first

            def get_rows():
                expect(table).to_be_visible(timeout=timeout)
                return table.locator("tbody tr")

            def current_page_number():
                active = pagination.locator("li.page-item.active a.page-link").first
                if active.count() == 0:
                    return None
                txt = self._clean(active.inner_text())
                return int(txt) if txt.isdigit() else None

            def next_btn():
                if pagination.count() == 0:
                    return None
                return pagination.locator("a.page-link[aria-label='Next'], a.page-link", has_text=re.compile(r"^\s*Next\s*$", re.IGNORECASE)).first

            def prev_btn():
                if pagination.count() == 0:
                    return None
                return pagination.locator(
                    "a.page-link[aria-label='Previous'], a.page-link",
                    has_text=re.compile(r"^\s*Previous\s*$", re.IGNORECASE)
                ).first

            def is_disabled(btn) -> bool:
                if btn is None or btn.count() == 0:
                    return True

                li = btn.locator("xpath=ancestor::li[1]").first
                cls = (li.get_attribute("class") or "").lower()
                aria = (btn.get_attribute("aria-disabled") or "").lower()
                return "disabled" in cls or aria == "true"

            def goto_first_page():
                if pagination.count() == 0:
                    return

                for _ in range(MAX_SCROLL_PAGES):
                    p = prev_btn()
                    if p is None or p.count() == 0 or is_disabled(p):
                        break

                    before = current_page_number()
                    p.click(force=True)

                    self.wait_until(
                        lambda: is_disabled(prev_btn()) or current_page_number() != before,
                        timeout_ms=min(timeout, 4000),
                        interval_ms=150
                    )

            def alarm_is_cleared() -> bool:
                try:
                    cells = target_row.locator("td")

                    # Severity column is td index 2:
                    # Ack = 0, Message = 1, Severity = 2
                    severity_text = self._clean(cells.nth(2).inner_text())

                    return re.search(r"\bClear\b", severity_text, re.IGNORECASE) is not None

                except Exception:
                    return False

            goto_first_page()

            idx = row_index
            target_row = None

            for _ in range(MAX_SCROLL_PAGES):
                rows = get_rows()
                count = rows.count()

                if count == 0:
                    raise AssertionError("No alarm rows found.")

                if idx < count:
                    target_row = rows.nth(idx)
                    break

                idx -= count

                n = next_btn()
                if n is None or n.count() == 0 or is_disabled(n):
                    break

                before = current_page_number()
                n.click(force=True)

                self.wait_until(
                    lambda: current_page_number() != before,
                    timeout_ms=timeout,
                    interval_ms=150
                )

            if target_row is None:
                raise AssertionError(f"row_index={row_index} out of range across pages.")

            target_row.scroll_into_view_if_needed()
            target_row.click(force=True)
            sleep(SLEEP)

            ack_checkbox = target_row.locator("td").nth(0).locator("app-checkbox").first
            expect(ack_checkbox).to_be_visible(timeout=timeout)

            checkbox_label = ack_checkbox.locator("label.checkbox-container").first
            expect(checkbox_label).to_be_visible(timeout=timeout)

            # If already acknowledged
            if ack_checkbox.locator("svg.checked").count() > 0:
                return True

            checkbox_label.click(force=True)
            sleep(SLEEP)

            ack_btn = self.page.locator("div.service-actionWrapper-footer button", has_text=re.compile(r"^\s*Acknowledge\s*$", re.IGNORECASE)).first

            expect(ack_btn).to_be_visible(timeout=timeout)
            self.wait_until(lambda: ack_btn.is_enabled(), timeout_ms=timeout, interval_ms=150)

            ack_btn.click(force=True)

            self.wait_until(
                lambda: ack_checkbox.locator("svg.checked").count() > 0,
                timeout_ms=timeout,
                interval_ms=200
            )

            sleep(SLEEP)

            # Click Clear button
            clear_btn = self.page.locator("button", has_text=re.compile(r"^\s*Clear\s*$", re.IGNORECASE)).first

            expect(clear_btn).to_be_visible(timeout=timeout)

            self.wait_until(
                lambda: clear_btn.is_enabled(),
                timeout_ms=timeout,
                interval_ms=150
            )

            clear_btn.click(force=True)

            # Wait until alarm is cleared
            self.wait_until(
                alarm_is_cleared,
                timeout_ms=timeout,
                interval_ms=200
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"acknowledge_alarm failed. Problem: {e}")

    # =========================
    # Performance
    # ========================= 
 
    # ✅
    def click_on_performance_button(self, service_name: str, timeout: int = 8000):
        """
        Select a service and click the Performance button.
        """

        try:
            # Select the service first
            self.click_on_service(service_name, timeout=timeout)

            btn = self.page.locator("button:has(app-icon[name='chart-bar'])").filter(has_text=re.compile(r"Performance", re.I)).first

            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)

            btn.scroll_into_view_if_needed()
            btn.click(force=True)

            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(f"click_on_performance_button('{service_name}') failed. Problem: {e}")


    def performance_set_display(self, display_value: str) -> bool:
        self.performance.set_display(display_value)


    def performance_get_display(self):
        pass
    
    # ✅
    def performance_set_period_start(self, period_start: str) -> bool:
        self.performance.set_period_start(period_start)

    # ✅
    def performance_get_period_start(self) -> str:
        return self.performance.get_period_start()

    # ✅
    def performance_set_period_end(self, period_end: str) -> bool:
        self.performance.set_period_end(period_end)

    # ✅
    def performance_get_period_end(self) -> str:
        return self.performance.get_period_end()

    # ✅
    def performance_set_device_A(self, device_a: str, timeout: int = 8000) -> bool:
        """
        Select Device A from the embedded Performance panel.
        """

        try:
            device_a = (device_a or "").strip()
            if not device_a:
                raise ValueError("device_a is empty")

            dropdown = self.page.locator(
                "app-performance-filter app-dropdown[formcontrolname='deviceA'], "
                "app-dropdown[formcontrolname='deviceA']:has(.label:text-is('Device A'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            current = self.performance_get_device_A(timeout=timeout)
            if current.lower() == device_a.lower():
                return True

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)

            btn.click(force=True)

            menu = dropdown.locator(
                "div.dropdown-menu[data-label='Device A'], "
                "div.dropdown-menu"
            ).first

            expect(menu).to_be_visible(timeout=timeout)

            item = menu.locator(
                "li.dropdown-item",
                has_text=re.compile(rf"^\s*{re.escape(device_a)}\s*$", re.IGNORECASE)
            ).first

            if item.count() == 0:
                options = [
                    self._clean(x)
                    for x in menu.locator("li.dropdown-item").all_inner_texts()
                    if self._clean(x)
                ]
                raise AssertionError(
                    f"Device A '{device_a}' not found. Available: {options}"
                )

            item.scroll_into_view_if_needed()
            item.click(force=True)

            self.wait_until(
                lambda: self.performance_get_device_A(timeout=timeout).lower() == device_a.lower(),
                timeout_ms=timeout,
                interval_ms=150
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"performance_set_device_A('{device_a}') failed. Problem: {e}")

    # ✅
    def performance_get_device_A(self, timeout: int = 8000) -> str:
        """
        Get selected Device A value from the embedded Performance panel.
        """

        try:
            dropdown = self.page.locator(
                "app-performance-filter app-dropdown[formcontrolname='deviceA'], "
                "app-dropdown[formcontrolname='deviceA']:has(.label:text-is('Device A'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            selected = dropdown.locator(".selected-view span").first
            expect(selected).to_be_visible(timeout=timeout)

            return self._clean(selected.inner_text())

        except Exception as e:
            raise AssertionError(f"performance_get_device_A failed. Problem: {e}")

    # ✅
    def performance_set_device_Z(self, device_z: str, timeout: int = 8000) -> bool:
        """
        Select Device Z from the embedded Performance panel.
        """

        try:
            device_z = (device_z or "").strip()
            if not device_z:
                raise ValueError("device_z is empty")

            dropdown = self.page.locator(
                "app-performance-filter app-dropdown[formcontrolname='deviceZ'], "
                "app-dropdown[formcontrolname='deviceZ']:has(.label:text-is('Device Z'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            current = self.performance_get_device_Z(timeout=timeout)
            if current.lower() == device_z.lower():
                return True

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)

            btn.click(force=True)

            menu = self.page.locator("div.dropdown-menu[data-label='Device Z']").first

            expect(menu).to_be_visible(timeout=timeout)

            item = menu.locator(
                "li.dropdown-item",
                has_text=re.compile(
                    rf"^\s*{re.escape(device_z)}\s*$",
                    re.IGNORECASE
                )
            ).first

            if item.count() == 0:
                options = [
                    self._clean(x)
                    for x in menu.locator("li.dropdown-item").all_inner_texts()
                    if self._clean(x)
                ]
                raise AssertionError(
                    f"Device Z '{device_z}' not found. Available: {options}"
                )

            item.scroll_into_view_if_needed()
            item.click(force=True)

            self.wait_until(
                lambda: self.performance_get_device_Z(timeout=timeout).lower()
                == device_z.lower(),
                timeout_ms=timeout,
                interval_ms=150
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"performance_set_device_Z('{device_z}') failed. Problem: {e}")
    
    # ✅
    def performance_get_device_Z(self, timeout: int = 8000) -> str:
        """
        Get selected Device Z value from the embedded Performance panel.
        """

        try:
            dropdown = self.page.locator(
                "app-performance-filter app-dropdown[formcontrolname='deviceZ'], "
                "app-dropdown[formcontrolname='deviceZ']:has(.label:text-is('Device Z'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            selected = dropdown.locator(".selected-view span").first

            expect(selected).to_be_visible(timeout=timeout)

            return self._clean(selected.inner_text())

        except Exception as e:
            raise AssertionError(f"performance_get_device_Z failed. Problem: {e}")

    # ✅
    def performance_set_port_A(self, port_a: str, timeout: int = 8000) -> bool:
        """
        Select Port A from the embedded Performance panel.
        """

        try:
            port_a = (port_a or "").strip()
            if not port_a:
                raise ValueError("port_a is empty")

            dropdown = self.page.locator(
                "app-performance-filter app-dropdown[formcontrolname='portA'], "
                "app-dropdown[formcontrolname='portA']:has(.label:text-is('Port A'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            current = self.performance_get_port_A(timeout=timeout)
            if current.lower() == port_a.lower():
                return True

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)

            btn.click(force=True)

            menu = self.page.locator("div.dropdown-menu[data-label='Port A']").first

            expect(menu).to_be_visible(timeout=timeout)

            item = menu.locator(
                "li.dropdown-item",
                has_text=re.compile(rf"^\s*{re.escape(port_a)}\s*$", re.IGNORECASE)
            ).first

            if item.count() == 0:
                options = [
                    self._clean(x)
                    for x in menu.locator("li.dropdown-item").all_inner_texts()
                    if self._clean(x)
                ]
                raise AssertionError(
                    f"Port A '{port_a}' not found. Available: {options}"
                )

            item.scroll_into_view_if_needed()
            item.click(force=True)

            self.wait_until(
                lambda: self.performance_get_port_A(timeout=timeout).lower() == port_a.lower(),
                timeout_ms=timeout,
                interval_ms=150
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"performance_set_port_A('{port_a}') failed. Problem: {e}")

    # ✅
    def performance_get_port_A(self, timeout: int = 8000) -> str:
        """
        Get selected Port A value from the embedded Performance panel.
        """

        try:
            dropdown = self.page.locator(
                "app-performance-filter app-dropdown[formcontrolname='portA'], "
                "app-dropdown[formcontrolname='portA']:has(.label:text-is('Port A'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            selected = dropdown.locator(".selected-view span").first
            expect(selected).to_be_visible(timeout=timeout)

            return self._clean(selected.inner_text())

        except Exception as e:
            raise AssertionError(f"performance_get_port_A failed. Problem: {e}")

    # ✅
    def performance_set_port_Z(self, port_z: str, timeout: int = 8000) -> bool:
        """
        Select Port Z from the embedded Performance panel.
        """

        try:
            port_z = (port_z or "").strip()
            if not port_z:
                raise ValueError("port_z is empty")

            dropdown = self.page.locator(
                "app-performance-filter app-dropdown[formcontrolname='portZ'], "
                "app-dropdown[formcontrolname='portZ']:has(.label:text-is('Port Z'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            current = self.performance_get_port_Z(timeout=timeout)
            if current.lower() == port_z.lower():
                return True

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)

            btn.click(force=True)

            menu = self.page.locator("div.dropdown-menu[data-label='Port Z']").first

            expect(menu).to_be_visible(timeout=timeout)

            item = menu.locator(
                "li.dropdown-item",
                has_text=re.compile(rf"^\s*{re.escape(port_z)}\s*$", re.IGNORECASE)
            ).first

            if item.count() == 0:
                options = [
                    self._clean(x)
                    for x in menu.locator("li.dropdown-item").all_inner_texts()
                    if self._clean(x)
                ]
                raise AssertionError(
                    f"Port Z '{port_z}' not found. Available: {options}"
                )

            item.scroll_into_view_if_needed()
            item.click(force=True)

            self.wait_until(
                lambda: self.performance_get_port_Z(timeout=timeout).lower() == port_z.lower(),
                timeout_ms=timeout,
                interval_ms=150
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"performance_set_port_Z('{port_z}') failed. Problem: {e}")

    # ✅
    def performance_get_port_Z(self, timeout: int = 8000) -> str:
        """
        Get selected Port Z value from the embedded Performance panel.
        """

        try:
            dropdown = self.page.locator(
                "app-performance-filter app-dropdown[formcontrolname='portZ'], "
                "app-dropdown[formcontrolname='portZ']:has(.label:text-is('Port Z'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            selected = dropdown.locator(".selected-view span").first
            expect(selected).to_be_visible(timeout=timeout)

            return self._clean(selected.inner_text())

        except Exception as e:
            raise AssertionError(f"performance_get_port_Z failed. Problem: {e}")

    # ✅
    def performance_set_pm_period_type(self, pm_period_type: str) -> bool:
        self.performance.set_pm_period_type(pm_period_type)

    # ✅
    def performance_get_pm_period_type(self) -> str:
        return self.performance.get_pm_period_type()

    # ✅
    def performance_set_pm_type(self, pm_type: str) -> bool:
        self.performance.set_pm_type(pm_type)

    # ✅
    def performance_get_pm_type(self) -> str:
        return self.performance.get_pm_type()

    # ✅
    def performance_get_pm_table(self, all_pages: bool = False, timeout: int = 8000) -> list[dict]:
        """
        Read the embedded Performance PM table inside Service List.

        Works generically for any number of columns.

        If all_pages=True, reads all paginated PM table pages.
        """

        try:
            self.performance_refresh_pm_table()

            table = self.page.locator(
                ".service-actionWrapper-modePanels app-performance-table "
                "app-universal-table table, "
                "app-performance-table.performance-actionWrapper-embedded table, "
                "app-performance-table app-universal-table table"
            ).first

            expect(table).to_be_visible(timeout=timeout)

            def read_current_page() -> list[dict]:
                header_cells = table.locator("thead th:not(.expand):not(.edit)")

                headers = []

                for i in range(header_cells.count()):
                    header_text = self._clean(header_cells.nth(i).inner_text())
                    if header_text:
                        headers.append(header_text)

                if not headers:
                    raise AssertionError("Embedded PM table headers were not found.")

                rows = table.locator("tbody tr")
                data = []

                for i in range(rows.count()):
                    row = rows.nth(i)

                    # Ignore empty/helper rows
                    raw_cells = row.locator("td")
                    values = []

                    for j in range(len(headers)):
                        if j < raw_cells.count():
                            values.append(self._clean(raw_cells.nth(j).inner_text()))
                        else:
                            values.append("")

                    row_dict = {
                        headers[j]: values[j]
                        for j in range(len(headers))
                    }

                    if any(row_dict.values()):
                        data.append(row_dict)

                return data

            def first_row_fingerprint() -> str:
                first_row = table.locator("tbody tr").first
                if first_row.count() == 0:
                    return ""
                return self._clean(first_row.inner_text())

            def active_page_text() -> str:
                active = self.page.locator(
                    ".service-actionWrapper-modePanels "
                    "app-performance-table ul.pagination "
                    "li.page-item.active a.page-link"
                ).first

                if active.count() == 0:
                    return ""

                return self._clean(active.inner_text())

            def next_button():
                return self.page.locator(
                    ".service-actionWrapper-modePanels "
                    "app-performance-table ul.pagination "
                    "li.page-item:has(a[aria-label='Next'])"
                ).first

            def click_next_embedded() -> bool:
                next_li = next_button()

                if next_li.count() == 0:
                    return False

                cls = (next_li.get_attribute("class") or "")
                if "disabled" in cls.split():
                    return False

                next_a = next_li.locator("a[aria-label='Next']").first
                expect(next_a).to_be_visible(timeout=timeout)

                next_a.click(force=True)
                return True

            if not all_pages:
                return read_current_page()

            all_data = []
            seen = set()

            while True:
                for row in read_current_page():
                    key = tuple(row.items())
                    if key not in seen:
                        seen.add(key)
                        all_data.append(row)

                pager = self.page.locator(".service-actionWrapper-modePanels app-performance-table ul.pagination").first

                if pager.count() == 0:
                    break

                before_page = active_page_text()
                before_fp = first_row_fingerprint()

                clicked = click_next_embedded()
                if not clicked:
                    break

                self.wait_until(
                    lambda: (
                        active_page_text() != before_page
                        or first_row_fingerprint() != before_fp
                    ),
                    timeout_ms=timeout,
                    interval_ms=200
                )

                expect(table).to_be_visible(timeout=timeout)

            return all_data

        except Exception as e:
            raise AssertionError(f"performance_get_pm_table failed. Problem: {e}")

    # ✅
    def performance_refresh_pm_table(self):
        self.performance.refresh_pm_table()

    # =========================
    # Path
    # =========================
    
    # ✅
    def click_on_path(self, row_index: int | str | None = None, service_name: str | None = None, timeout: int = 8000) -> bool:
        """
        Click Path for a service by GLOBAL row index across all pages OR by service name.

        Usage:
            click_on_path(row_index=1)
            click_on_path(service_name="test0")
        """

        try:
            if isinstance(row_index, str) and service_name is None:
                service_name = row_index
                row_index = None

            if row_index is None and not service_name:
                raise ValueError("Either row_index or service_name must be provided")

            if row_index is not None and service_name:
                raise ValueError("Provide either row_index or service_name, not both")

            selected_row = self.page.locator(
                "app-services-table app-universal-table table tbody tr.selected, "
                "app-universal-table table tbody tr.selected, "
                "tbody tr.selected"
            ).first

            already_selected = False
            expected_service_name = ""

            if selected_row.count() > 0:
                cells = selected_row.locator("td")
                if cells.count() > 1:
                    selected_service_name = self._clean(cells.nth(1).inner_text())

                    if service_name:
                        expected_service_name = self._clean(service_name)
                        already_selected = selected_service_name.lower() == expected_service_name.lower()
                    elif row_index is not None:
                        visible_index = self._clean(cells.nth(0).inner_text())
                        already_selected = visible_index == str(row_index)
                        expected_service_name = selected_service_name

            if not already_selected:
                if service_name:
                    self.click_on_service(service_name=service_name, timeout=timeout)
                    expected_service_name = self._clean(service_name)
                else:
                    self.click_on_service(row_index=row_index, timeout=timeout)

                    selected_row = self.page.locator(
                        "app-services-table app-universal-table table tbody tr.selected, "
                        "app-universal-table table tbody tr.selected, "
                        "tbody tr.selected"
                    ).first

                    expect(selected_row).to_be_visible(timeout=timeout)
                    cells = selected_row.locator("td")
                    expected_service_name = self._clean(cells.nth(1).inner_text())

            path_btn = self.page.locator(
                "div.service-actionWrapper-footer button",
                has_text=re.compile(r"^\s*Path\s*$", re.IGNORECASE)
            ).first

            expect(path_btn).to_be_visible(timeout=timeout)
            self.wait_until(lambda: path_btn.is_enabled(), timeout_ms=timeout, interval_ms=150)

            path_btn.click(force=True)

            path_dialog = self.page.locator(
                "app-service-workspace-path-dialog div.service-path-dialog[role='dialog'], "
                "div.service-path-dialog[role='dialog'], "
                "div.service-path-dialog"
            ).filter(
                has_text=re.compile(r"ROADM\s+Service\s+Path", re.IGNORECASE)
            ).first

            expect(path_dialog).to_be_visible(timeout=timeout)

            title = path_dialog.locator(
                ".service-path-dialog-title, "
                "#service-path-dialog-title"
            ).first

            expect(title).to_be_visible(timeout=timeout)

            actual_title = self._clean(title.inner_text())
            if expected_service_name and actual_title.lower() != expected_service_name.lower():
                raise AssertionError(
                    f"Path dialog opened for wrong service. "
                    f"Expected '{expected_service_name}', got '{actual_title}'."
                )

            path_table = path_dialog.locator(
                "table.service-path-dialog-table, "
                ".service-path-dialog-tableWrap table, "
                "table"
            ).first

            expect(path_table).to_be_visible(timeout=timeout)

            return True

        except Exception as e:
            raise AssertionError(f"click_on_path(row_index={row_index}, service_name={service_name}) failed. Problem: {e}")

    # ✅
    def close_ROADM_service_path_table(self, timeout: int = 8000) -> bool:
        """
        Close the ROADM Service Path dialog.
        """

        try:
            dialog = self.page.locator(
                "app-service-workspace-path-dialog div.service-path-dialog[role='dialog'], "
                "div.service-path-dialog[role='dialog'], "
                "div.service-path-dialog"
            ).first

            expect(dialog).to_be_visible(timeout=timeout)

            # Try close icon/button
            close_btn = dialog.locator(
                "app-icon[name='close-square'], "
                "button[aria-label='Close'], "
                ".close-button, "
                ".service-path-dialog-close"
            ).first

            if close_btn.count() > 0:
                close_btn.click(force=True)
            else:
                # Fallback
                self.page.keyboard.press("Escape")

            self.wait_until(
                lambda: dialog.count() == 0 or not dialog.is_visible(),
                timeout_ms=timeout,
                interval_ms=150
            )

            return True

        except Exception as e:
            raise AssertionError(f"close_service_path_table failed. Problem: {e}")

    # ✅
    def get_ROADM_service_path_table(self, row_index: int | str | None = None, service_name: str | None = None, timeout: int = 8000) -> list[dict]:
        """
        Open and read the ROADM Service Path dialog table.

        Expected columns:
            Chassis, Device 1, Port 1, Device 2, Port 2
        """

        try:
            # Supports get_ROADM_service_path_table("test0")
            if isinstance(row_index, str) and service_name is None:
                service_name = row_index
                row_index = None

            if row_index is None and not service_name:
                raise ValueError("Either row_index or service_name must be provided")

            if row_index is not None and service_name:
                raise ValueError("Provide either row_index or service_name, not both")

            if row_index is not None:
                self.click_on_path(row_index=row_index, timeout=timeout)
            else:
                self.click_on_path(service_name=service_name, timeout=timeout)

            path_dialog = self.page.locator(
                "app-service-workspace-path-dialog div.service-path-dialog[role='dialog'], "
                "div.service-path-dialog[role='dialog'], "
                "div.service-path-dialog"
            ).filter(
                has_text=re.compile(r"ROADM\s+Service\s+Path", re.IGNORECASE)
            ).first

            expect(path_dialog).to_be_visible(timeout=timeout)

            table = path_dialog.locator(
                "table.service-path-dialog-table, "
                ".service-path-dialog-tableWrap table, "
                "table"
            ).first

            expect(table).to_be_visible(timeout=timeout)

            headers = [
                self._clean(h)
                for h in table.locator("thead th").all_inner_texts()
                if self._clean(h)
            ]

            if not headers:
                headers = ["Chassis", "Device 1", "Port 1", "Device 2", "Port 2"]

            rows = table.locator("tbody tr")
            data = []

            for i in range(rows.count()):
                row = rows.nth(i)

                cells = [
                    self._clean(c)
                    for c in row.locator("td").all_inner_texts()
                ]

                if not any(cells):
                    continue

                row_dict = {}

                for j, header in enumerate(headers):
                    row_dict[header] = cells[j] if j < len(cells) else ""

                data.append(row_dict)

            return data

        except Exception as e:
            raise AssertionError(f"get_ROADM_service_path_table failed. Problem: {e}")

    # =========================
    # Rename
    # =========================
 
    # ✅
    def rename_service(self, new_service_name: str, old_service_name: str | None = None, row_index: int | None = None, timeout: int = 8000) -> bool:
        """
        Rename a service by GLOBAL row index across all pages.

        row_index:
            1 = first service across all pages
            2 = second service across all pages

        old_service_name:
            exact service name to search across all pages
        """

        try:
            if row_index is None and old_service_name is None:
                raise ValueError("row_index or old_service_name must be provided")

            if row_index is not None and old_service_name:
                raise ValueError("Provide either row_index or old_service_name, not both")

            if row_index is not None and row_index <= 0:
                raise ValueError("row_index must be >= 1")

            new_service_name = (new_service_name or "").strip()
            if not new_service_name:
                raise ValueError("new_service_name is empty")

            if old_service_name is None:
                self.click_on_service(row_index=row_index, timeout=timeout)
            else:
                self.click_on_service(service_name=old_service_name, timeout=timeout)

            selected_row = self.page.locator(
                "app-services-table app-universal-table table tbody tr.selected, "
                "app-universal-table table tbody tr.selected, "
                "tbody tr.selected"
            ).first

            expect(selected_row).to_be_visible(timeout=timeout)

            cells = selected_row.locator("td")
            old_service_name = self._clean(cells.nth(1).inner_text())

            rename_btn = self.page.locator("div.service-actionWrapper-footer button",has_text=re.compile(r"^\s*Rename\s*$", re.IGNORECASE)).first

            expect(rename_btn).to_be_visible(timeout=timeout)
            self.wait_until(lambda: rename_btn.is_enabled(), timeout_ms=timeout, interval_ms=150)

            rename_btn.click(force=True)

            modal = self.page.locator(
                "app-service-workspace-dialog div.service-dialog[role='dialog'], "
                "div.service-dialog[role='dialog'], "
                "div.service-dialog"
            ).filter(
                has_text=re.compile(r"Rename\s+Service", re.IGNORECASE)
            ).first

            expect(modal).to_be_visible(timeout=timeout)

            name_input = modal.locator(
                "input.service-dialog-input, "
                "label.service-dialog-field input, "
                "input[type='text'], "
                "input"
            ).first

            expect(name_input).to_be_visible(timeout=timeout)
            expect(name_input).to_be_enabled(timeout=timeout)

            name_input.click(force=True)
            name_input.fill(new_service_name)

            self.wait_until(
                lambda: (name_input.input_value() or "").strip() == new_service_name,
                timeout_ms=timeout,
                interval_ms=150
            )

            confirm_btn = modal.locator(
                "button.btn-primary, "
                "button",
                has_text=re.compile(r"^\s*Rename\s*$", re.IGNORECASE)
            ).first

            expect(confirm_btn).to_be_visible(timeout=timeout)
            self.wait_until(lambda: confirm_btn.is_enabled(), timeout_ms=timeout, interval_ms=150)

            confirm_btn.click(force=True)

            # Wait until dialog closes
            self.wait_until(
                lambda: modal.count() == 0 or not modal.is_visible(),
                timeout_ms=timeout,
                interval_ms=200
            )

            # Wait until the selected row/table shows the new name
            self.wait_until(
                lambda: self.page.locator(
                    "app-services-table app-universal-table table tbody tr, "
                    "app-universal-table table tbody tr, "
                    "tbody tr",
                    has_text=re.compile(re.escape(new_service_name), re.IGNORECASE)
                ).count() > 0,
                timeout_ms=timeout,
                interval_ms=300
            )

            return True

        except Exception as e:
            raise AssertionError(f"rename_service(row_index={row_index}) failed. Problem: {e}")

    # ✅
    def rename_service_cancel_button(self, timeout: int = 8000) -> bool:
        """
        Click Cancel in Rename Service dialog.
        """

        try:
            cancel_btn = self.page.get_by_role("button", name=re.compile(r"^\s*Cancel\s*$", re.IGNORECASE)).last
            expect(cancel_btn).to_be_visible(timeout=timeout)
            expect(cancel_btn).to_be_enabled(timeout=timeout)

            cancel_btn.click()

            self.wait_until(
                lambda: self.page.get_by_role(
                    "button",
                    name=re.compile(r"^\s*Cancel\s*$", re.IGNORECASE)
                ).count() == 0,
                timeout_ms=timeout,
                interval_ms=200
            )

            return True

        except Exception as e:
            raise AssertionError(f"rename_service_cancel_button failed. Problem: {e}")

    # =========================
    # Remove
    # =========================
 
    # ✅
    def remove_service(self, row_index: int | None = None, service_name: str | None = None, timeout: int = 8000) -> bool:
        """
        Remove a service by GLOBAL row index across all pages.

        row_index:
            1 = first service across all pages
            2 = second service across all pages

        service_name:
            exact service name to search across all pages
        """

        try:
            if row_index is None and service_name is None:
                raise ValueError("row_index or service_name must be provided")

            if row_index is not None and service_name:
                raise ValueError("Provide either row_index or service_name, not both")

            if row_index is not None and row_index <= 0:
                raise ValueError("row_index must be >= 1")

            # Reuse pagination-safe service selection
            if service_name:
                self.click_on_service(service_name=service_name, timeout=timeout)
            else:
                self.click_on_service(row_index=row_index, timeout=timeout)

            selected_row = self.page.locator(
                "app-services-table app-universal-table table tbody tr.selected, "
                "app-universal-table table tbody tr.selected, "
                "tbody tr.selected"
            ).first

            expect(selected_row).to_be_visible(timeout=timeout)

            cells = selected_row.locator("td")
            service_name = self._clean(cells.nth(1).inner_text())

            remove_btn = self.page.locator(
                "div.service-actionWrapper-footer button",
                has_text=re.compile(r"^\s*Remove\s*$", re.IGNORECASE)
            ).first

            expect(remove_btn).to_be_visible(timeout=timeout)
            self.wait_until(lambda: remove_btn.is_enabled(), timeout_ms=timeout, interval_ms=150)

            remove_btn.click(force=True)

            # New modal structure is app-service-workspace-dialog / service-dialog
            modal = self.page.locator(
                "app-service-workspace-dialog div.service-dialog[role='dialog'], "
                "div.service-dialog[role='dialog'], "
                "div.service-dialog"
            ).filter(
                has_text=re.compile(r"Remove\s+Service", re.IGNORECASE)
            ).first

            expect(modal).to_be_visible(timeout=timeout)

            confirm_btn = modal.locator(
                "button.btn-primary, "
                "button",
                has_text=re.compile(r"^\s*Remove\s*$", re.IGNORECASE)
            ).first

            expect(confirm_btn).to_be_visible(timeout=timeout)
            self.wait_until(lambda: confirm_btn.is_enabled(), timeout_ms=timeout, interval_ms=150)

            confirm_btn.click(force=True)
            sleep(SLEEP)

            # Wait until dialog closes
            self.wait_until(
                lambda: modal.count() == 0 or not modal.is_visible(),
                timeout_ms=timeout,
                interval_ms=200
            )

            # Wait until service no longer appears in the table
            self.wait_until(
                lambda: self.page.locator(
                    "app-services-table app-universal-table table tbody tr, "
                    "app-universal-table table tbody tr, "
                    "tbody tr",
                    has_text=re.compile(re.escape(service_name), re.IGNORECASE)
                ).count() == 0,
                timeout_ms=timeout,
                interval_ms=300
            )

            return True

        except Exception as e:
            raise AssertionError(f"remove_service(row_index={row_index}) failed. Problem: {e}")
    
    # ✅
    def remove_service_cancel_button(self, timeout: int = 8000) -> bool:
        """
        Click Cancel in Remove Service dialog.
        """

        try:
            cancel_btn = self.page.get_by_role("button", name=re.compile(r"^\s*Cancel\s*$", re.IGNORECASE)).last

            expect(cancel_btn).to_be_visible(timeout=timeout)
            expect(cancel_btn).to_be_enabled(timeout=timeout)

            cancel_btn.click()

            self.wait_until(
                lambda: self.page.get_by_role(
                    "button",
                    name=re.compile(r"^\s*Cancel\s*$", re.IGNORECASE)
                ).count() == 0,
                timeout_ms=timeout,
                interval_ms=200
            )

            return True

        except Exception as e:
            raise AssertionError(f"remove_service_cancel_button failed. Problem: {e}")

    # =========================
    # Export CSV
    # =========================

    # ✅
    def export_CSV(self, timeout: int = 8000, save_dir: str = r"C:\temp") -> str:
        """
        Click Export CSV and save the downloaded file to the desired folder.
        Returns the saved file path.
        """

        try:
            export_btn = self.page.locator("button", has_text=re.compile(r"^\s*Export\s+CSV\s*$", re.IGNORECASE)).first

            expect(export_btn).to_be_visible(timeout=timeout)
            self.wait_until(lambda: export_btn.is_enabled(), timeout_ms=timeout, interval_ms=150)

            with self.page.expect_download(timeout=timeout) as download_info:
                export_btn.click(force=True)

            download = download_info.value

            save_path = Path(save_dir) / download.suggested_filename
            download.save_as(str(save_path))

            print(f"CSV downloaded to: {save_path}")
            return str(save_path)

        except Exception as e:
            raise AssertionError(f"export_CSV failed. Problem: {e}")

    def verify_CSV_valid(self):
        """
        Verify the downloaded CSV is valid and matches the services in the table.
        """

        pass

        