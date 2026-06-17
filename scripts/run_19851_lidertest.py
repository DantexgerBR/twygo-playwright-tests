# -*- coding: utf-8 -*-
"""19851 — loga como o LIDER qalider19851@teste.com (visao do lider) no 19653 e explora:
ve Continuidade? tem liderados na Analise individual? o drawer Acoes de resposta >
Adicionar tem Funcao vinculada / Iniciativa vazias (bug) ou populadas?"""
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
        for sel in ("#user_email","input[name='user[email]']","input[type=email]"):
            if pg.locator(sel).count(): pg.fill(sel, LOGIN); break
        for sel in ("#user_password","input[name='user[password]']","input[type=password]"):
            if pg.locator(sel).count(): pg.fill(sel, SENHA); break
        for sel in ("#user_submit","button[type=submit]","input[type=submit]"):
            if pg.locator(sel).count():
                try: pg.locator(sel).first.click(timeout=4000); break
                except Exception: pass
        pg.wait_for_timeout(5000)
        log("apos login url:", pg.url[-45:])
        tw.dispensar_nps(pg); pg.wait_for_timeout(1500)
        menu = pg.evaluate(r"""()=>[...document.querySelectorAll('a,nav span,[class*=menu] span,[class*=sidebar] span')].map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<30&&/continuidade|sucess|dashboard|cursos|play|equipe|an[aá]lise|a[cç][oõ]es|boas-vindas/i.test(t)).slice(0,15)""")
        log("menu do lider:", [*dict.fromkeys(menu)])
        tw.snap(pg, PASTA, "lider-01-home", full=True)
        pg.goto(base+f"/o/{org}/succession_people_analysis", wait_until="domcontentloaded", timeout=25000); pg.wait_for_timeout(3000)
        rows = pg.evaluate("()=>document.querySelectorAll('tbody tr').length")
        log("Analise individual (lider) linhas:", rows, "| url:", pg.url[-35:])
        tw.snap(pg, PASTA, "lider-02-analise", full=True)
        pg.goto(base+f"/o/{org}/succession_actions", wait_until="domcontentloaded", timeout=25000); pg.wait_for_timeout(3000)
        log("Acoes de resposta url:", pg.url[-35:])
        add = pg.get_by_role("button", name=re.compile("Adicionar", re.I))
        log("botao Adicionar:", add.count())
        if add.count():
            add.first.click(timeout=5000); pg.wait_for_timeout(2500)
            sels = pg.evaluate(r"""()=>{const drw=document.querySelector('.chakra-modal__content,[role=dialog]')||document;
              return [...drw.querySelectorAll('select')].filter(e=>e.getBoundingClientRect().width>0).map(s=>({name:s.name||s.id||'',n:s.options.length,opts:[...s.options].map(o=>o.text.trim()).slice(0,5)}));}""")
            log("selects do drawer (lider):")
            for s in sels: log(f"   {s['name']!r}: {s['n']} opcoes -> {s['opts']}")
        tw.snap(pg, PASTA, "lider-03-drawer", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "lider-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
