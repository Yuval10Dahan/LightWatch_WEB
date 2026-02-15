"""
Created by: Yuval Dahan
Date: 29/01/2026
"""

from __future__ import annotations
import re
import time
import random
from typing import Callable, Optional, Any
from playwright.sync_api import Page, expect
from time import sleep
from Utils.utils import refresh_page


class DomainManagement:
    """
    Domain Management page – handles domain creation, removal,
    renaming, chassis ID changes, and device/domain assignments.
    """

    def __init__(self, page: Page):
        self.page = page

    # ==========================================================
    # Generic helpers
    # ==========================================================

    # ✅
    def wait_until_old(self, condition: Callable[[], bool], timeout_ms: int = 10_000, interval_ms: int = 200):
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
    def wait_until(self, condition: Callable[[], bool], timeout_ms: int = 10_000, interval_ms: int = 200, *, desc: str = "condition",
        allow_exceptions: tuple[type[BaseException], ...] = (Exception,), stable_successes: int = 1, on_timeout: Optional[Callable[[], Any]] = None):
        """
        Polls condition() until it returns True or timeout.
        Raises AssertionError on timeout.
        """
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be > 0")
        if interval_ms <= 0:
            raise ValueError("interval_ms must be > 0")
        if stable_successes <= 0:
            raise ValueError("stable_successes must be >= 1")

        start = time.perf_counter()
        deadline = start + (timeout_ms / 1000.0)

        attempts = 0
        last_exc: Optional[BaseException] = None
        consecutive = 0

        while True:
            now = time.perf_counter()
            if now >= deadline:
                break

            attempts += 1
            try:
                ok = bool(condition())
                last_exc = None
                if ok:
                    consecutive += 1
                    if consecutive >= stable_successes:
                        return
                else:
                    consecutive = 0

            except allow_exceptions as e:
                # retryable exception: keep polling
                last_exc = e
                consecutive = 0

            # sleep with jitter, but never past deadline
            remaining_s = max(0.0, deadline - time.perf_counter())
            base_sleep_s = interval_ms / 1000.0
            jitter_s = random.uniform(0.0, min(0.05, base_sleep_s * 0.25))  # up to 50ms or 25%
            sleep_s = min(remaining_s, base_sleep_s + jitter_s)

            if sleep_s <= 0:
                break
            time.sleep(sleep_s)

        # Collect extra debug on timeout (optional)
        extra = ""
        if on_timeout:
            try:
                val = on_timeout()
                if val is not None:
                    extra = f"\nExtra debug: {val}"
            except Exception as e:
                extra = f"\nExtra debug failed: {e}"

        elapsed_ms = int((time.perf_counter() - start) * 1000)

        if last_exc:
            raise AssertionError(
                f"wait_until timeout after {elapsed_ms}ms waiting for {desc}. "
                f"Attempts={attempts}. Last error: {type(last_exc).__name__}: {last_exc}"
                f"{extra}"
            )
        raise AssertionError(f"wait_until timeout after {elapsed_ms}ms waiting for {desc}. Attempts={attempts}.{extra}")

    # ✅
    def root(self):
        """
        Return the main Domain Management page container.
        """
        return self.page.locator("app-device-management, section.domain-management-container").first

    # ✅
    def tree_container(self):
        """
        Return the inventory tree container element.
        """
        return self.page.locator("section.domain-management-container app-inventory-tree").first

    # ✅
    def tree_by_title(self, title: str):
        """
        Return the inventory tree with the given title.
        """
        return self.page.locator("section.domain-management-container app-inventory-tree").filter(has=self.page.locator("h3", has_text=re.compile(rf"^\s*{re.escape(title)}\s*$"))).first

    # ✅
    def from_tree(self):
        """
        Return the 'From' inventory tree.
        """
        return self.tree_by_title("From")

    # ✅
    def to_tree(self):
        """
        Return the 'To' inventory tree.
        """
        return self.tree_by_title("To")

    # ✅
    def bottom_actions(self):
        """
        Return the bottom action buttons container('Add domain', 'Remove', 'Rename', 'Change Chassis ID', 'Move to domain').
        """
        return self.page.locator("section.domain-management-bottom-actions").first

    # ✅
    def action_btn(self, text: str):
        """
        Return a bottom action button by its visible text.
        """
        bottom_action_button = self.bottom_actions().locator("button.btn", has_text=re.compile(rf"^\s*{re.escape(text)}\s*$")).first
        sleep(1)

        return bottom_action_button

    # ✅
    def nav_text_regex(self, element_name: str) -> re.Pattern:
        """
        Create a flexible regex to match tree item names despite spacing or symbol differences.
        """
        s = element_name.strip()

        esc = re.escape(s)

        # Allow spaces around slashes: "DC-14/14" == "DC-14 / 14"
        esc = esc.replace(r"\/", r"\s*/\s*")

        # Treat '-' and '–' as equivalent in UI text
        esc = esc.replace(r"\-", r"[-–]")

        # Collapse any escaped spaces into flexible whitespace
        esc = esc.replace(r"\ ", r"\s+")

        return re.compile(esc)

    # ✅
    def row_locator(self, name: str, tree_title: str = "From"):
        """
        Locate a tree row by name inside the specified tree.
        """
        rx = self.nav_text_regex(name)
        tree = self.from_tree() if tree_title == "From" else self.to_tree()
        row_locator = tree.locator("div.inventory-tree-level-title", has_text=rx).first
        sleep(0.5)

        return row_locator

    # ✅
    def select_row_old(self, name: str, tree_title: str = "From", timeout: int = 5000):
        """
        Click a tree row.
        """
        row = self.row_locator(name, tree_title=tree_title)

        expect(row).to_be_visible(timeout=timeout)
        row.scroll_into_view_if_needed()
        row.click(force=True)

        expect(row).to_have_class(re.compile(r"\bcurrent\b"), timeout=timeout)

    # ✅
    def select_row_old2(self, name: str, tree_title: str = "From", timeout: int = 5000):
        """
        Click a tree row.
        """
        row = self.row_locator(name, tree_title=tree_title)
        self.click_row_and_wait_actions_enabled(row, timeout=timeout)

    # ✅
    def select_row(self, name: str, tree_title: str = "From", timeout: int = 5000):
        """
        Click a tree row.
        """
        row = self.row_locator(name, tree_title=tree_title)
        self.click_row_and_wait(row, timeout=timeout, wait_for="any_action", desc=f"any action enabled after selecting '{name}'")

    # ✅
    def domain_row_locator(self, name: str, tree_title: str = "From"):
        """
        Locate a DOMAIN-type row (used to enable Add domain).
        """
        rx = self.nav_text_regex(name)
        tree = self.from_tree() if tree_title == "From" else self.to_tree()
        row_locator = tree.locator("div.inventory-tree-level-title[type='DOMAIN']", has_text=rx).first
        sleep(0.5)

        return row_locator 

    # ✅
    def chassis_row_locator(self, name: str, tree_title: str = "From"):
        """
        Locate a CHASSIS-type row by name inside the specified tree.
        """
        rx = self.nav_text_regex(name)
        tree = self.from_tree() if tree_title == "From" else self.to_tree()

        row = tree.locator("div.inventory-tree-level-title[type='CHASSIS']", has_text=rx).first
        sleep(0.5)

        if row.count() > 0:
            return row

        # Fallback (in case some builds don't expose type='CHASSIS' consistently)
        return tree.locator("div.inventory-tree-level-title", has_text=rx).first

    # ✅
    def device_row_locator(self, device_name_or_ip: str, tree_title: str = "From"):
        """
        Locate a device row by "NAME (IP)" OR by IP only.
        Supports types: ROADM / TRANSPONDER / MUXPONDER.
        """
        target = (device_name_or_ip or "").strip()
        if not target:
            raise ValueError("device_name_or_ip is empty")

        tree = self.from_tree() if tree_title == "From" else self.to_tree()
        device_types = ("ROADM", "TRANSPONDER", "MUXPONDER")

        # If user passed only IP -> match "(IP)"
        is_ip_only = re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", target) is not None
        if is_ip_only:
            rx = re.compile(rf"\(\s*{re.escape(target)}\s*\)")
        else:
            # Prefer your flexible matcher for "NAME (IP)"
            rx = self.nav_text_regex(target)

        rows = tree.locator(", ".join([f"div.inventory-tree-level-title[type='{t}']" for t in device_types]))
        sleep(0.5)

        return rows.filter(has_text=rx).first

    # ✅
    def select_domain_row_old(self, name: str, tree_title: str = "From", timeout: int = 5000):
        """
        Select a DOMAIN row.
        """
        row = self.domain_row_locator(name, tree_title=tree_title)

        expect(row).to_be_visible(timeout=timeout)
        row.scroll_into_view_if_needed()
        row.click(force=True)

        expect(row).to_have_class(re.compile(r"\bcurrent\b"), timeout=timeout)

    # ✅
    def select_domain_row_old2(self, name: str, tree_title: str = "From", timeout: int = 5000):
        """
        Select a DOMAIN row.
        """
        row = self.domain_row_locator(name, tree_title=tree_title)
        self.click_row_and_wait_single_action_enabled(row, action_text="Add domain", timeout=timeout)

    # ✅
    def select_domain_row(self, name: str, tree_title: str = "From", timeout: int = 5000):
        """
        Select a DOMAIN row.
        """
        row = self.domain_row_locator(name, tree_title=tree_title)
        self.click_row_and_wait(row, timeout=timeout, wait_for="action", action_text="Add domain")

    # ✅
    def select_chassis_row_old(self, name: str, tree_title: str = "From", timeout: int = 5000):
        """
        Select a CHASSIS row.
        """
        row = self.chassis_row_locator(name, tree_title=tree_title)
        sleep(1)
        expect(row).to_be_visible(timeout=timeout)
        row.scroll_into_view_if_needed()
        row.click(force=True)
        expect(row).to_have_class(re.compile(r"\bcurrent\b"), timeout=timeout)

    # ✅
    def select_chassis_row(self, name: str, tree_title: str = "From", timeout: int = 5000):
        """
        Select a CHASSIS row.
        """
        row = self.chassis_row_locator(name, tree_title=tree_title)
        self.click_row_and_wait_actions_enabled(row, timeout=timeout)

    # ✅
    def select_device_row_old(self, device_name_or_ip: str, tree_title: str = "From", timeout: int = 5000):
        """
        Select a device row in the tree.
        """
        row = self.device_row_locator(device_name_or_ip, tree_title=tree_title)
        expect(row).to_be_visible(timeout=timeout)
        row.scroll_into_view_if_needed()
        row.click(force=True)
        expect(row).to_have_class(re.compile(r"\bcurrent\b"), timeout=timeout)

    # ✅
    def select_device_row(self, device_name_or_ip: str, tree_title: str = "From", timeout: int = 5000):
        """
        Select a device row in the tree.
        """
        row = self.device_row_locator(device_name_or_ip, tree_title=tree_title)
        self.click_row_and_wait_actions_enabled(row, timeout=timeout)

    # ✅
    def expand_element(self, element_name: str, tree_title: str = "From", timeout: int = 5000) -> bool:
        """
        Expand a tree element (domain/chassis/etc.).
        """
        try:
            row = self.row_locator(element_name, tree_title=tree_title)
            if row.count() == 0:
                raise AssertionError(f"expand_element('{element_name}') failed: element not found in '{tree_title}' tree.")

            expect(row).to_be_visible(timeout=timeout)
            row.scroll_into_view_if_needed()
 
            arrow_down = row.locator("app-icon[name='arrow-down']").first
            arrow_up = row.locator("app-icon[name='arrow-up']").first

            # If arrow-up is visible, it's already expanded
            try:
                if arrow_up.count() > 0 and arrow_up.is_visible():
                    return False
            except Exception:
                pass

            # If arrow-down exists & visible -> expand
            if arrow_down.count() > 0:
                expect(arrow_down).to_be_visible(timeout=timeout)
                arrow_down.click(force=True)

                # Wait until it becomes expanded 
                def expanded() -> bool:
                    try:
                        if arrow_up.count() > 0 and arrow_up.is_visible():
                            return True
                        if arrow_down.count() > 0 and not arrow_down.is_visible():
                            return True
                        return False
                    except Exception:
                        return False

                self.wait_until(expanded, timeout_ms=timeout, interval_ms=150)
                return True

            # No expander found for that row (leaf node)
            return False

        except Exception as e:
            raise AssertionError(f"expand_element('{element_name}') failed. Problem: {e}")

    # ✅
    def click_button_and_validate_toast(self, success_text: str, failure_label: str, timeout: int = 8000) -> bool:
        """
        Wait for a success toast or failure modal and validate the action result.
        """
        try:
            toast = self.page.locator("div", has_text=re.compile(rf"\b{re.escape(success_text)}\b", re.IGNORECASE)).first

            # Modals you already implemented
            msg_modal = self.message_modal()
            warn_modal = self.warning_remove_modal()

            def toast_visible() -> bool:
                try:
                    return toast.count() > 0 and toast.is_visible()
                except Exception:
                    return False

            def message_visible() -> bool:
                try:
                    return msg_modal.count() > 0 and msg_modal.is_visible()
                except Exception:
                    return False

            def warning_visible() -> bool:
                try:
                    return warn_modal.count() > 0 and warn_modal.is_visible()
                except Exception:
                    return False

            # Wait until either toast appears OR a modal appears
            self.wait_until(lambda: toast_visible() or message_visible() or warning_visible(),
                            timeout_ms=timeout, interval_ms=150)

            # If Message modal popped -> click Ok and fail with the message text
            if message_visible():
                msg = self.message_text()
                expect(msg).to_be_visible(timeout=timeout)
                msg_text = msg.inner_text().strip()

                ok = self.message_ok_btn()
                expect(ok).to_be_visible(timeout=timeout)
                ok.click()

                raise AssertionError(f"{failure_label} failed (Message modal): {msg_text}")

            # If Warning modal popped -> this helper does NOT auto-confirm (caller should decide)
            if warning_visible():
                # Let caller handle Yes/No flows explicitly
                raise AssertionError(f"{failure_label} blocked (Warning modal appeared). Handle confirmation in the caller.")

            # Toast appeared -> wait it disappears
            expect(toast).to_be_visible(timeout=timeout)
            expect(toast).to_be_hidden(timeout=timeout)

            return True

        except Exception as e:
            raise AssertionError(f"{failure_label} failed. Problem: {e}")
    
    # ✅
    def normalize_chassis_name(self, x: str) -> str:
        """
        Normalize a chassis name to its base format.

        Supported inputs:
        -----------------
        1) 'STRING-NUMBER/NUMBER'  -> 'STRING-NUMBER'
        Example: 'BS-12/12'      -> 'BS-12'

        2) 'STRING-NUMBER'         -> unchanged
        Example: 'BS-12'         -> 'BS-12'

        3) 'STRING: NUMBER/NUMBER' -> 'STRING: NUMBER'
        Example: 'Chassis: 8/8'  -> 'Chassis: 8'

        4) 'STRING: NUMBER'        -> unchanged
        Example: 'Chassis: 8'    -> 'Chassis: 8'

        Any other format raises ValueError.
        """
        if not isinstance(x, str):
            raise ValueError(f"Expected string, got {type(x).__name__}")

        value = x.strip()

        # Case 1: STRING-NUMBER/NUMBER
        m = re.fullmatch(r"(.+?-\d+)\s*/\s*\d+", value)
        if m:
            return m.group(1)

        # Case 2: STRING-NUMBER
        if re.fullmatch(r".+?-\d+", value):
            return value

        # Case 3: STRING: NUMBER/NUMBER
        m = re.fullmatch(r"(.+?:\s*\d+)\s*/\s*\d+", value)
        if m:
            return m.group(1)

        # Case 4: STRING: NUMBER
        if re.fullmatch(r".+?:\s*\d+", value):
            return value

        raise ValueError(
            f"normalize_chassis_name: "
            f"Unknown chassis format: '{x}'. "
            f"Expected 'STRING-NUMBER', 'STRING-NUMBER/NUMBER', "
            f"'STRING: NUMBER', or 'STRING: NUMBER/NUMBER'."
        )

    # ✅
    def expand_chassis_and_click_on_device(self, device_id: str, parent_chassis: str | None = None, timeout: int = 8000):
        """
        Expand Chassis and click on the desired device.
        """
        try:
            sleep(1)
            target = (device_id or "").strip()
            if not target:
                raise ValueError("chassis_id is empty")

            tree = self.from_tree()

            device_types = ("ROADM", "TRANSPONDER", "MUXPONDER")

            is_ip_only = re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", target) is not None
            if is_ip_only:
                dev_rx = re.compile(rf"\(\s*{re.escape(target)}\s*\)")
            else:
                if re.search(r"\(\s*\d{1,3}(?:\.\d{1,3}){3}\s*\)", target) is None:
                    raise AssertionError(f"'{target}' does not look like a device row. Use 'NAME (IP)' or IP only.")
                dev_rx = self.nav_text_regex(target)

            # Default: search whole tree (domain case where devices already visible)
            search_root = tree

            # If parent_chassis is provided: expand it and scope search to it
            if parent_chassis:
                parent = (parent_chassis or "").strip()
                if not parent:
                    raise ValueError("parent_chassis is empty")

                parent_rx = self.nav_text_regex(parent)
                sleep(0.5)

                parent_row = tree.locator("div.inventory-tree-level-title[type='CHASSIS']").filter(has_text=parent_rx).first
                sleep(0.5)

                if parent_row.count() == 0:
                    # fallback: if in some builds it isn't typed as CHASSIS
                    parent_row = tree.locator("div.inventory-tree-level-title").filter(has_text=parent_rx).first
                    sleep(0.5)

                if parent_row.count() == 0:
                    raise AssertionError(f"parent_chassis '{parent}' not found in 'From' tree.")

                parent_row.scroll_into_view_if_needed()
                expect(parent_row).to_be_visible(timeout=timeout)

                # Expand chassis if needed 
                self.expand_tree_node_if_collapsed(parent_row, timeout=timeout)

                # Scope future device lookup ONLY inside this chassis subtree
                search_root = parent_row.locator("xpath=ancestor::app-inventory-tree-level[1]")
                sleep(0.5)

            device_rows = search_root.locator(", ".join([f"div.inventory-tree-level-title[type='{t}']" for t in device_types]))
            sleep(0.5)
            row = device_rows.filter(has_text=dev_rx).first

            if row.count() == 0:
                raise AssertionError(
                    f"Device '{target}' was not found."
                    + (f" (under parent_chassis='{parent_chassis}')" if parent_chassis else
                    " If it is under a collapsed 'Chassis: X/X', pass parent_chassis.")
                )

            # Click device -> enable button
            row.scroll_into_view_if_needed()
            expect(row).to_be_visible(timeout=timeout)
            row.click(force=True)
    
        except Exception as e:
            raise AssertionError(f"expand_chassis_and_click_on_device('{device_id}' failed. Problem: {e}")

    # ✅
    def click_row_and_wait_actions_enabled(self, row, timeout: int = 8000):
        """
        Click a row and wait until bottom actions react (button enabled).
        """
        expect(row).to_be_visible(timeout=timeout)
        row.scroll_into_view_if_needed()
        row.click(force=True)

        rm = self.action_btn("Remove")
        self.wait_until(lambda: rm.count() > 0 and rm.is_visible() and rm.is_enabled(), timeout_ms=timeout, interval_ms=150)

    # ✅
    def click_row_and_wait_single_action_enabled(self, row, action_text: str, timeout: int = 8000):
        """
        Click a row and wait until a specific bottom action becomes enabled.
        """
        expect(row).to_be_visible(timeout=timeout)
        row.scroll_into_view_if_needed()
        row.click(force=True)

        btn = self.action_btn(action_text)
        self.wait_until(lambda: btn.count() > 0 and btn.is_visible() and btn.is_enabled(), timeout_ms=timeout, interval_ms=150)

    # ✅
    def click_row_and_wait(self, row, timeout: int = 8000, *, wait_for: str = "any_action", action_text: str | None = None, 
                           tree_title: str | None = None, desc: str = "UI reaction after row click"):
        """
        Click a row and wait for a specified UI reaction.

        wait_for:
        - "any_action"      -> any bottom action button becomes enabled
        - "action"          -> a specific bottom action button text becomes enabled (action_text required)
        - "middle_arrow"    -> middle move arrow becomes enabled (Move to domain mode)
        - "none"            -> just click (no waiting)
        """
        expect(row).to_be_visible(timeout=timeout)
        row.scroll_into_view_if_needed()
        row.click(force=True)

        if wait_for == "none":
            return

        if wait_for == "action":
            if not action_text:
                raise ValueError("action_text is required when wait_for='action'")
            btn = self.action_btn(action_text)
            self.wait_until(lambda: btn.count() > 0 and btn.is_visible() and btn.is_enabled(), timeout_ms=timeout, interval_ms=150, 
                            desc=f"bottom action '{action_text}' enabled")
            return

        if wait_for == "middle_arrow":
            arrow = self.middle_move_arrow_btn()
            self.wait_until(lambda: arrow.count() > 0 and arrow.is_visible() and arrow.is_enabled(), timeout_ms=timeout, interval_ms=150,
                desc="middle arrow enabled")
            return

        if wait_for == "any_action":
            # any enabled bottom action button
            buttons = self.bottom_actions().locator("button.btn")
            def any_enabled() -> bool:
                try:
                    n = buttons.count()
                    for i in range(n):
                        b = buttons.nth(i)
                        if b.is_visible() and b.is_enabled():
                            return True
                    return False
                except Exception:
                    return False

            self.wait_until(any_enabled, timeout_ms=timeout, interval_ms=150, desc=desc)
            return

        raise ValueError(f"Unknown wait_for='{wait_for}'")


    # ==========================================================
    # Modal handling
    # ==========================================================

    # ✅
    def modal(self):
        """
        Return the currently visible modal dialog.
        """
        return self.page.locator("div.modal-dialog.pl-modal:visible, div.modal-dialog:visible").first

    # ✅
    def modal_title(self):
        """
        Return the title element of the active modal.
        """
        return self.modal().locator(".domain-management-modal-header .title, .title").first

    # ✅
    def modal_close_x(self):
        """
        Return the close (X) button of the modal.
        """
        return self.modal().locator("app-icon[name='close-square'], .domain-management-modal-header app-icon").first

    # ✅
    def modal_button(self, text: str):
        """
        Return a modal button by its text.
        """
        return self.modal().locator("button", has_text=re.compile(rf"^\s*{re.escape(text)}\s*$")).first

    # ✅
    def modal_ok_button(self):
        """
        Return the 'Ok' button in a modal.
        """
        return self.modal_button("Ok")

    # ✅
    def modal_yes_button(self):
        """
        Return the 'Yes' button in a modal.
        """
        return self.modal_button("Yes")

    # ✅
    def modal_no_button(self):
        """
        Return the 'No' button in a modal.
        """
        return self.modal_button("No")

    # ==========================================================
    # Add domain
    # ==========================================================

    # ✅
    def add_domain_modal(self):
        """
        Return the 'Add new domain' modal window.
        """
        return (self.page.locator("div.modal-dialog.pl-modal")
            .filter(has=self.page.locator("div.domain-management-modal-header div.title", has_text=re.compile(r"^\s*Add new domain\s*$"))).first)

    # ✅
    def add_domain_name_input(self):
        """
        Return the domain name input field in the Add Domain modal window.
        """
        return self.add_domain_modal().locator("app-input[formcontrolname='name'] input[type='text']").first

    # ✅
    def add_domain_description_input(self):
        """
        Return the domain description input field in the Add Domain modal window.
        """
        modal = self.add_domain_modal()
        ta = modal.locator("app-input[formcontrolname='description'] textarea").first
        if ta.count() > 0:
            return ta
        return modal.locator("app-input[formcontrolname='description'] input").first

    # ✅
    def add_domain_confirm_btn(self):
        """
        Return the 'Add' button in the Add Domain modal window.
        """
        return self.add_domain_modal().locator("section.form-actions button.btn.btn-primary", has_text="Add").first

    # ✅
    def add_domain_close_btn(self):
        """
        Return the close (X) button of the Add Domain modal window.
        """
        return self.add_domain_modal().locator("div.domain-management-modal-header app-icon[name='close-square']").first

    # ✅
    def add_domain_error_page(self):
        """
        Return the full-page error component shown when add-domain fails.
        """
        return self.page.locator("app-error").first

    # ✅
    def add_domain_error_title(self):
        """
        Return the error page title text (h1).
        """
        return self.add_domain_error_page().locator("h1").first

    # ✅
    def add_domain_error_go_back_btn(self):
        """
        Return the 'Go to Back' button on the error page.
        """
        return self.add_domain_error_page().locator("button.btn", has_text=re.compile(r"^\s*Go to Back\s*$")).first

    # ✅
    def is_add_domain_error_page_visible(self) -> bool:
        """
        True if the add-domain error page is currently displayed.
        """
        try:
            p = self.add_domain_error_page()
            return p.count() > 0 and p.is_visible()
        except Exception:
            return False

    # ✅
    def handle_add_domain_error_page(self, timeout: int = 5000) -> bool:
        """
        If the add-domain error page appears, click 'Go to Back'.
        """
        try:
            if not self.is_add_domain_error_page_visible():
                return

            title = self.add_domain_error_title()
            expect(title).to_be_visible(timeout=timeout)
            title_text = title.inner_text().strip()

            btn = self.add_domain_error_go_back_btn()
            expect(btn).to_be_visible(timeout=timeout)
            btn.click(force=True)

            # Wait until error page is gone (back to Domain Management)
            self.wait_until(lambda: not self.is_add_domain_error_page_visible(), timeout_ms=timeout, interval_ms=200)
            return True

        except Exception as e:
            print(f"handle_add_domain_error_page failed. Problem: {title_text}")
            return False

    # ✅
    def click_add_domain(self, parent_domain_name: str = "Inventory", timeout: int = 5000):
        """
        Select a parent domain and open the Add Domain modal window.
        """
        try:
            # Ensure a DOMAIN row is selected so the button becomes enabled
            self.select_domain_row(parent_domain_name, tree_title="From", timeout=timeout)
            sleep(0.25)

            # Now the button should be enabled
            btn = self.action_btn("Add domain")
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()

            # Modal window opened
            modal = self.add_domain_modal()
            sleep(0.25)
            expect(modal).to_be_visible(timeout=timeout)

        except Exception as e:
            raise AssertionError(f"click_add_domain failed. Problem: {e}")

    # ✅
    def submit_add_domain(self, domain_name: str, domain_description: str = "", timeout: int = 5000):
        """
        Submit the Add Domain modal and verify the domain was created.
        """
        try:
            modal = self.add_domain_modal()
            sleep(0.25)
            expect(modal).to_be_visible(timeout=timeout)

            # Fill name (required)
            name_inp = self.add_domain_name_input()
            expect(name_inp).to_be_visible(timeout=timeout)
            name_inp.fill(domain_name)

            # Fill description (optional)
            if domain_description:
                desc_inp = self.add_domain_description_input()
                expect(desc_inp).to_be_visible(timeout=timeout)
                desc_inp.fill(domain_description)

            # Confirm
            add_btn = self.add_domain_confirm_btn()
            expect(add_btn).to_be_visible(timeout=timeout)
            expect(add_btn).to_be_enabled(timeout=timeout)
            sleep(5)
            add_btn.click()
            sleep(0.25)

            # --- Wait for either success toast OR server error banner behind the modal ---
            toast = self.page.locator("div", has_text=re.compile(r"\bAdd domain\b", re.IGNORECASE)).first
            sleep(0.25)
            error_h1 = self.page.locator("app-error h1", has_text=re.compile(r"^\s*Some problems with adding Domain\s*$", re.IGNORECASE)).first
            sleep(0.25)

            def toast_visible() -> bool:
                try:
                    return toast.count() > 0 and toast.is_visible()
                except Exception:
                    return False

            def error_visible() -> bool:
                try:
                    return error_h1.count() > 0 and error_h1.is_visible()
                except Exception:
                    return False

            # self.wait_until(lambda: toast_visible() or error_visible(), timeout_ms=timeout, interval_ms=150)

            # If server error appeared -> close modal and raise
            if error_visible():
                close_btn = self.add_domain_close_btn()
                expect(close_btn).to_be_visible(timeout=timeout)
                close_btn.click(force=True)

                # Ensure modal closed so test can continue cleanly
                expect(self.add_domain_modal()).to_be_hidden(timeout=timeout)

                if self.handle_add_domain_error_page(timeout=timeout):
                    raise AssertionError(f"add_domain('{domain_name}') failed: likely domain already exists")
                else:
                    exit(1)

            # Otherwise: success toast flow
            # self.click_button_and_validate_toast(success_text="Add domain", failure_label=f"add_domain('{domain_name}')", timeout=timeout)

            # Assert domain appears in tree
            self.wait_until(lambda: self.row_locator(domain_name).count() > 0, timeout_ms=timeout, interval_ms=200)
            expect(self.row_locator(domain_name)).to_be_visible(timeout=timeout)

        except Exception as e:
            raise AssertionError(f"submit_add_domain('{domain_name}') failed. Problem: {e}")

    # ✅
    def add_domain(self, domain_name: str, domain_description: str = "", parent_domain_name: str = "Inventory", timeout: int = 5000):
        """
        Full flow to create a new domain under a parent domain.
        """
        self.click_add_domain(parent_domain_name=parent_domain_name, timeout=timeout)
        self.submit_add_domain(domain_name, domain_description, timeout=timeout)
        sleep(10)

    # ==========================================================
    # Remove domain
    # ==========================================================
    
    # ✅
    def warning_remove_modal(self):
        """
        Return the Warning modal window shown before domain deletion.
        """
        warning_remove_modal = (self.page.locator("div.modal-dialog.pl-modal")
            .filter(has=self.page.locator("div.domain-management-modal-header div.title", has_text=re.compile(r"^\s*Warning\s*$"))).first)
        sleep(0.5)

        return warning_remove_modal

    # ✅
    def warning_yes_btn(self):
        """
        Return the 'Yes' button in the Warning modal window.
        """
        return self.warning_remove_modal().locator("section.form-actions button.btn.btn-primary", has_text="Yes").first

    # ✅
    def warning_no_btn(self):
        """
        Return the 'No' button in the Warning modal window.
        """
        return self.warning_remove_modal().locator("section.form-actions button.btn", has_text="No").first

    # ✅
    def message_modal(self):
        """
        Return the message modal displayed when some elements cannot be deleted.
        """
        return (self.page.locator("div.modal-dialog.pl-modal")
            .filter(has=self.page.locator("div.domain-management-modal-header div.title", has_text=re.compile(r"^\s*Message\s*$"))).first)

    # ✅
    def message_text(self):
        """
        Return the text content of the Message modal window.
        """
        return self.message_modal().locator("div.domain-management-modal-content article").first

    # ✅
    def message_ok_btn(self):
        """
        Return the 'Ok' button in the Message modal window.
        """
        return self.message_modal().locator("section.form-actions button.btn.btn-primary", has_text="Ok").first

    # ✅
    def click_remove_domain_btn(self, domain_name: str, timeout: int = 5000):
        """
        Select a domain and click the Remove button.
        """
        # Validate domain exists
        row = self.row_locator(domain_name, tree_title="From")
        if row.count() == 0:
            raise AssertionError(f"remove_domain('{domain_name}') failed: element not found in tree.")

        # Select domain
        self.select_row(domain_name, tree_title="From", timeout=timeout)

        # Click Remove
        rm = self.action_btn("Remove")
        expect(rm).to_be_visible(timeout=timeout)
        expect(rm).to_be_enabled(timeout=timeout)
        rm.click()

    # ✅
    def click_remove_chassis_btn(self, chassis_name: str, timeout: int = 5000):
        """
        Select a chassis and click the Remove button.
        """
        row = self.chassis_row_locator(chassis_name, tree_title="From")
        sleep(1)

        if row.count() == 0:
            raise AssertionError(f"remove_chassis('{chassis_name}') failed: chassis not found in tree.")

        self.select_chassis_row(chassis_name, tree_title="From", timeout=timeout)

        rm = self.action_btn("Remove")
        expect(rm).to_be_visible(timeout=timeout)
        expect(rm).to_be_enabled(timeout=timeout)
        rm.click()

    # ✅
    def click_remove_device_btn(self, device_name_or_ip: str, timeout: int = 5000):
        """
        Select a device and click the Remove button.
        """
        row = self.device_row_locator(device_name_or_ip, tree_title="From")
        if row.count() == 0:
            raise AssertionError(f"remove_device('{device_name_or_ip}') failed: device not found in tree.")

        self.select_device_row(device_name_or_ip, tree_title="From", timeout=timeout)

        rm = self.action_btn("Remove")
        expect(rm).to_be_visible(timeout=timeout)
        expect(rm).to_be_enabled(timeout=timeout)
        rm.click()

    # ✅
    def remove_domain(self, domain_name: str, timeout: int = 5000):
        """
        Delete a domain.
        """
        try:
            refresh_page(self.page)

            # Click Remove 
            self.click_remove_domain_btn(domain_name, timeout=timeout)

            # Warning modal must appear
            warn = self.warning_remove_modal()
            expect(warn).to_be_visible(timeout=timeout)

            # Optional validation of warning text
            try:
                article = warn.locator("article").first
                if article.count() > 0:
                    text = article.inner_text().lower()
                    if "will be deleted" not in text:
                        raise AssertionError(f"Unexpected Warning text: {text}")
            except Exception:
                pass  # keep flow robust to minor UI text changes

            # Confirm deletion
            yes = self.warning_yes_btn()
            expect(yes).to_be_visible(timeout=timeout)
            expect(yes).to_be_enabled(timeout=timeout)
            yes.click()

            # Verify domain removed from tree
            self.wait_until(lambda: self.row_locator(domain_name, tree_title="From").count() == 0, timeout_ms=timeout, interval_ms=200)
            refresh_page(self.page)

        except Exception as e:
            raise AssertionError(f"remove_domain('{domain_name}') failed. Problem: {e}")

    # ✅
    def remove_chassis(self, chassis_name: str, parent_domain_name: str | None = None, timeout: int = 8000):
        """
        Delete a chassis (e.g., 'Chassis: 99/99' or 'Chassis: 99').
        If the chassis is under a collapsed domain, pass parent_domain_name to expand first.
        """
        try:
            refresh_page(self.page)
            name = (chassis_name or "").strip()
            if not name:
                raise ValueError("chassis_name is empty")

            # Optional: expand parent domain so the chassis row becomes visible
            if parent_domain_name:
                self.expand_element(parent_domain_name, tree_title="From", timeout=timeout)

            # Click Remove
            self.click_remove_chassis_btn(name, timeout=timeout)
            sleep(0.5)

            warn = self.warning_remove_modal()
            msg = self.message_modal()

            def warning_visible() -> bool:
                try:
                    return warn.count() > 0 and warn.is_visible()
                except Exception:
                    return False

            def message_visible() -> bool:
                try:
                    return msg.count() > 0 and msg.is_visible()
                except Exception:
                    return False
                
            sleep(0.5)

            # Wait until either Warning OR Message modal appears
            self.wait_until(lambda: warning_visible() or message_visible(), timeout_ms=timeout, interval_ms=150)

            # If Message modal popped -> cannot delete (or blocked)
            if message_visible():
                t = self.message_text()
                expect(t).to_be_visible(timeout=timeout)
                msg_text = t.inner_text().strip()

                ok = self.message_ok_btn()
                expect(ok).to_be_visible(timeout=timeout)
                ok.click()

                raise AssertionError(f"remove_chassis('{name}') failed (Message modal): {msg_text}")

            # Warning modal must appear -> confirm
            expect(warn).to_be_visible(timeout=timeout)

            yes = self.warning_yes_btn()
            expect(yes).to_be_visible(timeout=timeout)
            expect(yes).to_be_enabled(timeout=timeout)
            sleep(0.5)
            yes.click()
            refresh_page(self.page)

            # After confirming, sometimes a Message modal can still appear.
            # Give it a short chance before assert disappearance.
            try:
                self.wait_until(lambda: message_visible() or (self.chassis_row_locator(name).count() == 0), timeout_ms=min(timeout, 3000), interval_ms=150)
            except Exception:
                pass

            if message_visible():
                t = self.message_text()
                expect(t).to_be_visible(timeout=timeout)
                msg_text = t.inner_text().strip()

                ok = self.message_ok_btn()
                expect(ok).to_be_visible(timeout=timeout)
                ok.click()
                sleep(0.5)

                raise AssertionError(f"remove_chassis('{name}') failed after confirmation (Message modal): {msg_text}")

            # Verify chassis removed from tree
            self.wait_until(lambda: self.chassis_row_locator(name, tree_title="From").count() == 0, timeout_ms=timeout, interval_ms=200)

            refresh_page(self.page)
            sleep(1)  # UI stabilize

        except Exception as e:
            raise AssertionError(f"remove_chassis('{chassis_name}') failed. Problem: {e}")
        
    # ✅
    def remove_device(self, device_name_or_ip: str, parent_domain_name: str | None = None, parent_chassis: str | None = None, timeout: int = 8000):
        """
        Delete a device row (ROADM/MUXPONDER/TRANSPONDER).
        - device_name_or_ip: "NAME (IP)" or IP only.
        - If the device is hidden under a collapsed domain/chassis, pass parent_domain_name and/or parent_chassis to expand first.
        """
        try:
            refresh_page(self.page)
            target = (device_name_or_ip or "").strip()
            if not target:
                raise ValueError("device_name_or_ip is empty")

            # Optional: expand domain, then chassis (if relevant)
            if parent_domain_name:
                self.expand_element(parent_domain_name, tree_title="From", timeout=timeout)

            if parent_chassis:
                self.expand_chassis_and_click_on_device(device_id=device_name_or_ip, parent_chassis=parent_chassis)
            else:
                self.expand_chassis_and_click_on_device(device_id=device_name_or_ip)

            # Click Remove
            self.click_remove_device_btn(target, timeout=timeout)

            warn = self.warning_remove_modal()
            msg = self.message_modal()

            def warning_visible() -> bool:
                try:
                    return warn.count() > 0 and warn.is_visible()
                except Exception:
                    return False

            def message_visible() -> bool:
                try:
                    return msg.count() > 0 and msg.is_visible()
                except Exception:
                    return False

            # Wait until either Warning OR Message modal appears
            self.wait_until(lambda: warning_visible() or message_visible(), timeout_ms=timeout, interval_ms=150)

            # If Message modal popped -> cannot delete
            if message_visible():
                t = self.message_text()
                expect(t).to_be_visible(timeout=timeout)
                msg_text = t.inner_text().strip()

                ok = self.message_ok_btn()
                expect(ok).to_be_visible(timeout=timeout)
                ok.click()

                raise AssertionError(f"remove_device('{target}') failed (Message modal): {msg_text}")

            # Warning modal must appear -> confirm
            expect(warn).to_be_visible(timeout=timeout)

            yes = self.warning_yes_btn()
            expect(yes).to_be_visible(timeout=timeout)
            expect(yes).to_be_enabled(timeout=timeout)
            yes.click()

            # After confirming, sometimes a Message modal can still appear (blocked by dependencies)
            try:
                self.wait_until(lambda: message_visible() or (self.device_row_locator(target, tree_title="From").count() == 0), timeout_ms=min(timeout, 3000), interval_ms=150)
            except Exception:
                pass

            if message_visible():
                t = self.message_text()
                expect(t).to_be_visible(timeout=timeout)
                msg_text = t.inner_text().strip()

                ok = self.message_ok_btn()
                expect(ok).to_be_visible(timeout=timeout)
                ok.click()

                raise AssertionError(f"remove_device('{target}') failed after confirmation (Message modal): {msg_text}")

            # Verify device removed from tree
            self.wait_until(lambda: self.device_row_locator(target, tree_title="From").count() == 0, timeout_ms=timeout, interval_ms=200)

            refresh_page(self.page)
            sleep(1)

        except Exception as e:
            raise AssertionError(f"remove_device('{device_name_or_ip}') failed. Problem: {e}")
        
    # ==========================================================
    # Rename domain
    # ==========================================================

    # ✅
    def expand_name_with_number(self, value: str) -> str:
        """
        Supported formats:
        - 'NAME-NUMBER'   -> 'NAME-NUMBER/NUMBER'
        - 'NAME: NUMBER'  -> 'NAME: NUMBER/NUMBER'
        """
        value = value.strip()

        # Case 1: NAME-NUMBER
        if "-" in value and "/" not in value:
            try:
                name, number = value.rsplit("-", 1)
                number = number.strip()
                if number.isdigit():
                    return f"{name}-{number}/{number}"
            except ValueError:
                pass

        # Case 2: NAME: NUMBER
        if ":" in value and "/" not in value:
            try:
                name, number = value.split(":", 1)
                number = number.strip()
                if number.isdigit():
                    return f"{name.strip()}: {number}/{number}"
            except ValueError:
                pass

        raise ValueError(
            f"Invalid format. Expected 'NAME-NUMBER' or 'NAME: NUMBER', got: {value}"
        )

    # ✅
    def rename_chassis_modal(self):
        """
        Return the Rename Chassis modal window.
        """
        return (self.page.locator("div.modal-dialog.pl-modal")
            .filter(has=self.page.locator("div.domain-management-modal-header div.title", has_text=re.compile(r"^\s*Rename chassis\s*$"))).first)

    # ✅
    def rename_chassis_name_input(self):
        """
        Return the chassis name input field.
        """
        return self.rename_chassis_modal().locator("app-input[formcontrolname='name'] input[type='text']").first

    # ✅
    def rename_chassis_description_input(self):
        """
        Return the chassis description input field.
        """
        return self.rename_chassis_modal().locator("app-input[formcontrolname='description'] input[type='text']").first

    # ✅
    def rename_chassis_update_btn(self):
        """
        Return the Update button in the Rename Chassis modal window.
        """
        return self.rename_chassis_modal().locator("section.form-actions button.btn.btn-primary", has_text="Update").first
    
    # ✅
    def click_rename_chassis_old(self, chassis_name: str, timeout: int = 5000):
        """
        Open the Rename Chassis modal window for the selected chassis.
        """
        try:
            # Select chassis row in the tree
            self.select_row(chassis_name, timeout=timeout)
            
            # Click Rename (enabled only for chassis element)
            btn = self.action_btn("Rename")
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).not_to_be_disabled(timeout=timeout)
            btn.click()

            # Assert modal opened
            modal = self.rename_chassis_modal()
            expect(modal).to_be_visible(timeout=timeout)

        except Exception as e:
            raise AssertionError(f"click_rename_chassis('{chassis_name}') failed. Problem: {e}")
        
    # ✅
    def click_rename_chassis_old2(self, chassis_name: str, timeout: int = 8000):
        """
        Open the Rename Chassis modal window for the selected chassis.
        """
        try:
            name = (chassis_name or "").strip()
            if not name:
                raise ValueError("chassis_name is empty")

            # Chassis in the tree is often displayed as NAME-NUM/NUM.
            # If user gave NAME-NUM, expand it to NAME-NUM/NUM for lookup.
            lookup = name
            if "/" not in lookup and (re.search(r".+?-\d+$", lookup) or re.search(r".+?:\s*\d+$", lookup)):
                try:
                    lookup = self.expand_name_with_number(lookup)
                except Exception:
                    pass

            # IMPORTANT: select the CHASSIS row (not generic)
            row = self.chassis_row_locator(lookup, tree_title="From")
            if row.count() == 0:
                # fallback: try original string
                row = self.chassis_row_locator(name, tree_title="From")
            if row.count() == 0:
                raise AssertionError(f"Chassis '{chassis_name}' not found in tree.")

            # Wait specifically for Rename button to become enabled
            self.click_row_and_wait_single_action_enabled(row, action_text="Rename", timeout=timeout)

            # Click Rename
            btn = self.action_btn("Rename")
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()

            # Assert modal opened (per your HTML)
            modal = self.rename_chassis_modal()
            expect(modal).to_be_visible(timeout=timeout)

        except Exception as e:
            raise AssertionError(f"click_rename_chassis('{chassis_name}') failed. Problem: {e}")

    # ✅
    def click_rename_chassis(self, chassis_name: str, timeout: int = 8000):
        """
        Open the Rename Chassis modal window for the selected chassis.
        """
        try:
            name = (chassis_name or "").strip()
            if not name:
                raise ValueError("chassis_name is empty")

            # Chassis in the tree is often displayed as NAME-NUM/NUM.
            # If user gave NAME-NUM, expand it to NAME-NUM/NUM for lookup.
            lookup = name
            if "/" not in lookup and (re.search(r".+?-\d+$", lookup) or re.search(r".+?:\s*\d+$", lookup)):
                try:
                    lookup = self.expand_name_with_number(lookup)
                except Exception:
                    pass

            # IMPORTANT: select the CHASSIS row (not generic)
            row = self.chassis_row_locator(lookup, tree_title="From")
            if row.count() == 0:
                # fallback: try original string
                row = self.chassis_row_locator(name, tree_title="From")
            if row.count() == 0:
                raise AssertionError(f"Chassis '{chassis_name}' not found in tree.")

            # Wait specifically for Rename button to become enabled
            self.click_row_and_wait(row, timeout=timeout, wait_for="action", action_text="Rename")

            # Click Rename
            btn = self.action_btn("Rename")
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()

            # Assert modal opened (per your HTML)
            modal = self.rename_chassis_modal()
            expect(modal).to_be_visible(timeout=timeout)

        except Exception as e:
            raise AssertionError(f"click_rename_chassis('{chassis_name}') failed. Problem: {e}")

    # ✅
    def submit_rename_chassis(self, new_name: str, new_description: str | None = None, timeout: int = 5000):
        """
        Submit the Rename Chassis modal window with new values.
        """
        try:
            modal = self.rename_chassis_modal()
            expect(modal).to_be_visible(timeout=timeout)

            name_inp = self.rename_chassis_name_input()
            expect(name_inp).to_be_visible(timeout=timeout)
            name_inp.fill(new_name)

            if new_description is not None:
                desc_inp = self.rename_chassis_description_input()
                expect(desc_inp).to_be_visible(timeout=timeout)
                desc_inp.fill(new_description)

            update_btn = self.rename_chassis_update_btn()
            expect(update_btn).to_be_visible(timeout=timeout)
            expect(update_btn).to_be_enabled(timeout=timeout)
            sleep(5)
            update_btn.click()

        except Exception as e:
            raise AssertionError(f"submit_rename_chassis('{new_name}') failed. Problem: {e}")

    # ✅        
    def rename_domain(self, old_chassis_name: str, new_chassis_name: str, new_description: str | None = None, timeout: int = 5000):
        """
        Rename a chassis and verify the tree updates correctly.
        """
        try:
            refresh_page(self.page)
            self.click_rename_chassis(old_chassis_name, timeout=timeout)
            sleep(1)
            self.submit_rename_chassis(new_chassis_name, new_description=new_description, timeout=timeout)
            sleep(1)

            # change the name format for verification
            new_expanded_chassis_name = self.expand_name_with_number(new_chassis_name)

            # Assert old disappears and new appears in tree
            if (self.row_locator(new_chassis_name).count() > 0):
                self.wait_until(lambda: self.row_locator(new_chassis_name).count() > 0, timeout_ms=timeout, interval_ms=200)
            elif (self.row_locator(new_expanded_chassis_name).count() > 0):
                self.wait_until(lambda: self.row_locator(new_expanded_chassis_name).count() > 0, timeout_ms=timeout, interval_ms=200)

            expect(self.row_locator(new_chassis_name)).to_be_visible(timeout=timeout)
            refresh_page(self.page)
            sleep(5)  # Allow UI to stabilize

        except Exception as e:
            raise AssertionError(f"rename_domain('{old_chassis_name}' -> '{new_chassis_name}') failed. Problem: {e}")

    # ==========================================================
    # Change Chassis ID
    # ==========================================================

    # ✅
    def expand_tree_node_if_collapsed(self, title_row, timeout: int = 8000) -> bool:
        """
        Expand a tree node (Domain/Chassis/etc.) if it's collapsed.
        """
        level = title_row.locator("xpath=ancestor::app-inventory-tree-level[1]")
        collapse = level.locator("div.collapse").first

        # If no collapse container, nothing to expand
        if collapse.count() == 0:
            return False

        # Decide collapsed state
        aria_hidden = (collapse.get_attribute("aria-hidden") or "").strip().lower()
        style = (collapse.get_attribute("style") or "").lower()
        is_collapsed = (aria_hidden == "true") or ("display: none" in style)

        if not is_collapsed:
            return False

        arrow_down = title_row.locator("xpath=../app-icon[@name='arrow-down']").first
        expect(arrow_down).to_be_visible(timeout=timeout)

        arrow_down.click(force=True)

        # Wait expanded
        def expanded() -> bool:
            ah = (collapse.get_attribute("aria-hidden") or "").strip().lower()
            st = (collapse.get_attribute("style") or "").lower()
            return (ah == "false") or ("display: block" in st) or ("show" in (collapse.get_attribute("class") or ""))

        self.wait_until(expanded, timeout_ms=timeout, interval_ms=150)
        return True

    # ✅
    def change_CHASSIS_ID_modal(self):
        """
        Return the 'Changing chassis ID for <ip>' modal window.
        """
        return (self.page.locator("div.modal-dialog.pl-modal").filter(has=self.page.locator("div.domain-management-modal-header div.title",
                has_text=re.compile(r"^\s*Changing chassis ID for\s+.+\s*$", re.IGNORECASE))).first)

    # ✅
    def change_the_chassis_ID_to_new_chassis_ID(self, timeout: int = 5000):
        """
        Select the 'New Chassis ID' option.
        """
        try:
            modal = self.change_CHASSIS_ID_modal()
            expect(modal).to_be_visible(timeout=timeout)

            # Click the LABEL 
            lbl = modal.locator("label[for='radio-new']").first
            expect(lbl).to_be_visible(timeout=timeout)
            lbl.click(force=True)

            # Verify selection by label class 
            expect(lbl).to_have_class(re.compile(r"\bchecked\b"), timeout=timeout)
            sleep(0.5)

        except Exception as e:
            raise AssertionError(f"change_the_chassis_ID_to_new_chassis_ID failed. Problem: {e}")

    # ✅
    def change_the_chassis_ID_to_existing_chassis_ID(self, timeout: int = 5000):
        """
        Select the 'Existing Chassis ID' option.
        """
        try:
            modal = self.change_CHASSIS_ID_modal()
            expect(modal).to_be_visible(timeout=timeout)

            lbl = modal.locator("label[for='radio-existing']").first
            expect(lbl).to_be_visible(timeout=timeout)
            lbl.click(force=True)

            expect(lbl).to_have_class(re.compile(r"\bchecked\b"), timeout=timeout)

            sleep(0.5)

        except Exception as e:
            raise AssertionError(f"change_the_chassis_ID_to_existing_chassis_ID failed. Problem: {e}")

    # ✅
    def change_the_chassis_ID_next_btn(self, timeout: int = 5000):
        """
        Click the 'Next' button in the Change Chassis ID modal.
        """
        try:
            btn = self.change_CHASSIS_ID_modal().locator("section.form-actions button.btn.btn-primary", has_text=re.compile(r"^\s*Next\s*$")).first

            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()

        except Exception as e:
            raise AssertionError(f"change_the_chassis_ID_next_btn failed. Problem: {e}")

    # ✅
    def close_change_the_chassis_ID_window(self, timeout: int = 5000):
        """
        Close the Change Chassis ID modal using the X button.
        """
        try:
            close_btn = self.change_CHASSIS_ID_modal().locator("div.domain-management-modal-header app-icon[name='close-square']").first

            expect(close_btn).to_be_visible(timeout=timeout)
            close_btn.click()

            # Ensure modal is closed
            expect(self.change_CHASSIS_ID_modal()).to_be_hidden(timeout=timeout)

        except Exception as e:
            raise AssertionError(f"close_change_the_chassis_ID_window failed. Problem: {e}")

    # ✅
    def change_the_chassis_ID_previous_btn(self, timeout: int = 5000):
        """
        Click the 'Previous' button in the Change Chassis ID modal.
        """
        try:
            btn = self.change_CHASSIS_ID_modal().locator("section.form-actions button.btn.btn-primary", has_text=re.compile(r"^\s*Previous\s*$", re.IGNORECASE)).first

            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()

        except Exception as e:
            raise AssertionError(f"change_the_chassis_ID_previous_btn failed. Problem: {e}")

    # ✅
    def change_the_chassis_ID_save_btn(self, timeout: int = 5000):
        """
        Click the 'Save' button in the Change Chassis ID modal.
        """
        try:
            btn = self.change_CHASSIS_ID_modal().locator("section.form-actions button.btn.btn-primary",has_text=re.compile(r"^\s*Save\s*$", re.IGNORECASE)).first

            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()

        except Exception as e:
            raise AssertionError(f"change_the_chassis_ID_save_btn failed. Problem: {e}")

    # ✅
    def set_new_chassis_ID(self, new_chassis_id: str | int, timeout: int = 5000):
        """
        Fill the 'New Chassis ID' number input in the Change Chassis ID modal.
        """
        try:
            inp = self.change_CHASSIS_ID_modal().locator("app-input[label='New Chassis ID'] input[type='number']").first

            expect(inp).to_be_visible(timeout=timeout)

            # Clear first to avoid leftovers
            inp.fill("")
            inp.fill(str(new_chassis_id))

            sleep(0.5)

        except Exception as e:
            raise AssertionError(f"set_new_chassis_ID('{new_chassis_id}') failed. Problem: {e}")

    # ✅
    def select_chassis_ID(self, chassis_id_to_select: str, timeout: int = 5000):
        """
        Open the 'Select Chassis ID' dropdown and pick the requested chassis ID.
        """
        try:
            sleep(0.5)
            modal = self.change_CHASSIS_ID_modal()
            expect(modal).to_be_visible(timeout=timeout)

            # Click the dropdown toggle 
            toggle = modal.locator("button#button-basic").first
            expect(toggle).to_be_visible(timeout=timeout)
            expect(toggle).to_be_enabled(timeout=timeout)
            toggle.click()
            sleep(0.5)

            menu = modal.locator("div#dropdown-basic.dropdown-menu.show").first
            expect(menu).to_be_visible(timeout=timeout)

            # Use flexible regex helper to match items despite spaces / dash variants
            rx = self.nav_text_regex(chassis_id_to_select)

            option = menu.locator("li.dropdown-item[role='menuitem']", has_text=rx).first
            if option.count() == 0:
                raise AssertionError(f"Chassis ID '{chassis_id_to_select}' not found in dropdown options.")

            option.scroll_into_view_if_needed()
            expect(option).to_be_visible(timeout=timeout)
            option.click()

            # Verify dropdown selection updated 
            self.wait_until(lambda: rx.search((toggle.inner_text() or "").strip()) is not None, timeout_ms=timeout, interval_ms=150)

        except Exception as e:
            raise AssertionError(f"select_chassis_ID('{chassis_id_to_select}') failed. Problem: {e}")

    # ✅
    def click_change_CHASSIS_ID(self, chassis_id: str, parent_chassis: str | None = None, timeout: int = 8000) -> bool:
        """
        Click 'Change Chassis ID' ONLY for a device row.
        If the device is under a collapsed "Chassis: X/X" node, pass parent_chassis to expand it first.
        If the device is under a domain node (already visible), only pass chassis_id.
        """
        try:
            sleep(1)
            target = (chassis_id or "").strip()
            if not target:
                raise ValueError("chassis_id is empty")

            tree = self.from_tree()

            device_types = ("ROADM", "TRANSPONDER", "MUXPONDER")

            is_ip_only = re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", target) is not None
            if is_ip_only:
                dev_rx = re.compile(rf"\(\s*{re.escape(target)}\s*\)")
            else:
                if re.search(r"\(\s*\d{1,3}(?:\.\d{1,3}){3}\s*\)", target) is None:
                    raise AssertionError(f"'{target}' does not look like a device row. Use 'NAME (IP)' or IP only.")
                dev_rx = self.nav_text_regex(target)

            # Default: search whole tree (domain case where devices already visible)
            search_root = tree

            # If parent_chassis is provided: expand it and scope search to it
            if parent_chassis:
                parent = (parent_chassis or "").strip()
                if not parent:
                    raise ValueError("parent_chassis is empty")

                parent_rx = self.nav_text_regex(parent)
                sleep(0.5)

                parent_row = tree.locator("div.inventory-tree-level-title[type='CHASSIS']").filter(has_text=parent_rx).first
                sleep(0.5)

                if parent_row.count() == 0:
                    # fallback: if in some builds it isn't typed as CHASSIS
                    parent_row = tree.locator("div.inventory-tree-level-title").filter(has_text=parent_rx).first
                    sleep(0.5)

                if parent_row.count() == 0:
                    raise AssertionError(f"parent_chassis '{parent}' not found in 'From' tree.")

                parent_row.scroll_into_view_if_needed()
                expect(parent_row).to_be_visible(timeout=timeout)

                # Expand chassis if needed 
                self.expand_tree_node_if_collapsed(parent_row, timeout=timeout)

                # Scope future device lookup ONLY inside this chassis subtree
                search_root = parent_row.locator("xpath=ancestor::app-inventory-tree-level[1]")
                sleep(0.5)

            device_rows = search_root.locator(", ".join([f"div.inventory-tree-level-title[type='{t}']" for t in device_types]))
            sleep(0.5)
            row = device_rows.filter(has_text=dev_rx).first

            if row.count() == 0:
                raise AssertionError(
                    f"Device '{target}' was not found."
                    + (f" (under parent_chassis='{parent_chassis}')" if parent_chassis else
                    " If it is under a collapsed 'Chassis: X/X', pass parent_chassis.")
                )

            # Click device -> enable button
            row.scroll_into_view_if_needed()
            expect(row).to_be_visible(timeout=timeout)
            row.click(force=True)

            btn = self.action_btn("Change Chassis ID")
            self.wait_until(lambda: btn.count() > 0 and btn.is_visible() and btn.is_enabled(),
                            timeout_ms=timeout, interval_ms=150)
            btn.click()
            sleep(1)
            return True

        except Exception as e:
            raise AssertionError(f"click_change_CHASSIS_ID('{chassis_id}', parent_chassis={parent_chassis}) failed. Problem: {e}")
        
    # ❌
    def change_CHASSIS_ID(self, chassis_id: str, to_mode: str = "new", new_chassis_id: str | int | None = None, existing_chassis_id: str | None = None,
        parent_chassis: str | None = None, timeout: int = 5000):
        """
        Full Change Chassis ID flow.
        to_mode: "new" or "existing"
        """
        for attempt in range(1, 4):
            try:
                refresh_page(self.page)
                sleep(15)
                mode = to_mode.strip().lower()
                if mode not in ("new", "existing"):
                    raise AssertionError(f"Invalid to_mode='{to_mode}'. Expected 'new' or 'existing'.")

                # 1) Open the Change Chassis ID modal
                if parent_chassis:
                    self.click_change_CHASSIS_ID(chassis_id, parent_chassis, timeout=timeout)
                else:
                    self.click_change_CHASSIS_ID(chassis_id, timeout=timeout)

                modal = self.change_CHASSIS_ID_modal()
                expect(modal).to_be_visible(timeout=timeout)

                # Title sanity check
                try:
                    title = modal.locator("div.domain-management-modal-header div.title").first
                    if title.count() > 0:
                        expect(title).to_be_visible(timeout=timeout)
                except Exception:
                    pass

                # 2) Choose New/Existing and click Next
                if mode == "new":
                    self.change_the_chassis_ID_to_new_chassis_ID(timeout=timeout)
                else:
                    self.change_the_chassis_ID_to_existing_chassis_ID(timeout=timeout)

                self.change_the_chassis_ID_next_btn(timeout=timeout)

                # 3) Either fill New Chassis ID OR select from dropdown
                if mode == "new":
                    if new_chassis_id is None:
                        raise AssertionError("new_chassis_id is required when to_mode='new'.")

                    # Wait until the New Chassis ID input exists 
                    new_input = modal.locator("app-input[label='New Chassis ID'] input[type='number']").first
                    expect(new_input).to_be_visible(timeout=timeout)

                    # Fill value using your setter
                    self.set_new_chassis_ID(new_chassis_id, timeout=timeout)

                else:
                    if not existing_chassis_id:
                        raise AssertionError("existing_chassis_id is required when to_mode='existing'.")
                    
                    if existing_chassis_id:
                        existing_chassis_id = self.normalize_chassis_name(existing_chassis_id)

                    # Wait until the dropdown exists 
                    dd_toggle = modal.locator("button#button-basic").first
                    expect(dd_toggle).to_be_visible(timeout=timeout)

                    # Select option using dropdown function 
                    self.select_chassis_ID(existing_chassis_id, timeout=timeout)

                # 4) Save + validate success toast
                self.change_the_chassis_ID_save_btn(timeout=timeout)

                # self.click_button_and_validate_toast(success_text="Success", failure_label=f"change_CHASSIS_ID('{chassis_id}', mode='{mode}')", timeout=max(timeout, 8000))

                # Optional: modal should close after success 
                try:
                    expect(self.change_CHASSIS_ID_modal()).to_be_hidden(timeout=timeout)
                except Exception:
                    pass

                refresh_page(self.page)
                return

            except Exception as e:
                try:
                    close_btn = self.change_CHASSIS_ID_modal().locator("div.domain-management-modal-header app-icon[name='close-square']").first
                    if close_btn.count() > 0 and close_btn.is_visible():
                        close_btn.click()
                except Exception:
                    pass

                raise AssertionError(f"change_CHASSIS_ID('{chassis_id}', to_mode='{to_mode}') failed. Problem: {e}")
            
        raise AssertionError(f"change_CHASSIS_ID('{chassis_id}', to_mode='{to_mode}') failed after 3 attempts. ")

    # ==========================================================
    # Move to domain
    # ==========================================================

    # ✅
    def handle_message_modal_if_present(self, timeout: int = 5000) -> str | None:
        """
        If a Message modal is visible, read its text, close it (Ok), and return the text.
        Returns None if no Message modal appeared.
        """
        try:
            modal = self.message_modal()
            if modal.count() == 0:
                return None

            # Make sure it's actually visible
            if not modal.is_visible():
                return None

            msg = self.message_text()
            expect(msg).to_be_visible(timeout=timeout)
            msg_text = msg.inner_text().strip()

            ok = self.message_ok_btn()
            expect(ok).to_be_visible(timeout=timeout)
            ok.click()

            # Ensure it closed
            expect(modal).to_be_hidden(timeout=timeout)

            return msg_text

        except Exception:
            # If something went wrong while handling, don't silently swallow it.
            raise AssertionError("Failed to handle message modal.")

    # ✅
    def middle_move_arrow_btn(self):
        """
        Return the middle arrow button used to move items between trees.
        """
        middle_move_arrow_btn = self.page.locator("div.domain-management-middle-actions button.btn").first
        sleep(0.5)

        return middle_move_arrow_btn

    # ✅
    def click_move_to_domain_mode(self, timeout: int = 5000):
        """
        Enable Move to Domain mode and show the target tree.
        """
        try:
            btn = self.action_btn("Move to domain")
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()
            
            # To tree should appear
            expect(self.to_tree()).to_be_visible(timeout=timeout)
            expect(self.middle_move_arrow_btn()).to_be_visible(timeout=timeout)

        except Exception as e:
            raise AssertionError(f"click_move_to_domain_mode failed. Problem: {e}")
    
    # ✅
    def move_to_domain_old(self, source_item_name: str, target_domain_name: str, timeout: int = 5000):
        """
        Move an item from the From tree to a target domain in the To tree.
        """
        try:
            # Pick source in From
            self.select_row(source_item_name, tree_title="From", timeout=timeout)

            # Ensure move mode UI exists
            if self.to_tree().count() == 0:
                self.click_move_to_domain_mode(timeout=timeout)

            # Pick target in To
            self.select_row(target_domain_name, tree_title="To", timeout=timeout)

            # Click middle arrow to perform move
            arrow = self.middle_move_arrow_btn()
            expect(arrow).to_be_visible(timeout=timeout)
            expect(arrow).to_be_enabled(timeout=timeout)
            arrow.click()

            # If Warning pops -> Yes
            if self.modal().count() > 0 and self.modal_title().count() > 0:
                title = self.modal_title().inner_text().strip().lower()
                if title == "warning":
                    yes = self.modal_yes_button()
                    expect(yes).to_be_visible(timeout=timeout)
                    yes.click()

            # We don't want to hang if no modal appears, so we poll briefly.
            def message_visible() -> bool:
                try:
                    m = self.message_modal()
                    return m.count() > 0 and m.is_visible()
                except Exception:
                    return False

            # If Message modal popped -> read text, close Ok, and fail clearly
            if message_visible():
                msg = self.message_text()
                expect(msg).to_be_visible(timeout=timeout)
                msg_text = msg.inner_text().strip()

                lower = msg_text.lower()

                close = self.modal_close_x()
                expect(close).to_be_visible(timeout=timeout)
                close.click()

                # Ensure modal closed so it doesn't affect next actions
                expect(self.message_modal()).to_be_hidden(timeout=timeout)

                # Case 1: cannot move domain to itself
                if "cannot move domain to itself" in lower:
                    raise AssertionError(f"move_to_domain('{source_item_name}' → '{target_domain_name}') blocked: cannot move domain to itself.")

                # Case 2: already belongs to parent domain
                if "belongs already to this parent domain" in lower:
                    raise AssertionError(f"move_to_domain('{source_item_name}' → '{target_domain_name}') blocked: domain already belongs to this parent domain.")

                # Fallback: unknown message text
                raise AssertionError(f"move_to_domain('{source_item_name}' → '{target_domain_name}') blocked (Message modal): {msg_text}")
            
            # Minimal stability check
            expect(self.to_tree()).to_be_visible(timeout=timeout)
            refresh_page(self.page)

            sleep(1)  # Allow UI to stabilize

        except Exception as e:
            raise AssertionError(f"move_to_domain('{source_item_name}' -> '{target_domain_name}') failed. Problem: {e}")
    
    # ✅
    def move_to_domain(self, source_item_name: str, target_domain_name: str, timeout: int = 8000):
        """
        Move an item from the From tree to a target domain in the To tree.
        """
        try:
            # 1) Select SOURCE in "From" tree
            # Wait until "Move to domain" button becomes enabled
            src_row = self.row_locator(source_item_name, tree_title="From")

            expect(src_row).to_be_visible(timeout=timeout)
            src_row.scroll_into_view_if_needed()
            src_row.click(force=True)

            move_btn = self.action_btn("Move to domain")

            self.wait_until(lambda: move_btn.count() > 0 and move_btn.is_visible() and move_btn.is_enabled(), timeout_ms=timeout,
                interval_ms=150, desc="Move to domain button enabled")

            # 2) Enable Move-to-domain mode (if not already)
            if self.to_tree().count() == 0:
                move_btn.click()
                expect(self.to_tree()).to_be_visible(timeout=timeout)


            # 3) Select TARGET in "To" tree
            # Wait until middle arrow becomes enabled
            tgt_row = self.row_locator(target_domain_name, tree_title="To")

            expect(tgt_row).to_be_visible(timeout=timeout)
            tgt_row.scroll_into_view_if_needed()
            tgt_row.click(force=True)

            arrow = self.middle_move_arrow_btn()

            self.wait_until(lambda: arrow.count() > 0 and arrow.is_visible() and arrow.is_enabled(), timeout_ms=timeout, interval_ms=150,
                desc="Middle move arrow enabled")

            # 4) Click middle arrow
            arrow.click()

            # 5) Handle Warning modal (if appears)
            try:
                warn = self.warning_remove_modal()
                if warn.count() > 0 and warn.is_visible():
                    yes = self.warning_yes_btn()
                    expect(yes).to_be_visible(timeout=timeout)
                    yes.click()
            except Exception:
                pass

            # 6) Handle Message modal (blocking cases)
            try:
                msg = self.message_modal()
                if msg.count() > 0 and msg.is_visible():
                    text_el = self.message_text()
                    expect(text_el).to_be_visible(timeout=timeout)
                    msg_text = text_el.inner_text().strip()

                    ok = self.message_ok_btn()
                    expect(ok).to_be_visible(timeout=timeout)
                    ok.click()

                    raise AssertionError(f"move_to_domain('{source_item_name}' → '{target_domain_name}') blocked: {msg_text}")
            except AssertionError:
                raise
            except Exception:
                pass

            refresh_page(self.page)
            sleep(5)

            self.wait_until(lambda: self.from_tree().count() > 0, timeout_ms=timeout, desc="From tree reloaded after move")

        except Exception as e:
            raise AssertionError(f"move_to_domain('{source_item_name}' -> '{target_domain_name}') failed. Problem: {e}")