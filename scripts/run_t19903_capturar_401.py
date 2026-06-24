"""
QA 1.16 - Capturar endpoint exato que retorna 401 no form Adicionar
como Gestor de Turma (qalider, perfil ativo = Gestor de Turma).
Objetivo: saber se e o mesmo endpoint da 1.6 ou um novo bug.
"""
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
from dotenv import load_dotenv

load_dotenv(tw.ROOT / ".env")

c = {
    "base_url": os.environ["REGISTROSF2_BASE_URL"].rstrip("/"),
    "org_id": os.environ["REGISTROSF2_ORG_ID"],
    "email": os.environ["REGISTROSF2_ADMIN_EMAIL"],
    "senha": os.environ["REGISTROSF2_ADMIN_PASSWORD"],
}
c_lider = {
    "email": "qalider@teste.com",
    "senha": "123456",
}

SLUG = "registros-f2-qa116"
BASE = tw.ROOT / "evidencias" / SLUG
BASE.mkdir(parents=True, exist_ok=True)
BASE_URL = c["base_url"]
ORG_ID = c["org_id"]
REGISTROS_URL = f"{BASE_URL}/o/{ORG_ID}/records"

falhas_401 = []
todas_requests = []

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)

    # Interceptar respostas
    def on_response(response):
        url = response.url
        status = response.status
        # Capturar qualquer erro (4xx, 5xx) de API
        if status >= 400 and '/o/' in url:
            falhas_401.append({
                "url": url,
                "status": status,
                "method": response.request.method
            })
            print(f"  [RESPONSE {status}] {response.request.method} {url}")
        # Capturar requests relevantes (APIs de registros/professionals)
        if any(k in url for k in ['professionals', 'provider', 'record', 'learning', 'users']):
            todas_requests.append({
                "url": url,
                "status": status,
                "method": response.request.method
            })

    page.on("response", on_response)

    # Login como lider
    print("=== LOGIN COMO LIDER ===")
    page.context.clear_cookies()
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", c_lider["email"])
    page.fill("#user_password", c_lider["senha"])
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # Navegar para Registros
    print("\n=== NAVEGAR PARA REGISTROS ===")
    page.goto(REGISTROS_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_selector("tbody tr", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(3000)

    perfil_atual = page.evaluate("""
        () => {
            const btns = Array.from(document.querySelectorAll('button'));
            const b = btns.find(b => /gestor|administrador|colaborador/i.test(b.innerText||''));
            return b ? b.innerText.trim() : 'desconhecido';
        }
    """)
    print(f"Perfil na tela Registros: {perfil_atual}")
    tw.snap(page, BASE, "401_registros_antes_clicar")

    # Limpar lista de falhas antes de clicar em Adicionar
    falhas_401.clear()
    todas_requests.clear()

    # Clicar em Adicionar
    print("\n=== CLICAR EM ADICIONAR ===")
    btn_add = page.locator("button", has_text="Adicionar").first
    if btn_add.count():
        box = btn_add.bounding_box()
        if box:
            page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)

    # Aguardar carregamento do form (e requests)
    try:
        page.wait_for_selector("form, [class*='Form'], h1:has-text('Novo')", timeout=8000)
    except Exception:
        pass
    page.wait_for_timeout(4000)  # Aguardar requests assincronas
    tw.snap(page, BASE, "401_form_adicionar")

    print(f"\n=== FALHAS 4xx/5xx CAPTURADAS ===")
    for f in falhas_401:
        print(f"  {f['status']} {f['method']} {f['url']}")

    print(f"\n=== REQUESTS RELEVANTES (professionals/provider/record) ===")
    for r in todas_requests:
        print(f"  {r['status']} {r['method']} {r['url']}")

    # Verificar se toast de erro aparece
    toast_info = page.evaluate("""
        () => {
            const toasts = Array.from(document.querySelectorAll(
                '[class*="toast"], [class*="Toast"], [role="alert"], [class*="alert"]'
            )).filter(el => el.offsetParent !== null);
            return toasts.map(t => ({
                cls: (t.className || '').substring(0, 80),
                texto: (t.innerText || '').trim().substring(0, 100)
            }));
        }
    """)
    print(f"\nToasts visiveis: {json.dumps(toast_info, ensure_ascii=False)}")
    tw.snap(page, BASE, "401_toast_visivel")

    # Salvar resultado
    resultado = {
        "perfil_lider": perfil_atual,
        "falhas_4xx_5xx": falhas_401,
        "requests_relevantes": todas_requests,
        "toasts": toast_info
    }
    with open(BASE / "401_analise.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    ctx.close()
    browser.close()

print("\nResultado salvo em 401_analise.json")
print(f"Total de falhas 4xx/5xx: {len(falhas_401)}")
for f in falhas_401:
    print(f"  {f['status']} {f['method']} {f['url']}")
