# -*- coding: utf-8 -*-
"""Recon 19948 — detalhe da flag modulo_de_desempenho (headless, read-only):
como está habilitada e como adicionar uma org como actor."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19948_calibracao"
c = tw.cfg(); base = c["base_url"].rstrip("/")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=True)  # SEM janela
    tw.login(page, c)
    try:
        page.goto(base + "/admin/manage/features", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
        link = page.get_by_role("link", name=re.compile(r"^modulo_de_desempenho$", re.I)).first
        if not link.count():
            link = page.get_by_text(re.compile(r"^modulo_de_desempenho$", re.I)).first
        print("[flag] achou link?", link.count())
        link.click(timeout=6000); page.wait_for_timeout(2500)
        print("[flag] url:", page.url)
        tw.snap(page, PASTA, "flag-detalhe", full=True)
        corpo = page.evaluate("()=>document.body.innerText")
        # achar actors atualmente habilitados (Organization;<id>)
        actors = re.findall(r"Organization;\d+|\b\d{4,6}\b", corpo)
        print("[flag] trechos de actors/ids:", actors[:15])
        info = page.evaluate(r"""()=>({
          inputs:[...document.querySelectorAll('input')].map(i=>({name:i.name||'',ph:i.placeholder||'',type:i.type})),
          botoes:[...document.querySelectorAll('button,input[type=submit],a.btn')].map(b=>(b.innerText||b.value||'').trim()).filter(Boolean).slice(0,15),
          secoes:[...document.querySelectorAll('h1,h2,h3,h4,label,legend')].map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,20)
        })""")
        print("[flag] inputs:", info["inputs"])
        print("[flag] botoes:", info["botoes"])
        print("[flag] secoes:", info["secoes"])
    except Exception as e:
        print("ERRO:", e); tw.snap(page, PASTA, "flag-erro")
    finally:
        ctx.close(); browser.close()
