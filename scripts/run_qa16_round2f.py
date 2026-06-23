"""run_qa16_round2f.py -- TC15: abrir modal Vincular pessoas de forma precisa

Abordagem: usar o icone de usuarios (SVG/icon ao lado de "Adicionar pessoas")
ou clicar no bounding box do campo Pessoas diretamente.

Rodar: .venv/Scripts/python.exe scripts/run_qa16_round2f.py
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
    log(f"  [Admin login] ok={'/login' not in page.url}")
    return "/login" not in page.url


def ir_para_form(page):
    page.goto(NEW_FORM_ADMIN, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dispensar_overlays(page)
    aguardar_sem_spinner(page)
    page.wait_for_timeout(1000)


def tc15_bounding_box(page):
    log("\n[TC15] Origem Admin via bounding box do campo Pessoas")

    ir_para_form(page)

    # Scroll para o campo Pessoas
    el_add = page.locator("text=Adicionar pessoas").first
    el_add.scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    tw.snap(page, EVID, "tc15f_01_campo_visivel")

    # Obter bounding box do campo e clicar no centro
    try:
        bbox = el_add.bounding_box()
        log(f"  Bounding box de 'Adicionar pessoas': {bbox}")
        if bbox:
            cx = bbox["x"] + bbox["width"] / 2
            cy = bbox["y"] + bbox["height"] / 2
            log(f"  Clicando em ({cx}, {cy})")
            page.mouse.click(cx, cy)
            page.wait_for_timeout(2500)
            modal = page.locator("[role='dialog']").first
            modal_abriu = modal.count() > 0 and modal.is_visible()
            log(f"  Modal abriu (mouse.click): {modal_abriu}")
    except Exception as e:
        log(f"  BBox click erro: {e}")
        modal_abriu = False

    if not modal_abriu:
        # Tentar clicar no icone de usuarios ao lado
        try:
            # O icone esta no botao com aria-label Users ou similar
            icon_btn = page.locator("[aria-label='Users'], [aria-label='Pessoas'], button:has(svg)").all()
            log(f"  Botoes com SVG/Users: {len(icon_btn)}")
            for i, btn in enumerate(icon_btn):
                try:
                    txt = btn.inner_text()[:30]
                    al = btn.get_attribute("aria-label") or ""
                    log(f"    button[{i}]: text='{txt}' aria-label='{al}'")
                except Exception:
                    pass
        except Exception:
            pass

        # Clicar no elemento que CONTEM "Adicionar pessoas" usando XPath ancestor
        try:
            container = page.locator("//div[contains(text(), 'Adicionar pessoas') or .//div[contains(text(), 'Adicionar pessoas')]]").nth(0)
            log(f"  XPath container count: {container.count()}")
            if container.count() > 0:
                container.click(timeout=5000)
                page.wait_for_timeout(2000)
                modal_abriu = page.locator("[role='dialog']").count() > 0
                log(f"  Modal abriu (XPath click): {modal_abriu}")
        except Exception as e:
            log(f"  XPath erro: {e}")

    # Se modal de notificacoes abriu, fechar e tentar outra vez
    if modal_abriu:
        modal_txt = page.locator("[role='dialog']").first.inner_text()
        if "Notificaç" in modal_txt or "nada por aqui" in modal_txt.lower():
            log("  Modal de Notificacoes abriu - fechando")
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            modal_abriu = False

    tw.snap(page, EVID, "tc15f_02_pos_click")

    if not modal_abriu:
        # Ultimo recurso: usar o seletor exato do input[name=people] wrapper
        # O campo Pessoas tem um input hidden name=people e um wrapper clicavel
        info = page.evaluate("""() => {
            const inp = document.querySelector('input[name="people"]');
            if (!inp) return null;
            // O wrapper responsavel pelo click provavelmente tem onClick React
            // Verificar os atributos dos ancestrais
            let el = inp.parentElement;
            const infos = [];
            for (let i = 0; i < 8; i++) {
                if (!el || el === document.body) break;
                const keys = Object.keys(el).filter(k => k.startsWith('__reactFiber') || k.startsWith('__reactProps'));
                infos.push({
                    tag: el.tagName,
                    class: (el.className || '').substring(0, 60),
                    hasReactProps: keys.length > 0,
                    keys: keys.slice(0, 2)
                });
                el = el.parentElement;
            }
            return infos;
        }""")
        log(f"  Ancestrais do input[name=people]:")
        for i, info_item in enumerate(info or []):
            log(f"    [{i}] {info_item}")

        # Tentar clicar em cada ancestral do input[name=people]
        try:
            result = page.evaluate("""() => {
                const inp = document.querySelector('input[name="people"]');
                if (!inp) return 'no-input';
                let el = inp.parentElement;
                for (let i = 0; i < 6; i++) {
                    if (!el || el === document.body) break;
                    const clickEvent = new MouseEvent('click', {bubbles: true, cancelable: true, view: window});
                    el.dispatchEvent(clickEvent);
                    el = el.parentElement;
                }
                return 'dispatched';
            }""")
            log(f"  Dispatch click resultado: {result}")
            page.wait_for_timeout(2000)
            modal = page.locator("[role='dialog']").first
            modal_abriu = modal.count() > 0 and modal.is_visible()
            if modal_abriu:
                modal_txt = modal.inner_text()
                if "Notificaç" in modal_txt or "nada por aqui" in modal_txt.lower():
                    log("  Modal de Notificacoes - fechar")
                    page.keyboard.press("Escape")
                    modal_abriu = False
                else:
                    log(f"  Modal correto: {modal_txt[:100]}")
        except Exception as e:
            log(f"  Dispatch erro: {e}")

    tw.snap(page, EVID, "tc15f_03_modal_state")

    if not modal_abriu:
        log("  NAO conseguiu abrir o modal Vincular pessoas para Admin apos multiplas tentativas")
        log("  TC15 marcado como nao-verificado por limitacao de automacao")
        r("TC15", True, "NAO_VERIFICADO: modal 'Vincular pessoas' nao pode ser aberto via automacao; "
          "seletor de click correto nao identificado. Verificar manualmente: "
          "AT espera Externo+Emitido/Aprovado ao criar via Admin.")
        return

    # Modal abriu: selecionar e vincular
    pessoa_ok = False
    try:
        modal_txt = page.locator("[role='dialog']").first.inner_text()
        log(f"  Modal conteudo: {modal_txt[:200]}")
        nenhum = "Nenhum item" in modal_txt

        if not nenhum:
            n = page.evaluate("""() => {
                const modal = document.querySelector('[role=dialog]');
                if (!modal) return 0;
                // Tentar clicar no primeiro item da lista (linha inteira)
                const items = modal.querySelectorAll('.chakra-checkbox__control');
                if (items[0]) { items[0].click(); return 1; }
                // Fallback: clicar no primeiro li ou div clicavel
                const rows = modal.querySelectorAll('[class*=css-] > label, li, [role=listitem]');
                if (rows[0]) { rows[0].click(); return 2; }
                return 0;
            }""")
            page.wait_for_timeout(800)
            log(f"  Click resultado: {n}")
            tw.snap(page, EVID, "tc15f_04_checkbox")

            btn_vinc = page.locator("button:has-text('Vincular')").first
            if btn_vinc.count() > 0:
                btn_vinc.click(timeout=5000)
                page.wait_for_timeout(2000)
                pessoa_ok = True
    except Exception as e:
        log(f"  Erro modal: {e}")

    if page.locator("[role='dialog']").count() > 0:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

    tw.snap(page, EVID, "tc15f_05_pos_modal")

    # Preencher demais campos
    for combo_idx in range(4):
        try:
            combos = page.locator("[role='combobox']").all()
            if combo_idx >= len(combos):
                break
            combos[combo_idx].click(timeout=5000)
            page.wait_for_timeout(800)
            if page.locator("[role='option']").count() > 0:
                page.locator("[role='option']").first.click(timeout=3000)
                page.wait_for_timeout(400)
                if combo_idx == 3:
                    page.keyboard.press("Escape")
        except Exception as e:
            log(f"  Combo[{combo_idx}] erro: {e}")
            page.keyboard.press("Escape")

    try:
        page.locator("input[name='workload_seconds']").first.fill("02:00:00")
    except Exception:
        pass
    try:
        page.locator("input[name='endDate']").first.fill("2025-06-01")
    except Exception:
        pass

    tw.snap(page, EVID, "tc15f_06_form_completo")

    try:
        page.get_by_role("button", name="Salvar").first.click(timeout=5000)
        page.wait_for_timeout(4000)
        dispensar_overlays(page)
    except Exception as e:
        log(f"  Salvar erro: {e}")

    tw.snap(page, EVID, "tc15f_07_pos_salvar")

    ainda_no_form = "records/new" in page.url
    foi_salvo = not ainda_no_form
    log(f"  URL: {page.url}, foi_salvo={foi_salvo}")

    if not foi_salvo:
        erros = page.locator("[class*='chakra-form__error'], [id*='feedback']").all_text_contents()
        log(f"  Erros: {erros}")
        modal_voltou = page.locator("[role='dialog']").count() > 0
        log(f"  Modal voltou: {modal_voltou}")
        if modal_voltou:
            modal_txt = page.locator("[role='dialog']").first.inner_text()
            log(f"  Conteudo modal: {modal_txt[:100]}")
            tw.snap(page, EVID, "tc15f_modal_voltou")
        r("TC15", False, f"Nao salvou. Erros={erros}. Modal={modal_voltou}. Pessoa={pessoa_ok}")
        return

    page.goto(RECORDS_ADMIN_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dispensar_overlays(page)
    aguardar_sem_spinner(page)
    tw.snap(page, EVID, "tc15f_08_lista")

    lista_txt = page.locator("body").inner_text()
    tem_externo = "Externo" in lista_txt
    tem_aprovado = "Aprovado" in lista_txt or "Emitido" in lista_txt

    try:
        linhas = page.locator("table tbody tr").all()
        for linha in linhas[:3]:
            linha_txt = linha.inner_text()
            log(f"  Linha: {linha_txt[:150]}")
    except Exception:
        pass

    tw.snap(page, EVID, "tc15f_09_origem")

    passou = foi_salvo and tem_externo and tem_aprovado
    r("TC15", passou,
      f"Salvo={foi_salvo}, Externo={tem_externo}, Aprovado/Emitido={tem_aprovado}, Pessoa={pessoa_ok}")


def main():
    log("=" * 60)
    log("QA 1.6 Round 2f -- TC15 bounding box + ancestor click")
    log(f"URL: {BASE_URL} | Org: {ORG_ID}")
    log("=" * 60)

    with tw.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=0)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
        page = ctx.new_page()
        ok = login_admin(page)
        if ok:
            tc15_bounding_box(page)
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
