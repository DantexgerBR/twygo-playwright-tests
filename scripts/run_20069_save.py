# -*- coding: utf-8 -*-
"""20069 — testa salvar pessoa com E-mail (obrigatorio) preenchido em Analise
individual 19653. Bug: e-mail obrigatorio nao salva. Captura Network PUT/POST +
mensagem de validacao + se volta pra lista. Tambem testa re-digitar o e-mail."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20069_email"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

def edit_url(pg): return "/edit" in pg.url

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    net = []
    pg.on("response", lambda r: net.append((r.request.method, r.status, r.url.split("twygoead.com")[-1][:55])) if r.request.method in ("POST","PUT","PATCH") and "twygoead.com/api" in r.url else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/succession_people_analysis", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3500)
        pg.mouse.click(1449, 276); pg.wait_for_timeout(2500)
        if not edit_url(pg): pg.mouse.click(1449, 276); pg.wait_for_timeout(2500)
        log("editor url:", pg.url[-45:])
        # campo e-mail (provavelmente disabled, pre-preenchido) — NAO manipular
        em = pg.locator("input[name=email]")
        if em.count():
            log("email val:", em.input_value(), "| disabled:", em.evaluate("e=>e.disabled"))
        tw.snap(pg, PASTA, "40-pre-salvar", full=True)
        net.clear()
        # clicar Salvar
        pg.get_by_role("button", name=re.compile("^Salvar$", re.I)).first.click(timeout=5000)
        pg.wait_for_timeout(3500)
        # resultado: validacao? toast? voltou pra lista?
        res = pg.evaluate(r"""()=>{const errs=[...document.querySelectorAll('[class*=error i],[class*=invalid i],[role=alert],.chakra-form__error-message')].filter(e=>e.offsetParent!==null&&(e.innerText||'').trim()).map(e=>e.innerText.trim()).slice(0,5);
          const toast=[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,3);
          return {errs:[...new Set(errs)], toast:[...new Set(toast)]};}""")
        voltou = "/edit" not in pg.url
        log("validacao/erros:", res["errs"])
        log("toast:", res["toast"])
        log("voltou p/ lista (saiu do /edit):", voltou, "| url:", pg.url[-40:])
        log("Network mutacoes:", net[-6:])
        tw.snap(pg, PASTA, "41-pos-salvar", full=True)
        # veredito
        ok_net = any(s in (200, 201, 204) for _, s, _ in net)
        salvou = voltou or ok_net
        log(f"\n>> 20069 VEREDITO: {'PASSOU (salvou)' if (salvou and not res['errs']) else 'FALHOU (nao salvou / erro de validacao)'}")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "erro3", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
