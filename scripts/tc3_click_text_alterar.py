"""tc3_click_text_alterar.py — Clica diretamente no texto 'Alterar senha' do menu.

Teoria: o clique anterior estava no container do menuitem (wrapper div).
Desta vez, clicamos diretamente no texto 'Alterar senha' que aparece no item.
"""
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

    page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=60000)
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
    if row.count() == 0:
        BLOQUEIO = "Linha nao encontrada"
        return False

    kebab = row.locator("button").last
    kebab.click(force=True)
    page.wait_for_timeout(1200)

    # ABORDAGEM: localizar o SPAN ou TEXT que diz "Alterar senha" dentro do menu visivel
    # e clicar diretamente nele (nao no li parent)
    alterar_text = page.locator("[role='menu'] >> text='Alterar senha'").first
    if alterar_text.count() == 0:
        alterar_text = page.get_by_role("menuitem", name="Alterar senha").first
    if alterar_text.count() == 0:
        # Tenta pelo span de texto dentro do menu visivel
        alterar_text = page.locator("[class*='chakra-text']").filter(has_text="Alterar senha").first

    if alterar_text.count() > 0:
        log(f"  Localizou texto 'Alterar senha', tentando clicar...")
        try:
            bbox = alterar_text.bounding_box()
            if bbox:
                log(f"  BBox: x={bbox['x']:.0f} y={bbox['y']:.0f} w={bbox['width']:.0f} h={bbox['height']:.0f}")
        except Exception:
            pass
        alterar_text.click(timeout=5000)
        page.wait_for_timeout(2000)
    else:
        log("  Nao encontrou texto 'Alterar senha' por locator")
        BLOQUEIO = "Texto 'Alterar senha' nao encontrado no menu"
        return False

    # Verifica resultado
    campos_pw = page.locator("input[type='password']").count()
    menus = page.evaluate(
        "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
    )
    log(f"  Campos password: {campos_pw}, menus abertos: {menus}")
    tw.snap(page, EVID, "tc3_text_click_resultado")

    if campos_pw == 0:
        # Tenta uma ultima abordagem: usar get_by_text com clique forcado
        log("  Ultima tentativa: get_by_text force=True...")
        kebab.click(force=True)
        page.wait_for_timeout(1000)

        # Espera o menu aparecer e usa get_by_text
        try:
            page.wait_for_selector("[role='menu']", timeout=3000)
            alterar = page.get_by_text("Alterar senha", exact=True).first
            alterar.click(force=True)
            page.wait_for_timeout(2000)
            campos_pw2 = page.locator("input[type='password']").count()
            log(f"  Campos password pos get_by_text: {campos_pw2}")
            tw.snap(page, EVID, "tc3_text_click_final")
            if campos_pw2 == 0:
                BLOQUEIO = "Modal nao abriu mesmo clicando no texto"
                return False
        except Exception as e:
            log(f"  Erro: {e}")
            BLOQUEIO = f"Erro ao clicar no texto: {e}"
            return False

    # Preenche a senha
    campo = page.locator("input[type='password']").first
    campo.fill(TC3_NOVA_SENHA)
    page.wait_for_timeout(500)
    tw.snap(page, EVID, "tc3_text_senha_preenchida")

    btn = page.locator("button").filter(
        has_text=__import__("re").compile(r"Salvar|Confirmar|Alterar|OK", __import__("re").I)
    ).last
    btn.click()
    page.wait_for_timeout(2000)
    tw.snap(page, EVID, "fechamento_tc3_senha_definida")
    log("  Senha definida!")
    return True


def run_tc3(page):
    global BLOQUEIO

    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
    page.fill("#user_email", TC3_EMAIL)
    page.fill("#user_password", TC3_NOVA_SENHA)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    log(f"  URL: {page.url[:80]}")
    tw.snap(page, EVID, "tc3_text_pos_login")

    if "/login" in page.url:
        BLOQUEIO = f"Login falhou"
        tw.snap(page, EVID, "tc3_text_login_falhou")
        return

    page.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true", wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    tw.snap(page, EVID, "tc3_text_meu_historico")

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
    log("  Screenshot fechamento_tc3_empty_ok.png capturado")


def main():
    global BLOQUEIO

    log("=" * 60)
    log("tc3_click_text_alterar.py")
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
