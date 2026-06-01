"""Descobre a rota de edição da atividade no admin."""
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"]
EMAIL = os.environ["ADMIN_EMAIL"]
PWD = os.environ["ADMIN_PASSWORD"]
ATIV_ID = os.environ["ATIVIDADE_VIDEO_MARCA_DAGUA_ID"]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Login
        page.goto(BASE + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(EMAIL)
        page.locator("#user_password").fill(PWD)
        page.locator("#user_submit").click()
        page.wait_for_load_state("networkidle", timeout=20000)
        print("Pós-login:", page.url, "—", page.title())

        page.screenshot(path="/tmp/twygo-admin-home.png", full_page=True)

        # Tenta encontrar o admin dashboard
        for cand in ["admin", "admin/dashboard", "admin/contents", "admin/activities", "admin/cursos"]:
            try:
                page.goto(BASE + cand, wait_until="domcontentloaded", timeout=15000)
                print(f"\n[{cand}] → final={page.url} title={page.title()}")
                if "doesn't exist" not in page.content() and "404" not in page.title():
                    # lista links que contenham o ID da atividade
                    hrefs = page.eval_on_selector_all(
                        "a", "els => els.map(e => e.getAttribute('href'))"
                    )
                    relevant = [h for h in hrefs if h and ATIV_ID in h][:10]
                    if relevant:
                        print(f"   links com ID {ATIV_ID}: {relevant}")
            except Exception as e:
                print(f"[{cand}] ERROR {e}")

        # Tenta variações de rota direta com o ID
        for rota in [
            f"admin/contents/{ATIV_ID}/edit",
            f"admin/activities/{ATIV_ID}/edit",
            f"admin/atividades/{ATIV_ID}",
            f"contents/{ATIV_ID}/edit",
            f"contents/{ATIV_ID}",
            f"admin/contents/{ATIV_ID}",
        ]:
            try:
                page.goto(BASE + rota, wait_until="domcontentloaded", timeout=15000)
                ok = "doesn't exist" not in page.content()
                print(f"\n[{rota}] → ok={ok} final={page.url} title={page.title()}")
            except Exception as e:
                print(f"[{rota}] ERROR {e}")

        browser.close()


if __name__ == "__main__":
    main()
