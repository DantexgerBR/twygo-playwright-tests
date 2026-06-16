# -*- coding: utf-8 -*-
"""Recon 19948 — abre o form 'Novo ciclo' e dumpa os campos. Headless, não salva."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19948_calibracao"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=True)
    tw.login(page, c)
    try:
        page.goto(base + f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(page); page.wait_for_timeout(3000)
        page.get_by_role("button", name=re.compile(r"Novo ciclo", re.I)).first.click(timeout=6000)
        page.wait_for_timeout(3000)
        print("[novo ciclo] url:", page.url)
        tw.snap(page, PASTA, "novociclo-form", full=True)
        campos = page.evaluate(r"""()=>[...document.querySelectorAll('input,select,textarea')]
          .map(e=>({tag:e.tagName,name:e.name||'',type:e.type||'',ph:e.placeholder||'',
                    label:(e.labels&&e.labels[0]?e.labels[0].innerText:'').replace(/\s+/g,' ').trim()}))
          .filter(x=>x.type!=='hidden').slice(0,30)""")
        print("[novo ciclo] campos:")
        for f in campos: print("   ", f)
        botoes = page.evaluate(r"""()=>[...document.querySelectorAll('button,input[type=submit]')]
          .map(b=>(b.innerText||b.value||'').trim()).filter(Boolean).slice(0,15)""")
        print("[novo ciclo] botões:", botoes)
        # passos/etapas (wizard?)
        etapas = page.evaluate(r"""()=>[...document.querySelectorAll('h1,h2,h3,[class*=step],[class*=stepper]')]
          .map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean).slice(0,12)""")
        print("[novo ciclo] etapas/títulos:", etapas)
    except Exception as e:
        print("ERRO:", e); tw.snap(page, PASTA, "novociclo-erro")
    finally:
        ctx.close(); browser.close()
