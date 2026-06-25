"""
QA 1.16 - Editar qalider via mouse click real e ver paginas do lider.
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

    # 1. Editar qalider - clicar em Editar no menu kebab
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

    # Abrir kebab via mouse.click (gotcha 1.8)
    try:
        linha_lider = page.locator("tr").filter(has_text="qalider@teste.com").first
        if linha_lider.count():
            kebab = linha_lider.locator("button:has-text('more_vert'), button[class*='kebab'], button:last-child").last
            box = kebab.bounding_box()
            if box:
                page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                page.wait_for_timeout(1500)
                tw.snap(page, BASE, "lider_kebab2")

                # Clicar em Editar via mouse.click
                editar_item = page.locator("text=Editar").first
                if editar_item.count():
                    edit_box = editar_item.bounding_box()
                    if edit_box:
                        page.mouse.click(edit_box["x"] + edit_box["width"]/2,
                                        edit_box["y"] + edit_box["height"]/2)
                        page.wait_for_timeout(3000)
                        tw.snap(page, BASE, "lider_editar_pagina")
                        print(f"URL editar: {page.url}")

                        # Verificar perfis (checkboxes marcados)
                        perfis = page.evaluate("""
                            () => {
                                const resultado = {};

                                // Checkboxes e radios marcados
                                const marcados = Array.from(
                                    document.querySelectorAll('input[type="checkbox"]:checked, input[type="radio"]:checked')
                                ).map(el => ({
                                    id: el.id,
                                    value: el.value,
                                    name: el.name,
                                    label: (() => {
                                        const lbl = document.querySelector(`label[for="${el.id}"]`);
                                        return lbl ? lbl.innerText.trim() : '';
                                    })()
                                }));

                                // Switches marcados (Chakra)
                                const switches = Array.from(
                                    document.querySelectorAll('[role="checkbox"][aria-checked="true"]')
                                ).map(el => ({
                                    aria: el.getAttribute('aria-label') || '',
                                    txt: (el.parentElement?.innerText || '').trim().substring(0, 50)
                                }));

                                // Texto completo da pagina (primeiras 1000 chars)
                                const texto = (document.body.innerText || '').substring(0, 1500);

                                return {marcados, switches, texto};
                            }
                        """)
                        print(f"Perfis marcados: {perfis['marcados']}")
                        print(f"Switches: {perfis['switches']}")
                        print(f"Texto pagina:\\n{perfis['texto'][:800]}")
    except Exception as e:
        print(f"Erro ao editar lider: {e}")

    # 2. Verificar paginas do lider (soma dos registros)
    print("\n=== LIDER: PAGINAS E TOTAL ===")
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
        page.wait_for_selector("tbody tr", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(3000)

    # Scroll para o rodape para ver paginacao completa
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)
    tw.snap(page, BASE, "lider_rodape_full")

    # Ler paginacao completa
    pag = page.evaluate("""
        () => {
            // Tentar encontrar todos indicadores de pagina
            const rodape = document.body.innerText || '';

            // Procurar padrao "X de Y" na paginacao
            const m1 = rodape.match(/(\\d+)\\s+de\\s+(\\d+)/g);

            // Contar botoes de pagina numerados
            const btns = Array.from(document.querySelectorAll('button'));
            const nums = btns.filter(b => /^\\d+$/.test((b.innerText || '').trim()))
                .map(b => parseInt(b.innerText.trim(), 10))
                .filter(n => n > 0 && n < 10000);
            const maxBtn = nums.length > 0 ? Math.max(...nums) : 0;

            // Ver texto especifico de paginacao (rodape da tabela)
            const allText = rodape.split('\\n')
                .filter(l => l.match(/\\d+.*de.*\\d+|por p.gina|pagina/i))
                .slice(0, 5);

            return {
                m1: m1 ? m1.slice(0, 5) : [],
                maxBtn,
                nums: nums.slice(0, 10),
                linhas_tbody: document.querySelectorAll('tbody tr').length,
                rodape_pag_texto: allText
            };
        }
    """)
    print(f"Paginacao lider: {json.dumps(pag, ensure_ascii=False)}")

    # Ir para ultima pagina
    if pag.get("maxBtn", 0) > 1:
        try:
            max_pag = pag["maxBtn"]
            btn_max = page.locator("button").filter(has_text=str(max_pag)).last
            if btn_max.count():
                box = btn_max.bounding_box()
                if box:
                    page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                    page.wait_for_timeout(2000)
                    linhas_ultima = page.evaluate("() => document.querySelectorAll('tbody tr').length")
                    total_estimado = (max_pag - 1) * 25 + linhas_ultima
                    print(f"Lider ultima pagina ({max_pag}): {linhas_ultima} linhas, total~{total_estimado}")
                    tw.snap(page, BASE, "lider_ultima_pagina")
        except Exception as e:
            print(f"Erro ultima pagina: {e}")

    # 3. KPIs do lider (scroll para o topo)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)
    tw.snap(page, BASE, "lider_kpis_final")

    # Ler KPIs pelo texto DOM cru
    kpis_texto = page.evaluate("""
        () => {
            // Encontrar os 4 cards de KPI
            // Procurar elementos que contem "Emitidos", "Expirados", etc.
            const resultado = {};
            const labels = ['Emitidos', 'Expirados', 'Pendentes', 'Recusados'];

            for (const label of labels) {
                // Buscar o texto no DOM
                const xp = document.evaluate(
                    `//*[normalize-space(text())='${label}']`,
                    document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
                );
                const node = xp.singleNodeValue;
                if (node) {
                    // Pegar o elemento pai do card
                    let el = node.parentElement;
                    let numEncontrado = null;
                    for (let i = 0; i < 6 && el; i++) {
                        const txt = el.textContent || '';
                        const m = txt.match(/^\\s*(\\d+)\\s*${label}/) ||
                                  txt.match(/(\\d+)\\s*\\n\\s*${label}/);
                        if (m) { numEncontrado = parseInt(m[1]); break; }
                        // Tenta pegar o primeiro numero grande no container
                        const mNum = txt.match(/\\b(\\d{1,4})\\b/);
                        if (mNum && parseInt(mNum[1]) > 0) {
                            numEncontrado = parseInt(mNum[1]);
                            break;
                        }
                        el = el.parentElement;
                    }
                    resultado[label.toLowerCase()] = numEncontrado;
                } else {
                    resultado[label.toLowerCase()] = 'label nao encontrado';
                }
            }

            return resultado;
        }
    """)
    print(f"KPIs lider (XPath): {kpis_texto}")

    ctx.close()
    browser.close()

print("\nDone.")
