"""
Created by: Yuval Dahan
Date: 26/10/2026
"""



from playwright.sync_api import Page, Locator, expect
import re


class SystemConfiguration:
    """
    Page Object Model for the System Configuration screen:
    Server Information / Fault Emails / Fault Traps.
    """

    def __init__(self, page: Page):
        """
        Initialize SystemConfiguration with Playwright page instance.
        """
        self.page = page
        self.root = page.locator("app-configuration")
        self.fault_emails = self.root.locator("app-fault-emails")
        self.fault_traps = self.root.locator("app-fault-traps")
        self.smtp_form = self.root.locator("app-fault-emails-smtp-settings")
        self.trap_receiver = self.fault_traps.locator('tab[heading="Trap Receiver"]')
        self.trap_forwarder = self.fault_traps.locator('tab[heading="Trap Forwarder"]')


    # ==========================================================
    # Internal small helpers
    # ==========================================================

    # ✅
    def _click_nav(self, name: str, timeout: int = 8000) -> bool:
        """Click a left-hand navigation entry and wait until it is active."""
        try:
            btn = self.root.locator("button.configuration-nav-link").filter(
                has=self.page.locator("span", has_text=re.compile(rf"^\s*{name}\s*$"))
            )
            expect(btn).to_be_visible(timeout=timeout)
            if "active" not in (btn.get_attribute("class") or ""):
                btn.click()
            expect(btn).to_have_class(re.compile(r"\bactive\b"), timeout=timeout)
            return True
        except Exception as e:
            print(f"❌ Failed to click '{name}' navigation entry: {e}")
            return False

    # ✅
    def _click_tab(self, scope: Locator, name: str, timeout: int = 8000) -> bool:
        """Click a tab inside `scope` (a tabset owner) and wait until it is active."""
        try:
            tab = scope.locator("ul.nav-tabs a.nav-link").filter(
                has=self.page.locator("span", has_text=re.compile(rf"^\s*{name}\s*$"))
            )
            expect(tab).to_be_visible(timeout=timeout)
            if "active" not in (tab.get_attribute("class") or ""):
                tab.click()
            expect(tab).to_have_class(re.compile(r"\bactive\b"), timeout=timeout)
            return True
        except Exception as e:
            print(f"❌ Failed to click '{name}' tab: {e}")
            return False

    # ✅
    def _fill(self, input_loc: Locator, value, label: str, timeout: int = 8000) -> bool:
        try:
            expect(input_loc).to_be_visible(timeout=timeout)
            expect(input_loc).to_be_enabled(timeout=timeout)
            input_loc.fill(str(value))
            return True
        except Exception as e:
            print(f"❌ Failed to set {label}: {e}")
            return False

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
    def _set_checkbox(self, checkbox: Locator, checked: bool, label: str, timeout: int = 8000) -> bool:
        """Set an app-checkbox to the requested state (no-op if already there)."""
        try:
            container = checkbox.locator("label.checkbox-container")
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
            print(f"❌ Failed to {'check' if checked else 'uncheck'} {label}: {e}")
            return False

    # ✅
    def _active_nav(self) -> str:
        """Name of the currently active left-hand navigation entry ('' if unknown)."""
        try:
            return self.root.locator("button.configuration-nav-link.active").inner_text().strip()
        except Exception:
            return ""


    # ==========================================================
    # Server Information
    # ==========================================================

    # ✅
    def click_server_information(self, timeout: int = 8000) -> bool:
        return self._click_nav("Server Information", timeout)

    # ✅
    def _get_server_value(self, parameter: str, timeout: int = 8000) -> str:
        """Return the 'Effective value' (e.g. '172.16.10.22 : 73') of a parameter row, '' on failure."""
        try:
            row = self.root.locator("table.server-information-table tbody tr").filter(
                has=self.page.locator("p.server-information-table-info-col1",
                                      has_text=re.compile(rf"^\s*{re.escape(parameter)}\s*$"))
            )
            value = row.locator("td.server-information-table-value")
            expect(value).to_be_visible(timeout=timeout)
            return " ".join(value.inner_text().split())
        except Exception as e:
            print(f"❌ Failed to read '{parameter}': {e}")
            return ""

    # ✅
    def get_performance_FTP_server(self) -> str:
        return self._get_server_value("Performance FTP server")

    # ✅
    def get_OSA_FTP_server(self) -> str:
        return self._get_server_value("OSA FTP server")

    # ✅
    def get_OTDR_FTP_server(self) -> str:
        return self._get_server_value("OTDR FTP server")

    # ✅
    def get_provisioning_service_TFTP_server(self) -> str:
        return self._get_server_value("Provisioning service TFTP server")

    # ✅
    def get_provisioning_service_SFTP_server(self) -> str:
        return self._get_server_value("Provisioning service SFTP server")


    # ==========================================================
    # Fault Emails
    # ==========================================================

    # ✅
    def click_fault_emails(self, timeout: int = 8000) -> bool:
        return self._click_nav("Fault Emails", timeout)

    # ✅
    def click_forwarding(self, timeout: int = 8000) -> bool:
        return self._click_tab(self.fault_emails, "Forwarding", timeout)

    # ✅
    def click_event_filters(self, timeout: int = 8000) -> bool:
        return self._click_tab(self.fault_emails, "Event Filters", timeout)

    # ✅
    def click_SMTP_settings(self, timeout: int = 8000) -> bool:
        return self._click_tab(self.fault_emails, "SMTP Settings", timeout)

    # ✅
    def click_refresh(self, timeout: int = 8000) -> bool:
        """Click Refresh on the active Fault Emails tab (Forwarding / Event Filters)."""
        btn = self.fault_emails.locator("tab.tab-pane.active footer button").filter(has_text="Refresh")
        return self._click_button(btn, "Refresh", timeout)

    # ✅
    def click_add(self, timeout: int = 8000) -> bool:
        """
        Click Add on the active screen:
        - Fault Emails: the Add button of the active tab (Forwarding / Event Filters)
        - Fault Traps:  the Add button next to the Community field (Trap Receiver)
        """
        if self._active_nav() == "Fault Traps":
            btn = self.trap_receiver.locator("button.fault-configuration-add-button")
        else:
            btn = self.fault_emails.locator("tab.tab-pane.active footer button").filter(has_text="Add")
        return self._click_button(btn, "Add", timeout)

    # --- Add Forwarding Rule dialog ---

    @property
    def _rule_dialog(self) -> Locator:
        return self.page.locator('div[role="dialog"].fault-emails-forwarding-rules-modal-container--editor')

    # ✅
    def _rule_input(self, control: str) -> Locator:
        return self._rule_dialog.locator(f'app-input[formcontrolname="{control}"] input')

    # ✅
    def add_forwarding_rule_enabled(self) -> bool:
        return self._set_checkbox(self._rule_dialog.locator('app-checkbox[formcontrolname="enabled"]'),
                                  True, "Enabled")

    # ✅
    def add_forwarding_rule_disabled(self) -> bool:
        return self._set_checkbox(self._rule_dialog.locator('app-checkbox[formcontrolname="enabled"]'),
                                  False, "Enabled")

    # ✅
    def add_forwarding_rule_check_urgent(self) -> bool:
        return self._set_checkbox(self._rule_dialog.locator('app-checkbox[formcontrolname="urgent"]'),
                                  True, "Urgent")

    # ✅
    def add_forwarding_rule_uncheck_urgent(self) -> bool:
        return self._set_checkbox(self._rule_dialog.locator('app-checkbox[formcontrolname="urgent"]'),
                                  False, "Urgent")

    # ✅
    def add_forwarding_rule_set_display_name(self, value: str) -> bool:
        return self._fill(self._rule_input("displayName"), value, "Display Name")

    # ✅
    def add_forwarding_rule_set_event_filter(self, value: str, timeout: int = 8000) -> bool:
        """Open the Event Filter dropdown and pick the option whose text equals `value`."""
        try:
            dropdown = self._rule_dialog.locator('app-dropdown[formcontrolname="filter"]')
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
            print(f"❌ Failed to select event filter '{value}': {e}")
            return False

    # ✅
    def add_forwarding_rule_set_destination_email(self, value: str) -> bool:
        return self._fill(self._rule_input("destinationAddress"), value, "Destination Email")

    # ✅
    def add_forwarding_rule_set_header_text(self, value: str) -> bool:
        return self._fill(self._rule_input("header"), value, "Header Text")

    # ✅
    def add_forwarding_rule_set_bundling_period_hours(self, value) -> bool:
        return self._fill(self._rule_input("bundlingPeriodHours"), value, "Bundling Period (hours)")

    # ✅
    def add_forwarding_rule_set_max_events_per_message(self, value) -> bool:
        return self._fill(self._rule_input("maxEventsPerMessage"), value, "Max Events per Message")

    # ✅
    def cancel_add_forwarding_rule(self, timeout: int = 8000) -> bool:
        btn = self._rule_dialog.locator("button").filter(has_text=re.compile(r"^\s*Cancel\s*$"))
        return self._click_button(btn, "Cancel", timeout)

    # ✅
    def save_add_forwarding_rule(self, timeout: int = 8000) -> bool:
        btn = self._rule_dialog.locator("button[type='submit']")
        return self._click_button(btn, "Save forwarding rule", timeout)
   
    # ✅
    def close_add_forwarding_rule(self, timeout: int = 8000) -> bool:
        btn = self._rule_dialog.locator('button[aria-label="Close forwarding rule dialog"]')
        return self._click_button(btn, "Close forwarding rule dialog", timeout)

    # ✅
    @property
    def _forwarding_rules_table(self) -> Locator:
        return self.fault_emails.locator("table.fault-emails-forwarding-rules-table")

    # ✅
    def _forwarding_rule_action(self, action: str, name: str, timeout: int = 8000) -> bool:
        try:
            btn = self._forwarding_rules_table.locator(f'button[aria-label="{action} {name}"]').first
            expect(btn).to_be_attached(timeout=timeout)
            btn.scroll_into_view_if_needed(timeout=timeout)
            return self._click_button(btn, f"{action.lower()} forwarding rule '{name}'", timeout)
        except Exception as e:
            print(f"❌ Failed to {action.lower()} forwarding rule '{name}': {e}")
            return False

    # ✅
    def edit_forwarding_rule(self, name: str, timeout: int = 8000) -> bool:
        """Click the Edit (pencil) icon of the forwarding rule row with this name."""
        return self._forwarding_rule_action("Edit", name, timeout)

    # ✅
    def delete_forwarding_rule(self, name: str, timeout: int = 8000) -> bool:
        """
        Click the Delete (trash) icon of the forwarding rule row with this name,
        then confirm the "Delete Forwarding Rule" dialog by clicking Delete.
        """
        if not self._forwarding_rule_action("Delete", name, timeout):
            return False
        try:
            confirm = self.page.locator('div[role="alertdialog"][aria-labelledby="delete-forwarding-rule-title"]')
            expect(confirm).to_be_visible(timeout=timeout)
            btn = confirm.locator("button.btn-danger").filter(has_text=re.compile(r"^\s*Delete\s*$"))
            if not self._click_button(btn, "Delete (confirm)", timeout):
                return False
            expect(confirm).to_be_hidden(timeout=timeout)
            return True
        except Exception as e:
            print(f"❌ Failed to confirm deletion of forwarding rule '{name}': {e}")
            return False

    # ✅
    def cancel_delete_forwarding_rule(self, name: str, timeout: int = 8000) -> bool:
        """
        Click the Delete (trash) icon of the forwarding rule row with this name,
        then dismiss the confirmation dialog with Cancel (rule is kept).
        """
        if not self._forwarding_rule_action("Delete", name, timeout):
            return False
        try:
            confirm = self.page.locator('div[role="alertdialog"][aria-labelledby="delete-forwarding-rule-title"]')
            expect(confirm).to_be_visible(timeout=timeout)
            btn = confirm.locator("button").filter(has_text=re.compile(r"^\s*Cancel\s*$"))
            if not self._click_button(btn, "Cancel (delete confirmation)", timeout):
                return False
            expect(confirm).to_be_hidden(timeout=timeout)
            return True
        except Exception as e:
            print(f"❌ Failed to cancel deletion of forwarding rule '{name}': {e}")
            return False

    # ✅
    def get_forwarding_rules(self) -> list[dict]:
        """
        Return the Forwarding table as
        [{"active": bool, "name": str, "last_bundling": str}, ...].
        Empty list if the table is not shown (no rules) or on failure.
        """
        try:
            rows = self._forwarding_rules_table.locator("tbody tr")
            result = []
            for i in range(rows.count()):
                row = rows.nth(i)
                cells = row.locator("td")
                checkbox = row.locator("label.checkbox-container").first
                result.append({
                    "active": "checked" in (checkbox.get_attribute("class") or "").split(),
                    "name": cells.nth(1).inner_text().strip(),
                    "last_bundling": cells.nth(2).inner_text().strip(),
                })
            return result
        except Exception as e:
            print(f"❌ Failed to read forwarding rules: {e}")
            return []

    # --- Add Event Filter dialog ---

    # ✅
    @property
    def _filter_dialog(self) -> Locator:
        return self.page.locator('div[role="dialog"].fault-emails-event-filters-modal-container--editor')

    # ✅
    def _filter_dropdown_pick(self, control: str, values, label: str, timeout: int = 8000) -> bool:
        """
        Select one or more options (str or list of str) in an Add Event Filter dropdown.
        Re-opens the menu between picks if it closed, and leaves it closed at the end.
        """
        if isinstance(values, str):
            values = [values]
        try:
            dropdown = self._filter_dialog.locator(f'app-dropdown[formcontrolname="{control}"]')
            toggle = dropdown.locator("button.dropdown-toggle")
            expect(toggle).to_be_visible(timeout=timeout)
            expect(toggle).to_be_enabled(timeout=timeout)

            def is_open() -> bool:
                return toggle.get_attribute("aria-expanded") == "true"

            for value in values:
                if not is_open():
                    toggle.click()
                item = dropdown.locator("div.dropdown-menu li.dropdown-item").filter(
                    has_text=re.compile(rf"^\s*{re.escape(str(value))}\s*$", re.IGNORECASE)
                ).first
                expect(item).to_be_visible(timeout=timeout)
                item.scroll_into_view_if_needed()
                item.click()

            if is_open():
                toggle.click()
            return True
        except Exception as e:
            print(f"❌ Failed to select {values} in '{label}': {e}")
            return False

    # ✅
    def add_event_filter_set_device_types(self, values) -> bool:
        return self._filter_dropdown_pick("deviceTypes", values, "Device Types")

    # ✅
    def add_event_filter_set_subnetworks(self, values) -> bool:
        return self._filter_dropdown_pick("subNetworkIds", values, "Subnetworks")

    # ✅
    def add_event_filter_set_devices(self, values) -> bool:
        return self._filter_dropdown_pick("deviceIdentityKeys", values, "Devices")

    # ✅
    def add_event_filter_set_category(self, values) -> bool:
        return self._filter_dropdown_pick("categories", values, "Category")

    # ✅
    def add_event_filter_set_severity(self, values) -> bool:
        return self._filter_dropdown_pick("severities", values, "Severity")

    # ✅
    def add_event_filter_set_message(self, value: str) -> bool:
        return self._fill(self._filter_dialog.locator('app-input[formcontrolname="message"] input'),
                          value, "Message")

    # ✅
    def add_event_filter_set_filter_name(self, value: str) -> bool:
        return self._fill(self._filter_dialog.locator('app-input[formcontrolname="filterName"] input'),
                          value, "Filter Name")

    # ✅
    def cancel_add_event_filter(self, timeout: int = 8000) -> bool:
        btn = self._filter_dialog.locator("button").filter(has_text=re.compile(r"^\s*Cancel\s*$"))
        return self._click_button(btn, "Cancel", timeout)

    # ✅
    def save_add_event_filter(self, timeout: int = 8000) -> bool:
        btn = self._filter_dialog.locator("button[type='submit']")
        return self._click_button(btn, "Save event filter", timeout)

    # ✅
    def close_add_event_filter(self, timeout: int = 8000) -> bool:
        btn = self._filter_dialog.locator('button[aria-label="Close event filter dialog"]')
        return self._click_button(btn, "Close event filter dialog", timeout)

    # ✅
    @property
    def _event_filters_table(self) -> Locator:
        return self.fault_emails.locator("table.fault-emails-event-filters-table")

    # ✅
    def _event_filter_action(self, action: str, name: str, timeout: int = 8000) -> bool:
        try:
            btn = self._event_filters_table.locator(f'button[aria-label="{action} {name}"]').first
            expect(btn).to_be_attached(timeout=timeout)
            btn.scroll_into_view_if_needed(timeout=timeout)
            return self._click_button(btn, f"{action.lower()} event filter '{name}'", timeout)
        except Exception as e:
            print(f"❌ Failed to {action.lower()} event filter '{name}': {e}")
            return False

    # ✅
    def edit_event_filter(self, name: str, timeout: int = 8000) -> bool:
        """Click the Edit (pencil) icon of the event filter row with this name."""
        return self._event_filter_action("Edit", name, timeout)

    # ✅
    def delete_event_filter(self, name: str, timeout: int = 8000) -> bool:
        """
        Click the Delete (trash) icon of the event filter row with this name,
        then confirm the "Delete Event Filter" dialog by clicking Delete.
        """
        if not self._event_filter_action("Delete", name, timeout):
            return False
        try:
            confirm = self.page.locator('div[role="alertdialog"][aria-labelledby="delete-event-filter-title"]')
            expect(confirm).to_be_visible(timeout=timeout)
            btn = confirm.locator("button.btn-danger").filter(has_text=re.compile(r"^\s*Delete\s*$"))
            if not self._click_button(btn, "Delete (confirm)", timeout):
                return False
            expect(confirm).to_be_hidden(timeout=timeout)
            return True
        except Exception as e:
            print(f"❌ Failed to confirm deletion of event filter '{name}': {e}")
            return False

    # ✅
    def cancel_delete_event_filter(self, name: str, timeout: int = 8000) -> bool:
        """
        Click the Delete (trash) icon of the event filter row with this name,
        then dismiss the confirmation dialog with Cancel (filter is kept).
        """
        if not self._event_filter_action("Delete", name, timeout):
            return False
        try:
            confirm = self.page.locator('div[role="alertdialog"][aria-labelledby="delete-event-filter-title"]')
            expect(confirm).to_be_visible(timeout=timeout)
            btn = confirm.locator("button").filter(has_text=re.compile(r"^\s*Cancel\s*$"))
            if not self._click_button(btn, "Cancel (delete confirmation)", timeout):
                return False
            expect(confirm).to_be_hidden(timeout=timeout)
            return True
        except Exception as e:
            print(f"❌ Failed to cancel deletion of event filter '{name}': {e}")
            return False

    # ✅
    def get_event_filters(self) -> list[dict]:
        """
        Return the Event Filters table as [{"name": str, "conditions": int | str}, ...].
        Empty list if the table is not shown (no filters) or on failure.
        """
        try:
            rows = self._event_filters_table.locator("tbody tr")
            result = []
            for i in range(rows.count()):
                cells = rows.nth(i).locator("td")
                name = cells.nth(0).inner_text().strip()
                conditions = cells.nth(1).inner_text().strip()
                result.append({"name": name,
                                "conditions": int(conditions) if conditions.isdigit() else conditions})
            return result
        except Exception as e:
            print(f"❌ Failed to read event filters: {e}")
            return []


    # --- SMTP Settings ---

    # ✅
    def _smtp_input(self, control: str) -> Locator:
        return self.smtp_form.locator(f'app-input[formcontrolname="{control}"] input')

    # ✅
    def set_host(self, value: str) -> bool:
        return self._fill(self._smtp_input("host"), value, "SMTP host")

    # ✅
    def set_port(self, value) -> bool:
        return self._fill(self._smtp_input("port"), value, "SMTP port")

    # ✅
    def set_SMTP_user(self, value: str) -> bool:
        return self._fill(self._smtp_input("username"), value, "SMTP user")

    # ✅
    def set_SMTP_password(self, value: str) -> bool:
        return self._fill(self._smtp_input("password"), value, "SMTP password")

    # ✅
    def _set_security(self, radio_id: str, label: str, timeout: int = 8000) -> bool:
        try:
            option = self.smtp_form.locator(f'label[for="radio-{radio_id}"]')
            expect(option).to_be_visible(timeout=timeout)
            if "checked" not in (option.get_attribute("class") or "").split():
                option.click()
            expect(option).to_have_class(re.compile(r"\bchecked\b"), timeout=timeout)
            return True
        except Exception as e:
            print(f"❌ Failed to select '{label}': {e}")
            return False

    # ✅
    def set_No_security(self) -> bool:
        return self._set_security("NO", "No security")

    # ✅
    def set_TLS(self) -> bool:
        return self._set_security("TLS", "TLS")

    # ✅
    def set_SSL(self) -> bool:
        return self._set_security("SSL", "SSL")

    # ✅
    def set_from_address(self, value: str) -> bool:
        return self._fill(self._smtp_input("fromAddress"), value, "From Address")

    # ✅
    def set_from_alias(self, value: str) -> bool:
        return self._fill(self._smtp_input("fromAlias"), value, "From Alias")

    # ✅
    def send_test_message(self, timeout: int = 8000) -> bool:
        btn = self.smtp_form.locator("button").filter(has_text="Send Test Message")
        return self._click_button(btn, "Send Test Message", timeout)

    # ✅
    def SMTP_settings_click_save(self, timeout: int = 8000) -> bool:
        btn = self.smtp_form.locator("button[type='submit']")
        return self._click_button(btn, "SMTP Save", timeout)


    # ==========================================================
    # Fault Traps
    # ==========================================================

    # ✅
    def click_fault_traps(self, timeout: int = 8000) -> bool:
        return self._click_nav("Fault Traps", timeout)

    # --- Trap Receiver ---

    # ✅
    def click_trap_receiver(self, timeout: int = 8000) -> bool:
        return self._click_tab(self.fault_traps, "Trap Receiver", timeout)

    # ✅
    def set_community(self, value: str) -> bool:
        """Type a new community (field is disabled while 'Accept All' is checked)."""
        return self._fill(self.trap_receiver.locator('app-input[formcontrolname="newCommunity"] input'),
                          value, "community")

    # ✅
    def delete_community(self, value: str, timeout: int = 8000) -> bool:
        """Delete a community from the table (button is disabled while 'Accept All' is checked)."""
        btn = self.trap_receiver.locator(f'button[aria-label="Remove {value}"]')
        return self._click_button(btn.first, f"delete community '{value}'", timeout)

    # ✅
    def check_accept_all(self) -> bool:
        return self._set_checkbox(self.trap_receiver.locator('app-checkbox[formcontrolname="acceptAllTraps"]'),
                                  True, "Accept All")

    # ✅
    def uncheck_accept_all(self) -> bool:
        return self._set_checkbox(self.trap_receiver.locator('app-checkbox[formcontrolname="acceptAllTraps"]'),
                                  False, "Accept All")

    # ✅
    def trap_receiver_click_save(self, timeout: int = 8000) -> bool:
        btn = self.trap_receiver.locator("button[type='submit']")
        return self._click_button(btn, "Trap Receiver Save", timeout)

    # --- Trap Forwarder ---

    # ✅
    def click_trap_forwarder(self, timeout: int = 8000) -> bool:
        return self._click_tab(self.fault_traps, "Trap Forwarder", timeout)

    # ✅
    def check_enable(self) -> bool:
        return self._set_checkbox(self.trap_forwarder.locator('app-checkbox[formcontrolname="enabled"]'),
                                  True, "Enable")

    # ✅
    def uncheck_enable(self) -> bool:
        return self._set_checkbox(self.trap_forwarder.locator('app-checkbox[formcontrolname="enabled"]'),
                                  False, "Enable")

    # ✅
    def _forwarder_input(self, control: str) -> Locator:
        return self.trap_forwarder.locator(f'app-input[formcontrolname="{control}"] input')

    # ✅
    def set_SNMPv2_remote_host(self, value: str) -> bool:
        return self._fill(self._forwarder_input("remoteHost"), value, "SNMP v2 Remote Host")

    # ✅
    def set_SNMPv2_remote_port(self, value) -> bool:
        return self._fill(self._forwarder_input("remotePort"), value, "SNMP v2 Remote Port")

    # ✅
    def set_SNMPv2_community(self, value: str) -> bool:
        return self._fill(self._forwarder_input("community"), value, "SNMP v2 Community")

    # ✅
    def send_test_trap(self, timeout: int = 8000) -> bool:
        btn = self.trap_forwarder.locator("button").filter(has_text="Send Test Trap")
        return self._click_button(btn, "Send Test Trap", timeout)

    # ✅
    def trap_forwarder_click_save(self, timeout: int = 8000) -> bool:
        btn = self.trap_forwarder.locator("button[type='submit']")
        return self._click_button(btn, "Trap Forwarder Save", timeout)
