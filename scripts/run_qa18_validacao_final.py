"""
QA 1.8 — Validacao Final Discriminatoria
Card Artia 19895 | 2026-06-24

Pontos criticos a resolver (ordem de prioridade):
  A) Clique real vs Enter: Visualizar em Externo via click() e comparar com Editar no mesmo metodo
  B) Interno Emitido via click() — caminho de codigo diferente (nova aba ?cert=)
  C) Administrador headed — resolver inconsistencia spinner 23/06 vs 24/06
  D) Em andamento (situation=in_progress) — tentar criar/localizar dado via admin
  E) Compartilhado (origin=shared) — verificar se ha dado ou documentar bloqueio

Estrategia:
  1. Abrir kebab, guardar estado antes do clique
  2. Clicar via locator.click() com scroll_into_view_if_needed (garantia de que o click pousa)
  3. Verificar se menu fechou (= click pousou) antes de verificar resultado
  4. Se menu NAO fechou = click nao pousou (falha de interacao, nao de handler)
  5. Repetir com Editar no mesmo metodo como controle
  6. Usar ctx.expect_page() para capturar nova aba (Interno)
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
ADMIN_EMAIL = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
ALUNO_EMAIL = "qa11tc342588@twygotest.com"
ALUNO_PASSWORD = "twygoqa2026"

PASTA = Path(__file__).resolve().parents[1] / "evidencias" / "registros-f2-qa18"
PASTA.mkdir(parents=True, exist_ok=True)

c_admin = {"base_url": BASE_URL, "org_id": ORG_ID, "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}
c_aluno = {"base_url": BASE_URL, "org_id": ORG_ID, "email": ALUNO_EMAIL, "senha": ALUNO_PASSWORD}

results = {}  # chave -> (veredito: str, descricao: str)


def snap(page, nome, full=False):
    fp = PASTA / f"vf_{nome}.png"
    page.screenshot(path=str(fp), full_page=full)
    print(f"   [snap] {fp.name}")
    return fp


def login_aluno(p):
    browser, ctx, page = tw.nova_pagina(p)
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
    page.fill("#user_email", ALUNO_EMAIL)
    page.fill("#user_password", ALUNO_PASSWORD)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=12000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    return browser, ctx, page


def login_admin(p):
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c_admin, admin=True)
    return browser, ctx, page


def aguardar_tabela_admin(page, timeout_s=40):
    """Aguarda tabela admin renderizar. Retorna True se carregou."""
    page.goto(f"{BASE_URL}/o/{ORG_ID}/records",
              wait_until="domcontentloaded", timeout=30000)
    print(f"   Aguardando tabela admin (max {timeout_s}s)...")
    try:
        page.wait_for_function(
            "() => document.querySelectorAll('tbody tr').length > 0",
            timeout=timeout_s * 1000
        )
        page.wait_for_timeout(2000)
        n = page.locator("tbody tr").count()
        print(f"   Tabela admin: {n} linhas")
        return n > 0
    except Exception as e:
        print(f"   Tabela admin nao carregou: {e}")
        return False


def abrir_kebab_linha(page, linha_locator):
    """Abre o kebab da linha e aguarda o menu aparecer. Retorna True se abriu."""
    kebab = linha_locator.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
    if kebab.count() == 0:
        print("   ERRO: kebab nao encontrado na linha")
        return False
    kebab.click()
    page.wait_for_timeout(1200)
    # Verifica se pelo menos 1 menuitem ficou visivel na viewport
    menuitems_visiveis = page.locator("[role='menuitem']:visible").count()
    print(f"   Menuitems visiveis apos click no kebab: {menuitems_visiveis}")
    return menuitems_visiveis > 0


def click_menuitem_real(page, ctx, item_name, snap_prefix):
    """
    Clica num item de menuitem via locator.click() com garantia de que pousou.
    Retorna (click_pousou, nova_aba, url_mudou, descricao)
    """
    url_antes = page.url
    pages_antes = len(ctx.pages)

    # Localizar item pelo role + nome. Filtrar pelo lado direito da viewport (X > 500)
    # para evitar itens de sidebar com o mesmo nome
    items = page.locator(f"[role='menuitem']:visible")
    n = items.count()
    target = None
    for i in range(n):
        it = items.nth(i)
        txt = it.inner_text().strip().lower()
        if item_name.lower() in txt:
            bbox = it.bounding_box()
            if bbox and bbox["x"] > 400:  # exclui sidebar
                target = it
                print(f"   Item '{item_name}' encontrado (x={bbox['x']:.0f}, y={bbox['y']:.0f})")
                break

    if target is None:
        print(f"   Item '{item_name}' NAO encontrado nos {n} menuitems visiveis")
        snap(page, f"{snap_prefix}_sem_item")
        return False, False, False, f"Item '{item_name}' nao encontrado no menu"

    snap(page, f"{snap_prefix}_01_antes_click", full=False)

    # Garantir visibilidade + scroll
    try:
        target.scroll_into_view_if_needed(timeout=3000)
    except Exception:
        pass

    # Clique real com Playwright (move mouse + click)
    target.click(timeout=5000)
    page.wait_for_timeout(3500)

    # Verificar se menu fechou (= click pousou)
    menuitems_pos = page.locator("[role='menuitem']:visible").count()
    menu_fechou = menuitems_pos == 0
    print(f"   Menu fechou apos click: {menu_fechou} (menuitems_pos={menuitems_pos})")

    url_depois = page.url
    pages_depois = len(ctx.pages)
    url_mudou = url_depois != url_antes
    nova_aba = pages_depois > pages_antes

    snap(page, f"{snap_prefix}_02_apos_click", full=True)

    print(f"   URL antes: {url_antes}")
    print(f"   URL depois: {url_depois}")
    print(f"   Nova aba: {nova_aba} (antes={pages_antes}, depois={pages_depois})")
    print(f"   URL mudou: {url_mudou}")

    descricao = (
        f"click_pousou={menu_fechou} | nova_aba={nova_aba} | url_mudou={url_mudou} | "
        f"url_depois={url_depois[:80]}"
    )
    return menu_fechou, nova_aba, url_mudou, descricao


def fechar_menu_se_aberto(page):
    """Fecha menu Chakra se ainda aberto."""
    try:
        if page.locator("[role='menuitem']:visible").count() > 0:
            page.keyboard.press("Escape")
            page.wait_for_timeout(600)
    except Exception:
        pass


def encontrar_linha_por_tipo(page, origem=None, cert_sit=None, situation=None):
    """
    Procura linha na tabela admin por colunas.
    Retorna (index, linha_locator) ou (None, None).
    """
    rows = page.locator("tbody tr")
    n = rows.count()
    for i in range(min(n, 50)):  # max 50 linhas para nao travar
        row = rows.nth(i)
        txt = row.inner_text().lower()
        if origem and origem.lower() not in txt:
            continue
        if cert_sit and cert_sit.lower() not in txt:
            continue
        if situation and situation.lower() not in txt:
            continue
        return i, row
    return None, None


# ============================================================
# PARTE A: CLIQUE REAL vs ENTER — Externo via Aluno e Admin
# ============================================================
def parte_a_clique_real_externo(p):
    print("\n" + "=" * 70)
    print("PARTE A: Clique real no Visualizar (Externo) — Aluno e Admin")
    print("=" * 70)

    # --- A1: Aluno com Externo Emitido ---
    print("\n--- A1: Aluno + Externo Emitido (click real) ---")
    browser_a, ctx_a, page_a = login_aluno(p)
    page_a.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                wait_until="domcontentloaded", timeout=25000)
    page_a.wait_for_timeout(3000)

    rows_a = page_a.locator("tbody tr")
    n_a = rows_a.count()
    print(f"   Aluno: {n_a} linhas na tabela")

    if n_a == 0:
        snap(page_a, "a1_sem_tabela", full=True)
        results["A1_aluno_externo_click"] = ("blocked", "Tabela aluno vazia")
    else:
        snap(page_a, "a1_00_lista_aluno", full=True)

        # Encontrar linha com Externo+Emitido (preferir Emitido, senao qualquer)
        linha_emitido = None
        for i in range(n_a):
            row = rows_a.nth(i)
            txt = row.inner_text().lower()
            if "emitido" in txt:
                linha_emitido = row
                print(f"   Linha {i}: Externo+Emitido encontrado")
                break
        if linha_emitido is None:
            linha_emitido = rows_a.first
            print("   Nenhum Emitido — usando primeira linha")

        # Abrir kebab
        abriu = abrir_kebab_linha(page_a, linha_emitido)
        if not abriu:
            results["A1_aluno_externo_click"] = ("blocked", "Kebab nao abriu")
        else:
            snap(page_a, "a1_01_menu_aberto")

            # --- CLIQUE em Visualizar ---
            click_pousou, nova_aba_v, url_mudou_v, desc_v = click_menuitem_real(
                page_a, ctx_a, "Visualizar", "a1_visualizar"
            )

            if not click_pousou:
                results["A1_aluno_externo_click"] = (
                    "inconclusive",
                    f"Click nao pousou no Visualizar (menu nao fechou). {desc_v}"
                )
            elif nova_aba_v:
                nova = ctx_a.pages[-1]
                nova.wait_for_load_state("domcontentloaded", timeout=15000)
                nova.wait_for_timeout(2000)
                snap(nova, "a1_visualizar_nova_aba", full=True)
                print(f"   A1 VISUALIZAR: nova aba URL={nova.url}")
                tem_cert = "cert" in nova.url.lower() or "certificado" in nova.inner_text("body").lower()
                results["A1_aluno_externo_click"] = (
                    "pass" if tem_cert else "fail",
                    f"Nova aba aberta. URL={nova.url[:80]}. tem_cert={tem_cert}"
                )
                nova.close()
            elif url_mudou_v:
                texto = page_a.inner_text("body")
                tem_viewing = "visualizar registro" in texto.lower()
                tem_disabled = page_a.evaluate(
                    "() => document.querySelectorAll('input:disabled,textarea:disabled,select:disabled').length"
                )
                print(f"   A1 VISUALIZAR: navegou. tem_viewing={tem_viewing}, disabled={tem_disabled}")
                results["A1_aluno_externo_click"] = (
                    "pass" if (tem_viewing or tem_disabled > 0) else "fail",
                    f"Navegou. URL={page_a.url[:80]}. tem_viewing={tem_viewing}, disabled={tem_disabled}"
                )
            else:
                results["A1_aluno_externo_click"] = (
                    "fail",
                    f"Click pousou (menu fechou) mas SEM acao: URL igual, sem nova aba. {desc_v}"
                )

        # Agora Editar como CONTROLE (mesmo metodo de click)
        print("\n   --- A1 CONTROLE: Editar no mesmo aluno (click real) ---")
        page_a.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                    wait_until="domcontentloaded", timeout=25000)
        page_a.wait_for_timeout(3000)
        rows_a2 = page_a.locator("tbody tr")
        if rows_a2.count() > 0:
            abriu2 = abrir_kebab_linha(page_a, rows_a2.first)
            if abriu2:
                snap(page_a, "a1_editar_00_menu_aberto")
                click_pousou_e, nova_aba_e, url_mudou_e, desc_e = click_menuitem_real(
                    page_a, ctx_a, "Editar", "a1_editar"
                )
                if click_pousou_e and url_mudou_e:
                    print(f"   A1 EDITAR: FUNCIONOU. URL={page_a.url}")
                    results["A1_editar_controle"] = ("pass", f"Editar navegou. URL={page_a.url[:80]}")
                elif click_pousou_e:
                    results["A1_editar_controle"] = ("fail", f"Editar click pousou mas URL nao mudou. {desc_e}")
                else:
                    results["A1_editar_controle"] = ("inconclusive", f"Click nao pousou no Editar. {desc_e}")

    browser_a.close()

    # --- A2: Admin + Externo via click real ---
    print("\n--- A2: Admin + Externo (click real) ---")
    browser_adm, ctx_adm, page_adm = login_admin(p)
    carregou = aguardar_tabela_admin(page_adm)

    if not carregou:
        snap(page_adm, "a2_admin_sem_tabela", full=True)
        results["A2_admin_externo_click"] = ("blocked", "Tabela admin nao carregou")
    else:
        snap(page_adm, "a2_00_lista_admin", full=True)

        # Preferir Externo+Emitido
        rows_adm = page_adm.locator("tbody tr")
        linha_adm = None
        for i in range(min(rows_adm.count(), 30)):
            row = rows_adm.nth(i)
            txt = row.inner_text().lower()
            if "externo" in txt and "emitido" in txt:
                linha_adm = row
                print(f"   Admin linha {i}: Externo+Emitido")
                break
        if linha_adm is None:
            # Qualquer linha Externo
            for i in range(min(rows_adm.count(), 30)):
                row = rows_adm.nth(i)
                if "externo" in row.inner_text().lower():
                    linha_adm = row
                    print(f"   Admin linha {i}: Externo (qualquer status)")
                    break
        if linha_adm is None:
            linha_adm = rows_adm.first
            print("   Admin: usando primeira linha")

        abriu_adm = abrir_kebab_linha(page_adm, linha_adm)
        if not abriu_adm:
            results["A2_admin_externo_click"] = ("blocked", "Kebab admin nao abriu")
        else:
            snap(page_adm, "a2_01_menu_aberto")
            click_pousou_adm, nova_aba_adm, url_mudou_adm, desc_adm = click_menuitem_real(
                page_adm, ctx_adm, "Visualizar", "a2_visualizar"
            )
            if not click_pousou_adm:
                results["A2_admin_externo_click"] = (
                    "inconclusive",
                    f"Click nao pousou no admin (menu nao fechou). {desc_adm}"
                )
            elif nova_aba_adm:
                nova = ctx_adm.pages[-1]
                nova.wait_for_load_state("domcontentloaded", timeout=15000)
                snap(nova, "a2_visualizar_nova_aba", full=True)
                results["A2_admin_externo_click"] = ("pass" if "cert" in nova.url else "fail",
                                                     f"Nova aba URL={nova.url[:80]}")
                nova.close()
            elif url_mudou_adm:
                texto = page_adm.inner_text("body")
                tem_viewing = "visualizar registro" in texto.lower()
                tem_disabled = page_adm.evaluate(
                    "() => document.querySelectorAll('input:disabled,textarea:disabled').length"
                )
                results["A2_admin_externo_click"] = (
                    "pass" if (tem_viewing or tem_disabled > 0) else "fail",
                    f"Navegou. tem_viewing={tem_viewing}, disabled={tem_disabled}, URL={page_adm.url[:80]}"
                )
            else:
                results["A2_admin_externo_click"] = (
                    "fail",
                    f"Click pousou (menu fechou) mas SEM acao: URL igual, sem nova aba. {desc_adm}"
                )

        # Controle Editar admin
        print("\n   --- A2 CONTROLE: Editar no admin (click real) ---")
        page_adm.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                      wait_until="domcontentloaded", timeout=30000)
        try:
            page_adm.wait_for_function(
                "() => document.querySelectorAll('tbody tr').length > 0", timeout=20000
            )
            page_adm.wait_for_timeout(1500)
        except Exception:
            pass
        rows_adm2 = page_adm.locator("tbody tr")
        if rows_adm2.count() > 0:
            abriu_e = abrir_kebab_linha(page_adm, rows_adm2.first)
            if abriu_e:
                snap(page_adm, "a2_editar_00_menu_aberto")
                click_pousou_ae, nova_aba_ae, url_mudou_ae, desc_ae = click_menuitem_real(
                    page_adm, ctx_adm, "Editar", "a2_editar"
                )
                if click_pousou_ae and url_mudou_ae:
                    results["A2_editar_controle"] = ("pass", f"Editar admin navegou. URL={page_adm.url[:80]}")
                elif click_pousou_ae:
                    results["A2_editar_controle"] = ("fail", f"Click pousou mas URL nao mudou. {desc_ae}")
                else:
                    results["A2_editar_controle"] = ("inconclusive", f"Click nao pousou no Editar admin. {desc_ae}")

    browser_adm.close()


# ============================================================
# PARTE B: Interno Emitido via click (nova aba ?cert=)
# ============================================================
def parte_b_interno_emitido(p):
    print("\n" + "=" * 70)
    print("PARTE B: Interno Emitido — click em Visualizar (deve abrir nova aba ?cert=)")
    print("=" * 70)

    browser, ctx, page = login_admin(p)
    carregou = aguardar_tabela_admin(page)

    if not carregou:
        snap(page, "b_sem_tabela", full=True)
        results["B_interno_emitido_click"] = ("blocked", "Tabela admin nao carregou")
        browser.close()
        return

    snap(page, "b_00_lista_admin", full=True)

    # Encontrar Interno+Emitido
    rows = page.locator("tbody tr")
    n = rows.count()
    linha_interno = None
    for i in range(min(n, 50)):
        row = rows.nth(i)
        txt = row.inner_text().lower()
        if "interno" in txt and "emitido" in txt:
            linha_interno = row
            print(f"   Linha {i}: Interno+Emitido encontrado")
            break

    if linha_interno is None:
        print("   Interno+Emitido nao encontrado nas primeiras 50 linhas — tentando via API")
        # Buscar via API para encontrar ID de um registro Interno+Emitido
        resp = page.request.get(
            f"{BASE_URL}/api/v1/o/{ORG_ID}/records?order_type=desc&per_page=50&page=1&order_by=created_at",
            headers={"Accept": "application/json"}
        )
        if resp.status == 200:
            data = resp.json()
            recs = data.get("data", {}).get("records", [])
            interno_emitido = [r for r in recs if r.get("origin") == "internal" and
                               r.get("certificate_situation") == "emitted"]
            print(f"   Via API (pagina 1): {len(interno_emitido)} Interno+Emitido")
            if not interno_emitido:
                # Tentar mais paginas
                for pg in range(2, 8):
                    resp2 = page.request.get(
                        f"{BASE_URL}/api/v1/o/{ORG_ID}/records?order_type=desc&per_page=50&page={pg}&order_by=created_at",
                        headers={"Accept": "application/json"}
                    )
                    if resp2.status == 200:
                        d2 = resp2.json()
                        r2 = d2.get("data", {}).get("records", [])
                        interno_emitido.extend([r for r in r2 if r.get("origin") == "internal" and
                                                r.get("certificate_situation") == "emitted"])
                        if len(interno_emitido) > 0:
                            break
                        if not d2.get("data", {}).get("pagination", {}).get("next_page"):
                            break

            if interno_emitido:
                rec = interno_emitido[0]
                rec_id = rec.get("id")
                cert_token = rec.get("certificate_token", "")
                print(f"   Registro Interno+Emitido via API: id={rec_id}, token={str(cert_token)[:20]}, user={rec.get('user_email')}")

                # Acessar tela standalone diretamente com o token
                if cert_token:
                    url_standalone = f"{BASE_URL}/certificates/{cert_token}"
                    print(f"   Tentando acessar standalone direto: {url_standalone}")
                    page.goto(url_standalone, wait_until="domcontentloaded", timeout=20000)
                    page.wait_for_timeout(2000)
                    snap(page, "b_standalone_direto", full=True)
                    url_atual = page.url
                    texto = page.inner_text("body")
                    tem_cert = "certificado" in texto.lower() or "certificate" in texto.lower() or "cert" in url_atual.lower()
                    print(f"   Standalone direto: URL={url_atual}, tem_cert={tem_cert}")
                    if tem_cert:
                        results["B_interno_emitido_standalone_direto"] = (
                            "pass", f"Standalone acessivel via URL direta. URL={url_atual[:80]}"
                        )
                    else:
                        results["B_interno_emitido_standalone_direto"] = (
                            "fail", f"URL acessada mas sem conteudo de certificado. URL={url_atual}"
                        )

                    # Agora tentar via kebab na tabela — precisamos filtrar por Interno na UI
                    # Usar filtro da tabela admin
                    page.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                              wait_until="domcontentloaded", timeout=30000)
                    try:
                        page.wait_for_function(
                            "() => document.querySelectorAll('tbody tr').length > 0", timeout=30000
                        )
                        page.wait_for_timeout(2000)
                    except Exception:
                        pass

                    # Filtrar por Interno na UI (botao Filtro)
                    print("   Tentando filtrar por Origem=Interno na UI...")
                    filtro_btn = page.locator("button:has-text('Filtro'), [aria-label*='filtro'], [aria-label*='Filtro']").first
                    if filtro_btn.count() > 0:
                        filtro_btn.click()
                        page.wait_for_timeout(1500)
                        snap(page, "b_filtro_aberto")
                        # Tentar selecionar Interno
                        interno_opt = page.get_by_text("Interno", exact=True).first
                        if interno_opt.count() > 0:
                            interno_opt.click()
                            page.wait_for_timeout(2000)
                            snap(page, "b_filtro_interno", full=True)
                            rows_int = page.locator("tbody tr")
                            n_int = rows_int.count()
                            print(f"   Apos filtro Interno: {n_int} linhas")
                            if n_int > 0:
                                linha_interno = rows_int.first
                                print(f"   Primeira linha filtrada: {rows_int.first.inner_text()[:80]}")
                        else:
                            print("   Opcao 'Interno' nao encontrada no filtro")
                            page.keyboard.press("Escape")

                results["B_interno_emitido_click"] = (
                    "blocked",
                    f"Linha nao encontrada na tabela da UI (primeiras 50 linhas sao Externo). "
                    f"Dado existe via API (id={rec_id}). Standalone direto testado separadamente."
                ) if linha_interno is None else results.get("B_interno_emitido_click", ("pending", ""))
            else:
                print("   Nenhum Interno+Emitido encontrado via API")
                results["B_interno_emitido_click"] = ("blocked", "Nenhum Interno+Emitido encontrado via API")
        else:
            results["B_interno_emitido_click"] = ("blocked", f"API retornou {resp.status}")

    if linha_interno is not None:
        # Temos linha — abrir kebab e clicar Visualizar
        abriu = abrir_kebab_linha(page, linha_interno)
        if not abriu:
            results["B_interno_emitido_click"] = ("blocked", "Kebab nao abriu na linha Interno")
        else:
            snap(page, "b_01_menu_interno_aberto")
            print("   Aguardando nova aba ao clicar Visualizar em Interno (usa ctx.expect_page)...")
            try:
                with ctx.expect_page(timeout=8000) as pg_info:
                    click_pousou_b, _, _, desc_b = click_menuitem_real(
                        page, ctx, "Visualizar", "b_visualizar"
                    )
                nova_pagina_obj = pg_info.value
                nova_pagina_obj.wait_for_load_state("domcontentloaded", timeout=15000)
                nova_pagina_obj.wait_for_timeout(2000)
                snap(nova_pagina_obj, "b_nova_aba_standalone", full=True)
                url_nova = nova_pagina_obj.url
                texto_nova = nova_pagina_obj.inner_text("body")
                tem_cert = "cert" in url_nova.lower() or "certificado" in texto_nova.lower()
                tem_token_valido = any(kw in texto_nova.lower() for kw in ["certificado valido", "certificado válido", "token", "validacao"])
                print(f"   B INTERNO: nova aba URL={url_nova}, tem_cert={tem_cert}")
                results["B_interno_emitido_click"] = (
                    "pass" if tem_cert else "fail",
                    f"Visualizar Interno abriu nova aba. URL={url_nova[:80]}. tem_cert={tem_cert}, click_pousou={click_pousou_b}"
                )
                nova_pagina_obj.close()
            except Exception as e:
                # Nova aba nao abriu — verificar se navegou na mesma aba
                url_pos = page.url
                print(f"   B INTERNO: sem nova aba. Exception={str(e)[:100]}. URL pos={url_pos}")
                snap(page, "b_sem_nova_aba", full=True)
                if page.url != f"{BASE_URL}/o/{ORG_ID}/records":
                    texto = page.inner_text("body")
                    results["B_interno_emitido_click"] = (
                        "fail",
                        f"Interno Visualizar nao abriu nova aba, navegou para {url_pos[:80]}"
                    )
                else:
                    results["B_interno_emitido_click"] = (
                        "fail",
                        f"Interno Visualizar nao abriu nova aba e URL nao mudou. {desc_b if 'desc_b' in dir() else str(e)[:80]}"
                    )

    browser.close()


# ============================================================
# PARTE C: Headed — resolver spinner vs lista (admin)
# ============================================================
def parte_c_headed(p):
    print("\n" + "=" * 70)
    print("PARTE C: Admin headed (TW_HEADED=1 forcado) — resolver inconsistencia spinner")
    print("=" * 70)

    # Forcando headed independentemente do env
    browser_h = p.chromium.launch(headless=False, slow_mo=400)
    ctx_h = browser_h.new_context(viewport={"width": 1500, "height": 950}, locale="pt-BR")
    page_h = ctx_h.new_page()

    # Login admin
    page_h.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
    page_h.fill("#user_email", ADMIN_EMAIL)
    page_h.fill("#user_password", ADMIN_PASSWORD)
    page_h.click("#user_submit")
    try:
        page_h.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page_h.wait_for_timeout(2000)
    page_h.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                wait_until="domcontentloaded", timeout=30000)
    print("   Aguardando tabela headed (max 40s)...")
    try:
        page_h.wait_for_function(
            "() => document.querySelectorAll('tbody tr').length > 0", timeout=40000
        )
        page_h.wait_for_timeout(2500)
        n_h = page_h.locator("tbody tr").count()
        print(f"   Tabela headed: {n_h} linhas")
        snap(page_h, "c_00_lista_headed", full=True)

        # Abrir kebab e clicar Visualizar no modo headed
        rows_h = page_h.locator("tbody tr")
        abriu_h = abrir_kebab_linha(page_h, rows_h.first)
        if abriu_h:
            snap(page_h, "c_01_menu_aberto")
            click_pousou_h, nova_aba_h, url_mudou_h, desc_h = click_menuitem_real(
                page_h, ctx_h, "Visualizar", "c_visualizar"
            )
            page_h.wait_for_timeout(2000)  # wait extra pos-click headed

            if nova_aba_h:
                nova = ctx_h.pages[-1]
                nova.wait_for_load_state("domcontentloaded", timeout=12000)
                snap(nova, "c_nova_aba", full=True)
                results["C_headed_admin_visualizar"] = (
                    "pass" if "cert" in nova.url else "fail",
                    f"Headed: nova aba aberta. URL={nova.url[:80]}"
                )
                nova.close()
            elif url_mudou_h:
                texto = page_h.inner_text("body")
                tem_viewing = "visualizar registro" in texto.lower()
                results["C_headed_admin_visualizar"] = (
                    "pass" if tem_viewing else "fail",
                    f"Headed: navegou. tem_viewing={tem_viewing}. URL={page_h.url[:80]}"
                )
            elif click_pousou_h:
                # Click pousou mas sem acao — bug confirmado em headed tambem
                url_pos = page_h.url
                texto = page_h.inner_text("body")
                tem_spinner = page_h.locator("[role='status'], .chakra-spinner, [class*='spinner']").count() > 0
                print(f"   Headed: click pousou, sem acao. URL={url_pos}, spinner={tem_spinner}")
                snap(page_h, "c_pos_click_detalhe", full=True)
                results["C_headed_admin_visualizar"] = (
                    "fail",
                    f"Headed CONFIRMA BUG: click pousou mas SEM acao (URL={url_pos[:60]}, spinner={tem_spinner})"
                )
            else:
                results["C_headed_admin_visualizar"] = (
                    "inconclusive",
                    f"Headed: click nao pousou. {desc_h}"
                )
    except Exception as e:
        snap(page_h, "c_erro_tabela", full=True)
        results["C_headed_admin_visualizar"] = (
            "blocked",
            f"Tabela headed nao carregou em 40s: {str(e)[:100]}"
        )

    ctx_h.close()
    browser_h.close()


# ============================================================
# PARTE D: Dados — Em andamento, Compartilhado, Interno via UI
# ============================================================
def parte_d_dados_e_cobertura(p):
    print("\n" + "=" * 70)
    print("PARTE D: Verificar/criar dados — Em andamento, Compartilhado")
    print("=" * 70)

    browser, ctx, page = login_admin(p)

    # --- D1: Em andamento (situation=in_progress) via API paginada ---
    print("\n   --- D1: Buscar Em andamento (situation=in_progress) via API ---")
    em_andamento = []
    for pg in range(1, 16):
        resp = page.request.get(
            f"{BASE_URL}/api/v1/o/{ORG_ID}/records?order_type=desc&per_page=50&page={pg}&order_by=created_at",
            headers={"Accept": "application/json"}
        )
        if resp.status != 200:
            break
        data = resp.json()
        recs = data.get("data", {}).get("records", [])
        em_andamento.extend([r for r in recs if r.get("situation") == "in_progress"])
        if not data.get("data", {}).get("pagination", {}).get("next_page"):
            break

    print(f"   Em andamento encontrados: {len(em_andamento)}")
    for r in em_andamento[:3]:
        print(f"   - id={r.get('id')} email={r.get('user_email')} origin={r.get('origin')} cert_sit={r.get('certificate_situation')}")

    if em_andamento:
        # Ha dados — testar TC1 linha "Em andamento" via admin
        rec_em = em_andamento[0]
        rec_id_em = rec_em.get("id")
        print(f"   Encontrado Em andamento: id={rec_id_em}. Buscando na tabela admin...")
        carregou = aguardar_tabela_admin(page)
        if carregou:
            # Buscar linha na tabela pelo email do usuario
            rows = page.locator("tbody tr")
            email_em = rec_em.get("user_email", "")
            linha_em = None
            for i in range(min(rows.count(), 50)):
                row = rows.nth(i)
                txt = row.inner_text()
                if email_em[:10] in txt or str(rec_id_em) in txt:
                    linha_em = row
                    print(f"   Linha {i}: registro Em andamento encontrado na UI")
                    break
            if linha_em:
                abriu_em = abrir_kebab_linha(page, linha_em)
                if abriu_em:
                    snap(page, "d1_menu_em_andamento")
                    # Verificar estado do item Visualizar
                    items = page.locator("[role='menuitem']:visible")
                    for i in range(items.count()):
                        it = items.nth(i)
                        txt_it = it.inner_text().lower()
                        if "visualizar" in txt_it:
                            is_disabled = it.get_attribute("aria-disabled") == "true" or \
                                          it.get_attribute("data-disabled") is not None
                            bbox = it.bounding_box()
                            if bbox and bbox["x"] > 400:
                                print(f"   Visualizar no Em andamento: aria-disabled={it.get_attribute('aria-disabled')}, data-disabled={it.get_attribute('data-disabled')}")
                                # Verificar tooltip
                                it.hover()
                                page.wait_for_timeout(800)
                                snap(page, "d1_tooltip_em_andamento")
                                tooltip_text = page.locator("[role='tooltip']:visible").first.inner_text() if page.locator("[role='tooltip']:visible").count() > 0 else ""
                                print(f"   Tooltip: '{tooltip_text}'")
                                results["D1_em_andamento_disabled"] = (
                                    "pass" if is_disabled and "conclus" in tooltip_text.lower() else "fail",
                                    f"Visualizar disabled={is_disabled}, tooltip='{tooltip_text}'"
                                )
                                break
                    fechar_menu_se_aberto(page)
            else:
                print(f"   Linha Em andamento nao encontrada na UI (email={email_em[:20]})")
                results["D1_em_andamento_disabled"] = (
                    "blocked",
                    f"Dado existe via API (id={rec_id_em}) mas linha nao localizada na UI da tabela admin"
                )
        else:
            results["D1_em_andamento_disabled"] = ("blocked", "Tabela admin nao carregou")
    else:
        print("   NENHUM Em andamento na stage inteira")
        # Tentar criar um: precisaria de registro Interno com enrollment in_progress
        # Isso requer criar enrollment de um conteudo — documentar bloqueio
        results["D1_em_andamento_disabled"] = (
            "blocked",
            "0 registros situation=in_progress em toda a stage. "
            "Para criar: precisaria adicionar registro interno de um conteudo com progresso < 100%. "
            "Fluxo: Conteudos -> selecionar conteudo -> aprovar aluno -> aluno nao completa 100%. "
            "Nao foi possivel criar automaticamente sem conhecer qual conteudo aceita registros internos."
        )

    # --- D2: Compartilhado (origin=shared) ---
    print("\n   --- D2: Buscar Compartilhado (origin=shared) via API ---")
    compartilhado = []
    for pg in range(1, 16):
        resp = page.request.get(
            f"{BASE_URL}/api/v1/o/{ORG_ID}/records?order_type=desc&per_page=50&page={pg}&order_by=created_at",
            headers={"Accept": "application/json"}
        )
        if resp.status != 200:
            break
        data = resp.json()
        recs = data.get("data", {}).get("records", [])
        compartilhado.extend([r for r in recs if r.get("origin") == "shared"])
        if not data.get("data", {}).get("pagination", {}).get("next_page"):
            break

    print(f"   Compartilhados encontrados: {len(compartilhado)}")
    for r in compartilhado[:3]:
        print(f"   - id={r.get('id')} email={r.get('user_email')} cert_sit={r.get('certificate_situation')} token={str(r.get('certificate_token',''))[:20]}")

    if compartilhado:
        rec_comp = next((r for r in compartilhado if r.get("certificate_situation") == "emitted"), compartilhado[0])
        token_comp = rec_comp.get("certificate_token", "")
        print(f"   Compartilhado Emitido: id={rec_comp.get('id')}, token={str(token_comp)[:20]}")
        if token_comp:
            url_standalone = f"{BASE_URL}/certificates/{token_comp}"
            page.goto(url_standalone, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2000)
            snap(page, "d2_compartilhado_standalone", full=True)
            texto = page.inner_text("body")
            tem_cert = "certificado" in texto.lower() or "cert" in page.url.lower()
            results["D2_compartilhado_standalone"] = (
                "pass" if tem_cert else "fail",
                f"Compartilhado standalone via URL direta. URL={page.url[:80]}, tem_cert={tem_cert}"
            )
        else:
            results["D2_compartilhado_standalone"] = ("blocked", "Compartilhado encontrado mas sem token")
        # Tentar via kebab admin (mesmo raciocinio do Interno)
        results["D2_compartilhado_kebab"] = (
            "blocked",
            f"Dado existe (id={rec_comp.get('id')}) mas testar via kebab requer localizar na tabela admin. "
            "Bug P1 (click nao age) torna teste do kebab indireto — standalone direto testado acima."
        )
    else:
        print("   NENHUM Compartilhado na stage")
        # Documentar como criar
        results["D2_compartilhado_standalone"] = (
            "blocked",
            "0 registros origin=shared em toda a stage. "
            "Para criar: conteudo com opcao de compartilhamento habilitada precisa ser completado por aluno. "
            "Nao foi possivel criar automaticamente — requer config de conteudo especifica."
        )

    # --- D3: Interno Emitido via API (complemento da Parte B) ---
    print("\n   --- D3: Contagem de Interno Emitido via API ---")
    interno_emitido = []
    for pg in range(1, 10):
        resp = page.request.get(
            f"{BASE_URL}/api/v1/o/{ORG_ID}/records?order_type=desc&per_page=50&page={pg}&order_by=created_at",
            headers={"Accept": "application/json"}
        )
        if resp.status != 200:
            break
        data = resp.json()
        recs = data.get("data", {}).get("records", [])
        interno_emitido.extend([r for r in recs if r.get("origin") == "internal" and
                                 r.get("certificate_situation") == "emitted"])
        if not data.get("data", {}).get("pagination", {}).get("next_page"):
            break
        if len(interno_emitido) >= 5:
            break

    print(f"   Interno+Emitido encontrados: {len(interno_emitido)}")
    for r in interno_emitido[:3]:
        print(f"   - id={r.get('id')} email={r.get('user_email')} token={str(r.get('certificate_token',''))[:20]}")

    if interno_emitido:
        rec_int = interno_emitido[0]
        token_int = rec_int.get("certificate_token", "")
        if token_int:
            url_int = f"{BASE_URL}/certificates/{token_int}"
            page.goto(url_int, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2000)
            snap(page, "d3_interno_standalone_direto", full=True)
            texto = page.inner_text("body")
            tem_cert = "certificado" in texto.lower() or "cert" in page.url.lower()
            results["D3_interno_standalone_url"] = (
                "pass" if tem_cert else "fail",
                f"Interno standalone via URL direta. URL={page.url[:80]}, tem_cert={tem_cert}"
            )

    browser.close()


# ============================================================
# MAIN
# ============================================================
def main():
    print("=== QA 1.8 — Validacao Final Discriminatoria (2026-06-24) ===")
    print(f"Pasta evidencias: {PASTA}")

    with tw.sync_playwright() as p:
        parte_a_clique_real_externo(p)
        parte_b_interno_emitido(p)
        parte_c_headed(p)
        parte_d_dados_e_cobertura(p)

    # --- Sumario ---
    print("\n\n" + "=" * 70)
    print("SUMARIO FINAL")
    print("=" * 70)
    for chave, (veredito, desc) in results.items():
        label = {"pass": "PASSOU", "fail": "FALHOU", "blocked": "BLOQUEADO", "inconclusive": "INCONCLUS", "pending": "PENDENTE"}.get(veredito, veredito.upper())
        print(f"   [{label}] {chave}: {desc[:120]}")

    return results


if __name__ == "__main__":
    main()
