# -*- coding: utf-8 -*-
"""19851 setup recon — no editor de pessoa (Analise individual 19653), abre os selects
'Responsavel' (lider de equipe) e 'Funcoes' e lista opcoes. Define quem sera o lider
de teste e qual funcao atribuir pra reproduzir a visao do lider."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider_acoes"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        # vai direto ao editor de uma pessoa (id 6382287 do 20069)
        pg.goto(base+f"/o/{c['org_id']}/succession_people_analysis/6382287/edit", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3500)
        log("url:", pg.url[-45:])
        # react-selects: Area (react-select-2), Responsavel (react-select-3), Funcoes (react-select-4)
        # clica cada um e captura opcoes
        for nome, rsid in [("Responsável","react-select-3-input"), ("Funções","react-select-4-input")]:
            inp = pg.locator(f"#{rsid}")
            if not inp.count(): log(f"{nome}: input {rsid} nao achado"); continue
            try:
                inp.click(timeout=3000); pg.wait_for_timeout(1200)
                opts = pg.evaluate(r"""()=>[...document.querySelectorAll('[id^=react-select][id*=option],[class*=option]')].filter(e=>e.offsetParent!==null&&(e.innerText||'').trim()).map(e=>(e.innerText||'').trim()).slice(0,15)""")
                log(f"{nome} opcoes:", [*dict.fromkeys(opts)][:12])
                pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
            except Exception as ex: log(f"{nome} erro: {str(ex)[:50]}")
        tw.snap(pg, PASTA, "setup-editor", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "setup-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
