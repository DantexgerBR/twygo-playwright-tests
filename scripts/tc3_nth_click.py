"""tc3_nth_click.py — Clica no 3o menuitem (Alterar senha) usando nth() e tab/enter."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
from playwright.sync_api import sync_playwright

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
    log(f"Menu: {itens}")
    # Alterar senha e o 3o item (index 2)
    alterar_idx = next((i for i, t in enumerate(itens) if "alterar" in t.lower()), -1)
    log(f"Indice de 'Alterar senha': {alterar_idx}")

    if alterar_idx < 0:
        BLOQUEIO = "Item nao encontrado"
        return False

    # Metodo 1: nth() no menu visivel
    log("  Metodo 1: nth() no menu visivel...")
    menus_loc = page.locator("[role='menu']").filter(
        has=page.locator("[role='menuitem']")
    )
    item_nth = menus_loc.locator("[role='menuitem']").nth(alterar_idx)
    log(f"  Item nth text: {item_nth.inner_text()[:30]!r}")
    item_nth.click(timeout=5000)
    page.wait_for_timeout(2000)
    campos = page.locator("input[type='password']").count()
    menus = page.evaluate(
        "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
    )
    log(f"  Campos password: {campos}, menus: {menus}")
    tw.snap(page, EVID, "tc3_nth_m1")

    if campos > 0:
        log("  MODAL ABRIU!")
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

    # Metodo 2: keyboard Tab + Enter para navegar e selecionar
    log("  Metodo 2: Reabrindo kebab e usando Tab+Enter...")
    if menus > 0:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

    kebab.click(force=True)
    page.wait_for_timeout(1000)

    # Tab para navegar ate "Alterar senha" e Enter para selecionar
    for _ in range(alterar_idx + 1):
        page.keyboard.press("Tab")
        page.wait_for_timeout(200)

    # Enter para confirmar
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)
    campos2 = page.locator("input[type='password']").count()
    log(f"  Campos password apos Tab+Enter: {campos2}")
    tw.snap(page, EVID, "tc3_nth_m2")

    if campos2 > 0:
        log("  MODAL ABRIU via Tab+Enter!")
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

    # Metodo 3: Fecha e usa ArrowDown + Enter para navegar
    log("  Metodo 3: ArrowDown+Enter no menu...")
    if page.evaluate(
        "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
    ) > 0:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

    kebab.click(force=True)
    page.wait_for_timeout(1000)

    # ArrowDown para navegar no menu ate Alterar senha
    for _ in range(alterar_idx):
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(200)

    tw.snap(page, EVID, "tc3_nth_m3_before_enter")
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)
    campos3 = page.locator("input[type='password']").count()
    log(f"  Campos password apos ArrowDown+Enter: {campos3}")
    tw.snap(page, EVID, "tc3_nth_m3")

    if campos3 > 0:
        log("  MODAL ABRIU via ArrowDown+Enter!")
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

    BLOQUEIO = "Nenhum metodo conseguiu abrir o modal de Alterar Senha"
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
    tw.snap(page, EVID, "tc3_nth_meu_historico")

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
    log("tc3_nth_click.py")
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
