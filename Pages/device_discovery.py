"""
Created by: Yuval Dahan
Date: 28/01/2026
"""

import re
import time
from time import sleep
from typing import Callable

from playwright.sync_api import Page, expect


class DeviceDiscovery:
    """
    Device Discovery page – handles IP configuration, SNMP v2/v3 settings,
    discovery execution, and default management.
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
    def clean(self, s: str) -> str:
        """
        Normalize whitespace and strip.
        """
        return re.sub(r"\s+", " ", (s or "").strip())

    # ==========================================================
    # Base locators
    # ==========================================================
    
    # ✅
    def container(self):
        """
        Return the device discovery container.
        """
        container = self.page.locator("div.device-discovery-container").first
        if container.count() == 0:
            raise AssertionError("DeviceDiscovery: container not found (div.device-discovery-container).")
        return container

    # ✅
    def header(self):
        """
        Return header section (title + controls).
        """
        return self.container().locator("div.device-discovery-header").first

    # ✅
    def content(self):
        """
        Return content section (fields + tabs).
        """
        return self.container().locator("div.device-discovery-content").first

    # ✅
    def footer(self):
        """
        Return footer section (Reset/Save/Start Discovery).
        """
        return self.container().locator("footer").first

    # ==========================================================
    # Header controls
    # ==========================================================

    # ✅
    def range_toggle(self):
        """
        Return the Range slide-toggle component in the header.
        """
        toggle = self.header().locator("div.controls app-slide-toggle:has-text('Range')").first
        if toggle.count() == 0:
            raise AssertionError("DeviceDiscovery: Range toggle not found (app-slide-toggle with text 'Range').")
        return toggle

    # ✅
    def is_range_enabled(self) -> bool:
        """
        Return True if Range toggle is ON according to the SVG knob position.
        """
        t = self.range_toggle()
        svg = t.locator("svg").first

        # OFF: knob is a 16x16 rect at x=16
        # ON : knob is a 24x24 rect at x=32
        knob = svg.locator("rect[fill='#FFFFFF']").first  # exists only when ON
        if knob.count() > 0:
            return True

        knob_off = svg.locator("rect[x='16'][y='16'][width='16'][height='16']").first
        if knob_off.count() > 0:
            return False

        # Fallback: if DOM changed, consider not enabled
        return False

    # ✅
    def close_btn(self):
        """
        Close (X) icon button.
        """
        return self.header().locator("app-icon[name='close-square']").first

    # ==========================================================
    # Main IP input
    # ==========================================================

    # ✅
    def ip_app_input(self):
        """
        Return the app-input container for the IP address field.
        """
        inp = self.content().locator("app-input[formcontrolname='ip']").first
        if inp.count() == 0:
            raise AssertionError("DeviceDiscovery: IP app-input not found (formcontrolname='ip').")
        return inp

    # ✅
    def ip_input(self):
        """
        Return the visible input element of the IP address field.
        """
        # When Range mode is enabled, the single IP input may become hidden/disabled but still exist in DOM.
        return self.ip_app_input().locator("input:visible").first

    # ✅
    def set_ip_address(self, ip: str, timeout: int = 8000):
        """
        Set IP address field (single IP mode).
        """
        try:
            # If range is enabled, this field is often not editable.
            if self.is_range_enabled():
                raise AssertionError("Range mode is enabled. Use set_range_start_ip/set_range_end_ip instead.")

            inp = self.ip_input()
            expect(inp).to_be_visible(timeout=timeout)
            expect(inp).to_be_enabled(timeout=timeout)
            expect(inp).to_be_editable(timeout=timeout)

            inp.scroll_into_view_if_needed()
            inp.click(force=True)

            # More robust than fill() on some Angular inputs
            inp.press("Control+A")
            inp.type(str(ip), delay=5)

        except Exception as e:
            raise AssertionError(f"set_ip_address('{ip}') failed. Problem: {e}")

    # ✅
    def get_ip_address(self, timeout: int = 8000) -> str:
        """
        Get IP address field value.
        """
        try:
            inp = self.ip_app_input().locator("input:visible").first

            expect(inp).to_be_visible(timeout=timeout)
            expect(inp).to_be_enabled(timeout=timeout)

            return self.clean(inp.input_value())

        except Exception as e:
            raise AssertionError(f"get_ip_address failed. Problem: {e}")

    # =========================
    # IP Range
    # =========================

    # ✅
    def click_start_discovery_for_ip_range(self, timeout: int = 8000):
        """
        Enable Range toggle (IP range discovery).
        """
        try:
            t = self.range_toggle()
            expect(t).to_be_visible(timeout=timeout)

            if self.is_range_enabled():
                return

            # Click SVG directly (more reliable)
            svg = t.locator("svg").first
            expect(svg).to_be_visible(timeout=timeout)
            svg.click(force=True)

            # Wait until toggle becomes enabled
            self.wait_until(lambda: self.is_range_enabled(), timeout_ms=timeout, interval_ms=200)

        except Exception as e:
            raise AssertionError(f"click_start_discovery_for_ip_range failed. Problem: {e}")

    # ✅
    def click_stop_discovery_for_ip_range(self, timeout: int = 8000):
        """
        Disable Range toggle (return to single IP discovery).
        """
        try:
            t = self.range_toggle()
            expect(t).to_be_visible(timeout=timeout)

            # If already disabled -> nothing to do
            if not self.is_range_enabled():
                return

            # Click SVG directly (more reliable)
            svg = t.locator("svg").first
            expect(svg).to_be_visible(timeout=timeout)
            svg.click(force=True)

            # Wait until toggle becomes disabled
            self.wait_until(lambda: not self.is_range_enabled(), timeout_ms=timeout, interval_ms=200)

        except Exception as e:
            raise AssertionError(f"click_stop_discovery_for_ip_range failed. Problem: {e}")

    # ✅
    def set_range_start_ip(self, start_ip: str, timeout: int = 8000):
        """
        Set the Start IP field (Range mode).
        """
        try:
            inp = self.app_input_field("startIP")
            expect(inp).to_be_visible(timeout=timeout)
            inp.click(force=True)
            inp.fill("")
            inp.type(str(start_ip), delay=5)
        except Exception as e:
            raise AssertionError(f"set_range_start_ip('{start_ip}') failed. Problem: {e}")

    # ✅
    def get_range_start_ip(self, timeout: int = 8000) -> str:
        """
        Get the Start IP field value (Range mode).
        """
        try:
            inp = self.app_input_field("startIP")
            expect(inp).to_be_visible(timeout=timeout)
            return self.clean(inp.input_value())
        except Exception as e:
            raise AssertionError(f"get_range_start_ip failed. Problem: {e}")

    # ✅
    def set_range_end_ip(self, end_ip: str, timeout: int = 8000):
        """
        Set the End IP field (Range mode).
        """
        try:
            inp = self.app_input_field("endIP")
            expect(inp).to_be_visible(timeout=timeout)
            inp.click(force=True)
            inp.fill("")
            inp.type(str(end_ip), delay=5)
        except Exception as e:
            raise AssertionError(f"set_range_end_ip('{end_ip}') failed. Problem: {e}")

    # ✅
    def get_range_end_ip(self, timeout: int = 8000) -> str:
        """
        Get the End IP field value (Range mode).
        """
        try:
            inp = self.app_input_field("endIP")
            expect(inp).to_be_visible(timeout=timeout)
            return self.clean(inp.input_value())
        except Exception as e:
            raise AssertionError(f"get_range_end_ip failed. Problem: {e}")

    # ==========================================================
    # Protocol tabs (ICMP / SNMPv2 / SNMPv3)
    # ==========================================================
    
    # ✅
    def protocol_tabset(self, timeout: int = 10000):
        """
        Return protocol tabset container.
        """
        try:
            ts = self.content().locator("tabset.tab-container").first
            self.wait_until(lambda: ts.count() > 0 and ts.is_visible(), timeout_ms=timeout, interval_ms=200)
            return ts

        except Exception as e:
            raise AssertionError(f"protocol_tabset failed. Problem: {e}")
    
    # ✅
    def click_protocol_tab(self, tab_name: str, timeout: int = 10000):
        """
        Click protocol tab by name and assert the tab content becomes active.
        """
        try:
            tabset = self.protocol_tabset(timeout=timeout)

            tab_btn = tabset.locator("ul.nav.nav-tabs a.nav-link", has_text=re.compile(rf"^\s*{re.escape(tab_name)}\s*$")).first
            expect(tab_btn).to_be_visible(timeout=timeout)
            tab_btn.click(force=True)

            # Assert the tab pane became active (this is more stable than the <a>.active)
            tab_pane = tabset.locator(f"div.tab-content tab[heading='{tab_name}']").first

            self.wait_until(lambda: tab_pane.count() > 0 and tab_pane.is_visible() and ("active" in (tab_pane.get_attribute("class") or "")), timeout_ms=timeout)

        except Exception as e:
            raise AssertionError(f"click_protocol_tab('{tab_name}') failed. Problem: {e}")

    # ✅
    def click_ICMP(self, timeout: int = 10000):
        """
        Switch to ICMP tab.
        """
        self.click_protocol_tab("ICMP", timeout=timeout)

    # ✅
    def click_SNMPv2(self, timeout: int = 10000):
        """
        Switch to SNMPv2 tab.
        """
        self.click_protocol_tab("SNMPv2", timeout=timeout)

    # ✅
    def click_SNMPv3(self, timeout: int = 10000):
        """
        Switch to SNMPv3 tab.
        """
        self.click_protocol_tab("SNMPv3", timeout=timeout)

    # ==========================================================
    # app-input helpers
    # ==========================================================

    # ✅
    def active_tab_pane(self):
        """
        Return the currently active tab-pane under the protocol tabset.
        """
        ts = self.protocol_tabset()
        pane = ts.locator("div.tab-content tab.active.tab-pane").first
        if pane.count() == 0:
            raise AssertionError("DeviceDiscovery: active tab pane not found.")
        return pane

    # ✅
    def app_input(self, formcontrolname: str, scope=None):
        """
        Return app-input.
        """
        root = scope if scope is not None else self.container()
        loc = root.locator(f"app-input[formcontrolname='{formcontrolname}']").first
        if loc.count() == 0:
            raise AssertionError(f"DeviceDiscovery: app-input not found (formcontrolname='{formcontrolname}').")
        return loc

    # ✅
    def app_input_field(self, formcontrolname: str, scope=None):
        """
        Return <input> inside app-input.
        """
        return self.app_input(formcontrolname, scope=scope).locator("input").first

    # ✅
    def set_app_input_value(self, formcontrolname: str, value: str, timeout: int = 8000, scope=None):
        """
        Fill an app-input.
        """
        try:
            inp = self.app_input_field(formcontrolname, scope=scope)
            expect(inp).to_be_visible(timeout=timeout)
            inp.click(force=True)
            inp.fill("")
            inp.type(str(value), delay=5)
        except Exception as e:
            raise AssertionError(f"set_app_input_value('{formcontrolname}', '{value}') failed. Problem: {e}")

    # ✅
    def get_app_input_value(self, formcontrolname: str, timeout: int = 8000, scope=None) -> str:
        """
        Read an app-input value.
        """
        try:
            inp = self.app_input_field(formcontrolname, scope=scope)
            expect(inp).to_be_visible(timeout=timeout)
            return self.clean(inp.input_value())
        except Exception as e:
            raise AssertionError(f"get_app_input_value('{formcontrolname}') failed. Problem: {e}")

    # ==========================================================
    # Dropdowns
    # ==========================================================
    
    # ✅
    def app_dropdown(self, label: str):
        """
        Return app-dropdown by label.
        """
        dropdown = self.container().locator(f"app-dropdown[label='{label}']").first
        sleep(1)
        if dropdown.count() == 0:
            raise AssertionError(f"DeviceDiscovery: dropdown not found (label='{label}').")
        return dropdown

    # ✅
    def dropdown_selected_text(self, label: str, timeout: int = 8000) -> str:
        """
        Return current selected text of a dropdown.
        """
        try:
            dropdown = self.app_dropdown(label)
            selected = dropdown.locator(".selected-view span").first
            expect(selected).to_be_visible(timeout=timeout)
            return self.clean(selected.inner_text())
        except Exception as e:
            raise AssertionError(f"dropdown_selected_text('{label}') failed. Problem: {e}")

    # ✅
    def open_dropdown(self, label: str, timeout: int = 8000):
        """
        Open a dropdown by label.
        """
        try:
            dropdown = self.app_dropdown(label)
            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
            expect(btn).to_be_visible(timeout=timeout)
            btn.click(force=True)
        except Exception as e:
            raise AssertionError(f"open_dropdown('{label}') failed. Problem: {e}")

    # ✅
    def dropdown_pick(self, label: str, value: str, timeout: int = 8000):
        """
        Pick a value from a labeled dropdown.
        """
        try:
            menu = self.open_dropdown_menu(label, timeout=timeout)

            item = menu.locator("li.dropdown-item", has_text=re.compile(rf"^\s*{re.escape(value)}\s*$", re.IGNORECASE)).first

            if item.count() == 0:
                options = menu.locator("li.dropdown-item").all_inner_texts()
                options = [self.clean(x) for x in options if self.clean(x)]
                raise AssertionError(f"Value '{value}' not found in '{label}'. Available: {options}")

            item.scroll_into_view_if_needed()
            item.click(force=True)

            # Wait for selected-view to update
            self.wait_until(lambda: self.dropdown_selected_text(label, timeout=timeout).strip().lower() == value.strip().lower(), timeout_ms=timeout, interval_ms=150)

        except Exception as e:
            raise AssertionError(f"dropdown_pick('{label}', '{value}') failed. Problem: {e}")

    # ✅
    def set_dropdown_with_validation(self, label: str, value: str, timeout: int = 8000):
        """
        Validate the value exists in the dropdown and then select it.
        """
        try:
            menu = self.open_dropdown_menu(label, timeout=timeout)

            options = menu.locator("li.dropdown-item").all_inner_texts()
            options = [self.clean(x) for x in options if self.clean(x)]

            if value.strip() not in [o.strip() for o in options]:
                raise AssertionError(f"'{value}' not found in '{label}'. Available values: {options}")

            self.dropdown_pick(label, value, timeout=timeout)

        except Exception as e:
            raise AssertionError(f"set_dropdown_with_validation('{label}', '{value}') failed. Problem: {e}")

    # ✅
    def dropdown_menu(self, label: str, timeout: int = 8000):
        """
        Return the dropdown menu for a labeled dropdown.
        Works whether the menu is rendered inside the dropdown or as an overlay.
        """
        dd = self.app_dropdown(label)

        btn = dd.locator("button.dropdown-button, button[dropdowntoggle]").first
        if btn.count() == 0:
            raise AssertionError(f"DeviceDiscovery: dropdown button not found (label='{label}').")

        # 1) First try: menu inside the dropdown
        menu_inside = dd.locator("div.dropdown-menu").first
        if menu_inside.count() > 0:
            return menu_inside

        # 2) Second try: menu rendered as overlay, linked by aria-labelledby to button id
        btn_id = btn.get_attribute("id")
        if btn_id:
            menu_by_aria = self.page.locator(f"div.dropdown-menu[aria-labelledby='{btn_id}']").first
            if menu_by_aria.count() > 0:
                return menu_by_aria

        # 3) Last fallback: by data-label (if exists)
        menu_by_label = self.page.locator(f"div.dropdown-menu[data-label='{label}']").first
        if menu_by_label.count() > 0:
            return menu_by_label

        raise AssertionError(
            f"DeviceDiscovery: dropdown menu not found (label='{label}'). "
            f"button_id='{btn_id}'"
        )

    # ✅
    def try_open_dropdown_menu(self, label: str, timeout: int = 8000):
        """
        Best-effort open for a dropdown. Returns the menu if visible, else None.
        """
        dd = self.app_dropdown(label)
        btn = dd.locator("button.dropdown-button, button[dropdowntoggle]").first
        expect(btn).to_be_visible(timeout=timeout)

        attempts = [
            lambda: btn.click(force=True),
            lambda: btn.click(force=True),
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
                menu = self.dropdown_menu(label, timeout=timeout)  # <-- now after click
                self.wait_until(lambda: menu.count() > 0 and menu.is_visible(), timeout_ms=min(timeout, 1500), interval_ms=150)
                if menu.is_visible():
                    return menu
            except Exception:
                pass

        return None

    # ✅
    def open_dropdown_menu(self, label: str, timeout: int = 8000):
        """
        Open dropdown and return its menu locator.
        """
        try:
            menu = self.try_open_dropdown_menu(label, timeout=timeout)
            if menu is None:
                raise AssertionError(f"Dropdown '{label}' did not open (menu stayed hidden).")
            return menu
        except Exception as e:
            raise AssertionError(f"open_dropdown_menu('{label}') failed. Problem: {e}")
    # =========================
    # ICMP
    # =========================
    pass

    # ==========================================================
    # SNMPv2 
    # ==========================================================

    # ✅
    def set_SNMPv2_read_community(self, value: str, timeout: int = 8000):
        """
        Set SNMPv2 Read Community.
        """
        self.click_SNMPv2()
        self.set_app_input_value("readCommunity", value, timeout=timeout)

    # ✅
    def get_SNMPv2_read_community(self, timeout: int = 8000) -> str:
        """
        Get SNMPv2 Read Community.
        """
        self.click_SNMPv2()
        return self.get_app_input_value("readCommunity", timeout=timeout)

    # ✅
    def set_SNMPv2_write_community(self, value: str, timeout: int = 8000):
        """
        Set SNMPv2 Write Community.
        """
        self.click_SNMPv2()
        self.set_app_input_value("writeCommunity", value, timeout=timeout)

    # ✅
    def get_SNMPv2_write_community(self, timeout: int = 8000) -> str:
        """
        Get SNMPv2 Write Community.
        """
        self.click_SNMPv2()
        return self.get_app_input_value("writeCommunity", timeout=timeout)

    # ✅
    def set_SNMPv2_admin_community(self, value: str, timeout: int = 8000):
        """
        Set SNMPv2 Admin Community.
        """
        self.click_SNMPv2()
        self.set_app_input_value("adminCommunity", value, timeout=timeout)

    # ✅
    def get_SNMPv2_admin_community(self, timeout: int = 8000) -> str:
        """
        Get SNMPv2 Admin Community.
        """
        self.click_SNMPv2()
        return self.get_app_input_value("adminCommunity", timeout=timeout)

    # ✅
    def set_SNMPv2_contact_port(self, port: int, timeout: int = 8000):
        """
        Set SNMPv2 Contact Port.
        """
        self.click_SNMPv2()
        self.set_app_input_value("contactPort", str(port), timeout=timeout)

    # ✅
    def get_SNMPv2_contact_port(self, timeout: int = 8000) -> str:
        """
        Get SNMPv2 Contact Port.
        """
        self.click_SNMPv2()
        return self.get_app_input_value("contactPort", timeout=timeout)

    # ==========================================================
    # SNMPv3 fields
    # ==========================================================

    # ✅
    def SNMPv3_security_level_text(self, timeout: int = 8000) -> str:
        """
        Return the current SNMPv3 Security Level selected text.
        """
        try:
            self.click_SNMPv3(timeout=timeout)
            return self.clean(self.dropdown_selected_text("Security Level", timeout=timeout))
        except Exception as e:
            raise AssertionError(f"_snmpv3_security_level_text failed. Problem: {e}")
    
    # ✅
    def SNMPv3_expected_fields(self, timeout: int = 8000) -> dict:
        """
        Return which SNMPv3 fields should be visible based on the selected Security Level.
        """
        try:
            level = self.SNMPv3_security_level_text(timeout=timeout)

            # Normalize
            level_l = level.lower()

            expected = {
                "auth_protocol": False,
                "auth_password": False,
                "privacy_protocol": False,
                "privacy_password": False,
            }

            if level_l.lower() == "authentication, no privacy":
                expected["auth_protocol"] = True
                expected["auth_password"] = True
                return expected

            if level_l.lower() == "authentication, privacy":
                expected["auth_protocol"] = True
                expected["auth_password"] = True
                expected["privacy_protocol"] = True
                expected["privacy_password"] = True
                return expected

            # No Auth, No Privacy (default option)
            return expected

        except Exception as e:
            raise AssertionError(f"_snmpv3_expected_fields failed. Problem: {e}")

    # ✅
    def SNMPv3_assert_visibility_by_security_level(self, timeout: int = 8000):
        """
        Assert SNMPv3 UI fields visibility matches the selected Security Level.
        """
        try:
            self.click_SNMPv3(timeout=timeout)
            expected = self.SNMPv3_expected_fields(timeout=timeout)

            auth_protocol = self.page.locator("app-dropdown[label='Authentication Protocol']").first
            auth_password = self.page.locator("app-input[formcontrolname='authenticationPassword']").first
            privacy_protocol = self.page.locator("app-dropdown[label='Privacy Protocol']").first
            privacy_password = self.page.locator("app-input[formcontrolname='privacyPassword']").first

            # Authentication Protocol
            if expected["auth_protocol"]:
                expect(auth_protocol).to_be_visible(timeout=timeout)
            else:
                expect(auth_protocol).to_be_hidden(timeout=timeout)

            # Authentication Password
            if expected["auth_password"]:
                expect(auth_password).to_be_visible(timeout=timeout)
            else:
                expect(auth_password).to_be_hidden(timeout=timeout)

            # Privacy Protocol
            if expected["privacy_protocol"]:
                expect(privacy_protocol).to_be_visible(timeout=timeout)
            else:
                expect(privacy_protocol).to_be_hidden(timeout=timeout)

            # Privacy Password
            if expected["privacy_password"]:
                expect(privacy_password).to_be_visible(timeout=timeout)
            else:
                expect(privacy_password).to_be_hidden(timeout=timeout)

        except Exception as e:
            raise AssertionError(f"_snmpv3_assert_visibility_by_security_level failed. Problem: {e}")

    # ✅
    def set_SNMPv3_user_name(self, value: str, timeout: int = 8000):
        """
        Set SNMPv3 User Name.
        """
        self.click_SNMPv3()
        self.set_app_input_value("userName", value, timeout=timeout)

    # ✅
    def get_SNMPv3_user_name(self, timeout: int = 8000) -> str:
        """
        Get SNMPv3 User Name.
        """
        self.click_SNMPv3()
        return self.get_app_input_value("userName", timeout=timeout)
    
    # ✅
    def set_SNMPv3_security_level(self, value: str, timeout: int = 8000):
        """
        Set SNMPv3 Security Level dropdown.
        """
        self.click_SNMPv3(timeout=timeout)
        self.set_dropdown_with_validation("Security Level", value, timeout=timeout)

    # ✅
    def get_SNMPv3_security_level(self, timeout: int = 8000) -> str:
        """
        Get SNMPv3 Security Level dropdown value.
        """
        self.click_SNMPv3(timeout=timeout)
        return self.dropdown_selected_text("Security Level", timeout=timeout)

    # ✅
    def set_SNMPv3_contact_port(self, port: int, timeout: int = 8000):
        """
        Set SNMPv3 Contact Port.
        """
        self.click_SNMPv3(timeout=timeout)
        pane = self.active_tab_pane()
        self.set_app_input_value("contactPort", str(port), timeout=timeout, scope=pane)

    # ✅
    def get_SNMPv3_contact_port(self, timeout: int = 8000) -> str:
        """
        Get SNMPv3 Contact Port.
        """
        try:
            self.click_SNMPv3(timeout=timeout)
            pane = self.active_tab_pane()
            return self.get_app_input_value("contactPort", timeout=timeout, scope=pane)
        except Exception as e:
            raise AssertionError(f"get_SNMPv3_contact_port failed. Problem: {e}")

    # ✅
    def set_SNMPv3_authentication_protocol(self, value: str, timeout: int = 8000):
        """
        Set SNMPv3 Authentication Protocol dropdown.
        """
        try:
            self.click_SNMPv3(timeout=timeout)

            dropdown = self.app_dropdown("Authentication Protocol")
            expect(dropdown).to_be_visible(timeout=timeout)

            self.set_dropdown_with_validation("Authentication Protocol", value, timeout=timeout)

        except Exception as e:
            raise AssertionError(f"set_SNMPv3_authentication_protocol('{value}') failed. Problem: {e}")

    # ✅
    def get_SNMPv3_authentication_protocol(self, timeout: int = 8000) -> str:
        """
        Get SNMPv3 Authentication Protocol value.
        """
        try:
            self.click_SNMPv3(timeout=timeout)

            dropdown = self.app_dropdown("Authentication Protocol")
            expect(dropdown).to_be_visible(timeout=timeout)

            return self.dropdown_selected_text("Authentication Protocol", timeout=timeout)

        except Exception as e:
            raise AssertionError(f"get_SNMPv3_authentication_protocol failed. Problem: {e}")

    # ✅
    def set_SNMPv3_authentication_password(self, password: str, timeout: int = 8000):
        """
        Set SNMPv3 Authentication Password.
        """
        try:
            self.click_SNMPv3(timeout=timeout)

            inp = self.app_input_field("authenticationPassword")
            expect(inp).to_be_visible(timeout=timeout)

            inp.click(force=True)
            inp.fill("")
            inp.type(str(password), delay=5)

        except Exception as e:
            raise AssertionError(f"set_SNMPv3_authentication_password failed. Problem: {e}")

    # ✅
    def get_SNMPv3_authentication_password(self, timeout: int = 8000) -> str:
        """
        Get SNMPv3 Authentication Password value.
        """
        try:
            self.click_SNMPv3(timeout=timeout)

            inp = self.app_input_field("authenticationPassword")
            expect(inp).to_be_visible(timeout=timeout)

            return self.clean(inp.input_value())

        except Exception as e:
            raise AssertionError(f"get_SNMPv3_authentication_password failed. Problem: {e}")

    # ✅
    def set_SNMPv3_privacy_protocol(self, value: str, timeout: int = 8000):
        """
        Set SNMPv3 Privacy Protocol dropdown.
        """
        try:
            self.click_SNMPv3(timeout=timeout)

            dropdown = self.app_dropdown("Privacy Protocol")
            expect(dropdown).to_be_visible(timeout=timeout)

            self.set_dropdown_with_validation("Privacy Protocol", value, timeout=timeout)

        except Exception as e:
            raise AssertionError(f"set_SNMPv3_privacy_protocol('{value}') failed. Problem: {e}")

    # ✅
    def get_SNMPv3_privacy_protocol(self, timeout: int = 8000) -> str:
        """
        Get SNMPv3 Privacy Protocol value.
        """
        try:
            self.click_SNMPv3(timeout=timeout)

            dropdown = self.app_dropdown("Privacy Protocol")
            expect(dropdown).to_be_visible(timeout=timeout)

            return self.dropdown_selected_text("Privacy Protocol", timeout=timeout)

        except Exception as e:
            raise AssertionError(f"get_SNMPv3_privacy_protocol failed. Problem: {e}")

    # ✅
    def set_SNMPv3_privacy_password(self, password: str, timeout: int = 8000):
        """
        Set SNMPv3 Privacy Password.
        """
        try:
            self.click_SNMPv3(timeout=timeout)

            inp = self.app_input_field("privacyPassword")
            expect(inp).to_be_visible(timeout=timeout)

            inp.click(force=True)
            inp.fill("")
            inp.type(str(password), delay=5)

        except Exception as e:
            raise AssertionError(f"set_SNMPv3_privacy_password failed. Problem: {e}")

    # ✅
    def get_SNMPv3_privacy_password(self, timeout: int = 8000) -> str:
        """
        Get SNMPv3 Privacy Password value.
        """
        try:
            self.click_SNMPv3(timeout=timeout)

            inp = self.app_input_field("privacyPassword")
            expect(inp).to_be_visible(timeout=timeout)

            return self.clean(inp.input_value())

        except Exception as e:
            raise AssertionError(f"get_SNMPv3_privacy_password failed. Problem: {e}")

    # ✅
    def configure_SNMPv3_entire_process(
        self,
        security_level: str,
        auth_protocol: str = None,
        auth_password: str = None,
        privacy_protocol: str = None,
        privacy_password: str = None,
        timeout: int = 8000
    ):
        """
        Configure SNMPv3 settings safely based on the requested Security Level.
        """
        try:
            # 1) Set security level first (this drives which fields appear)
            self.set_SNMPv3_security_level(security_level, timeout=timeout)

            # 2) Validate UI state matches the selected level
            self.SNMPv3_assert_visibility_by_security_level(timeout=timeout)

            expected = self.SNMPv3_expected_fields(timeout=timeout)

            # 3) Authentication fields (only if expected)
            if expected["auth_protocol"]:
                if auth_protocol is None:
                    raise AssertionError("configure_SNMPv3: auth_protocol is required for this Security Level.")
                self.set_SNMPv3_authentication_protocol(auth_protocol, timeout=timeout)

            if expected["auth_password"]:
                if auth_password is None:
                    raise AssertionError("configure_SNMPv3: auth_password is required for this Security Level.")
                self.set_SNMPv3_authentication_password(auth_password, timeout=timeout)

            # 4) Privacy fields (only if expected)
            if expected["privacy_protocol"]:
                if privacy_protocol is None:
                    raise AssertionError("configure_SNMPv3: privacy_protocol is required for this Security Level.")
                self.set_SNMPv3_privacy_protocol(privacy_protocol, timeout=timeout)

            if expected["privacy_password"]:
                if privacy_password is None:
                    raise AssertionError("configure_SNMPv3: privacy_password is required for this Security Level.")
                self.set_SNMPv3_privacy_password(privacy_password, timeout=timeout)

            # 5) Final sanity check: UI still matches the level
            self.SNMPv3_assert_visibility_by_security_level(timeout=timeout)

        except Exception as e:
            raise AssertionError(f"configure_SNMPv3 failed. Problem: {e}")

    # ==========================================================
    # Performance Transport Protocol
    # ==========================================================

    # ✅
    def set_performance_transport_protocol(self, value: str, timeout: int = 8000):
        """
        Set Performance Transport Protocol dropdown.
        """
        self.set_dropdown_with_validation("Performance Transport Protocol", value, timeout=timeout)

    # ✅
    def get_performance_transport_protocol(self, timeout: int = 8000) -> str:
        """
        Get Performance Transport Protocol dropdown value.
        """
        return self.dropdown_selected_text("Performance Transport Protocol", timeout=timeout)

    # ==========================================================
    # Footer buttons
    # ==========================================================

    # ✅
    def reset_to_default_btn(self):
        """
        Return Reset to Default button.
        """
        return self.footer().locator("button.btn.simple-btn", has_text=re.compile(r"^\s*Reset to Default\s*$")).first

    # ✅
    def save_as_default_btn(self):
        """
        Return Save as Default button.
        """
        return self.footer().locator("button.btn.simple-btn.with-icon-btn", has_text=re.compile(r"^\s*Save as Default\s*$")).first

    # ✅
    def start_discovery_btn(self):
        """
        Return Start Discovery button.
        """
        return self.footer().locator("button.btn.btn-primary.default-btn", has_text=re.compile(r"^\s*Start Discovery\s*$")).first

    # ✅
    def default_override_modal(self):
        """
        Return the 'Confirm default override' modal dialog.
        """
        modal = self.page.locator("div.modal-dialog.pl-modal").filter(has=self.page.locator("div.title", has_text=re.compile(r"^\s*Confirm default override\s*$"))).first
        return modal

    # ✅
    def default_override_yes_btn(self):
        """
        Return the Yes button in the default override modal.
        """
        modal = self.default_override_modal()
        return modal.locator("div.actions button", has_text=re.compile(r"^\s*Yes\s*$")).first

    # ✅
    def default_override_no_btn(self):
        """
        Return the No button in the default override modal.
        """
        modal = self.default_override_modal()
        return modal.locator("div.actions button", has_text=re.compile(r"^\s*No\s*$")).first

    # ✅
    def click_button_and_validate_toast(self, success_text: str, failure_label: str, timeout: int = 8000) -> bool:
        """
        Click action validation using toast + overlay wrapper visibility.
        """
        try:
            toast = self.page.locator(f"text={success_text}")
            expect(toast).to_be_visible(timeout=timeout)

            overlay = self.page.locator("div.cdk-global-overlay-wrapper").first
            expect(overlay).to_be_visible(timeout=timeout)

            # wait toast disappear + overlay disappear
            expect(toast).to_be_hidden(timeout=timeout)
            expect(overlay).to_be_hidden(timeout=timeout)

            return True

        except Exception as e:
            raise AssertionError(f"{failure_label} failed. Problem: {e}")

    # ✅
    def click_reset_to_default(self, timeout: int = 8000):
        """
        Click Reset to Default button.
        """
        try:
            btn = self.reset_to_default_btn()
            expect(btn).to_be_visible(timeout=timeout)
            btn.click(force=True)
        except Exception as e:
            raise AssertionError(f"click_reset_to_default failed. Problem: {e}")

    # ✅
    def click_save_as_default(self, timeout: int = 8000):
        """
        Click Save as Default button.
        """
        try:
            btn = self.save_as_default_btn()
            expect(btn).to_be_visible(timeout=timeout)
            btn.click(force=True)
        except Exception as e:
            raise AssertionError(f"click_save_as_default failed. Problem: {e}")

    # ✅
    def confirm_default_override(self, timeout: int = 8000):
        """
        Click Yes on the default override confirmation modal that comes
        after the 'Save as Default' button.
        """
        try:
            modal = self.default_override_modal()
            self.wait_until(lambda: modal.count() > 0 and modal.is_visible(), timeout_ms=timeout, interval_ms=200)

            yes_btn = self.default_override_yes_btn()
            expect(yes_btn).to_be_visible(timeout=timeout)
            yes_btn.click(force=True)

            # wait modal to close
            self.wait_until(lambda: modal.count() == 0 or (not modal.is_visible()), timeout_ms=timeout, interval_ms=200)

        except Exception as e:
            raise AssertionError(f"confirm_default_override failed. Problem: {e}")

    # ✅
    def reject_default_override(self, timeout: int = 8000):
        """
        Click No on the default override confirmation modal that comes
        after the 'Save as Default' button.
        """
        try:
            modal = self.default_override_modal()
            self.wait_until(lambda: modal.count() > 0 and modal.is_visible(), timeout_ms=timeout, interval_ms=200)

            no_btn = self.default_override_no_btn()
            expect(no_btn).to_be_visible(timeout=timeout)
            no_btn.click(force=True)

            # wait modal to close
            self.wait_until(lambda: modal.count() == 0 or (not modal.is_visible()), timeout_ms=timeout, interval_ms=200)

        except Exception as e:
            raise AssertionError(f"reject_default_override failed. Problem: {e}")

    # ✅
    def click_start_discovery(self, timeout: int = 8000) -> bool:
        """
        Click Start Discovery and verify that the action succeeded.
        """
        try:
            btn = self.start_discovery_btn()
            expect(btn).to_be_visible(timeout=timeout)

            if btn.get_attribute("disabled") is not None:
                raise AssertionError("Start Discovery button is disabled.")

            btn.click(force=True)

            # Verify success message
            return self.click_button_and_validate_toast(success_text="Discovery process start Success", failure_label="click_start_discovery", timeout=timeout)

        except Exception as e:
            raise AssertionError(f"click_start_discovery failed. Problem: {e}")

    # ==========================================================
    # Close
    # ==========================================================

    # ✅
    def close_device_discovery(self, timeout: int = 10000):
        """
        Close the Device Discovery container using the X icon.
        """
        try:
            x = self.close_btn()
            expect(x).to_be_visible(timeout=timeout)

            inner = x.locator("i").first
            if inner.count() > 0:
                inner.click(force=True)
            else:
                x.click(force=True)

            # Wait container to disappear/hide
            cont = self.page.locator("div.device-discovery-container").first

            def closed():
                try:
                    return cont.count() == 0 or (not cont.is_visible())
                except Exception:
                    return True

            self.wait_until(closed, timeout_ms=timeout, interval_ms=200)

        except Exception as e:
            raise AssertionError(f"close_device_discovery failed. Problem: {e}")