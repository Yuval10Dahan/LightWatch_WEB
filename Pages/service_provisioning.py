"""
Created by: Yuval Dahan
Date: 28/01/2026
"""

import re
import time
from typing import Callable 
from time import sleep
from playwright.sync_api import Page, expect
from Utils.utils import refresh_page

SLEEP = 0.2


class ServiceProvisioning:
    """
    Service Provisioning page – actions for creating services (ROADM / OTN / CHASSIS)
    and exiting the provisioning screen.
    """

    def __init__(self, page: Page):
        self.page = page

    # ==========================================================
    # Locators
    # ==========================================================

    # ✅
    def modal(self):
        """
        Return the service provisioning modal container.
        """
        modal = self.page.locator("div.main-modal-content").first
        if modal.count() == 0:
            raise AssertionError("Service Provisioning modal not found: div.main-modal-content")
        return modal

    # ✅
    def modal_title(self):
        """
        Return the modal title element.
        """
        return self.modal().locator("div.title").first

    # ✅
    def service_btn(self, name: str):
        """
        Return a service button by name.
        """
        service_button = self.modal().locator("button.btn.btn-primary", has_text=re.compile(rf"^\s*{re.escape(name)}\s*$")).first
        sleep(SLEEP)

        return service_button 

    # ✅
    def exit_btn(self):
        """
        Return the Exit button in the modal.
        """
        return self.modal().locator("button.btn.btn-stroke", has_text=re.compile(r"^\s*Exit\s*$")).first

    # ==========================================================
    # Internal small helpers
    # ==========================================================

    # ✅
    def roadm_dropdown_by_label(self, label_text: str):
        """
        Returns ROADM Service dropdown container by label.
        """
        dropdown = self.page.locator(f"app-dropdown:has(div.label:has-text('{label_text}'))").first
        sleep(1)
        
        return dropdown

    # ✅
    def otn_dropdown_by_label(self, label_text: str):
        """
        Returns OTN Service dropdown container by label.
        """
        dropdown = self.page.locator(f"app-dropdown:has(div.label:has-text('{label_text}'))").first
        sleep(SLEEP)

        return dropdown

    # ==========================================================
    # Modal state helpers (using wait_until)
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
    def wait_modal_visible(self, timeout_ms: int = 12000):
        """
        Wait until the service provisioning modal is visible and ready.
        """
        self.wait_until(lambda: self.modal().is_visible(), timeout_ms=timeout_ms)
        self.wait_until(lambda: self.modal_title().is_visible(), timeout_ms=timeout_ms)
        self.wait_until(lambda: bool(re.match(r"^\s*Choose Service to create\s*$", self.modal_title().inner_text())), timeout_ms=timeout_ms)

    # ✅
    def wait_modal_hidden(self, timeout_ms: int = 12000):
        """
        Wait until the service provisioning modal is hidden or removed.
        """
        def _hidden():
            try:
                return not self.modal().is_visible()
            except Exception:
                return True

        self.wait_until(_hidden, timeout_ms=timeout_ms)

    # ==========================================================
    # Click actions 
    # ==========================================================
    
    # ✅
    def create_service(self, service_name: str, timeout_ms: int = 12000, close_modal_expected: bool = True):
        """
        Generic click on a service button inside 'Choose Service to create' modal.
        service_name: 'ROADM' / 'OTN' / 'CHASSIS'
        """
        self.wait_modal_visible(timeout_ms=timeout_ms)

        btn = self.service_btn(service_name)
        self.wait_until(lambda: btn.is_visible() and btn.is_enabled(), timeout_ms=timeout_ms)
        
        sleep(SLEEP)
        btn.click(force=True)

        if close_modal_expected:
            self.wait_modal_hidden(timeout_ms=timeout_ms)

    # ✅
    def create_ROADM_service(self, timeout_ms: int = 12000, close_modal_expected: bool = True):
        """
        Create a ROADM service from the modal.
        """
        self.create_service("ROADM", timeout_ms=timeout_ms, close_modal_expected=close_modal_expected)

    # ✅
    def create_OTN_service(self, timeout_ms: int = 12000, close_modal_expected: bool = True):
        """
        Create an OTN service from the modal.
        """
        self.create_service("OTN", timeout_ms=timeout_ms, close_modal_expected=close_modal_expected)
        sleep(3)
        refresh_page(self.page)

    # ✅
    def create_CHASSIS_service(self, timeout_ms: int = 12000, close_modal_expected: bool = True):
        """
        Create a CHASSIS service from the modal.
        """
        self.create_service("CHASSIS", timeout_ms=timeout_ms, close_modal_expected=close_modal_expected)

    # ✅
    def click_exit(self, timeout_ms: int = 12000):
        """
        Exit the create services window.
        """
        self.wait_modal_visible(timeout_ms=timeout_ms)
        btn = self.exit_btn()

        self.wait_until(lambda: btn.is_visible() and btn.is_enabled(), timeout_ms=timeout_ms)
        btn.click(force=True)

        # Exit should close modal / navigate away
        self.wait_modal_hidden(timeout_ms=timeout_ms)

    # ==========================================================
    # ROADM Service 
    # ==========================================================

    # ✅
    def set_ROADM_mode(self, mode: str, timeout_ms: int = 10000):
        """
        Set ROADM Service Mode.
        """

        try:
            dropdown = self.roadm_dropdown_by_label("Mode")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = dropdown.locator(".selected-view").first.inner_text(timeout=timeout_ms).strip()
            sleep(SLEEP)

            if selected_value == mode:
                return True

            dropdown.locator("button.dropdown-button").click(force=True)
            sleep(SLEEP)

            option = dropdown.locator(".dropdown-menu .dropdown-item", has_text=re.compile(rf"^\s*{re.escape(mode)}\s*$")).first
            sleep(SLEEP)

            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            self.wait_until(
                lambda: dropdown.locator(".selected-view").first.inner_text().strip() == mode,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            return True

        except Exception as e:
            raise AssertionError(f"set_ROADM_mode('{mode}') failed. Problem: {e}")
    
    # ✅
    def set_ROADM_protection(self, protection: str, timeout_ms: int = 10000):
        """
        Set ROADM Service Protection.
        """

        try:
            dropdown = self.roadm_dropdown_by_label("Protection")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = (
                dropdown.locator(".selected-view")
                .first
                .inner_text(timeout=timeout_ms)
                .strip()
            )

            sleep(SLEEP)

            # Already selected
            if selected_value == protection:
                return True

            # Open dropdown
            dropdown.locator("button.dropdown-button").click(force=True)
            sleep(SLEEP)

            # Select option
            option = dropdown.locator(".dropdown-menu .dropdown-item", has_text=re.compile(rf"^\s*{re.escape(protection)}\s*$")).first
            sleep(SLEEP)

            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            # Verify selected value updated
            self.wait_until(
                lambda: (
                    dropdown.locator(".selected-view")
                    .first
                    .inner_text()
                    .strip()
                ) == protection,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            return True

        except Exception as e:
            raise AssertionError(f"set_ROADM_protection('{protection}') failed. Problem: {e}")
    
    # ✅
    def set_ROADM_A_chassis(self, chassis: str, timeout_ms: int = 10000):
        """
        Set ROADM Service A chassis.
        """

        try:
            dropdown = self.roadm_dropdown_by_label("A chassis")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = (
                dropdown.locator(".selected-view")
                .first
                .inner_text(timeout=timeout_ms)
                .strip()
            )

            sleep(SLEEP)

            # Already selected
            if selected_value == chassis:
                return True

            # Open dropdown
            dropdown.locator("button.dropdown-button").click(force=True)
            sleep(SLEEP)

            # Select chassis option
            option = dropdown.locator(".dropdown-menu .dropdown-item", has_text=re.compile(rf"^\s*{re.escape(chassis)}\s*$")).first
            sleep(SLEEP)

            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            # Verify chassis updated
            self.wait_until(
                lambda: (
                    dropdown.locator(".selected-view")
                    .first
                    .inner_text()
                    .strip()
                ) == chassis,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(f"set_ROADM_A_chassis('{chassis}') failed. Problem: {e}")

    # ✅
    def set_ROADM_Z_chassis(self, chassis: str, timeout_ms: int = 10000):
        """
        Set ROADM Service Z chassis.
        """

        try:
            dropdown = self.roadm_dropdown_by_label("Z chassis")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = (
                dropdown.locator(".selected-view")
                .first
                .inner_text(timeout=timeout_ms)
                .strip()
            )

            sleep(SLEEP)

            # Already selected
            if selected_value == chassis:
                return True

            # Open dropdown
            dropdown.locator("button.dropdown-button").click(force=True)
            sleep(SLEEP)

            # Select chassis option
            option = dropdown.locator(".dropdown-menu .dropdown-item", has_text=re.compile(rf"^\s*{re.escape(chassis)}\s*$")).first
            sleep(SLEEP)

            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            # Verify chassis updated
            self.wait_until(
                lambda: (
                    dropdown.locator(".selected-view")
                    .first
                    .inner_text()
                    .strip()
                ) == chassis,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            return True

        except Exception as e:
            raise AssertionError(f"set_ROADM_Z_chassis('{chassis}') failed. Problem: {e}")

    # ✅
    def set_ROADM_provisioning_type(self, provisioning_type: str, timeout_ms: int = 10000):
        """
        Set ROADM Service Provisioning type.
        """

        try:
            dropdown = self.roadm_dropdown_by_label("Provisioning type")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = (
                dropdown.locator(".selected-view")
                .first
                .inner_text(timeout=timeout_ms)
                .strip()
            )

            sleep(SLEEP)

            # Already selected
            if selected_value == provisioning_type:
                return True

            # Open dropdown
            dropdown.locator("button.dropdown-button").click(force=True)
            sleep(SLEEP)

            # Select option
            option = dropdown.locator(".dropdown-menu .dropdown-item", 
            has_text=re.compile(rf"^\s*{re.escape(provisioning_type)}\s*$")).first
            sleep(SLEEP)

            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            # Verify provisioning type updated
            self.wait_until(
                lambda: (
                    dropdown.locator(".selected-view")
                    .first
                    .inner_text()
                    .strip()
                ) == provisioning_type,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            return True

        except Exception as e:
            raise AssertionError(f"set_ROADM_provisioning_type('{provisioning_type}') failed. Problem: {e}")

    # ✅
    def set_ROADM_bandwidth(self, bandwidth: str, timeout_ms: int = 10000):
        """
        Set ROADM Service Bandwidth.
        """

        try:
            dropdown = self.roadm_dropdown_by_label("Bandwidth")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = (
                dropdown.locator(".selected-view")
                .first
                .inner_text(timeout=timeout_ms)
                .strip()
            )

            sleep(SLEEP)

            # Already selected
            if selected_value == bandwidth:
                return True

            # Open dropdown
            dropdown.locator("button.dropdown-button").click(force=True)
            sleep(SLEEP)

            # Select bandwidth option
            option = dropdown.locator(".dropdown-menu .dropdown-item", has_text=re.compile(rf"^\s*{re.escape(bandwidth)}\s*$")).first
            sleep(SLEEP)

            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            # Verify bandwidth updated
            self.wait_until(
                lambda: (
                    dropdown.locator(".selected-view")
                    .first
                    .inner_text()
                    .strip()
                ) == bandwidth,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            return True

        except Exception as e:
            raise AssertionError(f"set_ROADM_bandwidth('{bandwidth}') failed. Problem: {e}")

    # ✅
    def set_ROADM_service_name(self, service_name: str, timeout_ms: int = 10000):
        """
        Set ROADM Service Name.
        """

        try:
            input_wrapper = self.page.locator("app-input:has(label.input-label:has-text('Service name'))").first
            sleep(SLEEP)

            expect(input_wrapper).to_be_visible(timeout=timeout_ms)

            input_field = input_wrapper.locator("input[type='text']").first
            sleep(SLEEP)

            expect(input_field).to_be_visible(timeout=timeout_ms)
            expect(input_field).to_be_enabled(timeout=timeout_ms)

            current_value = (input_field.input_value() or "").strip()

            if current_value == service_name:
                return True

            input_field.click(force=True)
            input_field.fill(service_name)

            self.wait_until(
                lambda: (input_field.input_value() or "").strip() == service_name,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            return True

        except Exception as e:
            raise AssertionError(f"set_ROADM_service_name('{service_name}') failed. Problem: {e}")
    
    # ✅
    def enable_ROADM_path_restriction(self, timeout_ms: int = 10000):
        """
        Enable ROADM Path restriction checkbox.

        - If already enabled -> do nothing
        - Else click checkbox and verify it became enabled
        """

        try:
            checkbox = self.page.locator("app-checkbox:has-text('Path restriction')").first
            sleep(SLEEP)

            expect(checkbox).to_be_visible(timeout=timeout_ms)

            # Inner clickable checkbox element
            checkbox_input = checkbox.locator("input[type='checkbox']").first
            sleep(SLEEP)

            is_checked = checkbox_input.is_checked()

            # Already enabled
            if is_checked:
                return True

            checkbox.click(force=True)

            self.wait_until(
                lambda: checkbox_input.is_checked(),
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            return True

        except Exception as e:
            raise AssertionError(f"enable_ROADM_path_restriction failed. Problem: {e}")

    # ✅
    def disable_ROADM_path_restriction(self, timeout_ms: int = 10000):
        """
        Disable ROADM Path restriction checkbox.

        - If already disabled -> do nothing
        - Else click checkbox and verify it became disabled
        """

        try:
            checkbox = self.page.locator("app-checkbox:has-text('Path restriction')").first
            sleep(SLEEP)

            expect(checkbox).to_be_visible(timeout=timeout_ms)

            # Inner checkbox input
            checkbox_input = checkbox.locator("input[type='checkbox']").first
            sleep(SLEEP)

            is_checked = checkbox_input.is_checked()

            # Already disabled
            if not is_checked:
                return True

            checkbox.click(force=True)

            self.wait_until(
                lambda: not checkbox_input.is_checked(),
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            return True

        except Exception as e:
            raise AssertionError(f"disable_ROADM_path_restriction failed. Problem: {e}")

    # ✅
    def ROADM_service_click_next(self, timeout_ms: int = 10000):
        """
        Click the ROADM Service 'Next' button.
        """

        try:
            next_btn = self.page.locator("button.next-btn", has_text=re.compile(r"^\s*Next\s*$")).first
            sleep(SLEEP)

            expect(next_btn).to_be_visible(timeout=timeout_ms)
            expect(next_btn).to_be_enabled(timeout=timeout_ms)

            before_content = self.page.locator(".roadm-service-content").first.inner_text(timeout=timeout_ms)
            sleep(SLEEP)

            next_btn.click(force=True)

            self.wait_until(
                lambda: (
                    self.page.locator(".roadm-service-content")
                    .first
                    .inner_text()
                    != before_content
                ),
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(f"ROADM_service_click_next failed. Problem: {e}")

    # ✅ 
    def ROADM_service_click_back(self, timeout_ms: int = 10000):
        """
        Click the ROADM Service 'Back' button.

        - Wait until button is visible and enabled
        - Click it
        - Verify the wizard moved back to the previous step
        """

        try:
            back_btn = self.page.locator("button.back-btn", has_text=re.compile(r"^\s*Back\s*$")).first
            sleep(SLEEP)

            expect(back_btn).to_be_visible(timeout=timeout_ms)
            expect(back_btn).to_be_enabled(timeout=timeout_ms)

            before_content = self.page.locator(".roadm-service-content").first.inner_text(timeout=timeout_ms)
            sleep(SLEEP)

            back_btn.click(force=True)

            self.wait_until(
                lambda: (
                    self.page.locator(".roadm-service-content")
                    .first
                    .inner_text()
                    != before_content
                ),
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(f"ROADM_service_click_back failed. Problem: {e}")

    # ✅ 
    def set_ROADM_path1_A_device(self, device: str, timeout_ms: int = 10000):
        """
        Set ROADM Path 1 A device.
        """

        try:
            dropdown = self.roadm_dropdown_by_label("Path 1: A device")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = (
                dropdown.locator(".selected-view")
                .first
                .inner_text(timeout=timeout_ms)
                .strip()
            )

            sleep(SLEEP)

            if selected_value == device:
                return True

            dropdown.locator("button.dropdown-button").click(force=True)
            sleep(SLEEP)

            option = dropdown.locator(".dropdown-menu .dropdown-item", has_text=re.compile(rf"^\s*{re.escape(device)}\s*$")).first

            sleep(SLEEP)

            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            self.wait_until(
                lambda: (
                    dropdown.locator(".selected-view")
                    .first
                    .inner_text()
                    .strip()
                ) == device,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(f"set_ROADM_path1_A_device('{device}') failed. Problem: {e}")

    # ✅
    def set_ROADM_path1_A_port(self, port: str, timeout_ms: int = 10000):
        """
        Set ROADM Path 1 A port.
        """

        try:
            dropdown = self.roadm_dropdown_by_label("Path 1: A port")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = (
                dropdown.locator(".selected-view")
                .first
                .inner_text(timeout=timeout_ms)
                .strip()
            )

            sleep(SLEEP)

            # Already selected
            if selected_value == port:
                return True

            # Open dropdown
            dropdown.locator("button.dropdown-button").click(force=True)
            sleep(SLEEP)

            # Select port option
            option = dropdown.locator(".dropdown-menu .dropdown-item",
                has_text=re.compile(rf"^\s*{re.escape(port)}\s*$")).first

            sleep(SLEEP)

            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            # Verify selected port updated
            self.wait_until(
                lambda: (
                    dropdown.locator(".selected-view")
                    .first
                    .inner_text()
                    .strip()
                ) == port,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(
                f"set_ROADM_path1_A_port('{port}') failed. Problem: {e}"
            )

    # ✅
    def set_ROADM_path1_Z_device(self, device: str, timeout_ms: int = 10000):
        """
        Set ROADM Path 1 Z device.
        """

        try:
            dropdown = self.roadm_dropdown_by_label("Path 1: Z device")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = (
                dropdown.locator(".selected-view")
                .first
                .inner_text(timeout=timeout_ms)
                .strip()
            )

            sleep(SLEEP)

            # Already selected
            if selected_value == device:
                return True

            # Open dropdown
            dropdown.locator("button.dropdown-button").click(force=True)
            sleep(SLEEP)

            # Select device option
            option = dropdown.locator(".dropdown-menu .dropdown-item",
                has_text=re.compile(rf"^\s*{re.escape(device)}\s*$")).first
            sleep(SLEEP)

            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            # Verify selected device updated
            self.wait_until(
                lambda: (
                    dropdown.locator(".selected-view")
                    .first
                    .inner_text()
                    .strip()
                ) == device,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(f"set_ROADM_path1_Z_device('{device}') failed. Problem: {e}")

    # ✅
    def set_ROADM_path1_Z_port(self, port: str, timeout_ms: int = 10000):
        """
        Set ROADM Path 1 Z port.
        """

        try:
            dropdown = self.roadm_dropdown_by_label("Path 1: Z port")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = (
                dropdown.locator(".selected-view")
                .first
                .inner_text(timeout=timeout_ms)
                .strip()
            )

            sleep(SLEEP)

            # Already selected
            if selected_value == port:
                return True

            # Open dropdown
            dropdown.locator("button.dropdown-button").click(force=True)
            sleep(SLEEP)

            # Select port option
            option = dropdown.locator(".dropdown-menu .dropdown-item",
                has_text=re.compile(rf"^\s*{re.escape(port)}\s*$")).first

            sleep(SLEEP)

            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            # Verify selected port updated
            self.wait_until(
                lambda: (
                    dropdown.locator(".selected-view")
                    .first
                    .inner_text()
                    .strip()
                ) == port,
                timeout_ms=timeout_ms,
                interval_ms=200
            )
            
            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(f"set_ROADM_path1_Z_port('{port}') failed. Problem: {e}")

    # ✅
    def set_ROADM_path2_A_device(self, device: str, timeout_ms: int = 10000):
        """
        Set ROADM Path 2 A device.
        """

        try:
            dropdown = self.roadm_dropdown_by_label("Path 2: A device")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = (
                dropdown.locator(".selected-view")
                .first
                .inner_text(timeout=timeout_ms)
                .strip()
            )

            sleep(SLEEP)

            if selected_value == device:
                return True

            dropdown.locator("button.dropdown-button").click(force=True)
            sleep(SLEEP)

            option = dropdown.locator(".dropdown-menu .dropdown-item", has_text=re.compile(rf"^\s*{re.escape(device)}\s*$")).first

            sleep(SLEEP)

            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            self.wait_until(
                lambda: (
                    dropdown.locator(".selected-view")
                    .first
                    .inner_text()
                    .strip()
                ) == device,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(f"set_ROADM_path2_A_device('{device}') failed. Problem: {e}")

    # ✅
    def set_ROADM_path2_A_port(self, port: str, timeout_ms: int = 10000):
        """
        Set ROADM Path 2 A port.
        """

        try:
            dropdown = self.roadm_dropdown_by_label("Path 2: A port")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = (
                dropdown.locator(".selected-view")
                .first
                .inner_text(timeout=timeout_ms)
                .strip()
            )

            sleep(SLEEP)

            # Already selected
            if selected_value == port:
                return True

            # Open dropdown
            dropdown.locator("button.dropdown-button").click(force=True)
            sleep(SLEEP)

            # Select port option
            option = dropdown.locator(".dropdown-menu .dropdown-item",
                has_text=re.compile(rf"^\s*{re.escape(port)}\s*$")).first

            sleep(SLEEP)

            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            # Verify selected port updated
            self.wait_until(
                lambda: (
                    dropdown.locator(".selected-view")
                    .first
                    .inner_text()
                    .strip()
                ) == port,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(
                f"set_ROADM_path2_A_port('{port}') failed. Problem: {e}"
            )

    # ✅
    def set_ROADM_path2_Z_device(self, device: str, timeout_ms: int = 10000):
        """
        Set ROADM Path 2 Z device.
        """

        try:
            dropdown = self.roadm_dropdown_by_label("Path 2: Z device")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = (
                dropdown.locator(".selected-view")
                .first
                .inner_text(timeout=timeout_ms)
                .strip()
            )

            sleep(SLEEP)

            # Already selected
            if selected_value == device:
                return True

            # Open dropdown
            dropdown.locator("button.dropdown-button").click(force=True)
            sleep(SLEEP)

            # Select device option
            option = dropdown.locator(".dropdown-menu .dropdown-item",
                has_text=re.compile(rf"^\s*{re.escape(device)}\s*$")).first
            sleep(SLEEP)

            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            # Verify selected device updated
            self.wait_until(
                lambda: (
                    dropdown.locator(".selected-view")
                    .first
                    .inner_text()
                    .strip()
                ) == device,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(f"set_ROADM_path2_Z_device('{device}') failed. Problem: {e}")

    # ✅
    def set_ROADM_path2_Z_port(self, port: str, timeout_ms: int = 10000):
        """
        Set ROADM Path 2 Z port.
        """

        try:
            dropdown = self.roadm_dropdown_by_label("Path 2: Z port")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = (
                dropdown.locator(".selected-view")
                .first
                .inner_text(timeout=timeout_ms)
                .strip()
            )

            sleep(SLEEP)

            # Already selected
            if selected_value == port:
                return True

            # Open dropdown
            dropdown.locator("button.dropdown-button").click(force=True)
            sleep(SLEEP)

            # Select port option
            option = dropdown.locator(".dropdown-menu .dropdown-item",
                has_text=re.compile(rf"^\s*{re.escape(port)}\s*$")).first

            sleep(SLEEP)

            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            # Verify selected port updated
            self.wait_until(
                lambda: (
                    dropdown.locator(".selected-view")
                    .first
                    .inner_text()
                    .strip()
                ) == port,
                timeout_ms=timeout_ms,
                interval_ms=200
            )
            
            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(f"set_ROADM_path2_Z_port('{port}') failed. Problem: {e}")
    
    # ✅
    def get_ROADM_path1_routes_table(self, timeout_ms: int = 10000) -> list[dict]:
        """
        Read ROADM Path 1 routes table.

        Example return:
            [
                {
                    "#": "0",
                    "Hops [v]": "2",
                    "Lengths, km": "0",
                    "SRLG in use": ""
                }
            ]
        """

        try:
            table = self.page.locator(".roadm-service-content table").first
            sleep(SLEEP)

            expect(table).to_be_visible(timeout=timeout_ms)

            headers = [
                h.strip()
                for h in table.locator("thead th").all_inner_texts()
                if h.strip()
            ]

            rows = table.locator("tbody tr")
            result = []

            for i in range(rows.count()):
                cells = [
                    c.strip()
                    for c in rows.nth(i).locator("td").all_inner_texts()
                ]

                if not cells:
                    continue

                row_dict = {}

                for idx, header in enumerate(headers):
                    row_dict[header] = cells[idx] if idx < len(cells) else ""

                result.append(row_dict)

            return result

        except Exception as e:
            raise AssertionError(f"get_ROADM_path1_routes_table failed. Problem: {e}")

    # ✅
    def ROADM_path1_click_on_route(self, index: int = 0, timeout_ms: int = 10000):
        """
        Click a route row in the ROADM Path Selection step.

        Args:
            index:
                0 = first route
                1 = second route
                ...
        """

        try:
            rows = self.page.locator("app-roadm-path-selection-step tbody tr")

            row_count = rows.count()

            if index < 0 or index >= row_count:
                raise AssertionError(f"Route index {index} out of range. Available routes: {row_count}")

            row = rows.nth(index)

            expect(row).to_be_visible(timeout=timeout_ms)

            row.scroll_into_view_if_needed()
            sleep(SLEEP)

            row.click(force=True)

            # Wait until row becomes selected
            self.wait_until(
                lambda: "selected" in (
                    row.get_attribute("class") or ""
                ),
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            # Wait until Next becomes enabled
            next_btn = self.page.locator("button.next-btn").first

            expect(next_btn).to_be_visible(timeout=timeout_ms)

            self.wait_until(
                lambda: next_btn.is_enabled(),
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(f"click_on_route({index}) failed. Problem: {e}")

    # ✅
    def set_ROADM_path1_channel(self, channel: str, timeout_ms: int = 10000):
        """
        Set ROADM Path 1 Channel.

        Example:
            set_ROADM_path1_channel("# 13")
        """

        try:
            channel = (channel or "").strip()
            if not channel:
                raise ValueError("channel is empty")

            # Normalize channel value
            if not channel.startswith("#"):
                channel = f"#{channel}"

            dropdown = self.roadm_dropdown_by_label("Path 1: Channel")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = (
                dropdown.locator(".selected-view")
                .first
                .inner_text(timeout=timeout_ms)
                .strip()
            )

            if selected_value == channel:
                return True

            btn = dropdown.locator("button.dropdown-button").first
            expect(btn).to_be_visible(timeout=timeout_ms)
            expect(btn).to_be_enabled(timeout=timeout_ms)

            btn.click(force=True)
            sleep(SLEEP)

            menu = dropdown.locator(".dropdown-menu").first
            expect(menu).to_be_visible(timeout=timeout_ms)

            option = menu.locator(".dropdown-item",has_text=re.compile(rf"^\s*{re.escape(channel)}\s*$", re.IGNORECASE)).first

            if option.count() == 0:
                options = [
                    x.strip()
                    for x in menu.locator(".dropdown-item").all_inner_texts()
                    if x.strip()
                ]
                raise AssertionError(
                    f"ROADM Path 1 Channel '{channel}' not found. Available: {options}"
                )

            option.scroll_into_view_if_needed()
            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            self.wait_until(
                lambda: (
                    dropdown.locator(".selected-view")
                    .first
                    .inner_text()
                    .strip()
                ) == channel,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"set_ROADM_path1_channel('{channel}') failed. Problem: {e}")

    # ✅
    def ROADM_service_create(self, timeout_ms: int = 10000):
        """
        Click the ROADM Service 'Create' button.

        Used on the final ROADM step after selecting the channel.
        """

        try:
            create_btn = self.page.locator("button.btn.btn-primary.default-btn",has_text=re.compile(r"^\s*Create\s*$")).first

            sleep(SLEEP)

            expect(create_btn).to_be_visible(timeout=timeout_ms)
            expect(create_btn).to_be_enabled(timeout=timeout_ms)

            before_url = self.page.url
            before_content = self.page.locator(".roadm-service-content").first.inner_text(timeout=timeout_ms)

            create_btn.click(force=True)

            # After create, usually modal closes / page changes / content changes.
            self.wait_until(
                lambda: (
                    self.page.locator(".roadm-service-content").count() == 0
                    or not self.page.locator(".roadm-service-content").first.is_visible()
                    or self.page.url != before_url
                    or self.page.locator(".roadm-service-content").first.inner_text() != before_content
                ),
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(10)
            return True

        except Exception as e:
            raise AssertionError(f"ROADM_service_create failed. Problem: {e}")

    # ==========================================================
    # OTN Service  
    # ==========================================================
    
    # ✅
    def set_OTN_A_node(self, node: str, timeout_ms: int = 40000):
        """
        Set OTN Service A-Node.
        """

        try:
            node = (node or "").strip()
            if not node:
                raise ValueError("node is empty")

            dropdown = self.page.locator(
                "app-dropdown:has(div.label:text-is('A-Node')), "
                "app-dropdown[label='A-Node']"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected = dropdown.locator(".selected-view span, .selected-view").first
            expect(selected).to_be_visible(timeout=timeout_ms)

            current_value = self._clean(selected.inner_text()) if hasattr(self, "_clean") else re.sub(r"\s+", " ", selected.inner_text().strip())

            if current_value.lower() == node.lower():
                return True

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
            expect(btn).to_be_visible(timeout=timeout_ms)
            expect(btn).to_be_enabled(timeout=timeout_ms)

            btn.click(force=True)

            # Menu can be inside the dropdown OR attached globally
            menu = self.page.locator(
                "div.dropdown-menu[data-label='A-Node'].show, "
                "div.dropdown-menu[data-label='A-Node'], "
                "app-dropdown:has(div.label:text-is('A-Node')) div.dropdown-menu.show, "
                "app-dropdown:has(div.label:text-is('A-Node')) div.dropdown-menu"
            ).first

            expect(menu).to_be_visible(timeout=timeout_ms)

            def clean_text(txt: str) -> str:
                return re.sub(r"\s+", " ", (txt or "").strip())

            target = clean_text(node).lower()

            items = menu.locator("li.dropdown-item")
            target_item = None

            for i in range(items.count()):
                item = items.nth(i)
                item_text = clean_text(item.inner_text())

                if item_text.lower() == target:
                    target_item = item
                    break

            if target_item is None:
                options = [
                    clean_text(x)
                    for x in items.all_inner_texts()
                    if clean_text(x)
                ]

                raise AssertionError(f"A-Node '{node}' not found. Available options: {options}")

            target_item.scroll_into_view_if_needed()
            expect(target_item).to_be_visible(timeout=timeout_ms)
            target_item.click(force=True)

            self.wait_until(
                lambda: clean_text(
                    dropdown.locator(".selected-view span, .selected-view").first.inner_text()
                ).lower() == target,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"set_OTN_A_node('{node}') failed. Problem: {e}")
    
    # ✅
    def set_OTN_A_port(self, port: str, timeout_ms: int = 40000):
        """
        Set OTN Service A-Port.
        """

        try:
            port = (port or "").strip()
            if not port:
                raise ValueError("port is empty")

            dropdown = self.page.locator(
                "app-dropdown[formcontrolname='aPort'], "
                "app-dropdown[label='A-Port'], "
                "app-dropdown:has(div.label:text-is('A-Port'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected = dropdown.locator(".selected-view span, .selected-view").first
            expect(selected).to_be_visible(timeout=timeout_ms)

            current_value = self._clean(selected.inner_text()) if hasattr(self, "_clean") else re.sub(r"\s+", " ", selected.inner_text().strip())

            if current_value.lower() == port.lower():
                return True

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
            expect(btn).to_be_visible(timeout=timeout_ms)
            expect(btn).to_be_enabled(timeout=timeout_ms)

            btn.click(force=True)

            menu = self.page.locator(
                "div.dropdown-menu[data-label='A-Port'].show, "
                "div.dropdown-menu[data-label='A-Port'], "
                "app-dropdown[formcontrolname='aPort'] div.dropdown-menu.show, "
                "app-dropdown[formcontrolname='aPort'] div.dropdown-menu"
            ).first

            expect(menu).to_be_visible(timeout=timeout_ms)

            # Wait until options are loaded
            self.wait_until(
                lambda: menu.locator("li.dropdown-item").count() > 0,
                timeout_ms=timeout_ms,
                interval_ms=300
            )

            def clean_text(txt: str) -> str:
                return re.sub(r"\s+", " ", (txt or "").strip())

            target = clean_text(port).lower()
            items = menu.locator("li.dropdown-item")

            target_item = None
            for i in range(items.count()):
                item = items.nth(i)
                item_text = clean_text(item.inner_text())

                if item_text.lower() == target:
                    target_item = item
                    break

            if target_item is None:
                options = [
                    clean_text(x)
                    for x in items.all_inner_texts()
                    if clean_text(x)
                ]

                raise AssertionError(f"A-Port '{port}' not found. Available options: {options}")

            target_item.scroll_into_view_if_needed()
            expect(target_item).to_be_visible(timeout=timeout_ms)
            target_item.click(force=True)

            self.wait_until(
                lambda: clean_text(
                    dropdown.locator(".selected-view span, .selected-view").first.inner_text()
                ).lower() == target,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"set_OTN_A_port('{port}') failed. Problem: {e}")

    
    def OTN_service_refresh(self, timeout_ms: int = 10000):
        """
        Click the OTN Service refresh/swap button.

        The button is located between A-Port and the other side selection.
        """

        try:
            # refresh_btn = self.page.locator("button.btn-reset:has(app-icon[name='right-left'])").first
            refresh_btn = self.page.locator("button.btn-reset").first
            sleep(SLEEP)

            expect(refresh_btn).to_be_visible(timeout=timeout_ms)
            expect(refresh_btn).to_be_enabled(timeout=timeout_ms)

            refresh_btn.click(force=True)

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"OTN_service_refresh failed. Problem: {e}")

    # ✅
    def enable_OTN_protection(self, timeout_ms: int = 10000):
        """
        Enable OTN Protection slide toggle.

        - If already enabled -> do nothing
        - Else click toggle and verify it became enabled
        """

        try:
            toggle = self.page.locator("app-slide-toggle:has(span:text-is('Protection'))").first
            sleep(SLEEP)

            expect(toggle).to_be_visible(timeout=timeout_ms)

            svg = toggle.locator("svg").first
            sleep(SLEEP)

            current_class = svg.get_attribute("class") or ""

            # Already enabled
            if "init" not in current_class:
                return True

            # Click the actual toggle
            svg.click(force=True)

            self.wait_until(
                lambda: (
                    self.page.locator(
                        "app-slide-toggle:has(span:text-is('Protection')) svg rect"
                    ).nth(0).get_attribute("fill") == "#FFD520"
                    and
                    self.page.locator(
                        "app-slide-toggle:has(span:text-is('Protection')) svg rect"
                    ).nth(2).get_attribute("x") == "32"
                ),
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(f"enable_OTN_protection failed. Problem: {e}")

    # ✅
    def disable_OTN_protection(self, timeout_ms: int = 10000):
        """
        Disable OTN Protection slide toggle.

        - If already disabled -> do nothing
        - Else click toggle and verify it became disabled
        """

        try:
            toggle = self.page.locator("app-slide-toggle:has(span:text-is('Protection'))").first
            sleep(SLEEP)

            expect(toggle).to_be_visible(timeout=timeout_ms)

            # Disabled state:
            # rect[0] fill = #EAEAEA
            # rect[2] x = 16

            background_rect = toggle.locator("svg rect").nth(0)
            sleep(SLEEP)
            knob_rect = toggle.locator("svg rect").nth(2)
            sleep(SLEEP)

            current_fill = background_rect.get_attribute("fill")
            current_x = knob_rect.get_attribute("x")

            # Already disabled
            if current_fill == "#EAEAEA" and current_x == "16":
                return True

            # Click toggle
            toggle.locator("svg").first.click(force=True)

            # Re-query every poll because Angular re-renders
            self.wait_until(
                lambda: (
                    self.page.locator(
                        "app-slide-toggle:has(span:text-is('Protection')) svg rect"
                    ).nth(0).get_attribute("fill") == "#EAEAEA"
                    and
                    self.page.locator(
                        "app-slide-toggle:has(span:text-is('Protection')) svg rect"
                    ).nth(2).get_attribute("x") == "16"
                ),
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(f"disable_OTN_protection failed. Problem: {e}")

    
    def set_OTN_service_type(self, service_type: str, timeout_ms: int = 10000):
        """
        Set OTN Service Type.
        """

        try:
            service_type = (service_type or "").strip()
            if not service_type:
                raise ValueError("service_type is empty")

            dropdown = self.page.locator(
                "app-dropdown[formcontrolname='serviceType'], "
                "app-dropdown[label='Service Type'], "
                "app-dropdown:has(div.label:text-is('Service Type'))"
            ).first

            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected = dropdown.locator(".selected-view span, .selected-view").first
            expect(selected).to_be_visible(timeout=timeout_ms)

            current_value = self._clean(selected.inner_text()) if hasattr(self, "_clean") else re.sub(r"\s+", " ", selected.inner_text().strip())

            if current_value.lower() == service_type.lower():
                return True

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle]").first
            expect(btn).to_be_visible(timeout=timeout_ms)
            expect(btn).to_be_enabled(timeout=timeout_ms)

            btn.click(force=True)

            menu = self.page.locator(
                "div.dropdown-menu[data-label='Service Type'].show, "
                "div.dropdown-menu[data-label='Service Type'], "
                "app-dropdown[formcontrolname='serviceType'] div.dropdown-menu.show, "
                "app-dropdown[formcontrolname='serviceType'] div.dropdown-menu"
            ).first

            expect(menu).to_be_visible(timeout=timeout_ms)

            self.wait_until(
                lambda: menu.locator("li.dropdown-item").count() > 0,
                timeout_ms=timeout_ms,
                interval_ms=300
            )

            def clean_text(txt: str) -> str:
                return re.sub(r"\s+", " ", (txt or "").strip())

            target = clean_text(service_type).lower()
            items = menu.locator("li.dropdown-item")

            target_item = None
            for i in range(items.count()):
                item = items.nth(i)
                if clean_text(item.inner_text()).lower() == target:
                    target_item = item
                    break

            if target_item is None:
                options = [
                    clean_text(x)
                    for x in items.all_inner_texts()
                    if clean_text(x)
                ]
                raise AssertionError(f"Service Type '{service_type}' not found. Available options: {options}")

            target_item.scroll_into_view_if_needed()
            expect(target_item).to_be_visible(timeout=timeout_ms)
            target_item.click(force=True)

            self.wait_until(
                lambda: clean_text(
                    dropdown.locator(".selected-view span, .selected-view").first.inner_text()
                ).lower() == target,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"set_OTN_service_type('{service_type}') failed. Problem: {e}")
   
    # ✅
    def enable_OTN_rate_limit(self, timeout_ms: int = 10000):
        """
        Enable OTN Rate Limit slide toggle.

        - If already enabled -> do nothing
        - Else click toggle and verify it became enabled
        """

        try:
            sleep(SLEEP)
            toggle = self.page.locator("app-slide-toggle:has(span:text-is('Rate Limit'))").first
            sleep(SLEEP)

            expect(toggle).to_be_visible(timeout=timeout_ms)

            # Enabled state:
            # rect[0] fill = #FFD520
            # rect[2] x = 32

            background_rect = toggle.locator("svg rect").nth(0)
            knob_rect = toggle.locator("svg rect").nth(2)

            current_fill = background_rect.get_attribute("fill")
            current_x = knob_rect.get_attribute("x")

            # Already enabled
            if current_fill == "#FFD520" and current_x == "32":
                return True

            # Click toggle
            toggle.locator("svg").first.click(force=True)
            sleep(SLEEP)

            # Re-query every poll because Angular re-renders
            self.wait_until(
                lambda: (
                    self.page.locator(
                        "app-slide-toggle:has(span:text-is('Rate Limit')) svg rect"
                    ).nth(0).get_attribute("fill") == "#FFD520"
                    and
                    self.page.locator(
                        "app-slide-toggle:has(span:text-is('Rate Limit')) svg rect"
                    ).nth(2).get_attribute("x") == "32"
                ),
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)

            return True

        except Exception as e:
            raise AssertionError(f"enable_OTN_rate_limit failed. Problem: {e}")

    # ✅
    def set_OTN_limit_to(self, limit_to: str, timeout_ms: int = 10000):
        """
        Set OTN Rate Limit 'Limit to' dropdown.
        """

        try:
            dropdown = self.otn_dropdown_by_label("Limit to")
            expect(dropdown).to_be_visible(timeout=timeout_ms)

            selected_value = (
                dropdown.locator(".selected-view")
                .first
                .inner_text(timeout=timeout_ms)
                .strip()
            )

            if selected_value == limit_to:
                return True

            dropdown.locator("button.dropdown-button").click(force=True)
            sleep(SLEEP)

            option = dropdown.locator(".dropdown-menu .dropdown-item", has_text=limit_to).first
            sleep(SLEEP)

            expect(option).to_be_visible(timeout=timeout_ms)
            option.click(force=True)

            self.wait_until(
                lambda: (
                    dropdown.locator(".selected-view")
                    .first
                    .inner_text()
                    .strip()
                ) == limit_to,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"set_OTN_limit_to('{limit_to}') failed. Problem: {e}")

    # ✅
    def disable_OTN_rate_limit(self, timeout_ms: int = 10000):
        try:
            toggle = self.page.locator("app-slide-toggle:has(span:text-is('Rate Limit'))").first

            sleep(SLEEP)
            expect(toggle).to_be_visible(timeout=timeout_ms)

            background_rect = toggle.locator("svg rect").nth(0)
            knob_rect = toggle.locator("svg rect").nth(2)

            current_fill = background_rect.get_attribute("fill")
            current_x = knob_rect.get_attribute("x")

            if current_fill == "#EAEAEA" and current_x == "16":
                return True

            toggle.locator("svg").first.click(force=True)

            self.wait_until(
                lambda: (
                    self.page.locator(
                        "app-slide-toggle:has(span:text-is('Rate Limit')) svg rect"
                    ).nth(0).get_attribute("fill") == "#EAEAEA"
                    and
                    self.page.locator(
                        "app-slide-toggle:has(span:text-is('Rate Limit')) svg rect"
                    ).nth(2).get_attribute("x") == "16"
                ),
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"disable_OTN_rate_limit failed. Problem: {e}")
    

    def set_OTN_Z_node(self, node: str, timeout_ms: int = 40000):
        pass


    def set_OTN_Z_port(self, port: str, timeout_ms: int = 40000):
        pass

    # ✅
    def set_OTN_service_name(self, service_name: str, timeout_ms: int = 40000):
        """
        Set OTN Service Name.
        """

        try:
            service_name = (service_name or "").strip()
            if not service_name:
                raise ValueError("service_name is empty")

            input_wrapper = self.page.locator(
                "app-input[formcontrolname='serviceName'], "
                "app-input:has(label.input-label:text-is('Service Name'))"
            ).first

            expect(input_wrapper).to_be_visible(timeout=timeout_ms)

            input_field = input_wrapper.locator("input[type='text']").first

            expect(input_field).to_be_visible(timeout=timeout_ms)
            expect(input_field).to_be_enabled(timeout=timeout_ms)

            current_value = (input_field.input_value() or "").strip()

            if current_value == service_name:
                return True

            input_field.click(force=True)
            input_field.fill(service_name)

            self.wait_until(
                lambda: (input_field.input_value() or "").strip() == service_name,
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"set_OTN_service_name('{service_name}') failed. Problem: {e}")
     
    # ✅
    def enable_OTN_auto_path(self, timeout_ms: int = 10000):
        """
        Enable OTN Auto Path toggle.
        """

        try:
            toggle = self.page.locator(
                "app-slide-toggle[formcontrolname='autoPath'], "
                "app-slide-toggle:has(span:text-is('Auto Path'))"
            ).first

            expect(toggle).to_be_visible(timeout=timeout_ms)

            def is_enabled():
                try:
                    knob_rect = toggle.locator("svg rect").nth(2)
                    return (knob_rect.get_attribute("x") or "").strip() == "32"
                except Exception:
                    return False

            if is_enabled():
                return True

            svg = toggle.locator("svg").first
            expect(svg).to_be_visible(timeout=timeout_ms)

            svg.click(force=True)

            self.wait_until(
                lambda: is_enabled(),
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"enable_OTN_auto_path failed. Problem: {e}")

    # ✅
    def disable_OTN_auto_path(self, timeout_ms: int = 10000):
        """
        Disable OTN Auto Path toggle.

        Disabled:
            knob x = 16

        Enabled:
            knob x = 32
        """

        try:
            toggle = self.page.locator(
                "app-slide-toggle[formcontrolname='autoPath'], "
                "app-slide-toggle:has(span:text-is('Auto Path'))"
            ).first

            expect(toggle).to_be_visible(timeout=timeout_ms)

            def is_disabled():
                try:
                    knob_rect = toggle.locator("svg rect").nth(2)
                    return (knob_rect.get_attribute("x") or "").strip() == "16"
                except Exception:
                    return False

            if is_disabled():
                return True

            svg = toggle.locator("svg").first
            expect(svg).to_be_visible(timeout=timeout_ms)

            svg.click(force=True)

            self.wait_until(
                lambda: is_disabled(),
                timeout_ms=timeout_ms,
                interval_ms=200
            )

            sleep(SLEEP)
            return True

        except Exception as e:
            raise AssertionError(f"disable_OTN_auto_path failed. Problem: {e}")