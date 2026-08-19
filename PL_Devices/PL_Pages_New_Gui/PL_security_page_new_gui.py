"""
Created by: Yuval Dahan
Date: 03/08/2026
"""

from __future__ import annotations
from playwright.sync_api import Page, Frame, expect
from typing import List, Optional, Tuple, Union
from Utils.utils import refresh_page
import re
from time import time, sleep


class PL_SecurityPage:
    """
    PacketLight Left Menu -> Security page object.
    """

    def __init__(self, page: Page):
        self.page = page

    # ------------------------------------------------------------
    # Frames
    # ------------------------------------------------------------

    # ✅
    @property
    def vertical_menu_frame(self) -> Frame | None:
        try:
            return self.page.frame(name="vertical_menu_frame")
        except Exception:
            return None

    # ✅
    @property
    def main_page_frame(self) -> Frame | None:
        try:
            return self.page.frame(name="main_page")
        except Exception:
            return None

    # ------------------------------------------------------------
    # Locators (resolved per-frame at runtime)
    # ------------------------------------------------------------

    # ✅
    def security_btn(self, frame: Frame):
        return frame.locator("#Security").first

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------

    # ✅
    def is_security_active(self, frame: Frame) -> bool:
        try:
            cls = (self.security_btn(frame).get_attribute("class") or "")
            return "vertical_button_active" in cls
        except Exception:
            return False

    # ✅
    def accept_any_dialog_once(self) -> None:
        # Sometimes pops alerts - we accept so it won't block
        try:
            self.page.once("dialog", lambda d: d.accept())
        except Exception:
            pass

    # ------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------
    # ✅
    def open_security_tab(self, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Open Security from the left vertical menu (PacketLight GUI).

        Returns:
            True  -> Security is selected (active) and main_page navigated to Security.asp
            False -> failed after retries
        """
        sleep(0.5)

        for _ in range(retries):
            try:
                # Re-resolve frames each attempt
                vfr = self.vertical_menu_frame
                if vfr is None:
                    self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
                    vfr = self.vertical_menu_frame
                if vfr is None:
                    raise AssertionError("vertical_menu_frame not found")

                btn = self.security_btn(vfr)
                expect(btn).to_be_visible(timeout=timeout)

                # If not active -> click
                if not self.is_security_active(vfr):
                    self.accept_any_dialog_once()
                    btn.click(force=True)

                # Wait until it becomes active
                try:
                    vfr.wait_for_function("() => (document.getElementById('Security')?.className || '').includes('vertical_button_active')", timeout=timeout)
                except Exception:
                    # If the class didn't flip, treat as failure and retry
                    raise AssertionError("Security button did not become active")

                # Optional-but-strong validation
                mfr = self.main_page_frame
                if mfr is not None:
                    try:
                        mfr.wait_for_load_state("domcontentloaded", timeout=timeout)
                    except Exception:
                        pass

                    try:
                        if "Security.asp" in (mfr.url or ""):
                            return True
                    except Exception:
                        pass

                # If active state is confirmed, we consider it success even if URL check is flaky
                return True

            except Exception:
                try:
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass
                continue

        return False

    # ✅
    def click_on_users(self, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Click 'Users' tab under Security section (PacketLight GUI),
        """
        sleep(0.5)

        def get_main_page() -> Frame | None:
            try:
                return self.page.frame(name="main_page")
            except Exception:
                return None

        def get_security_iframe() -> Frame | None:
            try:
                return self.page.frame(name="Security")
            except Exception:
                return None

        def accept_any_dialog_once() -> None:
            try:
                self.page.once("dialog", lambda d: d.accept())
            except Exception:
                pass

        for _ in range(retries):
            try:
                if hasattr(self, "open_security_tab"):
                    self.open_security_tab(retries=2, timeout=timeout)

                main_fr = get_main_page()
                if main_fr is None:
                    self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
                    main_fr = get_main_page()
                if main_fr is None:
                    raise AssertionError("main_page frame not found")

                users_tab = main_fr.locator("#tab_users").first
                expect(users_tab).to_be_visible(timeout=timeout)

                # Click Users tab if not already active
                cls = (users_tab.get_attribute("class") or "")
                if "tabactive" not in cls:
                    accept_any_dialog_once()
                    users_tab.click(force=True)

                # Wait it becomes active (matches Selenium check)
                main_fr.wait_for_function("() => (document.getElementById('tab_users')?.className || '').includes('tabactive')", timeout=timeout)

                # Wait the inner iframe exists and loads Users page
                main_fr.wait_for_selector("iframe#Security_tab, iframe[name='Security']", timeout=timeout)

                sec_fr = get_security_iframe()
                if sec_fr is None:
                    # allow attach time
                    self.page.wait_for_timeout(200)
                    sec_fr = get_security_iframe()
                if sec_fr is None:
                    raise AssertionError("Security iframe not found")

                try:
                    sec_fr.wait_for_load_state("domcontentloaded", timeout=timeout)
                except Exception:
                    pass

                # URL check
                try:
                    if "Security_Users.asp" not in (sec_fr.url or ""):
                        # sometimes url has params; still fine, continue to header validation
                        pass
                except Exception:
                    pass

                # Header validation
                header = sec_fr.locator("#sec_user_header").first
                expect(header).to_be_visible(timeout=timeout)
                header_text = (header.inner_text() or "").strip()
                if header_text != "Local User Management":
                    raise AssertionError(f"Unexpected header: '{header_text}'")

                return True

            except Exception:
                # Selenium: Refresh_Screen() and retry
                try:
                    if hasattr(self, "click_reload_button"):
                        self.click_reload_button()
                    else:
                        self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass
                continue

        return False

    # ✅
    def get_users_table(self, retries: int = 5, timeout: int = 10_000) -> List[List[str]]:
        """
        Collect all Users and their details into a 2D list.

        New GUI renders Users rows as plain read-only <td> text (no more per-row
        #permission_{idx}/#slmSnmpv3Auth_{idx}/#slmSnmpv3Priv_{idx} selects) --
        editing moved to a shared modal. Read the cell text directly instead.
        """
        sleep(0.5)

        def get_security_frame():
            try:
                return self.page.frame(name="Security")
            except Exception:
                return None

        for _ in range(retries):
            try:
                if hasattr(self, "click_on_users"):
                    ok = self.click_on_users(retries=2, timeout=timeout)
                    if not ok:
                        raise AssertionError("click_on_users failed")

                sec_fr = get_security_frame()
                if sec_fr is None:
                    raise AssertionError("Security frame not found")

                # Verify header
                header = sec_fr.locator("#sec_user_header").first
                sleep(0.5)
                expect(header).to_be_visible(timeout=timeout)
                if (header.inner_text() or "").strip() != "Local User Management":
                    raise AssertionError("Not on Users table page")

                # Users table body -- #sec_user_table is now a <div> wrapping separate
                # #thead/#tbody <table>s (same pattern as the SNMP traps table).
                table = sec_fr.locator("#sec_user_table").first
                sleep(0.5)
                expect(table).to_be_visible(timeout=timeout)

                rows = table.locator("table#tbody tr")
                sleep(0.5)
                row_count = rows.count()

                users_detailed: List[List[str]] = []

                for i in range(row_count):
                    row = rows.nth(i)
                    cells = row.locator("td")
                    cell_count = cells.count()

                    # Header-only rows (<th>) or stray rows have no <td> -- skip.
                    if cell_count < 3:
                        continue

                    username = (cells.nth(0).inner_text() or "").strip()
                    permission = (cells.nth(1).inner_text() or "").strip()

                    # Columns: username, permission, masked password, [auth, priv], action
                    if cell_count >= 6:
                        snmpv3_auth = (cells.nth(3).inner_text() or "").strip()
                        snmpv3_priv = (cells.nth(4).inner_text() or "").strip()
                    else:
                        snmpv3_auth = ""
                        snmpv3_priv = ""

                    if not username:
                        continue

                    users_detailed.append([username, permission, snmpv3_auth, snmpv3_priv])
                    sleep(0.2)

                return users_detailed

            except Exception:
                try:
                    self.accept_any_dialog_once()
                    if hasattr(self, "click_reload_button"):
                        self.click_reload_button()
                    else:
                        self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass
                continue

        return []

    # ✅
    def is_user_located_in_users_table(self, user_name: str, users_table: List[List[str]], retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Return True if the given user exists in the Users table.
        Return False otherwise.

        Based on get_users_table().
        """
        sleep(0.5)

        if not user_name:
            raise ValueError("user_name must not be empty")

        for _ in range(retries):
            try:
                for row in users_table:
                    if not row:
                        continue

                    username = (row[0] or "").strip()

                    if username.lower() == user_name.strip().lower():
                        return True

                return False

            except Exception:
                try:
                    if hasattr(self, "click_reload_button"):
                        self.click_reload_button()
                    else:
                        self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False

    # ✅
    def return_user_parameters(self, user_name: str, users_table: List[List[str]], retries: int = 5, timeout: int = 10_000) -> Optional[List[str]]:
        """
        Return the user parameters: User Name, Permission, SNMPv3 Auth, SNMPv3 Priv.

        Returns:
            List[str] -> if user found
            None      -> if user not found
        """
        sleep(0.5)

        if not user_name:
            raise ValueError("user_name must not be empty")

        for _ in range(retries):
            try:
                for row in users_table:
                    if not row:
                        continue

                    username = (row[0] or "").strip()

                    if username.lower() == user_name.strip().lower():
                        return row

                sleep(1)

                return None

            except Exception:
                try:
                    if hasattr(self, "click_reload_button"):
                        self.click_reload_button()
                    else:
                        self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return None

    # ✅
    def _find_user_row(self, sec_fr: Frame, user_name: str, timeout: int = 10_000):
        """
        Locate the <tr> for a given username in the new GUI's read-only Users table
        (rows have no id -- match on the first cell's text, unlike the old GUI's
        td[id^='name_'] rows).

        Returns the row Locator, or None if not found.
        """
        table = sec_fr.locator("#sec_user_table").first
        expect(table).to_be_visible(timeout=timeout)

        rows = table.locator("table#tbody tr")
        target = user_name.strip().lower()

        for i in range(rows.count()):
            row = rows.nth(i)
            first_cell = row.locator("td").first
            if first_cell.count() == 0:
                continue
            username = (first_cell.inner_text() or "").strip()
            if username.lower() == target:
                return row

        return None

    # ✅
    def _open_user_modal(self, sec_fr: Frame, mode: str, row=None, timeout: int = 10_000) -> bool:
        """
        Open the shared Add/Edit user modal (#userModal). Its own JS relocates it to
        the top-level page on open (same pattern as the SNMP Add-Manager modal), so
        every field must be addressed via self.page afterwards, not sec_fr.

        mode: "add" -> click the "Add User" button.
              "edit" -> click the given row's "Edit User" button.

        Returns True if the modal became visible on the top-level page.
        """
        if mode == "add":
            open_btn = sec_fr.locator("button[name='adduser']").first
        else:
            if row is None:
                return False
            open_btn = row.locator("button[title='Edit User']").first

        if open_btn.count() == 0:
            return False

        expect(open_btn).to_be_visible(timeout=timeout)
        open_btn.click(force=True)
        expect(self.page.locator("#userModal").first).to_be_visible(timeout=timeout)
        return True

    # ✅
    def add_new_user(self, user_name: Optional[str] = None, permission: Optional[str] = None,
        password: Optional[str] = None, verify_password: Optional[str] = None, snmpv3_auth: Optional[str] = None,
        snmpv3_priv: Optional[str] = None, password_auth: Optional[str] = None, password_priv: Optional[str] = None,
        copy_paste: bool = False, alert_msg: Optional[str] = None, verify_last: bool = False,
        retries: int = 5, timeout: int = 10_000) -> Union[bool, Tuple[bool, str]]:
        """
        Add a new user in Security -> Users table (PacketLight GUI).

        New GUI: fields moved from an inline last-row of the table into a shared
        modal (#userModal) opened via the "Add User" button; its own JS relocates
        the modal to the top-level page, so fields are filled via self.page.

        Returns:
            - True  : user added successfully OR expected alert verified
            - False : failed
            - (False, 'Blocked from adding New Users') : when username field is readonly/disabled
        """
        sleep(0.5)

        ALERT_USER_NAME = "Specify a User Name"
        ALERT_USER_EXIST = "User Already Exists."
        MAX_USERS_MSG = "Cannot add any more users."

        def normalize_permission_to_value(p: Optional[str]) -> Optional[str]:
            if p is None:
                return None
            s = p.strip().lower()

            if s in {"1", "read only", "readonly", "read-only", "ro", "read only user", "read-only user"}:
                return "1"
            if s in {"2", "read/write", "read write", "read-write", "rw", "read/write user", "read write user"}:
                return "2"
            if s in {"4", "admin", "administrator", "admin user"}:
                return "4"

            if "read" in s and "only" in s:
                return "1"
            if "read" in s and ("write" in s or "rw" in s):
                return "2"
            if "admin" in s:
                return "4"

            raise AssertionError(f"Unsupported permission value: '{p}'")

        def select_by_visible_text_contains(select_loc, wanted: str):
            if wanted == "SHA-1":
                wanted = (wanted or "").strip().replace('-', '')  # e.g. SHA-1 -> SHA1
            else:
                wanted = (wanted or "").strip()

            if not wanted:
                return

            try:
                select_loc.select_option(label=wanted)
                return
            except Exception:
                pass

            opts = select_loc.locator("option")
            for i in range(opts.count()):
                t = (opts.nth(i).inner_text() or "").strip()
                if t and (t == wanted or wanted in t or t in wanted):
                    select_loc.select_option(label=t)
                    return

            raise AssertionError(f"Option not found in select: '{wanted}'")

        def arm_dialog_capture_once():
            holder = {"text": None}

            def _handler(d):
                try:
                    holder["text"] = (d.message or "").strip()
                except Exception:
                    holder["text"] = None
                try:
                    d.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

            return holder

        def wait_for_captured_dialog(holder, ms: int = 3000) -> Optional[str]:
            step = 50
            loops = max(1, ms // step)
            for _ in range(loops):
                if holder.get("text") is not None:
                    return holder["text"]
                try:
                    self.page.wait_for_timeout(step)
                except Exception:
                    break
            return holder.get("text")

        for attempt in range(retries):
            try:
                ok = self.click_on_users(retries=2, timeout=timeout)
                if not ok:
                    raise AssertionError("click_on_users failed")

                sec_fr = self.page.frame(name="Security")
                if sec_fr is None:
                    raise AssertionError("Security frame not found")

                header = sec_fr.locator("#sec_user_header").first
                expect(header).to_be_visible(timeout=timeout)

                if not self._open_user_modal(sec_fr, "add", timeout=timeout):
                    raise AssertionError("Could not open Add User modal")

                ctx = self.page

                username_in = ctx.locator("input[name='user_name']").first
                perm_sel = ctx.locator("select#PermissionSelect").first
                password_in = ctx.locator("input[name='password']").first
                verify_in = ctx.locator("input[name='verify_password']").first

                auth_sel = ctx.locator("select#slmSnmpv3Auth, select[name='slmSnmpv3Auth']").first
                priv_sel = ctx.locator("select#slmSnmpv3Priv, select[name='slmSnmpv3Priv']").first

                auth_pass_in = ctx.locator("input#authPass, input[name='authPass']").first
                verify_auth_pass_in = ctx.locator("input#verify_authPass, input[name='verify_authPass']").first
                priv_pass_in = ctx.locator("input#privPass, input[name='privPass']").first
                verify_priv_pass_in = ctx.locator("input#verify_privPass, input[name='verify_privPass']").first

                add_btn = ctx.locator("#btnSaveUser").first
                expect(add_btn).to_be_attached(timeout=timeout)

                # Username
                if user_name is not None:
                    expect(username_in).to_be_visible(timeout=timeout)
                    if (username_in.get_attribute("readonly") or "").strip() or (username_in.get_attribute("disabled") or "").strip():
                        return (False, "Blocked from adding New Users")

                    username_in.click()
                    username_in.fill("")
                    if copy_paste:
                        username_in.fill(user_name)
                    else:
                        username_in.type(user_name, delay=20)

                # Permission
                if permission is not None:
                    expect(perm_sel).to_be_visible(timeout=timeout)
                    perm_value = normalize_permission_to_value(permission)
                    perm_sel.select_option(value=perm_value)

                # SNMPv3 Auth / Priv
                if snmpv3_auth is not None and auth_sel.count() > 0:
                    expect(auth_sel).to_be_visible(timeout=timeout)
                    dlg_holder = arm_dialog_capture_once()
                    select_by_visible_text_contains(auth_sel, snmpv3_auth)

                if snmpv3_priv is not None and priv_sel.count() > 0:
                    expect(priv_sel).to_be_visible(timeout=timeout)
                    dlg_holder = arm_dialog_capture_once()
                    select_by_visible_text_contains(priv_sel, snmpv3_priv)

                # Password / Verify
                if password is not None:
                    expect(password_in).to_be_visible(timeout=timeout)
                    password_in.click()
                    password_in.fill(password)

                    expect(verify_in).to_be_visible(timeout=timeout)
                    verify_in.click()
                    verify_in.fill(verify_password if verify_password is not None else password)

                # Auth/Priv passwords
                if password_auth is not None and auth_pass_in.count() > 0:
                    try:
                        auth_pass_in.fill(password_auth)
                        verify_auth_pass_in.fill(password_auth)
                    except Exception as e:
                        print(f"error: {e}")

                if password_priv is not None and priv_pass_in.count() > 0:
                    try:
                        priv_pass_in.fill(password_priv)
                        verify_priv_pass_in.fill(password_priv)
                    except Exception as e:
                        print(f"error: {e}")

                # Click Save (single dialog handling)
                add_btn.scroll_into_view_if_needed()
                expect(add_btn).to_be_visible(timeout=timeout)

                dlg_holder = arm_dialog_capture_once()

                try:
                    add_btn.click(timeout=timeout)
                except Exception:
                    add_btn.click(timeout=timeout, force=True)

                dlg_txt = wait_for_captured_dialog(dlg_holder, ms=4000)

                # Alert verification
                if alert_msg:
                    if dlg_txt is None:
                        if alert_msg == ALERT_USER_NAME:
                            return True
                        return False

                    if dlg_txt.lower() == alert_msg.lower():
                        try:
                            self.click_reload_button()
                        except Exception:
                            pass
                        return True

                    if dlg_txt in (ALERT_USER_NAME, ALERT_USER_EXIST):
                        return True

                    try:
                        self.click_reload_button()
                    except Exception:
                        pass
                    return False

                # Optional: verify user appears
                if verify_last and user_name:
                    try:
                        expect(sec_fr.locator(f"#sec_user_table >> text={user_name}").first).to_be_visible(timeout=timeout)
                    except Exception:
                        return False

                    try:
                        if sec_fr.locator(f"text={MAX_USERS_MSG}").first.is_visible():
                            try:
                                self.click_reload_button()
                            except Exception:
                                pass
                            return False
                    except Exception:
                        pass

                sleep(1)

                return True

            except Exception:
                try:
                    self.click_reload_button()
                except Exception:
                    try:
                        self.page.reload(wait_until="domcontentloaded")
                    except Exception:
                        pass
                continue

        try:
            self.click_reload_button()
        except Exception:
            pass
        return False

    # ✅
    def delete_user(self, user_name: str, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Delete an existing user from Security -> Users table.

        New GUI: rows have no id/name_{idx} anchor and no submit-type Delete
        button -- match the row by its username cell text and click its
        button[title='Delete User'] "quick action" instead.

        Returns:
            True  -> user deleted successfully
            False -> user not found, delete button not available, or delete failed
        """
        sleep(0.5)

        if not user_name:
            raise ValueError("user_name must not be empty")

        def arm_dialog_accept_once():
            holder = {"text": None}

            def _handler(dialog):
                try:
                    holder["text"] = (dialog.message or "").strip()
                except Exception:
                    holder["text"] = None

                try:
                    dialog.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

            return holder

        for _ in range(retries):
            try:
                ok = self.click_on_users(retries=2, timeout=timeout)
                if not ok:
                    raise AssertionError("click_on_users failed")

                sec_fr = self.page.frame(name="Security")
                if sec_fr is None:
                    raise AssertionError("Security frame not found")

                header = sec_fr.locator("#sec_user_header").first
                expect(header).to_be_visible(timeout=timeout)

                target_row = self._find_user_row(sec_fr, user_name, timeout=timeout)
                if target_row is None:
                    return False

                delete_btn = target_row.locator("button[title='Delete User']").first

                # Users like tech/admin may not have a Delete button (isSacred)
                if delete_btn.count() == 0:
                    return False

                expect(delete_btn).to_be_visible(timeout=timeout)

                dialog_holder = arm_dialog_accept_once()

                delete_btn.scroll_into_view_if_needed()
                delete_btn.click(force=True, timeout=timeout)

                # The button calls SubmitQuickAction(1, ...), usually causing form submit/reload.
                try:
                    sec_fr.wait_for_load_state("domcontentloaded", timeout=timeout)
                except Exception:
                    pass

                try:
                    self.page.wait_for_timeout(500)
                except Exception:
                    pass

                # Re-open Users page after submit/reload
                ok = self.click_on_users(retries=2, timeout=timeout)
                if not ok:
                    raise AssertionError("Failed returning to Users page after delete")

                sec_fr = self.page.frame(name="Security")
                if sec_fr is None:
                    raise AssertionError("Security frame not found after delete")

                still_there = self._find_user_row(sec_fr, user_name, timeout=timeout)
                if still_there is not None:
                    return False

                sleep(1)

                return True

            except Exception:
                try:
                    self.click_reload_button()
                except Exception:
                    try:
                        self.page.reload(wait_until="domcontentloaded")
                    except Exception:
                        pass

        return False

    # ✅
    def modify_user(self, user_name: str, permission: Optional[str] = None, password: Optional[str] = None, verify_password: Optional[str] = None,
        snmpv3_auth: Optional[str] = None, snmpv3_priv: Optional[str] = None, password_auth: Optional[str] = None,
        verify_password_auth: Optional[str] = None, password_priv: Optional[str] = None, verify_password_priv: Optional[str] = None,
        retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Modify an existing user in Security -> Users table.

        New GUI: editing moved from inline per-row selects/inputs to the shared
        Add/Edit modal, opened via the row's button[title='Edit User'] -- fields
        are filled via self.page since the modal relocates to the top-level page.

        You can change:
            - permission
            - password / verify_password
            - snmpv3_auth
            - snmpv3_priv
            - password_auth / verify_password_auth
            - password_priv / verify_password_priv

        Returns:
            True  -> modify action submitted successfully
            False -> user not found, modify failed, or user cannot be modified
        """
        sleep(0.5)

        if not user_name:
            raise ValueError("user_name must not be empty")

        def normalize_permission_to_value(p: str) -> str:
            s = p.strip().lower()

            if s in {"1", "read only", "readonly", "read-only", "ro"}:
                return "1"
            if s in {"2", "read/write", "read write", "read-write", "rw"}:
                return "2"
            if s in {"4", "admin", "administrator"}:
                return "4"

            if "read" in s and "only" in s:
                return "1"
            if "read" in s and "write" in s:
                return "2"
            if "admin" in s:
                return "4"

            raise AssertionError(f"Unsupported permission value: '{p}'")

        def select_by_visible_text_contains(select_loc, wanted: str) -> None:
            wanted = (wanted or "").strip()

            if wanted == "SHA-1":
                wanted = "SHA1"

            try:
                select_loc.select_option(label=wanted)
                return
            except Exception:
                pass

            opts = select_loc.locator("option")
            for i in range(opts.count()):
                txt = (opts.nth(i).inner_text() or "").strip()
                if txt and (txt.lower() == wanted.lower() or wanted.lower() in txt.lower()):
                    select_loc.select_option(label=txt)
                    return

            raise AssertionError(f"Option not found: '{wanted}'")

        def arm_dialog_accept_once():
            holder = {"text": None}

            def _handler(dialog):
                try:
                    holder["text"] = (dialog.message or "").strip()
                except Exception:
                    holder["text"] = None

                try:
                    dialog.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

            return holder

        for _ in range(retries):
            try:
                ok = self.click_on_users(retries=2, timeout=timeout)
                if not ok:
                    raise AssertionError("click_on_users failed")

                sec_fr = self.page.frame(name="Security")
                if sec_fr is None:
                    raise AssertionError("Security frame not found")

                header = sec_fr.locator("#sec_user_header").first
                expect(header).to_be_visible(timeout=timeout)

                target_row = self._find_user_row(sec_fr, user_name, timeout=timeout)
                if target_row is None:
                    return False

                if not self._open_user_modal(sec_fr, "edit", row=target_row, timeout=timeout):
                    return False

                ctx = self.page

                # Permission
                if permission is not None:
                    permission_sel = ctx.locator("select#PermissionSelect").first
                    expect(permission_sel).to_be_visible(timeout=timeout)

                    if permission_sel.is_disabled():
                        return False

                    permission_sel.select_option(value=normalize_permission_to_value(permission))

                # Password
                if password is not None:
                    password_in = ctx.locator("input[name='password']").first
                    verify_in = ctx.locator("input[name='verify_password']").first

                    expect(password_in).to_be_visible(timeout=timeout)
                    expect(verify_in).to_be_visible(timeout=timeout)

                    password_in.fill(password)
                    verify_in.fill(verify_password if verify_password is not None else password)

                # SNMPv3 Auth
                if snmpv3_auth is not None:
                    auth_sel = ctx.locator("select#slmSnmpv3Auth").first
                    expect(auth_sel).to_be_visible(timeout=timeout)
                    select_by_visible_text_contains(auth_sel, snmpv3_auth)

                # SNMPv3 Priv
                if snmpv3_priv is not None:
                    priv_sel = ctx.locator("select#slmSnmpv3Priv").first
                    expect(priv_sel).to_be_visible(timeout=timeout)
                    select_by_visible_text_contains(priv_sel, snmpv3_priv)

                # SNMPv3 Auth password
                if password_auth is not None:
                    auth_pass_in = ctx.locator("input#authPass").first
                    verify_auth_pass_in = ctx.locator("input#verify_authPass").first

                    expect(auth_pass_in).to_be_visible(timeout=timeout)
                    expect(verify_auth_pass_in).to_be_visible(timeout=timeout)

                    auth_pass_in.fill(password_auth)
                    verify_auth_pass_in.fill(verify_password_auth if verify_password_auth is not None else password_auth)

                # SNMPv3 Priv password
                if password_priv is not None:
                    priv_pass_in = ctx.locator("input#privPass").first
                    verify_priv_pass_in = ctx.locator("input#verify_privPass").first

                    expect(priv_pass_in).to_be_visible(timeout=timeout)
                    expect(verify_priv_pass_in).to_be_visible(timeout=timeout)

                    priv_pass_in.fill(password_priv)
                    verify_priv_pass_in.fill(verify_password_priv if verify_password_priv is not None else password_priv)

                save_btn = ctx.locator("#btnSaveUser").first
                expect(save_btn).to_be_visible(timeout=timeout)

                dialog_holder = arm_dialog_accept_once()

                save_btn.scroll_into_view_if_needed()
                save_btn.click(force=True, timeout=timeout)

                try:
                    sec_fr.wait_for_load_state("domcontentloaded", timeout=timeout)
                except Exception:
                    pass

                try:
                    self.page.wait_for_timeout(500)
                except Exception:
                    pass

                sleep(1)

                return True

            except Exception:
                try:
                    self.click_reload_button()
                except Exception:
                    try:
                        self.page.reload(wait_until="domcontentloaded")
                    except Exception:
                        pass

        return False

    # ✅
    def disable_user(self, user_name: str, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Disable an existing active user from Security -> Users table.

        New GUI: the separate Enable/Disable buttons were replaced by a single
        toggle checkbox per row (checked = enabled). Unchecking it fires the same
        SubmitQuickAction(2, ...) flow the old buttons used.

        Returns:
            True  -> user disabled successfully
            False -> user not found, toggle not available, already disabled, or action failed
        """
        sleep(0.5)

        if not user_name:
            raise ValueError("user_name must not be empty")

        def arm_dialog_accept_once():
            holder = {"text": None}

            def _handler(dialog):
                try:
                    holder["text"] = (dialog.message or "").strip()
                except Exception:
                    holder["text"] = None

                try:
                    dialog.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

            return holder

        for _ in range(retries):
            try:
                ok = self.click_on_users(retries=2, timeout=timeout)
                if not ok:
                    raise AssertionError("click_on_users failed")

                sec_fr = self.page.frame(name="Security")
                if sec_fr is None:
                    raise AssertionError("Security frame not found")

                header = sec_fr.locator("#sec_user_header").first
                expect(header).to_be_visible(timeout=timeout)

                target_row = self._find_user_row(sec_fr, user_name, timeout=timeout)
                if target_row is None:
                    return False

                toggle = target_row.locator("input[type='checkbox']").first

                # User may already be disabled, or may not support the toggle (isSacred)
                if toggle.count() == 0:
                    return False

                if not toggle.is_checked():
                    # Already disabled -- nothing to do
                    return False

                # The native checkbox is visually hidden (zero-size, custom toggle-switch
                # CSS) -- click its wrapping label instead, same as a real user would.
                toggle_label = target_row.locator("label.custom-toggle").first
                expect(toggle_label).to_be_visible(timeout=timeout)

                dialog_holder = arm_dialog_accept_once()

                toggle_label.click(force=True, timeout=timeout)
                self.click_reload_button()

                try:
                    sec_fr.wait_for_load_state("domcontentloaded", timeout=timeout)
                except Exception:
                    pass

                try:
                    self.page.wait_for_timeout(500)
                except Exception:
                    pass

                # Re-open Users page and verify the toggle is now unchecked
                ok = self.click_on_users(retries=2, timeout=timeout)
                if not ok:
                    raise AssertionError("Failed returning to Users page after disable")

                sec_fr = self.page.frame(name="Security")
                if sec_fr is None:
                    raise AssertionError("Security frame not found after disable")

                target_row = self._find_user_row(sec_fr, user_name, timeout=timeout)
                if target_row is None:
                    return False

                toggle = target_row.locator("input[type='checkbox']").first
                sleep(1)

                return toggle.count() > 0 and not toggle.is_checked()

            except Exception:
                try:
                    self.click_reload_button()
                except Exception:
                    try:
                        self.page.reload(wait_until="domcontentloaded")
                    except Exception:
                        pass

        return False

    # ✅
    def enable_user(self, user_name: str, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Enable an existing disabled user from Security -> Users table.

        New GUI: see disable_user() -- same single toggle checkbox, checking it
        instead of unchecking it.

        Returns:
            True  -> user enabled successfully
            False -> user not found, toggle not available, already enabled, or action failed
        """
        sleep(0.5)

        if not user_name:
            raise ValueError("user_name must not be empty")

        def arm_dialog_accept_once():
            holder = {"text": None}

            def _handler(dialog):
                try:
                    holder["text"] = (dialog.message or "").strip()
                except Exception:
                    holder["text"] = None

                try:
                    dialog.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

            return holder

        for _ in range(retries):
            try:
                ok = self.click_on_users(retries=2, timeout=timeout)
                if not ok:
                    raise AssertionError("click_on_users failed")

                sec_fr = self.page.frame(name="Security")
                if sec_fr is None:
                    raise AssertionError("Security frame not found")

                header = sec_fr.locator("#sec_user_header").first
                expect(header).to_be_visible(timeout=timeout)

                target_row = self._find_user_row(sec_fr, user_name, timeout=timeout)
                if target_row is None:
                    return False

                toggle = target_row.locator("input[type='checkbox']").first

                # User may already be enabled, or may not support the toggle (isSacred)
                if toggle.count() == 0:
                    return False

                if toggle.is_checked():
                    # Already enabled -- nothing to do
                    return False

                # The native checkbox is visually hidden (zero-size, custom toggle-switch
                # CSS) -- click its wrapping label instead, same as a real user would.
                toggle_label = target_row.locator("label.custom-toggle").first
                expect(toggle_label).to_be_visible(timeout=timeout)

                dialog_holder = arm_dialog_accept_once()

                toggle_label.click(force=True, timeout=timeout)
                self.click_reload_button()

                try:
                    sec_fr.wait_for_load_state("domcontentloaded", timeout=timeout)
                except Exception:
                    pass

                try:
                    self.page.wait_for_timeout(500)
                except Exception:
                    pass

                # Re-open Users page and verify the toggle is now checked
                ok = self.click_on_users(retries=2, timeout=timeout)
                if not ok:
                    raise AssertionError("Failed returning to Users page after enable")

                sec_fr = self.page.frame(name="Security")
                if sec_fr is None:
                    raise AssertionError("Security frame not found after enable")

                target_row = self._find_user_row(sec_fr, user_name, timeout=timeout)
                if target_row is None:
                    return False

                toggle = target_row.locator("input[type='checkbox']").first
                sleep(1)

                return toggle.count() > 0 and toggle.is_checked()

            except Exception:
                try:
                    self.click_reload_button()
                except Exception:
                    try:
                        self.page.reload(wait_until="domcontentloaded")
                    except Exception:
                        pass

        return False

    # ✅
    def click_reload_button(self) -> bool:
        refresh_page(self.page)
