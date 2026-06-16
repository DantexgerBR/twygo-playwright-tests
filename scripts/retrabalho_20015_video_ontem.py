# -*- coding: utf-8 -*-
"""20015 [P0] — Vídeo travado em processamento (PR #10688).
Abre as atividades de vídeo deixadas ONTEM no Studio do curso 807533 e confere
o estado ATUAL: player de vídeo carrega (processou) x mensagem "em processamento".
"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20015_video"
CURSO = "807533"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
URL = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"

# JS: lista cards de atividade (id + título/subtítulo) pra achar os de vídeo
JS_CARDS = (
    "()=>Array.from(document.querySelectorAll('[data-test-id^=\"creation-studio-activity-card-\"]'))"
    ".map(el=>({id:el.getAttribute('data-test-id').replace('creation-studio-activity-card-',''),"
    "txt:(el.innerText||'').replace(/\\s+/g,' ').trim()}))"
)

res = []
with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1500, height=900)
    tw.login(page, c)
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
        page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=25000)
        page.wait_for_timeout(3000)
        cards = page.evaluate(JS_CARDS)
        # filtra cards de vídeo (subtítulo "Video upload"/"Vídeo")
        videos = [cd for cd in cards if re.search(r"v[ií]deo upload|^v[ií]deo|qa20015", cd["txt"], re.I)]
        print(f"[info] {len(cards)} atividades; {len(videos)} de vídeo: {[(v['id'], v['txt'][:40]) for v in videos]}")
        tw.snap(page, PASTA, "00-lista-studio")

        for cd in videos:
            aid = cd["id"]
            try:
                page.goto(URL, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000)
                page.wait_for_timeout(2000)
                card = page.locator(tid(f"creation-studio-activity-card-{aid}")).first
                card.scroll_into_view_if_needed(); card.click(force=True, timeout=8000)
                page.wait_for_timeout(6000)  # deixa o preview carregar
                corpo = page.evaluate("()=>document.body.innerText")
                processando = bool(re.search(r"em processamento|processando|logo estar[aá]", corpo, re.I))
                tem_player = page.evaluate(
                    "()=>!!document.querySelector('video') || "
                    "[...document.querySelectorAll('iframe')].some(f=>/video|player|bunny|vimeo|mediadelivery/i.test(f.src||''))"
                )
                ok = tem_player and not processando
                print(f"  [video {aid}] '{cd['txt'][:35]}' -> player={tem_player} processando={processando} => {'OK' if ok else 'X'}")
                tw.snap(page, PASTA, f"video-{aid}", full=True)
                res.append((aid, cd["txt"][:35], ok, f"player={tem_player} processando={processando}"))
            except Exception as e:
                print(f"  [video {aid}] erro: {e}")
                res.append((aid, cd["txt"][:35], False, f"erro: {e}"))
    except Exception as e:
        print(f"ERRO geral: {e}"); tw.snap(page, PASTA, "99-erro")
    finally:
        print("\n=== RESUMO 20015 (vídeos de ontem) ===")
        algum_ok = any(ok for *_, ok, _ in [(a,t,o,d) for (a,t,o,d) in res])
        for aid, txt, ok, det in res:
            print(f"  video {aid} ({txt}): {'PROCESSOU ✅' if ok else 'TRAVADO/❌'} | {det}")
        print(f"=> algum vídeo processado? {any(o for _,_,o,_ in res)}")
        ctx.close(); browser.close()
