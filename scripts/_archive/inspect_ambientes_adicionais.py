"""Inspeção: localizar a feature 'Ambientes adicionais' na org 36675,
achar a LISTAGEM (onde fica a URL/subdomínio de cada ambiente) e confirmar
se 'ambiente_adicional' realmente existe. Não cadastra nada — só inspeciona."""
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
    page.screenshot(path=str(p), full_page=True)
    print(f"  [snap] {p}")
    return p


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=400)
    context = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
    page = context.new_page()

    # Login admin
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
    page.fill("#user_email", ADMIN_EMAIL)
    page.fill("#user_password", ADMIN_PASSWORD)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass

    # Switch pra admin
    page.goto(f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
              wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    print("[ok] logado como admin")

    # 1) Procurar na sidebar/nav qualquer link com 'ambiente'
    links = page.eval_on_selector_all(
        "a",
        "els => els.map(e => ({txt:(e.innerText||'').trim(), href:e.getAttribute('href')}))"
        ".filter(o => o.txt && /ambient/i.test(o.txt))",
    )
    print("[sidebar] links com 'ambiente':")
    for l in links:
        print("   ", l)

    # 2) Tentar rotas candidatas (não presumir /appearance como verdade)
    candidatas = [
        f"/o/{ORG_ID}/appearance",
        f"/o/{ORG_ID}/environments",
        f"/o/{ORG_ID}/additional_environments",
        f"/o/{ORG_ID}/edit",
    ]
    for rota in candidatas:
        url = f"{BASE_URL}{rota}"
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=15000)
            status = resp.status if resp else "?"
        except Exception as e:
            status = f"erro {e}"
        page.wait_for_timeout(1500)
        tem_ambiente = page.locator("text=/ambiente_adicional/i").count()
        tem_adicionar = page.locator("text=/Adicionar ambiente/i").count()
        print(f"[rota] {rota} -> status={status} | ambiente_adicional={tem_ambiente} | btnAdicionar={tem_adicionar}")
        slug = rota.strip("/").split("/")[-1]
        snap(page, f"rota-{slug}")

    print("\n[fim] revise os screenshots em evidencias/ambiente_adicional/")
    context.close()
    browser.close()
