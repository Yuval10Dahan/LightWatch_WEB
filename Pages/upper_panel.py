"""
Created by: Yuval Dahan
Date: 08/02/2026
"""



from playwright.sync_api import Page, expect
from typing import Callable
import time
import re
from time import sleep
from datetime import datetime



class UpperPanel:
    """
    Page Object Model for the upper panel (top navigation bar).
    """

    def __init__(self, page: Page):
        """
        Initialize UpperPanel with Playwright page instance.
        """
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
    # =========================
    # User / Avatar
    # =========================

    # ✅
    def click_on_avatar_icon(self, timeout: int = 8000):
        """
        Click on the user avatar icon to open the user menu.
        """
        try:
            sleep(0.5)
            avatar = self.page.locator("app-avatar .avatar-container").first
            expect(avatar).to_be_visible(timeout=timeout)
            expect(avatar).to_be_enabled(timeout=timeout)

            dropdown_container = self.page.locator("app-avatar div[dropdown]").first

            # If already open, do nothing
            if dropdown_container.count() > 0:
                cls = dropdown_container.get_attribute("class") or ""
                if "open" in cls or "show" in cls:
                    return

            avatar.click(force=True)

            # Wait until dropdown is opened (Angular adds open/show classes)
            self.wait_until(lambda: (dropdown_container.count() > 0 and ("open" in (dropdown_container.get_attribute("class") or "")
                        or "show" in (dropdown_container.get_attribute("class") or ""))), timeout_ms=timeout, interval_ms=150)

        except Exception as e:
            raise AssertionError(f"click_on_avatar_icon failed. Problem: {e}")

    # ✅
    def click_on_change_password(self, timeout: int = 8000):
        """
        Click on the 'Change Password' option from the avatar menu.
        """
        try:
            sleep(0.5)
            # Ensure avatar dropdown is open
            self.click_on_avatar_icon(timeout=timeout)

            menu = self.page.locator("app-avatar ul.dropdown-menu").first
            expect(menu).to_be_visible(timeout=timeout)

            change_pwd = menu.locator("a.dropdown-item", has_text=re.compile(r"^\s*Change Password\s*$", re.IGNORECASE)).first

            expect(change_pwd).to_be_visible(timeout=timeout)
            expect(change_pwd).to_be_enabled(timeout=timeout)
            change_pwd.click(force=True)

            # Wait for navigation / page load
            self.page.wait_for_url(re.compile(r"/user-change-password"), timeout=timeout)

        except Exception as e:
            raise AssertionError(f"click_on_change_password failed. Problem: {e}")

    # ✅
    def get_username(self, timeout: int = 8000) -> str:
        """
        Return the current username shown in the change password form.
        """
        try:
            user_inp = self.page.locator("app-input[formcontrolname='username'] input").first
            expect(user_inp).to_be_visible(timeout=timeout)
            return (user_inp.input_value() or "").strip()
        except Exception as e:
            raise AssertionError(f"get_username failed. Problem: {e}")

    # ❌
    def set_username(self, username: str, timeout: int = 8000):
        """
        Set the username field value.
        """
        try:
            username = (username or "").strip()
            user_inp = self.page.locator("app-input[formcontrolname='username'] input").first
            expect(user_inp).to_be_visible(timeout=timeout)

            # It's disabled in the DOM, so we cannot set it
            if user_inp.is_disabled():
                if username:
                    current = (user_inp.input_value() or "").strip()
                    if current.lower() != username.lower():
                        raise AssertionError(f"Username is read-only. UI shows '{current}', expected '{username}'.")
                return

            # Fallback (in case in other builds it's editable)
            user_inp.fill(username)
            sleep(0.5)
        except Exception as e:
            raise AssertionError(f"set_username('{username}') failed. Problem: {e}")

    # ✅
    def set_current_password(self, password: str, timeout: int = 8000):
        """
        Set the current password field value.
        """
        try:
            inp = self.page.locator("app-input[formcontrolname='currentPassword'] input").first
            expect(inp).to_be_visible(timeout=timeout)
            expect(inp).to_be_enabled(timeout=timeout)
            inp.fill(password or "")

            sleep(0.5)
        except Exception as e:
            raise AssertionError(f"set_current_password failed. Problem: {e}")

    # ✅
    def set_new_password(self, password: str, timeout: int = 8000):
        """
        Set the new password field value.
        """
        try:
            inp = self.page.locator("app-input[formcontrolname='newPassword'] input").first
            expect(inp).to_be_visible(timeout=timeout)
            expect(inp).to_be_enabled(timeout=timeout)
            inp.fill(password or "")

            sleep(0.5)
        except Exception as e:
            raise AssertionError(f"set_new_password failed. Problem: {e}")

    # ✅
    def set_confirm_password(self, password: str, timeout: int = 8000):
        """
        Set the confirm password field value.
        """
        try:
            inp = self.page.locator("app-input[formcontrolname='confirmPassword'] input").first
            expect(inp).to_be_visible(timeout=timeout)
            expect(inp).to_be_enabled(timeout=timeout)
            inp.fill(password or "")

            sleep(0.5)
        except Exception as e:
            raise AssertionError(f"set_confirm_password failed. Problem: {e}")

    # ❌
    def click_save_new_password(self, timeout: int = 12000):
        """
        Click Save to apply the new password.
        """
        try:
            save_btn = self.page.locator("div.user-form footer button.btn.btn-primary.btn-default", has_text=re.compile(r"^\s*Save\s*$", re.IGNORECASE)).first
            expect(save_btn).to_be_visible(timeout=timeout)

            # Wait until form becomes valid -> Save enabled
            self.wait_until(lambda: save_btn.is_enabled(), timeout_ms=timeout, interval_ms=200)

            save_btn.click(force=True)

            # After click: usually a message appears in .user-message (success or error)
            msg = self.page.locator("div.user-form footer div.user-message").first
            # don't hard-fail if message isn't used in some builds, but wait if it exists
            if msg.count() > 0:
                self.wait_until(lambda: (msg.inner_text() or "").strip() != "", timeout_ms=timeout, interval_ms=200)

        except Exception as e:
            raise AssertionError(f"click_save_new_password failed. Problem: {e}")

    # =========================
    # Global Search
    # =========================

    # ✅
    def click_on_global_search(self, timeout: int = 8000):
        """
        Click on the global search icon.
        """
        try:
            sleep(0.5)
            search = self.page.locator("app-global-search").first
            expect(search).to_be_visible(timeout=timeout)

            # The actual interactive element is the input
            search_input = search.locator("input#g-search").first
            expect(search_input).to_be_visible(timeout=timeout)
            expect(search_input).to_be_enabled(timeout=timeout)

            # Click to focus 
            search_input.click(force=True)

            # Verify input is focused
            self.wait_until(lambda: self.page.evaluate("() => document.activeElement?.id") == "g-search", timeout_ms=timeout, interval_ms=150)

        except Exception as e:
            raise AssertionError(f"click_on_global_search failed. Problem: {e}")

    # ✅
    def set_global_search_value(self, value: str, timeout: int = 8000):
        """
        Type a value into the global search input.
        """
        try:
            value = value or ""

            # Ensure search input is open
            self.click_on_global_search(timeout=timeout)

            search_input = self.page.locator("app-global-search input#g-search").first
            expect(search_input).to_be_visible(timeout=timeout)
            expect(search_input).to_be_enabled(timeout=timeout)

            # Clear existing value and type
            search_input.fill("")
            if value:
                search_input.type(value, delay=30)  # small delay helps Angular change detection

            # Wait until the value is reflected in the input
            self.wait_until(lambda: (search_input.input_value() or "") == value, timeout_ms=timeout, interval_ms=150)
            sleep(0.5)

        except Exception as e:
            raise AssertionError(f"set_global_search_value('{value}') failed. Problem: {e}")

    # ✅
    def close_global_search(self, timeout: int = 8000):
        """
        Close the global search input using the close icon.
        """
        try:
            container = self.page.locator("app-global-search").first
            expect(container).to_be_visible(timeout=timeout)

            search_input = container.locator("input#g-search").first
            expect(search_input).to_be_visible(timeout=timeout)

            # Preferred: click the close (X) icon if present
            close_icon = container.locator("app-icon[name='close-square']").first
            if close_icon.count() > 0 and close_icon.is_visible():
                close_icon.click(force=True)

                # Wait until input is cleared OR loses focus
                self.wait_until(
                    lambda: (
                        (search_input.input_value() or "") == ""
                        or self.page.evaluate(
                            "() => !document.activeElement || document.activeElement.id !== 'g-search'"
                        )
                    ),
                    timeout_ms=timeout,
                    interval_ms=150,
                )
                return

            # Fallback: ESC key
            self.page.keyboard.press("Escape")

            self.wait_until(lambda: self.page.evaluate("() => !document.activeElement || document.activeElement.id !== 'g-search'"), timeout_ms=timeout, interval_ms=150)

        except Exception as e:
            raise AssertionError(f"close_global_search failed. Problem: {e}")

    # =========================
    # Sub-domain / Domain
    # =========================

    # ❌
    def click_on_sub_domains_dropdown(self):
        """
        Open the sub-domains dropdown.
        """
        pass

    # ❌
    def select_sub_domain(self, sub_domain: str):
        """
        Select a sub-domain from the dropdown.
        """
        pass

    # ✅
    def click_on_domains_dropdown(self, timeout: int = 8000):
        """
        Open the domains dropdown in the upper panel.
        """
        try:
            sleep(0.5)  
            dd = self.page.locator("app-header-dropdown.domain[root='Domains']").first
            expect(dd).to_be_visible(timeout=timeout)

            btn = dd.locator("button.header-dropdown-button").first
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)

            menu = dd.locator("div.dropdown-menu.header-dropdown-menu").first

            # If already open/visible --> do nothing
            if menu.count() > 0 and menu.is_visible():
                return

            btn.click(force=True)

            # Wait until menu is visible (opened)
            self.wait_until(lambda: menu.count() > 0 and menu.is_visible(), timeout_ms=timeout, interval_ms=150)

        except Exception as e:
            raise AssertionError(f"click_on_domains_dropdown failed. Problem: {e}")

    # ✅
    def select_domain(self, domain: str, timeout: int = 8000):
        """
        Select a domain from the Domains dropdown.
        """
        try:
            domain = (domain or "").strip()
            if not domain:
                raise ValueError("domain is empty")

            # Open dropdown 
            self.click_on_domains_dropdown(timeout=timeout)

            dd = self.page.locator("app-header-dropdown.domain[root='Domains']").first
            expect(dd).to_be_visible(timeout=timeout)

            menu = dd.locator("div.dropdown-menu.header-dropdown-menu").first
            expect(menu).to_be_visible(timeout=timeout)

            tree = menu.locator("app-inventory-tree").first
            expect(tree).to_be_visible(timeout=timeout)

            # Click the domain row by its visible text 
            row = tree.locator("div.inventory-tree-level-title[type='DOMAIN'] span", has_text=re.compile(rf"^\s*{re.escape(domain)}\s*$", re.IGNORECASE),).first

            if row.count() == 0:
                available = [t.strip() for t in tree.locator("div.inventory-tree-level-title[type='DOMAIN'] span").all_inner_texts()]
                raise AssertionError(f"Domain '{domain}' not found. Available: {available}")

            row.scroll_into_view_if_needed()
            expect(row).to_be_visible(timeout=timeout)
            row.click(force=True)

            # Wait until button text updates
            btn_span = dd.locator("button.header-dropdown-button span").first
            expect(btn_span).to_be_visible(timeout=timeout)

            expected_rx = re.compile(rf"^\s*{re.escape(domain)}\s*$", re.IGNORECASE)

            self.wait_until(lambda: expected_rx.search((btn_span.inner_text() or "").strip()) is not None, timeout_ms=timeout, interval_ms=150)

            # Optional: close dropdown (ESC).
            try:
                self.page.keyboard.press("Escape")
            except Exception:
                pass

        except Exception as e:
            raise AssertionError(f"select_domain('{domain}') failed. Problem: {e}")