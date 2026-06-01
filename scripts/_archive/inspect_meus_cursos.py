"""Abre 'Meus Cursos' do aluno e lista todos os cursos com seus IDs."""
import os, re
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
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        page.goto(BASE + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(EMAIL)
        page.locator("#user_password").fill(PWD)
        page.locator("#user_submit").click()
        page.wait_for_load_state("domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)

        page.goto(BASE + "dashboard_students", wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        # Clica em "Meus Cursos"
        try:
            page.get_by_text("Meus Cursos", exact=True).first.click()
            page.wait_for_timeout(4000)
        except Exception as e:
            print(f"Não achei link 'Meus Cursos': {e}")
        print("URL pós-click:", page.url)
        page.screenshot(path="/tmp/meus-cursos.png", full_page=True)

        # Lista TUDO que pareça curso
        hrefs = page.eval_on_selector_all(
            "a",
            "els => els.map(e => ({href: e.getAttribute('href'), text: (e.innerText||'').trim().slice(0,120)})).filter(x => x.href)"
        )
        # Procura padrões de ID numérico ou referência a evento/curso
        com_id = [h for h in hrefs if re.search(r"/\d{4,8}", h["href"] or "")]
        print(f"\nLinks com IDs numéricos ({len(com_id)}):")
        for h in com_id[:30]:
            print(f"  href={h['href']!r}  text={h['text']!r}")

        # Tem o evento alvo?
        alvo = [h for h in hrefs if EVENTO in (h["href"] or "")]
        print(f"\nLinks com evento alvo ({EVENTO}): {len(alvo)}")
        for h in alvo[:5]:
            print(f"  {h}")

        # Lista títulos de cards/textos visíveis
        print("\nTextos visíveis (h1-h4 + .card-title-like):")
        texts = page.eval_on_selector_all(
            "h1, h2, h3, h4, [class*='title' i], [class*='Title']",
            "els => els.map(e => (e.innerText||'').trim().slice(0,120)).filter(Boolean)"
        )
        for t in texts[:30]:
            print(f"  - {t}")

        browser.close()


if __name__ == "__main__":
    main()
