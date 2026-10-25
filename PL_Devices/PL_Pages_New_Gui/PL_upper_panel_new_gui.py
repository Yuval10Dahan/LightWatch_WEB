'''
Created by: Yuval Dahan
Date: 03/08/2026
'''

from playwright.sync_api import Page, expect
from time import sleep, monotonic
import re


class PL_Upper_Panel:
    def __init__(self, page: Page):
        self.page = page

    # ==========================================================
    # Frame Helpers
    # ==========================================================

    # ✅
    def horizontal_menu_frame(self):
        return self.page.frame_locator("iframe[name='horizontal_menu_frame'], frame[name='horizontal_menu_frame']")

    # ✅
    def upper_panel_frame(self):
        return self.horizontal_menu_frame().frame_locator("iframe[name='box_menu'], frame[name='box_menu']")

    # ✅
    def logo_frame(self):
        return self.page.frame_locator("iframe[name='logo'], frame[name='logo']")

    # ✅
    def right_panel_frame(self):
        return self.page.frame_locator("iframe[name='right_panel'], frame[name='right_panel']")

    # ✅
    def vertical_menu_frame(self):
        return self.page.frame_locator("iframe[name='vertical_menu_frame'], frame[name='vertical_menu_frame']")

    # ✅
    def main_page_frame(self):
        return self.page.frame_locator("iframe[name='main_page'], frame[name='main_page']")

    # ✅
    def main_page_url(self) -> str:
        """Current URL of the main_page frame ('' if the frame isn't there yet)."""
        try:
            frame = self.page.frame(name="main_page")
            return (frame.url or "") if frame else ""
        except Exception:
            return ""

    # ✅
    def wait_for_main_page(self, fragment: str, timeout: int = 10_000) -> bool:
        """Poll until the main_page frame's URL contains `fragment` (case-insensitive)."""
        deadline = monotonic() + timeout / 1000.0
        needle = fragment.lower()
        while monotonic() < deadline:
            if needle in self.main_page_url().lower():
                return True
            self.page.wait_for_timeout(200)
        return False

    # ==========================================================
    # Upper Panel Buttons
    # ==========================================================

    # ✅
    def click_system(self, retries: int = 5, timeout: int = 10_000) -> bool:
        for attempt in range(retries):
            try:
                system_btn = self.upper_panel_frame().locator("#System").first
                sleep(2)
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

    # ✅
    def fault_is_selected(self) -> bool:
        """True when the left menu's Fault entry is active and Faults.asp is loaded."""
        try:
            cls = self.vertical_menu_frame().locator("#Fault").first.get_attribute("class") or ""
        except Exception:
            return False
        return "vertical_button_active" in cls and "faults.asp" in self.main_page_url().lower()

    # ✅
    def wait_for_fault_selected(self, timeout: int = 10_000, settle_ms: int = 400) -> bool:
        """Poll until the Fault page is up and still up `settle_ms` later."""
        deadline = monotonic() + timeout / 1000.0
        while monotonic() < deadline:
            if self.fault_is_selected():
                self.page.wait_for_timeout(settle_ms)
                if self.fault_is_selected():
                    return True
            else:
                self.page.wait_for_timeout(200)
        return False

    # ✅
    def click_fault(self, retries: int = 3, timeout: int = 10_000) -> bool:
        """
        Select 'Fault' in the left (vertical) menu.

        The #Fault entry is a div whose onclick runs SelectMenu('Fault'): that marks the
        entry active, stores db_menu, then — after a deliberate 250 ms setTimeout that
        works around iframe load ordering — points main_page at the Fault page. So the
        navigation lags the click and has to be waited for, not assumed.

        Returns:
            True  -> Fault selected and Faults.asp loaded in main_page
            False -> Fault entry not found/clickable, or the page never loaded
        """
        for attempt in range(retries):
            # ---- Guard: already on the Fault page ----
            if self.fault_is_selected():
                return True

            try:
                fault_btn = self.vertical_menu_frame().locator("#Fault").first
                expect(fault_btn).to_be_visible(timeout=timeout)
                fault_btn.scroll_into_view_if_needed()
                fault_btn.click(force=True, timeout=timeout)

                # Poll the combined state (menu entry active AND Faults.asp loaded), then
                # re-check after a short settle: coming from another section, main_page can
                # still be showing the old Faults.asp while that section's navigation is
                # in flight, which would otherwise read as an instant false success.
                if self.wait_for_fault_selected(timeout=timeout):
                    return True

                print(f"Fault tab clicked but Faults.asp did not load at attempt {attempt + 1} "
                      f"(main_page={self.main_page_url()})")

            except Exception as e:
                print(f"Fault tab not found/clickable at attempt {attempt + 1}: {e}")

        return False

    # ✅
    def all_is_selected(self) -> bool:
        """True when the ALL button carries its active class (ALLButton_active)."""
        try:
            cls = self.main_page_frame().locator("#ALL").first.get_attribute("class") or ""
            return "ALLButton_active" in cls
        except Exception:
            return False    # frame is mid-navigation — caller polls again

    # ✅
    def click_all(self, retries: int = 3, timeout: int = 10_000) -> bool:
        """
        Click the ALL button on the Fault page.

        In the new GUI the ALL button is NOT in the upper panel (horizontal_menu_frame ->
        box_menu, which now holds only the port buttons). It lives in Faults.asp, which
        loads into main_page only once Fault is selected in the left menu — so select the
        Fault tab first, then click ALL.

        Clicking it runs SelectFrame('ALL'), which stores db_frame=ALL and reloads
        main_page as Faults.asp?filter=All (the nested faults iframe follows with
        Faults_Tabs.asp?aore=0&filter=All). Because that reload replaces the button,
        success is confirmed by polling for its active class rather than by the click
        returning.

        Returns:
            True  -> ALL is selected on the Fault page
            False -> Fault page unreachable, or ALL never became active
        """
        if not self.click_fault(retries=retries, timeout=timeout):
            print("ALL button: could not open the Fault page")
            return False

        for attempt in range(retries):
            # ---- Guard: ALL already selected (db_frame persists across navigation) ----
            if self.all_is_selected():
                return True

            try:
                all_btn = self.main_page_frame().locator("#ALL").first
                expect(all_btn).to_be_visible(timeout=timeout)
                all_btn.scroll_into_view_if_needed()
                all_btn.click(force=True, timeout=timeout)

                deadline = monotonic() + timeout / 1000.0
                while monotonic() < deadline:
                    if self.all_is_selected():
                        return True
                    self.page.wait_for_timeout(200)

                print(f"ALL clicked but did not become active at attempt {attempt + 1} "
                      f"(main_page={self.main_page_url()})")

            except Exception as e:
                print(f"ALL button not found/clickable at attempt {attempt + 1}: {e}")

        return False

    # ✅
    def click_port_old(self, port_id, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Click a port button in the upper panel.
        """
        port_id = str(port_id).strip()
        if port_id.isdigit():
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
                try:
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False

    # ✅
    def click_port(self, port_id, retries: int = 5, timeout: int = 10_000) -> bool:
        """
        Playwright version of Click_Port.

        Supports:
        - 1 / "1" / "Port-1"
        - 22 / 23 / 24 (including dropdown under Port-21 when needed)
        - "200G" / "100G #1" / "100G #2"
        - "U0/1", "U0/1/2", "U1/2", "U1/2/1"
        - "C1/1"
        - "COM", "COM1", "COM2", "COM #1", "COM1 #2"
        - "MC1", "DCM1", "MUX1", "EDFA1"
        - "ETH1", "ETH2"
        - "MNG1", "MNG2"
        - "FAN"
        - "ADD", "WSS", "DROP"
        - "CH1", "P7"
        - "Uplink1"
        """

        dropdown_menu_dict = {
            "200G": "#Uplink-Cell > div:nth-child(3) > a:nth-child(1)",
            "100G #1": "#Uplink-Cell > div:nth-child(3) > a:nth-child(2)",
            "100G #2": "#Uplink-Cell > div:nth-child(3) > a:nth-child(3)",
            22: "#Port-21-Cell > div:nth-child(3) > a:nth-child(2)",
            23: "#Port-21-Cell > div:nth-child(3) > a:nth-child(3)",
            24: "#Port-21-Cell > div:nth-child(3) > a:nth-child(4)",
            "22": "#Port-21-Cell > div:nth-child(3) > a:nth-child(2)",
            "23": "#Port-21-Cell > div:nth-child(3) > a:nth-child(3)",
            "24": "#Port-21-Cell > div:nth-child(3) > a:nth-child(4)",
        }

        dc_client_port_dict = {
            "1": {"1": "257", "2": "258", "3": "259", "4": "260"},
            "2": {"1": "513", "2": "514", "3": "515", "4": "516"},
            "3": {"1": "769", "2": "770", "3": "771", "4": "772"},
            "4": {"1": "1025", "2": "1026", "3": "1027", "4": "1028"},
        }

        dc_uplink_port_dict = {
            "0": {"1": "Port-200", "2": "Port-201", "3": "Port-202", "4": "Port-203"},
            "1": {"1": "456", "2": "457"},
            "2": {"1": "712", "2": "713"},
            "3": {"1": "968", "2": "969"},
            "4": {"1": "1224", "2": "1225"},
        }

        dc_logic_uplink_port_dict = {
            "0": {
                "1": {
                    "1": "div.slot:nth-child(2) > div:nth-child(1) > div:nth-child(3) > a:nth-child(2)",
                    "2": "div.slot:nth-child(2) > div:nth-child(1) > div:nth-child(3) > a:nth-child(3)",
                },
                "2": {
                    "1": "div.slot:nth-child(3) > div:nth-child(1) > div:nth-child(3) > a:nth-child(2)",
                    "2": "div.slot:nth-child(3) > div:nth-child(1) > div:nth-child(3) > a:nth-child(3)",
                },
                "3": {
                    "1": "div.slot:nth-child(4) > div:nth-child(1) > div:nth-child(3) > a:nth-child(2)",
                    "2": "div.slot:nth-child(4) > div:nth-child(1) > div:nth-child(3) > a:nth-child(3)",
                },
                "4": {
                    "1": "div.slot:nth-child(5) > div:nth-child(1) > div:nth-child(3) > a:nth-child(2)",
                    "2": "div.slot:nth-child(5) > div:nth-child(1) > div:nth-child(3) > a:nth-child(3)",
                },
            },
            "1": {
                "1": {
                    "1": "#SlotX1 > div:nth-child(1) > div:nth-child(3) > a:nth-child(2)",
                    "2": "#SlotX1 > div:nth-child(1) > div:nth-child(3) > a:nth-child(3)",
                },
                "2": {
                    "1": "#SlotX1 > div:nth-child(3) > div:nth-child(3) > a:nth-child(2)",
                    "2": "#SlotX1 > div:nth-child(3) > div:nth-child(3) > a:nth-child(3)",
                },
            },
            "2": {
                "1": {
                    "1": "#SlotX2 > div:nth-child(1) > div:nth-child(3) > a:nth-child(2)",
                    "2": "#SlotX2 > div:nth-child(1) > div:nth-child(3) > a:nth-child(3)",
                },
                "2": {
                    "1": "#SlotX2 > div:nth-child(3) > div:nth-child(3) > a:nth-child(2)",
                    "2": "#SlotX2 > div:nth-child(3) > div:nth-child(3) > a:nth-child(3)",
                },
            },
            "3": {
                "1": {
                    "1": "#SlotX3 > div:nth-child(1) > div:nth-child(3) > a:nth-child(2)",
                    "2": "#SlotX3 > div:nth-child(1) > div:nth-child(3) > a:nth-child(3)",
                },
                "2": {
                    "1": "#SlotX3 > div:nth-child(3) > div:nth-child(3) > a:nth-child(2)",
                    "2": "#SlotX3 > div:nth-child(3) > div:nth-child(3) > a:nth-child(3)",
                },
            },
            "4": {
                "1": {
                    "1": "#SlotX4 > div:nth-child(1) > div:nth-child(3) > a:nth-child(2)",
                    "2": "#SlotX4 > div:nth-child(1) > div:nth-child(3) > a:nth-child(3)",
                },
                "2": {
                    "1": "#SlotX4 > div:nth-child(3) > div:nth-child(3) > a:nth-child(2)",
                    "2": "#SlotX4 > div:nth-child(3) > div:nth-child(3) > a:nth-child(3)",
                },
            },
        }

        def panel():
            return self.upper_panel_frame()

        def click_if_not_active(locator) -> None:
            expect(locator).to_be_visible(timeout=timeout)
            locator.scroll_into_view_if_needed()
            cls = (locator.get_attribute("class") or "").strip()
            if "_active" not in cls:
                locator.click(force=True, timeout=timeout)

        def click_plain(locator) -> None:
            expect(locator).to_be_visible(timeout=timeout)
            locator.scroll_into_view_if_needed()
            locator.click(force=True, timeout=timeout)

        def wait_and_click_dropdown(base_button_locator, option_selector: str) -> None:
            click_plain(base_button_locator)
            self.page.wait_for_timeout(1500)
            option = panel().locator(option_selector).first
            expect(option).to_be_visible(timeout=timeout)
            option.click(force=True, timeout=timeout)

        raw = str(port_id).strip()

        for attempt in range(retries):
            try:
                p = panel()

                # ==========================================================
                # Ports 22-24 (try direct id first, otherwise dropdown of Port-21)
                # ==========================================================
                if raw in {"22", "23", "24"} or port_id in {22, 23, 24}:
                    try:
                        direct_id = f"Port-{raw}"
                        btn = p.locator(f"#{direct_id}").first
                        click_if_not_active(btn)
                        return True
                    except Exception:
                        port_21 = p.locator("#Port-21").first
                        wait_and_click_dropdown(port_21, dropdown_menu_dict[raw])
                        return True

                # ==========================================================
                # Port 19 / 20 special handling (single/split mode)
                # ==========================================================
                elif raw in {"19", "20"} or port_id in {19, 20}:
                    if str(port_id) == "19" or port_id == 19:
                        uplink_btn = p.locator("#Port-19").first
                    else:
                        uplink_btn = p.locator("#Port-20").first

                    click_plain(uplink_btn)
                    self.page.wait_for_timeout(500)

                    dropdown_items = p.locator("#Uplink-Cell .dropdown-content a")
                    if dropdown_items.count() == 0:
                        return True

                    want_19 = str(raw) == "19"
                    found = None

                    for i in range(dropdown_items.count()):
                        a = dropdown_items.nth(i)
                        txt = (a.inner_text() or "").strip()
                        onclick = a.get_attribute("onclick") or ""

                        if want_19:
                            if txt == "100G #1" or "Port-19" in onclick:
                                found = a
                                break
                        else:
                            if txt == "100G #2" or "Port-20" in onclick:
                                found = a
                                break

                    if found is None:
                        raise Exception("Uplink dropdown present but no suitable 100G option found")

                    found.click(force=True, timeout=timeout)
                    return True

                # ==========================================================
                # Regular numeric ports: 1..99 etc
                # ==========================================================
                elif not isinstance(port_id, str) or re.match(r"^\d{1,2}$", raw):
                    try:
                        locator = p.locator(f"#Port-{raw}").first
                        click_if_not_active(locator)
                    except Exception:
                        port_value = f"P{raw}"
                        locator = p.locator(f"xpath=//*[@value='{port_value}']").first
                        click_if_not_active(locator)
                    return True

                # ==========================================================
                # 200G / 100G #1 / 100G #2
                # ==========================================================
                elif raw in {"200G", "100G #1", "100G #2"}:
                    uplink_btn = p.locator("#Port-19").first
                    wait_and_click_dropdown(uplink_btn, dropdown_menu_dict[raw])
                    return True

                # ==========================================================
                # DC / 2000T uplink syntax: U0/1 , U0/1/2 , U1/2 , U1/2/1
                # ==========================================================
                elif re.match(r"^[Uu]\s?(0(\/)[1-4]|0(\/)[1-4](\/)[1-2]|[1-4]((\/)[1-2]){1,2})$", raw):
                    cleaned = raw.replace(" ", "")
                    slot = cleaned[1]
                    uplink = cleaned[3]
                    logic_port = cleaned[-1] if len(cleaned) > 4 and cleaned.count("/") == 2 else None

                    main_btn_id = dc_uplink_port_dict[slot][uplink]
                    main_btn = p.locator(f"#{main_btn_id}").first
                    click_plain(main_btn)

                    if logic_port is not None:
                        self.page.wait_for_timeout(1500)
                        selector = dc_logic_uplink_port_dict[slot][uplink][logic_port]
                        option = p.locator(selector).first
                        expect(option).to_be_visible(timeout=timeout)
                        option.click(force=True, timeout=timeout)

                    self.page.reload(wait_until="domcontentloaded")
                    return True

                # ==========================================================
                # DC client syntax: C1/1 ... C4/4
                # ==========================================================
                elif re.match(r"^[Cc]\s?[1-4]((\/|\\)[1-4])$", raw):
                    cleaned = raw.replace(" ", "").replace("\\", "/")
                    slot = cleaned[1]
                    client_port = cleaned[3]

                    btn_id = dc_client_port_dict[slot][client_port]
                    btn = p.locator(f"#{btn_id}").first
                    click_if_not_active(btn)
                    return True

                # ==========================================================
                # COM / COM1 / COM2 (+ dropdown #1-#4)
                # ==========================================================
                elif re.match(r"(^(([Cc][Oo][Mm])([1-2])?)$)|([Cc][Oo][Mm][1-2]?\s?([#][1-4])$)", raw):
                    lower = raw.lower().replace(" ", "")

                    if re.match(r"^(com)$|^(com#[1-4])$", lower):
                        btn = p.locator("#COM").first
                        div_nchild = "3"
                    elif re.match(r"^(com1)$|^(com1#[1-4])$", lower):
                        btn = p.locator("#COM-1").first
                        div_nchild = "4"
                    elif re.match(r"^(com2)$|^(com2#[1-4])$", lower):
                        btn = p.locator("#COM-2").first
                        div_nchild = "5"
                    else:
                        raise Exception(f"Unsupported COM syntax: {raw}")

                    click_plain(btn)

                    hash_match = re.search(r"#([1-4])$", raw.replace(" ", ""))
                    if hash_match:
                        a_nchild = hash_match.group(1)
                        selector = (
                            "#box_nolines > div.panelbuttons > div:nth-child("
                            + div_nchild
                            + f") > div:nth-child(3) > a:nth-child({a_nchild})"
                        )
                        option = p.locator(selector).first
                        expect(option).to_be_visible(timeout=timeout)
                        option.click(force=True, timeout=timeout)
                        self.page.reload(wait_until="domcontentloaded")

                    return True

                # ==========================================================
                # MCx
                # ==========================================================
                elif re.match(r"^[Mm][Cc]", raw):
                    mc_id = f"MC-{raw[-1]}"
                    click_plain(p.locator(f"#{mc_id}").first)
                    return True

                # ==========================================================
                # DCMx
                # ==========================================================
                elif re.match(r"^[Dd][Cc][Mm]", raw):
                    dcm_id = f"DCM-{raw[-1]}"
                    click_plain(p.locator(f"#{dcm_id}").first)
                    return True

                # ==========================================================
                # MUXx / MUX
                # ==========================================================
                elif re.match(r"^[Mm][Uu][Xx]", raw):
                    mux_num = raw[-1] if raw[-1].isdigit() else "1"
                    mux_id = f"MUX-{mux_num}"
                    click_plain(p.locator(f"#{mux_id}").first)
                    return True

                # ==========================================================
                # EDFAx
                # ==========================================================
                elif re.match(r"^[Ee][Dd][Ff][Aa]", raw):
                    edfa_num = raw[-1] if raw[-1].isdigit() else "1"
                    edfa_id = f"EDFA-{edfa_num}"
                    click_plain(p.locator(f"#{edfa_id}").first)
                    return True

                # ==========================================================
                # ETH1 / ETH2
                # ==========================================================
                elif re.match(r"^[Ee][Tt][Hh]", raw):
                    self.page.wait_for_timeout(1000)
                    eth_num = raw[-1]
                    eth_id = "Ethernet" if eth_num == "1" else f"Eth{eth_num}"
                    btn = p.locator(f"#{eth_id}").first

                    for eth_attempt in range(10):
                        cls = (btn.get_attribute("class") or "").strip()
                        if "_active" in cls:
                            return True
                        try:
                            click_plain(btn)
                        except Exception:
                            continue
                        self.page.wait_for_timeout(300)

                    cls = (btn.get_attribute("class") or "").strip()
                    if "_active" not in cls:
                        raise Exception(f"ETH{eth_num} did not become active")
                    return True

                # ==========================================================
                # MNG1 / MNG2
                # ==========================================================
                elif re.match(r"^[Mm][Nn][Gg]", raw):
                    self.page.wait_for_timeout(1000)
                    mng_num = raw[-1]
                    mng_id = f"MNG-{mng_num}"
                    btn = p.locator(f"#{mng_id}").first

                    for mng_attempt in range(10):
                        cls = (btn.get_attribute("class") or "").strip()
                        if "_active" in cls:
                            return True
                        try:
                            click_plain(btn)
                        except Exception:
                            continue
                        self.page.wait_for_timeout(300)

                    cls = (btn.get_attribute("class") or "").strip()
                    if "_active" not in cls:
                        raise Exception(f"MNG{mng_num} did not become active")
                    return True

                # ==========================================================
                # FAN
                # New GUI moved FAN (along with PSU/ExtAlarm) out of box_menu and into the
                # top-level "right_panel" frame. Try there first, fall back to the old
                # box_menu location for products that never moved it.
                # ==========================================================
                elif re.match(r"^[Ff][Aa][Nn]", raw):
                    try:
                        fan_btn = self.right_panel_frame().locator("#FAN").first
                        expect(fan_btn).to_be_visible(timeout=2_000)
                    except Exception:
                        fan_btn = p.locator("#FAN").first
                    click_plain(fan_btn)
                    return True

                # ==========================================================
                # ADD / WSS
                # ==========================================================
                elif re.match(r"^[Aa][Dd][Dd]", raw) or re.match(r"^[Ww][Ss][Ss]", raw):
                    click_plain(p.locator("[name='WSS']").first)
                    return True

                # ==========================================================
                # DROP
                # ==========================================================
                elif re.match(r"^[Dd][Rr][Oo][Pp]", raw):
                    click_plain(p.locator("[name='WSS-OCM']").first)
                    return True

                # ==========================================================
                # CHx
                # ==========================================================
                elif re.match(r"^[Cc][Hh]\s?(?:[1-8])$", raw):
                    num = raw[2:] if raw[1].lower() == "h" else raw[1:]
                    num = num.strip()
                    port_val = f"CH{num}"
                    btn = p.locator(f"xpath=//*[@value='{port_val}']").first
                    expect(btn).to_be_visible(timeout=timeout)
                    btn.scroll_into_view_if_needed()
                    return True

                # ==========================================================
                # Px
                # ==========================================================
                elif re.match(r"^[Pp]\s?(?:[1-9]|[1-2][0-9]|3[0-2])$", raw):
                    num = raw[1:].strip()
                    port_val = f"P{num}"
                    btn = p.locator(f"xpath=//*[@value='{port_val}']").first
                    click_if_not_active(btn)
                    return True

                # ==========================================================
                # Uplinkx
                # ==========================================================
                elif re.match(r"^[Uu][Pp][Ll][Ii][Nn][Kk]", raw):
                    uplink_num = raw[-1]
                    uplink_id = f"Uplink-{uplink_num}"
                    click_plain(p.locator(f"#{uplink_id}").first)
                    return True

                else:
                    print("Invalid Port identifier")
                    return False

            except Exception as e:
                print(e)
                self.page.wait_for_timeout(1000)
                try:
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass
                continue

        return False

    # ✅
    def upper_panel_logout(self, retries: int = 5, timeout: int = 10_000) -> bool:
        for attempt in range(retries):
            try:
                logout_btn = self.logo_frame().locator("#Logout").first
                sleep(3)
                expect(logout_btn).to_be_visible(timeout=timeout)
                logout_btn.scroll_into_view_if_needed()
                self.refresh()  # Ensure we're on the latest page state before clicking logout
                logout_btn.click(force=True, timeout=timeout)
                return True

            except Exception as e:
                print(f"Logout button not found/clickable at attempt {attempt + 1}: {e}")
                try:
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False

    # ✅
    def refresh(self, retries: int = 5, timeout: int = 10_000) -> bool:
        for attempt in range(retries):
            try:
                refresh_btn = self.logo_frame().locator("#refresh").first
                sleep(2)
                expect(refresh_btn).to_be_visible(timeout=timeout)
                refresh_btn.scroll_into_view_if_needed()
                refresh_btn.click(force=True, timeout=timeout)
                return True

            except Exception as e:
                print(f"Refresh button not found/clickable at attempt {attempt + 1}: {e}")
                try:
                    self.page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

        return False
