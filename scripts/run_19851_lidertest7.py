# -*- coding: utf-8 -*-
"""19851 re-teste 7 — clica icone grafico da Natalia (coord) e sonda rotas diretas de
Continuidade do lider. Acha Acoes de resposta, abre Adicionar, le selects."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider_acoes"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/"); org = c["org_id"]
LOGIN = "qalider19851@teste.com"; SENHA = "123456"; TL = "4298356"
log = lambda *a: print(*a, flush=True)

def login(pg):
    pg.goto(base+"/login", wait_until="domcontentloaded", timeout=30000); pg.wait_for_timeout(1500)
    pg.fill("#user_email", LOGIN); pg.fill("#user_password", SENHA)
    pg.locator("#user_submit,button[type=submit]").first.click(timeout=4000); pg.wait_for_timeout(5000)
    ac = pg.get_by_role("button", name=re.compile("^Aceitar$", re.I))
    if ac.count(): ac.first.click(timeout=4000); pg.wait_for_timeout(1500)

def selects(pg):
    return pg.evaluate(r"""()=>{const drw=document.querySelector('.chakra-modal__content,[role=dialog]')||document;
      return [...drw.querySelectorAll('select')].filter(e=>e.getBoundingClientRect().width>0).map(s=>({name:s.name||s.id||'',n:s.options.length,opts:[...s.options].map(o=>o.text.trim()).slice(0,6)}));}""")

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True)
    try:
        login(pg)
        # 1) clica icone grafico da Natalia por coordenada
        pg.goto(base+f"/o/{org}/team_leaders/{TL}/users", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        pg.mouse.click(1401, 276); pg.wait_for_timeout(3000)
        log("apos icone grafico url:", pg.url[-55:])
        nav = pg.evaluate(r"""()=>[...document.querySelectorAll('a,[role=tab],span,button')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<32&&/continuidade|sucess|an[aá]lise|a[cç][oõ]es de resposta|desempenho|par[aâ]metros|dashboard geral/i.test(t)).slice(0,14)""")
        log("nav apos icone:", [*dict.fromkeys(nav)])
        tw.snap(pg, PASTA, "rt7-01-icone", full=True)
        # 2) sonda rotas diretas
        for path in (f"/team_leaders/{TL}/succession_actions", f"/team_leaders/{TL}/succession_people_analysis",
                     f"/team_leaders/{TL}/continuity_actions", f"/team_leaders/{TL}/response_actions"):
            try:
                pg.goto(base+f"/o/{org}{path}", wait_until="domcontentloaded", timeout=18000); pg.wait_for_timeout(2500)
                perm = "não tem permissão" in pg.content()[:5000] or "doesn't exist" in pg.content()[:5000]
                add = pg.get_by_role("button", name=re.compile("Adicionar", re.I)).count()
                log(f"[{path[-32:]}] perm/404={perm} Adicionar={add} url={pg.url[-30:]}")
                if add and not perm: break
            except Exception as ex: log(f"[{path[-25:]}] err {str(ex)[:30]}")
        # se achou Adicionar, abre e le
        add = pg.get_by_role("button", name=re.compile("Adicionar", re.I))
        log("Adicionar final:", add.count())
        if add.count():
            add.first.click(timeout=5000); pg.wait_for_timeout(2500)
            sl = selects(pg)
            log("=== SELECTS DRAWER (LIDER) ===")
            for s in sl: log(f"   {s['name']!r}: {s['n']} opcoes -> {s['opts']}")
            tw.snap(pg, PASTA, "rt7-02-drawer", full=True)
        else:
            tw.snap(pg, PASTA, "rt7-02-final", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "rt7-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
