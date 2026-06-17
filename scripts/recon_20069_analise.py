# -*- coding: utf-8 -*-
"""Recon 20069 — Analise individual no 19653 (25 pessoas). Abre a tela, lista colunas
e acoes (editar pessoa), tenta abrir o editor de uma pessoa pra achar o campo e-mail
e o botao salvar (bug: e-mail obrigatorio nao salva)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20069_email"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/succession_people_analysis", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3500)
        cols = pg.evaluate(r"""()=>[...document.querySelectorAll('thead th,[role=columnheader]')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean)""")
        log("colunas:", cols)
        # acoes por linha (botoes/icones)
        acoes = pg.evaluate(r"""()=>{const tr=document.querySelector('tbody tr');if(!tr)return[];
          return [...tr.querySelectorAll('button,a,[role=button],svg')].map(e=>(e.getAttribute('aria-label')||e.title||e.innerText||e.tagName).trim()).filter(Boolean).slice(0,10);}""")
        log("acoes 1a linha:", acoes)
        tw.snap(pg, PASTA, "01-lista", full=True)
        # tenta abrir editor da 1a pessoa: clicar no nome ou icone editar
        nome1 = pg.evaluate(r"""()=>{const tr=document.querySelector('tbody tr');return tr?(tr.innerText||'').split('\n')[0].slice(0,40):''}""")
        log("1a pessoa:", nome1)
        row = pg.locator("tbody tr").first
        # tentar clicar na linha / kebab / icone
        opened = False
        for sel in ['button[aria-label*=ditar]','[aria-label*=ditar]','svg']:
            el = row.locator(sel)
            if el.count():
                try: el.first.click(timeout=3000); pg.wait_for_timeout(2000); opened=True; log("cliquei acao:", sel); break
                except Exception as ex: log("falhou", sel, str(ex)[:40])
        if not opened:
            row.click(timeout=3000); pg.wait_for_timeout(2000); log("cliquei na linha")
        # dump do que abriu
        info = pg.evaluate(r"""()=>{const inputs=[...document.querySelectorAll('input')].filter(e=>e.offsetParent!==null).map(e=>({ph:e.placeholder||'',name:e.name||'',type:e.type,val:(e.value||'').slice(0,20)}));
          const labels=[...document.querySelectorAll('label,h2,h3')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<40).slice(0,18);
          const btns=[...document.querySelectorAll('button')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,12);
          return {inputs:inputs.slice(0,15), labels, btns:[...new Set(btns)]};}""")
        log("inputs:", info["inputs"])
        log("labels:", info["labels"])
        log("btns:", info["btns"])
        tw.snap(pg, PASTA, "02-editor", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
