"""Captura frame do vídeo via canvas em DESKTOP pra comparar com mobile."""
import base64, os
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ALUNO_EMAIL"]
PWD = os.environ["ALUNO_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]
OUT = Path("/tmp"); OUT.mkdir(exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="pt-BR")
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
        page.wait_for_timeout(5000)

        # Capturar via canvas
        result = page.evaluate("""() => {
            const v = document.querySelector('video');
            if (!v) return {ok: false};
            const c = document.createElement('canvas');
            c.width = v.videoWidth; c.height = v.videoHeight;
            const ctx = c.getContext('2d');
            ctx.drawImage(v, 0, 0, c.width, c.height);
            return {ok: true, currentTime: v.currentTime, w: c.width, h: c.height, dataUrl: c.toDataURL('image/png')};
        }""")
        if result.get("ok"):
            b64 = result["dataUrl"].split(",", 1)[1]
            (OUT / "desktop-canvas-frame.png").write_bytes(base64.b64decode(b64))
            print(f"Canvas (desktop): {result['w']}x{result['h']} t={result['currentTime']:.2f}s → /tmp/desktop-canvas-frame.png")

        # E pra referência, o page.screenshot capturando o player visível
        page.screenshot(path="/tmp/desktop-page-screenshot.png", clip={"x": 0, "y": 0, "width": 1920, "height": 1080})
        print("page.screenshot (desktop): /tmp/desktop-page-screenshot.png")
        browser.close()


if __name__ == "__main__":
    main()
