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
    def set_admin_status(self, port_number, status: str, action_dismiss: bool = False, retries: int = 5, timeout: int = 10_000):
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