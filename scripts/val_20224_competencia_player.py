"""20224: abrir player de COMPETENCIAS (Julia) e verificar banner do avaliado + botoes."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")
cj = dict(c); cj["email"] = "julia@sophia.tech.com.br"; cj["senha"] = "123456"


def aceitar(page):
    try:
        b = page.get_by_role("button", name=re.compile(r"^Aceitar$", re.I)).first
        if b.count() and b.is_visible(): b.click(); page.wait_for_timeout(1000)
    except Exception: pass


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, cj, admin=False)
    page.wait_for_timeout(2500); aceitar(page)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/development", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3500); aceitar(page); tw.dispensar_nps(page)
    tw.snap(page, PASTA, "26-listagem-julia")
    linhas = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&!/Não há dados|^Ciclo\s+Liderado/.test(t))""")
    print("LISTAGEM JULIA:", linhas)

    # clicar Responder na linha de COMPETENCIAS
    compRow = page.locator("tr,[role=row]").filter(has_text=re.compile("compet", re.I)).first
    abriu = False
    try:
        compRow.get_by_role("button", name=re.compile("Responder", re.I)).first.click(timeout=5000); abriu = True
        print("clicou Responder na linha de competencias")
    except Exception:
        # fallback: primeiro Responder
        try:
            page.get_by_role("button", name=re.compile("Responder", re.I)).first.click(timeout=5000); abriu = True
            print("clicou primeiro Responder (fallback)")
        except Exception as ex:
            print("nao achou Responder:", str(ex)[:80])
    page.wait_for_timeout(4000); aceitar(page)
    print("URL player:", page.url)
    tw.snap(page, PASTA, "27-player-competencia", full=False)

    # banner do avaliado
    banner = page.evaluate(r"""()=>{
        const b=document.querySelector('[data-test-id="assessment-player-evaluatee-banner"]');
        if(!b) return {achou:false, html:(document.body.innerText||'').replace(/\s+/g,' ').slice(0,200)};
        const texts=Array.from(b.querySelectorAll('p,span,div')).map(e=>({t:(e.innerText||'').replace(/\s+/g,' ').trim(),fw:getComputedStyle(e).fontWeight,fs:getComputedStyle(e).fontSize})).filter(x=>x.t&&x.t.length<60);
        return {achou:true, txt:(b.innerText||'').replace(/\s+/g,' ').trim().slice(0,150), border:getComputedStyle(b).borderColor, temAvatar:!!b.querySelector('img,[class*=avatar],[class*=Avatar]'), texts:texts.slice(0,8)};
    }""")
    print("BANNER:", banner)
    # botoes
    btns = page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('button')).map(b=>(b.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/Salvar|Finalizar|rascunho/i.test(t)))]""")
    print("BOTOES:", btns)
    ctx.close(); browser.close()
print("OK")
