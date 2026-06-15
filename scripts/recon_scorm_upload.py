# -*- coding: utf-8 -*-
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
c = tw.cfg("NOVOEST"); CURSO="807533"
SCORM=str(tw.ROOT/"evidencias"/"_assets_teste"/"scorm_teste.zip")
PASTA=tw.ROOT/"evidencias"/"val_retrabalhos_grupoD"
tid=lambda v:f'[data-test-id="{v}"]'
us=f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"
with tw.sync_playwright() as p:
    b,ctx,page=tw.nova_pagina(p,width=1440,height=900); tw.login(page,c)
    aid=None
    try:
        for _ in range(3):
            page.goto(us,wait_until="domcontentloaded",timeout=45000); tw.dispensar_nps(page)
            try: page.locator(tid("creation-studio-activities-list")).wait_for(state="visible",timeout=15000); break
            except: pass
        page.wait_for_timeout(2500)
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible",timeout=10000); page.wait_for_timeout(800)
        page.locator(tid("creation-studio-type-selector-scorm")).first.click(timeout=8000); page.wait_for_timeout(4000); tw.dispensar_nps(page)
        m=re.search(r"/studio/activities/(\d+)/edit",page.url); aid=m.group(1) if m else None
        page.get_by_text(re.compile(r"^Conteúdo$",re.I)).first.click(timeout=6000,force=True); page.wait_for_timeout(2500)
        # contar inputs file ANTES
        n0=page.locator('input[type=file]').count()
        print(f"inputs file antes do clique: {n0}")
        # clicar 'Enviar arquivo' e ver o que aparece (sem expect_file_chooser)
        page.get_by_role("button",name=re.compile(r"Enviar arquivo",re.I)).first.click(timeout=5000)
        page.wait_for_timeout(2500)
        tw.snap(page,PASTA,"recon-apos-enviar-arquivo",full=True)
        estado=page.evaluate("""()=>{
            const modal=[...document.querySelectorAll('[role=dialog],.chakra-modal__content,[class*=drawer i]')].find(e=>e.offsetParent!==null);
            const inputs=[...document.querySelectorAll('input[type=file]')].map(i=>({accept:i.getAttribute('accept'),vis:i.offsetParent!==null}));
            const dropzoneTxt=[...document.querySelectorAll('*')].filter(e=>e.offsetParent!==null && /arraste|solte|selecione|\.zip|formato/i.test((e.innerText||''))).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim().slice(0,80)).slice(0,5);
            return {modal: modal?(modal.innerText||'').replace(/\s+/g,' ').slice(0,200):null, inputs, dropzoneTxt};
        }""")
        print("ESTADO apos 'Enviar arquivo':", estado)
        # tentar set no primeiro input file (mesmo oculto)
        fis=page.locator('input[type=file]')
        if fis.count():
            fis.first.set_input_files(SCORM); page.wait_for_timeout(6000)
            tw.snap(page,PASTA,"recon-apos-setfile",full=True)
            depois=page.evaluate(r"""()=>{const t=document.body.innerText;return {temNome:/scorm_teste|\.zip/i.test(t), trecho:(t.match(/[^\n]*(scorm_teste|enviando|carregando|sucesso|conclu)[^\n]*/i)||[''])[0].slice(0,100)};}""")
            print("APOS set file:", depois)
    except Exception as e:
        print("ERRO",e)
    finally:
        if aid:
            try:
                page.goto(us,wait_until="domcontentloaded",timeout=30000); page.locator(tid("creation-studio-activities-list")).wait_for(state="visible",timeout=15000); page.wait_for_timeout(2000)
                cd=page.locator(tid(f"creation-studio-activity-card-{aid}")).first; cd.scroll_into_view_if_needed(); cd.click(timeout=8000,force=True); page.wait_for_timeout(2000)
                page.locator(tid("creation-studio-preview-delete")).first.click(timeout=8000,force=True); page.wait_for_timeout(1200)
                page.locator(tid("creation-studio-preview-delete-dialog")).get_by_role("button",name=re.compile("^Excluir",re.I)).first.click(timeout=8000); page.wait_for_timeout(2500); print(f"[cleanup] {aid}")
            except Exception as e: print(f"[cleanup] manual {aid} ({e})")
    ctx.close(); b.close()
