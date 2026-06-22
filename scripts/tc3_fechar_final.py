"""tc3_fechar_final.py — Abre modal Alterar senha, preenche ambos os campos, confirma.
Tambem valida o empty state do Meu historico como o usuario qa11tc342588.
"""
import re
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


def main():
    log("=" * 60)
    log("tc3_fechar_final.py — Alterar senha + validar empty state")
    log("=" * 60)

    # --- PARTE 1: Admin altera senha ---
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
            page.fill("#user_email", "dante.tavares@twygo.com")
            page.fill("#user_password", "123456")
            page.click("#user_submit")
            page.wait_for_timeout(3000)
            page.goto(
                f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
                wait_until="domcontentloaded",
            )
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)

            page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded")
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

            # Obtem ID do menuitem
            id_alterar = page.evaluate("""() => {
                const ms = Array.from(document.querySelectorAll('[role=menu]')).filter(m => {
                    const c = getComputedStyle(m);
                    return c.visibility === 'visible' && parseFloat(c.opacity) > 0.5;
                });
                const m = ms[ms.length - 1];
                if (!m) return '';
                const it = Array.from(m.querySelectorAll('[role=menuitem]')).find(
                    e => /alterar senha/i.test(e.innerText || '')
                );
                return it ? it.id : '';
            }""")
            log(f"ID menuitem: {id_alterar!r}")

            if not id_alterar:
                log("ERRO: menuitem nao encontrado")
                return

            # hover + click(force) para abrir o modal
            item = page.locator(f'[id="{id_alterar}"]')
            item.hover()
            page.wait_for_timeout(300)
            item.click(force=True)
            page.wait_for_timeout(2000)

            campos = page.locator("input[type='password']").count()
            log(f"Campos password no modal: {campos}")

            if campos < 2:
                log(f"ERRO: Esperava 2 campos password, encontrou {campos}")
                tw.snap(page, EVID, "tc3_final_erro_modal")
                return

            # Preenche "Nova Senha" (campo 0) e "Confirmacao de senha" (campo 1)
            campos_pw = page.locator("input[type='password']")
            campos_pw.nth(0).fill(TC3_NOVA_SENHA)
            page.wait_for_timeout(300)
            campos_pw.nth(1).fill(TC3_NOVA_SENHA)
            page.wait_for_timeout(300)

            tw.snap(page, EVID, "fechamento_tc3_senha_definida")
            log("Campos preenchidos. Clicando em Confirmar...")

            btn_confirmar = page.get_by_role("button", name=re.compile(r"Confirmar", re.I))
            btn_confirmar.click()
            page.wait_for_timeout(3000)

            # Verifica toast de sucesso
            toast = page.locator("[class*='toast'], [role='alert'], [class*='chakra-toast']").first
            toast_text = ""
            try:
                if toast.is_visible(timeout=3000):
                    toast_text = toast.inner_text()
                    log(f"Toast: {toast_text!r}")
            except Exception:
                pass

            tw.snap(page, EVID, "tc3_final_apos_confirmar")
            log("Senha alterada (ou tentativa registrada)")

        finally:
            browser.close()

    # --- PARTE 2: Login como aluno e valida empty state ---
    log("\nValidando empty state como usuario qa11tc342588...")
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
            page.fill("#user_email", TC3_EMAIL)
            page.fill("#user_password", TC3_NOVA_SENHA)
            page.click("#user_submit")
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)
            log(f"URL pos login: {page.url[:80]}")

            if "/login" in page.url:
                log("BLOQUEADO: Login falhou — senha nao foi alterada com sucesso")
                tw.snap(page, EVID, "tc3_final_login_falhou")
                return

            page.goto(
                f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                wait_until="domcontentloaded",
            )
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)

            # Verifica mensagem de empty state
            msg = False
            for selector in [
                "text=Você ainda não tem registros. Adicione o primeiro pelo botão acima.",
                "text=Você ainda não tem registros",
                "text=ainda não tem registros",
            ]:
                try:
                    if page.locator(selector).first.is_visible(timeout=3000):
                        msg = True
                        log(f"  Mensagem empty state encontrada: {selector!r}")
                        break
                except Exception:
                    pass

            check(msg, "mensagem_empty_state")

            # Verifica 4 KPIs com valor 0
            kpis_ok = 0
            for label in ["Emitidos", "Expirados", "Pendentes", "Recusados"]:
                try:
                    c = page.locator(f"text={label}").locator("..").locator("..").first
                    t = c.inner_text()
                    if "0" in t:
                        kpis_ok += 1
                        log(f"  KPI '{label}': 0 OK")
                    else:
                        log(f"  KPI '{label}': {t!r}")
                except Exception as e:
                    log(f"  KPI '{label}': erro {e}")

            check(kpis_ok == 4, f"4_kpis_zero ({kpis_ok}/4)")

            tw.snap(page, EVID, "fechamento_tc3_empty_ok")
            log("Screenshot fechamento_tc3_empty_ok.png capturado")

        finally:
            browser.close()

    log("\n" + "=" * 60)
    if not FALHOU:
        log(f"TC3: PASSOU ({len(PASSOU)} checks OK)")
    else:
        log(f"TC3: FALHOU — {FALHOU}")
    log("=" * 60)


if __name__ == "__main__":
    main()
