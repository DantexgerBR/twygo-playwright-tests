"""run_qa16_round2e.py -- TC15: abrir modal via JS click no container de Pessoas

Rodar: .venv/Scripts/python.exe scripts/run_qa16_round2e.py
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
    status = "PASSOU" if dados["pass"] else "FALHOU"
    print(f"  [{status}] {tc}: {nota}")


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


def tc15_via_js(page):
    log("\n[TC15] Origem Admin via JS click")

    ir_para_form(page)
    page.wait_for_timeout(500)

    # Inspecionar o DOM do campo Pessoas para entender a estrutura
    dom_info = page.evaluate("""() => {
        // Buscar o elemento que contem "Adicionar pessoas"
        const allDivs = document.querySelectorAll('div, button, span, input');
        const results = [];
        for (const el of allDivs) {
            const txt = (el.innerText || el.value || '').trim();
            if (txt === 'Adicionar pessoas' || txt.includes('Adicionar pessoas')) {
                const parent = el.parentElement;
                const gp = parent ? parent.parentElement : null;
                results.push({
                    tag: el.tagName,
                    id: el.id,
                    class: (el.className || '').substring(0, 80),
                    text: txt.substring(0, 50),
                    parentTag: parent ? parent.tagName : '',
                    parentClass: parent ? (parent.className || '').substring(0, 80) : '',
                    gpTag: gp ? gp.tagName : '',
                    gpClass: gp ? (gp.className || '').substring(0, 80) : '',
                    // Qual elemento tem o handler de click?
                    hasOnClick: el.onclick !== null,
                    parentHasOnClick: parent ? parent.onclick !== null : false,
                });
            }
        }
        return results;
    }""")

    log(f"  DOM info Adicionar pessoas:")
    for info in dom_info[:5]:
        log(f"    {info}")

    # Tentar via JS: clicar no container correto
    # O modal abre quando se clica no wrapper do campo input[name='people']
    clicked = page.evaluate("""() => {
        // Encontrar o input oculto de Pessoas
        const inp = document.querySelector('input[name="people"]');
        if (inp) {
            // Tentar o wrapper mais proximo que tem handler
            let el = inp.parentElement;
            for (let i = 0; i < 5; i++) {
                if (!el) break;
                el.click();
                el = el.parentElement;
            }
            return 'clicked-ancestors';
        }

        // Alternativa: buscar div com placeholder "Adicionar pessoas"
        const divs = document.querySelectorAll('div');
        for (const div of divs) {
            if (div.innerText && div.innerText.trim() === 'Adicionar pessoas') {
                const parent = div.parentElement;
                if (parent) {
                    parent.click();
                    return 'clicked-parent-of-placeholder';
                }
                div.click();
                return 'clicked-placeholder-div';
            }
        }
        return 'not-found';
    }""")
    log(f"  JS click result: {clicked}")
    page.wait_for_timeout(2500)

    modal = page.locator("[role='dialog']").first
    modal_abriu = modal.count() > 0 and modal.is_visible()
    log(f"  Modal abriu: {modal_abriu}")

    if modal_abriu:
        tw.snap(page, EVID, "tc15e_modal_abriu")
    else:
        # Tentar de outra forma: dispatch click event
        clicked2 = page.evaluate("""() => {
            const inp = document.querySelector('input[name="people"]');
            if (!inp) return 'no-input';
            // Clicar no irmao anterior do input (o container visual)
            const container = inp.previousElementSibling || inp.parentElement;
            if (container) {
                container.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                return 'dispatched';
            }
            return 'no-container';
        }""")
        log(f"  JS dispatch: {clicked2}")
        page.wait_for_timeout(2000)
        modal_abriu = page.locator("[role='dialog']").count() > 0
        log(f"  Modal abriu (v2): {modal_abriu}")

    if not modal_abriu:
        # Ultima tentativa: usar Playwright force click no proprio elemento de texto
        try:
            el = page.locator("text=Adicionar pessoas").first
            el.click(force=True, timeout=5000)
            page.wait_for_timeout(2000)
            modal_abriu = page.locator("[role='dialog']").count() > 0
            log(f"  Modal abriu (force click): {modal_abriu}")
        except Exception as e:
            log(f"  Force click erro: {e}")

    tw.snap(page, EVID, "tc15e_pos_click")

    pessoa_ok = False
    if modal_abriu:
        # Clicar no primeiro checkbox via JS (span do Chakra)
        n = page.evaluate("""() => {
            const modal = document.querySelector('[role=dialog]');
            if (!modal) return 0;
            const spans = modal.querySelectorAll('.chakra-checkbox__control');
            let clicked = 0;
            for (const span of spans) {
                span.click();
                clicked++;
                break;  // Apenas o primeiro
            }
            return clicked;
        }""")
        log(f"  Spans clicados: {n}")
        page.wait_for_timeout(800)

        checked = page.evaluate("""() => {
            const inputs = document.querySelectorAll('[role=dialog] input[type=checkbox]');
            return Array.from(inputs).filter(i => i.checked).length;
        }""")
        log(f"  Checkboxes marcados: {checked}")

        # Clicar Vincular
        try:
            btn_vinc = page.locator("button:has-text('Vincular')").first
            if btn_vinc.count() > 0:
                btn_vinc.click(timeout=5000)
                page.wait_for_timeout(2000)
                modal_fechou = page.locator("[role='dialog']").count() == 0
                log(f"  Modal fechou: {modal_fechou}")
                pessoa_ok = True
        except Exception as e:
            log(f"  Vincular erro: {e}")

    tw.snap(page, EVID, "tc15e_pos_modal")

    # Fechar qualquer modal restante
    if page.locator("[role='dialog']").count() > 0:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

    # Preencher demais campos
    try:
        combos = page.locator("[role='combobox']").all()
        log(f"  Comboboxes: {len(combos)}")
        if combos:
            combos[0].click(timeout=5000)
            page.wait_for_timeout(800)
            if page.locator("[role='option']").count() > 0:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
    except Exception as e:
        log(f"  Provedor erro: {e}")
        page.keyboard.press("Escape")

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

    try:
        page.locator("input[name='workload_seconds']").first.fill("02:00:00")
    except Exception:
        pass
    try:
        page.locator("input[name='endDate']").first.fill("2025-06-01")
    except Exception:
        pass

    tw.snap(page, EVID, "tc15e_form_completo")

    try:
        page.get_by_role("button", name="Salvar").first.click(timeout=5000)
        page.wait_for_timeout(4000)
        dispensar_overlays(page)
    except Exception as e:
        log(f"  Salvar erro: {e}")

    tw.snap(page, EVID, "tc15e_pos_salvar")

    ainda_no_form = "records/new" in page.url
    foi_salvo = not ainda_no_form
    log(f"  URL: {page.url}, foi_salvo={foi_salvo}")

    if not foi_salvo:
        erros = page.locator("[class*='chakra-form__error'], [id*='feedback']").all_text_contents()
        log(f"  Erros: {erros}")
        modal_voltou = page.locator("[role='dialog']").count() > 0
        log(f"  Modal voltou: {modal_voltou}")
        r("TC15", False, f"Nao salvou. Erros={erros}. Modal={modal_voltou}. Pessoa={pessoa_ok}")
        return

    # Lista Admin
    page.goto(RECORDS_ADMIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dispensar_overlays(page)
    aguardar_sem_spinner(page)
    tw.snap(page, EVID, "tc15e_lista")

    lista_txt = page.locator("body").inner_text()
    tem_externo = "Externo" in lista_txt
    tem_aprovado = "Aprovado" in lista_txt or "Emitido" in lista_txt

    try:
        primeira_linha = page.locator("table tbody tr").first
        if primeira_linha.count() > 0:
            linha_txt = primeira_linha.inner_text()
            log(f"  Primeira linha: {linha_txt[:250]}")
    except Exception:
        pass

    tw.snap(page, EVID, "tc15e_origem")

    passou = foi_salvo and tem_externo and tem_aprovado
    r("TC15", passou,
      f"Salvo={foi_salvo}, Externo={tem_externo}, Aprovado/Emitido={tem_aprovado}, Pessoa={pessoa_ok}")


def main():
    log("=" * 60)
    log("QA 1.6 Round 2e -- TC15 via JS click")
    log(f"URL: {BASE_URL} | Org: {ORG_ID}")
    log("=" * 60)

    with tw.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=0)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
        page = ctx.new_page()
        ok = login_admin(page)
        if ok:
            tc15_via_js(page)
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
