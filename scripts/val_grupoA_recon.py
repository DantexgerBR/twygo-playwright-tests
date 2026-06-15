# -*- coding: utf-8 -*-
"""Recon do curso 807533 p/ planejar o Grupo A: lista atividades (tipo, badges
pendentes), checa aba Modelo (cards/visualizar) e o kebab da listagem."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "val_retrabalhos_grupoA"
CURSO = "807533"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)

    # estúdio: atividades + badges pendentes
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio",
              wait_until="domcontentloaded", timeout=45000)
    tw.dispensar_nps(page)
    try:
        page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    ativs = page.evaluate(
        r"""()=>{const out=[];document.querySelectorAll('[data-test-id]').forEach(e=>{
            const m=(e.getAttribute('data-test-id')||'').match(/^creation-studio-activity-card-(\d+)$/);
            if(m)out.push({id:m[1],txt:(e.innerText||'').replace(/\s+/g,' ').trim().slice(0,90)});});return out;}"""
    )
    tem_pendentes = page.evaluate("()=>/pendentes?/i.test(document.body.innerText)")
    tem_aula = any("Aula" in a["txt"] for a in ativs)
    print(f"[807533] {len(ativs)} atividades | tem badge 'pendentes'? {tem_pendentes} | tem Aula? {tem_aula}")
    for a in ativs[:12]:
        print(f"   - {a['id']}: {a['txt']}")
    tw.snap(page, PASTA, "recon-estudio")

    # aba Modelo (19795)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=model",
              wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    modelo_botoes = page.evaluate(
        """()=>[...document.querySelectorAll('button,[role=button]')].filter(e=>e.offsetParent!==null)
            .map(e=>(e.innerText||e.getAttribute('aria-label')||'').replace(/\\s+/g,' ').trim())
            .filter(t=>/visualiz|selecionar|prever|olho|eye/i.test(t))"""
    )
    print(f"[19795 Modelo] botões visualizar/selecionar: {modelo_botoes}")
    tw.snap(page, PASTA, "recon-modelo")

    # kebab da listagem (20026)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin",
              wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    page.get_by_placeholder(re.compile("Pesquise", re.I)).first.fill("Construindo times de alta performance")
    page.wait_for_timeout(4000)
    page.get_by_text("more_vert", exact=True).last.click(timeout=6000, force=True)
    page.wait_for_timeout(1500)
    menu = page.evaluate(
        """()=>{const ms=[...document.querySelectorAll('[role=menu]')].filter(m=>{const s=getComputedStyle(m);return s.visibility==='visible'&&parseFloat(s.opacity)>0.5;});
            const m=ms[ms.length-1];return m?[...m.querySelectorAll('[role=menuitem]')].map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()):[];}"""
    )
    print(f"[20026 kebab] itens: {menu}")
    print(f"[20026 kebab] tem 'Atividades'? {any('Atividade' in x for x in menu)}")
    tw.snap(page, PASTA, "recon-kebab")
    ctx.close(); browser.close()
