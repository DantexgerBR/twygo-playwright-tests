"""Inspeciona estrutura do checkbox de marca d'água na página de edição."""
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"]
EMAIL = os.environ["ADMIN_EMAIL"]
PWD = os.environ["ADMIN_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]
ATIV = os.environ["ATIVIDADE_VIDEO_MARCA_DAGUA_ID"]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 768})

        # Login
        page.goto(BASE + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(EMAIL)
        page.locator("#user_password").fill(PWD)
        page.locator("#user_submit").click()
        page.wait_for_load_state("networkidle", timeout=20000)

        # Edição
        page.goto(f"{BASE}e/{EVENTO}/contents/{ATIV}/edit", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)
        page.screenshot(path="/tmp/twygo-edit.png", full_page=True)
        with open("/tmp/twygo-edit.html", "w") as f:
            f.write(page.content())
        print("Screenshot e HTML salvos.")

        # Procura por "marca d'água" no DOM e mostra contexto
        elements = page.get_by_text("marca d'água", exact=False).all()
        print(f"\nTextos com 'marca d\\'água': {len(elements)}")
        for el in elements[:5]:
            try:
                # outerHTML do pai
                outer = el.evaluate(
                    "el => el.parentElement ? el.parentElement.outerHTML.substring(0, 400) : el.outerHTML.substring(0, 400)"
                )
                print(f"  ─ {outer!r}\n")
            except Exception as e:
                print(f"  ─ ERROR {e}")

        # Estrutura específica do checkbox
        checkboxes = page.locator(".chakra-checkbox").all()
        print(f"\nchakra-checkbox: {len(checkboxes)}")
        for cb in checkboxes[:10]:
            try:
                txt = cb.inner_text()
                checked = cb.locator("input").get_attribute("aria-checked")
                outer = cb.evaluate("el => el.outerHTML.substring(0, 300)")
                print(f"  txt={txt[:60]!r} input.aria-checked={checked} outer={outer[:200]!r}")
            except Exception as e:
                print(f"  ERROR {e}")

        # Listar botões Salvar
        btns = page.get_by_role("button", name="Salvar").all()
        print(f"\nBotões 'Salvar': {len(btns)}")

        browser.close()


if __name__ == "__main__":
    main()
