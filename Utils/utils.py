'''
Created by: Yuval Dahan
Date: 26/01/2026
'''


from playwright.sync_api import Page, TimeoutError


# ✅
def refresh_page(page: Page, timeout: int = 30_000) -> bool:
    """
    Refresh the current page regardless of UI.
    
    Returns:
        True  -> Page reloaded successfully
        False -> Reload failed or timed out
    """
    try:
        page.reload(wait_until="domcontentloaded", timeout=timeout)
        return True
    except TimeoutError:
        return False