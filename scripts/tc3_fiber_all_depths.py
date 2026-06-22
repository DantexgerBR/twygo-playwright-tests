"""tc3_fiber_all_depths.py — Tenta onClick em todas as depths do fiber chain."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa11"
EVID.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg, flush=True)


def abrir_kebab_e_pegar_id(page):
    busca = page.locator("input[placeholder='Pesquise aqui']").first
    if busca.is_visible(timeout=2000):
        busca.fill("qa11tc342588")
        page.wait_for_timeout(1500)

    row = page.locator("tr").filter(has_text="qa11tc342588@twygotest.com").first
    kebab = row.locator("button").last
    kebab.click(force=True)
    page.wait_for_timeout(1200)

    return page.evaluate(
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

            # Tenta cada depth separadamente, reabrindo o kebab entre cada tentativa
            for target_depth in [1, 2, 3, 4]:
                log(f"\n=== Tentando onClick na depth {target_depth} ===")
                id_alterar = abrir_kebab_e_pegar_id(page)
                if not id_alterar:
                    log("  ID nao encontrado")
                    continue

                result = page.evaluate(
                    """(args) => {
                        const {rid, targetDepth} = args;
                        const el = document.getElementById(rid);
                        if (!el) return 'nao encontrado';
                        const fk = Object.keys(el).find(k =>
                            k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance')
                        );
                        if (!fk) return 'sem fiber';
                        let f = el[fk];
                        let depth = 0;
                        // Navega ate a depth alvo
                        while (f && depth < targetDepth) {
                            f = f.return;
                            depth++;
                        }
                        if (!f) return `sem fiber em depth ${targetDepth}`;
                        const mp = f.memoizedProps || {};
                        const typeName = typeof f.type === 'string' ? f.type :
                            (f.type && (f.type.displayName || f.type.name)) || 'unknown';
                        if (!mp.onClick) return `sem onClick em depth ${targetDepth}, type=${typeName}`;
                        try {
                            mp.onClick({
                                preventDefault: () => {},
                                stopPropagation: () => {},
                                target: el,
                                currentTarget: el
                            });
                            return `onClick chamado em depth ${targetDepth}, type=${typeName}`;
                        } catch(e) {
                            return `onClick erro em depth ${targetDepth}: ${e.message}`;
                        }
                    }""",
                    {"rid": id_alterar, "targetDepth": target_depth}
                )
                log(f"  Resultado: {result!r}")
                page.wait_for_timeout(1500)

                campos_pw = page.locator("input[type='password']").count()
                menus = page.evaluate(
                    "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
                )
                log(f"  Campos password: {campos_pw}, menus: {menus}")
                tw.snap(page, EVID, f"tc3_fiber_depth{target_depth}")

                if campos_pw > 0:
                    log(f"  *** MODAL ABERTO NA DEPTH {target_depth}! ***")
                    # Preenche e salva
                    campo = page.locator("input[type='password']").first
                    campo.fill("twygoqa2026")
                    page.wait_for_timeout(500)
                    btn = page.locator("button").filter(
                        has_text=__import__("re").compile(r"Salvar|Confirmar|OK", __import__("re").I)
                    ).last
                    btn.click()
                    page.wait_for_timeout(2000)
                    tw.snap(page, EVID, "fechamento_tc3_senha_definida")
                    log("  Senha definida!")
                    break

                # Fecha o menu se ainda aberto para a proxima tentativa
                if menus > 0:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)

        finally:
            ctx.close()
            browser.close()


if __name__ == "__main__":
    main()
