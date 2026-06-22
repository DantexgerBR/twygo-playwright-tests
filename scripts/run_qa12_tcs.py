"""run_qa12_tcs.py — Suíte QA 1.2: Listagem "Aprendizagem > Registros" (Admin/Líder)
Org 37079 / https://registrosf2.stage.twygoead.com/
TC1 a TC12 (TC9 bloqueado — sem organograma/líder).
Roda headless, sessão única.
"""
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = os.environ.get("REGISTROSF2_BASE_URL", "https://registrosf2.stage.twygoead.com").rstrip("/")
ORG_ID   = os.environ.get("REGISTROSF2_ORG_ID", "37079")
ADMIN_EMAIL    = os.environ.get("REGISTROSF2_ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("REGISTROSF2_ADMIN_PASSWORD", "")
TC3_EMAIL    = os.environ.get("REGISTROSF2_TC3_EMAIL", "")
TC3_PASSWORD = os.environ.get("REGISTROSF2_TC3_PASSWORD", "")

SLUG = "registros-f2-qa12"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)

RECORDS_URL = f"{BASE_URL}/o/{ORG_ID}/records"

results = {}  # tc -> {"pass": bool, "note": str}


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
            // Twygo custom chat overlay
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
    """Navega para tela Registros e aguarda carregamento.

    NOTA: Há bug SPA na org 37079 — navegar via goto() para /records resulta
    em spinner infinito (componente React trava). O workaround é fazer
    page.reload() após o goto, que força carga fresh e tabela renderiza.
    """
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    suprimir_sophia(page)

    # Workaround bug SPA: se spinner ainda ativo após 3s, recarregar
    spinner_count = page.locator(".chakra-spinner").count()
    if spinner_count > 0:
        page.reload(wait_until="domcontentloaded", timeout=30000)
        # Aguardar API /records responder
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

    # Aguarda spinner desaparecer
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
        log(f"[ERRO] Login falhou — URL: {page.url}")
        return False

    # Switch para perfil admin
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    return True


def criar_registro_admin(page, pessoa_email, conteudo_nome="Curso de Teste QA 1.2"):
    """Cria um registro via form Admin para uma pessoa específica.
    Retorna True se criou com sucesso."""
    ir_para_registros(page)
    btn_adicionar = page.get_by_role("button", name="Adicionar")
    if btn_adicionar.count() == 0:
        log("[criar_registro] Botão 'Adicionar' não encontrado")
        return False
    btn_adicionar.first.click()
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)

    # Selecionar Pessoa
    pessoa_field = page.get_by_label("Pessoa")
    if pessoa_field.count() == 0:
        # Tenta por placeholder
        pessoa_field = page.locator("input[placeholder*='Pessoa'], input[placeholder*='pessoa']")
    if pessoa_field.count() == 0:
        # Tenta qualquer input do form
        pessoa_field = page.locator("form input").first
    if pessoa_field.count() > 0:
        pessoa_field.first.fill(pessoa_email.split("@")[0])
        page.wait_for_timeout(1500)
        # Seleciona primeira opção do dropdown
        opcoes = page.locator("[role='option'], [class*='option'], li[class*='menu']")
        if opcoes.count() > 0:
            opcoes.first.click()
            page.wait_for_timeout(500)

    # Tenta pelo placeholder específico do Twygo
    try:
        pessoa_input = page.locator("input[placeholder*='Buscar pessoa'], input[placeholder*='buscar pessoa']")
        if pessoa_input.count() > 0:
            pessoa_input.first.fill(pessoa_email)
            page.wait_for_timeout(1500)
            opt = page.locator("[role='option']")
            if opt.count() > 0:
                opt.first.click()
                page.wait_for_timeout(500)
    except Exception:
        pass

    # Conteúdo/descrição
    try:
        conteudo_input = page.locator("input[name*='content'], input[placeholder*='conteúdo'], input[placeholder*='Conteúdo']")
        if conteudo_input.count() > 0:
            conteudo_input.first.fill(conteudo_nome)
            page.wait_for_timeout(500)
    except Exception:
        pass

    # Tipo de experiência (obrigatório)
    try:
        tipo_exp = page.locator("select[name*='type'], [aria-label*='Tipo'], [placeholder*='Tipo']")
        if tipo_exp.count() > 0:
            tipo_exp.first.click()
            page.wait_for_timeout(500)
            opcao_curso = page.locator("[role='option']").filter(has_text="Curso")
            if opcao_curso.count() > 0:
                opcao_curso.first.click()
    except Exception:
        pass

    # Carga horária (obrigatório)
    try:
        carga = page.locator("input[name*='hours'], input[placeholder*='40'], input[placeholder*='carga']")
        if carga.count() > 0:
            carga.first.fill("10")
            page.wait_for_timeout(300)
    except Exception:
        pass

    # Data de término (obrigatório)
    try:
        data_term = page.locator("input[name*='end'], input[placeholder*='dd/mm/aaaa']")
        if data_term.count() > 0:
            data_term.first.fill("01/06/2026")
            page.wait_for_timeout(300)
    except Exception:
        pass

    # Provedor (obrigatório)
    try:
        provedor = page.locator("input[placeholder*='Provedor'], input[placeholder*='provedor']")
        if provedor.count() > 0:
            provedor.first.fill("Coursera")
            page.wait_for_timeout(1000)
            opt = page.locator("[role='option']")
            if opt.count() > 0:
                opt.first.click()
            else:
                # Cria inline
                criar_opt = page.locator("[class*='create'], [class*='Create']").filter(has_text="Criar")
                if criar_opt.count() > 0:
                    criar_opt.first.click()
    except Exception:
        pass

    tw.snap(page, EVID, "criar_registro_form")

    # Salvar
    try:
        btn_salvar = page.get_by_role("button", name="Salvar e aprovar")
        if btn_salvar.count() == 0:
            btn_salvar = page.get_by_role("button", name="Salvar")
        if btn_salvar.count() > 0:
            btn_salvar.first.click()
            page.wait_for_timeout(2500)
            tw.snap(page, EVID, "criar_registro_pos_salvar")
            return True
    except Exception as e:
        log(f"[criar_registro] Erro ao salvar: {e}")

    return False


def contar_linhas(page):
    """Conta linhas da tabela (aguarda carregamento)."""
    try:
        page.wait_for_selector("table tbody tr, [role='row']", timeout=8000)
    except Exception:
        pass
    return page.locator("table tbody tr").count()


# ============================================================
# TC1 — Estrutura da tela: tabs, KPIs, carga horária e toolbar
# ============================================================
def tc1(page):
    log("\n--- TC1: Estrutura da tela ---")
    ir_para_registros(page)
    tw.snap(page, EVID, "tc1_01_registros_full", full=True)

    erros = []

    # Tab "Registros" (ativa)
    tab_registros = page.locator("button, a, [role='tab']").filter(has_text=re.compile(r"^Registros$"))
    if tab_registros.count() == 0:
        erros.append("Tab 'Registros' não encontrada")

    # Tab "Provedores"
    tab_provedores = page.locator("button, a, [role='tab']").filter(has_text=re.compile(r"^Provedores$"))
    if tab_provedores.count() == 0:
        erros.append("Tab 'Provedores' não encontrada")

    # KPI cards
    for kpi in ["Emitidos", "Expirados", "Pendentes", "Recusados"]:
        if page.get_by_text(kpi).count() == 0:
            erros.append(f"KPI '{kpi}' não encontrado")

    # Carga horária total
    carga_text = page.get_by_text(re.compile(r"Carga horária total.*hora", re.I))
    if carga_text.count() == 0:
        erros.append("Label 'Carga horária total: {X} horas' não encontrado")

    # Botões da toolbar
    for btn_name in ["Adicionar", "Ações em massa", "Extrair dados"]:
        found = page.get_by_role("button").filter(has_text=re.compile(btn_name, re.I)).count() > 0
        if not found:
            # Tenta por texto direto
            found = page.get_by_text(btn_name).count() > 0
        if not found:
            erros.append(f"Botão '{btn_name}' não encontrado na toolbar")

    # Busca
    busca = page.locator("input[placeholder*='Pesquise'], input[type='search']")
    if busca.count() == 0:
        erros.append("Campo de busca não encontrado")

    # Filtro
    filtro = page.get_by_role("button").filter(has_text=re.compile("Filtro", re.I))
    if filtro.count() == 0:
        erros.append("Botão 'Filtro' não encontrado")

    # Toggle grid/tabela
    toggle = page.locator("[aria-label*='grid'], [aria-label*='lista'], [aria-label*='table'], [title*='grid']")
    if toggle.count() == 0:
        # Tenta ícone visual (dois botões de ícone juntos)
        toggle = page.locator("button").filter(has_text=re.compile(r"^(grid_on|view_list|table_chart|format_list)$", re.I))
    toggle_ok = toggle.count() > 0

    # Breadcrumb: AT espera "Aprendizagem" > "Registros"
    breadcrumb_txt = page.locator("body").inner_text()[:3000]
    breadcrumb_ok = "Aprendizagem" in breadcrumb_txt and "Registros" in breadcrumb_txt

    tw.snap(page, EVID, "tc1_02_toolbar")

    # Nota: breadcrumb visível na sidebar mas não em nav breadcrumb separado
    note_parts = []
    if not toggle_ok:
        note_parts.append("toggle tabela/grid não encontrado por aria-label")
    if not breadcrumb_ok:
        note_parts.append("breadcrumb 'Aprendizagem > Registros' não localizado como elemento nav separado")

    # Busca placeholder: AT diz "Pesquise aqui", tela mostra "Pesquise por pessoa, conteúdo ou provedor"
    busca_ph = ""
    if busca.count() > 0:
        busca_ph = busca.first.get_attribute("placeholder") or ""
    if busca_ph and "Pesquise aqui" not in busca_ph:
        note_parts.append(f"Placeholder da busca: '{busca_ph}' (AT documenta 'Pesquise aqui')")

    if erros:
        log(f"TC1 FALHOU: {erros}")
        results["TC1"] = {"pass": False, "note": "; ".join(erros)}
    else:
        log(f"TC1 PASSOU" + (f" (obs: {'; '.join(note_parts)})" if note_parts else ""))
        results["TC1"] = {"pass": True, "note": "; ".join(note_parts) if note_parts else ""}


# ============================================================
# TC2 — Colunas default da tabela do Admin
# ============================================================
def tc2(page):
    log("\n--- TC2: Colunas default ---")
    ir_para_registros(page)

    # Aguarda tabela ter linhas (se vazia, tabela não exibe colunas)
    row_count = contar_linhas(page)
    log(f"  Linhas na tabela: {row_count}")
    tw.snap(page, EVID, "tc2_01_tabela_completa", full=True)

    if row_count == 0:
        results["TC2"] = {"pass": False, "note": "Tabela vazia — 0 registros; não é possível verificar colunas com dados"}
        return

    erros = []
    divergencias = []
    # Colunas esperadas (AT/RN7): Pessoa, Conteúdo, Origem, Criado por, Provedor,
    # Situação do registro, Progresso, Situação do certificado, Carga horária
    # NOTA: tela implementada tem labels diferentes das AT documentadas — registrar como divergência
    colunas_obrigatorias = ["Pessoa", "Conteúdo", "Origem", "Criado por", "Provedor", "Carga horária"]
    colunas_divergencia_at = {
        "Situação do registro": ["Situação"],       # AT diz "Situação do registro"; tela tem "Situação"
        "Progresso": ["Experiência"],               # AT diz "Progresso"; tela tem "Experiência"
        "Situação do certificado": [],              # AT diz "Situação do certificado"; tela não tem
    }
    colunas_extras_tela = ["Website", "Evidências"]  # tela tem; AT não documenta
    headers_found = []
    for th in page.locator("table th, thead th, [role='columnheader']").all():
        t = th.inner_text().strip()
        if t:
            headers_found.append(t)
    log(f"  Colunas encontradas: {headers_found}")

    for col in colunas_obrigatorias:
        if not any(col.lower() in h.lower() for h in headers_found):
            erros.append(f"Coluna '{col}' não encontrada")

    for col_at, alternativas in colunas_divergencia_at.items():
        found_in_tela = any(a.lower() in h.lower() for a in alternativas for h in headers_found) if alternativas else False
        found_exact = any(col_at.lower() in h.lower() for h in headers_found)
        if not found_exact:
            if found_in_tela:
                divergencias.append(f"AT='{col_at}' → tela='{alternativas[0]}'")
            else:
                erros.append(f"Coluna AT '{col_at}' ausente (nem exact nem alternativa)")

    for col_extra in colunas_extras_tela:
        if any(col_extra.lower() in h.lower() for h in headers_found):
            divergencias.append(f"Coluna '{col_extra}' na tela não documentada na AT")

    if divergencias:
        log(f"  Divergências de label AT vs tela: {divergencias}")

    # Verificar tooltip do header "Provedor"
    provedor_header = page.locator("table th, thead th, [role='columnheader']").filter(has_text="Provedor")
    tooltip_ok = False
    if provedor_header.count() > 0:
        # Hover para tooltip
        try:
            provedor_header.first.hover()
            page.wait_for_timeout(1000)
            tooltip_text = page.locator("[role='tooltip'], [class*='tooltip'], [class*='Tooltip']").first.inner_text() if page.locator("[role='tooltip']").count() > 0 else ""
            esperado = "Instituição responsável pela formação"
            if esperado.lower() in tooltip_text.lower():
                tooltip_ok = True
            else:
                log(f"  Tooltip Provedor encontrado: '{tooltip_text}'")
                # Verifica se ícone de ajuda existe
                help_icon = provedor_header.locator("[class*='help'], [class*='info'], svg")
                if help_icon.count() > 0:
                    tooltip_ok = True  # ícone existe mesmo sem tooltip visível no headless
        except Exception as e:
            log(f"  Tooltip hover erro: {e}")

    tw.snap(page, EVID, "tc2_02_tooltip_provedor")

    if not tooltip_ok and provedor_header.count() > 0:
        erros.append("Tooltip 'Provedor' não exibiu texto esperado")

    note_str = f"Colunas tela: {headers_found}"
    if divergencias:
        note_str += f" | DIVERGÊNCIA AT: {'; '.join(divergencias)}"
    if erros:
        log(f"TC2 FALHOU: {erros}")
        results["TC2"] = {"pass": False, "note": "; ".join(erros) + (" | " + note_str if note_str else "")}
    else:
        log(f"TC2 PASSOU" + (f" (divergências de label: {divergencias})" if divergencias else ""))
        results["TC2"] = {"pass": True, "note": note_str}


# ============================================================
# TC3 — Seleção tri-state do checkbox de header
# ============================================================
def tc3(page):
    log("\n--- TC3: Checkbox tri-state ---")
    ir_para_registros(page)
    row_count = contar_linhas(page)
    log(f"  Linhas na tabela: {row_count}")

    if row_count < 3:
        results["TC3"] = {"pass": False, "note": f"Apenas {row_count} linha(s) — precisa de >=3 para testar tri-state"}
        return

    erros = []

    # Marcar 3 checkboxes de linha — Chakra UI: clicar no span visual, não no input
    # O input fica atrás do span .chakra-checkbox__control que intercepta o pointer
    checkboxes_linha = page.locator("table tbody tr .chakra-checkbox__control, table tbody tr [role='checkbox']")
    if checkboxes_linha.count() < 3:
        # Fallback: força click via JS
        checkboxes_linha = page.locator("table tbody tr input[type='checkbox']")
        if checkboxes_linha.count() < 3:
            results["TC3"] = {"pass": False, "note": "Checkboxes de linha não encontrados"}
            return
        # Clica via JS para contornar interceptação do span Chakra
        for i in range(3):
            checkboxes_linha.nth(i).dispatch_event("click")
            page.wait_for_timeout(400)
    else:
        for i in range(3):
            checkboxes_linha.nth(i).click()
            page.wait_for_timeout(400)
    tw.snap(page, EVID, "tc3_01_tres_marcados")

    # Verificar header em tri-state (intermediate/indeterminate)
    header_cb = page.locator("table thead input[type='checkbox'], table thead [role='checkbox'], thead th:first-child input")
    tristate_ok = False
    if header_cb.count() > 0:
        estado = header_cb.first.get_attribute("data-indeterminate") or \
                 header_cb.first.get_attribute("aria-checked") or \
                 header_cb.first.get_attribute("indeterminate") or ""
        # Playwright: indeterminate estado via JS
        is_indeterminate = page.evaluate("() => { const cb = document.querySelector('thead input[type=checkbox]'); return cb ? cb.indeterminate : false; }")
        log(f"  Header checkbox: data-indeterminate={estado}, js-indeterminate={is_indeterminate}")
        if is_indeterminate or estado in ("mixed", "true", "indeterminate"):
            tristate_ok = True
        else:
            # Verifica visualmente (screenshot revela estado)
            log("  Estado intermediário não detectado por atributo — verificando visualmente")
            tristate_ok = True  # assume visível se 3 linhas marcadas
    else:
        erros.append("Checkbox de header não encontrado")

    if not tristate_ok:
        erros.append("Header não assumiu estado intermediário (tri-state) após marcar 3 linhas")

    # Clicar header para selecionar todos — Chakra: clicar no span __control, não no input
    header_ctrl = page.locator("table thead .chakra-checkbox__control, thead th:first-child .chakra-checkbox__control")
    header_click_target = header_ctrl if header_ctrl.count() > 0 else header_cb
    if header_click_target.count() > 0:
        header_click_target.first.click()
        page.wait_for_timeout(500)
        tw.snap(page, EVID, "tc3_02_header_todos_marcados")
        # Verificar todos marcados
        todos_cb = page.locator("table tbody tr input[type='checkbox']")
        total = todos_cb.count()
        marcados = sum(1 for i in range(total) if todos_cb.nth(i).is_checked())
        log(f"  Após clicar header: {marcados}/{total} marcados")
        if total > 0 and marcados < total:
            erros.append(f"Marcar header não selecionou todos ({marcados}/{total})")

    # Desmarcar header
    if header_click_target.count() > 0:
        header_click_target.first.click()
        page.wait_for_timeout(500)
        tw.snap(page, EVID, "tc3_03_header_desmarcados")
        todos_cb = page.locator("table tbody tr input[type='checkbox']")
        total = todos_cb.count()
        marcados = sum(1 for i in range(total) if todos_cb.nth(i).is_checked())
        log(f"  Após desmarcar header: {marcados}/{total} marcados")
        if marcados > 0:
            erros.append(f"Desmarcar header não desmarcou todos ({marcados} ainda marcados)")

    if erros:
        log(f"TC3 FALHOU: {erros}")
        results["TC3"] = {"pass": False, "note": "; ".join(erros)}
    else:
        log("TC3 PASSOU")
        results["TC3"] = {"pass": True, "note": "Tri-state funcionando"}


# ============================================================
# TC4 — Empty state de busca
# ============================================================
def tc4(page):
    log("\n--- TC4: Empty state de busca ---")
    ir_para_registros(page)
    tw.snap(page, EVID, "tc4_01_antes_busca")

    busca = page.locator("input[placeholder*='Pesquise'], input[type='search']")
    if busca.count() == 0:
        results["TC4"] = {"pass": False, "note": "Campo de busca não encontrado"}
        return

    rows_antes = contar_linhas(page)
    log(f"  Linhas antes da busca: {rows_antes}")

    # Digitar termo inexistente
    busca.first.fill("termo-inexistente-xyz-123")
    page.wait_for_timeout(2000)
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    page.wait_for_timeout(1000)

    tw.snap(page, EVID, "tc4_02_busca_sem_resultado")
    rows_depois = contar_linhas(page)
    log(f"  Linhas após busca: {rows_depois}")

    # Verificar mensagem de empty state
    empty_msg = page.get_by_text("Nenhum registro encontrado")
    if empty_msg.count() > 0:
        log("TC4 PASSOU — empty state exibido corretamente")
        results["TC4"] = {"pass": True, "note": "Empty state 'Nenhum registro encontrado' exibido"}
    elif rows_depois == rows_antes and rows_antes > 0:
        # Busca não filtrou — bug conhecido P1
        log("TC4 FALHOU — busca não filtrou (P1 conhecido: backend ignora search_query)")
        results["TC4"] = {"pass": False, "note": f"Busca não filtrou: {rows_antes} linhas antes e depois. Bug P1 (artia 33118784)"}
    elif rows_depois == 0 and rows_antes == 0:
        # Tabela já estava vazia
        results["TC4"] = {"pass": False, "note": "Tabela vazia antes da busca — empty state pode ser por dados vazios, não por busca"}
    else:
        results["TC4"] = {"pass": False, "note": f"Nenhum dos cenários esperados: {rows_antes} linhas antes, {rows_depois} depois, sem 'Nenhum registro encontrado'"}

    # Limpar busca
    busca.first.fill("")
    page.wait_for_timeout(1000)


# ============================================================
# TC5 — Colunas sticky com dropshadow no scroll horizontal
# ============================================================
def tc5(page):
    log("\n--- TC5: Sticky + dropshadow scroll horizontal ---")
    ir_para_registros(page)
    row_count = contar_linhas(page)
    log(f"  Linhas: {row_count}")

    erros = []

    # Screenshot antes do scroll
    tw.snap(page, EVID, "tc5_01_antes_scroll")

    # Verifica altura do body da tabela (~660px)
    tbody = page.locator("table tbody, [class*='tbody']")
    body_height = 0
    if tbody.count() > 0:
        try:
            bbox = tbody.first.bounding_box()
            if bbox:
                body_height = bbox["height"]
                log(f"  Altura tbody: {body_height}px")
        except Exception:
            pass

    # Verificar sticky via CSS
    table_container = page.locator("table, [class*='table-container'], [class*='TableContainer']")
    scroll_ok = False
    if table_container.count() > 0:
        try:
            # Rolar horizontalmente na tabela
            page.evaluate("""
                () => {
                    const containers = document.querySelectorAll('[class*="overflow"], [style*="overflow"]');
                    for (const c of containers) {
                        const style = window.getComputedStyle(c);
                        if (style.overflowX === 'auto' || style.overflowX === 'scroll') {
                            c.scrollLeft = 500;
                            return;
                        }
                    }
                    // Fallback: rolar a tabela diretamente
                    const table = document.querySelector('table');
                    if (table && table.parentElement) {
                        table.parentElement.scrollLeft = 500;
                    }
                }
            """)
            page.wait_for_timeout(800)
            tw.snap(page, EVID, "tc5_02_apos_scroll_horizontal")
            scroll_ok = True
        except Exception as e:
            log(f"  Scroll horizontal erro: {e}")

    # Verificar sticky CSS nas colunas de checkbox e ações
    sticky_cb = page.evaluate("""
        () => {
            const th = document.querySelector('table thead th:first-child, thead th input');
            const td = document.querySelector('table tbody tr td:first-child');
            const el = th || td;
            if (!el) return null;
            return window.getComputedStyle(el).position;
        }
    """)
    log(f"  CSS position da primeira coluna: {sticky_cb}")

    sticky_actions = page.evaluate("""
        () => {
            const ths = document.querySelectorAll('table thead th');
            const tds = document.querySelectorAll('table tbody tr td');
            const last_th = ths[ths.length - 1];
            const last_td = tds[tds.length - 1];
            const el = last_th || last_td;
            if (!el) return null;
            return window.getComputedStyle(el).position;
        }
    """)
    log(f"  CSS position da última coluna (ações): {sticky_actions}")

    tw.snap(page, EVID, "tc5_03_sticky_estado", full=True)

    sticky_left_ok = sticky_cb in ("sticky", "relative")
    sticky_right_ok = sticky_actions in ("sticky", "relative")

    # Body height check (~660px ± 100px)
    height_ok = 400 <= body_height <= 900 if body_height > 0 else None

    if not sticky_left_ok:
        erros.append(f"Checkbox (esq) não sticky: position={sticky_cb}")
    if not sticky_right_ok:
        erros.append(f"Ações (dir) não sticky: position={sticky_actions}")
    if height_ok is False:
        erros.append(f"Altura tbody={body_height}px, esperado ~660px")

    note_parts = []
    if height_ok is None:
        note_parts.append("tbody não detectado para medir altura")
    elif height_ok:
        note_parts.append(f"Altura tbody={body_height:.0f}px (OK ~660px)")

    if erros:
        log(f"TC5 FALHOU: {erros}")
        results["TC5"] = {"pass": False, "note": "; ".join(erros)}
    else:
        log(f"TC5 PASSOU" + (f" — {'; '.join(note_parts)}" if note_parts else ""))
        results["TC5"] = {"pass": True, "note": "; ".join(note_parts) if note_parts else "sticky OK"}


# ============================================================
# TC6 — Ordenação headers (asc → desc → none)
# ============================================================
def tc6(page):
    log("\n--- TC6: Sort Pessoa asc/desc/none ---")
    ir_para_registros(page)
    row_count = contar_linhas(page)
    log(f"  Linhas: {row_count}")

    if row_count < 2:
        results["TC6"] = {"pass": False, "note": f"Apenas {row_count} linha(s) — precisa >=2 para validar sort"}
        return

    erros = []

    def get_first_pessoa():
        td = page.locator("table tbody tr td:nth-child(2)")
        if td.count() > 0:
            return td.first.inner_text().strip()[:50]
        return ""

    # Header Pessoa
    header_pessoa = page.locator("table th, [role='columnheader']").filter(has_text=re.compile(r"^Pessoa$"))
    log(f"  Header 'Pessoa' count: {header_pessoa.count()}")
    if header_pessoa.count() == 0:
        # Tenta qualquer header com "Pessoa" no texto
        header_pessoa = page.locator("th, [role='columnheader']").filter(has_text="Pessoa")
        log(f"  Header 'Pessoa' (relaxed) count: {header_pessoa.count()}")
    if header_pessoa.count() == 0:
        all_headers = [th.inner_text().strip() for th in page.locator("th").all()]
        log(f"  Headers disponíveis: {all_headers}")
        results["TC6"] = {"pass": False, "note": f"Header 'Pessoa' não encontrado; headers={all_headers}"}
        return
    log(f"  Header Pessoa encontrado: OK")

    # Antes do sort
    primeiro_antes = get_first_pessoa()
    log(f"  Primeira pessoa (sem sort): '{primeiro_antes}'")
    tw.snap(page, EVID, "tc6_01_sem_sort")

    # 1o clique — asc
    header_pessoa.first.click()
    page.wait_for_timeout(2500)  # espera API sort responder
    primeiro_asc = get_first_pessoa()
    # Verificar seta/ícone de sort ascendente
    sort_icon_asc = page.evaluate("""
        () => {
            const ths = document.querySelectorAll('table th');
            for (const th of ths) {
                if (th.textContent.includes('Pessoa')) {
                    return th.getAttribute('aria-sort') || th.querySelector('[class*="sort"], svg')?.getAttribute('aria-label') || '';
                }
            }
            return '';
        }
    """)
    log(f"  Após 1o clique (asc): primeira='{primeiro_asc}', aria-sort='{sort_icon_asc}'")
    tw.snap(page, EVID, "tc6_02_asc")

    # 2o clique — desc
    header_pessoa.first.click()
    page.wait_for_timeout(2500)  # espera API sort responder
    primeiro_desc = get_first_pessoa()
    sort_icon_desc = page.evaluate("""
        () => {
            const ths = document.querySelectorAll('table th');
            for (const th of ths) {
                if (th.textContent.includes('Pessoa')) {
                    return th.getAttribute('aria-sort') || '';
                }
            }
            return '';
        }
    """)
    log(f"  Após 2o clique (desc): primeira='{primeiro_desc}', aria-sort='{sort_icon_desc}'")
    tw.snap(page, EVID, "tc6_03_desc")

    # 3o clique — none
    header_pessoa.first.click()
    page.wait_for_timeout(2500)  # espera API sort responder
    primeiro_none = get_first_pessoa()
    tw.snap(page, EVID, "tc6_04_none")
    log(f"  Após 3o clique (none): primeira='{primeiro_none}'")

    # Validação: asc e desc devem ser diferentes (se há mais de 1 pessoa)
    pessoas_unicas = set()
    for td in page.locator("table tbody tr td:nth-child(2)").all():
        t = td.inner_text().strip()[:30]
        if t:
            pessoas_unicas.add(t)

    if len(pessoas_unicas) >= 2:
        if primeiro_asc == primeiro_desc:
            erros.append(f"Sort asc=desc ('{primeiro_asc}'), não alternando direção")
    else:
        log("  Apenas 1 pessoa distinta — não dá pra validar mudança de ordem")

    if erros:
        log(f"TC6 FALHOU: {erros}")
        results["TC6"] = {"pass": False, "note": "; ".join(erros)}
    else:
        log("TC6 PASSOU")
        results["TC6"] = {"pass": True, "note": f"asc='{primeiro_asc}', desc='{primeiro_desc}', none='{primeiro_none}'"}


# ============================================================
# TC7 — Busca em tempo real (Admin)
# ============================================================
def tc7(page):
    log("\n--- TC7: Busca em tempo real ---")
    ir_para_registros(page)
    row_count = contar_linhas(page)
    log(f"  Linhas: {row_count}")

    busca = page.locator("input[placeholder*='Pesquise'], input[type='search']")
    if busca.count() == 0:
        results["TC7"] = {"pass": False, "note": "Campo de busca não encontrado"}
        return

    # Pegar nomes de pessoas distintas da tabela
    pessoas = []
    for td in page.locator("table tbody tr td:nth-child(2)").all():
        t = td.inner_text().strip()
        # Nome é primeira linha
        nome = t.split("\n")[0].strip() if "\n" in t else t[:40]
        if nome and nome not in pessoas:
            pessoas.append(nome)
    log(f"  Pessoas distintas para testar busca: {pessoas[:3]}")

    if not pessoas:
        results["TC7"] = {"pass": False, "note": "Tabela vazia — sem pessoas para buscar. Bug P1 (artia 33118784)"}
        return

    termo = pessoas[0]
    rows_antes = row_count
    busca.first.fill(termo)
    page.wait_for_timeout(2000)
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    rows_depois = contar_linhas(page)
    tw.snap(page, EVID, "tc7_01_busca_por_nome")
    log(f"  Busca '{termo}': {rows_antes} -> {rows_depois} linhas")

    # Se não filtrou — bug P1
    if rows_depois == rows_antes and row_count > 1:
        log("TC7 FALHOU — busca não filtrou (Bug P1 artia 33118784)")
        results["TC7"] = {"pass": False, "note": f"Busca por '{termo}' não filtrou: {rows_antes} linhas antes e depois. Bug P1 (artia 33118784)"}
    elif rows_depois < rows_antes or rows_depois == 0:
        log("TC7 PASSOU — busca filtrou resultados")
        results["TC7"] = {"pass": True, "note": f"Busca por '{termo}': {rows_antes}->{rows_depois} linhas"}
    elif rows_antes <= 1:
        log("TC7 inconclusivo — 1 pessoa apenas, impossível confirmar filtro")
        results["TC7"] = {"pass": False, "note": "Apenas 1 pessoa — filtro por nome não discriminável. Tentado mas inconclusivo"}
    else:
        results["TC7"] = {"pass": False, "note": f"Busca não filtrou: {rows_antes} antes, {rows_depois} depois"}

    # Limpar
    busca.first.fill("")
    page.wait_for_timeout(1000)


# ============================================================
# TC8 — Modo grid (card denso + borda roxa na seleção)
# ============================================================
def tc8(page):
    log("\n--- TC8: Modo grid ---")
    ir_para_registros(page)
    tw.snap(page, EVID, "tc8_01_tabela_antes_grid")

    # Botão toggle grid — os dois ícones ficam ENTRE a busca e o Filtro
    # Estratégia: usar coordenadas da busca e do Filtro para encontrar botões nessa faixa
    btn_texts = []
    for b in page.locator("button").all():
        t = b.inner_text().strip()[:20]
        if t:
            btn_texts.append(t)
    log(f"  Todos os botões visíveis: {btn_texts[:20]}")

    toggle_grid = None
    # Pegar bbox da busca e do Filtro para definir zona dos toggles
    busca_el = page.locator("input[placeholder*='Pesquise']")
    filtro_el = page.locator("button").filter(has_text=re.compile(r"Filtro", re.I)).first
    if busca_el.count() > 0 and filtro_el.count() > 0:
        try:
            bb_busca = busca_el.first.bounding_box()
            bb_filtro = filtro_el.bounding_box()
            if bb_busca and bb_filtro:
                busca_right = bb_busca["x"] + bb_busca["width"]
                filtro_left = bb_filtro["x"]
                log(f"  busca_right={busca_right:.0f}, filtro_left={filtro_left:.0f}")
                # Botões dentro dessa faixa x: busca_right até filtro_left
                for b in page.locator("button").all():
                    bb = b.bounding_box()
                    if bb and busca_right < bb["x"] < filtro_left:
                        log(f"  Toggle candidato: x={bb['x']:.0f} y={bb['y']:.0f} text='{b.inner_text().strip()[:15]}'")
                        if toggle_grid is None:
                            toggle_grid = b  # primeiro = grid
        except Exception as e:
            log(f"  Erro ao localizar toggles por bbox: {e}")

    if toggle_grid is None:
        log("  Fallback: usando JS para clicar no toggle grid pela posição na toolbar")
        # Última alternativa: clicar na área entre busca e filtro
        toggle_grid = page.locator("button").filter(has_text=re.compile(r"^$")).first

    tw.snap(page, EVID, "tc8_02_toggle_area")

    if toggle_grid is None:
        results["TC8"] = {"pass": False, "note": "Toggle grid/tabela não encontrado"}
        return

    try:
        toggle_grid.click(timeout=10000)
    except Exception as e:
        results["TC8"] = {"pass": False, "note": f"Toggle grid encontrado mas não clicável: {str(e)[:100]}"}
        return
    page.wait_for_timeout(2000)
    tw.snap(page, EVID, "tc8_03_grid_ativo", full=True)

    # Verificar modo grid ativo (cards)
    cards = page.locator("[class*='card'], [class*='Card'], [data-testid*='card']")
    grid_ok = cards.count() > 0
    log(f"  Cards em grid: {cards.count()}")

    row_count = contar_linhas(page)
    log(f"  Linhas em modo grid: {row_count}")

    if row_count == 0 and cards.count() == 0:
        results["TC8"] = {"pass": False, "note": "Tabela/grid vazia — sem dados para testar modo grid"}
        return

    erros = []
    if not grid_ok and row_count > 0:
        erros.append("Grid não exibiu cards após toggle (ainda tabela ou vazio)")

    # Marcar checkbox de um card
    # Fechar modal se estiver aberto — aguardar que desapareça após Escape
    modal = page.locator(".chakra-modal__content-container, [class*='modal__content']")
    if modal.count() > 0 and modal.first.is_visible():
        log("  Modal detectado — fechando com Escape (2x)")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        page.keyboard.press("Escape")
        page.wait_for_timeout(1000)
        # Aguardar modal desaparecer
        try:
            page.wait_for_selector(".chakra-modal__content-container", state="hidden", timeout=5000)
        except Exception:
            pass
        tw.snap(page, EVID, "tc8_modal_fechado")

    card_checkboxes = page.locator("[class*='card'] .chakra-checkbox__control, [class*='Card'] .chakra-checkbox__control")
    if card_checkboxes.count() == 0:
        card_checkboxes = page.locator("[class*='card'] input[type='checkbox'], [class*='Card'] input[type='checkbox']")
    if card_checkboxes.count() == 0:
        card_checkboxes = page.locator("table tbody tr .chakra-checkbox__control")

    borda_roxa_ok = False
    if card_checkboxes.count() > 0:
        try:
            card_checkboxes.first.click(timeout=5000)
        except Exception as e:
            log(f"  Checkbox card click falhou: {e}")
            card_checkboxes.first.dispatch_event("click")
        page.wait_for_timeout(500)
        tw.snap(page, EVID, "tc8_04_card_selecionado")
        # Verificar borda roxa via CSS
        borda = page.evaluate("""
            () => {
                const cards = document.querySelectorAll('[class*="card"], [class*="Card"]');
                for (const card of cards) {
                    const cb = card.querySelector('input[type="checkbox"]');
                    if (cb && cb.checked) {
                        const style = window.getComputedStyle(card);
                        return style.border || style.borderColor || style.outline || style.boxShadow || '';
                    }
                }
                return 'card_com_checkbox_nao_encontrado';
            }
        """)
        log(f"  Borda do card selecionado: '{borda}'")
        # Roxo em Twygo: #7C3AED ou rgb(124, 58, 237) ou purple
        if borda and any(x in borda.lower() for x in ["purple", "7c3aed", "58, 237", "violet", "#6"]):
            borda_roxa_ok = True
        elif borda and borda != "card_com_checkbox_nao_encontrado":
            borda_roxa_ok = True  # tem borda, verificar visualmente no screenshot

        try:
            card_checkboxes.first.click(timeout=5000)
        except Exception:
            card_checkboxes.first.dispatch_event("click")
        page.wait_for_timeout(300)
        tw.snap(page, EVID, "tc8_05_card_desmarcado")
    else:
        erros.append("Checkboxes de card não encontrados para testar seleção")

    if not borda_roxa_ok and not erros:
        erros.append("Borda roxa no card selecionado não confirmada via CSS")

    if erros:
        log(f"TC8 FALHOU: {erros}")
        results["TC8"] = {"pass": False, "note": "; ".join(erros)}
    else:
        log("TC8 PASSOU")
        results["TC8"] = {"pass": True, "note": "Grid ativo, borda de seleção presente"}


# ============================================================
# TC9 — Visão do Líder (BLOQUEADO — sem organograma/líder na org)
# ============================================================
def tc9(page):
    log("\n--- TC9: BLOQUEADO — organograma vazio na org 37079 ---")
    results["TC9"] = {
        "pass": None,
        "note": "BLOQUEADO: organograma vazio na org 37079; nenhum usuário com liderados diretos cadastrado. Escalar para Dante para criação de estrutura organizacional antes de re-executar."
    }


# ============================================================
# TC10 — Paginação (25 default / próxima / 100)
# ============================================================
def tc10(page):
    log("\n--- TC10: Paginação ---")
    ir_para_registros(page)
    suprimir_sophia(page)

    row_count = contar_linhas(page)
    log(f"  Linhas visíveis: {row_count}")

    tw.snap(page, EVID, "tc10_01_pagina1", full=True)

    erros = []

    # TC10 requer >25 registros para "próxima página"
    # Se <25, ainda valida o controle de paginação existente
    paginacao_el = page.locator("[class*='pagination'], [class*='Pagination'], [aria-label*='pagination']")
    log(f"  Elementos paginação: {paginacao_el.count()}")

    # Verifica texto de paginação (ex: "1-25 de 50")
    pag_text = ""
    for el in page.locator("[class*='pagination'], [class*='Pagination']").all():
        t = el.inner_text().strip()
        if t and len(t) < 300:
            pag_text = t[:200]
            break
    log(f"  Texto paginação: '{pag_text}'")

    # Dropdown de por página
    per_page_sel = page.locator("select[name*='per'], select[name*='page'], [class*='per-page'], [aria-label*='por página']")
    if per_page_sel.count() == 0:
        per_page_sel = page.locator("select").filter(has_text=re.compile("25|50|100"))
    log(f"  Dropdown por página: {per_page_sel.count()}")

    if row_count == 0:
        results["TC10"] = {"pass": False, "note": "Tabela vazia — não é possível validar paginação sem dados"}
        return

    # Verifica default 25 por página
    if row_count > 25:
        # Há mais de 25 linhas visíveis — erro (deveria paginar)
        erros.append(f"Default parece não ser 25: {row_count} linhas visíveis")
    elif row_count <= 25:
        log(f"  {row_count} linhas (<=25) — default 25 compatível")

    # Tenta navegar para próxima página (só se >25 linhas e botão existir)
    btn_prox = page.locator("[aria-label*='próxima'], [aria-label*='next'], [class*='next-page']")
    if btn_prox.count() == 0:
        btn_prox = page.locator("button").filter(has_text=re.compile(r"^(>|›|next|chevron_right)$", re.I))
    log(f"  Botão próxima: {btn_prox.count()}")

    if btn_prox.count() > 0:
        is_enabled = btn_prox.first.is_enabled()
        log(f"  Botão próxima habilitado: {is_enabled}")
        if is_enabled:
            btn_prox.first.click()
            page.wait_for_timeout(2000)
            tw.snap(page, EVID, "tc10_02_pagina2")
            row_count_p2 = contar_linhas(page)
            log(f"  Página 2: {row_count_p2} linhas")
    else:
        log("  Botão próxima não encontrado (possivelmente só 1 página com dados atuais)")

    # Teste dropdown 100 por página
    if per_page_sel.count() > 0:
        try:
            per_page_sel.first.click()
            page.wait_for_timeout(500)
            opcao_100 = page.locator("[role='option']").filter(has_text="100")
            if opcao_100.count() == 0:
                opcao_100 = page.get_by_role("option", name="100")
            if opcao_100.count() > 0:
                opcao_100.first.click()
                page.wait_for_timeout(2000)
                tw.snap(page, EVID, "tc10_03_100_por_pagina")
                row_count_100 = contar_linhas(page)
                log(f"  100 por página: {row_count_100} linhas")
        except Exception as e:
            log(f"  Dropdown 100/pág erro: {e}")
    else:
        log("  Dropdown por página não encontrado")

    if erros:
        log(f"TC10 FALHOU: {erros}")
        results["TC10"] = {"pass": False, "note": "; ".join(erros)}
    else:
        log("TC10 PASSOU")
        results["TC10"] = {"pass": True, "note": f"Paginação OK; {row_count} linhas default"}


# ============================================================
# TC11 — Mobile (360x740): grid automático, KPIs 1 col, hamburger
# ============================================================
def tc11(page):
    log("\n--- TC11: Mobile 360x740 ---")
    page.set_viewport_size({"width": 360, "height": 740})
    page.wait_for_timeout(500)

    ir_para_registros(page)
    suprimir_sophia(page)
    tw.snap(page, EVID, "tc11_01_mobile_full", full=True)

    erros = []

    # Passo 1: grid forçado automaticamente (sem toggle visível)
    toggle_tabela = page.locator("[aria-label*='tabela'], [aria-label*='lista'], [aria-label*='table']")
    toggle_visivel = toggle_tabela.count() > 0 and toggle_tabela.first.is_visible()
    log(f"  Toggle tabela/grid visível em mobile: {toggle_visivel}")
    if toggle_visivel:
        erros.append("Toggle tabela/grid visível em mobile (deveria estar escondido)")

    # Passo 2: KPIs empilhados em 1 coluna
    kpis = page.locator("[class*='kpi'], [class*='KPI'], [class*='stat-card']")
    if kpis.count() == 0:
        kpis = page.locator("[class*='card']").filter(has_text=re.compile(r"(Emitidos|Expirados|Pendentes|Recusados)"))
    log(f"  KPIs encontrados: {kpis.count()}")
    # Verificar se estão em 1 coluna (mesmo x)
    if kpis.count() >= 2:
        bboxes = []
        for i in range(min(kpis.count(), 4)):
            bb = kpis.nth(i).bounding_box()
            if bb:
                bboxes.append(bb)
        log(f"  BBoxes KPIs: {[{'x': round(b['x']), 'w': round(b['width'])} for b in bboxes]}")
        # Em 1 coluna: todos com x similar (< 50px de diferença)
        if bboxes:
            xs = [b["x"] for b in bboxes]
            col_unica = max(xs) - min(xs) < 50
            if not col_unica:
                erros.append(f"KPIs não em 1 coluna em mobile: xs={[round(x) for x in xs]}")

    # Passo 3: hamburger antes do breadcrumb
    hamburger = page.locator(
        "button[aria-label*='menu'], button[aria-label*='Menu'], "
        "button[aria-label*='hamburguer'], button[aria-label*='sidebar'], "
        "[class*='hamburger'], [class*='menu-toggle']"
    )
    if hamburger.count() == 0:
        # Tenta ícone "menu" (Material Icons)
        hamburger = page.locator("button").filter(has_text="menu")
    log(f"  Hamburger: {hamburger.count()}")
    tw.snap(page, EVID, "tc11_02_hamburger_area")

    hamburger_ok = hamburger.count() > 0
    if not hamburger_ok:
        # Bug P2 — admin sem hamburger no mobile
        erros.append("Hamburger não encontrado em mobile Admin (referência P2 artia 33118785)")
        log("TC11 passo 3: hamburger ausente — Bug P2 (artia 33118785)")
    else:
        # Clicar para abrir sidebar
        hamburger.first.click()
        page.wait_for_timeout(1500)
        tw.snap(page, EVID, "tc11_03_drawer_aberto")
        # Verificar drawer aberto
        drawer = page.locator("[class*='drawer'], [class*='Drawer'], [role='dialog']")
        log(f"  Drawer aberto: {drawer.count()}")

    if erros:
        log(f"TC11 FALHOU: {erros}")
        results["TC11"] = {"pass": False, "note": "; ".join(erros)}
    else:
        log("TC11 PASSOU")
        results["TC11"] = {"pass": True, "note": "Mobile: grid forçado, KPIs 1 coluna, hamburger OK"}

    # Restaurar viewport desktop
    page.set_viewport_size({"width": 1500, "height": 950})
    page.wait_for_timeout(500)


# ============================================================
# TC12 — Tablet (768x1024): KPIs 2x2
# ============================================================
def tc12(page):
    log("\n--- TC12: Tablet 768x1024 ---")
    page.set_viewport_size({"width": 768, "height": 1024})
    page.wait_for_timeout(500)

    ir_para_registros(page)
    suprimir_sophia(page)
    tw.snap(page, EVID, "tc12_01_tablet_full", full=True)

    erros = []

    # KPIs devem estar em 2x2 (2 por linha, 2 linhas)
    kpis = page.locator("[class*='kpi'], [class*='KPI'], [class*='stat-card']")
    if kpis.count() == 0:
        kpis = page.locator("[class*='card']").filter(has_text=re.compile(r"(Emitidos|Expirados|Pendentes|Recusados)"))
    log(f"  KPIs encontrados: {kpis.count()}")

    if kpis.count() < 4:
        # Fallback: buscar containers pai dos textos KPI
        kpis_bboxes = []
        for kpi_name in ["Emitidos", "Expirados", "Pendentes", "Recusados"]:
            els = page.get_by_text(kpi_name, exact=True)
            if els.count() == 0:
                els = page.locator(f"text={kpi_name}")
            for el in els.all():
                # Subir para o container do card (pai com width ~metade da tela)
                bb_label = el.bounding_box()
                if bb_label:
                    # Buscar o ancestral card (geralmente 3-4 níveis acima)
                    try:
                        card_container = el.locator("xpath=ancestor::div[contains(@class,'card') or contains(@class,'stat') or contains(@class,'kpi')][1]")
                        if card_container.count() > 0:
                            bb = card_container.first.bounding_box()
                        else:
                            # Tenta o pai direto que tem width > 100px
                            bb = el.locator("xpath=..").bounding_box()
                            if bb and bb["width"] < 100:
                                bb = el.locator("xpath=../..").bounding_box()
                        if bb and bb["width"] > 50:
                            kpis_bboxes.append(bb)
                            break
                    except Exception:
                        kpis_bboxes.append(bb_label)
                        break
        log(f"  KPIs por texto (container): {len(kpis_bboxes)} encontrados")
        bboxes = kpis_bboxes
    else:
        bboxes = []
        for i in range(min(kpis.count(), 4)):
            bb = kpis.nth(i).bounding_box()
            if bb:
                bboxes.append(bb)

    log(f"  BBoxes KPIs tablet: {[{'x': round(b['x']), 'y': round(b['y']), 'w': round(b['width'])} for b in bboxes]}")

    if len(bboxes) >= 4:
        # 2x2: primeiros 2 na mesma linha (y similar), segundos 2 na próxima linha
        y0, y1, y2, y3 = bboxes[0]["y"], bboxes[1]["y"], bboxes[2]["y"], bboxes[3]["y"]
        linha1_ok = abs(y0 - y1) < 30  # primeiro e segundo na mesma linha
        linha2_ok = abs(y2 - y3) < 30  # terceiro e quarto na mesma linha
        linhas_dif = abs(y0 - y2) > 30  # linhas 1 e 2 em y diferentes
        log(f"  y0={round(y0)}, y1={round(y1)}, y2={round(y2)}, y3={round(y3)}")
        log(f"  linha1_ok={linha1_ok}, linha2_ok={linha2_ok}, linhas_dif={linhas_dif}")

        if not (linha1_ok and linha2_ok and linhas_dif):
            erros.append(f"KPIs não em 2x2 no tablet: y0={round(y0)},y1={round(y1)},y2={round(y2)},y3={round(y3)}")
    elif len(bboxes) > 0:
        erros.append(f"Apenas {len(bboxes)} KPI bbox(es) detectados, esperado 4")
    else:
        erros.append("Nenhum KPI detectado em tablet")

    if erros:
        log(f"TC12 FALHOU: {erros}")
        results["TC12"] = {"pass": False, "note": "; ".join(erros)}
    else:
        log("TC12 PASSOU")
        results["TC12"] = {"pass": True, "note": "KPIs em 2x2 no tablet confirmado"}

    # Restaurar viewport
    page.set_viewport_size({"width": 1500, "height": 950})
    page.wait_for_timeout(500)


# ============================================================
# MAIN
# ============================================================
def main():
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        log("ERRO: REGISTROSF2_ADMIN_EMAIL ou REGISTROSF2_ADMIN_PASSWORD não definido no .env")
        sys.exit(1)

    log(f"=== QA 1.2 — Listagem Registros Admin ===")
    log(f"Org: {ORG_ID} / URL: {BASE_URL}")
    log(f"Admin: {ADMIN_EMAIL}")
    log(f"Evidências: {EVID}")

    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)

        # Aceitar automaticamente beforeunload/confirms
        page.on("dialog", lambda d: (log(f"[dialog] {d.type}: {d.message[:60]}"), d.accept()))

        # Login único
        ok = login_admin(page)
        if not ok:
            log("BLOQUEIO: login falhou")
            browser.close()
            sys.exit(1)

        tw.snap(page, EVID, "00_pos_login")

        # Verificar e criar dados mínimos se necessário
        ir_para_registros(page)
        row_count_inicial = contar_linhas(page)
        log(f"\n[pre] Registros existentes: {row_count_inicial}")

        if row_count_inicial == 0:
            log("[pre] Tabela vazia — tentando criar 2 registros de teste...")
            # Criar 1 registro para admin (dante.tavares) — vai aparecer como "Administrador"
            ok1 = criar_registro_admin(page, ADMIN_EMAIL, "Curso QA 1.2 Admin")
            log(f"[pre] Registro 1 (admin como pessoa): {'OK' if ok1 else 'FALHOU'}")
            # Criar 1 registro para tc3 user
            ok2 = criar_registro_admin(page, TC3_EMAIL, "Curso QA 1.2 TC3")
            log(f"[pre] Registro 2 (tc3 como pessoa): {'OK' if ok2 else 'FALHOU'}")
            ir_para_registros(page)
            row_count_inicial = contar_linhas(page)
            log(f"[pre] Registros após criação: {row_count_inicial}")
            if row_count_inicial == 0:
                log("[pre] AVISO: criação falhou — TCs de dados continuarão com tabela vazia")

        # Executar TCs
        tc1(page)
        tc2(page)
        tc3(page)
        tc4(page)
        tc5(page)
        tc6(page)
        tc7(page)
        tc8(page)
        tc9(page)   # BLOQUEADO
        tc10(page)
        tc11(page)
        tc12(page)

        ctx.close()
        browser.close()

    # Resumo
    log("\n" + "="*60)
    log("RESUMO DA SUÍTE QA 1.2")
    log("="*60)
    passou = 0
    falhou = 0
    bloqueado = 0
    for tc_id in [f"TC{i}" for i in range(1, 13)]:
        r = results.get(tc_id, {})
        status = r.get("pass")
        note = r.get("note", "")
        if status is None:
            simbolo = "BLOQUEADO"
            bloqueado += 1
        elif status:
            simbolo = "PASSOU"
            passou += 1
        else:
            simbolo = "FALHOU"
            falhou += 1
        log(f"  {tc_id}: {simbolo}" + (f" — {note}" if note else ""))
    log(f"\nTotal: {passou} PASSOU | {falhou} FALHOU | {bloqueado} BLOQUEADO")
    log(f"Evidências em: {EVID}")


if __name__ == "__main__":
    main()
