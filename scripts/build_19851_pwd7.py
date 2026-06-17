# -*- coding: utf-8 -*-
"""19851 senha (headed, shot limpo) — abre kebab, clica 'Alterar senha', ESPERA dialog
ate 6s, preenche 123456. Se nao abrir, confirma bloqueio (provavel 1o-acesso)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider_acoes"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=False); tw.login(pg, c)
    try:
        pg.goto(base+f"/o/{c['org_id']}/users", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        pg.get_by_placeholder(re.compile("Pesquis|Buscar", re.I)).first.fill("qalider19851"); pg.wait_for_timeout(3000)
        pg.locator("tbody tr").first.wait_for(timeout=8000)
        pg.locator("tbody tr").first.locator("button").last.click(timeout=4000); pg.wait_for_timeout(1500)
        # clica Alterar senha (Playwright real)
        try:
            pg.get_by_role("menuitem", name=re.compile("Alterar senha", re.I)).first.click(timeout=4000)
        except Exception as ex: log("click menuitem:", str(ex)[:40])
        # espera explicita por dialog OU password input
        modal_ok = False
        for _ in range(12):
            n = pg.evaluate(r"""()=>{const d=document.querySelector('[role=dialog],.chakra-modal__content');const pw=[...document.querySelectorAll('input')].filter(e=>e.offsetParent!==null&&(e.type==='password'||/senha|password/i.test(e.name||e.id||e.placeholder||'')));
              return {dialog:!!d, dlgTxt:d?(d.innerText||'').slice(0,60):'', pw:pw.length};}""")
            if n["pw"] or (n["dialog"] and "senha" in n["dlgTxt"].lower()):
                modal_ok = True; log("modal/senha detectado:", n); break
            pg.wait_for_timeout(500)
        if not modal_ok:
            log("modal de senha NAO abriu apos 6s")
        # preenche se abriu
        pwds = pg.locator("input[type=password]:visible, input[name*=password]:visible, input[name*=senha]:visible, input[placeholder*=senha i]:visible")
        log("campos senha:", pwds.count())
        for i in range(pwds.count()):
            try: pwds.nth(i).fill("123456", timeout=2500); log("  campo", i, "ok")
            except Exception: pass
        if pwds.count():
            sv = pg.get_by_role("button", name=re.compile("Salvar|Confirmar|Alterar|Redefinir", re.I))
            if sv.count(): sv.first.click(timeout=4000); pg.wait_for_timeout(2500)
            toast = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,3)""")
            log("toast:", [*dict.fromkeys(toast)]); log(">> SENHA 123456 definida (ver toast)")
        tw.snap(pg, PASTA, "pwd7-final", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-300:])
        try: tw.snap(pg, PASTA, "pwd7-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
