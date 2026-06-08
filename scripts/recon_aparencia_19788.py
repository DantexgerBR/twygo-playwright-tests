# -*- coding: utf-8 -*-
"""Recon do Kit de Marca em Configuracoes > Aparencia (retrabalho 19788) — novoestudio org 37061.
Login + sidebar Configuracoes > Aparencia + screenshot + dump dos campos de cor. Nao altera nada."""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
AGENTS_ENV = Path(r"D:\Estudo\Programação\cursor\twygo-work\twygo-agents-qa\agent-playwright\.env")
env = {}
for l in AGENTS_ENV.read_text(encoding="utf-8").splitlines():
    l = l.strip()
    if l and not l.startswith("#") and "=" in l:
        k, _, v = l.partition("="); env[k.strip()] = v.strip().strip('"').strip("'")
EMAIL = env["TWYGO_STAGING_NOVO_ESTUDIO_EMAIL"]; PWD = env["TWYGO_STAGING_NOVO_ESTUDIO_PASSWORD"]
BASE = "https://novoestudio.stage.twygoead.com"; ORG = "37061"
PASTA = Path(__file__).resolve().parents[1] / "evidencias" / "cores_modelo_19788"
PASTA.mkdir(parents=True, exist_ok=True)
from playwright.sync_api import sync_playwright

def snap(page, nome):
    page.screenshot(path=str(PASTA / f"{nome}.png"), full_page=True); print(f"  [snap] {nome}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=400)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, locale="pt-BR")
    page = ctx.new_page()
    page.goto(f"{BASE}/users/login", wait_until="domcontentloaded")
    try:
        page.get_by_role("textbox", name="Login").fill(EMAIL)
        page.locator("#user_password, input[type=password]").first.fill(PWD)
        page.get_by_role("button", name="Entrar").click()
    except Exception as e: print("login:", e)
    page.wait_for_timeout(4000)
    print("login url:", page.url)

    # 1) tentar URL direta de aparencia; se nao, sidebar
    print("[1] tentando rotas diretas de aparencia")
    achou = False
    for rota in ("/o/37061/appearance", "/o/37061/settings/appearance", "/o/37061/organizations/edit", "/o/37061/brand", "/o/37061/brands"):
        try:
            page.goto(f"{BASE}{rota}", wait_until="domcontentloaded"); page.wait_for_timeout(2500)
            body = page.locator("body").inner_text(timeout=3000)
            if any(w in body for w in ("Primária", "Kit de marca", "Kit de Marca", "Paleta", "Aparência")):
                print(f"  rota {rota} parece ter o conteudo"); achou = True; break
        except Exception as e: print(f"  {rota}: {e}")
    # 2) fallback: sidebar Configuracoes > Aparencia
    if not achou:
        print("[2] fallback sidebar Configuracoes > Aparencia")
        page.goto(f"{BASE}/o/{ORG}/dashboard", wait_until="domcontentloaded"); page.wait_for_timeout(3000)
        try:
            cfg = page.locator("#menu").get_by_text("Configurações", exact=True).first
            cfg.dispatch_event("click"); page.wait_for_timeout(1200)
        except Exception as e: print("  expand cfg:", e)
        try:
            page.locator("#menu").get_by_text("Aparência", exact=True).first.click(timeout=4000)
        except Exception as e:
            print("  click aparencia:", e)
            try: page.get_by_text("Aparência", exact=True).first.click(timeout=4000)
            except Exception as e2: print("  click aparencia 2:", e2)
        page.wait_for_timeout(4000)
    print("  url aparencia:", page.url)
    snap(page, "10-aparencia")

    print("[3] dump de cores")
    print("  input[type=color]:", page.locator("input[type=color]").count())
    for kw in ("Primária", "Secundária", "Terciária", "Kit de marca", "Cor", "Paleta", "Salvar"):
        try:
            n = page.get_by_text(kw, exact=False).count()
            if n: print(f"  texto '{kw}': {n}")
        except Exception: pass
    try:
        vals = page.eval_on_selector_all("input", "els=>els.map(e=>({id:e.id,name:e.name,type:e.type,val:e.value})).filter(o=>/^#?[0-9a-fA-F]{6}$/.test(o.val||''))")
        print("  inputs hex:", vals)
    except Exception as e: print("  hex:", e)
    # botoes visiveis
    try:
        btns = page.eval_on_selector_all("button", "els=>els.filter(b=>b.offsetParent).map(b=>b.innerText.trim()).filter(Boolean).slice(0,25)")
        print("  botoes:", btns)
    except Exception as e: print("  botoes:", e)
    page.wait_for_timeout(1500)
    ctx.close(); browser.close()
