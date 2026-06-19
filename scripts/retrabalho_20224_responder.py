"""20224: abrir 'Responder avaliacao' (autoavaliacao) e verificar banner do avaliado."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")


def aceitar(page):
    try:
        b = page.get_by_role("button", name=re.compile(r"^Aceitar$", re.I)).first
        if b.count() and b.is_visible(): b.click(); page.wait_for_timeout(1000)
    except Exception: pass


def tentar_responder(page, cu, quem):
    tw.login(page, cu, admin=False)
    page.wait_for_timeout(2500); aceitar(page)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/development", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3500); aceitar(page); tw.dispensar_nps(page)
    tw.snap(page, PASTA, f"12-{quem}-avaliacoes")
    linhas = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t && !/Ciclo\s+Liderado|Não há dados/.test(t))""")
    print(f"  [{quem}] itens avaliacoes:", linhas)
    # tentar abrir a 1a avaliacao (botao Responder / Iniciar / clique na linha)
    abriu = False
    for nome in ["Responder", "Iniciar", "Preencher", "Continuar", "Avaliar"]:
        b = page.get_by_role("button", name=re.compile(nome, re.I))
        if b.count() and b.first.is_visible():
            b.first.click(); abriu = True; print(f"  clicou '{nome}'"); break
    if not abriu and linhas:
        try:
            page.locator("tr,[role=row]").filter(has_text=re.compile("autoavaliacao|QA 20224|Ciclo", re.I)).first.click(); abriu = True
        except Exception: pass
    page.wait_for_timeout(3500); aceitar(page)
    return abriu


with tw.sync_playwright() as p:
    # tentar Julia primeiro, depois Adriana
    for email, quem in [("julia@sophia.tech.com.br", "julia"), ("adriana@twygo.com", "adriana")]:
        cu = dict(c); cu["email"] = email; cu["senha"] = "123456"
        browser, ctx, page = tw.nova_pagina(p)
        try:
            abriu = tentar_responder(page, cu, quem)
            print(f"  [{quem}] abriu responder? {abriu} | url={page.url}")
            if "assessment" in page.url or "player" in page.url or "responder" in page.url.lower() or abriu:
                tw.snap(page, PASTA, f"13-{quem}-responder-avaliacao", full=False)
                # checar banner do avaliado + computed styles
                banner = page.evaluate(r"""()=>{
                    const b=document.querySelector('[data-test-id="assessment-player-evaluatee-banner"]');
                    if(!b) return {achou:false};
                    const cs=getComputedStyle(b);
                    // nome (PersonCell) vs eyebrow
                    const texts=Array.from(b.querySelectorAll('p,span,div')).map(e=>({t:(e.innerText||'').replace(/\s+/g,' ').trim(),fw:getComputedStyle(e).fontWeight,fs:getComputedStyle(e).fontSize})).filter(x=>x.t);
                    return {achou:true, html:(b.innerText||'').replace(/\s+/g,' ').trim().slice(0,150), border:cs.borderColor, texts:texts.slice(0,8)};
                }""")
                print(f"  [{quem}] BANNER:", banner)
        except SystemExit as e:
            print(f"  [{quem}] login falhou:", e)
        except Exception as e:
            print(f"  [{quem}] erro:", str(e)[:120])
        ctx.close(); browser.close()
        if "BANNER" in str(locals()):
            pass
print("OK")
