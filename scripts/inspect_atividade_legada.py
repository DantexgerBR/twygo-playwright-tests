"""Descobrir atividade de video 'legada' (marca d'agua nao habilitada) em algum
curso onde dante.tavares e admin+aluno. Output: lista (evento_id, atividade_id, titulo, config)."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pages.login_page import LoginPage  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
BASE_URL = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_EMAIL"]
SENHA = os.environ["ADMIN_PASSWORD"]
ORG = os.environ["ORG_ID"]
OUT = Path("test-results/inspect_atividade_legada")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        try:
            LoginPage(page).login(BASE_URL, EMAIL, SENHA)
        except Exception:
            # networkidle pode estourar timeout por causa do chat widget; o login ja
            # aconteceu — segue.
            page.wait_for_timeout(3000)

        # admin events listing (espera mais tempo — listagem carrega assincrona)
        page.goto(f"{BASE_URL}o/{ORG}/events?tab=events&profile=admin",
                  wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(15000)
        page.screenshot(path=str(OUT / "01-events-admin.png"), full_page=True)

        eventos = page.evaluate(r"""() => {
            // tentar varios padroes de listagem
            const candidatos = new Map();
            document.querySelectorAll('tr[data-item-id]').forEach(tr => {
                candidatos.set(tr.getAttribute('data-item-id'), tr.getAttribute('data-item-name') || '');
            });
            // fallback: cards/items com data-id
            document.querySelectorAll('[data-id]').forEach(el => {
                const id = el.getAttribute('data-id');
                if (!candidatos.has(id) && /^\d+$/.test(id)) {
                    candidatos.set(id, (el.innerText || '').trim().slice(0, 80));
                }
            });
            return Array.from(candidatos.entries()).map(([id, name]) => ({id, name}));
        }""")
        print(f"[1] eventos da org {ORG}: {len(eventos)}")
        for e in eventos: print(" ", e)

        # para cada evento, listar atividades e checar config marca d'agua
        candidatos_legados = []
        for e in eventos:
            try:
                page.goto(f"{BASE_URL}e/{e['id']}/contents", wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(6000)
                atividades = page.evaluate(r"""() => Array.from(document.querySelectorAll('li.dd-item[data-id]'))
                    .map(li => ({
                        id: li.getAttribute('data-id'),
                        title: li.getAttribute('data-title') || (li.innerText || '').trim().slice(0,80),
                    }))""")
                print(f"\n[2] evento {e['id']} ({e['name']}) — {len(atividades)} atividade(s):")
                for a in atividades:
                    try:
                        page.goto(f"{BASE_URL}e/{e['id']}/contents/{a['id']}/edit", wait_until="domcontentloaded", timeout=15000)
                        page.wait_for_timeout(5000)
                        cfg = page.evaluate("""() => {
                            const cb = document.querySelector('#water-mark-video-enabled');
                            if (!cb) return {nao_e_video: true};
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
                        print(f"   atividade {a['id']} ({a['title']!r}): {cfg}")
                        if cfg.get("enabled") is False:
                            candidatos_legados.append({
                                "evento_id": e["id"],
                                "evento_name": e["name"],
                                "atividade_id": a["id"],
                                "atividade_title": a["title"],
                                "config": cfg,
                            })
                    except Exception as ex:
                        print(f"   ! falhou abrir {a['id']}: {type(ex).__name__}")
            except Exception as ex:
                print(f" ! falhou abrir contents do evento {e['id']}: {type(ex).__name__}")

        print(f"\n[3] CANDIDATOS LEGADOS (enabled=False):")
        for c in candidatos_legados:
            print(" ", c)

        browser.close()


if __name__ == "__main__":
    main()
