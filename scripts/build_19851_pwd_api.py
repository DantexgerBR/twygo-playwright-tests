# -*- coding: utf-8 -*-
"""19851 senha via API (headless, sem janela). Tenta endpoints de troca de senha do
usuario 4298356 com 123456. Usa csrf-token do meta. Reporta status de cada tentativa."""
import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

c = tw.cfg("MIGR"); org = c["org_id"]; base = c["base_url"].rstrip("/")
UID = 4298356
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{org}/users", wait_until="domcontentloaded", timeout=30000); pg.wait_for_timeout(2000)
        result = pg.evaluate(r"""async (arg)=>{const[org,uid]=arg;
          const csrf=(document.querySelector('meta[name=csrf-token]')||{}).content||'';
          const tries=[
            ['PUT', '/api/v1/o/'+org+'/users/'+uid, {user:{password:'123456',password_confirmation:'123456'}}],
            ['PUT', '/api/v1/o/'+org+'/professionals/'+uid, {professional:{password:'123456',password_confirmation:'123456'}}],
            ['PATCH', '/api/v1/o/'+org+'/users/'+uid+'/password', {password:'123456',password_confirmation:'123456'}],
            ['POST', '/api/v1/o/'+org+'/users/'+uid+'/change_password', {password:'123456',password_confirmation:'123456'}],
            ['PUT', '/api/v1/o/'+org+'/users/'+uid+'/update_password', {password:'123456',password_confirmation:'123456'}],
          ];
          const out=[];
          for(const [m,url,body] of tries){
            try{const res=await fetch(url,{method:m,headers:{'Content-Type':'application/json','Accept':'application/json','X-CSRF-Token':csrf},credentials:'include',body:JSON.stringify(body)});
              const t=await res.text();out.push({m,url:url.split('/o/')[1],status:res.status,head:t.slice(0,80)});}
            catch(e){out.push({m,url,err:String(e).slice(0,50)});}
          }
          return {csrf:csrf?'present':'none', out};
        }""", [org, UID])
        log("csrf:", result["csrf"])
        for r in result["out"]: log("  ", r.get("m"), r.get("url"), "->", r.get("status"), "|", r.get("head") or r.get("err"))
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
