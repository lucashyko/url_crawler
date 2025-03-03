from dotenv import load_dotenv
import os
import json
import csv
import logging
import time
import asyncio
from urllib.parse import urlparse
from pathlib import Path
from playwright.async_api import async_playwright
from modules.login_handler import attempt_login

# Load environment variables
load_dotenv()

# Constants
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
URLS_FILE = "urls.json"
RESULTS_FILE = "playwright_results.csv"
SCREENSHOTS_DIR = "screenshots"
TIMEOUT = 12000  # Timeout in milliseconds
CONCURRENT_INSTANCES = 20  # Number of instances to run concurrently

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%H:%M"  # Show only hour and minute
)

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
        logging.error(f"[ERROR] Failed to load URLs from {file_path}: {str(e)}")
        raise

def sanitize_filename(url: str) -> str:
    """Sanitize URL to create a valid filename."""
    parsed_url = urlparse(url)
    return f"{parsed_url.netloc}{parsed_url.path}".replace("/", "_").replace(":", "_")

async def check_page_state(page) -> str:
    """Check the state of the page and return the appropriate status."""
    try:
        body_text = await page.locator("body").text_content(timeout=TIMEOUT)

        # Check for specific states
        if "Você não está autorizado a acessar esta página." in body_text:
            return "Acesso Negado"
        elif "página não encontrada" in body_text:
            return "página não encontrada"
        elif "not found" in body_text.lower():
            return "not found"
        elif await page.evaluate("""() => {
                const status = document.querySelector('h1');
                return status && status.textContent.includes('404');
            }"""):
            return "404"
        else:
            return "Positivo"
    except Exception:
        return "Failed - Unknown Error"

def save_results(results: list, file_path: str):
    """Save results to a CSV file."""
    try:
        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["URL", "Status"])
            writer.writeheader()
            writer.writerows(results)
        logging.info(f"[SUCCESS] Results saved to {file_path}")
    except Exception as e:
        logging.error(f"[ERROR] Failed to save results to {file_path}: {str(e)}")
        raise

async def worker(browser, login_url: str, username: str, password: str, urls: list, results: list, instance_id: int):
    """Worker function to handle a single browser instance."""
    context = await browser.new_context()
    page = await context.new_page()

    # Log in
    try:
        logging.info(f"[INSTANCE {instance_id}] Logging in...")
        await page.goto(login_url, timeout=TIMEOUT)
        await page.wait_for_selector("body", state="visible", timeout=TIMEOUT)
        await attempt_login(page, username, password)
        logging.info(f"[INSTANCE {instance_id}] Login successful.")
    except Exception as e:
        logging.error(f"[INSTANCE {instance_id}] Login failed: {str(e)}")
        await context.close()
        return

    # Process URLs
    for url in urls:
        try:
            logging.info(f"[INSTANCE {instance_id}] Accessing {url}...")
            await page.goto(url, timeout=TIMEOUT)
            await page.wait_for_selector("body", state="visible", timeout=TIMEOUT)

            # Check the page state
            status = await check_page_state(page)
            logging.info(f"[INSTANCE {instance_id}] Page state: {status}")

            # Take a screenshot
            screenshot_path = f"{SCREENSHOTS_DIR}/{sanitize_filename(url)}.png"
            await page.screenshot(path=screenshot_path)
            logging.info(f"[INSTANCE {instance_id}] Screenshot saved to {screenshot_path}")

        except Exception as e:
            logging.error(f"[INSTANCE {instance_id}] Error accessing {url}: {str(e)}")
            status = f"Failed - {str(e)}"
            # Take a screenshot on error
            screenshot_path = f"{SCREENSHOTS_DIR}/error_{sanitize_filename(url)}.png"
            await page.screenshot(path=screenshot_path)
            logging.info(f"[INSTANCE {instance_id}] Error screenshot saved to {screenshot_path}")

        # Log results
        results.append({"URL": url, "Status": status})
        logging.info(f"[INSTANCE {instance_id}] {url} - {status}")

        # Add a delay between requests
        await asyncio.sleep(3)  # 3-second delay

    await context.close()

def split_urls(urls: list, num_instances: int) -> list:
    """Split the URL list into equal parts for each instance."""
    chunk_size = len(urls) // num_instances
    return [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]

async def test_urls():
    """Test all URLs and log their status."""
    logging.info("[START] Starting URL testing process.")

    # Validate environment variables
    validate_environment_variables()

    # Load URLs
    urls = load_urls(URLS_FILE)
    if not urls:
        logging.warning("[WARNING] No URLs found in the file.")
        return

    # Prepare results list
    results = []

    # Create screenshots directory
    Path(SCREENSHOTS_DIR).mkdir(exist_ok=True)
    logging.info(f"[INFO] Screenshots will be saved to {SCREENSHOTS_DIR}.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Run in headless mode
        logging.info("[INFO] Browser launched.")

        # Split URLs into chunks for each instance
        url_chunks = split_urls(urls, CONCURRENT_INSTANCES)
        logging.info(f"[INFO] URLs split into {CONCURRENT_INSTANCES} chunks.")

        # Create and run worker tasks
        tasks = []
        for i in range(CONCURRENT_INSTANCES):
            task = worker(browser, "https://takedapro.com.br/", USERNAME, PASSWORD, url_chunks[i], results, i + 1)
            tasks.append(task)
        logging.info("[INFO] Worker tasks created.")

        # Run all tasks concurrently
        await asyncio.gather(*tasks)
        logging.info("[INFO] All worker tasks completed.")

        await browser.close()
        logging.info("[INFO] Browser closed.")

    # Save results to CSV
    save_results(results, RESULTS_FILE)
    logging.info("[COMPLETE] URL testing process finished.")

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(test_urls())
    end_time = time.time()
    logging.info(f"[INFO] Script execution time: {end_time - start_time:.2f} seconds")