"""Localiza onde o texto 'CPF' está renderizado (SVG, shadow DOM, iframe, etc)."""
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_EMAIL"]
PWD = os.environ["ADMIN_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(BASE + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(EMAIL)
        page.locator("#user_password").fill(PWD)
        page.locator("#user_submit").click()
        page.wait_for_timeout(3000)

        page.goto(f"{BASE}e/{EVENTO}/learn?learn_origin=my-contents", wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        try:
            page.get_by_text("vídeo", exact=False).first.click(timeout=3000)
            page.wait_for_timeout(4000)
        except Exception:
            pass
        videos = page.locator("video").element_handles()
        if videos:
            videos[0].evaluate("v => v.play()")
            page.wait_for_timeout(3000)

        # 1) Conta iframes
        print(f"iframes: {page.locator('iframe').count()}")
        for fr in page.frames:
            if "CPF" in fr.content():
                print(f"  *** CPF está no frame: {fr.url}")

        # 2) Procura "CPF" em qualquer atributo (data-*, title, aria-label) ou nas folhas SVG
        info = page.evaluate("""() => {
            const out = {svg_texts: [], with_cpf_attr: [], shadow_hosts: []};

            // SVG <text>
            for (const t of document.querySelectorAll('svg text, svg textPath, svg tspan')) {
                const txt = (t.textContent || '').trim();
                if (txt) out.svg_texts.push({tag: t.tagName, text: txt.slice(0, 80)});
            }

            // Qualquer elemento com 'CPF' em algum atributo
            for (const el of document.querySelectorAll('*')) {
                for (const attr of el.attributes || []) {
                    if (/CPF/i.test(attr.value)) {
                        out.with_cpf_attr.push({tag: el.tagName, attr: attr.name, value: attr.value.slice(0, 100)});
                        break;
                    }
                }
            }

            // Shadow DOM hosts
            const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
            let n;
            while ((n = tw.nextNode())) {
                if (n.shadowRoot) {
                    out.shadow_hosts.push({tag: n.tagName, cls: (n.className && n.className.toString) ? n.className.toString().slice(0, 100) : ''});
                    // procura CPF no shadow
                    const inner = n.shadowRoot.textContent || '';
                    if (/CPF/i.test(inner)) {
                        out.shadow_hosts[out.shadow_hosts.length - 1].has_cpf = true;
                    }
                }
            }
            return out;
        }""")
        print("\nSVG textos:", info.get("svg_texts"))
        print("\nAtributos com 'CPF':")
        for x in info.get("with_cpf_attr", [])[:10]:
            print(f"  {x}")
        print(f"\nShadow hosts: {info.get('shadow_hosts')}")

        # 3) Salva HTML completo (com possíveis comentários/scripts) e procura "CPF"
        html = page.content()
        idx = html.find("CPF")
        if idx >= 0:
            print(f"\n'CPF' em HTML[main] posição {idx}: ...{html[max(0,idx-80):idx+80]}...")
        else:
            print("\n'CPF' NÃO está no HTML da página principal — está em iframe, shadow DOM ou canvas")

        browser.close()


if __name__ == "__main__":
    main()
