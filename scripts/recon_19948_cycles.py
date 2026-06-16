# -*- coding: utf-8 -*-
"""Recon 19948 — página de ciclos /o/37048/cycles: ciclos existentes, botão criar,
kebab. Captura network. Headless."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19948_calibracao"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
erros = []

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, headless=True)
    page.on("response", lambda r: erros.append((r.status, r.url)) if (lambda: r.status >= 500)() else None)
    tw.login(page, c)
    try:
        page.goto(base + f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(page); page.wait_for_timeout(4000)
        tw.snap(page, PASTA, "cyc-00-lista", full=True)
        # botões/ações
        botoes = page.evaluate(r"""()=>[...document.querySelectorAll('button,a')]
          .map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t && t.length<32 &&
            /ciclo|criar|novo|campanh|gerenciar|more_vert|\.\.\./i.test(t)).slice(0,20)""")
        print("[cycles] botões/ações:", list(dict.fromkeys(botoes)))
        # ciclos existentes (linhas/cards)
        ciclos = page.evaluate(r"""()=>{
          const rows=[...document.querySelectorAll('tr,[class*=card],[class*=row],li')];
          return rows.map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t.length>8 && t.length<120 && /ciclo|campanh|\d{4}|ativ|encerr|andamento/i.test(t)).slice(0,12);
        }""")
        print("[cycles] possíveis ciclos:")
        for cc in ciclos: print("   -", cc[:90])
        # tem botão "more_vert" (kebab) na lista?
        kb = page.get_by_text("more_vert", exact=True)
        print("[cycles] kebabs na página:", kb.count())
        corpo = page.evaluate("()=>document.body.innerText")
        print("[cycles] menciona 'Gerenciar campanhas'?", bool(re.search(r"gerenciar campanh", corpo, re.I)))
        print("[cycles] menciona 'calibra'?", bool(re.search(r"calibra", corpo, re.I)))
        print("\n[net 500]:", [e for e in erros if e[0]>=500][:10])
    except Exception as e:
        print("ERRO:", e); tw.snap(page, PASTA, "cyc-erro")
    finally:
        ctx.close(); browser.close()
