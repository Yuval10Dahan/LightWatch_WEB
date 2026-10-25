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
from Utils.utils import refresh_page



class NetworkTopology:
    """
    Network Topology page – Encapsulates all map-level interactions, including alarm visibility, severity filters,
    layer toggles, zoom controls, navigation info, and element detail panels, providing
    a structured API for reliable map automation.
    """

    def __init__(self, page: Page):
        self.page = page
        self.mapLocator = MapLocators(page)
        self.reload_button = page.locator('button', has_text="Reload")

    # ==========================================================
    # Internal small helpers
    # ==========================================================

    # ✅
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

    # ✅
    def is_filter_disabled(self, label_text: str) -> bool:
        """
        OFF == tile has class 'disabled'
        """
        cls = self.mapLocator.events_filter_tile_class(label_text)
        if cls is None:
            raise AssertionError(f"is_filter_disabled failed: class 'disabled' is missing for filter '{label_text}'")

        return "disabled" in cls.split()

    # ✅
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
                # keep last exception to show helpful info if we time out
                last_exc = e

            time.sleep(interval_ms / 1000.0)

        if last_exc:
            raise AssertionError(f"Condition not met within {timeout_ms}ms. Last error: {last_exc}")
        raise AssertionError(f"Condition not met within {timeout_ms}ms.")

    # ✅
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

    # ✅
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
                # self.wait_until(lambda: self.get_alarms_status() == "hidden", timeout_ms=5000, interval_ms=200)
                self.wait_until(lambda: self.get_alarms_status() == "shown", timeout_ms=5000, interval_ms=200)

            except Exception as e:
                raise AssertionError(f"show_alarms failed: alarms did not become 'shown'. Problem: {e}")

            return

        raise AssertionError(f"show_alarms failed: unexpected alarms status '{status}'")

    # ✅
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

    # ✅    
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

    # ✅
    def set_severity_filter(self, label_text: str, enable: bool):
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
    
    # ✅
    def show_critical_major(self):
        self.set_severity_filter("Critical", enable=True)

    # ✅
    def hide_critical_major(self):
        self.set_severity_filter("Critical", enable=False)

    # ✅
    def show_minor(self):
        self.set_severity_filter("Minor", enable=True)

    # ✅
    def hide_minor(self):
        self.set_severity_filter("Minor", enable=False)

    # ✅
    def show_cleared(self):
        self.set_severity_filter("Cleared", enable=True)

    # ✅
    def hide_cleared(self):
        self.set_severity_filter("Cleared", enable=False)

    # ==========================================================
    # Map interaction controls
    # ==========================================================

    # ✅
    def unlock_map(self):
        """
        - If unlock map is already enabled -> do nothing
        - Else click 'Unlock Map' and ASSERT it disappears
        """

        btn = self.mapLocator.unlock_map_button()

        # If button is already gone → Unlock map is already enabled
        if not btn.is_visible():
            return
        
        btn.click()

        try:
            # After enabling Unlock map, the button should disappear
            expect(btn).not_to_be_visible(timeout=5000)

            # Edit-mode controls should show up (Save/Discard)
            expect(self.mapLocator.controls_center_bottom).to_be_visible(timeout=5000)

            sleep(0.5)

        except Exception as e:
            raise AssertionError(f"unlock_map failed: edit mode did not start properly. Problem: {e}")

    # ✅
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

            sleep(0.5)

        except Exception as e:
            raise AssertionError(f"save_and_lock failed: did not exit edit mode after Save & Lock. Problem: {e}")

    # ✅
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

            sleep(0.5)

        except Exception as e:
            raise AssertionError(f"discard_and_lock failed: did not exit edit mode after Discard & Lock. Problem: {e}")

    # ✅
    def double_click_on_element_via_the_map_by_data_id(self, element_data_id: str | int, timeout: int = 12000) -> bool:
        """
        Double-click an element on the map using its SVG data-id.
        data-id is the ONLY supported selector (most stable).

        How to find the `data-id` manually (step-by-step):
        --------------------------------------------------
        1. Open the GUI and navigate to the map view.
        2. Right-click the desired element (chassis or device) on the map.
        3. Choose "Inspect" (open DevTools).
        4. In the Elements tab, locate the SVG <path> that represents the element.
        It will look similar to:

            <path class="gradient"
                    fill="url(#fault_gradient)"
                    data-idKey=""
                    data-id="7"
                    d="M24 0H8C3.58..."></path>

        or for devices:

            <path class="in-chassis-gradient device"
                    fill="url(#fault_gradient)"
                    data-id="22"
                    data-idKey="10.60.100.34"
                    d="M24 0H8C3.58..."></path>

        5. Copy the value of `data-id` (for example: "7").

        Notes:
        ------
        - Double-clicking a chassis typically expands it to show the elements inside.
        - Double-clicking a device may open its PacketLight GUI in another tab.
        """
        try:
            did = str(element_data_id).strip()
            if not did:
                raise ValueError("data_id is empty")

            svg = self.page.locator("svg.svg-container").first

            # Target clickable SVG tile
            tile = svg.locator(
                f"path.gradient[data-id='{did}'], "
                f"path.gradient.device[data-id='{did}'], "
                f"path.in-chassis-gradient.device[data-id='{did}']"
            ).first

            if tile.count() == 0:
                raise AssertionError(f"Map element with data-id='{did}' not found.")

            tile.scroll_into_view_if_needed()
            refresh_page(self.page)
            sleep(2)
            tile.dblclick(timeout=timeout, force=True)
            sleep(2)
            tile.dblclick(timeout=timeout, force=True)
            sleep(5)

            return True

        except Exception as e:
            raise AssertionError(f"double_click_on_element_via_the_map(data_id={element_data_id}) failed. Problem: {e}")

    # ✅
    def click_on_element_via_the_map_by_data_id(self, element_data_id: str | int, timeout: int = 12000) -> bool:
        """
        Click an element on the map using its SVG data-id.
        data-id is the ONLY supported selector (most stable).

        How to find the `data-id` manually (step-by-step):
        --------------------------------------------------
        1. Open the GUI and navigate to the map view.
        2. Right-click the desired element (chassis or device) on the map.
        3. Choose "Inspect" (open DevTools).
        4. In the Elements tab, locate the SVG <path> that represents the element.
        It will look similar to:

            <path class="gradient"
                    fill="url(#fault_gradient)"
                    data-idKey=""
                    data-id="7"
                    d="M24 0H8C3.58..."></path>

        or for devices:

            <path class="in-chassis-gradient device"
                    fill="url(#fault_gradient)"
                    data-id="22"
                    data-idKey="10.60.100.34"
                    d="M24 0H8C3.58..."></path>

        5. Copy the value of `data-id` (for example: "7").
        """
        try:
            sleep(3)
            did = str(element_data_id).strip()
            if not did:
                raise ValueError("data_id is empty")

            svg = self.page.locator("svg.svg-container").first
            sleep(1)

            # Target clickable SVG tile
            tile = svg.locator(
                f"path.gradient[data-id='{did}'], "
                f"path.gradient.device[data-id='{did}'], "
                f"path.in-chassis-gradient.device[data-id='{did}']"
            ).first

            if tile.count() == 0:
                raise AssertionError(f"Map element with data-id='{did}' not found.")

            tile.scroll_into_view_if_needed()
            tile.click(timeout=timeout, force=True)

            sleep(1)
            return True

        except Exception as e:
            raise AssertionError(f"click_on_element_via_the_map(data_id={element_data_id}) failed. Problem: {e}")

    # ✅
    def double_click_on_element_via_the_map(self, element_name: str | None = None, element_ip: str | None = None, timeout: int = 12000) -> bool:
        """
        Double-click an element on the map.

        Supported search methods:
        - By element name   (example: "Chassis: 17" or "PL-2000T")
        - By device IP      (example: "172.16.30.17")

        Notes:
        - If more than one identifier is provided, priority is:
            element_ip -> element_name
        - Double-clicking a chassis typically expands it to show elements inside.
        - Double-clicking a device may open its PacketLight GUI in another tab.
        """

        try:
            svg = self.page.locator("svg.svg-container").first
            tile = None

            # 1) Search by IP 
            if element_ip is not None and str(element_ip).strip():
                ip = str(element_ip).strip()

                node = svg.locator(f"g.node:has(text.node-device-ip:has-text('({ip})'))").first

                if node.count() == 0:
                    raise AssertionError(f"Map element with IP '{ip}' not found.")

                tile = node.locator("path.gradient, path.gradient.device, path.in-chassis-gradient.device").first

                if tile.count() == 0:
                    raise AssertionError(f"Map node with IP '{ip}' does not contain a clickable path element.")

            # 2) Search by name
            elif element_name is not None and str(element_name).strip():
                name = str(element_name).strip()

                node = svg.locator(
                    f"g.node:has(text.node-user-name:has-text('{name}')), "
                    f"g.node:has(text.node-name:has-text('{name}'))"
                ).first

                if node.count() == 0:
                    raise AssertionError(f"Map element with name '{name}' not found.")

                tile = node.locator("path.gradient, path.gradient.device, path.in-chassis-gradient.device").first

                if tile.count() == 0:
                    raise AssertionError(f"Map node with name '{name}' does not contain a clickable path element.")

            else:
                raise ValueError("Provide at least one of: element_name, element_ip.")

            tile.scroll_into_view_if_needed()
            # refresh_page(self.page)
            sleep(2)
            tile.dblclick(timeout=timeout, force=True)
            sleep(2)
            # tile.dblclick(timeout=timeout, force=True)
            # sleep(5)

            return True

        except Exception as e:
            raise AssertionError(
                f"double_click_on_element_via_the_map("
                f"element_name={element_name}, element_ip={element_ip}"
                f") failed. Problem: {e}"
            )

    # ✅
    def click_on_element_via_the_map(self, element_name: str | None = None, element_ip: str | None = None, timeout: int = 12000) -> bool:
        """
        Click an element on the map.

        Supported search methods:
        - By element name   (example: "Chassis: 17" or "PL-2000T")
        - By device IP      (example: "172.16.30.17")

        Notes:
        - If more than one identifier is provided, priority is:
            element_ip -> element_name
        """

        try:
            sleep(3)
            svg = self.page.locator("svg.svg-container").first
            sleep(1)

            tile = None

            # 1) Search by IP
            if element_ip is not None and str(element_ip).strip():
                ip = str(element_ip).strip()

                node = svg.locator(f"g.node:has(text.node-device-ip:has-text('({ip})'))").first

                if node.count() == 0:
                    raise AssertionError(f"Map element with IP '{ip}' not found.")

                tile = node.locator("path.gradient, path.gradient.device, path.in-chassis-gradient.device").first

                if tile.count() == 0:
                    raise AssertionError(f"Map node with IP '{ip}' does not contain a clickable path element.")

            # 2) Search by name
            elif element_name is not None and str(element_name).strip():
                name = str(element_name).strip()

                node = svg.locator(
                    f"g.node:has(text.node-user-name:has-text('{name}')), "
                    f"g.node:has(text.node-name:has-text('{name}'))"
                ).first

                if node.count() == 0:
                    raise AssertionError(f"Map element with name '{name}' not found.")

                tile = node.locator("path.gradient, path.gradient.device, path.in-chassis-gradient.device").first

                if tile.count() == 0:
                    raise AssertionError(f"Map node with name '{name}' does not contain a clickable path element.")

            else:
                raise ValueError("Provide at least one of: element_name, element_ip.")

            tile.scroll_into_view_if_needed()
            tile.click(timeout=timeout, force=True)

            sleep(1)
            return True

        except Exception as e:
            raise AssertionError(
                f"click_on_element_via_the_map("
                f"element_name={element_name}, element_ip={element_ip}"
                f") failed. Problem: {e}"
            )

    # ✅
    def get_number_of_elements_inside_chassis(self, data_id: str | int, timeout: int = 5000) -> int:
        """
        Return the number shown in the small badge near the chassis icon on the map.
        This number represents the number of elements inside the chassis.
        """
        try:
            sleep(3)
            did = str(data_id).strip()
            if not did:
                raise ValueError("data_id is empty")

            svg = self.page.locator("svg.svg-container").first

            # Ensure chassis exists by its stable SVG data-id
            chassis_tile = svg.locator(f"path.gradient[data-id='{did}']").first
            if chassis_tile.count() == 0:
                raise AssertionError(f"Chassis with data-id='{did}' not found on the map.")

            # Locate the badge <text> inside the same node
            badge_text = svg.locator(f"g.node:has(path.gradient[data-id='{did}']) g.events-counts text").first

            if badge_text.count() == 0:
                return 0

            val = (badge_text.text_content(timeout=timeout) or "").strip()

            # Sometimes the SVG text might include whitespace/newlines
            val = re.sub(r"\s+", "", val)

            if not val.isdigit():
                raise AssertionError(f"Expected numeric badge value for chassis data-id='{did}', got '{val}'.")

            return int(val)

        except Exception as e:
            raise AssertionError(f"get_number_of_elements_inside_chassis(data_id={data_id}) failed. Problem: {e}")

    # ✅
    def get_map_element_color(self, element_name: str | None = None, element_ip: str | None = None) -> tuple[str, str]:
        """
        Returns 2 values for a map element (Device / Chassis / Domain):

        1. logical color state: "fault" / "warning" / "positive" / "neutral" or the raw gradient name if unknown.
        2. human-readable color string: "red" / "orange" / "green" / "gray" or "unknown".

        Search logic:
        - For chassis/domain/etc. -> use element_name, for example: "Chassis: 17"
        - For device -> use element_ip, for example: "172.16.30.17"

        Notes:
        - Provide either element_name or element_ip
        - If both are provided, element_ip is preferred
        """

        try:
            svg = self.page.locator("svg.svg-container").first
            sleep(1)

            node = None

            # Prefer searching by IP if provided
            if element_ip is not None and str(element_ip).strip():
                ip = str(element_ip).strip()

                node = svg.locator(f"g.node:has(text.node-device-ip:has-text('({ip})'))").first
                sleep(1)

                if node.count() == 0:
                    raise AssertionError(f"Map element with IP '{ip}' not found.")

            elif element_name is not None and str(element_name).strip():
                name = str(element_name).strip()

                node = svg.locator(
                    f"g.node:has(text.node-user-name:has-text('{name}')), "
                    f"g.node:has(text.node-name:has-text('{name}'))"
                ).first
                sleep(1)

                if node.count() == 0:
                    raise AssertionError(f"Map element with name '{name}' not found.")

            else:
                raise ValueError("Either element_name or element_ip must be provided.")

            # Read the colored path inside the located node
            element = node.locator("path.gradient, path.gradient.device, path.in-chassis-gradient.device").first
            sleep(1)

            if element.count() == 0:
                raise AssertionError("Located map node does not contain a color path element.")

            fill_value = element.get_attribute("fill")
            if fill_value is None:
                raise AssertionError("Located map element has no fill attribute.")

            match = re.search(r"url\(#(.*?)\)", fill_value)
            if not match:
                return fill_value, "unknown"

            gradient = match.group(1).strip()
            gradient_lower = gradient.lower()

            if "fault" in gradient_lower:
                return "fault", "red"

            if "warning" in gradient_lower:
                return "warning", "orange"

            if "positive" in gradient_lower:
                return "positive", "green"

            if "neutral" in gradient_lower:
                return "neutral", "gray"

            return gradient, "unknown"

        except Exception as e:
            raise AssertionError(f"get_map_element_color_by_name_or_ip(element_name={element_name}, element_ip={element_ip}) failed. Problem: {e}")

    # ==========================================================
    # Layer toggles
    # ==========================================================
    
    # ✅
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

    # ✅
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

    # ✅
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

    # ✅
    def enable_manage(self):
        """
        - If already selected -> do nothing
        - Else click and assert it became selected
        """
        if self.is_tab_currently_selected("MNG"):
            return

        self.mapLocator.find_tab("MNG").click()

        try:
            expect(self.mapLocator.find_tab("MNG")).to_have_class(re.compile(r"\bcurrent\b"), timeout=5000)

        except Exception as e:
            raise AssertionError(f"enable_manage failed: tab did not become current. Problem: {e}")

    # ==========================================================
    # Zoom controls
    # ==========================================================
    
    # ✅
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
        
    # ✅
    def map_zoom_in(self):
        """
        - Click zoom-in
        - ASSERT SVG transform changed
        """

        before = self.get_svg_transform()
        self.mapLocator.zoom_in_button().click()

        try:
            self.wait_until(lambda: self.get_svg_transform() != before, timeout_ms=10000, interval_ms=200)
            sleep(0.5)

        except Exception as e:
            raise AssertionError(f"map_zoom_in failed: SVG transform did not change. Problem: {e}")

    # ✅
    def map_zoom_out(self):
        """
        - If zoom percentage is <= 118%, automation cannot zoom out more -> continue
        - Else click zoom-out and assert zoom percentage changed
        """

        before_percentage = self.get_zoom_percentage()

        if before_percentage <= 118:
            print(f"Zoom out is not possible anymore - current zoom is {before_percentage}%.")
            return

        btn = self.mapLocator.zoom_out_button()
        expect(btn).to_be_visible(timeout=5000)
        btn.click(force=True)

        try:
            self.wait_until(lambda: self.get_zoom_percentage() < before_percentage, timeout_ms=10000, interval_ms=200)
            sleep(0.5)

        except Exception as e:
            raise AssertionError(
                f"map_zoom_out failed: zoom percentage did not decrease. "
                f"Before={before_percentage}%. Problem: {e}"
            )

    # ✅
    def get_zoom_percentage(self) -> int:
        """
        Returns the current map zoom percentage as int.
        Example: '118%' -> 118
        """
        try:
            zoom_text = self.mapLocator.zoom_controls.locator(".zoom-percentage").inner_text(timeout=5000)
            zoom_text = zoom_text.strip().replace("%", "").strip()

            if not zoom_text.isdigit():
                raise AssertionError(f"Invalid zoom percentage value: '{zoom_text}'")

            return int(zoom_text)

        except Exception as e:
            raise AssertionError(f"get_zoom_percentage failed. Problem: {e}")

    # ✅
    def reset_zoom_percentage(self):
        """
        Reset map zoom back to the default zoom level.

        Behavior:
        - If already at default zoom (100%) -> do nothing
        - Else hover zoom controls, click 'reset', and verify zoom became 100%
        """

        try:
            current_zoom = self.get_zoom_percentage()

            # Already default zoom
            if current_zoom == 100:
                return

            zoom_controls = self.mapLocator.zoom_controls
            reset_btn = zoom_controls.locator(".zoom-reset-btn")

            # 'reset' only appears on hover
            zoom_controls.hover()

            expect(reset_btn).to_be_visible(timeout=5000)

            reset_btn.click(force=True)

            self.wait_until(lambda: self.get_zoom_percentage() == 100, timeout_ms=10000, interval_ms=200)

            sleep(0.5)

        except Exception as e:
            raise AssertionError(f"reset_zoom_percentage failed. Problem: {e}")

    def map_scroll_up(self):
        pass

    def map_scroll_down(self):
        pass

    def map_scroll_right(self):
        pass

    def map_scroll_left(self):
        pass

    # ==========================================================
    # Navigation Info helpers
    # ==========================================================

    # ✅
    def navinfo_section(self):
        return self.mapLocator.root.locator("section.main-controls-section-inventory-tree")

    # ✅
    def navinfo_toggle(self):
        return self.navinfo_section().locator("div.main-controls-section-inventory-tree-inner")

    # ✅
    def navinfo_wrapper(self):
        return self.mapLocator.root.locator("div.main-controls-section-inventory-tree-wrapper")

    # ✅
    def navinfo_is_open(self) -> bool:
        """
        - closed => inner div contains class 'collapsed'
        - open   => wrapper appears and/or 'collapsed' removed
        We'll treat wrapper visibility as the strongest signal.
        """
        wrapper = self.navinfo_wrapper()
        if wrapper.count() > 0 and wrapper.is_visible():
            return True

        cls = self.navinfo_toggle().get_attribute("class") or ""
        
        if cls is None:
            raise AssertionError(f"navinfo_is_open failed.")
        
        return "collapsed" not in cls.split()

    # ✅
    def navigation_info_container(self):
        """
        Container of the Navigation Info tree.
        """
        return self.page.locator("section.main-controls-section-inventory-tree:has(header .title:has-text('Navigation Info'))")
    
    # ✅
    def nav_text_regex(self, element_name: str) -> re.Pattern:
        """
        Build a regex that matches even if the UI splits text into spans
        and inserts spaces around '/'.
        Example:
          'BS-12/12'  -> matches 'BS-12/12' or 'BS-12 / 12'
          'Chassis: 2/2' -> matches 'Chassis: 2/2' or 'Chassis: 2 / 2'
        """
        s = element_name.strip()

        # Escape everything, then allow optional spaces around "/"
        esc = re.escape(s)
        esc = esc.replace(r"\/", r"\s*/\s*")

        # Also tolerate multiple spaces generally
        esc = esc.replace(r"\ ", r"\s+")

        return re.compile(esc)

    # ✅
    def nav_row_locator(self, element_name: str):
        """
        Returns the Navigation Info "row title" locator for the given element text.
        Uses regex text matching so it works even if the title is split across spans.
        """
        container = self.navigation_info_container()

        # Prefer matching on the whole title element
        rx = self.nav_text_regex(element_name)
        container = container.locator("div.inventory-tree-level-title", has_text=rx).first
        sleep(1)
        return container
    
    # ✅
    def normalize_nav_label(self, s: str) -> str:
        """
        Normalize UI text from Navigation Info rows:
        - collapse whitespace
        - tolerate spaces around '/'
        """
        txt = (s or "").strip()
        txt = re.sub(r"\s+", " ", txt)           # collapse whitespace
        txt = re.sub(r"\s*/\s*", "/", txt)       # normalize " / " -> "/"
        return txt.strip()

    # ==========================================================
    # Navigation info
    # ==========================================================

    # ✅
    def show_navigation_info(self):
        """
        - If already open -> do nothing
        - Else click the navigation-info toggle and ASSERT it opened
        """
        if self.navinfo_is_open():
            return

        toggle = self.navinfo_toggle()
        try:
            toggle.click()
            self.wait_until(lambda: self.navinfo_is_open(), timeout_ms=5000, interval_ms=200)

            # Strong assertion: wrapper should become visible
            wrapper = self.navinfo_wrapper()
            if wrapper.count() == 0:
                raise AssertionError("Navigation info wrapper did not appear in DOM after opening.")
            expect(wrapper).to_be_visible(timeout=5000)

        except Exception as e:
            raise AssertionError(f"show_navigation_info failed: navigation panel did not open. Problem: {e}")

    # ✅
    def hide_navigation_info(self):
        """
        - If already closed -> do nothing
        - Else close via the close button (close-square) and ASSERT it closed
        """

        if not self.navinfo_is_open():
            return

        close_btn = self.page.locator("app-icon[name='close-square']").first

        try:
            # Prefer clicking the close button if it exists/visible
            if close_btn.count() > 0 and close_btn.is_visible():
                close_btn.click()

            self.wait_until(lambda: not self.navinfo_is_open(), timeout_ms=5000, interval_ms=200)

            # Optional strong assertions (don’t over-assume DOM removal)
            wrapper = self.navinfo_wrapper()
            if wrapper.count() > 0:
                # wrapper might remain in DOM but should not be visible when closed
                expect(wrapper).not_to_be_visible(timeout=5000)

            cls = self.navinfo_toggle().get_attribute("class") or ""
            if "collapsed" not in cls.split():
                raise AssertionError(f"Expected 'collapsed' class after closing. Actual class: '{cls}'")
            
            sleep(1)

        except Exception as e:
            raise AssertionError(f"hide_navigation_info failed: navigation panel did not close. Problem: {e}")
 
    # ✅
    def get_navigation_info_elements_list(self, timeout: int = 5000, visible_only: bool = False) -> list[str]:
        """
        Returns a list of all element titles currently present in the Navigation Info tree.

        Notes:
        - If visible_only=True, returns only rows that are currently visible.
        """
        try:
            # Ensure panel is open 
            self.show_navigation_info()
            sleep(1.5)

            container = self.navigation_info_container()
            expect(container).to_be_visible(timeout=timeout)

            # Each row title container in the tree
            rows = container.locator("div.inventory-tree-level-title")
            count = rows.count()

            elements: list[str] = []

            for i in range(count):
                row = rows.nth(i)

                if visible_only:
                    try:
                        if not row.is_visible():
                            continue
                    except Exception:
                        # If visibility check fails for any reason, skip safely
                        continue

                title = row.locator("div.inventory-tree-level-title-content").first
                if title.count() == 0:
                    continue

                raw = (title.inner_text(timeout=timeout) or "").strip()
                normalized = self.normalize_nav_label(raw)

                if normalized:
                    elements.append(normalized)

            return elements

        except Exception as e:
            raise AssertionError(f"get_navigation_info_elements_list failed. Problem: {e}")

    # ✅
    def is_element_exist_on_navigation_info_list(self, element_name: str, timeout: int = 5000) -> bool:
        """
        Checks if a given element exists in the Navigation Info tree.
        """
        try:
            target = (element_name or "").strip()
            if not target:
                raise ValueError("element_name is empty")

            self.show_navigation_info()

            container = self.navigation_info_container()
            expect(container).to_be_visible(timeout=timeout)

            rx = self.nav_text_regex(target)

            # Search row titles
            row = container.locator("div.inventory-tree-level-title", has_text=rx)
            sleep(3)
            if row.count() == 0:
                return False

            # If multiple matches exist, we still consider it found if any is visible
            for i in range(row.count()):
                if row.nth(i).is_visible():
                    return True

            # Found in DOM but not visible (collapsed/filtered)
            return True

        except Exception as e:
            print(f"is_element_exist_on_navigation_info_list('{element_name}') failed. Problem: {e}")
            return False

    # ✅
    def navigation_info_double_click_on_element(self, element_name: str, timeout: int = 10000):
        """
        Double-click an element in Navigation Info to navigate the map to it.

        1) Find Navigation Info panel
        2) Find row by text (works even if text is split into spans)
        3) Scroll into view
        4) Double-click
        """
        try:
            container = self.navigation_info_container()
            expect(container).to_be_visible(timeout=timeout)

            row = self.nav_row_locator(element_name)
            expect(row).to_be_visible(timeout=timeout)

            row.scroll_into_view_if_needed()
            sleep(1)
            row.dblclick()
            sleep(1)
            row.dblclick()

        except Exception as e:
            raise AssertionError(f"navigation_info_double_click_on_element('{element_name}') failed. Problem: {e}")

    # ✅
    def navigation_info_open_element_details(self, element_name: str, timeout: int = 5000):
        """
        Opens the element details panel by single-clicking the element
        in the Navigation Info tree.
        """
        self.show_navigation_info()
        row = self.nav_row_locator(element_name)
        expect(row).to_be_visible(timeout=timeout)

        try:
            row.scroll_into_view_if_needed()
            row.click()

            # Details panel title (left panel)
            panel_title = self.page.locator(
                "xpath=//div[contains(@class,'details') or contains(@class,'modal')]"
                "//span[contains(normalize-space(.), '{}')]".format(element_name.split("/")[0]))
            
            sleep(1)

            # Fallback: close button visibility means panel is open
            close_btn = self.page.locator(
                "xpath=//*[name()='svg']"
                "/ancestor::*[self::button or self::div][1]")
            
            sleep(1)

            self.wait_until(lambda: panel_title.count() > 0 or close_btn.count() > 0, timeout_ms=timeout,interval_ms=200)

        except Exception as e:
            raise AssertionError(f"navigation_info_open_element_details('{element_name}') failed: {e}")

    # ✅
    def navigation_info_close_element_details(self, timeout: int = 5000):
        """
        Close the opened Node Properties (details) panel by clicking the X (close-square) icon.
        Asserts that the node-properties container disappears.
        """
        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        close_icon = panel.locator(".node-properties-header .controls app-icon[name='close-square']").first
        expect(close_icon).to_be_visible(timeout=timeout)

        # click the icon (or inner <i>)
        target = close_icon.locator("i").first
        if target.count() > 0:
            target.click(timeout=timeout, force=True)
        else:
            close_icon.click(timeout=timeout, force=True)

        # assert closed
        expect(panel).to_be_hidden(timeout=timeout)
        sleep(1)

    # ✅  
    def navigation_info_expand_element_byClick_on_arrow(self, element_name: str, timeout: int = 5000):
        """
        Expands an element in Navigation Info by clicking its arrow icon
        and waits until its children container becomes visible.
        """
        row = self.nav_row_locator(element_name)
        expect(row).to_be_visible(timeout=timeout)

        arrow = row.locator("xpath=ancestor::header//app-icon[@name='arrow-down']")
        collapse = row.locator("xpath=ancestor::header/following-sibling::div[contains(@class,'collapse')]")

        try:
            # If already open → do nothing
            if collapse.get_attribute("aria-hidden") == "false":
                return

            arrow.click()

            self.wait_until(lambda: collapse.get_attribute("aria-hidden") == "false", timeout_ms=timeout, interval_ms=200
            )

            sleep(1)

        except Exception as e:
            raise AssertionError(f"navigation_info_open_element_details('{element_name}') failed: {e}") 
    
    # ✅
    def navigation_info_shrink_element_byClick_on_arrow(self, element_name: str, timeout: int = 5000):
        """
        Collapses an element in Navigation Info by clicking its toggle (arrow) and
        waits until its children container becomes hidden (aria-hidden='true').
        """
        row = self.nav_row_locator(element_name)
        expect(row).to_be_visible(timeout=timeout)
        row.scroll_into_view_if_needed()

        header = row.locator("xpath=ancestor::header[1]")
        expect(header).to_be_visible(timeout=timeout)

        # The collapsible children container is the next sibling after the header
        collapse = header.locator("xpath=following-sibling::div[contains(@class,'collapse')][1]")
        expect(collapse).to_be_attached(timeout=timeout)

        try:
            # If already closed -> do nothing
            if (collapse.get_attribute("aria-hidden") or "").lower() == "true":
                return

            # Try to click the real arrow (down/up arrow) if it exists 
            arrow = header.locator("xpath=.//app-icon[contains(@name,'arrow') or contains(@name,'chevron') or contains(@name,'caret')]").first

            if arrow.count() > 0:
                arrow.click(timeout=timeout, force=True)
            else:
                # Fallback: clicking the title area often toggles collapse too
                header.locator("div.inventory-tree-level-title-content").click(timeout=timeout, force=True)

            # Wait until it becomes closed
            self.wait_until(lambda: (collapse.get_attribute("aria-hidden") or "").lower() == "true",timeout_ms=timeout,interval_ms=200)

            # Optional extra guard (display none)
            self.wait_until(lambda: "none" in ((collapse.get_attribute("style") or "").lower()), timeout_ms=timeout,interval_ms=200)

            sleep(1)

        except Exception as e:
            raise AssertionError(f"navigation_info_shrink_element_byClick_on_arrow('{element_name}') failed: {e}")
    

    # ==========================================================
    # Element details
    # ==========================================================

    # ✅
    def element_details_click_format(self, label_text: str, timeout: int = 5000):
        """
        In the Node Properties (element details) panel:
        Click the top-level tab(Chassis/Services/Faults/Info).
        """

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        tab = panel.locator(f"tabset.secondary ul.nav-tabs a.nav-link:has(span:has-text('{label_text}'))").first
        expect(tab).to_be_visible(timeout=timeout)

        def is_active() -> bool:
            cls = (tab.get_attribute("class") or "")
            aria = (tab.get_attribute("aria-selected") or "").strip().lower()
            return ("active" in cls.split()) or (aria == "true")

        # already selected
        if is_active():
            return

        tab.scroll_into_view_if_needed()
        tab.click(force=True)

        try:
            self.wait_until(is_active, timeout_ms=timeout, interval_ms=200)
            expect(tab).to_have_class(re.compile(r"\bactive\b"), timeout=timeout)
            sleep(2)
        except Exception as e:
            raise AssertionError(f"element_details_click_on_{label_text.lower()} failed: tab did not become active. Problem: {e}")

    # ✅
    def element_details_click_on_chassis(self):
        self.element_details_click_format("Chassis")

    # ✅
    def element_details_click_on_links(self):
        self.element_details_click_format("Links")

    # ✅
    def element_details_click_on_services(self):
        self.element_details_click_format("Services")

    # ✅
    def element_details_click_on_faults(self):
        self.element_details_click_format("Faults")

    # ✅
    def element_details_click_on_info(self):
        self.element_details_click_format("Info")

    # ==========================================================
    # Links 
    # ==========================================================
    
    # ✅
    def element_details_links_click_on_add_link(self, timeout: int = 5000):
        """
        In the Node Properties panel → Links tab:
        Click the "Add Link" button.
        """
        # Make sure we are on Links main tab first
        self.element_details_click_on_links()
        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        btn = panel.locator("app-node-overview-properties .node-overview-footer button.btn-stroke:has-text('Add Link')").first
        try:
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.scroll_into_view_if_needed()
            btn.click()
        except Exception as e:
            raise AssertionError(f"element_details_links_click_on_add_link failed: {e}")

    # ✅
    def element_details_links_set_Mode(self, mode: str, timeout: int = 5000):
        """
        In the Node Properties panel → Add Link form:
        Select the link "Mode" (e.g. "CS") from the Mode dropdown.
        """
        form = self.page.locator("app-node-properties-add-link").first
        expect(form).to_be_visible(timeout=timeout)

        dropdown = form.locator("app-dropdown[formcontrolname='mode']").first
        toggle = dropdown.locator("button.dropdown-toggle").first
        selected = dropdown.locator(".selected-view span").first
        try:
            expect(toggle).to_be_visible(timeout=timeout)

            # already selected
            if (selected.inner_text() or "").strip() == mode:
                return

            toggle.click()
            option = dropdown.locator("ul li.dropdown-item").filter(has_text=re.compile(rf"^\s*{re.escape(mode)}\s*$")).first
            expect(option).to_be_visible(timeout=timeout)
            option.click()
            expect(selected).to_have_text(re.compile(rf"^\s*{re.escape(mode)}\s*$"), timeout=timeout)
        except Exception as e:
            raise AssertionError(f"element_details_links_set_Mode('{mode}') failed: {e}")

    # ✅
    def element_details_links_set_side_B(self, side_b: str, timeout: int = 5000):
        """
        In the Node Properties panel → Add Link form:
        Select the "Side B" target node (e.g. "WDC-12/12") from the Side B dropdown.
        """
        form = self.page.locator("app-node-properties-add-link").first
        expect(form).to_be_visible(timeout=timeout)

        dropdown = form.locator("app-dropdown[formcontrolname='targetNode']").first
        toggle = dropdown.locator("button.dropdown-toggle").first
        selected = dropdown.locator(".selected-view span").first
        exact = re.compile(rf"^\s*{re.escape(side_b)}\s*$")
        try:
            expect(toggle).to_be_visible(timeout=timeout)

            # already selected
            if (selected.inner_text() or "").strip() == side_b:
                return

            toggle.click()
            option = dropdown.locator("ul li.dropdown-item").filter(has_text=exact).first
            expect(option).to_be_visible(timeout=timeout)
            option.scroll_into_view_if_needed()
            option.click()
            expect(selected).to_have_text(exact, timeout=timeout)
        except Exception as e:
            raise AssertionError(f"element_details_links_set_side_B('{side_b}') failed: {e}")

    # ✅
    def element_details_links_set_binding(self, binding: str, timeout: int = 5000):
        """
        In the Node Properties panel → Add Link form:
        Select the "Binding" (e.g. "No link") from the Binding dropdown.
        """
        form = self.page.locator("app-node-properties-add-link").first
        expect(form).to_be_visible(timeout=timeout)

        dropdown = form.locator("app-dropdown[formcontrolname='binding']").first
        toggle = dropdown.locator("button.dropdown-toggle").first
        selected = dropdown.locator(".selected-view span").first
        exact = re.compile(rf"^\s*{re.escape(binding)}\s*$")
        try:
            expect(toggle).to_be_visible(timeout=timeout)

            # already selected
            if (selected.inner_text() or "").strip() == binding:
                return

            toggle.click()
            option = dropdown.locator("ul li.dropdown-item").filter(has_text=exact).first
            expect(option).to_be_visible(timeout=timeout)
            option.scroll_into_view_if_needed()
            option.click()
            expect(selected).to_have_text(exact, timeout=timeout)
        except Exception as e:
            raise AssertionError(f"element_details_links_set_binding('{binding}') failed: {e}")

    # ✅
    def element_details_links_cancel_link(self, timeout: int = 5000):
        """
        In the Node Properties panel → Add Link form:
        Click the "Cancel" button.
        """
        form = self.page.locator("app-node-properties-add-link").first
        expect(form).to_be_visible(timeout=timeout)

        btn = form.locator("button.node-properties-add-link-cancel").first
        try:
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.scroll_into_view_if_needed()
            btn.click()
        except Exception as e:
            raise AssertionError(f"element_details_links_cancel_link failed: {e}")

    # ✅
    def element_details_links_click_on_ROADM_link_editor(self, timeout: int = 5000):
        """
        In the Node Properties panel → Links tab:
        Click the "ROADM Link Editor" button.
        """
        # Make sure we are on Links main tab first
        self.element_details_click_on_links()
        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        btn = panel.locator("app-node-overview-properties .node-overview-footer button.btn-primary:has-text('ROADM Link Editor')").first
        try:
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.scroll_into_view_if_needed()
            btn.click()
        except Exception as e:
            raise AssertionError(f"element_details_links_click_on_ROADM_link_editor failed: {e}")

    # ✅
    def element_details_links_ROADM_link_editor_click_on_port(self, device_ip: str, port_name: str, timeout: int = 5000):
        """
        In the ROADM Link Editor map:
        Click a port (e.g. "Port 3") under the device card identified by its IP (e.g. "10.60.100.30").
        """
        card = self.page.locator(f"app-device-view-card[data-id='{device_ip}']").first
        sleep(1)
        exact = re.compile(rf"^\s*{re.escape(port_name)}\s*$")
        try:
            expect(card).to_be_visible(timeout=timeout)

            row = card.locator(".schematic-list-connection").filter(has=self.page.locator("span", has_text=exact)).first
            sleep(1)

            expect(row).to_be_visible(timeout=timeout)
            row.scroll_into_view_if_needed()
            sleep(1)
            row.click()
        except Exception as e:
            raise AssertionError(f"element_details_links_ROADM_link_editor_click_on_port('{device_ip}', '{port_name}') failed: {e}")

    # ✅
    def element_details_links_ROADM_link_editor_click_on_ELP(self, elp_label: str, chassis_name: str = None,
                                                             chassis_id: str = None, timeout: int = 5000):
        """
        In the ROADM Link Editor map:
        Click an ELP by its label (e.g. "ELP 2" or "ELP2").

        When the map shows several chassis side by side (after following an ELP
        to the connected chassis), scope the search to one chassis by its header
        name (chassis_name, e.g. "NY-16" or "HAR -14") and/or its data-chassis-id (chassis_id, e.g. "16").
        """
        # "ELP 2" / "ELP2" -> ^\s*ELP\s*2\s*$ (the label is split across two spans)
        digits = re.sub(r"(?i)^\s*ELP\s*", "", elp_label).strip()
        label_re = re.compile(rf"^\s*ELP\s*{re.escape(digits)}\s*$")

        scope = self.page.locator(".chassis-card")
        sleep(1)
        if chassis_id is not None:
            scope = self.page.locator(f".chassis-card[data-chassis-id='{chassis_id}']")
            sleep(1)
        if chassis_name is not None:
            # allow optional whitespace between characters: "HAR-14" -> H\s*A\s*R\s*-\s*1\s*4
            name_re = re.compile(r"^\s*" + r"\s*".join(re.escape(c) for c in chassis_name if not c.isspace()) + r"\s*$")
            scope = scope.filter(has=self.page.locator(".chassis-card-header > span:first-child", has_text=name_re))

        scope = scope.first
        try:
            if chassis_name is not None or chassis_id is not None:
                expect(scope).to_be_visible(timeout=timeout)
            elp = scope.locator(".elp-port").filter(has_text=label_re).first
            sleep(1)

            expect(elp).to_be_visible(timeout=timeout)
            elp.scroll_into_view_if_needed()
            sleep(1)
            elp.click()
        except Exception as e:
            raise AssertionError(
                f"element_details_links_ROADM_link_editor_click_on_ELP('{elp_label}', chassis_name={chassis_name}, "
                f"chassis_id={chassis_id}) failed: {e}"
            )

    # ✅
    def roadm_link_editor_set_filter(self, filter_name: str, show: bool, timeout: int = 5000):
        """
        Turn one of the ROADM Link Editor link filters (internal / devices / external)
        on or off by clicking its toggle in the bottom-left filter bar.
        Clicks only if the filter is not already in the requested state.
        """
        btn = self.page.locator(f"section.chassis-editor-controls-filters div.filter.{filter_name}").first
        sleep(1)

        def is_on() -> bool:
            tokens = set((btn.get_attribute("class") or "").split())
            if tokens & {"inactive", "disabled", "off", "hidden", "unselected"}:
                return False
            pressed = (btn.get_attribute("aria-pressed") or "").strip().lower()
            return pressed != "false"

        action = "show" if show else "hide"
        try:
            expect(btn).to_be_visible(timeout=timeout)

            # already in the requested state
            if is_on() == show:
                return

            sleep(0.5)
            btn.click()
            self.wait_until(lambda: is_on() == show, timeout_ms=timeout, interval_ms=200)
        except Exception as e:
            raise AssertionError(f"element_details_links_ROADM_link_editor_{action}_{filter_name} failed: {e}")

    # ✅
    def element_details_links_ROADM_link_editor_show_internal(self, timeout: int = 5000):
        """
        In the ROADM Link Editor map:
        Turn the "Internal" links filter on (internal links become visible).
        """
        self.roadm_link_editor_set_filter("internal", True, timeout)

    # ✅
    def element_details_links_ROADM_link_editor_hide_internal(self, timeout: int = 5000):
        """
        In the ROADM Link Editor map:
        Turn the "Internal" links filter off (internal links are hidden).
        """
        self.roadm_link_editor_set_filter("internal", False, timeout)

    # ✅
    def element_details_links_ROADM_link_editor_show_devices(self, timeout: int = 5000):
        """
        In the ROADM Link Editor map:
        Turn the "Devices" links filter on (device links become visible).
        """
        self.roadm_link_editor_set_filter("devices", True, timeout)
    
    # ✅
    def element_details_links_ROADM_link_editor_hide_devices(self, timeout: int = 5000):
        """
        In the ROADM Link Editor map:
        Turn the "Devices" links filter off (device links are hidden).
        """
        self.roadm_link_editor_set_filter("devices", False, timeout)

    # ✅
    def element_details_links_ROADM_link_editor_show_external(self, timeout: int = 5000):
        """
        In the ROADM Link Editor map:
        Turn the "External" links filter on (external links become visible).
        """
        self.roadm_link_editor_set_filter("external", True, timeout)

    # ✅
    def element_details_links_ROADM_link_editor_hide_external(self, timeout: int = 5000):
        """
        In the ROADM Link Editor map:
        Turn the "External" links filter off (external links are hidden).
        """
        self.roadm_link_editor_set_filter("external", False, timeout)


    # ==========================================================
    # Links → External MNG links
    # ==========================================================
    
    # ✅
    def element_details_links_click_on_external_MNG_links(self, timeout: int = 5000):
        """
        In the Node Properties panel → Links tab:
        Click the "External MNG links" sub-tab.
        """
        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        tab = panel.locator("tabset.node-overview-type-tabs ul.nav-tabs a.nav-link:has(span:has-text('External MNG links'))").first
        try:
            expect(tab).to_be_visible(timeout=timeout)

            # already selected
            if "active" in (tab.get_attribute("class") or "").split():
                return

            tab.scroll_into_view_if_needed()
            tab.click()
            expect(tab).to_have_class(re.compile(r"\bactive\b"), timeout=timeout)
        except Exception as e:
            raise AssertionError(f"element_details_links_click_on_external_MNG_links failed: {e}")

    # ✅
    def element_details_links_get_external_MNG_links(self, timeout: int = 5000) -> list:
        """
        Returns the list of links currently shown in Links -> External MNG links.

        Output example:
        [{'Side_A': 'PL-4000M (172.16.40.21)', 'Side_A_Info': '172.16.40.21 | MNG 1',
        'Link_Type': 'TOPO', 'Severity': 'positive',
        'Side_B': 'PL-4000M (172.16.30.119)', 'Side_B_Info': '172.16.30.119 | MNG 2'}]
        """
        self.element_details_links_click_on_external_MNG_links(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        pane = panel.locator("tabset.node-overview-type-tabs .tab-content > tab.tab-pane.active").first
        expect(pane).to_be_visible(timeout=timeout)

        rows = pane.locator(".node-overview-link-row")
        empty = pane.locator("p.node-overview-empty")

        # Rows render a moment after the tab switch: wait for either rows or the "No external links" text
        try:
            self.wait_until(lambda: rows.count() > 0 or empty.count() > 0, timeout_ms=timeout, interval_ms=200)
        except Exception as e:
            raise AssertionError(f"element_details_links_get_external_MNG_links failed: neither links nor the empty message appeared. Problem: {e}")

        def clean(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "").strip())

        out = []
        for i in range(rows.count()):
            row = rows.nth(i)
            side_a = row.locator(".node-overview-item-content:not(.node-overview-item-content-right)").first
            side_b = row.locator(".node-overview-item-content.node-overview-item-content-right").first

            line_cls = row.locator(".node-overview-link-line").first.get_attribute("class") or ""
            m = re.search(r"node-overview-severity-(\w+)", line_cls)

            out.append({
                "Side_A": clean(side_a.locator(".node-overview-title").first.inner_text(timeout=timeout)),
                "Side_A_Info": clean(side_a.locator(".node-overview-meta").first.inner_text(timeout=timeout)),
                "Link_Type": clean(row.locator(".node-overview-link-type").first.inner_text(timeout=timeout)),
                "Severity": m.group(1) if m else "",
                "Side_B": clean(side_b.locator(".node-overview-title").first.inner_text(timeout=timeout)),
                "Side_B_Info": clean(side_b.locator(".node-overview-meta").first.inner_text(timeout=timeout)),
            })
        return out

    # ✅
    def element_details_links_external_MNG_links_click_on_the_3_dots(self, side_a: str, side_b: str, timeout: int = 5000):
        """
        In Links -> External MNG links:
        Click the 3-dots (link actions) button of the link whose sides match
        side_a + side_b, using the same values element_details_links_get_external_MNG_links returns.
        Each side matches either its title or its info line. 
        If several rows match, the first one is used.
        """
        self.element_details_links_click_on_external_MNG_links(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        pane = panel.locator("tabset.node-overview-type-tabs .tab-content > tab.tab-pane.active").first
        expect(pane).to_be_visible(timeout=timeout)

        def clean(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "").strip())

        def side_matches(side, wanted: str) -> bool:
            texts = [
                side.locator(".node-overview-title").first.inner_text(timeout=timeout),
                side.locator(".node-overview-meta").first.inner_text(timeout=timeout),
            ]
            return clean(wanted) in [clean(t) for t in texts]

        rows = pane.locator(".node-overview-link-row")
        try:
            self.wait_until(lambda: rows.count() > 0, timeout_ms=timeout, interval_ms=200)

            for i in range(rows.count()):
                row = rows.nth(i)
                a = row.locator(".node-overview-item-content:not(.node-overview-item-content-right)").first
                b = row.locator(".node-overview-item-content.node-overview-item-content-right").first
                if side_matches(a, side_a) and side_matches(b, side_b):
                    btn = row.locator("button.node-overview-link-actions-button").first
                    expect(btn).to_be_visible(timeout=timeout)
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    return
            raise AssertionError(f"no external link row matches Side A '{side_a}' / Side B '{side_b}'")
        except Exception as e:
            raise AssertionError(
                f"element_details_links_external_MNG_links_click_on_the_3_dots('{side_a}', '{side_b}') failed: {e}"
            )

    # ✅
    def element_details_links_external_MNG_links_delete_link(self, side_a: str, side_b: str, timeout: int = 5000):
        """
        In Links -> External MNG links:
        Open the 3-dots menu of the link matching side_a / side_b and click "Delete link".
        """
        # Click the menu *button* (not the inner span): the menu can be re-rendered
        # while it is open, which detaches the element mid-click. If that happens,
        # reopen the menu and try again.
        item = self.page.locator(
            "div.node-overview-link-actions-menu button[role='menuitem']:has-text('Delete link')"
        ).first
        last_error = None
        for _ in range(3):
            try:
                self.element_details_links_external_MNG_links_click_on_the_3_dots(side_a, side_b, timeout=timeout)
                expect(item).to_be_visible(timeout=timeout)
                item.click(timeout=3000)
                return
            except Exception as e:
                last_error = e
                sleep(0.5)
        raise AssertionError(
            f"element_details_links_external_MNG_links_delete_link('{side_a}', '{side_b}') failed: {last_error}")



    # ==========================================================
    # Links → Internal MNG links
    # ==========================================================
    
    # ✅
    def element_details_links_click_on_internal_MNG_links(self, timeout: int = 5000):
        """
        In the Node Properties panel → Links tab:
        Click the "Internal MNG links" sub-tab.
        """
        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        tab = panel.locator("tabset.node-overview-type-tabs ul.nav-tabs a.nav-link:has(span:has-text('Internal MNG links'))").first
        try:
            expect(tab).to_be_visible(timeout=timeout)

            # already selected
            if "active" in (tab.get_attribute("class") or "").split():
                return

            tab.scroll_into_view_if_needed()
            tab.click()
            expect(tab).to_have_class(re.compile(r"\bactive\b"), timeout=timeout)
        except Exception as e:
            raise AssertionError(f"element_details_links_click_on_internal_MNG_links failed: {e}")

    def element_details_links_get_internal_MNG_links(self):
        """
        
        """
        pass

    def element_details_links_internal_MNG_links_click_on_the_3_dots(self):
        """
        
        """
        pass

    def element_details_links_internal_MNG_links_delete_link(self):
        """
        
        """
        pass

    # ==========================================================
    # Links → Devices
    # ==========================================================
    
    # ✅
    def element_details_links_click_on_Devices(self, timeout: int = 5000):
        """
        In the Node Properties panel → Links tab:
        Click the "Devices" sub-tab.
        """
        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        tab = panel.locator("tabset.node-overview-type-tabs ul.nav-tabs a.nav-link:has(span:has-text('Devices'))").first
        try:
            expect(tab).to_be_visible(timeout=timeout)

            # already selected
            if "active" in (tab.get_attribute("class") or "").split():
                return

            tab.scroll_into_view_if_needed()
            tab.click()
            expect(tab).to_have_class(re.compile(r"\bactive\b"), timeout=timeout)
        except Exception as e:
            raise AssertionError(f"element_details_links_click_on_Devices failed: {e}")

    # ✅
    def element_details_links_get_devices(self, timeout: int = 5000) -> list:
        """
        Returns the list of devices currently shown in Links -> Devices
        (empty list when the tab shows an empty message instead of rows).
        Output example:
        [
        {'Device': 'PL-4000M (172.16.40.21)', 'Info': '172.16.40.21 | PL-4000M | Muxponder',
        'IP': '172.16.40.21', 'Model': 'PL-4000M', 'Type': 'Muxponder'}
        ]
        """
        self.element_details_links_click_on_Devices(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        pane = panel.locator("tabset.node-overview-type-tabs .tab-content > tab.tab-pane.active").first
        expect(pane).to_be_visible(timeout=timeout)

        rows = pane.locator(".node-overview-device-row")
        empty = pane.locator("p.node-overview-empty")

        # Rows render a moment after the tab switch: wait for either rows or an empty message
        try:
            self.wait_until(lambda: rows.count() > 0 or empty.count() > 0, timeout_ms=timeout, interval_ms=200)
        except Exception as e:
            raise AssertionError(f"element_details_links_get_devices failed: neither devices nor an empty message appeared. Problem: {e}")

        def clean(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "").strip())

        out = []
        for i in range(rows.count()):
            content = rows.nth(i).locator(".node-overview-item-content").first
            title = clean(content.locator(".node-overview-title").first.inner_text(timeout=timeout))
            info = clean(content.locator(".node-overview-meta").first.inner_text(timeout=timeout))

            # "172.16.40.21 | PL-4000M | Muxponder"
            parts = [p.strip() for p in info.split("|")]
            out.append({
                "Device": title,
                "Info": info,
                "IP": parts[0] if len(parts) > 0 else "",
                "Model": parts[1] if len(parts) > 1 else "",
                "Type": parts[2] if len(parts) > 2 else "",
            })
        return out

    # ✅
    def element_details_links_Devices_click_on_the_3_dots(self, device: str, timeout: int = 5000):
        """
        In Links -> Devices:
        Click the 3-dots (device actions) button of the given device. `device` is
        the name element_details_links_get_devices returns (e.g. "PL-4000M (172.16.40.21)");
        its IP (e.g. "172.16.40.21") or full info line also match.
        If several rows match, the first one is used.
        """
        self.element_details_links_click_on_Devices(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        pane = panel.locator("tabset.node-overview-type-tabs .tab-content > tab.tab-pane.active").first
        expect(pane).to_be_visible(timeout=timeout)

        def clean(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "").strip())

        wanted = clean(device)
        rows = pane.locator(".node-overview-device-row")
        try:
            self.wait_until(lambda: rows.count() > 0, timeout_ms=timeout, interval_ms=200)

            for i in range(rows.count()):
                row = rows.nth(i)
                title = clean(row.locator(".node-overview-title").first.inner_text(timeout=timeout))
                info = clean(row.locator(".node-overview-meta").first.inner_text(timeout=timeout))
                ip = info.split("|")[0].strip()
                if wanted in (title, info, ip):
                    btn = row.locator("button.node-overview-device-actions-button").first
                    expect(btn).to_be_visible(timeout=timeout)
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    return
            raise AssertionError(f"no device row matches '{device}'")
        except Exception as e:
            raise AssertionError(f"element_details_links_Devices_click_on_the_3_dots('{device}') failed: {e}")

    # ✅
    def element_details_links_Devices_show_inventory(self, device: str, timeout: int = 5000):
        """
        In Links -> Devices:
        Open the 3-dots menu of the given device (same `device` values as
        element_details_links_Devices_click_on_the_3_dots) and click "Show Inventory".
        """
        # The menu can be re-rendered while it is open, which detaches the element
        # mid-click. If that happens, reopen the menu and try again.
        item = self.page.locator(
            "div.node-overview-device-actions-menu button[role='menuitem']:has-text('Show Inventory')"
        ).first
        last_error = None
        for _ in range(3):
            try:
                self.element_details_links_Devices_click_on_the_3_dots(device, timeout=timeout)
                expect(item).to_be_visible(timeout=timeout)
                item.click(timeout=3000)
                return
            except Exception as e:
                last_error = e
                sleep(0.5)
        raise AssertionError(f"element_details_links_Devices_show_inventory('{device}') failed: {last_error}")

    # ==========================================================
    # Services 
    # ==========================================================

    def element_details_services_click_on_add_service(self, timeout: int = 5000):
        """
        In the Node Properties panel → Services tab:
        Click the "Add Service" button.
        """
        # Make sure we are on Services main tab first
        self.element_details_click_on_services()
        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        btn = panel.locator("app-node-properties-services-tab .node-services-footer button.btn-primary:has-text('Add Service')").first
        try:
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.scroll_into_view_if_needed()
            btn.click()
        except Exception as e:
            raise AssertionError(f"element_details_services_click_on_add_service failed: {e}")

    def element_details_services_click_on_show_all(self, timeout: int = 5000):
        """
        In the Node Properties panel → Services tab:
        Click the "Show All" button.
        """
        # Make sure we are on Services main tab first
        self.element_details_click_on_services()
        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        btn = panel.locator("app-node-properties-services-tab .node-services-footer button.btn-stroke:has-text('Show All')").first
        try:
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.scroll_into_view_if_needed()
            btn.click()
        except Exception as e:
            raise AssertionError(f"element_details_services_click_on_show_all failed: {e}")

    def element_details_services_click_on_bandwidth(self):
        """
        
        """
        pass

    # ==========================================================
    # Services → OTN
    # ==========================================================
    
    def element_details_services_click_format(self, label_text: str, timeout: int = 5000):
        """
        In the Node Properties panel → Services tab:
        Click a services sub-tab (OTN / ROADM / CS).
        """
        # Make sure we are on Services main tab first
        self.element_details_click_on_services()
        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        tab = panel.locator("tabset.node-services-type-tabs ul.nav-tabs a.nav-link").filter(
            has=self.page.locator("span", has_text=re.compile(rf"^\s*{re.escape(label_text)}\s*$"))
        ).first
        try:
            expect(tab).to_be_visible(timeout=timeout)

            # already selected
            if "active" in (tab.get_attribute("class") or "").split():
                return

            tab.scroll_into_view_if_needed()
            tab.click()
            expect(tab).to_have_class(re.compile(r"\bactive\b"), timeout=timeout)
        except Exception as e:
            raise AssertionError(f"element_details_services_click_on_{label_text} failed: {e}")

    def element_details_services_click_on_OTN(self, timeout: int = 5000):
        """
        In the Node Properties panel → Services tab:
        Click the "OTN" sub-tab.
        """
        self.element_details_services_click_format("OTN", timeout=timeout)

    def element_details_services_OTN_get_all_services(self, timeout: int = 5000) -> list:
        """
        Returns the list of services currently shown in Services -> OTN
        (empty list when the tab shows "No OTN services").
        Output example:
        [
        {'Service': 'Service 1', 'A': 'PL-4000M (172.16.30.120):Port 1', 'Z': 'PL-4000M (172.16.30.119):Port 1',
        'Service_Type': '100GbE-LAN', 'Protection': 'Protected', 'State': 'Consistent'}
        ]
        """
        self.element_details_services_click_on_OTN(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        pane = panel.locator("tabset.node-services-type-tabs .tab-content > tab.tab-pane.active").first
        expect(pane).to_be_visible(timeout=timeout)

        services = pane.locator("app-service-list")
        empty = pane.locator(".node-services-empty")

        # The list renders a moment after the tab switch: wait for either services or the empty message
        try:
            self.wait_until(lambda: services.count() > 0 or empty.count() > 0, timeout_ms=timeout, interval_ms=200)
        except Exception as e:
            raise AssertionError(f"element_details_services_OTN_get_all_services failed: neither services nor the empty message appeared. Problem: {e}")

        def clean(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "").strip())

        out = []
        # The list is scrollable, but every service is in the DOM, so text can be read without scrolling
        for i in range(services.count()):
            svc = services.nth(i)

            name = clean(svc.locator(".name").first.text_content(timeout=timeout)).rstrip(":").strip()

            points = {}
            pts = svc.locator(".points .point")
            for j in range(pts.count()):
                label = clean(pts.nth(j).locator(".label").first.text_content(timeout=timeout)).rstrip(":")
                points[label] = clean(pts.nth(j).locator(".value").first.text_content(timeout=timeout))

            info = clean(svc.locator(".meta .info").first.text_content(timeout=timeout))
            state = clean(svc.locator(".meta .state").first.text_content(timeout=timeout))

            # "100GbE-LAN | Protected"
            parts = [p.strip() for p in info.split("|")]
            out.append({
                "Service": name,
                "A": points.get("A", ""),
                "Z": points.get("Z", ""),
                "Service_Type": parts[0] if len(parts) > 0 else "",
                "Protection": parts[1] if len(parts) > 1 else "",
                "State": state,
            })
        return out

    def element_details_services_OTN_click_on_the_3_dots(self, service: str, timeout: int = 5000):
        """
        In Services -> OTN:
        Click the 3-dots button of the given service. `service` is the name
        element_details_services_OTN_get_all_services returns (e.g. "Service 1");
        a trailing colon is ignored.
        """
        self.element_details_services_click_on_OTN(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        pane = panel.locator("tabset.node-services-type-tabs .tab-content > tab.tab-pane.active").first
        expect(pane).to_be_visible(timeout=timeout)

        wanted = re.sub(r"\s+", " ", service.strip()).rstrip(":").strip()
        name_re = re.compile(rf"^\s*{re.escape(wanted)}\s*:?\s*$")
        try:
            # The list is scrollable: the button is scrolled into view before the click
            entry = pane.locator("app-service-list").filter(
                has=self.page.locator(".name", has_text=name_re)
            ).first
            expect(entry).to_be_attached(timeout=timeout)

            btn = entry.locator("button.mat-mdc-menu-trigger").first
            btn.scroll_into_view_if_needed()
            expect(btn).to_be_visible(timeout=timeout)
            btn.click()
        except Exception as e:
            raise AssertionError(f"element_details_services_OTN_click_on_the_3_dots('{service}') failed: {e}")

    def element_details_services_OTN_navigate_to_service(self, service: str, timeout: int = 5000):
        """
        In Services -> OTN:
        Open the 3-dots menu of the given service (same `service` values as
        element_details_services_OTN_click_on_the_3_dots) and click "Navigate to".
        """
        # The menu is a Material menu rendered in the CDK overlay (outside the panel).
        # Reopen the menu and retry if the click fails (e.g. the menu closed or re-rendered).
        item = self.page.locator(
            ".cdk-overlay-pane .mat-mdc-menu-panel button[role='menuitem']"
        ).filter(has_text=re.compile(r"^\s*Navigate to\s*$")).first
        last_error = None
        for _ in range(3):
            try:
                self.element_details_services_OTN_click_on_the_3_dots(service, timeout=timeout)
                expect(item).to_be_visible(timeout=timeout)
                item.click(timeout=3000)
                return
            except Exception as e:
                last_error = e
                sleep(0.5)
        raise AssertionError(f"element_details_services_OTN_navigate_to_service('{service}') failed: {last_error}")

    def element_details_services_OTN_rename_service_button(self, service: str, timeout: int = 5000):
        """
        In Services -> OTN:
        Open the 3-dots menu of the given service (same `service` values as
        element_details_services_OTN_click_on_the_3_dots) and click "Rename".
        """
        # The menu is a Material menu rendered in the CDK overlay (outside the panel).
        # Reopen the menu and retry if the click fails (e.g. the menu closed or re-rendered).
        item = self.page.locator(
            ".cdk-overlay-pane .mat-mdc-menu-panel button[role='menuitem']"
        ).filter(has_text=re.compile(r"^\s*Rename\s*$")).first
        last_error = None
        for _ in range(3):
            try:
                self.element_details_services_OTN_click_on_the_3_dots(service, timeout=timeout)
                expect(item).to_be_visible(timeout=timeout)
                item.click(timeout=3000)
                return
            except Exception as e:
                last_error = e
                sleep(0.5)
        raise AssertionError(f"element_details_services_OTN_rename_service_button('{service}') failed: {last_error}")

    def element_details_services_OTN_rename_service(self, service: str, new_name: str, timeout: int = 5000):
        """
        In Services -> OTN:
        Rename the given service (same `service` values as
        element_details_services_OTN_click_on_the_3_dots): open its 3-dots menu,
        click "Rename", set the new name in the "Rename Service" dialog and click "Rename".
        """
        self.element_details_services_OTN_rename_service_button(service, timeout=timeout)

        dialog = self.page.locator("div.service-dialog[aria-labelledby='service-dialog-title-rename']").first
        try:
            expect(dialog).to_be_visible(timeout=timeout)

            field = dialog.locator("input.service-dialog-input").first
            expect(field).to_be_visible(timeout=timeout)
            field.fill(new_name)
            expect(field).to_have_value(new_name, timeout=timeout)

            btn = dialog.locator("button.btn-primary:has-text('Rename')").first
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()

            # The dialog closes once the rename is accepted
            expect(dialog).to_be_hidden(timeout=timeout)
        except Exception as e:
            raise AssertionError(f"element_details_services_OTN_rename_service('{service}', '{new_name}') failed: {e}")

    def element_details_services_OTN_cancel_rename_service(self, timeout: int = 5000):
        """
        In the "Rename Service" dialog (opened by element_details_services_OTN_rename_service_button):
        Click the "Cancel" button and wait for the dialog to close.
        """
        dialog = self.page.locator("div.service-dialog[aria-labelledby='service-dialog-title-rename']").first
        try:
            expect(dialog).to_be_visible(timeout=timeout)

            btn = dialog.locator("button.btn-stroke:has-text('Cancel')").first
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()

            expect(dialog).to_be_hidden(timeout=timeout)
        except Exception as e:
            raise AssertionError(f"element_details_services_OTN_cancel_rename_service failed: {e}")

    def element_details_services_OTN_remove_service_button(self, service: str, timeout: int = 5000):
        """
        In Services -> OTN:
        Open the 3-dots menu of the given service (same `service` values as
        element_details_services_OTN_click_on_the_3_dots) and click "Remove".
        Only opens the removal flow; it does not confirm any dialog that follows.
        """
        # The menu is a Material menu rendered in the CDK overlay (outside the panel).
        # Reopen the menu and retry if the click fails (e.g. the menu closed or re-rendered).
        item = self.page.locator(
            ".cdk-overlay-pane .mat-mdc-menu-panel button[role='menuitem']"
        ).filter(has_text=re.compile(r"^\s*Remove\s*$")).first
        last_error = None
        for _ in range(3):
            try:
                self.element_details_services_OTN_click_on_the_3_dots(service, timeout=timeout)
                expect(item).to_be_visible(timeout=timeout)
                item.click(timeout=3000)
                return
            except Exception as e:
                last_error = e
                sleep(0.5)
        raise AssertionError(f"element_details_services_OTN_remove_service_button('{service}') failed: {last_error}")

    def element_details_services_OTN_remove_service(self, service: str, timeout: int = 5000):
        """
        In Services -> OTN:
        Remove the given service (same `service` values as
        element_details_services_OTN_click_on_the_3_dots): open its 3-dots menu,
        click "Remove" and confirm in the "Remove Service" dialog.
        """
        self.element_details_services_OTN_remove_service_button(service, timeout=timeout)

        dialog = self.page.locator("div.service-dialog[aria-labelledby='service-dialog-title-remove']").first
        try:
            expect(dialog).to_be_visible(timeout=timeout)

            # Safety check: make sure the dialog is about the service we meant to remove
            wanted = re.sub(r"\s+", " ", service.strip()).rstrip(":").strip()
            shown = re.sub(r"\s+", " ", dialog.locator(".service-dialog-serviceName").first.inner_text(timeout=timeout)).strip()
            if shown != wanted:
                raise AssertionError(f"dialog asks to remove '{shown}', expected '{wanted}'")

            btn = dialog.locator("button.btn-primary:has-text('Remove')").first
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()

            # The dialog closes once the removal is accepted
            expect(dialog).to_be_hidden(timeout=timeout)
        except Exception as e:
            raise AssertionError(f"element_details_services_OTN_remove_service('{service}') failed: {e}")

    def element_details_services_OTN_cancel_remove_service(self, timeout: int = 5000):
        """
        In the "Remove Service" dialog (opened by element_details_services_OTN_remove_service_button):
        Click the "Cancel" button and wait for the dialog to close.
        """
        dialog = self.page.locator("div.service-dialog[aria-labelledby='service-dialog-title-remove']").first
        try:
            expect(dialog).to_be_visible(timeout=timeout)

            btn = dialog.locator("button.btn-stroke:has-text('Cancel')").first
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()

            expect(dialog).to_be_hidden(timeout=timeout)
        except Exception as e:
            raise AssertionError(f"element_details_services_OTN_cancel_remove_service failed: {e}")

    # ==========================================================
    # Services → ROADM
    # ==========================================================
    
    def element_details_services_click_on_ROADM(self, timeout: int = 5000):
        """
        In the Node Properties panel → Services tab:
        Click the "ROADM" sub-tab.
        """
        self.element_details_services_click_format("ROADM", timeout=timeout)

    def element_details_services_ROADM_get_all_services(self, timeout: int = 5000) -> list:
        """
        Returns the list of services currently shown in Services -> ROADM
        (empty list when the tab shows the empty message).
        Output example:
        [
        {'Service': 'ssss', 'A': 'PL-1000GRO (10.60.100.50):Port 5', 'Z': 'PL-1000GRO (10.60.100.1):Port 6',
        'Info': '87.5GHZ C. Frequency: 191.61875THz', 'Bandwidth': '87.5GHZ', 'Frequency': '191.61875THz',
        'Protection': 'Unprotected', 'State': 'Consistent'}
        ]
        """
        self.element_details_services_click_on_ROADM(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        pane = panel.locator("tabset.node-services-type-tabs .tab-content > tab.tab-pane.active").first
        expect(pane).to_be_visible(timeout=timeout)

        services = pane.locator("app-service-list")
        empty = pane.locator(".node-services-empty")

        # The list renders a moment after the tab switch: wait for either services or the empty message
        try:
            self.wait_until(lambda: services.count() > 0 or empty.count() > 0, timeout_ms=timeout, interval_ms=200)
        except Exception as e:
            raise AssertionError(f"element_details_services_ROADM_get_all_services failed: neither services nor the empty message appeared. Problem: {e}")

        def clean(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "").strip())

        out = []
        # The list is scrollable, but every service is in the DOM, so text can be read without scrolling
        for i in range(services.count()):
            svc = services.nth(i)

            name = clean(svc.locator(".name").first.text_content(timeout=timeout)).rstrip(":").strip()

            points = {}
            pts = svc.locator(".points .point")
            for j in range(pts.count()):
                label = clean(pts.nth(j).locator(".label").first.text_content(timeout=timeout)).rstrip(":")
                points[label] = clean(pts.nth(j).locator(".value").first.text_content(timeout=timeout))

            info_line = clean(svc.locator(".meta .info").first.text_content(timeout=timeout))
            state = clean(svc.locator(".meta .state").first.text_content(timeout=timeout))

            # "87.5GHZ C. Frequency: 191.61875THz | Unprotected"
            parts = [p.strip() for p in info_line.split("|")]
            info = parts[0] if len(parts) > 0 else ""
            m = re.match(r"^(\S+)\s+C\.\s*Frequency:\s*(\S+)$", info)

            out.append({
                "Service": name,
                "A": points.get("A", ""),
                "Z": points.get("Z", ""),
                "Info": info,
                "Bandwidth": m.group(1) if m else "",
                "Frequency": m.group(2) if m else "",
                "Protection": parts[1] if len(parts) > 1 else "",
                "State": state,
            })
        return out

    def element_details_services_ROADM_click_on_the_3_dots(self, service: str, timeout: int = 5000):
        """
        In Services -> ROADM:
        Click the 3-dots button of the given service. `service` is the name
        element_details_services_ROADM_get_all_services returns (e.g. "test(1)");
        a trailing colon is ignored.
        """
        self.element_details_services_click_on_ROADM(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        pane = panel.locator("tabset.node-services-type-tabs .tab-content > tab.tab-pane.active").first
        expect(pane).to_be_visible(timeout=timeout)

        wanted = re.sub(r"\s+", " ", service.strip()).rstrip(":").strip()
        name_re = re.compile(rf"^\s*{re.escape(wanted)}\s*:?\s*$")
        try:
            # The list is scrollable: the button is scrolled into view before the click
            entry = pane.locator("app-service-list").filter(
                has=self.page.locator(".name", has_text=name_re)
            ).first
            expect(entry).to_be_attached(timeout=timeout)

            btn = entry.locator("button.mat-mdc-menu-trigger").first
            btn.scroll_into_view_if_needed()
            expect(btn).to_be_visible(timeout=timeout)
            btn.click()
        except Exception as e:
            raise AssertionError(f"element_details_services_ROADM_click_on_the_3_dots('{service}') failed: {e}")

    def element_details_services_ROADM_navigate_to_service(self, service: str, timeout: int = 5000):
        """
        In Services -> ROADM:
        Open the 3-dots menu of the given service (same `service` values as
        element_details_services_ROADM_click_on_the_3_dots) and click "Navigate to".
        """
        # The menu is a Material menu rendered in the CDK overlay (outside the panel).
        # Reopen the menu and retry if the click fails (e.g. the menu closed or re-rendered).
        item = self.page.locator(
            ".cdk-overlay-pane .mat-mdc-menu-panel button[role='menuitem']"
        ).filter(has_text=re.compile(r"^\s*Navigate to\s*$")).first
        last_error = None
        for _ in range(3):
            try:
                self.element_details_services_ROADM_click_on_the_3_dots(service, timeout=timeout)
                expect(item).to_be_visible(timeout=timeout)
                item.click(timeout=3000)
                return
            except Exception as e:
                last_error = e
                sleep(0.5)
        raise AssertionError(f"element_details_services_ROADM_navigate_to_service('{service}') failed: {last_error}")

    def element_details_services_ROADM_rename_service_button(self, service: str, timeout: int = 5000):
        """
        In Services -> ROADM:
        Open the 3-dots menu of the given service (same `service` values as
        element_details_services_ROADM_click_on_the_3_dots) and click "Rename".
        """
        # The menu is a Material menu rendered in the CDK overlay (outside the panel).
        # Reopen the menu and retry if the click fails (e.g. the menu closed or re-rendered).
        item = self.page.locator(
            ".cdk-overlay-pane .mat-mdc-menu-panel button[role='menuitem']"
        ).filter(has_text=re.compile(r"^\s*Rename\s*$")).first
        last_error = None
        for _ in range(3):
            try:
                self.element_details_services_ROADM_click_on_the_3_dots(service, timeout=timeout)
                expect(item).to_be_visible(timeout=timeout)
                item.click(timeout=3000)
                return
            except Exception as e:
                last_error = e
                sleep(0.5)
        raise AssertionError(f"element_details_services_ROADM_rename_service_button('{service}') failed: {last_error}")

    def element_details_services_ROADM_rename_service(self, service: str, new_name: str, timeout: int = 5000):
        """
        In Services -> ROADM:
        Rename the given service (same `service` values as
        element_details_services_ROADM_click_on_the_3_dots): open its 3-dots menu,
        click "Rename", set the new name in the "Rename Service" dialog and click "Rename".
        """
        self.element_details_services_ROADM_rename_service_button(service, timeout=timeout)

        dialog = self.page.locator("div.service-dialog[aria-labelledby='service-dialog-title-rename']").first
        try:
            expect(dialog).to_be_visible(timeout=timeout)

            field = dialog.locator("input.service-dialog-input").first
            expect(field).to_be_visible(timeout=timeout)
            field.fill(new_name)
            expect(field).to_have_value(new_name, timeout=timeout)

            btn = dialog.locator("button.btn-primary:has-text('Rename')").first
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()

            # The dialog closes once the rename is accepted
            expect(dialog).to_be_hidden(timeout=timeout)
        except Exception as e:
            raise AssertionError(f"element_details_services_ROADM_rename_service('{service}', '{new_name}') failed: {e}")

    def element_details_services_ROADM_cancel_rename_service(self, timeout: int = 5000):
        """
        In the "Rename Service" dialog (opened by element_details_services_ROADM_rename_service_button):
        Click the "Cancel" button and wait for the dialog to close.
        """
        dialog = self.page.locator("div.service-dialog[aria-labelledby='service-dialog-title-rename']").first
        try:
            expect(dialog).to_be_visible(timeout=timeout)

            btn = dialog.locator("button.btn-stroke:has-text('Cancel')").first
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()

            expect(dialog).to_be_hidden(timeout=timeout)
        except Exception as e:
            raise AssertionError(f"element_details_services_ROADM_cancel_rename_service failed: {e}")

    def element_details_services_ROADM_remove_service_button(self, service: str, timeout: int = 5000):
        """
        In Services -> ROADM:
        Open the 3-dots menu of the given service (same `service` values as
        element_details_services_ROADM_click_on_the_3_dots) and click "Remove".
        Only opens the removal flow; it does not confirm any dialog that follows.
        """
        # The menu is a Material menu rendered in the CDK overlay (outside the panel).
        # Reopen the menu and retry if the click fails (e.g. the menu closed or re-rendered).
        item = self.page.locator(
            ".cdk-overlay-pane .mat-mdc-menu-panel button[role='menuitem']"
        ).filter(has_text=re.compile(r"^\s*Remove\s*$")).first
        last_error = None
        for _ in range(3):
            try:
                self.element_details_services_ROADM_click_on_the_3_dots(service, timeout=timeout)
                expect(item).to_be_visible(timeout=timeout)
                item.click(timeout=3000)
                return
            except Exception as e:
                last_error = e
                sleep(0.5)
        raise AssertionError(f"element_details_services_ROADM_remove_service_button('{service}') failed: {last_error}")

    def element_details_services_ROADM_remove_service(self, service: str, timeout: int = 5000):
        """
        In Services -> ROADM:
        Remove the given service (same `service` values as
        element_details_services_ROADM_click_on_the_3_dots): open its 3-dots menu,
        click "Remove" and confirm in the "Remove Service" dialog.
        """
        self.element_details_services_ROADM_remove_service_button(service, timeout=timeout)

        dialog = self.page.locator("div.service-dialog[aria-labelledby='service-dialog-title-remove']").first
        try:
            expect(dialog).to_be_visible(timeout=timeout)

            # Safety check: make sure the dialog is about the service we meant to remove
            wanted = re.sub(r"\s+", " ", service.strip()).rstrip(":").strip()
            shown = re.sub(r"\s+", " ", dialog.locator(".service-dialog-serviceName").first.inner_text(timeout=timeout)).strip()
            if shown != wanted:
                raise AssertionError(f"dialog asks to remove '{shown}', expected '{wanted}'")

            btn = dialog.locator("button.btn-primary:has-text('Remove')").first
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()

            # The dialog closes once the removal is accepted
            expect(dialog).to_be_hidden(timeout=timeout)
        except Exception as e:
            raise AssertionError(f"element_details_services_ROADM_remove_service('{service}') failed: {e}")

    def element_details_services_ROADM_cancel_remove_service(self, timeout: int = 5000):
        """
        In the "Remove Service" dialog (opened by element_details_services_ROADM_remove_service_button):
        Click the "Cancel" button and wait for the dialog to close.
        """
        dialog = self.page.locator("div.service-dialog[aria-labelledby='service-dialog-title-remove']").first
        try:
            expect(dialog).to_be_visible(timeout=timeout)

            btn = dialog.locator("button.btn-stroke:has-text('Cancel')").first
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()

            expect(dialog).to_be_hidden(timeout=timeout)
        except Exception as e:
            raise AssertionError(f"element_details_services_ROADM_cancel_remove_service failed: {e}")

    # ==========================================================
    # Services → CS
    # ==========================================================
    
    def element_details_services_click_on_CS(self, timeout: int = 5000):
        """
        In the Node Properties panel → Services tab:
        Click the "CS" sub-tab.
        """
        self.element_details_services_click_format("CS", timeout=timeout)

    # ==========================================================
    # Faults → Alarms
    # ==========================================================
    
    # ✅
    def element_details_faults_click_on_alarms(self, timeout: int = 5000):
        """
        In the Node Properties panel -> Faults tab:
        Click the inner tab "Alarms" and assert it becomes active.
        """
        # Make sure we are on Faults main tab first
        self.element_details_click_on_faults()

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        alarms_tab = panel.locator("tabset.primary ul.nav-tabs a.nav-link:has(span:has-text('Alarms'))").first
        expect(alarms_tab).to_be_visible(timeout=timeout)

        def is_active() -> bool:
            cls = (alarms_tab.get_attribute("class") or "")
            aria = (alarms_tab.get_attribute("aria-selected") or "").strip().lower()
            return ("active" in cls.split()) or (aria == "true")

        if is_active():
            return

        alarms_tab.scroll_into_view_if_needed()
        alarms_tab.click(force=True)

        try:
            self.wait_until(is_active, timeout_ms=timeout, interval_ms=200)
            expect(alarms_tab).to_have_class(re.compile(r"\bactive\b"), timeout=timeout)
            sleep(0.5)
        except Exception as e:
            raise AssertionError(f"element_details_faults_click_on_alarms failed: tab did not become active. Problem: {e}")

    # ✅
    def element_details_faults_view_all_alarms(self, timeout: int = 10000):
        """
        Clicks the "View All Alarms" button in Faults -> Alarms.
        Asserts something changed(direct the user straight to to Alarms & Events page).
        """
        self.element_details_faults_click_on_alarms(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        btn = panel.locator(".fault-pane-footer button.btn.btn-primary:has-text('View All Alarms')").first
        expect(btn).to_be_visible(timeout=timeout)

        before_url = self.page.url
        btn.scroll_into_view_if_needed()
        btn.click()

        # Assert a generic “something changed”.
        def changed() -> bool:
            try:
                url_changed = self.page.url != before_url
                btn_gone = (btn.count() == 0) or (not btn.is_visible())
                return url_changed or btn_gone
            except Exception:
                # If DOM changed and locator got stale, that's also a "changed"
                return True

        try:
            self.wait_until(changed, timeout_ms=timeout, interval_ms=200)
            sleep(0.5)
        except Exception as e:
            raise AssertionError(f"element_details_faults_view_all_alarms failed: click did not trigger any visible change. Problem: {e}")

    # ✅
    def element_details_faults_get_all_alarms_old(self, timeout: int = 5000) -> list:
        """
        Returns a list of alarms currently shown in Faults -> Alarms list.
        Output example:
        [
          {'Alarm_Type': 'Power Supply Failure', 'Alarm_Source': '172.16.30.16 PSU 2 | Device |', 'Alarm_Date_and_Time': 'Jan 20, 2026 16:41 | Jan 25, 2026 13:22:21'}
        ]
        """
        self.element_details_faults_click_on_alarms(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        alarms = panel.locator("app-alarm .alarm")
        # alarms can be 0; that's valid
        alarms_count = alarms.count()

        def clean(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "").strip())

        out = []
        for i in range(alarms_count):
            alarm = alarms.nth(i)

            alarm_type = clean(alarm.locator(".content .title").first.inner_text(timeout=timeout))

            meta_rows = alarm.locator(".content .meta-row")
            alarm_source = clean(meta_rows.nth(0).inner_text(timeout=timeout)) if meta_rows.count() > 0 else ""
            alarm_date_and_time = clean(meta_rows.nth(1).inner_text(timeout=timeout)) if meta_rows.count() > 1 else ""

            out.append(
                {
                    "Alarm_Type": alarm_type,
                    "Alarm_Source": alarm_source,
                    "Alarm_Date_and_Time": alarm_date_and_time,
                }
            )

        sleep(0.5)

        return out
    
    # ✅
    def element_details_faults_get_all_alarms(self, timeout: int = 5000) -> list:
        """
        Returns a normalized list of alarms currently shown in Faults -> Alarms list.

        Output example:
        [
            {
                'message': 'SW Flash Bank Corrupted',
                'source': '172.16.40.122',
                'category': 'Device',
                'creation_timestamp': 'Apr 28, 2026 11:58',
                'detection_timestamp': 'Apr 28, 2026 18:32:21'
            }
        ]
        """
        self.element_details_faults_click_on_alarms(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        alarms = panel.locator("app-alarm .alarm")
        # alarms can be 0; that's valid
        alarms_count = alarms.count()

        def clean(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "").strip())

        out = []

        for i in range(alarms_count):
            alarm = alarms.nth(i)

            # Alarm title/message
            message = clean(alarm.locator(".content .title").first.inner_text(timeout=timeout))

            meta_rows = alarm.locator(".content .meta-row")

            # Example:
            # '172.16.40.122 | Device |'
            source_row = clean(meta_rows.nth(0).inner_text(timeout=timeout)) if meta_rows.count() > 0 else ""

            # Example:
            # 'Apr 28, 2026 11:58 | Apr 28, 2026 18:32:21'
            timestamp_row = clean(meta_rows.nth(1).inner_text(timeout=timeout)) if meta_rows.count() > 1 else ""

            # Parse source + category
            source_parts = [clean(part) for part in source_row.split("|") if clean(part)]
            source = source_parts[0] if len(source_parts) > 0 else ""
            category = source_parts[1] if len(source_parts) > 1 else ""

            # Parse creation + detection timestamps
            timestamp_parts = [clean(part) for part in timestamp_row.split("|") if clean(part)]
            creation_timestamp = timestamp_parts[0] if len(timestamp_parts) > 0 else ""
            detection_timestamp = timestamp_parts[1] if len(timestamp_parts) > 1 else ""

            out.append(
                {
                    "message": message,
                    "source": source,
                    "category": category,
                    "creation_timestamp": creation_timestamp,
                    "detection_timestamp": detection_timestamp,
                }
            )

        sleep(0.5)

        return out

    # ==========================================================
    # Faults → Events
    # ==========================================================
    
    # ✅
    def element_details_faults_click_on_events(self, timeout: int = 5000):
        """
        In the Node Properties panel -> Faults tab:
        Click the inner tab "Events" and assert it becomes active.
        """
        # Make sure we are on Faults main tab first
        self.element_details_click_on_faults()

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        events_tab = panel.locator("tabset.primary ul.nav-tabs a.nav-link:has(span:has-text('Events'))").first
        expect(events_tab).to_be_visible(timeout=timeout)

        def is_active() -> bool:
            cls = (events_tab.get_attribute("class") or "")
            aria = (events_tab.get_attribute("aria-selected") or "").strip().lower()
            return ("active" in cls.split()) or (aria == "true")

        if is_active():
            return

        events_tab.scroll_into_view_if_needed()
        events_tab.click(force=True)

        try:
            self.wait_until(is_active, timeout_ms=timeout, interval_ms=200)
            expect(events_tab).to_have_class(re.compile(r"\bactive\b"), timeout=timeout)
            sleep(0.5)
        except Exception as e:
            raise AssertionError(f"element_details_faults_click_on_events failed: tab did not become active. Problem: {e}")

    # ✅
    def element_details_faults_view_all_events(self, timeout: int = 10000):
        """
        Clicks the "View All Events" button in Faults -> Events.
        Asserts something changed(direct the user straight to to Alarms & Events page).
        """
        self.element_details_faults_click_on_events(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        btn = panel.locator(".fault-pane-footer button.btn.btn-primary:has-text('View All Events')").first
        expect(btn).to_be_visible(timeout=timeout)

        before_url = self.page.url
        btn.scroll_into_view_if_needed()
        btn.click()

        def changed() -> bool:
            try:
                url_changed = self.page.url != before_url
                btn_gone = (btn.count() == 0) or (not btn.is_visible())
                return url_changed or btn_gone
            except Exception:
                # If DOM changed and locator got stale, that's also a "changed"
                return True

        try:
            self.wait_until(changed, timeout_ms=timeout, interval_ms=200)
            sleep(0.5)
        except Exception as e:
            raise AssertionError(f"element_details_faults_view_all_events failed: click did not trigger any visible change. Problem: {e}")

    # ✅
    def element_details_faults_get_all_events_old(self, timeout: int = 5000) -> list:
        """
        Returns a list of events currently shown in Faults -> Events list.
        Output example:
        [
        {'Event_Type': 'Ethernet Link Failure',
        'Event_Source': '10.60.100.29 Ethernet | Device |',
        'Event_Date_and_Time': 'Sep 21, 2025 10:08 | Jun 6, 2025 01:33:38'}
        ]
        """

        self.element_details_faults_click_on_events(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        
        # Takes a few seconds to render the events list
        # Wait until at least 1 event exists (or timeout)
        self.wait_until(lambda: panel.locator("app-event .event").count() > 0, timeout_ms=timeout, interval_ms=200)

        events = panel.locator("app-event .event")
        events_count = events.count()

        def clean(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "").strip())

        out = []
        seen = set()  # UI sometimes duplicates items

        for i in range(events_count):
            ev = events.nth(i)

            event_type = clean(ev.locator(".content .title").first.inner_text(timeout=timeout))

            meta_rows = ev.locator(".content .meta-row")
            event_source = clean(meta_rows.nth(0).inner_text(timeout=timeout)) if meta_rows.count() > 0 else ""
            event_date_and_time = clean(meta_rows.nth(1).inner_text(timeout=timeout)) if meta_rows.count() > 1 else ""

            key = (event_type, event_source, event_date_and_time)
            if key in seen:
                continue
            seen.add(key)

            out.append(
                {
                    "Event_Type": event_type,
                    "Event_Source": event_source,
                    "Event_Date_and_Time": event_date_and_time,
                }
            )
        
        sleep(0.5)

        return out

    # ✅
    def element_details_faults_get_all_events(self, timeout: int = 5000) -> list:
        """
        Returns a normalized list of events currently shown in Faults -> Events list.

        Output example:
        [
            {
                'message': 'Link Up',
                'source': '172.16.20.112 Ethernet',
                'category': 'Device',
                'creation_timestamp': 'Apr 28, 2026 12:05',
                'detection_timestamp': 'Apr 19, 2026 11:33:30'
            }
        ]
        """
        self.element_details_faults_click_on_events(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        # Takes a few seconds to render the events list.
        # If there are no events, return an empty list instead of failing.
        try:
            self.wait_until(
                lambda: panel.locator("app-event .event").count() > 0,
                timeout_ms=timeout,
                interval_ms=200
            )
        except AssertionError:
            return []

        events = panel.locator("app-event .event")
        events_count = events.count()

        def clean(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "").strip())

        out = []
        seen = set()  # UI sometimes duplicates items

        for i in range(events_count):
            ev = events.nth(i)

            message = clean(ev.locator(".content .title").first.inner_text(timeout=timeout))

            meta_rows = ev.locator(".content .meta-row")

            source_row = clean(meta_rows.nth(0).inner_text(timeout=timeout)) if meta_rows.count() > 0 else ""
            timestamp_row = clean(meta_rows.nth(1).inner_text(timeout=timeout)) if meta_rows.count() > 1 else ""

            # Parse source + category
            source_parts = [clean(part) for part in source_row.split("|") if clean(part)]
            source = source_parts[0] if len(source_parts) > 0 else ""
            category = source_parts[1] if len(source_parts) > 1 else ""

            # Parse creation + detection timestamps
            timestamp_parts = [clean(part) for part in timestamp_row.split("|") if clean(part)]
            creation_timestamp = timestamp_parts[0] if len(timestamp_parts) > 0 else ""
            detection_timestamp = timestamp_parts[1] if len(timestamp_parts) > 1 else ""

            key = (message, source, category, creation_timestamp, detection_timestamp)
            if key in seen:
                continue
            seen.add(key)

            out.append(
                {
                    "message": message,
                    "source": source,
                    "category": category,
                    "creation_timestamp": creation_timestamp,
                    "detection_timestamp": detection_timestamp,
                }
            )

        sleep(0.5)

        return out

    # ==========================================================
    # Info (Chassis)
    # ==========================================================

    def chassis_element_details_info_get_domain_name(self, timeout: int = 5000) -> str:
        """
        Returns the "Domain Name" value shown in the chassis Info tab (e.g. "BOS-11").
        """
        info = self.chassis_element_details_info_get_all_info(timeout=timeout)
        if "Domain Name" not in info:
            raise AssertionError(f"chassis_element_details_info_get_domain_name failed: 'Domain Name' not found in {info}")
        return info["Domain Name"]

    def chassis_element_details_info_get_domain_description(self, timeout: int = 5000) -> str:
        """
        Returns the "Domain Description" value shown in the chassis Info tab (e.g. "Chassis").
        """
        info = self.chassis_element_details_info_get_all_info(timeout=timeout)
        if "Domain Description" not in info:
            raise AssertionError(f"chassis_element_details_info_get_domain_description failed: 'Domain Description' not found in {info}")
        return info["Domain Description"]
    
    def chassis_element_details_info_get_all_info(self, timeout: int = 5000) -> dict:
        """
        Returns everything shown in the chassis Info tab as {label: value}
        (labels without the trailing colon).
        Output example:
        {'Domain Name': 'BOS-11', 'Domain Description': 'Chassis'}
        """
        self.element_details_click_on_info()

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        rows = panel.locator("app-domain-info-properties .domain-info-general-row")

        # Rows render a moment after the tab switch
        try:
            self.wait_until(lambda: rows.count() > 0, timeout_ms=timeout, interval_ms=200)
        except Exception as e:
            raise AssertionError(f"chassis_element_details_info_get_all_info failed: no info rows appeared. Problem: {e}")

        def clean(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "").strip())

        info = {}
        for i in range(rows.count()):
            row = rows.nth(i)
            label = clean(row.locator(".domain-info-general-label").first.text_content(timeout=timeout)).rstrip(":").strip()
            info[label] = clean(row.locator(".domain-info-general-value").first.text_content(timeout=timeout))
        return info

    # ==========================================================
    # Info (Device) → General
    # ==========================================================

    def device_element_details_info_click_format(self, label_text: str, timeout: int = 5000):
        """
        In the device Node Properties panel → Info tab:
        Click an Info sub-tab (General / Protocols).
        """
        # Make sure we are on Info main tab first
        self.element_details_click_on_info()
        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        tab = panel.locator("tabset.device-info-type-tabs ul.nav-tabs a.nav-link").filter(
            has=self.page.locator("span", has_text=re.compile(rf"^\s*{re.escape(label_text)}\s*$"))
        ).first
        try:
            expect(tab).to_be_visible(timeout=timeout)

            # already selected
            if "active" in (tab.get_attribute("class") or "").split():
                return

            tab.scroll_into_view_if_needed()
            tab.click()
            expect(tab).to_have_class(re.compile(r"\bactive\b"), timeout=timeout)
        except Exception as e:
            raise AssertionError(f"device_element_details_info_click_on_{label_text.lower()} failed: {e}")

    def device_element_details_info_click_on_general(self, timeout: int = 5000):
        """
        In the device Node Properties panel → Info tab:
        Click the "General" sub-tab.
        """
        self.device_element_details_info_click_format("General", timeout=timeout)

    def _device_info_general_get_text_value(self, label: str, timeout: int = 5000) -> str:
        """
        Returns the text value of a row in the device Info -> General tab by its
        label (e.g. "Domain Name"; the trailing colon is not part of `label`).
        """
        self.device_element_details_info_click_on_general(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        label_re = re.compile(rf"^\s*{re.escape(label)}\s*:?\s*$")
        row = panel.locator("app-device-info-properties .device-info-general-row").filter(
            has=self.page.locator(".device-info-general-label", has_text=label_re)
        ).first
        try:
            expect(row).to_be_attached(timeout=timeout)
            value = row.locator(".device-info-general-value").first.text_content(timeout=timeout)
        except Exception as e:
            raise AssertionError(f"device_element_details_info_general_get '{label}' failed: {e}")
        return re.sub(r"\s+", " ", (value or "").strip())

    def device_element_details_info_general_get_domain_name(self, timeout: int = 5000) -> str:
        """
        Returns the "Domain Name" value shown in the device Info -> General tab (e.g. "Default").
        """
        return self._device_info_general_get_text_value("Domain Name", timeout=timeout)

    def device_element_details_info_general_get_name(self, timeout: int = 5000) -> str:
        """
        Returns the "Name" value shown in the device Info -> General tab
        (empty string when the device has no name).
        """
        return self._device_info_general_get_text_value("Name", timeout=timeout)

    def device_element_details_info_general_get_ip(self, timeout: int = 5000) -> str:
        """
        Returns the "IP" value shown in the device Info -> General tab (e.g. "172.16.20.11").
        """
        return self._device_info_general_get_text_value("IP", timeout=timeout)

    def device_element_details_info_general_get_type(self, timeout: int = 5000) -> str:
        """
        Returns the "Type" value shown in the device Info -> General tab (e.g. "PL-4000M").
        """
        return self._device_info_general_get_text_value("Type", timeout=timeout)

    def device_element_details_info_general_get_location(self, timeout: int = 5000) -> str:
        """
        Returns the "Location" value shown in the device Info -> General tab
        (empty string when no location is set).
        """
        return self._device_info_general_get_text_value("Location", timeout=timeout)

    def device_element_details_info_general_get_description(self, timeout: int = 5000) -> str:
        """
        Returns the "Description" value shown in the device Info -> General tab
        (empty string when no description is set).
        """
        return self._device_info_general_get_text_value("Description", timeout=timeout)

    def _device_info_general_get_checkbox_value(self, label: str, timeout: int = 5000) -> bool:
        """
        Returns the state (True = checked) of a checkbox row in the device Info -> General tab
        by its label (e.g. "Managed"; the trailing colon is not part of `label`).
        """
        self.device_element_details_info_click_on_general(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        label_re = re.compile(rf"^\s*{re.escape(label)}\s*:?\s*$")
        row = panel.locator("app-device-info-properties .device-info-general-row").filter(
            has=self.page.locator(".device-info-general-label", has_text=label_re)
        ).first
        try:
            box = row.locator("label.checkbox-container").first
            expect(box).to_be_attached(timeout=timeout)
            # A checked checkbox carries the "checked" class (the read-only ones also carry "disabled")
            return "checked" in (box.get_attribute("class") or "").split()
        except Exception as e:
            raise AssertionError(f"device_element_details_info_general_get '{label}' failed: {e}")

    def device_element_details_info_general_get_managed(self, timeout: int = 5000) -> bool:
        """
        Returns the state of the "Managed" checkbox in the device Info -> General tab
        (True = checked).
        """
        return self._device_info_general_get_checkbox_value("Managed", timeout=timeout)

    def device_element_details_info_general_get_alarm_status(self, timeout: int = 5000) -> str:
        """
        Returns the "Alarm Status" value shown in the device Info -> General tab (e.g. "Major").
        """
        return self._device_info_general_get_text_value("Alarm Status", timeout=timeout)

    def device_element_details_info_general_get_connectivity_status(self, timeout: int = 5000) -> str:
        """
        Returns the "Connectivity Status" value shown in the device Info -> General tab
        as displayed text (e.g. "true").
        """
        return self._device_info_general_get_text_value("Connectivity Status", timeout=timeout)

    def device_element_details_info_general_get_OTDR_capable(self, timeout: int = 5000) -> bool:
        """
        Returns the state of the "OTDR Capable" checkbox in the device Info -> General tab
        (True = checked).
        """
        return self._device_info_general_get_checkbox_value("OTDR Capable", timeout=timeout)

    def device_element_details_info_general_get_NMS_owned(self, timeout: int = 5000) -> str:
        """
        Returns the "NMS Owned" value shown in the device Info -> General tab
        as displayed text (e.g. "false").
        """
        return self._device_info_general_get_text_value("NMS Owned", timeout=timeout)

    def device_element_details_info_general_show_device_performance(self, timeout: int = 5000):
        """
        In the device Node Properties panel → Info → General tab:
        Click the "Show Device Performance" button.
        """
        self.device_element_details_info_click_on_general(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        btn = panel.locator("app-device-info-properties .device-info-footer button.btn-primary:has-text('Show Device Performance')").first
        try:
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.scroll_into_view_if_needed()
            btn.click()
        except Exception as e:
            raise AssertionError(f"device_element_details_info_general_show_device_performance failed: {e}")

    def device_element_details_info_general_manage_device_OTN_services(self, timeout: int = 5000):
        """
        In the device Node Properties panel → Info → General tab:
        Click the "Manage Device OTN Services" button, then confirm the warning
        ("Releasing later the device ... Do you wish to proceed?") by clicking "Manage".
        """
        self.device_element_details_info_click_on_general(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        btn = panel.locator("app-device-info-properties .device-info-footer button.btn-primary:has-text('Manage Device OTN Services')").first
        # The release flow probably reuses the same warning box, so match it by its title
        warning = panel.locator("app-device-info-properties .device-info-owned-warning").filter(
            has=self.page.locator(".device-info-owned-warning-title", has_text=re.compile(r"^\s*Manage Device OTN Services\s*$"))
        ).first
        try:
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.scroll_into_view_if_needed()
            btn.click()

            expect(warning).to_be_visible(timeout=timeout)
            confirm = warning.locator("button.btn-primary:has-text('Manage')").first
            expect(confirm).to_be_enabled(timeout=timeout)
            confirm.click()

            # The warning closes once the choice is accepted
            expect(warning).to_be_hidden(timeout=timeout)
        except Exception as e:
            raise AssertionError(f"device_element_details_info_general_manage_device_OTN_services failed: {e}")

    def device_element_details_info_general_cancel_manage_device_OTN_services_button(self, timeout: int = 5000):
        """
        In the device Node Properties panel → Info → General tab:
        Open the "Manage Device OTN Services" warning (unless it is already open)
        and click "Cancel" in it.
        """
        self.device_element_details_info_click_on_general(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        btn = panel.locator("app-device-info-properties .device-info-footer button.btn-primary:has-text('Manage Device OTN Services')").first
        warning = panel.locator("app-device-info-properties .device-info-owned-warning").filter(
            has=self.page.locator(".device-info-owned-warning-title", has_text=re.compile(r"^\s*Manage Device OTN Services\s*$"))
        ).first
        try:
            if not warning.is_visible():
                expect(btn).to_be_visible(timeout=timeout)
                expect(btn).to_be_enabled(timeout=timeout)
                btn.scroll_into_view_if_needed()
                btn.click()
            expect(warning).to_be_visible(timeout=timeout)

            cancel = warning.locator("button.btn-stroke:has-text('Cancel')").first
            expect(cancel).to_be_enabled(timeout=timeout)
            cancel.click()

            expect(warning).to_be_hidden(timeout=timeout)
        except Exception as e:
            raise AssertionError(f"device_element_details_info_general_cancel_manage_device_OTN_services_button failed: {e}")

    def device_element_details_info_general_release_device_OTN_services(self, timeout: int = 5000):
        """
        In the device Node Properties panel → Info → General tab:
        Click the "Release Device OTN Services" button, then confirm the warning
        ("Releasing this device ... will erase all OTN services from it. Do you wish to proceed?")
        by clicking "Release".
        """
        self.device_element_details_info_click_on_general(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        btn = panel.locator("app-device-info-properties .device-info-footer button.btn-primary:has-text('Release Device OTN Services')").first
        # Same warning box as the manage flow: match it by its title
        warning = panel.locator("app-device-info-properties .device-info-owned-warning").filter(
            has=self.page.locator(".device-info-owned-warning-title", has_text=re.compile(r"^\s*Release Device OTN Services\s*$"))
        ).first
        try:
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.scroll_into_view_if_needed()
            btn.click()

            expect(warning).to_be_visible(timeout=timeout)
            confirm = warning.locator("button.btn-primary:has-text('Release')").first
            expect(confirm).to_be_enabled(timeout=timeout)
            confirm.click()

            # The warning closes once the choice is accepted
            expect(warning).to_be_hidden(timeout=timeout)
        except Exception as e:
            raise AssertionError(f"device_element_details_info_general_release_device_OTN_services failed: {e}")

    def device_element_details_info_general_cancel_release_device_OTN_services_button(self, timeout: int = 5000):
        """
        In the device Node Properties panel → Info → General tab:
        Open the "Release Device OTN Services" warning (unless it is already open)
        and click "Cancel" in it.
        """
        self.device_element_details_info_click_on_general(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        btn = panel.locator("app-device-info-properties .device-info-footer button.btn-primary:has-text('Release Device OTN Services')").first
        warning = panel.locator("app-device-info-properties .device-info-owned-warning").filter(
            has=self.page.locator(".device-info-owned-warning-title", has_text=re.compile(r"^\s*Release Device OTN Services\s*$"))
        ).first
        try:
            if not warning.is_visible():
                expect(btn).to_be_visible(timeout=timeout)
                expect(btn).to_be_enabled(timeout=timeout)
                btn.scroll_into_view_if_needed()
                btn.click()
            expect(warning).to_be_visible(timeout=timeout)

            cancel = warning.locator("button.btn-stroke:has-text('Cancel')").first
            expect(cancel).to_be_enabled(timeout=timeout)
            cancel.click()

            expect(warning).to_be_hidden(timeout=timeout)
        except Exception as e:
            raise AssertionError(f"device_element_details_info_general_cancel_release_device_OTN_services_button failed: {e}")

    # ==========================================================
    # Info (Device) → Protocols
    # ==========================================================

    def device_element_details_info_click_on_protocols(self, timeout: int = 5000):
        """
        In the device Node Properties panel → Info tab:
        Click the "Protocols" sub-tab.
        """
        self.device_element_details_info_click_format("Protocols", timeout=timeout)

    def device_element_details_info_protocols_set_data_exchange_protocol(self, protocol: str, timeout: int = 5000):
        """
        In the device Node Properties panel → Info → Protocols tab:
        Select a "Data exchange protocol" ("ICMP", "SNMPv2" or "SNMPv3") by clicking its checkbox.
        Does nothing if it is already selected. Does not press "Update".
        """
        self.device_element_details_info_click_on_protocols(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        box = panel.locator(f"app-device-info-properties .device-info-protocol-selector-options app-checkbox[label='{protocol}'] label.checkbox-container").first

        def classes() -> list:
            return (box.get_attribute("class") or "").split()

        try:
            expect(box).to_be_visible(timeout=timeout)

            # already selected
            if "checked" in classes():
                return
            if "disabled" in classes():
                raise AssertionError(f"'{protocol}' is disabled and cannot be selected")

            box.scroll_into_view_if_needed()
            box.click()
            expect(box).to_have_class(re.compile(r"\bchecked\b"), timeout=timeout)
        except Exception as e:
            raise AssertionError(f"device_element_details_info_protocols_set_data_exchange_protocol('{protocol}') failed: {e}")

    def _device_info_protocols_set_input(self, form_control: str, value, timeout: int = 5000):
        """
        Set a text/number input of the device Info -> Protocols form
        (identified by its formcontrolname, e.g. "readCommunity"). Does not press "Update".
        """
        self.device_element_details_info_click_on_protocols(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        field = panel.locator(f"app-device-info-properties app-input[formcontrolname='{form_control}'] input").first
        value = str(value)
        try:
            expect(field).to_be_visible(timeout=timeout)
            field.scroll_into_view_if_needed()
            field.fill(value)
            expect(field).to_have_value(value, timeout=timeout)
        except Exception as e:
            raise AssertionError(f"device_element_details_info_protocols_set '{form_control}' = '{value}' failed: {e}")

    def device_element_details_info_protocols_set_read_community(self, read_community: str, timeout: int = 5000):
        """
        In the device Node Properties panel → Info → Protocols tab:
        Set the "Read Community" field. Does not press "Update".
        """
        self._device_info_protocols_set_input("readCommunity", read_community, timeout=timeout)

    def device_element_details_info_protocols_set_write_community(self, write_community: str, timeout: int = 5000):
        """
        In the device Node Properties panel → Info → Protocols tab:
        Set the "Write Community" field. Does not press "Update".
        """
        self._device_info_protocols_set_input("writeCommunity", write_community, timeout=timeout)

    def device_element_details_info_protocols_set_admin_community(self, admin_community: str, timeout: int = 5000):
        """
        In the device Node Properties panel → Info → Protocols tab:
        Set the "Admin Community" field. Does not press "Update".
        """
        self._device_info_protocols_set_input("adminCommunity", admin_community, timeout=timeout)

    def device_element_details_info_protocols_set_contact_port(self, contact_port, timeout: int = 5000):
        """
        In the device Node Properties panel → Info → Protocols tab:
        Set the "Contact Port" field (a number, 0 - 65535; an int or a str is accepted).
        Does not press "Update".
        """
        self._device_info_protocols_set_input("contactPort", contact_port, timeout=timeout)

    def device_element_details_info_protocols_set_performance_transport_protocol(self, protocol: str, timeout: int = 5000):
        """
        In the device Node Properties panel → Info → Protocols tab:
        Select the "Performance Transport Protocol" (e.g. "SNMP") from its dropdown.
        Does nothing if it is already selected. Does not press "Update".
        """
        self.device_element_details_info_click_on_protocols(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        dropdown = panel.locator("app-device-info-properties app-dropdown[formcontrolname='performanceTransportProtocol']").first
        toggle = dropdown.locator("button.dropdown-toggle").first
        selected = dropdown.locator(".selected-view span").first
        exact = re.compile(rf"^\s*{re.escape(protocol)}\s*$")
        try:
            expect(toggle).to_be_visible(timeout=timeout)

            # already selected
            if (selected.inner_text() or "").strip() == protocol:
                return

            toggle.scroll_into_view_if_needed()
            toggle.click()
            option = dropdown.locator("ul li.dropdown-item").filter(has_text=exact).first
            expect(option).to_be_visible(timeout=timeout)
            option.scroll_into_view_if_needed()
            option.click()
            expect(selected).to_have_text(exact, timeout=timeout)
        except Exception as e:
            raise AssertionError(f"device_element_details_info_protocols_set_performance_transport_protocol('{protocol}') failed: {e}")

    def device_element_details_info_protocols_reset_to_default(self, timeout: int = 5000):
        """
        In the device Node Properties panel → Info → Protocols tab:
        Click the "Reset to Default" button.
        """
        self.device_element_details_info_click_on_protocols(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        btn = panel.locator(
            "app-device-info-properties tabset.device-info-type-tabs .tab-content > tab.tab-pane.active "
            ".device-info-footer button.simple-btn:has-text('Reset to Default')"
        ).first
        try:
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.scroll_into_view_if_needed()
            btn.click()
        except Exception as e:
            raise AssertionError(f"device_element_details_info_protocols_reset_to_default failed: {e}")

    def device_element_details_info_protocols_save_as_default(self, timeout: int = 5000):
        """
        In the device Node Properties panel → Info → Protocols tab:
        Click the "Save as Default" button.
        """
        self.device_element_details_info_click_on_protocols(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        btn = panel.locator(
            "app-device-info-properties tabset.device-info-type-tabs .tab-content > tab.tab-pane.active "
            ".device-info-footer button.with-icon-btn:has-text('Save as Default')"
        ).first
        try:
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.scroll_into_view_if_needed()
            btn.click()
        except Exception as e:
            raise AssertionError(f"device_element_details_info_protocols_save_as_default failed: {e}")

    def device_element_details_info_protocols_click_on_update_button(self, timeout: int = 5000):
        """
        In the device Node Properties panel → Info → Protocols tab:
        Click the "Update" button (applies the protocol settings).
        """
        self.device_element_details_info_click_on_protocols(timeout=timeout)

        panel = self.page.locator("app-node-properties .node-properties-container").first
        expect(panel).to_be_visible(timeout=timeout)

        btn = panel.locator(
            "app-device-info-properties tabset.device-info-type-tabs .tab-content > tab.tab-pane.active "
            ".device-info-footer button.btn-primary:has-text('Update')"
        ).first
        try:
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.scroll_into_view_if_needed()
            btn.click()
        except Exception as e:
            raise AssertionError(f"device_element_details_info_protocols_click_on_update_button failed: {e}")