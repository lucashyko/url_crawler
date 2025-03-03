from playwright.async_api import Page
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def attempt_login(page: Page, username: str, password: str):
    """Attempt to log in using a list of selectors."""
    selectors = [
        ".btn-danger.login-toggle",  # Your original selector
        "text=Login",  # Fallback selector (adjust based on the button text)
        "text=Sign in",  # Another fallback selector
        "text=Log in",  # Another fallback selector
        "text=Acessar",  # Another fallback selector
    ]

    # Try each selector to find and click the login button
    clicked = False
    for selector in selectors:
        try:
            logging.info(f"Waiting for selector: {selector}")
            elements = await page.query_selector_all(selector)
            for el in elements:
                if await el.is_visible():
                    await el.scroll_into_view_if_needed()
                    await el.hover()
                    await el.click(force=True, timeout=3000)
                    clicked = True
                    try:
                        logging.info("Filling login form...")
                        await page.fill("#edit-name", username)
                        await page.fill("#edit-pass", password)
                        await page.click("#edit-submit", timeout=5000)
                        logging.info("Login form submitted.")
                    except Exception as e:
                        raise Exception(f"Failed to fill or submit login form: {str(e)}")

                    # Verify login success
                    try:
                        logging.info("Verifying login...")
                        await page.wait_for_selector(".logout-button", timeout=5000)  # Adjust selector as needed
                        logging.info("Login successful.")
                    except Exception:
                        raise Exception("Login verification failed.")
                    break
            if clicked:
                break
        except Exception as e:
            logging.warning(f"Failed to click with selector {selector}: {str(e)}")

    if not clicked:
        raise Exception("No clickable login button found.")