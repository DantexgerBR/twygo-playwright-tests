# -*- coding: utf-8 -*-
"""19851 — procura lideres (responsaveis) ja configurados no 19653: pessoas com
'responsavel' setado + a funcao vinculada. Esse lider vira o usuario de teste."""
import json, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

c = tw.cfg("MIGR"); org = c["org_id"]; base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{org}/succession_people_analysis", wait_until="domcontentloaded", timeout=25000); tw.dispensar_nps(pg); pg.wait_for_timeout(2000)
        # API de pessoas: procura quem tem responsavel + funcoes
        data = pg.evaluate(r"""async (org)=>{try{const res=await fetch('/api/v1/o/'+org+'/succession_people_analysis?page=1&per_page=50',{headers:{'Accept':'application/json'}});const j=await res.json();return j;}catch(e){return {err:String(e)};}}""", org)
        txt = json.dumps(data)
        log("keys:", list(data.get("data", data).keys()) if isinstance(data, dict) else "?")
        # tenta extrair pessoas com responsavel
        import re
        resp = re.findall(r'"responsible[^"]*"\s*:\s*({[^}]*}|null|"[^"]*")', txt)
        log("amostra responsible:", resp[:5])
        # conta quantas pessoas tem funcoes
        funcs = txt.count('"role"') + txt.count('"organization_chart_role"')
        log("mencoes de role/funcao:", funcs)
        # dump cru parcial pra ver estrutura
        log("trecho:", txt[:600])
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
