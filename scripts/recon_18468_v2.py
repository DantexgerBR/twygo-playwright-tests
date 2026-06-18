"""RECON v2 18468 — clicar EXATAMENTE em 'Importacao Inteligente' e mapear o drawer/chat.
Dump: file inputs visiveis, textareas/inputs de texto, botoes do painel aberto.
"""
import re
import _twygo as tw

c = tw.cfg("MIGR")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "18468_recon"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{BASE}/o/{ORG}/question_lists", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)

    btn = page.get_by_text(re.compile(r"Importa.{0,4}o Inteligente", re.I)).first
    print(f"[btn import] count via text={page.get_by_text(re.compile(r'Importa.{0,4}o Inteligente', re.I)).count()}")
    btn.click(timeout=6000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    print(f"[url] {page.url}")
    tw.snap(page, PASTA, "10-drawer-import")

    files = page.evaluate(
        "()=>Array.from(document.querySelectorAll('input[type=file]')).map(i=>({accept:i.accept,name:i.name,id:i.id,vis:i.offsetParent!==null}))")
    print(f"[file inputs] {files}")

    texts = page.evaluate(
        "()=>Array.from(document.querySelectorAll('textarea,input[type=text]')).filter(e=>e.offsetParent!==null).map(e=>({tag:e.tagName,ph:e.placeholder,name:e.name,id:e.id}))")
    print(f"[campos texto visiveis] {texts}")

    botoes = page.evaluate(
        "()=>Array.from(document.querySelectorAll('button')).filter(b=>b.offsetParent!==null).map(b=>(b.innerText||b.getAttribute('aria-label')||'').replace(/\\s+/g,' ').trim()).filter(Boolean).slice(0,30)")
    print(f"[botoes visiveis] {botoes}")

    # container do chat de importacao
    cont = page.evaluate(
        "()=>{const sel=['[class*=import]','[class*=drawer]','[class*=modal]','[class*=thread]','[class*=assistant]'];for(const s of sel){const e=document.querySelector(s);if(e&&e.offsetParent!==null)return {sel:s,cls:(e.className||'').toString().slice(0,140)};}return null;}")
    print(f"[container] {cont}")

    page.wait_for_timeout(1500)
    ctx.close(); browser.close()
