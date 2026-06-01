"""Clica 'Adicionar atividade' e mapeia o modal/fluxo para cada tipo."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_EMAIL"]
PWD = os.environ["ADMIN_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]

OUT = Path("test-results/inspect_t1602_modal")
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        page.goto(BASE + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(EMAIL)
        page.locator("#user_password").fill(PWD)
        page.locator("#user_submit").click()
        page.wait_for_load_state("domcontentloaded", timeout=20000)
        page.wait_for_timeout(2500)

        page.goto(f"{BASE}e/{EVENTO}/contents", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(5000)

        # Clica "Adicionar atividade"
        page.get_by_text("Adicionar atividade").first.click()
        page.wait_for_timeout(2500)
        page.screenshot(path=str(OUT / "01-pos-clique-add.png"), full_page=True)

        # Captura URL e qualquer dialog/modal
        print(f"url depois do click: {page.url}")
        modais = page.evaluate(r"""() => {
            const dialogs = Array.from(document.querySelectorAll('dialog, .modal, [role="dialog"], .simplemodal-data, .simplemodal-wrap'));
            return dialogs.map(d => ({
                cls: d.className, id: d.id,
                outer: d.outerHTML.slice(0, 600),
                text: (d.innerText || '').slice(0, 300),
            }));
        }""")
        print(f"modais: {len(modais)}")
        for m in modais[:5]:
            print(f"  · cls={m['cls']!r} id={m['id']!r} text={m['text'][:200]!r}")

        # Em geral o modal tem opções de tipo. Lista links/buttons dentro.
        opcoes = page.evaluate(r"""() => {
            // procura cards visíveis com texto de tipo
            const wantedTexts = ['Texto', 'Página', 'Aula', 'Vídeo', 'PDF', 'Questionário', 'SCORM', 'Games', 'Vídeo Externo'];
            const out = [];
            for (const el of document.querySelectorAll('a, button, [role="button"], [data-media-type], [data-type]')) {
                const t = (el.innerText || '').trim();
                if (!t || t.length > 60) continue;
                for (const w of wantedTexts) {
                    if (t === w || t.toLowerCase().includes(w.toLowerCase())) {
                        out.push({
                            tag: el.tagName, text: t,
                            href: el.href || null,
                            id: el.id,
                            'data-media-type': el.getAttribute('data-media-type'),
                            'data-type': el.getAttribute('data-type'),
                            cls: el.className.slice(0, 80),
                        });
                        break;
                    }
                }
            }
            return out;
        }""")
        print(f"\nopções de tipo encontradas: {len(opcoes)}")
        for o in opcoes:
            print(f"  · text={o['text']!r} href={o.get('href')} id={o.get('id')} dmt={o.get('data-media-type')} dt={o.get('data-type')} cls={o.get('cls')}")

        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
