# -*- coding: utf-8 -*-
"""Recon 20108 — abre 'Gerenciar campanhas' do ciclo QA19948 (37048) e mapeia como
criar campanha + atribuir avaliacao/participante. Crux da viabilidade do 20108."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20108_desempenho"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/cycles", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        pg.locator("tbody tr").first.locator("button").last.click(timeout=4000); pg.wait_for_timeout(1000)
        pg.get_by_role("menuitem", name=re.compile("Gerenciar campanhas", re.I)).first.click(timeout=4000)
        pg.wait_for_timeout(3000)
        log("url:", pg.url[-55:])
        info = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.left>250};
          const btns=[...document.querySelectorAll('button,[role=button],a')].filter(vis).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<30&&!/^\d+$/.test(t));
          const heads=[...document.querySelectorAll('h1,h2,h3')].filter(vis).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,5);
          const rows=document.querySelectorAll('tbody tr').length;
          return {btns:[...new Set(btns)].slice(0,18), heads, rows};}""")
        log("heads:", info["heads"]); log("rows:", info["rows"]); log("btns:", info["btns"])
        tw.snap(pg, PASTA, "camp-01", full=True)
        # clicar criar campanha (Nova/Adicionar/Criar campanha)
        for alvo in ("Nova campanha","Adicionar campanha","Criar campanha","Nova","Adicionar","Criar"):
            bt = pg.get_by_role("button", name=re.compile(f"^{re.escape(alvo)}", re.I))
            if bt.count(): bt.first.click(timeout=3500); pg.wait_for_timeout(2500); log("cliquei:", alvo); break
        info2 = pg.evaluate(r"""()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.left>250};
          const inputs=[...document.querySelectorAll('input,textarea,select,[role=combobox]')].filter(vis).map(e=>(e.placeholder||e.name||e.getAttribute('aria-label')||e.tagName)).slice(0,12);
          const labels=[...document.querySelectorAll('label,h2,h3')].filter(vis).map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<40).slice(0,15);
          const btns=[...document.querySelectorAll('button')].filter(vis).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,12);
          return {inputs:[...new Set(inputs)], labels:[...new Set(labels)], btns:[...new Set(btns)]};}""")
        log("\n[criar campanha] inputs:", info2["inputs"]); log("  labels:", info2["labels"]); log("  btns:", info2["btns"])
        tw.snap(pg, PASTA, "camp-02-criar", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "camp-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
