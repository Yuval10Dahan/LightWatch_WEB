"""
Created by: Yuval Dahan
Date: 28/10/2026
"""


from playwright.sync_api import Page, Locator, expect
import re


class UserManagement:
    """
    Page Object Model for the User Management screen:
    quick filter, users table (edit / delete) and the Refresh / Add User buttons.
    """

    def __init__(self, page: Page):
        """
        Initialize UserManagement with Playwright page instance.
        """
        self.page = page
        self.root = page.locator("app-user section.user-management")
        self.quick_filter = self.root.locator('app-input[label="Quick filter"] input')
        self.table = self.root.locator("table.user-management-table")
        self.refresh_button = self.root.locator("footer.user-management-actions button").filter(
            has_text=re.compile(r"^\s*Refresh\s*$"))
        self.add_user_button = self.root.locator("footer.user-management-actions button").filter(
            has_text=re.compile(r"^\s*Add User\s*$"))


    # ==========================================================
    # Internal small helpers
    # ==========================================================

    # ✅
    def _click_button(self, btn: Locator, label: str, timeout: int = 8000) -> bool:
        try:
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click()
            return True
        except Exception as e:
            print(f"❌ Failed to click {label}: {e}")
            return False

    # ✅
    def _user_action(self, action: str, username: str, timeout: int = 8000) -> bool:
        """Click the Edit / Delete icon of the row whose username is `username`."""
        try:
            btn = self.table.locator(f'button[aria-label="{action} {username}"]').first
            expect(btn).to_be_attached(timeout=timeout)
            btn.scroll_into_view_if_needed(timeout=timeout)
            return self._click_button(btn, f"{action.lower()} user '{username}'", timeout)
        except Exception as e:
            print(f"❌ Failed to {action.lower()} user '{username}': {e}")
            return False


    # ==========================================================
    # Quick filter
    # ==========================================================

    # ✅
    def set_quick_filter(self, value: str, timeout: int = 8000) -> bool:
        """Type `value` into the Quick filter box (empty string clears it)."""
        try:
            expect(self.quick_filter).to_be_visible(timeout=timeout)
            expect(self.quick_filter).to_be_enabled(timeout=timeout)
            self.quick_filter.fill(str(value))
            return True
        except Exception as e:
            print(f"❌ Failed to set Quick filter: {e}")
            return False


    # ==========================================================
    # Users table
    # ==========================================================

    # ✅
    def get_all_users(self, timeout: int = 8000) -> dict[str, str]:
        """
        Return the users currently listed (respects the Quick filter) as
        {username: primary_group}, e.g. {"administrator": "Administrators"}.
        Empty dict if the table is empty or on failure.
        """
        try:
            expect(self.table).to_be_visible(timeout=timeout)
            rows = self.table.locator("tbody tr")
            users = {}
            for i in range(rows.count()):
                cells = rows.nth(i).locator("td")
                if cells.count() < 2:
                    continue
                username = " ".join((cells.nth(0).inner_text() or "").split())
                users[username] = " ".join((cells.nth(1).inner_text() or "").split())
            return users
        except Exception as e:
            print(f"❌ Failed to read users table: {e}")
            return {}

    # ✅
    def edit_user(self, username: str, timeout: int = 8000) -> bool:
        """Click the Edit (pencil) icon of the given user."""
        return self._user_action("Edit", username, timeout)

    # ✅
    def delete_user(self, username: str, timeout: int = 8000) -> bool:
        """
        Click the Delete (trash) icon of the given user, then confirm the
        "Delete User" dialog by clicking Delete.
        The icon is disabled for some users (e.g. the logged-in one) -> returns False.
        """
        if not self._user_action("Delete", username, timeout):
            return False
        try:
            confirm = self.page.locator('div[role="alertdialog"][aria-labelledby="delete-user-title"]')
            expect(confirm).to_be_visible(timeout=timeout)
            btn = confirm.locator("button.btn-danger").filter(has_text=re.compile(r"^\s*Delete\s*$"))
            if not self._click_button(btn, "Delete (confirm)", timeout):
                return False
            expect(confirm).to_be_hidden(timeout=timeout)
            return True
        except Exception as e:
            print(f"❌ Failed to confirm deletion of user '{username}': {e}")
            return False

    # ✅
    def cancel_delete_user(self, username: str, timeout: int = 8000) -> bool:
        """
        Click the Delete (trash) icon of the given user, then dismiss the
        confirmation dialog with Cancel (user is kept).
        """
        if not self._user_action("Delete", username, timeout):
            return False
        try:
            confirm = self.page.locator('div[role="alertdialog"][aria-labelledby="delete-user-title"]')
            expect(confirm).to_be_visible(timeout=timeout)
            btn = confirm.locator("button").filter(has_text=re.compile(r"^\s*Cancel\s*$"))
            if not self._click_button(btn, "Cancel (delete confirmation)", timeout):
                return False
            expect(confirm).to_be_hidden(timeout=timeout)
            return True
        except Exception as e:
            print(f"❌ Failed to cancel deletion of user '{username}': {e}")
            return False


    # ==========================================================
    # Edit User dialog
    # ==========================================================

    # ✅
    @property
    def _edit_dialog(self) -> Locator:
        return self.page.locator('div[role="dialog"][aria-labelledby="edit-user-title"]')

    # ✅
    def _edit_input(self, label: str) -> Locator:
        return self._edit_dialog.locator(f'app-input[label="{label}"] input')

    # ✅
    def _edit_fill(self, label: str, value, timeout: int = 8000) -> bool:
        try:
            field = self._edit_input(label)
            expect(field).to_be_visible(timeout=timeout)
            expect(field).to_be_enabled(timeout=timeout)
            field.fill(str(value))
            return True
        except Exception as e:
            print(f"❌ Failed to set {label}: {e}")
            return False

    # ✅
    def set_username(self, value: str, timeout: int = 8000) -> bool:
        """
        Fill the Username field. Note: the field is disabled in the Edit User
        dialog (existing users can't be renamed), so this returns False there.
        """
        return self._edit_fill("Username", value, timeout)

    # ✅
    def set_primary_group(self, value: str, timeout: int = 8000) -> bool:
        """Open the Primary Group dropdown and pick the option whose text equals `value`."""
        try:
            dropdown = self._edit_dialog.locator('app-dropdown[label="Primary Group"]')
            toggle = dropdown.locator("button.dropdown-toggle")
            expect(toggle).to_be_visible(timeout=timeout)
            toggle.click()
            option = dropdown.locator(".dropdown-menu li").filter(
                has_text=re.compile(rf"^\s*{re.escape(value)}\s*$")
            ).first
            expect(option).to_be_visible(timeout=timeout)
            option.click()
            return True
        except Exception as e:
            print(f"❌ Failed to select primary group '{value}': {e}")
            return False

    # ✅
    def set_full_name(self, value: str, timeout: int = 8000) -> bool:
        return self._edit_fill("Full Name", value, timeout)

    # ✅
    def set_description(self, value: str, timeout: int = 8000) -> bool:
        return self._edit_fill("Description", value, timeout)

    # ✅
    def set_new_password(self, value: str, timeout: int = 8000) -> bool:
        return self._edit_fill("New Password", value, timeout)

    # ✅
    def set_confirm_password(self, value: str, timeout: int = 8000) -> bool:
        return self._edit_fill("Confirm Password", value, timeout)

    # ✅
    def cancel_edit_user(self, timeout: int = 8000) -> bool:
        btn = self._edit_dialog.locator("button").filter(has_text=re.compile(r"^\s*Cancel\s*$"))
        return self._click_button(btn, "Cancel (Edit User)", timeout)

    # ✅
    def update_user(self, timeout: int = 8000) -> bool:
        btn = self._edit_dialog.locator("button[type='submit']")
        return self._click_button(btn, "Update User", timeout)


    # ==========================================================
    # Footer buttons
    # ==========================================================

    # ✅
    def refresh(self, timeout: int = 8000) -> bool:
        """Click the Refresh button."""
        return self._click_button(self.refresh_button, "Refresh", timeout)

    # ✅
    def add_user(self, timeout: int = 8000) -> bool:
        """Click the Add User button (opens the Add User dialog)."""
        return self._click_button(self.add_user_button, "Add User", timeout)
