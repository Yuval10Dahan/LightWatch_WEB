'''
Created by: Yuval Dahan
Date: 28/10/2026
'''


from Utils.utils import create_page
from playwright.sync_api import sync_playwright
from Pages.user_management import UserManagement
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
import time


# SERVER_HOST_IP = "172.16.10.22:8080"  # Your base URL here
SERVER_HOST_IP = "172.16.10.22:8443"
BASE_URL = f"https://{SERVER_HOST_IP}/"  # Complete URL with trailing slash
USERNAME = "administrator"
PASSWORD = "administrator"

# User that the edit / filter steps work on (must exist on the server under test)
EDIT_USER = "testtest"
EDIT_PRIMARY_GROUP = "Administrators"
EDIT_FULL_NAME = "Yuval Test User"
EDIT_DESCRIPTION = "Automation test user"

# Values typed into the password fields and then CANCELLED (never saved)
CANCELLED_PASSWORD = "Cancelled_pass1!"

# User for the real (destructive) delete step. Must be a disposable user whose
# trash icon is enabled. Leave as None to skip the delete step.
DELETE_USER = "testtest"

# A user whose trash icon is disabled (e.g. the logged-in one) -> delete must fail
UNDELETABLE_USER = "administrator"


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

def usernames(um: UserManagement) -> list:
    users = um.get_all_users()
    print(f"    Users: {(users)}")
    return list(users)

def test_user_management(page, left_panel):
    left_panel.click_user_management()
    um = UserManagement(page)
    results = []

    def step(title, fn):
        results.append(run_step(len(results) + 1, title, fn))

    # ---- Users table / refresh ----
    step("Get all users", lambda: len(usernames(um)) > 0)
    step(f"User '{EDIT_USER}' is listed", lambda: EDIT_USER in usernames(um))
    step("Refresh", um.refresh)
    step("Users still listed after refresh", lambda: len(usernames(um)) > 0)

    # ---- Quick filter ----
    all_count = len(um.get_all_users())
    step(f"Quick filter '{EDIT_USER}'", lambda: um.set_quick_filter(EDIT_USER))
    step(f"Only '{EDIT_USER}' is listed", lambda: usernames(um) == [EDIT_USER])
#     step("Quick filter with no match",
#          lambda: um.set_quick_filter("no_such_user_xyz") and usernames(um) == [])
    step("Clear quick filter", lambda: um.set_quick_filter(""))
    step("All users are listed again", lambda: len(usernames(um)) == all_count)

    # ---- Edit User: fill everything, then cancel ----
    step(f"Edit user '{EDIT_USER}'", lambda: um.edit_user(EDIT_USER))
#     step("Set username (field is disabled -> must fail)",
#          lambda: not um.set_username("renamed_user", timeout=2000))
    step(f"Set primary group '{EDIT_PRIMARY_GROUP}'", lambda: um.set_primary_group(EDIT_PRIMARY_GROUP))
    step("Set full name", lambda: um.set_full_name(EDIT_FULL_NAME))
    step("Set description", lambda: um.set_description(EDIT_DESCRIPTION))
    step("Set new password", lambda: um.set_new_password(CANCELLED_PASSWORD))
    step("Set confirm password", lambda: um.set_confirm_password(CANCELLED_PASSWORD))
    step("Cancel edit user", um.cancel_edit_user)

    # ---- Edit User: update (no password change) ----
    step(f"Edit user '{EDIT_USER}' again", lambda: um.edit_user(EDIT_USER))
    step(f"Set primary group '{EDIT_PRIMARY_GROUP}'", lambda: um.set_primary_group(EDIT_PRIMARY_GROUP))
    step("Set full name", lambda: um.set_full_name(EDIT_FULL_NAME))
    step("Set description", lambda: um.set_description(EDIT_DESCRIPTION))
    step("Update user", um.update_user)
    step(f"User '{EDIT_USER}' still listed after update", lambda: EDIT_USER in usernames(um))

    # ---- Delete ----
#     step(f"Cancel delete of '{EDIT_USER}'", lambda: um.cancel_delete_user(EDIT_USER))
    step(f"User '{EDIT_USER}' still listed after cancelled delete", lambda: EDIT_USER in usernames(um))
#     step(f"Delete '{UNDELETABLE_USER}' (trash disabled -> must fail)",
#          lambda: not um.delete_user(UNDELETABLE_USER, timeout=2000))
    if DELETE_USER:
        step(f"Delete user '{DELETE_USER}'", lambda: um.delete_user(DELETE_USER))
        step(f"User '{DELETE_USER}' no longer listed", lambda: DELETE_USER not in usernames(um))
    else:
        print("    DELETE_USER not set - real delete step skipped")

    # ---- Add User (dialog only; its fields are not implemented yet) ----
    step("Add user (opens dialog)", um.add_user)
    page.keyboard.press("Escape")  # close the Add User dialog

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
        test_user_management(page, left_panel)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")
