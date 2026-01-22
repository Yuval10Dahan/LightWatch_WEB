'''
Created by: Yuval Dahan
Date: 21/01/2026
'''




from playwright.sync_api import Page


class ServiceList:
    """
    Service List page – handles filters, ordering, navigation,
    and table-level operations for Events / Alarms.
    """

    def __init__(self, page: Page):
        self.page = page

    # =========================
    # Severity
    # =========================
    def get_severity(self):
        pass

    def set_severity(self, severity: str):
        pass

    # =========================
    # Category
    # =========================
    def get_category(self):
        pass

    def set_category(self, category: str):
        pass

    # =========================
    # Filter By (general)
    # =========================
    def get_filter_by(self):
        pass

    def set_filter_by(self, filter_by: str):
        pass

    # =========================
    # Filter By → Devices
    # =========================
    def set_all_devices_filterBy_devices(self):
        pass

    def get_all_selected_devices_filterBy_devices(self):
        pass

    def select_device_filterBy_devices(self, device_name: str):
        pass

    def remove_device_filterBy_devices(self, device_name: str):
        pass

    # =========================
    # Filter By → Domain / Chassis
    # =========================
    def get_selected_domain_or_chassis_filterBy_domain_or_chassis(self):
        pass

    def reset_domain_or_chassis_filterBy_domain_or_chassis(self):
        pass

    def select_domain_or_chassis_filterBy_domain_or_chassis(self, value: str):
        pass

    # =========================
    # Filter By → Device Type
    # =========================
    def set_all_devices_filter_by_device_type(self):
        pass

    def get_all_selected_devices_filterBy_device_type(self):
        pass

    def select_device_type_filterBy_device_type(self, device_type: str):
        pass

    def remove_device_type_filterBy_device_type(self, device_type: str):
        pass

    # =========================
    # Date
    # =========================
    def get_date(self):
        pass

    def set_date(self, from_date: str, to_date: str):
        pass

    # =========================
    # Message
    # =========================
    def set_message(self, message: str):
        pass

    # =========================
    # Ordering / Sorting
    # =========================
    def get_order_by(self):
        pass

    def set_order_by(self, column_name: str):
        pass

    def set_order_by_all(self):
        pass

    def enable_descending_order(self):
        pass

    def disable_descending_order(self):
        pass

    # =========================
    # Pagination
    # =========================
    def click_previous(self):
        pass

    def click_next(self):
        pass

    # =========================
    # Events / Alarms Panel
    # =========================
    def open_events_alarms(self):
        pass

    def close_events_alarms(self):
        pass

    # =========================
    # Column Editing
    # =========================
    def click_edit_columns(self):
        pass

    def click_save_changes(self):
        pass

    def click_revert_changes(self):
        pass