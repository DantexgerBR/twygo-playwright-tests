"""Inspeciona o conteúdo do div z-index 99999 (provável container da marca d'água) em desktop e mobile."""
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ALUNO_EMAIL"]
PWD = os.environ["ALUNO_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]


def inspecionar(context_kwargs, label):
    print(f"\n{'='*60}\n{label}\n{'='*60}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(**context_kwargs)
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
        page.wait_for_timeout(4000)

        info = page.evaluate("""() => {
            // Acha o div com z-index 99999 e inset:0px e pointer-events:none
            const candidatos = Array.from(document.querySelectorAll('div')).filter(el => {
                const cs = window.getComputedStyle(el);
                return cs.zIndex === '99999' && cs.position === 'absolute';
            });
            const out = {found: candidatos.length, divs: []};
            for (const el of candidatos.slice(0, 3)) {
                const r = el.getBoundingClientRect();
                out.divs.push({
                    rect: {x: r.x, y: r.y, w: r.width, h: r.height},
                    outerLength: el.outerHTML.length,
                    childCount: el.children.length,
                    innerText: (el.innerText || '').slice(0, 200),
                    innerHTMLSlice: el.innerHTML.slice(0, 800),
                    parentTag: el.parentElement ? el.parentElement.tagName : null,
                    parentCls: el.parentElement && el.parentElement.className && el.parentElement.className.toString
                        ? el.parentElement.className.toString().slice(0, 100) : '',
                });
            }
            return out;
        }""")
        import json
        print(json.dumps(info, indent=2, ensure_ascii=False)[:4000])
        browser.close()


inspecionar(dict(viewport={"width": 1920, "height": 1080}, locale="pt-BR"), "DESKTOP")
inspecionar(dict(
    viewport={"width": 360, "height": 740},
    is_mobile=True, has_touch=True, device_scale_factor=2,
    user_agent="Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile",
    locale="pt-BR",
), "MOBILE")
