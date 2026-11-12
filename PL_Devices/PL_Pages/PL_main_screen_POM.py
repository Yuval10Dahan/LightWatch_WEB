'''
Created by: Yuval Dahan
Date: 03/03/2026
'''


from playwright.sync_api import Page, expect
from typing import Dict, List, Optional, Tuple
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
                # Older products (e.g. PL-2000) render this field permanently
                # disabled with no value attribute -- an empty value there means "0".
                effective_current = current_value or "0"

                if effective_current == chassis_id_str:
                    return True, ""

                if chassis_input.is_disabled():
                    return False, "Chassis ID field is disabled on this device/firmware - not supported"

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
    def get_service_type_dropdown_options(self, port_number, retries: int = 5, timeout: int = 10_000):
        """
        Returns every selectable option of a port's Service Type dropdown
        (Configuration -> Port -> General) as a list of labels.

        Example:
            [None, "100GbE-LAN", "100GbE-LAN-CBR", "OTU4", "Encrypted 100GbE-LAN", ...]
        """

        def main_fl():
            return self.main_page_frame()

        def port_cfg_fl():
            return main_fl().frame_locator("iframe[name='config_port'], iframe#config_port")

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

                options = service_dd.locator("option")
                option_count = options.count()

                result = []
                for i in range(option_count):
                    opt = options.nth(i)
                    if opt.get_attribute("disabled") is not None:
                        continue  # skip the disabled separator entry

                    value = (opt.get_attribute("value") or "").strip()
                    label = (opt.inner_text() or "").strip()
                    result.append(label)

                return result

            except Exception as e:
                print(f"get_service_type_dropdown_options failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return []

    
    def click_provisioning_tab(self, port_number, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Navigate to Configuration -> Port -> Provisioning tab.

        Args:
            port_number:
                Examples: 1, "1", "Port-1"

        Returns:
            True if the Provisioning tab is active and its page (config_port iframe) is loaded,
            False otherwise.
        """

        def main_fl():
            return self.main_page_frame()

        def port_cfg_fl():
            return main_fl().frame_locator("iframe[name='config_port'], iframe#config_port")

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

                # The Provisioning screen is one of the Config_Port_Pro*.asp pages (product dependent)
                cfg_iframe = main_fl().locator("iframe[name='config_port'], iframe#config_port").first
                expect(cfg_iframe).to_have_attribute("src", re.compile(r"Config_Port_Pro"), timeout=timeout)

                expect(port_cfg_fl().locator("body").first).to_be_visible(timeout=timeout)
                return True

            except Exception as e:
                print(f"click_provisioning_tab failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return False

    def get_provisioning_table(self, port_number, retries: int = 5, timeout: int = 10_000) -> Optional[dict]:
        """
        Read the Provisioning tab of a port (Configuration -> Port -> Provisioning).

        Args:
            port_number:
                Examples: 1, "1", "Port-1"

        Returns:
            dict, e.g.:
                {
                    "service": "10GbE-LAN",            # from the "For <service> service, ..." guide text
                    "max_slots": 8,                    # None when provisioning is not needed (auto-provisioned)
                    "provisioned": True,               # this port has slots provisioned
                    "uplink": 1,                       # provisioned uplink (1/2), None if not provisioned
                    "protection": "Facility",          # "Facility" / "Equipment" / None
                    "facility_protection": True,
                    "provisioned_slots": [1, 2, ..., 8],
                    "slots": [
                        {"slot": 1, "checked": True, "enabled": False, "state": "this_port"},
                        {"slot": 9, "checked": False, "enabled": True, "state": "free"},
                        ...
                    ],
                }

            slot "state" is one of (matches the page Legend):
                "this_port"    - Occupied by this port            (class 'prov')
                "another_port" - Occupied by another port         (class 'local')
                "pass_through" - Occupied by Pass-through service (class 'passthru')
                "free"         - Free

            None if failed.
        """

        def main_fl():
            return self.main_page_frame()

        def port_cfg_fl():
            return main_fl().frame_locator("iframe[name='config_port'], iframe#config_port")

        class_to_state = {
            "prov": "this_port",
            "local": "another_port",
            "passthru": "pass_through",
        }

        def read_slots(cfg):
            # Slot checkboxes: id='slot<N>' (0-based, N=0..79) -> UI label N+1.
            # Row-select "==>" checkboxes also use id='slot<(8*row+1)*100>' (slot100, slot900, ...) -> skipped.
            # Legend checkboxes have no id -> not matched.
            rows = cfg.locator("input[type='checkbox'][id^='slot']").evaluate_all("""
                els => els.map(el => ({
                    id: el.id,
                    checked: el.checked,
                    disabled: el.disabled,
                    cls: el.className || ''
                }))
            """)

            result = []
            for r in rows:
                m = re.fullmatch(r"slot(\d+)", r["id"])
                if not m:
                    continue
                idx = int(m.group(1))
                if idx >= 100 and idx % 100 == 0:
                    continue  # row-select checkbox

                state = "free"
                for cls in r["cls"].split():
                    if cls in class_to_state:
                        state = class_to_state[cls]
                        break

                result.append({
                    "slot": idx + 1,
                    "checked": bool(r["checked"]),
                    "enabled": not r["disabled"],
                    "state": state,
                })

            result.sort(key=lambda x: x["slot"])
            return result

        def read_checked_uplink(cfg) -> Optional[int]:
            radios = cfg.locator("input[type='radio'][name='uplink']")
            count = radios.count()
            for i in range(count):
                radio = radios.nth(i)
                if radio.is_checked():
                    try:
                        return int((radio.get_attribute("value") or "").strip())
                    except ValueError:
                        return i + 1
            return None

        def read_protection(cfg) -> Optional[str]:
            # Page writes a red <font> "Facility Protection" / "Equipment Protection" only when that mode is set
            for mode in ("Facility", "Equipment"):
                labels = cfg.locator("font", has_text=re.compile(rf"{mode}\s+Protection", re.IGNORECASE))
                count = labels.count()
                for i in range(count):
                    if labels.nth(i).is_visible():
                        return mode
            return None

        for attempt in range(retries):
            try:
                if not self.click_provisioning_tab(port_number, timeout=timeout):
                    raise AssertionError(f"click_provisioning_tab failed for {port_number}")

                cfg = port_cfg_fl()
                body = cfg.locator("body").first
                expect(body).to_be_visible(timeout=timeout)

                guide_txt = (cfg.locator("span.blu12").first.inner_text() or "").strip()

                service = None
                max_slots = None
                m = re.search(r"For\s+(.+?)\s+service,\s*select\s+(?:up\s+to\s+)?(\d+)\s+slots?", guide_txt, re.IGNORECASE)
                if m:
                    service = m.group(1).strip()
                    max_slots = int(m.group(2))
                else:
                    # Auto-provisioned services: "For <service> service provisioning is not needed"
                    m = re.search(r"For\s+(.+?)\s+service\s+provisioning\s+is\s+not\s+needed", guide_txt, re.IGNORECASE)
                    if m:
                        service = m.group(1).strip()

                slots = read_slots(cfg)
                if not slots:
                    raise Exception("No provisioning slot checkboxes were found")

                provisioned_slots = [s["slot"] for s in slots if s["state"] == "this_port"]
                provisioned = bool(provisioned_slots)

                # When the port is not provisioned the page pre-checks Uplink 1 by default,
                # so the radio only reflects the provisioned uplink when provisioned.
                uplink = read_checked_uplink(cfg) if provisioned else None

                protection = read_protection(cfg)

                return {
                    "service": service,
                    "max_slots": max_slots,
                    "provisioned": provisioned,
                    "uplink": uplink,
                    "protection": protection,
                    "facility_protection": protection == "Facility",
                    "provisioned_slots": provisioned_slots,
                    "slots": slots,
                }

            except Exception as e:
                print(f"get_provisioning_table failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return None

    def get_provisioning_all_uplinks(self, port_number, retries: int = 5, timeout: int = 10_000) -> Optional[dict]:
        """
        Read the slot map of EVERY uplink from the Provisioning tab of 'port_number'.

        The old GUI draws a single slot grid (slot0..slot79) that MERGES both uplinks - genSlots()
        marks a slot as taken when any port holds it on Uplink 1 OR Uplink 2 - and shows the uplink
        only as a radio button. So the drawn grid cannot tell the uplinks apart.

        The page (Config_Port_Pro*.asp) carries the raw per-uplink data as globals, the same data the
        grid is drawn from:
            provArray[uplink][port] -> 10 bytes, bit (byte*8 + bit) = slot index (slot = index + 1)
            msi[uplink - 1][index]  -> non-zero (and not 0xFF) = slot in use on the uplink (pass-through
                                       when no local port holds it)
        so every uplink is decoded from that. Same output shape as the new-GUI
        PL_main_screen_POM_new_gui.get_provisioning_all_uplinks(), except "owner" (always None here).

        Args:
            port_number:
                Examples: 3, "3", "Port-3"

        Returns:
            dict, e.g.:
                {
                    "port": "3",
                    "selected_uplink_tab": 1,           # checked uplink radio (meaningful when provisioned)
                    "protection": "Facility",           # "Facility" / "Equipment" / None
                    "facility_protection_active": None, # the old GUI does not show the APS active line
                    "source": "raw",
                    "uplinks": {
                        1: [{"slot": 1, "state": "another_port", "owner": None},
                            {"slot": 9, "state": "this_port", "owner": None}, ...],
                        2: [{"slot": 1, "state": "another_port", "owner": None},
                            {"slot": 9, "state": "this_port", "owner": None}, ...],
                    },
                }
            slot "state" as in get_provisioning_table(). "owner" is always None: unlike the new GUI
            (data-port badge), the old GUI does not show which port occupies an 'another_port' slot.
            None if failed.
        """

        def main_fl():
            return self.main_page_frame()

        def port_cfg_fl():
            return main_fl().frame_locator("iframe[name='config_port'], iframe#config_port")

        m_port = re.search(r"\d+", str(port_number))
        if not m_port:
            print(f"get_provisioning_all_uplinks: invalid port '{port_number}'")
            return None
        this_port = int(m_port.group(0))

        def read_uplink_ids(cfg) -> List[int]:
            ids = []
            radios = cfg.locator("input[type='radio'][name='uplink']")
            for i in range(radios.count()):
                try:
                    ids.append(int((radios.nth(i).get_attribute("value") or "").strip()))
                except ValueError:
                    ids.append(i + 1)
            return sorted(set(ids))

        def read_checked_uplink(cfg) -> Optional[int]:
            radios = cfg.locator("input[type='radio'][name='uplink']")
            for i in range(radios.count()):
                radio = radios.nth(i)
                if radio.is_checked():
                    try:
                        return int((radio.get_attribute("value") or "").strip())
                    except ValueError:
                        return i + 1
            return None

        def read_protection(cfg) -> Optional[str]:
            # Page writes a red <font> "Facility Protection" / "Equipment Protection" only when that mode is set
            for mode in ("Facility", "Equipment"):
                labels = cfg.locator("font", has_text=re.compile(rf"{mode}\s+Protection", re.IGNORECASE))
                for i in range(labels.count()):
                    if labels.nth(i).is_visible():
                        return mode
            return None

        def read_raw(cfg, uplink_ids):
            # Page globals: provArray / msi (see docstring). evaluate() runs in the config_port frame.
            raw = cfg.locator("body").first.evaluate("""
                (_body, uplinkIds) => {
                    if (typeof provArray === 'undefined' || typeof msi === 'undefined') return null;
                    const ids = (uplinkIds && uplinkIds.length) ? uplinkIds
                              : Array.from(provArray.keys()).filter(u => u > 0 && provArray[u]);
                    // Slot boxes: id='slot<N>' (0-based); row-select boxes are slot100, slot900, ... -> skipped
                    const nSlots = Array.from(document.querySelectorAll("input[type='checkbox'][id^='slot']"))
                        .filter(el => {
                            const m = /^slot(\\d+)$/.exec(el.id);
                            return m && !(+m[1] >= 100 && +m[1] % 100 === 0);
                        }).length;
                    const out = {};
                    for (const u of ids) {
                        if (!provArray[u]) return null;
                        const ports = {};
                        for (let p = 1; p < provArray[u].length; p++) {
                            ports[p] = Array.from(provArray[u][p] || [], v => Number.isFinite(v) ? v : 0);
                        }
                        out[u] = {nSlots: nSlots, ports: ports, msi: Array.from(msi[u - 1] || [], v => Number(v) || 0)};
                    }
                    return out;
                }
            """, uplink_ids)
            if not raw:
                return None

            uplinks = {}
            for key, data in raw.items():
                uplink = int(key)
                if not data or not data["nSlots"]:
                    return None
                slots = []
                for index in range(data["nSlots"]):
                    byte, bit = divmod(index, 8)
                    owners = [int(p) for p, bytes_ in data["ports"].items()
                              if byte < len(bytes_) and (bytes_[byte] or 0) & (1 << bit)]
                    msi_val = data["msi"][index] if index < len(data["msi"]) else 0
                    if this_port in owners:
                        state, owner = "this_port", None
                    elif owners:
                        state = "another_port"
                    elif msi_val not in (0, 0xFF):
                        state = "pass_through"
                    else:
                        state = "free"
                    # The old GUI does not show which port occupies an 'another_port' slot
                    # (genSlots writes only class=local) -> owner is always None, like the screen.
                    slots.append({"slot": index + 1, "state": state, "owner": None})
                uplinks[uplink] = slots
            return dict(sorted(uplinks.items()))

        for attempt in range(retries):
            try:
                if not self.click_provisioning_tab(port_number, timeout=timeout):
                    raise AssertionError(f"click_provisioning_tab failed for {port_number}")

                cfg = port_cfg_fl()
                expect(cfg.locator("body").first).to_be_visible(timeout=timeout)

                uplinks = read_raw(cfg, read_uplink_ids(cfg))
                if not uplinks:
                    raise Exception("The page has no provArray/msi slot data (or no slot boxes)")

                protection = read_protection(cfg)

                return {
                    "port": str(port_number),
                    "selected_uplink_tab": read_checked_uplink(cfg),
                    "protection": protection,
                    "facility_protection_active": None,
                    "source": "raw",
                    "uplinks": uplinks,
                }

            except Exception as e:
                print(f"get_provisioning_all_uplinks failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return None

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
    def add_sntp_server(self, ip: str, protocol: str = "SNTP", key_id=None, key_value=None, 
    skip_protocol_and_key_and_value=False, retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
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

            skip_protocol_and_key_and_value:
                If True -> skip protocol selection, key_id selection and key_value fill.

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

                if skip_protocol_and_key_and_value == False:
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

                else:
                    pass

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

    def click_inventory(self, retries: int = 3, timeout: int = 20_000) -> bool:
        """
        Click the Inventory tab under Configuration -> System.

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

                btn = main_fl.locator("#tab_inventory").first
                expect(btn).to_be_visible(timeout=timeout)

                cls = (btn.get_attribute("class") or "").strip()
                if cls != "tab tabactive":
                    btn.scroll_into_view_if_needed()
                    btn.click(force=True, timeout=timeout)

                expect(btn).to_have_attribute("class", "tab tabactive", timeout=timeout)

                return True

            except Exception as e:
                print(f"click_inventory failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return False

    def get_inventory_list(self, retries: int = 3, timeout: int = 20_000) -> Optional[List[Dict[str, str]]]:
        """
        Read the inventory table under Configuration -> System -> Inventory.

        Returns:
            List of dicts, one per row, keyed by the table headers
            (Name, Description, Serial Number, Hardware Rev, Part Number, Manufacturer), e.g.:
                {"Name": "PSU 1", "Description": "AC Power Interface Card",
                 "Serial Number": "WC2127RE000V", "Hardware Rev": "00-00",
                 "Part Number": "D1U54P-W-650-12-HB4BC", "Manufacturer": "PacketLight Networks"}
            Cell text is whitespace-normalized (multi-line cells are joined with single spaces).
            None on failure.
        """

        # Collect every <tr> as a list of cell texts; header/data rows are picked in Python
        rows_js = """
        () => Array.from(document.querySelectorAll('tr')).map(tr =>
            Array.from(tr.querySelectorAll(':scope > th, :scope > td')).map(c => (c.innerText || c.textContent || ''))
        )
        """

        def norm(s: str) -> str:
            return re.sub(r"\s+", " ", s or "").strip()

        for attempt in range(retries):
            try:
                if not self.click_inventory(timeout=timeout):
                    raise Exception("click_inventory failed")

                inv_fl = self.main_page_frame().frame_locator("iframe[name='config_sys'], iframe#config_sys")
                expect(inv_fl.locator("tr", has_text="Serial Number").first).to_be_visible(timeout=timeout)

                cfg = self.page.frame(name="config_sys")
                if cfg is None:
                    raise Exception("config_sys frame not found")

                rows = [[norm(c) for c in r] for r in cfg.evaluate(rows_js)]

                header_idx = next(
                    (i for i, r in enumerate(rows) if "Name" in r and "Serial Number" in r),
                    None,
                )
                if header_idx is None:
                    raise Exception("Inventory table header row not found")

                headers = rows[header_idx]
                inventory = []
                for r in rows[header_idx + 1:]:
                    if len(r) != len(headers) or not any(r):
                        continue
                    inventory.append(dict(zip(headers, r)))

                return inventory

            except Exception as e:
                print(f"get_inventory_list failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return None

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
                    if not self.upper_panel.click_system(timeout=timeout): 
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