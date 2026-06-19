"""20224 prov passo 4 (v3): iniciar campanha via clique por coordenadas do mouse."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "responder_avaliacao_20224"
c = tw.cfg("")

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/cycles/174/campaigns", wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)

    row = page.locator("tr,[role=row]").filter(has_text=re.compile("Campanha QA 20224", re.I)).first
    row.get_by_text("more_vert", exact=True).last.click(timeout=4000)
    page.wait_for_timeout(1000)
    # achar o menuitem Iniciar VISIVEL e clicar pelo centro (mouse real)
    box = page.evaluate(r"""()=>{
        const its=Array.from(document.querySelectorAll('[role=menuitem]')).filter(e=>e.offsetParent!==null && /Iniciar/i.test(e.innerText||''));
        if(!its.length) return null; const r=its[its.length-1].getBoundingClientRect();
        return {x:r.x+r.width/2, y:r.y+r.height/2};
    }""")
    print("box Iniciar:", box)
    if box:
        page.mouse.click(box["x"], box["y"])
        page.wait_for_timeout(2000)
    tw.snap(page, PASTA, "20-modal-iniciar")
    # confirmar modal
    for nome in ["Iniciar", "Confirmar", "Sim", "Programar"]:
        b = page.get_by_role("button", name=re.compile(f"^{nome}", re.I))
        if b.count() and b.first.is_visible() and b.first.is_enabled():
            print("confirma:", nome); b.first.click(); break
    page.wait_for_timeout(3000)
    toast = page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('[role=alert],.chakra-toast,[class*=toast]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean))].slice(0,6)""")
    print("TOAST:", toast)
    rows = page.evaluate(r"""()=>Array.from(document.querySelectorAll('tr,[role=row]')).map(r=>(r.innerText||'').replace(/\s+/g,' ').trim()).filter(t=>/20224/i.test(t))""")
    print("STATUS:", rows)
    tw.snap(page, PASTA, "20b-pos-iniciar", full=True)
    ctx.close(); browser.close()
print("OK")
