"""Inspecao 5: abrir form Adicionar compartilhamento e mapear DOM do select 'Ambientes'."""
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
OUT = Path("test-results/inspect_compartilhar5")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        LoginPage(page).login(BASE_URL, EMAIL, SENHA)

        page.goto(BASE_URL + f"e/{EVENTO}/edit?tab=share", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(7000)
        page.evaluate("document.querySelector('#shared-events-add-button').click()")
        page.wait_for_timeout(6000)
        print("url apos clicar Adicionar:", page.url)
        page.screenshot(path=str(OUT / "01-form-adicionar.png"), full_page=True)

        # mapear radios, selects, inputs visiveis na pagina inteira
        info = page.evaluate(r"""() => {
            const data = {radios: [], selects: [], inputs: [], buttons: []};
            document.querySelectorAll('input[type=radio]').forEach(el => data.radios.push({
                name: el.name, value: el.value, id: el.id, checked: el.checked,
                label: (el.closest('label')?.innerText || document.querySelector(`label[for="${el.id}"]`)?.innerText || '').trim().slice(0,120),
            }));
            document.querySelectorAll('select, [role="combobox"]').forEach(el => data.selects.push({
                tag: el.tagName,
                role: el.getAttribute('role'),
                name: el.getAttribute('name') || '',
                id: el.id, aria: el.getAttribute('aria-label') || '',
                text: (el.innerText || '').slice(0,120),
                outerHTML: el.outerHTML.slice(0, 800),
            }));
            document.querySelectorAll('input:not([type=radio]):not([type=hidden]):not([type=checkbox])').forEach(el => {
                if (el.offsetParent === null) return;
                data.inputs.push({name: el.name, id: el.id, placeholder: el.placeholder, type: el.type, value: el.value});
            });
            document.querySelectorAll('button').forEach(el => {
                if (el.offsetParent === null) return;
                const t = (el.innerText || '').trim();
                if (t && t.length < 40) data.buttons.push({text: t, id: el.id, cls: (el.className||'').toString().slice(0,150)});
            });
            return data;
        }""")
        print("radios:")
        for r in info["radios"]: print(" ", r)
        print("\nselects/comboboxes:")
        for s in info["selects"]: print(" ", s)
        print("\ninputs visiveis:")
        for i in info["inputs"]: print(" ", i)
        print("\nbotoes visiveis:")
        for b in info["buttons"]: print(" ", b)

        # tentar abrir o select Ambientes pra ver opcoes (eh um chakra-react-select)
        try:
            page.evaluate("""() => {
                const combo = document.querySelector('[role="combobox"], .chakra-react-select__control, [class*="select__control"]');
                if (combo) combo.click();
            }""")
            page.wait_for_timeout(3000)
            page.screenshot(path=str(OUT / "02-ambientes-aberto.png"), full_page=True)
            opcoes = page.evaluate(r"""() => {
                return Array.from(document.querySelectorAll('[role="option"], [class*="select__option"], .chakra-react-select__option'))
                    .map(el => (el.innerText || '').trim()).filter(Boolean);
            }""")
            print("\nopcoes do dropdown Ambientes:", opcoes)
        except Exception as e:
            print("falha abrir select Ambientes:", e)

        # clicar no radio 'Controlado' e ver se algo muda
        try:
            page.evaluate(r"""() => {
                const radios = document.querySelectorAll('input[type=radio]');
                for (const r of radios) {
                    const lbl = r.closest('label')?.innerText || '';
                    if (/control/i.test(lbl)) { r.click(); return; }
                }
            }""")
            page.wait_for_timeout(2000)
            page.screenshot(path=str(OUT / "03-controlado-marcado.png"), full_page=True)
        except Exception as e:
            print("falha marcar Controlado:", e)

        browser.close()


if __name__ == "__main__":
    main()
