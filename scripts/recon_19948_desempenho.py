# -*- coding: utf-8 -*-
"""Recon 19948 — navegação do módulo Desempenho na org 37048 (RECERT, tem a flag
modulo_de_desempenho). Captura Network (>=400) pra achar o 500 de calibração.
Headless (sem janela)."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19948_calibracao"
c = tw.cfg("RECERT")
base = c["base_url"].rstrip("/")
erros = []

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=True)
    # captura de network: status >= 400
    def on_resp(r):
        try:
            if r.status >= 400:
                erros.append((r.status, r.url))
        except Exception:
            pass
    page.on("response", on_resp)
    tw.login(page, c)
    print("logado:", page.url)
    try:
        # dump do menu lateral
        menu = page.evaluate(r"""()=>[...document.querySelectorAll('a,button,[role=menuitem]')]
          .map(e=>({t:(e.innerText||'').replace(/\s+/g,' ').trim(), h:e.getAttribute&&e.getAttribute('href')||''}))
          .filter(x=>x.t && x.t.length<40)""")
        print("== itens de menu com Desenvolv/Desempenho/Ciclo/Campanha/Feedback ==")
        for it in menu:
            if re.search(r"desenvolv|desempenh|ciclo|campanh|feedback|calibra|avalia", it["t"], re.I):
                print("  *", it)
        tw.snap(page, PASTA, "des-00-home")

        # tentar achar a área de Desempenho via menu "Desenvolvimento"
        clicou = False
        for nome in ("Desenvolvimento", "Desempenho", "Desempenho e Feedback"):
            try:
                el = page.get_by_role("link", name=re.compile(nome, re.I)).first
                if el.count():
                    el.click(timeout=5000); page.wait_for_timeout(3000); clicou = True
                    print(f"[nav] cliquei '{nome}' -> {page.url}"); break
            except Exception: pass
        if not clicou:
            # tentar URLs diretas do módulo
            for path in (f"/o/{c['org_id']}/cycles", f"/o/{c['org_id']}/performance", f"/o/{c['org_id']}/development"):
                try:
                    page.goto(base + path, wait_until="domcontentloaded", timeout=15000); page.wait_for_timeout(2500)
                    txt = page.evaluate("()=>document.body.innerText.slice(0,120)")
                    print(f"[nav] {path} -> {page.url[-45:]} | {txt[:60].strip()!r}")
                except Exception as e:
                    print(f"[nav] {path} erro {str(e)[:40]}")
        tw.snap(page, PASTA, "des-01-modulo", full=True)
        body = page.evaluate("()=>document.body.innerText.slice(0,400)")
        print("[modulo] corpo:", body[:300].replace("\n", " | "))

        print("\n== erros de network (>=400) capturados ==")
        for s, u in erros[-20:]:
            print(f"  {s} {u}")
    except Exception as e:
        print("ERRO:", e); tw.snap(page, PASTA, "des-erro")
    finally:
        ctx.close(); browser.close()
