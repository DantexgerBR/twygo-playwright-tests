"""Inspeção da UI de Compartilhar curso (T-1599).

Procura por:
- Botão/menu "Compartilhar" / "Share" na pagina do curso (edicao ou listagem).
- Modal de compartilhamento com opcoes "Copia controlada" / "Espelho".
- Campo para selecionar org destinataria.

Tira screenshots em test-results/inspect_compartilhar/.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pages.login_page import LoginPage  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_EMAIL"]
SENHA = os.environ["ADMIN_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]
OUT = Path("test-results/inspect_compartilhar")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()

        LoginPage(page).login(BASE_URL, EMAIL, SENHA)
        print("[1] logado:", page.url)

        def safe_goto(url):
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(4000)
                return True
            except Exception as e:
                print(f"  ! falhou {url}: {type(e).__name__}")
                return False

        # 1) listagem de cursos (admin)
        for path in ["events", "admin/events", "manage/events", "events?admin=1"]:
            if safe_goto(BASE_URL + path):
                print(f"  listagem({path}):", page.url, "title=", page.title())
                page.screenshot(path=str(OUT / f"01-listagem-{path.replace('/', '_').replace('?','_').replace('=','_')}.png"), full_page=True)

        # 2) tela de edicao/detalhe do curso de origem
        urls_curso = [
            f"{BASE_URL}e/{EVENTO}/edit",
            f"{BASE_URL}e/{EVENTO}",
            f"{BASE_URL}e/{EVENTO}/contents",
        ]
        for u in urls_curso:
            if safe_goto(u):
                slug = u.rstrip("/").rsplit("/", 1)[-1]
                print(f"[2] curso ({slug}):", page.url)
                page.screenshot(path=str(OUT / f"02-curso-{slug}.png"), full_page=True)

        # 3) procurar elementos com texto "Compartilhar" / "Cópia" / "Espelho"
        sondagem = page.evaluate(
            r"""() => {
                const re = /compartilh|cópia controlada|copia controlada|espelho|sharing|share/i;
                const els = Array.from(document.querySelectorAll('a, button, span, div, li, [role="menuitem"], [role="button"]'))
                    .filter(el => re.test((el.innerText || '').trim()) && el.offsetParent !== null);
                return els.slice(0, 40).map(el => ({
                    tag: el.tagName,
                    text: (el.innerText || '').trim().slice(0, 120),
                    href: el.getAttribute('href'),
                    id: el.id,
                    cls: el.className && el.className.toString().slice(0, 200),
                    aria: el.getAttribute('aria-label'),
                }));
            }"""
        )
        print("\n[3] elementos com texto Compartilhar/Cópia/Espelho:")
        for s in sondagem:
            print(" ", s)

        # 4) procurar botoes de "..." / dropdowns na listagem que possam ter "Compartilhar"
        safe_goto(BASE_URL + "events")
        # Hover/click no item do curso
        trigs = page.evaluate(
            r"""(evento) => {
                const rows = Array.from(document.querySelectorAll('tr, li, [data-id], .card'))
                    .filter(el => (el.innerText || '').includes(evento) || el.getAttribute('data-id') === evento);
                if (!rows.length) return null;
                const row = rows[0];
                return {
                    text: (row.innerText || '').slice(0, 200),
                    html: row.outerHTML.slice(0, 1500),
                };
            }""",
            EVENTO,
        )
        print("\n[4] row do curso na listagem:")
        print(trigs)
        page.screenshot(path=str(OUT / "04-listagem-eventos.png"), full_page=True)

        browser.close()


if __name__ == "__main__":
    main()
