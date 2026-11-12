"""
Created by: Yuval Dahan
Date: 28/10/2026
""" 


from playwright.sync_api import Page, Locator, expect
import re


class Inventory:
    """
    Page Object Model for the Inventory screen: Filter By / Quick filter / Whole word,
    the expandable inventory table and the Refresh / Expand All / Save All Inventory buttons.
    """

    # Table columns, in the order they appear (the first one is the Expand / row-number cell)
    COLUMNS = ["row", "entity", "ip_address", "class", "hw_ver", "sw_ver",
               "fw_ver", "part_number", "serial_no", "fru", "manufacturer"]

    def __init__(self, page: Page):
        """
        Initialize Inventory with Playwright page instance.
        """
        self.page = page
        self.root = page.locator("app-inventory")
        self.filter_by = self.root.locator('app-dropdown[formcontrolname="filterBy"]')
        self.devices = self.root.locator('app-dropdown[formcontrolname="device"]')
        self.chassis = self.root.locator('app-dropdown[formcontrolname="chassis"]')
        self.quick_filter = self.root.locator('app-input[formcontrolname="query"] input')
        self.whole_word = self.root.locator('app-checkbox[formcontrolname="wholeWord"]')
        self.table = self.root.locator("app-inventory-table table")
        self.rows = self.table.locator("tbody > tr")
        actions = self.root.locator(".inventory-actionWrapper-actions")
        self.refresh_button = actions.locator("button").filter(has_text=re.compile(r"^\s*Refresh\s*$"))
        self.expand_all_button = actions.locator("button").filter(has_text=re.compile(r"^\s*Expand All\s*$"))
        # The same button toggles between "Expand All" and "Collapse All" (the app's DOM
        # spells it "Collaplse All"), so match any spelling
        self.collapse_all_button = actions.locator("button").filter(has_text=re.compile(r"^\s*Colla\w*se All\s*$"))
        self.save_button = actions.locator("button").filter(has_text=re.compile(r"^\s*Save All Inventory\s*$"))
        # Only rendered when Filter By = Device and a device is selected
        self.save_device_button = actions.locator("button").filter(has_text=re.compile(r"^\s*Save Device Inventory\s*$"))


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
    def _read_rows(self) -> list[dict]:
        """
        Read every row currently in the table body. Entity rows (the numbered ones,
        'pl-bold') come first; expanded child rows follow their entity row.
        """
        raw = self.rows.evaluate_all("""trs => trs.map(tr => ({
            bold: tr.classList.contains('pl-bold'),
            cells: Array.from(tr.querySelectorAll(':scope > td')).map(td => ({
                text: (td.innerText || '').replace(/\\s+/g, ' ').trim(),
                spans: Array.from(td.querySelectorAll('span')).map(s => (s.innerText || '').trim())
            }))
        }))""")
        result = []
        for r in raw:
            cells = r["cells"]
            row = {"is_child": not r["bold"]}
            for idx, key in enumerate(self.COLUMNS):
                if idx >= len(cells):
                    row[key] = ""
                    if key == "entity":
                        row["description"] = ""
                    elif key == "ip_address":
                        row["system_name"] = ""
                    continue
                cell = cells[idx]
                if key == "entity":
                    row["entity"] = cell["spans"][0] if len(cell["spans"]) > 0 else cell["text"]
                    row["description"] = cell["spans"][1] if len(cell["spans"]) > 1 else ""
                elif key == "ip_address":
                    row["ip_address"] = cell["spans"][0] if len(cell["spans"]) > 0 else cell["text"]
                    row["system_name"] = cell["spans"][1] if len(cell["spans"]) > 1 else ""
                else:
                    row[key] = cell["text"]
            result.append(row)
        return result

    # ✅
    def _entity_row(self, ip_or_name: str) -> Locator:
        """The numbered (chassis) row whose IP address or system name equals `ip_or_name`."""
        return self.table.locator("tbody > tr.pl-bold").filter(
            has=self.page.locator(
                "span.ownerIp, span.ownerSystemName",
                has_text=re.compile(rf"^\s*{re.escape(ip_or_name)}\s*$"))
        ).first

    _EXPANDED_JS = "r => { const n = r.nextElementSibling; return !!n && !n.classList.contains('pl-bold'); }"

    # ✅
    def _expand_row_locator(self, entity_row: Locator, label: str, timeout: int = 8000) -> bool:
        """Expand an entity row (no-op if it is already expanded)."""
        try:
            expect(entity_row).to_be_attached(timeout=timeout)
            entity_row.scroll_into_view_if_needed(timeout=timeout)
            if entity_row.evaluate(self._EXPANDED_JS):
                return True
            entity_row.locator(".expand-cell").click()
            self.page.wait_for_function(self._EXPANDED_JS, arg=entity_row.element_handle(), timeout=timeout)
            return True
        except Exception as e:
            print(f"❌ Failed to expand {label}: {e}")
            return False


    # ==========================================================
    # Filters
    # ==========================================================

    # ✅
    def set_filterBy(self, value: str, timeout: int = 8000) -> bool:
        """Open the Filter By dropdown and pick the option whose text equals `value` (Default / Device)."""
        try:
            toggle = self.filter_by.locator("button.dropdown-toggle")
            expect(toggle).to_be_visible(timeout=timeout)
            toggle.click()
            option = self.filter_by.locator(".dropdown-menu li.dropdown-item").filter(
                has_text=re.compile(rf"^\s*{re.escape(value)}\s*$")
            ).first
            expect(option).to_be_visible(timeout=timeout)
            option.click()
            return True
        except Exception as e:
            print(f"❌ Failed to set Filter By '{value}': {e}")
            return False

    # ✅
    def _pick_from_dropdown(self, dropdown: Locator, value: str, label: str, timeout: int = 8000) -> bool:
        """
        Open `dropdown` and pick the option whose text equals `value`; falls back to the
        first option containing `value` (e.g. an IP address inside "<name> (<ip>)").
        """
        try:
            toggle = dropdown.locator("button.dropdown-toggle")
            expect(toggle).to_be_visible(timeout=timeout)
            toggle.click()
            options = dropdown.locator(".dropdown-menu li.dropdown-item")
            exact = options.filter(has_text=re.compile(rf"^\s*{re.escape(value)}\s*$"))
            option = exact.first if exact.count() > 0 else options.filter(has_text=value).first
            expect(option).to_be_attached(timeout=timeout)
            option.scroll_into_view_if_needed(timeout=timeout)
            option.click()
            return True
        except Exception as e:
            print(f"❌ Failed to set {label} '{value}': {e}")
            return False

    # ✅
    def set_devices(self, value: str, timeout: int = 8000) -> bool:
        """Pick a device in the Devices dropdown (shown when Filter By is 'Device')."""
        return self._pick_from_dropdown(self.devices, value, "Devices", timeout)

    # ✅
    def set_chassis(self, value: str, timeout: int = 8000) -> bool:
        """Pick a chassis in the Chassis dropdown (shown when Filter By is 'Chassis')."""
        return self._pick_from_dropdown(self.chassis, value, "Chassis", timeout)

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

    # ✅
    def _set_whole_word(self, checked: bool, timeout: int = 8000) -> bool:
        try:
            container = self.whole_word.locator("label.checkbox-container")
            expect(container).to_be_visible(timeout=timeout)
            is_checked = "checked" in (container.get_attribute("class") or "").split()
            if is_checked != checked:
                container.click()
            expected = re.compile(r"\bchecked\b")
            if checked:
                expect(container).to_have_class(expected, timeout=timeout)
            else:
                expect(container).not_to_have_class(expected, timeout=timeout)
            return True
        except Exception as e:
            print(f"❌ Failed to {'check' if checked else 'uncheck'} Whole word: {e}")
            return False


    def get_chassis_list(self, timeout: int = 8000) -> list[str]:
        """
        Return the options of the Chassis dropdown, e.g. ['Chassis: 1996', 'Chassis: 1997', ...].
        Switches Filter By to 'Chassis' first if the Chassis dropdown isn't shown.
        """
        try:
            if not self.chassis.is_visible() and not self.set_filterBy("Chassis", timeout):
                return []
            expect(self.chassis).to_be_visible(timeout=timeout)

            # The menu items are rendered even while the dropdown is closed; open it only if they aren't
            options = self.chassis.locator(".dropdown-menu li.dropdown-item")
            opened = False
            if options.count() == 0:
                toggle = self.chassis.locator("button.dropdown-toggle")
                toggle.click()
                opened = True
                expect(options.first).to_be_attached(timeout=timeout)

            chassis_list = [" ".join(t.split()) for t in options.all_text_contents()]

            if opened:
                toggle.click()
            return chassis_list
        except Exception as e:
            print(f"❌ Failed to get Chassis list: {e}")
            return []

    # ✅
    def check_whole_word(self, timeout: int = 8000) -> bool:
        return self._set_whole_word(True, timeout)

    # ✅
    def uncheck_whole_word(self, timeout: int = 8000) -> bool:
        return self._set_whole_word(False, timeout)


    # ==========================================================
    # Table
    # ==========================================================

    # ✅
    def expand_by_row(self, row: int, timeout: int = 8000) -> bool:
        """Expand the entity row with this number (the value in the Expand column, 1-based)."""
        try:
            entity_row = self.table.locator("tbody > tr.pl-bold").filter(
                has=self.page.locator(".expand-cell span", has_text=re.compile(rf"^\s*{int(row)}\s*$"))
            ).first
            return self._expand_row_locator(entity_row, f"row {row}", timeout)
        except Exception as e:
            print(f"❌ Failed to expand row {row}: {e}")
            return False

    # ✅
    def expand_by_ip_address_or_system_name(self, value: str, timeout: int = 8000) -> bool:
        """Expand the entity row whose IP address or system name equals `value`."""
        return self._expand_row_locator(self._entity_row(value), f"'{value}'", timeout)

    # ✅
    def get_entity_inventory_list(self, ip_address: str, timeout: int = 8000) -> list[dict]:
        """
        Expand the entity with this IP address (or system name) and return its rows:
        the chassis row followed by its modules / PSUs / fans / ports, each as a dict with
        row, entity, description, ip_address, system_name, class, hw_ver, sw_ver, fw_ver,
        part_number, serial_no, fru, manufacturer, is_child.
        Empty list if the entity is not found or on failure.
        """
        try:
            if not self.expand_by_ip_address_or_system_name(ip_address, timeout):
                return []
            result, started = [], False
            for row in self._read_rows():
                if not row["is_child"]:
                    if started:
                        break
                    started = ip_address in (row["ip_address"], row["system_name"])
                if started:
                    result.append(row)
            return result
        except Exception as e:
            print(f"❌ Failed to read inventory of '{ip_address}': {e}")
            return []

    # ✅
    def get_all_inventory_list(self, timeout: int = 8000) -> list[dict]:
        """
        Return every row currently in the table (same dict shape as get_entity_inventory_list).
        Child rows only appear for entities that are expanded - call expand_all() first
        to get the full inventory. Empty list on failure.
        """
        try:
            expect(self.table).to_be_visible(timeout=timeout)
            return self._read_rows()
        except Exception as e:
            print(f"❌ Failed to read inventory table: {e}")
            return []

    # ✅
    def get_number_of_devices_on_inventory_list(self, timeout: int = 8000) -> int:
        """
        Return the number of devices (entity / chassis rows, the numbered 'pl-bold' ones)
        currently listed in the table. Expanded child rows are not counted.
        -1 on failure.
        """
        try:
            expect(self.table).to_be_visible(timeout=timeout)
            return self.table.locator("tbody > tr.pl-bold").count()
        except Exception as e:
            print(f"❌ Failed to count devices on the inventory list: {e}")
            return -1

    # ==========================================================
    # Buttons
    # ==========================================================

    # ✅
    def refresh(self, timeout: int = 8000) -> bool:
        """Click the Refresh button."""
        return self._click_button(self.refresh_button, "Refresh", timeout)

    # ✅
    def expand_all(self, timeout: int = 8000) -> bool:
        """Click the Expand All button."""
        return self._click_button(self.expand_all_button, "Expand All", timeout)

    # ✅
    def is_expanded_all(self, timeout: int = 8000) -> bool:
        """
        Return True if every entity row currently in the table is expanded, i.e. is directly
        followed by its child rows (the actual row state, not the Expand/Collapse All button text).
        Waits up to `timeout` for the expansion to render; prints the collapsed rows on failure.
        """
        try:
            expect(self.table).to_be_visible(timeout=timeout)
            entity_rows = self.table.locator("tbody > tr.pl-bold")
            if entity_rows.count() == 0:
                print("❌ No rows in the inventory table to check for expansion")
                return False

            all_expanded_js = f"t => [...t.querySelectorAll('tbody > tr.pl-bold')].every({self._EXPANDED_JS})"
            try:
                self.page.wait_for_function(all_expanded_js, arg=self.table.element_handle(), timeout=timeout)
                return True
            except Exception:
                pass

            collapsed = []
            for i in range(entity_rows.count()):
                row = entity_rows.nth(i)
                if not row.evaluate(self._EXPANDED_JS):
                    name = " ".join(row.locator(".entity .name").inner_text().split())
                    ip = " ".join(row.locator("span.ownerIp").inner_text().split())
                    collapsed.append(f"{name} ({ip})")
            print(f"❌ {len(collapsed)}/{entity_rows.count()} rows are not expanded: {collapsed}")
            return False
        except Exception as e:
            print(f"❌ Failed to check if all rows are expanded: {e}")
            return False

    # ✅
    def collapse_all(self, timeout: int = 8000) -> bool:
        """Click the Collapse All button (shown instead of Expand All once everything is expanded)."""
        return self._click_button(self.collapse_all_button, "Collapse All", timeout)


    def save_device_inventory(self, timeout: int = 8000) -> bool:
        """Click the Save Device Inventory button (does not handle a dialog / download, if any).
        The button only appears when Filter By = Device and a device is selected."""
        return self._click_button(self.save_device_button, "Save Device Inventory", timeout)

    # ✅
    def save_all_inventory(self, timeout: int = 8000) -> bool:
        """Click the Save All Inventory button (does not handle a dialog / download, if any)."""
        return self._click_button(self.save_button, "Save All Inventory", timeout)
