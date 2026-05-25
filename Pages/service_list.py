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


MAX_SCROLL_PAGES = 60
SLEEP = 0.2


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
    def filters_root(self):
        """
        Return the root locator for the Service List filters section.
        Used as a base for locating filter controls.
        """
        return self.page.locator(".service-filters").first

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
    def descending_checkbox(self):
        """
        Return the Descending order checkbox.
        """
        root = self.filters_root()
        cb = root.locator("app-checkbox[label='Descending']").first
        expect(cb).to_be_visible(timeout=5000)
        return cb

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
    # Events / Alarms Panel
    # =========================

    # ✅
    def events_tabset(self):
        """Return the Events/Alarms tabset container."""
        tabset = self.page.locator("tabset.tab-container").first
        if tabset.count() == 0:
            raise AssertionError("Events/Alarms tabset not found (tabset.tab-container).")
        return tabset

    # ✅
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

    # ✅
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

    # ✅
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

    # ✅
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
    
    # ✅
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

    # ✅
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

    # ✅
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

    # ✅
    def open_events_alarms(self, timeout: int = 12000):
        """
        Open the Events/Alarms inside panel.
        Clicks the corresponding action button and waits for the tabset to appear.
        """
        btn = self.page.locator("button:has-text('Events/Alarms')").first
        expect(btn).to_be_visible(timeout=timeout)
        btn.click(force=True)
        expect(self.page.locator("tabset.tab-container").first).to_be_visible(timeout=timeout)

    # ❌
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
    
    # ❌
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

    # ❌
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
    
    # ✅
    def close_events_alarms(self, timeout: int = 5000):
        """
        Close (hide) the Events/Alarms panel if it's currently open.
        """
        tabset = self.page.locator("tabset.tab-container").first
        sleep(0.5)

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
        sleep(0.5)

        if btn.count() == 0:
            # fallback by text (if icon selector changes)
            btn = self.page.locator("div.service-actionWrapper-footer button:has-text('Events/Alarms')").first
            sleep(0.5)

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
 
    # ✅
    def click_edit_columns(self):
        """
        Clicks the Edit Columns button.
        """
        btn = self.page.locator("button:has-text('Edit columns')").first
        expect(btn).to_be_visible(timeout=5000)
        btn.click()

    # ✅
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

    # ✅
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