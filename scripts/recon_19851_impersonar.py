# -*- coding: utf-8 -*-
"""Recon 19851 — achar caranovo (líder, 7092890) no 19653 e a opção 'acessar como'
pra impersonar e testar o drawer Ações de resposta. Headless."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        log("logado como:", pg.evaluate(r"""()=>{const e=[...document.querySelectorAll('*')].find(x=>/@|Gambeta|Administrador/.test(x.innerText||'')&&x.children.length===0);return e?e.innerText.trim().slice(0,30):'?'}"""))
        pg.goto(base + f"/o/{c['org_id']}/users", wait_until="domcontentloaded", timeout=30000); tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        # buscar caranovo
        srch = pg.locator('input[type=search], input[placeholder*="esquis" i], input[placeholder*="uscar" i]').first
        if srch.count(): srch.fill("caranovo"); pg.wait_for_timeout(2500)
        tw.snap(pg, PASTA, "recon-01-users")
        # achar a linha do caranovo e suas ações (kebab/acessar como)
        info = pg.evaluate(r"""()=>{
          const row=[...document.querySelectorAll('tr,[class*=row],li,div')].find(e=>/caranovo/i.test(e.innerText||'')&&(e.innerText||'').length<300);
          if(!row) return {achou:false};
          const acoes=[...row.querySelectorAll('a,button')].map(b=>(b.innerText||b.getAttribute('aria-label')||b.title||'').trim()).filter(Boolean);
          const kebab=[...row.querySelectorAll('*')].some(e=>(e.innerText||'').trim()==='more_vert');
          return {achou:true, txt:(row.innerText||'').replace(/\s+/g,' ').trim().slice(0,120), acoes, kebab};}""")
        log("[caranovo] row:", info)
        # se tem kebab, abrir e listar opções
        if info.get("kebab"):
            pg.evaluate(r"""()=>{const row=[...document.querySelectorAll('tr,[class*=row],li')].find(e=>/caranovo/i.test(e.innerText||''));const k=row&&[...row.querySelectorAll('*')].find(e=>(e.innerText||'').trim()==='more_vert');if(k)k.click();}""")
            pg.wait_for_timeout(1200)
            menu = pg.evaluate(r"""()=>[...document.querySelectorAll('[role=menuitem],a,button')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/acessar|entrar como|imperson|logar|visualizar como|perfil/i.test(t)).slice(0,8)""")
            log("[caranovo] menu acessar-como:", menu)
            tw.snap(pg, PASTA, "recon-02-kebab")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "recon-erro", full=True)
        except Exception: pass
    finally:
        ctx.close(); b.close()
