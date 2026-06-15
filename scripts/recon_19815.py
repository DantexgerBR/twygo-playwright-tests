# -*- coding: utf-8 -*-
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
c=tw.cfg("MIGR"); PASTA=tw.ROOT/"evidencias"/"val_retrabalhos_marca"
tid=lambda v:f'[data-test-id="{v}"]'
with tw.sync_playwright() as p:
    b,ctx,page=tw.nova_pagina(p,width=1440,height=900); tw.login(page,c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin",wait_until="domcontentloaded",timeout=45000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    # abrir primeiro curso pelo nome
    page.get_by_text("Curso Padrão",exact=True).first.click(timeout=8000,force=True)
    page.wait_for_timeout(5000); tw.dispensar_nps(page)
    print("url apos abrir curso:",page.url)
    tw.snap(page,PASTA,"19815-curso-aberto",full=True)
    # tem studio (flag on) ou legacy?
    studio=page.evaluate("()=>!!document.querySelector('[data-test-id=creation-studio-activities-list]')")
    abas=page.evaluate("""()=>[...document.querySelectorAll('[role=tab],p,span,button')].filter(e=>e.offsetParent!==null && /^(Identificação|Modelo|Atividades|Acesso|Conteúdo)$/.test((e.innerText||'').trim())).map(e=>e.innerText.trim())""")
    print("studio?",studio,"| abas:",sorted(set(abas)))
    # procurar atividade de vídeo e texto 'marca'
    page.goto(page.url.split('?')[0]+"?tab=studio" if studio else page.url,wait_until="domcontentloaded",timeout=30000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    body=page.evaluate("()=>document.body.innerText")
    print("tem 'marca' no body?", bool(re.search(r"marca d.{0,3}gua",body,re.I)))
    tw.snap(page,PASTA,"19815-explorar",full=True)
    ctx.close(); b.close()
