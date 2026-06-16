# -*- coding: utf-8 -*-
"""Recon 19794 — ver se NOVOEST tem brand logo e se há aula com vídeo renderizado
no Studio (pra validar logo no vídeo). PR #10611."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19794_logo"
tid = lambda v: f'[data-test-id="{v}"]'
c = tw.cfg("NOVOEST")
CURSO = "807533"
URL = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    try:
        # 1) brand kit / aparência tem logo?
        for path in (f"/o/{c['org_id']}/appearance", f"/o/{c['org_id']}/brands", f"/o/{c['org_id']}/configuracoes/aparencia"):
            try:
                page.goto(f"{c['base_url']}{path}", wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(2500)
                if page.url and "404" not in page.evaluate("()=>document.body.innerText").lower()[:200]:
                    print(f"[brand] {path} -> {page.url}")
                    break
            except Exception: pass
        tw.snap(page, PASTA, "00-aparencia")
        logos = page.evaluate(r"""()=>[...document.querySelectorAll('img')].map(i=>i.src).filter(s=>/logo|brand|main_logo/i.test(s)).slice(0,8)""")
        print(f"[brand] imgs logo: {logos}")

        # 2) Studio: listar atividades de Aula e checar se têm vídeo/preview
        page.goto(URL, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
        page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000); page.wait_for_timeout(2500)
        cards = page.evaluate(
            "()=>Array.from(document.querySelectorAll('[data-test-id^=\"creation-studio-activity-card-\"]'))"
            ".filter(e=>/^creation-studio-activity-card-\\d+$/.test(e.getAttribute('data-test-id')))"
            ".map(e=>({id:e.getAttribute('data-test-id').replace('creation-studio-activity-card-',''),txt:(e.innerText||'').replace(/\\s+/g,' ').trim().slice(0,50)}))"
        )
        aulas = [cd for cd in cards if re.search(r"aula", cd["txt"], re.I)]
        print(f"[studio] {len(cards)} atividades; aulas: {[(a['id'],a['txt']) for a in aulas][:8]}")
        # abrir a 1a aula e ver se renderiza vídeo/preview + logo
        if aulas:
            aid = aulas[0]["id"]
            card = page.locator(tid(f"creation-studio-activity-card-{aid}")).first
            card.scroll_into_view_if_needed(); card.click(force=True, timeout=8000)
            page.wait_for_timeout(6000)
            tem_video = page.evaluate("()=>!!document.querySelector('video')||[...document.querySelectorAll('iframe')].some(f=>/video|player|bunny|mediadelivery/i.test(f.src||''))")
            tem_render = bool(re.search(r"renderiz|gerar v[ií]deo|gerando", page.evaluate("()=>document.body.innerText"), re.I))
            print(f"[studio] aula {aid}: tem_video={tem_video} tem_acao_render={tem_render}")
            tw.snap(page, PASTA, "01-aula-preview", full=True)
        else:
            print("[studio] nenhuma aula encontrada")
    except Exception as e:
        print(f"ERRO: {e}"); tw.snap(page, PASTA, "99-erro")
    finally:
        ctx.close(); browser.close()
