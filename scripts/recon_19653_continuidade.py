# -*- coding: utf-8 -*-
"""Recon 19653 (flag continuidade_sucessao recem-ligada) — abre Dashboard geral,
Analise individual, Acoes de resposta e Parametros; conta dados reais (linhas/cards)
pra confirmar que 20074/20096/20069 agora reproduzem."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "recon_19653_continuidade"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

ROTAS = [
    ("dashboard_geral", "/succession_dashboards"),
    ("analise_individual", "/succession_people_analysis"),
    ("acoes_resposta", "/succession_actions"),
    ("parametros", "/succession_initiatives"),
]

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        for nome, path in ROTAS:
            url = base+f"/o/{c['org_id']}{path}"
            pg.goto(url, wait_until="domcontentloaded", timeout=25000); tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
            info = pg.evaluate(r"""()=>{const rows=document.querySelectorAll('tbody tr').length;
              const h=(document.querySelector('h1,h2,.chakra-heading')||{}).innerText||'';
              const pct=[...document.querySelectorAll('*')].filter(e=>e.children.length===0&&/%$/.test((e.innerText||'').trim())).map(e=>e.innerText.trim()).slice(0,6);
              const semdados=/n[aã]o h[aá] dados|sem [aá]rea/i.test(document.body.innerText);
              return {rows, h:h.slice(0,40), pct:[...new Set(pct)], semdados};}""")
            log(f"[{nome}] {pg.url[-45:]} | head='{info['h']}' rows={info['rows']} pct={info['pct']} sem_dados={info['semdados']}")
            tw.snap(pg, PASTA, nome, full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
