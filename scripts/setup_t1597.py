"""Setup pré-T-1597: garante marca d'água habilitada + Segurança='Visualizar e Baixar'.

Não toca em Tipo de Exibição/Posição (assume setup_t1595 já rodado).
"""
import os
import sys

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_EMAIL"]
PWD = os.environ["ADMIN_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]
ATIV = os.environ["ATIVIDADE_VIDEO_MARCA_DAGUA_ID"]

SEGURANCA_VISUALIZAR_E_BAIXAR = "2"  # 0=Somente Visualizar, 1=Somente Baixar, 2=Visualizar e Baixar


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
        page.wait_for_timeout(7000)

        # 1) Marca d'água continua ligada
        cb = page.get_by_label("Habilitar marca d'água no vídeo")
        cb.scroll_into_view_if_needed()
        if not cb.is_checked():
            try:
                cb.check(timeout=5000)
            except Exception:
                page.locator("text=Habilitar marca d'água no vídeo").first.click()
            page.wait_for_timeout(800)
        print(f"[setup] marca d'água habilitada: {cb.is_checked()}")

        # 2) Segurança: 'Visualizar e Baixar' (value=2)
        select_seguranca = page.locator("#content_file_security")
        select_seguranca.scroll_into_view_if_needed()
        select_seguranca.select_option(SEGURANCA_VISUALIZAR_E_BAIXAR)
        page.wait_for_timeout(500)
        valor_atual = select_seguranca.input_value()
        print(f"[setup] Segurança → {valor_atual} (esperado: {SEGURANCA_VISUALIZAR_E_BAIXAR})")

        # 3) Salvar
        page.locator("#button_send_form").click()
        page.wait_for_timeout(4000)
        print(f"[setup] salvou → URL: {page.url}")

        # Verificação: reabre o form
        page.goto(f"{BASE}e/{EVENTO}/contents/{ATIV}/edit", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(6000)
        cb2 = page.get_by_label("Habilitar marca d'água no vídeo")
        seg2 = page.locator("#content_file_security").input_value()
        print(f"[verify] marca d'água: {cb2.is_checked()}")
        print(f"[verify] Segurança: {seg2}")

        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
