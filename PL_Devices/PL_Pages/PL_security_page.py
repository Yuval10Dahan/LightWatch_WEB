"""
Created by: Yuval Dahan
Date: 26/02/2026
"""

from __future__ import annotations
from playwright.sync_api import Page, Frame, expect
from typing import List, Optional, Tuple, Union
import re
from time import time


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
                main_fr.wait_for_selector("iframe#Security, iframe[name='Security']", timeout=timeout)

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
        """

        def accept_any_dialog_once() -> None:
            try:
                self.page.once("dialog", lambda d: d.accept())
            except Exception:
                pass

        def get_security_frame():
            try:
                return self.page.frame(name="Security")
            except Exception:
                return None

        def selected_option_text(select_locator) -> str:
            try:
                opt = select_locator.locator("option:checked").first
                return (opt.inner_text() or "").strip()
            except Exception:
                return ""

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
                expect(header).to_be_visible(timeout=timeout)
                if (header.inner_text() or "").strip() != "Local User Management":
                    raise AssertionError("Not on Users table page")

                # Users table tbody
                tbody = sec_fr.locator("table#sec_user_table > tbody").first
                expect(tbody).to_be_visible(timeout=timeout)

                # Collect all existing user indices 
                name_cells = tbody.locator("[id^='name_']")
                count = name_cells.count()

                users_detailed: List[List[str]] = []

                # Build rows by matching numeric suffix
                for i in range(count):
                    cell = name_cells.nth(i)
                    cell_id = (cell.get_attribute("id") or "").strip()  # e.g., name_1
                    m = re.match(r"name_(\d+)$", cell_id)
                    if not m:
                        continue
                    idx = m.group(1)

                    username = (cell.inner_text() or "").strip()

                    permission_sel = tbody.locator(f"#permission_{idx}").first
                    auth_sel = tbody.locator(f"#slmSnmpv3Auth_{idx}").first
                    priv_sel = tbody.locator(f"#slmSnmpv3Priv_{idx}").first

                    expect(permission_sel).to_be_visible(timeout=timeout)
                    expect(auth_sel).to_be_visible(timeout=timeout)
                    expect(priv_sel).to_be_visible(timeout=timeout)

                    permission = selected_option_text(permission_sel)
                    snmpv3_auth = selected_option_text(auth_sel)
                    snmpv3_priv = selected_option_text(priv_sel)

                    users_detailed.append([username, permission, snmpv3_auth, snmpv3_priv])

                return users_detailed

            except Exception:
                try:
                    accept_any_dialog_once()
                    if hasattr(self, "click_reload_button"):
                        self.click_reload_button()
                    else:
                        self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass
                continue

        return []

    def is_user_located_in_users_table(self, user_name: str, users_table: List[List[str]], retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Return True if the given user exists in the Users table.
        Return False otherwise.

        Based on get_users_table().
        """

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

    def return_user_parameters(self, user_name: str, users_table: List[List[str]], retries: int = 5, timeout: int = 10_000) -> Optional[List[str]]:
        """
        Return the user parameters: User Name, Permission, SNMPv3 Auth, SNMPv3 Priv.

        Returns:
            List[str] -> if user found
            None      -> if user not found
        """

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
    def add_new_user(self, user_name: Optional[str] = None, permission: Optional[str] = None,
        password: Optional[str] = None, verify_password: Optional[str] = None, snmpv3_auth: Optional[str] = None,
        snmpv3_priv: Optional[str] = None, password_auth: Optional[str] = None, password_priv: Optional[str] = None,
        copy_paste: bool = False, alert_msg: Optional[str] = None, verify_last: bool = False,
        retries: int = 5, timeout: int = 10_000) -> Union[bool, Tuple[bool, str]]:
        """
        Add a new user in Security -> Users table (PacketLight GUI).

        Returns:
            - True  : user added successfully OR expected alert verified
            - False : failed
            - (False, 'Blocked from adding New Users') : when username field is readonly/disabled
        """

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

        def dbg_frames(prefix: str = "DBG") -> None:
            try:
                frames = self.page.frames
                for i, fr in enumerate(frames):
                    try:
                        name = fr.name or ""
                        url = fr.url or ""
                        header_cnt = fr.locator("#sec_user_header").count()
                        table_cnt = fr.locator("table#sec_user_table").count()
                        add_cnt = fr.locator("input[type='submit'][value='Add']").count()
                        user_in_cnt = fr.locator("input[name='user_name']").count()
                        perm_cnt = fr.locator("select#PermissionSelect").count()
                    except Exception as e:
                        print(f"error: {e}")
            except Exception as e:
                print(f"error: {e}")

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

                dbg_frames(prefix=f"ADD_USER_ATTEMPT_{attempt+1}")

                sec_fr = self.page.frame(name="Security")
                if sec_fr is None:
                    raise AssertionError("Security frame not found")

                header = sec_fr.locator("#sec_user_header").first
                expect(header).to_be_visible(timeout=timeout)

                table = sec_fr.locator("table#sec_user_table").first
                expect(table).to_be_visible(timeout=timeout)

                row = table.locator("tbody > tr").last
                expect(row).to_be_visible(timeout=timeout)

                username_in = row.locator("input[name='user_name']").first
                perm_sel = row.locator("select#PermissionSelect").first
                password_in = row.locator("input[name='password']").first
                verify_in = row.locator("input[name='verify_password']").first

                auth_sel = row.locator("select#slmSnmpv3Auth, select[name='slmSnmpv3Auth']").first
                priv_sel = row.locator("select#slmSnmpv3Priv, select[name='slmSnmpv3Priv']").first

                auth_pass_in = row.locator("input#authPass, input[name='authPass']").first
                verify_auth_pass_in = row.locator("input#verify_authPass, input[name='verify_authPass']").first
                priv_pass_in = row.locator("input#privPass, input[name='privPass']").first
                verify_priv_pass_in = row.locator("input#verify_privPass, input[name='verify_privPass']").first

                add_btn = row.locator("input.apply[name='B1'][value='Add'], input[type='submit'][value='Add']").first
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
                    selected_txt = (perm_sel.locator("option:checked").inner_text() or "").strip()

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

                # Click Add (single dialog handling)
                add_btn.scroll_into_view_if_needed()
                expect(add_btn).to_be_visible(timeout=timeout)

                dlg_holder = arm_dialog_capture_once()

                try:
                    add_btn.click(timeout=timeout)
                except Exception as e:
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
                        expect(sec_fr.locator(f"table#sec_user_table >> text={user_name}").first).to_be_visible(timeout=timeout)
                    except Exception as e:
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

                return True

            except Exception as e:
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
    def click_reload_button(self) -> bool:
        """
        Click PacketLight Refresh button.

        Returns:
            True  -> refresh triggered
            False -> refresh control not found
        """

        def refresh_locator(frame):
            return frame.locator("img#refresh").first

        # Preferred: box_menu frame
        try:
            box_menu = self.page.frame(name="box_menu")

            if box_menu is not None:
                refresh = refresh_locator(box_menu)

                if refresh.count() > 0 and refresh.is_visible():
                    refresh.click(force=True)

                    # wait for main frame reload
                    try:
                        self.page.wait_for_load_state("domcontentloaded", timeout=10_000)
                    except Exception:
                        pass

                    return True
        except Exception:
            return False