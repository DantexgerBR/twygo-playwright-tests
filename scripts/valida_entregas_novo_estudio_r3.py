# -*- coding: utf-8 -*-
"""Rodada 3 — fecha itens 18, 25 e 04 (org 37061, curso 807533).
Correções vs r2: typo do wait_for_timeout removido; FAB do copiloto detectado por
elementFromPoint (é um div/a com svg, não button)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "valida_entregas_novo_estudio"
CURSO = "807533"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
resultado = {}

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    print(f"[ok] logado em {page.url}\n")

    # ===================================================================== #
    # ITEM 18 — FAB do copiloto na Identificação (elementFromPoint + clique)
    # ===================================================================== #
    print("### ITEM 18 — FAB do copiloto na Identificação")
    try:
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=identification",
                  wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(7000)
        tw.dispensar_nps(page)

        # varrer o canto superior direito procurando um elemento redondo roxo (FAB)
        fab = page.evaluate(
            """()=>{
                const W=window.innerWidth;
                for(let y=90;y<=200;y+=8){
                  for(let x=W-20;x>=W-110;x-=8){
                    const el=document.elementFromPoint(x,y);
                    if(!el) continue;
                    // sobe até um clicável com fundo roxo / formato redondo
                    let n=el;
                    for(let i=0;i<5 && n;i++,n=n.parentElement){
                      const s=getComputedStyle(n); const r=n.getBoundingClientRect();
                      const round = parseFloat(s.borderRadius)>=20 || s.borderRadius.includes('50');
                      const purple=/rgb\\(1[0-4]\\d|rgb\\(\\d?\\d?[7-9]\\d, ?\\d+, ?2[0-5]\\d/.test(s.backgroundColor);
                      if(r.width>=36 && r.width<=80 && r.height>=36 && r.height<=80 && (round||purple)){
                        return {x,y, tag:n.tagName, testid:n.getAttribute('data-test-id'),
                                aria:n.getAttribute('aria-label'), bg:s.backgroundColor,
                                br:s.borderRadius, w:Math.round(r.width), h:Math.round(r.height),
                                cx:Math.round(r.left+r.width/2), cy:Math.round(r.top+r.height/2),
                                html:n.outerHTML.slice(0,160)};
                      }
                    }
                  }
                }
                return null;
            }"""
        )
        print(f"   FAB detectado: {fab}")
        tw.snap(page, PASTA, "18c-identificacao")

        abriu = False
        if fab:
            page.mouse.click(fab["cx"], fab["cy"])
            page.wait_for_timeout(3500)
            # detectar painel/drawer do copiloto aberto (test-id OU painel novo OU texto)
            estado = page.evaluate(
                """()=>{
                    const d=document.querySelector('[data-test-id=copilot-drawer]');
                    const drawerVis=d? d.offsetParent!==null : false;
                    const aside=[...document.querySelectorAll('aside,[role=dialog],[role=complementary],section')]
                      .some(e=>e.offsetParent!==null && /copilot|copiloto|assistente|pergunte|como posso/i.test(e.innerText||''));
                    const txt=/copiloto|assistente de cria|como posso ajudar|pergunte/i.test(document.body.innerText||'');
                    return {drawerVis, aside, txt};
                }"""
            )
            abriu = bool(estado["drawerVis"] or estado["aside"] or estado["txt"])
            print(f"   após clique no FAB: {estado} | copiloto aberto? {abriu}")
            tw.snap(page, PASTA, "18c-fab-clicado")

        ok18 = bool(fab) and abriu
        resultado[18] = (ok18, f"FAB presente={bool(fab)} | clique abre copiloto={abriu}")
        print(f"   => item 18: {'PASSOU' if ok18 else 'FALHOU'}\n")
    except Exception as e:
        resultado[18] = (False, f"erro: {e}")
        print(f"   => item 18: ERRO {e}\n")

    # ===================================================================== #
    # ITEM 25 — "Configurações de IA": Identificação vs Modelo
    # ===================================================================== #
    print("### ITEM 25 — section 'Configurações de IA' (Identificação vs Modelo)")
    try:
        achados = {}
        for aba_tab, label in [("identification", "Identificação"), ("model", "Modelo")]:
            page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab={aba_tab}",
                      wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)
            tw.dispensar_nps(page)
            try:
                t = page.get_by_text(re.compile(rf"^{label}$", re.I)).first
                if t.count() and t.is_visible():
                    t.click(timeout=3000, force=True); page.wait_for_timeout(3000)
            except Exception:
                pass
            corpo = page.evaluate("()=>document.body.innerText")
            tem = bool(re.search(r"Configura[çc][õo]es de IA", corpo, re.I))
            tem_var = bool(re.search(r"Intelig[êe]ncia Artificial", corpo, re.I))
            achados[label] = (tem, tem_var)
            print(f"   [{label}] 'Configurações de IA'={tem} | 'Inteligência Artificial'={tem_var}")
            tw.snap(page, PASTA, f"25c-{aba_tab}", full=True)
        na_ident = achados.get("Identificação", (False, False))[0]
        no_modelo = achados.get("Modelo", (False, False))[0]
        ok25 = na_ident
        resultado[25] = (ok25, f"Identificação={na_ident} | Modelo={no_modelo}")
        print(f"   => item 25: {'PASSOU' if ok25 else 'FALHOU'}\n")
    except Exception as e:
        resultado[25] = (False, f"erro: {e}")
        print(f"   => item 25: ERRO {e}\n")

    # ===================================================================== #
    # ITEM 04 — campo "Player do vídeo" na atividade Externa (tipo correto)
    # ===================================================================== #
    print("### ITEM 04 — campo 'Player do vídeo' na atividade Externa")
    ativ_id = None
    url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"
    try:
        for _ in range(3):
            page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
            tw.dispensar_nps(page)
            try:
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
                break
            except Exception:
                print("   [retry] hidratação")
        page.wait_for_timeout(2000)
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(1000)
        page.locator(tid("creation-studio-type-selector-external")).first.click(timeout=8000)
        page.wait_for_timeout(4000)
        tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url)
        ativ_id = m.group(1) if m else None
        print(f"   atividade Externa criada: {ativ_id} (url {page.url})")
        tw.snap(page, PASTA, "04c-form-externa", full=True)

        corpo = page.evaluate("()=>document.body.innerText")
        tem_player = bool(re.search(r"Player do v[íi]deo", corpo, re.I))
        tem_twygo = bool(re.search(r"Player da Twygo", corpo, re.I))
        tem_youtube_oficial = bool(re.search(r"Player oficial do YouTube", corpo, re.I))
        labels = page.evaluate(
            """()=>[...document.querySelectorAll('label,legend,p,span,h3,h4')]
                .filter(e=>e.offsetParent!==null && /player|v[íi]deo|youtube|vimeo/i.test(e.innerText||''))
                .map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).slice(0,30)"""
        )
        print(f"   labels player/vídeo no form: {labels}")
        ok04 = tem_player and (tem_twygo or tem_youtube_oficial)
        resultado[4] = (ok04, f"'Player do vídeo'={tem_player} | Twygo={tem_twygo} | YouTube oficial={tem_youtube_oficial}")
        print(f"   => item 04: {'PASSOU' if ok04 else 'FALHOU'}\n")
    except Exception as e:
        resultado[4] = (False, f"erro: {e}")
        print(f"   => item 04: ERRO {e}\n")
    finally:
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
                print(f"   [cleanup] FALHOU ({e}) — excluir manualmente {ativ_id} do curso {CURSO}")

    print("\n================= RESUMO RODADA 3 =================")
    nomes = {18: "FAB copiloto Identificação", 25: "Section Configurações de IA",
             4: "Player do vídeo (Externa)"}
    for it in (18, 25, 4):
        ok, det = resultado.get(it, (None, "não executado"))
        print(f"  Item {it:>2} ({nomes[it]}): {'PASSOU ✅' if ok else 'FALHOU ❌'}\n      {det}")
    ctx.close(); browser.close()
