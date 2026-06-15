# -*- coding: utf-8 -*-
"""Valida 4 entregas do Novo Estúdio (org 37061 / NOVOEST), curso 807533:

  (11) Card "Curso" -> Estúdio: criação de curso exibe abas "Modelo" e "Atividades"
       (PR 10601).
  (18) FAB do copiloto renderiza na aba Identificação (PRs 10675/10677).
  (25) Section "Configurações de IA" presente na aba Identificação.
  (04) Atividade Externa tem campo "Player do vídeo" (Player da Twygo /
       Player oficial do YouTube), flag youtubePlayerOficialEnabled (PR 10645).

Cada item é isolado em try/except (falha de um não derruba os demais). O item 04
cria uma atividade Externa (clicar no tipo JÁ CRIA) e faz cleanup ao final.
Read-only nos itens 11/18/25.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "valida_entregas_novo_estudio"
CURSO = "807533"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'

resultado = {}  # item -> (passou:bool|None, detalhe:str)


def abas_visiveis(page):
    return page.evaluate(
        """()=>[...document.querySelectorAll("[role='tab'], .chakra-tabs__tab, [data-test-id^='tab-']")]
            .filter(e=>e.offsetParent!==null)
            .map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(Boolean)"""
    )


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    print(f"[ok] logado em {page.url}\n")

    # ===================================================================== #
    # ITEM 11 — criação de curso exibe abas "Modelo" e "Atividades"
    # ===================================================================== #
    print("### ITEM 11 — abas Modelo/Atividades na criação de curso")
    try:
        abas_por_rota = {}
        for rota in ["contents/new?kind=course", "contents/new?kind=0"]:
            page.goto(f"{c['base_url']}/o/{c['org_id']}/{rota}",
                      wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)
            tw.dispensar_nps(page)
            abas = abas_visiveis(page)
            abas_por_rota[rota] = abas
            print(f"   [{rota}] abas: {abas}")
        tw.snap(page, PASTA, "11-criacao-curso-abas")
        todas = [a.lower() for ab in abas_por_rota.values() for a in ab]
        tem_modelo = any("modelo" in a for a in todas)
        tem_ativ = any("atividade" in a for a in todas)
        ok = tem_modelo and tem_ativ
        det = f"Modelo={'SIM' if tem_modelo else 'NÃO'} | Atividades={'SIM' if tem_ativ else 'NÃO'} | abas={abas_por_rota}"
        resultado[11] = (ok, det)
        print(f"   => item 11: {'PASSOU' if ok else 'FALHOU'} | {det}\n")
    except Exception as e:
        resultado[11] = (False, f"erro: {e}")
        print(f"   => item 11: ERRO {e}\n")

    # ===================================================================== #
    # ITENS 18 e 25 — aba Identificação do editor: FAB copiloto + section IA
    # ===================================================================== #
    print("### ITENS 18/25 — aba Identificação (FAB copiloto + Configurações de IA)")
    try:
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit",
                  wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(6000)
        tw.dispensar_nps(page)
        # garantir que estamos na aba Identificação (clicar se existir)
        try:
            ident = page.get_by_text(re.compile(r"^Identifica", re.I)).first
            if ident.count() and ident.is_visible():
                ident.click(timeout=4000, force=True)
                page.wait_for_timeout(2500)
        except Exception:
            pass
        print(f"   url editor: {page.url}")
        print(f"   abas: {abas_visiveis(page)}")
        tw.snap(page, PASTA, "18-25-identificacao", full=True)

        # ---- item 18: FAB do copiloto ----
        fab = page.evaluate(
            """()=>{
                const els=[...document.querySelectorAll('button,[role=button],a,[data-test-id]')]
                  .filter(e=>e.offsetParent!==null);
                const cand=els.filter(e=>{
                    const id=(e.getAttribute('data-test-id')||'');
                    const al=(e.getAttribute('aria-label')||'');
                    const tt=(e.title||'');
                    return /copilot/i.test(id) || /copilot|copiloto/i.test(al) || /copilot|copiloto/i.test(tt);
                }).map(e=>({testid:e.getAttribute('data-test-id'),aria:e.getAttribute('aria-label'),
                            title:e.title, vis:e.offsetParent!==null}));
                return cand;
            }"""
        )
        # fallback explícito ao test-id conhecido do FAB
        fab_tid = page.locator(tid("copilot-fab")).first
        fab_tid_vis = fab_tid.count() > 0 and fab_tid.is_visible()
        ok18 = bool(fab) or fab_tid_vis
        det18 = f"copilot-fab visível={fab_tid_vis} | candidatos copiloto={fab}"
        resultado[18] = (ok18, det18)
        print(f"   => item 18: {'PASSOU' if ok18 else 'FALHOU'} | {det18}")

        # ---- item 25: section "Configurações de IA" ----
        corpo = page.evaluate("()=>document.body.innerText")
        tem_section = bool(re.search(r"Configura[çc][õo]es de IA", corpo, re.I))
        # localizar o elemento pra screenshot focado
        if tem_section:
            try:
                sec = page.get_by_text(re.compile(r"Configura[çc][õo]es de IA", re.I)).first
                sec.scroll_into_view_if_needed()
                page.wait_for_timeout(800)
                tw.snap(page, PASTA, "25-configuracoes-ia")
            except Exception:
                pass
        resultado[25] = (tem_section, f"texto 'Configurações de IA' presente={tem_section}")
        print(f"   => item 25: {'PASSOU' if tem_section else 'FALHOU'} | section IA presente={tem_section}\n")
    except Exception as e:
        resultado[18] = (False, f"erro: {e}")
        resultado[25] = (False, f"erro: {e}")
        print(f"   => itens 18/25: ERRO {e}\n")

    # ===================================================================== #
    # ITEM 04 — atividade Externa: campo "Player do vídeo"
    # ===================================================================== #
    print("### ITEM 04 — campo 'Player do vídeo' na atividade Externa")
    ativ_id = None
    try:
        url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"
        for _ in range(3):
            page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
            tw.dispensar_nps(page)
            try:
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
                break
            except Exception:
                print("   [retry] hidratação do estúdio")
        page.wait_for_timeout(2000)

        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(1000)
        # mapear os tipos disponíveis no seletor
        tipos = page.evaluate(
            """()=>[...document.querySelectorAll('[data-test-id^="creation-studio-type-selector-"]')]
                .filter(e=>e.offsetParent!==null)
                .map(e=>({testid:e.getAttribute('data-test-id'),
                          txt:(e.innerText||'').replace(/\\s+/g,' ').trim()}))"""
        )
        print(f"   tipos no seletor: {tipos}")
        tw.snap(page, PASTA, "04-seletor-tipos")
        # escolher o tipo Externa (por test-id 'extern' ou texto 'Externa')
        alvo = None
        for t in tipos:
            if re.search(r"extern", t["testid"] or "", re.I) or re.search(r"extern", t["txt"] or "", re.I):
                alvo = t["testid"]
                break
        if not alvo:
            raise RuntimeError(f"tipo Externa não encontrado no seletor; tipos={tipos}")
        print(f"   clicando no tipo Externa: {alvo}")
        page.locator(f'[data-test-id="{alvo}"]').first.click(timeout=8000)
        page.wait_for_timeout(4000)
        tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url)
        ativ_id = m.group(1) if m else None
        print(f"   atividade Externa criada: {ativ_id} (url {page.url})")
        tw.snap(page, PASTA, "04-form-externa", full=True)

        corpo = page.evaluate("()=>document.body.innerText")
        tem_player = bool(re.search(r"Player do v[íi]deo", corpo, re.I))
        tem_twygo = bool(re.search(r"Player da Twygo", corpo, re.I))
        tem_youtube = bool(re.search(r"Player oficial do YouTube|YouTube", corpo, re.I))
        ok04 = tem_player and (tem_twygo or tem_youtube)
        det04 = (f"'Player do vídeo'={tem_player} | 'Player da Twygo'={tem_twygo} | "
                 f"opção YouTube={tem_youtube}")
        resultado[4] = (ok04, det04)
        print(f"   => item 04: {'PASSOU' if ok04 else 'FALHOU'} | {det04}\n")
    except Exception as e:
        resultado[4] = (False, f"erro: {e}")
        print(f"   => item 04: ERRO {e}\n")
    finally:
        # cleanup: excluir a atividade Externa criada (não deixar rascunho órfão)
        if ativ_id:
            try:
                page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
                page.wait_for_timeout(2000)
                card = page.locator(tid(f"creation-studio-activity-card-{ativ_id}")).first
                card.scroll_into_view_if_needed()
                card.click(timeout=8000, force=True)
                page.wait_for_timeout(2500)
                page.locator(tid("creation-studio-preview-delete")).first.click(timeout=8000, force=True)
                page.wait_for_timeout(1500)
                page.locator(tid("creation-studio-preview-delete-dialog")).get_by_role(
                    "button", name=re.compile("^Excluir", re.I)).first.click(timeout=8000)
                page.wait_for_timeout(3000)
                print(f"   [cleanup] atividade {ativ_id} excluída")
            except Exception as e:
                print(f"   [cleanup] FALHOU ({e}) — excluir manualmente a atividade {ativ_id} do curso {CURSO}")

    # ===================================================================== #
    print("\n================= RESUMO =================")
    nomes = {11: "Card Curso -> abas Estúdio", 18: "FAB copiloto Identificação",
             25: "Section Configurações de IA", 4: "Player do vídeo (Externa)"}
    for it in (11, 18, 25, 4):
        ok, det = resultado.get(it, (None, "não executado"))
        marca = "PASSOU ✅" if ok else "FALHOU ❌"
        print(f"  Item {it:>2} ({nomes[it]}): {marca}\n      {det}")
    ctx.close(); browser.close()
