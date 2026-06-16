# -*- coding: utf-8 -*-
"""19815 P1 (PR #10679) — Studio do 19653 (novo_estudio ON): atividade de vídeo,
aba Conteúdo, checar checkbox de marca d'água após "Segurança do arquivo"."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19815_marca_dagua"
tid = lambda v: f'[data-test-id="{v}"]'
c = tw.cfg("MIGR")  # 19653

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    aid = None; cid = None
    try:
        page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin",
                  wait_until="domcontentloaded", timeout=45000)
        tw.dispensar_nps(page); page.wait_for_timeout(4000)
        # kebab do 1o curso -> Editar (menuitem "edit Editar")
        page.get_by_text("more_vert", exact=True).first.click(force=True); page.wait_for_timeout(1200)
        clicou = page.evaluate(
            "()=>{const ms=[...document.querySelectorAll('[role=menu]')].filter(m=>{const s=getComputedStyle(m);return s.visibility==='visible'&&parseFloat(s.opacity)>0.5;});"
            "const m=ms[ms.length-1];if(!m)return null;const it=[...m.querySelectorAll('[role=menuitem]')].find(e=>/editar/i.test(e.innerText||''));"
            "if(it){it.click();return it.innerText.trim();}return null;}")
        print(f"[P1] cliquei menuitem: {clicou}")
        page.wait_for_timeout(4500); tw.dispensar_nps(page)
        m = re.search(r"/contents/(\d+)", page.url); cid = m.group(1) if m else None
        print(f"[P1] cid={cid} url={page.url}")
        if not cid:
            raise RuntimeError(f"sem cid (url={page.url})")
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{cid}/edit?tab=studio",
                  wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
        page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000)
        page.wait_for_timeout(2000)
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(800)
        page.locator(tid("creation-studio-type-selector-video")).first.click(timeout=8000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url); aid = m.group(1) if m else None
        print(f"[P1] atividade vídeo {aid}")
        page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True)
        page.wait_for_timeout(2500)
        for _ in range(6):
            page.mouse.wheel(0, 1200); page.wait_for_timeout(400)
        corpo = page.evaluate("()=>document.body.innerText")
        tem_seg = bool(re.search(r"Seguran[çc]a do arquivo", corpo, re.I))
        tem_marca = bool(re.search(r"marca d'?\s*[aá]gua", corpo, re.I))
        tw.snap(page, PASTA, "p1-19653-studio-conteudo", full=True)
        print(f"\n=> P1 (19653): Segurança do arquivo={tem_seg} | marca d'água={tem_marca}")
        print(f"=> P1 {'PASSOU (checkbox marca aparece no Studio)' if tem_marca else 'FALHOU (sem marca no Studio)'}")
    except Exception as e:
        print(f"[P1] ERRO {e}"); tw.snap(page, PASTA, "p1-19653-erro")
    finally:
        if aid and cid:
            try:
                url = f"{c['base_url']}/o/{c['org_id']}/contents/{cid}/edit?tab=studio"
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000); page.wait_for_timeout(2000)
                cd = page.locator(tid(f"creation-studio-activity-card-{aid}")).first
                cd.scroll_into_view_if_needed(); cd.click(force=True, timeout=8000); page.wait_for_timeout(1500)
                page.locator(tid("creation-studio-preview-delete")).first.click(force=True, timeout=8000); page.wait_for_timeout(1200)
                page.locator(tid("creation-studio-preview-delete-dialog")).get_by_role("button", name=re.compile("^Excluir", re.I)).first.click(timeout=8000); page.wait_for_timeout(2000)
                print(f"[P1 cleanup] {aid}")
            except Exception as e:
                print(f"[P1 cleanup manual] {aid} ({e})")
        ctx.close(); browser.close()
