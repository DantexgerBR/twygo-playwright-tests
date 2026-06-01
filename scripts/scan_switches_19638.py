"""Scan: switch 'Habilitar reinscricao' de cada conteudo da org 36912.
Acha o(s) conteudo(s) com reinscricao ON pra validar o retrabalho 19638.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
import _twygo as tw
_c = tw.cfg("EDUAPI")
BASE_URL, ORG_ID, EMAIL, SENHA = _c["base_url"], _c["org_id"], _c["email"], _c["senha"]
PASTA = ROOT / "evidencias" / "19638_botao_reinscricao"
PASTA.mkdir(parents=True, exist_ok=True)


def dispensar_nps(page):
    for sel in ["button:has-text('Pergunte depois')", "[aria-label='Close']", ".chakra-modal__close-btn"]:
        try:
            b = page.locator(sel).first
            if b.count() and b.is_visible():
                b.click(timeout=2000); page.wait_for_timeout(400)
        except Exception:
            pass


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=120)
    context = browser.new_context(viewport={"width": 1500, "height": 950}, locale="pt-BR")
    page = context.new_page()

    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", EMAIL); page.fill("#user_password", SENHA); page.click("#user_submit")
    try: page.wait_for_load_state("networkidle", timeout=20000)
    except Exception: pass
    page.goto(f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
              wait_until="domcontentloaded", timeout=30000)
    try: page.wait_for_load_state("networkidle", timeout=15000)
    except Exception: pass
    page.wait_for_timeout(3000)
    dispensar_nps(page)

    itens = page.evaluate(
        """() => Array.from(document.querySelectorAll('tr[data-item-id]')).map(r => ({
            id: r.getAttribute('data-item-id'),
            nome: r.getAttribute('data-item-name'),
            tipo: (r.querySelector('td p.chakra-text')||{}).innerText || '',
        }))""")
    print(f"[itens] {len(itens)} conteudos")

    resultados = []
    for it in itens:
        cid = it["id"]
        try:
            page.goto(f"{BASE_URL}/o/{ORG_ID}/contents/{cid}/edit?tab=access",
                      wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(1800)
            sw = page.evaluate(
                """() => {
                    const inp = document.querySelector('#has_recertification, input[name="has_recertification"]');
                    if (!inp) return {existe:false};
                    return {existe:true, checked: inp.checked};
                }""")
        except Exception as e:
            sw = {"erro": repr(e)[:80]}
        on = sw.get("existe") and sw.get("checked")
        flag = "  <<< ON" if on else ""
        print(f"   {cid}  reinscricao={sw}  {it['nome'][:40]}{flag}")
        resultados.append({**it, "switch": sw, "on": bool(on)})

    (PASTA / "_scan_switches.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")

    ons = [r for r in resultados if r["on"]]
    print(f"\n===== {len(ons)} conteudo(s) com reinscricao ON =====")
    for r in ons:
        print(f"   {r['id']}  {r['nome']}")

    context.close(); browser.close()
