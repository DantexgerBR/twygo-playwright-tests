"""Setup pré-T-1601: habilita marca d'água em 9280032 e configura a cor da fonte
com 0% de transparência (totalmente transparente) — hex `#FFFFFF00`.

ATENÇÃO: deixa a atividade 9280032 com marca habilitada + cor totalmente transparente.
Casos seguintes que esperam cor opaca devem rerodar seu próprio setup_t<N>.py.
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

COR_TRANSPARENTE = "#FFFFFF00"  # RGB branco + alpha=00 (totalmente transparente)


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        page.goto(BASE + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(EMAIL)
        page.locator("#user_password").fill(PWD)
        page.locator("#user_submit").click()
        page.wait_for_load_state("domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)

        page.goto(f"{BASE}e/{EVENTO}/contents/{ATIV}/edit", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(8000)

        # 1) Habilita marca d'água
        cb = page.get_by_label("Habilitar marca d'água no vídeo")
        cb.scroll_into_view_if_needed()
        if not cb.is_checked():
            try:
                cb.check(timeout=5000)
            except Exception:
                page.locator("text=Habilitar marca d'água no vídeo").first.click()
            page.wait_for_timeout(1500)
        print(f"[setup-t1601] marca d'agua habilitada: {cb.is_checked()}")

        # 2) Cor da fonte totalmente transparente
        inp = page.locator("#water-mark-video-font-color")
        inp.scroll_into_view_if_needed()
        inp.click()
        inp.fill("")
        inp.fill(COR_TRANSPARENTE)
        inp.press("Tab")
        page.wait_for_timeout(800)
        print(f"[setup-t1601] cor fonte → {inp.input_value()}")

        # 3) Salvar
        page.locator("#button_send_form").click()
        page.wait_for_timeout(5000)
        print(f"[setup-t1601] salvou → url={page.url}")

        # 4) Verificação: reabre form
        page.goto(f"{BASE}e/{EVENTO}/contents/{ATIV}/edit", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(7000)
        cb2 = page.get_by_label("Habilitar marca d'água no vídeo")
        cor_final = page.locator("#water-mark-video-font-color").input_value()
        print(f"[verify] marca enabled={cb2.is_checked()}, cor={cor_final}")

        # Tolerante: o backend pode normalizar pra lowercase ou ordem dos chars.
        # Exige que os últimos 2 chars (alpha) sejam 00.
        alpha_chars = cor_final.replace("#", "").upper()[-2:]
        assert cb2.is_checked(), "Setup falhou — marca d'agua nao habilitada"
        assert alpha_chars == "00", f"Setup falhou — alpha esperado=00, recebido={alpha_chars} (cor={cor_final})"

        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
