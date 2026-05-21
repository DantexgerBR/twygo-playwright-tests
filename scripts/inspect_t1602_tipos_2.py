"""Captura ícones/classes/data-* de cada atividade pra identificar o tipo
sem precisar abrir o form de edição de cada uma.

Foca no evento 787697 (Gestão para resultados) que parece o mais completo
em diversidade de conteúdos.
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_EMAIL"]
PWD = os.environ["ADMIN_PASSWORD"]

OUT = Path("test-results/inspect_t1602_tipos_2")
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

        # Tenta vários eventos pra cobrir diversidade
        for ev_id in ["787697", "787720", "787696"]:
            url = f"{BASE}e/{ev_id}/contents"
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(5000)
            page.screenshot(path=str(OUT / f"contents_{ev_id}.png"), full_page=True)

            info = page.evaluate(r"""() => {
                const items = Array.from(document.querySelectorAll('li.dd-item[data-id]'));
                return items.map(li => {
                    const dataId = li.getAttribute('data-id');
                    const title = li.getAttribute('data-title');
                    // ícones/classes dentro do item
                    const icons = Array.from(li.querySelectorAll('i, .material-symbols-outlined, [class*="icon"]'))
                        .map(i => ({tag: i.tagName, cls: i.className, text: (i.innerText||'').trim().slice(0, 30)}))
                        .slice(0, 6);
                    // imagem do tipo (alguns sistemas usam img)
                    const imgs = Array.from(li.querySelectorAll('img')).map(i => ({src: i.src, alt: i.alt})).slice(0, 3);
                    // tooltip / aria
                    const labelEl = li.querySelector('[aria-label], [title]');
                    const aria = labelEl ? {aria: labelEl.getAttribute('aria-label'), title: labelEl.getAttribute('title')} : null;
                    // outerHTML primeiros 600
                    const outer = li.outerHTML.slice(0, 600);
                    return {dataId, title, icons, imgs, aria, outer};
                });
            }""")
            print(f"\n========== Evento {ev_id} ==========")
            for it in info:
                print(f"id={it['dataId']:>10} title={it['title'][:40]:<40} icons={it['icons']} imgs={it['imgs']}")

            with open(OUT / f"event_{ev_id}.json", "w", encoding="utf-8") as f:
                json.dump(info, f, indent=2, ensure_ascii=False)

        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
