# -*- coding: utf-8 -*-
"""19851 — le os hrefs reais da linha da Natalia na Equipe do lider, pra saber a URL
exata da analise/Continuidade. Tambem dumpa todos os <a> da pagina Equipe."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/"); org = c["org_id"]
LOGIN = "qalider19851@teste.com"; SENHA = "123456"; TL = "4298356"
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True)
    try:
        pg.goto(base+"/login", wait_until="domcontentloaded", timeout=30000); pg.wait_for_timeout(1500)
        pg.fill("#user_email", LOGIN); pg.fill("#user_password", SENHA)
        pg.locator("#user_submit,button[type=submit]").first.click(timeout=4000); pg.wait_for_timeout(5000)
        ac = pg.get_by_role("button", name=re.compile("^Aceitar$", re.I))
        if ac.count(): ac.first.click(timeout=4000); pg.wait_for_timeout(1500)
        pg.goto(base+f"/o/{org}/team_leaders/{TL}/users", wait_until="domcontentloaded", timeout=25000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        hrefs = pg.evaluate(r"""()=>{const out=[];document.querySelectorAll('a[href]').forEach(a=>{const h=a.getAttribute('href');if(h&&!/^#|javascript:/.test(h))out.push({href:h,txt:(a.innerText||a.getAttribute('aria-label')||a.querySelector('svg')?'[icon]':'').replace(/\s+/g,' ').trim().slice(0,30)});});return out.slice(0,40);}""")
        log("=== TODOS OS <a> da Equipe ===")
        for h in hrefs:
            if "team_leaders" in h["href"] or "natalia" in h["href"].lower() or "success" in h["href"].lower() or "continu" in h["href"].lower() or h["txt"]=="[icon]":
                log("  ", h["txt"], "->", h["href"])
        # tambem clica a linha/nome da Natalia
        nat = pg.get_by_text(re.compile("Natália Souza", re.I))
        if nat.count():
            nat.first.click(timeout=4000); pg.wait_for_timeout(3000)
            log("\napos clicar Natalia url:", pg.url[-55:])
            nav = pg.evaluate(r"""()=>[...document.querySelectorAll('a,[role=tab],span')].map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<32&&/continuidade|sucess|a[cç][oõ]es de resposta|an[aá]lise|desempenho|par[aâ]metros/i.test(t)).slice(0,12)""")
            log("nav apos Natalia:", [*dict.fromkeys(nav)])
            tw.snap(pg, tw.ROOT/"evidencias"/"retrabalho_19851_lider_acoes", "hrefs-natalia", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
