"""Screenshot do form de edição da atividade 9280032 (admin) pra ver o que está renderizado."""
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_EMAIL"]
PWD = os.environ["ADMIN_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]
ATIV = os.environ["ATIVIDADE_VIDEO_MARCA_DAGUA_ID"]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        page.goto(BASE + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(EMAIL)
        page.locator("#user_password").fill(PWD)
        page.locator("#user_submit").click()
        page.wait_for_load_state("domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)

        page.goto(f"{BASE}e/{EVENTO}/contents/{ATIV}/edit", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(8000)
        page.screenshot(path="/tmp/admin-edit-now.png", full_page=True)
        print(f"URL: {page.url}")
        print(f"Title: {page.title()}")
        # Procura texto "marca d'água"
        tem_marca = page.locator(":text-matches('marca d.água', 'i')").count()
        print(f"Ocorrências de 'marca d'água' no DOM: {tem_marca}")
        browser.close()


if __name__ == "__main__":
    main()
