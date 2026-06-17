# -*- coding: utf-8 -*-
"""19851 senha — abre kebab e usa TECLADO (typeahead 'a' -> Alterar senha + Enter),
que ignora a camada de Tooltip que captura o clique. Preenche 123456."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider_acoes"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

def fill_senha(pg, tag):
    ins = pg.evaluate(r"""()=>[...document.querySelectorAll('input')].filter(e=>e.offsetParent!==null).map(e=>({n:e.name||e.id||'',t:e.type,ph:e.placeholder||''}))""")
    log(f"[{tag}] inputs visiveis:", ins)
    alvo = pg.locator("input[type=password]:visible")
    if not alvo.count(): alvo = pg.locator("input[name*=password]:visible, input[name*=senha]:visible, input[placeholder*=senha i]:visible")
    log(f"[{tag}] campos senha:", alvo.count())
    ok = False
    for i in range(alvo.count()):
        try: alvo.nth(i).fill("123456", timeout=2500); ok = True; log("  campo", i, "ok")
        except Exception: pass
    if ok:
        sv = pg.get_by_role("button", name=re.compile("Salvar|Confirmar|Alterar|Redefinir", re.I))
        if sv.count(): sv.first.click(timeout=4000); pg.wait_for_timeout(2500)
        toast = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,3)""")
        log("toast:", [*dict.fromkeys(toast)])
    return ok

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/users", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        pg.get_by_placeholder(re.compile("Pesquis|Buscar", re.I)).first.fill("qalider19851"); pg.wait_for_timeout(3000)
        pg.locator("tbody tr").first.wait_for(timeout=8000)
        pg.locator("tbody tr").first.locator("button").last.click(timeout=4000); pg.wait_for_timeout(1200)
        # TECLADO: typeahead 'a' -> Alterar senha, Enter
        pg.keyboard.press("a"); pg.wait_for_timeout(500); pg.keyboard.press("Enter"); pg.wait_for_timeout(2500)
        if not fill_senha(pg, "typeahead"):
            # fallback: reabrir e ArrowDown x3 + Enter
            log("typeahead falhou; tentando ArrowDown")
            pg.locator("tbody tr").first.locator("button").last.click(timeout=4000); pg.wait_for_timeout(1000)
            for _ in range(3): pg.keyboard.press("ArrowDown"); pg.wait_for_timeout(250)
            pg.keyboard.press("Enter"); pg.wait_for_timeout(2500)
            fill_senha(pg, "arrowdown")
        tw.snap(pg, PASTA, "pwd6-final", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "pwd6-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
