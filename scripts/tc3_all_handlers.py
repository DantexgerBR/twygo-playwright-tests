"""tc3_all_handlers.py — Lista todos os event handlers no fiber chain do menuitem."""
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

            all_handlers = page.evaluate("""() => {
                const ms = Array.from(document.querySelectorAll('[role=menu]')).filter(m => {
                    const c = getComputedStyle(m);
                    return c.visibility === 'visible' && parseFloat(c.opacity) > 0.5;
                });
                const m = ms[ms.length - 1];
                if (!m) return [{error: 'sem menu'}];

                const item = Array.from(m.querySelectorAll('[role=menuitem]')).find(
                    e => /alterar senha/i.test(e.innerText || '')
                );
                if (!item) return [{error: 'sem item'}];

                const fk = Object.keys(item).find(k =>
                    k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance')
                );
                if (!fk) return [{error: 'sem fiber', keys: Object.keys(item).filter(k=>k.startsWith('__'))}];

                let f = item[fk];
                const result = [];
                let depth = 0;

                while (f && depth < 30) {
                    const mp = f.memoizedProps || {};
                    const keys = Object.keys(mp).filter(k => typeof mp[k] === 'function');
                    if (keys.length > 0) {
                        const typeName = typeof f.type === 'string' ? f.type :
                            (f.type && (f.type.displayName || f.type.name)) || '?';
                        result.push({depth, type: typeName, handlers: keys});
                    }
                    f = f.return;
                    depth++;
                }
                return result;
            }""")

            log("Handlers no fiber chain do menuitem 'Alterar senha':")
            for h in all_handlers[:20]:
                if "error" in h:
                    log(f"  ERRO: {h}")
                else:
                    log(f"  depth={h['depth']} type={h['type']!r}: {h['handlers']}")

            # Tenta chamar especificamente onMouseDown ou onMouseUp
            log("\nTentando onMouseDown nos primeiros 5 levels...")
            for depth in range(5):
                result = page.evaluate(
                    """(args) => {
                        const {rid_search, targetDepth, evName} = args;
                        const ms = Array.from(document.querySelectorAll('[role=menu]')).filter(m => {
                            const c = getComputedStyle(m);
                            return c.visibility === 'visible' && parseFloat(c.opacity) > 0.5;
                        });
                        const m = ms[ms.length - 1];
                        if (!m) return 'sem menu visivel';
                        const item = Array.from(m.querySelectorAll('[role=menuitem]')).find(
                            e => /alterar senha/i.test(e.innerText || '')
                        );
                        if (!item) return 'sem item';
                        const fk = Object.keys(item).find(k =>
                            k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance')
                        );
                        if (!fk) return 'sem fiber';
                        let f = item[fk];
                        let d = 0;
                        while (f && d < targetDepth) { f = f.return; d++; }
                        if (!f) return `sem fiber em depth ${targetDepth}`;
                        const mp = f.memoizedProps || {};
                        const handler = mp[evName];
                        if (!handler) return `sem ${evName} em depth ${targetDepth}`;
                        try {
                            handler({preventDefault:()=>{}, stopPropagation:()=>{}, target: item, currentTarget: item});
                            return `${evName} chamado em depth ${targetDepth}`;
                        } catch(e) {
                            return `${evName} erro em depth ${targetDepth}: ${e.message}`;
                        }
                    }""",
                    {"rid_search": "Alterar senha", "targetDepth": depth, "evName": "onMouseDown"}
                )
                log(f"  depth={depth}: {result!r}")
                page.wait_for_timeout(500)

                campos_pw = page.locator("input[type='password']").count()
                if campos_pw > 0:
                    log(f"  *** MODAL ABERTO com onMouseDown na depth {depth}! ***")
                    break

        finally:
            ctx.close()
            browser.close()


if __name__ == "__main__":
    main()
