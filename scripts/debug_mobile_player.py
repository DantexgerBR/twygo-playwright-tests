"""Debug do estado do player em viewport mobile."""
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
            user_agent="Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            locale="pt-BR",
        )
        page = ctx.new_page()
        page.goto(BASE + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(EMAIL)
        page.locator("#user_password").fill(PWD)
        page.locator("#user_submit").click()
        page.wait_for_load_state("domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)

        page.goto(f"{BASE}e/{EVENTO}/learn?learn_origin=my-contents", wait_until="domcontentloaded")
        page.wait_for_timeout(6000)

        # Tenta clicar em "vídeo"
        try:
            page.get_by_text("vídeo", exact=False).first.click(timeout=5000)
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Click vídeo falhou: {e}")

        # Estado pre-play
        estado_pre = page.evaluate("""() => {
            const v = document.querySelector('video');
            if (!v) return {found: false};
            const r = v.getBoundingClientRect();
            return {
                found: true,
                src: (v.src || '').substring(0, 80),
                muted: v.muted,
                autoplay: v.autoplay,
                paused: v.paused,
                currentTime: v.currentTime,
                duration: v.duration,
                readyState: v.readyState,
                rect: {x: r.x, y: r.y, w: r.width, h: r.height, visible: r.width > 0 && r.height > 0},
            };
        }""")
        print(f"Pre-play: {estado_pre}")

        # Tenta tocar com muted=true (autoplay permitido)
        page.evaluate("""() => {
            const v = document.querySelector('video');
            if (v) {
                v.muted = true;
                v.play().then(() => console.log('play ok')).catch(e => console.error('play fail', e));
            }
        }""")
        page.wait_for_timeout(3000)

        estado_pos = page.evaluate("""() => {
            const v = document.querySelector('video');
            if (!v) return {found: false};
            return {
                paused: v.paused, currentTime: v.currentTime,
                readyState: v.readyState, ended: v.ended,
            };
        }""")
        print(f"Pos-play: {estado_pos}")

        page.screenshot(path="/tmp/mobile-debug.png", full_page=True)
        print("Screenshot: /tmp/mobile-debug.png")

        # Tenta clicar no chevron pra expandir
        try:
            page.locator("svg[class*='chevron'], [class*='Chevron'], [aria-label*='expand' i]").first.click(timeout=2000)
            page.wait_for_timeout(2000)
            page.screenshot(path="/tmp/mobile-debug-pos-chevron.png", full_page=True)
            print("Após chevron click: /tmp/mobile-debug-pos-chevron.png")
        except Exception as e:
            print(f"Chevron não clicável: {e}")

        browser.close()


if __name__ == "__main__":
    main()
