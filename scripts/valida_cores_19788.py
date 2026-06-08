# -*- coding: utf-8 -*-
"""Valida retrabalho 19788: muda Primaria do kit Roxo, salva, recarrega e rele (persistencia UI). Org 37061."""
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
PASTA=Path(__file__).resolve().parents[1]/"evidencias"/"cores_modelo_19788"
TESTE="#AB12CD"; HEX="#brand-form-colors-row-0-hex-input"
from playwright.sync_api import sync_playwright

def login(page):
    page.goto(f"{BASE}/users/login", wait_until="domcontentloaded")
    try:
        page.get_by_role("textbox",name="Login").fill(EMAIL)
        page.locator("#user_password, input[type=password]").first.fill(PWD)
        page.get_by_role("button",name="Entrar").click()
    except Exception as e: print("login:",e)
    page.wait_for_timeout(3500)

def abre_cores(page):
    page.goto(EDIT, wait_until="domcontentloaded"); page.wait_for_timeout(3500)
    (page.get_by_role("tab",name="Cores").first if page.get_by_role("tab",name="Cores").count() else page.get_by_text("Cores",exact=True).first).click()
    page.wait_for_timeout(2500)

with sync_playwright() as p:
    b=p.chromium.launch(headless=False, slow_mo=450)
    ctx=b.new_context(viewport={"width":1440,"height":900}, locale="pt-BR"); page=ctx.new_page()
    login(page); abre_cores(page)
    antes=page.input_value(HEX); print("Primaria ANTES:", antes)
    print(f"[muda] {antes} -> {TESTE}")
    page.fill(HEX, TESTE)
    page.locator(HEX).blur()
    page.wait_for_timeout(800)
    # salvar
    page.get_by_role("button", name="Salvar").first.click()
    page.wait_for_timeout(3500)
    page.screenshot(path=str(PASTA/"30-apos-salvar.png"), full_page=True); print("[snap] 30-apos-salvar")
    # toast?
    try:
        t=page.locator(".chakra-toast, [role=alert]").first
        if t.count(): print("toast:", t.inner_text(timeout=2000)[:80])
    except Exception: pass
    # recarrega e rele (persistencia UI)
    print("[reload] reabrindo editor")
    abre_cores(page)
    depois=page.input_value(HEX); print("Primaria DEPOIS do reload:", depois)
    page.screenshot(path=str(PASTA/"31-pos-reload.png"), full_page=True); print("[snap] 31-pos-reload")
    print("RESULTADO UI:", "PERSISTIU" if depois.lower().lstrip("#")==TESTE.lower().lstrip("#") else f"NAO PERSISTIU (voltou {depois})")
    page.wait_for_timeout(1000); ctx.close(); b.close()
