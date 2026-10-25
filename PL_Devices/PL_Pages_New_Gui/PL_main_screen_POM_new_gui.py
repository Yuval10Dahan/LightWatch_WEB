'''
Created by: Yuval Dahan
Date: 03/08/2026
'''


from playwright.sync_api import Page, expect
from typing import Optional, Tuple 
from PL_Devices.PL_Pages_New_Gui.PL_upper_panel_new_gui import PL_Upper_Panel
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
                # New GUI wraps #faultTab in a <div> (header/body split into separate
                # #thead/#tbody <table>s), same pattern as SNMP Traps/Security Users --
                # #faultTab itself still resolves fine either way, and "tbody tr" still
                # only matches real data rows (header cells are <th>, filtered out below).
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
                # See alarms_table(): #faultTab is unaffected by the id being a <div> now.
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
                sleep(1)
                expect(btn).to_be_visible(timeout=timeout)

                cls = (btn.get_attribute("class") or "").strip()
                if cls != "tab tabactive":
                    btn.scroll_into_view_if_needed()
                    sleep(1)
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

                # New GUI changed this field's tag from <input type="text"> to <textarea> --
                # drop the tag qualifier so the same selector matches either GUI version.
                chassis_input = cfg.locator("[name='slmSysChassisId']").first
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
                new_value = (cfg.locator("[name='slmSysChassisId']").first.input_value() or "").strip()

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
                sleep(1)

                config_sys = main_frame.frame_locator("iframe[name='config_sys']")
                sleep(1)

                # New GUI dropped table#gen_sys_info_table entirely -- Product Name is now a
                # plain <span class="label_text">Product Name</span> followed by a sibling
                # <span class="value_text">. Try the new layout first, fall back to the old
                # table-based layout for products/versions that never got the redesign.
                product_cell = config_sys.locator(
                    "xpath=//span[contains(@class,'label_text') and normalize-space()='Product Name']"
                    "/following-sibling::span[contains(@class,'value_text')][1]"
                ).first
                sleep(1)

                if product_cell.count() == 0:
                    product_cell = config_sys.locator(
                        "xpath=//table[@id='gen_sys_info_table']//td[contains(normalize-space(),'Product Name')]/following-sibling::td[1]"
                    ).first
                    sleep(1)

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

        New GUI replaced the separate #green_button/#red_button pair with a single
        toggle checkbox (id="admin_toggle") inside #formMaintXpdrAdmin -- clicking it
        flips the current state (there's no "set to up" vs "set to down" element
        anymore, so we always click the toggle once we know current != desired).
        The raw checkbox has a zero-size bounding box (custom toggle-switch CSS), so
        the click must land on its wrapping label.custom-toggle, same lesson as the
        Security Users enable/disable toggle. Falls back to the old #green_button/
        #red_button pair for any port-type page that never adopted the toggle.

        NOTE: adjusted from a structural HTML diff and the same toggle-click lesson
        already confirmed working on the Security Users page, but NOT itself
        exercised against real hardware -- toggling a live port's admin status would
        risk disrupting real traffic/services on this shared lab device. Verify on a
        known-idle port before relying on it.

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

        def get_admin_toggle_label(ctx):
            """
            Returns (label_locator, is_new_toggle). New GUI: single toggle checkbox,
            clicking it always flips state. Old GUI: separate directional buttons.
            """
            toggle_label = ctx.locator("#formMaintXpdrAdmin label.custom-toggle, label.custom-toggle").first
            if toggle_label.count() > 0:
                return toggle_label, True

            if desired_status == "up":
                return ctx.locator("#formMaintXpdrAdmin #green_button, #green_button").first, False
            return ctx.locator("#formMaintXpdrAdmin #red_button, #red_button").first, False

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

                btn, _is_toggle = get_admin_toggle_label(ctx)

                expect(btn).to_be_visible(timeout=timeout)

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
                    # result.append((value, label))
                    result.append(label)

                return result

            except Exception as e:
                print(f"get_service_type_dropdown_options failed (attempt {attempt + 1}): {e}")
                try:
                    self.page.wait_for_timeout(1000)
                except Exception:
                    pass

        return []

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

            # Single-uplink ports (e.g. PL4000M port config) render no uplink radio
            # buttons at all -- there's nothing to select, so treat uplink_number as
            # already satisfied rather than raising.
            if count == 0:
                return

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

                make_btn = cfg.locator("#make_break, input[name='make_break'], input.prov_but").first
                if make_btn.count() == 0:
                    raise Exception("Make Provisioning button not found on the Provisioning page")

                # The device's own SetProvisioningButtonsText() sets #make_break's
                # visibility:hidden whenever the port's Service Type is still "None" --
                # there is nothing to provision until a real service type is assigned.
                # Detect that directly instead of burning the full visibility timeout
                # on every retry with an opaque "expected visible, got hidden" error.
                if not make_btn.is_visible():
                    raise Exception(
                        f"Cannot provision port {port_number}: no Service Type is assigned "
                        f"('Make Provisioning' stays hidden until set_service_type() is called)"
                    )

                # Already provisioned -> continue successfully
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
            These are rendered as class='prov' and checked+disabled.

            New GUI ids these "up1_slot0", "up2_slot3", etc. (old GUI: "slot9") --
            match on the '.prov' class alone and let the regex pull the number from
            wherever "slot" appears in the id, instead of requiring id^='slot'.
            """
            slots = cfg.locator("input[type='checkbox'].prov")
            result = []
            count = slots.count()

            for i in range(count):
                cb = slots.nth(i)
                try:
                    slot_id = (cb.get_attribute("id") or "").strip()   # e.g. slot9 or up1_slot0
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

        New GUI moved the add-server fields out of the inline last table row into a
        modal (#addServerModal) opened via an "Add Server [+]" button, whose JS
        relocates the modal to the top-level page (same pattern as SNMP Add-Manager /
        Security Add-User) -- fields must be addressed via self.page once opened.
        Falls back to the old inline-row flow when the modal-open button isn't found.

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
                    sleep(1)
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

        def open_add_server_modal(cfg) -> bool:
            try:
                open_btn = cfg.locator("button[onclick='openAddServerModal()']").first
                if open_btn.count() == 0:
                    return False
                expect(open_btn).to_be_visible(timeout=2_000)
                sleep(1)
                open_btn.click(force=True)
                expect(self.page.locator("#addServerModal").first).to_be_visible(timeout=timeout)
                return True
            except Exception:
                return False

        for attempt in range(retries):
            try:
                if not self.click_time(timeout=timeout):
                    raise Exception("click_time failed")

                self.page.wait_for_timeout(500)

                cfg = time_config_frame()
                sleep(0.5)

                use_modal = open_add_server_modal(cfg)
                ctx = self.page if use_modal else cfg

                # ---- Locate fields ----
                ip_field = ctx.locator("input[name='ip_address']").first
                sleep(0.5)
                expect(ip_field).to_be_visible(timeout=timeout)

                if use_modal:
                    row = ctx  # fields are flat inside the relocated modal, not a <tr>
                else:
                    row = ip_field.locator("xpath=./ancestor::tr[1]")
                sleep(0.5)

                # IP
                sleep(1)
                ip_field.fill(ip)

                if skip_protocol_and_key_and_value == False:
                    # Protocol
                    protocol_select = (
                        ctx.locator("select#slSntpConfigVersion, select[name='slSntpConfigVersion']").first
                        if use_modal
                        else row.locator("xpath=./td[position()=2]//select").first
                    )
                    sleep(0.5)
                    expect(protocol_select).to_be_visible(timeout=timeout)
                    protocol_select.select_option(label=protocol)

                    # Key ID
                    if key_id not in (None, ""):
                        key_id_el = (
                            ctx.locator("[name='slSntpConfigServerKeyId']").first
                            if use_modal
                            else row.locator("xpath=./td[position()=3]//input[not(@type='hidden')]").first
                        )
                        sleep(0.5)
                        expect(key_id_el).to_be_visible(timeout=timeout)
                        key_id_el.fill(str(key_id))

                    # Key Value
                    if key_value not in (None, ""):
                        key_value_el = (
                            ctx.locator("[name='slSntpConfigServerKeyVal']").first
                            if use_modal
                            else row.locator("xpath=./td[position()=4]//input[not(@type='hidden')]").first
                        )
                        sleep(0.5)
                        expect(key_value_el).to_be_visible(timeout=timeout)
                        key_value_el.fill(str(key_value))

                else:
                    pass

                # ---- Click Add ----
                if use_modal:
                    add_btn = self.page.locator("#btnSubmitAddServer").first
                    sleep(1)
                else:
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

        New GUI removed the separate #sntp_tz_sel timezone dropdown (whose option
        labels were "GMT+2"-style text). It's replaced by #combined_tz_sel, whose
        options are keyed by an "hour_minute" VALUE (e.g. "2_0", "-5_30") and a
        "+2:00"/"-5:30" display label -- selecting it drives the old hidden
        slSntpConfigTimeZone/slSntpConfigFractTimeZone fields via JS. gmt still
        accepts the old "GMT+2" style (or "+2:30", "2", etc.) -- it's parsed into
        (hours, minutes) and matched against #combined_tz_sel's option VALUE so the
        input format callers already use doesn't need to change.

        Args:
            status:
                Supported values:
                    "Enable", "Enabled", "Disable", "Disabled"

            gmt:
                Optional timezone offset, for example: "GMT+2", "+2:30", "-5", "0"

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

        def parse_gmt_offset(gmt_str) -> Tuple[int, int]:
            s = str(gmt_str).strip().upper().replace("GMT", "").replace("UTC", "").strip()
            m = re.match(r"^([+-]?\d+)(?::(\d+))?$", s)
            if not m:
                raise ValueError(f"Unrecognized GMT offset format: '{gmt_str}'")
            hours = int(m.group(1))
            minutes = int(m.group(2)) if m.group(2) else 0
            return hours, minutes

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

                # New GUI: combined "+H:MM" dropdown replaces the old #sntp_tz_sel select.
                tz_sel = cfg.locator("#combined_tz_sel").first
                using_combined_tz = tz_sel.count() > 0
                if not using_combined_tz:
                    tz_sel = cfg.locator("#sntp_tz_sel").first
                expect(tz_sel).to_be_visible(timeout=timeout)

                daylight_sel = cfg.locator("#sntp_dls_sel").first
                expect(daylight_sel).to_be_visible(timeout=timeout)

                # Read current values first
                current_status = (sntp_enable_sel.locator("option:checked").inner_text() or "").strip()
                current_daylight = (daylight_sel.locator("option:checked").inner_text() or "").strip()

                if using_combined_tz:
                    current_tz_value = (tz_sel.input_value() or "").strip()  # e.g. "2_0"
                else:
                    current_tz_value = (tz_sel.locator("option:checked").inner_text() or "").strip()

                desired_tz_value = None
                if gmt not in (None, ""):
                    if using_combined_tz:
                        hours, minutes = parse_gmt_offset(gmt)
                        desired_tz_value = f"{hours}_{minutes}"
                    else:
                        desired_tz_value = str(gmt).strip()

                # Nothing to change -> succeed immediately
                nothing_to_change = (
                    current_status == status_value
                    and (desired_tz_value is None or current_tz_value == desired_tz_value)
                    and (daylight_value is None or current_daylight == daylight_value)
                )
                if nothing_to_change:
                    return True, ""

                # Enable / Disable
                if current_status != status_value:
                    sntp_enable_sel.select_option(label=status_value)

                # GMT / Time zone
                if desired_tz_value is not None and current_tz_value != desired_tz_value:
                    if using_combined_tz:
                        tz_sel.select_option(value=desired_tz_value)
                    else:
                        tz_sel.select_option(label=desired_tz_value)

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
    def device_restart_old(self, restart_type: str, action_dismiss: bool = False, retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
        """
        Playwright version of Device_Restart for the new GUI, under:
            Maintenance -> Restart tab

        Args:
            restart_type: 'cold' | 'warm' | 'factory' | 'shutdown'
            action_dismiss: if True -> dismiss the confirm() dialog (Cancel), nothing
                is submitted. If False -> accept it (OK) and follow through with the
                actual restart/shutdown.
            retries: retries for navigation/click stability
            timeout: playwright timeout in ms

        New GUI change: clicking the restart image button (#cold_restart /
        #warm_restart / #restart_factory / #shutdown, same ids as the old GUI)
        still raises the same native browser confirm() dialog, handled here the
        same way as the old GUI. But accepting it no longer navigates/submits the
        frame -- submitRestartForm() fires an async XHR instead and shows a
        #statusModal overlay whose own JS reparents it out of the maint_sys iframe
        onto the TOP-LEVEL page (`(parentFrame || window.top).document.body
        .appendChild(modal)`). So once the dialog is accepted, the modal must be
        read from self.page directly -- a frame_locator into maint_sys will not
        see it anymore. The modal's message text is the source of truth: it
        settles on "...System is restarting..." / "...shutting down..." (no Close
        button) on success, or one of "is forbidden" / "not allowed" / "failed"
        (Close button shown) on failure. This does not wait for the page's own
        180s auto-reload -- it just confirms the action was initiated and
        returns, leaving "wait for the device to come back up" to the caller
        (Device_Is_Up / devices_are_up in Utils/utils.py).

        Returns:
            (success, message)
                success=True when the dialog was handled as requested AND, for
                    action_dismiss=False, the status modal confirms the action
                    was initiated (not one of the forbidden/not-allowed/failed
                    responses).
                message is the confirm() dialog text when action_dismiss=True,
                    otherwise the modal's settled status text (or '' if neither
                    was captured).
        """
        rt = (restart_type or "").strip().lower()
        if rt == "cold":
            reset_type_id = "cold_restart"
        elif rt == "warm":
            reset_type_id = "warm_restart"
        elif rt == "factory":
            reset_type_id = "restart_factory"
        elif rt == "shutdown":
            reset_type_id = "shutdown"
        else:
            return False, ""

        FAILURE_MARKERS = ("is forbidden", "not allowed", "failed")
        SUCCESS_MARKERS = ("restarting", "shutting down")

        def arm_dialog_capture_once() -> dict:
            holder = {"text": None}

            def _handler(d):
                holder["text"] = (d.message or "").strip()
                
                try:
                    if action_dismiss:
                        d.dismiss()
                    else:
                        d.accept()
                except Exception:
                    try:
                        d.accept()
                    except Exception:
                        pass

            try:
                self.page.once("dialog", _handler)
            except Exception:
                pass
            return holder

        def wait_for_dialog_text(holder: dict, ms: int = 5000) -> Optional[str]:
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

        def wait_for_status_modal_result(ms: int = 15000) -> Tuple[str, bool]:
            """
            Polls the (reparented, top-level) status modal until it settles on a
            recognized success/failure message.

            Returns:
                (message_text, is_failure)
            """
            step = 250
            loops = max(1, ms // step)
            msg_loc = self.page.locator("#statusModalMessage").first
            close_btn = self.page.locator("#statusModalCloseBtn").first

            for _ in range(loops):
                try:
                    if msg_loc.count() > 0:
                        text = (msg_loc.inner_text() or "").strip()
                        lower = text.lower()

                        if any(m in lower for m in FAILURE_MARKERS):
                            return text, True

                        if any(m in lower for m in SUCCESS_MARKERS):
                            return text, False

                        # Close button visible with no recognized success marker
                        # yet still means the server rejected the request.
                        close_style = (close_btn.get_attribute("style") or "") if close_btn.count() > 0 else ""
                        if text and "none" not in close_style and ("flex" in close_style or "block" in close_style):
                            return text, True
                except Exception:
                    pass

                self.page.wait_for_timeout(step)

            return "", True

        def resolve_reset_button(ms: int = 12000):
            """
            Re-derives maintenance_frame() fresh on every poll instead of resolving
            it once -- ActivateTab() reassigns #maint_sys's src and only settles it
            via its own 250ms setTimeout (see the iframe's onload in
            Maint_System*.asp), and click_system() immediately before
            click_maintenance() can still have a main_page navigation in flight when
            we get here. A single frame_locator().locator() grabbed too early can
            end up pointed at whatever main_page was showing mid-transition, so this
            polls for the actual button, and if it never shows up, self-heals by
            re-clicking the Restart tab (in case #tab_restart never really made it
            back to active) before trying again.
            """
            step = 300
            loops = max(1, ms // step)
            re_clicked_tab = False

            for i in range(loops):
                try:
                    btn = self.maintenance_frame().locator(f"#{reset_type_id}").first
                    if btn.count() > 0 and btn.is_visible() and btn.is_enabled():
                        # print(f"btn: {btn}")
                        return btn
                except Exception:
                    pass

                # Halfway through the poll window with nothing found yet -- the
                # Restart tab likely never (re)loaded into #maint_sys. Try once to
                # nudge it back into place instead of waiting out the full timeout.
                if not re_clicked_tab and i == loops // 2:
                    re_clicked_tab = True
                    try:
                        tab_restart = self.main_page_frame().locator("#tab_restart").first
                        tab_restart.scroll_into_view_if_needed()
                        tab_restart.click(force=True, timeout=2000)
                    except Exception:
                        pass

                self.page.wait_for_timeout(step)

            raise AssertionError(
                f"Restart button '#{reset_type_id}' never appeared in maintenance_frame() "
                f"after {ms}ms"
            )

        success = False
        message = ""

        for attempt in range(retries):
            try:
                if not self.upper_panel.click_system(timeout=timeout):
                    raise AssertionError("click_system_btn failed")

                if not self.click_maintenance(timeout=timeout):
                    raise Exception("click_maintenance failed")

                main_fl = self.main_page_frame()

                tab_restart = main_fl.locator("#tab_restart").first
                expect(tab_restart).to_be_visible(timeout=timeout)

                if (tab_restart.get_attribute("class") or "").strip() != "tab tabactive":
                    tab_restart.scroll_into_view_if_needed()
                    tab_restart.click(force=True, timeout=timeout)
                    expect(tab_restart).to_have_attribute("class", "tab tabactive", timeout=timeout)

                reset_btn = resolve_reset_button(ms=max(timeout, 12000))

                dlg_holder = arm_dialog_capture_once()

                reset_btn.scroll_into_view_if_needed()
                reset_btn.click(force=True, timeout=timeout)

                dialog_text = wait_for_dialog_text(dlg_holder, ms=5000) or ""
                # print(f"Device Restart dialog text: '{dialog_text}'")

                if dialog_text == "":
                    # confirmRestart() returns false without ever calling confirm()
                    # when checkReadOnly() fails first -- most likely a read-only user.
                    raise AssertionError(
                        "No confirm() dialog appeared after clicking restart button "
                        "(possibly a read-only user)"
                    )

                if action_dismiss:
                    success = True
                    message = dialog_text
                    break

                # Confirm accepted -- submitRestartForm() fires the XHR and shows
                # the reparented, top-level status modal.
                modal_text, is_failure = wait_for_status_modal_result(ms=15000)

                if is_failure:
                    return False, modal_text or dialog_text

                success = True
                message = modal_text
                break

            except Exception as e:
                print(f"{attempt + 1} attempt, for Device Restart, failed: {e}")
                try:
                    self.reload()
                except Exception:
                    pass
                continue

        return success, message

    # ✅
    def device_restart(self, restart_type: str, action_dismiss: bool = False, retries: int = 5, timeout: int = 10_000) -> Tuple[bool, str]:
        """
        Playwright version of Device_Restart (robust against duplicate dialog handlers).

        restart_type: 'cold' | 'warm' | 'factory' | 'shutdown'
        action_dismiss:
            True  -> dismiss dialog (Cancel)
            False -> accept dialog (OK)

        NOTE: button ids (#cold_restart/#warm_restart/#restart_factory/#shutdown) are
        unchanged in the new GUI, but the submission mechanism changed from a
        blocking form POST to an async XMLHttpRequest that shows a relocated status
        modal (#statusModal / #statusModalMessage) instead of navigating away. This
        method additionally waits for that modal as a completion signal, alongside
        the original dialog-capture logic (which still applies -- confirmRestart()/
        the underlying confirm() flow is unchanged). This was adjusted from the
        structural diff alone -- unlike every other method in this file, it was NOT
        exercised against real hardware, since actually clicking any of these
        buttons reboots a shared lab device. Verify carefully before relying on it.

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

        def wait_for_status_modal(ms: int = 5000) -> Optional[str]:
            """
            New GUI: after confirming, an async XHR fires and a relocated
            #statusModal/#statusModalMessage appears on the top-level page instead
            of a normal navigation. Returns its message text if it showed up.
            """
            try:
                modal = self.page.locator("#statusModal").first
                modal.wait_for(state="visible", timeout=ms)
                msg = self.page.locator("#statusModalMessage").first
                return (msg.inner_text() or "").strip()
            except Exception:
                return None

        for attempt in range(retries):
            try:
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

                # Restart button is input type=image by ID (unchanged in new GUI)
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

                # New GUI: the confirm() being accepted fires an async XHR and shows
                # #statusModal instead of navigating -- pick up its text if present.
                status_txt = wait_for_status_modal(ms=5000)
                if status_txt:
                    return True, status_txt

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
