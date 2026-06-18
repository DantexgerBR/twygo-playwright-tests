"""RECON menu ☰ 18468 — achar/clicar o hamburguer do chat de importacao e mapear
o que abre (esperado: lista de conversas + 'Nova conversa'). Objetivo: comecar uma
conversa NOVA pra furar o cache de resposta da sessao.
"""
import re
import _twygo as tw

c = tw.cfg("MIGR")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "18468_recon"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{BASE}/o/{ORG}/question_lists", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    page.get_by_role("button", name=re.compile(r"Importa.{0,4}o Inteligente", re.I)).first.click(force=True)
    page.wait_for_timeout(4000)
    tw.snap(page, PASTA, "60-chat")

    # localizar o hamburguer: icone material 'menu' no topo-esquerda do overlay
    info = page.evaluate(r"""()=>{
        const cand=Array.from(document.querySelectorAll('button,span,i,[role=button]'))
          .filter(e=>e.offsetParent!==null)
          .map(e=>({txt:(e.innerText||'').trim(), aria:e.getAttribute('aria-label')||'',
                    cls:String(e.className).slice(0,40),
                    r:e.getBoundingClientRect()}))
          .filter(o=>o.r.top<160 && o.r.left<760 && o.r.left>590 && o.r.width<60 && o.r.height<60);
        return cand.slice(0,15);
    }""")
    print("[candidatos topo-esq do overlay]")
    for o in info:
        print("   ", {k: o[k] for k in ("txt", "aria", "cls")}, f"x={int(o['r']['left'])},y={int(o['r']['top'])}")

    # tentar clicar o que tem texto/aria 'menu'
    clicou = False
    el = page.locator("button, [role=button], span").filter(has_text=re.compile(r"^menu$", re.I)).first
    if el.count():
        try:
            el.click(timeout=3000); clicou = True; print("[menu] cliquei via has_text menu")
        except Exception as e:
            print(f"[menu] has_text falhou: {e}")
    if not clicou:
        # clicar por posicao aproximada do hamburguer (canto sup-esq do overlay)
        try:
            page.mouse.click(632, 90); clicou = True; print("[menu] cliquei por posicao 632,90")
        except Exception as e:
            print(f"[menu] posicao falhou: {e}")
    page.wait_for_timeout(2000)
    tw.snap(page, PASTA, "61-pos-menu")

    itens = page.evaluate(
        "()=>Array.from(document.querySelectorAll('button,a,[role=menuitem],li,h1,h2,h3')).filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(t=>t&&t.length<45).slice(0,50)")
    print(f"[itens visiveis pos-menu] {itens}")

    page.wait_for_timeout(1500)
    ctx.close(); browser.close()
