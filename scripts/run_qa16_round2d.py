"""run_qa16_round2d.py -- TC15 com scroll para encontrar Adicionar pessoas

Rodar: .venv/Scripts/python.exe scripts/run_qa16_round2d.py
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


def aguardar_sem_spinner(page):
    try:
        page.wait_for_selector(".chakra-spinner", state="hidden", timeout=15000)
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
    log(f"  [Admin login] ok={ok}")
    return ok


def ir_para_form(page):
    page.goto(NEW_FORM_ADMIN, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dispensar_overlays(page)
    aguardar_sem_spinner(page)
    page.wait_for_timeout(1000)


def scroll_para_elemento(page, locator):
    """Scrolla a pagina para tornar o elemento visivel."""
    try:
        locator.scroll_into_view_if_needed(timeout=5000)
        page.wait_for_timeout(500)
    except Exception:
        pass


def tc15_com_scroll(page):
    log("\n[TC15] Origem Admin (Externo + Emitido) - com scroll")

    ir_para_form(page)
    tw.snap(page, EVID, "tc15c_01_form_inicial")

    # Scroll para topo
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)

    # Verificar visibilidade do campo Pessoas
    el_adicionar = page.locator("text=Adicionar pessoas").first
    log(f"  'Adicionar pessoas' count: {el_adicionar.count()}")

    # Scrollar ate o elemento Pessoas
    if el_adicionar.count() > 0:
        scroll_para_elemento(page, el_adicionar)
        page.wait_for_timeout(500)
        visivel = el_adicionar.is_visible()
        log(f"  'Adicionar pessoas' visivel apos scroll: {visivel}")
        tw.snap(page, EVID, "tc15c_02_pessoas_visivel")

    # Abrir modal clicando com scroll
    pessoa_ok = False
    try:
        if el_adicionar.count() > 0:
            el_adicionar.click(timeout=8000)
            page.wait_for_timeout(2500)
            modal = page.locator("[role='dialog']").first
            modal_abriu = modal.count() > 0 and modal.is_visible()
            log(f"  Modal abriu: {modal_abriu}")

            if modal_abriu:
                tw.snap(page, EVID, "tc15c_03_modal_aberto")
                modal_txt = modal.inner_text()
                log(f"  Modal: {modal_txt[:200]}")

                # Usar JS click no primeiro checkbox Chakra
                try:
                    n_selecionados = page.evaluate("""() => {
                        const modal = document.querySelector('[role=dialog]');
                        if (!modal) return 0;
                        const spans = modal.querySelectorAll('.chakra-checkbox__control');
                        if (spans[0]) {
                            spans[0].click();
                            return 1;
                        }
                        return 0;
                    }""")
                    page.wait_for_timeout(800)
                    log(f"  JS click nos checkboxes: {n_selecionados}")
                    tw.snap(page, EVID, "tc15c_04_checkbox")

                    # Verificar se algum foi marcado
                    checked = page.evaluate("""() => {
                        const inputs = document.querySelectorAll('[role=dialog] input[type=checkbox]');
                        return Array.from(inputs).filter(i => i.checked).length;
                    }""")
                    log(f"  Checkboxes marcados: {checked}")

                    # Clicar Vincular
                    btn_vinc = page.locator("button:has-text('Vincular')").first
                    if btn_vinc.count() > 0:
                        btn_vinc.click(timeout=5000)
                        page.wait_for_timeout(2000)
                        modal_fechou = page.locator("[role='dialog']").count() == 0
                        log(f"  Modal fechou: {modal_fechou}")
                        pessoa_ok = modal_fechou or checked > 0

                        # Verificar chip de pessoa no campo
                        tw.snap(page, EVID, "tc15c_05_pos_vincular")
                except Exception as e:
                    log(f"  Erro JS checkbox: {e}")
                    page.keyboard.press("Escape")
    except Exception as e:
        log(f"  Erro ao abrir modal: {e}")

    log(f"  Pessoa OK: {pessoa_ok}")

    # Garantir modal fechado
    if page.locator("[role='dialog']").count() > 0:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

    # Preencher Provedor
    try:
        combos = page.locator("[role='combobox']").all()
        log(f"  Comboboxes: {len(combos)}")
        if combos:
            combos[0].click(timeout=5000)
            page.wait_for_timeout(800)
            opcoes = page.locator("[role='option']").all_text_contents()
            log(f"  Provedor opcoes: {opcoes[:3]}")
            if opcoes:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
    except Exception as e:
        log(f"  Provedor erro: {e}")
        page.keyboard.press("Escape")

    # Conteudo
    try:
        combos = page.locator("[role='combobox']").all()
        if len(combos) > 1:
            combos[1].click(timeout=5000)
            page.wait_for_timeout(800)
            if page.locator("[role='option']").count() > 0:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
    except Exception as e:
        log(f"  Conteudo erro: {e}")
        page.keyboard.press("Escape")

    # Tipo
    try:
        combos = page.locator("[role='combobox']").all()
        if len(combos) > 2:
            combos[2].click(timeout=5000)
            page.wait_for_timeout(800)
            if page.locator("[role='option']").count() > 0:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
    except Exception as e:
        log(f"  Tipo erro: {e}")
        page.keyboard.press("Escape")

    # Categorias
    try:
        combos = page.locator("[role='combobox']").all()
        if len(combos) > 3:
            combos[3].click(timeout=5000)
            page.wait_for_timeout(800)
            if page.locator("[role='option']").count() > 0:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
                page.keyboard.press("Escape")
    except Exception as e:
        log(f"  Categorias erro: {e}")
        page.keyboard.press("Escape")

    # Carga horaria
    try:
        inp_carga = page.locator("input[name='workload_seconds']").first
        if inp_carga.count() > 0:
            inp_carga.click()
            inp_carga.fill("02:00:00")
    except Exception as e:
        log(f"  Carga erro: {e}")

    # Data de termino
    try:
        page.locator("input[name='endDate']").first.fill("2025-06-01")
    except Exception as e:
        log(f"  Data erro: {e}")

    tw.snap(page, EVID, "tc15c_06_form_completo")

    # Salvar
    try:
        page.get_by_role("button", name="Salvar").first.click(timeout=5000)
        page.wait_for_timeout(4000)
        dispensar_overlays(page)
    except Exception as e:
        log(f"  Salvar erro: {e}")

    tw.snap(page, EVID, "tc15c_07_pos_salvar")

    ainda_no_form = "records/new" in page.url
    foi_salvo = not ainda_no_form
    log(f"  URL: {page.url}, foi_salvo={foi_salvo}")

    if not foi_salvo:
        erros = page.locator("[class*='chakra-form__error'], [id*='feedback']").all_text_contents()
        log(f"  Erros: {erros}")
        # Verificar se modal de Pessoas voltou
        modal_voltou = page.locator("[role='dialog']").count() > 0
        log(f"  Modal voltou: {modal_voltou}")
        if modal_voltou:
            tw.snap(page, EVID, "tc15c_modal_voltou")
        r("TC15", False, f"Nao salvou. Erros={erros}. Modal_voltou={modal_voltou}. Pessoa={pessoa_ok}")
        return

    # Lista Admin
    page.goto(RECORDS_ADMIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dispensar_overlays(page)
    aguardar_sem_spinner(page)
    tw.snap(page, EVID, "tc15c_08_lista")

    lista_txt = page.locator("body").inner_text()
    tem_externo = "Externo" in lista_txt
    tem_aprovado = "Aprovado" in lista_txt or "Emitido" in lista_txt

    try:
        primeira_linha = page.locator("table tbody tr").first
        if primeira_linha.count() > 0:
            linha_txt = primeira_linha.inner_text()
            log(f"  Primeira linha lista: {linha_txt[:250]}")
    except Exception:
        pass

    tw.snap(page, EVID, "tc15c_09_origem_status")

    passou = foi_salvo and tem_externo and tem_aprovado
    r("TC15", passou,
      f"Salvo={foi_salvo}, Externo={tem_externo}, Aprovado={tem_aprovado}, Pessoa={pessoa_ok}")


def main():
    log("=" * 60)
    log("QA 1.6 Round 2d -- TC15 com scroll")
    log(f"URL: {BASE_URL} | Org: {ORG_ID}")
    log("=" * 60)

    with tw.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=0)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
        page = ctx.new_page()
        ok = login_admin(page)
        if ok:
            tc15_com_scroll(page)
        else:
            r("TC15", False, "Login falhou")
        ctx.close()
        browser.close()

    log("\n" + "=" * 60)
    for tc, dados in sorted(results.items()):
        status = "PASSOU" if dados["pass"] else "FALHOU"
        log(f"  {tc}: {status} -- {dados.get('note','')[:150]}")
    log("=" * 60)


if __name__ == "__main__":
    main()
