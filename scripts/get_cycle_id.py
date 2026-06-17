# -*- coding: utf-8 -*-
"""Pega o id do ciclo QA19948 via API e testa navegar direto pra campaigns/activate."""
import json, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    caps = []
    pg.on("response", lambda r: caps.append(r) if "/api/v1/o/" in r.url and "cycle" in r.url.lower() and r.request.method=="GET" else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3500)
        cid = None
        for r in caps:
            try:
                data = r.json()
                txt = json.dumps(data)
                log("API:", r.url.split("/o/")[-1][:60], "len", len(txt))
                # procura id + name
                import re
                for m in re.finditer(r'"id"\s*:\s*(\d+)[^}]*?"name"\s*:\s*"([^"]*)"', txt):
                    if "Calibracao" in m.group(2) or "QA19948" in m.group(2):
                        cid = m.group(1); log("  -> ciclo", m.group(2), "id", cid)
                # fallback: name antes de id
                for m in re.finditer(r'"name"\s*:\s*"([^"]*Calibracao[^"]*)"[^}]*?"id"\s*:\s*(\d+)', txt):
                    cid = cid or m.group(2); log("  -> (alt)", m.group(1), "id", m.group(2))
            except Exception as ex: log("  json err", str(ex)[:40])
        log("CICLO ID:", cid)
        if cid:
            for path in (f"/o/{c['org_id']}/cycles/{cid}/campaigns", f"/o/{c['org_id']}/cycles/{cid}"):
                pg.goto(base+path, wait_until="domcontentloaded", timeout=25000); pg.wait_for_timeout(3000)
                ok = "/cycles/"+cid in pg.url
                heads = pg.evaluate(r"""()=>[...document.querySelectorAll('h1,h2,h3')].map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<50).slice(0,5)""")
                log(f"[{path[-30:]}] url_ok={ok} url={pg.url[-45:]} heads={heads}")
                tw.snap(pg, tw.ROOT/"evidencias"/"retrabalho_20108_desempenho", "id-"+path.split('/')[-1][:12], full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
