"""
QA 1.16 - Investigacao detalhada:
1. Admin: total real de registros (scroll/paginas)
2. Lider: total real de registros
3. Comparar se lider ve mesmo conjunto que admin
4. Interagir com campo Pessoas (react-select-2-input)
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


def login_como(page, email, senha):
    page.context.clear_cookies()
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", email)
    page.fill("#user_password", senha)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)


def login_admin(page):
    login_como(page, c["email"], c["senha"])
    # Switch para admin
    page.goto(f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
              wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(3000)


def ir_registros(page):
    page.goto(REGISTROS_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_selector("tbody tr", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)


def info_completa(page, label):
    """Coleta info completa da tela de Registros."""
    # Captura os numeros dos KPI cards via innerText dos itens graficos
    kpi_raw = page.evaluate("""
        () => {
            // Pegar todo o texto da area dos KPIs (acima da lista)
            // Os KPIs ficam num container antes da tabela
            const containers = Array.from(document.querySelectorAll(
                '[class*="KPI"], [class*="kpi"], [class*="stat"], [class*="Stat"], [class*="card"], [class*="Card"]'
            )).filter(el => el.offsetParent !== null);

            const resultado = {containers_encontrados: containers.length, kpis: []};
            containers.forEach(c => {
                const txt = (c.innerText || '').replace(/\\s+/g, ' ').trim();
                if (txt.length > 0 && txt.length < 100) {
                    resultado.kpis.push(txt);
                }
            });
            return resultado;
        }
    """)
    print(f"  KPI containers ({label}): {json.dumps(kpi_raw, ensure_ascii=False)[:500]}")

    # Info da lista
    lista_info = page.evaluate("""
        () => {
            // Total de linhas
            const linhas = document.querySelectorAll('tbody tr').length;

            // Tentar achar "Capacidade total: X pessoas" ou "X registros"
            const body = document.body.innerText || '';
            const mCap = body.match(/Capacidade total[:\\s]+(\\d+)/i);
            const mReg = body.match(/(\\d+)\\s+registros/i);

            // Achar todos os numeros grandes na pagina
            const matches = body.match(/\\b([1-9]\\d{2,})\\b/g) || [];
            const numeros = [...new Set(matches.map(Number))].sort((a,b) => b-a).slice(0,10);

            // Botoes de paginacao
            const pagArea = document.querySelector('[class*="pagination"], [class*="Pagination"], nav[aria-label]');
            const pagTxt = pagArea ? (pagArea.innerText || '').replace(/\\s+/g, ' ').trim() : '';

            // Texto completo do rodape da tabela
            const tfoot = document.querySelector('tfoot');
            const tfootTxt = tfoot ? (tfoot.innerText || '').trim() : '';

            return {
                linhas,
                capacidade: mCap ? parseInt(mCap[1]) : null,
                num_registros: mReg ? parseInt(mReg[1]) : null,
                numeros_grandes: numeros,
                paginacao_texto: pagTxt,
                tfoot: tfootTxt
            };
        }
    """)
    print(f"  Lista ({label}): {json.dumps(lista_info, ensure_ascii=False)}")

    # Emails distintos na lista
    emails = page.evaluate("""
        () => {
            const set = new Set();
            document.querySelectorAll('tbody tr').forEach(r => {
                const m = (r.innerText || '').match(/[\\w.+%-]+@[\\w.-]+\\.[a-z]{2,}/gi);
                if (m) m.forEach(e => set.add(e.toLowerCase()));
            });
            return Array.from(set);
        }
    """)
    print(f"  Emails ({label}): {emails}")
    return lista_info


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)

    # ADMIN
    print("=== ADMIN ===")
    login_admin(page)
    ir_registros(page)
    info_admin = info_completa(page, "admin")
    tw.snap(page, BASE, "kpi_admin_full")

    # Tentar clicar em uma proxima pagina se existir
    try:
        prox = page.locator("button[aria-label*='roxim'], button[aria-label*='next'], button:has-text('>')").first
        if prox.count() and prox.is_enabled():
            prox.click()
            page.wait_for_timeout(2000)
            linhas_p2 = page.evaluate("() => document.querySelectorAll('tbody tr').length")
            print(f"  Admin pagina 2: {linhas_p2} linhas")
            tw.snap(page, BASE, "kpi_admin_pagina2")
    except Exception as e:
        print(f"  Nao foi possivel ir para pagina 2: {e}")

    # LIDER
    print("\n=== LIDER ===")
    login_como(page, c_lider["email"], c_lider["senha"])
    ir_registros(page)

    # Confirmar perfil
    perfil = page.evaluate("""
        () => {
            const btns = Array.from(document.querySelectorAll('button'));
            const b = btns.find(b => /gestor|administrador|colaborador/i.test(b.innerText || ''));
            return {perfil: b ? b.innerText.trim() : '?', url: window.location.href};
        }
    """)
    print(f"  Perfil lider na tela: {perfil}")
    info_lider = info_completa(page, "lider")
    tw.snap(page, BASE, "kpi_lider_full")

    # FORM ADICIONAR - campo Pessoas via react-select
    print("\n=== FORM ADICIONAR - CAMPO PESSOAS (react-select) ===")
    btn_add = page.locator("button", has_text="Adicionar").first
    if btn_add.count():
        btn_add.click()
        page.wait_for_timeout(3000)
        tw.snap(page, BASE, "kpi_lider_form")

        # O campo Pessoas eh um react-select custom - nao tem placeholder simples
        # Id encontrado: react-select-2-input
        # O container clicavel do react-select fica acima do input
        try:
            # Clicar no container do react-select de Pessoas (2o react-select, apos website)
            # Scrollar para o campo Pessoas
            pessoas_container = page.locator("[class*='pessoas'], [class*='Pessoas'],"
                " label:has-text('Pessoas') + *, "
                "[class*='select']:nth-of-type(1)"
            ).first
            if not pessoas_container.count():
                # Tentar pelo id do input interno
                pessoas_input = page.locator("#react-select-2-input")
                if pessoas_input.count():
                    pessoas_input.scroll_into_view_if_needed()
                    # Clicar no container pai do react-select
                    container = page.evaluate("""
                        () => {
                            const input = document.getElementById('react-select-2-input');
                            if (!input) return null;
                            // Subir ate achar o container do react-select
                            let el = input;
                            for (let i = 0; i < 5; i++) {
                                if (el.parentElement) {
                                    const cls = el.parentElement.className || '';
                                    if (cls.includes('container') || cls.includes('control')) {
                                        return {found: true, class: cls};
                                    }
                                    el = el.parentElement;
                                }
                            }
                            return {found: false};
                        }
                    """)
                    print(f"  Container react-select: {container}")
                    pessoas_input.click()
                    page.wait_for_timeout(1000)
                    tw.snap(page, BASE, "kpi_lider_pessoas_click")

                    # Ler opcoes abertas
                    opcoes = page.evaluate("""
                        () => {
                            const menu = document.querySelector('[class*="menu"]');
                            if (!menu) return {menu: false};
                            const opts = Array.from(menu.querySelectorAll('[class*="option"]'));
                            return {
                                menu: true,
                                total_opcoes: opts.length,
                                primeiras: opts.slice(0, 10).map(o => (o.innerText || '').trim())
                            };
                        }
                    """)
                    print(f"  Opcoes dropdown Pessoas: {json.dumps(opcoes, ensure_ascii=False)}")

                    # Digitar algo para ver resultados
                    page.keyboard.type("qa")
                    page.wait_for_timeout(1500)
                    tw.snap(page, BASE, "kpi_lider_pessoas_qa")
                    opcoes_qa = page.evaluate("""
                        () => {
                            const menu = document.querySelector('[class*="menu"]');
                            if (!menu) return {menu: false};
                            const opts = Array.from(menu.querySelectorAll('[class*="option"]'));
                            return {
                                menu: true,
                                total_opcoes: opts.length,
                                primeiras: opts.slice(0, 10).map(o => (o.innerText || '').trim())
                            };
                        }
                    """)
                    print(f"  Opcoes 'qa' no campo Pessoas: {json.dumps(opcoes_qa, ensure_ascii=False)}")

        except Exception as e:
            print(f"  Erro no campo Pessoas: {e}")

    ctx.close()
    browser.close()

print("\nDone.")
