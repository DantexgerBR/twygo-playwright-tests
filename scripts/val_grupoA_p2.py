# -*- coding: utf-8 -*-
"""Grupo A parte 2 — fecha 19795 (botão Visualizar modelo funciona?),
20026 (Editar memoriza última aba) e confirma 19798 (regerar acessível)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "val_retrabalhos_grupoA"
CURSO = "807533"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
V = {}

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)

    # ===== 19795 — botão 'Visualizar modelo' abre preview? =====
    print("### 19795 — Visualizar modelo")
    try:
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        page.get_by_text(re.compile(r"^Modelo$", re.I)).first.click(timeout=6000, force=True)
        page.wait_for_timeout(3500)
        antes = page.evaluate("()=>document.body.innerText.length")
        btn = page.get_by_role("button", name=re.compile(r"Visualizar modelo", re.I)).first
        btn.click(timeout=6000, force=True)
        page.wait_for_timeout(3000)
        modal = page.evaluate(
            """()=>{const d=[...document.querySelectorAll('[role=dialog],[role=alertdialog],.chakra-modal__content')].find(e=>e.offsetParent!==null && (e.innerText||'').trim().length>10);
                return d?{aberto:true, txt:(d.innerText||'').replace(/\\s+/g,' ').slice(0,160)}:{aberto:false};}"""
        )
        tw.snap(page, PASTA, "19795-visualizar-clicado", full=True)
        V[19795] = ("PASSOU" if modal["aberto"] else "FALHOU", f"clicar 'Visualizar modelo' abre preview={modal.get('aberto')} | {modal.get('txt','')}")
    except Exception as e:
        V[19795] = ("FALHOU", f"erro: {e}")
    print(f"   => 19795: {V[19795]}")

    # ===== 20026 — Editar memoriza última aba =====
    print("### 20026 — Editar volta à última aba")
    try:
        # define última aba = studio
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        # agora abrir o 'edit' puro (como o botão Editar faz)
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(5000); tw.dispensar_nps(page)
        url_final = page.url
        # qual aba está ativa?
        ativa = page.evaluate(
            """()=>{const a=[...document.querySelectorAll('[role=tab],[aria-selected=true],.active')].find(e=>e.offsetParent!==null && /Identifica|Atividades|Modelo|Estúdio/i.test(e.innerText||''));
                const studio=!!document.querySelector('[data-test-id=creation-studio-activities-list]');
                return {studio, txt: a?(a.innerText||'').trim():''};}"""
        )
        tw.snap(page, PASTA, "20026-editar-volta", full=True)
        ok = ativa["studio"] or "studio" in url_final or "Atividade" in ativa.get("txt", "")
        V[20026] = ("PASSOU" if ok else "FALHOU", f"última aba lembrada (studio/Atividades)={ok} | url={url_final} | aba={ativa}")
    except Exception as e:
        V[20026] = ("FALHOU", f"erro: {e}")
    print(f"   => 20026: {V[20026]}")

    # ===== 19798 — confirmar 'Salvar e regerar' acessível (scroll) =====
    print("### 19798 — confirmar regerar acessível")
    try:
        for _ in range(3):
            page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio", wait_until="domcontentloaded", timeout=45000)
            tw.dispensar_nps(page)
            try:
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000); break
            except Exception: pass
        page.wait_for_timeout(2000)
        aula = page.evaluate(
            r"""()=>{let r=null;document.querySelectorAll('[data-test-id]').forEach(e=>{const m=(e.getAttribute('data-test-id')||'').match(/^creation-studio-activity-card-(\d+)$/);if(m && /Aula/i.test(e.innerText||'') && !r) r=m[1];});return r;}"""
        )
        page.goto(f"{c['base_url']}/o/{c['org_id']}/studio/activities/{aula}/edit?type=lesson&eventId={CURSO}", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000); tw.dispensar_nps(page)
        page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True)
        page.wait_for_timeout(3500)
        btn = page.get_by_role("button", name=re.compile(r"Salvar e regerar", re.I)).first
        btn.scroll_into_view_if_needed()
        page.wait_for_timeout(800)
        clicavel = btn.is_visible() and btn.is_enabled()
        tw.snap(page, PASTA, "19798-regerar-scroll", full=False)
        V[19798] = ("PASSOU" if clicavel else "FALHOU", f"'Salvar e regerar' acessível após scroll, clicável={clicavel}")
    except Exception as e:
        V[19798] = ("FALHOU", f"erro: {e}")
    print(f"   => 19798: {V[19798]}")

    print("\n=== RESUMO GRUPO A p2 ===")
    for k in (19795, 20026, 19798):
        print(f"  {k}: {V.get(k)}")
    ctx.close(); browser.close()
