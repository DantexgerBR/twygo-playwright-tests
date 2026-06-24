"""
QA 1.8 — TC7: Admin visualizando Externo (form viewing)
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

PASTA = Path(__file__).resolve().parents[1] / "evidencias" / "registros-f2-qa18"
PASTA.mkdir(parents=True, exist_ok=True)

c_admin = {"base_url": BASE_URL, "org_id": ORG_ID, "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}


def snap(page, nome, full=False):
    fp = PASTA / f"tc7_{nome}.png"
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


def main():
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        tw.login(page, c_admin, admin=True)
        page.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                  wait_until="domcontentloaded", timeout=30000)
        try:
            page.wait_for_function(
                "() => document.querySelectorAll('tbody tr').length > 0", timeout=35000
            )
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"   Tabela admin falhou: {e}")
            browser.close()
            return

        rows = page.locator("tbody tr")
        n = rows.count()
        print(f"   {n} linhas admin")
        snap(page, "00_lista", full=True)

        # Encontrar Externo
        linha_ext = None
        for i in range(min(n, 25)):
            row = rows.nth(i)
            txt = row.inner_text().lower()
            if "externo" in txt:
                linha_ext = row
                print(f"   Linha {i}: Externo — {row.inner_text()[:80]}")
                break

        if linha_ext is None:
            print("   Nenhum Externo encontrado nas primeiras 25 linhas")
            # Procurar kebab em qualquer linha
            linha_ext = rows.first

        # Verificar se a linha tem kebab
        kebab = linha_ext.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
        print(f"   Kebab count: {kebab.count()}")

        # Tentar via linha diferente se kebab nao encontrado
        if kebab.count() == 0:
            print("   Tentando linhas seguintes...")
            for i in range(min(n, 10)):
                row = rows.nth(i)
                k = row.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
                if k.count() > 0:
                    linha_ext = row
                    kebab = k
                    print(f"   Linha {i} tem kebab: {row.inner_text()[:60]}")
                    break

        if kebab.count() > 0:
            kebab.click()
            page.wait_for_timeout(1500)
            snap(page, "01_menu_aberto")
            clicou = mouse_click_item(page, "Visualizar")
            print(f"   Clicou Visualizar: {clicou}")
            if clicou:
                url = page.url
                print(f"   URL: {url}")
                txt = page.inner_text("body")
                txt_lower = txt.lower()
                print(f"   mode_view: {'mode=view' in url}")
                print(f"   cabecalho_visualizar: {'visualizar registro' in txt_lower}")
                print(f"   cabecalho_editar: {'registros > editar' in txt_lower}")
                n_disabled = page.evaluate("() => document.querySelectorAll('input[disabled], textarea[disabled], select[disabled]').length")
                n_total = page.evaluate("() => document.querySelectorAll('input, textarea, select').length")
                print(f"   inputs disabled: {n_disabled}/{n_total}")
                tem_arraste = "arraste o arquivo" in txt_lower
                btn_salvar_el = page.evaluate("() => Array.from(document.querySelectorAll('button')).some(b => ['salvar','excluir'].includes(b.innerText.trim().toLowerCase()))")
                tem_banner_rec = "recusado" in txt_lower and "registro" in txt_lower
                tem_banner_aprov = "certificado aprovado" in txt_lower
                btn_voltar = page.evaluate("() => Array.from(document.querySelectorAll('button')).some(b => b.innerText.toLowerCase().includes('voltar'))")
                print(f"   dropzone={tem_arraste}, btn_salvar/excluir={btn_salvar_el}")
                print(f"   banner_vermelho={tem_banner_rec}, banner_verde={tem_banner_aprov}")
                print(f"   btn_voltar={btn_voltar}")
                snap(page, "02_form_viewing", full=True)
        else:
            print("   Kebab nao encontrado em nenhuma linha")

        browser.close()


if __name__ == "__main__":
    main()
