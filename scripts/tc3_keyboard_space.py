"""tc3_keyboard_space.py — Navega menu com ArrowDown e ativa com Space."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
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


def admin_alterar_senha(page):
    global BLOQUEIO

    page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)

    busca = page.locator("input[placeholder='Pesquise aqui']").first
    if busca.is_visible(timeout=2000):
        busca.fill("qa11tc342588")
        page.wait_for_timeout(1500)

    row = page.locator("tr").filter(has_text="qa11tc342588@twygotest.com").first
    kebab = row.locator("button").last
    kebab.click(force=True)
    page.wait_for_timeout(1200)

    itens = tw.menu_visivel(page)
    alterar_idx = next((i for i, t in enumerate(itens) if "alterar" in t.lower()), -1)
    log(f"Menu: {itens} | idx Alterar senha: {alterar_idx}")

    if alterar_idx < 0:
        BLOQUEIO = "Item nao encontrado"
        return False

    # Navega com ArrowDown ate Alterar senha
    # Chakra poe foco no primeiro item por padrao quando o menu abre
    for _ in range(alterar_idx):
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(200)

    tw.snap(page, EVID, "tc3_kb_antes_ativar")
    log(f"  Menu com 'Alterar senha' destacado. Tentando ativar...")

    # Tenta Space (WAI-ARIA standard para ativar)
    page.keyboard.press("Space")
    page.wait_for_timeout(2000)
    campos = page.locator("input[type='password']").count()
    log(f"  Campos password apos Space: {campos}")
    tw.snap(page, EVID, "tc3_kb_apos_space")

    if campos > 0:
        log("  MODAL ABRIU via ArrowDown+Space!")
        campo = page.locator("input[type='password']").first
        campo.fill(TC3_NOVA_SENHA)
        page.wait_for_timeout(500)
        btn = page.locator("button").filter(
            has_text=__import__("re").compile(r"Salvar|Confirmar|OK", __import__("re").I)
        ).last
        btn.click()
        page.wait_for_timeout(2000)
        tw.snap(page, EVID, "fechamento_tc3_senha_definida")
        return True

    # Se nao funcionou com Space, tenta usar o focus + keyboard Enter em modo diferente
    # Primeiro fecha o menu se ainda aberto
    menus_count = page.evaluate(
        "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
    )
    if menus_count > 0:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

    # Tenta dar foco direto no kebab e navegar com teclado
    log("  Tentativa com foco direto no kebab...")
    kebab.focus()
    page.wait_for_timeout(200)
    page.keyboard.press("Enter")  # Abre o menu com Enter no botao
    page.wait_for_timeout(800)

    menus_apos_enter = page.evaluate(
        "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
    )
    log(f"  Menus apos Enter no kebab: {menus_apos_enter}")

    if menus_apos_enter > 0:
        # ArrowDown ate Alterar senha
        for _ in range(alterar_idx):
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(200)

        tw.snap(page, EVID, "tc3_kb_focus_antes")
        page.keyboard.press("Enter")
        page.wait_for_timeout(2000)
        campos2 = page.locator("input[type='password']").count()
        log(f"  Campos password apos foco+Enter: {campos2}")
        tw.snap(page, EVID, "tc3_kb_focus_depois")

        if campos2 > 0:
            log("  MODAL ABRIU via focus+keyboard!")
            campo = page.locator("input[type='password']").first
            campo.fill(TC3_NOVA_SENHA)
            page.wait_for_timeout(500)
            btn = page.locator("button").filter(
                has_text=__import__("re").compile(r"Salvar|Confirmar|OK", __import__("re").I)
            ).last
            btn.click()
            page.wait_for_timeout(2000)
            tw.snap(page, EVID, "fechamento_tc3_senha_definida")
            return True

    BLOQUEIO = "Nenhum metodo de teclado conseguiu abrir o modal de Alterar Senha"
    return False


def run_tc3(page):
    global BLOQUEIO

    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
    page.fill("#user_email", TC3_EMAIL)
    page.fill("#user_password", TC3_NOVA_SENHA)
    page.click("#user_submit")
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)
    log(f"  URL: {page.url[:80]}")

    if "/login" in page.url:
        BLOQUEIO = "Login falhou"
        return

    page.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true", wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    tw.snap(page, EVID, "tc3_kb_meu_historico")

    msg = False
    try:
        msg = page.locator("text=Você ainda não tem registros. Adicione o primeiro pelo botão acima.").first.is_visible(timeout=5000)
    except Exception:
        pass
    if not msg:
        try:
            msg = page.locator("text=Você ainda não tem registros").first.is_visible(timeout=2000)
        except Exception:
            pass
    check(msg, "mensagem_empty_state")

    kpis_ok = 0
    for label in ["Emitidos", "Expirados", "Pendentes", "Recusados"]:
        try:
            c = page.locator(f"text={label}").locator("..").locator("..").first
            t = c.inner_text()
            if "0" in t:
                kpis_ok += 1
        except Exception:
            pass
    check(kpis_ok == 4, f"4_kpis_zero ({kpis_ok}/4)")
    tw.snap(page, EVID, "fechamento_tc3_empty_ok")


def main():
    global BLOQUEIO

    log("=" * 60)
    log("tc3_keyboard_space.py")
    log("=" * 60)

    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
            page.fill("#user_email", "dante.tavares@twygo.com")
            page.fill("#user_password", "123456")
            page.click("#user_submit")
            page.wait_for_timeout(3000)
            page.goto(f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)
            ok = admin_alterar_senha(page)
        finally:
            ctx.close()
            browser.close()

    if BLOQUEIO or not ok:
        log(f"\nTC3: BLOQUEADO — {BLOQUEIO}")
        return

    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            run_tc3(page)
        finally:
            ctx.close()
            browser.close()

    log("\n" + "=" * 60)
    if BLOQUEIO:
        log(f"TC3: BLOQUEADO — {BLOQUEIO}")
    elif not FALHOU:
        log(f"TC3: PASSOU ({len(PASSOU)} checks)")
    else:
        log(f"TC3: FALHOU — {FALHOU}")
    log("=" * 60)


if __name__ == "__main__":
    main()
