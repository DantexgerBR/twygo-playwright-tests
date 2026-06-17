# -*- coding: utf-8 -*-
"""19851 — identifica o usuario LIDER no 19653 (gestor da area Liderança / 'Lider do
Jad') via API de usuarios, pra resetar senha e logar como ele e testar o drawer."""
import json, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

c = tw.cfg("MIGR"); org = c["org_id"]; base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{org}/organization_chart", wait_until="domcontentloaded", timeout=25000); pg.wait_for_timeout(2000)
        # busca usuarios por termos de lider
        for termo in ["lider", "jad", "aluno001"]:
            data = pg.evaluate(r"""async (arg)=>{const[org,q]=arg;try{const res=await fetch('/api/v1/o/'+org+'/users?search='+q+'&page=1&per_page=10',{headers:{'Accept':'application/json'}});return await res.json();}catch(e){return{err:String(e)}}}""", [org, termo])
            try:
                users = data.get("data", {}).get("users") or data.get("users") or []
                log(f"[busca '{termo}'] {len(users)} users:")
                for u in users[:6]:
                    log("   ", u.get("id"), "|", u.get("full_name") or u.get("name"), "|", u.get("email"), "| perfil:", u.get("profile") or u.get("role") or u.get("kind"))
            except Exception as ex:
                log(f"[busca '{termo}'] parse erro: {str(ex)[:50]} | raw: {json.dumps(data)[:200]}")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
