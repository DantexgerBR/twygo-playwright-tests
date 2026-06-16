# -*- coding: utf-8 -*-
"""20015 [P0] — upload robusto: cria atividade de vídeo, anexa arquivo, ESPERA o
modal de upload fechar (archive criado), libera, salva, CONFIRMA que o vídeo
anexou (preview != "não tem conteúdo") e então faz poll do processamento.
"""
import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20015_video"
CURSO = "807533"
VIDEO = str(tw.ROOT / "evidencias" / "_assets_teste" / "video_teste_5s.mp4")
TITULO = "QA20015 ROBUSTO"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
URL = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"

def diag(page):
    corpo = page.evaluate("()=>document.body.innerText")
    return {
        "proc": bool(re.search(r"em processamento|processando|logo estar[aá]", corpo, re.I)),
        "vazio": bool(re.search(r"n[aã]o tem conte[uú]do|n[aã]o h[aá] conte[uú]do|Ops!", corpo, re.I)),
        "bloq": bool(re.search(r"n[aã]o foi liberado para estudo", corpo, re.I)),
        "player": page.evaluate("()=>!!document.querySelector('video')||[...document.querySelectorAll('iframe')].some(f=>/video|player|bunny|vimeo|mediadelivery/i.test(f.src||''))"),
    }

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
        print(f"[ok] atividade {aid}")
        try: page.locator('input[name="title"]:visible').first.fill(TITULO)
        except Exception: pass
        # aba Conteúdo
        page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True)
        page.wait_for_timeout(2000)
        # abrir modal de upload
        page.get_by_role("button", name=re.compile(r"Enviar arquivo", re.I)).first.click(timeout=6000)
        page.wait_for_timeout(1500)
        # anexar arquivo
        page.locator('input[type=file]').last.set_input_files(VIDEO)
        page.wait_for_timeout(2500)
        tw.snap(page, PASTA, "rob-01-arquivo-selecionado")
        # clicar Enviar (dentro do modal)
        page.get_by_role("button", name=re.compile(r"^Enviar$", re.I)).first.click(timeout=6000)
        # ESPERAR o modal de upload fechar (arquivo enviado ao servidor)
        fechou = False
        for _ in range(40):  # até ~40s
            page.wait_for_timeout(1000)
            vis = page.get_by_text(re.compile(r"Enviar arquivo", re.I)).count()
            modal_aberto = page.get_by_text(re.compile(r"Arraste o arquivo", re.I)).count()
            if modal_aberto == 0:
                fechou = True; break
        print(f"[upload] modal fechou={fechou}")
        page.wait_for_timeout(2000); tw.dispensar_nps(page)
        tw.snap(page, PASTA, "rob-02-pos-envio")
        # liberar (toggle) ANTES de salvar, se houver
        try:
            liberou = page.evaluate(
                "()=>{const b=[...document.querySelectorAll('button')].find(x=>/liberar atividade/i.test((x.getAttribute('aria-label')||'')+(x.title||'')));"
                "if(b){b.click();return true;}return false;}")
            print(f"[liberar pre-save] {liberou}")
        except Exception: pass
        page.wait_for_timeout(1500)
        # salvar
        sv = page.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first
        if sv.count() and sv.is_visible(): sv.click(timeout=8000); page.wait_for_timeout(6000)
        tw.dispensar_nps(page)
        print("[ok] salvo")

        # CONFIRMA anexação: reabrir card e ver diag
        def reabrir():
            page.goto(URL, wait_until="domcontentloaded", timeout=30000); tw.dispensar_nps(page)
            page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
            page.wait_for_timeout(2000)
            card = page.locator(tid(f"creation-studio-activity-card-{aid}")).first
            card.scroll_into_view_if_needed(); card.click(force=True, timeout=8000); page.wait_for_timeout(5000)
        reabrir()
        d0 = diag(page); print(f"[confirmacao] {d0}")
        # se ainda bloqueada, tentar liberar de novo
        if d0["bloq"]:
            page.evaluate("()=>{const b=[...document.querySelectorAll('button')].find(x=>/liberar atividade/i.test((x.getAttribute('aria-label')||'')+(x.title||'')));if(b)b.click();}")
            page.wait_for_timeout(2500); reabrir(); d0 = diag(page); print(f"[confirmacao pos-liberar] {d0}")
        if d0["vazio"]:
            print("=> ANEXACAO FALHOU (preview vazio) — automação não persistiu o vídeo. INCONCLUSIVO.")
            tw.snap(page, PASTA, "rob-03-vazio", full=True)
        else:
            # poll
            concluiu = False; estados = []; fim = time.time() + 300; i = 0
            while time.time() < fim:
                reabrir(); d = diag(page)
                estados.append(f"t={i*30}s {d}")
                print(f"   [poll {i}] {d}")
                if d["player"] and not d["proc"]:
                    concluiu = True; break
                i += 1; page.wait_for_timeout(28000)
            tw.snap(page, PASTA, "rob-04-final", full=True)
            print(f"\n=> 20015 ROBUSTO: {'PROCESSOU ✅ (fix OK)' if concluiu else 'TRAVADO EM PROCESSAMENTO ❌ (bug persiste)'}")
            print(f"   estados={estados}")
    except Exception as e:
        print(f"ERRO: {e}"); tw.snap(page, PASTA, "rob-99-erro")
    finally:
        print(f"[nota] atividade {aid} mantida p/ evidência")
        ctx.close(); browser.close()
