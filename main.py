from dotenv import load_dotenv
import os
import json
import csv
from playwright.sync_api import sync_playwright
from login_handler import attempt_login

load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Carregar URLs do arquivo JSON
with open("urls.json", "r") as file:
    data = json.load(file)

RESULTS_FILE = "playwright_results.csv"

def test_urls():
    urls = data["urls"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        results = []

        for url in urls:
            try:
                print(f"🟡 Acessando {url}...")
                page.goto(url, timeout=15000)  
                page.wait_for_load_state("networkidle")

                # Chama a função de login
                attempt_login(page, USERNAME, PASSWORD)

                status = "Success"
            except Exception as e:
                print(f"❌ Erro em {url}: {str(e)}")
                status = "Failed"

            results.append([url, status])
            print(f"{url} - {status}")

            # Salvar captura de tela
            screenshot_path = f"screenshots/{url.replace('https://', '').replace('/', '_')}.png"
            os.makedirs("screenshots", exist_ok=True)
            page.screenshot(path=screenshot_path)

        # Salvar resultados em CSV
        with open(RESULTS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["URL", "Status"])
            writer.writerows(results)

        browser.close()

if __name__ == "__main__":
    test_urls()
    print(f"📄 Resultados salvos em {RESULTS_FILE}")
