# -*- coding: utf-8 -*-
"""19961 — probe 2: clicar na borda ESQUERDA da aba Copiloto (fora do iframe do chat)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "qa_lote_1106_responsivo"
CURSO = "807533"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'

with tw.sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=300)
    ctx = browser.new_context(viewport={"width": 360, "height": 740}, locale="pt-BR")
    page = ctx.new_page()
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio",
              wait_until="domcontentloaded", timeout=30000)
    tw.dispensar_nps(page)
    page.wait_for_timeout(6000)
    tw.dispensar_nps(page)

    # ponto 25% à esquerda dentro da aba (x≈270 ao invés do centro 300)
    info = page.evaluate(
        """()=>{
            const tab=[...document.querySelectorAll('*')].find(e=>
                (e.innerText||'').trim()==='Copiloto' && e.getBoundingClientRect().top>window.innerHeight-110);
            if(!tab) return null;
            const r=tab.getBoundingClientRect();
            const cx=r.left+r.width*0.2, cy=r.top+r.height*0.4;
            const alvo=document.elementFromPoint(cx,cy);
            return {cx,cy,quemRecebe:(alvo? alvo.tagName : 'nada')};
        }"""
    )
    print(f"[probe2] ponto à esquerda da aba: {info}")
    if info:
        page.mouse.click(info["cx"], info["cy"])
        page.wait_for_timeout(3500)
        aberto = page.locator(tid("copilot-drawer")).count() and page.locator(tid("copilot-drawer")).first.is_visible()
        print(f"[probe2] copiloto abriu (área/drawer)? {bool(aberto)}")
        corpo = page.evaluate("()=>document.body.innerText.includes('Copiloto do Estúdio')")
        print(f"[probe2] 'Copiloto do Estúdio' na tela? {corpo}")
        tw.snap(page, PASTA, "360-tab-copiloto-clique-esquerda")
    ctx.close(); browser.close()
