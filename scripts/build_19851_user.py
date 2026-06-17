# -*- coding: utf-8 -*-
"""19851 — cria usuario LIDER de teste no 19653 (com telefones p/ evitar 422), perfil
'Lider de equipe' + Colaborador + modo Aluno. Depois define senha 123456."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19851_lider_acoes"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
EMAIL = "qalider19851@teste.com"
log = lambda *a: print(*a, flush=True)

def check_label(pg, texto):
    box = pg.evaluate(r"""(t)=>{const labs=[...document.querySelectorAll('label,span,p,div')].filter(e=>(e.innerText||'').replace(/\s+/g,' ').trim()===t&&e.getBoundingClientRect().left>260);
      if(!labs.length)return null;const l=labs[0];l.scrollIntoView({block:'center'});const r=l.getBoundingClientRect();return{x:r.left-8,y:r.top+r.height/2};}""", texto)
    if not box: return False
    pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(300); return True

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    net = []
    pg.on("response", lambda r: net.append((r.request.method, r.status, r.url.split("twygoead.com")[-1][:40])) if r.request.method in ("POST","PUT") and "/api/" in r.url and ("user" in r.url.lower() or "professional" in r.url.lower()) else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/users/new", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        # campos texto
        campos = {"professional[email]":EMAIL, "professional[first_name]":"QALider", "professional[last_name]":"Teste19851",
                  "professional[phone1]":"(47) 98888-8888", "professional[phone2]":"(47) 3333-3333", "professional[cell_phone]":"(47) 98888-8888",
                  "professional[address]":"Rua Teste", "professional[city]":"Joinville", "professional[enterprise]":"Twygo", "professional[site]":"www.twygo.com"}
        for nm, val in campos.items():
            f = pg.locator(f"input[name='{nm}']")
            if f.count():
                try: f.fill(val, timeout=3000)
                except Exception: pass
        # selects (business_line, role, number_of_employees) -> 2a opcao
        for nm in ["professional[business_line]","professional[number_of_employees]","professional[role]"]:
            s = pg.locator(f"select[name='{nm}']")
            if s.count():
                try:
                    opts = s.first.evaluate("e=>[...e.options].map(o=>o.value).filter(v=>v)")
                    if opts: s.first.select_option(opts[0])
                except Exception as ex: log(f"select {nm}: {str(ex)[:30]}")
        # perfil: Lider de equipe + Colaborador + modo Aluno
        log("check Lider de equipe:", check_label(pg, "Líder de equipe"))
        log("check Colaborador:", check_label(pg, "Colaborador"))
        log("check Aluno:", check_label(pg, "Aluno"))
        tw.snap(pg, PASTA, "newuser-preenchido", full=True)
        net.clear()
        pg.get_by_role("button", name=re.compile("^Salvar$", re.I)).first.click(timeout=5000); pg.wait_for_timeout(3500)
        toast = pg.evaluate(r"""()=>[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert,[role=alert],[class*=error i]')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,5)""")
        log("net:", net[-4:]); log("toast:", [*dict.fromkeys(toast)]); log("url:", pg.url[-40:])
        criou = any(s in (200,201) for _,s,_ in net) or "users/new" not in pg.url
        log("USUARIO CRIADO:", criou, "| email:", EMAIL)
        tw.snap(pg, PASTA, "newuser-salvo", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "newuser-build-erro", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
