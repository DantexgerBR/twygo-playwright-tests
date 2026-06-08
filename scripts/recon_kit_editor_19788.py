# -*- coding: utf-8 -*-
"""Abre o editor do kit 'Roxo' (Aparencia) e dumpa os campos de cor. Nao salva nada. Org 37061."""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
AGENTS_ENV = Path(r"D:\Estudo\Programação\cursor\twygo-work\twygo-agents-qa\agent-playwright\.env")
env = {}
for l in AGENTS_ENV.read_text(encoding="utf-8").splitlines():
    l=l.strip()
    if l and not l.startswith("#") and "=" in l:
        k,_,v=l.partition("="); env[k.strip()]=v.strip().strip('"').strip("'")
EMAIL=env["TWYGO_STAGING_NOVO_ESTUDIO_EMAIL"]; PWD=env["TWYGO_STAGING_NOVO_ESTUDIO_PASSWORD"]
BASE="https://novoestudio.stage.twygoead.com"; ORG="37061"
PASTA=Path(__file__).resolve().parents[1]/"evidencias"/"cores_modelo_19788"; PASTA.mkdir(parents=True,exist_ok=True)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=False, slow_mo=450)
    ctx=b.new_context(viewport={"width":1440,"height":900}, locale="pt-BR"); page=ctx.new_page()
    page.goto(f"{BASE}/users/login", wait_until="domcontentloaded")
    try:
        page.get_by_role("textbox",name="Login").fill(EMAIL)
        page.locator("#user_password, input[type=password]").first.fill(PWD)
        page.get_by_role("button",name="Entrar").click()
    except Exception as e: print("login:",e)
    page.wait_for_timeout(3500)
    page.goto(f"{BASE}/o/{ORG}/appearance", wait_until="domcontentloaded"); page.wait_for_timeout(3500)
    print("[1] abre menu da linha 'Roxo'")
    try:
        row=page.locator("tr", has_text="Roxo").first
        row.locator("button:has-text('more_vert'), [aria-label*=opcoes], [aria-label*=options], button").last.click(timeout=4000)
    except Exception as e:
        print("  kebab fallback:", e)
        page.get_by_text("more_vert").last.click(timeout=4000)
    page.wait_for_timeout(1200)
    page.screenshot(path=str(PASTA/"20-menu-linha.png"), full_page=True); print("  [snap] 20-menu-linha")
    print("[2] clica Editar")
    for t in ("Editar","edit","Edit"):
        try:
            page.get_by_role("menuitem", name=t).first.click(timeout=2000); print(f"  menuitem {t}"); break
        except Exception:
            try: page.get_by_text(t, exact=True).first.click(timeout=1500); print(f"  text {t}"); break
            except Exception: pass
    page.wait_for_timeout(4000)
    page.screenshot(path=str(PASTA/"21-editor-kit.png"), full_page=True); print("  [snap] 21-editor-kit | url:", page.url)
    print("[3] dump inputs do editor")
    try:
        allin=page.eval_on_selector_all("input", "els=>els.filter(e=>e.offsetParent!==null).map(e=>({id:e.id,name:e.name,type:e.type,val:e.value,ph:e.placeholder}))")
        for i in allin: print("   in:", i)
    except Exception as e: print("  inputs:", e)
    print("  input[type=color]:", page.locator("input[type=color]").count())
    for kw in ("Primária","Secundária","Terciária","Salvar","Hex","#"):
        try:
            n=page.get_by_text(kw, exact=False).count()
            if n: print(f"  texto '{kw}': {n}")
        except Exception: pass
    page.wait_for_timeout(1500)
    ctx.close(); b.close()
