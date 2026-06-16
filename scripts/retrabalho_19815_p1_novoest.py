# -*- coding: utf-8 -*-
"""19815 P1 — re-teste no NOVOEST 37061 após habilitar a flag marca_dagua.
Cria atividade de vídeo no Studio (curso 807533), aba Conteúdo, e checa o checkbox
"Habilitar marca d'água no vídeo" após "Segurança do arquivo". PR #10679."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19815_marca_dagua"
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
        print(f"[P1] atividade vídeo {aid}")
        page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True); page.wait_for_timeout(3000)
        for _ in range(7): page.mouse.wheel(0, 1200); page.wait_for_timeout(400)
        corpo = page.evaluate("()=>document.body.innerText")
        tem_seg = bool(re.search(r"Seguran[çc]a do arquivo", corpo, re.I))
        tem_marca = bool(re.search(r"marca d'?\s*[aá]gua", corpo, re.I))
        # checar ordem: marca aparece DEPOIS de Segurança?
        ordem_ok = False
        if tem_seg and tem_marca:
            i_seg = re.search(r"Seguran[çc]a do arquivo", corpo, re.I).start()
            i_marca = re.search(r"marca d'?\s*[aá]gua", corpo, re.I).start()
            ordem_ok = i_marca > i_seg
        tw.snap(page, PASTA, "p1-novoest-conteudo", full=True)
        print(f"\n=> P1 (NOVOEST 37061, marca_dagua ON): Segurança={tem_seg} | marca d'água={tem_marca} | marca_apos_seguranca={ordem_ok}")
        print(f"=> P1 {'PASSOU (checkbox de marca aparece no Studio após Segurança)' if (tem_marca and ordem_ok) else ('PASSOU (marca presente)' if tem_marca else 'FALHOU (sem checkbox de marca no Studio)')}")
    except Exception as e:
        print(f"[P1] ERRO {e}"); tw.snap(page, PASTA, "p1-novoest-erro")
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
