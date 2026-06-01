"""Inspeciona o(s) botão(s) de adicionar atividade em /e/{evento}/contents."""
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
EVENTO = os.environ["EVENTO_ID"]

OUT = Path("test-results/inspect_t1602_add")
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
        page.screenshot(path=str(OUT / "lista.png"), full_page=True)

        # Lista botões/links com texto adicionar/novo/criar
        candidates = page.evaluate(r"""() => {
            const matches = [];
            for (const el of document.querySelectorAll('a, button, [role="button"]')) {
                const t = (el.innerText || '').trim();
                const aria = el.getAttribute('aria-label') || '';
                if (/adicionar|novo|nova|criar|add/i.test(t + ' ' + aria)) {
                    matches.push({
                        tag: el.tagName, text: t.slice(0, 80),
                        href: el.href || null,
                        id: el.id, cls: el.className,
                        aria, outer: el.outerHTML.slice(0, 300),
                    });
                }
            }
            return matches;
        }""")
        print(f"\n== {len(candidates)} candidatos ==")
        for c in candidates[:40]:
            print(f"  {c['tag']} text={c['text']!r} href={c['href']} id={c['id']!r} aria={c['aria']!r}")

        # Tenta clicar no botão de adicionar atividade e ver pra onde vai (sem submeter)
        # Alguns simplemodal abrem dialog inline ao invés de navegar.
        with open(OUT / "candidates.json", "w", encoding="utf-8") as f:
            json.dump(candidates, f, indent=2, ensure_ascii=False)

        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
