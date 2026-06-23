"""run_qa16_recon2_modal.py -- Recon do modal "Vincular pessoas" e dropdowns
Org 37079 / https://registrosf2.stage.twygoead.com/
Descobre seletores reais para:
  - TC3/TC8/TC14/TC15: campo Pessoas / modal "Vincular pessoas"
  - TC5: dropdown "Tipo de experiencia"
  - TC7: verificar provedores cadastrados como Admin

Rodar: .venv/Scripts/python.exe scripts/run_qa16_recon2_modal.py
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
LIDER_EMAIL    = "qalider@teste.com"
LIDER_PASSWORD = "123456"

SLUG = "registros-f2-qa16"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)

RECORDS_ADMIN_URL = f"{BASE_URL}/o/{ORG_ID}/records"
NEW_FORM_ADMIN    = f"{BASE_URL}/o/{ORG_ID}/records/new"


def log(msg):
    print(msg)


def dispensar_overlays(page):
    tw.dispensar_nps(page)
    try:
        page.evaluate("""() => {
            document.querySelectorAll('#hubspot-messages-iframe-container,[id*="sophia"],[id*="hubspot"]')
                .forEach(e => e.style.display='none');
        }""")
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
    log(f"  [Admin login] URL={page.url}")


def login_lider(page):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", LIDER_EMAIL)
    page.fill("#user_password", LIDER_PASSWORD)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    dispensar_overlays(page)
    log(f"  [Lider login] URL={page.url}")


def ir_para_form(page):
    page.goto(NEW_FORM_ADMIN, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dispensar_overlays(page)
    try:
        page.wait_for_selector(".chakra-spinner", state="hidden", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(1000)


def dump_interativos(page, contexto=""):
    """Imprime todos os elementos interativos visiveis da pagina."""
    log(f"\n--- DUMP INTERATIVOS: {contexto} ---")
    try:
        infos = page.evaluate("""() => {
            const sels = ['button', 'input', '[role=combobox]', '[role=listbox]',
                          '[role=option]', '[role=dialog]', '[role=checkbox]',
                          '[role=menuitem]', 'select', 'a[href]', '[tabindex]',
                          '[data-test-id]', '[aria-label]'];
            const results = [];
            sels.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => {
                    if (el.offsetParent !== null || el.offsetWidth > 0 || el.offsetHeight > 0) {
                        results.push({
                            tag: el.tagName,
                            role: el.getAttribute('role'),
                            type: el.getAttribute('type'),
                            id: el.id,
                            name: el.getAttribute('name'),
                            placeholder: el.getAttribute('placeholder'),
                            ariaLabel: el.getAttribute('aria-label'),
                            dataTestId: el.getAttribute('data-test-id'),
                            text: (el.innerText || el.value || '').substring(0, 80),
                            class: el.className.substring(0, 60),
                        });
                    }
                });
            });
            return results;
        }""")
        for el in infos:
            linha = f"  <{el['tag']}> role={el['role']} type={el['type']} id={el['id']} name={el['name']} placeholder={el['placeholder']} aria-label={el['ariaLabel']} data-test-id={el['dataTestId']} text={repr(el['text'][:60])} class={el['class'][:40]}"
            log(linha)
    except Exception as e:
        log(f"  Erro no dump: {e}")
    log("--- FIM DUMP ---")


def recon_tipo_experiencia(page):
    """Descobre como abrir o dropdown Tipo de experiencia."""
    log("\n[RECON] Tipo de experiencia")

    ir_para_form(page)
    tw.snap(page, EVID, "recon_form_inicial")

    # Estrategia 1: clicar no elemento com texto "Selecione o tipo"
    log("  Tentativa 1: clicar em 'Selecione o tipo'")
    try:
        el = page.locator("text=Selecione o tipo").first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=5000)
            page.wait_for_timeout(1000)
            opcoes = page.locator("[role='option']").all_text_contents()
            log(f"  Opcoes via 'Selecione o tipo': {opcoes}")
            tw.snap(page, EVID, "recon_tc5_via_texto_placeholder")
            if opcoes:
                return opcoes
    except Exception as e:
        log(f"  Falha 1: {e}")

    # Estrategia 2: via div container do select Chakra
    log("  Tentativa 2: via container Chakra do label")
    try:
        # Chakra Select gera um div com role=combobox dentro de um FormControl
        combo = page.locator("div[role='combobox']").all()
        log(f"  Encontrados {len(combo)} comboboxes")
        for i, cb in enumerate(combo):
            try:
                txt = cb.inner_text()
                log(f"    combobox[{i}]: '{txt[:60]}'")
            except Exception:
                pass
    except Exception as e:
        log(f"  Falha 2: {e}")

    # Estrategia 3: via aria-label
    log("  Tentativa 3: via aria-label")
    try:
        all_combos = page.locator("[role='combobox']").all()
        for i, cb in enumerate(all_combos):
            try:
                aria = cb.get_attribute("aria-label") or ""
                txt = cb.inner_text()[:40] if cb.is_visible() else "(oculto)"
                log(f"    combobox[{i}]: aria-label='{aria}' text='{txt}'")
            except Exception:
                pass
    except Exception as e:
        log(f"  Falha 3: {e}")

    # Estrategia 4: listar todos os selects/inputs visiveis
    log("  Estrategia 4: dump completo")
    dump_interativos(page, "form-antes-clique")

    # Tentar clicar no 3o combobox (normalmente Tipo de experiencia e o 3o campo select)
    try:
        combos = page.locator("[role='combobox']").all()
        for i, cb in enumerate(combos):
            log(f"  Clicando combobox[{i}]")
            try:
                cb.click(timeout=3000)
                page.wait_for_timeout(800)
                opcoes = page.locator("[role='option']").all_text_contents()
                if opcoes:
                    log(f"  Opcoes em combobox[{i}]: {opcoes}")
                    tw.snap(page, EVID, f"recon_tc5_combobox_{i}")
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
                else:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(300)
            except Exception as e2:
                log(f"    Erro: {e2}")
    except Exception as e:
        log(f"  Falha 4: {e}")

    return []


def recon_modal_pessoas(page):
    """Descobre como abrir o modal Vincular pessoas."""
    log("\n[RECON] Modal Vincular pessoas (Admin)")

    ir_para_form(page)

    # Capturar requests de pessoas
    requests_capturados = []
    page.on("response", lambda resp: requests_capturados.append({
        "url": resp.url,
        "status": resp.status,
        "method": resp.request.method,
    }) if "user" in resp.url.lower() or "people" in resp.url.lower() or "record" in resp.url.lower() or "person" in resp.url.lower() else None)

    # Estrategia 1: clicar no texto "Adicionar pessoas"
    log("  Tentativa 1: clicar em 'Adicionar pessoas'")
    try:
        el = page.locator("text=Adicionar pessoas").first
        if el.count() > 0 and el.is_visible():
            el.click(timeout=5000)
            page.wait_for_timeout(2000)
            tw.snap(page, EVID, "recon_modal_via_texto_add")
            # Verificar se modal abriu
            modal = page.locator("[role='dialog']").first
            if modal.count() > 0 and modal.is_visible():
                log("  Modal aberto via 'Adicionar pessoas'!")
                dump_interativos(page, "modal-aberto")
                return "Adicionar pessoas"
    except Exception as e:
        log(f"  Falha 1: {e}")

    # Estrategia 2: clicar no container que contem o label Pessoas
    log("  Tentativa 2: clicar no container apos label Pessoas")
    try:
        # O padrao Chakra: label -> FormControl container -> botao ou input
        area = page.locator("label:has-text('Pessoas')").locator("xpath=ancestor::div[contains(@class,'chakra-form-control') or contains(@class,'FormControl')][1]").first
        if area.count() > 0:
            area.click(timeout=5000)
            page.wait_for_timeout(1500)
            tw.snap(page, EVID, "recon_modal_via_form_control")
            modal = page.locator("[role='dialog']").first
            if modal.count() > 0 and modal.is_visible():
                log("  Modal aberto via FormControl!")
                dump_interativos(page, "modal-aberto-fc")
                return "FormControl"
    except Exception as e:
        log(f"  Falha 2: {e}")

    # Estrategia 3: clicar no input oculto relativo a Pessoas
    log("  Tentativa 3: encontrar input oculto de Pessoas")
    try:
        # Listar todos inputs do form
        inputs = page.locator("input").all()
        log(f"  Total inputs no form: {len(inputs)}")
        for i, inp in enumerate(inputs):
            try:
                typ = inp.get_attribute("type") or "text"
                nm = inp.get_attribute("name") or ""
                pid = inp.get_attribute("id") or ""
                ph = inp.get_attribute("placeholder") or ""
                vis = inp.is_visible()
                log(f"    input[{i}]: type={typ} name={nm} id={pid} placeholder={ph} visible={vis}")
            except Exception:
                pass
    except Exception as e:
        log(f"  Falha 3: {e}")

    # Estrategia 4: clicar no botao que estiver no campo Pessoas
    log("  Tentativa 4: button dentro de area Pessoas")
    try:
        # Buscar button com texto ou arialabel relacionado a pessoas
        btns = page.locator("button").all()
        for i, btn in enumerate(btns):
            try:
                txt = (btn.inner_text() or "").strip()
                al = btn.get_attribute("aria-label") or ""
                if txt or al:
                    log(f"    button[{i}]: text='{txt[:40]}' aria-label='{al[:40]}'")
            except Exception:
                pass
    except Exception as e:
        log(f"  Falha 4: {e}")

    tw.snap(page, EVID, "recon_modal_dump_form")
    dump_interativos(page, "form-sem-modal")

    # Estrategia 5: clicar em qualquer elemento clicavel proximo ao label Pessoas
    log("  Tentativa 5: clicar em qualquer filho do form-control de Pessoas")
    try:
        # Pegar o ancestor form-control do label Pessoas
        script = """() => {
            const labels = document.querySelectorAll('label');
            for (const lbl of labels) {
                if (lbl.innerText.includes('Pessoas')) {
                    const fc = lbl.closest('[class*=form-control],[class*=FormControl],[class*=chakra-form]');
                    if (fc) {
                        return {
                            outerHTML: fc.outerHTML.substring(0, 500),
                            children: Array.from(fc.querySelectorAll('*')).map(el => ({
                                tag: el.tagName,
                                class: el.className.substring(0, 60),
                                text: (el.innerText || '').substring(0, 40),
                                role: el.getAttribute('role'),
                                clickable: el.onclick !== null || ['A','BUTTON','INPUT','SELECT'].includes(el.tagName)
                            }))
                        };
                    }
                }
            }
            return null;
        }"""
        resultado = page.evaluate(script)
        if resultado:
            log(f"  FormControl HTML: {resultado['outerHTML'][:300]}")
            log(f"  Filhos do FC:")
            for child in resultado['children'][:20]:
                log(f"    {child}")
    except Exception as e:
        log(f"  Falha 5: {e}")

    return None


def recon_provedores_admin(page):
    """Verifica provedores cadastrados como Admin (no painel de configuracao)."""
    log("\n[RECON] Provedores cadastrados na org 37079")

    # Tentar acessar o painel de Provedores
    urls_tentar = [
        f"{BASE_URL}/o/{ORG_ID}/providers",
        f"{BASE_URL}/o/{ORG_ID}/admin/providers",
        f"{BASE_URL}/o/{ORG_ID}/settings/providers",
        f"{BASE_URL}/o/{ORG_ID}/knowledge_providers",
        f"{BASE_URL}/o/{ORG_ID}/records/providers",
    ]

    for url in urls_tentar:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(2000)
            status_code = page.evaluate("() => window.location.href")
            log(f"  URL {url} -> atual: {status_code}")
            if "404" not in page.url and "not_found" not in page.url.lower():
                tw.snap(page, EVID, f"recon_prov_url_{url.split('/')[-1]}")
                # Ver conteudo
                txt = page.locator("body").inner_text()
                log(f"  Conteudo (200 chars): {txt[:200]}")
                if "provedor" in txt.lower() or "provider" in txt.lower():
                    log("  Encontrado! Esta pode ser a pagina de Provedores.")
                    break
        except Exception as e:
            log(f"  Erro em {url}: {e}")

    # Tambem verificar no dropdown do form
    log("\n  Verificando provedores via dropdown do form (Admin)")
    ir_para_form(page)
    page.wait_for_timeout(1000)

    # Clicar no campo Provedor
    try:
        # Tentar via texto placeholder
        el_prov = page.locator("text=Escolha ou adicione").first
        if el_prov.count() == 0:
            el_prov = page.locator("[placeholder*='provedor'], [placeholder*='Provedor']").first
        if el_prov.count() == 0:
            # Tentar via role=combobox com texto do provedor
            combos = page.locator("[role='combobox']").all()
            log(f"  Comboboxes visiveis: {len(combos)}")
            for i, cb in enumerate(combos):
                try:
                    txt = cb.inner_text()
                    pl = cb.get_attribute("placeholder") or ""
                    log(f"    combobox[{i}]: text='{txt[:50]}' placeholder='{pl}'")
                    if "provedor" in txt.lower() or "provedor" in pl.lower():
                        log(f"    >>> Este parece ser o campo Provedor!")
                        cb.click(timeout=5000)
                        page.wait_for_timeout(1500)
                        opcoes = page.locator("[role='option']").all_text_contents()
                        log(f"    Opcoes Provedor (Admin): {opcoes}")
                        tw.snap(page, EVID, "recon_prov_admin_dropdown")
                        page.keyboard.press("Escape")
                        return opcoes
                except Exception:
                    pass

        if el_prov.count() > 0 and el_prov.is_visible():
            el_prov.click(timeout=5000)
            page.wait_for_timeout(1500)
            opcoes = page.locator("[role='option']").all_text_contents()
            log(f"  Opcoes Provedor (Admin): {opcoes}")
            tw.snap(page, EVID, "recon_prov_admin_dropdown")
            page.keyboard.press("Escape")
            return opcoes
    except Exception as e:
        log(f"  Erro: {e}")

    return []


def recon_lider_modal(page):
    """Recon do modal de Pessoas para o Lider - verifica 401."""
    log("\n[RECON] Modal Pessoas - LIDER (TC3 - verificar 401)")

    respostas_401 = []
    todas_respostas = []

    def capturar_resp(resp):
        info = {
            "url": resp.url,
            "status": resp.status,
            "method": resp.request.method,
        }
        todas_respostas.append(info)
        if resp.status == 401:
            respostas_401.append(info)
            log(f"  [401 CAPTURADO] {resp.request.method} {resp.url}")

    page.on("response", capturar_resp)

    # Ir para o form como Lider
    page.goto(NEW_FORM_ADMIN, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    dispensar_overlays(page)
    tw.snap(page, EVID, "tc3b_01_form_lider")

    # Tentar abrir modal Pessoas com varias estrategias
    modal_aberto = False

    # Estrategia 1: texto "Adicionar pessoas"
    try:
        el = page.locator("text=Adicionar pessoas").first
        if el.count() > 0 and el.is_visible():
            log("  Clicando 'Adicionar pessoas'")
            el.click(timeout=5000)
            page.wait_for_timeout(2500)
            modal_aberto = page.locator("[role='dialog']").count() > 0
            log(f"  Modal aberto: {modal_aberto}")
            tw.snap(page, EVID, "tc3b_02_modal_apos_click")
            if modal_aberto:
                log("  Conteudo do modal:")
                try:
                    modal_txt = page.locator("[role='dialog']").first.inner_text()
                    log(f"  {modal_txt[:300]}")
                except Exception:
                    pass
    except Exception as e:
        log(f"  Estrategia 1 falhou: {e}")

    if not modal_aberto:
        # Estrategia 2: clicar no campo Pessoas (area)
        try:
            # Dump dos botoes visiveis
            btns = page.locator("button").all()
            for i, btn in enumerate(btns):
                try:
                    txt = (btn.inner_text() or "").strip()[:50]
                    log(f"  button[{i}]: '{txt}'")
                except Exception:
                    pass

            # Tentar button com texto relacionado
            btn_add_pessoa = page.locator("button:has-text('Vincular'), button:has-text('Adicionar pessoas'), button:has-text('Pessoas')").first
            if btn_add_pessoa.count() > 0 and btn_add_pessoa.is_visible():
                log("  Clicando botao Pessoas/Vincular/Adicionar")
                btn_add_pessoa.click(timeout=5000)
                page.wait_for_timeout(2000)
                modal_aberto = page.locator("[role='dialog']").count() > 0
                tw.snap(page, EVID, "tc3b_03_estrategia2")
        except Exception as e:
            log(f"  Estrategia 2 falhou: {e}")

    page.wait_for_timeout(1000)
    tw.snap(page, EVID, "tc3b_04_estado_final")

    log(f"\n  Total respostas 401: {len(respostas_401)}")
    for r401 in respostas_401:
        log(f"    401: {r401['method']} {r401['url']}")

    log(f"\n  Total respostas capturadas: {len(todas_respostas)}")
    for resp in todas_respostas[-10:]:
        if resp["status"] >= 400:
            log(f"    [{resp['status']}] {resp['method']} {resp['url']}")

    return respostas_401, modal_aberto


def main():
    log("=" * 60)
    log("RECON 2 -- Modal Vincular Pessoas + Tipo Experiencia + Provedores")
    log(f"URL: {BASE_URL} | Org: {ORG_ID}")
    log("=" * 60)

    with tw.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=0)

        # --- Recon Admin ---
        log("\n[SESSAO ADMIN]")
        ctx_admin = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
        page_admin = ctx_admin.new_page()
        login_admin(page_admin)

        # 1. Recon provedores (Admin)
        provedores_admin = recon_provedores_admin(page_admin)
        log(f"\nProvedores Admin: {provedores_admin}")

        # 2. Recon Tipo de experiencia
        opcoes_tipo = recon_tipo_experiencia(page_admin)
        log(f"\nOpcoes Tipo de experiencia: {opcoes_tipo}")

        # 3. Recon modal Pessoas (Admin)
        seletor_modal = recon_modal_pessoas(page_admin)
        log(f"\nSeletor modal descoberto: {seletor_modal}")

        ctx_admin.close()

        # --- Recon Lider ---
        log("\n[SESSAO LIDER]")
        ctx_lider = browser.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
        page_lider = ctx_lider.new_page()
        login_lider(page_lider)

        respostas_401, modal_aberto_lider = recon_lider_modal(page_lider)

        ctx_lider.close()
        browser.close()

    log("\n" + "=" * 60)
    log("SUMARIO RECON 2")
    log("=" * 60)
    log(f"Provedores Admin no dropdown: {len(provedores_admin)} encontrados")
    log(f"Opcoes Tipo de experiencia: {len(opcoes_tipo)} encontradas: {opcoes_tipo}")
    log(f"Modal Pessoas Lider aberto: {modal_aberto_lider}")
    log(f"Respostas 401 capturadas: {len(respostas_401)}")
    log("=" * 60)


if __name__ == "__main__":
    main()
