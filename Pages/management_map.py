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



class ManagementMap:
    """
    Management Map page – Encapsulates all map-level interactions, including alarm visibility, severity filters,
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
                self.wait_until(lambda: self.get_alarms_status() == "hidden", timeout_ms=5000, interval_ms=200)

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

        except Exception as e:
            raise AssertionError(f"discard_and_lock failed: did not exit edit mode after Discard & Lock. Problem: {e}")

    # ✅
    def double_click_on_element_via_the_map(self, element_data_id: str | int, timeout: int = 12000) -> bool:
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
            sleep(5)

            return True

        except Exception as e:
            raise AssertionError(f"double_click_on_element_via_the_map(data_id={element_data_id}) failed. Problem: {e}")

    # ✅
    def click_on_element_via_the_map(self, element_data_id: str | int, timeout: int = 12000) -> bool:
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

        self.mapLocator.zoom_controls.locator("button").nth(0).click()

        try:
            self.wait_until(lambda: self.get_svg_transform() != before, timeout_ms=10000, interval_ms=200)

        except Exception as e:
            raise AssertionError(f"map_zoom_in failed: SVG transform did not change. Problem: {e}")

    # ✅
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
        sleep(1)
        self.mapLocator.zoom_controls.locator("button").nth(1).click()
        sleep(1)
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
        return container.locator("div.inventory-tree-level-title", has_text=rx).first
        

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
            
            sleep(0.5)

        except Exception as e:
            raise AssertionError(f"hide_navigation_info failed: navigation panel did not close. Problem: {e}")

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
        row = self.nav_row_locator(element_name)
        expect(row).to_be_visible(timeout=timeout)

        try:
            row.scroll_into_view_if_needed()
            row.click()

            # Details panel title (left panel)
            panel_title = self.page.locator(
                "xpath=//div[contains(@class,'details') or contains(@class,'modal')]"
                "//span[contains(normalize-space(.), '{}')]".format(element_name.split("/")[0]))

            # Fallback: close button visibility means panel is open
            close_btn = self.page.locator(
                "xpath=//*[name()='svg']"
                "/ancestor::*[self::button or self::div][1]")

            self.wait_until(lambda: panel_title.count() > 0 or close_btn.count() > 0, timeout_ms=timeout,interval_ms=200)

            sleep(0.5)

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
        sleep(0.5)

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

            sleep(0.5)

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

            sleep(0.5)

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
            sleep(0.5)
        except Exception as e:
            raise AssertionError(f"element_details_click_on_{label_text.lower()} failed: tab did not become active. Problem: {e}")

    # ✅
    def element_details_click_on_chassis(self):
        self.element_details_click_format("Chassis")

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
    def element_details_faults_get_all_alarms(self, timeout: int = 5000) -> list:
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
    def element_details_faults_get_all_events(self, timeout: int = 5000) -> list:
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