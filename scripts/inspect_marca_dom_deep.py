"""Inspeção profunda: canvas/svg/shadow DOM em volta do player."""
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

        info = page.evaluate("""() => {
            const out = {};
            const v = document.querySelector('video');
            if (!v) return {error: 'no video'};

            // Sobe até o container raiz do player (4 níveis acima)
            let root = v;
            for (let i = 0; i < 5 && root.parentElement; i++) root = root.parentElement;

            // Todos os descendentes do root com info
            const descs = [];
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null);
            let n;
            while ((n = walker.nextNode())) {
                if (n.tagName === 'VIDEO') continue;
                const r = n.getBoundingClientRect();
                if (r.width === 0 && r.height === 0) continue;
                const cs = window.getComputedStyle(n);
                const item = {
                    tag: n.tagName,
                    cls: (n.className && n.className.toString) ? n.className.toString().slice(0,150) : '',
                    id: n.id,
                    pos: cs.position,
                    zIndex: cs.zIndex,
                    rect: {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)},
                };
                // Pega texto direto (não texto de descendentes profundos)
                const direct = Array.from(n.childNodes).filter(c => c.nodeType === 3).map(c => c.nodeValue.trim()).join(' ').slice(0, 60);
                if (direct) item.text = direct;
                descs.push(item);
            }
            out.descs_count = descs.length;
            // Filtra os que têm posição absolute/fixed (overlays típicos)
            out.overlays = descs.filter(d => d.pos === 'absolute' || d.pos === 'fixed').slice(0, 20);
            // Tudo que tem texto direto
            out.com_texto = descs.filter(d => d.text).slice(0, 20);
            // Procura canvas
            out.canvas_count = root.querySelectorAll('canvas').length;
            out.svg_count = root.querySelectorAll('svg').length;
            return out;
        }""")
        import json
        print(json.dumps(info, indent=2, ensure_ascii=False))

        browser.close()


if __name__ == "__main__":
    main()
