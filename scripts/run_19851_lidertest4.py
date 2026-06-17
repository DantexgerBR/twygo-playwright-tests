# -*- coding: utf-8 -*-
"""19851 re-teste 4 — login QALider, ACEITA consentimento, clica 'Equipe', navega ate
Acoes de resposta (Continuidade do lider), abre Adicionar e le Funcao/Iniciativa."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider_acoes"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/"); org = c["org_id"]
LOGIN = "qalider19851@teste.com"; SENHA = "123456"
log = lambda *a: print(*a, flush=True)

def click_txt(pg, alvo, xmin=0):
    box = pg.evaluate(r"""(a)=>{const[al,xm]=a;const els=[...document.querySelectorAll('a,button,div,span,li')].filter(e=>{const t=(e.innerText||'').replace(/\s+/g,' ').trim();return t===al||t.endsWith(' '+al)||t===al}).filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&r.left>=xm});
      if(!els.length)return null;els[0].scrollIntoView({block:'center'});const r=els[0].getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2}}""", [alvo, xmin])
    if not box: return False
    pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(800); return True

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True)
    try:
        pg.goto(base+"/login", wait_until="domcontentloaded", timeout=30000); pg.wait_for_timeout(1500)
        pg.fill("#user_email", LOGIN); pg.fill("#user_password", SENHA)
        for sel in ("#user_submit","button[type=submit]"):
            if pg.locator(sel).count():
                try: pg.locator(sel).first.click(timeout=4000); break
                except Exception: pass
        pg.wait_for_timeout(5000)
        # aceita consentimento
        ac = pg.get_by_role("button", name=re.compile("^Aceitar$", re.I))
        if ac.count(): ac.first.click(timeout=4000); pg.wait_for_timeout(2000); log("aceitou consentimento")
        tw.dispensar_nps(pg); pg.wait_for_timeout(1000)
        # clica Equipe (menu lateral, x<260)
        log("clicou Equipe:", click_txt(pg, "Equipe")); pg.wait_for_timeout(3000)
        log("url:", pg.url[-45:])
        itens = pg.evaluate(r"""()=>[...document.querySelectorAll('a,[role=tab],span,li')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/continuidade|sucess|dashboard geral|an[aá]lise individual|a[cç][oõ]es de resposta|par[aâ]metros|desenvolv|feedback|vis[aã]o/i.test(t)&&t.length<32).slice(0,14)""")
        log("itens Equipe:", [*dict.fromkeys(itens)])
        tw.snap(pg, PASTA, "rt4-01-equipe", full=True)
        # Acoes de resposta
        if click_txt(pg, "Ações de resposta") or click_txt(pg, "Acoes de resposta"):
            pg.wait_for_timeout(3000); log("entrou em Acoes, url:", pg.url[-40:])
        tw.snap(pg, PASTA, "rt4-02-acoes", full=True)
        add = pg.get_by_role("button", name=re.compile("Adicionar", re.I))
        log("botao Adicionar:", add.count())
        if add.count():
            add.first.click(timeout=5000); pg.wait_for_timeout(2500)
            sels = pg.evaluate(r"""()=>{const drw=document.querySelector('.chakra-modal__content,[role=dialog]')||document;
              return [...drw.querySelectorAll('select')].filter(e=>e.getBoundingClientRect().width>0).map(s=>({name:s.name||s.id||'',n:s.options.length,opts:[...s.options].map(o=>o.text.trim()).slice(0,6)}));}""")
            log("=== SELECTS DRAWER (LIDER) ===")
            for s in sels: log(f"   {s['name']!r}: {s['n']} opcoes -> {s['opts']}")
            tw.snap(pg, PASTA, "rt4-03-drawer", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "rt4-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
