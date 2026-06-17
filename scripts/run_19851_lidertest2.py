# -*- coding: utf-8 -*-
"""19851 re-teste — loga como QALider, dumpa a sidebar inteira, clica Continuidade/
Sucessao (rota do lider, learner), vai em Acoes de resposta > Adicionar e le os selects
Funcao vinculada / Iniciativa (vazios=bug, populados=corrigido)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider_acoes"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/"); org = c["org_id"]
LOGIN = "qalider19851@teste.com"; SENHA = "123456"
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True)
    try:
        pg.goto(base+"/login", wait_until="domcontentloaded", timeout=30000); pg.wait_for_timeout(1500)
        for sel in ("#user_email","input[type=email]"):
            if pg.locator(sel).count(): pg.fill(sel, LOGIN); break
        for sel in ("#user_password","input[type=password]"):
            if pg.locator(sel).count(): pg.fill(sel, SENHA); break
        for sel in ("#user_submit","button[type=submit]"):
            if pg.locator(sel).count():
                try: pg.locator(sel).first.click(timeout=4000); break
                except Exception: pass
        pg.wait_for_timeout(5000); tw.dispensar_nps(pg); pg.wait_for_timeout(1500)
        log("url:", pg.url[-40:])
        sidebar = pg.evaluate(r"""()=>[...document.querySelectorAll('nav a,[class*=sidebar] a,[class*=menu] a, aside a')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean).slice(0,25)""")
        log("sidebar do lider:", [*dict.fromkeys(sidebar)])
        tw.snap(pg, PASTA, "rt-01-home", full=True)
        # clica Continuidade/Sucessao
        cont = pg.get_by_role("link", name=re.compile("Continuidade|Sucess", re.I))
        log("link Continuidade na sidebar:", cont.count())
        if cont.count():
            cont.first.click(timeout=4000); pg.wait_for_timeout(3000)
            log("url continuidade:", pg.url[-40:])
            sub = pg.evaluate(r"""()=>[...document.querySelectorAll('a,[role=tab]')].map(e=>(e.innerText||'').trim()).filter(t=>/dashboard geral|an[aá]lise|a[cç][oõ]es de resposta|par[aâ]metros/i.test(t)).slice(0,8)""")
            log("submenu Continuidade:", [*dict.fromkeys(sub)])
            # vai pra Acoes de resposta
            acoes = pg.get_by_role("link", name=re.compile("A[cç][oõ]es de resposta", re.I))
            if acoes.count(): acoes.first.click(timeout=4000); pg.wait_for_timeout(3000)
            log("url acoes:", pg.url[-40:])
            tw.snap(pg, PASTA, "rt-02-acoes", full=True)
            add = pg.get_by_role("button", name=re.compile("Adicionar", re.I))
            log("botao Adicionar:", add.count())
            if add.count():
                add.first.click(timeout=5000); pg.wait_for_timeout(2500)
                sels = pg.evaluate(r"""()=>{const drw=document.querySelector('.chakra-modal__content,[role=dialog]')||document;
                  return [...drw.querySelectorAll('select')].filter(e=>e.getBoundingClientRect().width>0).map(s=>({name:s.name||s.id||'',n:s.options.length,opts:[...s.options].map(o=>o.text.trim()).slice(0,5)}));}""")
                log("=== SELECTS DO DRAWER (LIDER) ===")
                for s in sels: log(f"   {s['name']!r}: {s['n']} opcoes -> {s['opts']}")
                tw.snap(pg, PASTA, "rt-03-drawer", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "rt-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
