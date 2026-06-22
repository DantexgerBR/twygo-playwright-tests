"""run_qa11_gate.py — GATE para a suíte QA 1.1 [Registros F2] Listagem 'Meu histórico'.

Valida 3 condições antes de qualquer TC:
1. Feature habilitada (tela 'Meu histórico' renderiza)
2. Perfil correto (visão Aluno, não Admin)
3. Massa de dados (conta registros e distribui por origem/status)

Roda headless (não abre janela).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

SLUG = "registros-f2-qa11"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg)


def login_aluno(page, base_url, email, senha):
    """Login como aluno — sem switch admin."""
    page.goto(f"{base_url}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", email)
    page.wait_for_timeout(500)
    page.fill("#user_password", senha)
    page.wait_for_timeout(500)
    tw.snap(page, EVID, "gate_00_login_preenchido")
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    return page.url


def gate():
    # Carrega credenciais do .env
    base_url = os.environ.get("BASE_URL", "").rstrip("/")
    aluno_email = os.environ.get("ALUNO_EMAIL", "")
    # Tenta ALUNO_PASSWORD primeiro; fallback para ADMIN_PASSWORD se o mesmo usuário
    aluno_senha = os.environ.get("ALUNO_PASSWORD", "")
    admin_senha = os.environ.get("ADMIN_PASSWORD", "")
    org_id = os.environ.get("ORG_ID", "36675")

    if not aluno_email:
        log("BLOQUEIO: ALUNO_EMAIL não definido no .env")
        return False

    log(f"[gate] Aluno email: {aluno_email}")
    log(f"[gate] Aluno senha definida: {'sim' if aluno_senha else 'nao'}")
    log(f"[gate] Admin senha definida: {'sim' if admin_senha else 'nao'}")
    log(f"[gate] BASE_URL: {base_url}")

    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)

        # Tenta com ALUNO_PASSWORD
        log(f"\n[gate] Tentativa 1: usando ALUNO_PASSWORD...")
        url_pos_login = login_aluno(page, base_url, aluno_email, aluno_senha)
        log(f"[gate] URL após login (tentativa 1): {url_pos_login}")
        tw.snap(page, EVID, "gate_01_pos_login_t1")

        if "/users/login" in url_pos_login:
            log("[gate] ALUNO_PASSWORD falhou. Tentando ADMIN_PASSWORD...")
            url_pos_login = login_aluno(page, base_url, aluno_email, admin_senha)
            log(f"[gate] URL após login (tentativa 2): {url_pos_login}")
            tw.snap(page, EVID, "gate_01_pos_login_t2")

            if "/users/login" in url_pos_login:
                log("BLOQUEIO: ambas as senhas falharam — sessão caiu em /users/login.")
                log("Provável motivo: sessão concorrente ativa (usuário logado no browser) ou credenciais incorretas.")
                log("Ação necessária: Dante deve fechar a sessão ativa ou fornecer a senha correta.")
                ctx.close(); browser.close()
                return False

        log(f"[gate] Login bem-sucedido. URL: {url_pos_login}")

        # — Verificar se caiu perfil admin —
        # Twygo redireciona pra /dashboard_students — se tiver botão "Gerenciar" ou toolbar admin, é admin
        # Para aluno puro: fica em /dashboard_students sem toolbar admin
        current_url = page.url
        log(f"[gate] URL atual: {current_url}")

        # Verifica se há indicadores de visão admin
        has_admin_toolbar = page.locator("[data-testid='admin-toolbar'], .admin-toolbar").count() > 0
        # O botão "Gerenciar" na área do aluno indica que pode alternar para admin
        gerenciar_btn = page.get_by_role("link", name="Gerenciar").count() > 0
        log(f"[gate] Botão 'Gerenciar' visível: {gerenciar_btn}")

        # Captura screenshot do estado atual
        tw.snap(page, EVID, "gate_02_dashboard")

        # — Navega para "Meu histórico" —
        log("\n[gate] Tentando navegar para 'Meu histórico'...")

        # Primeiro verifica se há link na sidebar
        sidebar_link = page.get_by_role("link", name="Meu histórico")
        sidebar_link_count = sidebar_link.count()
        log(f"[gate] Links 'Meu histórico' encontrados: {sidebar_link_count}")

        if sidebar_link_count > 0:
            # Tenta o primeiro link visível
            for i in range(sidebar_link_count):
                try:
                    lnk = sidebar_link.nth(i)
                    if lnk.is_visible():
                        href = lnk.get_attribute("href") or ""
                        log(f"[gate] Link {i}: href='{href}'")
                        lnk.click()
                        try:
                            page.wait_for_load_state("networkidle", timeout=15000)
                        except Exception:
                            pass
                        page.wait_for_timeout(2000)
                        log(f"[gate] URL após click no link: {page.url}")
                        break
                except Exception as e:
                    log(f"[gate] Erro ao clicar link {i}: {e}")
        else:
            # Tenta via URL direta (hipóteses de rota)
            rotas = [
                f"{base_url}/o/{org_id}/records",
                f"{base_url}/o/{org_id}/learning_records",
                f"{base_url}/dashboard_students#records",
            ]
            for rota in rotas:
                log(f"[gate] Tentando rota direta: {rota}")
                page.goto(rota, wait_until="domcontentloaded", timeout=20000)
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                page.wait_for_timeout(1500)
                current = page.url
                log(f"[gate] URL resultante: {current}")
                if "/users/login" not in current and "404" not in page.content()[:200]:
                    has_hist = page.get_by_text("Meu histórico").count() > 0
                    if has_hist:
                        log(f"[gate] 'Meu histórico' encontrado via rota: {rota}")
                        break

        tw.dispensar_nps(page)
        tw.snap(page, EVID, "gate_03_meu_historico", full=True)

        if "/users/login" in page.url:
            log("BLOQUEIO: sessão invalidada após navegar.")
            ctx.close(); browser.close()
            return False

        log(f"\n[gate] URL atual: {page.url}")
        log(f"[gate] Título: {page.title()}")

        # Captura todo o texto visível para diagnóstico
        body_text = page.locator("body").inner_text()[:1000]
        log(f"[gate] Trecho do body:\n{body_text[:500]}")

        # — Verifica GATE 1: feature habilitada —
        has_meu_historico = page.get_by_text("Meu histórico", exact=True).count() > 0
        has_hist_heading = page.locator("h1, h2, h3").filter(has_text="Meu histórico").count() > 0
        kpi_emitidos = page.get_by_text("Emitidos").count() > 0
        kpi_expirados = page.get_by_text("Expirados").count() > 0
        kpi_pendentes = page.get_by_text("Pendentes").count() > 0
        kpi_recusados = page.get_by_text("Recusados").count() > 0

        log(f"\n[gate] 'Meu histórico' exact: {has_meu_historico}")
        log(f"[gate] heading Meu histórico: {has_hist_heading}")
        log(f"[gate] KPIs: Emitidos={kpi_emitidos} Expirados={kpi_expirados} Pendentes={kpi_pendentes} Recusados={kpi_recusados}")

        # — Verifica GATE 2: perfil Aluno (não Admin) —
        has_admin_registros = page.get_by_text("Registros de Aprendizagem", exact=True).count() > 0
        # breadcrumb admin seria "Aprendizagem > Registros" (não "Meu histórico")
        has_aprendizagem_breadcrumb = page.locator("text=Aprendizagem").count() > 0 and not has_meu_historico

        log(f"[gate] 'Registros de Aprendizagem' (admin): {has_admin_registros}")
        log(f"[gate] Breadcrumb admin pattern: {has_aprendizagem_breadcrumb}")

        # — Conta registros —
        row_count = page.locator("table tbody tr").count()
        log(f"[gate] Linhas na tabela: {row_count}")

        card_count = 0
        if row_count == 0:
            # Pode estar em modo grid
            card_count = page.locator("[data-testid*='card'], [class*='card-body'], [class*='CardBody']").count()
            log(f"[gate] Cards (grid mode): {card_count}")

        # Distribuição origens
        internos = page.locator("td").filter(has_text="Interno").count()
        externos = page.locator("td").filter(has_text="Externo").count()
        compartilhados = page.locator("td").filter(has_text="Compartilhado").count()
        aprovados = page.locator("td").filter(has_text="Aprovado").count()
        pendentes_rows = page.locator("td").filter(has_text="Pendente").count()
        expirados_rows = page.locator("td").filter(has_text="Expirado").count()
        recusados_rows = page.locator("td").filter(has_text="Recusado").count()

        log(f"[gate] Origens: Interno={internos}, Externo={externos}, Compartilhado={compartilhados}")
        log(f"[gate] Status nas linhas: Aprovado={aprovados}, Pendente={pendentes_rows}, Expirado={expirados_rows}, Recusado={recusados_rows}")

        # — Avalia GATE —
        feature_ok = has_meu_historico or has_hist_heading or (kpi_emitidos and kpi_expirados)

        log("\n=== RESULTADO DO GATE ===")

        if not feature_ok:
            log("GATE 1 FALHOU: Feature 'Meu histórico' NÃO renderizou.")
            log("BLOQUEIO: feature 'Registros de Aprendizagem' não habilitada/visível na org 36675 para o Aluno.")
            log("Ação: Dante deve habilitar a feature flag na org 36675.")
            ctx.close(); browser.close()
            return False

        log("GATE 1 OK: Feature 'Meu histórico' renderizou.")

        if has_admin_registros and not has_meu_historico:
            log("GATE 2 FALHOU: Usuário carregou visão ADMIN ('Registros de Aprendizagem'), não Aluno ('Meu histórico').")
            log("BLOQUEIO: dante.tavares@twygo.com é admin — a suíte Aluno não pode ser executada com este usuário.")
            log("Ação: Dante deve fornecer credenciais de um usuário Aluno sem perfil admin.")
            ctx.close(); browser.close()
            return False

        log("GATE 2 OK: Visão Aluno ('Meu histórico') confirmada.")

        total_registros = row_count + card_count
        log(f"GATE 3 — MASSA: {total_registros} registros visíveis.")
        log(f"  Origens: Interno={internos}, Externo={externos}, Compartilhado={compartilhados}")
        log(f"  Status: Aprovado={aprovados}, Pendente={pendentes_rows}, Expirado={expirados_rows}, Recusado={recusados_rows}")

        if total_registros < 26:
            log(f"  TC11 (paginação) BLOQUEADO: requer >=26 registros; Aluno tem {total_registros}.")
        if total_registros == 0:
            log("  TC3 (empty state) EXECUTÁVEL; maioria dos TCs de dados BLOQUEADOS.")

        ctx.close(); browser.close()
        return True


if __name__ == "__main__":
    ok = gate()
    sys.exit(0 if ok else 1)
