"""
QA 1.8 — Verificacao detalhada do form viewing v2
Card 19895 | 2026-06-24 — corrigido erro de seletor CSS
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
    fp = PASTA / f"fv2_{nome}.png"
    page.screenshot(path=str(fp), full_page=full)
    print(f"   [snap] {fp.name}")
    return fp


def mouse_click_item(page, item_name):
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
        return {{ x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 }};
    }}""")
    if not coords:
        print(f"   Coordenadas de '{item_name}' nao encontradas")
        return False
    print(f"   mouse.click '{item_name}' em ({coords['x']:.0f}, {coords['y']:.0f})")
    page.mouse.move(coords["x"], coords["y"])
    page.wait_for_timeout(400)
    page.mouse.click(coords["x"], coords["y"])
    page.wait_for_timeout(3500)
    return True


def verificar_rn48(page, snap_prefix, label):
    """Verifica criterios da RN 48 usando evaluate() para evitar problemas de CSS selector."""
    url = page.url
    print(f"\n   [{label}] URL: {url}")

    data = page.evaluate("""() => {
        const body = document.body;
        const txt = body.innerText.toLowerCase();

        // 1. Cabecalho
        const h1 = document.querySelector('h1, [class*="title"], [class*="heading"]');
        const breadcrumb = document.querySelector('[aria-label="breadcrumb"], nav');
        const cabecalho = (h1 ? h1.innerText : '') + (breadcrumb ? breadcrumb.innerText : '');

        // 2. Campos disabled
        const allInputs = Array.from(document.querySelectorAll('input, textarea, select'));
        const disabledInputs = allInputs.filter(el => el.disabled || el.getAttribute('aria-disabled') === 'true');

        // 3. Toolbar do editor
        const toolbars = Array.from(document.querySelectorAll('[class*="toolbar"]'));
        const toolbarsVisiveis = toolbars.filter(el => {
            const r = el.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
        });

        // 4. Drop zone
        const dropzones = Array.from(document.querySelectorAll('[class*="dropzone"], [class*="drop"]'));
        const dropVisivel = dropzones.filter(el => {
            const r = el.getBoundingClientRect();
            const t = el.innerText || '';
            return r.width > 0 && t.toLowerCase().includes('arraste');
        });
        // Texto de upload
        const textoArraste = txt.includes('arraste o arquivo') || txt.includes('clique para selecionar');

        // 5. Botoes rodape
        const botoesTexto = Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim().toLowerCase());
        const btnSalvar = botoesTexto.some(t => t.includes('salvar'));
        const btnExcluir = botoesTexto.some(t => t.includes('excluir') || t.includes('deletar'));
        const btnCancelar = botoesTexto.some(t => t.includes('cancelar'));
        const btnVoltar = botoesTexto.some(t => t.includes('voltar'));

        // 6. Banners
        const bannerVerde = txt.includes('certificado aprovado');
        const bannerVermelho = txt.includes('recusado') || txt.includes('registro de aprendizagem recusado');

        // 7. Card IA
        const cardIA = txt.includes('preencher com ia');

        // 8. Modo view na URL
        const modeView = window.location.href.includes('mode=view');

        // 9. Titulo visivel na pagina
        const tituloVisualizarReg = txt.includes('visualizar registro');
        const tituloEditar = txt.includes('registros > editar') || (breadcrumb && breadcrumb.innerText.toLowerCase().includes('editar'));

        return {
            url: window.location.href,
            mode_view_url: modeView,
            titulo_visualizar_registro: tituloVisualizarReg,
            titulo_editar: tituloEditar,
            cabecalho: cabecalho.substring(0, 100),
            n_inputs: allInputs.length,
            n_disabled: disabledInputs.length,
            toolbars_visiveis: toolbarsVisiveis.length,
            texto_arraste: textoArraste,
            btn_salvar: btnSalvar,
            btn_excluir: btnExcluir,
            btn_cancelar: btnCancelar,
            btn_voltar: btnVoltar,
            banner_verde: bannerVerde,
            banner_vermelho: bannerVermelho,
            card_ia: cardIA
        };
    }""")

    print(f"   mode_view_url: {data['mode_view_url']}")
    print(f"   titulo_visualizar_registro: {data['titulo_visualizar_registro']}")
    print(f"   titulo_editar: {data['titulo_editar']}")
    print(f"   cabecalho: '{data['cabecalho']}'")
    print(f"   inputs: {data['n_disabled']}/{data['n_inputs']} disabled")
    print(f"   toolbars visiveis: {data['toolbars_visiveis']}")
    print(f"   texto_arraste (dropzone): {data['texto_arraste']}")
    print(f"   btn_salvar={data['btn_salvar']}, btn_excluir={data['btn_excluir']}, btn_cancelar={data['btn_cancelar']}, btn_voltar={data['btn_voltar']}")
    print(f"   banner_verde={data['banner_verde']}, banner_vermelho={data['banner_vermelho']}")
    print(f"   card_ia={data['card_ia']}")

    snap(page, f"{snap_prefix}_form", full=True)

    return data


def main():
    print("=== QA 1.8 — Form viewing v2 ===")
    resultados = {}

    with tw.sync_playwright() as p:
        # ALUNO
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
        print(f"   {n_a} linhas")

        # TC5: Externo Emitido
        linha_emit = None
        linha_rec = None
        for i in range(n_a):
            row = rows_a.nth(i)
            txt = row.inner_text().lower()
            if "emitido" in txt and linha_emit is None:
                linha_emit = row
            if "recusado" in txt and linha_rec is None:
                linha_rec = row

        print(f"   Externo Emitido: {'sim' if linha_emit else 'nao'}")
        print(f"   Externo Recusado: {'sim' if linha_rec else 'nao'}")

        if linha_emit:
            print("\n--- TC5: Externo Emitido (aluno) ---")
            kebab = linha_emit.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
            kebab.click()
            page_a.wait_for_timeout(1200)
            mouse_click_item(page_a, "Visualizar")
            data_tc5 = verificar_rn48(page_a, "tc5_aluno_emitido", "TC5")
            resultados["TC5"] = data_tc5

        if linha_rec:
            print("\n--- TC6: Externo Recusado (aluno) ---")
            page_a.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                        wait_until="domcontentloaded", timeout=25000)
            page_a.wait_for_timeout(2500)
            rows_a2 = page_a.locator("tbody tr")
            for i in range(rows_a2.count()):
                if "recusado" in rows_a2.nth(i).inner_text().lower():
                    linha_rec2 = rows_a2.nth(i)
                    kebab_r = linha_rec2.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
                    kebab_r.click()
                    page_a.wait_for_timeout(1200)
                    mouse_click_item(page_a, "Visualizar")
                    data_tc6 = verificar_rn48(page_a, "tc6_aluno_recusado", "TC6")
                    resultados["TC6"] = data_tc6
                    break

        browser_a.close()

        # ADMIN
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
            goto_tc2_tc3 = False
        else:
            rows_adm = page_adm.locator("tbody tr")
            n_adm = rows_adm.count()

            # TC7: Admin + Externo (qualquer status)
            linha_ext = None
            for i in range(min(n_adm, 25)):
                row = rows_adm.nth(i)
                if "externo" in row.inner_text().lower():
                    linha_ext = row
                    print(f"   Admin linha {i}: Externo para TC7")
                    break
            if linha_ext is None:
                linha_ext = rows_adm.first

            print("\n--- TC7: Admin + Externo ---")
            kebab_adm = linha_ext.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
            if kebab_adm.count() > 0:
                kebab_adm.click()
                page_adm.wait_for_timeout(1200)
                mouse_click_item(page_adm, "Visualizar")
                data_tc7 = verificar_rn48(page_adm, "tc7_admin_externo", "TC7")
                resultados["TC7"] = data_tc7

            # TC2/TC3: Interno Emitido — buscar token via API
            print("\n--- TC2: Interno Emitido — buscar via API ---")
            token_int = None
            rec_id_int = None
            for pg in range(1, 10):
                resp = page_adm.request.get(
                    f"{BASE_URL}/api/v1/o/{ORG_ID}/records?order_type=desc&per_page=50&page={pg}&order_by=created_at",
                    headers={"Accept": "application/json"}
                )
                if resp.status != 200:
                    break
                recs = resp.json().get("data", {}).get("records", [])
                int_emit_com_token = [r for r in recs
                                      if r.get("origin") == "internal"
                                      and r.get("certificate_situation") == "emitted"
                                      and r.get("certificate_token")]
                if int_emit_com_token:
                    rec = int_emit_com_token[0]
                    token_int = rec.get("certificate_token")
                    rec_id_int = rec.get("id")
                    print(f"   Interno+Emitido com token: id={rec_id_int}, token={token_int[:20] if token_int else 'VAZIO'}, user={rec.get('user_email')}")
                    break
                if not resp.json().get("data", {}).get("pagination", {}).get("next_page"):
                    break

            if token_int:
                url_st = f"{BASE_URL}/certificates/{token_int}"
                page_adm.goto(url_st, wait_until="domcontentloaded", timeout=20000)
                page_adm.wait_for_timeout(2000)
                snap(page_adm, "tc2_standalone", full=True)
                url_st_atual = page_adm.url
                texto_st = page_adm.inner_text("body")
                print(f"   TC2 standalone URL: {url_st_atual}")

                tem_cert = "certificado" in texto_st.lower() or "certificate" in texto_st.lower()
                tem_cinta_roxa = page_adm.evaluate("""() => {
                    const styles = Array.from(document.querySelectorAll('[style*="7f27d8"], [style*="7F27D8"]'));
                    return styles.length;
                }""")
                tem_validacao_txt = "validacao" in texto_st.lower() or "válido" in texto_st.lower() or "valido" in texto_st.lower()
                tem_baixar = "baixar" in texto_st.lower()
                tem_linkedin = "linkedin" in texto_st.lower()

                print(f"   tem_cert={tem_cert}, tem_validacao={tem_validacao_txt}, tem_baixar={tem_baixar}, tem_linkedin={tem_linkedin}")
                resultados["TC2"] = {
                    "url": url_st_atual,
                    "tem_cert": tem_cert,
                    "tem_validacao": tem_validacao_txt,
                    "tem_baixar": tem_baixar,
                    "tem_linkedin": tem_linkedin,
                    "texto_parcial": texto_st[:300]
                }

                # TC3: botao "Validar outro certificado"
                btn_validar = page_adm.locator("button:has-text('Validar outro certificado')").first
                n_btn = btn_validar.count()
                print(f"\n   TC3: botao 'Validar outro certificado' encontrado: {n_btn}")
                if n_btn > 0:
                    snap(page_adm, "tc3_botao", full=False)
                    # Clicar e verificar (em mesma aba, window.close() nao fecha)
                    pages_antes = len(ctx_adm.pages)
                    btn_validar.click()
                    page_adm.wait_for_timeout(2000)
                    pages_depois = len(ctx_adm.pages)
                    print(f"   TC3 apos click: paginas={pages_depois} (antes={pages_antes}), URL={page_adm.url}")
                    snap(page_adm, "tc3_apos_click", full=True)
                    resultados["TC3"] = {
                        "botao_presente": True,
                        "pages_antes": pages_antes,
                        "pages_depois": pages_depois,
                        "url_apos": page_adm.url
                    }
                else:
                    snap(page_adm, "tc3_sem_botao", full=True)
                    resultados["TC3"] = {"botao_presente": False, "texto_pagina": texto_st[:200]}
            else:
                print("   Nenhum Interno+Emitido com certificate_token encontrado")
                resultados["TC2"] = {"bloqueado": "Nenhum Interno+Emitido com token na stage (19 registros sem token)"}
                resultados["TC3"] = {"bloqueado": "Depende de TC2"}

            browser_adm.close()

    # Sumario
    print("\n\n=== SUMARIO FORM VIEWING v2 ===")
    for tc, data in resultados.items():
        print(f"\n   [{tc}]:")
        if isinstance(data, dict):
            for k, v in data.items():
                val_str = str(v)[:100]
                print(f"      {k}: {val_str}")
        else:
            print(f"      {data}")


if __name__ == "__main__":
    main()
