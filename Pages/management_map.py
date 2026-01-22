"""
Created by: Yuval Dahan
Date: 20/01/2026
"""

from playwright.sync_api import Page, expect
from Utils.map_locators import MapLocators
import time
from typing import Callable
import re
from time import sleep



class ManagementMap:
    """
    Management Map page – Encapsulates all map-level interactions, including alarm visibility, severity filters,
    layer toggles, zoom controls, navigation info, and element detail panels, providing
    a structured API for reliable map automation.
    """

    def __init__(self, page: Page):
        self.page = page
        self.mapLocator = MapLocators(page)

    # ==========================================================
    # Internal small helpers
    # ==========================================================
    def is_pressed(self, label_text: str) -> bool:
        """
        Checks if a filter is ACTIVE.
        When active, the span has class "pressed".

        Raises:
            AssertionError if the element exists but has no class attribute.
        """
        span = self.mapLocator.events_filter_span(label_text)

        cls = span.get_attribute("class")
        if cls is None:
            raise AssertionError(f"is_pressed failed: 'class' attribute is missing for filter '{label_text}'")

        return "pressed" in cls.split()

    def is_filter_disabled(self, label_text: str) -> bool:
        """
        OFF == tile has class 'disabled'
        """
        cls = self.mapLocator.events_filter_tile_class(label_text)
        if cls is None:
            raise AssertionError(f"is_filter_disabled failed: class 'disabled' is missing for filter '{label_text}'")

        return "disabled" in cls.split()

    def is_tab_currently_selected(self, tab_name: str) -> bool:
        """
        Checks if a tab is currently selected.
        The selected tab has class "current".

        Raises:
            AssertionError if the element exists but has no class attribute.
        """
        tab = self.mapLocator.find_tab(tab_name)

        cls = tab.get_attribute("class")
        if cls is None:
            raise AssertionError(f"is_tab_currently_selected failed: 'class' attribute is missing for tab '{tab_name}'")

        return "current" in cls.split()
    
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
                # keep last exception to show helpful info if we time out
                last_exc = e

            time.sleep(interval_ms / 1000.0)

        if last_exc:
            raise AssertionError(f"Condition not met within {timeout_ms}ms. Last error: {last_exc}")
        raise AssertionError(f"Condition not met within {timeout_ms}ms.")

    def is_edit_mode(self) -> bool:
        """
        When edit mode is active, center-bottom Save/Discard buttons appear.
        (Sometimes the section exists but is hidden; we treat visible as edit-mode.)
        """
        try:
            return self.mapLocator.controls_center_bottom.is_visible()
        except Exception as e:
            print(f"is_edit_mode failed. Problem: {e}")
            return False
        
    # ==========================================================
    # Alarms visibility
    # ==========================================================
    def show_alarms(self):
        """
        - If already shown -> do nothing
        - If hidden -> click and ASSERT it became shown
        - If state is invalid -> get_alarms_status() will raise
        """
        status = self.get_alarms_status()

        if status == "shown":
            return

        if status == "hidden":
            self.mapLocator.events_filter_tile("Alarms").click()
            try:
                self.wait_until(lambda: self.get_alarms_status() == "hidden", timeout_ms=5000, interval_ms=200)

            except Exception as e:
                raise AssertionError(f"show_alarms failed: alarms did not become 'shown'. Problem: {e}")

            return

        raise AssertionError(f"show_alarms failed: unexpected alarms status '{status}'")

    def hide_alarms(self):
        """
        - If already hidden -> do nothing
        - If shown -> click and ASSERT it became hidden
        - If state is invalid -> get_alarms_status() will raise
        """
        status = self.get_alarms_status()

        if status == "hidden":
            return

        if status == "shown":
            self.mapLocator.events_filter_tile("Alarms").click()
            try:
                self.wait_until(lambda: self.get_alarms_status() == "hidden", timeout_ms=5000, interval_ms=200)
            except Exception as e:
                raise AssertionError(f"hide_alarms failed: alarms did not become 'hidden'. Problem: {e}")

            return

        raise AssertionError(f"hide_alarms failed: unexpected alarms status '{status}'")

    def get_alarms_status(self) -> str:
        """
        Returns: "shown" | "hidden" | "unknown"
        Based on app-icon name attribute (e.g., 'eye' / 'eye-slash').
        """
        icon_name = self.mapLocator.events_filter_icon_name("Alarms").strip()
        if icon_name.strip() == "eye":
            return "hidden"
        if icon_name.strip() == "eye-slash":
            return "shown"
        
        # Icon exists but state is not recognized → logical failure
        raise AssertionError(f"Unknown alarms icon state: '{icon_name}'")

    # ==========================================================
    # Severity filters
    # ==========================================================
    def _set_severity_filter(self, label_text: str, enable: bool):
        """
          - Enabled (ON)  => tile does NOT have class 'disabled'
          - Disabled (OFF)=> tile HAS class 'disabled'
        """
        currently_enabled = not self.is_filter_disabled(label_text)

        if enable and currently_enabled:
            return
        if (not enable) and (not currently_enabled):
            return

        self.mapLocator.events_filter_tile(label_text).click()
        tile = self.mapLocator.events_filter_tile(label_text)

        try:
            if enable:
                expect(tile).not_to_have_class(re.compile(r"\bdisabled\b"), timeout=5000)
            else:
                expect(tile).to_have_class(re.compile(r"\bdisabled\b"), timeout=5000)
        except Exception as e:
            desired = "enabled" if enable else "disabled"
            raise AssertionError(f"{label_text} filter did not become {desired}. Problem: {e}")
        
    def show_critical_major(self):
        self._set_severity_filter("Critical", enable=True)

    def hide_critical_major(self):
        self._set_severity_filter("Critical", enable=False)

    def show_minor(self):
        self._set_severity_filter("Minor", enable=True)

    def hide_minor(self):
        self._set_severity_filter("Minor", enable=False)

    def show_cleared(self):
        self._set_severity_filter("Cleared", enable=True)

    def hide_cleared(self):
        self._set_severity_filter("Cleared", enable=False)

    # ==========================================================
    # Map interaction controls
    # ==========================================================
    def enable_drag(self):
        """
        - If drag is already enabled -> do nothing
        - Else click 'Enable drag' and ASSERT it disappears
        """

        btn = self.mapLocator.enable_drag_button()

        # If button is already gone → drag is already enabled
        if not btn.is_visible():
            return
        
        btn.click()

        try:
            # After enabling drag, the button should disappear
            expect(btn).not_to_be_visible(timeout=5000)

            # Edit-mode controls should show up (Save/Discard)
            expect(self.mapLocator.controls_center_bottom).to_be_visible(timeout=5000)

        except Exception as e:
            raise AssertionError(f"enable_drag failed: edit mode did not start properly. Problem: {e}")

    def save_and_lock(self):
        """
        - If not in edit mode -> do nothing
        - Else click 'Save & Lock' and ASSERT edit controls disappear
        """
        if not self.is_edit_mode():
            return

        btn = self.mapLocator.save_and_lock_button()
        try:
            expect(btn).to_be_visible(timeout=5000)
            btn.click()

            expect(self.mapLocator.controls_center_bottom).not_to_be_visible(timeout=10000)

        except Exception as e:
            raise AssertionError(f"save_and_lock failed: did not exit edit mode after Save & Lock. Problem: {e}")

    def discard_and_lock(self):
        """
        - If not in edit mode -> do nothing
        - Else click 'Discard & Lock' and ASSERT edit controls disappear
        """
        if not self.is_edit_mode():
            return

        btn = self.mapLocator.discard_and_lock_button()
        try:
            expect(btn).to_be_visible(timeout=5000)
            btn.click()

            expect(self.mapLocator.controls_center_bottom).not_to_be_visible(timeout=10000)

        except Exception as e:
            raise AssertionError(f"discard_and_lock failed: did not exit edit mode after Discard & Lock. Problem: {e}")

    # ==========================================================
    # Layer toggles
    # ==========================================================
    def enable_chassis(self):
        """
        - If already selected -> do nothing
        - Else click and assert it became selected
        """
        if self.is_tab_currently_selected("Chassis"):
            return

        self.mapLocator.find_tab("Chassis").click()

        try:
            expect(self.mapLocator.find_tab("Chassis")).to_have_class(re.compile(r"\bcurrent\b"), timeout=5000)

        except Exception as e:
            raise AssertionError(f"enable_chassis failed: tab did not become current. Problem: {e}")

    def enable_OTN(self):
        """
        - If already selected -> do nothing
        - Else click and assert it became selected
        """
        if self.is_tab_currently_selected("OTN"):
            return

        self.mapLocator.find_tab("OTN").click()

        try:
            expect(self.mapLocator.find_tab("OTN")).to_have_class(re.compile(r"\bcurrent\b"), timeout=5000)

        except Exception as e:
            raise AssertionError(f"enable_OTN failed: tab did not become current. Problem: {e}")

    def enable_ROADM(self):
        """
        - If already selected -> do nothing
        - Else click and assert it became selected
        """
        if self.is_tab_currently_selected("ROADM"):
            return

        self.mapLocator.find_tab("ROADM").click()

        try:
            expect(self.mapLocator.find_tab("ROADM")).to_have_class(re.compile(r"\bcurrent\b"), timeout=5000)

        except Exception as e:
            raise AssertionError(f"enable_ROADM failed: tab did not become current. Problem: {e}")

    def enable_manage(self):
        """
        - If already selected -> do nothing
        - Else click and assert it became selected
        """
        if self.is_tab_currently_selected("Manage"):
            return

        self.mapLocator.find_tab("Manage").click()

        try:
            expect(self.mapLocator.find_tab("Manage")).to_have_class(re.compile(r"\bcurrent\b"), timeout=5000)

        except Exception as e:
            raise AssertionError(f"enable_manage failed: tab did not become current. Problem: {e}")

    # ==========================================================
    # Zoom controls
    # ==========================================================
    
    def get_svg_transform(self) -> str:
        """
        Helper: returns the current transform value of the main SVG <g>.
        Used to validate zoom actually changed something.
        """
        g = self.mapLocator.svg_map.locator("g").first
        transform = g.get_attribute("transform")
        if transform is None:
            raise AssertionError("SVG transform attribute is missing.")
        return transform

    def map_zoom_in(self):
        """
        - Click zoom-in
        - ASSERT SVG transform changed
        """
        before = self.get_svg_transform()

        self.mapLocator.zoom_controls.locator("button").nth(0).click()

        try:
            self.wait_until(lambda: self.get_svg_transform() != before, timeout_ms=10000, interval_ms=200)

        except Exception as e:
            raise AssertionError(f"map_zoom_in failed: SVG transform did not change. Problem: {e}")

    def map_zoom_out(self):
        """
        - Click zoom-out
        - If already at max zoom-out -> do nothing
        - Else ASSERT viewport size increased
        """

        view_port = self.page.locator("div.cdk-drag.view-port")

        def get_viewport_size():
            # wait for it to exist/visible to avoid implicit hangs time
            if view_port.count() == 0:
                raise AssertionError("Zoom viewport element not found: div.cdk-drag.view-port")

            style = view_port.get_attribute("style") or ""
            width = height = None

            for part in style.split(";"):
                part = part.strip()
                if part.startswith("width:"):
                    width = float(part.split(":", 1)[1].replace("px", "").strip())
                elif part.startswith("height:"):
                    height = float(part.split(":", 1)[1].replace("px", "").strip())

            if width is None or height is None:
                raise AssertionError(f"Failed to parse viewport size from style: '{style}'")

            return width, height
        
        # Zoom in and out once before to get the actual max zoom-out range
        # (at first width: 320px; height: 225.774px --> actual max zoom-out range: width: 251.733px; height: 177.609px)
        self.mapLocator.zoom_controls.locator("button").nth(0).click()
        sleep(2)
        self.mapLocator.zoom_controls.locator("button").nth(1).click()
        sleep(2)
        before_w, before_h = get_viewport_size()

        # Click zoom-out
        self.mapLocator.zoom_controls.locator("button").nth(1).click()

        # Try to detect a change quickly; if no change -> already at max zoom-out
        try:
            self.wait_until(lambda: get_viewport_size() != (before_w, before_h), timeout_ms=2000, interval_ms=200)
        except AssertionError:
            # No size change => max zoom-out reached, do nothing
            print("Zoom out is not possible anymore - got to the max zoom-out range. (Continue with the script)")
            return

        after_w, after_h = get_viewport_size()

        # Zooming out should make the viewport larger (or at least not smaller)
        if after_w <= before_w or after_h <= before_h:
            raise AssertionError(
                f"map_zoom_out failed: viewport did not grow. "
                f"Before=({before_w}, {before_h}), After=({after_w}, {after_h})")
        
    def map_scroll_up(self):
        pass

    def map_scroll_down(self):
        pass

    def map_scroll_right(self):
        pass

    def map_scroll_left(self):
        pass

    # ==========================================================
    # Navigation info
    # ==========================================================
    def show_navigation_info(self):
        # Not provided in your HTML snippet (leave empty for now)
        pass

    def hide_navigation_info(self):
        # Not provided in your HTML snippet (leave empty for now)
        pass

    def navigation_info_double_click_on_element(self):
        # Not provided in your HTML snippet (leave empty for now)
        pass

    def navigation_info_open_element_details(self):
        # Not provided in your HTML snippet (leave empty for now)
        pass

    def navigation_info_close_element_details(self):
        # Not provided in your HTML snippet (leave empty for now)
        pass

    # ==========================================================
    # Element details
    # ==========================================================
    def element_details_chassis(self):
        # Not provided in your HTML snippet (leave empty for now)
        pass

    def element_details_services(self):
        # Not provided in your HTML snippet (leave empty for now)
        pass

    def element_details_faults(self):
        # Not provided in your HTML snippet (leave empty for now)
        pass

    # ==========================================================
    # Faults → Alarms
    # ==========================================================
    def element_details_faults_click_on_alarms(self):
        # Not provided in your HTML snippet (leave empty for now)
        pass

    def element_details_faults_view_all_alarms(self):
        # Not provided in your HTML snippet (leave empty for now)
        pass

    def element_details_faults_get_all_alarms(self):
        # Not provided in your HTML snippet (leave empty for now)
        pass

    # ==========================================================
    # Faults → Events
    # ==========================================================
    def element_details_faults_click_on_events(self):
        # Not provided in your HTML snippet (leave empty for now)
        pass

    def element_details_faults_view_all_events(self):
        # Not provided in your HTML snippet (leave empty for now)
        pass

    def element_details_faults_get_all_events(self):
        # Not provided in your HTML snippet (leave empty for now)
        pass

    # ==========================================================
    # General info
    # ==========================================================
    def element_details_info(self):
        # Not provided in your HTML snippet (leave empty for now)
        pass
