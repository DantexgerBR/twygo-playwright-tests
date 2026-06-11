# -*- coding: utf-8 -*-
"""19961 — sondagem da aba 'Copiloto' em 360px: o FAB flutuante sobrepõe a aba.
Clique físico nas coordenadas da aba (como o dedo do usuário) → quem recebe?"""
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

    info = page.evaluate(
        """()=>{
            const tab=[...document.querySelectorAll('*')].find(e=>
                (e.innerText||'').trim()==='Copiloto' && e.getBoundingClientRect().top>window.innerHeight-110);
            if(!tab) return null;
            const r=tab.getBoundingClientRect();
            const cx=r.left+r.width/2, cy=r.top+r.height/2;
            const alvo=document.elementFromPoint(cx,cy);
            return {cx,cy,tab:r, quemRecebe:(alvo? alvo.tagName+'.'+(alvo.className&&String(alvo.className).slice(0,40)) : 'nada'),
                    aria:alvo?alvo.closest('button')?.getAttribute('aria-label'):null};
        }"""
    )
    print(f"[probe] aba Copiloto: {info}")
    if info:
        page.mouse.click(info["cx"], info["cy"])
        page.wait_for_timeout(3500)
        drawer_aberto = page.locator(tid("copilot-drawer")).first.is_visible() if page.locator(tid("copilot-drawer")).count() else False
        corpo = page.evaluate("()=>{const e=document.querySelector('[data-test-id=copilot-drawer]');return e? 'drawer-visivel':'sem-drawer';}")
        print(f"[probe] após clique físico no centro da aba: copilot-drawer visível? {drawer_aberto} ({corpo})")
        tw.snap(page, PASTA, "360-tab-copiloto-clique-fisico")
    ctx.close(); browser.close()
