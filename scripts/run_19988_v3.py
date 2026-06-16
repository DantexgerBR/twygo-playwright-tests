# -*- coding: utf-8 -*-
"""19988 v3 — cria função (cai no editor), vai na aba Competências > Gerar com IA e
testa digitação DIRETA no campo 'Informações adicionais' (PlateJS). 37048. PR #10713."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19988_info_adicionais"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)
TESTE = "teste digitacao direta 19988"

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        # criar função -> cai no editor
        pg.goto(base + f"/o/{c['org_id']}/roles", wait_until="domcontentloaded", timeout=30000); tw.dispensar_nps(pg); pg.wait_for_timeout(2500)
        pg.get_by_role("button", name=re.compile(r"Adicionar", re.I)).first.click(timeout=6000); pg.wait_for_timeout(2000)
        pg.locator("#name").fill("QA19988 Funcao Teste")
        pg.get_by_role("button", name=re.compile(r"^Salvar$", re.I)).first.click(timeout=6000); pg.wait_for_timeout(3500); tw.dispensar_nps(pg)
        log("[editor] url:", pg.url)
        # aba Competências
        pg.get_by_text(re.compile(r"^Compet[êe]ncias$", re.I)).first.click(timeout=6000); pg.wait_for_timeout(2500)
        tw.snap(pg, PASTA, "v3-01-competencias", full=True)
        # Gerar com IA
        pg.get_by_role("button", name=re.compile(r"Gerar com IA", re.I)).first.click(timeout=6000); pg.wait_for_timeout(3000); tw.dispensar_nps(pg)
        tw.snap(pg, PASTA, "v3-02-gerar-ia", full=True)
        # campo Informações adicionais — digitar DIRETO sem usar toolbar
        foco = pg.evaluate(r"""()=>{const lab=[...document.querySelectorAll('label,p,span,div')].find(e=>/Informa[çc][õo]es adicionais/i.test((e.innerText||'').trim().slice(0,40)));
          if(!lab) return 'sem-label'; let cont=lab.parentElement,ce=null;
          for(let k=0;k<6&&cont;k++){ce=cont.querySelector('[contenteditable=true],textarea,[role=textbox]');if(ce)break;cont=cont.parentElement;}
          if(!ce) return 'sem-campo'; ce.scrollIntoView({block:'center'}); ce.focus(); ce.click(); return 'focado';}""")
        log("[campo] foco:", foco)
        pg.wait_for_timeout(500); pg.keyboard.type(TESTE, delay=35); pg.wait_for_timeout(900)
        val = pg.evaluate(r"""()=>{const lab=[...document.querySelectorAll('label,p,span,div')].find(e=>/Informa[çc][õo]es adicionais/i.test((e.innerText||'').trim().slice(0,40)));
          let cont=lab&&lab.parentElement,ce=null;for(let k=0;k<6&&cont;k++){ce=cont.querySelector('[contenteditable=true],textarea,[role=textbox]');if(ce)break;cont=cont.parentElement;}
          return ce?(ce.value!==undefined?ce.value:ce.innerText):'(sem campo)';}""")
        entrou = "teste" in (val or "").lower()
        log(f"[campo] valor após digitar: {val!r} | entrou={entrou}")
        tw.snap(pg, PASTA, "v3-03-pos-digitar", full=True)
        log(f"\n=> 19988: {'PASSOU (digitação direta funciona)' if entrou else 'FALHOU (campo não aceitou digitação direta)'}")
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "v3-99-erro", full=True)
        except Exception: pass
    finally:
        ctx.close(); b.close()
