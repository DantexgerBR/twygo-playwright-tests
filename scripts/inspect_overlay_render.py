"""Compara como o overlay de marca d'água é renderizado em desktop vs mobile.

Procura: pseudo-elements ::before/::after, background-image (data URI / svg), canvas
adicional, e qualquer outra técnica que pinte 'CPF :' sem text node no DOM.
"""
import os, json
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

        result = page.evaluate("""() => {
            const out = {bg_images: [], pseudo_with_content: [], canvas_count: 0, divs_z_high: []};
            // 1) elementos com background-image diferente de 'none'
            for (const el of document.querySelectorAll('*')) {
                const cs = window.getComputedStyle(el);
                if (cs.backgroundImage && cs.backgroundImage !== 'none') {
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) continue;
                    const v = document.querySelector('video');
                    if (!v) continue;
                    const vr = v.getBoundingClientRect();
                    // só os que estão sobrepostos ao video
                    const sobreVideo = r.x < vr.x + vr.width && r.x + r.width > vr.x &&
                                       r.y < vr.y + vr.height && r.y + r.height > vr.y;
                    if (!sobreVideo) continue;
                    out.bg_images.push({
                        tag: el.tagName,
                        cls: (el.className && el.className.toString) ? el.className.toString().slice(0, 100) : '',
                        bg: cs.backgroundImage.slice(0, 200),
                        rect: {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)},
                        pos: cs.position,
                        zIndex: cs.zIndex,
                    });
                }
                // 2) pseudo-elements
                const before = window.getComputedStyle(el, '::before');
                const after = window.getComputedStyle(el, '::after');
                for (const [name, cs2] of [['::before', before], ['::after', after]]) {
                    if (cs2.content && cs2.content !== 'none' && cs2.content !== 'normal' && cs2.content !== '""') {
                        out.pseudo_with_content.push({
                            tag: el.tagName,
                            cls: (el.className && el.className.toString) ? el.className.toString().slice(0, 80) : '',
                            pseudo: name,
                            content: cs2.content.slice(0, 100),
                            bg: cs2.backgroundImage.slice(0, 100),
                        });
                    }
                }
            }
            // 3) canvas (extra)
            out.canvas_count = document.querySelectorAll('canvas').length;
            // 4) divs com z-index alto sobre o video
            const v = document.querySelector('video');
            const vr = v ? v.getBoundingClientRect() : null;
            if (vr) {
                for (const el of document.querySelectorAll('div, span')) {
                    const cs = window.getComputedStyle(el);
                    const z = parseInt(cs.zIndex);
                    if (isNaN(z) || z < 10) continue;
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) continue;
                    const sobreVideo = r.x < vr.x + vr.width && r.x + r.width > vr.x &&
                                       r.y < vr.y + vr.height && r.y + r.height > vr.y;
                    if (!sobreVideo) continue;
                    out.divs_z_high.push({
                        tag: el.tagName,
                        cls: (el.className && el.className.toString) ? el.className.toString().slice(0, 100) : '',
                        z: z,
                        rect: {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)},
                        innerSlice: el.outerHTML.substring(0, 250),
                    });
                }
            }
            return out;
        }""")
        # Imprime resumo
        print(f"canvas extras: {result['canvas_count']}")
        print(f"\nbackground-image sobre vídeo ({len(result['bg_images'])}):")
        for b in result['bg_images'][:10]:
            print(f"  tag={b['tag']} pos={b['pos']} z={b['zIndex']} rect={b['rect']}")
            print(f"    bg: {b['bg']}")
            print(f"    cls: {b['cls']}\n")
        print(f"\npseudo-elements com content ({len(result['pseudo_with_content'])}):")
        for p in result['pseudo_with_content'][:5]:
            print(f"  {p}")
        print(f"\ndivs com z-index alto sobre vídeo ({len(result['divs_z_high'])}):")
        for d in result['divs_z_high'][:5]:
            print(f"  tag={d['tag']} z={d['z']} cls={d['cls'][:60]}")
            print(f"    rect={d['rect']}")
            print(f"    outer: {d['innerSlice']}\n")
        browser.close()


# Desktop
inspecionar(dict(viewport={"width": 1920, "height": 1080}, locale="pt-BR"), "DESKTOP 1920x1080")
# Mobile
inspecionar(dict(
    viewport={"width": 360, "height": 740},
    is_mobile=True, has_touch=True, device_scale_factor=2,
    user_agent="Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile",
    locale="pt-BR",
), "MOBILE 360x740")
