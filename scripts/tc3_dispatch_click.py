"""tc3_dispatch_click.py — Tenta abrir o modal Alterar Senha via dispatch_event('click').

O problema: click_menuitem usa page.locator.click() que nao funciona.
Tentativa: usar locator.dispatch_event('click') que dispara o evento sintetico React.
"""
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

    log("\n[ADMIN] Abrindo kebab e clicando Alterar senha via dispatch_event...")
    page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)

    # Pesquisa
    try:
        busca = page.locator("input[placeholder='Pesquise aqui']").first
        if busca.is_visible(timeout=2000):
            busca.fill("qa11tc342588")
            page.wait_for_timeout(1500)
    except Exception:
        pass

    row = page.locator("tr").filter(has_text="qa11tc342588@twygotest.com").first
    if row.count() == 0:
        BLOQUEIO = "Linha nao encontrada"
        return False

    kebab = row.locator("button").last
    kebab.click(force=True)
    page.wait_for_timeout(1200)

    # Pega o id do menuitem Alterar senha
    id_alterar = page.evaluate(
        "(pal)=>{const ms=Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
        "const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;});"
        "const m=ms[ms.length-1];if(!m)return '';"
        "const it=Array.from(m.querySelectorAll('[role=menuitem]'))"
        ".find(e=>new RegExp(pal,'i').test(e.innerText||''));return it?it.id:'';}",
        "Alterar senha"
    )
    log(f"ID menuitem: {id_alterar!r}")

    if not id_alterar:
        BLOQUEIO = "Menuitem nao encontrado"
        return False

    # Tenta varios metodos de clique
    item = page.locator(f'[id="{id_alterar}"]')

    # Metodo 1: dispatch_event('click')
    log("  Tentativa 1: dispatch_event('click')...")
    item.dispatch_event("click")
    page.wait_for_timeout(2000)
    menus_apos = page.evaluate(
        "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
        "const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
    )
    log(f"  Menus apos dispatch_event('click'): {menus_apos}")
    campos_pw = page.locator("input[type='password']").count()
    log(f"  Campos password: {campos_pw}")
    tw.snap(page, EVID, "tc3_dispatch_m1")

    # Metodo 2: se menu ainda aberto, tenta pointerdown + pointerup + click
    if menus_apos > 0 or campos_pw == 0:
        log("  Tentativa 2: pointerdown + click...")
        kebab.click(force=True)
        page.wait_for_timeout(800)
        id_alterar2 = page.evaluate(
            "(pal)=>{const ms=Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
            "const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;});"
            "const m=ms[ms.length-1];if(!m)return '';"
            "const it=Array.from(m.querySelectorAll('[role=menuitem]'))"
            ".find(e=>new RegExp(pal,'i').test(e.innerText||''));return it?it.id:'';}",
            "Alterar senha"
        )
        if id_alterar2:
            item2 = page.locator(f'[id="{id_alterar2}"]')
            item2.dispatch_event("pointerdown")
            page.wait_for_timeout(100)
            item2.dispatch_event("pointerup")
            page.wait_for_timeout(100)
            item2.dispatch_event("click")
            page.wait_for_timeout(2000)
            menus_m2 = page.evaluate(
                "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
                "const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
            )
            campos_m2 = page.locator("input[type='password']").count()
            log(f"  Menus apos M2: {menus_m2}, campos_pw: {campos_m2}")
            tw.snap(page, EVID, "tc3_dispatch_m2")

    # Verifica se modal abriu
    campos_pw_final = page.locator("input[type='password']").count()
    log(f"  Campos password final: {campos_pw_final}")

    if campos_pw_final == 0:
        # Inspeciona o DOM para ver o que existe de novo
        dom_info = page.evaluate("""() => {
            // Todos inputs visiveis
            const inputs = Array.from(document.querySelectorAll('input, [class*="chakra-modal"]')).filter(el => {
                const s = getComputedStyle(el);
                return s.display !== 'none' && s.visibility !== 'hidden' && parseFloat(s.opacity) > 0.5;
            });
            return inputs.map(el => ({
                tag: el.tagName,
                type: el.type || '',
                id: el.id,
                ph: el.placeholder || '',
                cls: el.className.slice(0, 50)
            }));
        }""")
        log(f"  DOM visiveis: {dom_info[:5]}")
        BLOQUEIO = "Modal de Alterar Senha nao abriu via dispatch_event"
        return False

    # Preenche a senha
    campo = page.locator("input[type='password']").first
    campo.fill(TC3_NOVA_SENHA)
    page.wait_for_timeout(500)
    tw.snap(page, EVID, "tc3_dispatch_senha_preenchida")

    # Confirma
    btn = page.locator("button[type='submit'], button").filter(
        has_text=__import__("re").compile(r"Salvar|Confirmar|Alterar|OK", __import__("re").I)
    ).last
    btn.click()
    page.wait_for_timeout(2000)
    tw.snap(page, EVID, "fechamento_tc3_senha_definida")
    log("  Senha definida com sucesso")
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
    log(f"  URL: {page.url[:80]}")
    tw.snap(page, EVID, "tc3_dispatch_pos_login")

    if "/login" in page.url:
        BLOQUEIO = f"Login falhou para {TC3_EMAIL}"
        tw.snap(page, EVID, "tc3_dispatch_login_falhou")
        return

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
    log(f"  URL Historico: {page.url[:80]}")
    tw.snap(page, EVID, "tc3_dispatch_meu_historico")

    msg_esperada = "Você ainda não tem registros. Adicione o primeiro pelo botão acima."
    msg = False
    try:
        msg = page.locator(f"text={msg_esperada}").first.is_visible(timeout=5000)
    except Exception:
        pass
    if not msg:
        try:
            msg = page.locator("text=Você ainda não tem registros").first.is_visible(timeout=2000)
        except Exception:
            pass
    check(msg, "mensagem_empty_state")

    tw.snap(page, EVID, "tc3_dispatch_kpis")
    kpis_ok = 0
    for label in ["Emitidos", "Expirados", "Pendentes", "Recusados"]:
        try:
            c = page.locator(f"text={label}").locator("..").locator("..").first
            texto = c.inner_text()
            if "0" in texto:
                kpis_ok += 1
            log(f"  KPI {label!r}: {texto[:40].strip()!r}")
        except Exception as e:
            log(f"  KPI {label!r}: {e}")
    check(kpis_ok == 4, f"4_kpis_zero ({kpis_ok}/4)")

    tw.snap(page, EVID, "fechamento_tc3_empty_ok")
    log("  Screenshot fechamento_tc3_empty_ok.png capturado")


def main():
    global BLOQUEIO

    log("=" * 60)
    log("tc3_dispatch_click.py")
    log("=" * 60)

    # Sessao 1: Admin
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
            ok = admin_alterar_senha(page)
            if BLOQUEIO or not ok:
                log(f"BLOQUEIO: {BLOQUEIO}")
        finally:
            ctx.close()
            browser.close()

    if BLOQUEIO:
        log(f"\nTC3: BLOQUEADO — {BLOQUEIO}")
        return

    # Sessao 2: Aluno
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
