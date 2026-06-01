"""Inspeção 3 (destrave):
1) Estabelecer profile=admin no /events ANTES e reabrir a listagem sem query.
2) Derivar URL do subdomínio do ambiente adicional e abrir em CONTEXTO LIMPO
   (sem cookies de admin) pra testar branding/isolamento ponta a ponta."""
import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

BASE_URL = os.environ["BASE_URL"].rstrip("/")
ORG_ID = os.environ["ORG_ID"]
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]

PASTA = ROOT / "evidencias" / "ambiente_adicional"
PASTA.mkdir(parents=True, exist_ok=True)


def snap(page, nome):
    p = PASTA / f"{nome}.png"
    try:
        page.screenshot(path=str(p), full_page=True)
        print(f"  [snap] {p}")
    except Exception as e:
        print(f"  [snap-falhou] {nome}: {e}")
    return p


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=400)

    # ---- Contexto ADMIN: profile-first depois listagem ----
    ctx_admin = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
    page = ctx_admin.new_page()
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
    page.fill("#user_email", ADMIN_EMAIL)
    page.fill("#user_password", ADMIN_PASSWORD)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass

    # 1) profile=admin PRIMEIRO no /events (estabelece perfil na sessão)
    page.goto(f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
              wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    print("[ok] perfil admin estabelecido via /events")

    # depois listagem SEM query
    page.goto(f"{BASE_URL}/o/{ORG_ID}/additional_environments", wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    sem_perm = page.locator("text=/não tem permissão/i").count()
    tem_amb = page.locator("text=/ambiente_adicional/i").count()
    print(f"[listagem pós-profile] semPermissao={sem_perm} | ambiente_adicional={tem_amb}")
    snap(page, "v3-listagem-pos-profile")
    ctx_admin.close()

    # ---- Contexto LIMPO: testar subdomínios do ambiente adicional ----
    # padrão stage: *.stage.twygoead.com ; nome = ambiente_adicional
    candidatos = [
        "https://ambiente_adicional.stage.twygoead.com/",
        "https://ambiente-adicional.stage.twygoead.com/",
        "https://ambienteadicional.stage.twygoead.com/",
    ]
    for i, url in enumerate(candidatos, 1):
        ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
        pg = ctx.new_page()
        slug = url.split("//")[1].split(".")[0]
        print(f"\n[subdominio] tentando {url}")
        try:
            resp = pg.goto(url, wait_until="domcontentloaded", timeout=20000)
            status = resp.status if resp else "?"
            print(f"  status={status} | url_final={pg.url}")
            pg.wait_for_timeout(2000)
            snap(pg, f"v3-subdominio-{i}-{slug}")
        except Exception as e:
            print(f"  NAO resolveu/erro: {e}")
        ctx.close()

    print("\n[fim] inspeção 3 concluída")
    browser.close()
