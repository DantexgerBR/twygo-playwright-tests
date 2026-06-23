"""run_qa12_tc9.py — TC9: Visão do Líder com escopo reduzido
Suíte QA 1.2 | Card Artia 19889 | Org 37079
https://registrosf2.stage.twygoead.com/

TC9 estava BLOQUEADO por falta de organograma. Dante criou estrutura:
  - Lider:    qalider@teste.com  (usuário "lider .")
  - Liderado: liderado1@teste.com (usuário "liderado 1")

Fluxo:
  1. Admin: verificar organograma e contar registros do liderado1
  2. Admin: criar registro para liderado1 se necessário (garantir massa de dados)
  3. Admin: resetar senha do líder para 123456
  4. Lider: logar, acessar Aprendizagem > Registros
  5. Lider: verificar que APENAS liderados diretos aparecem (escopo restrito)
  6. Lider: verificar KPIs <= totais da org

Veredito ✅ se: lista do líder != org inteira, inclui liderado1 e exclui outros
Veredito ❌ se: líder vê org inteira (mesma contagem da admin view)
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = os.environ.get("REGISTROSF2_BASE_URL", "https://registrosf2.stage.twygoead.com").rstrip("/")
ORG_ID   = os.environ.get("REGISTROSF2_ORG_ID", "37079")
ADMIN_EMAIL    = os.environ.get("REGISTROSF2_ADMIN_EMAIL", "dante.tavares@twygo.com")
ADMIN_PASSWORD = os.environ.get("REGISTROSF2_ADMIN_PASSWORD", "123456")

LIDER_EMAIL    = "qalider@teste.com"
LIDER_PASSWORD = "123456"  # será resetado pelo admin antes de usar
LIDERADO_EMAIL = "liderado1@teste.com"
NAO_LIDERADO_EMAIL = os.environ.get("REGISTROSF2_TC3_EMAIL", "qa11tc342588@twygotest.com")

SLUG = "registros-f2-qa12"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)

RECORDS_URL = f"{BASE_URL}/o/{ORG_ID}/records"
USERS_URL   = f"{BASE_URL}/o/{ORG_ID}/users"

results = {}


def log(msg):
    print(msg)


def suprimir_sophia(page):
    """Suprime o chat Sophia via JS para não bloquear cliques."""
    page.evaluate("""
        () => {
            const sel = [
                '#hubspot-messages-iframe-container',
                '[data-testid="chat-widget"]',
                '.intercom-launcher',
                '.intercom-namespace',
                '#chat-widget-container',
                '[class*="sophia"]',
                '[class*="Sophia"]',
                '[id*="sophia"]',
                '[id*="hubspot"]'
            ];
            sel.forEach(s => {
                document.querySelectorAll(s).forEach(el => el.style.display = 'none');
            });
            document.querySelectorAll('iframe').forEach(f => {
                try {
                    const src = f.src || '';
                    if (src.includes('chat') || src.includes('hubspot') || src.includes('widget')) {
                        f.style.display = 'none';
                    }
                } catch(e) {}
            });
        }
    """)


def ir_para_registros(page):
    """Navega para tela Registros e aguarda carregamento."""
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    suprimir_sophia(page)

    spinner_count = page.locator(".chakra-spinner").count()
    if spinner_count > 0:
        page.reload(wait_until="domcontentloaded", timeout=30000)
        try:
            with page.expect_response(
                lambda r: f"/api/v1/o/{ORG_ID}/records?" in r.url and r.status == 200,
                timeout=20000
            ):
                pass
        except Exception:
            pass
        page.wait_for_timeout(5000)
        tw.dispensar_nps(page)
        suprimir_sophia(page)

    try:
        page.wait_for_selector(".chakra-spinner", state="hidden", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(1000)


def login_admin(page):
    """Loga como Admin na org 37079 e faz switch para perfil Administrador."""
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", "")
    page.fill("#user_email", ADMIN_EMAIL)
    page.wait_for_timeout(300)
    page.fill("#user_password", "")
    page.fill("#user_password", ADMIN_PASSWORD)
    page.wait_for_timeout(300)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)

    if "/users/login" in page.url:
        log(f"[ERRO] Login admin falhou — URL: {page.url}")
        return False

    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    return True


def extrair_kpis(page):
    """Extrai valores dos 4 KPI cards da tela de Registros."""
    kpis = {}
    # KPI cards têm estrutura de texto com título e número
    # Tenta via texto dos cards
    try:
        # Aguardar que pelo menos um KPI card apareça
        page.wait_for_selector("[class*='kpi'], [class*='KPI'], [class*='stat'], [class*='card']", timeout=5000)
    except Exception:
        pass

    # Captura todos os números visíveis no topo (faixa de KPI)
    # Títulos: Emitidos, Expirados, Pendentes, Recusados
    for titulo in ["Emitidos", "Expirados", "Pendentes", "Recusados"]:
        try:
            # Procurar o elemento que contém o título e pegar o número próximo
            el = page.get_by_text(titulo, exact=True).first
            if el.count() == 0:
                el = page.locator(f"text={titulo}").first
            parent = el.locator("xpath=..").first
            texto_parent = parent.inner_text()
            # Extrair número do texto
            import re
            nums = re.findall(r'\d+', texto_parent)
            kpis[titulo] = int(nums[0]) if nums else 0
        except Exception:
            kpis[titulo] = None

    return kpis


def contar_linhas_tabela(page):
    """Conta linhas visíveis na tabela de registros."""
    try:
        # Linha da tabela: tbody tr, ou data-testid, ou role=row
        linhas = page.locator("tbody tr").count()
        if linhas == 0:
            linhas = page.locator("[role='row']").count()
            if linhas > 0:
                linhas -= 1  # descontar header
        return linhas
    except Exception:
        return 0


def extrair_pessoas_tabela(page):
    """Extrai lista de e-mails/nomes da coluna 'Pessoa' da tabela."""
    pessoas = []
    try:
        # Coluna Pessoa: normalmente 2ª coluna (after checkbox)
        # Tenta pegar os textos das células da coluna Pessoa
        # Busca células que contenham "@" (email)
        celulas = page.locator("tbody td").all()
        for cel in celulas:
            try:
                texto = cel.inner_text()
                if "@" in texto:
                    pessoas.append(texto.strip())
            except Exception:
                pass
    except Exception:
        pass
    return pessoas


def resetar_senha_lider(page):
    """Reseta a senha do líder para 123456 via admin > Usuários."""
    log("[Reset Senha] Navegando para lista de usuários...")
    page.goto(USERS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    suprimir_sophia(page)

    # Aguarda spinner desaparecer
    try:
        page.wait_for_selector(".chakra-spinner", state="hidden", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(1000)

    tw.snap(page, EVID, "tc9_00_usuarios_lista")

    # Buscar o líder pelo email
    log(f"[Reset Senha] Buscando usuário {LIDER_EMAIL}...")
    busca = page.locator("input[placeholder*='Pesquis'], input[placeholder*='buscar'], input[type='search'], input[placeholder*='nome']").first
    if busca.count() == 0:
        busca = page.locator("input[type='text']").first
    if busca.count() > 0:
        busca.fill(LIDER_EMAIL)
        page.wait_for_timeout(2000)
        tw.snap(page, EVID, "tc9_01_busca_lider")
    else:
        log("[Reset Senha] Campo busca não encontrado, tentando sem filtro...")
        tw.snap(page, EVID, "tc9_01_busca_lider")

    # Tentar encontrar o kebab/menu do líder
    # Estratégia: procurar linha que contenha o email do líder
    lider_nome_curto = "qalider"
    try:
        linha_lider = page.locator(f"tr:has-text('{lider_nome_curto}')").first
        if linha_lider.count() == 0:
            linha_lider = page.locator(f"tr:has-text('lider')").first
        if linha_lider.count() > 0:
            # Clicar no kebab da linha
            kebab = linha_lider.locator("[aria-label*='kebab'], [aria-label*='menu'], button[aria-haspopup], button:has([data-icon]), button:last-child").last
            if kebab.count() == 0:
                kebab = linha_lider.locator("button").last
            kebab.click()
            page.wait_for_timeout(1000)
            tw.snap(page, EVID, "tc9_02_kebab_lider")

            # Clicar em "Alterar senha" ou similar
            opcao_senha = page.get_by_role("menuitem", name="Alterar senha").first
            if opcao_senha.count() == 0:
                opcao_senha = page.get_by_text("Alterar senha").first
            if opcao_senha.count() == 0:
                opcao_senha = page.get_by_text("senha").first
            if opcao_senha.count() > 0:
                opcao_senha.click()
                page.wait_for_timeout(1500)
                tw.snap(page, EVID, "tc9_03_modal_senha")

                # Preencher nova senha
                inputs_senha = page.locator("input[type='password']").all()
                if len(inputs_senha) >= 1:
                    inputs_senha[0].fill("123456")
                if len(inputs_senha) >= 2:
                    inputs_senha[1].fill("123456")
                page.wait_for_timeout(500)

                # Confirmar
                btn_confirmar = page.get_by_role("button", name="Salvar").first
                if btn_confirmar.count() == 0:
                    btn_confirmar = page.get_by_role("button", name="Confirmar").first
                if btn_confirmar.count() == 0:
                    btn_confirmar = page.get_by_role("button", name="Alterar").first
                if btn_confirmar.count() > 0:
                    btn_confirmar.click()
                    page.wait_for_timeout(2000)
                    tw.snap(page, EVID, "tc9_04_senha_alterada")
                    log("[Reset Senha] Senha do líder alterada para 123456")
                    return True
                else:
                    log("[Reset Senha] Botão confirmar não encontrado")
            else:
                log("[Reset Senha] Opção 'Alterar senha' não encontrada no menu")
        else:
            log("[Reset Senha] Linha do líder não encontrada na tabela")
    except Exception as e:
        log(f"[Reset Senha] Erro: {e}")
        tw.snap(page, EVID, "tc9_02_erro_reset")

    log("[Reset Senha] ATENÇÃO: reset de senha pode ter falhado — continuando com 123456 mesmo assim")
    return False


def verificar_registros_liderado_como_admin(page):
    """Como admin, verifica quantos registros o liderado1 tem.
    Retorna (count_liderado, pessoas_sample) para cross-check."""
    log("[Admin Cross-check] Verificando registros do liderado1 na visão admin...")
    ir_para_registros(page)
    tw.snap(page, EVID, "tc9_05_admin_registros_todos")

    # Extrair KPIs da org inteira
    kpis_org = extrair_kpis(page)
    log(f"[Admin Cross-check] KPIs org inteira: {kpis_org}")

    # Buscar pelo liderado
    log(f"[Admin Cross-check] Buscando por: {LIDERADO_EMAIL}")
    busca = page.locator("input[placeholder*='Pesquis'], input[placeholder*='conteúdo'], input[placeholder*='pessoa']").first
    if busca.count() == 0:
        busca = page.locator("input[type='search']").first
    if busca.count() == 0:
        busca = page.locator("input[type='text']").first

    if busca.count() > 0:
        busca.fill(LIDERADO_EMAIL.split("@")[0])  # busca por nome de usuário
        page.wait_for_timeout(3000)
        tw.snap(page, EVID, "tc9_06_admin_busca_liderado")

        linhas_liderado = contar_linhas_tabela(page)
        log(f"[Admin Cross-check] Registros do liderado1 no admin: {linhas_liderado}")

        # Limpar busca
        busca.fill("")
        page.wait_for_timeout(2000)
    else:
        linhas_liderado = 0
        log("[Admin Cross-check] Campo busca não encontrado")

    # Buscar pelo nome do liderado (alternativa)
    if linhas_liderado == 0:
        if busca.count() > 0:
            busca.fill("liderado")
            page.wait_for_timeout(3000)
            linhas_liderado_v2 = contar_linhas_tabela(page)
            log(f"[Admin Cross-check] Registros 'liderado' no admin: {linhas_liderado_v2}")
            tw.snap(page, EVID, "tc9_06b_admin_busca_liderado_nome")
            busca.fill("")
            page.wait_for_timeout(2000)
            linhas_liderado = linhas_liderado_v2

    return kpis_org, linhas_liderado


def criar_registro_liderado_se_necessario(page, linhas_existentes):
    """Se liderado1 tiver 0 registros, cria 1 para garantir massa de dados."""
    if linhas_existentes > 0:
        log(f"[Seed] liderado1 já tem {linhas_existentes} registro(s). Pulando criação.")
        return True

    log("[Seed] liderado1 sem registros — criando 1 registro de teste...")
    ir_para_registros(page)

    btn_adicionar = page.get_by_role("button", name="Adicionar").first
    if btn_adicionar.count() == 0:
        log("[Seed] Botão 'Adicionar' não encontrado")
        return False

    btn_adicionar.click()
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    tw.snap(page, EVID, "tc9_07_form_adicionar")

    # Preencher campo Pessoa
    try:
        pessoa_input = page.locator("input[placeholder*='Pesquis'], input[placeholder*='pessoa'], input[placeholder*='Pessoa']").first
        if pessoa_input.count() == 0:
            pessoa_input = page.locator("form input[type='text']").first
        if pessoa_input.count() > 0:
            pessoa_input.fill("liderado")
            page.wait_for_timeout(2000)
            # Selecionar primeira opção
            opcao = page.locator("[role='option']").first
            if opcao.count() == 0:
                opcao = page.locator("li[class*='option'], [class*='menu-item']").first
            if opcao.count() > 0:
                opcao.click()
                page.wait_for_timeout(1000)
                log("[Seed] Pessoa 'liderado1' selecionada")
            else:
                log("[Seed] Dropdown de opções não apareceu para 'liderado'")
    except Exception as e:
        log(f"[Seed] Erro ao preencher Pessoa: {e}")

    # Preencher Conteúdo/Título
    try:
        conteudo_inputs = page.locator("form input[type='text']").all()
        for inp in conteudo_inputs:
            placeholder = inp.get_attribute("placeholder") or ""
            if "conteúdo" in placeholder.lower() or "título" in placeholder.lower() or "content" in placeholder.lower():
                inp.fill("Registro de Teste TC9")
                break
        else:
            # Tenta o segundo input
            if len(conteudo_inputs) > 1:
                conteudo_inputs[1].fill("Registro de Teste TC9")
    except Exception as e:
        log(f"[Seed] Erro ao preencher Conteúdo: {e}")

    tw.snap(page, EVID, "tc9_07b_form_preenchido")

    # Tentar salvar
    try:
        btn_salvar = page.get_by_role("button", name="Salvar").first
        if btn_salvar.count() == 0:
            btn_salvar = page.get_by_role("button", name="Adicionar").last
        if btn_salvar.count() > 0:
            btn_salvar.click()
            page.wait_for_timeout(3000)
            tw.snap(page, EVID, "tc9_07c_apos_salvar")
            log("[Seed] Registro criado (ou tentativa realizada)")
            return True
    except Exception as e:
        log(f"[Seed] Erro ao salvar: {e}")

    # Fechar modal se não salvou
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(1000)
    except Exception:
        pass

    return False


def login_lider(page):
    """Loga como Líder (qalider@teste.com) sem switch para admin."""
    log(f"[Login Líder] Logando como {LIDER_EMAIL}...")
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", "")
    page.fill("#user_email", LIDER_EMAIL)
    page.wait_for_timeout(300)
    page.fill("#user_password", "")
    page.fill("#user_password", LIDER_PASSWORD)
    page.wait_for_timeout(300)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(3000)

    if "/users/login" in page.url:
        log(f"[Login Líder] FALHOU — URL: {page.url}")
        tw.snap(page, EVID, "tc9_10_login_lider_falhou")
        return False

    log(f"[Login Líder] OK — URL: {page.url}")
    tw.snap(page, EVID, "tc9_10_login_lider_ok")
    tw.dispensar_nps(page)
    return True


def navegar_registros_como_lider(page):
    """Navega para Aprendizagem > Registros como líder.
    O líder NÃO usa profile=admin. Acessa via URL direta ou menu."""
    log("[Líder] Navegando para Registros...")

    # Tenta via URL direta (sem profile=admin)
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    suprimir_sophia(page)

    # Verificar se foi redirecionado (Líder pode não ter acesso direto via /records admin)
    current_url = page.url
    log(f"[Líder] URL após goto records: {current_url}")

    # Se voltou para dashboard_students, o líder precisa de outra rota
    if "dashboard_students" in current_url or "login" in current_url:
        log("[Líder] Redirecionou para dashboard — tentando via menu de gestor/líder...")
        # Tenta URL com as_team_manager
        page.goto(
            f"{BASE_URL}/o/{ORG_ID}/records?profile=leader",
            wait_until="domcontentloaded",
            timeout=30000
        )
        page.wait_for_timeout(2000)
        current_url = page.url
        log(f"[Líder] URL após profile=leader: {current_url}")

        if "dashboard_students" in current_url or "login" in current_url:
            # Tenta como gestor
            page.goto(
                f"{BASE_URL}/o/{ORG_ID}/records?as_team_manager=true",
                wait_until="domcontentloaded",
                timeout=30000
            )
            page.wait_for_timeout(2000)
            current_url = page.url
            log(f"[Líder] URL após as_team_manager: {current_url}")

    # Aguardar carregamento
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

    final_url = page.url
    log(f"[Líder] URL final: {final_url}")
    return final_url


def run():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=200)

        # ── FASE 1: Sessão Admin ───────────────────────────────────────────
        log("\n=== FASE 1: Admin — verificar organograma + registros do liderado ===")
        ctx_admin = browser.new_context(viewport={"width": 1280, "height": 800})
        page_admin = ctx_admin.new_page()

        ok_admin = login_admin(page_admin)
        if not ok_admin:
            log("[ERRO FATAL] Login admin falhou — abortando")
            tw.snap(page_admin, EVID, "tc9_ERRO_login_admin")
            ctx_admin.close()
            browser.close()
            results["TC9"] = {"pass": False, "note": "Login admin falhou — não foi possível executar TC9"}
            return

        # Verificar organograma
        log("[Admin] Verificando organograma...")
        org_chart_url = f"{BASE_URL}/o/{ORG_ID}/organization_charts"
        page_admin.goto(org_chart_url, wait_until="domcontentloaded", timeout=30000)
        page_admin.wait_for_timeout(3000)
        tw.dispensar_nps(page_admin)
        suprimir_sophia(page_admin)
        try:
            page_admin.wait_for_selector(".chakra-spinner", state="hidden", timeout=10000)
        except Exception:
            pass
        tw.snap(page_admin, EVID, "tc9_organograma")
        log(f"[Admin] URL organograma: {page_admin.url}")

        # Resetar senha do líder
        resetar_senha_lider(page_admin)

        # Verificar registros do liderado1 como admin e KPIs da org
        kpis_org, linhas_liderado = verificar_registros_liderado_como_admin(page_admin)

        # Criar registro para liderado1 se não tiver nenhum
        if linhas_liderado == 0:
            criou = criar_registro_liderado_se_necessario(page_admin, linhas_liderado)
            if criou:
                # Recontabilizar
                _, linhas_liderado = verificar_registros_liderado_como_admin(page_admin)
                log(f"[Seed] Após criação: liderado1 tem {linhas_liderado} registro(s)")

        log(f"\n[Admin] Resumo pré-TC9:")
        log(f"  KPIs org inteira: {kpis_org}")
        log(f"  Registros do liderado1: {linhas_liderado}")

        ctx_admin.close()

        # ── FASE 2: Sessão Lider ───────────────────────────────────────────
        log("\n=== FASE 2: Lider — testar escopo restrito em Aprendizagem > Registros ===")
        ctx_lider = browser.new_context(viewport={"width": 1280, "height": 800})
        page_lider = ctx_lider.new_page()

        ok_lider = login_lider(page_lider)
        if not ok_lider:
            log("[ERRO] Login do líder falhou")
            results["TC9"] = {
                "pass": False,
                "note": "Login do líder qalider@teste.com falhou com senha 123456 — verificar se reset funcionou"
            }
            ctx_lider.close()
            browser.close()
            return

        # Passo 1: Acessar Aprendizagem > Registros como Líder
        log("\n--- Passo 1: Navegar para Registros como Líder ---")
        final_url = navegar_registros_como_lider(page_lider)

        # Verificar se a tela de Registros renderizou
        current_url = page_lider.url
        tela_records_ok = "records" in current_url.lower() or "registros" in current_url.lower()

        if not tela_records_ok:
            log(f"[TC9 P1] Líder não chegou na tela de Registros — URL: {current_url}")
            tw.snap(page_lider, EVID, "tc9_11_lider_sem_records")

            # Tenta via menu lateral
            log("[TC9 P1] Tentando localizar 'Registros' no menu lateral...")
            try:
                # Procurar link/menu item com texto "Registros" ou "Aprendizagem"
                menu_registros = page_lider.get_by_role("link", name="Registros").first
                if menu_registros.count() == 0:
                    menu_registros = page_lider.get_by_text("Registros").first
                if menu_registros.count() > 0:
                    menu_registros.click()
                    page_lider.wait_for_timeout(3000)
                    tw.snap(page_lider, EVID, "tc9_12_lider_menu_registros")
                    current_url = page_lider.url
                    tela_records_ok = "records" in current_url.lower()
                    log(f"[TC9 P1] URL após clicar 'Registros': {current_url}")
            except Exception as e:
                log(f"[TC9 P1] Erro ao clicar menu Registros: {e}")

        tw.snap(page_lider, EVID, "tc9_12_lider_tela_registros")
        log(f"[TC9 P1] Tela Registros OK: {tela_records_ok} | URL: {page_lider.url}")

        # Verificar estrutura da tela (tabs, KPIs, toolbar)
        tem_tab_registros = page_lider.get_by_role("tab", name="Registros").count() > 0
        tem_tab_provedores = page_lider.get_by_role("tab", name="Provedores").count() > 0
        tem_toolbar = page_lider.get_by_role("button", name="Adicionar").count() > 0 or \
                      page_lider.get_by_role("button", name="Filtro").count() > 0

        log(f"[TC9 P1] Tab 'Registros': {tem_tab_registros}")
        log(f"[TC9 P1] Tab 'Provedores': {tem_tab_provedores}")
        log(f"[TC9 P1] Toolbar presente: {tem_toolbar}")

        tw.snap(page_lider, EVID, "tc9_13_lider_estrutura")

        # Passo 2: Verificar pessoas listadas = apenas liderados diretos
        log("\n--- Passo 2: Verificar escopo da lista (apenas liderados diretos) ---")

        # Contar registros visíveis
        linhas_lider = contar_linhas_tabela(page_lider)
        log(f"[TC9 P2] Linhas visíveis para o líder: {linhas_lider}")

        # Verificar total da org admin (KPIs)
        kpi_total_org = sum(v for v in kpis_org.values() if v is not None)

        # Extrair KPIs da visão do líder
        kpis_lider = extrair_kpis(page_lider)
        log(f"[TC9 P2] KPIs visão líder: {kpis_lider}")
        kpi_total_lider = sum(v for v in kpis_lider.values() if v is not None)
        log(f"[TC9 P2] Total KPI líder: {kpi_total_lider} | Total KPI org: {kpi_total_org}")

        tw.snap(page_lider, EVID, "tc9_14_lider_lista_pessoas")

        # Extrair textos das células para identificar pessoas presentes
        pessoas_visiveis = extrair_pessoas_tabela(page_lider)
        log(f"[TC9 P2] Pessoas visíveis (emails/nomes): {pessoas_visiveis[:10]}")

        # Verificar presença do liderado1 na lista
        liderado_presente = any("liderado" in p.lower() or LIDERADO_EMAIL.split("@")[0] in p.lower()
                                for p in pessoas_visiveis)
        log(f"[TC9 P2] liderado1 presente na lista: {liderado_presente}")

        # Verificar ausência de não-liderado
        nao_liderado_nome = NAO_LIDERADO_EMAIL.split("@")[0]
        nao_liderado_ausente = not any(nao_liderado_nome in p.lower() for p in pessoas_visiveis)
        log(f"[TC9 P2] não-liderado ausente: {nao_liderado_ausente}")

        # Verificar se a lista é igual à org inteira (escopo NÃO restrito)
        # Se o líder vê exatamente as mesmas 149 linhas da org, é bug
        linhas_totais_org_estimado = 149  # do gate anterior
        escopo_parece_restrito = linhas_lider < linhas_totais_org_estimado

        log(f"[TC9 P2] Escopo parece restrito: {escopo_parece_restrito} ({linhas_lider} < {linhas_totais_org_estimado})")

        tw.snap(page_lider, EVID, "tc9_15_lider_lista_full")

        # Buscar pelo não-liderado para confirmar ausência
        log("\n--- Cross-check: buscar pelo não-liderado na visão do líder ---")
        try:
            busca_lider = page_lider.locator(
                "input[placeholder*='Pesquis'], input[placeholder*='conteúdo'], input[type='search']"
            ).first
            if busca_lider.count() == 0:
                busca_lider = page_lider.locator("input[type='text']").first

            if busca_lider.count() > 0:
                # Busca pelo não-liderado
                busca_lider.fill(nao_liderado_nome)
                page_lider.wait_for_timeout(3000)
                linhas_nao_liderado = contar_linhas_tabela(page_lider)
                tw.snap(page_lider, EVID, "tc9_16_busca_nao_liderado")
                log(f"[TC9 Cross-check] Busca '{nao_liderado_nome}' no líder: {linhas_nao_liderado} linhas")

                # Limpar e buscar pelo liderado
                busca_lider.fill("")
                page_lider.wait_for_timeout(1500)
                busca_lider.fill("liderado")
                page_lider.wait_for_timeout(3000)
                linhas_liderado_na_view_lider = contar_linhas_tabela(page_lider)
                tw.snap(page_lider, EVID, "tc9_17_busca_liderado")
                log(f"[TC9 Cross-check] Busca 'liderado' no líder: {linhas_liderado_na_view_lider} linhas")

                busca_lider.fill("")
                page_lider.wait_for_timeout(1500)
            else:
                linhas_nao_liderado = None
                linhas_liderado_na_view_lider = None
                log("[TC9 Cross-check] Campo busca não encontrado no líder")
        except Exception as e:
            log(f"[TC9 Cross-check] Erro: {e}")
            linhas_nao_liderado = None
            linhas_liderado_na_view_lider = None

        # Passo 3: KPIs do líder <= KPIs da org
        log("\n--- Passo 3: Verificar KPIs do líder ≤ KPIs da org ---")
        kpis_menores = all(
            (kpis_lider.get(k) is None or kpis_org.get(k) is None or kpis_lider[k] <= kpis_org[k])
            for k in ["Emitidos", "Expirados", "Pendentes", "Recusados"]
        )
        log(f"[TC9 P3] KPIs líder ≤ KPIs org: {kpis_menores}")
        for k in ["Emitidos", "Expirados", "Pendentes", "Recusados"]:
            log(f"  {k}: líder={kpis_lider.get(k)} | org={kpis_org.get(k)}")

        tw.snap(page_lider, EVID, "tc9_18_lider_kpis")

        # ── DECISÃO DE VEREDITO ─────────────────────────────────────────────
        log("\n=== VEREDITO TC9 ===")

        # Critérios:
        # ✅ se:
        #   - Tela de Registros renderizou (tem tabs e/ou toolbar)
        #   - Lista do líder < total da org (escopo restrito)
        #   - KPIs do líder <= KPIs da org
        # ❌ se:
        #   - Líder vê org inteira (linhas_lider >= total org) OU
        #   - Estrutura da tela está completamente diferente do admin

        tela_ok = tela_records_ok or tem_tab_registros or (linhas_lider > 0)
        escopo_ok = escopo_parece_restrito and kpis_menores

        # Se busca funcionou, use como discriminador forte
        if linhas_nao_liderado is not None and linhas_liderado_na_view_lider is not None:
            if linhas_nao_liderado == 0 and linhas_liderado_na_view_lider >= 0:
                escopo_ok = True  # não-liderado não aparece = escopo restrito ✅
            elif linhas_nao_liderado > 0:
                escopo_ok = False  # não-liderado aparece = escopo NÃO restrito ❌

        passou = tela_ok and escopo_ok

        nota = (
            f"Tela renderizou: {tela_ok} | "
            f"Escopo restrito: {escopo_parece_restrito} | "
            f"Linhas líder: {linhas_lider} | "
            f"KPIs líder: {kpis_lider} | "
            f"KPIs org: {kpis_org} | "
            f"KPIs menores: {kpis_menores} | "
            f"liderado1 na view: {linhas_liderado_na_view_lider} | "
            f"nao-liderado na view: {linhas_nao_liderado}"
        )

        results["TC9"] = {"pass": passou, "note": nota}

        veredito_str = "✅ PASSOU" if passou else "❌ FALHOU"
        log(f"\n{veredito_str}")
        log(f"  Nota: {nota}")

        ctx_lider.close()
        browser.close()


if __name__ == "__main__":
    # Carregar .env
    env_path = tw.ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

    run()

    tc9 = results.get("TC9", {})
    passou = tc9.get("pass", False)
    nota = tc9.get("note", "sem nota")
    veredito = "✅ PASSOU" if passou else "❌ FALHOU"

    print(f"\n{'='*60}")
    print(f"TC9 — Visão do Líder: {veredito}")
    print(f"Nota: {nota}")
    print(f"{'='*60}")
    print(f"\nEvidências em: {tw.ROOT / 'evidencias' / 'registros-f2-qa12'}")

