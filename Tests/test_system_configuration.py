'''
Created by: Yuval Dahan
Date: 28/10/2026
'''


from Utils.utils import create_page
from playwright.sync_api import sync_playwright
from Pages.system_configuration import SystemConfiguration
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
import time


# SERVER_HOST_IP = "172.16.10.22:8080"  # Your base URL here
SERVER_HOST_IP = "172.16.10.22:8443"
BASE_URL = f"https://{SERVER_HOST_IP}/"  # Complete URL with trailing slash
USERNAME = "administrator"
PASSWORD = "administrator"

# SMTP test values
SMTP_HOST = "smtp.example.com"
SMTP_PORT = 25
SMTP_USER = "test_user"
SMTP_PASSWORD = "test_password"
SMTP_FROM_ADDRESS = "lightwatch@example.com"
SMTP_FROM_ALIAS = "LightWatch"

# Add Event Filter dialog test values (must exist on the server under test)
FILTER_NAME = "dfgfdgfg"
FILTER_DEVICE_TYPES = ["PL-4000T"]
FILTER_CATEGORIES = ["SYSLOG"]
FILTER_SEVERITIES = ["Critical"]
FILTER_MESSAGE = "test message"
FILTER_SUBNETWORKS = "WDC-12"   # fill with subnetwork names that exist on the server
FILTER_DEVICES = "127.0.0.1"       # fill with device names that exist on the server

# Add Forwarding Rule dialog test values
RULE_NAME = "test_forwarding_rule"
RULE_EMAIL = "test@example.com"
RULE_HEADER = "LightWatch test"
RULE_BUNDLING_HOURS = 1
RULE_MAX_EVENTS = 10
RULE_HEADER_EDITED = "LightWatch test (edited)"
FILTER_MESSAGE_EDITED = "test message (edited)"

# Trap test values
TEST_COMMUNITY = "test_community"
FWD_HOST = "172.16.10.100"
FWD_PORT = 162
FWD_COMMUNITY = "public"


def run_step(step_num: int, title: str, fn):
    """
    Runs a step and prints consistent success/fail indication.
    A step fails if it raises, or if it returns False / an empty string.
    """
    try:
        result = fn()
        if result is False or result == "":
            raise AssertionError("step returned a failure result")
        print(f"Step {step_num} Success ✅  |  {title}")
        return True
    except Exception as e:
        print(f"Step {step_num} Failed ❌  |  {title}  |  Error: {e}")
        return False


def printed(label: str, getter):
    """Wrap a getter so the value it returns is printed (and still returned to run_step)."""
    def wrapper():
        value = getter()
        print(f"    {label}: '{value}'")
        return value
    return wrapper


def printed_rows(label: str, getter, expect_name: str = None, present: bool = True):
    """
    Wrap a table getter: print every row, and (optionally) fail unless a row named
    `expect_name` is present / absent according to `present`.
    """
    def wrapper():
        rows = getter()
        print(f"    {label}: {len(rows)} row(s)")
        for row in rows:
            print(f"      {row}")
        if expect_name is not None:
            found = any(r.get("name") == expect_name for r in rows)
            if found != present:
                raise AssertionError(
                    f"'{expect_name}' is {'missing from' if present else 'still in'} {label}")
        return True
    return wrapper


def test_system_configuration(page, left_panel):
    left_panel.click_system_configuration()
    sc = SystemConfiguration(page)
    results = []

    def step(title, fn):
        results.append(run_step(len(results) + 1, title, fn))

    # ----------------------------
    # Server Information
    # ----------------------------
    step("Click Server Information", sc.click_server_information)
    step("Get Performance FTP server", printed("Performance FTP server", sc.get_performance_FTP_server))
    step("Get OSA FTP server", printed("OSA FTP server", sc.get_OSA_FTP_server))
    step("Get OTDR FTP server", printed("OTDR FTP server", sc.get_OTDR_FTP_server))
    step("Get Provisioning service TFTP server",
         printed("Provisioning service TFTP server", sc.get_provisioning_service_TFTP_server))
    step("Get Provisioning service SFTP server",
         printed("Provisioning service SFTP server", sc.get_provisioning_service_SFTP_server))

    # ----------------------------
    # Fault Emails
    # ----------------------------
    step("Click Fault Emails", sc.click_fault_emails)

    # ----------------------------
    # Event Filters (+ Add Event Filter dialog)
    # ----------------------------
    step("Click Event Filters tab", sc.click_event_filters)
    step("Event Filters - click Refresh", sc.click_refresh)

    step("Event Filters - click Add (to cancel)", sc.click_add)
    step("Add Event Filter - set Filter Name", lambda: sc.add_event_filter_set_filter_name(FILTER_NAME))
    step("Add Event Filter - click Cancel", sc.cancel_add_event_filter)

    step("Event Filters - click Add (to close)", sc.click_add)
    step("Add Event Filter - click Close (X)", sc.close_add_event_filter)

    step("Event Filters - click Add (to save)", sc.click_add)
    step(f"Add Event Filter - set Device Types {FILTER_DEVICE_TYPES}",
         lambda: sc.add_event_filter_set_device_types(FILTER_DEVICE_TYPES))
    step("Add Event Filter - set Subnetworks",
         lambda: sc.add_event_filter_set_subnetworks(FILTER_SUBNETWORKS))
    step("Add Event Filter - set Devices",
         lambda: sc.add_event_filter_set_devices(FILTER_DEVICES))
    step(f"Add Event Filter - set Category {FILTER_CATEGORIES}",
         lambda: sc.add_event_filter_set_category(FILTER_CATEGORIES))
    step(f"Add Event Filter - set Severity {FILTER_SEVERITIES}",
         lambda: sc.add_event_filter_set_severity(FILTER_SEVERITIES))
    step(f"Add Event Filter - set Message '{FILTER_MESSAGE}'",
         lambda: sc.add_event_filter_set_message(FILTER_MESSAGE))
    step(f"Add Event Filter - set Filter Name '{FILTER_NAME}'",
         lambda: sc.add_event_filter_set_filter_name(FILTER_NAME))
    step("Add Event Filter - click Save", sc.save_add_event_filter)

    # ----------------------------
    # Forwarding (+ Add Forwarding Rule dialog)
    # ----------------------------
    step("Click Forwarding tab", sc.click_forwarding)
    step("Forwarding - click Refresh", sc.click_refresh)

    step("Forwarding - click Add (to cancel)", sc.click_add)
    step("Add Forwarding Rule - set Display Name", lambda: sc.add_forwarding_rule_set_display_name(RULE_NAME))
    step("Add Forwarding Rule - click Cancel", sc.cancel_add_forwarding_rule)

    step("Forwarding - click Add (to close)", sc.click_add)
    step("Add Forwarding Rule - click Close (X)", sc.close_add_forwarding_rule)

    step("Forwarding - click Add (to save)", sc.click_add)
    step("Add Forwarding Rule - Disabled", sc.add_forwarding_rule_disabled)
    step("Add Forwarding Rule - Enabled", sc.add_forwarding_rule_enabled)
    step("Add Forwarding Rule - check Urgent", sc.add_forwarding_rule_check_urgent)
    step("Add Forwarding Rule - uncheck Urgent", sc.add_forwarding_rule_uncheck_urgent)
    step(f"Add Forwarding Rule - set Display Name '{RULE_NAME}'",
         lambda: sc.add_forwarding_rule_set_display_name(RULE_NAME))
    step(f"Add Forwarding Rule - set Event Filter '{FILTER_NAME}'",
         lambda: sc.add_forwarding_rule_set_event_filter(FILTER_NAME))
    step(f"Add Forwarding Rule - set Destination Email '{RULE_EMAIL}'",
         lambda: sc.add_forwarding_rule_set_destination_email(RULE_EMAIL))
    step(f"Add Forwarding Rule - set Header Text '{RULE_HEADER}'",
         lambda: sc.add_forwarding_rule_set_header_text(RULE_HEADER))
    step(f"Add Forwarding Rule - set Bundling Period {RULE_BUNDLING_HOURS}h",
         lambda: sc.add_forwarding_rule_set_bundling_period_hours(RULE_BUNDLING_HOURS))
    step(f"Add Forwarding Rule - set Max Events per Message {RULE_MAX_EVENTS}",
         lambda: sc.add_forwarding_rule_set_max_events_per_message(RULE_MAX_EVENTS))
    step("Add Forwarding Rule - click Save", sc.save_add_forwarding_rule)

    step("Get forwarding rules (new rule listed)",
         printed_rows("Forwarding rules", sc.get_forwarding_rules, RULE_NAME))

    step(f"Edit forwarding rule '{RULE_NAME}'", lambda: sc.edit_forwarding_rule(RULE_NAME))
    step(f"Edit Forwarding Rule - set Header Text '{RULE_HEADER_EDITED}'",
         lambda: sc.add_forwarding_rule_set_header_text(RULE_HEADER_EDITED))
    step("Edit Forwarding Rule - click Save", sc.save_add_forwarding_rule)
    step("Get forwarding rules (after edit)",
         printed_rows("Forwarding rules", sc.get_forwarding_rules, RULE_NAME))

    step(f"Delete forwarding rule '{RULE_NAME}'", lambda: sc.delete_forwarding_rule(RULE_NAME))
    step("Get forwarding rules (rule removed)",
         printed_rows("Forwarding rules", sc.get_forwarding_rules, RULE_NAME, present=False))

    # ----------------------------
    # Event Filters - get / edit / delete
    # ----------------------------
    step("Click Event Filters tab (again)", sc.click_event_filters)
    step("Get event filters (new filter listed)",
         printed_rows("Event filters", sc.get_event_filters, FILTER_NAME))

    step(f"Edit event filter '{FILTER_NAME}'", lambda: sc.edit_event_filter(FILTER_NAME))
    # step(f"Edit Event Filter - set Message '{FILTER_MESSAGE_EDITED}'",
    #      lambda: sc.add_event_filter_set_message(FILTER_MESSAGE_EDITED))
    step("Edit Event Filter - click Save", sc.save_add_event_filter)
    step("Get event filters (after edit)",
         printed_rows("Event filters", sc.get_event_filters, FILTER_NAME))

    step(f"Delete event filter '{FILTER_NAME}'", lambda: sc.delete_event_filter(FILTER_NAME))
    step("Get event filters (filter removed)",
         printed_rows("Event filters", sc.get_event_filters, FILTER_NAME, present=False))

    # ----------------------------
    # SMTP Settings
    # ----------------------------
    step("Click SMTP Settings tab", sc.click_SMTP_settings)
    step(f"Set SMTP host '{SMTP_HOST}'", lambda: sc.set_host(SMTP_HOST))
    step(f"Set SMTP port '{SMTP_PORT}'", lambda: sc.set_port(SMTP_PORT))
    step(f"Set SMTP user '{SMTP_USER}'", lambda: sc.set_SMTP_user(SMTP_USER))
    step("Set SMTP password", lambda: sc.set_SMTP_password(SMTP_PASSWORD))
    step("Select security: No security", sc.set_No_security)
    step("Select security: TLS", sc.set_TLS)
    step("Select security: SSL", sc.set_SSL)
    step(f"Set From Address '{SMTP_FROM_ADDRESS}'", lambda: sc.set_from_address(SMTP_FROM_ADDRESS))
    step(f"Set From Alias '{SMTP_FROM_ALIAS}'", lambda: sc.set_from_alias(SMTP_FROM_ALIAS))
    step("Send Test Message", sc.send_test_message)
    step("SMTP Settings - click Save", sc.SMTP_settings_click_save)

    # ----------------------------
    # Fault Traps - Trap Receiver
    # ----------------------------
    step("Click Fault Traps", sc.click_fault_traps)
    step("Click Trap Receiver tab", sc.click_trap_receiver)
    step("Uncheck Accept All", sc.uncheck_accept_all)
    step(f"Set community '{TEST_COMMUNITY}'", lambda: sc.set_community(TEST_COMMUNITY))
    step("Click Add (community)", sc.click_add)
    step("Trap Receiver - click Save", sc.trap_receiver_click_save)
    step(f"Delete community '{TEST_COMMUNITY}'", lambda: sc.delete_community(TEST_COMMUNITY))
    step("Trap Receiver - click Save (after delete)", sc.trap_receiver_click_save)
    step("Check Accept All", sc.check_accept_all)
    step("Trap Receiver - click Save (Accept All)", sc.trap_receiver_click_save)

    # ----------------------------
    # Fault Traps - Trap Forwarder
    # ----------------------------
    step("Click Trap Forwarder tab", sc.click_trap_forwarder)
    step("Check Enable", sc.check_enable)
    step(f"Set SNMPv2 remote host '{FWD_HOST}'", lambda: sc.set_SNMPv2_remote_host(FWD_HOST))
    step(f"Set SNMPv2 remote port '{FWD_PORT}'", lambda: sc.set_SNMPv2_remote_port(FWD_PORT))
    step(f"Set SNMPv2 community '{FWD_COMMUNITY}'", lambda: sc.set_SNMPv2_community(FWD_COMMUNITY))
    step("Send Test Trap", sc.send_test_trap)
    step("Trap Forwarder - click Save", sc.trap_forwarder_click_save)
    step("Uncheck Enable", sc.uncheck_enable)
    step("Trap Forwarder - click Save (disabled)", sc.trap_forwarder_click_save)

    if all(results):
        print("Test Success ✅")
    else:
        print(f"Test Failed ❌  |  {results.count(False)} of {len(results)} steps failed")


if __name__ == "__main__":
    start_time = time.perf_counter()

    with sync_playwright() as p:
        browser, context, page = create_page(p, max_size=True)

        login_page = LoginPage(page)
        login_page.goto(BASE_URL)
        if login_page.login(USERNAME, PASSWORD):
            print("Login Success ✅")
        else:
            print("Login Failed ❌")

        left_panel = LeftPanel(page)

        # Run the test
        test_system_configuration(page, left_panel)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")
