"""
QA 1.8 — Form viewing v3 (simplificado)
Card 19895 | 2026-06-24
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
    fp = PASTA / f"fv3_{nome}.png"
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
        return False
    page.mouse.move(coords["x"], coords["y"])
    page.wait_for_timeout(400)
    page.mouse.click(coords["x"], coords["y"])
    page.wait_for_timeout(4000)
    return True


def verificar_simples(page, snap_prefix, label):
    url = page.url
    mode_view = "mode=view" in url
    print(f"   [{label}] URL={url[:70]}, mode_view={mode_view}")

    snap(page, f"{snap_prefix}_form", full=True)

    # Checagens pontuais simples
    n_disabled = page.evaluate("() => document.querySelectorAll('input[disabled], textarea[disabled], select[disabled]').length")
    n_inputs_total = page.evaluate("() => document.querySelectorAll('input, textarea, select').length")

    texto = page.inner_text("body")
    txt_lower = texto.lower()

    cabecalho_editar = "registros > editar" in txt_lower
    cabecalho_visualizar = "visualizar registro" in txt_lower
    tem_toolbar = page.evaluate("() => document.querySelectorAll('[class*=toolbar]').length") > 0
    tem_arraste = "arraste o arquivo" in txt_lower
    btn_salvar = "salvar" in txt_lower
    btn_excluir_rodape = page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button'));
        return btns.some(b => b.innerText.trim().toLowerCase() === 'excluir' || b.innerText.trim().toLowerCase() === 'salvar');
    }""")
    banner_verde = "certificado aprovado" in txt_lower
    banner_vermelho = "recusado" in txt_lower and "registro de aprendizagem" in txt_lower
    btn_voltar = page.evaluate("() => Array.from(document.querySelectorAll('button')).some(b => b.innerText.toLowerCase().includes('voltar'))")

    print(f"   cabecalho_editar={cabecalho_editar}, cabecalho_visualizar={cabecalho_visualizar}")
    print(f"   inputs disabled: {n_disabled}/{n_inputs_total}")
    print(f"   toolbar={tem_toolbar}, arraste={tem_arraste}")
    print(f"   btn_salvar_texto={btn_salvar}, btn_excluir_ou_salvar_element={btn_excluir_rodape}")
    print(f"   banner_verde={banner_verde}, banner_vermelho={banner_vermelho}")
    print(f"   btn_voltar={btn_voltar}")

    return {
        "url": url,
        "mode_view": mode_view,
        "cabecalho_editar": cabecalho_editar,
        "cabecalho_visualizar": cabecalho_visualizar,
        "n_disabled": n_disabled,
        "n_inputs": n_inputs_total,
        "toolbar_presente": tem_toolbar,
        "dropzone_presente": tem_arraste,
        "btn_salvar_excluir_presente": btn_excluir_rodape,
        "banner_verde": banner_verde,
        "banner_vermelho": banner_vermelho,
        "btn_voltar": btn_voltar,
    }


def main():
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
        snap(page_a, "lista_aluno", full=True)

        for i in range(rows_a.count()):
            row = rows_a.nth(i)
            txt = row.inner_text().lower()
            if "emitido" in txt:
                print(f"\n--- TC5: linha {i} Externo Emitido ---")
                kebab = row.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
                kebab.click()
                page_a.wait_for_timeout(1200)
                snap(page_a, "tc5_menu_aberto")
                if mouse_click_item(page_a, "Visualizar"):
                    resultados["TC5"] = verificar_simples(page_a, "tc5_emitido", "TC5 Aluno Externo Emitido")
                break

        # Reload para TC6
        page_a.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                    wait_until="domcontentloaded", timeout=25000)
        page_a.wait_for_timeout(2500)
        rows_a2 = page_a.locator("tbody tr")
        for i in range(rows_a2.count()):
            row = rows_a2.nth(i)
            txt = row.inner_text().lower()
            if "recusado" in txt:
                print(f"\n--- TC6: linha {i} Externo Recusado ---")
                kebab = row.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
                kebab.click()
                page_a.wait_for_timeout(1200)
                snap(page_a, "tc6_menu_aberto")
                if mouse_click_item(page_a, "Visualizar"):
                    resultados["TC6"] = verificar_simples(page_a, "tc6_recusado", "TC6 Aluno Externo Recusado")
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
            print(f"   Tabela admin falhou: {e}")
            browser_adm.close()
            return

        rows_adm = page_adm.locator("tbody tr")
        snap(page_adm, "lista_admin", full=True)

        # TC7: Admin + Externo Emitido ou Recusado
        for i in range(min(rows_adm.count(), 25)):
            row = rows_adm.nth(i)
            txt = row.inner_text().lower()
            if "externo" in txt and ("emitido" in txt or "recusado" in txt):
                print(f"\n--- TC7: Admin linha {i} Externo ---")
                kebab = row.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
                if kebab.count() > 0:
                    kebab.click()
                    page_adm.wait_for_timeout(1200)
                    snap(page_adm, "tc7_menu_aberto")
                    if mouse_click_item(page_adm, "Visualizar"):
                        resultados["TC7"] = verificar_simples(page_adm, "tc7_admin_externo", "TC7 Admin Externo")
                break

        # TC2/TC3: buscar Interno+Emitido com token
        print("\n--- TC2: Buscar Interno+Emitido com token ---")
        token_int = None
        for pg in range(1, 15):
            resp = page_adm.request.get(
                f"{BASE_URL}/api/v1/o/{ORG_ID}/records?order_type=desc&per_page=50&page={pg}&order_by=created_at",
                headers={"Accept": "application/json"}
            )
            if resp.status != 200:
                print(f"   API status {resp.status}")
                break
            data = resp.json()
            recs = data.get("data", {}).get("records", [])
            for r in recs:
                if (r.get("origin") == "internal" and
                        r.get("certificate_situation") == "emitted" and
                        r.get("certificate_token")):
                    token_int = r.get("certificate_token")
                    print(f"   Encontrado: id={r.get('id')}, token={token_int[:20]}, user={r.get('user_email')}")
                    break
            if token_int:
                break
            if not data.get("data", {}).get("pagination", {}).get("next_page"):
                break

        if token_int:
            url_st = f"{BASE_URL}/certificates/{token_int}"
            print(f"   Acessando: {url_st}")
            page_adm.goto(url_st, wait_until="domcontentloaded", timeout=20000)
            page_adm.wait_for_timeout(2500)
            snap(page_adm, "tc2_standalone", full=True)
            url_atual = page_adm.url
            texto_st = page_adm.inner_text("body")
            print(f"   TC2 URL: {url_atual}")
            print(f"   Texto (200): {texto_st[:200]}")

            resultados["TC2"] = {
                "url": url_atual,
                "tem_cert": "certificado" in texto_st.lower(),
                "tem_validacao": "valido" in texto_st.lower() or "válido" in texto_st.lower() or "validar" in texto_st.lower(),
                "tem_baixar": "baixar" in texto_st.lower(),
                "tem_linkedin": "linkedin" in texto_st.lower(),
                "conteudo": texto_st[:300]
            }

            # TC3
            btn_validar = page_adm.locator("button:has-text('Validar outro certificado')").first
            if btn_validar.count() > 0:
                snap(page_adm, "tc3_botao")
                btn_validar.click()
                page_adm.wait_for_timeout(2500)
                url_pos = page_adm.url
                print(f"   TC3 apos click: URL={url_pos}")
                snap(page_adm, "tc3_apos_click", full=True)
                resultados["TC3"] = {"botao_presente": True, "url_apos_click": url_pos}
            else:
                print("   Botao TC3 nao encontrado")
                snap(page_adm, "tc3_sem_botao", full=True)
                resultados["TC3"] = {"botao_presente": False}
        else:
            print("   Nenhum Interno+Emitido com token encontrado em toda a stage")
            resultados["TC2"] = {"bloqueado": True, "motivo": "Nenhum Interno+Emitido com certificate_token na stage"}
            resultados["TC3"] = {"bloqueado": True, "motivo": "Depende de TC2"}

        browser_adm.close()

    print("\n\n=== SUMARIO FINAL ===")
    for tc, data in resultados.items():
        print(f"\n   [{tc}]")
        if isinstance(data, dict):
            for k, v in data.items():
                print(f"      {k}: {str(v)[:120]}")


if __name__ == "__main__":
    main()
