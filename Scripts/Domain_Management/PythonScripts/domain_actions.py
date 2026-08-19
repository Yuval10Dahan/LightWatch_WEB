"""
Created by: Ron Shuster
Date: 28/02/2026

Comprehensive Domain Management Test – Domains
=====================================================
Tests the "Domains" actions inside Domain Management:
    - Create new domain
    - Move device to a different domain
    - Remove domain
    - Remove domain with device (negative test)
    - Create a domain with a duplicate name (negative test)
    - Create a domain with a case-only duplicate name (negative test)
    - Remove a domain containing a nested empty domain (negative test)
    - Move a nested domain chain with a device embedded partway through it,
      to another domain, and verify every level and the device relocated
      intact
    - Create a domain with an empty / whitespace-only name (negative test)
    - Cancel a domain removal / a domain creation (negative test)


*** Runtime: approximately 15 minutes ***
"""

from playwright.sync_api import sync_playwright

from Pages.login_page import LoginPage
from Pages.left_panel_page import LeftPanel
from Pages.domain_management import DomainManagement
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
    # print(path)
    globals().update(const_dict)
elif 2 < len(argv) < 3:
    directory = argv[1] + ' ' + argv[2]
    # print(path)
    const_dict = eval(open(directory, 'r').read())

    globals().update(const_dict)
else:
    # ================================================================
    # Values for the Parameter file (from QC)
    # ================================================================

    LW_SERVER_HOST_IP  = "172.16.10.22:8080"
    LW_USERNAME = "administrator"
    LW_PASSWORD = "administrator"

    # Device already discovered and present under the "Default" domain.
    DEVICE_IP = "172.16.20.126"

    DOMAIN_IN_DEFAULT_NAME   = "testDomainInDefault"
    DOMAIN_IN_INVENTORY_NAME = "testDomainInInventory"

    # Used only by the nested-empty-domain removal negative test.
    PARENT_WITH_CHILD_DOMAIN_NAME = "testParentDomain"
    CHILD_DOMAIN_NAME = "testChildDomain"

    # Used only by the cancel-removal negative test.
    CANCEL_TEST_DOMAIN_NAME = "testCancelDomain"

    # Used only by the nested-chain-with-device move test.
    CHAIN_DOMAIN_PREFIX = "testMoveChainDomain_"
    CHAIN_DEPTH = 5
    DEVICE_CHAIN_LAYER = 3  # 1-indexed: DEVICE_IP goes into the 3rd domain in the chain



# ================================================================
# Values that should not be changed
# ================================================================

BASE_URL = f"http://{LW_SERVER_HOST_IP}/"

# Root nodes of the Domain Management tree.
INVENTORY_ROOT_NAME = "Inventory"
DEFAULT_DOMAIN_NAME = "Default"

LOGGER_ROOT_DIRECTORY = 'G:\\Python\\PacketLight Automation\\LightWatch_WEB\\Scripts\\Domain_Management'
LOGGER_DIRECTORY_NAME = "domains_actions"
LOG_FILE_NAME = 'domains_actions.log'
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

def device_row_under_domain(domain_management: DomainManagement, domain_name: str, device_ip: str):
    """
    Locate device_ip scoped strictly to the tree subtree of the given domain.

    device_row_locator() searches the whole "From" tree, so it cannot tell
    which domain a device currently sits under. Scoping the search to a
    single domain's subtree lets a caller assert a device is NOT there,
    which is what proves a move actually relocated it instead of duplicating it.
    """
    domain_row = domain_management.row_locator(domain_name)
    domain_subtree = domain_row.locator("xpath=ancestor::app-inventory-tree-level[1]")

    device_rx = re.compile(rf"(^|\()\s*{re.escape(device_ip)}\s*(\)|$)")
    device_types = ("DEVICE", "ROADM", "TRANSPONDER", "MUXPONDER")

    return domain_subtree.locator(
        ", ".join(f"div.inventory-tree-level-title[type='{t}']" for t in device_types)
    ).filter(has_text=device_rx)

def attempt_add_duplicate_domain(domain_management: DomainManagement, left_panel: LeftPanel, domain_name: str, parent_domain_name: str, timeout: int = 20000) -> bool:
    """
    Try to create a domain whose name already exists under parent_domain_name.
    Returns True if the system visibly rejected it, False if the Add Domain
    modal closed with no rejection shown.

    Reimplemented here instead of calling add_domain()/submit_add_domain():
    that shared flow checks for one specific rejection signal with a single
    one-shot read and no wait, so it can both miss a delayed signal and miss
    an entirely different signal it never checks for. Confirmed by watching
    real runs: this rejection can show up as EITHER of two different things -
    a full client-side route navigation to /error?errorCode=... ("Some
    problems with adding Domain", dismissed via "Go to Back"), OR a "Message"
    modal ("Domain name is not unique...", dismissed via its own "Ok" button)
    while staying on the normal Domain Management URL. Both are checked here.
    """
    domain_management.click_add_domain(parent_domain_name=parent_domain_name, timeout=timeout)

    name_input = domain_management.add_domain_name_input()
    name_input.fill(domain_name)

    domain_management.add_domain_confirm_btn().click()

    modal = domain_management.add_domain_modal()
    msg_modal = domain_management.message_modal()
    page = domain_management.page

    def error_route_shown() -> bool:
        try:
            if "errorCode" in page.url or "adding%20Domain" in page.url:
                return True
            return domain_management.is_add_domain_error_page_visible()
        except Exception:
            return False

    def message_modal_shown() -> bool:
        try:
            return msg_modal.count() > 0 and msg_modal.is_visible()
        except Exception:
            return False

    def blocked_shown() -> bool:
        return error_route_shown() or message_modal_shown()

    def modal_gone() -> bool:
        try:
            return modal.count() == 0 or not modal.is_visible()
        except Exception:
            return False

    domain_management.wait_until(lambda: blocked_shown() or modal_gone(),
                                  timeout_ms=timeout, interval_ms=200,
                                  desc="Add Domain modal to resolve (success close, Message modal, or error route)")

    # Grace period: either rejection signal can appear a beat after the Add
    # Domain modal itself has already closed - give it a generous window
    # before concluding "not blocked".
    try:
        domain_management.wait_until(blocked_shown, timeout_ms=15000, interval_ms=300,
                                      desc="delayed rejection signal (Message modal or error route) after modal close")
    except AssertionError:
        pass

    was_blocked = blocked_shown()

    if was_blocked:
        recovered = False

        if message_modal_shown():
            # "Message" modal case - just click its own "Ok" button.
            try:
                domain_management.message_ok_btn().click()
                domain_management.wait_until(lambda: not message_modal_shown(), timeout_ms=timeout, interval_ms=200,
                                              desc="Message modal to close after clicking Ok")
                recovered = True
            except Exception:
                recovered = False
        else:
            # Full-page /error route case - click "Go to Back" ourselves
            # rather than calling the shared handle_add_domain_error_page():
            # it swallows its own exception and just prints a misleading
            # "failed" line internally, even on runs where this step is fine.
            try:
                domain_management.add_domain_error_go_back_btn().click(force=True)
                domain_management.wait_until(lambda: not error_route_shown(), timeout_ms=timeout, interval_ms=200,
                                              desc="error route to clear after clicking 'Go to Back'")
                recovered = True
            except Exception:
                recovered = False

        if not recovered:
            # Neither dismissal path finished in time - escape with a fresh
            # navigation (reloading /error would just re-show it) and
            # re-enter Domain Management from scratch.
            page.goto(BASE_URL)
            left_panel.click_domain_management()

    return was_blocked

def domain_children_locator(domain_management: DomainManagement, parent_domain_name: str):
    """
    Return a locator for all DOMAIN-type rows nested in the tree subtree of
    parent_domain_name. Used as a before/after count to detect whether a
    supposedly-blocked "Add domain" attempt silently created something anyway
    - relevant when the attempted name is blank/whitespace and can't be
    searched for by name text directly.
    """
    parent_row = domain_management.row_locator(parent_domain_name)
    parent_subtree = parent_row.locator("xpath=ancestor::app-inventory-tree-level[1]")

    return parent_subtree.locator("div.inventory-tree-level-title[type='DOMAIN']")

def attempt_add_domain_with_invalid_name(domain_management: DomainManagement, name: str, parent_domain_name: str, timeout: int = 5000) -> bool:
    """
    Try to create a domain using a name expected to fail validation (e.g.
    blank or whitespace-only). Returns True if the system correctly refused
    it - either by keeping "Add" disabled, or by the modal staying open
    after a click. Returns False only if the modal actually closed as if a
    domain were created.
    """
    domain_management.click_add_domain(parent_domain_name=parent_domain_name, timeout=timeout)

    name_input = domain_management.add_domain_name_input()
    name_input.fill(name)

    add_btn = domain_management.add_domain_confirm_btn()

    if not add_btn.is_enabled():
        domain_management.add_domain_close_btn().click()
        return True

    add_btn.click()

    modal = domain_management.add_domain_modal()

    def modal_closed() -> bool:
        try:
            return modal.count() == 0 or not modal.is_visible()
        except Exception:
            return False

    try:
        domain_management.wait_until(modal_closed, timeout_ms=timeout, interval_ms=200,
                                      desc="Add Domain modal to close after submitting an invalid name")
    except AssertionError:
        # Modal never closed - inline validation kept it open, which counts as blocked.
        domain_management.add_domain_close_btn().click()
        return True

    return False

# ================================================================
# Main test
# ================================================================

def test_domains_actions(page, left_panel: LeftPanel, logger, report):
    domain_management = DomainManagement(page)

    results = {}

    #########################################################################
    # Step 1 – Create two new domains:                                      #
    # one nested under the "Default" domain, one directly under the         #
    # "Inventory" root. Verify both were created successfully.              #
    #########################################################################
    def step_1():
        left_panel.click_domain_management()

        for test_domain in (DOMAIN_IN_DEFAULT_NAME, DOMAIN_IN_INVENTORY_NAME):
            if domain_management.verify_element_deleted(test_domain, element_type="domain", refresh=False):
                continue

            try:
                domain_management.expand_element(test_domain)
                if domain_management.device_row_locator(DEVICE_IP).count() > 0:
                    domain_management.move_to_domain(source_item_name=DEVICE_IP, target_domain_name=DEFAULT_DOMAIN_NAME)
            except Exception:
                pass

            try:
                remove_domain_with_retry(domain_management, page, test_domain)
            except Exception:
                pass

        domain_management.add_domain(DOMAIN_IN_DEFAULT_NAME, parent_domain_name=DEFAULT_DOMAIN_NAME)
        domain_management.add_domain(DOMAIN_IN_INVENTORY_NAME, parent_domain_name=INVENTORY_ROOT_NAME)

        assert domain_management.row_locator(DOMAIN_IN_DEFAULT_NAME).count() > 0, (
            f"'{DOMAIN_IN_DEFAULT_NAME}' was not created under '{DEFAULT_DOMAIN_NAME}'.")
        assert domain_management.row_locator(DOMAIN_IN_INVENTORY_NAME).count() > 0, (
            f"'{DOMAIN_IN_INVENTORY_NAME}' was not created under '{INVENTORY_ROOT_NAME}'.")

    results[1] = run_step(1, step_1, logger, report)

    #########################################################################
    # Step 2 – Move DEVICE_IP from its current domain ("Default") into     #
    # DOMAIN_IN_INVENTORY. Verify the device is visible under its new      #
    # domain once expanded, AND that it is no longer under "Default" –     #
    # proving the device was actually moved, not duplicated.               #
    #########################################################################
    def step_2():
        domain_management.move_to_domain(source_item_name=DEVICE_IP, target_domain_name=DOMAIN_IN_INVENTORY_NAME)

        domain_management.expand_element(DOMAIN_IN_INVENTORY_NAME)
        assert domain_management.device_row_locator(DEVICE_IP).count() > 0, (
            f"'{DEVICE_IP}' was not found under '{DOMAIN_IN_INVENTORY_NAME}' after the move.")

        assert device_row_under_domain(domain_management, DEFAULT_DOMAIN_NAME, DEVICE_IP).count() == 0, (
            f"'{DEVICE_IP}' is still present under '{DEFAULT_DOMAIN_NAME}' after being moved to '{DOMAIN_IN_INVENTORY_NAME}'.")

    results[2] = run_step(2, step_2, logger, report)

    #########################################################################
    # Step 3 – Remove domain (positive test).                              #
    # DOMAIN_IN_DEFAULT_NAME is still empty, so removing it must succeed.  #
    #########################################################################
    def step_3():
        remove_domain_with_retry(domain_management, page, DOMAIN_IN_DEFAULT_NAME)

        assert domain_management.verify_element_deleted(DOMAIN_IN_DEFAULT_NAME, element_type="domain"), (
            f"'{DOMAIN_IN_DEFAULT_NAME}' is still present in the tree after removal.")

    results[3] = run_step(3, step_3, logger, report)

    #########################################################################
    # Step 4 – Remove domain with device (negative test).                  #
    # DOMAIN_IN_INVENTORY_NAME now holds DEVICE_IP, so the system must     #
    # block the removal and keep the domain in the tree.                   #
    #########################################################################
    def step_4():
        removal_was_blocked = False
        try:
            domain_management.remove_domain(DOMAIN_IN_INVENTORY_NAME)
        except AssertionError:
            removal_was_blocked = True

        assert removal_was_blocked, (
            f"remove_domain('{DOMAIN_IN_INVENTORY_NAME}') was expected to be blocked "
            f"because it still contains a device, but it succeeded.")

        assert not domain_management.verify_element_deleted(DOMAIN_IN_INVENTORY_NAME, element_type="domain"), (
            f"'{DOMAIN_IN_INVENTORY_NAME}' was unexpectedly removed even though it contains a device.")

    results[4] = run_step(4, step_4, logger, report)

    #########################################################################
    # Step 5 – Duplicate domain name (negative test).                      #
    # DOMAIN_IN_INVENTORY_NAME already exists (created in Step 1, still    #
    # with that exact same name under the same parent. The system is      #
    # expected to reject it, leaving exactly one domain with that name.    #
    # No setup/cleanup of its own is needed here: this domain's lifecycle  #
    # is already fully owned by Step 1 (create) and Step 11 (remove, at   #
    # the end of the script).                                             #
    #########################################################################
    def step_5():
        duplicate_was_blocked = attempt_add_duplicate_domain(
            domain_management, left_panel, DOMAIN_IN_INVENTORY_NAME, parent_domain_name=INVENTORY_ROOT_NAME)

        assert duplicate_was_blocked, (
            f"Creating a second domain named '{DOMAIN_IN_INVENTORY_NAME}' under '{INVENTORY_ROOT_NAME}' "
            f"was expected to be rejected, but the Add Domain modal closed with no error shown.")

        refresh_page(page)
        rx = domain_management.nav_text_regex(DOMAIN_IN_INVENTORY_NAME)
        duplicate_rows = domain_management.from_tree().locator("div.inventory-tree-level-title", has_text=rx)
        assert duplicate_rows.count() == 1, (
            f"Expected exactly one '{DOMAIN_IN_INVENTORY_NAME}' domain in the tree after the blocked "
            f"duplicate attempt, found {duplicate_rows.count()}.")

    results[5] = run_step(5, step_5, logger, report)

    #########################################################################
    # Step 6 – Case-sensitive duplicate domain name (negative test).       #
    # Attempt to create a domain whose name differs from                   #
    # DOMAIN_IN_INVENTORY_NAME only by letter case. If LightWatch treats    #
    # domain names case-insensitively, this must be rejected the same way   #
    # an exact duplicate is (Step 5).                                      #
    #########################################################################
    def step_6():
        case_variant_name = DOMAIN_IN_INVENTORY_NAME.upper()

        try:
            duplicate_was_blocked = attempt_add_duplicate_domain(
                domain_management, left_panel, case_variant_name, parent_domain_name=INVENTORY_ROOT_NAME)

            assert duplicate_was_blocked, (
                f"Creating a domain named '{case_variant_name}' (a case-only variant of the "
                f"existing '{DOMAIN_IN_INVENTORY_NAME}') was expected to be rejected as a "
                f"duplicate, but the Add Domain modal closed with no error shown.")

            refresh_page(page)
            case_insensitive_rx = re.compile(re.escape(DOMAIN_IN_INVENTORY_NAME), re.IGNORECASE)
            matches = domain_management.from_tree().locator("div.inventory-tree-level-title", has_text=case_insensitive_rx)
            assert matches.count() == 1, (
                f"Expected exactly one domain matching '{DOMAIN_IN_INVENTORY_NAME}' (case-insensitive) "
                f"after the blocked case-variant duplicate attempt, found {matches.count()}.")
        finally:
            if not domain_management.verify_element_deleted(case_variant_name, element_type="domain", refresh=True):
                remove_domain_with_retry(domain_management, page, case_variant_name)

    results[6] = run_step(6, step_6, logger, report)

    #########################################################################
    # Step 7 – Remove a domain that contains a nested empty domain.        #
    # Mirrors Step 4 (device inside a domain), but this time the domain's  #
    # only content is an empty child domain instead of a device. Verifies  #
    # the system blocks removal consistently in both cases.                #
    #########################################################################
    def step_7():
        try:
            domain_management.add_domain(PARENT_WITH_CHILD_DOMAIN_NAME, parent_domain_name=INVENTORY_ROOT_NAME)
            domain_management.add_domain(CHILD_DOMAIN_NAME, parent_domain_name=PARENT_WITH_CHILD_DOMAIN_NAME)

            assert domain_management.row_locator(CHILD_DOMAIN_NAME).count() > 0, (
                f"'{CHILD_DOMAIN_NAME}' was not created under '{PARENT_WITH_CHILD_DOMAIN_NAME}'.")

            removal_was_blocked = False
            try:
                domain_management.remove_domain(PARENT_WITH_CHILD_DOMAIN_NAME)
            except AssertionError:
                removal_was_blocked = True

            assert removal_was_blocked, (
                f"remove_domain('{PARENT_WITH_CHILD_DOMAIN_NAME}') was expected to be blocked because it "
                f"still contains a nested domain ('{CHILD_DOMAIN_NAME}'), but it succeeded.")

            assert not domain_management.verify_element_deleted(PARENT_WITH_CHILD_DOMAIN_NAME, element_type="domain"), (
                f"'{PARENT_WITH_CHILD_DOMAIN_NAME}' was unexpectedly removed even though it still contains a nested domain.")
        finally:
            remove_domain_with_retry(domain_management, page, CHILD_DOMAIN_NAME)
            remove_domain_with_retry(domain_management, page, PARENT_WITH_CHILD_DOMAIN_NAME)

    results[7] = run_step(7, step_7, logger, report)

    #########################################################################
    # Step 8 – Move a nested domain chain with a device embedded partway    #
    # through it, to another domain (positive test).                       #
    # Build a CHAIN_DEPTH-level chain of domains, move DEVICE_IP into the   #
    # DEVICE_CHAIN_LAYER-th level, then move the TOP of the chain into      #
    # DOMAIN_IN_INVENTORY_NAME. Verify every level of the chain relocated   #
    # intact, in the same nested order, AND that the device moved along     #
    # with it rather than being lost or left behind.                       #
    #########################################################################
    def step_8():
        chain_names = [f"{CHAIN_DOMAIN_PREFIX}{i}" for i in range(1, CHAIN_DEPTH + 1)]
        device_layer_name = chain_names[DEVICE_CHAIN_LAYER - 1]

        try:
            # Build the chain, each domain nested inside the previous one.
            parent = INVENTORY_ROOT_NAME
            for name in chain_names:
                domain_management.add_domain(name, parent_domain_name=parent)
                parent = name

            # Move the device into the middle of the chain.
            domain_management.move_to_domain(source_item_name=DEVICE_IP, target_domain_name=device_layer_name)
            domain_management.expand_element(device_layer_name)
            assert domain_management.device_row_locator(DEVICE_IP).count() > 0, (
                f"'{DEVICE_IP}' was not found under '{device_layer_name}' before the chain move.")

            # Move the WHOLE chain (from its top) into DOMAIN_IN_INVENTORY_NAME.
            domain_management.move_to_domain(source_item_name=chain_names[0], target_domain_name=DOMAIN_IN_INVENTORY_NAME)

            domain_management.expand_element(DOMAIN_IN_INVENTORY_NAME)
            for depth_index, name in enumerate(chain_names, start=1):
                assert domain_management.row_locator(name).count() > 0, (
                    f"'{name}' (chain level {depth_index}) was not found after moving the "
                    f"chain into '{DOMAIN_IN_INVENTORY_NAME}' - the chain did not relocate intact.")

                if name == device_layer_name:
                    assert domain_management.device_row_locator(DEVICE_IP).count() > 0, (
                        f"'{DEVICE_IP}' did not move along with the chain - it was expected "
                        f"under '{device_layer_name}' after the move.")

                domain_management.expand_element(name)
        finally:
            domain_management.move_to_domain(source_item_name=DEVICE_IP, target_domain_name=DOMAIN_IN_INVENTORY_NAME)
            for name in reversed(chain_names):
                remove_domain_with_retry(domain_management, page, name)

    results[8] = run_step(8, step_8, logger, report)

    #########################################################################
    # Step 9 – Empty / whitespace-only domain name (negative test).        #
    # Attempt to create a domain with a blank name, then with a            #
    # whitespace-only name. Neither should actually add a new domain.      #
    #########################################################################
    INVALID_DOMAIN_NAMES = ["", "   "]

    def step_9():
        for invalid_name in INVALID_DOMAIN_NAMES:
            children_before = domain_children_locator(domain_management, INVENTORY_ROOT_NAME).count()

            was_blocked = attempt_add_domain_with_invalid_name(
                domain_management, invalid_name, parent_domain_name=INVENTORY_ROOT_NAME)

            refresh_page(page)
            children_after = domain_children_locator(domain_management, INVENTORY_ROOT_NAME).count()

            assert was_blocked and children_after == children_before, (
                f"Creating a domain with name={invalid_name!r} was expected to be rejected "
                f"(no new domain added under '{INVENTORY_ROOT_NAME}'), but child count went "
                f"from {children_before} to {children_after} (blocked={was_blocked}).")

    results[9] = run_step(9, step_9, logger, report)

    #########################################################################
    # Step 10 – Cancel paths (negative tests).                              #
    # (a) Click "Remove" on a domain, then click "No" on the confirmation   #
    #     warning - the domain must remain untouched.                      #
    # (b) Open "Add domain", fill in a name, then close via "X" instead of  #
    #     submitting - nothing should be created.                          #
    #########################################################################
    def step_10():
        # (a) Cancel a domain removal via "No".
        try:
            domain_management.add_domain(CANCEL_TEST_DOMAIN_NAME, parent_domain_name=INVENTORY_ROOT_NAME)

            domain_management.click_remove_domain_btn(CANCEL_TEST_DOMAIN_NAME)
            domain_management.wait_until(
                lambda: domain_management.warning_remove_modal().count() > 0 and domain_management.warning_remove_modal().is_visible(),
                timeout_ms=8000, interval_ms=200, desc="Warning modal to appear after clicking Remove")
            domain_management.warning_no_btn().click()

            assert not domain_management.verify_element_deleted(CANCEL_TEST_DOMAIN_NAME, element_type="domain", refresh=True), (
                f"'{CANCEL_TEST_DOMAIN_NAME}' was removed even though 'No' was clicked on the confirmation warning.")
        finally:
            remove_domain_with_retry(domain_management, page, CANCEL_TEST_DOMAIN_NAME)

        # (b) Cancel an "Add domain" via the "X" close button.
        cancelled_add_name = "testCancelledAddDomain"
        children_before = domain_children_locator(domain_management, INVENTORY_ROOT_NAME).count()

        domain_management.click_add_domain(parent_domain_name=INVENTORY_ROOT_NAME)
        domain_management.add_domain_name_input().fill(cancelled_add_name)
        domain_management.add_domain_close_btn().click()

        domain_management.wait_until(
            lambda: domain_management.add_domain_modal().count() == 0 or not domain_management.add_domain_modal().is_visible(),
            timeout_ms=8000, interval_ms=200, desc="Add Domain modal to close after clicking 'X'")

        refresh_page(page)
        children_after = domain_children_locator(domain_management, INVENTORY_ROOT_NAME).count()

        assert children_after == children_before, (
            f"Closing the Add Domain modal via 'X' was expected to discard the input, but the "
            f"domain count under '{INVENTORY_ROOT_NAME}' changed from {children_before} to {children_after}.")
        assert domain_management.verify_element_deleted(cancelled_add_name, element_type="domain", refresh=False), (
            f"'{cancelled_add_name}' was found in the tree even though the Add Domain modal was cancelled via 'X'.")

    results[10] = run_step(10, step_10, logger, report)

    #########################################################################
    # Step 11 – Cleanup (must run last: Step 4 is a negative test that     #
    # relies on DEVICE_IP still sitting inside DOMAIN_IN_INVENTORY_NAME,    #
    # and several steps above reuse DOMAIN_IN_INVENTORY_NAME as their       #
    # target/baseline domain, so the environment can only be restored once  #
    # every test that depends on that state has already run).              #
    # Move DEVICE_IP back to "Default" (rather than deleting it – a live   #
    # device gets auto re-discovered by the server and would otherwise     #
    # reappear inside DOMAIN_IN_INVENTORY_NAME right as we try to remove   #
    # it), remove the now-empty domain, and confirm DEVICE_IP really ended #
    # up back under "Default".                                            #
    #########################################################################
    def step_11():
        domain_management.move_to_domain(source_item_name=DEVICE_IP, target_domain_name=DEFAULT_DOMAIN_NAME)
        remove_domain_with_retry(domain_management, page, DOMAIN_IN_INVENTORY_NAME)

        assert domain_management.verify_element_deleted(DOMAIN_IN_INVENTORY_NAME, element_type="domain"), (
            f"'{DOMAIN_IN_INVENTORY_NAME}' is still present in the tree after cleanup.")

        assert device_row_under_domain(domain_management, DEFAULT_DOMAIN_NAME, DEVICE_IP).count() > 0, (
            f"'{DEVICE_IP}' was expected to be back under '{DEFAULT_DOMAIN_NAME}' after cleanup, but it isn't.")

    results[11] = run_step(11, step_11, logger, report)

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

        test_domains_actions(page, left_panel, logger, report)

        context.close()
        browser.close()
        close_report(report)

    end_time = time.perf_counter()
    print(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")
    logger.info(f"\nTotal test runtime: {end_time - start_time:.2f} seconds")