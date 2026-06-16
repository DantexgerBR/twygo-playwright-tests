# -*- coding: utf-8 -*-
"""19815 v3 (PR #10679) — P2 com dropdown robusto + recon P1 no 19653."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19815_marca_dagua"
res = {}

JS_SECAO = r"""()=>{const txt=document.body.innerText;return{
  checkbox:!!document.querySelector('#water-mark-video-enabled')||/Habilitar marca d'?\s*[aá]gua no v[ií]deo/i.test(txt),
  infoExibir:/Informa[çc][õo]es a exibir/i.test(txt),
  tamFonte:/Tamanho da fonte/i.test(txt),
  corFonte:/Cor da fonte/i.test(txt),
  posicao:/Posi[çc][ãa]o/i.test(txt),
  tipoExib:/Tipo de exibi[çc][ãa]o/i.test(txt)};}"""

def problema2():
    c = tw.cfg()  # 36675
    URL = f"{c['base_url']}/e/787696/contents/9280032/edit"
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
        tw.login(page, c, admin=False)
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000); tw.dispensar_nps(page)
            lbl = page.locator("label.chakra-checkbox", has_text="Habilitar marca d'água no vídeo")
            if lbl.count() and lbl.first.get_attribute("data-checked") is None:
                lbl.first.scroll_into_view_if_needed(); lbl.first.click(); page.wait_for_timeout(1500)
            antes = page.evaluate(JS_SECAO)
            print(f"[P2] ANTES: {antes}")
            tw.snap(PASTA and page, PASTA, "v3-p2-01-antes") if False else tw.snap(page, PASTA, "v3-p2-01-antes")

            # abrir o multi-select clicando no container do chip "CPF"
            abriu = page.evaluate(r"""()=>{
              const all=[...document.querySelectorAll('*')];
              const chip=all.find(e=>(e.children.length===0)&&/^CPF$/.test((e.innerText||'').trim()));
              const cont=chip?chip.closest('div'):null;
              const target=cont||all.find(e=>/Informa[çc][õo]es a exibir/i.test((e.innerText||'').trim()));
              if(!target) return 'sem-alvo';
              target.scrollIntoView({block:'center'}); target.click();
              return (target.className||target.tagName||'').toString().slice(0,60);
            }""")
            print(f"[P2] abri controle via: {abriu}")
            page.wait_for_timeout(1200)
            tw.snap(page, PASTA, "v3-p2-02-dropdown")
            # listar opções visíveis no menu
            opcoes = page.evaluate(r"""()=>[...document.querySelectorAll('li.menu-item,[role=option],.chakra-menu__menuitem,li[class*=option]')]
              .map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,20)""")
            print(f"[P2] opções no dropdown: {opcoes}")
            # selecionar uma opção nova (não CPF/E-mail) via JS
            sel = page.evaluate(r"""()=>{
              const cands=[...document.querySelectorAll('li.menu-item,[role=option],.chakra-menu__menuitem,li[class*=option]')]
                .filter(e=>{const t=(e.innerText||'').trim();return t&&!/^(CPF|E-?mail)$/i.test(t);});
              if(!cands.length) return null;
              const o=cands[0]; const t=o.innerText.trim();
              o.scrollIntoView({block:'center'}); o.click(); return t;
            }""")
            print(f"[P2] selecionei: {sel}")
            page.wait_for_timeout(2500)
            tw.snap(page, PASTA, "v3-p2-03-apos-selecionar", full=True)
            depois = page.evaluate(JS_SECAO)
            print(f"[P2] DEPOIS: {depois}")
            campos_ok = all(depois.values())
            res["P2_editor_legado"] = (campos_ok and sel is not None,
                                       f"selecionou={sel} opcoes={opcoes} | antes={antes} depois={depois}")
        except Exception as e:
            print(f"[P2] ERRO {e}"); tw.snap(page, PASTA, "v3-p2-99-erro")
            res["P2_editor_legado"] = (False, f"erro: {e}")
        finally:
            ctx.close(); browser.close()

def recon_p1():
    c = tw.cfg("MIGR")  # 19653
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
        tw.login(page, c)
        try:
            page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin",
                      wait_until="domcontentloaded", timeout=45000)
            tw.dispensar_nps(page); page.wait_for_timeout(4000)
            tw.snap(page, PASTA, "v3-p1-listagem")
            # coletar links de conteúdo (contents/{id}) — abrir kebab Editar se preciso
            hrefs = page.evaluate(r"""()=>[...document.querySelectorAll('a')].map(a=>a.getAttribute('href')||'').filter(h=>/\/contents\/\d+/.test(h)).slice(0,10)""")
            print(f"[P1] hrefs contents: {hrefs}")
            cid = None
            if hrefs:
                m = re.search(r"/contents/(\d+)", hrefs[0]); cid = m.group(1) if m else None
            if not cid:
                # tentar via kebab Editar do 1o conteúdo
                try:
                    page.get_by_text("more_vert", exact=True).first.click(force=True); page.wait_for_timeout(1000)
                    ed = page.get_by_role("menuitem", name=re.compile(r"^Editar$", re.I)).first
                    if ed.count():
                        ed.click(); page.wait_for_timeout(4000)
                        m = re.search(r"/contents/(\d+)", page.url); cid = m.group(1) if m else None
                except Exception as e:
                    print(f"[P1] kebab editar: {e}")
            print(f"[P1] cid escolhido: {cid} (url={page.url})")
            if cid:
                page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{cid}/edit?tab=studio",
                          wait_until="domcontentloaded", timeout=45000)
                tw.dispensar_nps(page); page.wait_for_timeout(5000)
                tabs = page.evaluate("()=>Array.from(document.querySelectorAll('[role=tab]')).map(t=>(t.innerText||'').trim())")
                tem_studio = any(re.search(r"Atividades|Est.dio", t, re.I) for t in tabs)
                print(f"[P1] cid={cid} abas={tabs} tem_studio={tem_studio}")
                tw.snap(page, PASTA, "v3-p1-edit")
                res["P1_recon_19653"] = (None, f"cid={cid} abas={tabs} tem_studio={tem_studio}")
            else:
                res["P1_recon_19653"] = (None, "sem conteudo p/ inspecionar")
        except Exception as e:
            print(f"[P1] ERRO {e}"); tw.snap(page, PASTA, "v3-p1-erro")
            res["P1_recon_19653"] = (None, f"erro: {e}")
        finally:
            ctx.close(); browser.close()

if __name__ == "__main__":
    PASTA.mkdir(parents=True, exist_ok=True)
    problema2()
    recon_p1()
    print("\n=== RESUMO 19815 v3 ===")
    for k,(ok,det) in res.items():
        print(f"  {k}: {('PASSOU' if ok else 'FALHOU') if ok is not None else 'RECON'} | {det}")
