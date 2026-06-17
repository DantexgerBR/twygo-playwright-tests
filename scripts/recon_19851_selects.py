# -*- coding: utf-8 -*-
"""19851 — le as opcoes dos <select> do drawer 'Adicionar acao' (admin, 19653) direto
do DOM. Confirma se Funcao vinculada / Iniciativa populam (baseline antes do teste lider)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider_acoes"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/succession_actions", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        pg.get_by_role("button", name=re.compile("Adicionar", re.I)).first.click(timeout=5000); pg.wait_for_timeout(2000)
        info = pg.evaluate(r"""()=>{const drw=document.querySelector('.chakra-modal__content,[role=dialog]')||document;
          const sels=[...drw.querySelectorAll('select')].filter(e=>e.getBoundingClientRect().width>0).map(s=>({
            name:s.name||s.id||'', n:s.options.length, opts:[...s.options].map(o=>o.text.trim()).slice(0,8)}));
          // tambem react-select / combobox (nao-nativos)
          const combos=[...drw.querySelectorAll('[class*=select__control],[role=combobox]')].length;
          return {sels, combos};}""")
        log("selects nativos no drawer:")
        for s in info["sels"]: log(f"   {s['name']!r}: {s['n']} opcoes -> {s['opts']}")
        log("combos nao-nativos:", info["combos"])
        tw.snap(pg, PASTA, "admin-selects", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
