'''
Created by: Yuval Dahan
Date: 03/03/2026
'''


from playwright.sync_api import Page, expect
from typing import Optional, Tuple
from PL_Devices.PL_Pages.PL_upper_panel import PL_Upper_Panel
from time import sleep
import re


class PL_Main_Screen_POM:
    def __init__(self, page: Page):
        self.page = page
        self.upper_panel = PL_Upper_Panel(page)

    # ==========================================================
    # Frame Helpers
    # ==========================================================

    # ✅
    def horizontal_menu_frame(self):
        frame_loc = self.page.frame_locator("iframe[name='horizontal_menu_frame'], frame[name='horizontal_menu_frame']")
        sleep(1)
        return frame_loc

    # ✅
    def vertical_menu_frame(self):
        frame_loc = self.page.frame_locator("iframe[name='vertical_menu_frame'], frame[name='vertical_menu_frame']")
        sleep(1)
        return frame_loc

    # ✅
    def main_page_frame(self):
        frame_loc = self.page.frame_locator("iframe[name='main_page'], iframe#main_body")
        sleep(1)
        return frame_loc

    # ✅
    def security_frame(self):
        return self.page.frame(name="Security")

    # ✅
    def maintenance_frame(self):
        frame_loc = self.main_page_frame().frame_locator("iframe[name='maint_sys'], iframe#maint_sys")
        sleep(1)
        return frame_loc

    # ==========================================================
    # Navigation Buttons 
    # ==========================================================

    # ✅
    def click_Fault(self, retries: int = 3, timeout: int = 20_000) -> bool:
        for attempt in range(retries):
            try:
                left_fl = self.page.frame_locator("iframe[name='vertical_menu_frame'], frame[name='vertical_menu_frame']")
                btn = left_fl.locator("#Fault").first

                expect(btn).to_be_visible(timeout=timeout)

                cls = (btn.get_attribute("class") or "").strip()
                if cls != "vertical_button vertical_button_active":
                    btn.scroll_into_view_if_needed()
                    btn.click(force=True, timeout=timeout)

                return True

            except Exception as e:
                print(f"Fault btn fail (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(3000)
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False

    # ✅
    def click_Configuration(self, retries: int = 3, timeout: int = 20_000) -> bool:
        for attempt in range(retries):
            try:
                left_fl = self.page.frame_locator("iframe[name='vertical_menu_frame'], frame[name='vertical_menu_frame']")
                sleep(1)
                btn = left_fl.locator("#Configuration").first
                sleep(1)

                expect(btn).to_be_visible(timeout=timeout)

                cls = (btn.get_attribute("class") or "").strip()
                if cls != "vertical_button vertical_button_active":
                    btn.scroll_into_view_if_needed()
                    btn.click(force=True, timeout=timeout)

                return True

            except Exception as e:
                print(f"Configuration btn fail (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(3000)
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False

    # ✅
    def click_Performance(self, retries: int = 3, timeout: int = 20_000) -> bool:
        for attempt in range(retries):
            try:
                left_fl = self.page.frame_locator("iframe[name='vertical_menu_frame'], frame[name='vertical_menu_frame']")
                btn = left_fl.locator("#Performance").first

                expect(btn).to_be_visible(timeout=timeout)

                cls = (btn.get_attribute("class") or "").strip()
                if cls != "vertical_button vertical_button_active":
                    btn.scroll_into_view_if_needed()
                    btn.click(force=True, timeout=timeout)

                return True

            except Exception as e:
                print(f"Performance btn fail (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(3000)
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False

    # ✅
    def click_Security(self, retries: int = 3, timeout: int = 20_000) -> bool:
        for attempt in range(retries):
            try:
                left_fl = self.page.frame_locator("iframe[name='vertical_menu_frame'], frame[name='vertical_menu_frame']")
                btn = left_fl.locator("#Security").first

                expect(btn).to_be_visible(timeout=timeout)

                cls = (btn.get_attribute("class") or "").strip()
                if cls != "vertical_button vertical_button_active":
                    btn.scroll_into_view_if_needed()
                    btn.click(force=True, timeout=timeout)

                return True

            except Exception as e:
                print(f"Security btn fail (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(3000)
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False
 
    # ✅
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
    # Fault Tab
    # ==========================================================

    # ✅
    def click_Alarms(self, retries: int = 3, timeout: int = 20_000) -> bool:
        self.click_Fault(timeout=timeout)  # Ensure we're on the Fault page
        for attempt in range(retries):
            try:
                main_fl = self.main_page_frame()
                btn = main_fl.locator("#tab_alarms").first

                expect(btn).to_be_visible(timeout=timeout)

                cls = (btn.get_attribute("class") or "").strip()
                if cls != "tab tabactive":
                    btn.scroll_into_view_if_needed()
                    btn.click(force=True, timeout=timeout)

                return True

            except Exception as e:
                # print(f"Alarms tab fail (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(3000)
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False

    # ✅
    def click_Events(self, retries: int = 3, timeout: int = 20_000) -> bool:
        self.click_Fault(timeout=timeout)  # Ensure we're on the Fault page
        for attempt in range(retries):
            try:
                main_fl = self.main_page_frame()
                btn = main_fl.locator("#tab_events").first

                expect(btn).to_be_visible(timeout=timeout)

                cls = (btn.get_attribute("class") or "").strip()
                if cls != "tab tabactive":
                    btn.scroll_into_view_if_needed()
                    btn.click(force=True, timeout=timeout)

                return True

            except Exception as e:
                # print(f"Events tab fail (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(3000)
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False

    # ✅
    def click_Configuration_Changes(self, retries: int = 3, timeout: int = 20_000) -> bool:
        self.click_Fault(timeout=timeout)  # Ensure we're on the Fault page
        for attempt in range(retries):
            try:
                main_fl = self.main_page_frame()
                btn = main_fl.locator("#tab_config_changes").first

                expect(btn).to_be_visible(timeout=timeout)

                cls = (btn.get_attribute("class") or "").strip()
                if cls != "tab tabactive":
                    btn.scroll_into_view_if_needed()
                    btn.click(force=True, timeout=timeout)

                return True

            except Exception as e:
                # print(f"Configuration Changes tab fail (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(3000)
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False

    # ✅
    def alarms_table(self, retries: int = 3, timeout: int = 20_000):
        """
        Returns the alarms table as a list of rows.

        Each row is returned as:
            [date_time, source, severity, message, note]

        Example:
            [
                ['3/12/2026 1:42:31 PM', 'Port 4', 'Minor', 'FarLCS (Far-end Loss of Client Signal)', 'S.A.'],
                ['3/12/2026 3:32:38 PM', 'Port 4', 'Critical', 'Optics Loss of Light', 'S.A.'],
            ]
        """
        self.click_Alarms(retries=retries, timeout=timeout)
        sleep(0.5)

        for attempt in range(retries):
            try:
                fault_table = (self.main_page_frame().frame_locator("iframe[name='faults'], iframe#faults").locator("#faultTab"))
                sleep(0.5)

                expect(fault_table).to_be_visible(timeout=timeout)

                rows = fault_table.locator("tbody tr")
                sleep(0.5)
                row_count = rows.count()

                alarms_table = []

                for i in range(row_count):
                    row = rows.nth(i)
                    cells = row.locator("td")
                    sleep(0.5)
                    cell_count = cells.count()

                    row_data = []
                    for j in range(cell_count):
                        text = cells.nth(j).inner_text().replace("\xa0", " ").strip()
                        row_data.append(text)

                    if row_data:
                        alarms_table.append(row_data)

                return alarms_table

            except Exception as e:
                # print(f"get_alarms_table failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(3000)
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return []

    # ✅
    def get_alarms_table(self, button_or_port: str, retries: int = 3, timeout: int = 20_000):
        """
        Gets the alarms table after clicking a button or port in the upper panel.

        button_or_port: 'System' / 'ALL' / '1' / '2' / '3' / ... / MNG 1 / MNG 2 / ETH 1 / ETH 2 / ...

        Returns:
            List of rows, where each row is a list of cell texts.
        """
        self.click_Fault(timeout=timeout)
        sleep(0.5)

        if isinstance(button_or_port, str):
            btn = button_or_port.strip().lower()
            if btn == "system":
                if not self.upper_panel.click_system(timeout=timeout):
                    print("Failed to click System button")
                    return []
            elif btn == "all":
                if not self.upper_panel.click_all(timeout=timeout):
                    print("Failed to click ALL button")
                    return []
            else:
                if not self.upper_panel.click_port(button_or_port, timeout=timeout):
                    print(f"Failed to click {button_or_port} button")
                    return []
        else:
            print(f"Invalid type for button_or_port: {type(button_or_port)}")
            return []
        
        sleep(0.5)

        # After clicking, get the alarms table
        return self.alarms_table(retries=retries, timeout=timeout)
        
    # ✅
    def events_table(self, retries: int = 3, timeout: int = 20_000):
        """
        Returns the events table as a list of rows.

        Each row is returned as:
            [date_time, source, severity, message, note]
        """
        self.click_Events(retries=retries, timeout=timeout)
        sleep(0.5)

        for attempt in range(retries):
            try:
                fault_table = (self.main_page_frame().frame_locator("iframe[name='faults'], iframe#faults").locator("#faultTab"))
                sleep(0.5)

                expect(fault_table).to_be_visible(timeout=timeout)

                rows = fault_table.locator("tbody tr")
                sleep(0.5)
                row_count = rows.count()

                events_table = []

                for i in range(row_count):
                    row = rows.nth(i)
                    cells = row.locator("td")
                    sleep(0.5)
                    cell_count = cells.count()

                    row_data = []
                    for j in range(cell_count):
                        text = cells.nth(j).inner_text().replace("\xa0", " ").strip()
                        row_data.append(text)

                    if row_data:
                        events_table.append(row_data)

                return events_table

            except Exception as e:
                # print(f"events_table failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(3000)
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return []

    # ✅
    def get_events_table(self, button_or_port: str, retries: int = 3, timeout: int = 20_000):
        """
        Gets the events table after clicking a button or port in the upper panel.

        button_or_port: 'System' / 'ALL' / '1' / '2' / ... / MNG 1 / ETH 1 / etc.

        Returns:
            List of rows
        """
        self.click_Fault(timeout=timeout)
        sleep(0.5)

        if isinstance(button_or_port, str):
            btn = button_or_port.strip().lower()

            if btn == "system":
                if not self.upper_panel.click_system(timeout=timeout):
                    print("Failed to click System button")
                    return []

            elif btn == "all":
                if not self.upper_panel.click_all(timeout=timeout):
                    print("Failed to click ALL button")
                    return []

            else:
                if not self.upper_panel.click_port(button_or_port, timeout=timeout):
                    print(f"Failed to click {button_or_port} button")
                    return []
        else:
            print(f"Invalid type for button_or_port: {type(button_or_port)}")
            return []

        sleep(0.5)

        return self.events_table(retries=retries, timeout=timeout)

    # ==========================================================
    # Configuration Tab
    # ==========================================================

    # ✅
    def click_time(self, retries: int = 3, timeout: int = 20_000) -> bool:
        """
        Click the Time tab under Configuration -> System.

        Returns:
            True on success, False otherwise.
        """

        for attempt in range(retries):
            try:
                if not self.click_Configuration(timeout=timeout):
                    raise Exception("click_Configuration failed")

                if not self.upper_panel.click_system(timeout=timeout):
                    raise Exception("upper_panel.click_system failed")

                self.page.wait_for_timeout(500)

                main_fl = self.main_page_frame()

                btn = main_fl.locator("#tab_time").first
                expect(btn).to_be_visible(timeout=timeout)

                cls = (btn.get_attribute("class") or "").strip()
                if cls != "tab tabactive":
                    btn.scroll_into_view_if_needed()
                    btn.click(force=True, timeout=timeout)

                expect(btn).to_have_attribute("class", "tab tabactive", timeout=timeout)

                return True

            except Exception as e:
                print(f"click_time failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return False

    # ✅
    def set_chassis_id(self, chassis_id, retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
        """
        Set the Chassis ID under Configuration -> System -> General.

        Args:
            chassis_id:
                Integer/string value between 0 and 10000.

        Returns:
            tuple[bool, str]:
                (success, alert_text)

                success:
                    True  -> operation completed successfully
                    False -> operation failed

                alert_text:
                    Browser alert text if an alert appeared, otherwise "".
        """

        try:
            if chassis_id is None:
                chassis_id = ""

            if chassis_id == "" or chassis_id == " ":
                chassis_id = "0"

            chassis_id_str = str(chassis_id).strip()
            chassis_id_int = int(chassis_id_str)
            if chassis_id_int < 0 or chassis_id_int > 10000:
                return False, "Please specify chassis Id between 1 and 10000, or 0 for non multi-chassis"
        except Exception:
            return False, "Please specify chassis Id between 1 and 10000, or 0 for non multi-chassis"

        def config_system_frame():
            fr = self.page.frame(name="config_sys")
            if fr is None:
                raise AssertionError("config_sys frame not found")
            return fr

        def arm_dialog_capture_once(holder: dict):
            def _handler(d):
                try:
                    holder["text"] = (d.message or "").strip()
                except Exception:
                    holder["text"] = ""

                try:
                    d.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

        def wait_for_dialog_text(holder: dict, ms: int = 3000) -> str:
            step = 50
            loops = max(1, ms // step)
            for _ in range(loops):
                if holder.get("text") is not None:
                    return holder.get("text") or ""
                self.page.wait_for_timeout(step)
            return holder.get("text") or ""

        for attempt in range(retries):
            try:
                if not self.click_Configuration(timeout=timeout):
                    raise Exception("click_Configuration failed")

                if not self.upper_panel.click_system(timeout=timeout):
                    raise Exception("upper_panel.click_system failed")

                self.page.wait_for_timeout(500)

                cfg = config_system_frame()

                chassis_input = cfg.locator("input[name='slmSysChassisId']").first
                expect(chassis_input).to_be_visible(timeout=timeout)

                current_value = (chassis_input.input_value() or "").strip()
                if current_value == chassis_id_str:
                    return True, ""

                chassis_input.fill(chassis_id_str)

                apply_btn = cfg.locator("#gen_sys_apply").first
                expect(apply_btn).to_be_visible(timeout=timeout)
                expect(apply_btn).to_be_enabled(timeout=timeout)

                dlg_holder = {"text": None}
                arm_dialog_capture_once(dlg_holder)

                apply_btn.click(force=True, timeout=timeout)

                self.page.wait_for_timeout(500)
                alert_text = wait_for_dialog_text(dlg_holder, ms=3000)

                if alert_text:
                    return False, alert_text

                # verify value stayed applied
                self.page.wait_for_timeout(1000)
                new_value = (cfg.locator("input[name='slmSysChassisId']").first.input_value() or "").strip()

                if new_value == chassis_id_str:
                    return True, ""

                return False, ""

            except Exception as e:
                print(f"set_chassis_id failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return False, ""

    # ✅
    def get_system_product_name(self, retries: int = 5, timeout: int = 10000):
        """
        Returns the Product Name from the System Configuration page.
        Example: 'PL-2000ADS'
        """

        for attempt in range(retries):
            try:
                # open Configuration
                if not self.click_Configuration(timeout=timeout):
                    raise Exception("click_Configuration failed")
                
                if not self.upper_panel.click_system():
                        raise AssertionError(f"upper_panel.click_system failed")

                # wait for config page to load
                main_frame = self.page.frame_locator("iframe[name='main_page']")

                config_sys = main_frame.frame_locator("iframe[name='config_sys']")

                product_cell = config_sys.locator(
                    "xpath=//table[@id='gen_sys_info_table']//td[contains(normalize-space(),'Product Name')]/following-sibling::td[1]"
                ).first

                expect(product_cell).to_be_visible(timeout=timeout)

                return product_cell.inner_text().strip()

            except Exception as e:
                print(f"error in get_system_product_name attempt {attempt+1}: {e}")
                self.page.wait_for_timeout(1000)

        return None

    # ✅
    def set_admin_status_old(self, port_number, status: str, action_dismiss: bool = False, retries: int = 5, timeout: int = 10_000):
        """
        Set the Admin Status of a PacketLight port to Up or Down.

        Args:
            port_number: Examples: 1, "1", "Port-1", "ETH1", "COM1", "EDFA1", "MNG2"

            status:
                Supported values: "up", "down"

            action_dismiss:
                Controls how the confirmation dialog is handled after clicking:
                    False -> Accept the dialog and apply the change.
                    True  -> Dismiss the dialog and cancel the change.

        Returns:
            tuple[bool, str]:
                (success, dialog_text)

                success:
                    True  -> operation completed successfully, or the requested
                            state was already active.
                    False -> operation failed.

                dialog_text:
                    The text captured from the browser dialog if one appeared,
                    otherwise an empty string.
        """
        desired_status = (status or "").strip().lower()
        if desired_status not in {"up", "down"}:
            raise ValueError(f"Unsupported status '{status}'. Expected 'up' or 'down'.")

        def main_fl():
            return self.main_page_frame()

        def config_ctx():
            port_lower = str(port_number).lower()

            if "com" in port_lower:
                com_locator = main_fl().frame_locator("iframe[name='config_com'], frame[name='config_com']")
                sleep(1)
                return com_locator
            
            elif "eth" in port_lower or "edfa" in port_lower:
                return main_fl()
            
            else:
                config_locator = main_fl().frame_locator("iframe[name='config_port'], frame[name='config_port']")
                sleep(1)
                return config_locator

        def arm_dialog_capture_once(holder: dict):
            def _handler(d):
                try:
                    holder["text"] = (d.message or "").strip()
                except Exception:
                    holder["text"] = ""

                try:
                    if holder["text"] == "Not enough privileges":
                        d.accept()
                    elif action_dismiss:
                        d.dismiss()
                    else:
                        d.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

        def wait_for_dialog_text(holder: dict, ms: int = 5000) -> str:
            step = 50
            loops = max(1, ms // step)
            for _ in range(loops):
                if holder.get("text") is not None:
                    return holder.get("text") or ""
                self.page.wait_for_timeout(step)
            return holder.get("text") or ""

        def wait_modal_disappears():
            for _ in range(25):
                try:
                    modal = self.page.locator("#modalWait").first
                    sleep(1)
                    modal.wait_for(state="hidden", timeout=1000)
                    return
                except Exception:
                    self.page.wait_for_timeout(500)

        def get_current_admin_status(ctx) -> str:
            status_cell = ctx.locator("#AdminStatus").first
            sleep(1)
            expect(status_cell).to_be_visible(timeout=timeout)
            return (status_cell.inner_text() or "").strip().lower()

        def wait_until_admin_status(ctx, expected: str, ms: int = 10000) -> bool:
            step = 200
            loops = max(1, ms // step)
            for _ in range(loops):
                try:
                    current = get_current_admin_status(ctx)
                    if current == expected:
                        return True
                except Exception:
                    pass
                self.page.wait_for_timeout(step)
            return False

        success = False
        actual_alert_message = ""

        for attempt in range(retries):
            try:
                if not self.click_Configuration(timeout=timeout):
                    raise AssertionError("click_Configuration failed")

                if hasattr(self, "upper_panel"):
                    if not self.upper_panel.click_port(port_number, timeout=timeout):
                        raise AssertionError(f"upper_panel.click_port failed for {port_number}")
                else:
                    if not self.click_port(port_number, timeout=timeout):
                        raise AssertionError(f"click_port failed for {port_number}")

                port_lower = str(port_number).lower()

                if "eth" not in port_lower and "edfa" not in port_lower:
                    tab_general = main_fl().locator("#tab_general").first
                    expect(tab_general).to_be_visible(timeout=timeout)
                    tab_general.click(force=True, timeout=timeout)
                    expect(tab_general).to_have_attribute("class", "tab tabactive", timeout=timeout)

                ctx = config_ctx()
                self.page.wait_for_timeout(1000)

                current_status = get_current_admin_status(ctx)
                if current_status == desired_status:
                    # print(f"Admin {desired_status.title()} already active - nothing to do")
                    success = True
                    actual_alert_message = ""
                    break

                if desired_status == "up":
                    btn = ctx.locator("#formMaintXpdrAdmin #green_button").first
                else:
                    btn = ctx.locator("#formMaintXpdrAdmin #red_button").first

                expect(btn).to_be_visible(timeout=timeout)
                expect(btn).to_be_enabled(timeout=timeout)

                dlg_holder = {"text": None}
                arm_dialog_capture_once(dlg_holder)

                btn.scroll_into_view_if_needed()
                sleep(0.5)
                btn.click(force=True, timeout=timeout)
                sleep(0.5)

                self.page.wait_for_timeout(1000)
                actual_alert_message = wait_for_dialog_text(dlg_holder, ms=5000)

                if not actual_alert_message:
                    raise Exception("No browser alert appeared after click")

                if action_dismiss:
                    success = True
                    break

                if not wait_until_admin_status(ctx, desired_status, ms=10000):
                    raise Exception(
                        f"Admin Status did not change to '{desired_status}'. "
                        f"Current value is '{get_current_admin_status(ctx)}'"
                    )

                success = True
                break

            except Exception as e:
                print(f"Set Admin Status Failure {attempt + 1}: {e}")
                try:
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass
                continue

        wait_modal_disappears()
        self.reload()

        return success, actual_alert_message

    # ✅
    def set_admin_status(self, port_number, status: str, action_dismiss: bool = False, retries: int = 5, timeout: int = 10_000):
        """
        Set the Admin Status of a PacketLight port to Up or Down.

        Args:
            port_number:
                Examples: 1, "1", "Port-1", "ETH1", "COM1", "EDFA1", "MNG2", "COM"

            status:
                Supported values: "up", "down"

            action_dismiss:
                Controls how the confirmation dialog is handled after clicking:
                    False -> Accept the dialog and apply the change.
                    True  -> Dismiss the dialog and cancel the change.

        Returns:
            tuple[bool, str]:
                (success, dialog_text)

                success:
                    True  -> operation completed successfully, or the requested
                            state was already active.
                    False -> operation failed.

                dialog_text:
                    The text captured from the browser dialog if one appeared,
                    otherwise an empty string.
        """
        desired_status = (status or "").strip().lower()
        if desired_status not in {"up", "down"}:
            raise ValueError(f"Unsupported status '{status}'. Expected 'up' or 'down'.")

        def main_fl():
            return self.main_page_frame()

        def config_ctx():
            port_lower = str(port_number).lower()

            if "com" in port_lower:
                com_locator = main_fl().frame_locator("iframe[name='config_com'], frame[name='config_com']")
                sleep(1)
                return com_locator

            elif "eth" in port_lower or "edfa" in port_lower:
                return main_fl()

            else:
                config_locator = main_fl().frame_locator("iframe[name='config_port'], frame[name='config_port']")
                sleep(1)
                return config_locator

        def arm_dialog_capture_once(holder: dict):
            def _handler(d):
                try:
                    holder["text"] = (d.message or "").strip()
                except Exception:
                    holder["text"] = ""

                try:
                    if holder["text"] == "Not enough privileges":
                        d.accept()
                    elif action_dismiss:
                        d.dismiss()
                    else:
                        d.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

        def wait_for_dialog_text(holder: dict, ms: int = 5000) -> str:
            step = 50
            loops = max(1, ms // step)
            for _ in range(loops):
                if holder.get("text") is not None:
                    return holder.get("text") or ""
                self.page.wait_for_timeout(step)
            return holder.get("text") or ""

        def wait_modal_disappears():
            for _ in range(25):
                try:
                    modal = self.page.locator("#modalWait").first
                    sleep(1)
                    modal.wait_for(state="hidden", timeout=1000)
                    return
                except Exception:
                    self.page.wait_for_timeout(500)

        def get_current_admin_status(ctx) -> str:
            status_cell = ctx.locator("#AdminStatus").first
            sleep(1)
            expect(status_cell).to_be_visible(timeout=timeout)
            return (status_cell.inner_text() or "").strip().lower()

        def wait_until_admin_status(ctx, expected: str, ms: int = 10000) -> bool:
            step = 200
            loops = max(1, ms // step)
            for _ in range(loops):
                try:
                    current = get_current_admin_status(ctx)
                    if current == expected:
                        return True
                except Exception:
                    pass
                self.page.wait_for_timeout(step)
            return False

        def get_admin_button(ctx, port_number, desired_status: str):
            port_lower = str(port_number).lower()

            # COM page uses direct ids inside maint_com_admin_form
            if "com" in port_lower:
                if desired_status == "up":
                    return ctx.locator("#green_button").first
                return ctx.locator("#red_button").first

            # Other regular port pages
            if desired_status == "up":
                return ctx.locator("#formMaintXpdrAdmin #green_button").first
            return ctx.locator("#formMaintXpdrAdmin #red_button").first

        success = False
        actual_alert_message = ""

        for attempt in range(retries):
            try:
                if not self.click_Configuration(timeout=timeout):
                    raise AssertionError("click_Configuration failed")

                if hasattr(self, "upper_panel"):
                    if not self.upper_panel.click_port(port_number, timeout=timeout):
                        raise AssertionError(f"upper_panel.click_port failed for {port_number}")
                else:
                    if not self.click_port(port_number, timeout=timeout):
                        raise AssertionError(f"click_port failed for {port_number}")

                port_lower = str(port_number).lower()

                if "eth" not in port_lower and "edfa" not in port_lower:
                    tab_general = main_fl().locator("#tab_general").first
                    expect(tab_general).to_be_visible(timeout=timeout)
                    tab_general.click(force=True, timeout=timeout)
                    expect(tab_general).to_have_attribute("class", "tab tabactive", timeout=timeout)

                ctx = config_ctx()
                self.page.wait_for_timeout(1000)

                current_status = get_current_admin_status(ctx)
                if current_status == desired_status:
                    success = True
                    actual_alert_message = ""
                    break

                btn = get_admin_button(ctx, port_number, desired_status)

                expect(btn).to_be_visible(timeout=timeout)
                expect(btn).to_be_enabled(timeout=timeout)

                dlg_holder = {"text": None}
                arm_dialog_capture_once(dlg_holder)

                btn.scroll_into_view_if_needed()
                sleep(0.5)
                btn.click(force=True, timeout=timeout)
                sleep(0.5)

                self.page.wait_for_timeout(1000)
                actual_alert_message = wait_for_dialog_text(dlg_holder, ms=5000)

                if not actual_alert_message:
                    raise Exception("No browser alert appeared after click")

                if action_dismiss:
                    success = True
                    break

                if not wait_until_admin_status(ctx, desired_status, ms=10000):
                    raise Exception(
                        f"Admin Status did not change to '{desired_status}'. "
                        f"Current value is '{get_current_admin_status(ctx)}'"
                    )

                success = True
                break

            except Exception as e:
                print(f"Set Admin Status Failure {attempt + 1}: {e}")
                try:
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass
                continue

        wait_modal_disappears()
        self.reload()

        return success, actual_alert_message
    
    # ✅
    def set_service_type(self, port_number, service_type_value, action_dismiss: bool = False,
        retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
        """
        Set port Service Type by option VALUE and click Apply.

        Args:
            port_number:
                Examples: 1, "1", "Port-1"

            service_type_value:
                The <option value="..."> to select, for example: "10GbE-LAN"

            action_dismiss:
                False -> accept confirm/alert dialogs
                True  -> dismiss confirm dialogs when possible

        Returns:
            (success, dialog_text)
        """

        desired = str(service_type_value).strip()
        if not desired:
            return False, "service_type_value is empty"

        def main_fl():
            return self.main_page_frame()

        def port_cfg_fl():
            return main_fl().frame_locator("iframe[name='config_port'], iframe#config_port")

        def arm_dialog_capture_once(holder: dict):
            def _handler(d):
                try:
                    holder["text"] = (d.message or "").strip()
                except Exception:
                    holder["text"] = ""

                try:
                    if getattr(d, "type", "") == "confirm" and action_dismiss:
                        d.dismiss()
                    else:
                        d.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

        def wait_for_dialog_text(holder: dict, ms: int = 5000) -> str:
            step = 50
            loops = max(1, ms // step)
            for _ in range(loops):
                if holder.get("text") is not None:
                    return holder.get("text") or ""
                self.page.wait_for_timeout(step)
            return holder.get("text") or ""

        for attempt in range(retries):
            try:
                if not self.click_Configuration(timeout=timeout):
                    raise AssertionError("click_Configuration failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"upper_panel.click_port failed for {port_number}")

                tab_general = main_fl().locator("#tab_general").first
                expect(tab_general).to_be_visible(timeout=timeout)
                if (tab_general.get_attribute("class") or "").strip() != "tab tabactive":
                    tab_general.click(force=True, timeout=timeout)
                    expect(tab_general).to_have_attribute("class", "tab tabactive", timeout=timeout)

                cfg = port_cfg_fl()

                service_dd = cfg.locator("select[name='service_type']").first
                expect(service_dd).to_be_visible(timeout=timeout)

                # Read current selection BEFORE checking enabled/disabled
                current_value = (service_dd.input_value() or "").strip()
                current_label = (service_dd.locator("option:checked").inner_text() or "").strip()

                # Same behavior style as set_admin_status:
                # if already selected, return success even if dropdown is disabled
                if desired in {current_value, current_label}:
                    return True, ""

                # Only from here we require the dropdown to be enabled,
                # because we actually need to change something
                expect(service_dd).to_be_enabled(timeout=timeout)

                selected = False

                # Try by VALUE first
                try:
                    service_dd.select_option(value=desired)
                    selected = True
                except Exception:
                    pass

                # If not found by value, try by LABEL
                if not selected:
                    try:
                        service_dd.select_option(label=desired)
                        selected = True
                    except Exception:
                        pass

                if not selected:
                    return False, f"Service type '{desired}' was not found in the dropdown"

                apply_btn = cfg.locator("#xpdrApply").first
                expect(apply_btn).to_be_visible(timeout=timeout)
                expect(apply_btn).to_be_enabled(timeout=timeout)

                dlg_holder = {"text": None}
                arm_dialog_capture_once(dlg_holder)

                apply_btn.click(force=True, timeout=timeout)

                self.page.wait_for_timeout(1000)
                dialog_text = wait_for_dialog_text(dlg_holder, ms=5000)

                if action_dismiss and dialog_text:
                    return True, dialog_text

                result = self.get_service_type(port_number, timeout=timeout)
                if result is None:
                    return False, dialog_text

                new_value, new_label = result
                if desired in {new_value, new_label}:
                    return True, dialog_text

                return False, dialog_text

            except Exception as e:
                print(f"set_service_type failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                    self.reload()
                except Exception:
                    pass

        return False, ""

    # ✅
    def get_service_type(self, port_number, retries: int = 5, timeout: int = 10_000) -> Optional[Tuple[str, str]]:
        """
        Get the currently selected Service Type of a port.

        Returns:
            tuple(value, label)
                Example:
                    ("33", "10GbE-LAN")

            None if failed.
        """

        def main_fl():
            return self.main_page_frame()

        def port_cfg_fl():
            return main_fl().frame_locator("iframe[name='config_port'], iframe#config_port")

        for attempt in range(retries):
            try:
                # Navigate to Configuration -> Port
                if not self.click_Configuration(timeout=timeout):
                    raise AssertionError("click_Configuration failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"upper_panel.click_port failed for {port_number}")

                # Ensure General tab active
                tab_general = main_fl().locator("#tab_general").first
                expect(tab_general).to_be_visible(timeout=timeout)

                if (tab_general.get_attribute("class") or "").strip() != "tab tabactive":
                    tab_general.click(force=True, timeout=timeout)

                expect(tab_general).to_have_attribute("class", "tab tabactive", timeout=timeout)

                # Enter port config iframe
                cfg = port_cfg_fl()

                service_dd = cfg.locator("select[name='service_type']").first

                expect(service_dd).to_be_visible(timeout=timeout)

                # Selected VALUE
                selected_value = (service_dd.input_value() or "").strip()

                # Selected LABEL/TEXT
                selected_label = (service_dd.locator("option:checked").inner_text() or "").strip()

                return selected_value, selected_label

            except Exception as e:
                print(f"get_service_type failed (attempt {attempt + 1}): {e}")

                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return None

    # ✅
    def set_provisioning_old(self, port_number, uplink_number: Optional[int] = None,
                         retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
        """
        Args:
            port_number:
                Examples: 1, "1", "Port-1"

            uplink_number:
                Optional. Usually 1 or 2.
                If provided, selects the matching uplink radio button.

        Returns:
            (success, dialog_text)

        Raises:
            Exception:
                If the provisioning page is missing the instruction,
                if the slot count cannot be parsed,
                or if there are not enough continuous free slots.
        """

        def main_fl():
            return self.main_page_frame()

        def port_cfg_fl():
            return main_fl().frame_locator("iframe[name='config_port'], iframe#config_port")

        def arm_dialog_capture_once(holder: dict):
            def _handler(d):
                try:
                    holder["text"] = (d.message or "").strip()
                except Exception:
                    holder["text"] = ""

                try:
                    d.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

        def wait_for_dialog_text(holder: dict, ms: int = 5000) -> str:
            step = 50
            loops = max(1, ms // step)
            for _ in range(loops):
                if holder.get("text") is not None:
                    return holder.get("text") or ""
                self.page.wait_for_timeout(step)
            return holder.get("text") or ""

        def extract_required_slots(cfg) -> int:
            body = cfg.locator("body").first
            expect(body).to_be_visible(timeout=timeout)
            txt = body.inner_text()

            m = re.search(r"select\s+up\s+to\s+(\d+)\s+slots?", txt, re.IGNORECASE)
            if not m:
                raise Exception("Could not parse required slot count from provisioning page text")

            return int(m.group(1))

        def select_uplink_if_needed(cfg, uplink: Optional[int]) -> None:
            if uplink is None:
                return

            if uplink not in {1, 2}:
                raise ValueError(f"Unsupported uplink_number '{uplink}'. Expected 1 or 2.")

            # First try direct label-based radio selection
            radio_candidates = cfg.locator("input[type='radio']")
            count = radio_candidates.count()

            for i in range(count):
                radio = radio_candidates.nth(i)
                try:
                    label_text = radio.evaluate("""
                        el => {
                            let txt = '';
                            let n = el.nextSibling;
                            while (n) {
                                if (n.nodeType === Node.TEXT_NODE && n.textContent.trim()) {
                                    txt = n.textContent.trim();
                                    break;
                                }
                                if (n.nodeType === Node.ELEMENT_NODE && n.innerText && n.innerText.trim()) {
                                    txt = n.innerText.trim();
                                    break;
                                }
                                n = n.nextSibling;
                            }
                            if (!txt && el.parentElement) txt = el.parentElement.innerText || '';
                            return txt.trim();
                        }
                    """)
                except Exception:
                    label_text = ""

                if f"Uplink {uplink}" in label_text:
                    radio.check(force=True)
                    self.page.wait_for_timeout(500)
                    return

            # Fallback: if there are exactly 2 radios, use index
            if count >= 2:
                radio_candidates.nth(uplink - 1).check(force=True)
                self.page.wait_for_timeout(500)
                return

            raise Exception(f"Could not find Uplink {uplink} radio button")

        def get_numeric_slot_checkboxes(cfg):
            """
            Return list of:
                {
                    "index": locator index,
                    "slot": int,
                    "enabled": bool,
                    "checked": bool
                }

            Only numeric slot checkboxes are returned.
            Legend / decorative checkboxes are ignored.
            """
            cbs = cfg.locator("input[type='checkbox']")
            total = cbs.count()
            result = []

            for i in range(total):
                cb = cbs.nth(i)

                try:
                    slot_text = cb.evaluate("""
                        el => {
                            let txt = '';
                            let n = el.nextSibling;
                            while (n) {
                                if (n.nodeType === Node.TEXT_NODE && n.textContent.trim()) {
                                    txt = n.textContent.trim();
                                    break;
                                }
                                if (n.nodeType === Node.ELEMENT_NODE && n.innerText && n.innerText.trim()) {
                                    txt = n.innerText.trim();
                                    break;
                                }
                                n = n.nextSibling;
                            }
                            if (!txt && el.parentElement) txt = el.parentElement.innerText || '';
                            return txt.trim();
                        }
                    """)
                except Exception:
                    slot_text = ""

                m = re.search(r"\b(\d+)\b", slot_text)
                if not m:
                    continue

                slot_num = int(m.group(1))

                try:
                    enabled = cb.is_enabled()
                except Exception:
                    enabled = False

                try:
                    checked = cb.is_checked()
                except Exception:
                    checked = False

                result.append(
                    {
                        "index": i,
                        "slot": slot_num,
                        "enabled": enabled,
                        "checked": checked,
                    }
                )

            # sort by visible slot number
            result.sort(key=lambda x: x["slot"])
            return result

        def find_first_continuous_free_block(slot_rows, needed: int):
            """
            Free means:
                enabled == True and checked == False

            Continuous means numeric sequence:
                n, n+1, n+2, ...
            """
            free_slots = [r for r in slot_rows if r["enabled"] and not r["checked"]]

            for start in range(len(free_slots)):
                block = [free_slots[start]]

                for j in range(start + 1, len(free_slots)):
                    if free_slots[j]["slot"] == block[-1]["slot"] + 1:
                        block.append(free_slots[j])
                        if len(block) == needed:
                            return block
                    elif free_slots[j]["slot"] > block[-1]["slot"] + 1:
                        break

            return None

        for attempt in range(retries):
            try:
                if not self.click_Configuration(timeout=timeout):
                    raise AssertionError("click_Configuration failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"upper_panel.click_port failed for {port_number}")

                main_frame = main_fl()

                provisioning_tab = main_frame.locator("#tab_provisioning").first
                expect(provisioning_tab).to_be_visible(timeout=timeout)

                if (provisioning_tab.get_attribute("class") or "").strip() != "tab tabactive":
                    provisioning_tab.click(force=True, timeout=timeout)
                    expect(provisioning_tab).to_have_attribute("class", "tab tabactive", timeout=timeout)

                cfg = port_cfg_fl()
                body = cfg.locator("body").first
                expect(body).to_be_visible(timeout=timeout)

                # Select uplink if requested
                select_uplink_if_needed(cfg, uplink_number)

                # Parse required number of slots from page instruction
                needed_slots = extract_required_slots(cfg)

                slot_rows = get_numeric_slot_checkboxes(cfg)
                if not slot_rows:
                    raise Exception("No numeric provisioning slot checkboxes were found")

                block = find_first_continuous_free_block(slot_rows, needed_slots)
                if not block:
                    raise Exception(
                        f"There are no {needed_slots} continuous available slots for provisioning"
                    )

                # Select the block
                cbs = cfg.locator("input[type='checkbox']")
                for item in block:
                    cb = cbs.nth(item["index"])
                    if not cb.is_checked():
                        cb.check(force=True)

                # Click Make Provisioning
                make_btn = cfg.locator(
                    "#make_break, input[name='make_break'], input.prov_but[value='Make Provisioning']"
                ).first

                expect(make_btn).to_be_visible(timeout=timeout)
                expect(make_btn).to_be_enabled(timeout=timeout)

                dlg_holder = {"text": None}
                arm_dialog_capture_once(dlg_holder)

                make_btn.click(force=True, timeout=timeout)

                self.page.wait_for_timeout(1000)
                dialog_text = wait_for_dialog_text(dlg_holder, ms=5000)

                return True, dialog_text

            except Exception as e:
                print(f"set_provisioning failed (attempt {attempt + 1}): {e}")
                if attempt == retries - 1:
                    raise
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        raise Exception("set_provisioning failed")

    # ✅
    def set_provisioning(self, port_number, uplink_number: Optional[int] = None, slots_number: Optional[int] = None,
        retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
        """
        Args:
            port_number:
                Examples: 1, "1", "Port-1"

            uplink_number:
                Optional. Usually 1 or 2.
                If provided, selects the matching uplink radio button.

            slots_number:
                Optional.
                If None -> provision the full required block from the page instruction.
                If given -> provision exactly this many slots from the beginning of the
                first continuous free block found.

        Returns:
            (success, dialog_text)

        Raises:
            Exception:
                If the provisioning page is missing the instruction,
                if the slot count cannot be parsed,
                or if there are not enough continuous free slots.
        """

        def main_fl():
            return self.main_page_frame()

        def port_cfg_fl():
            return main_fl().frame_locator("iframe[name='config_port'], iframe#config_port")

        def arm_dialog_capture_once(holder: dict):
            def _handler(d):
                try:
                    holder["text"] = (d.message or "").strip()
                except Exception:
                    holder["text"] = ""

                try:
                    d.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

        def wait_for_dialog_text(holder: dict, ms: int = 5000) -> str:
            step = 50
            loops = max(1, ms // step)
            for _ in range(loops):
                if holder.get("text") is not None:
                    return holder.get("text") or ""
                self.page.wait_for_timeout(step)
            return holder.get("text") or ""

        def extract_required_slots(cfg) -> int:
            body = cfg.locator("body").first
            expect(body).to_be_visible(timeout=timeout)
            txt = body.inner_text()

            m = re.search(r"select\s+up\s+to\s+(\d+)\s+slots?", txt, re.IGNORECASE)
            if not m:
                raise Exception("Could not parse required slot count from provisioning page text")

            return int(m.group(1))

        def select_uplink_if_needed(cfg, uplink: Optional[int]) -> None:
            if uplink is None:
                return

            if uplink not in {1, 2}:
                raise ValueError(f"Unsupported uplink_number '{uplink}'. Expected 1 or 2.")

            radio_candidates = cfg.locator("input[type='radio']")
            count = radio_candidates.count()

            for i in range(count):
                radio = radio_candidates.nth(i)
                try:
                    label_text = radio.evaluate("""
                        el => {
                            let txt = '';
                            let n = el.nextSibling;
                            while (n) {
                                if (n.nodeType === Node.TEXT_NODE && n.textContent.trim()) {
                                    txt = n.textContent.trim();
                                    break;
                                }
                                if (n.nodeType === Node.ELEMENT_NODE && n.innerText && n.innerText.trim()) {
                                    txt = n.innerText.trim();
                                    break;
                                }
                                n = n.nextSibling;
                            }
                            if (!txt && el.parentElement) txt = el.parentElement.innerText || '';
                            return txt.trim();
                        }
                    """)
                except Exception:
                    label_text = ""

                if f"Uplink {uplink}" in label_text:
                    radio.check(force=True)
                    self.page.wait_for_timeout(500)
                    return

            if count >= 2:
                radio_candidates.nth(uplink - 1).check(force=True)
                self.page.wait_for_timeout(500)
                return

            raise Exception(f"Could not find Uplink {uplink} radio button")

        def get_numeric_slot_checkboxes(cfg):
            cbs = cfg.locator("input[type='checkbox']")
            total = cbs.count()
            result = []

            for i in range(total):
                cb = cbs.nth(i)

                try:
                    slot_text = cb.evaluate("""
                        el => {
                            let txt = '';
                            let n = el.nextSibling;
                            while (n) {
                                if (n.nodeType === Node.TEXT_NODE && n.textContent.trim()) {
                                    txt = n.textContent.trim();
                                    break;
                                }
                                if (n.nodeType === Node.ELEMENT_NODE && n.innerText && n.innerText.trim()) {
                                    txt = n.innerText.trim();
                                    break;
                                }
                                n = n.nextSibling;
                            }
                            if (!txt && el.parentElement) txt = el.parentElement.innerText || '';
                            return txt.trim();
                        }
                    """)
                except Exception:
                    slot_text = ""

                m = re.search(r"\b(\d+)\b", slot_text)
                if not m:
                    continue

                slot_num = int(m.group(1))

                try:
                    enabled = cb.is_enabled()
                except Exception:
                    enabled = False

                try:
                    checked = cb.is_checked()
                except Exception:
                    checked = False

                result.append(
                    {
                        "index": i,
                        "slot": slot_num,
                        "enabled": enabled,
                        "checked": checked,
                    }
                )

            result.sort(key=lambda x: x["slot"])
            return result

        def find_first_continuous_free_block(slot_rows, needed: int):
            free_slots = [r for r in slot_rows if r["enabled"] and not r["checked"]]

            for start in range(len(free_slots)):
                block = [free_slots[start]]

                for j in range(start + 1, len(free_slots)):
                    if free_slots[j]["slot"] == block[-1]["slot"] + 1:
                        block.append(free_slots[j])
                        if len(block) == needed:
                            return block
                    elif free_slots[j]["slot"] > block[-1]["slot"] + 1:
                        break

            return None

        for attempt in range(retries):
            try:
                if not self.click_Configuration(timeout=timeout):
                    raise AssertionError("click_Configuration failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"upper_panel.click_port failed for {port_number}")

                main_frame = main_fl()

                provisioning_tab = main_frame.locator("#tab_provisioning").first
                expect(provisioning_tab).to_be_visible(timeout=timeout)

                if (provisioning_tab.get_attribute("class") or "").strip() != "tab tabactive":
                    provisioning_tab.click(force=True, timeout=timeout)
                    expect(provisioning_tab).to_have_attribute("class", "tab tabactive", timeout=timeout)

                cfg = port_cfg_fl()
                body = cfg.locator("body").first
                expect(body).to_be_visible(timeout=timeout)

                # Already provisioned -> continue successfully
                make_btn = cfg.locator("#make_break, input[name='make_break'], input.prov_but").first
                expect(make_btn).to_be_visible(timeout=timeout)

                btn_value = (make_btn.get_attribute("value") or "").strip()
                if btn_value == "Remove Provisioning":
                    return True, ""

                select_uplink_if_needed(cfg, uplink_number)

                required_slots = extract_required_slots(cfg)

                if slots_number is None:
                    slots_to_provision = required_slots
                else:
                    try:
                        slots_to_provision = int(slots_number)
                    except Exception:
                        raise Exception(f"Invalid slots_number '{slots_number}'")

                    if slots_to_provision <= 0:
                        raise Exception("slots_number must be greater than 0")

                    if slots_to_provision > required_slots:
                        raise Exception(
                            f"slots_number={slots_to_provision} is greater than the allowed "
                            f"number from the page instruction ({required_slots})"
                        )

                slot_rows = get_numeric_slot_checkboxes(cfg)
                if not slot_rows:
                    raise Exception("No numeric provisioning slot checkboxes were found")

                block = find_first_continuous_free_block(slot_rows, required_slots)
                if not block:
                    raise Exception(f"There are no {required_slots} continuous available slots for provisioning")

                selected_block = block[:slots_to_provision]

                cbs = cfg.locator("input[type='checkbox']")
                for item in selected_block:
                    cb = cbs.nth(item["index"])
                    if not cb.is_checked():
                        cb.check(force=True)

                expect(make_btn).to_be_enabled(timeout=timeout)

                dlg_holder = {"text": None}
                arm_dialog_capture_once(dlg_holder)

                make_btn.click(force=True, timeout=timeout)

                self.page.wait_for_timeout(1000)
                dialog_text = wait_for_dialog_text(dlg_holder, ms=5000)

                return True, dialog_text

            except Exception as e:
                print(f"set_provisioning failed (attempt {attempt + 1}): {e}")
                if attempt == retries - 1:
                    raise
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        raise Exception("set_provisioning failed")

    # ✅
    def remove_provisioning(self, port_number, retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
        """
        Remove provisioning from the requested port.

        Args:
            port_number:
                Examples: 1, "1", "Port-1"

        Returns:
            (success, dialog_text)
        """

        def main_fl():
            return self.main_page_frame()

        def port_cfg_fl():
            return main_fl().frame_locator("iframe[name='config_port'], iframe#config_port")

        def arm_dialog_capture_once(holder: dict):
            def _handler(d):
                try:
                    holder["text"] = (d.message or "").strip()
                except Exception:
                    holder["text"] = ""

                try:
                    d.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

        def wait_for_dialog_text(holder: dict, ms: int = 5000) -> str:
            step = 50
            loops = max(1, ms // step)
            for _ in range(loops):
                if holder.get("text") is not None:
                    return holder.get("text") or ""
                self.page.wait_for_timeout(step)
            return holder.get("text") or ""

        def get_this_port_prov_slots(cfg):
            """
            Returns all currently provisioned slots belonging to this port.
            These are rendered as class='prov' and checked+disabled. :contentReference[oaicite:1]{index=1}
            """
            slots = cfg.locator("input[type='checkbox'].prov[id^='slot']")
            result = []
            count = slots.count()

            for i in range(count):
                cb = slots.nth(i)
                try:
                    slot_id = (cb.get_attribute("id") or "").strip()   # e.g. slot9
                    m = re.search(r"slot(\d+)$", slot_id)
                    if not m:
                        continue

                    slot_num = int(m.group(1)) + 1  # UI labels are 1-based
                    checked = cb.is_checked()
                    result.append((slot_num, checked))
                except Exception:
                    continue

            return result

        for attempt in range(retries):
            try:
                if not self.click_Configuration(timeout=timeout):
                    raise AssertionError("click_Configuration failed")

                if not self.upper_panel.click_port(port_number, timeout=timeout):
                    raise AssertionError(f"upper_panel.click_port failed for {port_number}")

                provisioning_tab = main_fl().locator("#tab_provisioning").first
                expect(provisioning_tab).to_be_visible(timeout=timeout)

                if (provisioning_tab.get_attribute("class") or "").strip() != "tab tabactive":
                    provisioning_tab.click(force=True, timeout=timeout)
                    expect(provisioning_tab).to_have_attribute("class", "tab tabactive", timeout=timeout)

                cfg = port_cfg_fl()
                body = cfg.locator("body").first
                expect(body).to_be_visible(timeout=timeout)

                current_slots = get_this_port_prov_slots(cfg)
                if not current_slots:
                    return False, "No provisioning exists for this port"

                remove_btn = cfg.locator("#make_break, input[name='make_break'], input.prov_but[value='Remove Provisioning']").first
                expect(remove_btn).to_be_visible(timeout=timeout)
                expect(remove_btn).to_be_enabled(timeout=timeout)

                btn_value = (remove_btn.get_attribute("value") or "").strip()
                if btn_value != "Remove Provisioning":
                    raise Exception(f"Expected 'Remove Provisioning' button, got '{btn_value}'")

                dlg_holder = {"text": None}
                arm_dialog_capture_once(dlg_holder)

                remove_btn.click(force=True, timeout=timeout)

                self.page.wait_for_timeout(1000)
                dialog_text = wait_for_dialog_text(dlg_holder, ms=5000)

                # Re-resolve frame after submit/refresh
                cfg = port_cfg_fl()
                body = cfg.locator("body").first
                expect(body).to_be_visible(timeout=timeout)

                remaining_slots = get_this_port_prov_slots(cfg)
                if not remaining_slots:
                    return True, dialog_text

                return False, dialog_text

            except Exception as e:
                print(f"remove_provisioning failed (attempt {attempt + 1}): {e}")
                if attempt == retries - 1:
                    raise
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return False, ""

    # ✅
    def add_sntp_server(self, ip: str, protocol: str = "SNTP", key_id=None, key_value=None, retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
        """
        Add a time server (SNTP/NTP) with optional symmetric key authentication.

        Args:
            ip:
                IPv4 address as string.

            protocol:
                "SNTP" or "NTP" (case-insensitive).

            key_id:
                Optional Key ID. If None/empty -> left blank.

            key_value:
                Optional Key Value. If None/empty -> left blank.

        Returns:
            tuple[bool, str]:
                (success, alert_text)

                success:
                    True  -> server was added successfully
                    False -> operation failed

                alert_text:
                    Browser alert text if an alert appeared, otherwise "".
        """
        # ---- Validation ----
        if not ip or not re.match(r"^((25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(25[0-5]|2[0-4]\d|1?\d?\d)$", ip):
            return False, "Invalid IP Address (requires numeric IPv4)"

        protocol = (protocol or "SNTP").strip().upper()
        if protocol not in {"SNTP", "NTP"}:
            return False, f"Invalid protocol '{protocol}' (use SNTP or NTP)"

        PRIV_WARN_SUB = "Not enough privileges"
        IP_WARN_SUB = "valid IP address"

        def time_config_frame():
            return self.main_page_frame().frame_locator("iframe[name='config_sys'], iframe#config_sys")
        
        def arm_dialog_capture_once(holder: dict):
            def _handler(d):
                try:
                    holder["text"] = (d.message or "").strip()
                except Exception:
                    holder["text"] = ""

                try:
                    d.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

        def wait_for_dialog_text(holder: dict, ms: int = 5000) -> str:
            step = 50
            loops = max(1, ms // step)
            for _ in range(loops):
                if holder.get("text") is not None:
                    return holder.get("text") or ""
                self.page.wait_for_timeout(step)
            return holder.get("text") or ""

        for attempt in range(retries):
            try:
                if not self.click_time(timeout=timeout):
                    raise Exception("click_time failed")

                self.page.wait_for_timeout(500)

                cfg = time_config_frame()
                sleep(0.5)

                # ---- Locate the add row by the IP input ----
                ip_field = cfg.locator("input[name='ip_address']").first
                sleep(0.5)
                expect(ip_field).to_be_visible(timeout=timeout)

                row = ip_field.locator("xpath=./ancestor::tr[1]")
                sleep(0.5)

                # IP
                ip_field.fill(ip)

                # Protocol
                protocol_select = row.locator("xpath=./td[position()=2]//select").first
                sleep(0.5)
                expect(protocol_select).to_be_visible(timeout=timeout)
                protocol_select.select_option(label=protocol)

                # Key ID
                if key_id not in (None, ""):
                    key_id_el = row.locator("xpath=./td[position()=3]//input[not(@type='hidden')]").first
                    sleep(0.5)
                    expect(key_id_el).to_be_visible(timeout=timeout)
                    key_id_el.fill(str(key_id))

                # Key Value
                if key_value not in (None, ""):
                    key_value_el = row.locator("xpath=./td[position()=4]//input[not(@type='hidden')]").first
                    sleep(0.5)
                    expect(key_value_el).to_be_visible(timeout=timeout)
                    key_value_el.fill(str(key_value))

                # ---- Click Add ----
                add_btn = row.locator(
                    "xpath=./td[last()]//input[@name='sntp_add' or @type='button' or @type='submit']"
                ).first
                sleep(0.5)
                expect(add_btn).to_be_visible(timeout=timeout)
                expect(add_btn).to_be_enabled(timeout=timeout)

                dlg_holder = {"text": None}
                arm_dialog_capture_once(dlg_holder)
                sleep(0.5)

                add_btn.click(force=True, timeout=timeout)

                # ---- Handle possible alert ----
                self.page.wait_for_timeout(500)
                alert_text = wait_for_dialog_text(dlg_holder, ms=4000)

                if alert_text:
                    if PRIV_WARN_SUB.lower() in alert_text.lower():
                        return False, alert_text
                    if IP_WARN_SUB.lower() in alert_text.lower():
                        return False, alert_text
                    return False, alert_text

                # ---- No alert = success path ----
                return True, ""

            except Exception as e:
                print(f"add_sntp_server failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                    self.reload()
                except Exception:
                    pass

        return False, ""

    # ✅
    def set_sntp_configuration_old(self, status: str, gmt: Optional[str] = None, daylight_save: Optional[str] = None,
        retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
        """
        Set the SNTP/NTP configuration under Configuration -> System -> Time.

        Args:
            status:
                Supported values:
                    "Enable", "Enabled", "Disable", "Disabled"

            gmt:
                Optional timezone text as shown in the GUI, for example:
                    "GMT+2"

            daylight_save:
                Optional daylight saving value as shown in the GUI, for example:
                    "Enabled" / "Disabled"

        Returns:
            tuple[bool, str]:
                (success, alert_text)

                success:
                    True  -> operation completed successfully
                    False -> operation failed

                alert_text:
                    Browser alert text if an alert appeared, otherwise "".
        """

        PRIV_WARN_SUB = "Not enough privileges"
        WARN_SUB = "Add at least one server first"

        normalized_status = (status or "").strip().lower()
        if normalized_status in {"enable", "enabled"}:
            status_value = "Enabled"
        elif normalized_status in {"disable", "disabled"}:
            status_value = "Disabled"
        else:
            return False, f"Invalid status '{status}'"

        def time_config_frame():
            return self.main_page_frame().frame_locator("iframe[name='config_sys'], iframe#config_sys")

        def arm_dialog_capture_once(holder: dict):
            def _handler(d):
                try:
                    holder["text"] = (d.message or "").strip()
                except Exception:
                    holder["text"] = ""

                try:
                    d.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

        def wait_for_dialog_text(holder: dict, ms: int = 3000) -> str:
            step = 50
            loops = max(1, ms // step)
            for _ in range(loops):
                if holder.get("text") is not None:
                    return holder.get("text") or ""
                self.page.wait_for_timeout(step)
            return holder.get("text") or ""

        for attempt in range(retries):
            try:
                if not self.click_time(timeout=timeout):
                    raise Exception("click_time failed")

                self.page.wait_for_timeout(500)

                cfg = time_config_frame()

                # Enable / Disable
                sntp_enable_sel = cfg.locator("#sntp_enable_sel").first
                expect(sntp_enable_sel).to_be_visible(timeout=timeout)
                sntp_enable_sel.select_option(label=status_value)

                # GMT / Time zone
                if gmt not in (None, ""):
                    sntp_tz_sel = cfg.locator("#sntp_tz_sel").first
                    expect(sntp_tz_sel).to_be_visible(timeout=timeout)
                    sntp_tz_sel.select_option(label=str(gmt).strip())

                # Daylight Saving
                if daylight_save not in (None, ""):
                    daylight_sel = cfg.locator("#daylight_save_sel, #sntp_daylight_sel, #sntp_dst_sel").first
                    expect(daylight_sel).to_be_visible(timeout=timeout)
                    daylight_sel.select_option(label=str(daylight_save).strip())

                # Apply
                apply_btn = cfg.locator("#sntp_apply").first
                expect(apply_btn).to_be_visible(timeout=timeout)
                expect(apply_btn).to_be_enabled(timeout=timeout)

                dlg_holder = {"text": None}
                arm_dialog_capture_once(dlg_holder)

                apply_btn.click(force=True, timeout=timeout)
                sleep(2)

                self.page.wait_for_timeout(500)
                alert_text = wait_for_dialog_text(dlg_holder, ms=3000)

                # No alert = success path
                if not alert_text:
                    return True, ""

                # Known alerts
                if PRIV_WARN_SUB.lower() in alert_text.lower():
                    return False, alert_text

                if WARN_SUB.lower() in alert_text.lower():
                    return False, alert_text

                # Unknown alert -> return it as failure
                return False, alert_text

            except Exception as e:
                print(f"set_sntp_configuration failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return False, ""

    # ✅
    def set_sntp_configuration(self, status: str, gmt: Optional[str] = None, daylight_save: Optional[str] = None,
        retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
        """
        Set the SNTP/NTP configuration under Configuration -> System -> Time.

        Args:
            status:
                Supported values:
                    "Enable", "Enabled", "Disable", "Disabled"

            gmt:
                Optional timezone text as shown in the GUI, for example:
                    "GMT+2"

            daylight_save:
                Optional daylight saving value as shown in the GUI, for example:
                    "Enabled" / "Disabled"

        Returns:
            tuple[bool, str]:
                (success, alert_text)

                success:
                    True  -> operation completed successfully
                    False -> operation failed

                alert_text:
                    Browser alert text if an alert appeared, otherwise "".
        """

        PRIV_WARN_SUB = "Not enough privileges"
        WARN_SUB = "Add at least one server first"

        normalized_status = (status or "").strip().lower()
        if normalized_status in {"enable", "enabled"}:
            status_value = "Enabled"
        elif normalized_status in {"disable", "disabled"}:
            status_value = "Disabled"
        else:
            return False, f"Invalid status '{status}'"

        daylight_value = None
        if daylight_save not in (None, ""):
            normalized_daylight = str(daylight_save).strip().lower()
            if normalized_daylight in {"enable", "enabled"}:
                daylight_value = "Enabled"
            elif normalized_daylight in {"disable", "disabled"}:
                daylight_value = "Disabled"
            else:
                return False, f"Invalid daylight_save '{daylight_save}'"

        def time_config_frame():
            return self.main_page_frame().frame_locator("iframe[name='config_sys'], iframe#config_sys")

        def arm_dialog_capture_once(holder: dict):
            def _handler(d):
                try:
                    holder["text"] = (d.message or "").strip()
                except Exception:
                    holder["text"] = ""

                try:
                    d.accept()
                except Exception:
                    pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass

        def wait_for_dialog_text(holder: dict, ms: int = 3000) -> str:
            step = 50
            loops = max(1, ms // step)
            for _ in range(loops):
                if holder.get("text") is not None:
                    return holder.get("text") or ""
                self.page.wait_for_timeout(step)
            return holder.get("text") or ""

        for attempt in range(retries):
            try:
                if not self.click_time(timeout=timeout):
                    raise Exception("click_time failed")

                self.page.wait_for_timeout(500)

                cfg = time_config_frame()

                sntp_enable_sel = cfg.locator("#sntp_enable_sel").first
                expect(sntp_enable_sel).to_be_visible(timeout=timeout)

                sntp_tz_sel = cfg.locator("#sntp_tz_sel").first
                expect(sntp_tz_sel).to_be_visible(timeout=timeout)

                daylight_sel = cfg.locator("#sntp_dls_sel").first
                expect(daylight_sel).to_be_visible(timeout=timeout)

                # Read current values first
                current_status = (sntp_enable_sel.locator("option:checked").inner_text() or "").strip()
                current_gmt = (sntp_tz_sel.locator("option:checked").inner_text() or "").strip()
                current_daylight = (daylight_sel.locator("option:checked").inner_text() or "").strip()

                # Nothing to change -> succeed immediately
                nothing_to_change = (
                    current_status == status_value
                    and (gmt in (None, "") or current_gmt == str(gmt).strip())
                    and (daylight_value is None or current_daylight == daylight_value)
                )
                if nothing_to_change:
                    return True, ""

                # Enable / Disable
                if current_status != status_value:
                    sntp_enable_sel.select_option(label=status_value)

                # GMT / Time zone
                if gmt not in (None, "") and current_gmt != str(gmt).strip():
                    sntp_tz_sel.select_option(label=str(gmt).strip())

                # Daylight Saving
                if daylight_value is not None and current_daylight != daylight_value:
                    daylight_sel.select_option(label=daylight_value)

                apply_btn = cfg.locator("#sntp_apply").first
                expect(apply_btn).to_be_visible(timeout=timeout)
                expect(apply_btn).to_be_enabled(timeout=timeout)

                dlg_holder = {"text": None}
                arm_dialog_capture_once(dlg_holder)

                apply_btn.click(force=True, timeout=timeout)
                sleep(2)

                self.page.wait_for_timeout(500)
                alert_text = wait_for_dialog_text(dlg_holder, ms=3000)

                if not alert_text:
                    return True, ""

                if PRIV_WARN_SUB.lower() in alert_text.lower():
                    return False, alert_text

                if WARN_SUB.lower() in alert_text.lower():
                    return False, alert_text

                return False, alert_text

            except Exception as e:
                print(f"set_sntp_configuration failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return False, ""

    # ==========================================================
    # Maintenance Tab
    # ==========================================================

    # ✅
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
                # print(f"[DBG] device_restart attempt {attempt + 1} failed: {e}")
                try:
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass
                continue

        return False, ""

    # ==========================================================
    # Generic Helpers
    # ==========================================================

    # ✅
    def reload(self):
        self.page.reload(wait_until="domcontentloaded")

    # ✅
    def accept_dialog_once(self):
        try:
            self.page.once("dialog", lambda d: d.accept())
        except Exception:
            pass
    
    # ✅
    def wait_ms(self, ms: int):
        self.page.wait_for_timeout(ms)