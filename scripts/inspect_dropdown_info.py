"""Abre o select Informações e lista as opções disponíveis."""
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
        page.wait_for_timeout(7000)

        # Clica no select de Informações
        page.evaluate("""() => {
            const sf = Array.from(document.querySelectorAll('.select-field__control'))
                .find(el => (el.innerText || '').trim() === 'CPF');
            if (sf) sf.click();
        }""")
        page.wait_for_timeout(1200)

        # Lista as opções visíveis após abrir
        opts = page.evaluate("""() => {
            const out = [];
            // react-select usa .select-field__option ou data-react-select-option
            const sel = document.querySelectorAll('[class*="select-field__option"], [class*="option"][role="option"]');
            for (const o of sel) {
                const r = o.getBoundingClientRect();
                if (r.width === 0) continue;
                out.push({
                    cls: o.className.toString().slice(0, 100),
                    text: (o.innerText || '').trim(),
                });
            }
            return out;
        }""")
        print("Opções visíveis após abrir o select:")
        for o in opts:
            print(f"  {o}")

        page.screenshot(path="/tmp/dropdown-info.png", full_page=False)
        print("Screenshot: /tmp/dropdown-info.png")
        browser.close()


if __name__ == "__main__":
    main()
