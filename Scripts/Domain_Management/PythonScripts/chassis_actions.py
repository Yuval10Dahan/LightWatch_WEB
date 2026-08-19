"""
Created by: Ron Shuster
Date: 02/08/2026

Comprehensive Domain Management Test – Chassis
=====================================================
Tests the "Chassis" actions inside Domain Management:
    - Create chassis (assign a new Chassis ID to a device)
    - Add several elements to the same chassis
    - Move a chassis (with its devices) to a different domain
    - Assign an existing Chassis ID via "New Chassis ID" and verify no
      duplicate chassis is created (merges into the existing one instead)
    - Rename chassis, and verify the resulting name keeps the original
      Chassis ID as a fixed suffix
    - Enter an invalid Chassis ID (non-numeric) and verify it is rejected
      (negative test) – a Chassis ID must be numbers only
    - Remove a chassis that still contains devices (negative test)
    - Remove a device from a chassis (leaving it empty), then remove the
      now-empty chassis
    - Verify the two devices used by this test are actually discovered and
      available in the network (via Network Topology) before touching
      Domain Management

*** Runtime: approximately 15 minutes ***
"""

from playwright.sync_api import sync_playwright

from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.domain_management import DomainManagement
from Pages.network_topology import NetworkTopology
from Utils.utils import refresh_page, create_page
import re
import time
from time import sleep
from Utils.Logger import create_logger
import sys
from sys import argv
from Utilities.QCreporter import open_report, close_report, step_passed, step_failed



# Allow emojis on QC
import os
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass



# ================================================================
# Configuration
# ================================================================

if len(argv) == 2:
    directory = argv[1]
    const_dict = eval(open(directory, 'r').read())
    globals().update(const_dict)
elif 2 < len(argv) < 3:
    directory = argv[1] + ' ' + argv[2]
    const_dict = eval(open(directory, 'r').read())
    globals().update(const_dict)
else:
    # ================================================================
    # Values for the Parameter file (from QC)
    # ================================================================

    LW_SERVER_HOST_IP  = "172.16.10.22:8080"
    LW_USERNAME = "administrator"
    LW_PASSWORD = "administrator"

    DEVICE_IP = "172.16.20.126"
    DEVICE_IP_2 = "172.16.20.120"

    NEW_CHASSIS_ID = "777"
    TEMP_CHASSIS_ID = "778"
    CHASSIS_DOMAIN_NAME = "testChassisDomain"
    RENAMED_CHASSIS_PREFIX = "AutomationChassis"
    INVALID_CHASSIS_ID = "abc"



# ================================================================
# Values that should not be changed
# ================================================================

BASE_URL = f"http://{LW_SERVER_HOST_IP}/"

# Root nodes of the Domain Management tree.
INVENTORY_ROOT_NAME = "Inventory"
DEFAULT_DOMAIN_NAME = "Default"

# A chassis created via "New Chassis ID" is always named "Chassis: <id>" by
# the system, displayed in the tree as "Chassis: <id>/<id>".
CHASSIS_BASE_NAME = f"Chassis: {NEW_CHASSIS_ID}"
CHASSIS_FULL_NAME = f"Chassis: {NEW_CHASSIS_ID}/{NEW_CHASSIS_ID}"

RENAMED_CHASSIS_BASE_NAME = f"{RENAMED_CHASSIS_PREFIX}: {NEW_CHASSIS_ID}"
RENAMED_CHASSIS_FULL_NAME = f"{RENAMED_CHASSIS_PREFIX}: {NEW_CHASSIS_ID}/{NEW_CHASSIS_ID}"

TEMP_CHASSIS_BASE_NAME = f"Chassis: {TEMP_CHASSIS_ID}"

LOGGER_ROOT_DIRECTORY = 'G:\\Python\\PacketLight Automation\\LightWatch_WEB\\Scripts\\Domain_Management'
LOGGER_DIRECTORY_NAME = "chassis_actions"
LOG_FILE_NAME = 'chassis_actions.log'
REPORT_PATH = None

# ================================================================
# Helper – step runner
# ================================================================

def run_step(step_num, step_function, logger, report) -> bool:
    """
    Runs a step - prints consistent success / fail line.
    Returns True on success, False on failure.
    """
    try:
        step_function()
        print(f"Step {step_num} – Pass ✅")
        logger.info(f"Step {step_num} – Pass.")
        step_passed(report, f"Step {step_num} – Pass.")
        return True
    except Exception as e:
        print(f"Step {step_num} – Fail ❌  Error: {e}")
        logger.info(f"Step {step_num} – Fail.")
        logger.info(f"Step {step_num} Error: {e}")
        step_failed(report, f"Step {step_num} – Fail.")
        return False

def remove_domain_with_retry(domain_management: DomainManagement, page, domain_name: str, attempts: int = 3, delay_seconds: int = 3):
    """
    Remove a domain, retrying a few times on failure.

    remove_domain() confirms the removal by re-checking the tree right after a
    fixed render wait. On a slow render the backend deletion can complete a few
    seconds after that check already reported "still exists". Retrying is safe:
    remove_domain() itself first checks whether the domain is already gone and
    returns immediately in that case, so a retry never repeats a real UI action
    unless the previous attempt truly failed.
    """
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            domain_management.remove_domain(domain_name)
            return
        except AssertionError as e:
            last_error = e
            refresh_page(page)
            sleep(delay_seconds)

    raise last_error

def remove_chassis_with_retry(domain_management: DomainManagement, page, chassis_name: str, parent_domain_name: str | None = None,
    attempts: int = 3, delay_seconds: int = 3):
    """
    Remove a chassis, retrying a few times on failure - same rationale as
    remove_domain_with_retry() above: remove_chassis() is idempotent (it
    first checks whether the chassis is already gone), so a retry never
    repeats a real UI action unless the previous attempt truly failed.
    """
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            domain_management.remove_chassis(chassis_name, parent_domain_name=parent_domain_name)
            return
        except AssertionError as e:
            last_error = e
            refresh_page(page)
            sleep(delay_seconds)

    raise last_error

def rename_chassis_with_retry(domain_management: DomainManagement, page, old_chassis_name: str, new_chassis_name: str,
    new_description: str | None = None, attempts: int = 3, delay_seconds: int = 3):
    """
    Rename a chassis, retrying a few times on failure.

    click_rename_chassis() selects the chassis row with a single click and
    a single wait for the "Rename" button to become enabled - unlike e.g.
    click_remove_chassis_btn(), it never retries that click itself. When the
    first click occasionally doesn't register as a real row selection, the
    whole wait just times out - retrying the whole rename here (which
    re-selects the row from scratch each time) works around that.
    """
    last_error = None
    for attempt in range(1, attempts + 1):
        # If a previous attempt actually succeeded despite raising (e.g. the
        # rename went through but a later verification step timed out),
        # don't try to rename an already-renamed (and now missing) old name.
        if not domain_management.verify_element_deleted(new_chassis_name, element_type="chassis", refresh=False):
            return

        try:
            domain_management.rename_chassis(old_chassis_name, new_chassis_name, new_description=new_description)
            return
        except AssertionError as e:
            last_error = e
            refresh_page(page)
            sleep(delay_seconds)

    raise last_error

def device_rows_under_chassis(domain_management: DomainManagement, chassis_name: str, device_ip: str | None = None):
    """
    Locate device rows scoped strictly to the tree subtree of the given
    chassis. With device_ip=None, the returned locator's .count() is the
    total number of devices currently sitting inside that one chassis -
    used to prove several elements share the same chassis, and later to
    prove a chassis is truly empty before removing it. With device_ip set,
    it narrows down to that specific device only.
    """
    chassis_row = domain_management.chassis_row_locator(chassis_name)
    chassis_subtree = chassis_row.locator("xpath=ancestor::app-inventory-tree-level[1]")

    device_types = ("DEVICE", "ROADM", "TRANSPONDER", "MUXPONDER")
    rows = chassis_subtree.locator(", ".join(f"div.inventory-tree-level-title[type='{t}']" for t in device_types))

    if device_ip:
        device_rx = re.compile(rf"(^|\()\s*{re.escape(device_ip)}\s*(\)|$)")
        return rows.filter(has_text=device_rx)

    return rows

def find_parent_chassis_of_device(domain_management: DomainManagement, device_ip: str, timeout: int = 8000) -> str | None:
    """
    If device_ip is currently nested inside a chassis anywhere in the "From"
    tree, expand that chassis (so the device row becomes visible/clickable)
    and return its on-screen name. Returns None if the device isn't inside
    any chassis right now (e.g. it already sits directly under a domain).

    Needed because a real lab device can already belong to some unrelated,
    pre-existing chassis before this test even starts - its row stays
    collapsed/invisible until that specific chassis is expanded, and
    click_change_CHASSIS_ID()/move_to_domain() only expand a parent chassis
    when the caller tells them which one.
    """
    tree = domain_management.from_tree()
    device_rx = re.compile(rf"(^|\()\s*{re.escape(device_ip)}\s*(\)|$)")
    device_types = ("DEVICE", "ROADM", "TRANSPONDER", "MUXPONDER")

    chassis_rows = tree.locator("div.inventory-tree-level-title[type='CHASSIS']")
    for i in range(chassis_rows.count()):
        chassis_row = chassis_rows.nth(i)
        chassis_subtree = chassis_row.locator("xpath=ancestor::app-inventory-tree-level[1]")
        device_rows = chassis_subtree.locator(
            ", ".join(f"div.inventory-tree-level-title[type='{t}']" for t in device_types)
        ).filter(has_text=device_rx)

        if device_rows.count() > 0:
            chassis_name = (chassis_row.inner_text() or "").strip()
            domain_management.expand_tree_node_if_collapsed(chassis_row, timeout=timeout)
            return chassis_name

    return None

def discover_device_ips(network_topology: NetworkTopology) -> list[str]:
    """
    Return every device IP currently visible in the Network Topology tree.

    get_navigation_info_elements_list() returns ALL element titles (domains,
    chassis AND devices) as raw tree text, so device rows are picked out
    here by extracting the "(IP)" suffix each device title carries -
    domain/chassis titles never have one.
    """
    ip_rx = re.compile(r"\((\d{1,3}(?:\.\d{1,3}){3})\)")

    ips = []
    for title in network_topology.get_navigation_info_elements_list():
        match = ip_rx.search(title)
        if match:
            ips.append(match.group(1))

    return ips

def attempt_set_invalid_chassis_id(domain_management: DomainManagement, element_name: str, invalid_chassis_id: str,
    parent_chassis: str | None = None, timeout: int = 8000) -> bool:
    """
    Try to assign invalid_chassis_id (expected to be rejected, since a
    Chassis ID must be numbers only) as a brand-new Chassis ID for
    element_name. Returns True if the system blocked it before it could be
    saved, False if it was somehow accepted.

    The "New Chassis ID" field is a browser <input type="number">, so typing
    a non-numeric value is expected to be refused right at the fill() step -
    either Playwright itself raises, or the browser silently leaves the
    field empty, which in turn keeps the "Save" button disabled. Both
    outcomes count as blocked here.
    """
    domain_management.click_change_CHASSIS_ID(element_name, parent_chassis=parent_chassis, timeout=timeout)
    domain_management.change_the_chassis_ID_to_new_chassis_ID(timeout=timeout)
    domain_management.change_the_chassis_ID_next_btn(timeout=timeout)

    was_blocked = False
    try:
        domain_management.set_new_chassis_ID(invalid_chassis_id, timeout=timeout)
    except Exception:
        was_blocked = True

    if not was_blocked:
        try:
            domain_management.change_the_chassis_ID_save_btn(timeout=min(timeout, 3000))
        except AssertionError:
            was_blocked = True

    # Leave the modal in a clean state regardless of outcome, so a rejected
    # attempt never leaks an open modal into the next step.
    try:
        domain_management.close_change_the_chassis_ID_window(timeout=timeout)
    except Exception:
        pass

    return was_blocked

# ================================================================
# Main test
# ================================================================

def test_chassis_actions(page, left_panel: LeftPanel, logger, report):
    domain_management = DomainManagement(page)
    network_topology = NetworkTopology(page)

    results = {}

    #########################################################################
    # Step 1 – Verify prerequisite devices are available in the network.   #
    # Before touching Domain Management, use Network Topology's device     #
    # list to confirm DEVICE_IP and DEVICE_IP_2 are actually discovered on  #
    # the network right now - if either is missing, every later step would #
    # fail for an unrelated reason (device not present), not a real bug.   #
    #########################################################################
    def step_1():
        left_panel.click_network_topology()
        network_topology.show_navigation_info()
        available_ips = discover_device_ips(network_topology)
        network_topology.hide_navigation_info()

        for ip in (DEVICE_IP, DEVICE_IP_2):
            assert ip in available_ips, (
                f"'{ip}' was expected to be discovered and available on the network before running "
                f"the Chassis actions test, but it was not found. Currently available device IPs: {available_ips}.")

        left_panel.click_domain_management()

    results[1] = run_step(1, step_1, logger, report)

    #########################################################################
    # Step 2 – Create chassis: assign a brand-new Chassis ID to DEVICE_IP. #
    # Verify a chassis with that ID now exists in the tree, and DEVICE_IP  #
    # is nested inside it.                                                 #
    #########################################################################
    def step_2():
        chassis_domain_exists = not domain_management.verify_element_deleted(
            CHASSIS_DOMAIN_NAME, element_type="domain", refresh=False)

        current_chassis_name = None
        if not domain_management.verify_element_deleted(RENAMED_CHASSIS_BASE_NAME, element_type="chassis", refresh=True):
            current_chassis_name = RENAMED_CHASSIS_BASE_NAME
        elif not domain_management.verify_element_deleted(CHASSIS_BASE_NAME, element_type="chassis", refresh=False):
            current_chassis_name = CHASSIS_BASE_NAME

        if current_chassis_name and chassis_domain_exists:
            # A whole chassis (unlike a device nested inside one) moves
            # between domains fine via "Move to domain".
            try:
                domain_management.move_to_domain(source_item_name=current_chassis_name, target_domain_name=DEFAULT_DOMAIN_NAME)
            except Exception:
                pass

        if current_chassis_name == RENAMED_CHASSIS_BASE_NAME:
            try:
                rename_chassis_with_retry(domain_management, page, RENAMED_CHASSIS_BASE_NAME, CHASSIS_BASE_NAME)
            except Exception:
                pass

        if not domain_management.verify_element_deleted(TEMP_CHASSIS_BASE_NAME, element_type="chassis", refresh=True):
            for ip in (DEVICE_IP, DEVICE_IP_2):
                if device_rows_under_chassis(domain_management, TEMP_CHASSIS_BASE_NAME, ip).count() > 0:
                    domain_management.change_CHASSIS_ID(
                        element_name=ip, to_mode="new", new_chassis_id=NEW_CHASSIS_ID, parent_chassis=TEMP_CHASSIS_BASE_NAME)

            if not domain_management.verify_element_deleted(TEMP_CHASSIS_BASE_NAME, element_type="chassis", refresh=True):
                remove_chassis_with_retry(
                    domain_management, page, TEMP_CHASSIS_BASE_NAME,
                    parent_domain_name=CHASSIS_DOMAIN_NAME if chassis_domain_exists else None)

        if chassis_domain_exists and not domain_management.verify_element_deleted(
            CHASSIS_DOMAIN_NAME, element_type="domain", refresh=True):
            remove_domain_with_retry(domain_management, page, CHASSIS_DOMAIN_NAME)

        existing_parent_chassis = find_parent_chassis_of_device(domain_management, DEVICE_IP)
        domain_management.change_CHASSIS_ID(
            element_name=DEVICE_IP, to_mode="new", new_chassis_id=NEW_CHASSIS_ID, parent_chassis=existing_parent_chassis)

        assert domain_management.row_locator(CHASSIS_FULL_NAME).count() > 0, (
            f"'{CHASSIS_FULL_NAME}' was not created after assigning Chassis ID {NEW_CHASSIS_ID} to '{DEVICE_IP}'.")

        domain_management.expand_element(CHASSIS_BASE_NAME)
        assert device_rows_under_chassis(domain_management, CHASSIS_BASE_NAME, DEVICE_IP).count() > 0, (
            f"'{DEVICE_IP}' was not found nested under '{CHASSIS_FULL_NAME}' after creating the chassis.")

    results[2] = run_step(2, step_2, logger, report)

    #########################################################################
    # Step 3 – Add several elements to the same chassis: assign DEVICE_IP_2 #
    # to the SAME Chassis ID via "Existing Chassis ID". Verify both devices #
    # now live under one chassis, and there is still exactly one chassis   #
    # row with that ID - adding a second device must never spawn a         #
    # duplicate chassis node.                                              #
    #########################################################################
    def step_3():
        existing_parent_chassis = find_parent_chassis_of_device(domain_management, DEVICE_IP_2)
        domain_management.change_CHASSIS_ID(
            element_name=DEVICE_IP_2, to_mode="existing", existing_chassis_id=CHASSIS_BASE_NAME,
            parent_chassis=existing_parent_chassis)

        domain_management.expand_element(CHASSIS_BASE_NAME)
        chassis_devices = device_rows_under_chassis(domain_management, CHASSIS_BASE_NAME)
        assert chassis_devices.count() == 2, (
            f"Expected exactly 2 devices under '{CHASSIS_FULL_NAME}' after adding '{DEVICE_IP_2}' to the "
            f"same chassis as '{DEVICE_IP}', found {chassis_devices.count()}.")

        chassis_rows = domain_management.from_tree().locator(
            "div.inventory-tree-level-title[type='CHASSIS']", has_text=domain_management.nav_text_regex(CHASSIS_BASE_NAME))
        assert chassis_rows.count() == 1, (
            f"Expected exactly one '{CHASSIS_BASE_NAME}' chassis row after adding a second device to it, "
            f"found {chassis_rows.count()}.")

    results[3] = run_step(3, step_3, logger, report)

    #########################################################################
    # Step 4 – Assign an existing Chassis ID via "New Chassis ID" (negative #
    # for duplication, positive for merging). A device removed from Domain  #
    # Management can only be re-added from a different window (Device      #
    # Discovery), so instead of remove+re-add, park DEVICE_IP_2 in a        #
    # different, temporary chassis first via "New Chassis ID", then        #
    # reassign it back to the ORIGINAL Chassis ID - again typed through     #
    # "New Chassis ID" (instead of picked from the "Existing Chassis ID"    #
    # dropdown, as Step 3 did). Verify it merges back into the existing     #
    # chassis rather than creating a second, duplicate one.                #
    #########################################################################
    def step_4():
        domain_management.change_CHASSIS_ID(
            element_name=DEVICE_IP_2, to_mode="new", new_chassis_id=TEMP_CHASSIS_ID, parent_chassis=CHASSIS_BASE_NAME)

        assert device_rows_under_chassis(domain_management, CHASSIS_BASE_NAME, DEVICE_IP_2).count() == 0, (
            f"'{DEVICE_IP_2}' is still present under '{CHASSIS_BASE_NAME}' after moving it to the "
            f"temporary '{TEMP_CHASSIS_BASE_NAME}' chassis.")

        domain_management.change_CHASSIS_ID(
            element_name=DEVICE_IP_2, to_mode="new", new_chassis_id=NEW_CHASSIS_ID, parent_chassis=TEMP_CHASSIS_BASE_NAME)

        chassis_rows = domain_management.from_tree().locator(
            "div.inventory-tree-level-title[type='CHASSIS']", has_text=domain_management.nav_text_regex(CHASSIS_BASE_NAME))
        assert chassis_rows.count() == 1, (
            f"Re-adding '{DEVICE_IP_2}' via 'New Chassis ID' with an already-used ID was expected to merge "
            f"into the existing chassis, but {chassis_rows.count()} '{CHASSIS_BASE_NAME}' rows were found.")

        domain_management.expand_element(CHASSIS_BASE_NAME)
        assert device_rows_under_chassis(domain_management, CHASSIS_BASE_NAME, DEVICE_IP_2).count() > 0, (
            f"'{DEVICE_IP_2}' was not found back under '{CHASSIS_BASE_NAME}' after the merge.")

        # Clean up the now-empty temporary chassis, if it's still around.
        if not domain_management.verify_element_deleted(TEMP_CHASSIS_BASE_NAME, element_type="chassis", refresh=True):
            remove_chassis_with_retry(domain_management, page, TEMP_CHASSIS_BASE_NAME)

    results[4] = run_step(4, step_4, logger, report)

    #########################################################################
    # Step 5 – Rename chassis. Verify the resulting name keeps the original #
    # numeric Chassis ID as a fixed suffix - renaming only ever replaces    #
    # the text prefix in front of it, never the ID itself.                 #
    #########################################################################
    def step_5():
        rename_chassis_with_retry(domain_management, page, CHASSIS_BASE_NAME, RENAMED_CHASSIS_BASE_NAME, new_description="renamed by automation")

        renamed_row = domain_management.row_locator(RENAMED_CHASSIS_BASE_NAME)
        assert renamed_row.count() > 0, (
            f"No chassis matching '{RENAMED_CHASSIS_BASE_NAME}' was found in the tree after renaming '{CHASSIS_BASE_NAME}'.")

        displayed_name = renamed_row.inner_text().strip()

        id_match = re.search(r"[:\-]\s*(\d+)\s*/\s*\1\s*$", displayed_name)
        assert id_match, f"'{displayed_name}' does not end with the expected 'ID/ID' suffix."
        assert id_match.group(1) == NEW_CHASSIS_ID, (
            f"Expected the renamed chassis to keep Chassis ID '{NEW_CHASSIS_ID}', but the tree shows "
            f"'{displayed_name}' (ID suffix = '{id_match.group(1)}').")

    results[5] = run_step(5, step_5, logger, report)

    #########################################################################
    # Step 6 – Invalid Chassis ID (negative test). A Chassis ID must be     #
    # numbers only - attempt to assign a non-numeric value and verify it   #
    # is rejected before it can be saved, leaving the chassis untouched.    #
    #########################################################################
    def step_6():
        was_blocked = attempt_set_invalid_chassis_id(
            domain_management, DEVICE_IP, INVALID_CHASSIS_ID, parent_chassis=RENAMED_CHASSIS_BASE_NAME)

        assert was_blocked, (
            f"Assigning non-numeric Chassis ID '{INVALID_CHASSIS_ID}' to '{DEVICE_IP}' was expected to be "
            f"rejected (a Chassis ID must be numbers only), but the system accepted it.")

        assert domain_management.row_locator(RENAMED_CHASSIS_FULL_NAME).count() > 0, (
            f"'{RENAMED_CHASSIS_FULL_NAME}' was expected to still exist unchanged after the rejected "
            f"invalid Chassis ID attempt.")

    results[6] = run_step(6, step_6, logger, report)

    #########################################################################
    # Step 7 – Move the chassis (with its devices) to a different domain.  #
    # Verify the chassis, AND both devices nested inside it, reappear      #
    # intact under the new domain.                                        #
    #########################################################################
    def step_7():
        domain_management.add_domain(CHASSIS_DOMAIN_NAME, parent_domain_name=INVENTORY_ROOT_NAME)
        domain_management.move_to_domain(source_item_name=RENAMED_CHASSIS_BASE_NAME, target_domain_name=CHASSIS_DOMAIN_NAME)

        domain_management.expand_element(CHASSIS_DOMAIN_NAME)
        assert domain_management.row_locator(RENAMED_CHASSIS_FULL_NAME).count() > 0, (
            f"'{RENAMED_CHASSIS_FULL_NAME}' was not found under '{CHASSIS_DOMAIN_NAME}' after the move.")

        domain_management.expand_element(RENAMED_CHASSIS_BASE_NAME)
        for ip in (DEVICE_IP, DEVICE_IP_2):
            assert device_rows_under_chassis(domain_management, RENAMED_CHASSIS_BASE_NAME, ip).count() > 0, (
                f"'{ip}' did not move along with its chassis into '{CHASSIS_DOMAIN_NAME}'.")

    results[7] = run_step(7, step_7, logger, report)

    #########################################################################
    # Step 8 – Remove a chassis that still contains devices (negative       #
    # test). The chassis now holds both DEVICE_IP and DEVICE_IP_2, so the  #
    # system must block the removal and keep the chassis in the tree.      #
    #########################################################################
    def step_8():
        removal_was_blocked = False
        try:
            domain_management.remove_chassis(RENAMED_CHASSIS_BASE_NAME, parent_domain_name=CHASSIS_DOMAIN_NAME)
        except AssertionError:
            removal_was_blocked = True

        assert removal_was_blocked, (
            f"remove_chassis('{RENAMED_CHASSIS_BASE_NAME}') was expected to be blocked because it still "
            f"contains devices, but it succeeded.")

        assert not domain_management.verify_element_deleted(RENAMED_CHASSIS_BASE_NAME, element_type="chassis"), (
            f"'{RENAMED_CHASSIS_BASE_NAME}' was unexpectedly removed even though it still contains devices.")

    results[8] = run_step(8, step_8, logger, report)

    #########################################################################
    # Step 9 – Remove a device from a chassis (leaving it empty), then      #
    # remove the now-empty chassis. This is demonstrated on the disposable  #
    # TEMP chassis rather than the persistent test chassis: a device can    #
    # only ever be REASSIGNED to a different chassis (never fully detached  #
    # to "no chassis" - see Step 4), and this suite's steady state is to    #
    # leave both devices inside the persistent chassis, not strip it bare.  #
    # Park DEVICE_IP_2 in TEMP, confirm it left the persistent chassis and  #
    # TEMP now holds exactly it, then reassign it straight back to the      #
    # persistent chassis's ID - the move that leaves TEMP empty - and       #
    # confirm removing TEMP only succeeds once it holds nothing.            #
    #########################################################################
    def step_9():
        domain_management.change_CHASSIS_ID(
            element_name=DEVICE_IP_2, to_mode="new", new_chassis_id=TEMP_CHASSIS_ID, parent_chassis=RENAMED_CHASSIS_BASE_NAME)

        assert device_rows_under_chassis(domain_management, RENAMED_CHASSIS_BASE_NAME, DEVICE_IP_2).count() == 0, (
            f"'{DEVICE_IP_2}' is still present under '{RENAMED_CHASSIS_BASE_NAME}' after moving it out to the "
            f"temporary '{TEMP_CHASSIS_BASE_NAME}' chassis.")

        assert device_rows_under_chassis(domain_management, TEMP_CHASSIS_BASE_NAME).count() == 1, (
            f"Expected exactly 1 device under '{TEMP_CHASSIS_BASE_NAME}' after parking '{DEVICE_IP_2}' there.")

        # Reassigning it straight back to the persistent chassis's ID is the
        # action that leaves TEMP empty.
        domain_management.change_CHASSIS_ID(
            element_name=DEVICE_IP_2, to_mode="new", new_chassis_id=NEW_CHASSIS_ID, parent_chassis=TEMP_CHASSIS_BASE_NAME)

        assert device_rows_under_chassis(domain_management, TEMP_CHASSIS_BASE_NAME).count() == 0, (
            f"'{TEMP_CHASSIS_BASE_NAME}' was expected to be empty after moving '{DEVICE_IP_2}' back out of it.")

        domain_management.remove_chassis(TEMP_CHASSIS_BASE_NAME, parent_domain_name=CHASSIS_DOMAIN_NAME)
        assert domain_management.verify_element_deleted(TEMP_CHASSIS_BASE_NAME, element_type="chassis"), (
            f"'{TEMP_CHASSIS_BASE_NAME}' is still present in the tree after removing it while empty.")

        domain_management.expand_element(CHASSIS_DOMAIN_NAME)
        domain_management.expand_element(RENAMED_CHASSIS_BASE_NAME)
        assert device_rows_under_chassis(domain_management, RENAMED_CHASSIS_BASE_NAME, DEVICE_IP_2).count() > 0, (
            f"'{DEVICE_IP_2}' was not found back under '{RENAMED_CHASSIS_BASE_NAME}' after being reassigned back.")

    results[9] = run_step(9, step_9, logger, report)

    #########################################################################
    # Step 10 – Final state check. This suite deliberately leaves its test  #
    # chassis in place (renamed, holding both devices, inside the test      #
    # domain) as the steady state for the next run to reuse - a device can  #
    # never be fully detached back to "no chassis" once assigned one, so    #
    # there is nothing to undo here. Just confirm the end state is right.   #
    #########################################################################
    def step_10():
        domain_management.expand_element(CHASSIS_DOMAIN_NAME)
        assert domain_management.row_locator(RENAMED_CHASSIS_FULL_NAME).count() > 0, (
            f"'{RENAMED_CHASSIS_FULL_NAME}' was expected to still exist under '{CHASSIS_DOMAIN_NAME}' "
            f"at the end of the test.")

        domain_management.expand_element(RENAMED_CHASSIS_BASE_NAME)
        for ip in (DEVICE_IP, DEVICE_IP_2):
            assert device_rows_under_chassis(domain_management, RENAMED_CHASSIS_BASE_NAME, ip).count() > 0, (
                f"'{ip}' was expected to still be inside '{RENAMED_CHASSIS_BASE_NAME}' at the end of the test.")

    results[10] = run_step(10, step_10, logger, report)

    ###################
    # Overall Results #
    ###################
    print("\n" + "=" * 60)
    all_passed = all(results.values())
    failed_steps = [str(k) for k, v in results.items() if not v]
    if all_passed:
        print("TEST PASSED ✅")
        logger.info(f"TEST PASSED")
    else:
        print(f"TEST FAILED ❌  Failed steps: {', '.join(failed_steps)}")
        logger.info(f"TEST FAILED")
    print("=" * 60)


# ================================================================
# Main
# ================================================================

if __name__ == "__main__":
    start_time = time.perf_counter()

    with sync_playwright() as p:
        logger = create_logger(LOGGER_ROOT_DIRECTORY, LOG_FILE_NAME, directory_name=LOGGER_DIRECTORY_NAME)
        report = open_report(path=REPORT_PATH)

        browser, context, page = create_page(p, max_size=True)

        login_page = LoginPage(page)
        login_page.goto(BASE_URL)

        if not login_page.login(LW_USERNAME, LW_PASSWORD):
            print("Login Failed ❌")
            context.close()
            browser.close()
            raise SystemExit(1)

        print("Login Success ✅\n")

        left_panel = LeftPanel(page)
        refresh_page(page)

        test_chassis_actions(page, left_panel, logger, report)

        context.close()
        browser.close()
        close_report(report)

    end_time = time.perf_counter()
    print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
    logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")