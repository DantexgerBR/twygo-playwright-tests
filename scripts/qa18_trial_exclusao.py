# -*- coding: utf-8 -*-
"""QA 1.18 — fase C: Sophia → Excluir informações → "Todas informações" (Tudo).

DESTRUTIVO (Trial 37062 dedicada de QA — mecanismo previsto no apontamento).
Prova via Network que o DELETE /delete_trial_data disparou e respondeu 2xx
(skill testar-exclusao-dados-trial-twygo: update otimista da UI engana sem isso).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "qa18_e2e_1106"
c = tw.cfg("NOVOTRIAL")
rede = []

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)

    page.on("request", lambda r: rede.append(f">> {r.method} {r.url}")
            if "delete_trial_data" in r.url or "trial_deletion" in r.url else None)
    page.on("response", lambda r: rede.append(f"<< {r.status} {r.url}")
            if "delete_trial_data" in r.url or "trial_deletion" in r.url else None)

    tw.login(page, c)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "20-pre-exclusao")

    # Ícone Sophia (coruja, canto inferior esquerdo) — sem testId
    sophia = page.get_by_role("button", name=re.compile("sofia|sophia", re.I)).first
    if not (sophia.count() and sophia.is_visible()):
        # fallback: botão flutuante no canto inferior esquerdo
        sophia = page.locator("button:visible").filter(has=page.locator("img, .chakra-icon")).last
        print("[warn] role-name não achou Sophia; tentando fallback")
        cands = page.evaluate(
            """()=>Array.from(document.querySelectorAll('button,[role=button]'))
                .filter(b=>{const r=b.getBoundingClientRect();
                    return r.left<200 && r.top>window.innerHeight-220 && r.width>20;})
                .map(b=>({aria:b.getAttribute('aria-label'),cls:b.className&&String(b.className).slice(0,60),txt:(b.innerText||'').slice(0,30)}))"""
        )
        print("[debug] candidatos canto inferior esquerdo:", cands)
        box = page.evaluate(
            """()=>{const els=Array.from(document.querySelectorAll('button,[role=button],div'))
                .filter(b=>{const r=b.getBoundingClientRect();
                    return r.left<160 && r.top>window.innerHeight-200 && r.width>40 && r.width<120 && r.height>40;});
                if(!els.length)return null;const r=els[els.length-1].getBoundingClientRect();
                return {x:r.left+r.width/2,y:r.top+r.height/2};}"""
        )
        if box:
            page.mouse.click(box["x"], box["y"])
        else:
            raise SystemExit("[erro] widget Sophia não encontrado")
    else:
        sophia.click(timeout=8000)
    page.wait_for_timeout(2000)
    tw.snap(page, PASTA, "21-popover-sophia")

    # Opção "Excluir informações"
    page.get_by_role("button", name=re.compile("Excluir informa", re.I)).first.click(timeout=8000)
    modal = page.get_by_role("dialog").filter(has_text=re.compile("Excluir informa", re.I)).first
    modal.wait_for(state="visible", timeout=10000)
    tw.snap(page, PASTA, "22-modal-exclusao")

    # Checkbox "Todas informações (pré-definidas e criadas pelos administradores)"
    alvo = modal.get_by_text(re.compile(r"Todas\s+informa", re.I)).last
    alvo.click(timeout=8000, force=True)
    page.wait_for_timeout(800)
    tw.snap(page, PASTA, "23-checkbox-tudo")

    # Confirmar (clique FÍSICO Playwright)
    modal.get_by_role("button", name=re.compile("^Excluir$", re.I)).first.click(timeout=8000)
    print("[ok] Excluir confirmado")
    try:
        modal.wait_for(state="hidden", timeout=60000)
    except Exception:
        print("[warn] modal não fechou em 60s")
    try:
        page.wait_for_load_state("networkidle", timeout=60000)
    except Exception:
        pass
    page.wait_for_timeout(10000)
    tw.snap(page, PASTA, "24-pos-exclusao")

    print("\n[rede]")
    for linha in rede:
        print("  ", linha)

    # Conferir listagem de Conteúdos depois
    page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "25-listagem-pos-exclusao")
    print("[ok] fim — ver evidencias 20-25")
    ctx.close(); browser.close()
