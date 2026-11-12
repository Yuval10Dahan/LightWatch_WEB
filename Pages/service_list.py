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

    def _wait_for_page_rows(self, rows_text: Callable[[], str], active_page: Callable[[], object],
                            before_rows: str, before_page, timeout: int = 8000):
        """
        After clicking a pager link (Next / Previous / a page number): wait until the table shows the
        new page's rows. LW tables highlight the new page number at once (~10 ms) but the rows of that
        page arrive from the server only later (~300 ms), so waiting for the page number reads the
        previous page's rows again and loses the new page. Waits for the ROWS to change, then for them
        to stop changing for 0.3 s. If two pages have the very same rows text, a moved page number is
        accepted instead.

        rows_text   - returns the table body text now
        active_page - returns the active page number/text now
        """
        try:
            self.wait_until(lambda: rows_text() not in ("", before_rows), timeout_ms=max(timeout, 10000), interval_ms=100)
        except AssertionError:
            if active_page() == before_page:
                raise

        last = [rows_text(), time.time()]

        def settled() -> bool:
            now_text = rows_text()
            if now_text != last[0]:
                last[0], last[1] = now_text, time.time()
                return False
            return time.time() - last[1] >= 0.3

        self.wait_until(settled, timeout_ms=min(max(timeout, 3000), 5000), interval_ms=100)

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

            sleep(1)

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

            # The Service List table's own pager (same one click_next / click_previous use);
            # the generic selectors are only a fallback for older layouts.
            pagination = self.page.locator("div.pagination ngb-pagination ul.pagination").first
            if pagination.count() == 0:
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
                    active = pagination.locator("li.page-item.active a.page-link").first
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
                """The whole table body text (all rows of the page shown)."""
                try:
                    return self._clean(table.locator("tbody").first.inner_text())
                except Exception:
                    return ""

            def wait_for_page_change(before_page: int | None, before_fp: str):
                # Wait for the new page's ROWS - the page number changes before they arrive
                self._wait_for_page_rows(first_row_fingerprint, current_page_number, before_fp, before_page, timeout)

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
                    wait_for_page_change(before_page, before_fp)

            def goto_page_one():
                """Jump straight to page 1 via its page link; fall back to clicking Previous."""
                if pagination.count() == 0 or current_page_number() == 1:
                    return

                first_link = pagination.locator(
                    "li.page-item a.page-link",
                    has_text=re.compile(r"^\s*1\s*$")
                ).first

                if first_link.count() > 0:
                    before_page = current_page_number()
                    before_fp = first_row_fingerprint()
                    first_link.click(force=True)
                    wait_for_page_change(before_page, before_fp)
                    return

                goto_first_page()

            def goto_next_page() -> bool:
                """Click Next and wait for the new page. False when already on the last page."""
                n = next_btn()
                if n is None or n.count() == 0 or is_disabled(n):
                    return False

                before_page = current_page_number()
                before_fp = first_row_fingerprint()

                n.click(force=True)
                wait_for_page_change(before_page, before_fp)
                return True

            def row_service_names(row) -> list[str]:
                """The Name cell's text, plus its title attribute(s) in case the shown text is cut."""
                cells = row.locator("td")
                if cells.count() <= 1:
                    return [self._clean(row.inner_text())]

                cell = cells.nth(1)
                names = [self._clean(cell.inner_text())]

                for el in [cell] + [cell.locator("[title]").nth(i) for i in range(cell.locator("[title]").count())]:
                    title = self._clean(el.get_attribute("title") or "")
                    if title:
                        names.append(title)

                return names

            def find_exact_on_current_page(name: str):
                rows = get_rows()
                for i in range(rows.count()):
                    row = rows.nth(i)
                    if any(n.lower() == name.lower() for n in row_service_names(row)):
                        return row
                return None

            def find_exact_across_pages(name: str):
                """Walk every page from page 1 and return the row whose Name is exactly 'name'."""
                goto_page_one()
                for _ in range(MAX_SCROLL_PAGES):
                    row = find_exact_on_current_page(name)
                    if row is not None:
                        return row
                    if not goto_next_page():
                        return None
                return None

            def names_containing_across_pages(part: str) -> list[str]:
                """Full names (Name column only) on every page that contain 'part'."""
                found = []
                goto_page_one()
                for _ in range(MAX_SCROLL_PAGES):
                    rows = get_rows()
                    for i in range(rows.count()):
                        shown = row_service_names(rows.nth(i))
                        if any(part.lower() in n.lower() for n in shown):
                            full = max(shown, key=len)
                            if full not in found:
                                found.append(full)
                    if not goto_next_page():
                        break
                return found

            target_row = None

            if service_name:
                # 1) exact Name match on ANY page wins - never settle for a partial match on an
                #    earlier page while the exact service sits on a later one.
                target_row = find_exact_across_pages(service_name)

                # 2) no exact match: accept a partial Name match only if exactly one service has it
                if target_row is None:
                    candidates = names_containing_across_pages(service_name)

                    if len(candidates) == 1:
                        target_row = find_exact_across_pages(candidates[0])
                    elif len(candidates) > 1:
                        raise AssertionError(
                            f"Service '{service_name}' was not found by exact name, and {len(candidates)} "
                            f"services contain it: {candidates}"
                        )

                if target_row is None:
                    raise AssertionError(f"Service '{service_name}' was not found across all pages.")

            else:
                goto_page_one()
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

            sleep(SLEEP * 5)

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

            # A filter with no match shows "No services found" instead of a table -> no rows
            no_services = self.page.get_by_text("No services found", exact=True).first
            expect(table.or_(no_services)).to_be_visible(timeout=timeout)
            if not table.is_visible() and no_services.is_visible():
                return []

            # The Service List table's own pager; the generic selectors are only a fallback
            pagination = self.page.locator("div.pagination ngb-pagination ul.pagination").first
            if pagination.count() == 0:
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
                """The whole table body text (all rows of the page shown)."""
                try:
                    return self._clean(table.locator("tbody").first.inner_text())
                except Exception:
                    return ""

            def wait_for_page_change(before_page: int | None, before_fp: str):
                # Wait for the new page's ROWS - the page number changes before they arrive
                self._wait_for_page_rows(first_row_fingerprint, current_page_number, before_fp, before_page, timeout)

            def current_page_number() -> int | None:
                try:
                    active = pagination.locator("li.page-item.active a.page-link").first

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
                    wait_for_page_change(before_page, before_fp)

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
                wait_for_page_change(before_page, before_fp)

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

    def get_events_list(self, max_pages: int | None = None, timeout: int = 15000) -> list[dict]:
        """
        Read the Events table of the Service List Events / Alarms panel.

        Only reads: the service must already be selected, the panel open and
        Faults type set to 'Events'.
        max_pages -> read at most this many pages (None = all pages). The panel lists the
                     newest events first, so max_pages=1 gives the most recent ones.

        Returns:
            list[dict] - one dict per event row, in table order (newest first), across the pages read.
            [] when the table has no events.
            Each dict (keys are the column headers; all values are str except 'Service affecting'):
            {
                "Message":             str,   # e.g. "Service status changed"
                "Severity":            str,   # e.g. "Info", "Clear", "Major"
                "Managed device":      str,   # e.g. "PL-2000ADS (172.16.40.15)/PL-2000ADS (172.16.40.19)"
                "Domain":              str,   # e.g. "OTN_Domain"
                "Category":            str,   # e.g. "OTN Service", "Device"
                "Source":              str,   # e.g. "Service: A-TO-B-PORT1-10G", "172.16.40.15 Port 1"
                "Detection Timestamp": str,   # "dd.mm.yyyy, HH:MM:SS", e.g. "10.11.2026, 17:45:54"
                "Creation Timestamp":  str,   # "dd.mm.yyyy, HH:MM:SS"
                "Service affecting":   bool,  # True = checkbox checked
                "Device type":         str,   # e.g. "PL-2000ADS"
            }
        """
        return self._read_faults_panel("Events", max_pages, timeout)

    def get_alarms_list(self, max_pages: int | None = None, timeout: int = 15000) -> list[dict]:
        """
        Read the Alarms table of the Service List Events / Alarms panel.

        Only reads: the service must already be selected, the panel open and
        Faults type set to 'Alarms'.
        max_pages -> read at most this many pages (None = all pages).

        Returns:
            list[dict] - one dict per alarm row, in table order, across the pages read.
            [] when the service has no alarms.
            Each dict (keys are the column headers; all values are str except 'Ack' and 'Service affecting'):
            {
                "Ack":                 bool,  # True = alarm acknowledged (checkbox checked)
                "Message":             str,   # e.g. "Power Supply Failure"
                "Severity":            str,   # e.g. "Major", "Minor", "Critical", "Clear"
                "Managed device":      str,   # e.g. "172.16.40.20"
                "Domain":              str,   # e.g. "OTN_Domain"
                "Category":            str,   # e.g. "Device"
                "Source":              str,   # e.g. "172.16.40.20 PSU 2"
                "Detection Timestamp": str,   # "dd.mm.yyyy, HH:MM:SS", e.g. "09.11.2026, 16:54:24"
                "Creation Timestamp":  str,   # "dd.mm.yyyy, HH:MM:SS"
                "Service affecting":   bool,  # True = checkbox checked
                "Device type":         str,   # e.g. "PL-2000ADS"
            }
        """
        return self._read_faults_panel("Alarms", max_pages, timeout)

    def _read_faults_panel(self, faults_type: str, max_pages: int | None, timeout: int) -> list[dict]:
        """
        Shared reader of the Service List Events / Alarms table for get_events_list / get_alarms_list.
        Does not select a service or change Faults type - it reads every page (or max_pages)
        of the table that is shown and returns one dict per row.
        Checkbox columns (Ack, Service affecting) are returned as bool.
        """

        try:
            faults = self.page.locator("app-faults-table").first
            expect(faults).to_be_visible(timeout=timeout)

            table = faults.locator("app-simple-table table").first
            tbody = table.locator("tbody").first
            expect(table.locator("thead").first).to_be_visible(timeout=timeout)

            # Make sure the table shown is the wanted one (it may still be re-rendering after a
            # Faults type change): Alarms start with an 'Ack' column, Events do not
            first_header = table.locator("thead th").first.locator("span.name").first
            want_ack = faults_type.lower() == "alarms"
            try:
                self.wait_until(lambda: (self._clean(first_header.inner_text()).lower() == "ack") == want_ack, timeout_ms=timeout, interval_ms=150)
            except AssertionError:
                raise AssertionError(f"the panel does not show the {faults_type} table - set Faults type to '{faults_type}' first.")

            # Scoped to the Events / Alarms table (the Service List table has its own pager)
            pagination = faults.locator("ul.pagination").first

            # Column headers: text columns, the 'Ack' / 'Service affecting' checkboxes, and the expand/edit icons (ignored)
            headers, kinds = [], []
            ths = table.locator("thead th")
            for i in range(ths.count()):
                th = ths.nth(i)
                cls = (th.get_attribute("class") or "").lower()
                name = th.locator("span.name").first
                header = self._clean(name.inner_text()) if name.count() else ""
                if not header or "expand" in cls or "edit" in cls:
                    headers.append("")
                    kinds.append("ignore")
                elif header.lower() in ("ack", "service affecting"):
                    headers.append(header)
                    kinds.append("checkbox")
                else:
                    headers.append(header)
                    kinds.append("text")

            # Whole page in one browser call: bool for the checkbox column, text otherwise
            read_page_js = """
                (tb, kinds) => Array.from(tb.querySelectorAll('tr')).map(tr =>
                    Array.from(tr.querySelectorAll('td')).slice(0, kinds.length).map((td, i) => {
                        if (kinds[i] === 'ignore') return null;
                        if (kinds[i] === 'checkbox') return td.querySelector('svg.checked') !== null;
                        const span = td.querySelector('span.name');
                        return (span || td).innerText;
                    }))
            """

            def read_page() -> list[dict]:
                rows = []
                for cells in tbody.evaluate(read_page_js, kinds):
                    row = {}
                    for i, value in enumerate(cells):
                        if kinds[i] == "ignore" or not headers[i]:
                            continue
                        row[headers[i]] = value if kinds[i] == "checkbox" else self._clean(value)
                    if any(v not in ("", False) for v in row.values()):
                        rows.append(row)
                return rows

            def pager_button(label: str):
                if pagination.count() == 0:
                    return None
                btn = pagination.locator(f"a.page-link[aria-label='{label}']").first
                return btn if btn.count() else None

            def is_disabled(btn) -> bool:
                if btn is None:
                    return True
                li = btn.locator("xpath=ancestor::li[1]").first
                return "disabled" in (li.get_attribute("class") or "").lower() or (btn.get_attribute("aria-disabled") or "").lower() == "true"

            def rows_text() -> str:
                try:
                    return self._clean(tbody.inner_text())
                except Exception:
                    return ""

            def click_and_wait(btn):
                # The pager highlights the new page number at once (~10 ms) but the rows of that page
                # arrive from the server only later (~300 ms). Wait for the ROWS to change - waiting for
                # the page number alone reads the previous page's rows again and loses the new page.
                def active_page() -> str:
                    active = pagination.locator("li.page-item.active").first
                    return self._clean(active.inner_text()) if active.count() else ""

                before, before_page = rows_text(), active_page()
                btn.click(force=True)
                try:
                    self.wait_until(lambda: rows_text() not in ("", before), timeout_ms=min(timeout, 10000), interval_ms=100)
                except AssertionError:
                    # Two pages with the very same rows text: accept it only if the page did move
                    if active_page() == before_page:
                        raise

                # ...and for the rows to stop changing (the table may render in more than one pass)
                last = [rows_text(), time.time()]

                def settled() -> bool:
                    now_text = rows_text()
                    if now_text != last[0]:
                        last[0], last[1] = now_text, time.time()
                        return False
                    return time.time() - last[1] >= 0.3

                self.wait_until(settled, timeout_ms=min(timeout, 5000), interval_ms=100)

            # Start from page 1 (the pager always shows a '1' link)
            if not is_disabled(pager_button("Previous")):
                first = pagination.locator("li.page-item a.page-link", has_text=re.compile(r"^\s*1\s*$")).first
                click_and_wait(first)

            events = read_page()
            pages_read = 1

            while max_pages is None or pages_read < max_pages:
                nxt = pager_button("Next")
                if is_disabled(nxt):
                    break
                click_and_wait(nxt)
                events += read_page()
                pages_read += 1

            return events

        except Exception as e:
            raise AssertionError(f"get_{faults_type.lower()}_list failed. Problem: {e}")

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
        """Select the PM period type and wait until LW shows the table of the new period type."""
        changed = self._clean(self.performance.get_pm_period_type()).lower() != self._clean(pm_period_type).lower()
        mark = self._performance_mark_table() if changed else ""
        self.performance.set_pm_period_type(pm_period_type)
        if changed:
            self._performance_wait_for_reload(mark)
        return True

    # ✅
    def performance_get_pm_period_type(self) -> str:
        return self.performance.get_pm_period_type()

    # ✅
    def performance_set_pm_type(self, pm_type: str) -> bool:
        """Select the PM type and wait until LW shows the table of the new PM type."""
        changed = self._clean(self.performance.get_pm_type()).lower() != self._clean(pm_type).lower()
        mark = self._performance_mark_table() if changed else ""
        self.performance.set_pm_type(pm_type)
        if changed:
            self._performance_wait_for_reload(mark)
        return True

    # ✅
    def performance_get_pm_type(self) -> str:
        return self.performance.get_pm_type()

    # Embedded Performance panel: how LW reloads the PM table
    # - Every filter change (PM type, PM period type, ports, dates...) makes LW remove the table, show
    #   'Loading data...' and build a new table ~2-3 s later; the rows then re-render once more ~1 s later.
    #   Reading before that returns the PREVIOUS filter's table - e.g. Native Signal rows while Egress PM
    #   is selected (same columns, so nothing looks wrong).
    # - The footer 'Refresh' button RESETS the PM type to 'Native Signal' (dates, devices, ports and
    #   PM period type are kept), so it must not be clicked before reading another PM type.

    def _performance_panel(self):
        return self.page.locator(".service-actionWrapper-modePanels app-performance-table").first

    def _performance_mark_table(self) -> str:
        """Mark the PM table body shown now (to tell later that LW replaced it). Returns the mark, '' if no table."""
        body = self._performance_panel().locator("table tbody").first
        if body.count() == 0:
            return ""
        mark = f"pm-{time.time_ns()}"
        try:
            body.evaluate("(tb, m) => tb.setAttribute('data-pm-read-mark', m)", mark)
        except Exception:
            return ""
        return mark

    def _performance_wait_for_reload(self, mark: str, timeout: int = 30000, start_timeout: int = 5000):
        """After a filter change: wait until LW removed the marked table (reload started), then for the new one."""
        if mark:
            marked = self.page.locator(f"[data-pm-read-mark='{mark}']")
            try:
                self.wait_until(lambda: marked.count() == 0, timeout_ms=start_timeout, interval_ms=100)
            except AssertionError:
                pass  # no reload (nothing to reload for this change) - the table shown is current
        self._performance_wait_for_table(timeout=timeout)

    def _performance_wait_for_table(self, timeout: int = 30000, settle_s: float = 1.5):
        """
        Wait until the embedded PM table is shown (no 'Loading data...') and its rows stopped changing
        for 'settle_s' seconds. Does NOT click Refresh (that would reset the PM type to Native Signal).
        """
        panel = self._performance_panel()
        expect(panel).to_be_visible(timeout=timeout)

        def loading() -> bool:
            return "loading data" in (panel.inner_text() or "").lower()

        def table_shown() -> bool:
            return not loading() and panel.locator("table tbody").count() > 0

        def body_text() -> str:
            try:
                return self._clean(panel.locator("table tbody").first.inner_text())
            except Exception:
                return ""

        self.wait_until(table_shown, timeout_ms=timeout, interval_ms=100)

        last = [body_text(), time.time()]

        def settled() -> bool:
            if not table_shown():
                last[1] = time.time()
                return False
            now_text = body_text()
            if now_text != last[0]:
                last[0], last[1] = now_text, time.time()
                return False
            return time.time() - last[1] >= settle_s

        self.wait_until(settled, timeout_ms=timeout, interval_ms=100)

    # ✅
    def performance_get_pm_table(self, all_pages: bool = False, timeout: int = 8000) -> list[dict]:
        """
        Read the embedded Performance PM table inside Service List.

        Works generically for any number of columns.

        If all_pages=True, reads all paginated PM table pages.

        Reads only after any reload in progress ended and the rows stopped changing, so the rows belong
        to the filters selected now. Refresh is NOT clicked: it resets the PM type to Native Signal.
        """

        try:
            self._performance_wait_for_table(timeout=max(timeout, 30000))

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

            def rows_text() -> str:
                try:
                    return self._clean(table.locator("tbody").first.inner_text())
                except Exception:
                    return ""

            def wait_for_next_page_rows(before_rows: str, before_page: str):
                """
                The pager highlights the new page number at once (~10 ms) but the rows of that page
                arrive from the server only later (~300 ms). Wait for the ROWS to change, then for them
                to stop changing - waiting for the page number alone reads the previous page's rows
                again and loses the new page.
                """
                try:
                    self.wait_until(lambda: rows_text() not in ("", before_rows), timeout_ms=max(timeout, 10000), interval_ms=100)
                except AssertionError:
                    # Two pages with the very same rows text: accept it only if the page did move
                    if active_page_text() == before_page:
                        raise

                last = [rows_text(), time.time()]

                def settled() -> bool:
                    now_text = rows_text()
                    if now_text != last[0]:
                        last[0], last[1] = now_text, time.time()
                        return False
                    return time.time() - last[1] >= 0.3

                self.wait_until(settled, timeout_ms=min(timeout, 5000), interval_ms=100)

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

            # Start from page 1 (no Refresh any more to reset the pager)
            if active_page_text() not in ("", "1"):
                first_link = self.page.locator(
                    ".service-actionWrapper-modePanels app-performance-table ul.pagination li.page-item a.page-link",
                    has_text=re.compile(r"^\s*1\s*$")
                ).first
                if first_link.count() > 0:
                    before_page, before_rows = active_page_text(), rows_text()
                    first_link.click(force=True)
                    wait_for_next_page_rows(before_rows, before_page)

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
                before_rows = rows_text()

                clicked = click_next_embedded()
                if not clicked:
                    break

                wait_for_next_page_rows(before_rows, before_page)

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
    def remove_service(self, row_index: int | None = None, service_name: str | None = None,
                       timeout: int = 8000, remove_timeout: int = 60000) -> bool:
        """
        Remove a service by GLOBAL row index across all pages, or by exact service name.

        row_index:
            1 = first service across all pages
            2 = second service across all pages

        service_name:
            exact service name to search across all pages

        timeout:
            UI waits (select the row, open the dialog, find the buttons).

        remove_timeout:
            How long LW may take to actually remove the service. After 'Remove' is confirmed the
            "Remove Service" dialog stays open - with its buttons disabled - while LW removes the
            service (measured 8-13 s), then the dialog and the row disappear together. When the
            last service is removed the table is replaced by "No services found".
        """

        requested = service_name
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

            # Never remove a different service than the one asked for
            if requested and service_name.lower() != self._clean(requested).lower():
                raise AssertionError(f"the selected row is '{service_name}', not '{requested}'")

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

            # The dialog says "Are you sure you want to remove <name>?" - make sure it is ours
            modal_text = self._clean(modal.inner_text())
            if service_name.lower() not in modal_text.lower():
                cancel_btn = modal.locator("button", has_text=re.compile(r"^\s*Cancel\s*$", re.IGNORECASE)).first
                if cancel_btn.count() > 0:
                    cancel_btn.click(force=True)
                raise AssertionError(f"the Remove Service dialog is not for '{service_name}': '{modal_text}'")

            confirm_btn = modal.locator(
                "button.btn-primary, "
                "button",
                has_text=re.compile(r"^\s*Remove\s*$", re.IGNORECASE)
            ).first

            expect(confirm_btn).to_be_visible(timeout=timeout)
            self.wait_until(lambda: confirm_btn.is_enabled(), timeout_ms=timeout, interval_ms=150)

            confirm_btn.click(force=True)

            # LW removes the service while the dialog stays open (buttons disabled) - wait for it to close
            try:
                self.wait_until(
                    lambda: modal.count() == 0 or not modal.is_visible(),
                    timeout_ms=remove_timeout,
                    interval_ms=300
                )
            except AssertionError:
                raise AssertionError(
                    f"the Remove Service dialog is still open {remove_timeout // 1000} s after confirming - "
                    f"LW did not finish removing '{service_name}'"
                )

            # Then the service must be gone: no row whose Name cell is the service
            # (the whole table is replaced by "No services found" after the last one)
            name_cells = self.page.locator("table tbody tr td:nth-child(2)")

            def service_gone() -> bool:
                names = [self._clean(t).lower() for t in name_cells.all_inner_texts()]
                return service_name.lower() not in names

            try:
                self.wait_until(service_gone, timeout_ms=timeout, interval_ms=300)
            except AssertionError:
                raise AssertionError(f"'{service_name}' is still in the Service List after the Remove Service dialog closed")

            return True

        except Exception as e:
            raise AssertionError(
                f"remove_service(row_index={row_index}, service_name={requested}) failed. Problem: {e}"
            )
    
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

        