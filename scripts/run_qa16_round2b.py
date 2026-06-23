"""run_qa16_round2b.py -- QA 1.6 Round 2b: TC7 (provedor Aluno real), TC8, TC15
Re-executar com correcoes de logica apos analise dos resultados parciais.

TC7: verificar ESPECIFICAMENTE o combobox Provedor para Aluno (indice 0)
TC8: corrigir fluxo (fechar modal apos vincular antes de clicar comboboxes)
TC15: idem TC8

Rodar: .venv/Scripts/python.exe scripts/run_qa16_round2b.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL       = "https://registrosf2.stage.twygoead.com"
ORG_ID         = "37079"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
ALUNO_EMAIL    = "qa11tc342588@twygotest.com"
ALUNO_PASSWORD = "twygoqa2026"

SLUG = "registros-f2-qa16"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)

RECORDS_ADMIN_URL = f"{BASE_URL}/o/{ORG_ID}/records"
RECORDS_ALUNO_URL = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"
NEW_FORM_ADMIN    = f"{BASE_URL}/o/{ORG_ID}/records/new"
NEW_FORM_ALUNO    = f"{BASE_URL}/o/{ORG_ID}/records/new?in_use_mode_layout=true"

results = {}


def log(msg):
    print(msg)


def r(tc, passou, nota=""):
    results[tc] = {"pass": passou, "note": nota}
    status = "PASSOU" if passou else "FALHOU"
    print(f"  [{status}] {tc}: {nota}")


def dispensar_overlays(page):
    tw.dispensar_nps(page)
    try:
        page.evaluate("""() => {
            document.querySelectorAll('#hubspot-messages-iframe-container,[id*="sophia"],[id*="hubspot"]')
                .forEach(e => e.style.display='none');
        }""")
    except Exception:
        pass
    try:
        btn = page.locator("button:has-text('Continuar mesmo assim')").first
        if btn.count() > 0 and btn.is_visible():
            btn.click()
            page.wait_for_timeout(500)
    except Exception:
        pass


def fechar_modal_se_aberto(page):
    """Fecha qualquer modal (dialog) aberto na pagina."""
    try:
        modal = page.locator("[role='dialog']").first
        if modal.count() > 0 and modal.is_visible():
            # Tentar fechar com Escape
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            if page.locator("[role='dialog']").count() > 0:
                # Tentar botao Cancelar no modal
                btn_cancel = page.locator("[role='dialog'] button:has-text('Cancelar'), [role='dialog'] button[aria-label='Close']").first
                if btn_cancel.count() > 0:
                    btn_cancel.click()
                    page.wait_for_timeout(500)
    except Exception:
        pass


def aguardar_sem_spinner(page, timeout=15000):
    try:
        page.wait_for_selector(".chakra-spinner", state="hidden", timeout=timeout)
    except Exception:
        pass


def login_como(page, email, senha, admin=False):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", email)
    page.fill("#user_password", senha)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    dispensar_overlays(page)
    if admin:
        page.goto(
            f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
            wait_until="domcontentloaded", timeout=30000,
        )
        page.wait_for_timeout(2000)
        dispensar_overlays(page)
    ok = "/login" not in page.url
    log(f"  [login] {email} -> ok={ok}")
    return ok


def ir_para_form(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dispensar_overlays(page)
    aguardar_sem_spinner(page)
    page.wait_for_timeout(1000)


# ══════════════════════════════════════════════════════════════════════════════
# TC7 -- Provedor para ALUNO: verificar especificamente o combobox correto
# ══════════════════════════════════════════════════════════════════════════════

def tc7_provedor_aluno_real(browser):
    log("\n" + "=" * 60)
    log("TC7 -- Provedor para Aluno (verificacao correta)")
    log("=" * 60)

    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
    page = ctx.new_page()

    respostas_prov = []

    def capturar(resp):
        if "provider" in resp.url.lower() or "event_source" in resp.url.lower() or "get_provider" in resp.url.lower():
            info = {"url": resp.url, "status": resp.status}
            respostas_prov.append(info)
            log(f"  [{resp.status}] API Provedor: {resp.url[:100]}")

    page.on("response", capturar)

    ok = login_como(page, ALUNO_EMAIL, ALUNO_PASSWORD, admin=False)
    if not ok:
        r("TC7", False, "Login Aluno falhou")
        ctx.close()
        return

    ir_para_form(page, NEW_FORM_ALUNO)
    page.wait_for_timeout(2000)  # aguardar requests iniciais

    # Ver a estrutura completa dos comboboxes do form Aluno
    combos = page.locator("[role='combobox']").all()
    log(f"  Total comboboxes no form Aluno: {len(combos)}")

    # Mapear cada combobox: qual e o seu campo?
    # O form Aluno tem: Pessoas (modal), Provedor*, Conteudo*, Tipo*, Categorias*, Carga (input), Data (input)
    # Os comboboxes sao: Provedor (0), Conteudo (1), Tipo (2), Categorias (3)
    # MAS: o form Aluno pode ter "Pessoas" extra via modal (nao combobox)

    log("\n  Mapeando comboboxes do form Aluno:")

    # Primeiro: verificar o combobox 0 (deve ser Provedor para Aluno)
    for idx in range(min(len(combos), 5)):
        try:
            # Re-obter lista de combos a cada iteracao (DOM pode ter mudado)
            combos = page.locator("[role='combobox']").all()
            if idx >= len(combos):
                break

            # Clicar no combobox
            combos[idx].click(timeout=3000)
            page.wait_for_timeout(1200)
            opcoes = page.locator("[role='option']").all_text_contents()
            placeholder_do_select = page.evaluate(f"""() => {{
                const combos = document.querySelectorAll('[role=combobox]');
                if (combos[{idx}]) {{
                    const id = combos[{idx}].getAttribute('aria-describedby') || '';
                    const plEl = document.getElementById(id);
                    return plEl ? plEl.innerText : (combos[{idx}].placeholder || '');
                }}
                return '';
            }}""")

            log(f"  combobox[{idx}]: placeholder='{placeholder_do_select}' opcoes={opcoes[:3]}")

            if idx == 0:
                # Verificar se e o campo Provedor
                provedores_esperados = ["alura", "coursera", "fgv", "udemy", "usp", "linkedin"]
                eh_provedor = any(any(p in op.lower() for p in provedores_esperados) for op in opcoes)
                log(f"  -> eh_provedor={eh_provedor}")
                if eh_provedor:
                    tw.snap(page, EVID, "tc7b_02_provedor_aluno_ok")
                    # Fechar dropdown
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(300)
                    # Provedor existe e listado para Aluno - PASSOU
                    r("TC7", True, f"Provedores visiveis para Aluno no combobox[0]: {opcoes}")
                    ctx.close()
                    return
                elif not opcoes:
                    log(f"  -> dropdown vazio")
                    tw.snap(page, EVID, "tc7b_02_provedor_aluno_vazio")
                    # Verificar resposta de API
                    erros_api = [x for x in respostas_prov if x["status"] >= 400]
                    if erros_api:
                        log(f"  API 401: {erros_api[0]}")
                        r("TC7", False, f"Dropdown Provedor vazio para Aluno. API retornou 401: {erros_api[0]['url'][:80]}. BUG de autorizacao.")
                    else:
                        r("TC7", False, f"Dropdown Provedor vazio para Aluno sem erro de API. Possivel bug de filtro.")
                    ctx.close()
                    return
                else:
                    log(f"  combobox[0] nao e Provedor: {opcoes[:3]}")

            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception as e:
            log(f"  Combobox[{idx}] erro: {e}")
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass
            page.wait_for_timeout(500)

    # Se chegou aqui, nao encontrou provedores de forma alguma
    tw.snap(page, EVID, "tc7b_03_sem_provedores")
    erros_api = [x for x in respostas_prov if x["status"] >= 400]
    if erros_api:
        r("TC7", False, f"Nenhum provedor listado para Aluno. API 401: {erros_api[:2]}")
    else:
        r("TC7", False, f"Nenhum provedor listado para Aluno e sem erro de API. Provedores nao chegam ao Aluno.")

    ctx.close()


# ══════════════════════════════════════════════════════════════════════════════
# TC8 e TC15: Admin com modal fechado corretamente
# ══════════════════════════════════════════════════════════════════════════════

def tc8_tc15_admin(browser):
    log("\n" + "=" * 60)
    log("TC8 + TC15 -- Admin (com fluxo corrigido)")
    log("=" * 60)

    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
    page = ctx.new_page()

    ok = login_como(page, ADMIN_EMAIL, ADMIN_PASSWORD, admin=True)
    if not ok:
        log("  Login Admin falhou")
        r("TC8", False, "Login Admin falhou")
        r("TC15", False, "Login Admin falhou")
        ctx.close()
        return

    # --- TC8: Validacoes da Carga horaria ---
    log("\n[TC8] Carga horaria (Admin)")

    ir_para_form(page, NEW_FORM_ADMIN)
    fechar_modal_se_aberto(page)

    # Estrategia: abrir modal Pessoas, selecionar, fechar, DEPOIS preencher outros
    log("  1. Abrir modal Pessoas")
    try:
        el = page.locator("text=Adicionar pessoas").first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=5000)
            page.wait_for_timeout(2500)
            modal_aberto = page.locator("[role='dialog']").count() > 0
            log(f"  Modal aberto: {modal_aberto}")
            if modal_aberto:
                tw.snap(page, EVID, "tc8b_modal_pessoas_admin")
                # Verificar conteudo do modal
                modal_txt = page.locator("[role='dialog']").first.inner_text()
                log(f"  Modal conteudo: {modal_txt[:150]}")
                nenhum = "Nenhum item" in modal_txt or "nenhum" in modal_txt.lower()
                if nenhum:
                    log("  Modal vazio - Admin nao ve pessoas!")
                    # Fechar modal e registrar
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
                else:
                    # Selecionar primeiro checkbox
                    checkboxes = page.locator("[role='dialog'] input[type='checkbox']").all()
                    log(f"  Checkboxes no modal: {len(checkboxes)}")
                    if checkboxes:
                        checkboxes[0].click()
                        page.wait_for_timeout(500)
                        tw.snap(page, EVID, "tc8b_pessoa_selecionada")
                        # Clicar Vincular
                        btn_vinc = page.locator("button:has-text('Vincular')").first
                        if btn_vinc.count() > 0:
                            btn_vinc.click()
                            page.wait_for_timeout(2000)
                            log("  Pessoa vinculada")
                        else:
                            log("  Botao Vincular nao encontrado")
                            page.keyboard.press("Escape")
    except Exception as e:
        log(f"  Erro ao vincular pessoa: {e}")
        fechar_modal_se_aberto(page)

    # Garantir que modal fechou
    fechar_modal_se_aberto(page)
    page.wait_for_timeout(1000)
    tw.snap(page, EVID, "tc8b_pos_modal_fechado")

    # Verificar que nao ha mais modal
    modal_ainda = page.locator("[role='dialog']").count() > 0
    log(f"  Modal ainda aberto: {modal_ainda}")

    # Agora preencher Provedor (combobox[0])
    log("  2. Preencher Provedor")
    try:
        combos = page.locator("[role='combobox']").all()
        log(f"  Comboboxes disponiveis: {len(combos)}")
        if combos:
            combos[0].click(timeout=5000)
            page.wait_for_timeout(1000)
            opcoes = page.locator("[role='option']").all_text_contents()
            log(f"  Opcoes combobox[0]: {opcoes[:3]}")
            if opcoes:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
    except Exception as e:
        log(f"  Provedor erro: {e}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    # Preencher Conteudo (combobox[1])
    log("  3. Preencher Conteudo")
    try:
        combos = page.locator("[role='combobox']").all()
        if len(combos) > 1:
            combos[1].click(timeout=5000)
            page.wait_for_timeout(1000)
            opcoes = page.locator("[role='option']").all_text_contents()
            if opcoes:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
    except Exception as e:
        log(f"  Conteudo erro: {e}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    # Preencher Tipo de experiencia (combobox[2])
    log("  4. Preencher Tipo de experiencia")
    try:
        combos = page.locator("[role='combobox']").all()
        if len(combos) > 2:
            combos[2].click(timeout=5000)
            page.wait_for_timeout(1000)
            opcoes = page.locator("[role='option']").all_text_contents()
            if opcoes:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
    except Exception as e:
        log(f"  Tipo erro: {e}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    # Preencher Categorias (combobox[3])
    log("  5. Preencher Categorias")
    try:
        combos = page.locator("[role='combobox']").all()
        if len(combos) > 3:
            combos[3].click(timeout=5000)
            page.wait_for_timeout(1000)
            opcoes = page.locator("[role='option']").all_text_contents()
            if opcoes:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
    except Exception as e:
        log(f"  Categorias erro: {e}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    # Preencher Data de termino
    log("  6. Preencher Data")
    try:
        date_inp = page.locator("input[name='endDate']").first
        if date_inp.count() > 0:
            date_inp.fill("2025-06-01")
    except Exception as e:
        log(f"  Data erro: {e}")

    # DEIXAR Carga horaria VAZIA e tentar salvar
    log("  7. Limpar Carga horaria e tentar salvar")
    try:
        inp_carga = page.locator("input[name='workload_seconds']").first
        if inp_carga.count() > 0:
            inp_carga.click()
            inp_carga.select_text()
            page.keyboard.press("Control+a")
            page.keyboard.press("Delete")
            page.wait_for_timeout(300)
    except Exception as e:
        log(f"  Clear carga erro: {e}")

    tw.snap(page, EVID, "tc8b_form_antes_salvar")

    try:
        page.get_by_role("button", name="Salvar").first.click(timeout=5000)
        page.wait_for_timeout(2500)
    except Exception as e:
        log(f"  Click Salvar erro: {e}")

    tw.snap(page, EVID, "tc8b_pos_salvar_carga_vazia")

    erros = page.locator("[class*='chakra-form__error'], [id*='feedback'], [class*='error-message']").all_text_contents()
    log(f"  Erros apos salvar carga vazia: {erros}")

    ainda_no_form = "records/new" in page.url
    log(f"  Ainda no form: {ainda_no_form}, URL: {page.url}")

    # Identificar se ha erro especifico de Carga horaria
    erro_carga = any("carga" in e.lower() or "horária" in e.lower() or "horaria" in e.lower() for e in erros)
    n_erros = len(erros)

    # Verificar se modal de Pessoas abriu novamente (indicaria que Pessoas nao foi preenchida)
    modal_pessoas_voltou = page.locator("[role='dialog']").count() > 0
    log(f"  Modal voltou: {modal_pessoas_voltou}")

    passed_tc8 = erro_carga and ainda_no_form and not modal_pessoas_voltou
    r("TC8", passed_tc8,
      f"Erro_carga={erro_carga}, ainda_no_form={ainda_no_form}, modal_voltou={modal_pessoas_voltou}, n_erros={n_erros}, erros={erros}")

    # --- TC15: Origem Admin ---
    log("\n[TC15] Origem Admin (Externo + Emitido)")

    fechar_modal_se_aberto(page)
    ir_para_form(page, NEW_FORM_ADMIN)
    fechar_modal_se_aberto(page)
    page.wait_for_timeout(1000)
    tw.snap(page, EVID, "tc15b_01_form_admin")

    # Preencher Pessoas via modal
    log("  Pessoas via modal")
    pessoa_preenchida = False
    try:
        el = page.locator("text=Adicionar pessoas").first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=5000)
            page.wait_for_timeout(2500)
            if page.locator("[role='dialog']").count() > 0:
                tw.snap(page, EVID, "tc15b_modal_aberto")
                modal_txt = page.locator("[role='dialog']").first.inner_text()
                nenhum = "Nenhum item" in modal_txt
                if not nenhum:
                    checkboxes = page.locator("[role='dialog'] input[type='checkbox']").all()
                    log(f"  Checkboxes: {len(checkboxes)}")
                    if checkboxes:
                        checkboxes[0].click()
                        page.wait_for_timeout(500)
                        btn_vinc = page.locator("button:has-text('Vincular')").first
                        if btn_vinc.count() > 0:
                            btn_vinc.click()
                            page.wait_for_timeout(2000)
                            pessoa_preenchida = True
                            log("  Pessoa vinculada para TC15")
                else:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
    except Exception as e:
        log(f"  Erro ao vincular pessoa TC15: {e}")
        fechar_modal_se_aberto(page)

    fechar_modal_se_aberto(page)
    page.wait_for_timeout(500)
    tw.snap(page, EVID, "tc15b_pos_modal")

    # Provedor
    try:
        combos = page.locator("[role='combobox']").all()
        if combos:
            combos[0].click(timeout=5000)
            page.wait_for_timeout(800)
            opcoes = page.locator("[role='option']").all_text_contents()
            if opcoes:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
    except Exception as e:
        log(f"  Provedor TC15 erro: {e}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    # Conteudo
    try:
        combos = page.locator("[role='combobox']").all()
        if len(combos) > 1:
            combos[1].click(timeout=5000)
            page.wait_for_timeout(800)
            opcoes = page.locator("[role='option']").all_text_contents()
            if opcoes:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
    except Exception as e:
        log(f"  Conteudo TC15 erro: {e}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    # Tipo
    try:
        combos = page.locator("[role='combobox']").all()
        if len(combos) > 2:
            combos[2].click(timeout=5000)
            page.wait_for_timeout(800)
            opcoes = page.locator("[role='option']").all_text_contents()
            if opcoes:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
    except Exception as e:
        log(f"  Tipo TC15 erro: {e}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    # Categorias
    try:
        combos = page.locator("[role='combobox']").all()
        if len(combos) > 3:
            combos[3].click(timeout=5000)
            page.wait_for_timeout(800)
            opcoes = page.locator("[role='option']").all_text_contents()
            if opcoes:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
    except Exception as e:
        log(f"  Categorias TC15 erro: {e}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    # Carga horaria
    try:
        inp_carga = page.locator("input[name='workload_seconds']").first
        if inp_carga.count() > 0:
            inp_carga.click()
            inp_carga.fill("02:00:00")
            page.wait_for_timeout(300)
    except Exception as e:
        log(f"  Carga TC15 erro: {e}")

    # Data de termino
    try:
        date_inp = page.locator("input[name='endDate']").first
        if date_inp.count() > 0:
            date_inp.fill("2025-06-01")
            page.wait_for_timeout(300)
    except Exception as e:
        log(f"  Data TC15 erro: {e}")

    tw.snap(page, EVID, "tc15b_form_completo")
    log(f"  Pessoa preenchida: {pessoa_preenchida}")

    # Salvar
    try:
        page.get_by_role("button", name="Salvar").first.click(timeout=5000)
        page.wait_for_timeout(4000)
        dispensar_overlays(page)
    except Exception as e:
        log(f"  Salvar TC15 erro: {e}")

    tw.snap(page, EVID, "tc15b_pos_salvar")

    ainda_no_form = "records/new" in page.url
    foi_salvo = not ainda_no_form
    log(f"  URL pos salvar: {page.url}, foi_salvo={foi_salvo}")

    if not foi_salvo:
        erros_save = page.locator("[class*='chakra-form__error'], [id*='feedback']").all_text_contents()
        log(f"  Erros: {erros_save}")
        tw.snap(page, EVID, "tc15b_erros_salvar")
        r("TC15", False, f"Nao salvou. Erros: {erros_save}. Pessoa={pessoa_preenchida}")
        ctx.close()
        return

    # Verificar na lista Admin
    page.goto(RECORDS_ADMIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dispensar_overlays(page)
    aguardar_sem_spinner(page)
    tw.snap(page, EVID, "tc15b_lista_admin")

    lista_txt = page.locator("body").inner_text()
    tem_externo = "Externo" in lista_txt
    tem_aprovado = "Aprovado" in lista_txt or "Emitido" in lista_txt

    try:
        primeira_linha = page.locator("table tbody tr").first
        if primeira_linha.count() > 0:
            linha_txt = primeira_linha.inner_text()
            log(f"  Primeira linha: {linha_txt[:200]}")
    except Exception:
        pass

    tw.snap(page, EVID, "tc15b_origem_status")

    passou = foi_salvo and tem_externo and tem_aprovado
    r("TC15", passou,
      f"Salvo={foi_salvo}, Externo={tem_externo}, Aprovado/Emitido={tem_aprovado}, Pessoa={pessoa_preenchida}")

    ctx.close()


# ══════════════════════════════════════════════════════════════════════════════
# TC14: Origem Aluno -- refazer com logica correta de Provedor
# ══════════════════════════════════════════════════════════════════════════════

def tc14_origem_aluno_v2(browser):
    log("\n" + "=" * 60)
    log("TC14 -- Origem Aluno (Externo + Pendente) v2")
    log("=" * 60)

    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
    page = ctx.new_page()

    ok = login_como(page, ALUNO_EMAIL, ALUNO_PASSWORD, admin=False)
    if not ok:
        r("TC14", False, "Login Aluno falhou")
        ctx.close()
        return

    ir_para_form(page, NEW_FORM_ALUNO)
    page.wait_for_timeout(1000)

    # Mapear comboboxes do Aluno
    combos = page.locator("[role='combobox']").all()
    log(f"  Comboboxes Aluno: {len(combos)}")

    # Preencher Provedor (combobox[0])
    log("  Provedor (combobox[0])")
    provedor_ok = False
    try:
        combos = page.locator("[role='combobox']").all()
        combos[0].click(timeout=5000)
        page.wait_for_timeout(1000)
        opcoes = page.locator("[role='option']").all_text_contents()
        log(f"  Opcoes combobox[0]: {opcoes[:5]}")
        if opcoes:
            page.locator("[role='option']").first.click(timeout=3000)
            page.wait_for_timeout(400)
            provedor_ok = True
        else:
            log("  Provedor vazio - tentar criar inline")
            inp = page.locator("#react-select-2-input").first
            if inp.count() == 0:
                inp = page.locator("[id^='react-select'][id$='-input']").first
            if inp.count() > 0:
                inp.fill("Alura")
                page.wait_for_timeout(800)
                opcoes2 = page.locator("[role='option']").all_text_contents()
                log(f"  Opcoes apos digitar 'Alura': {opcoes2}")
                if opcoes2:
                    page.locator("[role='option']").first.click(timeout=3000)
                    page.wait_for_timeout(400)
                    provedor_ok = True
            page.keyboard.press("Escape")
    except Exception as e:
        log(f"  Provedor erro: {e}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    # Preencher Conteudo (combobox[1])
    log("  Conteudo (combobox[1])")
    try:
        combos = page.locator("[role='combobox']").all()
        if len(combos) > 1:
            combos[1].click(timeout=5000)
            page.wait_for_timeout(1000)
            opcoes = page.locator("[role='option']").all_text_contents()
            if opcoes:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
    except Exception as e:
        log(f"  Conteudo erro: {e}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    # Preencher Tipo (combobox[2])
    log("  Tipo de experiencia (combobox[2])")
    try:
        combos = page.locator("[role='combobox']").all()
        if len(combos) > 2:
            combos[2].click(timeout=5000)
            page.wait_for_timeout(1000)
            opcoes = page.locator("[role='option']").all_text_contents()
            log(f"  Opcoes Tipo: {opcoes}")
            if opcoes:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
    except Exception as e:
        log(f"  Tipo erro: {e}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    # Preencher Categorias (combobox[3])
    log("  Categorias (combobox[3])")
    try:
        combos = page.locator("[role='combobox']").all()
        if len(combos) > 3:
            combos[3].click(timeout=5000)
            page.wait_for_timeout(1000)
            opcoes = page.locator("[role='option']").all_text_contents()
            if opcoes:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
    except Exception as e:
        log(f"  Categorias erro: {e}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    # Preencher Carga horaria
    try:
        inp_carga = page.locator("input[name='workload_seconds']").first
        if inp_carga.count() > 0:
            inp_carga.click()
            inp_carga.fill("01:30:00")
            page.wait_for_timeout(300)
    except Exception as e:
        log(f"  Carga erro: {e}")

    # Preencher Data de termino
    try:
        date_inp = page.locator("input[name='endDate']").first
        if date_inp.count() > 0:
            date_inp.fill("2025-06-01")
            page.wait_for_timeout(300)
    except Exception as e:
        log(f"  Data erro: {e}")

    tw.snap(page, EVID, "tc14b_02_form_preenchido")

    # Clicar Salvar
    try:
        page.get_by_role("button", name="Salvar").first.click(timeout=5000)
        page.wait_for_timeout(4000)
        dispensar_overlays(page)
    except Exception as e:
        log(f"  Salvar erro: {e}")

    tw.snap(page, EVID, "tc14b_03_pos_salvar")

    ainda_no_form = "records/new" in page.url
    foi_salvo = not ainda_no_form
    log(f"  URL pos salvar: {page.url}, foi_salvo={foi_salvo}")

    if not foi_salvo:
        erros_save = page.locator("[class*='chakra-form__error'], [id*='feedback']").all_text_contents()
        log(f"  Erros: {erros_save}")
        tw.snap(page, EVID, "tc14b_erros")
        r("TC14", False, f"Nao salvou. Erros: {erros_save}. Provedor={provedor_ok}")
        ctx.close()
        return

    # Verificar na lista Aluno
    page.goto(RECORDS_ALUNO_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dispensar_overlays(page)
    aguardar_sem_spinner(page)
    tw.snap(page, EVID, "tc14b_04_lista")

    lista_txt = page.locator("body").inner_text()
    tem_externo = "Externo" in lista_txt
    tem_pendente = "Pendente" in lista_txt

    try:
        primeira_linha = page.locator("table tbody tr").first
        if primeira_linha.count() > 0:
            linha_txt = primeira_linha.inner_text()
            log(f"  Primeira linha: {linha_txt[:200]}")
    except Exception:
        pass

    tw.snap(page, EVID, "tc14b_05_origem")

    passou = foi_salvo and tem_externo and tem_pendente
    r("TC14", passou,
      f"Salvo={foi_salvo}, Externo={tem_externo}, Pendente={tem_pendente}, Provedor={provedor_ok}")

    ctx.close()


def main():
    log("=" * 60)
    log("QA 1.6 Round 2b -- TC7 (real), TC8, TC14, TC15")
    log(f"URL: {BASE_URL} | Org: {ORG_ID}")
    log("=" * 60)

    with tw.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=0)

        tc7_provedor_aluno_real(browser)
        tc8_tc15_admin(browser)
        tc14_origem_aluno_v2(browser)

        browser.close()

    log("\n" + "=" * 60)
    log("SUMARIO Round 2b")
    log("=" * 60)
    passou_n = sum(1 for v in results.values() if v["pass"])
    falhou_n = sum(1 for v in results.values() if not v["pass"])
    for tc, dados in sorted(results.items()):
        status = "PASSOU" if dados["pass"] else "FALHOU"
        nota = dados["note"][:120] if dados.get("note") else ""
        log(f"  {tc}: {status} -- {nota}")
    log(f"\n  TOTAL: {passou_n} PASSOU | {falhou_n} FALHOU")
    log("=" * 60)


if __name__ == "__main__":
    main()
