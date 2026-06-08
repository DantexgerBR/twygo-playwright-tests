# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
AG=Path(r"D:\Estudo\Programação\cursor\twygo-work\twygo-agents-qa\agent-playwright\.env")
env={}
for l in AG.read_text(encoding="utf-8").splitlines():
    l=l.strip()
    if l and not l.startswith("#") and "=" in l:
        k,_,v=l.partition("="); env[k.strip()]=v.strip().strip('"').strip("'")
EMAIL=env["TWYGO_STAGING_NOVO_ESTUDIO_EMAIL"]; PWD=env["TWYGO_STAGING_NOVO_ESTUDIO_PASSWORD"]
BASE="https://novoestudio.stage.twygoead.com"
PASTA=Path(__file__).resolve().parents[1]/"evidencias"/"cores_modelo_19788"
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
    page.goto(f"{BASE}/o/37061/brands/807573/edit", wait_until="domcontentloaded"); page.wait_for_timeout(3500)
    page.get_by_role("tab", name="Cores").click() if page.get_by_role("tab",name="Cores").count() else page.get_by_text("Cores",exact=True).first.click()
    page.wait_for_timeout(3000)
    page.screenshot(path=str(PASTA/"22-aba-cores.png"), full_page=True); print("[snap] 22-aba-cores")
    allin=page.eval_on_selector_all("input","els=>els.filter(e=>e.offsetParent!==null).map(e=>({id:e.id,name:e.name,type:e.type,val:e.value,ph:e.placeholder}))")
    for i in allin: print("in:",i)
    print("input[type=color]:", page.locator("input[type=color]").count())
    # elementos clicaveis com cor de fundo hex (swatches)
    sw=page.eval_on_selector_all("*","els=>els.filter(e=>e.offsetParent&&/rgb/.test(getComputedStyle(e).backgroundColor)&&e.getBoundingClientRect().width<60&&e.getBoundingClientRect().width>15&&e.getBoundingClientRect().height<60&&e.getBoundingClientRect().height>15).slice(0,12).map(e=>({tag:e.tagName,cls:(e.className||'').toString().slice(0,40),bg:getComputedStyle(e).backgroundColor}))")
    print("possiveis swatches:", sw)
    page.wait_for_timeout(1000); ctx.close(); b.close()
