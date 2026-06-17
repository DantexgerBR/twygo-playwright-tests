# -*- coding: utf-8 -*-
"""20074 (tooltip nos textos de status dos 3 dashboards) + 20096 S1 (títulos em
negrito) no Dashboard geral da Continuidade (37048). Mede font-weight + tooltip."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_lote_37048"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base + f"/o/{c['org_id']}/succession_dashboards", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(4000)
        tw.snap(pg, PASTA, "20096-dashboard", full=True)
        # 20096 S1: font-weight dos títulos dos cards
        pesos = pg.evaluate(r"""()=>{const alvos=['Risco atual','Projeção em 6 meses','Projeção em 12 meses','Projeção de risco','Áreas com maior risco','Funções com maior risco'];
          return alvos.map(t=>{const e=[...document.querySelectorAll('h1,h2,h3,h4,p,span,div')].find(x=>(x.innerText||'').trim()===t);
            return {t, fw: e?getComputedStyle(e).fontWeight:'(não achou)'};});}""")
        log("[20096 S1] font-weight títulos:")
        for x in pesos: log(f"    {x['t']!r}: {x['fw']}")
        # 20074: tooltip nos badges de status (Baixo/Médio/Alto)
        badge = pg.get_by_text(re.compile(r"^(Baixo|M[ée]dio|Alto|Cr[íi]tico)$", re.I)).first
        info = "sem badge"
        if badge.count():
            attrs = pg.evaluate(r"""()=>{const e=[...document.querySelectorAll('*')].find(x=>/^(Baixo|M[ée]dio|Alto|Cr[íi]tico)$/i.test((x.innerText||'').trim())&&x.children.length===0);
              if(!e)return null;return {title:e.getAttribute('title')||e.parentElement.getAttribute('title')||'', aria:e.getAttribute('aria-label')||'', dataTip:e.getAttribute('data-tooltip')||e.closest('[data-tooltip],[title]')?'sim':''};}""")
            badge.hover(); pg.wait_for_timeout(1200)
            tip = pg.evaluate(r"""()=>[...document.querySelectorAll('[role=tooltip],[class*=tooltip i],[class*=Tooltip]')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,3)""")
            info = {"attrs": attrs, "tooltip_hover": tip}
        log(f"[20074] status badge tooltip: {info}")
        tw.snap(pg, PASTA, "20074-hover-status", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "dash-erro", full=True)
        except Exception: pass
    finally:
        ctx.close(); b.close()
