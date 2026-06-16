# -*- coding: utf-8 -*-
"""19815 P1 v2 — Studio 19653: click REAL do Playwright no 'Editar' do kebab
(dispara navegação React); fallback: extrair id do conteúdo da linha."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19815_marca_dagua"
tid = lambda v: f'[data-test-id="{v}"]'
c = tw.cfg("MIGR")  # 19653
LIST = f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    aid = None; cid = None
    try:
        page.goto(LIST, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page); page.wait_for_timeout(4000)
        # tentativa 1: kebab -> click REAL no menuitem Editar
        page.get_by_text("more_vert", exact=True).first.click(force=True); page.wait_for_timeout(1200)
        try:
            page.get_by_role("menuitem", name=re.compile("Editar", re.I)).first.click(timeout=5000)
            try: page.wait_for_url(re.compile(r"/contents/\d+"), timeout=12000)
            except Exception: pass
        except Exception as e:
            print(f"[P1] click Editar: {e}")
        m = re.search(r"/contents/(\d+)", page.url); cid = m.group(1) if m else None
        print(f"[P1] apos Editar: cid={cid} url={page.url}")

        # fallback: extrair id de qualquer atributo/href da 1a linha
        if not cid:
            page.goto(LIST, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page); page.wait_for_timeout(3000)
            cid = page.evaluate(r"""()=>{
              // procurar ids em hrefs, data-*, onclick
              const rx=/(?:contents?|events?|courses?)\D{0,3}(\d{5,})/i;
              for(const el of document.querySelectorAll('a,[href],[data-id],[data-href],[onclick],tr,div')){
                const s=(el.getAttribute&&((el.getAttribute('href')||'')+' '+(el.getAttribute('data-id')||'')+' '+(el.getAttribute('data-href')||'')+' '+(el.getAttribute('onclick')||'')))||'';
                const m=s.match(rx); if(m) return m[1];
              }
              return null;
            }""")
            print(f"[P1] fallback cid={cid}")

        if not cid:
            raise RuntimeError(f"sem cid (url={page.url})")

        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{cid}/edit?tab=studio",
                  wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
        page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000); page.wait_for_timeout(2000)
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000); page.wait_for_timeout(800)
        page.locator(tid("creation-studio-type-selector-video")).first.click(timeout=8000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url); aid = m.group(1) if m else None
        print(f"[P1] atividade vídeo {aid}")
        page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True); page.wait_for_timeout(2500)
        for _ in range(6): page.mouse.wheel(0, 1200); page.wait_for_timeout(400)
        corpo = page.evaluate("()=>document.body.innerText")
        tem_seg = bool(re.search(r"Seguran[çc]a do arquivo", corpo, re.I))
        tem_marca = bool(re.search(r"marca d'?\s*[aá]gua", corpo, re.I))
        tw.snap(page, PASTA, "p1-19653-studio-conteudo", full=True)
        print(f"\n=> P1 (19653): Segurança={tem_seg} | marca d'água={tem_marca}")
        print(f"=> P1 {'PASSOU' if tem_marca else 'FALHOU'} (cid={cid})")
    except Exception as e:
        print(f"[P1] ERRO {e}"); tw.snap(page, PASTA, "p1-19653-erro2")
    finally:
        if aid and cid:
            try:
                page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{cid}/edit?tab=studio", wait_until="domcontentloaded", timeout=30000)
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000); page.wait_for_timeout(2000)
                cd = page.locator(tid(f"creation-studio-activity-card-{aid}")).first
                cd.scroll_into_view_if_needed(); cd.click(force=True, timeout=8000); page.wait_for_timeout(1500)
                page.locator(tid("creation-studio-preview-delete")).first.click(force=True, timeout=8000); page.wait_for_timeout(1200)
                page.locator(tid("creation-studio-preview-delete-dialog")).get_by_role("button", name=re.compile("^Excluir", re.I)).first.click(timeout=8000); page.wait_for_timeout(2000)
                print(f"[P1 cleanup] {aid}")
            except Exception as e:
                print(f"[P1 cleanup manual] {aid} ({e})")
        ctx.close(); browser.close()
