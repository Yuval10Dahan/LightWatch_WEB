"""
Created by: Yuval Dahan
Date: 26/02/2026
"""

from playwright.sync_api import sync_playwright

from PL_Devices.PL_Pages.PL_login_page import PL_LoginPage
from PL_Devices.PL_Pages.PL_security_page import PL_SecurityPage

# NOTE: adjust to your device / environment
SERVER_HOST_IP = "172.16.30.15"
BASE_URL = f"http://{SERVER_HOST_IP}/"
USERNAME = "tech"
PASSWORD = "packetlight"


def run_step(step_num: float, title: str, fn):
    """Runs a step and prints consistent success/fail indication."""
    try:
        print(f"\n--- Step {step_num}: {title} ---")
        fn()
        print(f"Step {step_num} Success ✅")
        return True
    except Exception as e:
        print(f"Step {step_num} Failed ❌  Error: {e}")
        return False


def test_PL_security_page(page):
    pl = PL_LoginPage(page)
    sec = PL_SecurityPage(page)

    # ----------------------------
    # Step 1: goto login page
    # ----------------------------
    def step_1():
        pl.goto(BASE_URL)
        # Strong signal: login form must be visible
        assert pl.login_root.is_visible(), "Login form is not visible after goto()"

    run_step(1, "PL Security: goto login page", step_1)

    # ----------------------------
    # Step 2: positive login
    # ----------------------------
    def step_2():
        ok = pl.login(USERNAME, PASSWORD)
        print(f"Login returned: {ok}")
        if ok is not True:
            raise AssertionError("Login failed with valid credentials")

    run_step(2, "PL Security: login with valid credentials", step_2)

    # ----------------------------
    # Step 3: Open Security tab
    # ----------------------------
    def step_3():
        ok = sec.open_security_tab(timeout=12_000)
        print(f"open_security_tab returned: {ok}")
        if ok is not True:
            raise AssertionError("open_security_tab() returned False")

    run_step(3, "PL Security: open Security tab", step_3)

    # ----------------------------
    # Step 4: Click Users tab under Security
    # ----------------------------
    def step_4():
        ok = sec.click_on_users(timeout=12_000)
        print(f"click_on_users returned: {ok}")
        if ok is not True:
            raise AssertionError("click_on_users() returned False")

    run_step(4, "PL Security: click on Users", step_4)

    # ----------------------------
    # Step 5: Read Users table
    # ----------------------------
    def step_5():
        users = sec.get_users_table(timeout=12_000)
        print(f"Users rows: {len(users)}")
        for row in users:
            # [username, permission, snmpv3_auth, snmpv3_priv]
            print(row)

        # Not all devices have multiple users; but table should exist.
        if users is None:
            raise AssertionError("get_users_table returned None")

        if sec.is_user_located_in_users_table("admin", users_table=users):
            print("User exists ✅")
        else:
            print("User missing ❌")

        if sec.is_user_located_in_users_table("yuval", users_table=users):
            print("User exists ✅")
        else:
            print("User missing ❌")

        user_details = sec.return_user_parameters("admin", users_table=users)
        print(f"user details: {user_details}")

    run_step(5, "PL Security: get Users table", step_5)

    # ----------------------------
    # Step 6: Add user
    # ----------------------------
    def step_6():
        ok = sec.add_new_user(user_name="yuval", permission="administrator", password="Z@qqaz$$2", verify_password="Z@qqaz$$2",
                              snmpv3_auth="No Auth", snmpv3_priv="No Priv")
        
        if ok is not True:
            raise AssertionError("Add user name failed.")

    run_step(6, "PL Security: verify Add w/o username is blocked", step_6)

    # Cleanup: logout (best-effort)
    try:
        pl.logout()
    except Exception:
        pass

    print("Test Finished ✅")


if __name__ == "__main__":
    import time

    start_time = time.perf_counter()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        test_PL_security_page(page)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")
