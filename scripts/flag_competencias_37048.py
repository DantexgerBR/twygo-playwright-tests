# -*- coding: utf-8 -*-
"""Liga/desliga a flag avaliacao_de_competencias p/ Organization;37048 via Flipper.
Uso: python flag_competencias_37048.py [on|off|status]"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

acao = sys.argv[1] if len(sys.argv) > 1 else "status"
ACTOR = "Organization;37048"
c = tw.cfg(); URL = c["base_url"].rstrip("/") + "/admin/manage/features/avaliacao_de_competencias"

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    pg.goto(URL, wait_until="domcontentloaded", timeout=20000); pg.wait_for_timeout(2000)
    tem = ACTOR in pg.evaluate("()=>document.body.innerText")
    print(f"[status] {ACTOR} já é actor? {tem}")
    if acao == "on" and not tem:
        inp = pg.locator('input[placeholder="MODEL_NAME;ID"]').first
        inp.fill(ACTOR)
        inp.evaluate("e=>e.form.querySelector('input[type=submit],button[type=submit]').click()")
        pg.wait_for_timeout(2500)
        print(f"[on] adicionado? {ACTOR in pg.evaluate('()=>document.body.innerText')}")
    elif acao == "off" and tem:
        # remover: achar o form/Remove do actor 37048
        ok = pg.evaluate(r"""(a)=>{const rows=[...document.querySelectorAll('form,li,tr,div')].filter(e=>(e.innerText||'').includes(a));
          for(const r of rows){const btn=[...r.querySelectorAll('button,input[type=submit]')].find(x=>/remove/i.test((x.innerText||x.value||'')));if(btn){btn.click();return true}}return false}""", ACTOR)
        pg.wait_for_timeout(2500)
        print(f"[off] removido? cliquei={ok} | ainda actor? {ACTOR in pg.evaluate('()=>document.body.innerText')}")
    ctx.close(); b.close()
