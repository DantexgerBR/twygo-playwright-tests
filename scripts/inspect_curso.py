"""Inspeciona o que aparece em /aprender/787696 após login do aluno."""
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

        # Vamos pelo dashboard primeiro
        page.goto(BASE + "dashboard_students", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(5000)
        print("Dashboard URL:", page.url)
        page.screenshot(path="/tmp/dashboard.png", full_page=True)

        # Lista links com IDs de eventos
        hrefs = page.eval_on_selector_all(
            "a",
            "els => els.map(e => ({href: e.getAttribute('href'), text: (e.innerText||'').trim().slice(0,100)})).filter(x => x.href)"
        )
        com_evento = [h for h in hrefs if EVENTO in (h["href"] or "")]
        print(f"\nLinks com evento_id={EVENTO} no dashboard ({len(com_evento)}):")
        for h in com_evento[:10]:
            print(f"  href={h['href']!r}")
            print(f"  text={h['text']!r}\n")

        # Tenta clicar no primeiro link do evento
        if com_evento:
            url_curso = com_evento[0]["href"]
            if not url_curso.startswith("http"):
                url_curso = BASE.rstrip("/") + url_curso
            print(f"\n→ Navegando para {url_curso}")
            page.goto(url_curso, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(6000)
            print("URL final:", page.url, "| title:", page.title())
            page.screenshot(path="/tmp/curso-entrada.png", full_page=True)

            # Lista TUDO que tem texto na página
            print("\nElementos com texto visível:")
            txts = page.eval_on_selector_all(
                "h1, h2, h3, h4, button, a",
                "els => els.map(e => ({tag: e.tagName, text: (e.innerText||'').trim().slice(0,80), href: e.getAttribute('href')})).filter(x => x.text)"
            )
            for t in txts[:30]:
                print(f"  {t}")

            # Procura referência à atividade
            with_ativ = [h for h in page.eval_on_selector_all("a", "els => els.map(e => ({href: e.getAttribute('href'), text: (e.innerText||'').trim().slice(0,80)})).filter(x => x.href)") if ATIV in (h["href"] or "")]
            print(f"\nLinks com atividade_id={ATIV}: {len(with_ativ)}")
            for h in with_ativ[:5]:
                print(f"  {h}")

        browser.close()


if __name__ == "__main__":
    main()
