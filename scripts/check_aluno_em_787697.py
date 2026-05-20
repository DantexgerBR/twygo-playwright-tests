"""Confere se dante.tavares (aluno) tem acesso ao curso 787697."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pages.login_page import LoginPage  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
BASE_URL = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ALUNO_EMAIL"]
SENHA = os.environ["ALUNO_PASSWORD"]
OUT = Path("test-results/check_aluno_787697")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        try:
            LoginPage(page).login(BASE_URL, EMAIL, SENHA)
        except Exception:
            page.wait_for_timeout(3000)
        page.screenshot(path=str(OUT / "01-pos-login.png"), full_page=True)

        for ev_id in ["787697", "787696"]:
            # tentar /my-contents?event_id={id}
            page.goto(f"{BASE_URL}my-contents?event_id={ev_id}", wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(7000)
            page.screenshot(path=str(OUT / f"02-my-contents-{ev_id}.png"), full_page=True)
            body = page.evaluate("() => document.body.innerText.slice(0, 800)")
            print(f"\n[my-contents?event_id={ev_id}]:")
            print(body)
            # tentar /e/{id}/learn
            page.goto(f"{BASE_URL}e/{ev_id}/learn?learn_origin=my-contents", wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(7000)
            page.screenshot(path=str(OUT / f"03-learn-{ev_id}.png"), full_page=True)
            body2 = page.evaluate("() => document.body.innerText.slice(0, 800)")
            print(f"\n[/e/{ev_id}/learn]:")
            print(body2)

        browser.close()


if __name__ == "__main__":
    main()
