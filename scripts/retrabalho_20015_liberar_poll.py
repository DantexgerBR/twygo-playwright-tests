# -*- coding: utf-8 -*-
"""20015 — libera a atividade de vídeo já criada (9296301, vídeo anexado) e faz
poll do preview pra ver se PROCESSA (player) ou trava (em processamento)."""
import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20015_video"
CURSO = "807533"; AID = "9296301"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
URL = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"

def abrir_card(page):
    page.goto(URL, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
    page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000)
    page.wait_for_timeout(2500)
    card = page.locator(tid(f"creation-studio-activity-card-{AID}")).first
    card.scroll_into_view_if_needed(); card.click(force=True, timeout=8000)
    page.wait_for_timeout(5000)

def estado(page):
    corpo = page.evaluate("()=>document.body.innerText")
    proc = bool(re.search(r"em processamento|processando|logo estar[aá]", corpo, re.I))
    bloq = bool(re.search(r"n[aã]o foi liberado para estudo", corpo, re.I))
    pl = page.evaluate("()=>!!document.querySelector('video')||[...document.querySelectorAll('iframe')].some(f=>/video|player|bunny|vimeo|mediadelivery/i.test(f.src||''))")
    return proc, bloq, pl

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    try:
        abrir_card(page)
        proc, bloq, pl = estado(page)
        print(f"[inicial] processando={proc} bloqueada={bloq} player={pl}")
        tw.snap(page, PASTA, "lib-00-inicial")
        # se bloqueada, liberar: clicar no cadeado/ícone de status no topo do preview
        if bloq:
            liberou = page.evaluate(
                "()=>{const btns=[...document.querySelectorAll('button')];"
                "const alvo=btns.find(b=>/lock|liber|cadeado|bloq/i.test((b.getAttribute('aria-label')||'')+(b.title||'')+(b.innerText||'')));"
                "if(alvo){alvo.click();return (alvo.getAttribute('aria-label')||alvo.title||alvo.innerText||'botao').slice(0,40);}return null;}"
            )
            print(f"[liberar] cliquei: {liberou}")
            page.wait_for_timeout(3000); tw.dispensar_nps(page)
            # confirmar diálogo se houver
            try:
                page.get_by_role("button", name=re.compile(r"^(Liberar|Confirmar|Sim|Salvar)$", re.I)).first.click(timeout=3000)
                page.wait_for_timeout(2500)
            except Exception: pass
            tw.snap(page, PASTA, "lib-01-pos-liberar")
            abrir_card(page)
            proc, bloq, pl = estado(page)
            print(f"[pos-liberar] processando={proc} bloqueada={bloq} player={pl}")

        # poll até 5 min
        concluiu = False; estados = []; fim = time.time() + 300; i = 0
        while time.time() < fim:
            abrir_card(page)
            proc, bloq, pl = estado(page)
            estados.append(f"t={i*30}s proc={proc} bloq={bloq} player={pl}")
            print(f"   [poll {i}] processando={proc} bloqueada={bloq} player={pl}")
            if pl and not proc:
                concluiu = True; break
            if bloq:
                print("   [aviso] ainda bloqueada — liberação não pegou"); break
            i += 1; page.wait_for_timeout(28000)
        tw.snap(page, PASTA, "lib-02-final", full=True)
        print(f"\n=> 20015 (upload fresco liberado): {'PROCESSOU ✅' if concluiu else 'NAO PROCESSOU'}")
        print(f"   estados={estados}")
    except Exception as e:
        print(f"ERRO: {e}"); tw.snap(page, PASTA, "lib-99-erro")
    finally:
        ctx.close(); browser.close()
