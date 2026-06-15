# -*- coding: utf-8 -*-
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
c = tw.cfg("NOVOEST")
PASTA = tw.ROOT / "evidencias" / "val_retrabalhos_grupoA"
CURSO = "807533"
tid = lambda v: f'[data-test-id="{v}"]'
def aba_ativa(page):
    return page.evaluate("""()=>{
        const studio=!!document.querySelector('[data-test-id=creation-studio-activities-list]');
        const sel=[...document.querySelectorAll('[aria-selected=true],[role=tab][data-selected],.chakra-tabs__tab[aria-selected=true]')].map(e=>(e.innerText||'').trim()).filter(Boolean);
        // aba colorida (roxo) ativa por heurística de cor
        const tabs=[...document.querySelectorAll('p,span,button,[role=tab]')].filter(e=>e.offsetParent!==null && /^(Identificação|Modelo|Acesso|Atividades)$/.test((e.innerText||'').trim()));
        const ativa=tabs.find(e=>{const col=getComputedStyle(e).color;return /128|purple|rgb\(1[0-4]\d/i.test(col)|| e.className.includes('active');});
        return {studio, selByAria:sel, abaTextoAtiva: ativa?ativa.innerText.trim():null, url:location.href};
    }""")
with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    # 1) visitar studio (vira a "última aba")
    for _ in range(3):
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio", wait_until="domcontentloaded", timeout=45000)
        tw.dispensar_nps(page)
        try:
            page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000); break
        except Exception: pass
    page.wait_for_timeout(3000)
    print("apos ?tab=studio:", aba_ativa(page))
    # 2) abrir o /edit puro (como o botao Editar)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(6000); tw.dispensar_nps(page)
    est = aba_ativa(page)
    print("apos /edit puro:", est)
    tw.snap(page, PASTA, "20026-isolado")
    print("VEREDITO 20026:", "PASSOU (lembrou studio)" if est["studio"] else f"FALHOU/observar (abriu em {est['abaTextoAtiva']})")
    ctx.close(); browser.close()
