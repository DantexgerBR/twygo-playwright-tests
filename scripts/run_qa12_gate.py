"""run_qa12_gate.py — GATE para a suíte QA 1.2 [Registros F2] Listagem Admin/Líder.

Valida 3 condições antes de qualquer TC:
1. Feature/admin: tela "Aprendizagem > Registros" renderiza como Admin
2. Líder: existe usuário com liderados diretos na org 37079
3. Massa: conta registros e pessoas distintas

Org: 37079  /  https://registrosf2.stage.twygoead.com/
Roda headless.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
SLUG = "registros-f2-qa12"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg)


def try_login(page, email, senha):
    """Tenta login; retorna True se bem-sucedido."""
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", "")
    page.fill("#user_email", email)
    page.wait_for_timeout(300)
    page.fill("#user_password", "")
    page.fill("#user_password", senha)
    page.wait_for_timeout(300)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    return "/users/login" not in page.url


def gate():
    # Lê credenciais corretas da org 37079 (REGISTROSF2_*)
    email = os.environ.get("REGISTROSF2_ADMIN_EMAIL", "")
    senha = os.environ.get("REGISTROSF2_ADMIN_PASSWORD", "")

    if not email or not senha:
        log("BLOQUEIO: REGISTROSF2_ADMIN_EMAIL ou REGISTROSF2_ADMIN_PASSWORD não definido no .env")
        return False

    log(f"[gate] Admin email: {email}")
    log(f"[gate] BASE_URL: {BASE_URL}  ORG_ID: {ORG_ID}")

    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)

        # Login
        log(f"\n[gate] Tentando login com credenciais do .env: {email}")
        ok = try_login(page, email, senha)
        tw.snap(page, EVID, "gate_01_pos_login")

        if not ok:
            log(f"\nBLOQUEIO: credenciais do .env falharam na org 37079.")
            log(f"  URL após tentativa: {page.url}")
            log("  Mensagem: Login ou senha inválidos (credencial não existe nessa org).")
            log("  Ação necessária: Dante deve fornecer REGISTROSF2_ADMIN_EMAIL e REGISTROSF2_ADMIN_PASSWORD")
            log("  no .env, com credenciais válidas para https://registrosf2.stage.twygoead.com/")
            ctx.close(); browser.close()
            return False

        log(f"[gate] Login OK: {email}")

        # Switch para perfil admin na org 37079
        page.goto(
            f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        page.wait_for_timeout(3000)
        tw.dispensar_nps(page)
        tw.snap(page, EVID, "gate_01b_pos_switch")

        # Navegar para Aprendizagem > Registros
        log("\n[gate] Navegando para Aprendizagem > Registros...")
        rotas_candidatas = [
            f"{BASE_URL}/o/{ORG_ID}/learning_records",
            f"{BASE_URL}/o/{ORG_ID}/aprendizagem/registros",
            f"{BASE_URL}/o/{ORG_ID}/records",
        ]

        feature_ok = False
        rota_ok = ""
        for rota in rotas_candidatas:
            log(f"[gate] Tentando rota: {rota}")
            page.goto(rota, wait_until="domcontentloaded", timeout=20000)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)

            cur = page.url
            log(f"[gate] URL resultante: {cur}")
            if "/users/login" in cur:
                log("BLOQUEIO: sessão inválida — redirecionou para login.")
                ctx.close(); browser.close()
                return False

            has_tab_provedores = page.locator("button, a, [role=tab]").filter(has_text="Provedores").count() > 0
            has_adicionar = page.get_by_role("button", name="Adicionar").count() > 0
            has_kpi_emitidos = page.get_by_text("Emitidos").count() > 0

            log(f"[gate] tab Provedores={has_tab_provedores}, Adicionar={has_adicionar}, KPI Emitidos={has_kpi_emitidos}")

            if has_tab_provedores and has_adicionar:
                feature_ok = True
                rota_ok = rota
                log(f"[gate] Tela Admin de Registros encontrada em: {rota}")
                break

        tw.snap(page, EVID, "gate_02_registros_admin", full=True)

        if not feature_ok:
            body_text = page.locator("body").inner_text()[:600]
            log(f"[gate] Texto da tela:\n{body_text}")
            log("\nGATE 1 FALHOU: Tela 'Aprendizagem > Registros' não renderizou.")
            log("BLOQUEIO: feature não habilitada ou rota desconhecida na org 37079.")
            ctx.close(); browser.close()
            return False

        log("\nGATE 1 OK: Tela 'Aprendizagem > Registros' renderizou como Admin.")
        log(f"  Rota: {rota_ok}")

        # Recon — cabeçalhos da tabela
        headers = []
        for th in page.locator("table th, thead th, [role='columnheader']").all():
            t = th.inner_text().strip()
            if t:
                headers.append(t)
        log(f"\n[recon] Colunas da tabela: {headers}")

        # Breadcrumb
        breadcrumb_texts = []
        for el in page.locator("nav a, nav span, [aria-label='breadcrumb'] a, [aria-label='breadcrumb'] span").all():
            t = el.inner_text().strip()
            if t:
                breadcrumb_texts.append(t)
        log(f"[recon] Breadcrumb: {breadcrumb_texts}")

        # Toolbar botões
        toolbar_btns = []
        for btn in page.locator("button").all():
            t = btn.inner_text().strip()
            if t and len(t) < 40:
                toolbar_btns.append(t)
        log(f"[recon] Botões: {toolbar_btns[:20]}")

        # Campo busca
        busca = page.locator("input[placeholder*='Pesquise'], input[placeholder*='pesquise'], input[type='search']")
        if busca.count() > 0:
            ph = busca.first.get_attribute("placeholder") or ""
            log(f"[recon] Busca placeholder: '{ph}'")

        # Linhas e pessoas
        row_count = page.locator("table tbody tr").count()
        log(f"\n[recon] Linhas na tabela (page 1, 25/pág): {row_count}")

        pessoas_textos = []
        for td in page.locator("table tbody tr td:nth-child(2)").all():
            t = td.inner_text().strip()
            if t:
                pessoas_textos.append(t)
        distintas = len(set(pessoas_textos))
        log(f"[recon] Pessoas distintas visíveis: {distintas}")
        log(f"[recon] Pessoas (amostra): {list(set(pessoas_textos))[:5]}")

        # Paginação
        pag_text = ""
        for el in page.locator("[class*='pagination'], [class*='Pagination']").all():
            t = el.inner_text().strip()
            if t and len(t) < 200:
                pag_text = t[:200]
                break
        log(f"[recon] Texto paginação: '{pag_text}'")

        # GATE 2 — Líder com liderados
        log("\n[gate] Verificando organograma para Líder com liderados...")
        page.goto(
            f"{BASE_URL}/o/{ORG_ID}/organization_chart",
            wait_until="domcontentloaded",
            timeout=20000,
        )
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(2000)
        tw.snap(page, EVID, "gate_03_organograma")
        org_text = page.locator("body").inner_text()
        log(f"[gate] Organograma URL: {page.url}")
        log(f"[gate] Organograma texto:\n{org_text[:600]}")

        has_lider = (
            "Líder" in org_text
            or "liderado" in org_text.lower()
            or "Gestor" in org_text
            or "Manager" in org_text
        )

        page.goto(
            f"{BASE_URL}/o/{ORG_ID}/users",
            wait_until="domcontentloaded",
            timeout=20000,
        )
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(2000)
        tw.snap(page, EVID, "gate_04_usuarios", full=True)
        users_text = page.locator("body").inner_text()
        log(f"[gate] Usuários texto (primeiros 800):\n{users_text[:800]}")

        ctx.close(); browser.close()

        log("\n=== RESULTADO FINAL DO GATE ===")
        log(f"GATE 1 (feature Admin): OK — admin={email}, rota={rota_ok}")
        log(f"GATE 2 (Líder): {'POSSÍVEL' if has_lider else 'NÃO ENCONTRADO — TC9 BLOQUEADO'}")
        log(f"GATE 3 (massa): {row_count} registros visíveis, {distintas} pessoas distintas")
        if distintas < 2:
            log("  Atenção: <2 pessoas — criar 1-2 registros para qa11tc342588@twygotest.com.")

        return True


if __name__ == "__main__":
    ok = gate()
    sys.exit(0 if ok else 1)
