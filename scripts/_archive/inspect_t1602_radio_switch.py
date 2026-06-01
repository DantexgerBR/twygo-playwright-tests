"""Confirma que clicar no radio media_type re-renderiza o form de edição."""
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
ATIV = os.environ["ATIVIDADE_VIDEO_MARCA_DAGUA_ID"]

OUT = Path("test-results/inspect_t1602_switch")
OUT.mkdir(parents=True, exist_ok=True)

TIPOS = ["text", "page", "lesson", "pdf", "video", "external", "questions", "scorm", "games"]


def water_state(page) -> dict:
    return page.evaluate(r"""() => {
        const cb = document.querySelector('#water-mark-video-enabled');
        const visible = (el) => {
            if (!el) return false;
            const r = el.getBoundingClientRect();
            const cs = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none';
        };
        // pra checkbox Chakra, o input nativo é hidden — checa o label ancestral
        let labelVisible = false;
        if (cb) {
            const lbl = cb.closest('label.chakra-checkbox') || cb.parentElement;
            labelVisible = visible(lbl);
        }
        // Texto "Habilitar marca d'água no vídeo" presente em qualquer lugar visível?
        const textNodes = Array.from(document.querySelectorAll('label, p, span, div'))
            .filter(el => /Habilitar marca d['']água/i.test(el.innerText || ''))
            .filter(visible);
        return {
            cb_exists: !!cb,
            cb_label_visible: labelVisible,
            visible_text_nodes_count: textNodes.length,
        };
    }""")


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

        page.goto(f"{BASE}e/{EVENTO}/contents/{ATIV}/edit", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(7000)

        state_inicial = water_state(page)
        print(f"[initial=video] {state_inicial}")
        page.screenshot(path=str(OUT / "00-video-inicial.png"), full_page=True)

        for tipo in TIPOS:
            radio = page.locator(f"input[name='media_type'][value='{tipo}']").first
            if radio.count() == 0:
                print(f"[{tipo}] radio não encontrado")
                continue
            # label associado pelo id
            rid = radio.get_attribute("id")
            try:
                if rid:
                    lbl = page.locator(f"label[for='{rid}']").first
                    lbl.scroll_into_view_if_needed()
                    lbl.click()
                else:
                    radio.check(force=True, timeout=3000)
            except Exception as e:
                # fallback: JS direto
                radio.evaluate("r => { r.checked = true; r.dispatchEvent(new Event('change', {bubbles:true})); }")
            page.wait_for_timeout(3000)
            st = water_state(page)
            print(f"[{tipo}] {st}")
            page.screenshot(path=str(OUT / f"tipo_{tipo}.png"), full_page=True)

        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
