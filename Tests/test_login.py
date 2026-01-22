'''
Created by: Yuval Dahan
Date: 19/01/2026
'''


from playwright.sync_api import sync_playwright, expect
from Pages.login_page import LoginPage
from time import sleep
import time


SERVER_HOST_IP = "http://172.16.10.62:8080/"
USERNAME = "administrator"
PASSWORD = "administrator"



def test_login():
    base_url = SERVER_HOST_IP  # include trailing slash

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        login_page = LoginPage(page)
        login_page.goto(base_url)
        if login_page.login(USERNAME, PASSWORD):
            print("Login Success ✅")

            # Extra sanity: left menu exists
            expect(page.locator("app-sidenav")).to_be_visible()
            print("Step 1 Success ✅")
        else:
            print("Login Failed ❌")
            print("Step 1 Failed ❌")

        context.close()
        browser.close()

def test_login_short_username():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        login = LoginPage(page)
        login.goto(SERVER_HOST_IP)
        if login.login("admin", "administrator"):
            print("Step 2 Failed ❌")
        else:
            print("Step 2 Success ✅")

        context.close()
        browser.close()

def test_login_short_password():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        login = LoginPage(page)
        login.goto(SERVER_HOST_IP)
        if login.login("administrator", "123"):
            print("Step 3 Failed ❌")
        else:
            print("Step 3 Success ✅")

        context.close()
        browser.close()

def test_login_wrong_credentials():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        login = LoginPage(page)
        login.goto(SERVER_HOST_IP)
        if login.login("administrator", "wrongpass123"):
            print("Step 4 Failed ❌")
        else:
            print("Step 4 Success ✅")

        context.close()
        browser.close()

def test_logout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        login_page = LoginPage(page)
        login_page.goto(SERVER_HOST_IP)
        if login_page.login(USERNAME, PASSWORD):
            print("Login Success ✅")
        else:
            print("Login Failed ❌")

        if login_page.logout():
            print("Step 5 Success ✅")
        else:
            print("Step 5 Failed ❌")

        context.close()
        browser.close()




if __name__ == "__main__":
    start_time = time.perf_counter()
    # login_page = LoginPage()

    test_login()
    test_login_short_username()
    test_login_short_password()
    test_login_wrong_credentials()
    test_logout()

    end_time = time.perf_counter()
    print(f"Total runtime: {end_time - start_time:.2f} seconds")
