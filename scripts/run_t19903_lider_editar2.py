"""
QA 1.16 - Editar qalider clicando diretamente no botao Editar do menu.
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

    print("=== EDITAR QALIDER ===")
    page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)

    try:
        search = page.locator("input[placeholder*='esquise'], input[type='search']").first
        if search.count():
            search.fill("qalider")
            page.wait_for_timeout(2000)
    except Exception:
        pass

    # Abrir kebab
    linha = page.locator("tr").filter(has_text="qalider@teste.com").first
    btns = linha.locator("button").all()
    last_btn = btns[-1]
    box = last_btn.bounding_box()
    page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
    page.wait_for_timeout(1500)

    # Clicar em Editar pelo texto (agora o menu esta visivel)
    editar_btn = page.locator("button").filter(has_text="Editar").first
    box_editar = editar_btn.bounding_box()
    if box_editar:
        print(f"Botao Editar: {box_editar}")
        page.mouse.click(box_editar["x"] + box_editar["width"]/2,
                        box_editar["y"] + box_editar["height"]/2)
        page.wait_for_timeout(3000)
        print(f"URL apos clicar Editar: {page.url}")
        tw.snap(page, BASE, "lider_editar_final2")

        # Ler perfis
        texto_pagina = page.evaluate("""
            () => {
                const body = document.body.innerText || '';
                return {
                    url: window.location.href,
                    tem_admin: /administrador/i.test(body),
                    tem_gestor: /gestor de turma/i.test(body),
                    tem_colaborador: /colaborador/i.test(body),
                    preview: body.substring(0, 2000).replace(/\\s+/g, ' ')
                };
            }
        """)
        print(f"Perfis na pagina: {json.dumps(texto_pagina, ensure_ascii=False)[:1000]}")

        # Ver checkboxes de perfis
        checkboxes = page.evaluate("""
            () => {
                // Procurar inputs type checkbox
                const cbs = Array.from(document.querySelectorAll('input[type="checkbox"]'));
                return cbs.map(cb => ({
                    id: cb.id,
                    name: cb.name,
                    value: cb.value,
                    checked: cb.checked,
                    label: (() => {
                        // Pegar o label associado
                        const lbl = document.querySelector(`label[for="${cb.id}"]`);
                        return lbl ? lbl.innerText.trim() : cb.closest('label')?.innerText.trim() || '';
                    })()
                })).filter(cb => cb.label.length > 0 || cb.id.length > 0);
            }
        """)
        print(f"Checkboxes: {json.dumps(checkboxes, ensure_ascii=False)}")

        # Ver switches (perfis podem ser switches Chakra)
        switches = page.evaluate("""
            () => {
                const sws = Array.from(document.querySelectorAll('[role="checkbox"], [role="switch"]'));
                return sws.map(sw => ({
                    role: sw.getAttribute('role'),
                    checked: sw.getAttribute('aria-checked'),
                    label: (sw.getAttribute('aria-label') || ''),
                    parent_text: (sw.parentElement?.innerText || '').trim().substring(0, 80)
                })).filter(sw => sw.checked !== null);
            }
        """)
        print(f"Switches (perfis): {json.dumps(switches, ensure_ascii=False)[:500]}")

    ctx.close()
    browser.close()

print("\nDone.")
