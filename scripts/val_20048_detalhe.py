"""20048 — detalhar: campos do filtro (+ Novo), opções de Extrair dados, drill-down."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "competencias_20048"
c = tw.cfg("MIGR")


def painel(page):
    return page.evaluate(
        "()=>{const sels=['.chakra-modal__content','[role=dialog]','.chakra-popover__content','[role=menu]','section[role],aside'];"
        "let best='';for(const s of sels){document.querySelectorAll(s).forEach(el=>{"
        "if(el.offsetParent!==null){const t=(el.innerText||'').trim();if(t.length>best.length)best=t;}});}"
        "return best||'(vazio)';}"
    )


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)

    # ---- ANÁLISE INDIVIDUAL: filtro + Novo ----
    page.goto(c["base_url"] + "/o/19653/succession_people_analysis", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4500)
    tw.dispensar_nps(page)
    page.get_by_text("Filtro", exact=False).first.click()
    page.wait_for_timeout(1500)
    # clicar "+ Novo" DENTRO do drawer de filtros (não o badge NOVO da sidebar)
    ok = page.evaluate(
        "()=>{const cand=Array.from(document.querySelectorAll('button,a,[role=button],div'))"
        ".filter(e=>/^\\+?\\s*Novo$/i.test((e.innerText||'').trim())&&e.getBoundingClientRect().left>900&&e.offsetParent);"
        "if(cand.length){cand[0].click();return true;}return false;}"
    )
    print("clicou +Novo no drawer?", ok)
    page.wait_for_timeout(2000)
    tw.snap(page, PASTA, "ai-filtro-novo")
    print("\n### FILTRO + NOVO (análise individual):\n", painel(page)[:2000])
    # listar campos/opções de select
    campos = page.evaluate(
        "()=>Array.from(document.querySelectorAll('option,[role=option],label,button'))"
        ".map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(t=>t&&t.length<40)"
    )
    print("\nCampos visíveis:", sorted(set(campos)))
    page.keyboard.press("Escape"); page.wait_for_timeout(800)
    page.keyboard.press("Escape"); page.wait_for_timeout(800)

    # ---- EXTRAIR DADOS ----
    try:
        page.get_by_text("Extrair dados", exact=False).first.click(timeout=4000)
        page.wait_for_timeout(2500)
        tw.snap(page, PASTA, "ai-extrair-dados")
        print("\n### EXTRAIR DADOS (análise individual):\n", painel(page)[:1500])
    except Exception as e:
        print("Extrair dados falhou:", repr(e))
    page.keyboard.press("Escape"); page.wait_for_timeout(800)

    # ---- DASHBOARD GERAL: drill-down nos links de função/área ----
    page.goto(c["base_url"] + "/o/19653/succession_dashboards", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4500)
    tw.dispensar_nps(page)
    for alvo in ["Liderança", "QA", "Líder de Equipe"]:
        try:
            page.get_by_text(alvo, exact=True).first.click(timeout=3000)
            page.wait_for_timeout(2500)
            print(f"\n### DRILL '{alvo}': url={page.url}\n", painel(page)[:500])
            tw.snap(page, PASTA, f"drill2-{alvo[:10].replace(' ','_')}")
            if page.url.endswith("succession_dashboards"):
                pass
            else:
                page.go_back(); page.wait_for_timeout(2000)
            page.keyboard.press("Escape"); page.wait_for_timeout(600)
        except Exception as e:
            print(f"   '{alvo}' não clicável: {type(e).__name__}")

    ctx.close()
    browser.close()
