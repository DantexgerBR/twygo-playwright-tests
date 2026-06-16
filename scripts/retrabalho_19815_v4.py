# -*- coding: utf-8 -*-
"""19815 v4 (PR #10679).
P2 (editor legado 36675): react-select "Informações a exibir" — selecionar um
   campo novo e confirmar que checkbox/campos da marca NÃO somem.
P1 (Studio 19653, novo_estudio ON): abrir curso via kebab Editar, criar atividade
   de vídeo, aba Conteúdo, checar checkbox de marca d'água após "Segurança do arquivo".
"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19815_marca_dagua"
tid = lambda v: f'[data-test-id="{v}"]'
res = {}
JS_SECAO = r"""()=>{const txt=document.body.innerText;return{
  checkbox:!!document.querySelector('#water-mark-video-enabled')||/Habilitar marca d'?\s*[aá]gua no v[ií]deo/i.test(txt),
  infoExibir:/Informa[çc][õo]es a exibir/i.test(txt),tamFonte:/Tamanho da fonte/i.test(txt),
  corFonte:/Cor da fonte/i.test(txt),posicao:/Posi[çc][ãa]o/i.test(txt),tipoExib:/Tipo de exibi[çc][ãa]o/i.test(txt)};}"""

def problema2():
    c = tw.cfg()  # 36675
    URL = f"{c['base_url']}/e/787696/contents/9280032/edit"
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
        tw.login(page, c, admin=False)
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000); tw.dispensar_nps(page)
            lbl = page.locator("label.chakra-checkbox", has_text="Habilitar marca d'água no vídeo")
            if lbl.count() and lbl.first.get_attribute("data-checked") is None:
                lbl.first.scroll_into_view_if_needed(); lbl.first.click(); page.wait_for_timeout(1500)
            antes = page.evaluate(JS_SECAO); print(f"[P2] ANTES: {antes}")
            tw.snap(page, PASTA, "v4-p2-01-antes")
            # control react-select que contém o chip "CPF" = "Informações a exibir"
            control = page.locator(".select-field__control").filter(
                has=page.locator(".select-field__multi-value__label", has_text=re.compile(r"^CPF$", re.I))).first
            print(f"[P2] controls select-field total={page.locator('.select-field__control').count()} | infoExibir achou={control.count()}")
            control.scroll_into_view_if_needed()
            # abrir dropdown
            try:
                control.locator(".select-field__dropdown-indicator").click(timeout=4000)
            except Exception:
                control.click(timeout=4000)
            page.wait_for_timeout(1000)
            tw.snap(page, PASTA, "v4-p2-02-dropdown")
            opcoes = page.locator(".select-field__option")
            textos = [opcoes.nth(i).inner_text().strip() for i in range(min(opcoes.count(), 12))]
            print(f"[P2] opções: {textos}")
            sel = None
            for i in range(opcoes.count()):
                t = opcoes.nth(i).inner_text().strip()
                if t and not re.search(r"^(CPF|E-?mail)$", t, re.I):
                    opcoes.nth(i).scroll_into_view_if_needed(); opcoes.nth(i).click(); sel = t; break
            print(f"[P2] selecionei: {sel}")
            page.wait_for_timeout(2500)
            tw.snap(page, PASTA, "v4-p2-03-apos", full=True)
            depois = page.evaluate(JS_SECAO); print(f"[P2] DEPOIS: {depois}")
            res["P2_editor_legado"] = (all(depois.values()) and sel is not None,
                                       f"selecionou={sel} opcoes={textos} | depois={depois}")
        except Exception as e:
            print(f"[P2] ERRO {e}"); tw.snap(page, PASTA, "v4-p2-99-erro")
            res["P2_editor_legado"] = (False, f"erro: {e}")
        finally:
            ctx.close(); browser.close()

def problema1():
    c = tw.cfg("MIGR")  # 19653, novo_estudio ON
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
        tw.login(page, c)
        aid = None; cid = None
        try:
            page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin",
                      wait_until="domcontentloaded", timeout=45000)
            tw.dispensar_nps(page); page.wait_for_timeout(4000)
            # abrir kebab do 1o curso -> Editar
            page.get_by_text("more_vert", exact=True).first.click(force=True); page.wait_for_timeout(1000)
            ed = page.get_by_role("menuitem", name=re.compile(r"^Editar$", re.I)).first
            ed.click(timeout=6000); page.wait_for_timeout(4500); tw.dispensar_nps(page)
            m = re.search(r"/contents/(\d+)", page.url); cid = m.group(1) if m else None
            print(f"[P1] editando cid={cid} url={page.url}")
            if not cid:
                raise RuntimeError(f"sem cid (url={page.url})")
            # ir pro studio
            page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{cid}/edit?tab=studio",
                      wait_until="domcontentloaded", timeout=45000); tw.dispensar_nps(page)
            page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000)
            page.wait_for_timeout(2000)
            # criar atividade de vídeo
            page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
            page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000)
            page.wait_for_timeout(800)
            page.locator(tid("creation-studio-type-selector-video")).first.click(timeout=8000)
            page.wait_for_timeout(4000); tw.dispensar_nps(page)
            m = re.search(r"/studio/activities/(\d+)/edit", page.url); aid = m.group(1) if m else None
            print(f"[P1] atividade vídeo {aid}")
            page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True)
            page.wait_for_timeout(2500)
            for _ in range(6):
                page.mouse.wheel(0, 1200); page.wait_for_timeout(400)
            corpo = page.evaluate("()=>document.body.innerText")
            tem_seg = bool(re.search(r"Seguran[çc]a do arquivo", corpo, re.I))
            tem_marca = bool(re.search(r"marca d'?\s*[aá]gua", corpo, re.I))
            tw.snap(page, PASTA, "v4-p1-studio-conteudo", full=True)
            print(f"[P1] (19653) Segurança={tem_seg} marca_dagua={tem_marca}")
            res["P1_studio_19653"] = (tem_marca, f"seguranca={tem_seg} marca={tem_marca} cid={cid}")
        except Exception as e:
            print(f"[P1] ERRO {e}"); tw.snap(page, PASTA, "v4-p1-erro")
            res["P1_studio_19653"] = (False, f"erro: {e}")
        finally:
            if aid and cid:
                try:
                    url = f"{c['base_url']}/o/{c['org_id']}/contents/{cid}/edit?tab=studio"
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000); page.wait_for_timeout(2000)
                    cd = page.locator(tid(f"creation-studio-activity-card-{aid}")).first
                    cd.scroll_into_view_if_needed(); cd.click(force=True, timeout=8000); page.wait_for_timeout(1500)
                    page.locator(tid("creation-studio-preview-delete")).first.click(force=True, timeout=8000); page.wait_for_timeout(1200)
                    page.locator(tid("creation-studio-preview-delete-dialog")).get_by_role("button", name=re.compile("^Excluir", re.I)).first.click(timeout=8000); page.wait_for_timeout(2000)
                    print(f"[P1 cleanup] {aid}")
                except Exception as e:
                    print(f"[P1 cleanup manual] {aid} ({e})")
            ctx.close(); browser.close()

if __name__ == "__main__":
    PASTA.mkdir(parents=True, exist_ok=True)
    problema2()
    problema1()
    print("\n=== RESUMO 19815 v4 ===")
    for k,(ok,det) in res.items():
        print(f"  {k}: {'PASSOU' if ok else 'FALHOU'} | {det}")
