"""
Validação retrabalho Artia — card 20334
"[Registros F2] Tela de visualizar registro não fica totalmente em modo somente leitura"
PR de correção: https://github.com/Twygo/twyg-app/pull/10843

Reaproveita a lógica de scripts/run_qa18_form_viewing_v3.py (script que capturou
as evidências originais do bug), ajustando `verificar_simples` para checar
visibilidade REAL (offsetParent / getComputedStyle) em vez de só presença no DOM,
e para contar apenas inputs "reais" visíveis do formulário (evita falso negativo
por inputs ocultos de libs como react-select/date-picker que nunca ficam
'disabled' mas também não são editáveis por não estarem na tela).

Credenciais vêm do .env (prefixo REGISTROSF2_*) — NÃO hardcode.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = os.environ.get("REGISTROSF2_BASE_URL", "https://registrosf2.stage.twygoead.com").rstrip("/")
ORG_ID = os.environ.get("REGISTROSF2_ORG_ID", "37079")
ADMIN_EMAIL = os.environ["REGISTROSF2_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["REGISTROSF2_ADMIN_PASSWORD"]
ALUNO_EMAIL = os.environ["REGISTROSF2_TC3_EMAIL"]
ALUNO_PASSWORD = os.environ["REGISTROSF2_TC3_PASSWORD"]

PASTA = Path(__file__).resolve().parents[1] / "evidencias" / "registros-f2-qa18"
PASTA.mkdir(parents=True, exist_ok=True)

c_admin = {"base_url": BASE_URL, "org_id": ORG_ID, "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}


def snap(page, nome, full=False):
    fp = PASTA / f"pr10843_{nome}.png"
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
    try:
        titulo = page.locator("h1, h2, h3").filter(has_text="QA").first
        if titulo.count() == 0:
            titulo = page.locator("text=/QA\\d+-TC/").first
        print(f"   registro_id(texto)={titulo.inner_text() if titulo.count() else 'NAO ENCONTRADO'}")
    except Exception as e:
        print(f"   registro_id: erro ao ler ({e})")

    snap(page, f"{snap_prefix}_form", full=True)

    # Visibilidade REAL (não só presença no DOM) via offsetParent (null quando
    # display:none/visibility:hidden em ancestral) + getComputedStyle no próprio nó.
    def visivel_js(sel):
        return page.evaluate(f"""() => {{
            const els = Array.from(document.querySelectorAll('{sel}'));
            return els.filter(el => {{
                if (el.offsetParent === null) return false;
                const cs = getComputedStyle(el);
                return cs.visibility !== 'hidden' && cs.display !== 'none' && parseFloat(cs.opacity) > 0;
            }}).length;
        }}""")

    # Métrica ORIGINAL literal (igual ao script v3) — mantida para comparação
    # direta com o baseline "14/37" documentado no bug.
    n_disabled_original = page.evaluate("() => document.querySelectorAll('input[disabled], textarea[disabled], select[disabled]').length")
    n_inputs_total_original = page.evaluate("() => document.querySelectorAll('input, textarea, select').length")

    # inputs/textarea/select VISÍVEIS (exclui hidden inputs de libs, que nunca
    # ficam disabled mas também não contam como "editável na tela")
    n_inputs_total = visivel_js("input, textarea, select")
    n_disabled = page.evaluate("""() => {
        const els = Array.from(document.querySelectorAll('input, textarea, select'));
        return els.filter(el => {
            if (el.offsetParent === null) return false;
            const cs = getComputedStyle(el);
            if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) <= 0) return false;
            return el.disabled || el.readOnly || el.getAttribute('aria-disabled') === 'true';
        }).length;
    }""")

    # Enumera os campos VISÍVEIS que ainda estão editáveis (não disabled/readonly)
    # — precisamos NOMEAR o campo que vazou, não só contar.
    campos_editaveis = page.evaluate("""() => {
        const els = Array.from(document.querySelectorAll('input, textarea, select'));
        return els.filter(el => {
            if (el.offsetParent === null) return false;
            const cs = getComputedStyle(el);
            if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) <= 0) return false;
            return !(el.disabled || el.readOnly || el.getAttribute('aria-disabled') === 'true');
        }).map(el => ({
            tag: el.tagName.toLowerCase(),
            type: el.type || null,
            name: el.name || el.id || null,
            placeholder: el.placeholder || null,
        }));
    }""")

    texto = page.inner_text("body")
    txt_lower = texto.lower()

    cabecalho_editar = "registros > editar" in txt_lower
    cabecalho_visualizar = "visualizar registro" in txt_lower

    # ATENCAO: `[class*=toolbar]` da falso positivo — o editor de texto rico (Slate.js)
    # usa a classe interna "ignore-click-outside/toolbar" no proprio container do
    # texto, que SEMPRE existe no DOM (editavel ou nao). Isso NAO e a toolbar visual
    # (botoes de negrito/italico/etc). Checagem correta: existe algum botao de
    # formatacao visivel OU o editor esta contenteditable=true?
    tem_toolbar = page.evaluate("""() => {
        const editors = Array.from(document.querySelectorAll('.slate-editor, [contenteditable]'));
        const algumEditavel = editors.some(el => el.offsetParent !== null &&
            (el.getAttribute('contenteditable') === 'true' || el.isContentEditable));
        // botoes de formatacao (negrito/italico/lista/etc) tipicamente ficam
        // agrupados perto do editor com aria-label ou title reconheciveis
        const btns = Array.from(document.querySelectorAll('button, [role=button]'));
        const botoesFormatacao = btns.filter(b => {
            if (b.offsetParent === null) return false;
            const label = ((b.getAttribute('aria-label') || '') + ' ' + (b.title || '') + ' ' + b.innerText)
                .toLowerCase();
            return /negrito|italico|itálico|sublinhado|lista|bold|italic|underline|heading|link/.test(label);
        });
        return algumEditavel || botoesFormatacao.length > 0;
    }""")
    tem_arraste = "arraste o arquivo" in txt_lower
    dropzone_visivel = False
    try:
        dz = page.locator("text=Arraste o arquivo").first
        dropzone_visivel = dz.count() > 0 and dz.is_visible()
    except Exception:
        dropzone_visivel = tem_arraste
    btn_salvar = "salvar" in txt_lower
    btn_excluir_rodape = page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button'));
        return btns.some(b => {
            if (b.offsetParent === null) return false;
            const t = b.innerText.trim().toLowerCase();
            return t === 'excluir' || t === 'salvar';
        });
    }""")
    banner_verde = "certificado aprovado" in txt_lower
    banner_vermelho = "recusado" in txt_lower and "registro de aprendizagem" in txt_lower
    btn_voltar = page.evaluate("() => Array.from(document.querySelectorAll('button')).some(b => b.innerText.toLowerCase().includes('voltar'))")

    if n_inputs_total == 0:
        print("   [ALERTA] n_inputs_total(visiveis)=0 — suspeito (view pode ter renderizado texto puro"
              " OU form nao carregou). NAO tratar 0==0 como PASS automatico; conferir screenshot.")

    print(f"   cabecalho_editar={cabecalho_editar}, cabecalho_visualizar={cabecalho_visualizar}")
    print(f"   [ORIGINAL] inputs disabled (DOM total, igual ao script v3): {n_disabled_original}/{n_inputs_total_original}")
    print(f"   [VISIVEIS] inputs disabled/readonly (offsetParent+computedstyle): {n_disabled}/{n_inputs_total}")
    if campos_editaveis:
        print(f"   CAMPOS AINDA EDITAVEIS ({len(campos_editaveis)}): {campos_editaveis}")
    print(f"   toolbar_visivel={tem_toolbar}, dropzone_texto_presente={tem_arraste}, dropzone_visivel={dropzone_visivel}")
    print(f"   btn_salvar_texto={btn_salvar}, btn_excluir_ou_salvar_element_visivel={btn_excluir_rodape}")
    print(f"   banner_verde={banner_verde}, banner_vermelho={banner_vermelho}")
    print(f"   btn_voltar={btn_voltar}")

    return {
        "url": url,
        "mode_view": mode_view,
        "cabecalho_editar": cabecalho_editar,
        "cabecalho_visualizar": cabecalho_visualizar,
        "n_disabled_original": n_disabled_original,
        "n_inputs_original": n_inputs_total_original,
        "n_disabled": n_disabled,
        "n_inputs": n_inputs_total,
        "campos_editaveis": campos_editaveis,
        "toolbar_presente": tem_toolbar,
        "dropzone_presente": dropzone_visivel,
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
                    resultados["TC5_aluno_emitido"] = verificar_simples(page_a, "tc5_emitido", "TC5 Aluno Externo Emitido")
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
                    resultados["TC6_aluno_recusado"] = verificar_simples(page_a, "tc6_recusado", "TC6 Aluno Externo Recusado")
                break

        # BONUS (nao obrigatorio, nao bloqueia veredito): o registro original do bug
        # (QA19-TC4-28625 / id 44280002, Externo) mudou de "emitted" para "approved"
        # na stage entre a captura do bug e esta validacao — nao existe mais NENHUM
        # registro Externo+Emitido na org 37079 (confirmado via API). Abrimos o
        # registro Aprovado mesmo assim so para registrar um dado extra sobre o
        # banner verde, mas isso NAO substitui o caso "Emitido" exigido.
        print("\n--- BONUS: registro original (agora 'Aprovado', nao 'Emitido') ---")
        try:
            page_a.goto(f"{BASE_URL}/o/{ORG_ID}/records/44280002/edit?mode=view",
                        wait_until="domcontentloaded", timeout=20000)
            page_a.wait_for_timeout(3000)
            resultados["BONUS_aluno_aprovado_ex_emitido"] = verificar_simples(
                page_a, "bonus_aprovado", "BONUS Aluno Externo Aprovado (era Emitido no bug original)")
        except Exception as e:
            print(f"   BONUS falhou: {e}")

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
            return resultados

        rows_adm = page_adm.locator("tbody tr")
        snap(page_adm, "lista_admin", full=True)

        # TC7: Admin + Externo Recusado (caso obrigatório do bug original)
        achou_recusado = False
        for i in range(min(rows_adm.count(), 40)):
            row = rows_adm.nth(i)
            txt = row.inner_text().lower()
            if "externo" in txt and "recusado" in txt:
                print(f"\n--- TC7: Admin linha {i} Externo Recusado ---")
                kebab = row.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
                if kebab.count() > 0:
                    kebab.click()
                    page_adm.wait_for_timeout(1200)
                    snap(page_adm, "tc7_menu_aberto")
                    if mouse_click_item(page_adm, "Visualizar"):
                        resultados["TC7_admin_recusado"] = verificar_simples(page_adm, "tc7_admin_recusado", "TC7 Admin Externo Recusado")
                achou_recusado = True
                break
        if not achou_recusado:
            print("   TC7: nenhuma linha Externo Recusado encontrada para Admin")

        # Extra (não obrigatório): Admin + Externo Emitido, se existir
        page_adm.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                      wait_until="domcontentloaded", timeout=30000)
        page_adm.wait_for_timeout(2500)
        rows_adm2 = page_adm.locator("tbody tr")
        achou_emitido = False
        for i in range(min(rows_adm2.count(), 40)):
            row = rows_adm2.nth(i)
            txt = row.inner_text().lower()
            if "externo" in txt and "emitido" in txt:
                print(f"\n--- EXTRA: Admin linha {i} Externo Emitido ---")
                kebab = row.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
                if kebab.count() > 0:
                    kebab.click()
                    page_adm.wait_for_timeout(1200)
                    snap(page_adm, "tc7b_menu_aberto")
                    if mouse_click_item(page_adm, "Visualizar"):
                        resultados["EXTRA_admin_emitido"] = verificar_simples(page_adm, "tc7b_admin_emitido", "EXTRA Admin Externo Emitido")
                achou_emitido = True
                break
        if not achou_emitido:
            print("   EXTRA: nenhuma linha Externo Emitido encontrada para Admin (nao obrigatorio)")

        browser_adm.close()

    print("\n\n=== SUMARIO FINAL ===")
    for tc, data in resultados.items():
        print(f"\n   [{tc}]")
        if isinstance(data, dict):
            for k, v in data.items():
                print(f"      {k}: {str(v)[:120]}")

    return resultados


if __name__ == "__main__":
    main()
