"""Setup pré-T-1600: desmarca a marca d'água em ATIVIDADE_LEGADA_ID para simular
o estado de uma atividade legada (criada antes da feature de marca d'água).

ATENÇÃO: este setup deixa a atividade SEM marca d'água. Outros casos
(T-1595/T-1596/T-1597/T-1598) que exigem enabled=True têm seus próprios setup_t<N>.py
para re-habilitar. Sequência segura de execução:
    setup_t1600.py → pytest tests/marca_dagua/test_t1600_*.py
    setup_t1595.py → pytest tests/marca_dagua/test_t1595_*.py  (re-habilita)
"""
import os
import sys
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_EMAIL"]
PWD = os.environ["ADMIN_PASSWORD"]
EVENTO = os.environ.get("EVENTO_LEGADO_ID", os.environ["EVENTO_ID"])
ATIV = os.environ.get("ATIVIDADE_LEGADA_ID", os.environ["ATIVIDADE_VIDEO_MARCA_DAGUA_ID"])


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        page.goto(BASE + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(EMAIL)
        page.locator("#user_password").fill(PWD)
        page.locator("#user_submit").click()
        page.wait_for_load_state("domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)

        page.goto(f"{BASE}e/{EVENTO}/contents/{ATIV}/edit", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(8000)

        # Estado atual
        cb_input = page.locator("#water-mark-video-enabled")
        cb_label = page.locator("label.chakra-checkbox", has_text="Habilitar marca d'água no vídeo")
        antes_checked = bool(cb_label.get_attribute("data-checked") is not None)
        print(f"[setup-t1600] estado atual: checked={antes_checked}")

        if antes_checked:
            # Desmarcar: clica no label visual (input nativo eh hidden no Chakra)
            cb_label.scroll_into_view_if_needed()
            cb_label.click()
            page.wait_for_timeout(1500)
            print("[setup-t1600] checkbox clicado para desmarcar")
        else:
            print("[setup-t1600] ja estava desmarcado — nada a fazer")

        # Salvar (mesmo se ja desmarcado, salva pra garantir)
        save = page.locator("#button_send_form, button:has-text('Salvar')").first
        save.scroll_into_view_if_needed()
        save.click()
        page.wait_for_timeout(5000)
        print(f"[setup-t1600] salvou → url={page.url}")

        # Verificar estado final
        page.goto(f"{BASE}e/{EVENTO}/contents/{ATIV}/edit", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(7000)
        depois_checked = page.locator("label.chakra-checkbox", has_text="Habilitar marca d'água no vídeo").get_attribute("data-checked") is not None
        print(f"[verify] checkbox marca d'agua: checked={depois_checked}")
        assert not depois_checked, "Setup falhou — atividade ainda está com marca d'agua habilitada"

        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
