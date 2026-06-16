# -*- coding: utf-8 -*-
"""19815 v2 (PR #10679).
P2: editor legado (org 36675, ativ 9280032) — abrir "Informações a exibir"
    (select-multi-static), selecionar um campo novo e confirmar que o checkbox e
    os campos da marca d'água NÃO somem.
P1-recon: org 19653 (MIGR / testedemigracao, env do card) — verificar se tem
    Studio (novo_estudio) e se o form de vídeo do Studio mostra o checkbox de
    marca d'água após "Segurança do arquivo".
"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "retrabalho_19815_marca_dagua"
tid = lambda v: f'[data-test-id="{v}"]'
res = {}

def problema2_v2():
    c = tw.cfg()  # 36675
    URL = f"{c['base_url']}/e/787696/contents/9280032/edit"
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
        tw.login(page, c, admin=False)
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000); tw.dispensar_nps(page)
            lbl = page.locator("label.chakra-checkbox", has_text="Habilitar marca d'água no vídeo")
            # garantir habilitado
            if lbl.count() and lbl.first.get_attribute("data-checked") is None:
                lbl.first.scroll_into_view_if_needed(); lbl.first.click(); page.wait_for_timeout(1500)
            # estado ANTES de mexer no select
            def secao_marca():
                return page.evaluate("""()=>{
                    const txt=document.body.innerText;
                    return {
                      checkbox: !!document.querySelector('#water-mark-video-enabled') || /Habilitar marca d'?\\s*[aá]gua no v[ií]deo/i.test(txt),
                      infoExibir: /Informa[çc][õo]es a exibir/i.test(txt),
                      tamFonte: /Tamanho da fonte/i.test(txt),
                      corFonte: /Cor da fonte/i.test(txt),
                      posicao: /Posi[çc][ãa]o/i.test(txt),
                      tipoExib: /Tipo de exibi[çc][ãa]o/i.test(txt),
                    };}""")
            antes = secao_marca()
            print(f"[P2] secao marca ANTES: {antes}")
            tw.snap(page, PASTA, "v2-p2-01-antes")

            # localizar o controle do multi-select "Informações a exibir":
            # o container clicável fica logo após o label. Abrimos via JS clicando nele.
            abriu = page.evaluate("""()=>{
                const labels=[...document.querySelectorAll('label,div,span,p')];
                const lab=labels.find(e=>/^Informa[çc][õo]es a exibir/i.test((e.innerText||'').trim()));
                if(!lab) return 'sem-label';
                // sobe pro container do form-group e acha o controle de select
                let cont=lab.closest('div'); let ctrl=null;
                for(let k=0;k<4 && cont;k++){
                  ctrl=cont.querySelector('.css-* , [class*=control], [class*=select], .chakra-select__wrapper, [role=combobox], input');
                  if(ctrl) break; cont=cont.parentElement;
                }
                // fallback: clicar no próprio container que tem os chips CPF/E-mail
                const chip=[...document.querySelectorAll('*')].find(e=>/^CPF$/.test((e.innerText||'').trim()));
                const target = ctrl || (chip? chip.closest('div'):null) || lab.parentElement;
                target.scrollIntoView({block:'center'});
                target.click();
                return target.className||target.tagName;
            }""")
            print(f"[P2] abri controle: {abriu}")
            page.wait_for_timeout(1200)
            tw.snap(page, PASTA, "v2-p2-02-dropdown-aberto")
            # opções disponíveis (não selecionadas): pegar item de menu por texto e clicar via JS
            sel = page.evaluate("""()=>{
                const cands=[...document.querySelectorAll('[role=option], li.menu-item, li[class*=option], .chakra-menu__menuitem, [class*=option]')]
                  .filter(e=>{const t=(e.innerText||'').trim(); return /^(Nome|Matr[ií]cula|Empresa|Cargo|Telefone|Departamento)$/i.test(t);});
                if(!cands.length) return null;
                const o=cands[0]; const t=o.innerText.trim();
                o.scrollIntoView({block:'center'}); o.click();
                return t;
            }""")
            print(f"[P2] selecionei opção: {sel}")
            page.wait_for_timeout(2000)
            tw.snap(page, PASTA, "v2-p2-03-apos-selecionar", full=True)
            depois = secao_marca()
            print(f"[P2] secao marca DEPOIS: {depois}")
            # PASSA se, após selecionar, o checkbox e os campos da marca continuam presentes
            campos_ok = all([depois["checkbox"], depois["infoExibir"], depois["tamFonte"], depois["corFonte"], depois["posicao"], depois["tipoExib"]])
            efetivou = sel is not None
            res["P2_editor_legado"] = (campos_ok and efetivou, f"selecionou={sel} | antes={antes} depois={depois}")
        except Exception as e:
            print(f"[P2] ERRO {e}"); tw.snap(page, PASTA, "v2-p2-99-erro")
            res["P2_editor_legado"] = (False, f"erro: {e}")
        finally:
            ctx.close(); browser.close()

def recon_p1_19653():
    c = tw.cfg("MIGR")  # 19653 testedemigracao
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
        tw.login(page, c)
        try:
            page.goto(f"{c['base_url']}/o/{c['org_id']}/events?tab=events&profile=admin",
                      wait_until="domcontentloaded", timeout=45000)
            tw.dispensar_nps(page); page.wait_for_timeout(4000)
            tw.snap(page, PASTA, "v2-p1recon-listagem")
            # achar primeiro curso e abrir edição p/ ver se tem aba Atividades (Studio)
            anchor = page.locator('a[href*="/contents/"], a[href*="/events/"]').first
            href = anchor.get_attribute("href") if anchor.count() else None
            print(f"[P1recon] org 19653 — 1o conteudo href={href}")
            mid = re.search(r"/(?:contents|events)/(\d+)", href or "")
            cid = mid.group(1) if mid else None
            if cid:
                page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{cid}/edit?tab=studio",
                          wait_until="domcontentloaded", timeout=45000)
                tw.dispensar_nps(page); page.wait_for_timeout(5000)
                tabs = page.evaluate("()=>Array.from(document.querySelectorAll('[role=tab]')).map(t=>(t.innerText||'').trim())")
                tem_studio = any(re.search(r"Atividades|Est.dio", t, re.I) for t in tabs)
                print(f"[P1recon] cid={cid} abas={tabs} tem_studio={tem_studio}")
                tw.snap(page, PASTA, "v2-p1recon-edit")
                res["P1_recon_19653"] = (None, f"cid={cid} abas={tabs} tem_studio={tem_studio}")
            else:
                res["P1_recon_19653"] = (None, "nao achei conteudo p/ inspecionar")
        except Exception as e:
            print(f"[P1recon] ERRO {e}"); tw.snap(page, PASTA, "v2-p1recon-erro")
            res["P1_recon_19653"] = (None, f"erro: {e}")
        finally:
            ctx.close(); browser.close()

if __name__ == "__main__":
    PASTA.mkdir(parents=True, exist_ok=True)
    problema2_v2()
    recon_p1_19653()
    print("\n=== RESUMO 19815 v2 ===")
    for k, (ok, det) in res.items():
        print(f"  {k}: {('PASSOU' if ok else 'FALHOU') if ok is not None else 'RECON'} | {det}")
