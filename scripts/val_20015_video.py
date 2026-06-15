# -*- coding: utf-8 -*-
"""20015 [P0] — Vídeo travado em 'processamento' indefinidamente após upload.
Cria atividade Vídeo, sobe video_teste_5s.mp4, salva e faz poll do preview por
~5min checando se o processamento conclui (player) ou trava. Cleanup ao final."""
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "val_retrabalhos_grupoD"
CURSO = "807533"
VIDEO = str(tw.ROOT / "evidencias" / "_assets_teste" / "video_teste_5s.mp4")
TITULO = "QA20015 Video Teste"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    aid = None; veredito = "?"
    try:
        for _ in range(3):
            page.goto(url_studio, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
            try:
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000); break
            except Exception: pass
        page.wait_for_timeout(2500)
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000); page.wait_for_timeout(800)
        page.locator(tid("creation-studio-type-selector-video")).first.click(timeout=8000); page.wait_for_timeout(4000); tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url); aid = m.group(1) if m else None
        print(f"[ok] Vídeo {aid}")
        try: page.locator('input[name="title"]:visible').first.fill(TITULO)
        except Exception: pass
        try:
            sw = page.locator("input[type=checkbox]").first
            if sw.count() and not sw.is_checked(): page.get_by_text("Liberado", exact=False).first.click(timeout=3000)
        except Exception: pass
        # Conteúdo → upload via modal
        page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True); page.wait_for_timeout(2000)
        try:
            page.get_by_role("button", name=re.compile(r"Enviar arquivo|upload", re.I)).first.click(timeout=5000)
            page.wait_for_timeout(2000)
        except Exception:
            pass
        page.locator('input[type=file]').last.set_input_files(VIDEO)
        page.wait_for_timeout(3000)
        tw.snap(page, PASTA, "vid-01-modal", full=True)
        env = page.get_by_role("button", name=re.compile(r"^Enviar$", re.I)).first
        if env.count() and env.is_enabled(): env.click(timeout=6000)
        page.wait_for_timeout(8000); tw.dispensar_nps(page)
        sv = page.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first
        if sv.count() and sv.is_visible(): sv.click(timeout=8000); page.wait_for_timeout(6000)
        tw.dispensar_nps(page)
        print("[ok] vídeo enviado e salvo; iniciando poll do processamento")

        # poll do preview por ~5min
        concluiu = False; estados = []
        fim = time.time() + 300
        i = 0
        while time.time() < fim:
            page.goto(url_studio, wait_until="domcontentloaded", timeout=30000); tw.dispensar_nps(page)
            try: page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
            except Exception: pass
            page.wait_for_timeout(2000)
            card = page.locator(tid(f"creation-studio-activity-card-{aid}")).first
            card.scroll_into_view_if_needed(); card.click(timeout=8000, force=True)
            page.wait_for_timeout(5000)
            corpo = page.evaluate("()=>document.body.innerText")
            processando = bool(re.search(r"em processamento|processando|logo estará", corpo, re.I))
            tem_video = page.evaluate("()=>!!document.querySelector('video') || [...document.querySelectorAll('iframe')].some(f=>/video|player/i.test(f.src||''))")
            estados.append(f"t={i*30}s proc={processando} video={tem_video}")
            print(f"   [poll {i}] processando={processando} | tem player de vídeo={tem_video}")
            if tem_video and not processando:
                concluiu = True; break
            i += 1
            page.wait_for_timeout(28000)
        tw.snap(page, PASTA, "vid-02-final", full=True)
        veredito = "PASSOU (processou e ficou disponível)" if concluiu else "FALHOU (travado em processamento >5min)"
        print(f"\n=> 20015: {veredito}\n   estados: {estados}")
    except Exception as e:
        print(f"=> 20015: ERRO {e}")
    finally:
        if aid:
            try:
                page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000); page.wait_for_timeout(2000)
                cd = page.locator(tid(f"creation-studio-activity-card-{aid}")).first
                cd.scroll_into_view_if_needed(); cd.click(timeout=8000, force=True); page.wait_for_timeout(2000)
                page.locator(tid("creation-studio-preview-delete")).first.click(timeout=8000, force=True); page.wait_for_timeout(1200)
                page.locator(tid("creation-studio-preview-delete-dialog")).get_by_role("button", name=re.compile("^Excluir", re.I)).first.click(timeout=8000); page.wait_for_timeout(2500); print(f"[cleanup] {aid}")
            except Exception as e:
                print(f"[cleanup] manual {aid} ({e})")
    ctx.close(); browser.close()
