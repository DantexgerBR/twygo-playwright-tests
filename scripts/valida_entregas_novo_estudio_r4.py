# -*- coding: utf-8 -*-
"""Rodada 4 — fecha o item 04 (org 37061, curso 807533).
O form da atividade Externa tem sub-tabs 'Dados' e 'Conteúdo'. O link e o seletor
'Player do vídeo' (Player da Twygo / Player oficial do YouTube) ficam no 'Conteúdo'
e o seletor pode só aparecer ao colar um link do YouTube. Cleanup ao final."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "valida_entregas_novo_estudio"
CURSO = "807533"
YT = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    print(f"[ok] logado\n")

    ativ_id = None
    url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"
    try:
        for _ in range(3):
            page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
            tw.dispensar_nps(page)
            try:
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
                break
            except Exception:
                print("[retry] hidratação")
        page.wait_for_timeout(2000)
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(1000)
        page.locator(tid("creation-studio-type-selector-external")).first.click(timeout=8000)
        page.wait_for_timeout(4000)
        tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url)
        ativ_id = m.group(1) if m else None
        print(f"[ok] Externa criada: {ativ_id}")

        # ---- ir para o sub-tab 'Conteúdo' ----
        cont = page.get_by_role("tab", name=re.compile(r"^Conteúdo$", re.I))
        if not cont.count():
            cont = page.get_by_text(re.compile(r"^Conteúdo$", re.I))
        cont.first.click(timeout=8000, force=True)
        page.wait_for_timeout(3000)
        tw.dispensar_nps(page)
        tw.snap(page, PASTA, "04d-conteudo-vazio", full=True)

        # mapear inputs do sub-tab Conteúdo
        inputs = page.evaluate(
            """()=>[...document.querySelectorAll('input,textarea')]
                .filter(e=>e.offsetParent!==null)
                .map(e=>({type:e.type,name:e.name,ph:e.placeholder,testid:e.getAttribute('data-test-id')}))"""
        )
        print(f"[campos Conteúdo] {inputs}")

        # preencher o link com URL do YouTube
        link = page.locator(
            "input[placeholder*='link' i], input[placeholder*='url' i], input[placeholder*='vídeo' i], "
            "input[placeholder*='video' i], input[name*='url' i], input[name*='link' i]"
        ).filter(visible=True).first
        if not link.count():
            link = page.locator("input[type='url']:visible, input[type='text']:visible").first
        link.fill(YT, timeout=8000)
        link.press("Tab")
        page.wait_for_timeout(4000)
        tw.snap(page, PASTA, "04d-conteudo-com-link-youtube", full=True)

        corpo = page.evaluate("()=>document.body.innerText")
        tem_player = bool(re.search(r"Player do v[íi]deo", corpo, re.I))
        tem_twygo = bool(re.search(r"Player da Twygo", corpo, re.I))
        tem_youtube_oficial = bool(re.search(r"Player oficial do YouTube", corpo, re.I))
        labels = page.evaluate(
            """()=>[...document.querySelectorAll('label,legend,p,span,h3,h4,button')]
                .filter(e=>e.offsetParent!==null && /player|twygo|youtube|oficial/i.test(e.innerText||''))
                .map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).slice(0,30)"""
        )
        print(f"[labels player] {labels}")
        ok = tem_player and (tem_twygo or tem_youtube_oficial)
        print(f"\n=> ITEM 04: {'PASSOU ✅' if ok else 'FALHOU ❌'}")
        print(f"   'Player do vídeo'={tem_player} | 'Player da Twygo'={tem_twygo} | 'Player oficial do YouTube'={tem_youtube_oficial}")
    except Exception as e:
        print(f"=> ITEM 04: ERRO {e}")
    finally:
        if ativ_id:
            try:
                page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
                page.wait_for_timeout(2000)
                card = page.locator(tid(f"creation-studio-activity-card-{ativ_id}")).first
                card.scroll_into_view_if_needed()
                card.click(timeout=8000, force=True)
                page.wait_for_timeout(2500)
                page.locator(tid("creation-studio-preview-delete")).first.click(timeout=8000, force=True)
                page.wait_for_timeout(1500)
                page.locator(tid("creation-studio-preview-delete-dialog")).get_by_role(
                    "button", name=re.compile("^Excluir", re.I)).first.click(timeout=8000)
                page.wait_for_timeout(3000)
                print(f"[cleanup] atividade {ativ_id} excluída")
            except Exception as e:
                print(f"[cleanup] FALHOU ({e}) — excluir manualmente {ativ_id}")
    ctx.close(); browser.close()
