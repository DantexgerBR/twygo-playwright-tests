"""
QA 1.16 - Verificar perfil exato do qalider e paginacao do lider vs admin.
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
    "base_url": c["base_url"],
    "email": "qalider@teste.com",
    "senha": "123456",
}

SLUG = "registros-f2-qa116"
BASE = tw.ROOT / "evidencias" / SLUG
BASE.mkdir(parents=True, exist_ok=True)
BASE_URL = c["base_url"]
ORG_ID = c["org_id"]
REGISTROS_URL = f"{BASE_URL}/o/{ORG_ID}/records"


def login_admin(page):
    page.context.clear_cookies()
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector("#user_email", timeout=10000)
    tw.login(page, c, admin=True)


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    login_admin(page)

    # 1. Perfil exato do qalider - abrir edita via kebab
    print("=== PERFIL DO LIDER VIA EDICAO ===")
    page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)

    try:
        search = page.locator("input[placeholder*='esquise'], input[type='search']").first
        if search.count():
            search.fill("qalider")
            page.wait_for_timeout(2000)
    except Exception:
        pass

    # Clicar no kebab (more_vert) do qalider
    try:
        linha_lider = page.locator("tr").filter(has_text="qalider@teste.com")
        if linha_lider.count():
            # Clicar no kebab (ultimo botao da linha)
            kebab = linha_lider.locator("button").last
            kebab_box = kebab.bounding_box()
            if kebab_box:
                page.mouse.click(kebab_box["x"] + kebab_box["width"]/2,
                                 kebab_box["y"] + kebab_box["height"]/2)
                page.wait_for_timeout(1000)
                tw.snap(page, BASE, "lider_kebab_menu")

                # Clicar em Editar
                editar = page.locator("[role='menuitem'], li").filter(has_text="Editar").first
                if not editar.count():
                    editar = page.locator("a, button").filter(has_text="Editar").first
                if editar.count():
                    editar.click()
                    page.wait_for_timeout(3000)
                    tw.snap(page, BASE, "lider_editar_perfil")
                    print(f"URL editar lider: {page.url}")

                    # Ver todos os perfis marcados
                    perfis_info = page.evaluate("""
                        () => {
                            const body = document.body.innerText || '';
                            const checks = Array.from(document.querySelectorAll(
                                'input[type="checkbox"], input[type="radio"]'
                            ));
                            const marcados = checks.filter(c => c.checked)
                                .map(c => c.value || c.id || c.name);
                            const nao_marcados = checks.filter(c => !c.checked)
                                .map(c => c.value || c.id || c.name);
                            return {
                                url: window.location.href,
                                marcados,
                                nao_marcados: nao_marcados.slice(0, 10),
                                tem_admin: /administrador/i.test(body),
                                tem_gestor: /gestor.*turma/i.test(body),
                                preview: body.split('\\n').slice(0, 30).join(' | ')
                            };
                        }
                    """)
                    print(f"Perfis do lider: {json.dumps(perfis_info, ensure_ascii=False)}")
    except Exception as e:
        print(f"Erro kebab: {e}")

    # 2. Paginacao real do Admin em Registros
    print("\n=== PAGINACAO REAL (ADMIN) ===")
    page.goto(REGISTROS_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_selector("tbody tr", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(3000)

    # Scroll para o rodape
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)
    tw.snap(page, BASE, "admin_paginacao_rodape")

    # Contar total de registros indo ate ultima pagina
    max_pag = page.evaluate("""
        () => {
            const btns = Array.from(document.querySelectorAll('button'));
            const nums = btns.map(b => parseInt((b.innerText || '').trim(), 10))
                .filter(n => !isNaN(n) && n > 0 && n < 10000);
            return {max: nums.length > 0 ? Math.max(...nums) : 0, nums};
        }
    """)
    print(f"Admin paginacao: {max_pag}")

    # Ir para ultima pagina disponivel
    ultima_pag = max_pag.get("max", 0)
    if ultima_pag > 1:
        try:
            # Clicar no botao da ultima pagina numerada
            btn_ultima = page.locator("button").filter(has_text=str(ultima_pag)).last
            if btn_ultima.count():
                btn_ultima.click()
                page.wait_for_timeout(3000)
                linhas_ultima = page.evaluate("() => document.querySelectorAll('tbody tr').length")
                print(f"Admin ultima pagina ({ultima_pag}): {linhas_ultima} linhas")
                tw.snap(page, BASE, "admin_ultima_pagina")

                # Calcular total estimado
                total_estimado = (ultima_pag - 1) * 25 + linhas_ultima
                print(f"Total estimado de registros (admin): {total_estimado}")
        except Exception as e:
            print(f"Erro ao ir ultima pagina: {e}")

    # 3. Lider - paginacao
    print("\n=== PAGINACAO REAL (LIDER) ===")
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

    page.goto(REGISTROS_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_selector("tbody tr, [class*='empty']", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(3000)

    # Scroll para rodape
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)
    tw.snap(page, BASE, "lider_paginacao_rodape")

    pag_lider = page.evaluate("""
        () => {
            const btns = Array.from(document.querySelectorAll('button'));
            const nums = btns.map(b => parseInt((b.innerText || '').trim(), 10))
                .filter(n => !isNaN(n) && n > 0 && n < 10000);
            const linhas = document.querySelectorAll('tbody tr').length;
            return {max: nums.length > 0 ? Math.max(...nums) : 0, nums, linhas};
        }
    """)
    print(f"Lider paginacao: {pag_lider}")

    # Ver KPIs do lider (scroll para o topo)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)
    tw.snap(page, BASE, "lider_kpis_topo")

    kpis_lider_texto = page.evaluate("""
        () => {
            // Procurar area de KPIs - os elementos com numeros e labels
            const body = document.body.innerText || '';
            // Encontrar a regiao entre 'Registros' e 'Adicionar'
            const match = body.match(/Registros\\s+Provedores([\\s\\S]*?)\\+\\s*Adicionar/);
            return {
                area_kpi: match ? match[1].trim() : 'nao encontrado',
                preview_inicio: body.substring(0, 800).replace(/\\s+/g, ' ')
            };
        }
    """)
    print(f"KPIs lider texto: {kpis_lider_texto.get('area_kpi', '')}")

    ctx.close()
    browser.close()

print("\nDone.")
