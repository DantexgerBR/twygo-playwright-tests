"""Exploração 6: abrir edição de painel -> aba Identificação -> mapear campo Descrição (card 19423)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

SLUG = "paineis_descricao_19423"
EVID = tw.ROOT / "evidencias" / SLUG
c = tw.cfg("GOATWY")


def ir_paineis(page):
    page.goto(f"{c['base_url']}/o/{c['org_id']}/use_modes", wait_until="domcontentloaded")
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    page.get_by_text("Painéis", exact=True).first.click()
    page.wait_for_timeout(3000); tw.dispensar_nps(page)


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    EVID.mkdir(parents=True, exist_ok=True)
    ir_paineis(page)

    # clicar no lápis (edit) da primeira linha
    page.locator("td", has_text="edit").first.locator("text=edit").first.click()
    page.wait_for_timeout(4000); tw.dispensar_nps(page)
    print("URL edição:", page.url)
    tw.snap(page, EVID, "04_editar_painel_abriu", full=True)

    # mapear abas e campos
    info = page.evaluate(
        r"""()=>{
        const tabs=Array.from(document.querySelectorAll('[role=tab],button,a')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>t&&t.length<30);
        const fields=[];
        document.querySelectorAll('textarea,input[type=text],[contenteditable=true],.ql-editor,[role=textbox]').forEach(e=>{
            fields.push({tag:e.tagName,cls:(e.className||'').slice(0,60),ph:e.getAttribute('placeholder')||'',ce:e.getAttribute('contenteditable')||''});
        });
        const labels=Array.from(document.querySelectorAll('label')).map(l=>(l.innerText||'').trim()).filter(Boolean);
        return {tabs:[...new Set(tabs)], fields, labels};
    }"""
    )
    print("\nABAS:", info["tabs"])
    print("\nLABELS:", info["labels"])
    print("\nCAMPOS:")
    for f in info["fields"]:
        print(f"   <{f['tag']}> cls='{f['cls']}' ph='{f['ph']}' ce='{f['ce']}'")

    ctx.close(); browser.close()
print("\nFIM")
