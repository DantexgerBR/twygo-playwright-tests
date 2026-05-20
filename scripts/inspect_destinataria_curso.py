"""Achar o ID do evento espelhado na destinataria e ler a config de marca d'agua da atividade."""
import os
import sys
import time
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
OUT = Path("test-results/inspect_destinataria_curso")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        LoginPage(page).login(BASE_DEST, EMAIL, SENHA)
        page.goto(f"{BASE_DEST}o/{ORG_DEST}/events?tab=events&profile=admin",
                  wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(7000)
        page.screenshot(path=str(OUT / "01-events.png"), full_page=True)

        # mapear a linha com 'Construindo times' e capturar URL/data-id
        info = page.evaluate(r"""() => {
            const re = /Construindo times de alta performance/i;
            const data = {by_anchor: [], by_row: []};
            // (a) qualquer <a> com texto do curso
            Array.from(document.querySelectorAll('a')).forEach(a => {
                if (re.test(a.innerText || '') && a.offsetParent !== null) {
                    data.by_anchor.push({href: a.getAttribute('href'), text: (a.innerText || '').trim().slice(0,80)});
                }
            });
            // (b) qualquer tr/li/[data-id] com texto do curso — extrair data-id
            Array.from(document.querySelectorAll('tr, li, [data-id]')).forEach(el => {
                if (re.test(el.innerText || '') && el.offsetParent !== null) {
                    data.by_row.push({
                        tag: el.tagName,
                        dataId: el.getAttribute('data-id'),
                        cls: (el.className || '').toString().slice(0, 150),
                        outerHTML: el.outerHTML.slice(0, 800),
                    });
                }
            });
            return data;
        }""")
        print("anchors:", info["by_anchor"])
        print("\nrows (top 3):")
        for r in info["by_row"][:3]: print(" ", r)

        # tentar clicar na linha do curso para capturar URL final
        try:
            # busca: row inteira ou cell com o texto, capturar href via clique
            page.evaluate(r"""() => {
                const re = /Construindo times de alta performance/i;
                const el = Array.from(document.querySelectorAll('a, button, [role="button"], td, tr'))
                    .find(x => re.test(x.innerText || '') && x.offsetParent !== null);
                if (el) el.click();
            }""")
            page.wait_for_timeout(7000)
            print(f"\nURL apos clicar no curso: {page.url}")
            page.screenshot(path=str(OUT / "02-curso-aberto.png"), full_page=True)
        except Exception as e:
            print("falha click:", e)

        # se conseguimos uma URL /e/{id}, capturar
        m = page.url.split("/e/")[-1].split("/")[0] if "/e/" in page.url else None
        if not m:
            print("!! nao consegui evento_id pela URL. Tentando capturar via api de eventos.")
            # tentar a API GraphQL/REST do Twygo via networking
            return
        evento_dest_id = m
        print(f"\n[evento destinataria] id = {evento_dest_id}")

        # 2) navegar para /e/{id}/contents
        page.goto(f"{BASE_DEST}e/{evento_dest_id}/contents", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(8000)
        page.screenshot(path=str(OUT / "03-contents.png"), full_page=True)
        atividades = page.evaluate(r"""() => {
            return Array.from(document.querySelectorAll('li.dd-item[data-id]'))
                .map(li => ({
                    id: li.getAttribute('data-id'),
                    title: li.getAttribute('data-title') || (li.innerText || '').trim().slice(0,80),
                }));
        }""")
        print(f"\natividades em /e/{evento_dest_id}/contents:")
        for a in atividades: print(" ", a)

        # 3) tentar abrir a atividade de video (titulo bate com origem)
        # A atividade origem deve ter um titulo conhecido — vamos tentar todas
        for a in atividades:
            page.goto(f"{BASE_DEST}e/{evento_dest_id}/contents/{a['id']}/edit", wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(7000)
            page.screenshot(path=str(OUT / f"04-ativ-{a['id']}.png"), full_page=True)
            # ler config marca d'agua
            cfg = page.evaluate("""() => {
                const cb = document.querySelector('#water-mark-video-enabled');
                if (!cb) return null;
                const identif = Array.from(document.querySelectorAll('input[name="identificationFields"]')).map(i => i.value);
                const fontSize = document.querySelector('#fontSize');
                const fontColor = document.querySelector('#water-mark-video-font-color');
                const fontPos = document.querySelector('input[name="fontPosition"]');
                const fontMovSelected = document.querySelector('input[name="fontMovement"]:checked');
                return {
                    enabled: cb.checked,
                    identificationFields: identif,
                    fontSize: fontSize?.value || null,
                    fontColor: fontColor?.value || null,
                    fontPosition: fontPos?.value || null,
                    fontMovement: fontMovSelected?.value || null,
                };
            }""")
            if cfg:
                print(f"\natividade {a['id']} (titulo: {a['title']}): config marca d'agua = {cfg}")
            else:
                print(f"\natividade {a['id']}: nao parece ser de video (sem checkbox marca dagua)")

        browser.close()


if __name__ == "__main__":
    main()
