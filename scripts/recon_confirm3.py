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
    # menuitem Excluir: clicar no centro via mouse
    item = page.get_by_role("menuitem", name=re.compile("Excluir", re.I)).first
    box = item.bounding_box()
    print("box Excluir:", box)
    if box:
        page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2)
    page.wait_for_timeout(3000)
    tw.snap(page, PASTA, "confirm3")
    # procurar qualquer modal/alertdialog e seus botões
    modal = page.evaluate("""()=>{
        const ds=[...document.querySelectorAll('[role=alertdialog],[role=dialog],.chakra-modal__content,.chakra-alert-dialog__content')].filter(e=>e.offsetParent!==null);
        return ds.map(d=>({txt:(d.innerText||'').replace(/\s+/g,' ').slice(0,250),
            botoes:[...d.querySelectorAll('button')].map(b=>(b.innerText||'').trim()).filter(Boolean)}));
    }""")
    print("MODAIS:", modal)
    ctx.close(); browser.close()
