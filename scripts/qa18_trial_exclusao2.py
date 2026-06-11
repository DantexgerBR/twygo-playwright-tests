# -*- coding: utf-8 -*-
"""QA 1.18 — fase C (retry): exclusão Sophia "Todas informações" na Trial 37062.

Fix vs v1: checkbox Chakra (input oculto) → check(force=True) no 4º input do
modal; espera o botão Excluir HABILITAR antes do clique físico.
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

    # Popover Sophia: o widget fica no canto inferior esquerdo (coruja)
    sophia_btn = page.get_by_role("button", name=re.compile("sofia|sophia", re.I)).first
    if sophia_btn.count() and sophia_btn.is_visible():
        sophia_btn.click(timeout=8000)
    else:
        box = page.evaluate(
            """()=>{const els=Array.from(document.querySelectorAll('button,[role=button],div'))
                .filter(b=>{const r=b.getBoundingClientRect();
                    return r.left<160 && r.top>window.innerHeight-200 && r.width>40 && r.width<120 && r.height>40;});
                if(!els.length)return null;const r=els[els.length-1].getBoundingClientRect();
                return {x:r.left+r.width/2,y:r.top+r.height/2};}"""
        )
        if not box:
            raise SystemExit("[erro] widget Sophia não encontrado")
        page.mouse.click(box["x"], box["y"])
    page.wait_for_timeout(2000)

    page.get_by_role("button", name=re.compile("Excluir informa", re.I)).first.click(timeout=8000)
    modal = page.get_by_role("dialog").filter(has_text=re.compile("Excluir informa", re.I)).first
    modal.wait_for(state="visible", timeout=10000)

    # 4º checkbox = "Todas informações (pré-definidas e criadas pelos administradores)"
    inputs = modal.locator("input[type=checkbox]")
    print(f"[info] checkboxes no modal: {inputs.count()}")
    inputs.last.check(force=True, timeout=8000)
    page.wait_for_timeout(800)
    marcado = inputs.last.is_checked()
    print(f"[info] 'Todas informações' marcado? {marcado}")
    tw.snap(page, PASTA, "26-checkbox-marcado")

    btn = modal.get_by_role("button", name=re.compile("^Excluir$", re.I)).first
    btn.wait_for(state="visible", timeout=5000)
    page.wait_for_function(
        """()=>{const d=[...document.querySelectorAll('[role=dialog]')].find(x=>x.innerText.includes('Excluir informa'));
            if(!d)return false;const b=[...d.querySelectorAll('button')].find(x=>x.innerText.trim()==='Excluir');
            return b && !b.disabled;}""",
        timeout=10000,
    )
    btn.click(timeout=8000)
    print("[ok] Excluir confirmado (botão habilitado, clique físico)")
    try:
        modal.wait_for(state="hidden", timeout=60000)
        print("[ok] modal fechou")
    except Exception:
        print("[warn] modal não fechou em 60s")
    try:
        page.wait_for_load_state("networkidle", timeout=60000)
    except Exception:
        pass
    page.wait_for_timeout(15000)
    tw.snap(page, PASTA, "27-pos-exclusao")

    print("\n[rede]")
    for linha in rede:
        print("  ", linha)

    page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, "28-listagem-pos-exclusao")
    print("[ok] fim")
    ctx.close(); browser.close()
