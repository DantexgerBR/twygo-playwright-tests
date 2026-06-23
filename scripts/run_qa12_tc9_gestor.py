"""run_qa12_tc9_gestor.py — TC9 definitivo: Lider no perfil Gestor de turma
Muda o lider para perfil "Gestor de turma" e testa Registros com escopo correto.
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
            document.querySelectorAll('iframe').forEach(f => {
                try { if ((f.src||'').includes('chat')||f.src.includes('hubspot')) f.style.display='none'; } catch(e){}
            });
        }
    """)


def ir_para_registros(page):
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    suprimir_sophia(page)
    spinner_count = page.locator(".chakra-spinner").count()
    if spinner_count > 0:
        page.reload(wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        tw.dispensar_nps(page)
        suprimir_sophia(page)
    try:
        page.wait_for_selector(".chakra-spinner", state="hidden", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(1500)


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
        tw.snap(page, EVID, "tc9g_01_login_ok")

        # Abrir seletor de perfil
        print("[Perfil] Abrindo seletor de perfil...")
        # O botão de perfil é o que está no header (pode mostrar "Colaborador" ou "Administrador")
        perfil_btn = page.locator("button:has-text('Colaborador'), button:has-text('Administrador'), button:has-text('Gestor'), button:has-text('Instrutor')").first
        if perfil_btn.count() == 0:
            perfil_btn = page.locator("header button[aria-haspopup]").first
        if perfil_btn.count() == 0:
            # Procura o botão no canto superior direito
            perfil_btn = page.locator("[data-testid='profile-switch'], [aria-label*='perfil']").first

        print(f"[Perfil] Botão encontrado: {perfil_btn.count() > 0}")
        if perfil_btn.count() == 0:
            print("[ERRO] Botão de perfil não encontrado no dashboard inicial")
            tw.snap(page, EVID, "tc9g_ERRO_sem_perfil")
            ctx.close()
            browser.close()
            return

        perfil_btn.click()
        page.wait_for_timeout(1500)
        tw.snap(page, EVID, "tc9g_02_dropdown_perfil")

        # Verificar perfil atual
        perfil_texto = perfil_btn.inner_text().strip() if perfil_btn.count() > 0 else "?"
        print(f"[Perfil] Perfil ativo: {perfil_texto}")

        # Listar e imprimir todas as opções
        opcoes = page.locator("[role='menuitem'], [role='option']").all()
        print(f"[Perfil] Opções disponíveis ({len(opcoes)}):")
        for o in opcoes:
            try:
                print(f"  - '{o.inner_text().strip()}'")
            except Exception:
                pass

        # Mudar para Gestor de turma
        opcao_gestor = page.get_by_text("Gestor de turma", exact=True).first
        if opcao_gestor.count() == 0:
            opcao_gestor = page.get_by_role("menuitem", name="Gestor de turma").first
        if opcao_gestor.count() == 0:
            opcao_gestor = page.locator("text=Gestor de turma").first

        if opcao_gestor.count() > 0:
            print("[Perfil] Clicando em 'Gestor de turma'...")
            opcao_gestor.click()
            page.wait_for_timeout(3000)
            tw.dispensar_nps(page)
            print(f"[Perfil] URL após mudar para Gestor: {page.url}")
            tw.snap(page, EVID, "tc9g_03_como_gestor_turma")

            # ─── PASSO 1 ─────────────────────────────────────────────────────
            print("\n--- Passo 1: Acessar Registros como Gestor de turma ---")
            ir_para_registros(page)
            perfil_header = page.locator("button:has-text('Colaborador'), button:has-text('Administrador'), button:has-text('Gestor'), button:has-text('Instrutor')").first
            if perfil_header.count() > 0:
                print(f"[P1] Perfil atual: {perfil_header.inner_text()}")
            print(f"[P1] URL: {page.url}")
            tw.snap(page, EVID, "tc9_step1_registros_lider")

            # Verificar tabs e toolbar
            tem_tab_registros  = page.get_by_role("tab", name="Registros").count() > 0
            tem_tab_provedores = page.get_by_role("tab", name="Provedores").count() > 0
            tem_toolbar        = page.get_by_role("button", name="Adicionar").count() > 0 or \
                                 page.get_by_role("button", name="Filtro").count() > 0
            print(f"[P1] Tab Registros: {tem_tab_registros} | Tab Provedores: {tem_tab_provedores} | Toolbar: {tem_toolbar}")

            # ─── PASSO 2 ─────────────────────────────────────────────────────
            print("\n--- Passo 2: Verificar escopo (apenas liderados) ---")

            # Contar linhas totais
            linhas = page.locator("tbody tr").count()
            if linhas == 0:
                linhas = page.locator("[role='row']").count()
                if linhas > 0: linhas -= 1
            print(f"[P2] Linhas visíveis: {linhas}")

            # Extrair pessoas das células
            pessoas = []
            for cel in page.locator("tbody td").all():
                try:
                    t = cel.inner_text()
                    if "@" in t:
                        pessoas.append(t.strip()[:80])
                except Exception:
                    pass
            print(f"[P2] Emails na lista ({len(pessoas)}): {pessoas[:5]}")

            # Verificar se contém SOMENTE liderado1 (não outros usuários da org)
            nomes_liderado = [p for p in pessoas if "liderado" in p.lower()]
            nomes_outros = [p for p in pessoas if "liderado" not in p.lower() and "lider" not in p.lower()]
            print(f"[P2] Nomes com 'liderado': {nomes_liderado[:5]}")
            print(f"[P2] Outros usuarios: {nomes_outros[:5]}")

            tw.snap(page, EVID, "tc9_step2_lista_pessoas")

            # ─── KPIs ────────────────────────────────────────────────────────
            print("\n--- Passo 3: KPIs do líder ---")
            import re
            kpis_lider = {}
            for titulo in ["Emitidos", "Expirados", "Pendentes", "Recusados"]:
                try:
                    el = page.get_by_text(titulo, exact=True).first
                    parent = el.locator("xpath=..").first
                    nums = re.findall(r'\d+', parent.inner_text())
                    kpis_lider[titulo] = int(nums[0]) if nums else 0
                except Exception:
                    kpis_lider[titulo] = None
            print(f"[P3] KPIs líder (gestor): {kpis_lider}")
            kpis_org = {"Emitidos": 260, "Expirados": 13, "Pendentes": 80, "Recusados": 13}
            for k in kpis_org:
                lv = kpis_lider.get(k)
                ov = kpis_org[k]
                ok = lv is None or lv <= ov
                print(f"  {k}: líder={lv} | org={ov} | ≤: {ok}")

            tw.snap(page, EVID, "tc9_step3_kpis_lider")

            # ─── CROSS-CHECK: buscar por não-liderado ────────────────────────
            print("\n--- Cross-check: busca por não-liderado ---")
            busca = page.locator(
                "input[placeholder*='Pesquis'], input[placeholder*='conteúdo'], input[type='search']"
            ).first
            if busca.count() == 0:
                busca = page.locator("input[type='text']").first

            nao_liderado_ausente = None
            liderado_presente = None

            if busca.count() > 0:
                # Busca por usuário que NÃO é liderado
                nao_liderado_busca = "qa11tc342816"
                busca.fill(nao_liderado_busca)
                page.wait_for_timeout(3000)
                linhas_nao_lid = page.locator("tbody tr").count()
                tw.snap(page, EVID, "tc9_crosscheck_nao_liderado")
                print(f"[Cross-check] Busca '{nao_liderado_busca}': {linhas_nao_lid} linhas")

                # Checar se tem empty state
                empty = page.locator("text=Nenhum, text=Não há dados, text=Sem resultado").count() > 0
                nao_liderado_ausente = (linhas_nao_lid == 0) or empty
                print(f"[Cross-check] Não-liderado ausente: {nao_liderado_ausente}")

                # Limpar e buscar pelo liderado
                busca.fill("")
                page.wait_for_timeout(1500)
                busca.fill("liderado")
                page.wait_for_timeout(3000)
                linhas_lid = page.locator("tbody tr").count()
                tw.snap(page, EVID, "tc9_crosscheck_liderado")
                print(f"[Cross-check] Busca 'liderado': {linhas_lid} linhas")
                liderado_presente = linhas_lid > 0
                print(f"[Cross-check] Liderado presente: {liderado_presente}")

                busca.fill("")
                page.wait_for_timeout(1500)
            else:
                print("[Cross-check] Campo busca não encontrado no perfil Gestor")

            tw.snap(page, EVID, "tc9_final_gestor")

            # ─── VEREDITO ────────────────────────────────────────────────────
            print("\n=== VEREDITO FINAL TC9 ===")
            kpis_ok = all(
                kpis_lider.get(k) is None or kpis_org.get(k) is None or kpis_lider[k] <= kpis_org[k]
                for k in ["Emitidos", "Expirados", "Pendentes", "Recusados"]
            )
            escopo_ok = (linhas < 149)  # líder vê menos que a org inteira

            # Discriminador forte: se busca funcionou
            if nao_liderado_ausente is not None and liderado_presente is not None:
                # Nao-liderado ausente E liderado presente = escopo correto
                if nao_liderado_ausente and liderado_presente:
                    escopo_ok = True
                elif not nao_liderado_ausente:
                    escopo_ok = False  # não-liderado aparece = bug

            passou = (tem_tab_registros or tem_tab_provedores) and escopo_ok and kpis_ok

            print(f"  Tela OK (tabs): {tem_tab_registros or tem_tab_provedores}")
            print(f"  Escopo restrito: {escopo_ok} (linhas={linhas}, org=~149)")
            print(f"  KPIs ok: {kpis_ok}")
            print(f"  Não-liderado ausente: {nao_liderado_ausente}")
            print(f"  Liderado presente: {liderado_presente}")
            print(f"\n  {'PASSOU' if passou else 'FALHOU'}")

        else:
            print("[ERRO] Opção 'Gestor de turma' não encontrada no dropdown")
            tw.snap(page, EVID, "tc9g_ERRO_sem_gestor")

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
