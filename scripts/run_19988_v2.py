# -*- coding: utf-8 -*-
"""19988 v2 — cria uma função de negócio no 37048 (estava vazio), depois testa a
digitação direta no campo 'Informações adicionais' (Editar>Competências>Gerar com IA).
PR #10713. Headless. Resiliente (loga cada passo)."""
import re, sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19988_info_adicionais"
c = tw.cfg("RECERT"); base = c["base_url"].rstrip("/")
log = lambda *a: print(*a, flush=True)
ROLES = base + f"/o/{c['org_id']}/roles"
TESTE = "teste digitacao direta 19988"

with tw.sync_playwright() as p:
    b, ctx, pg = tw.nova_pagina(p, headless=True); tw.login(pg, c)
    try:
        # ---- criar função se não existir ----
        pg.goto(ROLES, wait_until="domcontentloaded", timeout=30000); tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
        tem = "Não há dados" not in pg.evaluate("()=>document.body.innerText")
        log("[roles] já tem função?", tem)
        if not tem:
            pg.get_by_role("button", name=re.compile(r"Adicionar", re.I)).first.click(timeout=6000); pg.wait_for_timeout(2500)
            tw.snap(pg, PASTA, "v2-01-form-funcao", full=True)
            # nome (campo visível do editor de função)
            pg.locator("#name").fill("QA19988 Funcao Teste")
            # preencher quaisquer campos obrigatórios óbvios (selects com *)
            log("[funcao] preenchido nome; tentando salvar")
            pg.get_by_role("button", name=re.compile(r"^(Salvar|Adicionar|Criar|Cadastrar)$", re.I)).first.click(timeout=6000)
            pg.wait_for_timeout(3500); tw.dispensar_nps(pg)
            corpo = pg.evaluate("()=>document.body.innerText")
            falta = re.search(r"obrigat[óo]ri|preencha|campo.*requerid", corpo, re.I)
            log("[funcao] bloqueio?", falta.group(0)[:80] if falta else "—")
            tw.snap(pg, PASTA, "v2-02-pos-salvar-funcao", full=True)
            pg.goto(ROLES, wait_until="domcontentloaded", timeout=30000); tw.dispensar_nps(pg); pg.wait_for_timeout(3000)
            tem = "Não há dados" not in pg.evaluate("()=>document.body.innerText")
            log("[roles] função criada?", tem)
        if not tem:
            log("=> 19988: BLOQUEADO — não consegui criar função (form exige campos extras). Ver v2-02.")
            raise SystemExit
        # ---- Editar a função -> Competências -> Gerar com IA ----
        ed = pg.get_by_role("button", name=re.compile(r"^Editar$", re.I)).first
        if not ed.count(): ed = pg.get_by_text(re.compile(r"^Editar$", re.I)).first
        ed.click(timeout=6000); pg.wait_for_timeout(3000); tw.dispensar_nps(pg)
        pg.get_by_text(re.compile(r"^Compet[êe]ncias$", re.I)).first.click(timeout=6000); pg.wait_for_timeout(2500)
        tw.snap(pg, PASTA, "v2-03-competencias", full=True)
        pg.get_by_role("button", name=re.compile(r"Gerar com IA", re.I)).first.click(timeout=6000); pg.wait_for_timeout(3000); tw.dispensar_nps(pg)
        tw.snap(pg, PASTA, "v2-04-gerar-ia", full=True)
        # ---- testar digitação direta no campo Informações adicionais ----
        foco = pg.evaluate(r"""()=>{const lab=[...document.querySelectorAll('label,p,span,div')].find(e=>/Informa[çc][õo]es adicionais/i.test((e.innerText||'').trim().slice(0,40)));
          if(!lab) return 'sem-label'; let cont=lab.parentElement,ce=null;
          for(let k=0;k<5&&cont;k++){ce=cont.querySelector('[contenteditable=true],textarea,[role=textbox]');if(ce)break;cont=cont.parentElement;}
          if(!ce) return 'sem-campo'; ce.scrollIntoView({block:'center'}); ce.focus(); ce.click(); return 'focado';}""")
        log("[campo] foco:", foco)
        pg.wait_for_timeout(500); pg.keyboard.type(TESTE, delay=30); pg.wait_for_timeout(800)
        val = pg.evaluate(r"""()=>{const lab=[...document.querySelectorAll('label,p,span,div')].find(e=>/Informa[çc][õo]es adicionais/i.test((e.innerText||'').trim().slice(0,40)));
          let cont=lab&&lab.parentElement,ce=null;for(let k=0;k<5&&cont;k++){ce=cont.querySelector('[contenteditable=true],textarea,[role=textbox]');if(ce)break;cont=cont.parentElement;}
          return ce?(ce.value!==undefined?ce.value:ce.innerText):'';}""")
        entrou = "teste" in (val or "").lower()
        log(f"[campo] valor: {val!r} | entrou={entrou}")
        tw.snap(pg, PASTA, "v2-05-pos-digitar", full=True)
        log(f"\n=> 19988: {'PASSOU (digitação direta funciona)' if entrou else 'FALHOU (não aceitou digitação direta)'}")
    except SystemExit: pass
    except Exception as e:
        log("ERRO:", e); log(traceback.format_exc()[-400:])
        try: tw.snap(pg, PASTA, "v2-99-erro", full=True)
        except Exception: pass
    finally:
        ctx.close(); b.close()
