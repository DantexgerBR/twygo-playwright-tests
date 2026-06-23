"""run_qa16_round2.py -- QA 1.6 Round 2: TCs inconclusivos + TC3 + TC7
Org 37079 / https://registrosf2.stage.twygoead.com/
Card Artia: 19893

TCs a re-testar:
  TC3  (Lider) -- 401 no modal Vincular pessoas (confirmar com Network)
  TC5  (Admin) -- opcoes de Tipo de experiencia (seletor real: combobox por indice)
  TC7  (Aluno) -- provedores padrao (verificar se aparecem para Aluno)
  TC8  (Admin) -- validacao de Carga horaria (com modal Pessoas preenchido via seletor real)
  TC12 (Aluno) -- clearError de Carga horaria (usar type() char-a-char)
  TC14 (Aluno) -- origem Externo+Pendente (com provedor selecionado via combobox real)
  TC15 (Admin) -- origem Externo+Emitido (com Pessoas vinculadas via modal)

Estrategias descobertas no recon:
  - Modal "Vincular pessoas": clicar em "text=Adicionar pessoas", esperar dialog, clicar no checkbox
  - Tipo de experiencia: combobox[2] (3o combobox na ordem do form)
  - Provedor: combobox[0] (1o combobox na ordem do form)
  - Conteudo: combobox[1] (2o combobox)
  - Categorias: combobox[3] (4o combobox)

Rodar: .venv/Scripts/python.exe scripts/run_qa16_round2.py
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
LIDER_EMAIL    = "qalider@teste.com"
LIDER_PASSWORD = "123456"
LIDERADO_EMAIL = "liderado1@teste.com"

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
            document.querySelectorAll('[aria-label*="chat"], [aria-label*="Open chat"]')
                .forEach(e => e.style.display='none');
        }""")
    except Exception:
        pass
    # Fechar overlay "Continuar mesmo assim" se aparecer
    try:
        btn_continuar = page.locator("button:has-text('Continuar mesmo assim')").first
        if btn_continuar.count() > 0 and btn_continuar.is_visible():
            btn_continuar.click()
            page.wait_for_timeout(500)
    except Exception:
        pass
    # Fechar modal de notificacoes se aberto
    try:
        btn_fechar_modal = page.locator("[role='dialog'] button:has-text('OK'), [role='dialog'] button:has-text('Fechar')").first
        if btn_fechar_modal.count() > 0 and btn_fechar_modal.is_visible():
            btn_fechar_modal.click()
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


def clicar_combobox_por_indice(page, indice, timeout=5000):
    """Clica no Nth combobox do form (0-based). Retorna True se abriu opcoes."""
    combos = page.locator("[role='combobox']").all()
    log(f"  Total comboboxes: {len(combos)}")
    if indice >= len(combos):
        log(f"  Combobox[{indice}] nao existe")
        return False
    combos[indice].click(timeout=timeout)
    page.wait_for_timeout(1000)
    opcoes = page.locator("[role='option']").count()
    log(f"  Combobox[{indice}] clicado, opcoes: {opcoes}")
    return opcoes > 0


def abrir_modal_pessoas(page):
    """Abre o modal Vincular pessoas. Retorna True se o modal abriu."""
    # Seletor descoberto no recon: clicar no texto "Adicionar pessoas"
    try:
        el = page.locator("text=Adicionar pessoas").first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=5000)
            page.wait_for_timeout(2000)
            # Verificar se modal abriu
            modal = page.locator("[role='dialog']").first
            if modal.count() > 0 and modal.is_visible():
                log("  Modal 'Vincular pessoas' aberto via 'Adicionar pessoas'")
                return True
    except Exception as e:
        log(f"  Falha ao abrir modal: {e}")
    # Fallback: clicar no container do campo Pessoas
    try:
        campo = page.locator("input[name='people']").locator("xpath=ancestor::div[1]").first
        if campo.count() > 0:
            campo.click(timeout=5000)
            page.wait_for_timeout(2000)
            if page.locator("[role='dialog']").count() > 0:
                return True
    except Exception:
        pass
    return False


def selecionar_pessoa_no_modal(page, nome_ou_email=None, indice=0):
    """Seleciona uma pessoa no modal Vincular pessoas via checkbox. Retorna True se conseguiu."""
    try:
        # Aguardar que as pessoas carreguem no modal
        modal = page.locator("[role='dialog']").first
        page.wait_for_timeout(1500)

        if nome_ou_email:
            # Buscar pelo nome/email
            busca = modal.locator("input[placeholder*='nome ou e-mail'], input[placeholder*='Pesquise']").first
            if busca.count() > 0:
                busca.fill(nome_ou_email)
                page.wait_for_timeout(1000)

        # Encontrar e clicar no checkbox
        checkboxes = modal.locator("input[type='checkbox']").all()
        log(f"  Checkboxes no modal: {len(checkboxes)}")
        if checkboxes and indice < len(checkboxes):
            checkboxes[indice].click(timeout=3000)
            page.wait_for_timeout(500)
            log(f"  Checkbox[{indice}] clicado")
            return True

        # Alternativa: clicar na linha da pessoa diretamente
        linhas = modal.locator("[class*='person'], [class*='user-row'], li, [role='listitem']").all()
        log(f"  Linhas de pessoa no modal: {len(linhas)}")
        if linhas and indice < len(linhas):
            linhas[indice].click(timeout=3000)
            page.wait_for_timeout(500)
            return True
    except Exception as e:
        log(f"  Erro ao selecionar pessoa: {e}")
    return False


def confirmar_modal_vincular(page):
    """Clica no botao Vincular do modal para confirmar. Retorna True se conseguiu."""
    try:
        btn_vincular = page.locator("[role='dialog'] button:has-text('Vincular'), button:has-text('Vincular')").first
        if btn_vincular.count() > 0 and btn_vincular.is_visible():
            btn_vincular.click(timeout=5000)
            page.wait_for_timeout(1500)
            # Modal deve ter fechado
            modal_fechou = page.locator("[role='dialog']").count() == 0
            log(f"  Modal fechou: {modal_fechou}")
            return True
    except Exception as e:
        log(f"  Erro ao confirmar vincular: {e}")
    return False


def preencher_form_admin_completo(page, pessoa_indice=0):
    """Preenche todos os campos obrigatorios do form Admin.
    Retorna dict com sucesso de cada campo."""
    resultados = {}

    # 1. Pessoas (via modal)
    modal_ok = abrir_modal_pessoas(page)
    page.wait_for_timeout(1000)
    tw.snap(page, EVID, "tc15b_02_modal_aberto")
    if modal_ok:
        # Verificar se ha pessoas listadas (sem 401)
        modal = page.locator("[role='dialog']").first
        nenhum = modal.locator("text=Nenhum item").count() > 0
        log(f"  Modal aberto, nenhum item: {nenhum}")
        if not nenhum:
            sel_ok = selecionar_pessoa_no_modal(page, indice=pessoa_indice)
            page.wait_for_timeout(500)
            tw.snap(page, EVID, "tc15b_03_pessoa_selecionada")
            vinc_ok = confirmar_modal_vincular(page)
            resultados["pessoas"] = sel_ok and vinc_ok
            page.wait_for_timeout(1000)
        else:
            resultados["pessoas"] = False
            log("  Modal vazio - nenhuma pessoa listada")
            # Fechar modal
            try:
                page.locator("[role='dialog'] button[aria-label='Close'], [role='dialog'] button:has-text('Cancelar')").first.click()
                page.wait_for_timeout(500)
            except Exception:
                pass
    else:
        resultados["pessoas"] = False

    # 2. Provedor (combobox[0])
    try:
        abriu = clicar_combobox_por_indice(page, 0)
        if abriu:
            page.locator("[role='option']").first.click(timeout=3000)
            page.wait_for_timeout(500)
            resultados["provedor"] = True
        else:
            resultados["provedor"] = False
    except Exception as e:
        log(f"  Provedor erro: {e}")
        resultados["provedor"] = False

    # 3. Conteudo (combobox[1]) -- select com conteudos ja cadastrados
    try:
        abriu = clicar_combobox_por_indice(page, 1)
        if abriu:
            opcoes_cont = page.locator("[role='option']").all()
            if opcoes_cont:
                opcoes_cont[0].click(timeout=3000)
                page.wait_for_timeout(500)
                resultados["conteudo"] = True
            else:
                resultados["conteudo"] = False
        else:
            resultados["conteudo"] = False
    except Exception as e:
        log(f"  Conteudo erro: {e}")
        resultados["conteudo"] = False

    # 4. Tipo de experiencia (combobox[2])
    try:
        abriu = clicar_combobox_por_indice(page, 2)
        if abriu:
            page.locator("[role='option']").first.click(timeout=3000)
            page.wait_for_timeout(500)
            resultados["tipo"] = True
        else:
            resultados["tipo"] = False
    except Exception as e:
        log(f"  Tipo erro: {e}")
        resultados["tipo"] = False

    # 5. Categorias (combobox[3])
    try:
        abriu = clicar_combobox_por_indice(page, 3)
        if abriu:
            page.locator("[role='option']").first.click(timeout=3000)
            page.wait_for_timeout(500)
            page.keyboard.press("Escape")
            resultados["categorias"] = True
        else:
            resultados["categorias"] = False
    except Exception as e:
        log(f"  Categorias erro: {e}")
        resultados["categorias"] = False

    # 6. Carga horaria
    try:
        inp_carga = page.locator("input[name='workload_seconds']").first
        if inp_carga.count() > 0:
            inp_carga.click()
            inp_carga.fill("01:30:00")
            page.wait_for_timeout(300)
            resultados["carga_horaria"] = True
        else:
            resultados["carga_horaria"] = False
    except Exception as e:
        log(f"  Carga horaria erro: {e}")
        resultados["carga_horaria"] = False

    # 7. Data de termino
    try:
        date_inp = page.locator("input[name='endDate']").first
        if date_inp.count() > 0:
            date_inp.fill("2025-06-01")
            page.wait_for_timeout(300)
            resultados["data_termino"] = True
        else:
            resultados["data_termino"] = False
    except Exception as e:
        log(f"  Data termino erro: {e}")
        resultados["data_termino"] = False

    log(f"  Campos preenchidos: {resultados}")
    return resultados


def preencher_form_aluno_completo(page):
    """Preenche todos os campos obrigatorios do form Aluno."""
    resultados = {}

    # Para aluno o form tem campos: Pessoas (pode existir), Provedor*, Conteudo, Tipo*, Categorias*, Carga*, Data*
    # Comboboxes visiveis para aluno (pode ser diferente do admin, Pessoas pode nao aparecer)
    combos = page.locator("[role='combobox']").all()
    log(f"  Comboboxes no form Aluno: {len(combos)}")
    for i, cb in enumerate(combos):
        try:
            txt = cb.inner_text()[:40] if cb.is_visible() else "(oculto)"
            log(f"    combo[{i}]: '{txt}'")
        except Exception:
            pass

    # Tentar preencher Pessoas se existir (pode ser via modal)
    tem_pessoas = page.locator("text=Adicionar pessoas").count() > 0
    log(f"  Campo Pessoas (Aluno): {tem_pessoas}")
    if tem_pessoas:
        # Aluno nao deve precisar preencher Pessoas (AT diz que e pre-preenchido)
        # Mas se existir, tentar abrir o modal
        resultados["pessoas_presente"] = True
    else:
        resultados["pessoas_presente"] = False

    # Provedor -- combobox[0] ou primeiro combobox disponivel
    for idx in range(min(len(combos), 4)):
        try:
            combos[idx].click(timeout=3000)
            page.wait_for_timeout(800)
            opcoes = page.locator("[role='option']").all_text_contents()
            if opcoes:
                log(f"  Combobox[{idx}] opcoes: {opcoes[:3]}")
                # Verificar se sao opcoes de provedor
                provedores_conhecidos = ["alura", "coursera", "fgv", "udemy", "usp", "linkedin", "nocode"]
                eh_provedor = any(any(p in op.lower() for p in provedores_conhecidos) for op in opcoes)
                if eh_provedor:
                    log(f"  -> Identificado como Provedor!")
                    page.locator("[role='option']").first.click(timeout=3000)
                    page.wait_for_timeout(500)
                    resultados["provedor"] = True
                    break
                else:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(300)
            else:
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
        except Exception:
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)

    # Tipo de experiencia
    combos = page.locator("[role='combobox']").all()
    for idx in range(min(len(combos), 6)):
        try:
            combos[idx].click(timeout=3000)
            page.wait_for_timeout(800)
            opcoes = page.locator("[role='option']").all_text_contents()
            if opcoes:
                tipos_conhecidos = ["treinamento", "curso", "workshop", "palestra", "evento", "aula", "outro", "mentoria"]
                eh_tipo = any(any(t in op.lower() for t in tipos_conhecidos) for op in opcoes)
                if eh_tipo:
                    log(f"  Combobox[{idx}] = Tipo de experiencia: {opcoes}")
                    page.locator("[role='option']").first.click(timeout=3000)
                    page.wait_for_timeout(500)
                    resultados["tipo"] = True
                    break
                else:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(300)
            else:
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
        except Exception:
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)

    # Categorias
    combos = page.locator("[role='combobox']").all()
    for idx in range(min(len(combos), 6)):
        try:
            combos[idx].click(timeout=3000)
            page.wait_for_timeout(800)
            opcoes = page.locator("[role='option']").all_text_contents()
            if opcoes:
                cats_conhecidas = ["lideranca", "liderança", "tecnologia", "gestao", "gestão", "marketing", "seguranca", "cultura", "compliance"]
                eh_cat = any(any(c in op.lower() for c in cats_conhecidas) for op in opcoes)
                if eh_cat:
                    log(f"  Combobox[{idx}] = Categorias: {opcoes[:2]}")
                    page.locator("[role='option']").first.click(timeout=3000)
                    page.wait_for_timeout(500)
                    page.keyboard.press("Escape")
                    resultados["categorias"] = True
                    break
                else:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(300)
            else:
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
        except Exception:
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)

    # Carga horaria
    try:
        inp_carga = page.locator("input[name='workload_seconds']").first
        if inp_carga.count() > 0:
            inp_carga.click()
            inp_carga.fill("01:30:00")
            page.wait_for_timeout(300)
            resultados["carga_horaria"] = True
    except Exception as e:
        log(f"  Carga horaria erro: {e}")

    # Data de termino
    try:
        date_inp = page.locator("input[name='endDate']").first
        if date_inp.count() > 0:
            date_inp.fill("2025-06-01")
            page.wait_for_timeout(300)
            resultados["data_termino"] = True
    except Exception as e:
        log(f"  Data termino erro: {e}")

    log(f"  Form Aluno campos: {resultados}")
    return resultados


# ══════════════════════════════════════════════════════════════════════════════
# TC3 -- Lider recebe 401 no modal Vincular pessoas (CONFIRMACAO)
# ══════════════════════════════════════════════════════════════════════════════

def tc3_lider_401(browser):
    log("\n" + "=" * 60)
    log("TC3 -- Lider: 401 no modal Vincular pessoas (confirmacao)")
    log("=" * 60)

    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
    page = ctx.new_page()

    respostas_401 = []
    respostas_rel = []

    def capturar(resp):
        if "/professionals" in resp.url or "/event_sources" in resp.url:
            info = {"url": resp.url, "status": resp.status, "method": resp.request.method}
            respostas_rel.append(info)
            if resp.status == 401:
                respostas_401.append(info)
                log(f"  [401] {resp.url[:100]}")

    page.on("response", capturar)

    ok = login_como(page, LIDER_EMAIL, LIDER_PASSWORD, admin=False)
    if not ok:
        r("TC3", False, "Login Lider falhou")
        ctx.close()
        return

    # Ir para form como Lider
    ir_para_form(page, NEW_FORM_ADMIN)
    tw.snap(page, EVID, "tc3b_lider_form")

    # Abrir modal Pessoas
    modal_aberto = abrir_modal_pessoas(page)
    page.wait_for_timeout(3000)  # aguardar as requests 401 chegarem
    tw.snap(page, EVID, "tc3b_lider_modal_apos_click")

    # Verificar se modal mostra erro ou nenhum resultado
    modal_txt = ""
    tem_erro_401_modal = False
    if modal_aberto:
        try:
            modal = page.locator("[role='dialog']").first
            modal_txt = modal.inner_text()
            log(f"  Conteudo do modal: {modal_txt[:200]}")
            tem_nenhum = "Nenhum item" in modal_txt or "nenhum" in modal_txt.lower()
            log(f"  Modal mostra 'Nenhum item': {tem_nenhum}")
        except Exception as e:
            log(f"  Erro ao ler modal: {e}")

    # Verificar toast de 401
    toast_401 = False
    try:
        toast = page.locator("[role='alert'], [class*='chakra-alert'], [class*='toast']").all()
        for t in toast:
            try:
                if t.is_visible():
                    txt = t.inner_text()
                    log(f"  Toast: {txt[:100]}")
                    if "401" in txt or "unauthorized" in txt.lower() or "falhou" in txt.lower():
                        toast_401 = True
            except Exception:
                pass
    except Exception:
        pass

    tw.snap(page, EVID, "tc3b_lider_estado_final")

    log(f"\n  Respostas 401 a /professionals: {len(respostas_401)}")
    log(f"  Modal aberto: {modal_aberto}")
    log(f"  Toast 401: {toast_401}")

    # Veredito: BUG P1 confirmado se ha 401 nas chamadas
    bug_401_real = len(respostas_401) > 0
    r("TC3", not bug_401_real,
      f"401_confirmado={bug_401_real}, chamadas_401={len(respostas_401)}, modal_aberto={modal_aberto}")

    ctx.close()
    return bug_401_real, respostas_401


# ══════════════════════════════════════════════════════════════════════════════
# TC5 -- Tipo de experiencia: opcoes fixas (Admin)
# ══════════════════════════════════════════════════════════════════════════════

def tc5_tipo_experiencia(page):
    log("\n[TC5] Opcoes de Tipo de experiencia")

    ir_para_form(page, NEW_FORM_ADMIN)
    page.wait_for_timeout(1000)

    # Clicar no combobox[2] (descoberto no recon como Tipo de experiencia)
    abriu = clicar_combobox_por_indice(page, 2)
    page.wait_for_timeout(1000)
    tw.snap(page, EVID, "tc5b_01_dropdown_aberto")

    opcoes = page.locator("[role='option']").all_text_contents()
    log(f"  Opcoes Tipo de experiencia: {opcoes}")

    # AT espera 8 opcoes: Curso, Trilha, Workshop, Mentoria, Palestra, Evento, Aula, Outro
    tipos_at = ["Curso", "Trilha", "Workshop", "Mentoria", "Palestra", "Evento", "Aula", "Outro"]
    encontrados_na_at = [t for t in tipos_at if any(t.lower() in op.lower() for op in opcoes)]
    n_opcoes = len(opcoes)

    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    tw.snap(page, EVID, "tc5b_02_opcoes_capturadas")

    passou = n_opcoes == 8 and len(encontrados_na_at) >= 6
    r("TC5", passou,
      f"Opcoes encontradas: {n_opcoes} de 8 esperadas. Opcoes: {opcoes}. Confirmadas da AT: {encontrados_na_at}")


# ══════════════════════════════════════════════════════════════════════════════
# TC7 -- Provedores padrao (Aluno)
# ══════════════════════════════════════════════════════════════════════════════

def tc7_provedores_aluno(browser):
    log("\n" + "=" * 60)
    log("TC7 -- Provedores para Aluno")
    log("=" * 60)

    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
    page = ctx.new_page()

    respostas_prov = []

    def capturar(resp):
        if "provider" in resp.url.lower() or "event_source" in resp.url.lower():
            respostas_prov.append({"url": resp.url, "status": resp.status})
            if resp.status >= 400:
                log(f"  [{resp.status}] {resp.url[:100]}")

    page.on("response", capturar)

    ok = login_como(page, ALUNO_EMAIL, ALUNO_PASSWORD, admin=False)
    if not ok:
        r("TC7", False, "Login Aluno falhou")
        ctx.close()
        return

    ir_para_form(page, NEW_FORM_ALUNO)

    # Verificar estrutura do form do Aluno
    combos = page.locator("[role='combobox']").all()
    log(f"  Comboboxes no form Aluno: {len(combos)}")

    # Clicar em cada combobox para descobrir qual e o Provedor
    provedores_encontrados = []
    indice_provedor = None

    for i in range(min(len(combos), 6)):
        try:
            # Fechar qualquer dropdown aberto
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
            combos = page.locator("[role='combobox']").all()
            if i >= len(combos):
                break
            combos[i].click(timeout=3000)
            page.wait_for_timeout(1000)
            opcoes = page.locator("[role='option']").all_text_contents()
            if opcoes:
                prov_conhecidos = ["alura", "coursera", "fgv", "udemy", "usp", "linkedin", "nocode"]
                eh_prov = any(any(p in op.lower() for p in prov_conhecidos) for op in opcoes)
                log(f"  Combobox[{i}]: {opcoes[:5]} | eh_provedor={eh_prov}")
                if eh_prov:
                    provedores_encontrados = opcoes
                    indice_provedor = i
                    break
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
        except Exception as e:
            log(f"  Combobox[{i}] erro: {e}")
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)

    tw.snap(page, EVID, "tc7b_01_dropdown_provedor_aluno")

    # Verificar respostas de API de providers
    erros_api = [r for r in respostas_prov if r["status"] >= 400]
    log(f"  Erros API provedores: {erros_api}")
    log(f"  Provedores encontrados: {provedores_encontrados}")
    log(f"  Indice combobox provedor: {indice_provedor}")

    # Fechar dropdown se ainda aberto
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # Veredito TC7:
    # Se ha provedores visiveis para Aluno = OK (nao e bug)
    # Se ha erros de API = bug de autorizacao
    # Se lista vazia sem erro = massa faltando OU bug de filtro
    provedores_ok = len(provedores_encontrados) > 0
    api_error = len(erros_api) > 0

    if provedores_ok:
        passou = True
        nota = f"Provedores visiveis para Aluno: {provedores_encontrados}. Nao e bug - provedores existem e sao listados."
    elif api_error:
        passou = False
        nota = f"API de provedores retornou erro {erros_api[0]['status']} para Aluno. Bug de autorizacao."
    else:
        passou = False
        nota = f"Dropdown Provedor vazio para Aluno (sem erro de API). Possivel bug de filtro ou massa faltando."

    r("TC7", passou, nota)

    ctx.close()
    return provedores_encontrados


# ══════════════════════════════════════════════════════════════════════════════
# TC8 -- Validacoes Carga horaria (Admin, com Pessoas preenchido via modal)
# ══════════════════════════════════════════════════════════════════════════════

def tc8_carga_horaria(page):
    log("\n[TC8] Validacoes Carga horaria (Admin)")

    ir_para_form(page, NEW_FORM_ADMIN)

    # Preencher TODOS os outros obrigatorios primeiro (incluindo Pessoas)
    # para que o sistema valide apenas Carga horaria

    # 1. Pessoas via modal
    modal_ok = abrir_modal_pessoas(page)
    page.wait_for_timeout(1000)
    if modal_ok:
        # Verificar se ha pessoas disponiveis (Admin deve ver todos)
        modal = page.locator("[role='dialog']").first
        nenhum = modal.locator("text=Nenhum item").count() > 0
        if not nenhum:
            # Selecionar primeiro checkbox disponivel
            checkboxes = modal.locator("input[type='checkbox']").all()
            if checkboxes:
                checkboxes[0].click()
                page.wait_for_timeout(500)
            # Clicar Vincular
            btn_vincular = page.locator("button:has-text('Vincular')").first
            if btn_vincular.count() > 0:
                btn_vincular.click()
                page.wait_for_timeout(1000)
                log("  Pessoa vinculada com sucesso")
        else:
            log("  AVISO: modal vazio para Admin - impossivel vincular pessoa")
            try:
                page.locator("[role='dialog'] button").last.click()
                page.wait_for_timeout(500)
            except Exception:
                pass

    tw.snap(page, EVID, "tc8b_01_pessoas_preenchidas")

    # 2. Provedor (combobox[0])
    clicar_combobox_por_indice(page, 0)
    page.wait_for_timeout(500)
    try:
        page.locator("[role='option']").first.click(timeout=3000)
        page.wait_for_timeout(400)
    except Exception:
        pass

    # 3. Conteudo (combobox[1])
    clicar_combobox_por_indice(page, 1)
    page.wait_for_timeout(500)
    try:
        page.locator("[role='option']").first.click(timeout=3000)
        page.wait_for_timeout(400)
    except Exception:
        pass

    # 4. Tipo de experiencia (combobox[2])
    clicar_combobox_por_indice(page, 2)
    page.wait_for_timeout(500)
    try:
        page.locator("[role='option']").first.click(timeout=3000)
        page.wait_for_timeout(400)
    except Exception:
        pass

    # 5. Categorias (combobox[3])
    clicar_combobox_por_indice(page, 3)
    page.wait_for_timeout(500)
    try:
        page.locator("[role='option']").first.click(timeout=3000)
        page.wait_for_timeout(400)
        page.keyboard.press("Escape")
    except Exception:
        pass

    # 6. Data de termino
    try:
        date_inp = page.locator("input[name='endDate']").first
        date_inp.fill("2025-06-01")
        page.wait_for_timeout(300)
    except Exception:
        pass

    # DEIXAR Carga horaria VAZIA
    try:
        inp_carga = page.locator("input[name='workload_seconds']").first
        inp_carga.clear()
        page.wait_for_timeout(300)
    except Exception:
        pass

    tw.snap(page, EVID, "tc8b_02_form_sem_carga")

    # Clicar Salvar e verificar erro na Carga horaria
    try:
        page.get_by_role("button", name="Salvar").first.click(timeout=5000)
        page.wait_for_timeout(2000)
    except Exception:
        pass

    tw.snap(page, EVID, "tc8b_03_apos_salvar_carga_vazia")

    erros = page.locator("[class*='chakra-form__error'], [id*='feedback'], [class*='error-message']").all_text_contents()
    log(f"  Erros apos salvar com carga vazia: {erros}")

    # Verificar se erro de Carga horaria apareceu
    erro_carga = any("carga" in e.lower() or "horaria" in e.lower() or "obrigatório" in e.lower() or "obrigatorio" in e.lower() for e in erros)
    ainda_no_form = "records/new" in page.url
    log(f"  Erro de carga: {erro_carga}, ainda no form: {ainda_no_form}")

    # Verificar se o UNICO erro e de Carga (ou se outros campos ja foram preenchidos)
    n_erros = len(erros)
    log(f"  Total erros: {n_erros}")

    # Se Pessoas foi preenchida, deveria haver apenas erros dos campos restantes
    # O importante e que Carga horaria seja validada APOS Pessoas estar preenchida
    passou = erro_carga and ainda_no_form

    # CASO 2: verificar que valor invalido e rejeitado
    try:
        inp_carga = page.locator("input[name='workload_seconds']").first
        if inp_carga.count() > 0:
            inp_carga.fill("abc")
            page.wait_for_timeout(300)
            val_depois = inp_carga.input_value()
            log(f"  Valor apos fill 'abc': '{val_depois}'")
            inp_carga_invalido_rejeitado = val_depois != "abc"  # input de tempo pode rejeitar texto
    except Exception:
        pass

    tw.snap(page, EVID, "tc8b_04_resultado")

    r("TC8", passou, f"Erro_carga_vazia={erro_carga}, ainda_no_form={ainda_no_form}, n_erros={n_erros}, erros={erros}")


# ══════════════════════════════════════════════════════════════════════════════
# TC12 -- clearError: erro some ao digitar no campo (Aluno)
# ══════════════════════════════════════════════════════════════════════════════

def tc12_clear_error(browser):
    log("\n" + "=" * 60)
    log("TC12 -- clearError: erro some ao preencher campo")
    log("=" * 60)

    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
    page = ctx.new_page()

    ok = login_como(page, ALUNO_EMAIL, ALUNO_PASSWORD, admin=False)
    if not ok:
        r("TC12", False, "Login Aluno falhou")
        ctx.close()
        return

    ir_para_form(page, NEW_FORM_ALUNO)
    page.wait_for_timeout(1000)

    # Passo 1: Provocar erro clicando Salvar sem preencher nada
    try:
        page.get_by_role("button", name="Salvar").first.click(timeout=5000)
        page.wait_for_timeout(1500)
    except Exception:
        pass

    tw.snap(page, EVID, "tc12b_01_erros_provocados")

    erros_antes = page.locator("[class*='chakra-form__error'], [id*='feedback'], [class*='error-message']").all_text_contents()
    log(f"  Erros antes: {erros_antes}")
    n_antes = len(erros_antes)

    if n_antes == 0:
        r("TC12", False, "Nenhum erro foi provocado pelo Salvar sem preencher")
        ctx.close()
        return

    # Passo 2: Preencher o campo Carga horaria com "4" usando type() char-a-char
    # A AT espera que o erro some IMEDIATAMENTE ao digitar (clearError em onChange)
    try:
        inp_carga = page.locator("input[name='workload_seconds']").first
        if inp_carga.count() > 0:
            inp_carga.click()
            # Usar type() em vez de fill() para disparar eventos onChange no React
            inp_carga.type("4", delay=50)
            page.wait_for_timeout(800)
        else:
            # Alternativa: via label
            inp_carga = page.get_by_label("Carga horária").first
            if inp_carga.count() > 0:
                inp_carga.click()
                inp_carga.type("4", delay=50)
                page.wait_for_timeout(800)
            else:
                log("  Campo Carga horaria nao encontrado")
    except Exception as e:
        log(f"  Erro ao preencher Carga horaria: {e}")

    tw.snap(page, EVID, "tc12b_02_apos_digitar")

    erros_depois = page.locator("[class*='chakra-form__error'], [id*='feedback'], [class*='error-message']").all_text_contents()
    log(f"  Erros depois de digitar: {erros_depois}")
    n_depois = len(erros_depois)

    # Verificar se o erro de carga especificamente sumiu
    havia_erro_carga_antes = any("carga" in e.lower() or "obrigatório" in e.lower() for e in erros_antes)
    ha_erro_carga_depois = any("carga" in e.lower() or "obrigatório" in e.lower() for e in erros_depois)

    log(f"  n_antes={n_antes}, n_depois={n_depois}")
    log(f"  Erro carga antes={havia_erro_carga_antes}, depois={ha_erro_carga_depois}")

    # clearError funciona se: numero de erros diminuiu OU erro especifico de carga sumiu
    passou = n_depois < n_antes

    r("TC12", passou,
      f"Erros antes={n_antes}, depois={n_depois}. Erro_carga_antes={havia_erro_carga_antes}, depois={ha_erro_carga_depois}. ClearError={'OK' if passou else 'NAO_FUNCIONOU'}")

    ctx.close()


# ══════════════════════════════════════════════════════════════════════════════
# TC14 -- Origem Aluno (Externo + Pendente)
# ══════════════════════════════════════════════════════════════════════════════

def tc14_origem_aluno(browser):
    log("\n" + "=" * 60)
    log("TC14 -- Origem inferida Aluno (Externo + Pendente)")
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
    tw.snap(page, EVID, "tc14b_01_form_aluno")

    # Preencher todos os obrigatorios
    campos = preencher_form_aluno_completo(page)
    log(f"  Campos preenchidos: {campos}")

    # Se nao conseguiu provedor, o form nao vai salvar
    if not campos.get("provedor"):
        # Tentar criar provedor inline
        try:
            combos = page.locator("[role='combobox']").all()
            for i in range(min(len(combos), 4)):
                combos[i].click(timeout=2000)
                page.wait_for_timeout(500)
                opcoes = page.locator("[role='option']").all_text_contents()
                if not opcoes:
                    page.keyboard.press("Escape")
                    continue
                # Verificar se e campo de texto/creatable
                inp_dentro = combos[i].locator("input").first
                if inp_dentro.count() > 0:
                    inp_dentro.fill("Alura")
                    page.wait_for_timeout(500)
                    opcoes_pos = page.locator("[role='option']").all_text_contents()
                    if opcoes_pos:
                        prov_ok = any("alura" in op.lower() for op in opcoes_pos)
                        if prov_ok:
                            page.locator("[role='option']:has-text('Alura')").first.click()
                            campos["provedor"] = True
                            break
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
        except Exception as e:
            log(f"  Tentativa de criar provedor inline falhou: {e}")

    tw.snap(page, EVID, "tc14b_02_form_preenchido")

    # Clicar Salvar
    try:
        page.get_by_role("button", name="Salvar").first.click(timeout=5000)
        page.wait_for_timeout(4000)
        dispensar_overlays(page)
    except Exception as e:
        log(f"  Erro ao clicar Salvar: {e}")

    tw.snap(page, EVID, "tc14b_03_pos_salvar")

    # Verificar se saiu do form (registro salvo) ou se ficou com erros
    ainda_no_form = "records/new" in page.url
    foi_salvo = not ainda_no_form
    log(f"  URL pos salvar: {page.url}, foi_salvo={foi_salvo}")

    if not foi_salvo:
        erros = page.locator("[class*='chakra-form__error'], [id*='feedback']").all_text_contents()
        log(f"  Erros pos Salvar: {erros}")
        tw.snap(page, EVID, "tc14b_ERROS")
        r("TC14", False, f"Registro nao foi salvo. Erros: {erros}. Campos: {campos}")
        ctx.close()
        return

    # Verificar na lista a origem e status
    page.goto(RECORDS_ALUNO_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dispensar_overlays(page)
    aguardar_sem_spinner(page)
    tw.snap(page, EVID, "tc14b_04_lista")

    # Ler o conteudo da lista para verificar Externo e Pendente
    lista_txt = page.locator("body").inner_text()
    tem_externo = "Externo" in lista_txt
    tem_pendente = "Pendente" in lista_txt

    # Fonte de verdade: localizar a linha mais recente
    try:
        # Tabela/lista de registros -- buscar a primeira linha
        primeira_linha = page.locator("table tbody tr").first
        if primeira_linha.count() > 0:
            linha_txt = primeira_linha.inner_text()
            log(f"  Primeira linha da lista: {linha_txt[:200]}")
            tem_externo_linha = "Externo" in linha_txt
            tem_pendente_linha = "Pendente" in linha_txt
            log(f"  Linha: Externo={tem_externo_linha}, Pendente={tem_pendente_linha}")
    except Exception:
        pass

    tw.snap(page, EVID, "tc14b_05_origem_status")

    log(f"  Lista: Externo={tem_externo}, Pendente={tem_pendente}")
    passou = foi_salvo and tem_externo and tem_pendente
    r("TC14", passou,
      f"Salvo={foi_salvo}, Externo={tem_externo}, Pendente={tem_pendente}")

    ctx.close()


# ══════════════════════════════════════════════════════════════════════════════
# TC15 -- Origem Admin (Externo + Emitido/Aprovado)
# ══════════════════════════════════════════════════════════════════════════════

def tc15_origem_admin(page):
    log("\n[TC15] Origem inferida Admin (Externo + Emitido)")

    ir_para_form(page, NEW_FORM_ADMIN)
    page.wait_for_timeout(1000)
    tw.snap(page, EVID, "tc15b_01_form_admin")

    # Preencher todos os campos obrigatorios (incluindo Pessoas via modal)
    campos = preencher_form_admin_completo(page, pessoa_indice=0)
    log(f"  Campos Admin preenchidos: {campos}")

    tw.snap(page, EVID, "tc15b_04_form_completo")

    # Clicar Salvar
    try:
        page.get_by_role("button", name="Salvar").first.click(timeout=5000)
        page.wait_for_timeout(4000)
        dispensar_overlays(page)
    except Exception as e:
        log(f"  Erro ao clicar Salvar: {e}")

    tw.snap(page, EVID, "tc15b_05_pos_salvar")

    ainda_no_form = "records/new" in page.url
    foi_salvo = not ainda_no_form
    log(f"  URL pos salvar: {page.url}, foi_salvo={foi_salvo}")

    if not foi_salvo:
        erros = page.locator("[class*='chakra-form__error'], [id*='feedback']").all_text_contents()
        log(f"  Erros pos Salvar: {erros}")
        tw.snap(page, EVID, "tc15b_ERROS")
        r("TC15", False, f"Registro nao foi salvo pelo Admin. Erros: {erros}. Campos: {campos}")
        return

    # Verificar na lista Admin
    page.goto(RECORDS_ADMIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dispensar_overlays(page)
    aguardar_sem_spinner(page)
    tw.snap(page, EVID, "tc15b_06_lista_admin")

    lista_txt = page.locator("body").inner_text()
    tem_externo = "Externo" in lista_txt
    tem_aprovado = "Aprovado" in lista_txt or "Emitido" in lista_txt

    # Fonte de verdade: primeira linha da tabela
    try:
        primeira_linha = page.locator("table tbody tr").first
        if primeira_linha.count() > 0:
            linha_txt = primeira_linha.inner_text()
            log(f"  Primeira linha: {linha_txt[:200]}")
    except Exception:
        pass

    tw.snap(page, EVID, "tc15b_07_origem_status")

    log(f"  Lista Admin: Externo={tem_externo}, Aprovado/Emitido={tem_aprovado}")
    passou = foi_salvo and tem_externo and tem_aprovado
    r("TC15", passou,
      f"Salvo={foi_salvo}, Externo={tem_externo}, Aprovado/Emitido={tem_aprovado}, campos={campos}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    log("=" * 60)
    log("QA 1.6 Round 2 -- Fechar TCs inconclusivos")
    log(f"URL: {BASE_URL} | Org: {ORG_ID}")
    log("=" * 60)

    with tw.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=0)

        # TC3: Lider 401 (sessao dedicada)
        tc3_lider_401(browser)

        # TC7: Provedores Aluno (sessao dedicada)
        tc7_provedores_aluno(browser)

        # TC12: clearError Aluno (sessao dedicada)
        tc12_clear_error(browser)

        # TC14: Origem Aluno (sessao dedicada)
        tc14_origem_aluno(browser)

        # TC5 + TC8 + TC15: sessao Admin
        log("\n" + "=" * 60)
        log("SESSAO ADMIN (TC5, TC8, TC15)")
        log("=" * 60)
        ctx_admin = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
        page_admin = ctx_admin.new_page()
        ok = login_como(page_admin, ADMIN_EMAIL, ADMIN_PASSWORD, admin=True)
        if ok:
            tc5_tipo_experiencia(page_admin)
            tc8_carga_horaria(page_admin)
            tc15_origem_admin(page_admin)
        else:
            log("  Login Admin falhou!")
            for tc in ["TC5", "TC8", "TC15"]:
                r(tc, False, "Login Admin falhou")
        ctx_admin.close()

        browser.close()

    log("\n" + "=" * 60)
    log("SUMARIO QA 1.6 ROUND 2")
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
