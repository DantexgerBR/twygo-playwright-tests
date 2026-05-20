"""Apos a origem enviar share, encontrar curso espelhado na destinataria.

Caminhos a verificar:
1. /o/{ORG_DEST}/shared_events tab 'Recebidos'
2. /o/{ORG_DEST}/events (listagem geral de conteudos)
3. Tentar localizar a atividade de video e ler config de marca d'agua
"""
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
OUT = Path("test-results/inspect_destinataria_recebidos")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        LoginPage(page).login(BASE_DEST, EMAIL, SENHA)

        # Switch profile -> Admin
        page.goto(f"{BASE_DEST}o/{ORG_DEST}/events?tab=events&profile=admin",
                  wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(7000)
        page.screenshot(path=str(OUT / "01-admin-events.png"), full_page=True)

        # 1) /o/{ORG_DEST}/shared_events
        page.goto(f"{BASE_DEST}o/{ORG_DEST}/shared_events", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(6000)
        page.screenshot(path=str(OUT / "02-shared_events-concedidos.png"), full_page=True)

        # clicar na aba "Recebidos"
        clicou = page.evaluate(r"""() => {
            const t = Array.from(document.querySelectorAll('button[role="tab"], .chakra-tabs__tab'))
                .find(el => (el.innerText || '').trim() === 'Recebidos' && el.offsetParent !== null);
            if (t) { t.click(); return true; }
            return false;
        }""")
        print(f"[click Recebidos] {clicou}")
        page.wait_for_timeout(6000)
        page.screenshot(path=str(OUT / "03-shared_events-recebidos.png"), full_page=True)

        # mapear conteudo recebido na tabela
        info = page.evaluate(r"""() => {
            const rows = Array.from(document.querySelectorAll('tr, [role=row]'))
                .filter(el => el.offsetParent !== null);
            return rows.slice(0, 30).map(r => ({
                text: (r.innerText || '').slice(0, 400),
                html: r.outerHTML.slice(0, 2000),
            }));
        }""")
        print("\nlinhas da tabela Recebidos:")
        for i, r in enumerate(info):
            if r["text"].strip():
                print(f"--- linha {i} ---")
                print(r["text"])

        # 2) Lista de cursos da destinataria
        page.goto(f"{BASE_DEST}o/{ORG_DEST}/events?tab=events", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(8000)
        page.screenshot(path=str(OUT / "04-events-lista.png"), full_page=True)
        eventos = page.evaluate(r"""() => {
            const data = [];
            document.querySelectorAll('[data-id], a[href*="/e/"]').forEach(el => {
                const dataId = el.getAttribute('data-id') || (el.href || '').match(/\/e\/(\d+)/)?.[1];
                if (!dataId) return;
                const text = (el.innerText || '').trim().slice(0,120);
                data.push({id: dataId, text, href: el.getAttribute('href')});
            });
            // dedup
            const seen = new Set();
            return data.filter(d => {
                if (seen.has(d.id)) return false;
                seen.add(d.id);
                return true;
            });
        }""")
        print("\neventos visiveis na destinataria:")
        for e in eventos: print(" ", e)

        # 3) Procurar curso "Construindo times de alta performance"
        candidato = page.evaluate(r"""() => {
            const re = /Construindo times de alta performance/i;
            const els = Array.from(document.querySelectorAll('a[href*="/e/"], [data-id]'))
                .filter(el => re.test(el.innerText || '') || re.test(el.title || ''));
            return els.slice(0,5).map(el => ({
                text: (el.innerText || '').trim().slice(0,120),
                href: el.getAttribute('href'),
                dataId: el.getAttribute('data-id'),
            }));
        }""")
        print("\ncandidatos curso 'Construindo times de alta performance':")
        for c in candidato: print(" ", c)

        # 4) Se encontrou, abrir /e/{id}/contents pra listar atividades
        if candidato:
            href = candidato[0]["href"] or ""
            m = href.split("/e/")[-1].split("/")[0] if "/e/" in href else candidato[0]["dataId"]
            evento_dest_id = m
            print(f"\n[evento destinataria] id = {evento_dest_id}")
            page.goto(f"{BASE_DEST}e/{evento_dest_id}/contents", wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(7000)
            page.screenshot(path=str(OUT / "05-curso-destinataria-contents.png"), full_page=True)
            atividades = page.evaluate(r"""() => {
                return Array.from(document.querySelectorAll('li.dd-item[data-id]'))
                    .map(li => ({
                        id: li.getAttribute('data-id'),
                        title: li.getAttribute('data-title') || (li.innerText || '').trim().slice(0,80),
                    }));
            }""")
            print("\natividades do curso destinataria:")
            for a in atividades: print(" ", a)

        browser.close()


if __name__ == "__main__":
    main()
