"""Setup pré-T-1596: marca d'água habilitada com Informações = CPF + E-mail, posição 'Sobre todo o vídeo'."""
import os, sys
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

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
        page.wait_for_timeout(8000)

        # 1) Estado do checkbox via JS (independente de label association)
        estado = page.evaluate("""() => {
            const all = Array.from(document.querySelectorAll('input[type="checkbox"]'));
            // Procura um checkbox cujo texto vizinho contenha 'Habilitar marca d'água'
            for (const cb of all) {
                const parent = cb.parentElement;
                const txt = parent ? (parent.innerText || '').trim() : '';
                if (/Habilitar marca d.água no vídeo/i.test(txt)) {
                    return {found: true, checked: cb.checked, id: cb.id, name: cb.name};
                }
            }
            return {found: false};
        }""")
        print(f"[setup] estado inicial checkbox: {estado}")
        if estado.get("found") and not estado.get("checked"):
            # clica no label vizinho
            page.locator("text=Habilitar marca d'água no vídeo").first.click()
            page.wait_for_timeout(700)
            print("[setup] clicou pra habilitar")

        # 2) Adiciona "E-mail" às Informações (mantém CPF)
        tags_antes = page.locator(".select-field__multi-value__label").all_inner_texts()
        print(f"[setup] tags antes: {tags_antes}")
        if "E-mail" not in tags_antes:
            # Localiza o select-field__control cujo texto é exatamente 'CPF' (campo Informações).
            # O do "Posição" tem texto 'Sobre todo o vídeo', então :has-text('CPF') deve isolar Informações.
            infos = page.locator(".select-field__control", has_text="CPF").first
            infos.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            infos.click()
            page.wait_for_timeout(1200)
            # Confirma que o dropdown abriu (presença de .select-field__menu)
            menu_aberto = page.locator(".select-field__menu, [class*='select-field__menu']").count()
            print(f"[setup] menu dropdown aberto: {menu_aberto > 0}")
            page.keyboard.type("E-mail")
            page.wait_for_timeout(900)
            page.keyboard.press("Enter")
            page.wait_for_timeout(900)
            # Fecha o dropdown clicando fora
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        tags_apos = page.locator(".select-field__multi-value__label").all_inner_texts()
        print(f"[setup] tags após: {tags_apos}")

        # 3) Salvar
        page.locator("#button_send_form").click()
        page.wait_for_timeout(4500)
        print(f"[setup] salvou → URL: {page.url}")

        # 4) Verificar
        page.goto(f"{BASE}e/{EVENTO}/contents/{ATIV}/edit", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(7000)
        tags_final = page.locator(".select-field__multi-value__label").all_inner_texts()
        cb_final = page.evaluate("""() => {
            const all = Array.from(document.querySelectorAll('input[type="checkbox"]'));
            for (const cb of all) {
                const parent = cb.parentElement;
                const txt = parent ? (parent.innerText || '').trim() : '';
                if (/Habilitar marca d.água no vídeo/i.test(txt)) return cb.checked;
            }
            return null;
        }""")
        print(f"[verify] checkbox marca d'água: {cb_final}")
        print(f"[verify] tags finais: {tags_final}")

        browser.close()
        ok = bool(cb_final) and "CPF" in tags_final and "E-mail" in tags_final and "Sobre todo o vídeo" in tags_final
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
