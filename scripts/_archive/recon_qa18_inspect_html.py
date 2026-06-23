"""
Inspecao do HTML do item Visualizar no menu aberto.
Compara com Editar para identificar diferenca no DOM.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"

PASTA = Path(__file__).resolve().parents[1] / "evidencias" / "registros-f2-qa18"
PASTA.mkdir(parents=True, exist_ok=True)


def snap(page, nome):
    fp = PASTA / f"{nome}.png"
    page.screenshot(path=str(fp))
    print(f"   [snap] {fp.name}")


def main():
    with tw.sync_playwright() as p:
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
        page.wait_for_timeout(1200)
        snap(page, "inspect_01_menu_aberto")

        # Inspecionar TODOS os elementos com texto matching menuitem names
        info = page.evaluate("""() => {
            // Buscar todos elementos com texto dos itens do menu
            const texts = ['Editar', 'Excluir', 'Visualizar', 'Evidencias', 'Historico'];
            const results = [];

            // Busca por role menuitem
            const byRole = Array.from(document.querySelectorAll('[role="menuitem"]'));
            console.log('By role menuitem count:', byRole.length);

            // Busca por class menuitem
            const byClass = Array.from(document.querySelectorAll('[class*="menuitem"]'));

            // Busca por button e li na area do menu
            const allMenuLists = Array.from(document.querySelectorAll('[class*="menu__menu-list"]'));

            const menuListItems = [];
            for (const list of allMenuLists) {
                const r = list.getBoundingClientRect();
                if (r.width > 0 && r.left > 100) {
                    // Este e o menu aberto
                    const children = Array.from(list.querySelectorAll('*'));
                    for (const child of children) {
                        const cr = child.getBoundingClientRect();
                        if (cr.width > 0 && cr.height > 0) {
                            menuListItems.push({
                                tag: child.tagName,
                                role: child.getAttribute('role'),
                                text: child.innerText ? child.innerText.trim().slice(0, 30) : '',
                                className: child.className ? child.className.toString().slice(0, 80) : '',
                                left: Math.round(cr.left),
                                top: Math.round(cr.top),
                                outerHTML: child.outerHTML ? child.outerHTML.slice(0, 300) : ''
                            });
                        }
                    }
                    break;
                }
            }

            return {
                byRoleCount: byRole.length,
                byRoleSamples: byRole.slice(0, 10).map(el => ({
                    text: el.innerText ? el.innerText.trim().slice(0,30) : '',
                    tag: el.tagName,
                    className: el.className ? el.className.toString().slice(0,60) : ''
                })),
                menuListCount: allMenuLists.length,
                menuListItems: menuListItems.slice(0, 30)
            };
        }""")

        print(f"\n   byRole count: {info['byRoleCount']}")
        print(f"   byRole samples:")
        for s in info['byRoleSamples']:
            print(f"   - '{s['text']}' tag={s['tag']} class={s['className']}")
        print(f"\n   menuList count: {info['menuListCount']}")
        print(f"   menuList items ({len(info['menuListItems'])}):")
        for item in info['menuListItems']:
            print(f"   - tag={item['tag']} role={item['role']} text='{item['text']}' left={item['left']} top={item['top']}")
            if item.get('outerHTML'):
                print(f"     HTML: {item['outerHTML'][:200]}")

        # Busca direta pelos nomes dos itens
        items_detail = page.evaluate("""() => {
            // Encontrar o dropdown aberto
            const lists = Array.from(document.querySelectorAll('ul[class*="menu"]'));
            const openList = lists.find(ul => {
                const r = ul.getBoundingClientRect();
                return r.width > 0 && r.left > 100;
            });
            if (!openList) return { error: 'no open list' };

            // Pegar todos children com texto
            const allChildren = Array.from(openList.querySelectorAll('button, li, a, [role]'));
            return allChildren.map(el => {
                const r = el.getBoundingClientRect();
                return {
                    tag: el.tagName,
                    role: el.getAttribute('role'),
                    text: el.innerText ? el.innerText.trim() : '',
                    disabled: el.hasAttribute('disabled'),
                    ariaDisabled: el.getAttribute('aria-disabled'),
                    type: el.getAttribute('type'),
                    href: el.getAttribute('href'),
                    left: Math.round(r.left),
                    top: Math.round(r.top),
                    width: Math.round(r.width),
                    height: Math.round(r.height)
                };
            }).filter(i => i.width > 0 && i.height > 0 && i.text);
        }""")

        print(f"\n   Items no menu aberto (ul[class*='menu']):")
        if isinstance(items_detail, dict) and 'error' in items_detail:
            print(f"   ERRO: {items_detail}")
        else:
            for item in items_detail:
                print(f"   tag={item['tag']} role={item['role']} text='{item['text']}' left={item['left']} top={item['top']} disabled={item['disabled']}")

        browser.close()
        print("\n=== FIM INSPECT ===")


if __name__ == "__main__":
    main()
