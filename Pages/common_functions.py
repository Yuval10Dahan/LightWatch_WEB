'''
Created by: Yuval Dahan
Date: 20/01/2026
'''



from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


class CommonFunctionsPage:
    """
    Common Functioms page – Provides high-level methods to trigger system actions (polling restart, OTN/ROADM sync and cleanup)
    and validates their success using toast messages and overlay state checks.
    """

    def __init__(self, page: Page):
        self.page = page

        # Locators for buttons inside the Common Functions section
        self.polling_restart_btn = page.locator('button', has_text="Polling Restart")
        self.deleting_otn_inconsistent_services_btn = page.locator('button', has_text="Deleting OTN inconsistent services")
        self.synchronizing_otn_services_btn = page.locator('button', has_text="Synchronizing OTN services")
        self.deleting_roadm_inconsistent_services_btn = page.locator('button', has_text="Deleting ROADM inconsistent services")
        self.synchronizing_roadm_services_btn = page.locator('button', has_text="Synchronizing ROADM services")
        self.exit_btn = page.locator('button', has_text="Exit")

        # The div that contains the buttons, to check if Common Functions page is opened
        self.common_functions_container = page.locator('.common-functions-container')


    # Methods for interacting with each section
    def click_polling_restart(self) -> bool:       
        success_message = "Topology polling restarted Successfully"
        failure_message = "Polling Restart"
        self.polling_restart_btn.click()
        self.click_button(success_message, failure_message)

    def click_polling_restart_backup(self) -> bool:
        self.polling_restart_btn.click()

        # be flexible: the toast might be split or have different casing
        toast = self.page.get_by_text("Topology polling restarted", exact=False)

        try:
            toast.wait_for(state="visible", timeout=10_000)

            # Optional: wait for it to disappear 
            toast.wait_for(state="hidden", timeout=15_000)
            print("Polling Restart was successful ✅")
            return True

        except PlaywrightTimeoutError:
            print("Polling Restart failed: toast did not appear ❌")
            return False

    def click_deleting_OTN_inconsistent_services(self) -> bool:
        success_message = "OTN services removed Successfully"
        failure_message = "Deleting OTN inconsistent services"
        self.deleting_otn_inconsistent_services_btn.click()
        self.click_button(success_message, failure_message)

    def click_synchronizing_OTN_services(self) -> bool:
        success_message = "OTN services synchronized Successfully"
        failure_message = "Synchronizing OTN services"
        self.synchronizing_otn_services_btn.click()
        self.click_button(success_message, failure_message)

    def click_deleting_ROADM_inconsistent_services(self) -> bool:
        success_message = "Inconsistent ROADM services deleted Successfully"
        failure_message = "Deleting ROADM inconsistent services"
        self.deleting_roadm_inconsistent_services_btn.click()
        self.click_button(success_message, failure_message)

    def click_synchronizing_ROADM_services(self) -> bool:
        success_message = "ROADM services synchronization started Successfully"
        failure_message = "Synchronizing ROADM services"
        self.synchronizing_roadm_services_btn.click()
        self.click_button(success_message, failure_message)

    def click_exit(self) -> bool:
        try:
            # Make sure the Common Functions window is open before exiting from it
            temp_verification = self.page.locator('div.common-functions-container')
            expect(temp_verification).to_be_visible(timeout=5000)

            self.exit_btn.click()
            
            # Check if the common functions content div disappears after exiting
            expect(temp_verification).to_be_hidden(timeout=10000) 

            return True

        except AssertionError:
            print(f"exit failed ❌")
            return False

    def is_common_functions_page_visible(self) -> bool:
        """
        Method to verify if the Common Functions window is loaded.
        """
        try:
            expect(self.common_functions_container).to_be_visible(timeout=10_000)
            return True

        except AssertionError:
            print("Common Functions window is closed ❌")
            return False
    
    # Generic function
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