"""
Recon QA 1.8 — dispatchEvent direto no elemento React do menuitem Visualizar.
Testa se o handler React responde ao evento sintetico.
Tambem testa: fechar menu manualmente e testar outros itens (Editar) para comparar.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
from playwright.sync_api import TimeoutError as PWTimeout

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"

PASTA = Path(__file__).resolve().parents[1] / "evidencias" / "registros-f2-qa18"
PASTA.mkdir(parents=True, exist_ok=True)

c_admin = {
    "base_url": BASE_URL, "org_id": ORG_ID,
    "email": "dante.tavares@twygo.com", "senha": "123456"
}


def snap(page, nome, full=False):
    fp = PASTA / f"{nome}.png"
    page.screenshot(path=str(fp), full_page=full)
    print(f"   [snap] {fp.name}")


def main():
    with tw.sync_playwright() as p:
        # === ALUNO: Externo Pendente — dispatchEvent + comparar Editar ===
        print("\n=== ALUNO: dispatch + comparar outros itens ===")
        browser, ctx, page = tw.nova_pagina(p)
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        page.fill("#user_email", "qa11tc342588@twygotest.com")
        page.fill("#user_password", "twygoqa2026")
        page.click("#user_submit")
        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        page.wait_for_timeout(2000)
        tw.dispensar_nps(page)
        page.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                  wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(3000)

        # Abrir kebab
        row = page.locator("tbody tr").first
        kebab = row.locator("button.chakra-menu__menu-button").first
        kebab.click()
        page.wait_for_timeout(1000)
        snap(page, "dispatch_aluno_01_menu_aberto")

        # 1. Testar Editar via get_by_role para ver se FECHA o menu
        print("   Testando 'Editar' via get_by_role para confirmar se fecha menu...")
        editar = page.get_by_role("menuitem", name="Editar")
        cnt_e = editar.count()
        print(f"   Editar count: {cnt_e}")
        if cnt_e > 0:
            nav_urls_e = []
            page.on("framenavigated", lambda f: nav_urls_e.append(f.url) if f == page.main_frame else None)
            pages_e_antes = len(ctx.pages)
            try:
                editar.first.click(timeout=5000)
                print("   Editar click OK")
            except Exception as ex:
                print(f"   Editar excecao: {ex}")
            page.wait_for_timeout(3000)
            pages_e_depois = len(ctx.pages)
            print(f"   URL apos Editar: {page.url}")
            print(f"   Paginas: {pages_e_antes} -> {pages_e_depois}")
            print(f"   Navegacoes Editar: {nav_urls_e}")
            snap(page, "dispatch_aluno_02_pos_editar", full=True)

        # Voltar para lista se navegou
        page.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                  wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(3000)

        # 2. Abrir menu novamente e testar dispatchEvent("click") no Visualizar
        print("\n   Abrindo menu novamente para dispatchEvent...")
        row2 = page.locator("tbody tr").first
        kebab2 = row2.locator("button.chakra-menu__menu-button").first
        kebab2.click()
        page.wait_for_timeout(1000)

        # Usar dispatchEvent direto no elemento
        result_dispatch = page.evaluate("""() => {
            const items = Array.from(document.querySelectorAll('[role="menuitem"]'));
            const vis = items.find(el => el.innerText && el.innerText.trim() === 'Visualizar');
            if (!vis) return { found: false };
            const r = vis.getBoundingClientRect();
            // Informacoes antes do dispatchEvent
            const info = {
                found: true,
                text: vis.innerText.trim(),
                left: Math.round(r.left),
                top: Math.round(r.top),
                tagName: vis.tagName,
                className: vis.className.slice(0, 100),
                hasOnClick: !!vis.onclick,
                attributes: Array.from(vis.attributes).map(a => a.name + '=' + a.value)
            };
            // Disparar click event
            vis.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
            return info;
        }""")

        print(f"   dispatchEvent resultado: {result_dispatch}")
        page.wait_for_timeout(3000)
        print(f"   URL apos dispatch: {page.url}")
        print(f"   Paginas: {len(ctx.pages)}")
        snap(page, "dispatch_aluno_03_pos_dispatch", full=True)

        # 3. Verificar se alguma rota React mudou (checar o DOM por "Visualizar registro")
        body = page.inner_text("body")
        if "Visualizar registro" in body:
            print("   ACHOU 'Visualizar registro' no DOM apos dispatch!")
        else:
            print("   'Visualizar registro' NAO encontrado apos dispatch")

        browser.close()

        # === ADMIN HEADED: mesmo teste ===
        print("\n=== ADMIN HEADED: dispatch + Editar ===")
        browser2, ctx2, page2 = tw.nova_pagina(p)
        tw.login(page2, c_admin, admin=True)
        page2.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                   wait_until="domcontentloaded", timeout=25000)
        page2.wait_for_timeout(5000)

        rows2 = page2.locator("tbody tr")
        n2 = rows2.count()
        print(f"   Linhas admin: {n2}")

        if n2 >= 2:
            # Testar Editar para confirmar que outro item do menu FUNCIONA
            row2_a = rows2.nth(2)
            row2_a.hover()
            page2.wait_for_timeout(300)
            kebab2_a = row2_a.locator("button.chakra-menu__menu-button").first
            kebab2_a.click()
            page2.wait_for_timeout(1000)
            snap(page2, "dispatch_admin_01_menu_aberto")

            print("   Testando Editar admin via get_by_role...")
            editar2 = page2.get_by_role("menuitem", name="Editar")
            cnt_e2 = editar2.count()
            print(f"   Editar count admin: {cnt_e2}")
            if cnt_e2 > 0:
                nav2 = []
                page2.on("framenavigated", lambda f: nav2.append(f.url) if f == page2.main_frame else None)
                p2_antes = len(ctx2.pages)
                try:
                    editar2.first.click(timeout=5000)
                    print("   Editar admin click OK")
                except Exception as ex:
                    print(f"   Excecao Editar admin: {ex}")
                page2.wait_for_timeout(3000)
                print(f"   URL apos Editar admin: {page2.url}")
                print(f"   Paginas: {p2_antes} -> {len(ctx2.pages)}")
                print(f"   Navegacoes: {nav2}")
                snap(page2, "dispatch_admin_02_pos_editar", full=True)

            # Voltar para lista
            page2.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                       wait_until="domcontentloaded", timeout=25000)
            page2.wait_for_timeout(5000)

            # Testar Visualizar via dispatch
            rows2_b = page2.locator("tbody tr")
            n2b = rows2_b.count()
            print(f"   Linhas admin (volta): {n2b}")

            if n2b >= 3:
                row2_b = rows2_b.nth(2)
                row2_b.hover()
                page2.wait_for_timeout(300)
                kebab2_b = row2_b.locator("button.chakra-menu__menu-button").first
                kebab2_b.click()
                page2.wait_for_timeout(1000)
                snap(page2, "dispatch_admin_03_menu_aberto_2")

                result2 = page2.evaluate("""() => {
                    const items = Array.from(document.querySelectorAll('[role="menuitem"]'));
                    const vis = items.find(el => {
                        const r = el.getBoundingClientRect();
                        return el.innerText && el.innerText.trim() === 'Visualizar' && r.left > 500;
                    });
                    if (!vis) return { found: false };
                    const r = vis.getBoundingClientRect();
                    return {
                        found: true,
                        text: vis.innerText.trim(),
                        left: Math.round(r.left),
                        top: Math.round(r.top),
                        hasOnClick: !!vis.onclick,
                        attributes: Array.from(vis.attributes).map(a => a.name + '=' + a.value)
                    };
                }""")
                print(f"   Visualizar admin info: {result2}")

                if result2.get("found"):
                    nav2b = []
                    page2.on("framenavigated", lambda f: nav2b.append(f.url) if f == page2.main_frame else None)
                    p2b_antes = len(ctx2.pages)
                    page2.evaluate("""() => {
                        const items = Array.from(document.querySelectorAll('[role="menuitem"]'));
                        const vis = items.find(el => {
                            const r = el.getBoundingClientRect();
                            return el.innerText && el.innerText.trim() === 'Visualizar' && r.left > 500;
                        });
                        if (vis) vis.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                    }""")
                    page2.wait_for_timeout(4000)
                    print(f"   URL apos dispatch admin Visualizar: {page2.url}")
                    print(f"   Paginas: {p2b_antes} -> {len(ctx2.pages)}")
                    print(f"   Navegacoes: {nav2b}")
                    snap(page2, "dispatch_admin_04_pos_dispatch", full=True)

                    body2 = page2.inner_text("body")
                    if "Visualizar registro" in body2:
                        print("   ACHOU 'Visualizar registro' no DOM admin!")
                    else:
                        print("   'Visualizar registro' NAO encontrado no DOM admin")

        ctx2.close()
        browser2.close()
        print("\n=== FIM DISPATCH TEST ===")


if __name__ == "__main__":
    main()
