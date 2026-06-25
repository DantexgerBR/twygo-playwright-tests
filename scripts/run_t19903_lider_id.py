"""
QA 1.16 - Descobrir ID do qalider e abrir edicao direto.
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

SLUG = "registros-f2-qa116"
BASE = tw.ROOT / "evidencias" / SLUG
BASE.mkdir(parents=True, exist_ok=True)
BASE_URL = c["base_url"]
ORG_ID = c["org_id"]


def login_admin(page):
    page.context.clear_cookies()
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector("#user_email", timeout=10000)
    tw.login(page, c, admin=True)


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    login_admin(page)

    # Buscar qalider na lista
    page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)
    try:
        search = page.locator("input[placeholder*='esquise'], input[type='search']").first
        if search.count():
            search.fill("qalider")
            page.wait_for_timeout(2000)
    except Exception:
        pass

    # Pegar todos os links com href contendo users
    links = page.evaluate("""
        () => Array.from(document.querySelectorAll('a'))
            .filter(a => a.href && /users\\/\\d+/.test(a.href))
            .map(a => ({href: a.href, texto: (a.innerText || '').trim()}))
            .slice(0, 5)
    """)
    print(f"Links de usuarios: {links}")

    # Tentar via API de usuarios
    users_api = page.evaluate(f"""
        async () => {{
            try {{
                const r = await fetch('/o/{ORG_ID}/api/users?search=qalider&per_page=5', {{
                    headers: {{'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}}
                }});
                if (!r.ok) return {{erro: r.status}};
                const data = await r.json();
                return {{keys: Object.keys(data), data: JSON.stringify(data).substring(0, 500)}};
            }} catch(e) {{
                return {{erro: e.message}};
            }}
        }}
    """)
    print(f"API users: {users_api}")

    # Tentar via data atributos na lista
    data_info = page.evaluate("""
        () => {
            const rows = Array.from(document.querySelectorAll('tr, [data-id], [data-user-id]'));
            return rows.map(r => ({
                dataset: JSON.stringify(r.dataset || {}),
                texto: (r.innerText || '').trim().substring(0, 80)
            })).filter(r => /qalider/.test(r.texto)).slice(0, 3);
        }
    """)
    print(f"Data info rows: {data_info}")

    # Interceptar requisicao ao clicar no kebab para ver URL com ID
    # Primeiro, registrar listener de request
    requests_captured = []
    def on_request(request):
        if 'users' in request.url and 'edit' in request.url.lower():
            requests_captured.append(request.url)
    page.on("request", on_request)

    # Tentar clicar no kebab novamente com mouse.click absoluto
    try:
        linha = page.locator("tr").filter(has_text="qalider@teste.com").first
        if linha.count():
            box = linha.bounding_box()
            print(f"Bounding box da linha lider: {box}")
            tw.snap(page, BASE, "lider_linha_inteira")

            # Pegar o kebab (last button na linha)
            btns = linha.locator("button").all()
            print(f"Botoes na linha: {len(btns)}")
            for i, b in enumerate(btns):
                b_box = b.bounding_box()
                b_txt = b.inner_text()
                print(f"  btn[{i}]: txt='{b_txt}' box={b_box}")

            if btns:
                last_btn = btns[-1]
                b_box = last_btn.bounding_box()
                if b_box:
                    # Click com mouse direto nas coordenadas
                    cx = b_box["x"] + b_box["width"]/2
                    cy = b_box["y"] + b_box["height"]/2
                    page.mouse.click(cx, cy)
                    page.wait_for_timeout(2000)
                    tw.snap(page, BASE, "lider_kebab_aberto")

                    # Agora pegar o href do item Editar no menu
                    menu_info = page.evaluate("""
                        () => {
                            const items = Array.from(document.querySelectorAll(
                                '[role="menu"] a, [role="menu"] button, [role="menuitem"]'
                            )).filter(el => el.offsetParent !== null);
                            return items.map(el => ({
                                tag: el.tagName,
                                href: el.getAttribute('href') || '',
                                texto: (el.innerText || '').trim()
                            }));
                        }
                    """)
                    print(f"Items do menu kebab: {menu_info}")

                    # Clicar em Editar se tiver href
                    editar_link = [i for i in menu_info if 'editar' in i.get('texto', '').lower() or 'edit' in i.get('href', '').lower()]
                    print(f"Link editar: {editar_link}")

                    if editar_link:
                        href = editar_link[0].get('href', '')
                        if href:
                            full_url = f"{BASE_URL}{href}" if href.startswith('/') else href
                            page.goto(full_url, wait_until="domcontentloaded", timeout=15000)
                            page.wait_for_timeout(2000)
                            tw.snap(page, BASE, "lider_editar_final")
                            print(f"URL: {page.url}")

                            # Ler perfis
                            perfis = page.evaluate("""
                                () => {
                                    const texto = document.body.innerText || '';
                                    // Secao de perfis
                                    const linhas = texto.split('\\n').filter(l => l.trim());
                                    return {
                                        perfis_secao: (() => {
                                            const idx = linhas.findIndex(l => /perfil/i.test(l));
                                            return idx >= 0 ? linhas.slice(idx, idx+10) : [];
                                        })(),
                                        tem_admin: /administrador/i.test(texto),
                                        tem_gestor: /gestor de turma/i.test(texto),
                                        tem_colaborador: /colaborador/i.test(texto),
                                        preview: texto.substring(0, 1000)
                                    };
                                }
                            """)
                            print(f"Perfis lider: {json.dumps(perfis, ensure_ascii=False)}")
    except Exception as e:
        print(f"Erro: {e}")

    ctx.close()
    browser.close()

print("\nDone.")
