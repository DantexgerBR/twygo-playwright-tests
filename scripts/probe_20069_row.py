# -*- coding: utf-8 -*-
"""Probe — detalhes dos elementos clicaveis da 1a linha de Analise individual (lapis)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    pg.goto(base+f"/o/{c['org_id']}/succession_people_analysis", wait_until="domcontentloaded", timeout=30000)
    tw.dispensar_nps(pg); pg.wait_for_timeout(3500)
    det = pg.evaluate(r"""()=>{const tr=document.querySelector('tbody tr');
      const cells=[...tr.querySelectorAll('a,button,[role=button],svg')].filter(e=>e.getBoundingClientRect().width>0);
      return cells.map(e=>({tag:e.tagName,href:(e.getAttribute&&e.getAttribute('href'))||'',aria:(e.getAttribute&&e.getAttribute('aria-label'))||'',cls:(e.className||'').toString().slice(0,30),x:Math.round(e.getBoundingClientRect().left)}));}""")
    for d in det: print(d, flush=True)
    # tenta clicar o ultimo (lapis) e ver se muda url ou abre drawer/modal
    print("--- clicando lapis ---", flush=True)
    tr = pg.locator("tbody tr").first
    last = tr.locator("a,button,[role=button]").last
    print("last count em a/button:", tr.locator("a,button,[role=button]").count(), flush=True)
    url0 = pg.url
    try:
        last.click(timeout=4000); pg.wait_for_timeout(2500)
    except Exception as ex:
        print("click falhou:", str(ex)[:80], flush=True)
    print("url antes:", url0[-40:], "| depois:", pg.url[-40:], flush=True)
    modal = pg.evaluate(r"""()=>{const m=document.querySelector('.chakra-modal__content,[role=dialog]');return m?(m.innerText||'').slice(0,200).replace(/\n/g,' | '):'(sem modal)'}""")
    print("modal/dialog:", modal, flush=True)
    tw.snap(pg, tw.ROOT/"evidencias"/"retrabalho_20069_email", "20-pos-lapis", full=True)
    ctx.close(); b.close()
