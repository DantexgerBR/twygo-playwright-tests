"""18539 — emojis no nome do conteúdo: não salva, mas a toast deve ser CLARA."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "emoji_toast_18539"
c = tw.cfg("MIGR")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(c["base_url"] + "/o/19653/events?tab=events", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "01-lista-conteudos")
    # achar link de edição do 1o conteúdo (curso)
    links = page.evaluate(
        "()=>Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href'))"
        ".filter(h=>h&&/\\/events\\/\\d+\\/edit/.test(h))"
    )
    print("links de edit:", links[:5])
    if links:
        page.goto(c["base_url"] + links[0], wait_until="domcontentloaded", timeout=40000)
        page.wait_for_timeout(4500)
        tw.dispensar_nps(page)
    tw.snap(page, PASTA, "02-edicao-identificacao")
    print("url edição:", page.url)
    # achar campo Nome
    campos = page.evaluate(
        "()=>Array.from(document.querySelectorAll('input,textarea')).map(e=>({id:e.id,name:e.name,ph:e.placeholder,vis:e.offsetParent!==null})).filter(x=>x.vis)"
    )
    print("campos visíveis:", campos[:15])
    ctx.close(); browser.close()
