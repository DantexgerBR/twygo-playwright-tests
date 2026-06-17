# -*- coding: utf-8 -*-
"""19851 — reset de senha via kebab da linha do usuario qalider19851 (lista Usuarios)."""
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
        srch = pg.get_by_placeholder(re.compile("Pesquis|Buscar", re.I))
        if srch.count(): srch.first.fill("qalider19851"); pg.wait_for_timeout(2500)
        # kebab da linha (ultimo botao da row)
        row = pg.locator("tbody tr").first
        kb = row.locator("button")
        log("botoes na row:", kb.count())
        if kb.count(): kb.last.click(timeout=4000); pg.wait_for_timeout(1200)
        opts = pg.evaluate(r"""()=>[...document.querySelectorAll('[role=menuitem],.chakra-menu__menuitem,[role=menu] button,[role=menu] a')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean)""")
        log("opcoes kebab:", opts)
        tw.snap(pg, PASTA, "pwd2-kebab", full=True)
        # clica "Alterar senha" por COORDENADA (mouse real)
        mi = pg.get_by_role("menuitem", name=re.compile("Alterar senha", re.I))
        log("menuitem Alterar senha count:", mi.count())
        if mi.count():
            try: mi.first.click(timeout=4000, force=True)
            except Exception as ex: log("click1:", str(ex)[:40])
            pg.wait_for_timeout(2000)
        if True:
            log("clicou Alterar senha")
            # preenche campos de senha (password ou text)
            pwds = pg.locator("input[type=password]:visible, input[name*=password]:visible, input[name*=senha]:visible")
            log("campos senha no modal:", pwds.count())
            if not pwds.count():
                # dump inputs do modal
                ins = pg.evaluate(r"""()=>{const m=document.querySelector('.chakra-modal__content,[role=dialog]');if(!m)return'(sem modal)';return [...m.querySelectorAll('input')].map(e=>e.name||e.type||e.id).slice(0,6);}""")
                log("inputs no modal:", ins)
            for i in range(pwds.count()):
                try: pwds.nth(i).fill("123456", timeout=2000)
                except Exception: pass
            tw.snap(pg, PASTA, "pwd2-modal", full=True)
            sv = pg.get_by_role("button", name=re.compile("Salvar|Confirmar|Alterar|Redefinir", re.I))
            if sv.count(): sv.first.click(timeout=4000); pg.wait_for_timeout(2500)
            toast = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert,[role=alert]')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,4)""")
            log("toast:", [*dict.fromkeys(toast)])
            tw.snap(pg, PASTA, "pwd2-salvo", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "pwd2-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
