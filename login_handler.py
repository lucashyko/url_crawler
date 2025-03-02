from playwright.sync_api import Page
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def attempt_login(page: Page, username: str, password: str):
    """Attempt to log in using a list of selectors."""
    selectors = [
        ".btn-danger.login-toggle",  # Your original selectorr
    ]

    # Try each selector to find and click the login button
    clicked = False
    for selector in selectors:
        elements = page.query_selector_all(selector)
        for el in elements:
            if el.is_visible():
                el.scroll_into_view_if_needed()
                el.hover()
                el.click(force=True, timeout=3000)
                clicked = True
                try:
                    logging.info("Filling login form...")
                    page.fill("#edit-name", username)
                    page.fill("#edit-pass", password)
                    page.click("#edit-submit", timeout=5000)
                    logging.info("Login form submitted.")
                except Exception as e:
                    raise Exception(f"Failed to fill or submit login form: {str(e)}")

    if not clicked:
        raise Exception("No clickable login button found.")