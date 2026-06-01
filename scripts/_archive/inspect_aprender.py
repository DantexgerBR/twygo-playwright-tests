"""Discovery do player na rota /contents/9280032 (Aprender)."""
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ALUNO_EMAIL"]
PWD = os.environ["ALUNO_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]
ATIV = os.environ["ATIVIDADE_VIDEO_MARCA_DAGUA_ID"]


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

        # Vai pra rota do curso e procura links pra atividade
        page.goto(f"{BASE}aprender/{EVENTO}", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(4000)
        print("URL curso:", page.url, "| title:", page.title())
        page.screenshot(path="/tmp/aprender-curso.png", full_page=True)

        # Lista links/clicáveis que contenham o ID 9280032 ou texto "vídeo"
        hrefs = page.eval_on_selector_all("a", "els => els.map(e => ({href: e.getAttribute('href'), text: (e.innerText||'').trim().slice(0,80)})).filter(x => x.href)")
        relevantes = [h for h in hrefs if ATIV in (h["href"] or "") or "vídeo" in (h["text"] or "").lower() or "video" in (h["text"] or "").lower()]
        print(f"\nLinks relevantes na página do curso ({len(relevantes)}):")
        for r in relevantes[:15]:
            print(f"  href={r['href']!r} text={r['text']!r}")

        # Tenta navegar para /contents/9280032 e inspeciona player
        page.goto(f"{BASE}contents/{ATIV}", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(5000)  # SPA carregar
        print(f"\nURL conteúdo: {page.url} | title: {page.title()}")
        page.screenshot(path="/tmp/aprender-conteudo.png", full_page=True)
        with open("/tmp/aprender-conteudo.html", "w") as f:
            f.write(page.content())

        print(f"\n<video>: {page.locator('video').count()}")
        print(f"<iframe>: {page.locator('iframe').count()}")
        for fr in page.frames:
            print(f"  frame: name={fr.name!r} url={fr.url!r}")

        # Procura padrões de player conhecidos
        for sel in [
            ".vjs-tech",
            ".plyr",
            ".video-js",
            "[data-vjs-player]",
            "[class*='player' i]",
            "[class*='Player']",
            "[class*='video' i]",
            "canvas",
        ]:
            c = page.locator(sel).count()
            if c:
                print(f"  {sel}: {c} elementos")

        # Procura marca d'água no DOM atual
        print("\nProcura marca d'água:")
        for sel in [
            "[class*='watermark' i]",
            "[class*='WaterMark']",
            "[class*='marca' i]",
            "[class*='Stamp']",
            "[data-watermark]",
        ]:
            els = page.locator(sel).all()
            for el in els[:3]:
                try:
                    txt = el.inner_text()
                    outer = el.evaluate("e => e.outerHTML.substring(0, 200)")
                    print(f"  {sel}: text={txt[:60]!r} outer={outer[:150]!r}")
                except Exception:
                    pass

        browser.close()


if __name__ == "__main__":
    main()
