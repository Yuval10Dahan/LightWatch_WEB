"""
Created by: Yuval Dahan
Date: 28/01/2026
"""

from playwright.sync_api import sync_playwright
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.device_discovery import DeviceDiscovery
import time
from Utils.utils import refresh_page


SERVER_HOST_IP = "172.16.10.22:8080"
BASE_URL = f"http://{SERVER_HOST_IP}/"
USERNAME = "administrator"
PASSWORD = "administrator"


def run_step(step_num: float, title: str, fn):
    """
    Runs a step and prints consistent success/fail indication.
    """
    try:
        fn()
        print(f"Step {step_num} Success ✅")
        return True
    except Exception as e:
        print(f"Step {step_num} Failed ❌  Error: {e}")
        return False


def _open_device_discovery(left_panel: LeftPanel):
    """
    Open Device Discovery via LeftPanel.
    """
    try:
        ok = left_panel.click_device_discovery()
    except Exception as e:
        raise AssertionError(f"Failed to call left_panel.click_device_discovery(). Error: {e}")

    if ok is not True:
        raise AssertionError("left_panel.click_device_discovery() returned False (Device Discovery did not open).")


def _pick_dropdown_best_effort(setter_fn, getter_fn, candidates: list[str]):
    """
    Best-effort dropdown selection:
    - try candidates
    - fallback to setting current value again (still tests setter)
    """
    current = getter_fn()
    for v in candidates:
        try:
            setter_fn(v)
            after = getter_fn()
            if after.strip().lower() == v.strip().lower():
                return v, current, after
        except Exception as e:
            print(f"error: {e}")
            continue

    # fallback: set current again (still exercises setter)
    try:
        if current:
            setter_fn(current)
    except Exception:
        pass

    after = getter_fn()
    return None, current, after


def test_device_discovery(page, left_panel):
    dd = DeviceDiscovery(page)

    # ----------------------------
    # Open Device Discovery
    # ----------------------------
    try:
        _open_device_discovery(left_panel)
        # basic visibility signal via container()
        _ = dd.container().is_visible()
        print("Opened Device Discovery ✅")
    except Exception as e:
        print(f"Failed to open Device Discovery ❌ | Error: {e}")
        return

    # ----------------------------
    # Step 1: IP address set/get
    # ----------------------------
    def step_1():
        ip = "172.16.10.1"
        dd.set_ip_address(ip)
        got = dd.get_ip_address()
        print(f"IP Address -> set: {ip} | got: {got}")
        if got != ip:
            raise AssertionError(f"IP mismatch. expected='{ip}' got='{got}'")

    run_step(1, "Device Discovery: set/get IP address", step_1)

    # ----------------------------
    # Step 2: Enable range mode + set/get range start/end
    # ----------------------------
    def step_2():
        dd.click_start_discovery_for_ip_range()

        start_ip = "172.16.10.10"
        end_ip = "172.16.10.20"

        dd.set_range_start_ip(start_ip)
        dd.set_range_end_ip(end_ip)

        got_start = dd.get_range_start_ip()
        got_end = dd.get_range_end_ip()

        print(f"Range Start -> set: {start_ip} | got: {got_start}")
        print(f"Range End   -> set: {end_ip} | got: {got_end}")

        if got_start != start_ip:
            raise AssertionError(f"Range start mismatch. expected='{start_ip}' got='{got_start}'")
        if got_end != end_ip:
            raise AssertionError(f"Range end mismatch. expected='{end_ip}' got='{got_end}'")

    run_step(2, "Device Discovery: range toggle + set/get start/end IP", step_2)

    # ----------------------------
    # Step 3: Protocol tabs clicks (ICMP / SNMPv2 / SNMPv3)
    # ----------------------------
    def step_3():
        dd.click_ICMP()
        dd.click_SNMPv2()
        dd.click_SNMPv3()
        dd.click_ICMP()

    run_step(3, "Device Discovery: click protocol tabs (ICMP/SNMPv2/SNMPv3)", step_3)

    # ----------------------------
    # Step 4: SNMPv2 fields set/get
    # ----------------------------
    def step_4():
        read_comm = "public"
        write_comm = "private"
        admin_comm = "admin"
        port = 161

        dd.set_SNMPv2_read_community(read_comm)
        got_read = dd.get_SNMPv2_read_community()
        print(f"SNMPv2 Read Community -> set: {read_comm} | got: {got_read}")
        if got_read != read_comm:
            raise AssertionError(f"SNMPv2 readCommunity mismatch. expected='{read_comm}' got='{got_read}'")

        dd.set_SNMPv2_write_community(write_comm)
        got_write = dd.get_SNMPv2_write_community()
        print(f"SNMPv2 Write Community -> set: {write_comm} | got: {got_write}")
        if got_write != write_comm:
            raise AssertionError(f"SNMPv2 writeCommunity mismatch. expected='{write_comm}' got='{got_write}'")

        dd.set_SNMPv2_admin_community(admin_comm)
        got_admin = dd.get_SNMPv2_admin_community()
        print(f"SNMPv2 Admin Community -> set: {admin_comm} | got: {got_admin}")
        if got_admin != admin_comm:
            raise AssertionError(f"SNMPv2 adminCommunity mismatch. expected='{admin_comm}' got='{got_admin}'")

        dd.set_SNMPv2_contact_port(port)
        got_port = dd.get_SNMPv2_contact_port()
        print(f"SNMPv2 Contact Port -> set: {port} | got: {got_port}")
        if got_port != str(port):
            raise AssertionError(f"SNMPv2 contactPort mismatch. expected='{port}' got='{got_port}'")

    run_step(4, "Device Discovery: SNMPv2 set/get fields", step_4)

    # ----------------------------
    # Step 5: SNMPv3 full configuration + explicit auth/privacy getters/setters
    # ----------------------------
    def step_5():
        user = "snmpv3_user"
        port = 179

        # Go to SNMPv3
        dd.click_SNMPv3()

        # User name
        dd.set_SNMPv3_user_name(user)
        got_user = dd.get_SNMPv3_user_name()
        print(f"SNMPv3 User Name -> set: {user} | got: {got_user}")
        if got_user != user:
            raise AssertionError(f"SNMPv3 userName mismatch. expected='{user}' got='{got_user}'")

        # Configure full process (this also asserts visibility by security level)
        security_level = "Authentication, Privacy"
        auth_protocol = "SHA-1"
        auth_password = "AuthPass123!"
        privacy_protocol = "AES-192"
        privacy_password = "PrivPass123!"

        dd.configure_SNMPv3_entire_process(
            security_level=security_level,
            auth_protocol=auth_protocol,
            auth_password=auth_password,
            privacy_protocol=privacy_protocol,
            privacy_password=privacy_password,
        )

        # dd.configure_SNMPv3_entire_process(
        #     security_level="Authentication, Privacy",
        #     auth_protocol=auth_protocol,
        #     auth_password=auth_password,
        #     privacy_protocol=privacy_protocol,
        #     privacy_password=privacy_password,
        # )

        # Security level getter
        got_level = dd.get_SNMPv3_security_level()
        print(f"SNMPv3 Security Level -> expected: {security_level} | got: {got_level}")
        if got_level.strip().lower() != security_level.strip().lower():
            raise AssertionError(f"SNMPv3 security level mismatch. expected='{security_level}' got='{got_level}'")

        # ---- Explicitly test Authentication Protocol set/get ----
        dd.set_SNMPv3_authentication_protocol(auth_protocol)
        got_auth_proto = dd.get_SNMPv3_authentication_protocol()
        print(f"SNMPv3 Auth Protocol -> set: {auth_protocol} | got: {got_auth_proto}")
        if got_auth_proto.strip().lower() != auth_protocol.strip().lower():
            raise AssertionError(f"SNMPv3 auth protocol mismatch. expected='{auth_protocol}' got='{got_auth_proto}'")

        # ---- Explicitly test Authentication Password set/get ----
        dd.set_SNMPv3_authentication_password(auth_password)
        got_auth_pass = dd.get_SNMPv3_authentication_password()
        print(f"SNMPv3 Auth Password -> set: {auth_password} | got: {got_auth_pass}")
        if got_auth_pass != auth_password:
            raise AssertionError(f"SNMPv3 auth password mismatch. expected='{auth_password}' got='{got_auth_pass}'")

        # ---- Explicitly test Privacy Protocol set/get ----
        dd.set_SNMPv3_privacy_protocol(privacy_protocol)
        got_priv_proto = dd.get_SNMPv3_privacy_protocol()
        print(f"SNMPv3 Privacy Protocol -> set: {privacy_protocol} | got: {got_priv_proto}")
        if got_priv_proto.strip().lower() != privacy_protocol.strip().lower():
            raise AssertionError(f"SNMPv3 privacy protocol mismatch. expected='{privacy_protocol}' got='{got_priv_proto}'")

        # ---- Explicitly test Privacy Password set/get ----
        dd.set_SNMPv3_privacy_password(privacy_password)
        got_priv_pass = dd.get_SNMPv3_privacy_password()
        print(f"SNMPv3 Privacy Password -> set: {privacy_password} | got: {got_priv_pass}")
        if got_priv_pass != privacy_password:
            raise AssertionError(f"SNMPv3 privacy password mismatch. expected='{privacy_password}' got='{got_priv_pass}'")

        # Contact port
        dd.set_SNMPv3_contact_port(port)
        got_port = dd.get_SNMPv3_contact_port()
        print(f"SNMPv3 Contact Port -> set: {port} | got: {got_port}")
        if got_port != str(port):
            raise AssertionError(f"SNMPv3 contactPort mismatch. expected='{port}' got='{got_port}'")


    run_step(5, "Device Discovery: SNMPv3 entire process + auth/privacy set/get", step_5)

    # ----------------------------
    # Step 6: Performance Transport Protocol dropdown set/get
    # ----------------------------
    def step_6():
        
        for i in range(3):
            dd.set_performance_transport_protocol("SFTP (bulk) if supported by device")
            sftp_protocol = dd.get_performance_transport_protocol()
            print(f"Performance Transport Protocol -> Expected: SFTP (bulk) if supported by device, Got: {sftp_protocol}")

            dd.set_performance_transport_protocol("SNMP")
            snmp_protocol = dd.get_performance_transport_protocol()
            print(f"Performance Transport Protocol -> Expected: SNMP, Got: {snmp_protocol}")

    run_step(6, "Device Discovery: set/get Performance Transport Protocol", step_6)

    # ----------------------------
    # Step 7: Reset/Save defaults + override modal (No/Yes) + Start Discovery
    # ----------------------------
    def step_7():
        # 1) Reset (smoke)
        dd.click_reset_to_default()

        # 2) Save as default -> reject (No)
        dd.click_save_as_default()
        dd.reject_default_override()

        # 3) Save as default -> confirm (Yes)
        dd.click_save_as_default()
        dd.confirm_default_override()

    run_step(7, "Device Discovery: reset + save default (No/Yes) + start discovery", step_7)

    # ----------------------------
    # Step 8: Start Discovery (smoke click)
    # ----------------------------
    def step_8():
        dd.click_stop_discovery_for_ip_range()
        dd.set_ip_address("10.60.100.36")
        ip = dd.get_ip_address()
        print(f"ip = {ip}")
        dd.click_start_discovery() 

    run_step(8, "Device Discovery: click Start Discovery", step_8)

    # ----------------------------
    # Step 9: Close Device Discovery
    # ----------------------------
    def step_9():
        dd.close_device_discovery()

    run_step(9, "Device Discovery: close container", step_9)

    print("Test Finished ✅")


if __name__ == "__main__":
    start_time = time.perf_counter()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        login_page = LoginPage(page)
        login_page.goto(BASE_URL)

        if not login_page.login(USERNAME, PASSWORD):
            print("Login Failed ❌")
            context.close()
            browser.close()
            raise SystemExit(1)

        print("Login Success ✅")

        left_panel = LeftPanel(page)
        refresh_page(page)

        test_device_discovery(page, left_panel)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")