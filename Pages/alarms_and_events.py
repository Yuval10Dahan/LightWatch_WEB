"""
Created by: Yuval Dahan
Date: 04/02/2026
"""


from bleach import clean
from playwright.sync_api import Page, expect
from typing import Callable
import time
import re
from time import sleep
from datetime import datetime


MAX_SCROLL_PAGES = 60



class AlarmsAndEvents:
    """
    Alarm & Events page - Contains filters and selectors for faults, severity, category,
    and device / domain / chassis filtering.
    """

    def __init__(self, page: Page):
        self.page = page

    # ==========================================================
    # Internal small helpers 
    # ==========================================================

    # ✅
    def wait_until(self, condition: Callable[[], bool], timeout_ms: int = 10000, interval_ms: int = 200):
        """
        Polls condition() until it returns True or timeout.
        Raises AssertionError on timeout.
        """
        end_time = time.time() + (timeout_ms / 1000.0)
        last_exc = None

        while time.time() < end_time:
            try:
                if condition():
                    return
                last_exc = None
            except Exception as e:
                last_exc = e

            time.sleep(interval_ms / 1000.0)

        if last_exc:
            raise AssertionError(f"Condition not met within {timeout_ms}ms. Last error: {last_exc}")
        raise AssertionError(f"Condition not met within {timeout_ms}ms.")

    # ✅
    @staticmethod
    def _clean(s: str) -> str:
        """
        Normalize whitespace in a string and strip leading/trailing spaces.
        """
        return re.sub(r"\s+", " ", (s or "").strip())
    
    # ✅
    def filters_root(self):
        """
        Return the root locator for the Alarms/Events filters section.
        """
        # Page uses .faults-filters (not .service-filters)
        return self.page.locator(".faults-filters").first

    # ✅
    def dropdown(self, label: str):
        """
        Locate an <app-dropdown> component by its label attribute.
        """
        # Prefer scoping to filters root if it exists, but fallback to whole page
        root = self.filters_root()
        dd = root.locator(f"app-dropdown[label='{label}']").first
        if dd.count() == 0:
            dd = self.page.locator(f"app-dropdown[label='{label}']").first

        expect(dd).to_be_visible(timeout=5000)
        return dd

    # ✅
    def dropdown_selected_text(self, label: str, timeout: int = 5000) -> str:
        """
        Return the currently selected value of a labeled dropdown.
        """
        dd = self.dropdown(label)
        selected = dd.locator("button.dropdown-button .selected-view span").first
        if selected.count() == 0:
            selected = dd.locator(".selected-view span").first  # fallback

        expect(selected).to_be_visible(timeout=timeout)
        return self._clean(selected.inner_text())

    # ✅
    def dropdown_pick(self, label: str, value: str, timeout: int = 8000):
        """
        Select a value from a labeled dropdown and wait until it becomes selected.
        """
        value_clean = self._clean(value)
        before = self.dropdown_selected_text(label, timeout=min(timeout, 3000))

        dd = self.dropdown(label)

        btn = dd.locator("button.dropdown-button, button[dropdowntoggle]").first
        expect(btn).to_be_visible(timeout=timeout)
        expect(btn).to_be_enabled(timeout=timeout)

        # Open dropdown
        btn.click(force=True)

        # Wait for open state 
        container = dd.locator("div.dropdown-container").first
        if container.count() > 0:
            self.wait_until(lambda: "open" in (container.get_attribute("class") or ""), timeout_ms=timeout, interval_ms=100)

        menu = dd.locator(f"div.dropdown-menu[data-label='{label}']").first
        expect(menu).to_be_visible(timeout=timeout)

        item = menu.locator("li.dropdown-item", has_text=re.compile(rf"^\s*{re.escape(value_clean)}\s*$", re.IGNORECASE),).first

        if item.count() == 0:
            options = [self._clean(x) for x in menu.locator("li.dropdown-item").all_inner_texts()]
            options = [x for x in options if x]
            raise AssertionError(f"Value '{value_clean}' not found in dropdown '{label}'. Available: {options}")

        item.scroll_into_view_if_needed()
        item.click(force=True)

        # Wait selected updated (read from button)
        target = value_clean.lower()
        self.wait_until(lambda: self.dropdown_selected_text(label, timeout=min(timeout, 2000)).lower() == target, timeout_ms=timeout, interval_ms=150)

        after = self.dropdown_selected_text(label, timeout=min(timeout, 3000))
        if after.lower() != target:
            if after == before:
                raise AssertionError(f"Dropdown '{label}' selection did not change (still '{after}').")
            raise AssertionError(f"Dropdown '{label}' selection mismatch. Expected '{value_clean}', got '{after}'.")
            
    # ✅
    def nav_text_regex(self, element_name: str) -> re.Pattern:
        """
        Create a flexible regex to match tree item names despite spacing or symbol differences.
        """
        s = element_name.strip()

        esc = re.escape(s)

        # Allow spaces around slashes: "DC-14/14" == "DC-14 / 14"
        esc = esc.replace(r"\/", r"\s*/\s*")

        # Treat '-' and '–' as equivalent in UI text
        esc = esc.replace(r"\-", r"[-–]")

        # Collapse any escaped spaces into flexible whitespace
        esc = esc.replace(r"\ ", r"\s+")

        return re.compile(esc)
    # ==========================================================
    # Faults Type
    # ==========================================================

    # ✅
    def set_faults_type(self, faults_type: str, timeout: int = 8000):
        """
        Set the Faults type dropdown to the given value.
        """
        try:
            target = self._clean(faults_type)
            if not target:
                raise ValueError("faults_type is empty")

            # If already selected, do nothing (fast + avoids extra UI clicks)
            try:
                current = self.get_faults_type(timeout=min(timeout, 3000))
                if self._clean(current).lower() == target.lower():
                    return
            except Exception:
                # If reading fails for some transient reason, continue with picking
                pass

            # Use your generic picker (opens dropdown, selects item, waits for change)
            self.dropdown_pick("Faults type", target, timeout=timeout)

            # Final verification using the stable selected-view text (button content)
            self.wait_until(
                lambda: self.get_faults_type(timeout=min(timeout, 2000)).strip().lower() == target.lower(),
                timeout_ms=timeout,
                interval_ms=150,
            )

            sleep(0.5)

        except Exception as e:
            raise AssertionError(f"set_faults_type('{faults_type}') failed. Problem: {e}")
    
    # ✅
    def get_faults_type(self, timeout: int = 5000) -> str:
        """
        Get the currently selected Faults type value.
        """
        dropdown = self.page.locator('app-dropdown[label="Faults type"]')

        selected = dropdown.locator("button.dropdown-toggle div.selected-view span")

        expect(selected).to_be_visible(timeout=timeout)
        return selected.inner_text().strip()

    # ==========================================================
    # Severity
    # ==========================================================

    # ✅
    def set_severity(self, severity: str, timeout: int = 8000):
        """
        Set the Severity dropdown to the given value.
        """
        try:
            self.dropdown_pick("Severity", severity, timeout=timeout)
            sleep(1)
        except Exception as e:
            raise AssertionError(f"set_severity('{severity}') failed. Problem: {e}")

    # ✅
    def get_severity(self) -> str:
        """
        Get the currently selected Severity value.
        """
        return self.dropdown_selected_text("Severity")
    
    # ✅
    def set_all_severities(self):
        """
        Set the Severity dropdown to 'All'.
        """
        self.set_severity("All")
    # ==========================================================
    # Category
    # ==========================================================

    # ✅
    def set_category(self, category: str, timeout: int = 8000):
        """
        Set the Category dropdown to the given value.
        """
        try:
            self.dropdown_pick("Category", category, timeout=timeout)
            sleep(1) 
        except Exception as e:
            raise AssertionError(f"set_category('{category}') failed. Problem: {e}")

    # ✅
    def get_category(self) -> str:
        """
        Get the currently selected Category value.
        """
        return self.dropdown_selected_text("Category")
    
    # ✅
    def set_all_categories(self):
        """
        Set the Category dropdown to 'All'.
        """
        self.set_category("All")

    # ==========================================================
    # Filter By (Devices / Domain / Chassis)
    # ==========================================================

    # ✅
    def set_filterBy(self, filter_by: str, timeout: int = 8000):
        """
        Set the 'Filter by' dropdown.
        """
        try:
            self.dropdown_pick("Filter by", filter_by, timeout=timeout)
            sleep(1)  
        except Exception as e:
            raise AssertionError(f"set_filterBy('{filter_by}') failed. Problem: {e}")

    # ✅
    def get_filterBy(self) -> str:
        """
        Get the currently selected 'Filter by' value.
        """
        return self.dropdown_selected_text("Filter by")

    # ==========================================================
    # Filter By: Devices
    # ==========================================================

    # ✅
    def set_all_devices_filterBy_devices(self, timeout: int = 10000):
        """
        Select all devices in the Devices filter by selecting each device row.
        Scrolls through the list and clicks any unchecked device until all are checked.
        """
        try:
            self.set_filterBy("Devices")

            dropdown = self.page.locator("app-dropdown[label='Devices']").first
            if dropdown.count() == 0:
                raise AssertionError("Devices dropdown not found (app-dropdown[label='Devices']).")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle], button#button-basic").first
            expect(btn).to_be_visible(timeout=timeout)

            menu = dropdown.locator("div.dropdown-menu[data-label='Devices']").first

            # Best-effort open 
            attempts = [
                lambda: btn.click(force=True),
                lambda: btn.click(force=True),
                lambda: btn.press("Enter"),
                lambda: btn.press("Space"),
                lambda: btn.press("ArrowDown"),
            ]
            opened = False
            for act in attempts:
                try:
                    act()
                except Exception:
                    pass
                try:
                    self.wait_until(lambda: menu.is_visible(), timeout_ms=min(timeout, 1500), interval_ms=150)
                    if menu.is_visible():
                        opened = True
                        break
                except Exception:
                    pass

            if not opened:
                raise AssertionError("Devices dropdown menu did not open (menu stayed hidden).")

            scroller = menu.locator("div.simplebar-content-wrapper").first
            expect(scroller).to_be_visible(timeout=timeout)

            def is_checked(device_li) -> bool:
                return device_li.locator("svg.unchecked").count() == 0

            def click_all_visible_unchecked() -> bool:
                clicked_any = False
                rows = menu.locator("li.dropdown-item.multiple")
                n = rows.count()
                for i in range(1, n):  # skip "All"
                    r = rows.nth(i)
                    if not is_checked(r):
                        r.scroll_into_view_if_needed()
                        r.click(force=True)
                        clicked_any = True
                return clicked_any

            def any_unchecked_visible() -> bool:
                rows = menu.locator("li.dropdown-item.multiple")
                n = rows.count()
                for i in range(1, n):
                    r = rows.nth(i)
                    if not is_checked(r):
                        return True
                return False

            def scroll_to_top():
                scroller.evaluate("el => { el.scrollTop = 0; }")

            def scroll_page_down():
                scroller.evaluate("el => { el.scrollTop = el.scrollTop + el.clientHeight; }")

            def get_scroll_state():
                return (
                    scroller.evaluate("el => el.scrollTop"),
                    scroller.evaluate("el => el.scrollHeight"),
                    scroller.evaluate("el => el.clientHeight"),
                )

            def all_selected_across_scroll() -> bool:
                try:
                    # Pass 1: scroll and click unchecked
                    scroll_to_top()
                    last_scroll_top = -1
                    for _ in range(MAX_SCROLL_PAGES):
                        click_all_visible_unchecked()

                        scroll_top, scroll_h, client_h = get_scroll_state()
                        if scroll_top + client_h >= scroll_h - 2:
                            break
                        if scroll_top == last_scroll_top:
                            break
                        last_scroll_top = scroll_top
                        scroll_page_down()

                    # Pass 2: verify none unchecked remain while scrolling
                    scroll_to_top()
                    last_scroll_top = -1
                    for _ in range(MAX_SCROLL_PAGES):
                        if any_unchecked_visible():
                            return False

                        scroll_top, scroll_h, client_h = get_scroll_state()
                        if scroll_top + client_h >= scroll_h - 2:
                            return not any_unchecked_visible()
                        if scroll_top == last_scroll_top:
                            return not any_unchecked_visible()
                        last_scroll_top = scroll_top
                        scroll_page_down()

                    return True
                except Exception:
                    return False

            self.wait_until(all_selected_across_scroll, timeout_ms=timeout, interval_ms=250)

        except Exception as e:
            raise AssertionError(f"set_all_devices_filterBy_devices failed. Problem: {e}")

    # ✅
    def get_all_selected_devices_filterBy_devices(self, timeout: int = 12000) -> list[str]:
        """
        Return ALL selected devices in the Devices filter.
        """
        try:
            self.set_filterBy("Devices")

            dropdown = self.page.locator("app-dropdown[label='Devices']").first
            if dropdown.count() == 0:
                return []

            btn = dropdown.locator("button#button-basic, button.dropdown-button, button[dropdowntoggle]").first
            expect(btn).to_be_visible(timeout=timeout)

            def clean(s: str) -> str:
                return self._clean(s)

            ip_like = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")

            # ------------------------------------------------------------------
            # 1) Read chips. If '+N' exists -> must do full menu scan.
            # ------------------------------------------------------------------
            chip_texts = [clean(t) for t in btn.locator("div.selected-view.multiple span").all_inner_texts()]
            has_plus = any(re.fullmatch(r"\+\s*\d+", t) for t in chip_texts)

            # If no "+N", chips represent full selection -> return them 
            if chip_texts and not has_plus:
                out, seen = [], set()
                for t in chip_texts:
                    if not t:
                        continue
                    m = ip_like.search(t)
                    name = m.group(0) if m else t
                    if name and name not in seen and name.lower() != "all":
                        seen.add(name)
                        out.append(name)
                return out

            # ------------------------------------------------------------------
            # 2) Full scan: open dropdown + scroll + collect checked rows
            # ------------------------------------------------------------------
            menu = dropdown.locator("div.dropdown-menu[data-label='Devices']").first

            # Only click if not visible 
            if menu.count() == 0 or not menu.is_visible():
                btn.click(force=True)
                self.wait_until(lambda: menu.count() > 0 and menu.is_visible(), timeout_ms=min(timeout, 2500), interval_ms=150)

            if menu.count() == 0 or not menu.is_visible():
                return []

            scroller = menu.locator("div.simplebar-content-wrapper").first
            if scroller.count() == 0:
                scroller = menu

            def scroll_to_top():
                try:
                    scroller.evaluate("el => { el.scrollTop = 0; }")
                except Exception:
                    pass

            def is_checked(li) -> bool:
                """
                Checked rows show a checked checkbox on the right.
                """
                try:
                    if li.locator("label.checkbox-container.checked").count() > 0:
                        return True
                    cls = li.get_attribute("class") or ""
                    return "selected" in cls.split()
                except Exception:
                    return False

            def extract_device(li) -> str:
                txt = clean(li.inner_text())
                if not txt:
                    return ""
                if re.fullmatch(r"all", txt.strip(), re.IGNORECASE):
                    return ""
                m = ip_like.search(txt)
                return m.group(0) if m else txt

            # Keep scrolling until the collected list is stable
            MAX_SCROLL_STEPS = 120
            STABLE_STEPS_TO_STOP = 5  # stop after N scrolls with no new selected items

            seen, out = set(), []

            def collect_visible_selected() -> int:
                """Collect selected devices visible in current viewport. Returns how many new were added."""
                added = 0
                rows = menu.locator("li.dropdown-item.multiple")
                n = rows.count()

                for i in range(n):
                    r = rows.nth(i)
                    if is_checked(r):
                        name = extract_device(r)
                        if name and name not in seen:
                            seen.add(name)
                            out.append(name)
                            added += 1
                return added

            def at_bottom() -> bool:
                try:
                    scroll_top = scroller.evaluate("el => el.scrollTop")
                    scroll_h = scroller.evaluate("el => el.scrollHeight")
                    client_h = scroller.evaluate("el => el.clientHeight")
                    return (scroll_top + client_h) >= (scroll_h - 2)
                except Exception:
                    return False

            def scroll_down():
                # Scroll by ~90% of viewport height to ensure overlap and avoid skipping
                try:
                    scroller.evaluate("el => { el.scrollTop = el.scrollTop + Math.floor(el.clientHeight * 0.9); }")
                except Exception:
                    pass

            # Start from top
            scroll_to_top()
            sleep(0.2)

            stable = 0
            prev_len = 0

            for _ in range(MAX_SCROLL_STEPS):
                new_added = collect_visible_selected()

                if len(out) == prev_len and new_added == 0:
                    stable += 1
                else:
                    stable = 0
                    prev_len = len(out)

                # If we are at bottom AND stable -> done
                if at_bottom() and stable >= STABLE_STEPS_TO_STOP:
                    break

                scroll_down()
                sleep(0.15)

            # One last collection at the end
            collect_visible_selected()

            return out

        except Exception as e:
            raise AssertionError(f"get_all_selected_devices_filterBy_devices failed. Problem: {e}")

    # ✅
    def select_device_filterBy_devices(self, device_name: str, timeout: int = 10000):
        """
        Select a specific device in the Devices filter (if not already selected).
        """
        try:
            self.set_filterBy("Devices")

            dropdown = self.page.locator("app-dropdown[label='Devices']").first
            if dropdown.count() == 0:
                raise AssertionError("Devices dropdown not found (app-dropdown[label='Devices']).")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle], button#button-basic").first
            expect(btn).to_be_visible(timeout=timeout)
            btn.scroll_into_view_if_needed()

            menu = dropdown.locator("div.dropdown-menu[data-label='Devices']").first

            # Open ONLY if not already open 
            if menu.count() == 0 or not menu.is_visible():
                def try_open():
                    try:
                        btn.click(force=True)
                    except Exception:
                        pass

                opened = False
                for _ in range(3):
                    try_open()
                    try:
                        self.wait_until(lambda: menu.count() > 0 and menu.is_visible(),
                                        timeout_ms=min(timeout, 2000),
                                        interval_ms=150)
                        opened = True
                        break
                    except Exception:
                        pass

                if not opened:
                    raise AssertionError("Devices dropdown menu did not open (menu stayed hidden).")

            expect(menu).to_be_visible(timeout=timeout)

            scroller = menu.locator("div.simplebar-content-wrapper").first
            if scroller.count() == 0:
                scroller = menu
            expect(scroller).to_be_visible(timeout=timeout)

            def is_checked(device_li) -> bool:
                return device_li.locator("svg.unchecked").count() == 0

            def scroll_to_top():
                try:
                    scroller.evaluate("el => { el.scrollTop = 0; }")
                except Exception:
                    pass

            def scroll_page_down():
                try:
                    scroller.evaluate("el => { el.scrollTop = el.scrollTop + el.clientHeight; }")
                except Exception:
                    pass

            def get_scroll_state():
                return (
                    scroller.evaluate("el => el.scrollTop"),
                    scroller.evaluate("el => el.scrollHeight"),
                    scroller.evaluate("el => el.clientHeight"),
                )

            scroll_to_top()
            last_scroll_top = -1

            for _ in range(MAX_SCROLL_PAGES):
                row = menu.locator("li.dropdown-item.multiple", has_text=re.compile(rf"^\s*{re.escape(device_name)}\s*$")).first

                if row.count() > 0:
                    row.scroll_into_view_if_needed()

                    # already selected -> done
                    if is_checked(row):
                        return

                    row.click(force=True)
                    self.wait_until(lambda: is_checked(row), timeout_ms=timeout, interval_ms=200)
                    return

                scroll_top, scroll_h, client_h = get_scroll_state()
                if scroll_top + client_h >= scroll_h - 2:
                    break
                if scroll_top == last_scroll_top:
                    break

                last_scroll_top = scroll_top
                scroll_page_down()

            raise AssertionError(f"Device '{device_name}' not found in Devices dropdown (even after scrolling).")

        except Exception as e:
            raise AssertionError(f"select_device_filterBy_devices('{device_name}') failed. Problem: {e}")

    # ✅
    def remove_device_filterBy_devices(self, device_name: str, timeout: int = 10000):
        """
        Unselect a specific device in the Devices filter.
        Scrolls until the device is found, then unselects it if selected.
        """
        try:
            self.set_filterBy("Devices")

            dropdown = self.page.locator("app-dropdown[label='Devices']").first
            if dropdown.count() == 0:
                raise AssertionError("Devices dropdown not found (app-dropdown[label='Devices']).")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle], button#button-basic").first
            expect(btn).to_be_visible(timeout=timeout)
            btn.scroll_into_view_if_needed()

            menu = dropdown.locator("div.dropdown-menu[data-label='Devices']").first

            # Open ONLY if not already open 
            if menu.count() == 0 or not menu.is_visible():
                attempts = [
                    lambda: btn.click(force=True),
                    lambda: btn.click(force=True),
                    lambda: btn.press("ArrowDown"),
                    lambda: btn.press("Enter"),
                    lambda: btn.press("Space"),
                ]
                opened = False
                for act in attempts:
                    try:
                        act()
                    except Exception:
                        pass
                    try:
                        self.wait_until(lambda: menu.count() > 0 and menu.is_visible(),
                                        timeout_ms=min(timeout, 2000),
                                        interval_ms=150)
                        if menu.is_visible():
                            opened = True
                            break
                    except Exception:
                        pass

                if not opened:
                    raise AssertionError("Devices dropdown menu did not open (menu stayed hidden).")

            expect(menu).to_be_visible(timeout=timeout)

            scroller = menu.locator("div.simplebar-content-wrapper").first
            if scroller.count() == 0:
                scroller = menu
            expect(scroller).to_be_visible(timeout=timeout)

            def is_checked(device_li) -> bool:
                return device_li.locator("svg.unchecked").count() == 0

            def scroll_to_top():
                try:
                    scroller.evaluate("el => { el.scrollTop = 0; }")
                except Exception:
                    pass

            def scroll_page_down():
                try:
                    scroller.evaluate("el => { el.scrollTop = el.scrollTop + el.clientHeight; }")
                except Exception:
                    pass

            def get_scroll_state():
                return (
                    scroller.evaluate("el => el.scrollTop"),
                    scroller.evaluate("el => el.scrollHeight"),
                    scroller.evaluate("el => el.clientHeight"),
                )

            scroll_to_top()
            last_scroll_top = -1

            for _ in range(MAX_SCROLL_PAGES):
                row = menu.locator("li.dropdown-item.multiple", has_text=re.compile(rf"^\s*{re.escape(device_name)}\s*$")).first

                if row.count() > 0:
                    row.scroll_into_view_if_needed()
                    if is_checked(row):
                        row.click(force=True)
                        self.wait_until(lambda: not is_checked(row), timeout_ms=timeout, interval_ms=200)
                    return

                scroll_top, scroll_h, client_h = get_scroll_state()
                if scroll_top + client_h >= scroll_h - 2:
                    break
                if scroll_top == last_scroll_top:
                    break

                last_scroll_top = scroll_top
                scroll_page_down()

            raise AssertionError(f"Device '{device_name}' not found in Devices dropdown (even after scrolling).")

        except Exception as e:
            raise AssertionError(f"remove_device_filterBy_devices('{device_name}') failed. Problem: {e}")

    # ✅
    def remove_all_devices_filterBy_devices(self, timeout: int = 10000):
        """
        Clear all selected devices in the Devices dropdown.
        """
        try:
            self.set_filterBy("Devices")

            dropdown = self.page.locator("app-dropdown[label='Devices']").first
            if dropdown.count() == 0:
                raise AssertionError("Devices dropdown not found (app-dropdown[label='Devices']).")

            btn = dropdown.locator("button.dropdown-button, button[dropdowntoggle], button#button-basic").first
            expect(btn).to_be_visible(timeout=timeout)
            btn.scroll_into_view_if_needed()

            menu = dropdown.locator("div.dropdown-menu[data-label='Devices']").first

            # Open ONLY if not already open 
            if menu.count() == 0 or not menu.is_visible():
                def try_open():
                    try:
                        btn.click(force=True)
                    except Exception:
                        pass

                opened = False
                for _ in range(3):
                    try_open()
                    try:
                        self.wait_until(lambda: menu.count() > 0 and menu.is_visible(),
                                        timeout_ms=min(timeout, 2000),
                                        interval_ms=150)
                        opened = True
                        break
                    except Exception:
                        pass

                if not opened:
                    raise AssertionError("Devices dropdown menu did not open (menu stayed hidden).")

            expect(menu).to_be_visible(timeout=timeout)

            # Selected devices are marked with 'selected' class on the <li>
            selected_rows = menu.locator("li.dropdown-item.multiple.selected")
            if selected_rows.count() == 0:
                return  # nothing to clear

            # "All" row is the first multiple item with text "All"
            all_row = menu.locator("li.dropdown-item.multiple", has_text=re.compile(r"^\s*All\s*$", re.IGNORECASE)).first
            expect(all_row).to_be_visible(timeout=timeout)
            all_row.scroll_into_view_if_needed()

            # Click All until nothing is selected
            for _ in range(3):
                all_row.click(force=True)
                try:
                    self.wait_until(lambda: selected_rows.count() == 0,
                                    timeout_ms=min(timeout, 3000),
                                    interval_ms=200)
                    return
                except Exception:
                    pass

            raise AssertionError(f"Failed to clear Devices selection. Still selected: {selected_rows.count()}")

        except Exception as e:
            raise AssertionError(f"remove_all_devices_filterBy_devices failed. Problem: {e}")


    # ==========================================================
    # Filter By: Domain / Chassis
    # ==========================================================

    # ✅
    def select_domain_or_chassis_filterBy_domain_or_chassis(self, name: str, timeout: int = 8000):
        """
        Open the Domain/Chassis tree dropdown and select a domain or chassis by visible text.
        """
        try:
            name = (name or "").strip()
            if not name:
                raise ValueError("name is empty")

            # Normalize "All Domains" variants
            wants_all = name.lower() in ("all domains", "all")
            expected_btn_text = "All" if wants_all else name.split("/", 1)[0].strip()
            expected_rx = self.nav_text_regex(expected_btn_text)

            # 1) Locate the Domain/Chassis dropdown component and open it
            dd = self.page.locator("app-dropdown-inventory-tree").filter(has=self.page.locator("div.label", has_text=re.compile(r"^\s*Domain/Chassis\s*$"))).first

            btn = dd.locator("button.dropdown-inventory-tree-button").first
            expect(btn).to_be_visible(timeout=timeout)
            expect(btn).to_be_enabled(timeout=timeout)
            btn.click(force=True)

            # 2) The dropdown opens a modal dialog
            modal = self.page.locator("div.modal-dialog").first
            expect(modal).to_be_visible(timeout=timeout)

            if wants_all:
                # 3) Click the default item inside the modal
                default_item = modal.locator("section.dropdown-inventory-tree-default-item", has_text=re.compile(r"\bAll Domains\b", re.IGNORECASE)).first
                expect(default_item).to_be_visible(timeout=timeout)
                default_item.click(force=True)

            else:
                # 4) Pick a node from the inventory tree
                tree = modal.locator("app-inventory-tree").first
                expect(tree).to_be_visible(timeout=timeout)

                row = tree.locator(
                    "div.inventory-tree-level-title[type='DOMAIN'], "
                    "div.inventory-tree-level-title[type='CHASSIS']"
                ).filter(has_text=self.nav_text_regex(name)).first

                if row.count() == 0:
                    raise AssertionError(f"Domain/Chassis '{name}' not found in tree.")

                row.scroll_into_view_if_needed()
                expect(row).to_be_visible(timeout=timeout)
                row.click(force=True)

            # 5) Wait until the dropdown button updates
            btn_span = dd.locator("button.dropdown-inventory-tree-button span").first
            expect(btn_span).to_be_visible(timeout=timeout)

            def selected_updated() -> bool:
                try:
                    current = (btn_span.inner_text() or "").strip()
                    return expected_rx.search(current) is not None
                except Exception:
                    return False

            self.wait_until(selected_updated, timeout_ms=timeout, interval_ms=150)

            # Optional: close modal if it remains open 
            try:
                if modal.is_visible():
                    self.page.keyboard.press("Escape")
            except Exception:
                pass

            sleep(1)

        except Exception as e:
            raise AssertionError(f"select_domain_or_chassis_filterBy_domain_or_chassis('{name}') failed. Problem: {e}")

    # ✅
    def get_selected_domain_or_chassis_filterBy_domain_or_chassis(self) -> str:
        """
        Return the currently selected value in the Domain/Chassis tree dropdown.
        """
        try:
            dd = self.page.locator("app-dropdown-inventory-tree").filter(has=self.page.locator("div.label", has_text=re.compile(r"^\s*Domain/Chassis\s*$"))).first

            btn_span = dd.locator("button.dropdown-inventory-tree-button span").first
            expect(btn_span).to_be_visible(timeout=5000)

            return (btn_span.inner_text() or "").strip()

        except Exception as e:
            raise AssertionError(f"get_selected_domain_or_chassis_filterBy_domain_or_chassis failed. Problem: {e}")

    # ✅    
    def select_all_domains_filterBy_domain_or_chassis(self):
        """
        Select the 'All Domains' item in the Domain/Chassis tree dropdown.
        """
        self.select_domain_or_chassis_filterBy_domain_or_chassis("All Domains")

    # ==========================================================
    # Date Range
    # ==========================================================

    # ✅   
    def set_from_date(self, from_date_and_time: str, timeout: int = 10000):
        """
        Set 'From date' using input like:
        'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD HH:MM:SS'
        """
        try:
            def parse(s: str) -> datetime:
                s = s.strip()
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                    try:
                        return datetime.strptime(s, fmt)
                    except ValueError:
                        pass
                raise ValueError(f"Unsupported datetime format: '{s}'. Use 'YYYY-MM-DD HH:MM[:SS]'")

            dt = parse(from_date_and_time)
            target = dt.strftime("%d/%m/%Y %H:%M:%S")  

            inp = self.page.locator("#datepickerFrom input[formcontrolname='dateRangeFrom']").first
            expect(inp).to_be_visible(timeout=timeout)

            inp.click(force=True)
            inp.fill("")
            inp.fill(target)

            # close picker if open 
            picker = self.page.locator("bs-datepicker-container[role='dialog'], bs-daterangepicker-container[role='dialog']").first
            if picker.count() > 0:
                try:
                    if picker.is_visible():
                        self.page.keyboard.press("Escape")
                except Exception:
                    pass

            sleep(1)
            self.wait_until(lambda: (self.get_from_date() or "").strip() == target, timeout_ms=timeout, interval_ms=200)

        except Exception as e:
            raise AssertionError(f"set_from_date('{from_date_and_time}') failed. Problem: {e}")
    
    # ✅   
    def get_from_date(self) -> str:
        """
        Return the currently selected 'From date' string.
        """
        inp = self.page.locator("#datepickerFrom input[formcontrolname='dateRangeFrom']").first
        try:
            return (inp.input_value() or "").strip()
        except Exception:
            return (inp.get_attribute("value") or "").strip()
    
    # ✅   
    def set_to_date(self, to_date_and_time: str, timeout: int = 10000):
        """
        Set 'To date' using input like:
        'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD HH:MM:SS'
        """
        try:
            def parse(s: str) -> datetime:
                s = s.strip()
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                    try:
                        return datetime.strptime(s, fmt)
                    except ValueError:
                        pass
                raise ValueError(f"Unsupported datetime format: '{s}'. Use 'YYYY-MM-DD HH:MM[:SS]'")

            dt = parse(to_date_and_time)
            target = dt.strftime("%d/%m/%Y %H:%M:%S")

            inp = self.page.locator("#datepickerTo input[formcontrolname='dateRangeTo']").first
            expect(inp).to_be_visible(timeout=timeout)

            inp.click(force=True)
            inp.fill("")
            inp.fill(target)

            # close picker if open 
            picker = self.page.locator("bs-datepicker-container[role='dialog'], bs-daterangepicker-container[role='dialog']").first
            if picker.count() > 0:
                try:
                    if picker.is_visible():
                        self.page.keyboard.press("Escape")
                except Exception:
                    pass

            sleep(1)
            self.wait_until(lambda: (self.get_to_date() or "").strip() == target, timeout_ms=timeout, interval_ms=200)

        except Exception as e:
            raise AssertionError(f"set_to_date('{to_date_and_time}') failed. Problem: {e}")
    
    # ✅   
    def get_to_date(self) -> str:
        """
        Return the currently selected 'To date' string.
        """
        inp = self.page.locator("#datepickerTo input[formcontrolname='dateRangeTo']").first
        try:
            return (inp.input_value() or "").strip()
        except Exception:
            return (inp.get_attribute("value") or "").strip()


    # ==========================================================
    # Message Filter
    # ==========================================================

    # ✅   
    def set_message(self, message: str, timeout: int = 8000):
        """
        Set the Message filter text.
        """
        try:
            msg = (message or "").strip()

            inp = self.page.locator("div.form-message app-input[label='Message'] input[type='text']").first
            expect(inp).to_be_visible(timeout=timeout)

            inp.click(force=True)
            inp.fill("")          # clear
            if msg:
                inp.fill(msg)     # set

            # Wait until the input reflects the new value
            def value_ok() -> bool:
                try:
                    v = inp.input_value()
                except Exception:
                    v = inp.get_attribute("value") or ""
                return (v or "").strip() == msg

            self.wait_until(value_ok, timeout_ms=timeout, interval_ms=200)
            sleep(1)

        except Exception as e:
            raise AssertionError(f"set_message('{message}') failed. Problem: {e}")

    # ✅   
    def message_check_exact_match_only(self, timeout: int = 8000):
        """
        Enable 'Exact match only' in the Message options dropdown.
        """
        try:
            toggle = self.page.locator("#messageDropdown").first
            expect(toggle).to_be_visible(timeout=timeout)

            menu = self.page.locator("div.dropdown-menu[aria-labelledby='messageDropdown']").first

            # Open dropdown if needed
            if menu.count() == 0 or not menu.is_visible():
                toggle.click(force=True)
                expect(menu).to_be_visible(timeout=timeout)

            cb = menu.locator("app-checkbox[label='Exact match only']").first
            expect(cb).to_be_visible(timeout=timeout)

            container = cb.locator("label.checkbox-container").first
            expect(container).to_be_visible(timeout=timeout)

            def is_checked() -> bool:
                try:
                    return cb.locator("svg.unchecked").count() == 0
                except Exception:
                    return False

            if not is_checked():
                container.click(force=True)
                self.wait_until(lambda: is_checked(), timeout_ms=timeout, interval_ms=200)

            # Optional: close dropdown 
            try:
                if menu.is_visible():
                    self.page.keyboard.press("Escape")
            except Exception:
                pass

        except Exception as e:
            raise AssertionError(f"message_check_exact_match_only failed. Problem: {e}")

    # ✅   
    def message_uncheck_exact_match_only(self, timeout: int = 8000):
        """
        Disable 'Exact match only' in the Message options dropdown.
        """
        try:
            toggle = self.page.locator("#messageDropdown").first
            expect(toggle).to_be_visible(timeout=timeout)

            menu = self.page.locator("div.dropdown-menu[aria-labelledby='messageDropdown']").first

            # Open dropdown if needed
            if menu.count() == 0 or not menu.is_visible():
                toggle.click(force=True)
                expect(menu).to_be_visible(timeout=timeout)

            cb = menu.locator("app-checkbox[label='Exact match only']").first
            expect(cb).to_be_visible(timeout=timeout)

            container = cb.locator("label.checkbox-container").first
            expect(container).to_be_visible(timeout=timeout)

            def is_checked() -> bool:
                try:
                    return cb.locator("svg.unchecked").count() == 0
                except Exception:
                    return False

            if is_checked():
                container.click(force=True)
                self.wait_until(lambda: not is_checked(), timeout_ms=timeout, interval_ms=200)

            # Optional: close dropdown 
            try:
                if menu.is_visible():
                    self.page.keyboard.press("Escape")
            except Exception:
                pass

        except Exception as e:
            raise AssertionError(f"message_uncheck_exact_match_only failed. Problem: {e}")

    # ==========================================================
    # Ack Column
    # ==========================================================

    # ❌
    def check_Ack(self, row_index: int, timeout: int = 8000):
        """
        Check (enable) the Ack checkbox in a specific table row (0-based index).
        """
        try:
            rows = self.page.locator("table tbody tr")
            if rows.count() == 0:
                raise AssertionError("Ack table rows not found (table tbody tr).")

            if row_index < 0 or row_index >= rows.count():
                raise AssertionError(f"row_index out of range: {row_index}. Rows count: {rows.count()}")

            row = rows.nth(row_index)

            # Ack cell 
            cb_label = row.locator("td.centered app-checkbox label.checkbox-container").first
            expect(cb_label).to_be_visible(timeout=timeout)

            def is_checked() -> bool:
                try:
                    cls = cb_label.get_attribute("class") or ""
                    return "checked" in cls.split()
                except Exception:
                    return False

            if not is_checked():
                cb_label.click(force=True)
                self.wait_until(lambda: is_checked(), timeout_ms=timeout, interval_ms=200)

        except Exception as e:
            raise AssertionError(f"check_Ack(row_index={row_index}) failed. Problem: {e}")

    # ❌
    def uncheck_Ack(self, row_index: int, timeout: int = 8000):
        """
        Uncheck (disable) the Ack checkbox in a specific table row (0-based index),
        """
        try:
            rows = self.page.locator("table tbody tr")
            if rows.count() == 0:
                raise AssertionError("Ack table rows not found (table tbody tr).")

            if row_index < 0 or row_index >= rows.count():
                raise AssertionError(f"row_index out of range: {row_index}. Rows count: {rows.count()}")

            row = rows.nth(row_index)

            cb_label = row.locator("td.centered app-checkbox label.checkbox-container").first
            expect(cb_label).to_be_visible(timeout=timeout)

            def is_checked() -> bool:
                try:
                    cls = cb_label.get_attribute("class") or ""
                    return "checked" in cls.split()
                except Exception:
                    return False

            # If it’s checked, try to click to uncheck.
            if is_checked():
                cb_label.click(force=True)

                # Some systems may not allow un-acking; in that case it will stay checked.
                # We'll wait briefly, and if still checked, raise a clear message.
                try:
                    self.wait_until(lambda: not is_checked(), timeout_ms=min(timeout, 2500), interval_ms=200)
                except Exception:
                    raise AssertionError("Ack checkbox appears not toggleable off (remains checked).")

        except Exception as e:
            raise AssertionError(f"uncheck_Ack(row_index={row_index}) failed. Problem: {e}")

    # ==========================================================
    # Table Retrieval
    # ==========================================================

    # ✅
    def get_pages_count(self, timeout: int = 8000) -> int:
        """
        Return total number of pages in the Alarms/Events table pagination.
        """
        pagination = self.page.locator("div.simple-table-footer ul.pagination").first
        expect(pagination).to_be_visible(timeout=timeout)

        # All page number links 
        page_links = pagination.locator("li.page-item a.page-link", has_not_text=re.compile(r"Previous|Next|\.\.\.", re.IGNORECASE))

        count = page_links.count()
        if count == 0:
            return 1

        # The LAST numeric page is the total pages
        last_page_text = page_links.nth(count - 1).inner_text().strip()
        return int(last_page_text)

    # ✅
    def get_all_events(self, timeout: int = 15000, max_pages: int = 200) -> list[dict]:
        """
        Return all rows currently displayed in the Alarms/Events table across pagination.
        Output: list of dicts keyed by the visible column headers.
        """
        try:
            self.set_faults_type("Events")
            table = self.page.locator("div.faults-actionWrapper-table app-simple-table table").first
            expect(table).to_be_visible(timeout=timeout)

            total_pages = self.get_pages_count(timeout=timeout)
            print(f"Go over {total_pages} pages of events...")

            thead = table.locator("thead").first
            tbody = table.locator("tbody").first
            expect(thead).to_be_visible(timeout=timeout)
            expect(tbody).to_be_visible(timeout=timeout)

            # ----------------------------
            # Column headers + column types
            # ----------------------------
            ths = thead.locator("th")
            th_count = ths.count()
            if th_count == 0:
                return []

            headers: list[str] = []
            col_kinds: list[str] = []  # "text" | "checkbox" | "ignore"

            for i in range(th_count):
                th = ths.nth(i)
                cls = (th.get_attribute("class") or "").strip()

                # Ignore non-data columns (expand/edit icons)
                if "expand" in cls or "edit" in cls:
                    headers.append("")
                    col_kinds.append("ignore")
                    continue

                name_span = th.locator("span.name").first
                header_txt = self._clean(name_span.inner_text()) if name_span.count() else ""

                # Service affecting column is a checkbox in tbody, not text
                if header_txt.lower() == "service affecting":
                    headers.append(header_txt or "Service affecting")
                    col_kinds.append("checkbox")
                else:
                    headers.append(header_txt)
                    col_kinds.append("text")

            # Remove completely empty header slots 
            def parse_row(tr) -> dict:
                tds = tr.locator("td")
                d: dict = {}
                td_count = tds.count()

                for i in range(min(td_count, len(headers))):
                    if col_kinds[i] == "ignore":
                        continue
                    key = headers[i]
                    if not key:
                        continue

                    td = tds.nth(i)

                    if col_kinds[i] == "checkbox":
                        unchecked = td.locator("svg.unchecked")
                        d[key] = (unchecked.count() == 0)
                    else:
                        span = td.locator("span.name").first
                        txt = span.inner_text() if span.count() else td.inner_text()
                        d[key] = self._clean(txt)

                return d

            def snapshot_tbody() -> str:
                # Used to detect page change
                try:
                    return self._clean(tbody.inner_text())
                except Exception:
                    return ""

            def read_current_page_rows() -> list[dict]:
                # Wait until there is at least 1 row OR table is stable (some pages can be empty)
                self.wait_until(lambda: tbody.locator("tr").count() >= 0, timeout_ms=timeout, interval_ms=200)
                rows = tbody.locator("tr")
                out: list[dict] = []
                for r in range(rows.count()):
                    out.append(parse_row(rows.nth(r)))
                return out

            next_btn = self.page.locator("button", has_text=re.compile(r"^\s*Next\s*$", re.IGNORECASE)).first
            if next_btn.count() == 0:
                next_btn = self.page.locator("a", has_text=re.compile(r"^\s*Next\s*$", re.IGNORECASE)).first

            all_rows: list[dict] = []
            seen = set()

            def add_unique(rows: list[dict]):
                for row in rows:
                    # build a stable key (tuple of sorted items)
                    key = tuple(sorted(row.items()))
                    if key not in seen:
                        seen.add(key)
                        all_rows.append(row)

            # Page 1
            add_unique(read_current_page_rows())

            # If no paginator -> return current page only
            if next_btn.count() == 0:
                return all_rows

            # Iterate pages
            for _ in range(max_pages):
                # Stop if Next disabled
                try:
                    disabled = next_btn.is_disabled()
                except Exception:
                    cls = (next_btn.get_attribute("class") or "")
                    aria_disabled = (next_btn.get_attribute("aria-disabled") or "").lower() == "true"
                    disabled = ("disabled" in cls) or aria_disabled

                if disabled:
                    break

                before = snapshot_tbody()

                # Click next and wait for tbody to change (or at least for a short stable wait)
                next_btn.click(force=True)

                self.wait_until(lambda: snapshot_tbody() != before, timeout_ms=min(timeout, 8000), interval_ms=200)

                add_unique(read_current_page_rows())

            return all_rows

        except Exception as e:
            raise AssertionError(f"get_all_events failed. Problem: {e}")

    # ❌
    def get_all_alarms(self) -> list[dict]:
        pass

    # =========================
    # Pagination
    # =========================

    # ✅   
    def click_previous(self, timeout: int = 5000) -> bool:
        """
        Click the Previous page button.
        Returns True if clicked, False if disabled/not clickable.
        """
        pager = self.page.locator("div.pagination ngb-pagination ul.pagination").first
        expect(pager).to_be_visible(timeout=timeout)

        prev_li = pager.locator("li.page-item:has(a[aria-label='Previous'])").first
        expect(prev_li).to_be_visible(timeout=timeout)

        cls = (prev_li.get_attribute("class") or "")
        if "disabled" in cls.split():
            return False

        prev_a = prev_li.locator("a[aria-label='Previous']").first
        expect(prev_a).to_be_visible(timeout=timeout)
        prev_a.click(force=True)

        # sleep(0.5)
        return True

    # ✅   
    def click_next(self, timeout: int = 5000) -> bool:
        """
        Click the Next page button.
        Returns True if clicked, False if disabled/not clickable.
        """
        pager = self.page.locator("div.pagination ngb-pagination ul.pagination").first
        expect(pager).to_be_visible(timeout=timeout)

        next_li = pager.locator("li.page-item:has(a[aria-label='Next'])").first
        expect(next_li).to_be_visible(timeout=timeout)

        cls = (next_li.get_attribute("class") or "")
        if "disabled" in cls.split():
            return False

        next_a = next_li.locator("a[aria-label='Next']").first
        expect(next_a).to_be_visible(timeout=timeout)
        next_a.click(force=True)

        # sleep(0.5)
        return True






