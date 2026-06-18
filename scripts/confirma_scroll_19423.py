"""Recorte correto do campo Descrição (scroller real = nivel1) - vazio vs muito texto (card 19423)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

SLUG = "paineis_descricao_19423"
EVID = tw.ROOT / "evidencias" / SLUG
c = tw.cfg("GOATWY")


def ir_aba_paineis(page):
    page.goto(f"{c['base_url']}/o/{c['org_id']}/use_modes", wait_until="domcontentloaded")
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    page.get_by_text("Painéis", exact=True).first.click()
    page.wait_for_timeout(3000); tw.dispensar_nps(page)


def scroller_handle(page):
    return page.evaluate_handle(
        r"""()=>{
        const ed=Array.from(document.querySelectorAll(".slate-editor[contenteditable='true'], .slate-editor [contenteditable='true']")).pop();
        let cur=ed;
        for(let i=0;i<6 && cur;i++){const cs=getComputedStyle(cur);if(/(auto|scroll)/.test(cs.overflowY)){return cur;}cur=cur.parentElement;}
        return ed;
    }"""
    )


def shot(page, nome):
    h = scroller_handle(page)
    box = h.bounding_box()
    if box:
        pad = 6
        page.screenshot(path=str(EVID / f"{nome}.png"), clip={
            "x": max(0, box["x"] - pad), "y": max(0, box["y"] - pad),
            "width": box["width"] + pad * 2 + 28, "height": box["height"] + pad * 2,
        })
        print(f"   [shot] {nome}.png  (box {round(box['width'])}x{round(box['height'])})")


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    EVID.mkdir(parents=True, exist_ok=True)

    ir_aba_paineis(page)
    page.get_by_role("link", name="Adicionar").first.click()
    page.wait_for_timeout(4000); tw.dispensar_nps(page)

    # VAZIO
    shot(page, "30_vazio_campo")

    # MUITO TEXTO
    ed = page.locator(".slate-editor[contenteditable='true']").last
    ed.click()
    for _ in range(30):
        page.keyboard.type("Texto longo para estourar a altura do campo. ")
        page.keyboard.press("Enter")
    page.wait_for_timeout(500)
    page.evaluate("()=>document.activeElement && document.activeElement.blur()")
    shot(page, "32_muito_texto_campo")

    ctx.close(); browser.close()
print("FIM")
