"""
Created by: Yuval Dahan
Date: 26/10/2026
"""


from playwright.sync_api import Page, expect
import re


class HelpAndAbout: 
    """
    Page Object Model for the "Help & About" modal (About / Details tabs).
    """

    def __init__(self, page: Page):
        """
        Initialize HelpAndAbout with Playwright page instance.
        """
        self.page = page
        self.dialog = page.locator("app-sidenav-details")


    # =========================
    # Tabs
    # =========================

    # ✅
    def _click_tab(self, name: str, timeout: int = 8000) -> bool:
        try:
            tab = self.dialog.locator("ul.nav-tabs a.nav-link").filter(
                has=self.page.locator("span", has_text=re.compile(rf"^\s*{name}\s*$"))
            )
            expect(tab).to_be_visible(timeout=timeout)
            if "active" not in (tab.get_attribute("class") or ""):
                tab.click()
            expect(tab).to_have_class(re.compile(r"\bactive\b"), timeout=timeout)
            return True
        except Exception as e:
            print(f"❌ Failed to click '{name}' tab: {e}")
            return False

    # ✅
    def click_about(self, timeout: int = 8000) -> bool:
        """
        Open the 'About' tab.
        """
        return self._click_tab("About", timeout)

    # ✅
    def click_details(self, timeout: int = 8000) -> bool:
        """
        Open the 'Details' tab.
        """
        return self._click_tab("Details", timeout)

    # =========================
    # About tab
    # =========================

    # ✅
    def get_LW_version(self, timeout: int = 8000) -> str:
        """
        Return the LightWatch version string shown in the About tab,
        e.g. "2.1 build 3" (the leading "Version" word is stripped).
        Returns an empty string on failure.
        """
        try:
            if not self.click_about(timeout):
                return ""
            version = self.dialog.locator("section.about .about-version")
            expect(version).to_be_visible(timeout=timeout)
            text = " ".join((version.inner_text() or "").split())
            return re.sub(r"^Version\s+", "", text, flags=re.IGNORECASE)
        except Exception as e:
            print(f"❌ Failed to read LightWatch version: {e}")
            return ""

    # =========================
    # Details tab
    # =========================
    
    # ✅
    def get_details_urls(self, timeout: int = 8000) -> list[str]:
        """
        Return the hrefs of all links shown in the Details tab, in page order.
        Empty list on failure.
        """
        try:
            if not self.click_details(timeout):
                return []
            details = self.dialog.locator("section.details")
            expect(details).to_be_visible(timeout=timeout)
            hrefs = details.locator("a").evaluate_all(
                "els => els.map(e => e.getAttribute('href')).filter(h => h)")
            return [h.strip() for h in hrefs]
        except Exception as e:
            print(f"❌ Failed to read Details links: {e}")
            return []

    # ✅
    def details_click_on_url(self, url: str, timeout: int = 8000) -> bool:
        """
        In the Details tab, click the link whose href equals `url`
        (falls back to the first link whose href contains `url`).
        Links open in a new browser tab, which is closed after the click.
        """
        try:
            if not self.click_details(timeout):
                return False

            details = self.dialog.locator("section.details")
            link = details.locator(f'xpath=.//a[@href={_xpath_literal(url)}]')
            if link.count() == 0:
                link = details.locator(f'xpath=.//a[contains(@href, {_xpath_literal(url)})]')
            if link.count() == 0:
                print(f"❌ Link not found in Details tab: {url}")
                return False

            link = link.first
            link.scroll_into_view_if_needed(timeout=timeout)
            expect(link).to_be_visible(timeout=timeout)

            with self.page.context.expect_page(timeout=timeout) as new_page_info:
                link.click()
            new_page = new_page_info.value
            try:
                new_page.wait_for_load_state("domcontentloaded", timeout=timeout)
            finally:
                new_page.close()
            return True
        except Exception as e:
            print(f"❌ Failed to click link '{url}': {e}")
            return False


# ===================================
# Not related to the Class functions
# ===================================

# ✅
def _xpath_literal(value: str) -> str:
    """Quote a string for safe use inside an XPath expression."""
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"