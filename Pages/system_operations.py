'''
Created by: Yuval Dahan
Date: 20/01/2026
'''



from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from Utils.utils import refresh_page, countdown_sleep
from time import sleep


class SystemOperationsPage:
    """
    System Operations page – Provides high-level methods to trigger system actions (polling restart, OTN/ROADM sync and cleanup)
    and validates their success using toast messages and overlay state checks.
    """

    def __init__(self, page: Page):
        self.page = page 

        # Locators for buttons inside the System Operations section
        self.restart_polling_btn = page.locator('button', has_text="Restart Polling")
        self.synchronize_inventory_btn = page.locator('button', has_text="Synchronize Inventory")
        self.delete_inconsistent_otn_services_btn = page.locator('button', has_text="Delete Inconsistent OTN Services")
        self.synchronize_otn_services_btn = page.locator('button', has_text="Synchronize OTN Services")
        self.delete_inconsistent_roadm_services_btn = page.locator('button', has_text="Delete Inconsistent ROADM Services")
        self.synchronize_roadm_services_btn = page.locator('button', has_text="Synchronize ROADM Services")
        self.exit_btn = page.locator('button', has_text="Exit")

        # The div that contains the buttons, to check if System Operations page is opened
        self.system_operations_container = page.locator('.common-functions-container')

    # ==========================================================
    # Methods for interacting with each section
    # ==========================================================

    # ✅
    def click_restart_polling(self) -> bool:
        success_message = "Topology polling restarted Successfully"
        failure_message = "Restart Polling"

        try:
            self.restart_polling_btn.click()
            result = self.click_button(success_message, failure_message)

            if result:
                refresh_page(self.page)
                countdown_sleep(15, "Waiting for polling to finish")

            return result

        except PlaywrightTimeoutError:
            print(f"{failure_message} failed ❌")
            return False

    # ✅
    def click_synchronize_inventory(self) -> bool:
        success_message = "Inventory synchronization started Successfully"
        failure_message = "Synchronize Inventory"

        try:
            self.synchronize_inventory_btn.click()
            sleep(0.5)

            # Confirmation dialog – make sure it opened, then confirm with "Yes"
            dialog = self.page.locator('.pl-modal', has_text="Synchronize inventory")
            sleep(2)
            expect(dialog).to_be_visible(timeout=5000)
            dialog.locator('button', has_text="Yes").click()
            sleep(0.5)

            return self.click_button(success_message, failure_message)

        except PlaywrightTimeoutError:
            print(f"{failure_message} failed ❌")
            return False

    
    def click_delete_inconsistent_OTN_services(self) -> bool:
        success_message = "OTN services removed Successfully"
        failure_message = "Delete Inconsistent OTN Services"
        self.delete_inconsistent_otn_services_btn.click()
        self.click_button(success_message, failure_message)

   
    def click_synchronize_OTN_services(self) -> bool:
        success_message = "OTN services synchronized Successfully"
        failure_message = "Synchronize OTN Services"
        self.synchronize_otn_services_btn.click()
        self.click_button(success_message, failure_message)

    
    def click_delete_inconsistent_ROADM_services(self) -> bool:
        success_message = "Inconsistent ROADM services deleted Successfully"
        failure_message = "Delete Inconsistent ROADM Services"
        self.delete_inconsistent_roadm_services_btn.click()
        self.click_button(success_message, failure_message)

  
    def click_synchronize_ROADM_services(self) -> bool:
        success_message = "ROADM services synchronization started Successfully"
        failure_message = "Synchronize ROADM Services"
        self.synchronize_roadm_services_btn.click()
        self.click_button(success_message, failure_message)

   
    def click_exit(self) -> bool:
        try:
            # Make sure the System Operations window is open before exiting from it
            temp_verification = self.page.locator('div.common-functions-container')
            expect(temp_verification).to_be_visible(timeout=5000)

            self.exit_btn.click()
            
            # Check if the System Operations content div disappears after exiting
            expect(temp_verification).to_be_hidden(timeout=10000) 

            return True

        except AssertionError:
            print(f"exit failed ❌")
            return False

    # ✅
    def is_system_operations_page_visible(self) -> bool:
        """
        Method to verify if the System Operations window is loaded.
        """
        try:
            expect(self.system_operations_container).to_be_visible(timeout=10_000)
            return True

        except AssertionError:
            print("System Operations window is closed ❌")
            return False
    
    # ==========================================================
    # Generic function
    # ==========================================================

    # ✅
    def click_button(self, success_message, failure_message):
        """
        Generic function to click a button and verify that the action succeeded.
        """
        try:
            # Ensure the success message is visible and verification wrapper appear(HTML)
            success_message = self.page.locator(f'text={success_message}')
            expect(success_message).to_be_visible(timeout=5000)  
            temp_verification = self.page.locator('div.cdk-global-overlay-wrapper')
            expect(temp_verification).to_be_visible(timeout=5000)
            
            # Optionally, wait for the success message to disappear (if you want to ensure it disappears after some time)
            expect(success_message).to_be_hidden(timeout=5000)
            
            # Check if the global overlay wrapper disappears after the message disappears
            expect(temp_verification).to_be_hidden(timeout=10000) 

            return True

        except AssertionError:
            print(f"{failure_message} failed ❌")
            return False