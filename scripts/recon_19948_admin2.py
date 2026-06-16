# -*- coding: utf-8 -*-
"""Recon 19948 (parte 2) — explora /admin: links/seções, tela de Features (flags)
e criação de org."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19948_calibracao"
c = tw.cfg(); base = c["base_url"].rstrip("/")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1500, height=950)
    tw.login(page, c)
    try:
        page.goto(base + "/admin", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2500); tw.dispensar_nps(page)
        tw.snap(page, PASTA, "adm-00-home")
        links = page.evaluate(r"""()=>[...document.querySelectorAll('a')]
          .map(a=>({t:(a.innerText||'').replace(/\s+/g,' ').trim(), h:a.getAttribute('href')||''}))
          .filter(x=>x.h && x.h.startsWith('/admin')).slice(0,60)""")
        print("== links /admin/* ==")
        seen=set()
        for l in links:
            if l["h"] not in seen:
                seen.add(l["h"]); print(f"   {l['t'][:30]!r:34} {l['h']}")

        # abrir a seção Features
        try:
            page.get_by_role("link", name=re.compile(r"^Features$", re.I)).first.click(timeout=6000)
            page.wait_for_timeout(2500)
            print("\n[features] url:", page.url)
            tw.snap(page, PASTA, "adm-01-features", full=True)
            # campos do form de feature (select de org + flag?)
            campos = page.evaluate(r"""()=>({
              selects:[...document.querySelectorAll('select')].map(s=>({name:s.name||'',opts:s.options.length})),
              inputs:[...document.querySelectorAll('input')].map(i=>({name:i.name||'',type:i.type,ph:i.placeholder||''})).slice(0,15),
              temDesemp: /modulo_de_desempenho|desempenh/i.test(document.body.innerText)
            })""")
            print("[features] campos:", campos)
        except Exception as e:
            print("[features] erro:", e)
    except Exception as e:
        print("ERRO:", e); tw.snap(page, PASTA, "adm-99-erro")
    finally:
        ctx.close(); browser.close()
