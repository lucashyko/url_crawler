from dotenv import load_dotenv
import os
import json
import csv
import logging
from urllib.parse import urlparse
from pathlib import Path
from playwright.sync_api import sync_playwright
from login_handler import attempt_login

# Load environment variables
load_dotenv()

# Constants
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
URLS_FILE = "urls.json"
RESULTS_FILE = "playwright_results.csv"
SCREENSHOTS_DIR = "screenshots"
TIMEOUT = 4000  # Global timeout in milliseconds

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def validate_environment_variables():
    """Validate that required environment variables are set."""
    if not USERNAME or not PASSWORD:
        raise ValueError("Username and password must be set in environment variables.")

def load_urls(file_path: str) -> list:
    """Load URLs from a JSON file."""
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data.get("urls", [])
    except Exception as e:
        logging.error(f"Failed to load URLs from {file_path}: {str(e)}")
        raise

def sanitize_filename(url: str) -> str:
    """Sanitize URL to create a valid filename."""
    parsed_url = urlparse(url)
    return f"{parsed_url.netloc}{parsed_url.path}".replace("/", "_").replace(":", "_")

def check_access_denied(page) -> bool:
    """Check if the page contains 'Você não está autorizado a acessar esta página.' in the body."""
    try:
        body_text = page.locator("body").text_content(timeout=TIMEOUT)
        return "Você não está autorizado a acessar esta página." in body_text
    except Exception:
        return False

def save_results(results: list, file_path: str):
    """Save results to a CSV file."""
    try:
        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["URL", "Status"])
            writer.writeheader()
            writer.writerows(results)
        logging.info(f"Results saved to {file_path}")
    except Exception as e:
        logging.error(f"Failed to save results to {file_path}: {str(e)}")

def test_urls():
    """Test all URLs and log their status."""
    # Validate environment variables
    validate_environment_variables()

    # Load URLs
    urls = load_urls(URLS_FILE)
    if not urls:
        logging.warning("No URLs found in the file.")
        return

    # Prepare results list
    results = []

    # Create screenshots directory
    Path(SCREENSHOTS_DIR).mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Track login status
        logged_in = False

        for url in urls:
            try:
                logging.info(f"Accessing {url}...")
                page.goto(url, timeout=TIMEOUT)
                page.wait_for_load_state("networkidle")

                # Check if the page loaded correctly
                if not page.is_visible("body"):
                    raise Exception("Page did not load correctly.")

                # Attempt login only if not already logged in
                if not logged_in:
                    try:
                        logging.info("Attempting to log in...")
                        attempt_login(page, USERNAME, PASSWORD)
                        logged_in = True  # Set flag to True after successful login
                    except Exception as e:
                        logging.warning(f"Login attempt failed: {str(e)}")

                # Check for "Acesso Negado"
                if check_access_denied(page):
                    status = "Acesso Negado"
                else:
                    status = "Positivo"

            except Exception as e:
                logging.error(f"Error accessing {url}: {str(e)}")
                status = f"Failed - {str(e)}"

            # Log results
            results.append({"URL": url, "Status": status})
            logging.info(f"{url} - {status}")

            # Save screenshot
            screenshot_path = f"{SCREENSHOTS_DIR}/{sanitize_filename(url)}.png"
            page.screenshot(path=screenshot_path)

        # Close browser
        context.close()
        browser.close()

    # Save results to CSV
    save_results(results, RESULTS_FILE)

if __name__ == "__main__":
    test_urls()