# -*- coding: utf-8 -*-
"""20074 — hover robusto nos badges de status (Alto/Crítico) do Dashboard geral 19653.
Usa locator.hover() real + espera + detecta QUALQUER portal/tooltip que apareca.
Tambem testa badges nas tabelas Areas/Funcoes e o help-icon."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20074_20096"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

def portais(pg):
    return pg.evaluate(r"""()=>{const sel='[role=tooltip],[class*=tooltip i],[class*=Tooltip],.chakra-tooltip,[data-popper-placement],[id*=popover],[class*=popover i]';
      return [...document.querySelectorAll(sel)].filter(e=>e.offsetParent!==null&&(e.innerText||'').trim()).map(e=>(e.innerText||'').trim()).slice(0,4);}""")

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/succession_dashboards", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(4000)
        achou = False
        # badges Alto/Crítico/Médio/Baixo (qualquer um visivel)
        for txt in ("Alto", "Crítico", "Médio", "Baixo"):
            loc = pg.get_by_text(re.compile(rf"^{txt}$")).filter(visible=True)
            n = loc.count()
            if not n: continue
            for i in range(min(n, 2)):
                try:
                    loc.nth(i).hover(timeout=3000); pg.wait_for_timeout(1500)
                    tip = portais(pg)
                    log(f"hover badge '{txt}' #{i} -> portais={tip}")
                    if tip: achou = True; tw.snap(pg, PASTA, f"hov-{txt}-{i}")
                except Exception as ex:
                    log(f"hover '{txt}' #{i} erro: {str(ex)[:50]}")
        # tambem: passar o mouse nos valores de risco "100%" nas tabelas
        risco = pg.get_by_text(re.compile(r"^100%$")).filter(visible=True)
        if risco.count():
            risco.first.hover(timeout=3000); pg.wait_for_timeout(1500)
            log(f"hover '100%' -> portais={portais(pg)}")
        tw.snap(pg, PASTA, "20074-final", full=True)
        log(f"\n>> 20074 algum tooltip/portal nos status: {achou}")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
