# -*- coding: utf-8 -*-
"""19851 re-teste 6 — na Equipe do lider (/team_leaders/4298356/users), clica o icone
de grafico (analise) da liderada Natalia, procura Continuidade/Acoes de resposta,
abre Adicionar e le Funcao vinculada/Iniciativa."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider_acoes"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/"); org = c["org_id"]
LOGIN = "qalider19851@teste.com"; SENHA = "123456"
log = lambda *a: print(*a, flush=True)

def dump_nav(pg, tag):
    items = pg.evaluate(r"""()=>[...document.querySelectorAll('a,[role=tab],button,span,li')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<32&&/continuidade|sucess|dashboard geral|an[aá]lise|a[cç][oõ]es de resposta|par[aâ]metros|desenvolv|feedback|desempenho|9-box|vis[aã]o/i.test(t)).slice(0,16)""")
    log(f"[{tag}] nav:", [*dict.fromkeys(items)]); log(f"[{tag}] url:", pg.url[-45:])

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True)
    try:
        pg.goto(base+"/login", wait_until="domcontentloaded", timeout=30000); pg.wait_for_timeout(1500)
        pg.fill("#user_email", LOGIN); pg.fill("#user_password", SENHA)
        pg.locator("#user_submit,button[type=submit]").first.click(timeout=4000); pg.wait_for_timeout(5000)
        ac = pg.get_by_role("button", name=re.compile("^Aceitar$", re.I))
        if ac.count(): ac.first.click(timeout=4000); pg.wait_for_timeout(1500)
        pg.goto(base+f"/o/{org}/team_leaders/4298356/users", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        dump_nav(pg, "equipe")
        # clica os icones da linha da Natalia (gráfico e trofeu) -> tenta o 1o (analytics)
        icons = pg.evaluate(r"""()=>{const tr=document.querySelector('tbody tr');if(!tr)return[];
          return [...tr.querySelectorAll('a,button,svg')].filter(e=>e.getBoundingClientRect().left>1200&&e.getBoundingClientRect().width>0).map(e=>{const r=e.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2,aria:(e.getAttribute&&(e.getAttribute('aria-label')||e.getAttribute('title')))||''};});}""")
        log("icones da linha:", icons)
        if icons:
            pg.mouse.click(icons[0]["x"], icons[0]["y"]); pg.wait_for_timeout(3000)
            dump_nav(pg, "apos-icone1")
            tw.snap(pg, PASTA, "rt6-01-icone", full=True)
        # procura Ações de resposta / Continuidade na pagina resultante
        for alvo in ("Ações de resposta","Continuidade","Continuidade e sucessão"):
            l = pg.get_by_text(re.compile("^"+re.escape(alvo)+"$", re.I))
            if l.count():
                try: l.first.click(timeout=3000, force=True); pg.wait_for_timeout(2500); log("cliquei:", alvo, "->", pg.url[-40:]); break
                except Exception: pass
        dump_nav(pg, "final")
        tw.snap(pg, PASTA, "rt6-02-final", full=True)
        add = pg.get_by_role("button", name=re.compile("Adicionar", re.I))
        log("Adicionar:", add.count())
        if add.count():
            add.first.click(timeout=5000); pg.wait_for_timeout(2500)
            sels = pg.evaluate(r"""()=>{const drw=document.querySelector('.chakra-modal__content,[role=dialog]')||document;
              return [...drw.querySelectorAll('select')].filter(e=>e.getBoundingClientRect().width>0).map(s=>({name:s.name||s.id||'',n:s.options.length,opts:[...s.options].map(o=>o.text.trim()).slice(0,6)}));}""")
            log("=== SELECTS DRAWER (LIDER) ===")
            for s in sels: log(f"   {s['name']!r}: {s['n']} opcoes -> {s['opts']}")
            tw.snap(pg, PASTA, "rt6-03-drawer", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "rt6-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
