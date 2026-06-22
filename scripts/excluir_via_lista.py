# -*- coding: utf-8 -*-
import os, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
c = tw.cfg("NOVOEST")
PASTA = tw.ROOT / "evidencias" / "qualidade_ia_cleanup"
RECON = os.environ.get("RECON") == "1"
CURSOS = {
    "Domine SQL Básico": "807992", "Git Essencial": "807993",
    "Segurança Essencial em Trabalho em Altura": "807994",
    "Atendimento ao Cliente: Excelência": "807995",
    "Lidere Equipes com Comunicação": "807996",
}
def kebab_menu(page):
    return page.evaluate("""()=>{const ms=Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{const s=getComputedStyle(m);return s.visibility==='visible'&&parseFloat(s.opacity)>0.5;});const m=ms[ms.length-1];return m?Array.from(m.querySelectorAll('[role=menuitem],button,a')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean):[];}""")
with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    itens = list(CURSOS.items())
    alvos = itens[:1] if RECON else itens
    for termo, cid in alvos:
        print(f"\n=== {termo} ({cid}) ===")
        page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        busca = page.get_by_placeholder(re.compile("Pesquise", re.I)).first
        busca.fill(termo); page.wait_for_timeout(4000)
        # kebab: ícone material 'more_vert' no fim da linha
        kb = page.get_by_text("more_vert", exact=True).last
        try:
            kb.click(timeout=6000, force=True); page.wait_for_timeout(1500)
        except Exception as e:
            print(f"  kebab err: {e}")
        menu = kebab_menu(page)
        print(f"  menu kebab: {menu}")
        tw.snap(page, PASTA, f"kebab-{cid}")
        if RECON: continue
        # clicar Excluir
        ex = page.get_by_role("menuitem", name=re.compile("Excluir|Remover", re.I)).first
        if not ex.count(): ex = page.get_by_text(re.compile("^Excluir$", re.I)).last
        ex.click(timeout=6000); page.wait_for_timeout(1500)
        conf = page.get_by_role("button", name=re.compile("^(Excluir|Confirmar|Sim)", re.I)).last
        conf.click(timeout=6000); page.wait_for_timeout(3000)
        tw.snap(page, PASTA, f"excluido-{cid}")
        print(f"  excluído {cid}")
    ctx.close(); browser.close()
