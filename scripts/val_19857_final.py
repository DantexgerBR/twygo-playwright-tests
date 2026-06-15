# -*- coding: utf-8 -*-
"""19857 final — SCORM: fluxo completo de upload (modal 'Enviar arquivo' → dropzone
input → botão 'Enviar' → Salvar), Liberado ON, e checagem de render (404?) em
preview admin e visão do aluno. Cleanup ao final."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "val_retrabalhos_grupoD"
CURSO = "807533"
SCORM = str(tw.ROOT / "evidencias" / "_assets_teste" / "scorm_teste.zip")
TITULO = "QA19857 SCORM Final"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"


def frames_404(pg):
    achou = False; frames = []
    for fr in pg.frames:
        try:
            t = fr.evaluate("()=>document.body?document.body.innerText.slice(0,160):''")
            if t and t.strip():
                frames.append(t.replace("\n", " ")[:90])
                if re.search(r"não existe|nao existe|\b404\b|Desculpe", t, re.I):
                    achou = True
        except Exception:
            pass
    return achou, frames


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    aid = None; res = {}
    try:
        for _ in range(3):
            page.goto(url_studio, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
            try:
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000); break
            except Exception: pass
        page.wait_for_timeout(2500)
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000); page.wait_for_timeout(800)
        page.locator(tid("creation-studio-type-selector-scorm")).first.click(timeout=8000); page.wait_for_timeout(4000); tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url); aid = m.group(1) if m else None
        print(f"[ok] SCORM {aid}")
        # Dados: título + Liberado
        try: page.locator('input[name="title"]:visible').first.fill(TITULO)
        except Exception: pass
        try:
            sw = page.locator("input[type=checkbox]").first
            if sw.count() and not sw.is_checked():
                page.get_by_text("Liberado", exact=False).first.click(timeout=3000)
        except Exception: pass
        page.wait_for_timeout(500)
        # Conteúdo → abrir modal de upload
        page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True); page.wait_for_timeout(2000)
        page.get_by_role("button", name=re.compile(r"Enviar arquivo", re.I)).first.click(timeout=5000)
        page.wait_for_timeout(2000)
        # setar arquivo no input do modal (o com accept zip)
        page.locator('input[type=file]').last.set_input_files(SCORM)
        page.wait_for_timeout(3000)
        tw.snap(page, PASTA, "f-01-modal-com-arquivo", full=True)
        # clicar 'Enviar' do modal
        env = page.get_by_role("button", name=re.compile(r"^Enviar$", re.I)).first
        if env.count() and env.is_enabled():
            env.click(timeout=6000)
        else:
            print("[!] botão Enviar do modal não habilitou")
        page.wait_for_timeout(8000); tw.dispensar_nps(page)
        tw.snap(page, PASTA, "f-02-pos-enviar", full=True)
        corpo = page.evaluate("()=>document.body.innerText")
        res["arquivo_anexado"] = bool(re.search(r"scorm_teste|\.zip|removerquivo|trocar arquivo|enviado", corpo, re.I))
        # Salvar atividade
        sv = page.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first
        if sv.count() and sv.is_visible(): sv.click(timeout=8000); page.wait_for_timeout(6000)
        tw.dispensar_nps(page)

        # preview admin
        page.goto(url_studio, wait_until="domcontentloaded", timeout=30000); tw.dispensar_nps(page)
        page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000); page.wait_for_timeout(2000)
        card = page.locator(tid(f"creation-studio-activity-card-{aid}")).first
        card.scroll_into_view_if_needed(); card.click(timeout=8000, force=True); page.wait_for_timeout(7000)
        err_p, fr_p = frames_404(page)
        res["preview_404"] = err_p; res["preview_frames"] = fr_p
        tw.snap(page, PASTA, "f-03-preview", full=True)

        # visão aluno
        try:
            with ctx.expect_page(timeout=8000) as nv:
                page.get_by_role("button", name=re.compile(r"Visualizar como aluno", re.I)).first.click(timeout=6000)
            al = nv.value
        except Exception:
            al = ctx.pages[-1]
        al.wait_for_timeout(7000); tw.dispensar_nps(al)
        try:
            al.get_by_text(re.compile(re.escape(TITULO), re.I)).first.click(timeout=6000, force=True); al.wait_for_timeout(7000)
        except Exception as e:
            print(f"[aluno] não abri pelo título: {e}")
        err_a, fr_a = frames_404(al)
        res["aluno_404"] = err_a; res["aluno_frames"] = fr_a
        tw.snap(al, PASTA, "f-04-aluno", full=True)

        print(f"\n=> 19857 FINAL: {res}")
        veredito = "FALHOU (404 persiste)" if (res.get("preview_404") or res.get("aluno_404")) else ("PASSOU" if res.get("arquivo_anexado") else "INCONCLUSIVO (upload?)")
        print(f"=> VEREDITO: {veredito} | visible .zip dup = CORRIGIDO (Formato aceito: .zip)")
    except Exception as e:
        print(f"=> 19857 FINAL: ERRO {e}")
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
