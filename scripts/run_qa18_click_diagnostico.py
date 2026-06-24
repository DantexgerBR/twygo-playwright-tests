"""
QA 1.8 — Diagnostico de clique no item Visualizar
Card 19895 | 2026-06-24

O click() padrao nao fecha o menu. Vamos investigar:
1. Inspecionar o DOM de Visualizar vs Editar (o que e diferente?)
2. Usar dispatch_event('click') no button-menuitem (bypassa hit-test)
3. Verificar se ha overlay/tooltip bloqueando
4. Confirmar se o handler React dispara ou nao com dispatch

Objetivo: separar "o Playwright nao consegue pousar o click por sobreposicao"
de "o handler React do Visualizar nao esta implementado"
"""
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

results = {}


def snap(page, nome, full=False):
    fp = PASTA / f"diag_{nome}.png"
    page.screenshot(path=str(fp), full_page=full)
    print(f"   [snap] {fp.name}")
    return fp


def inspecionar_menuitem(page, item_name):
    """Retorna informacoes do DOM do item especificado."""
    info = page.evaluate(f"""() => {{
        const allItems = Array.from(document.querySelectorAll('[role="menuitem"]'));
        const filtered = allItems.filter(el => {{
            const txt = el.innerText.toLowerCase();
            return txt.includes('{item_name.lower()}');
        }});
        // Pegar o que esta na viewport direita (x > 400)
        const visible = filtered.filter(el => {{
            const r = el.getBoundingClientRect();
            return r.x > 400 && r.width > 0 && r.height > 0;
        }});
        if (visible.length === 0) return null;
        const el = visible[0];
        const rect = el.getBoundingClientRect();
        // Verificar elemento no centro do item
        const cx = rect.x + rect.width / 2;
        const cy = rect.y + rect.height / 2;
        const elementAtCenter = document.elementFromPoint(cx, cy);
        return {{
            tagName: el.tagName,
            role: el.getAttribute('role'),
            ariaDisabled: el.getAttribute('aria-disabled'),
            dataDisabled: el.getAttribute('data-disabled'),
            dataTestId: el.getAttribute('data-test-id'),
            id: el.id,
            className: el.className.substring(0, 80),
            rect: {{ x: rect.x, y: rect.y, width: rect.width, height: rect.height }},
            innerText: el.innerText.trim().substring(0, 50),
            outerHTML: el.outerHTML.substring(0, 300),
            elementAtCenter: elementAtCenter ? {{
                tagName: elementAtCenter.tagName,
                id: elementAtCenter.id,
                className: elementAtCenter.className.substring(0, 80),
                role: elementAtCenter.getAttribute('role'),
                dataTestId: elementAtCenter.getAttribute('data-test-id'),
                innerText: elementAtCenter.innerText.trim().substring(0, 50)
            }} : null
        }};
    }}""")
    return info


def dispatch_click_e_verificar(page, ctx, item_name, snap_prefix):
    """
    Faz dispatch_event('click') direto no button do item.
    Isso bypassa o hit-test do Playwright e dispara diretamente no elemento.
    Se o handler React existir, ele sera chamado.
    """
    url_antes = page.url
    pages_antes = len(ctx.pages)

    # Encontrar o button[role='menuitem'] correto via JavaScript
    resultado = page.evaluate(f"""() => {{
        const allItems = Array.from(document.querySelectorAll('[role="menuitem"]'));
        const visible = allItems.filter(el => {{
            const txt = el.innerText.toLowerCase();
            const r = el.getBoundingClientRect();
            return txt.includes('{item_name.lower()}') && r.x > 400 && r.width > 0;
        }});
        if (visible.length === 0) return {{ found: false }};
        const el = visible[0];
        return {{
            found: true,
            text: el.innerText.trim(),
            id: el.id,
            dataTestId: el.getAttribute('data-test-id') || el.querySelector('[data-test-id]')?.getAttribute('data-test-id') || ''
        }};
    }}""")

    print(f"   dispatch: item '{item_name}' found={resultado.get('found')}, id={resultado.get('id')}, data-test-id={resultado.get('dataTestId')}")

    if not resultado.get("found"):
        snap(page, f"{snap_prefix}_sem_item")
        return False, "Item nao encontrado via dispatch"

    snap(page, f"{snap_prefix}_01_antes_dispatch")

    # Dispatch click no elemento
    page.evaluate(f"""() => {{
        const allItems = Array.from(document.querySelectorAll('[role="menuitem"]'));
        const visible = allItems.filter(el => {{
            const txt = el.innerText.toLowerCase();
            const r = el.getBoundingClientRect();
            return txt.includes('{item_name.lower()}') && r.x > 400 && r.width > 0;
        }});
        if (visible.length > 0) {{
            visible[0].dispatchEvent(new MouseEvent('click', {{
                bubbles: true, cancelable: true, view: window
            }}));
        }}
    }}""")

    page.wait_for_timeout(3500)
    url_depois = page.url
    pages_depois = len(ctx.pages)
    nova_aba = pages_depois > pages_antes
    url_mudou = url_depois != url_antes
    menu_fechou = page.locator("[role='menuitem']:visible").count() == 0

    print(f"   dispatch resultado: menu_fechou={menu_fechou}, nova_aba={nova_aba}, url_mudou={url_mudou}")
    print(f"   URL depois: {url_depois[:80]}")

    snap(page, f"{snap_prefix}_02_apos_dispatch", full=True)
    return True, f"dispatch_click: menu_fechou={menu_fechou}, nova_aba={nova_aba}, url_mudou={url_mudou}, url={url_depois[:80]}"


def main():
    print("=== QA 1.8 — Diagnostico de click (dispatch vs locator) ===")

    with tw.sync_playwright() as p:
        # --- SESSAO ALUNO ---
        print("\n=== ALUNO: inspecao DOM + dispatch click ===")
        browser_a, ctx_a, page_a = tw.nova_pagina(p)
        page_a.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        page_a.fill("#user_email", ALUNO_EMAIL)
        page_a.fill("#user_password", ALUNO_PASSWORD)
        page_a.click("#user_submit")
        try:
            page_a.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        page_a.wait_for_timeout(2000)
        tw.dispensar_nps(page_a)
        page_a.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                    wait_until="domcontentloaded", timeout=25000)
        page_a.wait_for_timeout(3000)

        rows_a = page_a.locator("tbody tr")
        n_a = rows_a.count()
        print(f"   Linhas aluno: {n_a}")

        if n_a > 0:
            # Preferir linha Externo+Emitido
            linha_aluno = None
            for i in range(n_a):
                row = rows_a.nth(i)
                txt = row.inner_text().lower()
                if "emitido" in txt:
                    linha_aluno = row
                    break
            if linha_aluno is None:
                linha_aluno = rows_a.first

            # Abrir kebab
            kebab_a = linha_aluno.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
            kebab_a.click()
            page_a.wait_for_timeout(1200)
            snap(page_a, "aluno_00_menu_aberto")

            # Inspecionar DOM do Visualizar
            info_vis = inspecionar_menuitem(page_a, "Visualizar")
            info_edit = inspecionar_menuitem(page_a, "Editar")
            print(f"\n   DOM Editar: {info_edit}")
            print(f"\n   DOM Visualizar: {info_vis}")

            if info_vis:
                el_at_center = info_vis.get("elementAtCenter", {}) or {}
                print(f"\n   ELEMENTO NO CENTRO do Visualizar: tag={el_at_center.get('tagName')}, "
                      f"role={el_at_center.get('role')}, id={el_at_center.get('id')}, "
                      f"text='{el_at_center.get('innerText', '')}'")
                print(f"   dataTestId no centro: {el_at_center.get('dataTestId')}")

                # Se o elemento no centro NAO for o menuitem (ex: tooltip overlay), identificar
                vis_is_menuitem = el_at_center.get("role") == "menuitem" or "menuitem" in (el_at_center.get("className", "") or "")
                print(f"   O elemento no centro do Visualizar e o menuitem? {vis_is_menuitem}")

                if info_edit:
                    el_at_center_e = info_edit.get("elementAtCenter", {}) or {}
                    edit_is_menuitem = el_at_center_e.get("role") == "menuitem" or "menuitem" in (el_at_center_e.get("className", "") or "")
                    print(f"   O elemento no centro do Editar e o menuitem? {edit_is_menuitem}")

            # Dispatch click no Visualizar
            print("\n   --- TESTE 1: dispatch_event('click') no Visualizar ---")
            found_d, desc_d = dispatch_click_e_verificar(page_a, ctx_a, "Visualizar", "aluno_disp_vis")
            results["dispatch_Visualizar_aluno"] = (found_d, desc_d)
            print(f"   Resultado dispatch Visualizar: {desc_d}")

            # Se menu ainda aberto, fechar e reabrir para testar Editar
            page_a.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                        wait_until="domcontentloaded", timeout=25000)
            page_a.wait_for_timeout(2000)

            # Agora dispatch no Editar como controle
            print("\n   --- TESTE 2: dispatch_event('click') no Editar (controle) ---")
            rows_a2 = page_a.locator("tbody tr")
            if rows_a2.count() > 0:
                linha_aluno2 = None
                for i in range(rows_a2.count()):
                    row = rows_a2.nth(i)
                    if "emitido" in row.inner_text().lower():
                        linha_aluno2 = row
                        break
                if linha_aluno2 is None:
                    linha_aluno2 = rows_a2.first
                kebab_a2 = linha_aluno2.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
                kebab_a2.click()
                page_a.wait_for_timeout(1200)
                snap(page_a, "aluno_editar_00_menu")
                found_de, desc_de = dispatch_click_e_verificar(page_a, ctx_a, "Editar", "aluno_disp_edit")
                results["dispatch_Editar_aluno"] = (found_de, desc_de)
                print(f"   Resultado dispatch Editar: {desc_de}")

        browser_a.close()

        # --- SESSAO ADMIN ---
        print("\n=== ADMIN: dispatch click em Visualizar + inspecao DOM ===")
        browser_adm, ctx_adm, page_adm = tw.nova_pagina(p)
        tw.login(page_adm, c_admin, admin=True)
        page_adm.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                      wait_until="domcontentloaded", timeout=30000)
        try:
            page_adm.wait_for_function(
                "() => document.querySelectorAll('tbody tr').length > 0", timeout=35000
            )
            page_adm.wait_for_timeout(2000)
        except Exception as e:
            print(f"   Tabela admin nao carregou: {e}")
            browser_adm.close()
        else:
            rows_adm = page_adm.locator("tbody tr")
            n_adm = rows_adm.count()
            print(f"   Linhas admin: {n_adm}")

            # Encontrar linha com Externo para testar o form viewing
            linha_adm_ext = None
            for i in range(min(n_adm, 30)):
                row = rows_adm.nth(i)
                txt = row.inner_text().lower()
                if "externo" in txt:
                    linha_adm_ext = row
                    print(f"   Admin linha {i}: Externo encontrado")
                    break
            if linha_adm_ext is None:
                linha_adm_ext = rows_adm.first
                print("   Admin: usando primeira linha")

            # Abrir kebab
            kebab_adm = linha_adm_ext.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
            if kebab_adm.count() > 0:
                kebab_adm.click()
                page_adm.wait_for_timeout(1200)
                snap(page_adm, "admin_00_menu_aberto")

                # Inspecionar DOM
                info_vis_adm = inspecionar_menuitem(page_adm, "Visualizar")
                info_edit_adm = inspecionar_menuitem(page_adm, "Editar")
                print(f"\n   DOM Editar admin: {info_edit_adm}")
                print(f"\n   DOM Visualizar admin: {info_vis_adm}")

                if info_vis_adm:
                    el_adm = info_vis_adm.get("elementAtCenter", {}) or {}
                    print(f"\n   ELEMENTO NO CENTRO Visualizar admin: tag={el_adm.get('tagName')}, "
                          f"role={el_adm.get('role')}, text='{el_adm.get('innerText', '')}'")

                # Dispatch click Visualizar no admin (Externo)
                print("\n   --- ADMIN TESTE 1: dispatch Visualizar em Externo ---")
                found_adm, desc_adm = dispatch_click_e_verificar(page_adm, ctx_adm, "Visualizar", "admin_disp_ext_vis")
                results["dispatch_Visualizar_admin_externo"] = (found_adm, desc_adm)
                print(f"   Resultado: {desc_adm}")
            else:
                print("   Kebab admin nao encontrado na linha")
                results["dispatch_Visualizar_admin_externo"] = (False, "Kebab nao encontrado")

            # Agora testar em linha Interno (se disponivel na tabela)
            print("\n   --- ADMIN TESTE 2: Interno+Emitido (scroll ou filtro) ---")
            page_adm.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                          wait_until="domcontentloaded", timeout=30000)
            try:
                page_adm.wait_for_function(
                    "() => document.querySelectorAll('tbody tr').length > 0", timeout=25000
                )
                page_adm.wait_for_timeout(2000)
            except Exception:
                pass

            # Iterar ate 25 linhas para achar Interno
            rows_adm2 = page_adm.locator("tbody tr")
            linha_adm_int = None
            for i in range(min(rows_adm2.count(), 25)):
                row = rows_adm2.nth(i)
                txt = row.inner_text().lower()
                if "interno" in txt and "emitido" in txt:
                    linha_adm_int = row
                    print(f"   Admin linha {i}: Interno+Emitido na tabela UI")
                    break
            if linha_adm_int is None:
                print("   Interno+Emitido nao visivel na primeira pagina da tabela admin")
                # Tentar acessar diretamente por ID via API
                resp = page_adm.request.get(
                    f"{BASE_URL}/api/v1/o/{ORG_ID}/records?order_type=desc&per_page=50&page=1&origin=internal&certificate_situation=emitted",
                    headers={"Accept": "application/json"}
                )
                print(f"   API filtro interno+emitted: status={resp.status}")
                if resp.status == 200:
                    recs = resp.json().get("data", {}).get("records", [])
                    print(f"   Registros via API filtro: {len(recs)}")
                    if recs:
                        rec_int = recs[0]
                        rec_id_int = rec_int.get("id")
                        token_int = rec_int.get("certificate_token", "")
                        print(f"   Primeiro Interno+Emitido: id={rec_id_int}, token={str(token_int)[:20]}, user={rec_int.get('user_email')}")
                        results["admin_interno_emitido_api"] = (True, f"id={rec_id_int}, token={'presente' if token_int else 'AUSENTE'}")

                        if token_int:
                            # Testar standalone diretamente
                            url_st = f"{BASE_URL}/certificates/{token_int}"
                            page_adm.goto(url_st, wait_until="domcontentloaded", timeout=20000)
                            page_adm.wait_for_timeout(2000)
                            snap(page_adm, "admin_interno_standalone", full=True)
                            texto_st = page_adm.inner_text("body")
                            url_st_atual = page_adm.url
                            tem_cert_st = any(kw in texto_st.lower() for kw in ["certificado", "certificate", "valido", "válido"])
                            print(f"   Standalone direto: URL={url_st_atual}, tem_cert={tem_cert_st}")
                            results["admin_interno_standalone_url"] = (
                                "pass" if tem_cert_st else "fail",
                                f"URL={url_st_atual[:80]}, tem_cert={tem_cert_st}"
                            )
                        else:
                            print("   AVISO: Interno+Emitido sem certificate_token — standalone nao testavel via URL direta")
                            results["admin_interno_standalone_url"] = (
                                "blocked",
                                f"Interno+Emitido (id={rec_id_int}) sem certificate_token — standalone nao testavel"
                            )
                    else:
                        results["admin_interno_emitido_api"] = (False, "API filtro interno+emitted retornou 0 registros")
                        results["admin_interno_standalone_url"] = ("blocked", "Nenhum Interno+Emitido via API")
                else:
                    results["admin_interno_emitido_api"] = (False, f"API retornou {resp.status}")
                    results["admin_interno_standalone_url"] = ("blocked", f"API status {resp.status}")
            else:
                # Abrir kebab e testar Visualizar em Interno
                kebab_int = linha_adm_int.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
                if kebab_int.count() > 0:
                    kebab_int.click()
                    page_adm.wait_for_timeout(1200)
                    snap(page_adm, "admin_interno_01_menu_aberto")
                    print("\n   --- ADMIN: dispatch Visualizar em Interno+Emitido ---")
                    try:
                        with ctx_adm.expect_page(timeout=8000) as pg_info:
                            found_int, desc_int = dispatch_click_e_verificar(
                                page_adm, ctx_adm, "Visualizar", "admin_disp_int_vis"
                            )
                        nova = pg_info.value
                        nova.wait_for_load_state("domcontentloaded", timeout=12000)
                        snap(nova, "admin_interno_nova_aba", full=True)
                        print(f"   Interno nova aba URL: {nova.url}")
                        results["dispatch_Visualizar_admin_interno"] = (
                            True,
                            f"nova_aba=True, URL={nova.url[:80]}, tem_cert={'cert' in nova.url}"
                        )
                        nova.close()
                    except Exception as e:
                        snap(page_adm, "admin_interno_sem_nova_aba", full=True)
                        results["dispatch_Visualizar_admin_interno"] = (
                            False,
                            f"Sem nova aba: {desc_int if 'desc_int' in dir() else str(e)[:80]}"
                        )
                else:
                    results["dispatch_Visualizar_admin_interno"] = (False, "Kebab nao encontrado na linha Interno")

            browser_adm.close()

    # Sumario
    print("\n\n=== SUMARIO DIAGNOSTICO ===")
    for chave, val in results.items():
        if isinstance(val, tuple):
            v, d = val
        else:
            v, d = val, str(val)
        print(f"   [{chave}]: {v} — {str(d)[:120]}")


if __name__ == "__main__":
    main()
