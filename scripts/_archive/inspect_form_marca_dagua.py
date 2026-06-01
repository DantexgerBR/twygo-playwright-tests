"""Captura os seletores reais do form de marca d'água na edição (Rails)."""
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

        # Pega TODOS os checkboxes e radios da seção de marca d'água
        info = page.evaluate("""() => {
            const out = {checkboxes: [], radios: [], selects: []};
            // Pega elementos dentro do escopo do form (todo o body é ok)
            for (const el of document.querySelectorAll('input[type="checkbox"]')) {
                const id = el.id;
                const label = id ? document.querySelector(`label[for='${id}']`) : null;
                const labelText = label ? (label.innerText||'').trim() : null;
                if (labelText && /marca d.água|water/i.test(labelText)) {
                    out.checkboxes.push({id, name: el.name, value: el.value, checked: el.checked, label: labelText});
                }
            }
            for (const el of document.querySelectorAll('input[type="radio"]')) {
                const id = el.id;
                const label = id ? document.querySelector(`label[for='${id}']`) : null;
                const labelText = label ? (label.innerText||'').trim() : null;
                if (labelText && /movimento|fixa/i.test(labelText)) {
                    out.radios.push({id, name: el.name, value: el.value, checked: el.checked, label: labelText});
                }
            }
            for (const el of document.querySelectorAll('select')) {
                out.selects.push({
                    id: el.id,
                    name: el.name,
                    value: el.value,
                    options: Array.from(el.options).map(o => ({value: o.value, text: o.text})),
                });
            }
            // Botão Salvar
            const salvar = Array.from(document.querySelectorAll('button, input[type="submit"], input[type="button"]'))
                .find(b => /salvar/i.test(b.innerText || b.value || ''));
            out.salvar = salvar ? {
                tag: salvar.tagName, id: salvar.id, name: salvar.name,
                outer: salvar.outerHTML.substring(0, 200)
            } : null;
            return out;
        }""")
        import json
        print(json.dumps(info, indent=2, ensure_ascii=False)[:5000])

        # Tentando achar o select de posição (tag style, talvez select2)
        # Procura por texto "Lateral esquerda superior" e mostra ancestral
        pos_info = page.evaluate("""() => {
            const w = document.evaluate("//*[contains(text(), 'Lateral esquerda')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (!w) return null;
            return {
                tag: w.tagName,
                text: (w.innerText || '').trim().slice(0, 80),
                outer_parent: w.parentElement ? w.parentElement.outerHTML.substring(0, 400) : null,
            };
        }""")
        print("\nPosição atual:")
        print(pos_info)

        browser.close()


if __name__ == "__main__":
    main()
