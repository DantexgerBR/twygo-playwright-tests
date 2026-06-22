"""fechamento_qa11_tc3_final.py — Valida TC3: empty state "Meu Historico".

Fluxo:
1. Admin altera senha do usuario QA11TC3 para "twygoqa2026"
2. Loga como QA11TC3 e acessa "Meu Historico"
3. Valida mensagem + 4 KPI cards com 0

Usuario: qa11tc342588@twygotest.com (id 4298402)
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ADMIN_EMAIL = "dante.tavares@twygo.com"
ADMIN_SENHA = "123456"
ORG_ID = "37079"
TC3_EMAIL = "qa11tc342588@twygotest.com"
TC3_NOVA_SENHA = "twygoqa2026"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa11"
EVID.mkdir(parents=True, exist_ok=True)

PASSOU = []
FALHOU = []


def log(msg):
    print(msg, flush=True)


def check(cond, label):
    if cond:
        PASSOU.append(label)
        log(f"  OK  {label}")
    else:
        FALHOU.append(label)
        log(f"  FAIL {label}")
    return cond


def admin_alterar_senha(page):
    """Admin altera senha do usuario QA11TC3 via kebab > Alterar senha."""
    log("\n[ADMIN] Acessando lista de usuarios...")
    page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)

    # Busca o usuario
    try:
        busca = page.locator("input[placeholder='Pesquise aqui']").first
        if busca.is_visible(timeout=3000):
            busca.fill("QA11TC3")
            page.wait_for_timeout(1500)
    except Exception:
        pass

    # Abre kebab da linha
    row = page.locator("tr, [role='row']").filter(has_text="QA11TC3").first
    if row.count() == 0:
        row = page.locator("tr, [role='row']").filter(has_text="qa11tc342588").first
    log(f"  Linha usuario: {row.count() > 0}")

    kebab = row.locator("button").last
    kebab.scroll_into_view_if_needed()
    kebab.click()
    page.wait_for_timeout(800)
    tw.snap(page, EVID, "tc3_kebab_menu")

    # Clica em "Alterar senha"
    item_senha = page.locator("[role='menuitem']").filter(has_text="Alterar senha").first
    item_senha.click()
    page.wait_for_timeout(1000)
    tw.snap(page, EVID, "tc3_modal_alterar_senha")
    log("  Modal alterar senha aberto")

    # Preenche a nova senha
    # Inspeciona os inputs do modal
    inputs = page.locator("dialog input, [role='dialog'] input, [data-focus-lock-disabled] input").all()
    log(f"  Inputs no modal: {len(inputs)}")
    for inp in inputs:
        try:
            placeholder = inp.get_attribute("placeholder") or ""
            tipo = inp.get_attribute("type") or ""
            log(f"    type={tipo!r} placeholder={placeholder!r}")
        except Exception:
            pass

    # Tenta pelo placeholder
    try:
        campo_senha = page.locator("input[placeholder*='senha'], input[placeholder*='Senha'], input[placeholder*='password']").first
        if campo_senha.count() > 0 and campo_senha.is_visible(timeout=2000):
            campo_senha.fill(TC3_NOVA_SENHA)
            log(f"  Senha preenchida via placeholder")
        else:
            # Fallback: primeiro input de tipo password visivel
            campo_pw = page.locator("input[type='password']").first
            if campo_pw.is_visible(timeout=2000):
                campo_pw.fill(TC3_NOVA_SENHA)
                log("  Senha preenchida via type=password")
    except Exception as e:
        log(f"  Erro ao preencher senha: {e}")

    tw.snap(page, EVID, "tc3_modal_senha_preenchida")

    # Confirma
    try:
        btn_salvar = page.locator("button").filter(has_text=re.compile(r"Salvar|Confirmar|Alterar|OK", re.I)).last
        btn_salvar.click()
        page.wait_for_timeout(1500)
        log("  Senha salva")
        tw.snap(page, EVID, "tc3_pos_alterar_senha")
    except Exception as e:
        log(f"  Erro ao salvar senha: {e}")

    # Dump do HTML do modal para debug
    modal_html = page.evaluate("""() => {
        const sel = '[role="dialog"], dialog, [data-focus-lock-disabled="false"]';
        const el = document.querySelector(sel);
        return el ? el.outerHTML.slice(0, 3000) : 'modal nao encontrado';
    }""")
    log(f"\n  HTML modal:\n{modal_html[:500]}")


def run_tc3(page):
    """Loga como QA11TC3 e valida empty state."""
    log("\n[TC3] Login como usuario sem registros...")
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("#user_email", timeout=15000)
    page.fill("#user_email", TC3_EMAIL)
    page.fill("#user_password", TC3_NOVA_SENHA)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    log(f"  URL pos-login: {page.url[:80]}")
    tw.snap(page, EVID, "fechamento_tc3_pos_login")

    # Navega para Meu Historico
    page.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
              wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    tw.snap(page, EVID, "fechamento_tc3_meu_historico")
    log(f"  URL Meu Historico: {page.url[:80]}")

    # PASSO 1: Valida mensagem empty state
    msg_esperada = "Você ainda não tem registros. Adicione o primeiro pelo botão acima."
    msg_loc = page.locator(f"text={msg_esperada}").first
    msg_encontrada = False
    try:
        msg_encontrada = msg_loc.is_visible(timeout=5000)
    except Exception:
        pass

    # Tenta variações da mensagem
    if not msg_encontrada:
        variacao = page.locator("text=Você ainda não tem registros").first
        try:
            msg_encontrada = variacao.is_visible(timeout=2000)
        except Exception:
            pass

    check(msg_encontrada, "mensagem_empty_state")
    if not msg_encontrada:
        # Dump do texto da pagina para debug
        corpo = page.locator("main, [class*='container'], [class*='content']").first
        try:
            log(f"  Texto da pagina: {corpo.inner_text()[:500]}")
        except Exception:
            pass

    # PASSO 2: Valida 4 KPI cards com "0"
    tw.snap(page, EVID, "fechamento_tc3_kpis")

    kpi_labels = ["Emitidos", "Expirados", "Pendentes", "Recusados"]
    kpis_ok = 0
    for label in kpi_labels:
        # Cada card deve ter label + valor "0"
        card = page.locator(f"text={label}").locator("..").locator("..").first
        try:
            card_text = card.inner_text()
            has_zero = "0" in card_text
            log(f"  KPI {label}: {card_text[:50].strip()!r} => zero={has_zero}")
            if has_zero:
                kpis_ok += 1
        except Exception as e:
            log(f"  KPI {label}: erro={e}")

    check(kpis_ok == 4, f"4_kpis_todos_zerados ({kpis_ok}/4)")
    tw.snap(page, EVID, "fechamento_tc3_visao_geral")


def main():
    log("=" * 60)
    log("fechamento_qa11_tc3_final.py")
    log("=" * 60)

    # Sessao 1: Admin altera senha
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("#user_email", timeout=15000)
            page.fill("#user_email", ADMIN_EMAIL)
            page.fill("#user_password", ADMIN_SENHA)
            page.click("#user_submit")
            try:
                page.wait_for_load_state("networkidle", timeout=25000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)

            page.goto(
                f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
                wait_until="domcontentloaded", timeout=60000
            )
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            log(f"Admin logado: {page.url[:60]}")

            admin_alterar_senha(page)
        finally:
            ctx.close()
            browser.close()

    # Sessao 2: Login como TC3 e valida empty state
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            run_tc3(page)
        finally:
            ctx.close()
            browser.close()

    log("\n" + "=" * 60)
    log("RESULTADO TC3:")
    log(f"  PASSOU: {len(PASSOU)} checks")
    log(f"  FALHOU: {len(FALHOU)} checks")
    for f in FALHOU:
        log(f"    - {f}")
    if not FALHOU:
        log("TC3: PASSOU")
    else:
        log("TC3: FALHOU")
    log("=" * 60)


if __name__ == "__main__":
    main()
