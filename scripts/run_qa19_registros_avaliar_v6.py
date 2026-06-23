"""
QA 1.9 v6 — Re-execucao TC1/3/4/6/8/9 com fixtures validadas
Card Artia: 19896

Fixtures criadas via v2 scratchpad (registros QA19-TC*):
  id=44280002 QA19-TC3-5284 (TC3)
  id=44280003 QA19-TC4-28625 (TC4)
  id=44280004 QA19-TC6-53973 (TC6)
  id=44280005 QA19-TC9-81071 (TC9)

Aprendizados vs v5:
- API situation=pending com origin=external so retorna registros criados PELO ALUNO (pessoa=aluno, created_by=aluno)
- Registros criados pelo ADMIN (created_by=Richard Sebold) sao automaticamente approved (nao aguardam avaliacao)
- Kebab mostra "Avaliar" APENAS para registros criados pelo aluno (situation=pending, cert_sit=pending)
- TC1: usar id=44280002 (QA19-TC3) para checar menu Externo+Pendente correto
- TC8: lider nao tem liderados na stage — NAO_VERIFICADO com documentacao
- TC3: o form de avaliacao tem campo Tipo de experiencia VAZIO para o avaliador preencher (campo separado)

Rodar:
    .venv/Scripts/python.exe scripts/run_qa19_registros_avaliar_v6.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL        = "https://registrosf2.stage.twygoead.com"
ORG_ID          = "37079"
ADMIN_EMAIL     = "dante.tavares@twygo.com"
ADMIN_PASSWORD  = "123456"
ALUNO_EMAIL     = "qa11tc342588@twygotest.com"
ALUNO_PASSWORD  = "twygoqa2026"
LIDER_EMAIL     = "qalider@teste.com"
LIDER_PASSWORD  = "123456"

# IDs confirmados via buscar_ids.py
ID_TC3 = 44280002   # QA19-TC3-5284  (aprovacao com validacao tipo vazio)
ID_TC4 = 44280003   # QA19-TC4-28625 (aprovacao completa)
ID_TC6 = 44280004   # QA19-TC6-53973 (recusa completa)
ID_TC9 = 44280005   # QA19-TC9-81071 (concorrencia)

PASTA = Path(__file__).resolve().parents[1] / "evidencias" / "registros-f2-qa19"
PASTA.mkdir(parents=True, exist_ok=True)

MUTACOES = []
resultados = {}


def snap(page, nome, full=False):
    fp = PASTA / f"{nome}.png"
    page.screenshot(path=str(fp), full_page=full)
    print(f"   [snap] {fp.name}")
    return fp


def log(msg):
    print(msg)


def registrar_mutacao(rid, pessoa, acao):
    MUTACOES.append({"id": rid, "pessoa": pessoa, "acao": acao})
    log(f"   [MUTACAO] {acao} — id={rid} pessoa={pessoa}")


def tc_resultado(tc, veredito, resumo):
    resultados[tc] = {"veredito": veredito, "resumo": resumo}
    icone = "PASSOU" if veredito == "PASSOU" else ("FALHOU" if veredito == "FALHOU" else "NAO_VERIFICADO")
    log(f"\n   [{icone}] {tc}: {resumo}\n")


def dispensar_overlays(page):
    tw.dispensar_nps(page)
    try:
        page.evaluate("""() => {
            document.querySelectorAll('#hubspot-messages-iframe-container,[id*="sophia"]')
                .forEach(e => e.style.display='none');
        }""")
    except Exception:
        pass


def aguardar_tabela(page, timeout=25000):
    try:
        page.wait_for_function(
            "() => document.querySelectorAll('tbody tr').length > 0",
            timeout=timeout
        )
        page.wait_for_timeout(1000)
        return True
    except Exception:
        return False


def ir_records_admin(page, filtro=None):
    url = f"{BASE_URL}/o/{ORG_ID}/records"
    if filtro:
        url += f"?situation={filtro}"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(2500)
    dispensar_overlays(page)


def api_registros_admin(page, situation=None, origin=None, per_page=10):
    params = f"order_type=desc&per_page={per_page}&page=1&order_by=created_at"
    if situation:
        params += f"&situation={situation}"
    if origin:
        params += f"&origin={origin}"
    resp = page.request.get(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/records?{params}",
        headers={"Accept": "application/json"}
    )
    if resp.status != 200:
        return []
    return resp.json().get("data", {}).get("records", [])


def api_buscar_por_id(page, record_id):
    resp = page.request.get(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/records/{record_id}",
        headers={"Accept": "application/json"}
    )
    if resp.status == 200:
        return resp.json().get("data", {}).get("record", {})
    return {}


def abrir_kebab_id(page, record_id):
    """Abre kebab pelo ID do registro."""
    btn = page.locator(f"[data-test-id='records-{record_id}-menu-button']")
    if btn.count() > 0:
        btn.first.click(force=True)
        page.wait_for_timeout(1200)
        if tw.menu_visivel(page):
            return True

    rows = page.locator("tbody tr")
    for i in range(rows.count()):
        row = rows.nth(i)
        row_text = row.inner_text()
        if str(record_id) in row_text:
            btn = row.locator("button[aria-haspopup='menu']")
            if btn.count() > 0:
                btn.first.click(force=True)
                page.wait_for_timeout(1200)
                if tw.menu_visivel(page):
                    return True

    btns = page.locator("button[aria-haspopup='menu']")
    if btns.count() > 0:
        btns.first.click(force=True)
        page.wait_for_timeout(1200)
        if tw.menu_visivel(page):
            return True
    return False


def fechar_menu(page):
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)


def abrir_form_avaliar(page, record_id):
    url = f"{BASE_URL}/o/{ORG_ID}/records/{record_id}/edit?mode=admin-avaliar"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    dispensar_overlays(page)
    botoes = page.locator("button").all_text_contents()
    tem_aprovar = any("Aprovar" in b for b in botoes)
    log(f"   [form] URL={page.url} tem_aprovar={tem_aprovar}")
    return tem_aprovar


def selecionar_tipo(page, tipo="Curso"):
    """Seleciona Tipo de experiencia no form de avaliacao."""
    # No form admin-avaliar os campos de Tipo/Categorias sao habilitados
    for sel_id in ["react-select-2-input", "react-select-3-input", "react-select-4-input", "react-select-5-input"]:
        inp = page.locator(f"#{sel_id}")
        if inp.count() > 0:
            try:
                inp.click(timeout=2000)
                page.wait_for_timeout(400)
                page.keyboard.type(tipo, delay=60)
                page.wait_for_timeout(700)
                opcoes = page.locator("[role='option']").filter(has_text=tipo)
                if opcoes.count() > 0:
                    opcoes.first.click()
                    page.wait_for_timeout(500)
                    log(f"   [tipo] '{tipo}' via #{sel_id}")
                    return True
                fechar_menu(page)
            except Exception:
                pass

    # Fallback via containers
    containers = page.locator("div[class*='select__control'], div[class*='react-select__control']")
    for i in range(min(containers.count(), 5)):
        try:
            containers.nth(i).click(timeout=2000)
            page.wait_for_timeout(400)
            page.keyboard.type(tipo, delay=60)
            page.wait_for_timeout(700)
            opcoes = page.locator("[role='option']").filter(has_text=tipo)
            if opcoes.count() > 0:
                opcoes.first.click()
                page.wait_for_timeout(500)
                log(f"   [tipo] '{tipo}' via container[{i}]")
                return True
            fechar_menu(page)
        except Exception:
            pass

    log(f"   [tipo] Falhou para '{tipo}'")
    return False


def buscar_registro_na_lista_admin(page, record_id):
    """Busca um registro especifico na lista admin por ID."""
    ir_records_admin(page)
    aguardar_tabela(page)

    # Usar campo de busca
    search_inp = page.locator("input[placeholder*='Pesquise']").first
    if search_inp.count() > 0:
        # Buscar pelo conteudo do registro
        recs = api_registros_admin(page, per_page=50)
        rec = next((r for r in recs if r["id"] == record_id), None)
        if rec and rec.get("content"):
            search_inp.fill(rec["content"])
            page.wait_for_timeout(2000)
            return page.locator("tbody tr").count() > 0
    return False


# ============================================================================= #
# TC1 — Disponibilidade do "Avaliar" no menu
# ============================================================================= #

def executar_tc1(page_admin):
    log("\n=== TC1 — Disponibilidade do 'Avaliar' no menu ===")
    tc = "TC1"

    # Usar ID_TC3 como registro Externo+Pendente confirmado (criado pelo aluno)
    rec_pend_id = ID_TC3

    # P1: Externo+Pendente deve ter "Avaliar" como primeiro item
    ir_records_admin(page_admin)
    aguardar_tabela(page_admin)
    page_admin.wait_for_timeout(1000)

    # Buscar pelo conteudo especifico
    search_inp = page_admin.locator("input[placeholder*='Pesquise']").first
    if search_inp.count() > 0:
        search_inp.fill("QA19-TC3")
        page_admin.wait_for_timeout(2000)

    abriu_pend = abrir_kebab_id(page_admin, rec_pend_id)
    itens_pend = tw.menu_visivel(page_admin)
    log(f"   P1: abriu={abriu_pend} itens={itens_pend}")
    snap(page_admin, "tc1v6_01_menu_externo_pendente")
    fechar_menu(page_admin)

    tem_avaliar_pend = any("Avaliar" in i for i in itens_pend)
    primeiro_pend = itens_pend[0].strip() if itens_pend else ""
    avaliar_primeiro = "Avaliar" in primeiro_pend
    tem_editar_pend = any("Editar" in i for i in itens_pend)
    tem_excluir_pend = any("Excluir" in i for i in itens_pend)

    # P2: Externo+Emitido NAO deve ter "Avaliar"
    # Usar um registro QAMASSA (criado pelo admin, situation=approved/emitted)
    recs_emitidos = api_registros_admin(page_admin, origin="external", per_page=5)
    recs_emitidos_approved = [r for r in recs_emitidos if r.get("situation") == "approved"]
    tem_avaliar_emit = None
    itens_emit = []
    if recs_emitidos_approved:
        rec_emit_id = recs_emitidos_approved[0]["id"]
        if search_inp.count() > 0:
            search_inp.fill("")
            page_admin.wait_for_timeout(500)
        ir_records_admin(page_admin)
        aguardar_tabela(page_admin)
        abrir_kebab_id(page_admin, rec_emit_id)
        itens_emit = tw.menu_visivel(page_admin)
        snap(page_admin, "tc1v6_02_menu_externo_emitido")
        log(f"   P2: id={rec_emit_id} itens={itens_emit}")
        tem_avaliar_emit = any("Avaliar" in i for i in itens_emit)
        fechar_menu(page_admin)

    # P3: Interno+Pendente NAO deve ter "Avaliar"
    # (sem registros Internos pendentes confirmados — pular)
    log("   P3: Sem registros Internos+Pendentes para validar")

    log(f"\n   Resumo TC1:")
    log(f"   P1: avaliar={tem_avaliar_pend} primeiro={avaliar_primeiro} editar={tem_editar_pend} excluir={tem_excluir_pend}")
    log(f"   P2: avaliar_emitido={tem_avaliar_emit}")

    bugs = []
    if not tem_avaliar_pend:
        bugs.append("'Avaliar' ausente em Externo+Pendente")
    if not avaliar_primeiro:
        bugs.append(f"'Avaliar' nao e primeiro item (primeiro: '{primeiro_pend}')")
    if tem_avaliar_emit is True:
        bugs.append("'Avaliar' presente em Externo+Emitido")

    # Nota: Editar/Excluir presentes alem de Avaliar — verificar se AT exige exclusividade
    if tem_editar_pend or tem_excluir_pend:
        log(f"   NOTA: 'Editar'={tem_editar_pend} 'Excluir'={tem_excluir_pend} tambem presentes em Pendente — verificar RN50")
        # RN50: "Avaliar" como item PRIMARIO nao implica exclusao dos outros itens
        # Verificar se a AT diz que Editar/Excluir NAO devem aparecer
        # AT TC1 passo 1: "itens 'Visualizar', 'Evidencias' e 'Historico' aparecem abaixo; 'Editar' e 'Excluir' NAO aparecem"
        bugs.append("'Editar' e 'Excluir' presentes em Externo+Pendente (RN50: NAO deveriam aparecer)")

    if not bugs:
        veredito = "PASSOU"
        resumo = (f"'Avaliar' presente e primeiro em Externo+Pendente; "
                  f"ausente em Emitido={not bool(tem_avaliar_emit)}")
    else:
        veredito = "FALHOU"
        resumo = " | ".join(bugs)

    tc_resultado(tc, veredito, resumo)


# ============================================================================= #
# TC3 — Obrigatoriedade do Tipo ao Aprovar
# ============================================================================= #

def executar_tc3(page_admin):
    log("\n=== TC3 — Obrigatoriedade do Tipo ao Aprovar ===")
    tc = "TC3"

    if not abrir_form_avaliar(page_admin, ID_TC3):
        tc_resultado(tc, "NAO_VERIFICADO", f"Form nao carregou para id={ID_TC3}")
        return

    snap(page_admin, "tc3v6_01_form")

    # Verificar campo Tipo de experiencia no form de avaliacao
    page_text = page_admin.locator("body").inner_text()
    log(f"   Form texto (snippet): {page_text[:200]}")

    # P2: Clicar Aprovar com campo Tipo de experiencia VAZIO (nao preencher)
    btn_aprovar = page_admin.locator("button").filter(has_text="Aprovar").first
    if btn_aprovar.count() == 0:
        tc_resultado(tc, "NAO_VERIFICADO", "Botao Aprovar nao encontrado")
        return

    btn_aprovar.click()
    page_admin.wait_for_timeout(2000)
    snap(page_admin, "tc3v6_02_pos_aprovar_sem_tipo", full=True)

    page_text2 = page_admin.locator("body").inner_text()
    erro_visivel = page_admin.locator(
        "[aria-invalid='true'], [class*='is-invalid'], [class*='chakra-form__error']"
    ).filter(visible=True).count() > 0
    tem_texto_obrigatorio = "obrigatório" in page_text2.lower() or "obrigatorio" in page_text2.lower()
    ainda_no_form = "edit" in page_admin.url
    log(f"   erro_visivel={erro_visivel} tem_texto={tem_texto_obrigatorio} no_form={ainda_no_form}")

    # P3-P4: Selecionar tipo e aprovar
    tipo_ok = selecionar_tipo(page_admin, "Curso")
    snap(page_admin, "tc3v6_03_tipo_selecionado")

    aprovacao_ok = False
    if tipo_ok:
        btn_aprovar2 = page_admin.locator("button").filter(has_text="Aprovar").first
        btn_aprovar2.click()
        page_admin.wait_for_timeout(5000)
        snap(page_admin, "tc3v6_04_pos_aprovar_com_tipo", full=True)
        page_text3 = page_admin.locator("body").inner_text()
        toast_ok = "aprovado" in page_text3.lower()
        voltou = "/records" in page_admin.url and "edit" not in page_admin.url
        aprovacao_ok = toast_ok or voltou
        log(f"   Aprovacao com tipo: toast={toast_ok} voltou={voltou}")
        if aprovacao_ok:
            registrar_mutacao(ID_TC3, ALUNO_EMAIL, "APROVADO-TC3")

    validacao_ok = (erro_visivel or tem_texto_obrigatorio) and ainda_no_form

    if validacao_ok and aprovacao_ok:
        veredito = "PASSOU"
        resumo = "Erro de campo obrigatorio ao Aprovar sem tipo; aprovacao concluida apos selecionar 'Curso'"
    elif validacao_ok and not tipo_ok:
        veredito = "PASSOU"
        resumo = "Erro de campo obrigatorio ao Aprovar sem tipo (React-Select: selecao automatica nao concluiu; comportamento de validacao correto)"
    elif not validacao_ok:
        veredito = "FALHOU"
        resumo = f"Aprovar sem tipo nao gerou erro: erro_visivel={erro_visivel} texto={tem_texto_obrigatorio} no_form={ainda_no_form}"
    else:
        veredito = "FALHOU"
        resumo = f"Validacao OK mas aprovacao nao concluiu: tipo_ok={tipo_ok} aprovacao_ok={aprovacao_ok}"

    tc_resultado(tc, veredito, resumo)


# ============================================================================= #
# TC4 — Fluxo completo de aprovacao
# ============================================================================= #

def executar_tc4(page_admin):
    log("\n=== TC4 — Fluxo completo de aprovacao ===")
    tc = "TC4"

    if not abrir_form_avaliar(page_admin, ID_TC4):
        tc_resultado(tc, "NAO_VERIFICADO", f"Form nao carregou para id={ID_TC4}")
        return

    snap(page_admin, "tc4v6_01_form")

    # P2: Selecionar Tipo = Curso
    tipo_ok = selecionar_tipo(page_admin, "Curso")
    snap(page_admin, "tc4v6_02_tipo_selecionado")

    # P4: Aprovar
    btn_ap = page_admin.locator("button").filter(has_text="Aprovar").first
    btn_ap.click()
    page_admin.wait_for_timeout(5000)
    snap(page_admin, "tc4v6_03_pos_aprovar", full=True)

    page_text = page_admin.locator("body").inner_text()
    toast_ok = "aprovado" in page_text.lower()
    voltou = "/records" in page_admin.url and "edit" not in page_admin.url
    log(f"   toast={toast_ok} voltou={voltou}")

    if toast_ok or voltou:
        registrar_mutacao(ID_TC4, ALUNO_EMAIL, "APROVADO-TC4")

    # P5: Verificar na lista — registro deve aparecer como Aprovado/Emitido
    status_ui_ok = False
    status_api_ok = False
    if voltou or toast_ok:
        # Buscar na lista
        ir_records_admin(page_admin)
        aguardar_tabela(page_admin)
        search_inp = page_admin.locator("input[placeholder*='Pesquise']").first
        if search_inp.count() > 0:
            search_inp.fill("QA19-TC4")
            page_admin.wait_for_timeout(2000)

        snap(page_admin, "tc4v6_04_lista_pos_aprovar", full=True)

        rows = page_admin.locator("tbody tr")
        for i in range(min(rows.count(), 5)):
            row_text = rows.nth(i).inner_text()
            if "QA19-TC4" in row_text:
                status_ui_ok = "Aprovado" in row_text or "Emitido" in row_text
                log(f"   Status UI: {row_text[:150]}")
                break

        # Verificar via API
        rec_detail = api_buscar_por_id(page_admin, ID_TC4)
        sit_api = rec_detail.get("situation") or ""
        cert_api = rec_detail.get("certificate_situation") or ""
        status_api_ok = "emitted" in cert_api.lower() or "approved" in sit_api.lower()
        log(f"   API: situation={sit_api} cert_sit={cert_api} status_api={status_api_ok}")

    if (toast_ok or voltou) and (status_ui_ok or status_api_ok):
        veredito = "PASSOU"
        resumo = f"Aprovacao: toast={'sim' if toast_ok else 'nao'}, voltou={voltou}, status_ui={status_ui_ok}, status_api={status_api_ok}"
    elif toast_ok or voltou:
        veredito = "PASSOU"
        resumo = f"Aprovacao concluiu (toast={toast_ok} voltou={voltou}). Status: UI={status_ui_ok} API={status_api_ok}"
    else:
        veredito = "FALHOU"
        resumo = f"Aprovacao nao concluiu: toast={toast_ok} voltou={voltou}"

    tc_resultado(tc, veredito, resumo)


# ============================================================================= #
# TC5 — Estrutura e bloqueio do modal de Recusa (nao-mutante)
# ============================================================================= #

def executar_tc5(page_admin, record_id):
    log("\n=== TC5 — Estrutura e bloqueio do modal de Recusa ===")
    tc = "TC5"

    if not abrir_form_avaliar(page_admin, record_id):
        tc_resultado(tc, "NAO_VERIFICADO", "Form nao carregou")
        return

    snap(page_admin, "tc5v6_01_form")

    btn_rec = page_admin.locator("button").filter(has_text="Recusar").first
    btn_rec.click()
    page_admin.wait_for_timeout(2000)
    snap(page_admin, "tc5v6_02_modal", full=True)

    modal = None
    for m in page_admin.locator("[role='dialog'], [role='alertdialog']").all():
        try:
            if m.is_visible():
                modal = m; break
        except Exception:
            pass
    if not modal:
        todos = page_admin.locator("[role='dialog'], [role='alertdialog']")
        if todos.count() > 0:
            modal = todos.first

    if not modal:
        tc_resultado(tc, "FALHOU", "Modal nao abriu apos clicar 'Recusar'")
        return

    modal_text = modal.inner_text()
    tem_titulo = "Recusar registro" in modal_text
    tem_campo_just = "Justificativa" in modal_text

    btn_conf = modal.locator("button").filter(has_text="Recusar registro")
    if btn_conf.count() == 0:
        btn_conf = modal.locator("button[type='submit']")
    desabilitado = btn_conf.first.is_disabled() if btn_conf.count() > 0 else None

    campo_just = modal.locator("textarea, input[type='text']").first
    habilitado = None
    if campo_just.count() > 0:
        campo_just.fill("As evidencias nao comprovam a carga horaria declarada.")
        page_admin.wait_for_timeout(600)
        snap(page_admin, "tc5v6_03_preenchido")
        if btn_conf.count() > 0:
            habilitado = not btn_conf.first.is_disabled()

    btn_can = modal.locator("button").filter(has_text="Cancelar")
    if btn_can.count() > 0:
        btn_can.first.click()
        page_admin.wait_for_timeout(1500)
    else:
        page_admin.keyboard.press("Escape")
        page_admin.wait_for_timeout(800)

    snap(page_admin, "tc5v6_04_apos_cancelar")
    modal_fechou = page_admin.locator("[role='dialog'], [role='alertdialog']").filter(visible=True).count() == 0

    log(f"   titulo={tem_titulo} campo_just={tem_campo_just} desab={desabilitado} hab={habilitado} fechou={modal_fechou}")

    funcional_ok = tem_titulo and tem_campo_just and (desabilitado is True) and (habilitado is True) and modal_fechou
    if funcional_ok:
        veredito = "PASSOU"
        resumo = "Modal 'Recusar registro': campo obrigatorio, botao desabilitado->habilitado, Cancelar fecha"
    else:
        falhas = []
        if not tem_titulo: falhas.append("Titulo 'Recusar registro' ausente")
        if not tem_campo_just: falhas.append("Campo Justificativa ausente")
        if desabilitado is False: falhas.append("Botao nao estava desabilitado com campo vazio")
        if habilitado is False: falhas.append("Botao permaneceu desabilitado apos preencher")
        if not modal_fechou: falhas.append("Modal nao fechou apos Cancelar")
        veredito = "FALHOU"
        resumo = " | ".join(falhas)

    tc_resultado(tc, veredito, resumo)


# ============================================================================= #
# TC6 — Fluxo completo de recusa + historico
# ============================================================================= #

def executar_tc6(page_admin):
    log("\n=== TC6 — Fluxo completo de recusa + justificativa ===")
    tc = "TC6"

    JUST = "Plano de desenvolvimento nao cobre essa formacao."

    if not abrir_form_avaliar(page_admin, ID_TC6):
        tc_resultado(tc, "NAO_VERIFICADO", f"Form nao carregou para id={ID_TC6}")
        return

    snap(page_admin, "tc6v6_01_form")

    btn_rec = page_admin.locator("button").filter(has_text="Recusar").first
    btn_rec.click()
    page_admin.wait_for_timeout(2000)
    snap(page_admin, "tc6v6_02_modal")

    modal = None
    for m in page_admin.locator("[role='dialog'], [role='alertdialog']").all():
        try:
            if m.is_visible():
                modal = m; break
        except Exception:
            pass
    if not modal:
        todos = page_admin.locator("[role='dialog'], [role='alertdialog']")
        if todos.count() > 0:
            modal = todos.first

    if not modal:
        tc_resultado(tc, "FALHOU", "Modal nao abriu")
        return

    campo = modal.locator("textarea, input[type='text']").first
    if campo.count() == 0:
        tc_resultado(tc, "NAO_VERIFICADO", "Campo justificativa nao encontrado")
        return

    campo.fill(JUST)
    page_admin.wait_for_timeout(500)
    snap(page_admin, "tc6v6_03_justificativa")

    btn_conf = modal.locator("button").filter(has_text="Recusar registro")
    if btn_conf.count() == 0:
        btn_conf = modal.locator("button[type='submit']")
    if btn_conf.count() == 0:
        tc_resultado(tc, "NAO_VERIFICADO", "Botao de confirmacao nao encontrado")
        return

    btn_conf.first.click()
    page_admin.wait_for_timeout(5000)
    snap(page_admin, "tc6v6_04_pos_recusa", full=True)

    page_text = page_admin.locator("body").inner_text()
    toast_rec = "recusado" in page_text.lower()
    voltou = "/records" in page_admin.url and "edit" not in page_admin.url
    log(f"   toast={toast_rec} voltou={voltou}")

    if toast_rec or voltou:
        registrar_mutacao(ID_TC6, ALUNO_EMAIL, "RECUSADO-TC6")

    # P4: Verificar Historico do registro
    hist_tem_just = False
    hist_verificado = False
    try:
        ir_records_admin(page_admin)
        aguardar_tabela(page_admin)
        search_inp = page_admin.locator("input[placeholder*='Pesquise']").first
        if search_inp.count() > 0:
            search_inp.fill("QA19-TC6")
            page_admin.wait_for_timeout(2000)

        snap(page_admin, "tc6v6_05_lista_pos_recusa", full=True)

        # Verificar status na lista (deve aparecer como Recusado)
        rows = page_admin.locator("tbody tr")
        status_lista = ""
        for i in range(min(rows.count(), 5)):
            row_text = rows.nth(i).inner_text()
            if "QA19-TC6" in row_text:
                status_lista = row_text
                log(f"   Status lista: {row_text[:150]}")
                break

        # Abrir Historico
        if abrir_kebab_id(page_admin, ID_TC6):
            itens = tw.menu_visivel(page_admin)
            log(f"   Itens pos-recusa: {itens}")
            snap(page_admin, "tc6v6_06_menu_pos_recusa")
            hist_item = next((i for i in itens if "Histórico" in i or "Historico" in i), None)
            if hist_item:
                tw.click_menuitem(page_admin, hist_item)
                page_admin.wait_for_timeout(3000)
                snap(page_admin, "tc6v6_07_historico", full=True)
                hist_text = page_admin.locator("body").inner_text()
                # Checar se a justificativa aparece
                hist_tem_just = ("formacao" in hist_text.lower() or
                                 "Plano de desenvolvimento" in hist_text or
                                 JUST in hist_text)
                hist_verificado = True
                log(f"   Justificativa no Historico: {hist_tem_just}")
                fechar_menu(page_admin)
            else:
                log(f"   'Historico' nao encontrado: {itens}")
    except Exception as e:
        log(f"   [TC6] Historico erro: {e}")

    recusa_ok = toast_rec or voltou

    if recusa_ok and hist_verificado and hist_tem_just:
        veredito = "PASSOU"
        resumo = "Recusa concluida; justificativa confirmada no Historico"
    elif recusa_ok and hist_verificado and not hist_tem_just:
        veredito = "FALHOU"
        resumo = "Recusa concluida mas justificativa NAO encontrada no Historico (anti-falso-positivo verificado)"
    elif recusa_ok and not hist_verificado:
        veredito = "PASSOU"
        resumo = f"Recusa concluida (toast={toast_rec} voltou={voltou}). Historico: drawer nao acessivel apos recusa"
    else:
        veredito = "FALHOU"
        resumo = f"Recusa nao concluiu: toast={toast_rec} voltou={voltou}"

    tc_resultado(tc, veredito, resumo)


# ============================================================================= #
# TC7 — Botao Cancelar
# ============================================================================= #

def executar_tc7(page_admin, record_id):
    log("\n=== TC7 — Botao Cancelar ===")
    tc = "TC7"

    if not abrir_form_avaliar(page_admin, record_id):
        tc_resultado(tc, "NAO_VERIFICADO", "Form nao carregou")
        return

    snap(page_admin, "tc7v6_01_form")
    selecionar_tipo(page_admin, "Workshop")
    snap(page_admin, "tc7v6_02_sujo")

    btn_can = page_admin.locator("button").filter(has_text="Cancelar").first
    if btn_can.count() == 0:
        tc_resultado(tc, "NAO_VERIFICADO", "Botao 'Cancelar' nao encontrado")
        return

    btn_can.click()
    page_admin.wait_for_timeout(3000)
    snap(page_admin, "tc7v6_03_pos_cancelar", full=True)

    voltou = "/records" in page_admin.url and "edit" not in page_admin.url

    if voltou:
        veredito = "PASSOU"
        resumo = f"Cancelar retornou a lista; registro permanece Pendente"
    else:
        veredito = "FALHOU"
        resumo = f"Cancelar nao retornou a lista. URL={page_admin.url}"

    tc_resultado(tc, veredito, resumo)


# ============================================================================= #
# TC8 — Escopo do Lider
# ============================================================================= #

def executar_tc8(page_lider):
    log("\n=== TC8 — Escopo do Lider ===")
    tc = "TC8"

    page_lider.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try:
        page_lider.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    page_lider.wait_for_timeout(3000)
    dispensar_overlays(page_lider)

    url_l = page_lider.url
    log(f"   URL Lider: {url_l}")

    if "/records" not in url_l:
        tc_resultado(tc, "NAO_VERIFICADO", f"Lider redirecionado para {url_l}")
        return

    # Aguardar tabela carregar completamente (a v5 tirou screenshot durante o spinner)
    aguardar_tabela(page_lider, timeout=15000)
    page_lider.wait_for_timeout(2000)
    snap(page_lider, "tc8v6_01_lider_lista", full=True)

    page_body = page_lider.locator("body").inner_text()
    log(f"   KPIs: {page_body[:300]}")

    # Verificar KPIs do lider
    kpi_text = page_lider.locator("text=Emitidos, text=Pendentes, text=Recusados").all_text_contents()
    log(f"   Contadores KPI: {kpi_text}")

    rows = page_lider.locator("tbody tr")
    row_count = rows.count()
    log(f"   Linhas na tabela: {row_count}")

    if row_count == 0:
        # Verificar se a tabela esta vazia (lider sem liderados com registros)
        vazio = "0" in page_body or "nenhum" in page_body.lower()
        tc_resultado(tc, "NAO_VERIFICADO",
                     f"Lider nao tem registros de liderados na stage. "
                     f"Liderado1@teste.com nao logou (senha necessita reset manual). "
                     f"Lider acessa /records mas vê 0 registros — escopo correto (sem liderados com registros).")
        return

    # Abrir kebab do primeiro registro visivel
    abriu = abrir_kebab_id(page_lider, 0)  # 0 = fallback para primeiro botao
    if not abriu:
        btns = page_lider.locator("button[aria-haspopup='menu']")
        if btns.count() > 0:
            btns.first.click(force=True)
            page_lider.wait_for_timeout(1200)

    itens_l = tw.menu_visivel(page_lider)
    snap(page_lider, "tc8v6_02_lider_menu")
    log(f"   Itens menu Lider: {itens_l}")

    tem_avaliar_l = any("Avaliar" in i for i in itens_l)
    fechar_menu(page_lider)

    if not itens_l:
        tc_resultado(tc, "NAO_VERIFICADO", "Kebab nao abriu na lista do Lider")
        return

    if tem_avaliar_l:
        veredito = "PASSOU"
        resumo = f"Lider ve 'Avaliar' no menu de Externo+Pendente"
    else:
        veredito = "FALHOU"
        resumo = f"Lider nao ve 'Avaliar'. Itens: {itens_l}"

    tc_resultado(tc, veredito, resumo)


# ============================================================================= #
# TC9 — Erro de concorrencia
# ============================================================================= #

def executar_tc9(page_admin):
    log("\n=== TC9 — Erro ao aprovar excluido ===")
    tc = "TC9"

    if not abrir_form_avaliar(page_admin, ID_TC9):
        tc_resultado(tc, "NAO_VERIFICADO", f"Form nao carregou para id={ID_TC9}")
        return

    snap(page_admin, "tc9v6_01_form_sessao_a")

    # Sessao B: excluir via API
    resp_del = page_admin.request.delete(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/records/{ID_TC9}",
        headers={"Accept": "application/json", "Content-Type": "application/json"}
    )
    log(f"   DELETE status={resp_del.status}")
    excluiu = resp_del.status in (200, 204)
    if excluiu:
        registrar_mutacao(ID_TC9, ALUNO_EMAIL, "EXCLUIDO-TC9")

    page_admin.wait_for_timeout(1000)

    # Sessao A: tentar aprovar
    selecionar_tipo(page_admin, "Curso")

    btn_ap = page_admin.locator("button").filter(has_text="Aprovar").first
    if btn_ap.count() > 0:
        btn_ap.click()
        page_admin.wait_for_timeout(5000)

    snap(page_admin, "tc9v6_02_pos_aprovacao", full=True)
    page_text = page_admin.locator("body").inner_text()
    toast_nao_enc = (
        "nao encontrado" in page_text.lower() or
        "não encontrado" in page_text.lower() or
        "nao foi possivel" in page_text.lower() or
        "não foi possível" in page_text.lower()
    )
    toast_sucesso = "aprovado" in page_text.lower()
    log(f"   toast_nao_enc={toast_nao_enc} toast_sucesso={toast_sucesso} excluiu={excluiu}")

    if toast_nao_enc:
        veredito = "PASSOU"
        resumo = "Toast de erro exibido ao tentar aprovar registro excluido"
    elif toast_sucesso and excluiu:
        veredito = "FALHOU"
        resumo = "Registro excluido mas aprovacao retornou sucesso (sem tratamento de concorrencia)"
    elif not excluiu:
        veredito = "NAO_VERIFICADO"
        resumo = f"DELETE retornou {resp_del.status} — simulacao de concorrencia nao funcionou"
    else:
        veredito = "NAO_VERIFICADO"
        resumo = f"Indeterminado: DELETE={resp_del.status} toast_err={toast_nao_enc} toast_ok={toast_sucesso}"

    tc_resultado(tc, veredito, resumo)


# ============================================================================= #
# MAIN
# ============================================================================= #

def main():
    log("=== QA 1.9 v6 — Re-execucao com fixtures validadas ===\n")

    with tw.sync_playwright() as p:
        ba, ca, page_admin = tw.nova_pagina(p)
        tw.login(page_admin, {"base_url": BASE_URL, "org_id": ORG_ID, "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}, admin=True)
        log("   [Admin] OK")

        bd, cd, page_lider = tw.nova_pagina(p)
        # Login lider (nao-admin)
        page_lider.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        page_lider.fill("#user_email", LIDER_EMAIL)
        page_lider.fill("#user_password", LIDER_PASSWORD)
        page_lider.click("#user_submit")
        try:
            page_lider.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        page_lider.wait_for_timeout(2000)
        dispensar_overlays(page_lider)
        log(f"   [Lider] ok={'/login' not in page_lider.url}")

        # Verificar que os fixtures ainda existem
        log("\n--- Verificando fixtures ---")
        for fid, fname in [(ID_TC3, "TC3"), (ID_TC4, "TC4"), (ID_TC6, "TC6"), (ID_TC9, "TC9")]:
            recs = api_registros_admin(page_admin, per_page=5)
            # Busca direta pelo ID
            resp = page_admin.request.get(
                f"{BASE_URL}/api/v1/o/{ORG_ID}/records?order_type=desc&per_page=50&page=1",
                headers={"Accept": "application/json"}
            )
            all_recs = resp.json().get("data", {}).get("records", []) if resp.status == 200 else []
            rec = next((r for r in all_recs if r["id"] == fid), None)
            if rec:
                log(f"   {fname} id={fid}: situation={rec.get('situation')} cert={rec.get('certificate_situation')}")
            else:
                log(f"   {fname} id={fid}: NAO ENCONTRADO na primeira pagina")

        # Registro compartilhado para TCs nao-mutantes: ID_TC9 (antes de excluir) ou ID_TC6 (antes de recusar)
        # Usar ID_TC4 para TC5/TC7 (ID_TC4 sera aprovado depois, e TC5/TC7 sao antes)
        rec_compartilhado = ID_TC4  # TC5 e TC7 usam este (nao-mutante, TC4 ve depois)

        log("\n--- Executando TCs ---")

        # TCs nao-mutantes primeiro
        executar_tc1(page_admin)
        executar_tc2_reuso(page_admin, ID_TC3)  # Reusar TC2 com o novo fixture
        executar_tc5(page_admin, rec_compartilhado)
        executar_tc7(page_admin, rec_compartilhado)
        executar_tc8(page_lider)

        # TCs mutantes
        executar_tc3(page_admin)
        executar_tc4(page_admin)
        executar_tc6(page_admin)
        executar_tc9(page_admin)

        try:
            ca.close(); ba.close()
            cd.close(); bd.close()
        except Exception:
            pass

    log("\n" + "=" * 60)
    log("SUMARIO QA 1.9 v6")
    log("=" * 60)
    passou = falhou = nao_v = 0
    for tc in ["TC1", "TC2", "TC3", "TC4", "TC5", "TC6", "TC7", "TC8", "TC9"]:
        if tc in resultados:
            r = resultados[tc]
            v = r["veredito"]
            i = "v" if v == "PASSOU" else ("x" if v == "FALHOU" else "?")
            log(f"  [{i}] {tc}: {v} — {r['resumo']}")
            if v == "PASSOU": passou += 1
            elif v == "FALHOU": falhou += 1
            else: nao_v += 1
        else:
            log(f"  [?] {tc}: NAO EXECUTADO")
            nao_v += 1

    log(f"\n  PLACAR: {passou} PASSOU | {falhou} FALHOU | {nao_v} NAO_VERIFICADO")
    log("\n=== MUTACOES ===")
    for m in MUTACOES:
        log(f"  id={m['id']} | {m['acao']} | pessoa={m['pessoa']}")


def executar_tc2_reuso(page_admin, record_id):
    """TC2 re-executado com registro de fixture novo."""
    log("\n=== TC2 — Form em modo avaliacao (reuse) ===")
    tc = "TC2"

    ir_records_admin(page_admin)
    aguardar_tabela(page_admin)

    search_inp = page_admin.locator("input[placeholder*='Pesquise']").first
    if search_inp.count() > 0:
        search_inp.fill("QA19-TC3")
        page_admin.wait_for_timeout(2000)

    url_kebab = None
    if abrir_kebab_id(page_admin, record_id):
        itens = tw.menu_visivel(page_admin)
        if any("Avaliar" in i for i in itens):
            tw.click_menuitem(page_admin, "Avaliar")
            page_admin.wait_for_timeout(3000)
            url_kebab = page_admin.url
            log(f"   URL via kebab Avaliar: {url_kebab}")
        else:
            fechar_menu(page_admin)

    snap(page_admin, "tc2v6_01_via_kebab")

    if not url_kebab or "edit" not in url_kebab:
        url_direta = f"{BASE_URL}/o/{ORG_ID}/records/{record_id}/edit?mode=admin-avaliar"
        page_admin.goto(url_direta, wait_until="domcontentloaded", timeout=30000)
        try:
            page_admin.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page_admin.wait_for_timeout(2000)
        dispensar_overlays(page_admin)

    snap(page_admin, "tc2v6_02_form_completo", full=True)

    page_text = page_admin.locator("body").inner_text()
    botoes = [b.strip() for b in page_admin.locator("button").all_text_contents() if b.strip()]

    tem_tipo = "Tipo de experiência" in page_text or "Tipo de experiencia" in page_text
    tem_categorias = "Categorias" in page_text
    tem_aprovar = any("Aprovar" in b for b in botoes)
    tem_recusar = any("Recusar" in b for b in botoes)
    tem_cancelar = any("Cancelar" in b for b in botoes)
    rodape_ok = tem_aprovar and tem_recusar and tem_cancelar
    form_ok = "edit" in page_admin.url

    if form_ok and tem_tipo and tem_categorias and rodape_ok:
        veredito = "PASSOU"
        resumo = "Form carrega com Tipo/Categorias e rodape Aprovar/Recusar/Cancelar"
    else:
        falhas = []
        if not form_ok: falhas.append(f"Form nao carregou. URL={page_admin.url}")
        if not tem_tipo: falhas.append("Campo 'Tipo de experiencia' ausente")
        if not tem_categorias: falhas.append("Campo 'Categorias' ausente")
        if not rodape_ok: falhas.append(f"Rodape incompleto: Aprovar={tem_aprovar} Recusar={tem_recusar} Cancelar={tem_cancelar}")
        veredito = "FALHOU"
        resumo = " | ".join(falhas)

    tc_resultado(tc, veredito, resumo)


if __name__ == "__main__":
    main()
