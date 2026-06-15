# -*- coding: utf-8 -*-
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
c=tw.cfg("NOVOEST"); CURSO="807533"; PASTA=tw.ROOT/"evidencias"/"val_retrabalhos_marca"
tid=lambda v:f'[data-test-id="{v}"]'; us=f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"
with tw.sync_playwright() as p:
    b,ctx,page=tw.nova_pagina(p,width=1440,height=900); tw.login(page,c); aid=None
    try:
        for _ in range(3):
            page.goto(us,wait_until="domcontentloaded",timeout=45000); tw.dispensar_nps(page)
            try: page.locator(tid("creation-studio-activities-list")).wait_for(state="visible",timeout=15000); break
            except: pass
        page.wait_for_timeout(2500)
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible",timeout=10000); page.wait_for_timeout(800)
        page.locator(tid("creation-studio-type-selector-video")).first.click(timeout=8000); page.wait_for_timeout(4000); tw.dispensar_nps(page)
        m=re.search(r"/studio/activities/(\d+)/edit",page.url); aid=m.group(1) if m else None
        # varrer Dados e Conteúdo por 'marca d'agua'
        achados={}
        for aba in ["Dados","Conteúdo"]:
            try: page.get_by_text(re.compile(rf"^{aba}$",re.I)).first.click(timeout=4000,force=True); page.wait_for_timeout(2500)
            except: pass
            body=page.evaluate("()=>document.body.innerText")
            achados[aba]=bool(re.search(r"marca d.{0,3}gua",body,re.I))
        print(f"[NOVOEST video] checkbox 'marca d'agua' em: {achados}")
        tw.snap(page,PASTA,"19815-novoest-video",full=True)
    except Exception as e: print("ERRO",e)
    finally:
        if aid:
            try:
                page.goto(us,wait_until="domcontentloaded",timeout=30000); page.locator(tid("creation-studio-activities-list")).wait_for(state="visible",timeout=15000); page.wait_for_timeout(2000)
                cd=page.locator(tid(f"creation-studio-activity-card-{aid}")).first; cd.scroll_into_view_if_needed(); cd.click(timeout=8000,force=True); page.wait_for_timeout(2000)
                page.locator(tid("creation-studio-preview-delete")).first.click(timeout=8000,force=True); page.wait_for_timeout(1200)
                page.locator(tid("creation-studio-preview-delete-dialog")).get_by_role("button",name=re.compile("^Excluir",re.I)).first.click(timeout=8000); page.wait_for_timeout(2500); print(f"[cleanup] {aid}")
            except Exception as e: print(f"[cleanup] manual {aid} ({e})")
    ctx.close(); b.close()
