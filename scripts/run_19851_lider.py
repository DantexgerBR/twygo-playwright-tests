# -*- coding: utf-8 -*-
"""19851 — loga como o LÍDER caranovo@gmail.com (123456?) no 19653 e testa o drawer
Ações de resposta > Adicionar: 'Função vinculada' e 'Iniciativa' devem listar opções.
Bug: vinham vazias pro líder. Headless."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)
LIDER_EMAIL = "caranovo@gmail.com"; LIDER_PWD = "123456"

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True)
    try:
        # login manual como o líder
        pg.goto(base + "/users/login", wait_until="domcontentloaded", timeout=30000); pg.wait_for_timeout(1500)
        pg.fill("#user_email", LIDER_EMAIL); pg.fill("#user_password", LIDER_PWD)
        pg.click("#user_submit")
        try: pg.wait_for_load_state("networkidle", timeout=12000)
        except Exception: pg.wait_for_timeout(4000)
        falhou_login = bool(re.search(r"inv[áa]lid|senha.*incorret|n[ãa]o conferem|credenciais", pg.evaluate("()=>document.body.innerText")[:300], re.I))
        log(f"[login] url={pg.url[-40:]} falhou={falhou_login}")
        if falhou_login or "/login" in pg.url:
            log("=> 19851: LOGIN DO LÍDER FALHOU (senha != 123456). Preciso da senha do caranovo.")
            tw.snap(pg, PASTA, "login-falhou"); raise SystemExit
        tw.dispensar_nps(pg)
        # ir pra Ações de resposta (Continuidade)
        pg.goto(base + f"/o/{c['org_id']}/succession_actions", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3500)
        log("[succession] url:", pg.url)
        tw.snap(pg, PASTA, "01-acoes-lider")
        # Adicionar -> drawer
        pg.get_by_role("button", name=re.compile(r"Adicionar", re.I)).first.click(timeout=6000); pg.wait_for_timeout(3000)
        tw.snap(pg, PASTA, "02-drawer-lider", full=True)
        # abrir Função vinculada e contar opções
        def opts(label):
            pg.evaluate(r"""(lb)=>{const l=[...document.querySelectorAll('label,p,span,div')].find(e=>new RegExp('^'+lb,'i').test((e.innerText||'').trim()));
              if(!l)return;let cont=l.parentElement;for(let k=0;k<4&&cont;k++){const ctrl=cont.querySelector('[class*=-control],[class*=__control],[role=combobox],select');if(ctrl){ctrl.click();return}cont=cont.parentElement;}}""", label)
            pg.wait_for_timeout(1000)
            return pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=option],[role=option],li[class*=menu]')].filter(e=>e.offsetParent!==null&&(e.innerText||'').trim()&&!/selecione/i.test(e.innerText)).map(e=>(e.innerText||'').trim()).slice(0,10)""")
        fv = opts("Função vinculada"); log(f"[Função vinculada] opções={len(fv)} {fv[:5]}")
        pg.keyboard.press("Escape"); pg.wait_for_timeout(500)
        iv = opts("Iniciativa"); log(f"[Iniciativa] opções={len(iv)} {iv[:5]}")
        tw.snap(pg, PASTA, "03-selects-lider", full=True)
        ok = len(fv) >= 1
        log(f"\n=> 19851: {'PASSOU (Função vinculada lista opções pro líder)' if ok else 'FALHOU (Função vinculada vazia pro líder — bug persiste)'}")
    except SystemExit: pass
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "99-erro", full=True)
        except Exception: pass
    finally:
        ctx.close(); b.close()
