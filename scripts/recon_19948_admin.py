# -*- coding: utf-8 -*-
"""Recon 19948 — no admin do 36675 (Dante staff), achar: (a) criação de org,
(b) painel de feature flags (modulo_de_desempenho). Mapeia menu + tenta URLs."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19948_calibracao"
c = tw.cfg()  # 36675
base = c["base_url"]

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1500, height=950)
    tw.login(page, c)
    print("logado:", page.url)
    try:
        # 1) menu lateral / itens de navegação
        itens = page.evaluate(r"""()=>[...document.querySelectorAll('a,button,[role=menuitem]')]
          .map(e=>({t:(e.innerText||'').replace(/\s+/g,' ').trim(), h:e.getAttribute&&e.getAttribute('href')||''}))
          .filter(x=>x.t && x.t.length<40).slice(0,60)""")
        print("== itens de menu (amostra) ==")
        for it in itens:
            if re.search(r"flag|desempenh|organiza|admin|painel|empresa|config|m[oó]dulo", it["t"], re.I):
                print("  *", it)
        tw.snap(page, PASTA, "00-home-admin")

        # 2) tentar URLs candidatas de feature flags / admin / org
        cands = [
            "/admin", "/admin/feature_flags", "/admin/organizations", "/admin/flipper",
            "/flipper", "/feature_flags", f"/o/{c['org_id']}/feature_flags",
            f"/o/{c['org_id']}/settings/feature_flags", "/super_admin", "/painel",
            f"/o/{c['org_id']}/admin", "/organizations/new", "/o/new",
        ]
        for path in cands:
            try:
                page.goto(base.rstrip('/') + path, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(1200)
                txt = page.evaluate("()=>document.body.innerText.slice(0,160)")
                url = page.url
                bad = bool(re.search(r"404|n[ãa]o encontrad|not found|acesso negado|forbidden|sem permiss", txt, re.I))
                tem_flag = bool(re.search(r"flag|modulo_de_desempenho|desempenh", txt, re.I))
                print(f"  [{path}] -> {url[-50:]} | flag?={tem_flag} bad?={bad} | {txt[:60].strip()!r}")
            except Exception as e:
                print(f"  [{path}] erro {str(e)[:50]}")
        tw.snap(page, PASTA, "01-ultima-url")
    except Exception as e:
        print("ERRO:", e); tw.snap(page, PASTA, "99-erro")
    finally:
        ctx.close(); browser.close()
