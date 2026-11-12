'''
Created by: Yuval Dahan
Date: 28/10/2026
'''


from Utils.utils import create_page
from playwright.sync_api import sync_playwright
from Pages.help_and_about import HelpAndAbout
from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
import time


# SERVER_HOST_IP = "172.16.10.22:8080"  # Your base URL here
SERVER_HOST_IP = "172.16.10.22:8443"
BASE_URL = f"https://{SERVER_HOST_IP}/"  # Complete URL with trailing slash
USERNAME = "administrator"
PASSWORD = "administrator"

# Expected LightWatch version as shown in the About tab (None = only check it is non-empty)
EXPECTED_VERSION = None


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

def test_help_and_about(page, left_panel):
    left_panel.click_help_and_about()
    ha = HelpAndAbout(page)
    results = []

    def step(title, fn):
        results.append(run_step(len(results) + 1, title, fn))

    def check_version():
        version = ha.get_LW_version()
        print(f"    LightWatch version: '{version}'")
        if EXPECTED_VERSION is not None and version != EXPECTED_VERSION:
            raise AssertionError(f"expected '{EXPECTED_VERSION}', got '{version}'")
        return version

    step("Click 'Details' tab", ha.click_details)
    step("Click 'About' tab", ha.click_about)
    step("Get LightWatch version", check_version)

    urls = [u for u in ha.get_details_urls() if u.startswith("http")]
    print(f"    Details links: {urls}")
    step("Details tab shows at least one link", lambda: len(urls) > 0)
    for url in urls:
        step(f"Details: click link {url}", lambda u=url: ha.details_click_on_url(u))

    step("Click 'About' tab again", ha.click_about)

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
        test_help_and_about(page, left_panel)

        context.close()
        browser.close()

    end_time = time.perf_counter()
    print(f"Total test runtime: {end_time - start_time:.2f} seconds")
