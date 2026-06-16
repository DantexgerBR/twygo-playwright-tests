# -*- coding: utf-8 -*-
"""Recon 19948 — formulário de criação de org (/admin/organizations) e detalhe da
flag modulo_de_desempenho (/admin/manage/features). Read-only (não cria/altera)."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19948_calibracao"
c = tw.cfg(); base = c["base_url"].rstrip("/")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1500, height=950)
    tw.login(page, c)
    try:
        # --- criação de org ---
        page.goto(base + "/admin/organizations", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000); tw.dispensar_nps(page)
        tw.snap(page, PASTA, "org-00-lista")
        # achar link/botão de nova org
        novo = page.evaluate(r"""()=>[...document.querySelectorAll('a,button')]
          .map(e=>({t:(e.innerText||'').trim(),h:e.getAttribute&&e.getAttribute('href')||''}))
          .filter(x=>/nov[ao]|adicionar|criar|new/i.test(x.t)).slice(0,8)""")
        print("[org] botões nova org:", novo)
        # tentar /admin/organizations/new
        page.goto(base + "/admin/organizations/new", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
        print("[org/new] url:", page.url)
        campos = page.evaluate(r"""()=>[...document.querySelectorAll('input,select,textarea')]
          .map(e=>({tag:e.tagName,name:e.name||'',type:e.type||'',label:(e.labels&&e.labels[0]?e.labels[0].innerText:'').trim()}))
          .filter(x=>x.name).slice(0,30)""")
        print("[org/new] campos do form:")
        for f in campos: print("   ", f)
        tw.snap(page, PASTA, "org-01-new-form", full=True)

        # --- detalhe da flag modulo_de_desempenho ---
        page.goto(base + "/admin/manage/features", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
        link = page.get_by_role("link", name=re.compile(r"modulo_de_desempenho", re.I)).first
        print("[flag] link modulo_de_desempenho encontrado?", link.count())
        if link.count():
            link.click(timeout=6000); page.wait_for_timeout(2000)
            print("[flag] url:", page.url)
            tw.snap(page, PASTA, "flag-00-detalhe", full=True)
            # estado: actors habilitados + como adicionar
            info = page.evaluate(r"""()=>({
              actors:[...document.querySelectorAll('*')].map(e=>(e.innerText||'').trim()).filter(t=>/Organization;|actor|ativad[oa] para/i.test(t)).slice(0,10),
              inputs:[...document.querySelectorAll('input')].map(i=>({name:i.name||'',ph:i.placeholder||'',type:i.type})).slice(0,12),
              botoes:[...document.querySelectorAll('button,input[type=submit]')].map(b=>(b.innerText||b.value||'').trim()).filter(Boolean).slice(0,12)
            })""")
            print("[flag] info:", info)
    except Exception as e:
        print("ERRO:", e); tw.snap(page, PASTA, "recon-erro")
    finally:
        ctx.close(); browser.close()
