# -*- coding: utf-8 -*-
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
c = tw.cfg("NOVOEST")
PASTA = tw.ROOT / "evidencias" / "qualidade_ia_cleanup"
with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    page.get_by_placeholder(re.compile("Pesquise", re.I)).first.fill("Domine SQL Básico")
    page.wait_for_timeout(4000)
    page.get_by_text("more_vert", exact=True).last.click(timeout=6000, force=True)
    page.wait_for_timeout(1200)
    ok = tw.click_menuitem(page, "Excluir")
    print("click_menuitem Excluir:", ok)
    page.wait_for_timeout(2500)
    tw.snap(page, PASTA, "confirm2")
    btns = page.evaluate("""()=>[...document.querySelectorAll('button')].filter(b=>b.offsetParent!==null).map(b=>(b.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean)""")
    print("BOTOES visíveis:", btns)
    ctx.close(); browser.close()
