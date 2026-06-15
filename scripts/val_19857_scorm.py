# -*- coding: utf-8 -*-
"""19857 — SCORM não funciona: (a) texto de extensões '.zip .zip' duplicado;
(b) preview admin e visão aluno não carregam (erro 404). Sobe scorm_teste.zip.
Cleanup ao final. (org 37061, curso 807533)"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "val_retrabalhos_grupoD"
CURSO = "807533"
SCORM = tw.ROOT / "evidencias" / "_assets_teste" / "scorm_teste.zip"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    ativ_id = None
    res = {}
    try:
        for _ in range(3):
            page.goto(url_studio, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
            try:
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000); break
            except Exception: pass
        page.wait_for_timeout(2500)
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(800)
        page.locator(tid("creation-studio-type-selector-scorm")).first.click(timeout=8000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url); ativ_id = m.group(1) if m else None
        print(f"[ok] SCORM criado: {ativ_id}")

        # ir para Conteúdo (área de upload)
        try:
            page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=5000, force=True)
            page.wait_for_timeout(2500)
        except Exception:
            pass
        tw.snap(page, PASTA, "01-scorm-upload-area", full=True)

        # (a) texto de extensões aceitas — checar duplicação .zip .zip
        ext_txt = page.evaluate(
            r"""()=>{const t=document.body.innerText;const m=t.match(/[^\n]*\.zip[^\n]*/gi);return m?m.join(' | '):'';}"""
        )
        dup_zip = bool(re.search(r"\.zip[\s,]+\.zip", ext_txt, re.I))
        print(f"[19857a] texto extensões: {ext_txt[:160]!r} | '.zip .zip' duplicado? {dup_zip}")
        res["ext_dup"] = dup_zip

        # upload do arquivo
        fi = page.locator('input[type="file"]').first
        fi.set_input_files(str(SCORM))
        print("[ok] arquivo enviado")
        page.wait_for_timeout(8000)
        tw.dispensar_nps(page)
        tw.snap(page, PASTA, "02-pos-upload", full=True)
        # salvar
        salvar = page.get_by_role("button", name=re.compile(r"^Salvar", re.I)).first
        if salvar.count() and salvar.is_visible():
            salvar.click(timeout=8000); page.wait_for_timeout(5000)
        tw.dispensar_nps(page)

        # (b) preview admin
        page.goto(url_studio, wait_until="domcontentloaded", timeout=30000); tw.dispensar_nps(page)
        page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
        page.wait_for_timeout(2000)
        card = page.locator(tid(f"creation-studio-activity-card-{ativ_id}")).first
        card.scroll_into_view_if_needed(); card.click(timeout=8000, force=True)
        page.wait_for_timeout(5000)
        corpo_prev = page.evaluate("()=>document.body.innerText")
        err_prev = bool(re.search(r"não existe|nao existe|404|Desculpe", corpo_prev, re.I))
        print(f"[19857b preview admin] erro/404? {err_prev}")
        res["preview_erro"] = err_prev
        tw.snap(page, PASTA, "03-preview-admin", full=True)

        # (b) visão do aluno
        try:
            with ctx.expect_page(timeout=8000) as nova:
                page.get_by_role("button", name=re.compile(r"Visualizar como aluno", re.I)).first.click(timeout=6000)
            aluno = nova.value
        except Exception:
            aluno = ctx.pages[-1]
        aluno.wait_for_timeout(7000); tw.dispensar_nps(aluno)
        # tentar abrir a atividade SCORM no player
        try:
            aluno.get_by_text(re.compile(r"SCORM|scorm_teste|Novo SCORM|Pacote", re.I)).first.click(timeout=5000, force=True)
            aluno.wait_for_timeout(6000)
        except Exception:
            pass
        corpo_aluno = aluno.evaluate("()=>document.body.innerText")
        err_aluno = bool(re.search(r"não existe|nao existe|404|Desculpe", corpo_aluno, re.I))
        carregou = bool(re.search(r"SCORM de Teste|carregou e renderizou|Concluir", corpo_aluno, re.I))
        print(f"[19857b visão aluno] erro/404? {err_aluno} | conteúdo SCORM carregou? {carregou}")
        res["aluno_erro"] = err_aluno; res["aluno_carregou"] = carregou
        tw.snap(aluno, PASTA, "04-visao-aluno", full=True)

        ok = (not res["ext_dup"]) and (not res["preview_erro"]) and (not res["aluno_erro"]) and res["aluno_carregou"]
        print(f"\n=> 19857: {'PASSOU' if ok else 'FALHOU'} | {res}")
    except Exception as e:
        print(f"=> 19857: ERRO {e}")
    finally:
        if ativ_id:
            try:
                page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
                page.wait_for_timeout(2000)
                card = page.locator(tid(f"creation-studio-activity-card-{ativ_id}")).first
                card.scroll_into_view_if_needed(); card.click(timeout=8000, force=True); page.wait_for_timeout(2000)
                page.locator(tid("creation-studio-preview-delete")).first.click(timeout=8000, force=True); page.wait_for_timeout(1200)
                page.locator(tid("creation-studio-preview-delete-dialog")).get_by_role("button", name=re.compile("^Excluir", re.I)).first.click(timeout=8000)
                page.wait_for_timeout(2500); print(f"[cleanup] {ativ_id} excluído")
            except Exception as e:
                print(f"[cleanup] excluir manualmente {ativ_id} ({e})")
    ctx.close(); browser.close()
