"""
Created by: Yuval Dahan
Date: 30/07/2026
"""

from __future__ import annotations
from playwright.sync_api import Page, Frame, expect
from typing import List, Optional, Tuple, Union
from Utils.utils import refresh_page
import re
from time import time, sleep
from PL_Devices.PL_Pages.PL_main_screen_POM import PL_Main_Screen_POM
from PL_Devices.PL_Pages.PL_upper_panel import PL_Upper_Panel


class PL_PerformancePage:
    """
    PacketLight Left Menu -> Performance page object.
    """

    def __init__(self, page: Page):
        self.page = page
        self.main_screen = PL_Main_Screen_POM(page)
        self.upper_panel = self.main_screen.upper_panel

    # ==========================================================
    # Frame Helpers
    # ==========================================================

    def main_page_frame(self):
        return self.main_screen.main_page_frame()

    def pm_port_table_frame(self):
        return self.main_page_frame().frame_locator("iframe#PmPortTable, iframe[name='PmPortTable']")

    # ==========================================================
    # Navigation
    # ==========================================================

    # ✅
    def open_performance_tab(self):
        self.main_screen = PL_Main_Screen_POM(self.page)
        self.main_screen.click_Performance()

    # ✅
    def set_PM_Period(self, port_number, period, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Set the "PM Period:" dropdown (name='interval') on the Performance page of the given port.

        Args:
            port_number: Examples: 1, "1", "Port-1", "ETH1", "Uplink1"
            period: Option value ("Intervals", "Days") or its visible label ("15 Minutes", "Days")

        Returns:
            True on success, False otherwise.
        """
        sleep(2)
        desired = str(period).strip()

        def resolve_period_dd():
            candidates = [
                self.main_page_frame().locator("select[name='interval']").first,
                self.main_page_frame().frame_locator("iframe[name='pm_port'], iframe#pm_port").locator("select[name='interval']").first,
            ]

            for candidate in candidates:
                try:
                    if candidate.count() > 0 and candidate.is_visible():
                        return candidate
                except Exception:
                    continue

            return None

        for attempt in range(retries):
            try:
                if not self.main_screen.click_Performance(timeout=timeout):
                    raise AssertionError("click_Performance failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"click_port failed for {port_number}")

                period_dd = None
                step = 300
                loops = max(1, timeout // step)
                for _ in range(loops):
                    period_dd = resolve_period_dd()
                    if period_dd is not None:
                        break
                    self.page.wait_for_timeout(step)

                if period_dd is None:
                    raise AssertionError(
                        "select[name='interval'] not found directly in main_page nor "
                        "nested inside a 'pm_port' iframe"
                    )

                try:
                    period_dd.select_option(value=desired)
                except Exception:
                    period_dd.select_option(label=desired)

                return True

            except Exception as e:
                print(f"set_PM_Period failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return False
    
    # ✅
    def set_PM_Type(self, port_number, pm_type, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Set the "Type:" dropdown (name='type') on the Performance page of the given port.

        Args:
            port_number: Examples: 1, "1", "Port-1", "ETH1", "Uplink1"
            pm_type: Option value (e.g. "Section", "OpticalPm", "Line") or its visible
                     label (e.g. "Native Signal", "Optical Level", "OTU Section").
                     Available options are port/service dependent.

        Returns:
            True on success, False otherwise.
        """
        sleep(2)
        desired = str(pm_type).strip()

        def resolve_type_dd():
            candidates = [
                self.main_page_frame().locator("select[name='type']").first,
                self.main_page_frame().frame_locator("iframe[name='pm_port'], iframe#pm_port").locator("select[name='type']").first,
            ]

            for candidate in candidates:
                try:
                    if candidate.count() > 0 and candidate.is_visible():
                        return candidate
                except Exception:
                    continue

            return None

        for attempt in range(retries):
            try:
                if not self.main_screen.click_Performance(timeout=timeout):
                    raise AssertionError("click_Performance failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"click_port failed for {port_number}")

                type_dd = None
                step = 300
                loops = max(1, timeout // step)
                for _ in range(loops):
                    type_dd = resolve_type_dd()
                    if type_dd is not None:
                        break
                    self.page.wait_for_timeout(step)

                if type_dd is None:
                    raise AssertionError(
                        "select[name='type'] not found directly in main_page nor "
                        "nested inside a 'pm_port' iframe"
                    )

                try:
                    type_dd.select_option(value=desired)
                except Exception:
                    type_dd.select_option(label=desired)

                return True

            except Exception as e:
                print(f"set_PM_Type failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return False

    # ✅
    def get_device_pm_type_current_dropdown_options(self, port_number, retries: int = 5, timeout: int = 10_000) -> List[Tuple[str, str]]:
        """
        Returns the Type dropdown's (name='type') currently available options on the
        Performance page of the given port, as labels.

        Returns:
            List of labels, e.g.:
                [Native Signal, Layer 2 PM, Optical Level]
            Empty list if the dropdown could not be read.
        """
        sleep(2)

        def resolve_type_dd():
            candidates = [
                self.main_page_frame().locator("select[name='type']").first,
                self.main_page_frame().frame_locator("iframe[name='pm_port'], iframe#pm_port").locator("select[name='type']").first,
            ]

            for candidate in candidates:
                try:
                    if candidate.count() > 0 and candidate.is_visible():
                        return candidate
                except Exception:
                    continue

            return None

        for attempt in range(retries):
            try:
                if not self.main_screen.click_Performance(timeout=timeout):
                    raise AssertionError("click_Performance failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"click_port failed for {port_number}")

                type_dd = None
                step = 300
                loops = max(1, timeout // step)
                for _ in range(loops):
                    type_dd = resolve_type_dd()
                    if type_dd is not None:
                        break
                    self.page.wait_for_timeout(step)

                if type_dd is None:
                    raise AssertionError(
                        "select[name='type'] not found directly in main_page nor "
                        "nested inside a 'pm_port' iframe"
                    )

                options = type_dd.locator("option")
                count = options.count()

                result = []
                for i in range(count):
                    opt = options.nth(i)
                    value = (opt.get_attribute("value") or "").strip()
                    label = (opt.inner_text() or "").strip()
                    # result.append((value, label))
                    result.append(label)

                return result

            except Exception as e:
                print(f"get_device_pm_type_current_dropdown_options failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return []

    # ✅
    def click_on_Get_PM(self, port_number, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Click the "Get PM" button on the Performance page of the given port, applying the
        currently selected PM Period / Type.

        Returns:
            True on success, False otherwise.
        """
        sleep(2)

        def resolve_pm_form_ctx():
            candidates = [
                self.main_page_frame(),
                self.main_page_frame().frame_locator("iframe[name='pm_port'], iframe#pm_port"),
            ]

            for ctx in candidates:
                try:
                    btn = ctx.locator("input[name='get_button']").first
                    if btn.count() > 0 and btn.is_visible():
                        return ctx
                except Exception:
                    continue

            return None

        for attempt in range(retries):
            try:
                if not self.main_screen.click_Performance(timeout=timeout):
                    raise AssertionError("click_Performance failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"click_port failed for {port_number}")

                ctx = None
                step = 300
                loops = max(1, timeout // step)
                for _ in range(loops):
                    ctx = resolve_pm_form_ctx()
                    if ctx is not None:
                        break
                    self.page.wait_for_timeout(step)

                if ctx is None:
                    raise AssertionError(
                        "input[name='get_button'] not found directly in main_page nor "
                        "nested inside a 'pm_port' iframe"
                    )

                get_btn = ctx.locator("input[name='get_button']").first
                expect(get_btn).to_be_visible(timeout=timeout)
                expect(get_btn).to_be_enabled(timeout=timeout)

                get_btn.scroll_into_view_if_needed()
                get_btn.click(force=True, timeout=timeout)

                self.page.wait_for_timeout(1000)
                expect(ctx.locator("form[name='pm_form']").first).to_be_visible(timeout=timeout)

                return True

            except Exception as e:
                print(f"click_on_Get_PM failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return False

    # ✅
    def get_PM_table(self, port_number, retries: int = 5, timeout: int = 10_000) -> List[dict]:
        """
        Returns the PM table (inside the PmPortTable iframe) of the given port as a
        list of header->value dicts, read from the table's OWN live header row
        (#thead) instead of assuming a fixed column schema.

        Column count and names are dynamic -- they vary by product AND by the
        currently selected PM Type, e.g.:
            "Native Signal": Interval, Errors, Errored Seconds, Severely Errored
                Seconds, Unavailable Seconds, Valid
            "Layer 2 PM":    Interval, RX Bytes, RX Packets, RX Bad Packets,
                TX Bytes, TX Packets, TX Bad Packets, Valid
            "Optical Level": Interval, Rx Level dBm, Tx Level dBm, Min Rx dBm,
                Max Rx dBm, Min Tx dBm, Max Tx dBm  (no Valid column at all)
        so there is no fixed schema to hardcode against. The trailing "Reset"
        button column has no header text and is dropped naturally, since only
        cells up to the header count are read.

        Different products also nest the PmPortTable iframe at different frame
        depths -- e.g. PL-2000 has it directly inside main_page, while PL-8000M
        (and other products sharing the same page template) nest it one level
        deeper: main_page -> pm_port iframe (Pm_Port_Pm.asp) -> PmPortTable
        iframe. This tries each known location in order and uses whichever one
        actually resolves.
        """
        sleep(2)

        def resolve_ctx():
            candidates = [
                self.main_page_frame().frame_locator("iframe#PmPortTable, iframe[name='PmPortTable']"),
                self.main_page_frame().frame_locator("iframe[name='pm_port'], iframe#pm_port")
                    .frame_locator("iframe#PmPortTable, iframe[name='PmPortTable']"),
            ]

            for ctx in candidates:
                try:
                    tbody = ctx.locator("#tbody").first
                    if tbody.count() > 0 and tbody.is_visible():
                        return ctx
                except Exception:
                    continue

            return None

        for attempt in range(retries):
            try:
                if not self.main_screen.click_Performance(timeout=timeout):
                    raise AssertionError("click_Performance failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"click_port failed for {port_number}")

                ctx = None
                step = 300
                loops = max(1, timeout // step)
                for _ in range(loops):
                    ctx = resolve_ctx()
                    if ctx is not None:
                        break
                    self.page.wait_for_timeout(step)

                if ctx is None:
                    raise AssertionError(
                        "#tbody not found directly in PmPortTable nor nested inside "
                        "a 'pm_port' iframe"
                    )

                header_cells = ctx.locator("#thead th")
                headers = []
                for i in range(header_cells.count()):
                    text = header_cells.nth(i).inner_text().replace("\xa0", " ").strip()
                    if text:
                        headers.append(text)

                if not headers:
                    raise AssertionError("PM table headers (#thead th) were not found.")

                rows = ctx.locator("#tbody").first.locator("tr")
                row_count = rows.count()

                pm_table = []

                for i in range(row_count):
                    row = rows.nth(i)
                    cells = row.locator("td")
                    cell_count = cells.count()

                    row_dict = {}
                    for j, header in enumerate(headers):
                        value = cells.nth(j).inner_text().replace("\xa0", " ").strip() if j < cell_count else ""
                        row_dict[header] = value

                    if any(row_dict.values()):
                        pm_table.append(row_dict)

                return pm_table

            except Exception as e:
                print(f"get_PM_table failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return []

    # ✅
    def click_reset_on_interval(self, port_number, interval_index, action_dismiss: bool = False,
                                 retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
        """
        Click the "Reset" button of one interval row in the PM table.

        Args:
            port_number: Examples: 1, "1", "Port-1"
            interval_index: 0 for "Current", 1, 2, ... for the historical rows below it.
            action_dismiss:
                False -> accept any confirmation dialog that appears
                True  -> dismiss it

        Returns:
            (success, dialog_text)
        """

        def arm_dialog_capture_once(holder: dict):
            def _handler(d):
                try:
                    holder["text"] = (d.message or "").strip()
                except Exception:
                    holder["text"] = ""
                try:
                    d.dismiss() if action_dismiss else d.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

        def wait_for_dialog_text(holder: dict, ms: int = 2000) -> str:
            step = 50
            loops = max(1, ms // step)
            for _ in range(loops):
                if holder.get("text") is not None:
                    return holder.get("text") or ""
                self.page.wait_for_timeout(step)
            return holder.get("text") or ""

        sleep(2)
        for attempt in range(retries):
            try:
                if not self.main_screen.click_Performance(timeout=timeout):
                    raise AssertionError("click_Performance failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"click_port failed for {port_number}")

                reset_btn = self.pm_port_table_frame().locator(f"input[name='Interval-{interval_index}']").first
                expect(reset_btn).to_be_visible(timeout=timeout)

                dlg_holder = {"text": None}
                arm_dialog_capture_once(dlg_holder)

                reset_btn.scroll_into_view_if_needed()
                reset_btn.click(force=True, timeout=timeout)

                self.page.wait_for_timeout(1000)
                dialog_text = wait_for_dialog_text(dlg_holder)

                return True, dialog_text

            except Exception as e:
                print(f"click_reset_on_interval failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return False, ""

    # ✅
    def reset_port_PM(self, port_number, action_dismiss: bool = False,
                       retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
        """
        Click "Reset Port PM" on the Performance page of the given port.

        Returns:
            (success, dialog_text)
        """

        def arm_dialog_capture_once(holder: dict):
            def _handler(d):
                try:
                    holder["text"] = (d.message or "").strip()
                except Exception:
                    holder["text"] = ""
                try:
                    d.dismiss() if action_dismiss else d.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

        def wait_for_dialog_text(holder: dict, ms: int = 2000) -> str:
            step = 50
            loops = max(1, ms // step)
            for _ in range(loops):
                if holder.get("text") is not None:
                    return holder.get("text") or ""
                self.page.wait_for_timeout(step)
            return holder.get("text") or ""

        sleep(2)
        for attempt in range(retries):
            try:
                if not self.main_screen.click_Performance(timeout=timeout):
                    raise AssertionError("click_Performance failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"click_port failed for {port_number}")

                reset_btn = self.main_page_frame().locator("form[name='reset_pm_form'] input[name='B1']").first
                expect(reset_btn).to_be_visible(timeout=timeout)

                dlg_holder = {"text": None}
                arm_dialog_capture_once(dlg_holder)

                reset_btn.scroll_into_view_if_needed()
                reset_btn.click(force=True, timeout=timeout)

                self.page.wait_for_timeout(1000)
                dialog_text = wait_for_dialog_text(dlg_holder)

                return True, dialog_text

            except Exception as e:
                print(f"reset_port_PM failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return False, ""

    # ✅
    def reset_all_ports_PM(self, port_number, action_dismiss: bool = False,
                            retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
        """
        Click "Reset All Ports PM" (resets PM counters on every port of the device).
        The button itself is global; port_number is only used to open the Performance
        page it lives on.

        Returns:
            (success, dialog_text)
        """

        def arm_dialog_capture_once(holder: dict):
            def _handler(d):
                try:
                    holder["text"] = (d.message or "").strip()
                except Exception:
                    holder["text"] = ""
                try:
                    d.dismiss() if action_dismiss else d.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

        def wait_for_dialog_text(holder: dict, ms: int = 2000) -> str:
            step = 50
            loops = max(1, ms // step)
            for _ in range(loops):
                if holder.get("text") is not None:
                    return holder.get("text") or ""
                self.page.wait_for_timeout(step)
            return holder.get("text") or ""

        def wait_modal_disappears():
            for _ in range(25):
                try:
                    modal = self.page.locator("#modalWait").first
                    modal.wait_for(state="hidden", timeout=1000)
                    return
                except Exception:
                    self.page.wait_for_timeout(500)

        sleep(2)
        for attempt in range(retries):
            try:
                if not self.main_screen.click_Performance(timeout=timeout):
                    raise AssertionError("click_Performance failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"click_port failed for {port_number}")

                reset_all_btn = self.main_page_frame().locator("form[name='reset_all_pm_form'] input[name='B1']").first
                expect(reset_all_btn).to_be_visible(timeout=timeout)

                dlg_holder = {"text": None}
                arm_dialog_capture_once(dlg_holder)

                reset_all_btn.scroll_into_view_if_needed()
                reset_all_btn.click(force=True, timeout=timeout)

                wait_modal_disappears()
                dialog_text = wait_for_dialog_text(dlg_holder)

                return True, dialog_text

            except Exception as e:
                print(f"reset_all_ports_PM failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return False, ""

    # ✅
    def click_reload_button(self) -> bool:
        refresh_page(self.page)
