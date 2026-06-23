"""run_qa16_round2c.py -- QA 1.6 Round 2c: TC8 e TC15 com checkbox Chakra corrigido
O <span> intercepta o input[checkbox] do Chakra. Usar force=True ou clicar no <span>.

Rodar: .venv/Scripts/python.exe scripts/run_qa16_round2c.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL       = "https://registrosf2.stage.twygoead.com"
ORG_ID         = "37079"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"

SLUG = "registros-f2-qa16"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)

RECORDS_ADMIN_URL = f"{BASE_URL}/o/{ORG_ID}/records"
NEW_FORM_ADMIN    = f"{BASE_URL}/o/{ORG_ID}/records/new"

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


def aguardar_sem_spinner(page, timeout=15000):
    try:
        page.wait_for_selector(".chakra-spinner", state="hidden", timeout=timeout)
    except Exception:
        pass


def login_admin(page):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", ADMIN_EMAIL)
    page.fill("#user_password", ADMIN_PASSWORD)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    dispensar_overlays(page)
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
        wait_until="domcontentloaded", timeout=30000,
    )
    page.wait_for_timeout(2000)
    dispensar_overlays(page)
    ok = "/login" not in page.url
    log(f"  [Admin login] ok={ok}, URL={page.url}")
    return ok


def ir_para_form(page):
    page.goto(NEW_FORM_ADMIN, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dispensar_overlays(page)
    aguardar_sem_spinner(page)
    page.wait_for_timeout(1000)


def vincular_pessoa_no_modal(page, indice=0):
    """
    Abre modal Vincular pessoas, seleciona a pessoa via span Chakra (force=True) e confirma.
    Retorna True se conseguiu vincular.
    """
    # Abrir modal
    el = page.locator("text=Adicionar pessoas").first
    if el.count() == 0 or not el.is_visible():
        log("  'Adicionar pessoas' nao encontrado")
        return False

    el.click(timeout=5000)
    page.wait_for_timeout(2500)

    modal = page.locator("[role='dialog']").first
    if modal.count() == 0 or not modal.is_visible():
        log("  Modal nao abriu")
        return False

    tw.snap(page, EVID, "tc_modal_aberto_v2")
    modal_txt = modal.inner_text()
    log(f"  Modal: {modal_txt[:200]}")

    nenhum = "Nenhum item" in modal_txt or "nenhum" in modal_txt.lower()
    if nenhum:
        log("  Modal vazio - nenhuma pessoa")
        try:
            modal.locator("button:has-text('Cancelar')").click()
            page.wait_for_timeout(500)
        except Exception:
            page.keyboard.press("Escape")
        return False

    # Verificar pessoas listadas
    try:
        # Chakra checkbox: o span.chakra-checkbox__control e o elemento clicavel
        # O input real tem pointer-events:none por baixo do span
        spans_check = modal.locator("span.chakra-checkbox__control, .chakra-checkbox__control").all()
        log(f"  Spans checkbox Chakra: {len(spans_check)}")

        if spans_check and indice < len(spans_check):
            # Usar force=True para bypassar o interceptador
            spans_check[indice].click(force=True, timeout=5000)
            page.wait_for_timeout(800)
            tw.snap(page, EVID, "tc_checkbox_clicado")
            log("  Checkbox clicado via force")
        else:
            # Fallback: clicar na linha inteira da pessoa
            linhas = modal.locator("[class*='css-']:has(input[type=checkbox])").all()
            log(f"  Linhas com checkbox: {len(linhas)}")
            if linhas and indice < len(linhas):
                linhas[indice].click(force=True, timeout=3000)
                page.wait_for_timeout(500)
            else:
                # Ultimo fallback: JS click
                page.evaluate(f"""() => {{
                    const spans = document.querySelectorAll('.chakra-checkbox__control');
                    if (spans[{indice}]) {{
                        spans[{indice}].click();
                    }}
                }}""")
                page.wait_for_timeout(500)

        # Verificar se algum checkbox ficou marcado
        checked = page.evaluate("""() => {
            const checkboxes = document.querySelectorAll('[role=dialog] input[type=checkbox]');
            return Array.from(checkboxes).filter(cb => cb.checked).length;
        }""")
        log(f"  Checkboxes marcados: {checked}")

    except Exception as e:
        log(f"  Erro ao clicar checkbox: {e}")

    # Clicar Vincular
    try:
        btn_vinc = page.locator("button:has-text('Vincular')").first
        if btn_vinc.count() > 0:
            btn_vinc.click(timeout=5000)
            page.wait_for_timeout(2000)
            modal_fechou = page.locator("[role='dialog']").count() == 0
            log(f"  Modal fechou apos Vincular: {modal_fechou}")

            # Verificar se a pessoa apareceu no campo Pessoas do form
            pessoas_chip = page.locator("[class*='chakra-badge'], [class*='tag'], .creatable-select-field__multi-value").all()
            log(f"  Chips de pessoa no form: {len(pessoas_chip)}")
            return True
        else:
            log("  Botao Vincular nao encontrado")
            page.keyboard.press("Escape")
            return False
    except Exception as e:
        log(f"  Erro ao clicar Vincular: {e}")
        page.keyboard.press("Escape")
        return False


def preencher_form_sem_pessoas(page, carga="02:00:00"):
    """Preenche todos os campos do form Admin EXCETO Pessoas."""
    # Provedor (combobox[0])
    try:
        combos = page.locator("[role='combobox']").all()
        log(f"  Comboboxes disponiveis: {len(combos)}")
        if combos:
            combos[0].click(timeout=5000)
            page.wait_for_timeout(800)
            opcoes = page.locator("[role='option']").all_text_contents()
            log(f"  Opcoes provedor: {opcoes[:3]}")
            if opcoes:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
    except Exception as e:
        log(f"  Provedor erro: {e}")
        page.keyboard.press("Escape")

    # Conteudo (combobox[1])
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
        log(f"  Conteudo erro: {e}")
        page.keyboard.press("Escape")

    # Tipo (combobox[2])
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
        log(f"  Tipo erro: {e}")
        page.keyboard.press("Escape")

    # Categorias (combobox[3])
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
    except Exception as e:
        log(f"  Categorias erro: {e}")
        page.keyboard.press("Escape")

    # Carga horaria
    try:
        inp_carga = page.locator("input[name='workload_seconds']").first
        if inp_carga.count() > 0 and carga:
            inp_carga.click()
            inp_carga.fill(carga)
            page.wait_for_timeout(300)
    except Exception as e:
        log(f"  Carga erro: {e}")

    # Data de termino
    try:
        date_inp = page.locator("input[name='endDate']").first
        if date_inp.count() > 0:
            date_inp.fill("2025-06-01")
            page.wait_for_timeout(300)
    except Exception as e:
        log(f"  Data erro: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TC8 -- Validacao Carga horaria: com Pessoas preenchida via modal
# ══════════════════════════════════════════════════════════════════════════════

def tc8_carga_horaria(page):
    log("\n[TC8] Validacoes Carga horaria (Admin)")
    ir_para_form(page)
    page.wait_for_timeout(500)

    # 1. Vincular pessoa PRIMEIRO (para que Pessoas nao bloqueie)
    pessoa_ok = vincular_pessoa_no_modal(page, indice=0)
    log(f"  Pessoa vinculada: {pessoa_ok}")

    # Garantir modal fechado
    if page.locator("[role='dialog']").count() > 0:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

    tw.snap(page, EVID, "tc8b_05_pos_vincular")

    # 2. Preencher demais campos (SEM carga horaria)
    preencher_form_sem_pessoas(page, carga="")

    tw.snap(page, EVID, "tc8b_06_form_sem_carga")

    # 3. Tentar Salvar -> deve mostrar erro em Carga horaria
    try:
        page.get_by_role("button", name="Salvar").first.click(timeout=5000)
        page.wait_for_timeout(2500)
    except Exception as e:
        log(f"  Click Salvar erro: {e}")

    tw.snap(page, EVID, "tc8b_07_pos_salvar_vazio")

    erros = page.locator("[class*='chakra-form__error'], [id*='feedback'], [class*='error-message']").all_text_contents()
    log(f"  Erros: {erros}")

    ainda_no_form = "records/new" in page.url
    log(f"  Ainda no form: {ainda_no_form}")

    # Verificar se modal voltou (indicaria que Pessoas nao foi salva)
    modal_voltou = page.locator("[role='dialog']").count() > 0
    log(f"  Modal voltou: {modal_voltou}")

    # O erro de Carga horaria deveria ser o unico (ou estar junto dos outros restantes)
    erro_carga = any("carga" in e.lower() or "horária" in e.lower() or "horaria" in e.lower() for e in erros)
    erro_pessoas = any("pessoas" in e.lower() or "pessoa" in e.lower() for e in erros)

    log(f"  Erro carga={erro_carga}, erro_pessoas={erro_pessoas}")

    # TC8 PASSA se: erro de Carga horaria aparece E formulario nao foi submetido
    # Bonus: se modal de Pessoas nao voltou (significa que Pessoas estava preenchida)
    passou = erro_carga and ainda_no_form

    r("TC8", passou,
      f"Erro_carga={erro_carga}, ainda_no_form={ainda_no_form}, modal_voltou={modal_voltou}, "
      f"pessoa_ok={pessoa_ok}, erros={erros}")


# ══════════════════════════════════════════════════════════════════════════════
# TC15 -- Origem Admin (Externo + Emitido)
# ══════════════════════════════════════════════════════════════════════════════

def tc15_origem_admin(page):
    log("\n[TC15] Origem Admin (Externo + Emitido)")
    ir_para_form(page)
    page.wait_for_timeout(500)

    # 1. Vincular pessoa
    pessoa_ok = vincular_pessoa_no_modal(page, indice=0)
    log(f"  Pessoa vinculada: {pessoa_ok}")

    if page.locator("[role='dialog']").count() > 0:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

    tw.snap(page, EVID, "tc15b_10_pos_vincular")

    # 2. Preencher demais campos (COM carga horaria)
    preencher_form_sem_pessoas(page, carga="02:00:00")

    tw.snap(page, EVID, "tc15b_11_form_completo")

    # 3. Salvar
    try:
        page.get_by_role("button", name="Salvar").first.click(timeout=5000)
        page.wait_for_timeout(4000)
        dispensar_overlays(page)
    except Exception as e:
        log(f"  Salvar erro: {e}")

    tw.snap(page, EVID, "tc15b_12_pos_salvar")

    ainda_no_form = "records/new" in page.url
    foi_salvo = not ainda_no_form
    log(f"  URL: {page.url}, foi_salvo={foi_salvo}")

    if not foi_salvo:
        erros = page.locator("[class*='chakra-form__error'], [id*='feedback']").all_text_contents()
        log(f"  Erros: {erros}")
        tw.snap(page, EVID, "tc15b_ERROS")
        r("TC15", False, f"Nao salvou. Erros: {erros}. Pessoa={pessoa_ok}")
        return

    # 4. Verificar na lista Admin
    page.goto(RECORDS_ADMIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dispensar_overlays(page)
    aguardar_sem_spinner(page)
    tw.snap(page, EVID, "tc15b_13_lista_admin")

    # Ler primeira linha da tabela
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

    tw.snap(page, EVID, "tc15b_14_origem_status")

    passou = foi_salvo and tem_externo and tem_aprovado
    r("TC15", passou,
      f"Salvo={foi_salvo}, Externo={tem_externo}, Aprovado/Emitido={tem_aprovado}, Pessoa={pessoa_ok}")


def main():
    log("=" * 60)
    log("QA 1.6 Round 2c -- TC8 e TC15 com checkbox Chakra corrigido")
    log(f"URL: {BASE_URL} | Org: {ORG_ID}")
    log("=" * 60)

    with tw.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=0)

        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
        page = ctx.new_page()

        ok = login_admin(page)
        if not ok:
            log("Login Admin falhou!")
            r("TC8", False, "Login falhou")
            r("TC15", False, "Login falhou")
        else:
            tc8_carga_horaria(page)
            tc15_origem_admin(page)

        ctx.close()
        browser.close()

    log("\n" + "=" * 60)
    log("SUMARIO Round 2c")
    log("=" * 60)
    for tc, dados in sorted(results.items()):
        status = "PASSOU" if dados["pass"] else "FALHOU"
        nota = dados["note"][:150] if dados.get("note") else ""
        log(f"  {tc}: {status} -- {nota}")
    log("=" * 60)


if __name__ == "__main__":
    main()
