# -*- coding: utf-8 -*-
"""19851 senha (final robusto) — abre kebab (retry), clica Alterar senha, dumpa TODOS
os inputs visiveis da pagina (modal pode ter container diferente), preenche 123456."""
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
        # abre kebab (retry ate menu popular)
        for _ in range(4):
            kb = pg.locator("tbody tr").first.locator("button")
            if kb.count():
                kb.last.click(timeout=4000); pg.wait_for_timeout(1000)
            n = pg.evaluate("()=>document.querySelectorAll('[role=menuitem],.chakra-menu__menuitem').length")
            if n: break
            pg.wait_for_timeout(800)
        log("menuitems:", pg.evaluate("()=>[...document.querySelectorAll('[role=menuitem]')].map(e=>e.innerText.replace(/\\s+/g,' ').trim())"))
        # clica Alterar senha (coordenada do menuitem que termina com 'Alterar senha')
        box = pg.evaluate(r"""()=>{const c=[...document.querySelectorAll('[role=menuitem]')].find(x=>/Alterar senha$/.test((x.innerText||'').replace(/\s+/g,' ').trim()));if(!c)return null;const r=c.getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2};}""")
        log("box:", box)
        if box: pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(2500)
        # dump TODOS inputs visiveis
        ins = pg.evaluate(r"""()=>[...document.querySelectorAll('input')].filter(e=>e.offsetParent!==null).map(e=>({name:e.name||e.id||'',type:e.type,ph:e.placeholder||''}))""")
        log("inputs visiveis na pagina:", ins)
        tw.snap(pg, PASTA, "pwd3-pos-click", full=True)
        # preenche os que parecem senha
        alvo = pg.locator("input[type=password]:visible")
        if not alvo.count():
            alvo = pg.locator("input[name*=password]:visible, input[name*=senha]:visible, input[placeholder*=senha i]:visible")
        log("campos senha:", alvo.count())
        for i in range(alvo.count()):
            try: alvo.nth(i).fill("123456", timeout=2000); log("  preenchi campo", i)
            except Exception: pass
        if alvo.count():
            sv = pg.get_by_role("button", name=re.compile("Salvar|Confirmar|Alterar|Redefinir", re.I))
            if sv.count(): sv.first.click(timeout=4000); pg.wait_for_timeout(2500)
            toast = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,3)""")
            log("toast:", [*dict.fromkeys(toast)])
            log(">> SENHA DEFINIDA (verificar toast)")
        tw.snap(pg, PASTA, "pwd3-final", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "pwd3-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
