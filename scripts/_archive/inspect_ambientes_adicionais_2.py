"""Inspeção 2: confirmar permissão em /additional_environments, testar /new,
e varrer TODO o DOM (a+button) por 'ambiente'. Procurar entry point real."""
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

    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
    page.fill("#user_email", ADMIN_EMAIL)
    page.fill("#user_password", ADMIN_PASSWORD)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.goto(f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
              wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    print("[ok] logado como admin")

    def diag(rota):
        url = f"{BASE_URL}{rota}"
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=15000)
            status = resp.status if resp else "?"
        except Exception as e:
            status = f"erro {e}"
        page.wait_for_timeout(1500)
        sem_perm = page.locator("text=/não tem permissão/i").count()
        tem_form = page.locator("text=/Nome do ambiente/i").count()
        tem_amb = page.locator("text=/ambiente_adicional/i").count()
        print(f"[rota] {rota} status={status} | semPermissao={sem_perm} | formAmbiente={tem_form} | ambiente_adicional={tem_amb}")
        return status, sem_perm, tem_form

    for rota in [
        f"/o/{ORG_ID}/additional_environments",
        f"/o/{ORG_ID}/additional_environments/new",
        f"/o/{ORG_ID}/additional_environments?profile=admin",
    ]:
        st, _, tem_form = diag(rota)
        slug = rota.replace(f"/o/{ORG_ID}/", "").replace("/", "-").replace("?", "-").replace("=", "-")
        snap(page, f"v2-{slug}")

    # Aba Customizações da Organização
    page.goto(f"{BASE_URL}/o/{ORG_ID}/edit", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    cust = page.locator("text=/Customiza/i").first
    if cust.count():
        cust.click()
        page.wait_for_timeout(2000)
        snap(page, "v2-edit-customizacoes")
        print("[custom] aba Customizações aberta, procurando 'ambiente'...")
        print("  formAmbiente:", page.locator("text=/Nome do ambiente/i").count())

    # Varredura DOM global por 'ambiente' em links e botões
    page.goto(f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
              wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    achados = page.eval_on_selector_all(
        "a, button, [role=menuitem]",
        "els => els.map(e => ({tag:e.tagName, txt:(e.innerText||'').trim(), href:e.getAttribute('href')}))"
        ".filter(o => o.txt && /ambient/i.test(o.txt))",
    )
    print("[DOM] elementos clicáveis com 'ambiente':", achados or "(nenhum)")

    print("\n[fim] inspeção 2 concluída")
    context.close()
    browser.close()
