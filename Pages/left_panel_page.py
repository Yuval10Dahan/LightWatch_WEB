'''
Created by: Yuval Dahan
Date: 20/01/2026
'''


from time import sleep
from playwright.sync_api import Page, expect
import re
from Utils.utils import refresh_page

class LeftPanel:
    """
    Left Panel page – Provides simple click methods for each navigation item and verifies successful navigation
    by checking active states or expected page elements (e.g., the Common Functions container).
    """

    def __init__(self, page: Page):
        self.page = page

        # Locators for each section
        self.management_map = page.locator('li[routerlink="map"]')
        self.service_list = page.locator('li[routerlink="service"]')  
        self.service_provisioning = page.locator('li[routerlink="addservice"]')
        self.performance = page.locator('li[routerlink="performance"]')
        self.device_discovery = page.locator('li[routerlink="map/discovery"]')
        self.domain_management = page.locator('li[routerlink="devicemanagement"]')
        self.inventory = page.locator('li[routerlink="inventory"]')
        self.alarms_and_events = page.locator('li[routerlink="map/faults"]')
        self.common_functions = page.locator('li', has_text="Common Functions")
        self.user_management = page.locator('li', has_text="User Management")
        self.task_manager = page.locator('li', has_text="Task Manager")
        self.system_configuration = page.locator('li', has_text="System Configuration")
        self.logout = page.locator('li', has_text="Logout")
        self.reload_button = page.locator('button', has_text="Reload")


    # ==========================================================
    # Methods for interacting with each section
    # ==========================================================

    # ✅
    def click_management_map(self) -> bool:
        try:
            self.management_map.click()
            expect(self.management_map).to_have_class('active')
            sleep(0.5)
            return True

        except TimeoutError:
            print(f"Click on 'Management Map' failed ❌")
            return False

    # ✅
    def click_service_list(self) -> bool:
        try:
            self.service_list.click()
            expect(self.service_list).to_have_class('active')
            sleep(5)
            return True
        
        except TimeoutError:
            print(f"Click on 'Service List' failed ❌")
            return False

    # ✅
    def click_service_provisioning(self) -> bool:
        try:
            self.service_provisioning.click()
            expect(self.service_provisioning).to_have_class('active')
            sleep(5)
            return True
        
        except TimeoutError:
            print(f"Click on 'Service Provisioning' failed ❌")
            return False

    # ✅
    def click_performance(self) -> bool:
        try:
            self.performance.click()
            expect(self.performance).to_have_class('active')
            sleep(5)
            return True
        
        except TimeoutError:
            print(f"Click on 'Performance' failed ❌")
            return False

    # ✅
    def click_device_discovery(self) -> bool:
        try:
            self.device_discovery.click()
            expect(self.device_discovery).to_have_class('active')
            sleep(5)
            return True
        
        except TimeoutError:
            print(f"Click on 'Device Discovery' failed ❌")
            return False

    # ✅
    def click_domain_management(self) -> bool:
        try:
            self.domain_management.click()
            expect(self.domain_management).to_have_class('sw-1-8 active')
            refresh_page(self.page)
            sleep(5)

            return True
        
        except TimeoutError:
            print(f"Click on 'Domain Management' failed ❌")
            return False

    # ✅
    def click_inventory(self) -> bool:
        try:
            self.inventory.click()
            expect(self.inventory).to_have_class('active')
            sleep(5)
            return True
        
        except TimeoutError:
            print(f"Click on 'Inventory' failed ❌")
            return False

    # ✅
    def click_alarms_and_events(self) -> bool:
        try:
            self.alarms_and_events.click()
            expect(self.alarms_and_events).to_have_class('active')
            sleep(5)
            return True
        
        except TimeoutError:
            print(f"Click on 'Alarms & Events' failed ❌")
            return False

    # ✅
    def click_common_functions(self) -> bool:
        try:
            self.common_functions.click()
            expect(self.page.locator('.common-functions-container')).to_be_visible(timeout=10_000)
            sleep(5)
            return True
        
        except TimeoutError:
            print(f"Click on 'Common Functions' failed ❌")
            return False

    # ✅
    def click_user_management(self) -> bool:
        try:
            self.user_management.click()
            expect(self.user_management).to_have_class('active')
            sleep(5)
            return True
        
        except TimeoutError:
            print(f"Click on 'User Management' failed ❌")
            return False

    # ✅
    def click_task_manager(self) -> bool:
        try:
            self.task_manager.click()
            expect(self.task_manager).to_have_class('active')
            sleep(5)
            return True
        
        except TimeoutError:
            print(f"Click on 'Task Manager' failed ❌")
            return False

    # ✅
    def click_system_configuration(self) -> bool:
        try:
            self.system_configuration.click()
            expect(self.system_configuration).to_have_class('active')
            sleep(5)
            return True
        
        except TimeoutError:
            print(f"Click on 'System Configuration' failed ❌")
            return False

    # ✅
    def click_logout(self) -> bool:
        try:
            self.logout.click()
            self.click_reload_button()
            sleep(1)
            return True
        
        except TimeoutError:
            print(f"Click on 'Logout' failed ❌")
            return False

    # ==========================================================
    # Reload Action
    # ==========================================================

    # ✅
    def click_reload_button(self) -> None:
        """
        Attempts to click the Reload button on the error page and waits for the page to reload successfully.

        Returns:
            True  -> Reload button clicked and page reloaded successfully.
            False -> Reload button not found or reload failed.
        """
        try:
            # Wait for the reload button to be visible and click it
            self.reload_button.wait_for(state="visible", timeout=15_000)
            self.reload_button.click()

            # After clicking, wait for the page to reload and ensure login elements appear again
            expect(self.page.locator('app-input[formcontrolname="username"]')).to_be_visible(timeout=15_000)
            expect(self.page.locator('app-input[formcontrolname="password"]')).to_be_visible(timeout=15_000)

            return True

        except TimeoutError:
            return False