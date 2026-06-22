"""tc3_conferir_empty_state.py — Loga como qa11tc342588, dispensa consentimento e captura empty state."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
TC3_EMAIL = "qa11tc342588@twygotest.com"
TC3_NOVA_SENHA = "twygoqa2026"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa11"
EVID.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg, flush=True)


def main():
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
            page.fill("#user_email", TC3_EMAIL)
            page.fill("#user_password", TC3_NOVA_SENHA)
            page.click("#user_submit")
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)
            log(f"URL pos login: {page.url[:80]}")

            if "/login" in page.url:
                log("Login falhou")
                tw.snap(page, EVID, "tc3_empty_login_falhou")
                return

            # Vai para Meu Historico
            page.goto(
                f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                wait_until="domcontentloaded",
            )
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(2000)

            # Dispensa modal de consentimento se presente
            try:
                btn_aceitar = page.get_by_role("button", name="Aceitar")
                if btn_aceitar.is_visible(timeout=3000):
                    log("Modal de consentimento detectado. Clicando em Aceitar...")
                    btn_aceitar.click()
                    page.wait_for_timeout(1500)
            except Exception:
                pass

            tw.dispensar_nps(page)
            page.wait_for_timeout(1000)

            tw.snap(page, EVID, "fechamento_tc3_empty_ok")
            log("Screenshot capturado: fechamento_tc3_empty_ok.png")

            # Verifica conteudo da pagina
            page_text = page.locator("body").inner_text()
            log(f"\nTexto da pagina (primeiros 500 chars):\n{page_text[:500]}")

            # Checa mensagens possiveis de empty state
            for msg in [
                "Você ainda não tem registros",
                "Adicione o primeiro",
                "Não há dados para exibir",
                "Nenhum registro",
                "sem registros",
            ]:
                found = msg.lower() in page_text.lower()
                log(f"  '{msg}': {'ENCONTRADO' if found else 'nao encontrado'}")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
