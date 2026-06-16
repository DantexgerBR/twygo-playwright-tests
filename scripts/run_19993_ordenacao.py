# -*- coding: utf-8 -*-
"""19993 — ordenação em colunas (PR #10711). 37048. Checa se as colunas-alvo têm
controle de ordenação (header clicável + indicador / aria-sort / chevron)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19993_ordenacao"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

# p/ cada coluna, checa se o header é ordenável (aria-sort, ou tem ícone de sort/chevron, ou é botão)
JS_COLS = r"""(cols)=>{
  const heads=[...document.querySelectorAll('th,[role=columnheader],thead [class*=head],[class*=header-cell]')];
  return cols.map(cn=>{
    const h=heads.find(e=>new RegExp('^'+cn,'i').test((e.innerText||'').replace(/\s+/g,' ').trim()));
    if(!h) return {col:cn, achou:false};
    const aria=h.getAttribute('aria-sort')||(h.querySelector('[aria-sort]')?'tem-aria':'');
    const icon=!!h.querySelector('svg,[class*=sort i],[class*=chevron i],[class*=arrow i],i.material-icons,.material-symbols-outlined');
    const clickable=h.tagName==='BUTTON'||!!h.querySelector('button')||/cursor:\s*pointer/.test(h.getAttribute('style')||'')||getComputedStyle(h).cursor==='pointer';
    return {col:cn, achou:true, aria:aria||'', icon, clickable};
  });}"""

def checa(pg, url, cols, nome):
    try:
        pg.goto(url, wait_until="domcontentloaded", timeout=25000); tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        r = pg.evaluate(JS_COLS, cols)
        log(f"\n[{nome}] {url[-35:]}")
        for x in r:
            ord_ok = x.get("achou") and (x.get("aria") or x.get("icon") or x.get("clickable"))
            log(f"   {x['col']:14} achou={x.get('achou')} aria={x.get('aria')!r} icon={x.get('icon')} click={x.get('clickable')} => ordenável={bool(ord_ok)}")
        tw.snap(pg, PASTA, "tela-"+re.sub(r'\W+','_',nome.lower())[:18])
        return r
    except Exception as e:
        log(f"[{nome}] ERRO {str(e)[:50]}"); return []

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        checa(pg, base+f"/o/{c['org_id']}/cycles", ["Período","Campanhas","Progresso","Criado"], "Desenvolvimento-ciclos")
        # Planos e Metas — achar a listagem (tentar URLs)
        for path in (f"/o/{c['org_id']}/goals", f"/o/{c['org_id']}/plans_and_goals", f"/o/{c['org_id']}/plans"):
            r = checa(pg, base+path, ["Período"], "PlanoseMetas")
            if r: break
        # Feedbacks e anotações
        checa(pg, base+f"/o/{c['org_id']}/feedback_log", ["Visualização","Visualizacao"], "Feedbacks")
    except Exception as e:
        log("ERRO geral:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
