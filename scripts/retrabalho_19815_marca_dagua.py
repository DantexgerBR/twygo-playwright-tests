# -*- coding: utf-8 -*-
"""19815 [P0] — Marca d'água com problemas (PR #10679).
Problema 1 (flag novo_estudio ON): checkbox "Habilitar marca d'água no vídeo"
  deve aparecer no Studio (aba Conteúdo, após "Segurança do arquivo").
  -> testado em NOVOEST (org 37061), flag ON.
Problema 2 (flag novo_estudio OFF, editor legado): ao selecionar um campo em
  "Informações a exibir", o checkbox e os campos NÃO podem sumir.
  -> testado na org principal 36675 (editor legado /e/.../edit), atividade 9280032.
"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19815_marca_dagua"
tid = lambda v: f'[data-test-id="{v}"]'
res = {}

# ---------------- PROBLEMA 1: Studio (flag ON) ----------------
def problema1():
    c = tw.cfg("NOVOEST")
    CURSO = "807533"
    URL = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
        tw.login(page, c)
        aid = None
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
            page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=25000)
            page.wait_for_timeout(2500)
            # cria atividade de vídeo nova
            page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
            page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000)
            page.wait_for_timeout(800)
            page.locator(tid("creation-studio-type-selector-video")).first.click(timeout=8000)
            page.wait_for_timeout(4000); tw.dispensar_nps(page)
            m = re.search(r"/studio/activities/(\d+)/edit", page.url); aid = m.group(1) if m else None
            print(f"[P1] atividade vídeo {aid}")
            # aba Conteúdo
            page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True)
            page.wait_for_timeout(3000)
            # rolar o painel até o fim pra revelar Segurança do arquivo + marca d'água
            for _ in range(6):
                page.mouse.wheel(0, 1200); page.wait_for_timeout(500)
            corpo = page.evaluate("()=>document.body.innerText")
            tem_seguranca = bool(re.search(r"Seguran[çc]a do arquivo", corpo, re.I))
            tem_marca = bool(re.search(r"marca d'?\s*[aá]gua", corpo, re.I))
            tw.snap(page, PASTA, "p1-studio-conteudo", full=True)
            print(f"[P1] 'Segurança do arquivo'={tem_seguranca} | 'marca d'água'={tem_marca}")
            res["P1_studio_checkbox"] = (tem_marca, f"seguranca={tem_seguranca} marca={tem_marca}")
        except Exception as e:
            print(f"[P1] ERRO {e}"); tw.snap(page, PASTA, "p1-erro")
            res["P1_studio_checkbox"] = (False, f"erro: {e}")
        finally:
            # cleanup da atividade criada
            if aid:
                try:
                    page.goto(URL, wait_until="domcontentloaded", timeout=30000)
                    page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
                    page.wait_for_timeout(2000)
                    cd = page.locator(tid(f"creation-studio-activity-card-{aid}")).first
                    cd.scroll_into_view_if_needed(); cd.click(force=True, timeout=8000); page.wait_for_timeout(1500)
                    page.locator(tid("creation-studio-preview-delete")).first.click(force=True, timeout=8000); page.wait_for_timeout(1200)
                    page.locator(tid("creation-studio-preview-delete-dialog")).get_by_role("button", name=re.compile("^Excluir", re.I)).first.click(timeout=8000)
                    page.wait_for_timeout(2000); print(f"[P1 cleanup] {aid}")
                except Exception as e:
                    print(f"[P1 cleanup manual] {aid} ({e})")
            ctx.close(); browser.close()

# ---------------- PROBLEMA 2: editor legado (flag OFF) ----------------
def problema2():
    c = tw.cfg()  # org principal 36675
    EVENTO = "787696"; ATIV = "9280032"
    URL = f"{c['base_url']}/e/{EVENTO}/contents/{ATIV}/edit"
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
        tw.login(page, c, admin=False)
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000); tw.dispensar_nps(page)
            cb = page.locator("#water-mark-video-enabled")
            lbl = page.locator("label.chakra-checkbox", has_text="Habilitar marca d'água no vídeo")
            cb_antes = lbl.count()
            print(f"[P2] checkbox marca d'água presente (antes): {cb_antes}")
            tw.snap(page, PASTA, "p2-01-antes", full=True)
            # garantir habilitado (pra revelar 'Informações a exibir')
            try:
                if lbl.count() and lbl.first.get_attribute("data-checked") is None:
                    lbl.first.scroll_into_view_if_needed(); lbl.first.click(); page.wait_for_timeout(1500)
            except Exception as e:
                print(f"[P2] toggle: {e}")
            tw.snap(page, PASTA, "p2-02-habilitado", full=True)
            # interagir com "Informações a exibir" (select-multi-static)
            campos_antes = page.evaluate("()=>document.querySelectorAll('input,select,label.chakra-checkbox').length")
            # abrir o select de "Informações a exibir" e escolher uma opção
            clicou_select = False
            try:
                # o controle costuma ter o label "Informações a exibir"
                ctrl = page.get_by_text(re.compile(r"Informa[çc][õo]es a exibir", re.I)).first
                ctrl.scroll_into_view_if_needed(); ctrl.click(timeout=4000); page.wait_for_timeout(800)
                # escolher primeira opção da lista que aparecer
                opt = page.locator("[role=option], .chakra-menu__menuitem, li").filter(
                    has_text=re.compile(r"nome|e-?mail|cpf|matr[ií]cula|empresa", re.I)).first
                if opt.count():
                    opt.click(timeout=4000); clicou_select = True
                page.wait_for_timeout(1500)
            except Exception as e:
                print(f"[P2] select: {e}")
            tw.snap(page, PASTA, "p2-03-apos-selecionar", full=True)
            # RE-VERIFICAR: checkbox e campos continuam presentes?
            cb_depois = page.locator("label.chakra-checkbox", has_text="Habilitar marca d'água no vídeo").count()
            campos_depois = page.evaluate("()=>document.querySelectorAll('input,select,label.chakra-checkbox').length")
            print(f"[P2] clicou_select={clicou_select} | checkbox depois={cb_depois} | campos antes={campos_antes} depois={campos_depois}")
            # PASSA se o checkbox NÃO sumiu e os campos não colapsaram
            nao_sumiu = cb_depois >= 1 and campos_depois >= max(3, campos_antes * 0.5)
            res["P2_editor_legado_nao_some"] = (
                nao_sumiu,
                f"checkbox_antes={cb_antes} depois={cb_depois} | campos {campos_antes}->{campos_depois} | clicou_select={clicou_select}",
            )
        except Exception as e:
            print(f"[P2] ERRO {e}"); tw.snap(page, PASTA, "p2-erro")
            res["P2_editor_legado_nao_some"] = (False, f"erro: {e}")
        finally:
            ctx.close(); browser.close()

if __name__ == "__main__":
    PASTA.mkdir(parents=True, exist_ok=True)
    problema1()
    problema2()
    print("\n=== RESUMO 19815 ===")
    for k, (ok, det) in res.items():
        print(f"  {k}: {'PASSOU' if ok else 'FALHOU'} | {det}")
