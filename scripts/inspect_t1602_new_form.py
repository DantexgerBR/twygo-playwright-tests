"""Acessa /e/{evento}/contents/new (form de criar atividade) e mostra a URL real,
testa clicar em cada radio media_type e checa se #water-mark-video-enabled aparece.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_EMAIL"]
PWD = os.environ["ADMIN_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]  # 787696

OUT = Path("test-results/inspect_t1602_new")
OUT.mkdir(parents=True, exist_ok=True)

TIPOS = ["text", "page", "lesson", "pdf", "video", "external", "other", "questions", "scorm", "games"]


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

        # Tenta URL de criar
        for path in [f"e/{EVENTO}/contents/new", f"events/{EVENTO}/contents/new"]:
            url = BASE + path
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(5000)
                final = page.url
                print(f"[try] {url} → {final} status_title={page.title()}")
                if "new" in final or "edit" in final:
                    break
            except Exception as e:
                print(f"[err] {url}: {e}")

        page.screenshot(path=str(OUT / "new-form.png"), full_page=True)

        # Lista os radios media_type encontrados
        radios = page.evaluate(r"""() => {
            return Array.from(document.querySelectorAll('input[name="media_type"]')).map(r => ({
                value: r.value, id: r.id, checked: r.checked,
                labelText: r.id ? (document.querySelector(`label[for='${r.id}']`)?.innerText || '').trim() : null,
            }));
        }""")
        print(f"\nradios media_type encontrados:")
        for r in radios:
            print(f"  - value={r['value']:<12} id={r['id']:<20} label={r['labelText']!r}")

        for tipo in TIPOS:
            try:
                # Clica no radio do tipo
                radio = page.locator(f"input[name='media_type'][value='{tipo}']").first
                if radio.count() == 0:
                    print(f"[{tipo}] radio não existe nesse form")
                    continue
                radio.scroll_into_view_if_needed()
                # input nativo pode ser hidden — clicar no label associado
                try:
                    radio.check(timeout=3000)
                except Exception:
                    rid = radio.get_attribute("id")
                    if rid:
                        lbl = page.locator(f"label[for='{rid}']").first
                        lbl.click()
                page.wait_for_timeout(2500)

                has_water = page.locator("#water-mark-video-enabled").count() > 0
                water_visible = page.locator("#water-mark-video-enabled").is_visible() if has_water else False
                # Texto "Habilitar marca d'água no vídeo" presente?
                lbl_count = page.get_by_text("Habilitar marca d'água no vídeo").count()
                print(f"[{tipo}] water-checkbox count={has_water} visible={water_visible} label_count={lbl_count}")
                page.screenshot(path=str(OUT / f"tipo_{tipo}.png"), full_page=True)
            except Exception as e:
                print(f"[{tipo}] erro: {e}")

        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
