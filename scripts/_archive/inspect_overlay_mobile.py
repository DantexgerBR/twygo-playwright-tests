"""Procura overlay de marca d'água no DOM em viewport mobile."""
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ALUNO_EMAIL"]
PWD = os.environ["ALUNO_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 360, "height": 740},
            is_mobile=True, has_touch=True, device_scale_factor=2,
            user_agent="Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile",
            locale="pt-BR",
        )
        page = ctx.new_page()
        page.goto(BASE + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(EMAIL)
        page.locator("#user_password").fill(PWD)
        page.locator("#user_submit").click()
        page.wait_for_timeout(3500)
        page.goto(f"{BASE}e/{EVENTO}/learn?learn_origin=my-contents", wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        try:
            page.get_by_text("vídeo", exact=False).first.click(timeout=5000)
            page.wait_for_timeout(4000)
        except Exception:
            pass
        page.evaluate("() => { const v = document.querySelector('video'); v.muted = true; v.play(); }")
        page.wait_for_timeout(3000)

        info = page.evaluate("""() => {
            const out = {};
            const v = document.querySelector('video');
            if (!v) return {error: 'no video'};
            const vRect = v.getBoundingClientRect();
            out.video_rect = {x: vRect.x, y: vRect.y, w: vRect.width, h: vRect.height};

            // Procura por TEXTO 'CPF' ou 'E-mail' em qualquer elemento (incluindo SVG, atributos)
            out.cpf_text_nodes = [];
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            let n;
            while ((n = walker.nextNode())) {
                const txt = (n.nodeValue || '').trim();
                if (/CPF|E-mail/i.test(txt) && txt.length < 80) {
                    const el = n.parentElement;
                    out.cpf_text_nodes.push({
                        text: txt,
                        tag: el.tagName,
                        cls: (el.className && el.className.toString) ? el.className.toString().slice(0, 100) : '',
                    });
                }
            }

            // Procura SVG text
            out.svg_texts = [];
            for (const t of document.querySelectorAll('svg text, svg tspan')) {
                const txt = (t.textContent || '').trim();
                if (txt) out.svg_texts.push({tag: t.tagName, text: txt.slice(0, 80)});
            }

            // Procura elementos posicionados absolute/fixed dentro da área do vídeo
            out.overlays_sobre_video = [];
            for (const el of document.querySelectorAll('*')) {
                const r = el.getBoundingClientRect();
                if (r.width === 0 || r.height === 0) continue;
                // Está dentro da área do vídeo?
                if (r.x >= vRect.x - 10 && r.x <= vRect.x + vRect.width + 10 &&
                    r.y >= vRect.y - 10 && r.y <= vRect.y + vRect.height + 10 && el.tagName !== 'VIDEO') {
                    const cs = window.getComputedStyle(el);
                    if (cs.position === 'absolute' || cs.position === 'fixed') {
                        const direct = Array.from(el.childNodes).filter(c => c.nodeType === 3).map(c => c.nodeValue.trim()).join(' ').slice(0, 50);
                        out.overlays_sobre_video.push({
                            tag: el.tagName,
                            cls: (el.className && el.className.toString) ? el.className.toString().slice(0, 80) : '',
                            pos: cs.position,
                            z: cs.zIndex,
                            text: direct,
                            rect: {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)},
                        });
                    }
                }
            }
            return out;
        }""")
        import json
        print(json.dumps(info, indent=2, ensure_ascii=False)[:4000])
        browser.close()


if __name__ == "__main__":
    main()
