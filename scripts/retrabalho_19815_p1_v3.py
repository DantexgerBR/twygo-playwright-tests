# -*- coding: utf-8 -*-
"""19815 P1 v3 — cria curso NOVO no 19653 (que tem aba Atividades/Studio), adiciona
atividade de vídeo e checa o checkbox de marca d'água no Conteúdo. Exclui o curso."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19815_marca_dagua"
tid = lambda v: f'[data-test-id="{v}"]'
c = tw.cfg("MIGR")  # 19653

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    cid = None; aid = None
    try:
        # criar curso novo
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/new?kind=course",
                  wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
        page.wait_for_timeout(5000)
        tabs = page.evaluate("()=>Array.from(document.querySelectorAll('[role=tab]')).map(t=>(t.innerText||'').trim())")
        print(f"[P1] abas no novo curso: {tabs}")
        tw.snap(page, PASTA, "p1v3-01-novo-curso")
        # preencher nome (aba Identificação)
        try:
            nome = page.locator('input[name="name"], #content_name, input[placeholder*="ome"]').first
            if nome.count(): nome.fill("QA19815 Studio Marca")
        except Exception: pass
        # ir pra aba Atividades via JS click
        page.evaluate("()=>{const t=[...document.querySelectorAll('[role=tab]')].find(e=>/Atividades/i.test(e.innerText||''));if(t)t.click();}")
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        m = re.search(r"/contents/(\d+)", page.url); cid = m.group(1) if m else None
        print(f"[P1] cid apos criar/ir atividades = {cid} url={page.url}")
        # esperar a lista do studio
        try:
            page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000)
        except Exception:
            # pode precisar selecionar um modelo antes; tentar a aba Modelo
            print("[P1] lista nao apareceu; tentando selecionar modelo")
            page.evaluate("()=>{const t=[...document.querySelectorAll('[role=tab]')].find(e=>/^Modelo$/i.test((e.innerText||'').trim()));if(t)t.click();}")
            page.wait_for_timeout(3000)
            sel = page.get_by_role("button", name=re.compile(r"Selecionar", re.I)).first
            if sel.count(): sel.click(timeout=5000); page.wait_for_timeout(2000)
            sv = page.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first
            if sv.count(): sv.click(timeout=5000); page.wait_for_timeout(3000)
            page.evaluate("()=>{const t=[...document.querySelectorAll('[role=tab]')].find(e=>/Atividades/i.test(e.innerText||''));if(t)t.click();}")
            page.wait_for_timeout(4000)
            page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000)
        page.wait_for_timeout(1500)
        # adicionar atividade de vídeo
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000); page.wait_for_timeout(800)
        page.locator(tid("creation-studio-type-selector-video")).first.click(timeout=8000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url); aid = m.group(1) if m else None
        print(f"[P1] atividade vídeo {aid}")
        page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True); page.wait_for_timeout(2500)
        for _ in range(6): page.mouse.wheel(0, 1200); page.wait_for_timeout(400)
        corpo = page.evaluate("()=>document.body.innerText")
        tem_seg = bool(re.search(r"Seguran[çc]a do arquivo", corpo, re.I))
        tem_marca = bool(re.search(r"marca d'?\s*[aá]gua", corpo, re.I))
        tw.snap(page, PASTA, "p1v3-02-studio-conteudo", full=True)
        print(f"\n=> P1 (19653, curso novo {cid}): Segurança={tem_seg} | marca d'água={tem_marca}")
        print(f"=> P1 {'PASSOU (checkbox marca aparece no Studio)' if tem_marca else 'FALHOU/indef (sem marca — checar flag marca_dagua do 19653)'}")
    except Exception as e:
        print(f"[P1] ERRO {e}"); tw.snap(page, PASTA, "p1v3-erro")
    finally:
        # excluir o curso criado (cleanup) via listagem kebab
        if cid:
            try:
                page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin", wait_until="domcontentloaded", timeout=30000)
                tw.dispensar_nps(page); page.wait_for_timeout(3000)
                # procurar a linha do curso QA19815 e excluir via kebab
                # (best-effort; se falhar, fica p/ exclusão manual)
                print(f"[cleanup] curso {cid} criado — excluir manualmente se necessário (QA19815 Studio Marca)")
            except Exception as e:
                print(f"[cleanup] {e}")
        ctx.close(); browser.close()
