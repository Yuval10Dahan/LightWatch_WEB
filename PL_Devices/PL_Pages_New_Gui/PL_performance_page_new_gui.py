"""
Created by: Yuval Dahan
Date: 03/08/2026
"""

from __future__ import annotations
from playwright.sync_api import Page, Frame, expect
from typing import List, Optional, Tuple, Union
from Utils.utils import refresh_page
import re
from time import time, sleep
from PL_Devices.PL_Pages_New_Gui.PL_main_screen_POM_new_gui import PL_Main_Screen_POM
from PL_Devices.PL_Pages_New_Gui.PL_upper_panel_new_gui import PL_Upper_Panel


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

    # ✅
    def main_page_frame(self):
        return self.main_screen.main_page_frame()

    # ✅
    def pm_port_frame(self):
        return self.main_page_frame().frame_locator("iframe[name='pm_port'], iframe#pm_port")

    # ✅
    def pm_port_table_frame(self):
        return self.pm_port_frame().frame_locator("iframe#PmPortTable, iframe[name='PmPortTable']")

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

        for attempt in range(retries):
            try:
                if not self.main_screen.click_Performance(timeout=timeout):
                    raise AssertionError("click_Performance failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"click_port failed for {port_number}")

                period_dd = self.pm_port_frame().locator("select[name='interval']").first
                expect(period_dd).to_be_visible(timeout=timeout)

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

        def resolve_type_option(ms: int):
            """
            Poll for the select's <option> list to actually contain `desired` (by
            value or label), re-deriving pm_port_frame() fresh on every iteration.

            select_option() alone isn't enough here: after click_port() the pm_port
            iframe (Pm_Port_Pm.asp) can take several seconds to settle into its
            final, service-dependent option set, and a locator resolved too early
            can end up pointed at a select mid-reload. select_option() with no
            explicit timeout then retries against that stale/detaching element for
            the full 30s Playwright default ("did not find some options") instead
            of failing fast or catching the frame once it re-settles -- same iframe
            reload lag as PL_Upper_PanelNewGui.click_fault().

            Returns:
                (type_dd locator, matched option VALUE)
            """
            step = 300
            loops = max(1, ms // step)
            last_options = []

            for _ in range(loops):
                try:
                    type_dd = self.pm_port_frame().locator("select[name='type']").first
                    if type_dd.count() > 0 and type_dd.is_visible():
                        opts = type_dd.locator("option")
                        n = opts.count()
                        last_options = []
                        for i in range(n):
                            opt = opts.nth(i)
                            val = (opt.get_attribute("value") or "").strip()
                            label = (opt.inner_text() or "").strip()
                            last_options.append((val, label))

                        for val, label in last_options:
                            if desired == val or desired == label:
                                return type_dd, val
                except Exception:
                    pass

                self.page.wait_for_timeout(step)

            raise AssertionError(
                f"PM Type '{desired}' not found in Type dropdown (available: {last_options})"
            )

        for attempt in range(retries):
            try:
                if not self.main_screen.click_Performance(timeout=timeout):
                    raise AssertionError("click_Performance failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"click_port failed for {port_number}")

                type_dd, matched_value = resolve_type_option(ms=max(timeout, 10_000))
                type_dd.select_option(value=matched_value, timeout=timeout)

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

        def resolve_stable_options(ms: int):
            """
            Poll until the Type select's <option> list is visible AND stable across
            two consecutive reads. Same rationale as set_PM_Type()'s settle-loop:
            after click_port() the pm_port iframe (Pm_Port_Pm.asp) can take a few
            seconds to settle into its final, service-dependent option set, so
            reading immediately can return a stale/mid-reload option list.
            """
            step = 300
            loops = max(1, ms // step)
            previous = None

            for _ in range(loops):
                try:
                    type_dd = self.pm_port_frame().locator("select[name='type']").first
                    if type_dd.count() > 0 and type_dd.is_visible():
                        opts = type_dd.locator("option")
                        n = opts.count()
                        current = []
                        for i in range(n):
                            opt = opts.nth(i)
                            value = (opt.get_attribute("value") or "").strip()
                            label = (opt.inner_text() or "").strip()
                            current.append((value, label))

                        if current and current == previous:
                            return current
                        previous = current
                except Exception:
                    previous = None

                self.page.wait_for_timeout(step)

            return previous or []

        for attempt in range(retries):
            try:
                if not self.main_screen.click_Performance(timeout=timeout):
                    raise AssertionError("click_Performance failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"click_port failed for {port_number}")

                options = resolve_stable_options(ms=max(timeout, 10_000))
                if not options:
                    raise AssertionError("Type dropdown options could not be read")

                # result.append((value, label))
                return [label for _value, label in options]

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
        for attempt in range(retries):
            try:
                if not self.main_screen.click_Performance(timeout=timeout):
                    raise AssertionError("click_Performance failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"click_port failed for {port_number}")

                pm_fl = self.pm_port_frame()
                get_btn = pm_fl.locator("input[name='get_button']").first
                expect(get_btn).to_be_visible(timeout=timeout)
                expect(get_btn).to_be_enabled(timeout=timeout)

                get_btn.scroll_into_view_if_needed()
                get_btn.click(force=True, timeout=timeout)

                self.page.wait_for_timeout(1000)
                expect(pm_fl.locator("form[name='pm_form']").first).to_be_visible(timeout=timeout)

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
        """
        sleep(2)
        for attempt in range(retries):
            try:
                if not self.main_screen.click_Performance(timeout=timeout):
                    raise AssertionError("click_Performance failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"click_port failed for {port_number}")

                ctx = self.pm_port_table_frame()
                tbody = ctx.locator("#tbody").first
                expect(tbody).to_be_visible(timeout=timeout)

                header_cells = ctx.locator("#thead th")
                headers = []
                for i in range(header_cells.count()):
                    text = header_cells.nth(i).inner_text().replace("\xa0", " ").strip()
                    if text:
                        headers.append(text)

                if not headers:
                    raise AssertionError("PM table headers (#thead th) were not found.")

                rows = tbody.locator("tr")
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
            interval_index: 0 for "Current"/"Untimed", 1, 2, ... for the historical rows below it.
            action_dismiss:
                False -> accept any confirmation dialog that appears
                True  -> dismiss it

        Returns:
            (success, dialog_text)

        Each Reset button's `name` attribute is NOT the static "Interval-N" pattern
        it looks like -- WritePmData() in Pm_Port_Table.asp builds a name PREFIX
        that depends on both the currently selected PM Type (e.g. "EgressPm" ->
        "EGRESS-", "Section" -> "", "Line" -> "OTN0-Line-") and PM Period
        ("Intervals" -> "Interval-", "Days" -> "Day-"), e.g. "EGRESS-Day-0" when
        Type=Egress PM and Period=Days. Reconstructing that whole prefix table in
        Python would be brittle, so instead this locates the Reset button by ROW
        POSITION within #tbody (same table/pattern already used by get_PM_table())
        -- every row has exactly one Reset button in its last cell, regardless of
        which Type/Period produced its name.
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

                tbody = self.pm_port_table_frame().locator("#tbody").first
                expect(tbody).to_be_visible(timeout=timeout)

                row = tbody.locator("tr").nth(interval_index)
                reset_btn = row.locator("input[type='submit']").first
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

                reset_btn = self.pm_port_frame().locator("form[name='reset_pm_form'] input[name='B1']").first
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

                reset_all_btn = self.pm_port_frame().locator("form[name='reset_all_pm_form'] input[name='B1']").first
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
