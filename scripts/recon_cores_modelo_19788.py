# -*- coding: utf-8 -*-
"""Recon do Kit de Marca / aba Modelo (retrabalho 19788) — novoestudio org 37061, curso 807573.
Login + navega ate a aba Modelo + screenshot + dump dos campos de cor. Nao altera nada."""
import os, sys, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

# creds do novoestudio (do .env do repo agents-qa)
AGENTS_ENV = Path(r"D:\Estudo\Programação\cursor\twygo-work\twygo-agents-qa\agent-playwright\.env")
env = {}
for l in AGENTS_ENV.read_text(encoding="utf-8").splitlines():
    l = l.strip()
    if l and not l.startswith("#") and "=" in l:
        k, _, v = l.partition("="); env[k.strip()] = v.strip().strip('"').strip("'")
EMAIL = env["TWYGO_STAGING_NOVO_ESTUDIO_EMAIL"]
PWD = env["TWYGO_STAGING_NOVO_ESTUDIO_PASSWORD"]
BASE = "https://novoestudio.stage.twygoead.com"
ORG = "37061"; COURSE = "807573"

PASTA = Path(__file__).resolve().parents[1] / "evidencias" / "cores_modelo_19788"
PASTA.mkdir(parents=True, exist_ok=True)

from playwright.sync_api import sync_playwright

def snap(page, nome):
    p = PASTA / f"{nome}.png"
    page.screenshot(path=str(p), full_page=True)
    print(f"  [snap] {p}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=400)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="pt-BR")
    page = ctx.new_page()
    print("[1] login")
    page.goto(f"{BASE}/users/login", wait_until="domcontentloaded")
    try:
        page.get_by_role("textbox", name="Login").fill(EMAIL)
        page.get_by_label("Senha").fill(PWD)
        page.get_by_role("button", name="Entrar").click()
    except Exception as e:
        print("  login fallback:", e)
        page.fill("#user_email", EMAIL); page.fill("#user_password", PWD); page.click("#user_submit")
    page.wait_for_timeout(4000)
    print("  url pos-login:", page.url)

    print("[2] abre edicao do curso 807573")
    page.goto(f"{BASE}/o/{ORG}/events/{COURSE}/edit", wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    # fecha modais oportunistas
    for txt in ("Continuar mesmo assim", "Agora não", "Fechar", "Entendi"):
        try:
            b = page.get_by_role("button", name=txt)
            if b.count() and b.first.is_visible(): b.first.click(timeout=1500)
        except Exception: pass
    snap(page, "01-edit-inicial")
    print("  url:", page.url, "| titulo:", page.title())

    print("[3] procura aba 'Modelo'")
    clicou = False
    for sel in ["text=Modelo", "[role=tab]:has-text('Modelo')", "a:has-text('Modelo')", "button:has-text('Modelo')"]:
        try:
            loc = page.locator(sel)
            if loc.count():
                loc.first.click(timeout=2500); clicou = True
                print(f"  cliquei via {sel}"); break
        except Exception as e:
            print(f"  {sel} falhou: {e}")
    page.wait_for_timeout(3500)
    snap(page, "02-aba-modelo")
    print("  url apos Modelo:", page.url)

    print("[4] dump de elementos de cor / kit de marca")
    # inputs type=color
    try:
        cor_inputs = page.locator("input[type=color]")
        print("  input[type=color]:", cor_inputs.count())
    except Exception: pass
    # textos/labels com cor/primaria/kit/marca
    for kw in ("Primária", "Secundária", "Terciária", "Kit de marca", "Kit de Marca", "Cor", "Paleta"):
        try:
            n = page.get_by_text(kw, exact=False).count()
            if n: print(f"  texto '{kw}': {n} ocorrencia(s)")
        except Exception: pass
    # inputs com value parecendo hex
    try:
        vals = page.eval_on_selector_all("input", "els => els.map(e=>({id:e.id,name:e.name,type:e.type,val:e.value})).filter(o=> /^#?[0-9a-fA-F]{6}$/.test(o.val||''))")
        print("  inputs com valor hex:", vals)
    except Exception as e:
        print("  hex dump erro:", e)
    print("\n[fim] revise os screenshots em", PASTA)
    page.wait_for_timeout(1500)
    ctx.close(); browser.close()
