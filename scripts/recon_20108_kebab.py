# -*- coding: utf-8 -*-
"""Recon 20108 — abre o kebab (more_vert) do ciclo existente QA19948 e lista as opcoes
(Editar/Iniciar/Ver/Duplicar etc). Tenta abrir o detalhe/editar pra ver se ja tem
avaliacoes e participantes (caminho rapido vs montar do zero)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20108_desempenho"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        # kebab da 1a linha
        kb = pg.get_by_role("button", name=re.compile("more_vert|Mais|Op", re.I))
        if not kb.count():
            # tenta o ultimo botao da linha
            kb = pg.locator("tbody tr").first.locator("button")
        log("kebab count:", kb.count())
        if kb.count(): kb.last.click(timeout=4000); pg.wait_for_timeout(1200)
        opts = pg.evaluate(r"""()=>[...document.querySelectorAll('[role=menuitem],[role=menu] button,[role=menu] a,.chakra-menu__menuitem')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean)""")
        log("opcoes do kebab:", opts)
        tw.snap(pg, PASTA, "kebab-01", full=True)
        # tenta clicar "Editar" (abre o wizard preenchido -> ver avaliacoes/etapas) ou "Iniciar"
        for alvo in ("Editar", "Iniciar ciclo", "Iniciar", "Ver detalhes", "Visualizar"):
            it = pg.get_by_role("menuitem", name=re.compile(alvo, re.I))
            if it.count():
                it.first.click(timeout=4000); pg.wait_for_timeout(3000); log("cliquei:", alvo, "-> url:", pg.url[-45:]); break
        # dump do que abriu
        info = pg.evaluate(r"""()=>{const tabs=[...document.querySelectorAll('[role=tab],button')].map(e=>(e.innerText||'').trim()).filter(t=>/identifica|avalia|etapa|configura|participante/i.test(t)).slice(0,10);
          const heads=[...document.querySelectorAll('h1,h2,h3')].map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,5);
          const rows=document.querySelectorAll('tbody tr').length;
          return {tabs:[...new Set(tabs)], heads, rows};}""")
        log("apos abrir -> heads:", info["heads"], "tabs:", info["tabs"], "rows:", info["rows"])
        tw.snap(pg, PASTA, "kebab-02-aberto", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "kebab-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
