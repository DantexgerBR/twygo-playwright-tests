# -*- coding: utf-8 -*-
"""19851 — clica o no 'Lideranca' do organograma (19653) e le o gestor/lider + email,
e os liderados. Via API do organograma se possivel."""
import json, re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider_acoes"
c = tw.cfg("MIGR"); org = c["org_id"]; base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    caps = []
    pg.on("response", lambda r: caps.append(r) if "/api/v1/o/" in r.url and "organization_chart" in r.url and r.request.method=="GET" else None)
    try:
        pg.goto(base+f"/o/{org}/organization_chart", wait_until="domcontentloaded", timeout=25000); tw.dispensar_nps(pg); pg.wait_for_timeout(3500)
        # captura a API do organograma (gestores/lideres + liderados)
        for r in caps[-6:]:
            try:
                j = r.json(); t = json.dumps(j)
                # procura nomes/emails de gestor/manager
                mg = re.findall(r'"(manager|gestor|leader|responsible|user)_?\w*"\s*:\s*("[^"]+"|{[^}]*"email"[^}]*})', t)
                emails = re.findall(r'"email"\s*:\s*"([^"]+)"', t)
                names = re.findall(r'"(?:full_name|name|manager_name)"\s*:\s*"([^"]+)"', t)
                log("API org_chart:", r.url.split("/o/")[-1][:45], "| emails:", list(dict.fromkeys(emails))[:8], "| names:", list(dict.fromkeys(names))[:8])
            except Exception as ex: log("parse:", str(ex)[:40])
        # clica o no Lideranca (texto) pra abrir detalhe
        node = pg.get_by_text("Liderança", exact=True)
        if node.count():
            node.first.click(timeout=4000); pg.wait_for_timeout(2000)
        det = pg.evaluate(r"""()=>{const txt=[...document.querySelectorAll('*')].filter(e=>{const r=e.getBoundingClientRect();return r.left>900&&r.width>0&&e.children.length<=2});
          return [...new Set(txt.map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<50&&(/@/.test(t)||/lider|gestor|respons/i.test(t))))].slice(0,10);}""")
        log("detalhe no (direita):", det)
        tw.snap(pg, PASTA, "node-lideranca", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "node-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
