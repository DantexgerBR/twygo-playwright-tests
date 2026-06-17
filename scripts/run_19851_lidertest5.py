# -*- coding: utf-8 -*-
"""19851 re-teste 5 — login QALider, aceita consent, clica o item 'Equipe' da sidebar
(coordenada x<260), dumpa url+submenu+conteudo, acha Acoes de resposta, abre Adicionar."""
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
        pg.fill("#user_email", LOGIN); pg.fill("#user_password", SENHA)
        pg.locator("#user_submit,button[type=submit]").first.click(timeout=4000); pg.wait_for_timeout(5000)
        ac = pg.get_by_role("button", name=re.compile("^Aceitar$", re.I))
        if ac.count(): ac.first.click(timeout=4000); pg.wait_for_timeout(2000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(1000)
        # clica o item Equipe da sidebar (link a com href)
        box = pg.evaluate(r"""()=>{const e=[...document.querySelectorAll('a,li,div')].find(x=>{const t=(x.innerText||'').replace(/\s+/g,' ').trim();return (t==='Equipe'||t.endsWith(' Equipe'))&&x.getBoundingClientRect().left<260&&x.getBoundingClientRect().width>0});
          if(!e)return null;const r=e.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2,href:(e.closest('a')||{}).href||''};}""")
        log("Equipe box:", box)
        if box: pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(3500)
        log("url apos Equipe:", pg.url[-50:])
        # dump submenu + conteudo
        info = pg.evaluate(r"""()=>{const links=[...document.querySelectorAll('a,[role=tab],span,li,button')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<32&&/continuidade|sucess|dashboard geral|an[aá]lise|a[cç][oõ]es de resposta|par[aâ]metros|desenvolv|feedback|vis[aã]o|desempenho|9-box/i.test(t));
          const heads=[...document.querySelectorAll('h1,h2,h3')].map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,5);
          return {links:[...new Set(links)].slice(0,16), heads};}""")
        log("heads:", info["heads"]); log("itens/submenu:", info["links"])
        tw.snap(pg, PASTA, "rt5-01-equipe", full=True)
        # tenta clicar Continuidade ou Acoes de resposta
        for alvo in ("Continuidade e sucessão","Continuidade","Ações de resposta"):
            l = pg.get_by_text(re.compile("^"+re.escape(alvo)+"$", re.I))
            if l.count():
                try: l.first.click(timeout=3500, force=True); pg.wait_for_timeout(2500); log("cliquei:", alvo, "->", pg.url[-35:])
                except Exception: pass
        tw.snap(pg, PASTA, "rt5-02-cont", full=True)
        add = pg.get_by_role("button", name=re.compile("Adicionar", re.I))
        log("Adicionar:", add.count())
        if add.count():
            add.first.click(timeout=5000); pg.wait_for_timeout(2500)
            sels = pg.evaluate(r"""()=>{const drw=document.querySelector('.chakra-modal__content,[role=dialog]')||document;
              return [...drw.querySelectorAll('select')].filter(e=>e.getBoundingClientRect().width>0).map(s=>({name:s.name||s.id||'',n:s.options.length,opts:[...s.options].map(o=>o.text.trim()).slice(0,6)}));}""")
            log("=== SELECTS DRAWER (LIDER) ===")
            for s in sels: log(f"   {s['name']!r}: {s['n']} opcoes -> {s['opts']}")
            tw.snap(pg, PASTA, "rt5-03-drawer", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "rt5-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
