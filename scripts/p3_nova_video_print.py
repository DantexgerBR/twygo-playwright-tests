# -*- coding: utf-8 -*-
"""P3 — captura print do nome padrão errado "Nova Vídeo upload" / breadcrumb
"Atividades > Nova Vídeo" ao criar atividade de vídeo no Studio. Exclui depois."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_p3_nova_video"
tid = lambda v: f'[data-test-id="{v}"]'
c = tw.cfg("NOVOEST")
CURSO = "807533"
URL = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    aid = None
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
        page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=25000)
        page.wait_for_timeout(2500)
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000); page.wait_for_timeout(800)
        page.locator(tid("creation-studio-type-selector-video")).first.click(timeout=8000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url); aid = m.group(1) if m else None
        corpo = page.evaluate("()=>document.body.innerText")
        tem = bool(re.search(r"Nova\s+V[ií]deo", corpo))
        print(f"[P3] atividade {aid} | breadcrumb/título tem 'Nova Vídeo'? {tem}")
        tw.snap(page, PASTA, "p3-nova-video-nome-padrao", full=True)
        # print focado no topo (breadcrumb + título)
        page.screenshot(path=str(PASTA / "p3-nova-video-topo.png"), clip={"x": 240, "y": 60, "width": 1100, "height": 220})
        print("[P3] prints salvos")
    except Exception as e:
        print(f"ERRO: {e}"); tw.snap(page, PASTA, "p3-erro")
    finally:
        if aid:
            try:
                page.goto(URL, wait_until="domcontentloaded", timeout=30000)
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000); page.wait_for_timeout(2000)
                cd = page.locator(tid(f"creation-studio-activity-card-{aid}")).first
                cd.scroll_into_view_if_needed(); cd.click(force=True, timeout=8000); page.wait_for_timeout(1500)
                page.locator(tid("creation-studio-preview-delete")).first.click(force=True, timeout=8000); page.wait_for_timeout(1200)
                page.locator(tid("creation-studio-preview-delete-dialog")).get_by_role("button", name=re.compile("^Excluir", re.I)).first.click(timeout=8000); page.wait_for_timeout(2000)
                print(f"[cleanup] {aid}")
            except Exception as e:
                print(f"[cleanup manual] {aid} ({e})")
        ctx.close(); browser.close()
