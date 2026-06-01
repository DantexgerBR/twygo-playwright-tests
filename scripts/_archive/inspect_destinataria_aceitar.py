"""Achar o botao 'editar' do share recebido e descobrir o fluxo de aceitacao."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pages.login_page import LoginPage  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
BASE_DEST = os.environ["BASE_URL_DESTINATARIA"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_DESTINATARIA_EMAIL"]
SENHA = os.environ["ADMIN_DESTINATARIA_PASSWORD"]
ORG_DEST = os.environ["ORG_DESTINATARIA_ID"]
OUT = Path("test-results/inspect_destinataria_aceitar")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        LoginPage(page).login(BASE_DEST, EMAIL, SENHA)
        page.goto(f"{BASE_DEST}o/{ORG_DEST}/events?tab=events&profile=admin",
                  wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(6000)

        page.goto(f"{BASE_DEST}o/{ORG_DEST}/shared_events", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(6000)
        # tab Recebidos
        page.evaluate(r"""() => {
            const t = Array.from(document.querySelectorAll('button[role="tab"], .chakra-tabs__tab'))
                .find(el => (el.innerText || '').trim() === 'Recebidos');
            if (t) t.click();
        }""")
        page.wait_for_timeout(5000)
        page.screenshot(path=str(OUT / "01-recebidos.png"), full_page=True)

        # mapear ALL buttons/icons na linha do share recebido
        info = page.evaluate(r"""() => {
            const rows = Array.from(document.querySelectorAll('tr, [role=row]'))
                .filter(r => /Construindo times de alta performance/i.test(r.innerText || ''));
            if (!rows.length) return null;
            const row = rows[0];
            const actions = Array.from(row.querySelectorAll('button, a, [role="button"], svg, .material-symbols-outlined, [aria-label]'))
                .map(el => ({
                    tag: el.tagName,
                    text: (el.innerText || '').trim().slice(0,60),
                    aria: el.getAttribute('aria-label') || '',
                    title: el.getAttribute('title') || '',
                    href: el.getAttribute('href'),
                    onclick: (el.getAttribute('onclick') || '').slice(0,200),
                    cls: (el.className || '').toString().slice(0, 200),
                }));
            return {row_text: (row.innerText || '').slice(0,400), actions};
        }""")
        print("linha do share recebido:")
        if info:
            print("text:", info["row_text"])
            print("\nacoes encontradas na linha:")
            for a in info["actions"]: print(" ", a)
        else:
            print("!! linha nao encontrada")

        # clicar no icone de edit (pencil) — span com text 'edit', subir ate o ancestral clickable
        clicou = page.evaluate(r"""() => {
            const rows = Array.from(document.querySelectorAll('tr, [role=row]'))
                .filter(r => /Construindo times de alta performance/i.test(r.innerText || ''));
            if (!rows.length) return 'sem-linha';
            const row = rows[0];
            const editIcon = Array.from(row.querySelectorAll('.material-symbols-outlined, span'))
                .find(el => (el.innerText || '').trim() === 'edit');
            if (!editIcon) return 'sem-icone';
            // achar o ancestral clickable (button, a, role=button)
            let p = editIcon;
            for (let i = 0; i < 6 && p; i++) {
                if (p.tagName === 'BUTTON' || p.tagName === 'A' || p.getAttribute('role') === 'button' || p.onclick) break;
                p = p.parentElement;
            }
            if (!p) p = editIcon;
            const desc = p.tagName + ' cls=' + (p.className || '').toString().slice(0,80) + ' onclick=' + (p.onclick ? 'yes' : 'no');
            p.click();
            return 'clicado: ' + desc;
        }""")
        print(f"\nclick: {clicou}")
        page.wait_for_timeout(6000)
        page.screenshot(path=str(OUT / "02-pos-click-edit.png"), full_page=True)
        print("url apos click:", page.url)

        # mapear o que apareceu (modal ou nova pagina)
        info2 = page.evaluate(r"""() => {
            const dialogs = Array.from(document.querySelectorAll('[role="dialog"], .chakra-modal__content'));
            const data = {dialogs: [], buttons: [], inputs: []};
            data.dialogs = dialogs.map(d => ({
                cls: (d.className || '').toString().slice(0,150),
                header: d.querySelector('header, h2, .chakra-modal__header')?.innerText?.trim()?.slice(0,200) || '',
                text: (d.innerText || '').slice(0,1500),
            }));
            document.querySelectorAll('button, a').forEach(el => {
                if (el.offsetParent === null) return;
                const t = (el.innerText || '').trim();
                if (t && t.length < 40) data.buttons.push({tag: el.tagName, text: t, id: el.id});
            });
            document.querySelectorAll('input:not([type=hidden])').forEach(el => {
                if (el.offsetParent === null) return;
                data.inputs.push({type: el.type, name: el.name, id: el.id, value: el.value, ph: el.placeholder});
            });
            return data;
        }""")
        print("\nmodais visiveis:", len(info2["dialogs"]))
        for d in info2["dialogs"]:
            print(" header:", d["header"])
            print(" text:")
            print(d["text"])
        print("\nbotoes visiveis (limit 25):")
        for b in info2["buttons"][:25]: print(" ", b)

        browser.close()


if __name__ == "__main__":
    main()
