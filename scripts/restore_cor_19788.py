# -*- coding: utf-8 -*-
"""Cleanup: restaura Primaria do kit Roxo para #9349DE. Org 37061."""
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
BASE="https://novoestudio.stage.twygoead.com"; EDIT=f"{BASE}/o/37061/brands/807573/edit"
ORIG="#9349DE"; HEX="#brand-form-colors-row-0-hex-input"
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=False, slow_mo=400)
    ctx=b.new_context(viewport={"width":1440,"height":900}, locale="pt-BR"); page=ctx.new_page()
    page.goto(f"{BASE}/users/login", wait_until="domcontentloaded")
    try:
        page.get_by_role("textbox",name="Login").fill(EMAIL)
        page.locator("#user_password, input[type=password]").first.fill(PWD)
        page.get_by_role("button",name="Entrar").click()
    except Exception as e: print("login:",e)
    page.wait_for_timeout(3500)
    page.goto(EDIT, wait_until="domcontentloaded"); page.wait_for_timeout(3500)
    (page.get_by_role("tab",name="Cores").first if page.get_by_role("tab",name="Cores").count() else page.get_by_text("Cores",exact=True).first).click()
    page.wait_for_timeout(2500)
    print("antes do restore:", page.input_value(HEX))
    page.fill(HEX, ORIG); page.locator(HEX).blur(); page.wait_for_timeout(700)
    page.get_by_role("button", name="Salvar").first.click(); page.wait_for_timeout(3000)
    print("restaurado para:", ORIG)
    page.wait_for_timeout(800); ctx.close(); b.close()
