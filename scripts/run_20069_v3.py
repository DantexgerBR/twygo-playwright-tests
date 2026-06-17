# -*- coding: utf-8 -*-
"""20069 v3 — isola o e-mail: preenche os campos de telefone obrigatorios e salva.
Se salvar (PATCH 2xx, volta pra lista) => o e-mail disabled foi aceito no payload
=> 20069 corrigido. Se voltar erro de E-MAIL => bug. Captura tudo."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_20069_email"
c = tw.cfg("MIGR"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    net = []
    pg.on("response", lambda r: net.append((r.request.method, r.status, r.url.split("twygoead.com")[-1][:55])) if r.request.method in ("POST","PUT","PATCH","DELETE") and "twygoead.com/api" in r.url else None)
    try:
        pg.goto(base+f"/o/{c['org_id']}/succession_people_analysis", wait_until="domcontentloaded", timeout=30000)
        tw.dispensar_nps(pg); pg.wait_for_timeout(3500)
        pg.mouse.click(1449, 276); pg.wait_for_timeout(2500)
        if "/edit" not in pg.url: pg.mouse.click(1449, 276); pg.wait_for_timeout(2500)
        log("editor:", pg.url[-40:])
        # mapeia inputs por label (Telefone pessoal/comercial/Celular)
        campos = pg.evaluate(r"""()=>{const out=[];document.querySelectorAll('input,textarea').forEach(e=>{
          if(e.offsetParent===null)return;
          // acha label associado: por for=id ou texto proximo acima
          let lab='';if(e.id){const l=document.querySelector('label[for="'+e.id+'"]');if(l)lab=(l.innerText||'').trim();}
          if(!lab){const p=e.closest('div');const l=p&&p.querySelector('label');if(l)lab=(l.innerText||'').trim();}
          out.push({lab:lab.slice(0,30),name:e.name||'',id:e.id||'',val:(e.value||'').slice(0,15),disabled:e.disabled});});return out;}""")
        for x in campos: log("  campo:", x)
        # preenche telefones obrigatorios (qualquer input cujo label tenha Telefone/Celular e esteja vazio)
        for kw, val in [("Telefone pessoal","11999990001"),("Telefone comercial","1133330001"),("Celular","11999990002")]:
            inp = pg.locator(f"input").filter(visible=True)
            # tenta por label via id
            target = pg.evaluate(r"""(kw)=>{const labs=[...document.querySelectorAll('label')].filter(l=>(l.innerText||'').trim().toLowerCase().startsWith(kw.toLowerCase()));
              if(!labs.length)return null;const l=labs[0];let inp=l.getAttribute('for')?document.getElementById(l.getAttribute('for')):(l.closest('div')?.querySelector('input'));
              return inp?inp.id||inp.name||'(noid)':null;}""", kw)
            if target and target != "(noid)":
                sel = f"#{target}" if not target.startswith("(") else None
                loc = pg.locator(f"input#{target}") if "#" in (sel or "") else pg.locator(f"input[name='{target}']")
                if loc.count():
                    try: loc.first.fill(val, timeout=3000); log(f"  preenchi {kw}={val} ({target})")
                    except Exception as ex: log(f"  falhou {kw}: {str(ex)[:40]}")
            else:
                log(f"  {kw}: input nao localizado (target={target})")
        tw.snap(pg, PASTA, "50-telefones", full=True)
        net.clear()
        pg.get_by_role("button", name=re.compile("^Salvar$", re.I)).first.click(timeout=5000); pg.wait_for_timeout(3500)
        res = pg.evaluate(r"""()=>{const toast=[...document.querySelectorAll('[class*=toast i],[role=status],.chakra-alert,[role=alert]')].filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,5);
          return {toast:[...new Set(toast)]};}""")
        log("\ntoast pos-salvar:", res["toast"])
        log("saiu do /edit:", "/edit" not in pg.url, "| url:", pg.url[-40:])
        log("Network:", net[-6:])
        email_err = any("mail" in t.lower() for t in res["toast"])
        ok = ("/edit" not in pg.url) or any(s in (200,201,204) for _,s,_ in net)
        log(f"\n>> erro de E-MAIL? {email_err} | salvou? {ok}")
        log(f">> 20069: {'PASSOU (e-mail nao bloqueia; salvou)' if ok and not email_err else ('FALHOU (erro de e-mail)' if email_err else 'inconclusivo — ver toast')}")
        tw.snap(pg, PASTA, "51-pos-salvar", full=True)
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "erro4", full=True)
        except: pass
    finally:
        ctx.close(); b.close()
