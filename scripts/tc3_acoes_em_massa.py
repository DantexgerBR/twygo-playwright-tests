"""tc3_acoes_em_massa.py — Usa Acoes em massa > Redefinir senha para o QA11TC3.

Fluxo:
1. Admin seleciona checkbox da linha do usuario
2. Clica em "Acoes em massa"
3. Seleciona a acao de redefinir/alterar senha no dropdown
4. Preenche a nova senha
5. Executa
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
USER_ID = "4298402"
TC3_EMAIL = "qa11tc342588@twygotest.com"
TC3_NOVA_SENHA = "twygoqa2026"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa11"
EVID.mkdir(parents=True, exist_ok=True)

BLOQUEIO = None
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


def admin_redefinir_senha_massa(page):
    global BLOQUEIO

    log("\n[ADMIN] Acoes em massa > Redefinir senha...")
    page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)

    if "/users" not in page.url:
        BLOQUEIO = f"Acesso negado. URL: {page.url}"
        return False

    # Pesquisa usuario
    try:
        busca = page.locator("input[placeholder='Pesquise aqui']").first
        if busca.is_visible(timeout=2000):
            busca.fill("qa11tc342588")
            page.wait_for_timeout(1500)
    except Exception:
        pass

    # Localiza linha e seleciona checkbox
    row = page.locator("tr").filter(has_text="qa11tc342588@twygotest.com").first
    if row.count() == 0:
        BLOQUEIO = "Linha do usuario nao encontrada"
        return False

    checkbox = row.locator("input[type='checkbox']").first
    if checkbox.count() == 0:
        # Tenta qualquer checkbox da linha
        checkbox = row.locator("td").first.locator("input").first
    if checkbox.count() > 0:
        checkbox.check(force=True)
        page.wait_for_timeout(500)
        log("  Checkbox selecionado")
    else:
        BLOQUEIO = "Checkbox nao encontrado na linha"
        return False

    tw.snap(page, EVID, "tc3_massa_checkbox")

    # Clica em "Acoes em massa"
    btn_acoes = page.locator("button").filter(has_text="Ações em massa").first
    if btn_acoes.count() == 0:
        BLOQUEIO = "Botao 'Acoes em massa' nao encontrado"
        tw.snap(page, EVID, "tc3_massa_sem_botao")
        return False

    btn_acoes.click()
    page.wait_for_timeout(1500)
    tw.snap(page, EVID, "tc3_massa_drawer")
    log("  Drawer 'Acoes em massa' aberto")

    # Inspeciona o dropdown "Acao"
    select_acao = page.locator("select, [role='combobox']").first
    if select_acao.count() == 0:
        # Tenta encontrar qualquer select no drawer
        select_acao = page.locator(".chakra-select, select[name], select[id]").first

    options_info = page.evaluate("""() => {
        const selects = document.querySelectorAll('select');
        const results = [];
        for (const sel of selects) {
            const opts = Array.from(sel.options).map(o => ({value: o.value, text: o.text}));
            results.push({id: sel.id, name: sel.name, options: opts});
        }
        return results;
    }""")
    log(f"  Selects e opcoes: {options_info}")

    # Encontra a opcao de redefinir/alterar senha
    senha_value = None
    for sel in options_info:
        for opt in sel.get("options", []):
            if "senha" in opt.get("text", "").lower() or "password" in opt.get("text", "").lower():
                senha_value = opt.get("value")
                log(f"  Opcao de senha encontrada: {opt}")
                break

    if not senha_value:
        log("  Opcao de senha nao encontrada. Opcoes disponiveis:")
        for sel in options_info:
            for opt in sel.get("options", []):
                log(f"    value={opt.get('value')!r} text={opt.get('text')!r}")
        tw.snap(page, EVID, "tc3_massa_sem_opcao_senha")
        BLOQUEIO = "Opcao de 'Redefinir/Alterar senha' nao encontrada no dropdown"
        return False

    # Seleciona a acao
    select_el = page.locator("select").first
    select_el.select_option(value=senha_value)
    page.wait_for_timeout(1000)
    tw.snap(page, EVID, "tc3_massa_acao_selecionada")
    log(f"  Acao selecionada: {senha_value!r}")

    # Verifica se apareceu campo de nova senha
    campo_nova_senha = page.locator("input[type='password'], input[placeholder*='senha'], input[placeholder*='Senha']").first
    if campo_nova_senha.count() > 0 and campo_nova_senha.is_visible(timeout=3000):
        campo_nova_senha.fill(TC3_NOVA_SENHA)
        log("  Nova senha preenchida")
    else:
        log("  Nao ha campo de nova senha — a acao pode ser 'enviar email de redefinicao'")

    tw.snap(page, EVID, "tc3_massa_pre_executar")

    # Clica em Executar
    btn_executar = page.locator("button").filter(has_text="Executar").last
    if btn_executar.count() > 0:
        btn_executar.click()
        page.wait_for_timeout(2000)
        log("  Executar clicado")
        tw.snap(page, EVID, "fechamento_tc3_senha_definida")
    else:
        BLOQUEIO = "Botao Executar nao encontrado"
        return False

    return True


def run_tc3(page):
    global BLOQUEIO

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
    tw.snap(page, EVID, "tc3_massa_pos_login")

    if "/login" in page.url:
        try:
            erro = page.locator("[class*='error'], [class*='alert'], [class*='flash']").first
            msg_erro = erro.inner_text() if erro.count() > 0 else "Sem mensagem de erro"
        except Exception:
            msg_erro = ""
        BLOQUEIO = f"Login falhou para {TC3_EMAIL}. Erro: {msg_erro[:200]}"
        tw.snap(page, EVID, "tc3_massa_login_falhou")
        return

    log("  Login bem-sucedido")

    # Navega para Meu Historico
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
        wait_until="domcontentloaded", timeout=60000
    )
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    log(f"  URL Meu Historico: {page.url[:80]}")
    tw.snap(page, EVID, "tc3_massa_meu_historico")

    # PASSO 1: Mensagem de empty state
    msg_esperada = "Você ainda não tem registros. Adicione o primeiro pelo botão acima."
    msg_encontrada = False
    try:
        msg_encontrada = page.locator(f"text={msg_esperada}").first.is_visible(timeout=5000)
    except Exception:
        pass
    if not msg_encontrada:
        try:
            msg_encontrada = page.locator("text=Você ainda não tem registros").first.is_visible(timeout=2000)
            if msg_encontrada:
                log("  Mensagem encontrada (variacao parcial)")
        except Exception:
            pass
    if not msg_encontrada:
        try:
            corpo = page.locator("main, body").first.inner_text()[:500]
            log(f"  Texto pagina: {corpo}")
        except Exception:
            pass

    check(msg_encontrada, "mensagem_empty_state")

    # PASSO 2: 4 KPI cards com 0
    tw.snap(page, EVID, "tc3_massa_kpis")
    kpi_labels = ["Emitidos", "Expirados", "Pendentes", "Recusados"]
    kpis_ok = 0
    for label in kpi_labels:
        try:
            container = page.locator(f"text={label}").locator("..").locator("..").first
            if container.count() == 0:
                container = page.locator(f"text={label}").locator("..").first
            texto = container.inner_text()
            tem_zero = "0" in texto
            log(f"  KPI {label!r}: {texto[:50].strip()!r} => zero={tem_zero}")
            if tem_zero:
                kpis_ok += 1
        except Exception as e:
            log(f"  KPI {label!r}: erro={e}")
    check(kpis_ok == 4, f"4_kpis_todos_zero ({kpis_ok}/4)")

    tw.snap(page, EVID, "fechamento_tc3_empty_ok")
    log("  Screenshot 'fechamento_tc3_empty_ok.png' capturado")


def main():
    global BLOQUEIO

    log("=" * 60)
    log("tc3_acoes_em_massa.py — TC3 via Acoes em Massa")
    log("=" * 60)

    # SESSAO 1: Admin redefine senha via Acoes em massa
    log("\n--- SESSAO 1: Admin ---")
    ok_alterar = False
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
            page.fill("#user_email", "dante.tavares@twygo.com")
            page.fill("#user_password", "123456")
            page.click("#user_submit")
            page.wait_for_timeout(3000)
            page.goto(
                f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
                wait_until="domcontentloaded"
            )
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)
            log(f"Admin: {page.url[:60]}")

            ok_alterar = admin_redefinir_senha_massa(page)
        finally:
            ctx.close()
            browser.close()

    if BLOQUEIO:
        log(f"\nBLOQUEIO: {BLOQUEIO}")
        log("TC3: BLOQUEADO")
        return

    if not ok_alterar:
        log("TC3: BLOQUEADO (alteracao de senha falhou)")
        return

    # SESSAO 2: Login como TC3 e valida empty state
    log("\n--- SESSAO 2: Usuario QA11TC3 ---")
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            run_tc3(page)
        finally:
            ctx.close()
            browser.close()

    log("\n" + "=" * 60)
    log("RESULTADO TC3:")
    if BLOQUEIO:
        log(f"  BLOQUEADO: {BLOQUEIO}")
    elif not FALHOU:
        log(f"  PASSOU: {len(PASSOU)} checks")
        log("TC3: PASSOU")
    else:
        log(f"  FALHOU: {len(FALHOU)} checks — {FALHOU}")
        log("TC3: FALHOU")
    log("=" * 60)


if __name__ == "__main__":
    main()
