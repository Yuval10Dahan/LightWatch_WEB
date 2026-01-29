"""
Created by: Yuval Dahan
Date: 29/01/2026
"""

from __future__ import annotations
import re
import time
from typing import Callable, Optional
from playwright.sync_api import Page, expect


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
    def wait_until(self, condition: Callable[[], bool], timeout_ms: int = 10_000, interval_ms: int = 200):
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

    def root(self):
        """
        Return the main Domain Management page container.
        """
        return self.page.locator("app-device-management, section.domain-management-container").first

    def tree_container(self):
        """
        Return the inventory tree container element.
        """
        return self.page.locator("section.domain-management-container app-inventory-tree").first

    def tree_by_title(self, title: str):
        """
        Return the inventory tree with the given title.
        """
        return self.page.locator("section.domain-management-container app-inventory-tree").filter(has=self.page.locator("h3", has_text=re.compile(rf"^\s*{re.escape(title)}\s*$"))).first

    def from_tree(self):
        """
        Return the 'From' inventory tree.
        """
        return self.tree_by_title("From")

    def to_tree(self):
        """
        Return the 'To' inventory tree.
        """
        return self.tree_by_title("To")

    def bottom_actions(self):
        """
        Return the bottom action buttons container('Add domain', 'Remove', 'Rename', 'Change Chassis ID', 'Move to domain').
        """
        return self.page.locator("section.domain-management-bottom-actions").first

    def action_btn(self, text: str):
        """
        Return a bottom action button by its visible text.
        """
        return self.bottom_actions().locator("button.btn", has_text=re.compile(rf"^\s*{re.escape(text)}\s*$")).first

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

    def row_locator(self, name: str, tree_title: str = "From"):
        """
        Locate a tree row by name inside the specified tree.
        """
        rx = self.nav_text_regex(name)
        tree = self.from_tree() if tree_title == "From" else self.to_tree()
        return tree.locator("div.inventory-tree-level-title", has_text=rx).first

    def select_row(self, name: str, tree_title: str = "From", timeout: int = 10_000):
        """
        Click a tree row.
        """
        row = self.row_locator(name, tree_title=tree_title)

        expect(row).to_be_visible(timeout=timeout)
        row.scroll_into_view_if_needed()
        row.click(force=True)

        expect(row).to_have_class(re.compile(r"\bcurrent\b"), timeout=timeout)

    def domain_row_locator(self, name: str, tree_title: str = "From"):
        """
        Locate a DOMAIN-type row (used to enable Add domain).
        """
        rx = self.nav_text_regex(name)
        tree = self.from_tree() if tree_title == "From" else self.to_tree()
        return tree.locator("div.inventory-tree-level-title[type='DOMAIN']", has_text=rx).first

    def select_domain_row(self, name: str, tree_title: str = "From", timeout: int = 10_000):
        """
        Select a DOMAIN row.
        """
        row = self.domain_row_locator(name, tree_title=tree_title)

        expect(row).to_be_visible(timeout=timeout)
        row.scroll_into_view_if_needed()
        row.click(force=True)

        expect(row).to_have_class(re.compile(r"\bcurrent\b"), timeout=timeout)

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
    # ==========================================================
    # Modal handling
    # ==========================================================
    def modal(self):
        """
        Return the currently visible modal dialog.
        """
        return self.page.locator("div.modal-dialog.pl-modal:visible, div.modal-dialog:visible").first

    def modal_title(self):
        """
        Return the title element of the active modal.
        """
        return self.modal().locator(".domain-management-modal-header .title, .title").first

    def modal_close_x(self):
        """
        Return the close (X) button of the modal.
        """
        return self.modal().locator("app-icon[name='close-square'], .domain-management-modal-header app-icon").first

    def modal_button(self, text: str):
        """
        Return a modal button by its text.
        """
        return self.modal().locator("button", has_text=re.compile(rf"^\s*{re.escape(text)}\s*$")).first

    def modal_ok_button(self):
        """
        Return the 'Ok' button in a modal.
        """
        return self.modal_button("Ok")

    def modal_yes_button(self):
        """
        Return the 'Yes' button in a modal.
        """
        return self.modal_button("Yes")

    def modal_no_button(self):
        """
        Return the 'No' button in a modal.
        """
        return self.modal_button("No")

    # ==========================================================
    # Add domain
    # ==========================================================
    def add_domain_modal(self):
        """
        Return the 'Add new domain' modal window.
        """
        return (self.page.locator("div.modal-dialog.pl-modal")
            .filter(has=self.page.locator("div.domain-management-modal-header div.title", has_text=re.compile(r"^\s*Add new domain\s*$"))).first)

    def add_domain_name_input(self):
        """
        Return the domain name input field in the Add Domain modal window.
        """
        return self.add_domain_modal().locator("app-input[formcontrolname='name'] input[type='text']").first

    def add_domain_description_input(self):
        """
        Return the domain description input field in the Add Domain modal window.
        """
        modal = self.add_domain_modal()
        ta = modal.locator("app-input[formcontrolname='description'] textarea").first
        if ta.count() > 0:
            return ta
        return modal.locator("app-input[formcontrolname='description'] input").first

    def add_domain_confirm_btn(self):
        """
        Return the 'Add' button in the Add Domain modal window.
        """
        return self.add_domain_modal().locator("section.form-actions button.btn.btn-primary", has_text="Add").first

    def add_domain_close_btn(self):
        """
        Return the close (X) button of the Add Domain modal window.
        """
        return self.add_domain_modal().locator("div.domain-management-modal-header app-icon[name='close-square']").first

    def click_add_domain(self, parent_domain_name: str = "Inventory", timeout: int = 10_000):
        """
        Select a parent domain and open the Add Domain modal window.
        """
        try:
            # Ensure a DOMAIN row is selected so the button becomes enabled
            self.select_domain_row(parent_domain_name, tree_title="From", timeout=timeout)

            # Now the button should be enabled
            btn = self.action_btn("Add domain")
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()

            # Modal window opened
            modal = self.add_domain_modal()
            expect(modal).to_be_visible(timeout=timeout)

        except Exception as e:
            raise AssertionError(f"click_add_domain failed. Problem: {e}")

    def submit_add_domain(self, domain_name: str, domain_description: str = "", timeout: int = 10_000):
        """
        Submit the Add Domain modal and verify the domain was created.
        """
        try:
            modal = self.add_domain_modal()
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
            add_btn.click()

            # Validate success toast 
            self.click_button_and_validate_toast(success_text="Add domain", failure_label=f"add_domain('{domain_name}')", timeout=timeout)

            # Assert domain appears in tree
            self.wait_until(lambda: self.row_locator(domain_name).count() > 0, timeout_ms=timeout, interval_ms=200)
            expect(self.row_locator(domain_name)).to_be_visible(timeout=timeout)

        except Exception as e:
            raise AssertionError(f"submit_add_domain('{domain_name}') failed. Problem: {e}")

    def add_domain(self, domain_name: str, domain_description: str = "", parent_domain_name: str = "Inventory", timeout: int = 10_000):
        """
        Full flow to create a new domain under a parent domain.
        """
        self.click_add_domain(parent_domain_name=parent_domain_name, timeout=timeout)
        self.submit_add_domain(domain_name, domain_description, timeout=timeout)

    # ==========================================================
    # Remove domain
    # ==========================================================
    def warning_remove_modal(self):
        """
        Return the Warning modal window shown before domain deletion.
        """
        return (self.page.locator("div.modal-dialog.pl-modal")
            .filter(has=self.page.locator("div.domain-management-modal-header div.title", has_text=re.compile(r"^\s*Warning\s*$"))).first)

    def warning_yes_btn(self):
        """
        Return the 'Yes' button in the Warning modal window.
        """
        return self.warning_remove_modal().locator("section.form-actions button.btn.btn-primary", has_text="Yes").first

    def warning_no_btn(self):
        """
        Return the 'No' button in the Warning modal window.
        """
        return self.warning_remove_modal().locator("section.form-actions button.btn", has_text="No").first

    def message_modal(self):
        """
        Return the message modal displayed when some elements cannot be deleted.
        """
        return (self.page.locator("div.modal-dialog.pl-modal")
            .filter(has=self.page.locator("div.domain-management-modal-header div.title", has_text=re.compile(r"^\s*Message\s*$"))).first)

    def message_text(self):
        """
        Return the text content of the Message modal window.
        """
        return self.message_modal().locator("div.domain-management-modal-content article").first

    def message_ok_btn(self):
        """
        Return the 'Ok' button in the Message modal window.
        """
        return self.message_modal().locator("section.form-actions button.btn.btn-primary", has_text="Ok").first

    def remove_domain(self, domain_name: str, timeout: int = 10_000):
        """
        Delete a domain and handle warning or blocking messages.
        """
        try:
            # Select domain
            self.select_row(domain_name, timeout=timeout)

            # Click Remove
            rm = self.action_btn("Remove")
            expect(rm).to_be_visible(timeout=timeout)
            expect(rm).not_to_be_disabled(timeout=timeout)
            rm.click()

            # Confirm Warning -> Yes
            warn = self.warning_remove_modal()
            expect(warn).to_be_visible(timeout=timeout)

            yes = self.warning_yes_btn()
            expect(yes).to_be_visible(timeout=timeout)
            expect(yes).to_be_enabled(timeout=timeout)
            yes.click()

            # Two possible outcomes:
            #    A) Message modal pops (non-empty domain) -> handle & raise
            #    B) Domain removed -> it disappears from tree

            def message_is_open() -> bool:
                try:
                    m = self.message_modal()
                    return m.count() > 0 and m.is_visible()
                except Exception:
                    return False

            def domain_removed() -> bool:
                try:
                    return self.row_locator(domain_name).count() == 0
                except Exception:
                    return False

            # Wait until either message appears OR domain disappears
            self.wait_until(lambda: message_is_open() or domain_removed(), timeout_ms=timeout, interval_ms=200)

            # If message modal shown -> read text, click Ok, raise
            if message_is_open():
                msg = self.message_text()
                expect(msg).to_be_visible(timeout=timeout)
                msg_text = msg.inner_text().strip()

                ok = self.message_ok_btn()
                expect(ok).to_be_visible(timeout=timeout)
                ok.click()

                raise AssertionError(f"remove_domain('{domain_name}') blocked by server rule: {msg_text}")

            # Otherwise: assert removed
            self.wait_until(lambda: self.row_locator(domain_name).count() == 0, timeout_ms=timeout, interval_ms=200)

        except Exception as e:
            raise AssertionError(f"remove_domain('{domain_name}') failed. Problem: {e}")
    
    # ==========================================================
    # Rename domain
    # ==========================================================
    def rename_chassis_modal(self):
        """
        Return the Rename Chassis modal window.
        """
        return (self.page.locator("div.modal-dialog.pl-modal")
            .filter(has=self.page.locator("div.domain-management-modal-header div.title", has_text=re.compile(r"^\s*Rename chassis\s*$"))).first)

    def rename_chassis_name_input(self):
        """
        Return the chassis name input field.
        """
        return self.rename_chassis_modal().locator("app-input[formcontrolname='name'] input[type='text']").first

    def rename_chassis_description_input(self):
        """
        Return the chassis description input field.
        """
        return self.rename_chassis_modal().locator("app-input[formcontrolname='description'] input[type='text']").first

    def rename_chassis_update_btn(self):
        """
        Return the Update button in the Rename Chassis modal window.
        """
        return self.rename_chassis_modal().locator("section.form-actions button.btn.btn-primary", has_text="Update").first
    
    def click_rename_chassis(self, chassis_name: str, timeout: int = 10_000):
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
        
    def submit_rename_chassis(self, new_name: str, new_description: str | None = None, timeout: int = 10_000):
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
            update_btn.click()

        except Exception as e:
            raise AssertionError(f"submit_rename_chassis('{new_name}') failed. Problem: {e}")
        
    def rename_domain(self, old_chassis_name: str, new_chassis_name: str, new_description: str | None = None, timeout: int = 10_000):
        """
        Rename a chassis and verify the tree updates correctly.
        """
        try:
            self.click_rename_chassis(old_chassis_name, timeout=timeout)
            self.submit_rename_chassis(new_chassis_name, new_description=new_description, timeout=timeout)

            # Assert old disappears and new appears in tree
            self.wait_until(lambda: self.row_locator(new_chassis_name).count() > 0, timeout_ms=timeout, interval_ms=200)
            self.wait_until(lambda: self.row_locator(old_chassis_name).count() == 0, timeout_ms=timeout, interval_ms=200)

            expect(self.row_locator(new_chassis_name)).to_be_visible(timeout=timeout)

        except Exception as e:
            raise AssertionError(f"rename_domain('{old_chassis_name}' -> '{new_chassis_name}') failed. Problem: {e}")

    # ==========================================================
    # Change Chassis ID
    # ==========================================================
    def click_change_CHASSIS_ID(self, chassis_id: str, timeout: int = 10_000):
        """
        
        """
        pass

    # ==========================================================
    # Move to domain
    # ==========================================================
    def middle_move_arrow_btn(self):
        """
        Return the middle arrow button used to move items between trees.
        """
        return self.page.locator("div.domain-management-middle-actions button.btn").first

    def click_move_to_domain_mode(self, timeout: int = 10_000):
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
        
    def move_to_domain(self, source_item_name: str, target_domain_name: str, timeout: int = 10_000):
        """
        Move an item from the From tree to a target domain in the To tree.
        """
        try:
            # Ensure move mode UI exists
            if self.to_tree().count() == 0:
                self.click_move_to_domain_mode(timeout=timeout)

            # Pick source in From
            self.select_row(source_item_name, tree_title="From", timeout=timeout)

            # Pick target in To
            self.select_row(target_domain_name, tree_title="To", timeout=timeout)

            # Click middle arrow to perform move
            arrow = self.middle_move_arrow_btn()
            expect(arrow).to_be_visible(timeout=timeout)
            expect(arrow).to_be_enabled(timeout=timeout)
            arrow.click()

            # If Warning pops -> Yes
            if self.modal().count() > 0 and self.modal_title().count() > 0:
                t = self.modal_title().inner_text().strip().lower()
                if t == "warning":
                    yes = self.modal_yes_button()
                    expect(yes).to_be_visible(timeout=timeout)
                    yes.click()

            # If Message pops -> Ok
            if self.modal().count() > 0 and self.modal_title().count() > 0:
                t2 = self.modal_title().inner_text().strip().lower()
                if t2 == "message":
                    ok = self.modal_ok_button()
                    if ok.count() > 0:
                        ok.click()

            # Verification (needs your expected behavior!)
            # Minimal: ensure UI is still stable and target exists.
            expect(self.to_tree()).to_be_visible(timeout=timeout)

        except Exception as e:
            raise AssertionError(f"move_to_domain('{source_item_name}' -> '{target_domain_name}') failed. Problem: {e}")