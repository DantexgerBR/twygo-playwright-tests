# -*- coding: utf-8 -*-
"""19851 senha — inspeciona o menuitem 'Alterar senha' (tag/href) e dispara do jeito
certo (navega se href, senao dispatchEvent click). Preenche o modal 123456."""
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
        pg.goto(base+f"/o/{c['org_id']}/users", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        pg.get_by_placeholder(re.compile("Pesquis|Buscar", re.I)).first.fill("qalider19851"); pg.wait_for_timeout(3000)
        pg.locator("tbody tr").first.wait_for(timeout=8000)
        pg.locator("tbody tr").first.locator("button").last.click(timeout=4000); pg.wait_for_timeout(1000)
        # inspeciona o menuitem
        det = pg.evaluate(r"""()=>{const c=[...document.querySelectorAll('[role=menuitem]')].find(x=>/Alterar senha$/.test((x.innerText||'').replace(/\s+/g,' ').trim()));
          if(!c)return null;const a=c.closest('a')||c.querySelector('a');
          return {tag:c.tagName, href:c.getAttribute('href')||(a&&a.getAttribute('href'))||'', cls:(c.className||'').toString().slice(0,40), outer:c.outerHTML.slice(0,160)};}""")
        log("menuitem detalhe:", det)
        # dispara via dispatchEvent (clica programaticamente no proprio elemento)
        fired = pg.evaluate(r"""()=>{const c=[...document.querySelectorAll('[role=menuitem]')].find(x=>/Alterar senha$/.test((x.innerText||'').replace(/\s+/g,' ').trim()));
          if(!c)return false; c.click(); return true;}""")
        log("dispatch click:", fired); pg.wait_for_timeout(2500)
        # se navegou por href, ou abriu modal: dump inputs
        ins = pg.evaluate(r"""()=>[...document.querySelectorAll('input')].filter(e=>e.offsetParent!==null).map(e=>({n:e.name||e.id||'',t:e.type,ph:e.placeholder||''}))""")
        log("url:", pg.url[-40:]); log("inputs visiveis:", ins)
        tw.snap(pg, PASTA, "pwd4-pos", full=True)
        # preenche senha (password OU text com 'senha')
        alvo = pg.locator("input[type=password]:visible")
        if not alvo.count(): alvo = pg.locator("input[name*=password]:visible, input[name*=senha]:visible, input[placeholder*=senha i]:visible")
        log("campos senha:", alvo.count())
        for i in range(alvo.count()):
            try: alvo.nth(i).fill("123456", timeout=2000); log("  campo", i, "ok")
            except Exception: pass
        if alvo.count():
            sv = pg.get_by_role("button", name=re.compile("Salvar|Confirmar|Alterar|Redefinir", re.I))
            if sv.count(): sv.first.click(timeout=4000); pg.wait_for_timeout(2500)
            toast = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,3)""")
            log("toast:", [*dict.fromkeys(toast)]); log(">> SENHA 123456 (verificar toast)")
        tw.snap(pg, PASTA, "pwd4-final", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "pwd4-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
