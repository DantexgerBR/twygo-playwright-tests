"""Ler config marca d'agua da atividade espelhada na destinataria (evento 806235)."""
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
EVENTO_DEST = "806235"
OUT = Path("test-results/inspect_destinataria_atividade")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        LoginPage(page).login(BASE_DEST, EMAIL, SENHA)
        page.goto(f"{BASE_DEST}o/{ORG_DEST}/events?tab=events&profile=admin",
                  wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(5000)

        # /e/806235/contents
        page.goto(f"{BASE_DEST}e/{EVENTO_DEST}/contents", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(8000)
        page.screenshot(path=str(OUT / "01-contents.png"), full_page=True)
        atividades = page.evaluate(r"""() => {
            return Array.from(document.querySelectorAll('li.dd-item[data-id]'))
                .map(li => ({
                    id: li.getAttribute('data-id'),
                    title: li.getAttribute('data-title') || (li.innerText || '').trim().slice(0,80),
                }));
        }""")
        print(f"atividades em /e/{EVENTO_DEST}/contents:")
        for a in atividades: print(" ", a)

        # ler config de cada atividade (procurando a de video com marca dagua)
        for a in atividades:
            page.goto(f"{BASE_DEST}e/{EVENTO_DEST}/contents/{a['id']}/edit", wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(7000)
            page.screenshot(path=str(OUT / f"02-ativ-{a['id']}.png"), full_page=True)
            cfg = page.evaluate("""() => {
                const cb = document.querySelector('#water-mark-video-enabled');
                if (!cb) return null;
                const lblCb = document.querySelector('label.chakra-checkbox');
                const identif = Array.from(document.querySelectorAll('input[name="identificationFields"]')).map(i => i.value);
                const fontSize = document.querySelector('#fontSize');
                const fontColor = document.querySelector('#water-mark-video-font-color');
                const fontPos = document.querySelector('input[name="fontPosition"]');
                const fontMovSelected = document.querySelector('input[name="fontMovement"]:checked');
                return {
                    enabled: cb.checked,
                    enabledLabelDataChecked: lblCb?.getAttribute('data-checked') ?? null,
                    identificationFields: identif,
                    fontSize: fontSize?.value || null,
                    fontColor: fontColor?.value || null,
                    fontPosition: fontPos?.value || null,
                    fontMovement: fontMovSelected?.value || null,
                };
            }""")
            print(f"\n*** atividade {a['id']} ({a['title']!r}) — config marca d'agua:")
            print("   ", cfg)

        browser.close()


if __name__ == "__main__":
    main()
