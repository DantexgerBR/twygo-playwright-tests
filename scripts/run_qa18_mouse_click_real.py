"""
QA 1.8 — Clique de mouse nas coordenadas exatas do Visualizar
Card 19895 | 2026-06-24

O locator.click() nao pousa no Visualizar (menu nao fecha) porque o Playwright
detecta que outro elemento esta na frente (elementFromPoint retorna o DIV interno,
nao o BUTTON).

Esse script:
1. Verifica o CSS pointer-events dos dois itens (Editar vs Visualizar)
2. Usa page.mouse.click(x, y) nas coordenadas exatas do button Visualizar
   — isso bypassa o hit-test do Playwright
3. Verifica se o menu fecha e se navega
4. Compara com Editar no mesmo metodo
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


def snap(page, nome, full=False):
    fp = PASTA / f"mouse_{nome}.png"
    page.screenshot(path=str(fp), full_page=full)
    print(f"   [snap] {fp.name}")
    return fp


def inspecionar_css_pointer_events(page, item_name):
    """Verifica pointer-events e z-index do item e de seus filhos."""
    return page.evaluate(f"""() => {{
        const allItems = Array.from(document.querySelectorAll('[role="menuitem"]'));
        const visible = allItems.filter(el => {{
            const txt = el.innerText.toLowerCase();
            const r = el.getBoundingClientRect();
            return txt.includes('{item_name.lower()}') && r.x > 400 && r.width > 0;
        }});
        if (!visible.length) return null;
        const el = visible[0];
        const rect = el.getBoundingClientRect();
        const computed = window.getComputedStyle(el);
        const children = Array.from(el.querySelectorAll('*')).slice(0, 5).map(child => {{
            const cs = window.getComputedStyle(child);
            const cr = child.getBoundingClientRect();
            return {{
                tag: child.tagName,
                id: child.id,
                class: child.className.substring(0, 40),
                pointerEvents: cs.pointerEvents,
                zIndex: cs.zIndex,
                position: cs.position,
                display: cs.display,
                rect: {{ x: cr.x.toFixed(0), y: cr.y.toFixed(0), w: cr.width.toFixed(0), h: cr.height.toFixed(0) }}
            }};
        }});
        return {{
            rect: {{ x: rect.x, y: rect.y, w: rect.width, h: rect.height }},
            pointerEvents: computed.pointerEvents,
            zIndex: computed.zIndex,
            position: computed.position,
            cursor: computed.cursor,
            tabIndex: el.getAttribute('tabindex'),
            children: children
        }};
    }}""")


def mouse_click_coordenada(page, ctx, item_name, snap_prefix):
    """Usa page.mouse.click() nas coordenadas do centro do item."""
    url_antes = page.url
    pages_antes = len(ctx.pages)

    # Obter coordenadas do button Visualizar/Editar
    coords = page.evaluate(f"""() => {{
        const allItems = Array.from(document.querySelectorAll('[role="menuitem"]'));
        const visible = allItems.filter(el => {{
            const txt = el.innerText.toLowerCase();
            const r = el.getBoundingClientRect();
            return txt.includes('{item_name.lower()}') && r.x > 400 && r.width > 0;
        }});
        if (!visible.length) return null;
        const el = visible[0];
        const rect = el.getBoundingClientRect();
        return {{ x: rect.x + rect.width / 2, y: rect.y + rect.height / 2, rect: rect }};
    }}""")

    if not coords:
        print(f"   [{item_name}] Coordenadas nao encontradas")
        return False, False, False, "Coordenadas nao encontradas"

    cx, cy = coords["x"], coords["y"]
    print(f"   [{item_name}] mouse.click em ({cx:.1f}, {cy:.1f})")

    snap(page, f"{snap_prefix}_01_antes")

    # CLIQUE DIRETO VIA MOUSE (bypassa hit-test do Playwright)
    page.mouse.move(cx, cy)
    page.wait_for_timeout(500)
    page.mouse.click(cx, cy)
    page.wait_for_timeout(3500)

    url_depois = page.url
    pages_depois = len(ctx.pages)
    nova_aba = pages_depois > pages_antes
    url_mudou = url_depois != url_antes
    menu_fechou = page.locator("[role='menuitem']:visible").count() == 0

    snap(page, f"{snap_prefix}_02_apos", full=True)

    print(f"   [{item_name}] menu_fechou={menu_fechou}, nova_aba={nova_aba}, url_mudou={url_mudou}")
    print(f"   URL depois: {url_depois[:80]}")

    desc = f"mouse.click({cx:.0f},{cy:.0f}): menu_fechou={menu_fechou}, nova_aba={nova_aba}, url_mudou={url_mudou}, url={url_depois[:70]}"
    return menu_fechou, nova_aba, url_mudou, desc


def main():
    print("=== QA 1.8 — Mouse click nas coordenadas exatas ===")
    print("=== Separando: hit-test vs handler React ===")

    results = {}

    with tw.sync_playwright() as p:
        # --- ALUNO ---
        print("\n=== ALUNO ===")
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
        print(f"   Linhas: {n_a}")

        if n_a > 0:
            # Encontrar linha Externo+Emitido
            linha_aluno = None
            for i in range(n_a):
                row = rows_a.nth(i)
                if "emitido" in row.inner_text().lower():
                    linha_aluno = row
                    break
            if linha_aluno is None:
                linha_aluno = rows_a.first

            # TESTE A: mouse.click no Visualizar
            print("\n--- Teste A1: Inspecao CSS pointer-events ---")
            kebab_a = linha_aluno.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
            kebab_a.click()
            page_a.wait_for_timeout(1200)
            snap(page_a, "aluno_menu_aberto")

            css_vis = inspecionar_css_pointer_events(page_a, "Visualizar")
            css_edit = inspecionar_css_pointer_events(page_a, "Editar")
            print(f"\n   CSS Editar: pointer={css_edit.get('pointerEvents')}, zIndex={css_edit.get('zIndex')}, cursor={css_edit.get('cursor')}, tabIndex={css_edit.get('tabIndex')}")
            print(f"   CSS Visualizar: pointer={css_vis.get('pointerEvents')}, zIndex={css_vis.get('zIndex')}, cursor={css_vis.get('cursor')}, tabIndex={css_vis.get('tabIndex')}")

            if css_vis and css_vis.get("children"):
                print("\n   Filhos do Visualizar:")
                for ch in css_vis["children"]:
                    print(f"   - {ch['tag']}#{ch['id']} .{ch['class']}: pointer={ch['pointerEvents']}, z={ch['zIndex']}, pos={ch['position']}, rect={ch['rect']}")

            print("\n--- Teste A2: mouse.click no Visualizar ---")
            mf_v, na_v, um_v, desc_v = mouse_click_coordenada(page_a, ctx_a, "Visualizar", "aluno_vis")
            results["aluno_mouse_Visualizar"] = (mf_v, na_v, um_v, desc_v)

            if na_v:
                nova = ctx_a.pages[-1]
                nova.wait_for_load_state("domcontentloaded", timeout=12000)
                snap(nova, "aluno_vis_nova_aba", full=True)
                print(f"   NOVA ABA: {nova.url}")
                results["aluno_Visualizar_nova_aba"] = nova.url

            # Se URL mudou (form viewing), inspecionar
            if um_v and not na_v:
                texto = page_a.inner_text("body")
                tem_viewing = "visualizar registro" in texto.lower()
                tem_disabled = page_a.evaluate("() => document.querySelectorAll('input:disabled').length")
                print(f"   Form viewing: tem_header={tem_viewing}, inputs_disabled={tem_disabled}")

            # Navegar de volta para testar Editar
            page_a.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                        wait_until="domcontentloaded", timeout=25000)
            page_a.wait_for_timeout(2500)

            rows_a2 = page_a.locator("tbody tr")
            if rows_a2.count() > 0:
                linha_aluno2 = None
                for i in range(rows_a2.count()):
                    if "emitido" in rows_a2.nth(i).inner_text().lower():
                        linha_aluno2 = rows_a2.nth(i)
                        break
                if linha_aluno2 is None:
                    linha_aluno2 = rows_a2.first
                kebab_a2 = linha_aluno2.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
                kebab_a2.click()
                page_a.wait_for_timeout(1200)
                print("\n--- Teste A3: mouse.click no Editar (controle) ---")
                mf_e, na_e, um_e, desc_e = mouse_click_coordenada(page_a, ctx_a, "Editar", "aluno_edit")
                results["aluno_mouse_Editar"] = (mf_e, na_e, um_e, desc_e)

        browser_a.close()

        # --- ADMIN ---
        print("\n=== ADMIN ===")
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

            linha_adm_ext = None
            for i in range(min(n_adm, 30)):
                row = rows_adm.nth(i)
                if "externo" in row.inner_text().lower():
                    linha_adm_ext = row
                    print(f"   Admin linha {i}: Externo")
                    break
            if linha_adm_ext is None:
                linha_adm_ext = rows_adm.first

            kebab_adm = linha_adm_ext.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
            if kebab_adm.count() > 0:
                kebab_adm.click()
                page_adm.wait_for_timeout(1200)
                snap(page_adm, "admin_menu_aberto")

                # CSS admin
                css_vis_adm = inspecionar_css_pointer_events(page_adm, "Visualizar")
                print(f"\n   CSS Visualizar admin: pointer={css_vis_adm.get('pointerEvents')}, cursor={css_vis_adm.get('cursor')}")

                print("\n--- Admin: mouse.click no Visualizar (Externo) ---")
                mf_adm, na_adm, um_adm, desc_adm = mouse_click_coordenada(page_adm, ctx_adm, "Visualizar", "admin_vis")
                results["admin_mouse_Visualizar_externo"] = (mf_adm, na_adm, um_adm, desc_adm)

                if na_adm:
                    nova = ctx_adm.pages[-1]
                    nova.wait_for_load_state("domcontentloaded", timeout=12000)
                    snap(nova, "admin_vis_nova_aba", full=True)
                    print(f"   NOVA ABA admin: {nova.url}")
                elif um_adm:
                    texto_adm = page_adm.inner_text("body")
                    tem_viewing_adm = "visualizar registro" in texto_adm.lower()
                    print(f"   Form viewing admin: {tem_viewing_adm}")
                    snap(page_adm, "admin_vis_form_viewing", full=True)
            else:
                print("   Kebab admin nao encontrado")
                results["admin_mouse_Visualizar_externo"] = (False, False, False, "Kebab nao encontrado")

            browser_adm.close()

    # Sumario final
    print("\n\n=== SUMARIO MOUSE CLICK ===")
    for chave, val in results.items():
        if isinstance(val, tuple) and len(val) == 4:
            mf, na, um, d = val
            status = "PASSOU" if (mf and (na or um)) else ("FALHOU" if mf else "HIT-MISS")
            print(f"   [{status}] {chave}: menu_fechou={mf}, nova_aba={na}, url_mudou={um}")
            print(f"            {d[:100]}")
        else:
            print(f"   [{chave}]: {val}")

    # Analise discriminatoria
    print("\n=== ANALISE DISCRIMINATORIA ===")
    vis_aluno = results.get("aluno_mouse_Visualizar", (False, False, False, ""))
    edit_aluno = results.get("aluno_mouse_Editar", (False, False, False, ""))
    vis_admin = results.get("admin_mouse_Visualizar_externo", (False, False, False, ""))

    vis_mf = vis_aluno[0] if isinstance(vis_aluno, tuple) else False
    edit_mf = edit_aluno[0] if isinstance(edit_aluno, tuple) else False
    vis_acao = vis_aluno[1] or vis_aluno[2] if isinstance(vis_aluno, tuple) else False

    if vis_mf and not vis_acao:
        print("   CONCLUSAO: mouse.click POUSOU no Visualizar (menu fechou) mas SEM acao.")
        print("   => Bug esta no HANDLER REACT (onClick nao implementado), NAO no hit-test.")
        print("   => Veredito: BUG DE PRODUTO (handler ausente). Nao e acessibilidade de teclado.")
    elif not vis_mf and edit_mf:
        print("   CONCLUSAO: mouse.click nao pousa no Visualizar, mas pousa no Editar.")
        print("   => Problema de SOBREPOSICAO CSS no item Visualizar (pointer-events?).")
        print("   => Veredito: Pode ser bug de CSS que impede qualquer interacao.")
    elif vis_mf and vis_acao:
        print("   CONCLUSAO: mouse.click FUNCIONOU — Visualizar abriu aba/navegou!")
        print("   => O bug anterior era de metodo de interacao (Enter/ArrowDown), NAO do handler.")
        print("   => Veredito: PASSOU. Se tiver nova aba, verificar conteudo.")
    else:
        print(f"   CONCLUSAO INCONCLUSIVA: vis_mf={vis_mf}, edit_mf={edit_mf}, vis_acao={vis_acao}")


if __name__ == "__main__":
    main()
