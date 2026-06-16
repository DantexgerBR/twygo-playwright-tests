# -*- coding: utf-8 -*-
"""20026 [P2] — Remover "Atividades" do kebab + "Editar" abre na última aba.
NOVOEST (org 37061), flag novo_estudio_criacao ON. PR #10694.
Valida:
  (1) kebab de um curso NÃO mostra mais a opção "Atividades";
  (2) "Editar" reabre na ÚLTIMA aba acessada (ex.: Estúdio), não fixo em Identificação.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20026_kebab_editar"
CURSO = "807533"
c = tw.cfg("NOVOEST")

LISTAGEM = f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin"

# JS: itens do menu Chakra atualmente visível
JS_MENU = (
    "()=>{const ms=Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
    "const s=getComputedStyle(m);return s.visibility==='visible'&&parseFloat(s.opacity)>0.5;});"
    "const m=ms[ms.length-1];return m?Array.from(m.querySelectorAll('[role=menuitem]'))"
    ".map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(Boolean):[];}"
)

# JS: aba ativa no editor (texto da tab com aria-selected=true)
JS_ABA_ATIVA = (
    "()=>{const t=document.querySelector('[role=tab][aria-selected=true]');"
    "return t?(t.innerText||'').replace(/\\s+/g,' ').trim():null;}"
)

res = {}

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    try:
        # ---------- PARTE 1: kebab sem "Atividades" ----------
        page.goto(LISTAGEM, wait_until="domcontentloaded", timeout=45000)
        tw.dispensar_nps(page)
        page.wait_for_timeout(4000)
        tw.snap(page, PASTA, "01-listagem")

        # localizar a linha/card do curso 807533 e abrir o kebab dele
        # tenta achar um link/elemento que referencie o curso e subir até a row
        kebab_aberto = False
        # estratégia A: âncora com o id do curso na href -> sobe pro container e acha more_vert
        try:
            anchor = page.locator(f'a[href*="/contents/{CURSO}"], a[href*="/events/{CURSO}"]').first
            if anchor.count():
                anchor.scroll_into_view_if_needed()
                row = anchor.locator(
                    "xpath=ancestor::tr[1] | xpath=ancestor::*[contains(@class,'card') or contains(@class,'row')][1]"
                ).first
                mv = row.get_by_text("more_vert", exact=True).first
                if mv.count():
                    mv.click(force=True)
                    kebab_aberto = True
        except Exception as e:
            print(f"[estrategiaA] {e}")

        # estratégia B: localizar texto do título e subir
        if not kebab_aberto:
            try:
                titulo = page.get_by_text(re.compile("Novo Est", re.I)).first
                titulo.scroll_into_view_if_needed()
                row = titulo.locator(
                    "xpath=ancestor::tr[1] | xpath=ancestor::*[contains(@class,'card') or contains(@class,'row')][1]"
                ).first
                mv = row.get_by_text("more_vert", exact=True).first
                mv.click(force=True)
                kebab_aberto = True
            except Exception as e:
                print(f"[estrategiaB] {e}")

        # estratégia C: primeiro more_vert da página (fallback)
        if not kebab_aberto:
            page.get_by_text("more_vert", exact=True).first.click(force=True)
            kebab_aberto = True

        page.wait_for_timeout(1200)
        itens = page.evaluate(JS_MENU)
        tw.snap(page, PASTA, "02-kebab-aberto")
        tem_atividades = any(re.search(r"^Atividades$", it, re.I) for it in itens)
        print(f"[P1] itens do kebab: {itens}")
        print(f"[P1] tem opção 'Atividades'? {tem_atividades}")
        res["P1_kebab_sem_atividades"] = (not tem_atividades, f"itens={itens}")

        # fechar menu
        page.keyboard.press("Escape")
        page.wait_for_timeout(800)

        # ---------- PARTE 2: "Editar" abre na última aba ----------
        # 2a) abrir editor, ir pra aba Estúdio, sair
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit",
                  wait_until="domcontentloaded", timeout=45000)
        tw.dispensar_nps(page)
        page.wait_for_timeout(4000)
        aba_inicial = page.evaluate(JS_ABA_ATIVA)
        print(f"[P2] aba ao abrir editor (1ª vez): {aba_inicial} | url={page.url}")
        tw.snap(page, PASTA, "03-editar-1a-vez")

        # clicar na aba Estúdio
        clicou_estudio = False
        for nome in ("Estúdio", "Estudio", "Studio"):
            try:
                tab = page.get_by_role("tab", name=re.compile(nome, re.I)).first
                if tab.count():
                    tab.click(timeout=5000)
                    clicou_estudio = True
                    break
            except Exception:
                pass
        page.wait_for_timeout(4000)  # tempo pra persistir last_tab
        aba_estudio = page.evaluate(JS_ABA_ATIVA)
        print(f"[P2] após clicar Estúdio: aba ativa={aba_estudio} url={page.url} (clicou={clicou_estudio})")
        tw.snap(page, PASTA, "04-aba-estudio")

        # 2b) sair pra listagem e reabrir o editor
        page.goto(LISTAGEM, wait_until="domcontentloaded", timeout=45000)
        tw.dispensar_nps(page)
        page.wait_for_timeout(3000)
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit",
                  wait_until="domcontentloaded", timeout=45000)
        tw.dispensar_nps(page)
        page.wait_for_timeout(4500)
        aba_reabertura = page.evaluate(JS_ABA_ATIVA)
        print(f"[P2] aba ao reabrir editor (2ª vez): {aba_reabertura} | url={page.url}")
        tw.snap(page, PASTA, "05-editar-2a-vez")

        voltou_estudio = bool(aba_reabertura and re.search(r"est.dio|studio", aba_reabertura, re.I))
        res["P2_editar_ultima_aba"] = (
            voltou_estudio,
            f"1a_vez={aba_inicial} | apos_estudio={aba_estudio} | reabertura={aba_reabertura}",
        )

    except Exception as e:
        print(f"=> 20026 ERRO: {e}")
        tw.snap(page, PASTA, "99-erro")
    finally:
        print("\n=== RESUMO 20026 ===")
        for k, (ok, det) in res.items():
            print(f"  {k}: {'PASSOU' if ok else 'FALHOU'} | {det}")
        ctx.close()
        browser.close()
