'''
Created by: Yuval Dahan
Date: 21/01/2026
'''



from playwright.sync_api import Page


class ServiceProvisioning:
    """
    Service Provisioning page – actions for creating services (ROADM / OTN / CHASSIS)
    and exiting the provisioning screen.
    """

    def __init__(self, page: Page):
        self.page = page

    # =========================
    # Service Provisioning
    # =========================
    def create_ROADM_service(self):
        pass

    def create_OTN_service(self):
        pass

    def create_CHASSIS_service(self):
        pass

    def click_exit(self):
        pass