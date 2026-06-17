# -*- coding: utf-8 -*-
"""20069 multi — edita varias pessoas (linhas 1,5,9) e clica Salvar, capturando se
salva ou 422 e qual campo bloqueia. Objetivo: ver se o e-mail bloqueia em algum caso
(20069) ou se o bloqueio e sempre telefone (achado separado)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20069_email"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    net = []
    pg.on("response", lambda r: net.append((r.status, r.url.split("twygoead.com")[-1][:50])) if r.request.method in ("PATCH","PUT","POST") and "succession_people" in r.url else None)
    try:
        for ystr, ylabel in [(276,"linha1"),(536,"linha~5"),(742,"linha~9")]:
            pg.goto(base+f"/o/{c['org_id']}/succession_people_analysis", wait_until="domcontentloaded", timeout=30000)
            tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
            pg.mouse.click(1449, ystr); pg.wait_for_timeout(2200)
            if "/edit" not in pg.url:
                log(f"[{ylabel}] nao abriu editor (url={pg.url[-30:]})"); continue
            pessoa = pg.evaluate(r"""()=>{const fn=document.querySelector('input[name=first_name]')?.value||'';const ln=document.querySelector('input[name=last_name]')?.value||'';const em=document.querySelector('input[name=email]');return {nome:(fn+' '+ln).trim(),email:em?em.value:'',email_disabled:em?em.disabled:null};}""")
            net.clear()
            try: pg.get_by_role("button", name=re.compile("^Salvar$", re.I)).first.click(timeout=4000)
            except Exception as ex: log(f"[{ylabel}] sem botao Salvar: {str(ex)[:40]}"); continue
            pg.wait_for_timeout(3000)
            toast = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert,[role=alert]')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,4)""")
            saiu = "/edit" not in pg.url
            log(f"[{ylabel}] {pessoa['nome'][:20]} email='{pessoa['email']}' disabled={pessoa['email_disabled']} | net={net[-3:]} saiu_edit={saiu}")
            log(f"         toast={[t[:90] for t in dict.fromkeys(toast)]}")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
    finally:
        ctx.close(); b.close()
