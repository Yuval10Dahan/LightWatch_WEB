"""
Created by: Yuval Dahan
Date: 28/01/2026
"""

import re
import time
from typing import Callable

from playwright.sync_api import Page


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
        return self.modal().locator("button.btn.btn-primary", has_text=re.compile(rf"^\s*{re.escape(name)}\s*$")).first

    # ✅
    def exit_btn(self):
        """
        Return the Exit button in the modal.
        """
        return self.modal().locator("button.btn.btn-stroke", has_text=re.compile(r"^\s*Exit\s*$")).first

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