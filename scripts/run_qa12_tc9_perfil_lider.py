"""run_qa12_tc9_perfil_lider.py — Inspeção do perfil do líder
Verifica se o lider tem seletor de perfil (Colaborador/Gestor/Admin)
e testa acessar Registros no perfil de Gestor/Colaborador.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID   = "37079"
LIDER_EMAIL    = "qalider@teste.com"
LIDER_PASSWORD = "123456"
RECORDS_URL = f"{BASE_URL}/o/{ORG_ID}/records"

SLUG = "registros-f2-qa12"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)


def suprimir_sophia(page):
    page.evaluate("""
        () => {
            ['#hubspot-messages-iframe-container', '[id*="sophia"]', '[id*="hubspot"]']
            .forEach(s => document.querySelectorAll(s).forEach(e => e.style.display='none'));
        }
    """)


def run():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=300)
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        page = ctx.new_page()

        # Login como lider
        print(f"[Login] Como {LIDER_EMAIL}...")
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("#user_email", timeout=10000)
        page.fill("#user_email", LIDER_EMAIL)
        page.fill("#user_password", LIDER_PASSWORD)
        page.click("#user_submit")
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        page.wait_for_timeout(3000)
        tw.dispensar_nps(page)

        print(f"[Login] URL: {page.url}")
        tw.snap(page, EVID, "tc9p_01_dashboard_lider")

        # Inspecionar botão de perfil no header
        print("[Perfil] Procurando botão de perfil no header...")
        perfil_btn = page.locator("button[aria-label*='perfil'], button[aria-haspopup='menu']").first
        if perfil_btn.count() == 0:
            # Tenta o botão que mostra "Administrador" / "Colaborador"
            perfil_btn = page.locator("button:has-text('Administrador')").first
        if perfil_btn.count() == 0:
            perfil_btn = page.locator("button:has-text('Colaborador')").first
        if perfil_btn.count() == 0:
            # Tenta o dropdown no canto superior direito
            perfil_btn = page.locator("header button, nav button").last

        print(f"[Perfil] Botão encontrado: {perfil_btn.count() > 0}")
        if perfil_btn.count() > 0:
            perfil_btn.click()
            page.wait_for_timeout(1500)
            tw.snap(page, EVID, "tc9p_02_dropdown_perfil")

            # Listar opções do dropdown
            opcoes = page.locator("[role='menu'] [role='menuitem'], [role='listbox'] [role='option']").all()
            print(f"[Perfil] Opções no dropdown: {len(opcoes)}")
            for opcao in opcoes:
                try:
                    print(f"  - {opcao.inner_text()}")
                except Exception:
                    pass

            # Verificar se tem opção de Gestor/Colaborador
            opcao_colaborador = page.get_by_role("menuitem", name="Colaborador").first
            opcao_gestor = page.get_by_role("menuitem", name="Gestor").first
            opcao_lider = page.get_by_role("menuitem", name="Lider").first

            if opcao_colaborador.count() > 0:
                print("[Perfil] Mudando para Colaborador...")
                opcao_colaborador.click()
                page.wait_for_timeout(2000)
                tw.snap(page, EVID, "tc9p_03_como_colaborador")
                print(f"[Perfil] URL como Colaborador: {page.url}")
            elif opcao_gestor.count() > 0:
                print("[Perfil] Mudando para Gestor...")
                opcao_gestor.click()
                page.wait_for_timeout(2000)
                tw.snap(page, EVID, "tc9p_03_como_gestor")
                print(f"[Perfil] URL como Gestor: {page.url}")
            else:
                print("[Perfil] Sem opção de Colaborador/Gestor no dropdown")
                # Fechar dropdown
                page.keyboard.press("Escape")
        else:
            print("[Perfil] Botão de perfil não encontrado")

        # Tentar acessar Registros no perfil de Colaborador (sem profile=admin)
        print(f"\n[Registros] Acessando {RECORDS_URL}...")
        page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        tw.dispensar_nps(page)
        suprimir_sophia(page)
        try:
            page.wait_for_selector(".chakra-spinner", state="hidden", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(1500)

        print(f"[Registros] URL final: {page.url}")
        perfil_atual = page.locator("button:has-text('Administrador'), button:has-text('Colaborador'), button:has-text('Gestor')").first
        if perfil_atual.count() > 0:
            try:
                print(f"[Registros] Perfil ativo: {perfil_atual.inner_text()}")
            except Exception:
                pass

        tw.snap(page, EVID, "tc9p_04_registros_lider_profile")

        # Contar linhas
        linhas = page.locator("tbody tr").count()
        print(f"[Registros] Linhas visíveis: {linhas}")

        # Verificar KPIs
        for titulo in ["Emitidos", "Expirados", "Pendentes", "Recusados"]:
            try:
                el = page.get_by_text(titulo, exact=True).first
                parent = el.locator("xpath=..").first
                print(f"[KPI] {titulo}: {parent.inner_text()[:50]}")
            except Exception:
                pass

        # Tentar URL com profile=leader
        print(f"\n[Lider Profile] Tentando ?profile=leader...")
        page.goto(f"{RECORDS_URL}?profile=leader", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        tw.dispensar_nps(page)
        try:
            page.wait_for_selector(".chakra-spinner", state="hidden", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(1500)
        tw.snap(page, EVID, "tc9p_05_records_profile_leader")
        print(f"[Lider Profile] URL: {page.url}")
        linhas2 = page.locator("tbody tr").count()
        print(f"[Lider Profile] Linhas: {linhas2}")

        # Tentar URL com as_team_manager
        print(f"\n[Team Manager] Tentando ?as_team_manager=true...")
        page.goto(f"{RECORDS_URL}?as_team_manager=true", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        tw.dispensar_nps(page)
        try:
            page.wait_for_selector(".chakra-spinner", state="hidden", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(1500)
        tw.snap(page, EVID, "tc9p_06_records_team_manager")
        print(f"[Team Manager] URL: {page.url}")
        linhas3 = page.locator("tbody tr").count()
        print(f"[Team Manager] Linhas: {linhas3}")

        # Verificar o HTML do botão de perfil atual para entender estrutura
        print("\n[Debug] Inspecionando header para seletor de perfil...")
        header_html = page.locator("header, nav").first.inner_html() if page.locator("header, nav").count() > 0 else ""
        # Procurar por "perfil" no HTML simplificado
        import re
        botoes_dropdown = re.findall(r'<button[^>]*>([^<]{2,50})</button>', header_html[:3000])
        print(f"[Debug] Botoes no header: {botoes_dropdown[:10]}")

        ctx.close()
        browser.close()


if __name__ == "__main__":
    env_path = tw.ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

    run()
