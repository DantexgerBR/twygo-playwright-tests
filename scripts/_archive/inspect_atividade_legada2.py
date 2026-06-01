"""Verificar atividades nos eventos 787696 e 787697 e ver quais sao 'legadas'."""
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
OUT = Path("test-results/inspect_atividade_legada2")
OUT.mkdir(parents=True, exist_ok=True)

EVENTOS = [
    ("787696", "Construindo times de alta performance"),
    ("787697", "Gestão para resultados"),
]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        page = ctx.new_page()
        try:
            LoginPage(page).login(BASE_URL, EMAIL, SENHA)
        except Exception:
            page.wait_for_timeout(3000)

        candidatos_legados = []
        candidatos_com_marca = []

        for ev_id, ev_name in EVENTOS:
            try:
                page.goto(f"{BASE_URL}e/{ev_id}/contents", wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(7000)
                page.screenshot(path=str(OUT / f"01-contents-{ev_id}.png"), full_page=True)
                atividades = page.evaluate(r"""() => Array.from(document.querySelectorAll('li.dd-item[data-id]'))
                    .map(li => ({
                        id: li.getAttribute('data-id'),
                        title: li.getAttribute('data-title') || (li.innerText || '').trim().slice(0,80),
                    }))""")
                print(f"\n[{ev_id} - {ev_name}] {len(atividades)} atividade(s):")
                for a in atividades:
                    try:
                        try:
                            page.goto(f"{BASE_URL}e/{ev_id}/contents/{a['id']}/edit", wait_until="networkidle", timeout=20000)
                        except Exception:
                            pass  # networkidle pode estourar — segue com domcontentloaded estado
                        page.wait_for_timeout(8000)
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
                        item = {"evento_id": ev_id, "evento_name": ev_name, "atividade_id": a["id"], "atividade_title": a["title"], "config": cfg}
                        if cfg.get("nao_e_video"):
                            continue
                        if cfg.get("enabled") is False:
                            candidatos_legados.append(item)
                        else:
                            candidatos_com_marca.append(item)
                    except Exception as ex:
                        print(f"   ! falhou abrir edit da atividade {a['id']}: {type(ex).__name__}")
            except Exception as ex:
                print(f" ! falhou abrir contents do evento {ev_id}: {type(ex).__name__}")

        print(f"\n=== LEGADOS (enabled=False): {len(candidatos_legados)} ===")
        for c in candidatos_legados: print(" ", c)
        print(f"\n=== COM MARCA (enabled=True): {len(candidatos_com_marca)} ===")
        for c in candidatos_com_marca: print(" ", c)

        browser.close()


if __name__ == "__main__":
    main()
