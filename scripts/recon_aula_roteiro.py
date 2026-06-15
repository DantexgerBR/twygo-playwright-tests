# -*- coding: utf-8 -*-
"""Recon do editor de Roteiro/cena da Aula (807533) p/ planejar 20000 (cena 5s) e
19797 (regerar roteiro vazio): abre uma aula, Conteúdo, seleciona uma parte e
mapeia o painel Roteiro, a duração da cena e ações de regerar."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "val_retrabalhos_grupoC"
CURSO = "807533"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=1000)
    tw.login(page, c)
    for _ in range(3):
        page.goto(url_studio, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
        try:
            page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000); break
        except Exception: pass
    page.wait_for_timeout(2500)
    aula = page.evaluate(
        r"""()=>{let r=null;document.querySelectorAll('[data-test-id]').forEach(e=>{const m=(e.getAttribute('data-test-id')||'').match(/^creation-studio-activity-card-(\d+)$/);if(m && /Aula/i.test(e.innerText||'') && !r) r=m[1];});return r;}"""
    )
    print(f"[aula] {aula}")
    page.goto(f"{c['base_url']}/o/{c['org_id']}/studio/activities/{aula}/edit?type=lesson&eventId={CURSO}",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True)
    page.wait_for_timeout(4000)
    tw.snap(page, PASTA, "recon-conteudo", full=True)

    # listar partes + durações
    partes = page.evaluate(
        r"""()=>{const out=[];document.querySelectorAll('*').forEach(e=>{const t=(e.innerText||'').trim();
            if(/^Duração:?\s*\d{2}:\d{2}:\d{2}$/.test(t) && e.children.length<3) out.push(t);});return out.slice(0,30);}"""
    )
    print(f"[durações das partes] {partes}")

    # selecionar a 1a parte e abrir painel Roteiro
    try:
        primeira = page.locator("[class*=part i], [data-test-id*=part], [data-test-id*=slide]").filter(visible=True).first
        primeira.click(timeout=5000, force=True)
        page.wait_for_timeout(2500)
    except Exception as e:
        print(f"[!] clicar parte: {e}")
    # abrir Roteiro
    try:
        page.get_by_text(re.compile(r"^Roteiro$", re.I)).first.click(timeout=5000, force=True)
        page.wait_for_timeout(2500)
    except Exception as e:
        print(f"[!] abrir Roteiro: {e}")
    tw.snap(page, PASTA, "recon-roteiro", full=True)
    painel = page.evaluate(
        """()=>{const vis=e=>e.offsetParent!==null;
            const btns=[...document.querySelectorAll('button,[role=button]')].filter(vis).map(e=>(e.innerText||e.getAttribute('aria-label')||'').replace(/\\s+/g,' ').trim()).filter(t=>/roteiro|regerar|gerar|áudio|audio|salvar|aplicar/i.test(t));
            const tas=[...document.querySelectorAll('textarea')].filter(vis).map(t=>({ph:t.placeholder,val:(t.value||'').slice(0,60)}));
            return {botoes:[...new Set(btns)], textareas:tas};}"""
    )
    print(f"[painel Roteiro] {painel}")
    ctx.close(); browser.close()
