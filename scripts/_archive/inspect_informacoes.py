"""Inspeciona estrutura DOM do campo 'Informações a exibir'."""
import os, json
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

        info = page.evaluate("""() => {
            const out = {labels_relevantes: [], select_fields: []};
            // Lista qualquer elemento com texto contendo 'Informações'
            const all = document.querySelectorAll('*');
            for (const el of all) {
                if (el.children.length > 0) continue;  // só nodos folha
                const txt = (el.innerText || '').trim();
                if (/Informações a exibir/i.test(txt) && txt.length < 100) {
                    out.labels_relevantes.push({
                        tag: el.tagName,
                        cls: (el.className && el.className.toString ? el.className.toString() : '').slice(0, 120),
                        text: txt,
                        outerSlice: el.outerHTML.substring(0, 200),
                    });
                }
            }
            // Lista todos os .select-field e seus conteúdos visíveis
            const sfs = document.querySelectorAll('.select-field, [class*="select-field"]');
            for (const sf of sfs) {
                if (sf.className && sf.className.toString && sf.className.toString().includes('multi-value')) continue;
                out.select_fields.push({
                    cls: sf.className.toString().slice(0, 120),
                    text: (sf.innerText || '').trim().slice(0, 200),
                    aria: sf.getAttribute('aria-label'),
                    rect: (() => {const r = sf.getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width};})(),
                });
            }
            return out;
        }""")
        print(json.dumps(info, indent=2, ensure_ascii=False)[:3000])

        browser.close()


if __name__ == "__main__":
    main()
