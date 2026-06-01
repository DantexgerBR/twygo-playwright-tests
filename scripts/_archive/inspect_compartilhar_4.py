"""Inspecao 4: clicar em 'Adicionar' na aba Compartilhar e mapear o modal."""
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
OUT = Path("test-results/inspect_compartilhar4")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        LoginPage(page).login(BASE_URL, EMAIL, SENHA)

        page.goto(BASE_URL + f"e/{EVENTO}/edit?tab=share", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(8000)
        page.screenshot(path=str(OUT / "01-aba-share-inicial.png"), full_page=True)

        # listagem existente de compartilhamentos
        listagem = page.evaluate(r"""() => {
            const body = document.body.innerText;
            return body.slice(0, 1500);
        }""")
        print("=== conteudo visivel na aba ===")
        print(listagem)

        # clicar em 'Adicionar' (shared-events-add-button) — usar click direto via JS pra evitar overlay
        clicou = page.evaluate("""() => {
            const b = document.querySelector('#shared-events-add-button');
            if (!b) return 'sem botao';
            b.scrollIntoView();
            b.click();
            return 'clicado';
        }""")
        print(f"[Adicionar] {clicou}")
        page.wait_for_timeout(8000)
        page.screenshot(path=str(OUT / "02-modal-adicionar.png"), full_page=True)

        # Mapear o modal chakra-modal (NAO o popover de notificacoes)
        info = page.evaluate(r"""() => {
            // procurar TODOS os dialogs/modais e classificar
            const all = Array.from(document.querySelectorAll('[role="dialog"], .chakra-modal__content'));
            const data = all.map(d => ({
                cls: (d.className || '').toString().slice(0, 200),
                role: d.getAttribute('role'),
                aria: d.getAttribute('aria-label') || '',
                header: d.querySelector('header, h2, .chakra-modal__header')?.innerText?.trim()?.slice(0,120) || '',
                text_sample: (d.innerText || '').slice(0, 600),
                outerHTML: d.outerHTML.slice(0, 6000),
            }));
            return data;
        }""")
        print("\n=== modais encontrados ===", len(info))
        for idx, m in enumerate(info):
            print(f"\n--- modal #{idx} ---")
            print("classe:", m["cls"])
            print("role:", m["role"], "aria:", m["aria"], "header:", m["header"])
            print("text_sample:", m["text_sample"])
        if info:
            with open(OUT / "modal_html.txt", "w") as f:
                for idx, m in enumerate(info):
                    f.write(f"\n--- MODAL {idx} ({m['header']}) ---\n{m['outerHTML']}\n")
            print(f"\nHTML completo salvo em {OUT / 'modal_html.txt'}")

        browser.close()


if __name__ == "__main__":
    main()
