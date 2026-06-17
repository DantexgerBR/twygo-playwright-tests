# -*- coding: utf-8 -*-
"""19851 — define senha 123456 pro usuario qalider19851@teste.com no 19653 (admin >
Usuarios > editar > alterar senha)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider_acoes"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
EMAIL = "qalider19851@teste.com"
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/users", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        # busca o usuario
        srch = pg.get_by_placeholder(re.compile("Pesquis|Buscar", re.I))
        if srch.count(): srch.first.fill("qalider19851"); pg.wait_for_timeout(2500)
        tw.snap(pg, PASTA, "pwd-01-lista", full=True)
        # clica o usuario / acao de editar (lapis) -> abre edicao
        row = pg.get_by_text(re.compile("QALider|qalider19851", re.I)).first
        if row.count(): row.click(timeout=4000); pg.wait_for_timeout(2500)
        log("url pos-click:", pg.url[-45:])
        # procura campo de senha ou link 'alterar senha'
        alterar = pg.get_by_text(re.compile("Alterar senha|Redefinir senha|Senha", re.I))
        log("link alterar senha:", alterar.count())
        if alterar.count():
            try: alterar.first.click(timeout=3000); pg.wait_for_timeout(1500)
            except Exception: pass
        # campos de senha
        pwds = pg.locator("input[type=password]")
        log("campos password:", pwds.count())
        for i in range(pwds.count()):
            try: pwds.nth(i).fill("123456", timeout=2000)
            except Exception: pass
        tw.snap(pg, PASTA, "pwd-02-form", full=True)
        # salvar
        sv = pg.get_by_role("button", name=re.compile("Salvar|Confirmar|Alterar", re.I))
        if sv.count(): sv.first.click(timeout=4000); pg.wait_for_timeout(2500)
        toast = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert,[role=alert]')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,4)""")
        log("toast:", [*dict.fromkeys(toast)])
        tw.snap(pg, PASTA, "pwd-03-salvo", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "pwd-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
