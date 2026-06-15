# -*- coding: utf-8 -*-
"""19857 v2 — SCORM: upload via file-chooser, Liberado ON, checa accept '.zip .zip',
preview admin e visão do aluno na atividade SCORM correta. Cleanup ao final."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "val_retrabalhos_grupoD"
CURSO = "807533"
SCORM = str(tw.ROOT / "evidencias" / "_assets_teste" / "scorm_teste.zip")
TITULO = "QA19857 SCORM Teste"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"


def iframe_ok(pg):
    """Procura iframe de SCORM renderizado (sem 404) em qualquer frame."""
    info = {"frames": [], "erro404": False, "scorm_txt": False}
    corpo = pg.evaluate("()=>document.body.innerText")
    info["erro404"] = bool(re.search(r"não existe|nao existe|\b404\b|Desculpe", corpo, re.I))
    for fr in pg.frames:
        try:
            t = fr.evaluate("()=>document.body?document.body.innerText.slice(0,200):''")
            if t and t.strip():
                info["frames"].append(t.replace("\n", " ")[:120])
                if re.search(r"SCORM de Teste|carregou e renderizou|Concluir", t, re.I):
                    info["scorm_txt"] = True
        except Exception:
            pass
    return info


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

        # Dados: título + Liberado ON
        try:
            page.locator('input[name="title"]:visible').first.fill(TITULO)
        except Exception:
            pass
        try:
            lib = page.get_by_text("Liberado", exact=False).first
            sw = page.locator("input[type=checkbox]").first  # toggle Liberado costuma ser o 1o switch
            if sw.count() and not sw.is_checked():
                lib.click(timeout=3000)
        except Exception:
            pass
        page.wait_for_timeout(500)

        # Conteúdo: upload via file-chooser
        page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True)
        page.wait_for_timeout(2500)
        # accept do input file (checar .zip duplicado)
        accept = page.evaluate("()=>{const i=document.querySelector('input[type=file]');return i?i.getAttribute('accept'):null;}")
        print(f"[19857a] accept do input file: {accept!r}")
        res["accept"] = accept
        res["zip_dup"] = bool(accept and len(re.findall(r"\.?zip", accept, re.I)) >= 2)
        # texto visível com .zip
        ztxt = page.evaluate(r"""()=>{const m=document.body.innerText.match(/[^\n]*\.?zip[^\n]*/gi);return m?m.join(' | '):'';}""")
        print(f"[19857a] texto com zip: {ztxt[:160]!r}")
        res["zip_dup_txt"] = bool(re.search(r"\.zip[\s,]+\.zip", ztxt, re.I))

        # upload: tentar file-chooser no botão 'Enviar arquivo'
        try:
            with page.expect_file_chooser(timeout=6000) as fcinfo:
                page.get_by_role("button", name=re.compile(r"Enviar arquivo", re.I)).first.click(timeout=5000)
            fcinfo.value.set_files(SCORM)
            print("[ok] arquivo via file-chooser")
        except Exception as e:
            print(f"[file-chooser falhou: {e}] tentando input direto")
            page.locator('input[type=file]').first.set_input_files(SCORM)
        page.wait_for_timeout(9000); tw.dispensar_nps(page)
        tw.snap(page, PASTA, "v2-01-pos-upload", full=True)

        salvar = page.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first
        if salvar.count() and salvar.is_visible():
            salvar.click(timeout=8000); page.wait_for_timeout(6000)
        tw.dispensar_nps(page)

        # preview admin
        page.goto(url_studio, wait_until="domcontentloaded", timeout=30000); tw.dispensar_nps(page)
        page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
        page.wait_for_timeout(2000)
        card = page.locator(tid(f"creation-studio-activity-card-{ativ_id}")).first
        card.scroll_into_view_if_needed(); card.click(timeout=8000, force=True)
        page.wait_for_timeout(6000)
        prev = iframe_ok(page)
        print(f"[19857b preview admin] {prev}")
        res["preview"] = prev
        tw.snap(page, PASTA, "v2-02-preview-admin", full=True)

        # visão do aluno — abrir a atividade SCORM pelo título
        try:
            with ctx.expect_page(timeout=8000) as nova:
                page.get_by_role("button", name=re.compile(r"Visualizar como aluno", re.I)).first.click(timeout=6000)
            aluno = nova.value
        except Exception:
            aluno = ctx.pages[-1]
        aluno.wait_for_timeout(7000); tw.dispensar_nps(aluno)
        try:
            aluno.get_by_text(re.compile(re.escape(TITULO), re.I)).first.click(timeout=6000, force=True)
            aluno.wait_for_timeout(7000)
        except Exception as e:
            print(f"   [aluno] não achei a atividade pelo título: {e}")
        al = iframe_ok(aluno)
        print(f"[19857b visão aluno] {al}")
        res["aluno"] = al
        tw.snap(aluno, PASTA, "v2-03-visao-aluno", full=True)

        print(f"\n=> 19857 v2 resumo: {res}")
    except Exception as e:
        print(f"=> 19857 v2: ERRO {e}")
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
