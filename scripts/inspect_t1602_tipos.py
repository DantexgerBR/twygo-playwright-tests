"""Lista todos os eventos da org e, para cada um, todos os contents com seu tipo.

Objetivo: identificar atividades dos tipos pedidos por T-1602:
Texto, Página, Aula, PDF estampado, Vídeo Externo, Questionário, Scorm, Games.
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
ORG = os.environ["ORG_ID"]

OUT = Path("test-results/inspect_t1602_tipos")
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

        page.goto(
            f"{BASE}o/{ORG}/events?tab=events&profile=admin",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        page.wait_for_timeout(6000)
        page.screenshot(path=str(OUT / "01-eventos.png"), full_page=True)

        # Extrai eventos pela tabela: tr[data-item-id, data-item-name]
        eventos = page.evaluate(r"""() => {
            return Array.from(document.querySelectorAll('tr[data-item-id]')).map(tr => ({
                id: tr.getAttribute('data-item-id'),
                name: tr.getAttribute('data-item-name'),
            }));
        }""")
        print(f"== eventos encontrados ({len(eventos)}) ==")
        for e in eventos:
            print(f"  - {e['id']} :: {e['name']}")

        all_contents = []
        for ev in eventos:
            ev_id = ev["id"]
            url = f"{BASE}e/{ev_id}/contents"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
            except Exception as e:
                print(f"  [warn] goto falhou em evento {ev_id}: {e}")
                continue
            page.wait_for_timeout(4000)
            # Cada li.dd-item tem data-id e data-type/data-media-type ou texto descritivo
            contents = page.evaluate(r"""() => {
                return Array.from(document.querySelectorAll('li.dd-item[data-id]')).map(li => {
                    const data = {};
                    for (const a of li.attributes) data[a.name] = a.value;
                    // texto curto (título + tipo)
                    const t = (li.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200);
                    return {data, text: t};
                });
            }""")
            for c in contents:
                c["evento_id"] = ev_id
                c["evento_nome"] = ev["name"]
            all_contents.extend(contents)

        with open(OUT / "all_contents.json", "w", encoding="utf-8") as f:
            json.dump(all_contents, f, indent=2, ensure_ascii=False)

        # Resumo: agrupa por tipo via heurística no texto
        print(f"\n== total de contents listados: {len(all_contents)} ==")
        for c in all_contents:
            data_id = c["data"].get("data-id")
            print(f"  ev={c['evento_id']:>6} | id={data_id:>10} | text={c['text'][:140]}")

        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
