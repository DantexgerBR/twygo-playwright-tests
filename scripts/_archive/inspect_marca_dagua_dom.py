"""Inspeciona o DOM enquanto o vídeo toca pra achar o overlay de marca d'água."""
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
        page.wait_for_load_state("domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)

        page.goto(f"{BASE}e/{EVENTO}/learn?learn_origin=my-contents", wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        try:
            page.get_by_text("vídeo", exact=False).first.click(timeout=3000)
            page.wait_for_timeout(4000)
        except Exception:
            pass

        # Inicia o video
        videos = page.locator("video").element_handles()
        if videos:
            videos[0].evaluate("v => v.play()")
            page.wait_for_timeout(3000)

        # Procura TODOS os elementos com texto "CPF" visíveis
        cpf_info = page.evaluate("""() => {
            const out = [];
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
            let node;
            while ((node = walker.nextNode())) {
                const text = (node.nodeValue || '').trim();
                if (/CPF\\s*:/i.test(text) && text.length < 50) {
                    const el = node.parentElement;
                    const r = el.getBoundingClientRect();
                    if (r.width > 0 && r.height > 0) {
                        out.push({
                            text,
                            tag: el.tagName,
                            cls: (el.className && el.className.toString) ? el.className.toString().slice(0, 200) : el.className,
                            id: el.id,
                            rect: {x: r.x, y: r.y, w: r.width, h: r.height},
                            parent_cls: el.parentElement && el.parentElement.className && el.parentElement.className.toString
                                ? el.parentElement.className.toString().slice(0, 200)
                                : null,
                        });
                    }
                }
            }
            return out;
        }""")
        print(f"\n=== Elementos com texto 'CPF :' visíveis: {len(cpf_info)} ===")
        for c in cpf_info[:10]:
            print(f"  tag={c['tag']} cls={c['cls']!r} parent_cls={c['parent_cls']!r}")
            print(f"    rect={c['rect']}\n")

        # Salva o ancestral comum (provável container da marca d'água)
        if cpf_info:
            print(f"\nProvável seletor da marca d'água:")
            primeiro = cpf_info[0]
            if primeiro["cls"]:
                print(f"  por classe filha: .{primeiro['cls'].split()[0]}")
            if primeiro["parent_cls"]:
                print(f"  por classe pai: .{primeiro['parent_cls'].split()[0] if primeiro['parent_cls'].strip() else '(vazio)'}")

        browser.close()


if __name__ == "__main__":
    main()
