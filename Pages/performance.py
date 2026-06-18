'''
Created by: Yuval Dahan
Date: 06/03/2026
'''

from playwright.sync_api import Page, expect
from typing import Callable
import time
import re
from time import sleep
from datetime import datetime
from pathlib import Path
from Utils.utils import create_frame_html, refresh_page


MAX_SCROLL_PAGES = 200
SLEEP = 0.2


class Performance:
    """
    Performance page – 
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
        root = "pass"
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
    
    # =========================
    # Display
    # =========================

    def set_display(self, display_value: str, timeout: int = 8000) -> bool:
        pass

    def get_display(self, timeout: int = 8000) -> str:
        pass

    # =========================
    # Period start
    # =========================

    # ✅
    def set_period_start(self, period_start: str, timeout: int = 8000) -> bool:
        """
        Set Period start.

        Example:
            set_period_start("07/06/2026 00:00")
        """

        try:
            period_start = (period_start or "").strip()
            if not period_start:
                raise ValueError("period_start is empty")

            date_input = self.page.locator(
                "#datepickerFrom input[name='periodStart'], "
                "#datepickerFrom input[formcontrolname='periodStart'], "
                "input[name='periodStart'], "
                "input[formcontrolname='periodStart']"
            ).first

            expect(date_input).to_be_visible(timeout=timeout)
            expect(date_input).to_be_enabled(timeout=timeout)

            current_value = self._clean(date_input.input_value())
            if current_value == period_start:
                return True

            # input has onkeydown=false, so use JS instead of typing
            date_input.evaluate(
                """(el, value) => {
                    el.value = value;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new Event('blur', { bubbles: true }));
                }""",
                period_start
            )

            self.wait_until(
                lambda: self._clean(date_input.input_value()) == period_start,
                timeout_ms=timeout,
                interval_ms=150
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"set_period_start failed. Problem: {e}")
    
    # ✅
    def get_period_start(self, timeout: int = 8000) -> str:
        """
        Get Period start value.
        """
        try:
            date_input = self.page.locator(
                "#datepickerFrom input[name='periodStart'], "
                "#datepickerFrom input[formcontrolname='periodStart'], "
                "input[name='periodStart'], "
                "input[formcontrolname='periodStart']"
            ).first

            expect(date_input).to_be_visible(timeout=timeout)

            return self._clean(date_input.input_value())

        except Exception as e:
            raise AssertionError(f"get_period_start failed. Problem: {e}")
    
    # =========================
    # Period end
    # =========================

    # ✅
    def set_period_end(self, period_end: str, timeout: int = 8000) -> bool:
        """
        Set Period end.

        Example:
            set_period_end("08/06/2026 23:59")
        """

        try:
            period_end = (period_end or "").strip()
            if not period_end:
                raise ValueError("period_end is empty")

            date_input = self.page.locator(
                "#datepickerTo input[name='periodEnd'], "
                "#datepickerTo input[formcontrolname='periodEnd'], "
                "input[name='periodEnd'], "
                "input[formcontrolname='periodEnd']"
            ).first

            expect(date_input).to_be_visible(timeout=timeout)
            expect(date_input).to_be_enabled(timeout=timeout)

            current_value = self._clean(date_input.input_value())
            if current_value == period_end:
                return True

            date_input.evaluate(
                """(el, value) => {
                    el.value = value;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new Event('blur', { bubbles: true }));
                }""",
                period_end
            )

            self.wait_until(
                lambda: self._clean(date_input.input_value()) == period_end,
                timeout_ms=timeout,
                interval_ms=150
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"set_period_end failed. Problem: {e}")

    # ✅
    def get_period_end(self, timeout: int = 8000) -> str:
        """
        Get Period end value.
        """
        try:
            date_input = self.page.locator(
                "#datepickerTo input[name='periodEnd'], "
                "#datepickerTo input[formcontrolname='periodEnd'], "
                "input[name='periodEnd'], "
                "input[formcontrolname='periodEnd']"
            ).first

            expect(date_input).to_be_visible(timeout=timeout)

            return self._clean(date_input.input_value())

        except Exception as e:
            raise AssertionError(f"get_period_end failed. Problem: {e}")


    # =========================
    # Device
    # =========================

    # ✅
    def set_device(self, device: str, timeout: int = 8000) -> bool:
        """
        Select Device from the Performance Device dropdown.
        """

        try:
            sleep(5)

            device = (device or "").strip()
            if not device:
                raise ValueError("device is empty")

            dropdown = self.page.locator("app-dropdown[formcontrolname='deviceA'], "
                "app-dropdown:has(.label:text-is('Device'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            current = self.get_device(timeout=timeout)
            if current.lower() == device.lower():
                return True

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)

            btn.click(force=True)

            menu = dropdown.locator(
                "div.dropdown-menu[data-label='Device'], "
                "div.dropdown-menu"
            ).first

            expect(menu).to_be_visible(timeout=timeout)

            item = menu.locator("li.dropdown-item", has_text=re.compile(rf"^\s*{re.escape(device)}\s*$", re.IGNORECASE)).first

            if item.count() == 0:
                options = [
                    self._clean(x)
                    for x in menu.locator("li.dropdown-item").all_inner_texts()
                    if self._clean(x)
                ]
                raise AssertionError(
                    f"Device '{device}' not found. Available: {options}"
                )

            item.scroll_into_view_if_needed()
            item.click(force=True)

            self.wait_until(
                lambda: self.get_device(timeout=timeout).lower() == device.lower(),
                timeout_ms=timeout,
                interval_ms=150
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"set_device('{device}') failed. Problem: {e}")

    # ✅
    def get_device(self, timeout: int = 8000) -> str:
        """
        Get selected Device value.
        """

        try:
            dropdown = self.page.locator(
                "app-dropdown[formcontrolname='deviceA'], "
                "app-dropdown:has(.label:text-is('Device'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            selected = dropdown.locator(".selected-view span").first
            expect(selected).to_be_visible(timeout=timeout)

            return self._clean(selected.inner_text())

        except Exception as e:
            raise AssertionError(f"get_device failed. Problem: {e}")

    # =========================
    # Port
    # =========================

    # ✅
    def set_port(self, port: str, timeout: int = 8000) -> bool:
        """
        Select Port from the Performance Port dropdown.
        """

        try:
            port = (port or "").strip()
            if not port:
                raise ValueError("port is empty")

            dropdown = self.page.locator(
                "app-dropdown[formcontrolname='portA'], "
                "app-dropdown:has(.label:text-is('Port'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            current = self.get_port(timeout=timeout)
            if current.lower() == port.lower():
                return True

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)

            btn.click(force=True)

            menu = dropdown.locator("div.dropdown-menu[data-label='Port'], div.dropdown-menu").first

            expect(menu).to_be_visible(timeout=timeout)

            item = menu.locator("li.dropdown-item", has_text=re.compile(rf"^\s*{re.escape(port)}\s*$", re.IGNORECASE)).first

            if item.count() == 0:
                options = [
                    self._clean(x)
                    for x in menu.locator("li.dropdown-item").all_inner_texts()
                    if self._clean(x)
                ]
                raise AssertionError(f"Port '{port}' not found. Available: {options}")

            item.scroll_into_view_if_needed()
            item.click(force=True)

            self.wait_until(
                lambda: self.get_port(timeout=timeout).lower() == port.lower(),
                timeout_ms=timeout,
                interval_ms=150
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"set_port('{port}') failed. Problem: {e}")

    # ✅
    def get_port(self, timeout: int = 8000) -> str:
        """
        Get selected Port value.
        """

        try:
            dropdown = self.page.locator(
                "app-dropdown[formcontrolname='portA'], "
                "app-dropdown:has(.label:text-is('Port'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            selected = dropdown.locator(".selected-view span").first
            expect(selected).to_be_visible(timeout=timeout)

            return self._clean(selected.inner_text())

        except Exception as e:
            raise AssertionError(f"get_port failed. Problem: {e}")

    # =========================
    # PM period type
    # =========================

    # ✅
    def set_pm_period_type(self, pm_period_type: str, timeout: int = 8000) -> bool:
        """
        Select PM period type.
        """

        try:
            pm_period_type = (pm_period_type or "").strip()
            if not pm_period_type:
                raise ValueError("pm_period_type is empty")

            dropdown = self.page.locator(
                "app-dropdown[formcontrolname='pmPeriodType'], "
                "app-dropdown[label='PM period type'], "
                "app-dropdown:has(.label:text-is('PM period type'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            current = self.get_pm_period_type(timeout=timeout)
            if current.lower() == pm_period_type.lower():
                return True

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)

            btn.click(force=True)

            menu = dropdown.locator(
                "div.dropdown-menu[data-label='PM period type'], "
                "div.dropdown-menu"
            ).first

            expect(menu).to_be_visible(timeout=timeout)

            item = menu.locator("li.dropdown-item", has_text=re.compile(rf"^\s*{re.escape(pm_period_type)}\s*$", re.IGNORECASE)).first

            if item.count() == 0:
                options = [
                    self._clean(x)
                    for x in menu.locator("li.dropdown-item").all_inner_texts()
                    if self._clean(x)
                ]
                raise AssertionError(
                    f"PM period type '{pm_period_type}' not found. Available: {options}"
                )

            item.scroll_into_view_if_needed()
            item.click(force=True)

            self.wait_until(
                lambda: self.get_pm_period_type(timeout=timeout).lower() == pm_period_type.lower(),
                timeout_ms=timeout,
                interval_ms=150
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"set_pm_period_type('{pm_period_type}') failed. Problem: {e}")

    # ✅
    def get_pm_period_type(self, timeout: int = 8000) -> str:
        """
        Get selected PM period type.
        """

        try:
            dropdown = self.page.locator(
                "app-dropdown[formcontrolname='pmPeriodType'], "
                "app-dropdown[label='PM period type'], "
                "app-dropdown:has(.label:text-is('PM period type'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            selected = dropdown.locator(".selected-view span").first
            expect(selected).to_be_visible(timeout=timeout)

            return self._clean(selected.inner_text())

        except Exception as e:
            raise AssertionError(f"get_pm_period_type failed. Problem: {e}")

    # =========================
    # PM type
    # =========================
 
    # ✅
    def set_pm_type(self, pm_type: str, timeout: int = 8000) -> bool:
        """
        Select PM type.
        """

        try:
            pm_type = (pm_type or "").strip()
            if not pm_type:
                raise ValueError("pm_type is empty")

            dropdown = self.page.locator(
                "app-dropdown[formcontrolname='pmType'], "
                "app-dropdown[label='PM type'], "
                "app-dropdown:has(.label:text-is('PM type'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            current = self.get_pm_type(timeout=timeout)
            if current.lower() == pm_type.lower():
                return True

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first

            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)

            btn.click(force=True)

            menu = dropdown.locator("div.dropdown-menu[data-label='PM type'], div.dropdown-menu").first

            expect(menu).to_be_visible(timeout=timeout)

            item = menu.locator("li.dropdown-item",has_text=re.compile(rf"^\s*{re.escape(pm_type)}\s*$", re.IGNORECASE)).first

            if item.count() == 0:
                options = [
                    self._clean(x)
                    for x in menu.locator("li.dropdown-item").all_inner_texts()
                    if self._clean(x)
                ]
                raise AssertionError(f"PM type '{pm_type}' not found. Available: {options}")

            item.scroll_into_view_if_needed()
            item.click(force=True)

            self.wait_until(
                lambda: self.get_pm_type(timeout=timeout).lower() == pm_type.lower(),
                timeout_ms=timeout,
                interval_ms=150
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"set_pm_type('{pm_type}') failed. Problem: {e}")

    # ✅
    def get_pm_type(self, timeout: int = 8000) -> str:
        """
        Get selected PM type.
        """

        try:
            dropdown = self.page.locator(
                "app-dropdown[formcontrolname='pmType'], "
                "app-dropdown[label='PM type'], "
                "app-dropdown:has(.label:text-is('PM type'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout)

            selected = dropdown.locator(".selected-view span").first
            expect(selected).to_be_visible(timeout=timeout)

            return self._clean(selected.inner_text())

        except Exception as e:
            raise AssertionError(f"get_pm_type failed. Problem: {e}")

    # =========================
    # PM Table
    # =========================

    # ✅
    def get_pm_table(self, all_pages: bool = False, timeout: int = 8000) -> list[dict]:
        """
        Generic PM table reader.
        Works with any number of PM fields/columns.
        """

        try:
            table = self.page.locator(
                "app-performance-table app-universal-table table, "
                "app-universal-table table, "
                ".universal-table-container table, "
                "table"
            ).first

            expect(table).to_be_visible(timeout=timeout)

            def read_current_page() -> list[dict]:
                # Read only real data headers, ignore expand/edit icon columns
                header_cells = table.locator(
                    "thead th:not(.expand):not(.edit)"
                )

                headers = []
                for i in range(header_cells.count()):
                    header_text = self._clean(header_cells.nth(i).inner_text())
                    if header_text:
                        headers.append(header_text)

                if not headers:
                    raise AssertionError("PM table headers were not found.")

                rows = table.locator("tbody tr")
                page_data = []

                for i in range(rows.count()):
                    row = rows.nth(i)
                    cells = row.locator("td")

                    row_dict = {}

                    for j, header in enumerate(headers):
                        if j < cells.count():
                            value = self._clean(cells.nth(j).inner_text())
                        else:
                            value = ""

                        row_dict[header] = value

                    if any(v for v in row_dict.values()):
                        page_data.append(row_dict)

                return page_data

            def first_row_fingerprint() -> str:
                first_row = table.locator("tbody tr").first
                if first_row.count() == 0:
                    return ""
                return self._clean(first_row.inner_text())

            def active_page_text() -> str:
                active = self.page.locator(
                    "div.pagination ngb-pagination ul.pagination li.page-item.active a.page-link, "
                    "ul.pagination li.page-item.active a.page-link"
                ).first

                if active.count() == 0:
                    return ""

                return self._clean(active.inner_text())

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

                pager = self.page.locator(
                    "div.pagination ngb-pagination ul.pagination, "
                    "ul.pagination"
                ).first

                if pager.count() == 0:
                    break

                before_page = active_page_text()
                before_fp = first_row_fingerprint()

                clicked = self.click_next(timeout=timeout)
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
            raise AssertionError(f"get_pm_table failed. Problem: {e}")

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
    # Refresh
    # =========================

    # ✅
    def refresh_pm_table(self, timeout: int = 8000) -> bool:
        """
        Click Refresh and wait until the PM table reloads.
        """

        try:
            table = self.page.locator(
                "app-universal-table table, "
                ".universal-table-container table, "
                "table"
            ).first

            expect(table).to_be_visible(timeout=timeout)

            before_fp = ""
            first_row = table.locator("tbody tr").first
            if first_row.count() > 0:
                before_fp = self._clean(first_row.inner_text())

            refresh_btn = self.page.locator("button.btn-primary", has_text=re.compile(r"^\s*Refresh\s*$", re.IGNORECASE)).first

            if refresh_btn.count() == 0:
                refresh_btn = self.page.locator(
                    "button",
                    has_text=re.compile(r"^\s*Refresh\s*$", re.IGNORECASE)
                ).first

            expect(refresh_btn).to_be_visible(timeout=timeout)
            expect(refresh_btn).to_be_enabled(timeout=timeout)

            refresh_btn.click(force=True)

            # Wait until table is visible again after refresh/re-render
            expect(table).to_be_visible(timeout=timeout)

            # If data changes/reloads, this catches it.
            # If data stays identical, visibility check above is still enough.
            self.wait_until(
                lambda: (
                    table.locator("tbody tr").count() > 0
                    and (
                        not before_fp
                        or self._clean(table.locator("tbody tr").first.inner_text()) != ""
                    )
                ),
                timeout_ms=timeout,
                interval_ms=200
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"refresh_pm_table failed. Problem: {e}")

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