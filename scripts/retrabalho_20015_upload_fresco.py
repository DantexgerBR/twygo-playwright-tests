# -*- coding: utf-8 -*-
"""20015 [P0] — Validação definitiva do fix #10688: upload FRESCO de vídeo no
Studio agora e poll do processamento. Se um vídeo recém-enviado processa, o fix
funciona (vídeos travados antigos são leftovers pré-deploy). Mantém a atividade
no fim p/ evidência (cleanup manual depois)."""
import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20015_video"
CURSO = "807533"
VIDEO = str(tw.ROOT / "evidencias" / "_assets_teste" / "video_teste_5s.mp4")
TITULO = "QA20015 FRESCO 1606"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
URL = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"

def player_ok(page):
    return page.evaluate(
        "()=>{const v=document.querySelector('video');"
        "const ifr=[...document.querySelectorAll('iframe')].some(f=>/video|player|bunny|vimeo|mediadelivery|iframe.media/i.test(f.src||''));"
        "return !!v||ifr;}"
    )

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    aid = None
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
        page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=25000)
        page.wait_for_timeout(2500)
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(800)
        page.locator(tid("creation-studio-type-selector-video")).first.click(timeout=8000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url); aid = m.group(1) if m else None
        print(f"[ok] atividade vídeo criada: {aid}")
        try: page.locator('input[name="title"]:visible').first.fill(TITULO)
        except Exception: pass
        # aba Conteúdo -> upload
        page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True)
        page.wait_for_timeout(2000)
        try:
            page.get_by_role("button", name=re.compile(r"Enviar arquivo|upload", re.I)).first.click(timeout=5000)
            page.wait_for_timeout(2000)
        except Exception: pass
        page.locator('input[type=file]').last.set_input_files(VIDEO)
        page.wait_for_timeout(3000)
        tw.snap(page, PASTA, "fresco-01-upload")
        env = page.get_by_role("button", name=re.compile(r"^Enviar$", re.I)).first
        if env.count() and env.is_enabled(): env.click(timeout=6000)
        page.wait_for_timeout(8000); tw.dispensar_nps(page)
        sv = page.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first
        if sv.count() and sv.is_visible(): sv.click(timeout=8000); page.wait_for_timeout(6000)
        tw.dispensar_nps(page)
        print("[ok] enviado e salvo; iniciando poll (até 6min)")

        concluiu = False; estados = []; fim = time.time() + 360; i = 0
        while time.time() < fim:
            page.goto(URL, wait_until="domcontentloaded", timeout=30000); tw.dispensar_nps(page)
            try: page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
            except Exception: pass
            page.wait_for_timeout(2000)
            card = page.locator(tid(f"creation-studio-activity-card-{aid}")).first
            card.scroll_into_view_if_needed(); card.click(timeout=8000, force=True)
            page.wait_for_timeout(5000)
            corpo = page.evaluate("()=>document.body.innerText")
            proc = bool(re.search(r"em processamento|processando|logo estar[aá]", corpo, re.I))
            pl = player_ok(page)
            estados.append(f"t={i*30}s proc={proc} player={pl}")
            print(f"   [poll {i}] processando={proc} player={pl}")
            if pl and not proc:
                concluiu = True; break
            i += 1; page.wait_for_timeout(28000)
        tw.snap(page, PASTA, "fresco-02-final", full=True)
        print(f"\n=> 20015 FRESCO: {'PASSOU (processou)' if concluiu else 'FALHOU (travado >6min)'}")
        print(f"   atividade={aid} estados={estados}")
    except Exception as e:
        print(f"ERRO: {e}"); tw.snap(page, PASTA, "fresco-99-erro")
    finally:
        print(f"[nota] atividade {aid} mantida p/ evidência (excluir manualmente depois)")
        ctx.close(); browser.close()
