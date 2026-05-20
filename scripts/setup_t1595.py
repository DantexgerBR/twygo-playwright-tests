"""Setup pré-T-1595: habilita marca d'água, tipo 'Em movimento', posição 'Sobre todo o vídeo'."""
import os, sys
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_EMAIL"]
PWD = os.environ["ADMIN_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]
ATIV = os.environ["ATIVIDADE_VIDEO_MARCA_DAGUA_ID"]


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

        # 1) Habilitar marca d'água
        cb = page.get_by_label("Habilitar marca d'água no vídeo")
        cb.scroll_into_view_if_needed()
        try:
            cb.check(timeout=5000)
        except Exception:
            # Fallback: clica no próprio label/checkbox
            page.locator("text=Habilitar marca d'água no vídeo").first.click()
        page.wait_for_timeout(1000)
        print(f"[setup] checkbox marca d'água → checked: {cb.is_checked()}")

        # 2) Tipo de exibição: Em movimento
        em_mov = page.get_by_label("Em movimento")
        em_mov.scroll_into_view_if_needed()
        try:
            em_mov.check(timeout=5000)
        except Exception:
            page.locator("text=Em movimento").first.click()
        page.wait_for_timeout(500)
        print(f"[setup] radio 'Em movimento' → checked: {em_mov.is_checked()}")

        # 3) Posição: remover atual e selecionar 'Sobre todo o vídeo'
        # Remove o tag atual clicando no X
        try:
            page.locator(".select-field__multi-value__remove[aria-label*='Lateral esquerda superior']").first.click(timeout=3000)
            page.wait_for_timeout(500)
        except Exception:
            print("[setup] não havia 'Lateral esquerda superior' pra remover (ok)")

        # Abre o select de posição clicando no controle perto do label "Posição"
        # O react-select tem um input com classe específica
        try:
            posicao_section = page.locator("text=Posição").first
            posicao_section.scroll_into_view_if_needed()
            # Clica no select-field (irmão/descendente do label Posição)
            page.evaluate("""() => {
                const label = Array.from(document.querySelectorAll('label, div, span, h3, h4'))
                    .find(el => el.tagName !== 'OPTION' && (el.innerText || '').trim() === 'Posição');
                if (label) {
                    const next = label.parentElement;
                    // Procura .select-field dentro do bloco
                    const sf = next ? next.querySelector('.select-field') : null;
                    if (sf) sf.click();
                }
            }""")
            page.wait_for_timeout(800)
            # Digita "Sobre todo" e seleciona
            page.keyboard.type("Sobre todo")
            page.wait_for_timeout(800)
            page.keyboard.press("Enter")
            page.wait_for_timeout(800)
            print("[setup] posição configurada (tentativa)")
        except Exception as e:
            print(f"[setup] falha ao configurar posição: {e}")

        # 4) Salvar
        page.locator("#button_send_form").click()
        page.wait_for_timeout(4000)
        print(f"[setup] salvou → URL: {page.url}")

        # Reabre pra verificar
        page.goto(f"{BASE}e/{EVENTO}/contents/{ATIV}/edit", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(6000)
        cb2 = page.get_by_label("Habilitar marca d'água no vídeo")
        em_mov2 = page.get_by_label("Em movimento")
        print(f"[verify] checkbox marca d'água: {cb2.is_checked()}")
        print(f"[verify] radio 'Em movimento': {em_mov2.is_checked()}")
        # Verifica posição via texto visível
        pos_text = page.locator(".select-field__multi-value__label").all_inner_texts()
        print(f"[verify] tags de posição visíveis: {pos_text}")

        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
