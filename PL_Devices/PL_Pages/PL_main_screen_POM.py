from playwright.sync_api import Page, expect
from typing import Optional, Tuple


class PL_Main_Screen_POM:
    def __init__(self, page: Page):
        self.page = page

    # ==========================================================
    # Frame Helpers
    # ==========================================================

    def horizontal_menu_frame(self):
        return self.page.frame_locator("iframe[name='horizontal_menu_frame'], frame[name='horizontal_menu_frame']")

    def vertical_menu_frame(self):
        return self.page.frame_locator("iframe[name='vertical_menu_frame'], frame[name='vertical_menu_frame']")

    def main_page_frame(self):
        return self.page.frame_locator("iframe[name='main_page'], iframe#main_body")

    def security_frame(self):
        return self.page.frame(name="Security")

    def maintenance_frame(self):
        return self.main_page_frame().frame_locator("iframe[name='maint_sys'], iframe#maint_sys")

    # ==========================================================
    # Debug
    # ==========================================================

    def print_frames_debug(self):
        print("\n=== FRAME DEBUG ===")
        for i, fr in enumerate(self.page.frames):
            try:
                print(f"{i}: name='{fr.name}' url='{fr.url}'")
            except Exception:
                pass
        print("===================\n")

    # ==========================================================
    # Navigation Buttons
    # ==========================================================

    def click_system_btn(self, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Playwright version of Click_System_Btn of PacketLight GUI.
        """
        def accept_any_dialog_once() -> None:
            def _safe_accept(d):
                try:
                    d.accept()
                except Exception:
                    # Dialog was already handled by another handler
                    pass

            try:
                self.page.once("dialog", _safe_accept)
            except Exception:
                pass

        for attempt in range(retries):
            try:
                accept_any_dialog_once()

                # 1) outer frame: horizontal_menu_frame
                h_fl = self.page.frame_locator("iframe[name='horizontal_menu_frame'], frame[name='horizontal_menu_frame']")
                # 2) inner frame: box_menu
                box_fl = h_fl.frame_locator("iframe[name='box_menu'], frame[name='box_menu']")

                # 3) System button
                # In LW old UI it can be <input name="System"> or <a name="System"> etc.
                sys_btn = box_fl.locator("[name='System']").first

                expect(sys_btn).to_be_visible(timeout=timeout)
                sys_btn.scroll_into_view_if_needed()
                sys_btn.click(force=True, timeout=timeout)

                return True

            except Exception as e:
                print(f"System btn not found at the {attempt + 1} attempt: {e}")
                try:
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False

    def click_maintenance(self, retries: int = 3, timeout: int = 20_000) -> bool:
        """
        Playwright version of Click_Maintenance of PacketLight GUI.

        Returns:
            True on success, False otherwise.
        """

        def accept_any_dialog_once() -> None:
            try:
                self.page.once("dialog", lambda d: d.accept())
            except Exception:
                pass

        for attempt in range(retries):
            try:
                # accept_any_dialog_once()

                # Left menu frame
                left_fl = self.page.frame_locator("iframe[name='vertical_menu_frame'], frame[name='vertical_menu_frame']")

                maint_btn = left_fl.locator("#Maintenance").first
                expect(maint_btn).to_be_visible(timeout=timeout)

                # If it's not already active, click it
                cls = (maint_btn.get_attribute("class") or "").strip()
                if cls != "vertical_button vertical_button_active":
                    maint_btn.scroll_into_view_if_needed()
                    maint_btn.click(force=True, timeout=timeout)

                return True

            except Exception as e:
                print(f"maintenance btn fail (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(3000)  # replace selenium sleep(3)
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False

    # ==========================================================
    # Tabs
    # ==========================================================

    def device_restart(self, restart_type: str, action_dismiss: bool = False, retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
        """
        Playwright version of Device_Restart (robust against duplicate dialog handlers).

        restart_type: 'cold' | 'warm' | 'factory' | 'shutdown'
        action_dismiss:
            True  -> dismiss dialog (Cancel)
            False -> accept dialog (OK)

        Returns:
            (success, dialog_text)
                - dialog_text may be '' if another global handler accepted it first.
        """
        PRIV_WARN = "Not enough privileges"
        SERVICE_LOCK_DETECTED = "System restore to factory default is forbidden."

        rt = (restart_type or "").strip().lower()
        if rt == "cold":
            reset_id = "cold_restart"
        elif rt == "warm":
            reset_id = "warm_restart"
        elif rt == "factory":
            reset_id = "restart_factory"
        elif rt == "shutdown":
            reset_id = "shutdown"
        else:
            return False, ""

        def main_page_fl():
            return self.page.frame_locator("iframe[name='main_page'], iframe#main_body")

        def maint_sys_fl():
            # Selenium: frame name='maint_sys'
            return main_page_fl().frame_locator("iframe[name='maint_sys'], iframe#maint_sys")

        def arm_dialog_capture_once() -> dict:
            """
            Arms a ONE-TIME dialog handler that:
            - captures dialog text (if we win the race)
            - accepts/dismisses it
            MUST NOT throw if dialog already handled elsewhere.
            """
            holder = {"text": None}

            def _handler(d):
                # capture message
                try:
                    holder["text"] = (d.message or "").strip()
                except Exception:
                    holder["text"] = ""

                # handle dialog (but never crash if already handled)
                try:
                    if holder["text"] == PRIV_WARN:
                        d.accept()
                    elif action_dismiss:
                        d.dismiss()
                    else:
                        d.accept()
                except Exception:
                    # another handler might have handled it already
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

            return holder

        def wait_for_captured_dialog(holder: dict, ms: int = 5000) -> Optional[str]:
            """
            Wait up to ms for holder['text'] to be set.
            Uses Playwright timeout wait (no Python time module).
            """
            step = 50
            loops = max(1, ms // step)
            for _ in range(loops):
                if holder.get("text") is not None:
                    return holder["text"]
                self.page.wait_for_timeout(step)
            return holder.get("text")

        for attempt in range(retries):
            try:
                # Navigate using your Playwright helpers if present
                if hasattr(self, "click_system_btn"):
                    if not self.click_system_btn(timeout=timeout):
                        raise AssertionError("click_system_btn failed")

                if hasattr(self, "click_maintenance"):
                    if not self.click_maintenance(timeout=timeout):
                        raise AssertionError("click_maintenance failed")

                # Click Restart tab (main_page frame)
                restart_tab = main_page_fl().locator("#tab_restart").first
                expect(restart_tab).to_be_visible(timeout=timeout)
                restart_tab.click()
                expect(restart_tab).to_have_attribute("class", "tab tabactive", timeout=timeout)

                # Restart button is input type=image by ID
                reset_btn = maint_sys_fl().locator(f"input#{reset_id}").first
                expect(reset_btn).to_be_visible(timeout=timeout)
                reset_btn.scroll_into_view_if_needed()

                # Arm dialog capture BEFORE clicking
                dlg_holder = arm_dialog_capture_once()

                # Click
                reset_btn.click(force=True)

                # Try to capture dialog message (may be stolen by another handler)
                dlg_txt = (wait_for_captured_dialog(dlg_holder, ms=7000) or "").strip()

                # Service lock text may be in the page body
                try:
                    body = maint_sys_fl().locator("body").first
                    if body.is_visible(timeout=1000):
                        body_text = body.inner_text() or ""
                        if SERVICE_LOCK_DETECTED in body_text:
                            try:
                                if hasattr(self, "click_reload_button"):
                                    self.click_reload_button()
                            except Exception:
                                pass
                            return False, SERVICE_LOCK_DETECTED
                except Exception:
                    pass

                # Privilege warning => treat as fail even if captured
                if dlg_txt == PRIV_WARN:
                    return False, dlg_txt

                # If we didn't capture dialog text, it can STILL be OK because
                # another global handler may have already accepted/dismissed it.
                # So we consider success if the click happened and no exception thrown.
                return True, dlg_txt

            except Exception as e:
                print(f"[DBG] device_restart attempt {attempt + 1} failed: {e}")
                try:
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass
                continue

        return False, ""

    # ==========================================================
    # Generic Helpers
    # ==========================================================

    def reload(self):
        self.page.reload(wait_until="domcontentloaded")

    def accept_dialog_once(self):
        try:
            self.page.once("dialog", lambda d: d.accept())
        except Exception:
            pass

    def wait_ms(self, ms: int):
        self.page.wait_for_timeout(ms)