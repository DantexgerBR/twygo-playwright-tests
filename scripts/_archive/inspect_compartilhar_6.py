"""Inspecao 6: explorar fluxo 'Ambiente externo' do form de compartilhamento."""
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
OUT = Path("test-results/inspect_compartilhar6")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        LoginPage(page).login(BASE_URL, EMAIL, SENHA)

        page.goto(BASE_URL + f"e/{EVENTO}/shared_events/new", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(7000)
        page.screenshot(path=str(OUT / "01-form-interno.png"), full_page=True)

        # marcar Ambiente externo (consumer_type=1)
        page.evaluate("""() => {
            const r = document.querySelector('input[name="consumer_type"][value="1"]');
            if (r) { r.click(); }
        }""")
        page.wait_for_timeout(4000)
        page.screenshot(path=str(OUT / "02-form-externo.png"), full_page=True)

        # listar inputs/labels/botoes visiveis agora
        info = page.evaluate(r"""() => {
            const data = {labels: [], inputs: [], selects: [], buttons: []};
            document.querySelectorAll('label').forEach(el => {
                if (el.offsetParent !== null) data.labels.push((el.innerText || '').trim().slice(0,80));
            });
            document.querySelectorAll('input:not([type=hidden])').forEach(el => {
                if (el.offsetParent === null) return;
                data.inputs.push({
                    type: el.type, name: el.name, id: el.id, placeholder: el.placeholder,
                    value: el.value, role: el.getAttribute('role') || '',
                });
            });
            document.querySelectorAll('select, [role=combobox]').forEach(el => {
                data.selects.push({tag: el.tagName, id: el.id, name: el.getAttribute('name')});
            });
            document.querySelectorAll('button').forEach(el => {
                if (el.offsetParent === null) return;
                const t = (el.innerText || '').trim();
                if (t && t.length < 40) data.buttons.push({text: t, id: el.id});
            });
            return data;
        }""")
        print("labels visiveis:", info["labels"])
        print("\ninputs visiveis:")
        for i in info["inputs"]: print(" ", i)
        print("\nselects:")
        for s in info["selects"]: print(" ", s)
        print("\nbotoes:")
        for b in info["buttons"]: print(" ", b)

        # tentar abrir combobox/select pra ver se ha lista de orgs externas
        try:
            combo = page.locator('input[role=combobox]').first
            combo.click()
            page.wait_for_timeout(3000)
            page.screenshot(path=str(OUT / "03-externo-dropdown.png"), full_page=True)
            opts = page.evaluate(r"""() => Array.from(document.querySelectorAll(
                '[role="option"], [class*="select__option"], .chakra-react-select__option'
            )).map(el => (el.innerText || '').trim()).filter(Boolean)""")
            print("\nopcoes do dropdown 'Ambiente externo':", opts)
        except Exception as e:
            print("falha abrir dropdown:", e)

        # tentar digitar 'danteshare' no combobox e ver se autocompleta
        try:
            combo = page.locator('input[role=combobox]').first
            combo.fill("danteshare")
            page.wait_for_timeout(3000)
            page.screenshot(path=str(OUT / "04-externo-search-danteshare.png"), full_page=True)
            opts = page.evaluate(r"""() => Array.from(document.querySelectorAll(
                '[role="option"], [class*="select__option"], .chakra-react-select__option'
            )).map(el => (el.innerText || '').trim()).filter(Boolean)""")
            print("\nopcoes apos digitar 'danteshare':", opts)

            # tambem tentar 'dante' e 'share' separadamente
            combo.fill("")
            page.wait_for_timeout(500)
            combo.fill("share")
            page.wait_for_timeout(2500)
            opts2 = page.evaluate(r"""() => Array.from(document.querySelectorAll(
                '[role="option"], [class*="select__option"], .chakra-react-select__option'
            )).map(el => (el.innerText || '').trim()).filter(Boolean)""")
            print("opcoes apos digitar 'share':", opts2)
        except Exception as e:
            print("falha busca:", e)

        browser.close()


if __name__ == "__main__":
    main()
