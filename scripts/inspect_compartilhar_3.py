"""Inspecao 3: abrir aba 'Compartilhar' dentro de /e/{evento}/edit."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pages.login_page import LoginPage  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
BASE_URL = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_EMAIL"]
SENHA = os.environ["ADMIN_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]
OUT = Path("test-results/inspect_compartilhar3")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        LoginPage(page).login(BASE_URL, EMAIL, SENHA)

        page.goto(BASE_URL + f"e/{EVENTO}/edit", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(8000)
        page.screenshot(path=str(OUT / "01-edit-default.png"), full_page=True)

        # Procurar o link/tab "Compartilhar"
        info = page.evaluate(r"""() => {
            const cands = Array.from(document.querySelectorAll('a, button, li, span, [role="tab"]'))
                .filter(el => /^Compartilhar\b/i.test((el.innerText || '').trim()) && el.offsetParent !== null);
            return cands.slice(0,5).map(el => ({
                tag: el.tagName,
                text: (el.innerText || '').trim(),
                href: el.getAttribute('href'),
                id: el.id,
                cls: el.className && el.className.toString(),
                outerHTML: el.outerHTML.slice(0,400),
            }));
        }""")
        print("links 'Compartilhar' candidatos:")
        for s in info:
            print(" ", s)

        # clicar no tab "Compartilhar" (Chakra tab)
        tab = page.locator('button[data-test-id="tab-share"]').first
        tab.scroll_into_view_if_needed()
        tab.click()
        page.wait_for_timeout(8000)
        print("\napos clicar em Compartilhar, url:", page.url)
        page.screenshot(path=str(OUT / "02-aba-compartilhar.png"), full_page=True)

        # listar campos/botoes visiveis na aba
        info2 = page.evaluate(r"""() => {
            const set = new Set();
            document.querySelectorAll('label, button, input, select, [role="button"], a').forEach(el => {
                const t = (el.innerText || '').trim();
                const aria = el.getAttribute('aria-label') || '';
                const ph = el.getAttribute('placeholder') || '';
                const name = el.getAttribute('name') || '';
                const tag = el.tagName;
                if ((t || aria || ph || name) && el.offsetParent !== null) {
                    set.add(JSON.stringify({tag, text: t.slice(0,80), aria, ph, name, id: el.id, cls: (el.className||'').toString().slice(0,150)}));
                }
            });
            return Array.from(set).slice(0,80);
        }""")
        print("\ncampos/botoes visiveis na aba Compartilhar:")
        for s in info2:
            print(" ", s)

        # tentar identificar inputs de tipo de compartilhamento e org destino
        radios = page.evaluate(r"""() => {
            return Array.from(document.querySelectorAll('input[type=radio]')).map(el => ({
                name: el.name, value: el.value, id: el.id, checked: el.checked,
                label: el.closest('label')?.innerText?.trim() || (document.querySelector(`label[for="${el.id}"]`)?.innerText?.trim() || ''),
            }));
        }""")
        print("\nradios na pagina:")
        for r in radios:
            print(" ", r)

        # procurar HTML do form de compartilhamento
        formhtml = page.evaluate(r"""() => {
            const form = document.querySelector('form#share_event, form[action*="share"], form[id*="share"]')
                || document.querySelector('.share_event, .shared_event_form, #shared_event');
            return form ? form.outerHTML.slice(0, 4000) : null;
        }""")
        print("\nform HTML (resumido):")
        print(formhtml)

        browser.close()


if __name__ == "__main__":
    main()
