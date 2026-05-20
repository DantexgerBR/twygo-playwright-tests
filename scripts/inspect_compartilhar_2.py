"""Inspecao parte 2: pagina /o/<org>/shared_events e botoes na listagem de eventos."""
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
ORG = os.environ.get("ORG_ID", "36675")
OUT = Path("test-results/inspect_compartilhar2")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        LoginPage(page).login(BASE_URL, EMAIL, SENHA)
        print("[1] logado:", page.url)

        # A. /o/<org>/shared_events
        page.goto(BASE_URL + f"o/{ORG}/shared_events", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(6000)
        print("\n[A] shared_events:", page.url)
        page.screenshot(path=str(OUT / "A-shared_events.png"), full_page=True)

        sondagem = page.evaluate(
            r"""() => {
                const re = /compartilh|copia|cópia|espelho|controlada|adicionar|enviar/i;
                const els = Array.from(document.querySelectorAll('a, button, [role="button"], [role="menuitem"]'))
                    .filter(el => re.test((el.innerText || '').trim()) && el.offsetParent !== null);
                return els.slice(0, 30).map(el => ({
                    tag: el.tagName,
                    text: (el.innerText || '').trim().slice(0, 120),
                    href: el.getAttribute('href'),
                    id: el.id,
                    cls: el.className && el.className.toString().slice(0, 200),
                }));
            }"""
        )
        print("  botoes/links suspeitos:")
        for s in sondagem:
            print(" ", s)

        # B. listagem de eventos: procurar acao "..." ou kebab per row
        page.goto(BASE_URL + f"o/{ORG}/events", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(6000)
        print("\n[B] /o/{org}/events:", page.url)
        page.screenshot(path=str(OUT / "B-eventos-org.png"), full_page=True)
        sondagem = page.evaluate(
            r"""(evento) => {
                const re = /compartilh|copia|cópia|espelho|controlada|enviar/i;
                const items = Array.from(document.querySelectorAll('[data-id], tr, li, .event-card, .card'))
                    .filter(el => (el.innerText || '').includes(evento) || el.getAttribute('data-id') === evento);
                return items.slice(0,3).map(el => ({
                    cls: el.className && el.className.toString().slice(0,200),
                    text: (el.innerText || '').slice(0,400),
                }));
            }""",
            EVENTO,
        )
        print("  row do curso:", sondagem)

        # C. tentar abrir menu de acoes do curso
        page.goto(BASE_URL + "events", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(6000)
        page.screenshot(path=str(OUT / "C-events-listagem.png"), full_page=True)
        # procurar elementos com material icon "more_vert" ou "more_horiz" relacionados ao evento
        sondagem = page.evaluate(
            r"""(evento) => {
                const rows = Array.from(document.querySelectorAll('tr, [data-id], li, .event-card, .card'))
                    .filter(el => (el.innerText || '').includes(evento));
                if (!rows.length) return {row: null};
                const r = rows[0];
                const trig = r.querySelector('button, .dropdown-toggle, [aria-label*="ações"], [aria-label*="opções"], [aria-haspopup]');
                return {
                    row_text: (r.innerText || '').slice(0,300),
                    row_html: r.outerHTML.slice(0,1200),
                    trig: trig ? trig.outerHTML.slice(0,400) : null,
                };
            }""",
            EVENTO,
        )
        print("\n[C] linha do curso 787696 na listagem /events:")
        print(sondagem)

        # D. tela de edicao do curso: ha algum botao "Compartilhar"?
        page.goto(BASE_URL + f"e/{EVENTO}/edit", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(8000)
        print("\n[D] /e/{evento}/edit:", page.url)
        page.screenshot(path=str(OUT / "D-edit-curso.png"), full_page=True)
        # listar TODOS os botoes/links da pagina, agrupados por texto curto
        sondagem = page.evaluate(
            r"""() => {
                const set = new Set();
                document.querySelectorAll('a, button, [role="button"]').forEach(el => {
                    const t = (el.innerText || '').trim();
                    if (t && el.offsetParent !== null && t.length < 60) set.add(t.slice(0,60));
                });
                return Array.from(set);
            }"""
        )
        print("  botoes/links visiveis na edicao do curso:")
        for s in sondagem:
            print(" ", repr(s))

        # E. modelos / acoes do curso via menu lateral
        page.goto(BASE_URL + f"e/{EVENTO}", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(8000)
        print("\n[E] /e/{evento}:", page.url)
        page.screenshot(path=str(OUT / "E-curso-home.png"), full_page=True)
        sondagem = page.evaluate(
            r"""() => {
                const set = new Set();
                document.querySelectorAll('a, button, [role="button"]').forEach(el => {
                    const t = (el.innerText || '').trim();
                    if (t && el.offsetParent !== null && t.length < 60) set.add(t.slice(0,60));
                });
                return Array.from(set);
            }"""
        )
        for s in sondagem:
            print(" ", repr(s))

        browser.close()


if __name__ == "__main__":
    main()
