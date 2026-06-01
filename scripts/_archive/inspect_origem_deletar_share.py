"""Inspecionar como deletar/remover um share existente em /e/{evento}/edit?tab=share da origem."""
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
OUT = Path("test-results/inspect_origem_deletar")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        LoginPage(page).login(BASE_URL, EMAIL, SENHA)
        page.goto(f"{BASE_URL}e/{EVENTO}/edit?tab=share", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(7000)
        page.screenshot(path=str(OUT / "01-aba-share.png"), full_page=True)

        # mapear cada linha da listagem de Concedidos
        info = page.evaluate(r"""() => {
            return Array.from(document.querySelectorAll('tr[data-item-id], tr[data-item-name]')).map(r => ({
                dataItemId: r.getAttribute('data-item-id'),
                dataItemName: r.getAttribute('data-item-name'),
                text: (r.innerText || '').slice(0, 300),
                actions: Array.from(r.querySelectorAll('button, a, [role="button"], .material-symbols-outlined'))
                    .map(el => ({tag: el.tagName, text: (el.innerText || '').trim().slice(0,40), cls: (el.className||'').toString().slice(0,150)})),
            }));
        }""")
        print("linhas de Concedidos:")
        for r in info:
            print(" data-item-id:", r["dataItemId"], "name:", r["dataItemName"])
            print(" text:", r["text"])
            print(" actions:", r["actions"])

        # focar na linha de DanteShare
        info_dant = page.evaluate(r"""() => {
            const re = /DanteShare/i;
            const row = Array.from(document.querySelectorAll('tr'))
                .find(r => re.test(r.innerText || '') && r.offsetParent !== null);
            if (!row) return null;
            return {
                dataItemId: row.getAttribute('data-item-id'),
                dataItemName: row.getAttribute('data-item-name'),
                text: (row.innerText || '').slice(0, 400),
                outerHTML: row.outerHTML.slice(0, 4000),
                spans: Array.from(row.querySelectorAll('span, button, [role="button"]')).map(el => ({
                    tag: el.tagName,
                    text: (el.innerText || '').trim().slice(0,40),
                    aria: el.getAttribute('aria-label') || '',
                    icon: el.getAttribute('data-icon') || '',
                    cls: (el.className||'').toString().slice(0,150),
                })),
            };
        }""")
        print("\n*** linha DanteShare ***")
        print(info_dant)

        # se houver action menu (3 dots ou similar), tentar clicar
        # icone tipico: more_vert, more_horiz, delete, edit
        clicou = page.evaluate(r"""() => {
            const re = /DanteShare/i;
            const row = Array.from(document.querySelectorAll('tr'))
                .find(r => re.test(r.innerText || ''));
            if (!row) return 'sem-row';
            // procurar icone de mais acoes ou trash
            const cand = Array.from(row.querySelectorAll('.material-symbols-outlined, span'))
                .find(el => /^(more_vert|more_horiz|delete|trash|edit|menu)$/.test((el.innerText || '').trim()));
            if (!cand) return 'sem-icone';
            let p = cand;
            for (let i = 0; i < 6 && p; i++) {
                if (p.tagName === 'BUTTON' || p.tagName === 'A' || p.onclick) break;
                p = p.parentElement;
            }
            (p || cand).click();
            return 'clicado: ' + (cand.innerText || '').trim();
        }""")
        print(f"\n[click action] {clicou}")
        page.wait_for_timeout(5000)
        page.screenshot(path=str(OUT / "02-action-aberto.png"), full_page=True)

        # se abriu menu/modal, mapear opcoes
        opcoes = page.evaluate(r"""() => {
            const data = {menu_items: [], buttons: []};
            document.querySelectorAll('[role="menuitem"], .chakra-menu__menuitem-option, [role="menu"]').forEach(el => {
                if (el.offsetParent !== null) data.menu_items.push((el.innerText || '').trim().slice(0,80));
            });
            // ou modal
            document.querySelectorAll('[role="dialog"] button').forEach(el => {
                if (el.offsetParent !== null) data.buttons.push((el.innerText || '').trim().slice(0,80));
            });
            return data;
        }""")
        print("\nopcoes apos clique:", opcoes)

        browser.close()


if __name__ == "__main__":
    main()
