'''
Created by: Yuval Dahan
Date: 11/03/2026
'''

from playwright.sync_api import Page, expect


class PL_Upper_Panel:
    def __init__(self, page: Page):
        self.page = page

    # ==========================================================
    # Frame Helpers
    # ==========================================================

    def horizontal_menu_frame(self):
        return self.page.frame_locator("iframe[name='horizontal_menu_frame'], frame[name='horizontal_menu_frame']")

    def upper_panel_frame(self):
        return self.horizontal_menu_frame().frame_locator("iframe[name='box_menu'], frame[name='box_menu']")
    
    # ==========================================================
    # Upper Panel Buttons
    # ==========================================================

    def click_system(self, retries: int = 5, timeout: int = 10_000) -> bool:
        for attempt in range(retries):
            try:
                system_btn = self.upper_panel_frame().locator("#System").first
                expect(system_btn).to_be_visible(timeout=timeout)
                system_btn.scroll_into_view_if_needed()
                system_btn.click(force=True, timeout=timeout)
                return True

            except Exception as e:
                print(f"System button not found/clickable at attempt {attempt + 1}: {e}")
                try:
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False

    def click_all(self, retries: int = 5, timeout: int = 10_000) -> bool:
        for attempt in range(retries):
            try:
                all_btn = self.upper_panel_frame().locator("#ALL").first
                expect(all_btn).to_be_visible(timeout=timeout)
                all_btn.scroll_into_view_if_needed()
                all_btn.click(force=True, timeout=timeout)
                return True

            except Exception as e:
                print(f"ALL button not found/clickable at attempt {attempt + 1}: {e}")
                try:
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False

    def click_port(self, port_id, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Click a port button in the upper panel.
        """
        port_id = str(port_id).strip()
        if not port_id.startswith("Port-"):
            port_id = f"Port-{port_id}"

        for attempt in range(retries):
            try:
                port_btn = self.upper_panel_frame().locator(f"#{port_id}").first
                expect(port_btn).to_be_visible(timeout=timeout)
                expect(port_btn).to_be_enabled(timeout=timeout)
                port_btn.scroll_into_view_if_needed()
                port_btn.click(force=True, timeout=timeout)
                return True

            except Exception as e:
                print(f"{port_id} not found/clickable at attempt {attempt + 1}: {e}")
                try:
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False