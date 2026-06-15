# -*- coding: utf-8 -*-
import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
c=tw.cfg("NOVOEST"); CURSO="807533"
VIDEO=str(tw.ROOT/"evidencias"/"_assets_teste"/"video_teste_5s.mp4")
TIT="QA20015 Video Recap"; PASTA=tw.ROOT/"evidencias"/"val_retrabalhos_grupoD"
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
        try: page.locator('input[name="title"]:visible').first.fill(TIT)
        except: pass
        try:
            sw=page.locator("input[type=checkbox]").first
            if sw.count() and not sw.is_checked(): page.get_by_text("Liberado",exact=False).first.click(timeout=3000)
        except: pass
        page.get_by_text(re.compile(r"^Conteúdo$",re.I)).first.click(timeout=6000,force=True); page.wait_for_timeout(2000)
        try: page.get_by_role("button",name=re.compile(r"Enviar arquivo|upload",re.I)).first.click(timeout=5000); page.wait_for_timeout(2000)
        except: pass
        page.locator('input[type=file]').last.set_input_files(VIDEO); page.wait_for_timeout(3000)
        env=page.get_by_role("button",name=re.compile(r"^Enviar$",re.I)).first
        if env.count() and env.is_enabled(): env.click(timeout=6000)
        page.wait_for_timeout(8000); tw.dispensar_nps(page)
        sv=page.get_by_role("button",name=re.compile(r"^Salvar$",re.I)).first
        if sv.count() and sv.is_visible(): sv.click(timeout=8000); page.wait_for_timeout(6000)
        # poll ate 3min, mantendo o card de video selecionado
        ok=False
        for i in range(9):
            page.goto(us,wait_until="domcontentloaded",timeout=30000); tw.dispensar_nps(page)
            try: page.locator(tid("creation-studio-activities-list")).wait_for(state="visible",timeout=15000)
            except: pass
            page.wait_for_timeout(2000)
            cd=page.locator(tid(f"creation-studio-activity-card-{aid}")).first
            cd.scroll_into_view_if_needed(); cd.click(timeout=8000,force=True); page.wait_for_timeout(5000)
            st=page.evaluate("""()=>{const prev=document.querySelector('[data-test-id=creation-studio-preview]')||document.querySelector('main');
                const txt=(prev?prev.innerText:'').replace(/\s+/g,' ');
                const v=prev?prev.querySelector('video'):null;
                return {proc:/em processamento|logo estará/i.test(txt), temVideoNoPreview:!!v, semConteudo:/Não há conteúdo/i.test(txt)};}""")
            print(f"[poll {i}] {st}")
            if st["temVideoNoPreview"] and not st["proc"]:
                ok=True; tw.snap(page,PASTA,"vid-recap-player"); break
            page.wait_for_timeout(18000)
        print(f"=> 20015 RECAP: {'PASSOU (player no preview)' if ok else 'INCONCLUSIVO/FALHOU'}")
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
