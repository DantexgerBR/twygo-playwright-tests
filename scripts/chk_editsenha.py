import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
c = tw.cfg("MIGR"); org = c["org_id"]; base = c["base_url"].rstrip("/")
with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    pg.goto(base+f"/o/{org}/users/4298356/edit", wait_until="domcontentloaded", timeout=30000)
    tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
    # procura qualquer mencao de senha/password na pagina (botoes, labels, inputs)
    r = pg.evaluate(r"""()=>{const txt=document.body.innerText;
      const senhaEls=[...document.querySelectorAll('button,a,label,input')].filter(e=>/senha|password/i.test((e.innerText||'')+' '+(e.name||'')+' '+(e.placeholder||''))).map(e=>(e.tagName+': '+((e.innerText||e.name||e.placeholder||'')).replace(/\s+/g,' ').trim()).slice(0,50));
      const temSenha=/senha/i.test(txt);
      return {temSenha, senhaEls:[...new Set(senhaEls)].slice(0,10)};}""")
    print("pagina menciona senha:", r["temSenha"], flush=True)
    print("elementos senha:", r["senhaEls"], flush=True)
    ctx.close(); b.close()
