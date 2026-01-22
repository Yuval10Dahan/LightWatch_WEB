"""
Created by: Yuval Dahan
Date: 21/01/2026

MapLocators:
Centralized locators for Management Map page
"""

from playwright.sync_api import Page, expect


class MapLocators:
    def __init__(self, page: Page):
        self.page = page

        # =========================
        # Main containers
        # =========================
        self.root = page.locator("div.layout-main app-map")

        self.controls_left_bottom = self.root.locator("section.main-controls-left-bottom")
        self.controls_center_bottom = self.root.locator("section.main-controls-center-bottom")

        self.maps_tab_section = self.root.locator("section.main-controls-section-maps-tab")
        self.zoom_controls = self.maps_tab_section.locator("div.zoom-controls")
        self.svg_map = self.root.locator("div.map-container svg.svg-container")

    # ==========================================================
    # Internal helpers
    # ==========================================================
    def must_be_visible(self, locator, description: str, timeout: int = 5000):
        """
        Ensures locator is visible.
        If not visible -> raise AssertionError with a clear message.
        """
        try:
            expect(locator).to_be_visible(timeout=timeout)
        except Exception:
            raise AssertionError(f"[MapLocators] Not visible: {description}.")

    # ==========================================================
    # Events / alarms filters
    # ==========================================================
    def events_filter_tile(self, label_text: str):
        """
        Returns the full clickable tile (icon + text) by label.
        Example: "Alarms", "Critical", "Minor", "Cleared".
        """
        loc = self.controls_left_bottom.locator(f"div.events-filter:has(span:has-text('{label_text}'))")
        # expect(loc).to_be_visible(timeout=5000)
        self.must_be_visible(loc, f"Events filter tile '{label_text}'")
        return loc

    def events_filter_span(self, label_text: str):
        """
        Returns ONLY the label span inside the filter tile.
        """
        tile = self.events_filter_tile(label_text)
        loc = tile.locator("span.no-select")
        self.must_be_visible(loc, f"Events filter span '{label_text}'")
        return loc
    
    def events_filter_icon(self, label_text: str):
        """
        Returns the app-icon locator inside the tile.
        """
        tile = self.events_filter_tile(label_text)
        icon = tile.locator("app-icon")
        self.must_be_visible(icon, f"Events filter icon '{label_text}'")
        return icon
    
    def events_filter_icon_name(self, label_text: str) -> str:
        """
        Returns the icon's 'name' attribute (string).
        Raises if:
          - icon is not visible
          - name attribute is missing
        """
        icon = self.events_filter_icon(label_text)

        name = icon.get_attribute("name")
        if not name:
            raise AssertionError(
                f"[MapLocators] Icon 'name' attribute is missing for filter '{label_text}'."
            )
        return name.strip()

    def events_filter_tile_class(self, label_text: str) -> str:
        """
        Returns the class attribute of the tile container.
        Useful because OFF-state in your UI is represented by:
            div.events-filter.disabled
        """
        tile = self.events_filter_tile(label_text)
        cls = tile.get_attribute("class")
        if cls is None:
            raise AssertionError(f"[MapLocators] 'class' attribute is missing for filter tile '{label_text}'.")
        return cls.strip()
    
    # ==========================================================
    # Map edit controls
    # ==========================================================
    def enable_drag_button(self):
        """
        Left-bottom button:
        """
        loc = self.controls_left_bottom.locator("div.btn:has-text('Enable drag')")
        return loc  # don't force visible: it may disappear when already enabled

    def save_and_lock_button(self):
        """
        'Save & Lock' button 
        """
        loc = self.controls_center_bottom.locator("button:has-text('Save')")
        self.must_be_visible(loc, f"Save & Lock button")
        return loc

    def discard_and_lock_button(self):
        """
        'Discard & Lock' button
        """
        loc = self.controls_center_bottom.locator("button:has-text('Discard')")
        self.must_be_visible(loc, f"Discard & Lock button")
        return loc
    
    # ==========================================================
    # Tabs
    # ==========================================================
    def find_tab(self, tab_name: str):
        """
        Returns the tab container locator for a given tab name.
        Tabs: "Chassis" / "OTN" / "ROADM" / "Manage".
        """
        loc = self.maps_tab_section.locator(f"div.tab:has(span:has-text('{tab_name}'))")
        self.must_be_visible(loc, f"Map tab '{tab_name}'")
        return loc