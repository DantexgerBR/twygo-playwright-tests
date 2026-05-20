"""Testa diferentes formas de capturar o frame do vídeo em mobile."""
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ALUNO_EMAIL"]
PWD = os.environ["ALUNO_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]


def test_config(name, context_kwargs, launch_args=None):
    print(f"\n=== {name} ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=launch_args or [],
        )
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
            page.wait_for_timeout(3000)
        except Exception:
            pass

        page.evaluate("() => { const v = document.querySelector('video'); if (v) { v.muted = true; v.play(); } }")
        page.wait_for_timeout(5000)  # mais tempo pra player desenhar

        # Captura frame do <video> via canvas
        ok, w, h, sample = page.evaluate("""() => {
            const v = document.querySelector('video');
            if (!v) return [false, 0, 0, null];
            const c = document.createElement('canvas');
            c.width = v.videoWidth || 640;
            c.height = v.videoHeight || 360;
            const ctx = c.getContext('2d');
            try {
                ctx.drawImage(v, 0, 0, c.width, c.height);
                const data = ctx.getImageData(c.width/2, c.height/2, 1, 1).data;
                // soma rgb do pixel central pra ver se é preto puro
                return [true, c.width, c.height, [data[0], data[1], data[2]]];
            } catch (e) {
                return [false, c.width, c.height, e.message];
            }
        }""")
        print(f"  videoWidth/Height: {w}x{h} | pixel central RGB: {sample}")

        slug = name.replace(" ", "_").replace(":", "")
        page.screenshot(path=f"/tmp/mobile-test-{slug}.png", full_page=True)
        print(f"  screenshot: /tmp/mobile-test-{slug}.png")
        browser.close()


# 1) Mobile + flags ativadas (atual)
test_config("mobile_default", dict(
    viewport={"width": 360, "height": 740},
    is_mobile=True, has_touch=True, device_scale_factor=2,
    user_agent="Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile",
    locale="pt-BR",
))

# 2) Mobile só por viewport (sem is_mobile/has_touch)
test_config("viewport_only", dict(
    viewport={"width": 360, "height": 740},
    locale="pt-BR",
))

# 3) Com flags pra forçar software rendering (frame capturável)
test_config("software_render", dict(
    viewport={"width": 360, "height": 740},
    is_mobile=True, has_touch=True, device_scale_factor=2,
    user_agent="Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile",
    locale="pt-BR",
), launch_args=["--use-gl=swiftshader", "--enable-features=VaapiVideoDecoder"])
