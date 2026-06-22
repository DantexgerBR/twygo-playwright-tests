"""tc3_fiber_inspect.py — Inspeciona React fiber handlers do menuitem Alterar Senha."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"


def log(msg):
    print(msg, flush=True)


def main():
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
            page.fill("#user_email", "dante.tavares@twygo.com")
            page.fill("#user_password", "123456")
            page.click("#user_submit")
            page.wait_for_timeout(3000)
            page.goto(f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)

            busca = page.locator("input[placeholder='Pesquise aqui']").first
            if busca.is_visible(timeout=2000):
                busca.fill("qa11tc342588")
                page.wait_for_timeout(1500)

            row = page.locator("tr").filter(has_text="qa11tc342588@twygotest.com").first
            kebab = row.locator("button").last
            kebab.click(force=True)
            page.wait_for_timeout(1200)

            id_alterar = page.evaluate(
                """(pal) => {
                    const ms = Array.from(document.querySelectorAll('[role=menu]')).filter(m => {
                        const c = getComputedStyle(m);
                        return c.visibility === 'visible' && parseFloat(c.opacity) > 0.5;
                    });
                    const m = ms[ms.length - 1];
                    if (!m) return '';
                    const it = Array.from(m.querySelectorAll('[role=menuitem]')).find(
                        e => new RegExp(pal, 'i').test(e.innerText || '')
                    );
                    return it ? it.id : '';
                }""",
                "Alterar senha"
            )
            log(f"ID menuitem: {id_alterar!r}")

            # Inspeciona React fiber handlers
            fiber_handlers = page.evaluate(
                """(rid) => {
                    const el = document.getElementById(rid);
                    if (!el) return [{error: 'nao encontrado'}];
                    const fk = Object.keys(el).find(k =>
                        k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance')
                    );
                    if (!fk) return [{error: 'sem fiber key'}];
                    let f = el[fk];
                    const handlers = [];
                    let depth = 0;
                    while (f && depth < 25) {
                        const mp = f.memoizedProps || {};
                        const keys = Object.keys(mp).filter(k =>
                            k.startsWith('on') && typeof mp[k] === 'function'
                        );
                        if (keys.length > 0) {
                            const typeName = typeof f.type === 'string' ? f.type :
                                (f.type && (f.type.displayName || f.type.name)) || 'unknown';
                            handlers.push({depth, type: typeName, events: keys});
                        }
                        f = f.return;
                        depth++;
                    }
                    return handlers;
                }""",
                id_alterar
            )
            log(f"Fiber handlers ({len(fiber_handlers)}):")
            for h in fiber_handlers:
                log(f"  depth={h.get('depth')} type={h.get('type')!r} events={h.get('events')}")

            # Tenta chamar o onClick do nivel mais proximo
            result = page.evaluate(
                """(rid) => {
                    const el = document.getElementById(rid);
                    if (!el) return 'nao encontrado';
                    const fk = Object.keys(el).find(k =>
                        k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance')
                    );
                    if (!fk) return 'sem fiber';
                    let f = el[fk];
                    let depth = 0;
                    while (f && depth < 25) {
                        const mp = f.memoizedProps || {};
                        if (mp.onClick && typeof mp.onClick === 'function') {
                            try {
                                mp.onClick({
                                    preventDefault: () => {},
                                    stopPropagation: () => {},
                                    target: el,
                                    currentTarget: el
                                });
                                return `onClick chamado na depth ${depth}, type=${typeof f.type === 'string' ? f.type : (f.type && f.type.name) || 'unknown'}`;
                            } catch(e) {
                                return `onClick erro na depth ${depth}: ${e.message}`;
                            }
                        }
                        f = f.return;
                        depth++;
                    }
                    return 'onClick nao encontrado em 25 levels';
                }""",
                id_alterar
            )
            log(f"\nResultado onClick fiber: {result!r}")
            page.wait_for_timeout(2000)

            # Verifica se modal abriu
            campos_pw = page.locator("input[type='password']").count()
            menus = page.evaluate(
                "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
            )
            log(f"Campos password: {campos_pw}, menus abertos: {menus}")

        finally:
            ctx.close()
            browser.close()


if __name__ == "__main__":
    main()
