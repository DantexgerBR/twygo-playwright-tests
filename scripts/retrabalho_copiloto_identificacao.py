# -*- coding: utf-8 -*-
"""Retrabalho R08 — FAB do Copiloto na aba Identificação (org 37061, curso 807533).

Bug original: "o botão flutuante do copiloto não renderiza na aba Identificação,
só existe na aba Atividades (Estúdio)". RN 4: o copiloto deve ser acessível na
Identificação em modo sugestão (responde no chat sem alterar os campos do form).

Validação:
  1. Abrir aba Identificação do curso e procurar o FAB do copiloto
     (test-id 'copilot-fab' OU varredura do canto INFERIOR-direito por um botão
     redondo roxo — é lá que o FAB renderiza, não no topo).
  2. Clicar no FAB e confirmar que o drawer 'Copiloto do Estúdio' abre.
  3. Comparar com a aba Atividades (onde o copiloto já funcionava).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "novo_estudio_retrabalhos"
CURSO = "807533"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'

# varredura do canto SUPERIOR-direito por um botão redondo/roxo (é lá que o FAB do
# Copiloto renderiza — sparkle roxo ~x=W-70,y=125; o chat roxo do RODAPÉ é o widget
# de suporte, NÃO o copiloto).
JS_SCAN_FAB = """()=>{
    const W=window.innerWidth;
    for(let y=95;y<=210;y+=6){
      for(let x=W-15;x>=W-130;x-=6){
        const el=document.elementFromPoint(x,y);
        if(!el) continue;
        let n=el;
        for(let i=0;i<6 && n;i++,n=n.parentElement){
          const s=getComputedStyle(n); const r=n.getBoundingClientRect();
          const round = parseFloat(s.borderRadius)>=20 || (s.borderRadius||'').includes('50');
          const m=(s.backgroundColor||'').match(/\\d+/g);
          const purple = m && m.length>=3 && (+m[0])>80 && (+m[2])>150 && (+m[1])<(+m[0]);
          if(r.width>=36 && r.width<=80 && r.height>=36 && r.height<=80 && (round||purple)){
            return {x,y, tag:n.tagName, testid:n.getAttribute('data-test-id'),
                    aria:n.getAttribute('aria-label'), bg:s.backgroundColor, br:s.borderRadius,
                    w:Math.round(r.width), h:Math.round(r.height),
                    cx:Math.round(r.left+r.width/2), cy:Math.round(r.top+r.height/2),
                    html:n.outerHTML.slice(0,160)};
          }
        }
      }
    }
    return null;
}"""

# o drawer 'Copiloto do Estúdio' está aberto?
JS_DRAWER_ABERTO = """()=>{
    const d=document.querySelector('[data-test-id=copilot-drawer]');
    const drawerVis = d ? d.offsetParent!==null : false;
    const txt=/copiloto do est[úu]dio|escreva uma mensagem|como posso ajudar|receba sugest/i
        .test(document.body.innerText||'');
    return {drawerVis, txt, abriu: drawerVis || txt};
}"""


def detecta_fab(page):
    """Retorna info do FAB: via test-id se existir, senão via varredura visual."""
    loc = page.locator(tid("copilot-fab")).first
    if loc.count() and loc.is_visible():
        box = loc.bounding_box() or {}
        return {"via": "test-id", "cx": int(box.get("x", 0) + box.get("width", 0) / 2),
                "cy": int(box.get("y", 0) + box.get("height", 0) / 2),
                "testid": "copilot-fab"}
    scan = page.evaluate(JS_SCAN_FAB)
    if scan:
        scan["via"] = "scan-canto-inferior-direito"
    return scan


def testa_aba(page, aba, label):
    print(f"\n### Aba {label} (tab={aba})")
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab={aba}",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(7000)
    tw.dispensar_nps(page)
    page.wait_for_timeout(1500)

    fab = detecta_fab(page)
    print(f"   FAB detectado: {fab}")
    tw.snap(page, PASTA, f"r08v-{aba}-fab")

    abriu = False
    if fab and fab.get("cx"):
        page.mouse.click(fab["cx"], fab["cy"])
        page.wait_for_timeout(3500)
        estado = page.evaluate(JS_DRAWER_ABERTO)
        abriu = bool(estado["abriu"])
        print(f"   após clique: {estado} | drawer abriu? {abriu}")
        tw.snap(page, PASTA, f"r08v-{aba}-drawer")
        # fechar o drawer pra não vazar pro próximo teste
        try:
            fechar = page.locator(tid("copilot-drawer-close")).first
            if fechar.count() and fechar.is_visible():
                fechar.click(timeout=3000)
            else:
                page.keyboard.press("Escape")
            page.wait_for_timeout(1000)
        except Exception:
            pass

    presente = bool(fab and fab.get("cx"))
    return {"fab_presente": presente, "drawer_abriu": abriu, "fab": fab}


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    print(f"[ok] logado em {page.url}")

    r_ident = testa_aba(page, "identification", "Identificação (alvo do retrabalho)")
    r_ativ = testa_aba(page, "studio", "Atividades / Estúdio (comparativo)")

    ok = r_ident["fab_presente"] and r_ident["drawer_abriu"]
    print("\n" + "=" * 60)
    print(f"IDENTIFICAÇÃO  → FAB presente={r_ident['fab_presente']} | drawer abre={r_ident['drawer_abriu']}")
    print(f"ATIVIDADES     → FAB presente={r_ativ['fab_presente']} | drawer abre={r_ativ['drawer_abriu']}")
    print("=" * 60)
    print(f"\n=> RETRABALHO R08: {'PASSOU ✅' if ok else 'FALHOU ❌'}")
    print("   (esperado: copiloto acessível na Identificação — RN 4, modo sugestão)")

    ctx.close(); browser.close()
