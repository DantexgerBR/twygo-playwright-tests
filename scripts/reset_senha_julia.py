"""Reset senha Julia - clique nativo Playwright no kebab + modal Alterar senha."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "filtros_dashboards_19363"
c = tw.cfg("")
ALVO = "julia@sophia.tech.com.br"
NOVA = "123456"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{c['base_url']}/o/{c['org_id']}/users?profile=admin", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000); tw.dispensar_nps(page)

    row = page.get_by_role("row").filter(has_text="julia@sophia")
    print("rows julia:", row.count())
    row.first.scroll_into_view_if_needed()
    row.first.get_by_text("more_vert").click(timeout=5000)  # clique nativo
    page.wait_for_timeout(1200)
    print("menu:", tw.menu_visivel(page))
    print("click_menuitem:", tw.click_menuitem(page, "Alterar senha"))
    page.wait_for_timeout(2800)
    tw.snap(page, PASTA, "11-modal-alterar-senha")

    # dump de qualquer modal/input visivel
    diag = page.evaluate(r"""()=>{
        const dlgs=Array.from(document.querySelectorAll('.chakra-modal__content,[role=dialog],[role=alertdialog]')).filter(d=>d.offsetParent!==null);
        const inputs=Array.from(document.querySelectorAll('input')).filter(i=>i.offsetParent!==null).map(i=>({t:i.type,ph:i.placeholder||'',id:i.id||''}));
        return {nDlg:dlgs.length, dlgTxt:dlgs.map(d=>(d.innerText||'').replace(/\s+/g,' ').slice(0,200)), inputs};
    }""")
    print("DIAG:", diag)

    # preencher inputs de senha visiveis (qualquer type)
    pwd = page.locator("input[type=password]")
    if pwd.count() == 0:
        pwd = page.locator("input").filter(has=page.locator("xpath=."))  # fallback noop
    n = page.locator("input[type=password]").count()
    print("password inputs:", n)
    for i in range(n):
        try: page.locator("input[type=password]").nth(i).fill(NOVA)
        except Exception as e: print("fill", i, e)
    page.wait_for_timeout(400)
    tw.snap(page, PASTA, "11b-modal-preenchido")
    for nome in ["Salvar", "Alterar", "Confirmar", "Atualizar", "OK"]:
        b = page.get_by_role("button", name=re.compile(f"^{nome}", re.I))
        if b.count() and b.first.is_visible() and b.first.is_enabled():
            print("salvando via", nome); b.first.click(); break
    page.wait_for_timeout(2500)
    toast = page.evaluate(r"""()=>[...new Set(Array.from(document.querySelectorAll('[role=alert],.chakra-toast,[class*=toast]')).map(e=>(e.innerText||'').replace(/\s+/g,' ').trim()).filter(Boolean))].slice(0,6)""")
    print("TOAST:", toast)
    tw.snap(page, PASTA, "11c-pos-salvar")
    ctx.close(); browser.close()
print("OK")
