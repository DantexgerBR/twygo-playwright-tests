# -*- coding: utf-8 -*-
"""Lote responsivo org 37061 / curso 807533 — valida:
  19813 [P2] layout responsivo <1366px sem scroll horizontal (PR 10644)
  19961 [P3] 3 abas no rodapé no mobile: Atividades · Preview · Copiloto (PR 10666)
Viewports: 1024x600 · 768x1024 · 767x800 · 360x740.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "qa_lote_1106_responsivo"
CURSO = "807533"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
VIEWPORTS = [(1024, 600), (768, 1024), (767, 800), (360, 740)]

with tw.sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=250)
    ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
    page = ctx.new_page()
    tw.login(page, c)
    url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"

    resumo = []
    for w, h in VIEWPORTS:
        page.set_viewport_size({"width": w, "height": h})
        page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(page)
        page.wait_for_timeout(6000)
        tw.dispensar_nps(page)

        scroll_h = page.evaluate(
            "()=>document.documentElement.scrollWidth > document.documentElement.clientWidth + 4"
        )
        # procura barra fixa no rodapé com as 3 abas
        rodape = page.evaluate(
            """()=>{
                const els=[...document.querySelectorAll('*')].filter(e=>{
                    const s=getComputedStyle(e);
                    if(!(s.position==='fixed'||s.position==='sticky'))return false;
                    const r=e.getBoundingClientRect();
                    return r.bottom>window.innerHeight-90 && r.width>window.innerWidth*0.6 && r.height>30 && r.height<140;});
                return els.map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim().slice(0,120));
            }"""
        )
        corpo = " ".join(rodape).lower()
        tem_3_abas = all(t in corpo for t in ["atividade"]) and ("preview" in corpo or "visualiza" in corpo) and ("copiloto" in corpo)
        print(f"[{w}x{h}] scroll horizontal? {scroll_h} | barras fixas no rodapé: {rodape or 'NENHUMA'} | 3 abas? {tem_3_abas}")
        tw.snap(page, PASTA, f"estudio-{w}x{h}")
        resumo.append((f"{w}x{h}", scroll_h, tem_3_abas, rodape))

    print("\n=== RESUMO ===")
    for vp, sh, abas, rod in resumo:
        print(f"  {vp:9s} | scroll-h: {'✖ TEM' if sh else '✔ sem'} | abas rodapé: {'✔' if abas else '✖'} | {rod}")
    ctx.close(); browser.close()
