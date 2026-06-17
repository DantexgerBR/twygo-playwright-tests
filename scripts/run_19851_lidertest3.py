# -*- coding: utf-8 -*-
"""19851 re-teste 3 — loga QALider, clica 'Equipe' na sidebar, navega ate Acoes de
resposta (Continuidade do lider), abre Adicionar e le Funcao vinculada/Iniciativa."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider_acoes"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/"); org = c["org_id"]
LOGIN = "qalider19851@teste.com"; SENHA = "123456"
log = lambda *a: print(*a, flush=True)

def selects_drawer(pg):
    return pg.evaluate(r"""()=>{const drw=document.querySelector('.chakra-modal__content,[role=dialog]')||document;
      return [...drw.querySelectorAll('select')].filter(e=>e.getBoundingClientRect().width>0).map(s=>({name:s.name||s.id||'',n:s.options.length,opts:[...s.options].map(o=>o.text.trim()).slice(0,6)}));}""")

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True)
    try:
        pg.goto(base+"/login", wait_until="domcontentloaded", timeout=30000); pg.wait_for_timeout(1500)
        pg.fill("#user_email", LOGIN); pg.fill("#user_password", SENHA)
        for sel in ("#user_submit","button[type=submit]"):
            if pg.locator(sel).count():
                try: pg.locator(sel).first.click(timeout=4000); break
                except Exception: pass
        pg.wait_for_timeout(5000); tw.dispensar_nps(pg); pg.wait_for_timeout(1500)
        # clica Equipe
        eq = pg.get_by_role("link", name=re.compile("Equipe", re.I))
        log("link Equipe:", eq.count())
        if eq.count(): eq.first.click(timeout=4000); pg.wait_for_timeout(3000)
        log("url apos Equipe:", pg.url[-45:])
        # submenu / abas dentro de Equipe
        itens = pg.evaluate(r"""()=>[...document.querySelectorAll('a,[role=tab],button,span')].map(e=>(e.innerText||'').trim()).filter(t=>/continuidade|sucess|dashboard geral|an[aá]lise individual|a[cç][oõ]es de resposta|par[aâ]metros|desenvolv|feedback/i.test(t)&&t.length<30).slice(0,12)""")
        log("itens de Equipe/Continuidade:", [*dict.fromkeys(itens)])
        tw.snap(pg, PASTA, "rt3-01-equipe", full=True)
        # tenta ir em Acoes de resposta
        acoes = pg.get_by_role("link", name=re.compile("A[cç][oõ]es de resposta", re.I))
        if not acoes.count(): acoes = pg.get_by_text(re.compile("^A[cç][oõ]es de resposta$", re.I))
        log("Acoes de resposta link:", acoes.count())
        if acoes.count():
            acoes.first.click(timeout=4000); pg.wait_for_timeout(3000)
        log("url acoes:", pg.url[-45:])
        # Analise individual liderados (rapido)
        tw.snap(pg, PASTA, "rt3-02-acoes", full=True)
        add = pg.get_by_role("button", name=re.compile("Adicionar", re.I))
        log("botao Adicionar:", add.count())
        if add.count():
            add.first.click(timeout=5000); pg.wait_for_timeout(2500)
            sels = selects_drawer(pg)
            log("=== SELECTS DRAWER (LIDER) ===")
            for s in sels: log(f"   {s['name']!r}: {s['n']} opcoes -> {s['opts']}")
            # veredito
            fn = next((s for s in sels if "role" in s["name"] or "funcao" in s["name"].lower()), None)
            ini = next((s for s in sels if "initiative" in s["name"] or "iniciativa" in s["name"].lower()), None)
            log("Funcao vinculada opcoes:", fn["n"]-1 if fn else "?", "| Iniciativa opcoes:", ini["n"]-1 if ini else "?")
            tw.snap(pg, PASTA, "rt3-03-drawer", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "rt3-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
