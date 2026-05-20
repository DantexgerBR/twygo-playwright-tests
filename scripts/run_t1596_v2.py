"""T-1596 v2: tenta dispensar o drawer Chakra antes de tocar pra ver marca d'água."""
import os, sys
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ALUNO_EMAIL"]
PWD = os.environ["ALUNO_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]
OUT = Path("test-results/t1596-v2"); OUT.mkdir(parents=True, exist_ok=True)


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

        # Pré: tenta múltiplas estratégias pra ver o player full
        page.screenshot(path=str(OUT / "01-antes.png"), full_page=True)

        # Estratégia 1: clicar no chevron `v` (expandir player) — procura SVG com path de chevron
        clicked_chevron = page.evaluate("""() => {
            // Procura SVGs visíveis com path/d que descreve chevron-down
            const svgs = document.querySelectorAll('svg');
            for (const s of svgs) {
                const r = s.getBoundingClientRect();
                if (r.width === 0 || r.height === 0) continue;
                if (r.y < 400 && r.y > 100 && r.x > 100 && r.x < 300) {  // área onde o chevron apareceu
                    s.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                    return {clicked: true, rect: r};
                }
            }
            return {clicked: false};
        }""")
        print(f"chevron click: {clicked_chevron}")
        page.wait_for_timeout(2500)
        page.screenshot(path=str(OUT / "02-pos-chevron.png"), full_page=True)

        # Estratégia 2: dispensar drawer Chakra programaticamente (style display: none)
        dismissed = page.evaluate("""() => {
            const drawer = document.querySelector('.chakra-modal__content-container, .chakra-modal__overlay');
            if (drawer) { drawer.style.display = 'none'; return true; }
            return false;
        }""")
        print(f"drawer dismiss via style: {dismissed}")
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / "03-pos-dismiss.png"), full_page=True)

        # Play
        page.evaluate("() => { const v = document.querySelector('video'); v.muted = true; v.play(); }")
        page.wait_for_timeout(4000)
        page.screenshot(path=str(OUT / "04-tocando.png"), full_page=True)

        # Verifica novamente o conteúdo do div z=99999
        watermark_info = page.evaluate("""() => {
            const cs = Array.from(document.querySelectorAll('div')).filter(el => {
                const s = window.getComputedStyle(el);
                return s.zIndex === '99999' && s.position === 'absolute';
            });
            return cs.map(el => ({
                childCount: el.children.length,
                innerHTMLSlice: el.innerHTML.substring(0, 600),
                rect: (() => {const r = el.getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width, h: r.height};})(),
            }));
        }""")
        print(f"watermark divs após dismiss + play: {watermark_info}")

        browser.close()


if __name__ == "__main__":
    main()
