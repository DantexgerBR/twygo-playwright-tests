# -*- coding: utf-8 -*-
"""19851 — recon do form Usuarios>Adicionar no 19653: campos (nome/email/senha) e
opcoes de perfil (lider de equipe?), pra criar o usuario de teste."""
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
        pg.goto(base+f"/o/{c['org_id']}/users", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        log("users url:", pg.url[-30:])
        add = pg.get_by_role("button", name=re.compile("Adicionar|Novo|Criar", re.I))
        if not add.count(): add = pg.get_by_role("link", name=re.compile("Adicionar|Novo", re.I))
        log("botao add:", add.count())
        if add.count(): add.first.click(timeout=4000); pg.wait_for_timeout(2500)
        log("url pos-add:", pg.url[-35:])
        info = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.left>260};
          const inputs=[...document.querySelectorAll('input,select,textarea')].filter(vis).map(e=>({name:e.name||e.id||'',ph:e.placeholder||'',type:e.type||e.tagName}));
          const labels=[...document.querySelectorAll('label,h1,h2,h3,legend')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<40);
          const perfil=[...document.querySelectorAll('option,[role=option],label')].map(e=>(e.innerText||'').trim()).filter(t=>/l[ií]der|aluno|admin|gestor|instrutor|perfil/i.test(t)).slice(0,12);
          const btns=[...document.querySelectorAll('button')].filter(vis).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,10);
          return {inputs:inputs.slice(0,16), labels:[...new Set(labels)].slice(0,18), perfil:[...new Set(perfil)], btns:[...new Set(btns)]};}""")
        log("labels:", info["labels"])
        log("inputs:", info["inputs"])
        log("perfil/opcoes:", info["perfil"])
        log("btns:", info["btns"])
        tw.snap(pg, PASTA, "newuser-form", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "newuser-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
