# -*- coding: utf-8 -*-
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
c=tw.cfg("MIGR")
PASTA=tw.ROOT/"evidencias"/"val_retrabalhos_marca"
with tw.sync_playwright() as p:
    b,ctx,page=tw.nova_pagina(p,width=1440,height=900); tw.login(page,c)
    print("logado:",page.url)
    # listar conteúdos
    page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin",wait_until="domcontentloaded",timeout=45000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    tw.snap(page,PASTA,"migr-conteudos")
    cursos=page.evaluate(r"""()=>[...document.querySelectorAll('tr,div')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/curso|v[ií]deo|aula/i.test(t)&&t.length<80).slice(0,15)""")
    print("amostra linhas:",cursos[:10])
    # flag novo_estudio? procurar aba Atividades/Estúdio
    body=page.evaluate("()=>document.body.innerText.slice(0,200)")
    print("body:",body[:120])
    ctx.close(); b.close()
