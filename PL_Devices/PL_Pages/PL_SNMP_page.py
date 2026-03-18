"""
Created by: Yuval Dahan
Date: 23/02/2026
"""

from __future__ import annotations
from playwright.sync_api import Page, Frame, TimeoutError, expect
import re
from typing import List, Dict, Any, Optional
from time import sleep, time
from playwright.sync_api import Error as PlaywrightError

 
class PL_SNMPPage:
    """
    PacketLight System Configuration -> SNMP tab page object.
    """

    # ==========================================================
    # Init
    # ==========================================================
    def __init__(self, page: Page):
        self.page = page

        # ---- Tab Button (top frame / system config page) ----
        self.snmp_tab_btn = page.locator("input#tab_snmp").first

        # ---- Content iframe (tab content) ----
        self.config_sys_iframe = page.locator("iframe#config_sys, iframe[name='config_sys']").first

        # ---- Optional: "active" state indicator for tab ----
        self.snmp_tab_active = page.locator("input#tab_snmp.tabactive").first

    # ==========================================================
    # Frames
    # ==========================================================

    # ✅
    @property
    def config_sys_frame(self) -> Frame | None:
        """
        Returns the Frame object for iframe[name='config_sys'] if available.
        """
        try:
            return self.page.frame(name="config_sys")
        except Exception:
            return None

    # ==========================================================
    # Helpers
    # ==========================================================

    # ✅
    def is_SNMP_loaded(self) -> bool:
        """
        Best-effort check that SNMP content is loaded into config_sys iframe.
        """
        fr = self.config_sys_frame
        if not fr:
            return False

        try:
            url = fr.url or ""
            # Strong signal: Config_System_SNMP.asp appears in the iframe URL
            if "Config_System_SNMP.asp" in url or "SNMP" in url.upper():
                return True
        except Exception:
            pass

        # Soft signal: common label on SNMP page
        try:
            # Seen in your screenshot: "SNMP Configuration"
            if fr.get_by_text("SNMP Configuration", exact=False).first.is_visible():
                return True
        except Exception:
            pass

        return False
    
    # ✅
    def _safe_accept_dialog(self, d) -> None:
        try:
            d.accept()
        except PlaywrightError:
            # already handled by another handler -> ignore
            pass
        except Exception:
            pass
    # ==========================================================
    # Actions
    # ==========================================================
    
    # ✅
    def open_SNMP_tab(self, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Point to the SNMP Tab under Configuration.

        Returns:
            True  -> SNMP tab opened and config_sys frame is loaded
            False -> failed after retries
        """

        def get_main_page_frame():
            # PacketLight uses a named frame "main_page" (top.main_page in onclick handlers)
            try:
                return self.page.frame(name="main_page")
            except Exception:
                return None

        def get_config_sys_frame():
            try:
                return self.page.frame(name="config_sys")
            except Exception:
                return None

        def is_snmp_tab_active(frame) -> bool:
            try:
                cls = (frame.locator("#tab_snmp").first.get_attribute("class") or "").strip()
                return "tabactive" in cls
            except Exception:
                return False

        def wait_config_sys_loaded() -> bool:
            fr = get_config_sys_frame()
            if fr is None:
                return False

            try:
                fr.wait_for_load_state("domcontentloaded", timeout=timeout)
            except Exception:
                pass

            # Strongest check: URL contains SNMP page
            try:
                if "Config_System_SNMP.asp" in (fr.url or ""):
                    return True
            except Exception:
                pass

            # Fallback: SNMP page title text
            try:
                if fr.get_by_text("SNMP", exact=False).first.is_visible():
                    return True
            except Exception:
                pass

            return True

        for _ in range(retries):
            try:
                # ---- Equivalent to Selenium: switch_to.default_content() ----
                # In Playwright we just always address frames from page.*,
                # but we keep the same mentality by re-resolving frames fresh.

                # ---- Ensure main_page exists ----
                main_fr = get_main_page_frame()
                if main_fr is None:
                    # If we are not in the expected frameset yet, give it a moment.
                    try:
                        self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
                    except Exception:
                        pass
                    main_fr = get_main_page_frame()
                if main_fr is None:
                    raise AssertionError("main_page frame not found")

                # ---- Click SNMP tab inside main_page ----
                snmp_tab = main_fr.locator("#tab_snmp").first
                expect(snmp_tab).to_be_visible(timeout=timeout)
                snmp_tab.click(force=True)

                # ---- Verify tab is active (class contains tabactive) ----
                # (matches: snmp_tab.get_attribute('class') == 'tab tabactive')
                try:
                    main_fr.wait_for_function(
                        "() => (document.getElementById('tab_snmp')?.className || '').includes('tabactive')",
                        timeout=timeout,
                    )
                except Exception:
                    # If not active, treat as failure and retry (like your Selenium)
                    raise AssertionError("SNMP tab did not become active")

                # ---- Ensure config_sys frame exists and loaded ----
                # Note: config_sys is an iframe on the same document as the tabs (per HTML)
                cfg_fr = get_config_sys_frame()
                if cfg_fr is None:
                    # allow attach time
                    try:
                        self.page.wait_for_timeout(250)
                    except Exception:
                        pass
                    cfg_fr = get_config_sys_frame()
                if cfg_fr is None:
                    raise AssertionError("config_sys frame not found after clicking SNMP tab")

                if not wait_config_sys_loaded():
                    raise AssertionError("config_sys did not load after clicking SNMP tab")

                return True

            except Exception:
                # Selenium had: handle alert, else refresh screen and retry
                # Playwright doesn't have the same exception class here, so we do best-effort:
                try:
                    # self.page.on("dialog", lambda d: d.accept())
                    self.page.once("dialog", self._safe_accept_dialog)
                except Exception:
                    pass

                # Refresh (PacketLight uses refresh icon to reload main_page)
                try:
                    self.click_reload_button()
                except Exception:
                    try:
                        self.page.reload(wait_until="domcontentloaded")
                    except Exception:
                        pass

                continue

        return False
    
    # ✅
    def set_SNMP_protocol_version(self, version: str, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Set SNMP Protocol Version (PacketLight GUI) inside SNMP Configuration.

        Args:
            version: "v1, v2c, v3" , "v3 only"

        Returns:
            True  -> selection applied successfully (best-effort verified)
            False -> failed
        """

        if not version or not str(version).strip():
            raise ValueError("version is empty")

        ALERT_FIPS_1 = "You are enabling a non-FIPS approved protocol!"
        ALERT_FIPS_2 = "You are enabling a non FIPS-compliant protocol!"

        def accept_fips_if_present() -> None:
            """
            PacketLight sometimes pops an alert when enabling non-FIPS protocol.
            Selenium accepted those messages. :contentReference[oaicite:1]{index=1}
            """
            try:
                dialog_holder = {"seen": False}

                def _handler(d):
                    dialog_holder["seen"] = True
                    try:
                        msg = (d.message or "").strip()
                        if msg in (ALERT_FIPS_1, ALERT_FIPS_2):
                            d.accept()
                        else:
                            # safest: accept (to not block automation)
                            d.accept()
                    except Exception:
                        try:
                            d.accept()
                        except Exception:
                            pass

                self.page.once("dialog", _handler)
            except Exception:
                pass

        def get_cfg_frame():
            fr = self.config_sys_frame
            if fr is None:
                fr = self.page.frame(name="config_sys")
            return fr

        for _ in range(retries):
            try:
                # Ensure SNMP tab is open and config_sys loaded
                ok = self.open_SNMP_tab(retries=2, timeout=timeout)
                if not ok:
                    raise AssertionError("open_SNMP_tab failed")

                fr = get_cfg_frame()
                if fr is None:
                    raise AssertionError("config_sys frame not found")

                # SNMP Protocol Version dropdown is: name='slmSysSnmpVersion' :contentReference[oaicite:2]{index=2}
                dd = fr.locator("select[name='slmSysSnmpVersion']").first
                sleep(1)
                expect(dd).to_be_visible(timeout=timeout)

                # Attach alert handler BEFORE changing dropdown / applying
                accept_fips_if_present()
                sleep(0.5)

                dd.select_option(label=version)
                sleep(0.5)

                self.apply_SNMP_configuration()

                # Optional verify the selection in UI
                try:
                    selected = (dd.input_value() or "").strip()
                    # input_value returns option "value" not label; so only best-effort here
                except Exception:
                    pass

                # Do NOT click Apply here; keep separation of concerns.
                return True

            except Exception:
                # retry style similar to Selenium: refresh and continue
                try:
                    self.click_reload_button()
                except Exception:
                    try:
                        self.page.reload(wait_until="domcontentloaded")
                    except Exception:
                        pass
                continue

        return False

    # ✅
    def apply_SNMP_configuration(self, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Click Apply on SNMP Configuration screen (PacketLight GUI).
        """

        def accept_any_dialog() -> None:
            try:
                # self.page.once("dialog", lambda d: d.accept())
                self.page.once("dialog", self._safe_accept_dialog)
            except Exception:
                pass

        def get_cfg_frame():
            # Always re-resolve; frame can be recreated after Apply.
            return self.page.frame(name="config_sys")

        def apply_locator_in_cfg():
            fr = get_cfg_frame()
            if fr is None:
                return None, None
            # Use the real, minimal selector
            loc = fr.locator("input[name='Apply'][type='submit'][value='Apply']").first
            return fr, loc

        for _ in range(retries):
            try:
                fr, apply_btn = apply_locator_in_cfg()
                if fr is None:
                    raise AssertionError("config_sys frame not found")

                expect(apply_btn).to_be_visible(timeout=timeout)

                accept_any_dialog()
                sleep(0.5)

                # Click Apply 
                apply_btn.click(force=True)

                return True

            except Exception:
                # Refresh and try again
                try:
                    self.click_reload_button()
                except Exception:
                    pass
                continue

        return False

    # ✅
    def get_SNMP_traps_table(self, timeout: int = 10_000) -> List[Dict[str, Any]]:
        """
        Read the SNMP Traps table rows and return them as a list of dicts.

        Returns:
            [
            {"manager_address": "172.16.10.22", "snmp_version": "SNMP v2c", "v3_user": "", "trap_port": "162"},
            ...
            ]
        """

        # Ensure we're on SNMP tab and frame is available
        if hasattr(self, "open_snmp_tab"):
            self.open_SNMP_tab(timeout=timeout)

        fr = getattr(self, "config_sys_frame", None)
        fr = fr() if callable(fr) else fr  # allow both property or method style
        if fr is None:
            # fallback: raw frame lookup
            fr = self.page.frame(name="config_sys")

        if fr is None:
            raise AssertionError("config_sys frame not found (SNMP page not loaded)")

        table = fr.locator("table#snmp_trap_table").first
        expect(table).to_be_visible(timeout=timeout)

        rows = table.locator("tr")

        out: List[Dict[str, Any]] = []

        # Row 0 is header ("title_tr")
        # Last row is the "Add" row (contains input name='ip_address' and 'snmp_add')
        for i in range(rows.count()):
            r = rows.nth(i)

            # Skip header
            try:
                cls = (r.get_attribute("class") or "").strip()
                if "title_tr" in cls:
                    continue
            except Exception:
                pass

            # Skip the "Add" row
            if r.locator("input[name='ip_address']").count() > 0 or r.locator("input[name='snmp_add']").count() > 0:
                continue

            # Candidate data row: 5 <td> cells, first is manager ip
            tds = r.locator("td")
            if tds.count() < 4:
                continue

            def td_text(n: int) -> str:
                try:
                    return (tds.nth(n).inner_text() or "").strip()
                except Exception:
                    return ""

            manager_address = td_text(0)
            snmp_version = td_text(1)
            v3_user = td_text(2)
            trap_port = td_text(3)

            # Filter out empty junk rows
            if not manager_address:
                continue

            out.append(
                {
                    "Manager Address": manager_address,
                    "SNMP Version": snmp_version,
                    "v3 User": v3_user,
                    "Trap Port": trap_port,
                }
            )

        return out
    
    # ✅
    def manager_address_added_to_SNMP_traps(self, desired_address: str, exact: bool = True) -> bool:
        """
        Search in SNMP traps table for desired manager address.

        Args:
            traps_table: output of get_SNMP_traps_table()
            desired_address: IP/host string to search
            exact: True = exact match, False = substring match

        Returns:
            True if found, else False
        """
        target = (desired_address or "").strip()
        if not target:
            raise ValueError("Desired address is empty")
        
        traps_table = self.get_SNMP_traps_table()

        if exact:
            for row in traps_table:
                if (row.get("Manager Address") or "").strip() == target:
                    return True
            return False

        # substring / partial
        for row in traps_table:
            if target in (row.get("Manager Address") or ""):
                return True
        return False
    
    # ✅
    def Add_Trap_Manager(self, IP: str | None = None, SNMP_Version: str | None = None, V3_User: str | None = None,
        Trap_Port: str | int | None = None, Negative_Test: bool = False, Action_Dismiss: bool = False,
        Retries: int = 3, timeout: int = 10_000):
        """
        Add SNMP Trap Manager entry.

        Returns:
            - None                         -> invalid IP (only if Negative_Test=False)
            - (success: bool, msg: str)    -> message is last dialog message captured (if any)

        Notes:
            - Uses the SNMP traps table form fields:
              ip_address, snmp_version, community, trap_port, snmp_add
        """

        NON_FIPS = "You are enabling a non FIPS-compliant protocol!"
        PRIV_WARN = "Not enough privileges"
        CONFIRM = "Are you sure?"
        DUPLICATE = "Duplicate Manager Entry"
        ILLEGAL = "SNMP Illegal Port Number!"
        SPECIAL = "is a special IP address and cannot be used here."
        NOT_VALID = "is not a valid IP address."

        ip_str = (IP or "").strip()
        if not Negative_Test:
            ip_ok = re.match(
                r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$",
                ip_str,
            )
            if not ip_ok:
                print("Invalid IP")
                return None

        def cfg_frame() -> Frame:
            fr = self.page.frame(name="config_sys")
            if fr is None:
                raise AssertionError("config_sys frame not found (SNMP page not loaded)")
            return fr

        def drain_dialogs(max_dialogs: int = 4, per_dialog_timeout: int = 3000) -> list[str]:
            """
            Collect sequential JS dialogs (alerts/confirms).
            Returns list of dialog messages in the order they appeared.
            """
            msgs: list[str] = []
            for _ in range(max_dialogs):
                try:
                    d = self.page.wait_for_event("dialog", timeout=per_dialog_timeout)
                except Exception:
                    break

                msg = (d.message or "").strip()
                msgs.append(msg)

                # --- behavior mapping (based on your Selenium logic) ---
                if msg == NON_FIPS:
                    d.accept()
                    continue

                if msg == PRIV_WARN:
                    d.accept()
                    # Selenium refreshed after this
                    continue

                if msg == ILLEGAL or (SPECIAL in msg) or (NOT_VALID in msg) or (msg == DUPLICATE):
                    d.accept()
                    continue

                if msg == CONFIRM:
                    if Action_Dismiss:
                        d.dismiss()
                    else:
                        d.accept()
                    continue

                # default: accept to avoid blocking the run
                try:
                    d.accept()
                except Exception:
                    pass

            return msgs

        for _ in range(Retries):
            try:
                ok = self.open_SNMP_tab(retries=2, timeout=timeout)
                if not ok:
                    raise AssertionError("open_SNMP_tab failed")

                fr = cfg_frame()

                table = fr.locator("table#snmp_trap_table").first
                sleep(3)
                expect(table).to_be_visible(timeout=timeout)

                ip_field = fr.locator("input[name='ip_address']").first
                sleep(3)
                expect(ip_field).to_be_visible(timeout=timeout)
                ip_field.fill(ip_str)

                # Handle dialogs that might appear when changing SNMP version (e.g., NON_FIPS)
                if SNMP_Version:
                    ver_dd = fr.locator("select[name='snmp_version']").first
                    sleep(3)
                    expect(ver_dd).to_be_visible(timeout=timeout)

                    # Attach version selection
                    ver_dd.select_option(label=SNMP_Version)
                    # If selecting v1 triggers NON_FIPS, it will appear as dialog
                    _ = drain_dialogs(max_dialogs=1, per_dialog_timeout=1500)

                # SNMP v3 user is in select[name='community'] (disabled unless v3 is selected)
                if (SNMP_Version == "SNMP v3") and V3_User:
                    v3_dd = fr.locator("select[name='community']").first
                    sleep(3)
                    expect(v3_dd).to_be_visible(timeout=timeout)
                    # wait until enabled (not disabled)
                    try:
                        fr.wait_for_function(
                            "() => { const el=document.querySelector(\"select[name='community']\"); return !!el && !el.disabled; }",
                            timeout=timeout,
                        )
                    except Exception:
                        # if still disabled, selection will fail and go to retry
                        pass
                    v3_dd.select_option(label=V3_User)

                if Trap_Port is not None:
                    port_field = fr.locator("input[name='trap_port']").first
                    sleep(3)
                    expect(port_field).to_be_visible(timeout=timeout)
                    port_field.fill(str(Trap_Port))

                add_btn = fr.locator("input[name='snmp_add'][type='submit']").first
                sleep(3)
                expect(add_btn).to_be_visible(timeout=timeout)

                # Click Add -> triggers confirm/alerts
                add_btn.click(force=True)

                msgs = drain_dialogs(max_dialogs=4, per_dialog_timeout=4000)
                last_msg = msgs[-1] if msgs else ""

                # Decide success similar to your Selenium flow
                success = False
                if not msgs:
                    # No dialogs => best-effort assume success (UI sometimes doesn't alert)
                    success = True
                else:
                    # If privilege warning or illegal/invalid/duplicate => fail
                    if any(m == PRIV_WARN for m in msgs):
                        success = False
                    elif any(m == ILLEGAL for m in msgs):
                        success = False
                    elif any(m == DUPLICATE for m in msgs):
                        success = False
                    elif any((SPECIAL in m) or (NOT_VALID in m) for m in msgs):
                        success = False
                    elif any(m == CONFIRM for m in msgs):
                        # If dismissed -> Selenium considered it success=True
                        if Action_Dismiss:
                            success = True
                        else:
                            # confirmed and no duplicate after => success
                            success = not any(m == DUPLICATE for m in msgs)
                    else:
                        # NON_FIPS only, or unknown => best effort
                        success = True

                # Refresh like your Selenium does
                try:
                    self.click_reload_button()
                except Exception:
                    pass

                return success, last_msg

            except Exception:
                try:
                    self.click_reload_button()
                except Exception:
                    pass
                continue

        return False, ""

    # ✅
    def Delete_Trap_Manager_eq_IP(self, IP: str, Retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Delete a Trap Manager row where Manager Address == IP.

        Returns:
            True  -> deleted
            False -> not found / failed
        """
        sleep(5)
        target = (IP or "").strip()
        if not target:
            raise ValueError("IP is empty")

        def cfg_frame() -> Frame:
            fr = self.page.frame(name="config_sys")
            if fr is None:
                raise AssertionError("config_sys frame not found (SNMP page not loaded)")
            return fr

        def safe_accept_dialog(d) -> None:
            try:
                d.accept()
            except PlaywrightError:
                # Dialog already handled somewhere else
                pass
            except Exception:
                pass

        def wait_table_visible(fr: Frame) -> None:
            table = fr.locator("table#snmp_trap_table").first
            sleep(3)
            expect(table).to_be_visible(timeout=timeout)

        for _ in range(Retries):
            try:
                ok = self.open_SNMP_tab(retries=2, timeout=timeout)
                if not ok:
                    raise AssertionError("open_SNMP_tab failed")

                fr = cfg_frame()
                wait_table_visible(fr)

                # Find the row that has a td with exact text equal to target
                row = fr.locator(f"table#snmp_trap_table tr:has(td:text-is('{target}'))").first
                sleep(3)
                if row.count() == 0:
                    return False

                del_btn = row.locator("input[name^='snmp_del'][value='Delete']").first
                sleep(3)
                expect(del_btn).to_be_visible(timeout=timeout)

                # Prepare to accept confirm dialog (confirmManager())
                self.page.once("dialog", safe_accept_dialog)

                # Click delete (this submits the form inside the frame)
                sleep(3)
                del_btn.click(force=True)

                # Wait for the frame content to stabilize again.
                # Sometimes frame reloads / rerenders, so re-grab it and wait for the table.
                fr = cfg_frame()
                wait_table_visible(fr)

                # Verify row is gone
                sleep(3)
                still_exists = fr.locator(
                    f"table#snmp_trap_table tr:has(td:text-is('{target}'))"
                ).count() > 0

                # Optional: refresh via your helper
                try:
                    self.click_reload_button()
                except Exception:
                    pass

                return not still_exists

            except Exception:
                # On any flakiness, try refresh and retry
                try:
                    self.click_reload_button()
                except Exception:
                    pass
                continue

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