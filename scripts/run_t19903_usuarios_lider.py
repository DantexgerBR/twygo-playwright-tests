"""
QA 1.16 - Verificar liderados do qalider via pagina de usuarios
e verificar se a lista de registros do lider e igual a do admin.
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

    # 1. Buscar usuarios na lista de admin
    print("=== USUARIOS DA ORG ===")
    page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)

    # Buscar qalider
    try:
        search = page.locator("input[placeholder*='esquise'], input[type='search']").first
        if search.count():
            search.fill("qalider")
            page.wait_for_timeout(2000)
    except Exception:
        pass
    tw.snap(page, BASE, "usuarios_busca_lider")

    linhas_lider = page.evaluate("""
        () => {
            const rows = Array.from(document.querySelectorAll('tbody tr'));
            return rows.map(r => (r.innerText || '').replace(/\\s+/g, ' ').trim()).slice(0, 5);
        }
    """)
    print(f"Linhas de qalider: {linhas_lider}")

    # Ver detalhes do usuario qalider - clicar para editar
    try:
        lider_link = page.locator("tr").filter(has_text="qalider").locator("a").first
        if not lider_link.count():
            lider_link = page.locator("tr").filter(has_text="lider").locator("a, button").first
        if lider_link.count():
            href = lider_link.get_attribute("href")
            print(f"Link lider: {href}")
            page.goto(f"{BASE_URL}{href}" if href and href.startswith('/') else (href or ''),
                      wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(2000)
            tw.snap(page, BASE, "lider_perfil_admin")
            # Ver perfis do usuario
            perfis = page.evaluate("""
                () => {
                    const body = document.body.innerText || '';
                    const linhas = body.split('\\n').filter(l => l.trim().length > 0);
                    return linhas.slice(0, 40);
                }
            """)
            print(f"Perfil lider (admin view):\\n" + "\\n".join(perfis[:30]))
    except Exception as e:
        print(f"Erro ao ver perfil: {e}")

    # 2. Buscar os usuarios qa11tc342588 e qa11tc342816
    print("\n=== USUARIOS DOS REGISTROS ===")
    for email_busca in ["qa11tc342588", "qa11tc342816"]:
        page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
        try:
            search = page.locator("input[placeholder*='esquise'], input[type='search']").first
            if search.count():
                search.fill(email_busca)
                page.wait_for_timeout(2000)
        except Exception:
            pass
        linha = page.evaluate("""
            () => {
                const rows = Array.from(document.querySelectorAll('tbody tr'));
                return rows.map(r => (r.innerText || '').replace(/\\s+/g, ' ').trim()).slice(0, 3);
            }
        """)
        print(f"Usuario {email_busca}: {linha}")

    # 3. Total de registros da org via API (se disponivel)
    print("\n=== CONTAGEM REAL DE REGISTROS ===")
    page.goto(REGISTROS_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_selector("tbody tr", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    tw.snap(page, BASE, "admin_registros_total")

    # Tentar API do registros para ver total
    try:
        resp = page.evaluate(f"""
            async () => {{
                const r = await fetch('/o/{ORG_ID}/api/records?per_page=1', {{
                    headers: {{'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}}
                }});
                if (!r.ok) return {{erro: r.status}};
                const data = await r.json();
                return {{
                    total: data.total || data.meta?.total || data.count || '?',
                    keys: Object.keys(data)
                }};
            }}
        """)
        print(f"API records: {resp}")
    except Exception as e:
        print(f"Erro API: {e}")

    # Paginacao na lista (metodo alternativo - verificar botoes de paginacao no DOM)
    pag_info = page.evaluate("""
        () => {
            // Procurar em toda a pagina por indicadores de paginacao
            const body = document.body.innerHTML || '';

            // Verificar se ha 'page=' nos botoes
            const btns = Array.from(document.querySelectorAll('button, a'));
            const pagBtns = btns.filter(b => {
                const txt = (b.innerText || '').trim();
                return /^\\d+$/.test(txt) && parseInt(txt) > 0 && parseInt(txt) < 1000;
            }).map(b => ({texto: b.innerText.trim(), aria: b.getAttribute('aria-label') || ''}));

            // Verificar qualquer elemento com 'page' no aria ou classe
            const pageEls = Array.from(document.querySelectorAll('[aria-label*="page"], [class*="page"]'))
                .filter(el => el.offsetParent !== null)
                .map(el => ({
                    tag: el.tagName,
                    cls: (el.className || '').substring(0, 50),
                    aria: el.getAttribute('aria-label') || '',
                    texto: (el.innerText || '').trim().substring(0, 30)
                })).slice(0, 10);

            return {
                pagBtns: pagBtns.slice(0, 10),
                pageEls: pageEls.slice(0, 10)
            };
        }
    """)
    print(f"Paginacao info: {json.dumps(pag_info, ensure_ascii=False)}")

    # Scroll para o fundo da lista para ver paginacao
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)
    tw.snap(page, BASE, "admin_registros_rodape")

    # Screenshot full page
    page.screenshot(path=str(BASE / "admin_registros_fullpage.png"), full_page=True)
    print("Screenshot full page salvo")

    ctx.close()
    browser.close()

print("\nDone.")
