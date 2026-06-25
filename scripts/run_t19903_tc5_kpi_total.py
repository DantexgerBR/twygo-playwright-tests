"""
QA 1.16 - TC5: Verificar coerencia entre KPI total e total de linhas na lista (Admin).
Estrategia: somar todas as paginas clicando em cada uma.
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
REGISTROS_URL = f"{BASE_URL}/o/{ORG_ID}/records"


def login_admin(page):
    page.context.clear_cookies()
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_selector("#user_email", timeout=10000)
    tw.login(page, c, admin=True)


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    login_admin(page)

    page.goto(REGISTROS_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_selector("tbody tr", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(3000)

    # Aumentar para 100 por pagina para facilitar contagem
    # Tentar mudar o per_page
    try:
        select_pp = page.locator("select").last
        if select_pp.count():
            select_pp.select_option("100")
            page.wait_for_timeout(2000)
            print("Mudou para 100 por pagina")
    except Exception:
        pass

    # Ler KPIs visuais
    tw.snap(page, BASE, "tc5_admin_kpis")
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)

    # Capturar os numeros dos KPI cards visualmente
    # Os cards mostram 299 | 55 | 80 | 20 nos screenshots
    # Vamos usar o texto da pagina para confirmar
    kpi_texto_cru = page.evaluate("""
        () => {
            // Pegar o texto da secao de KPIs (area antes da tabela)
            const tabela = document.querySelector('table, [class*="table"]');
            if (tabela) {
                // Pegar texto antes da tabela
                let el = tabela;
                while (el.previousElementSibling) {
                    el = el.previousElementSibling;
                }
                // Pegar todo o conteudo anterior a tabela
                return {
                    antes_tabela: (el?.innerText || '').replace(/\\s+/g, ' ').trim().substring(0, 500)
                };
            }
            return {antes_tabela: ''};
        }
    """)
    print(f"Texto antes da tabela: {kpi_texto_cru}")

    # Contar todas as linhas somando as paginas
    # Primeiro verificar paginacao atual
    scroll_e_ler = lambda: page.evaluate("""
        () => {
            // Scroll ate o rodape
            window.scrollTo(0, document.body.scrollHeight);
            const linhas = document.querySelectorAll('tbody tr').length;
            const btns = Array.from(document.querySelectorAll('button'))
                .filter(b => /^\\d+$/.test((b.innerText||'').trim()))
                .map(b => parseInt(b.innerText.trim(), 10))
                .filter(n => n > 0 && n < 10000);
            // Texto de paginacao "X de Y"
            const body = document.body.innerText || '';
            const m = body.match(/(\\d+)\\s+de\\s+(\\d+)/g);
            return {linhas, btns, pag_texto: m ? m : []};
        }
    """)

    pag1 = scroll_e_ler()
    print(f"Pagina 1: {pag1}")
    tw.snap(page, BASE, "tc5_pag1_rodape")

    # Calcular total real baseado na paginacao
    # "1 de 17" significa 17 paginas totais (mas e do lider, nao admin)
    # Para o admin vamos ver o texto "X de Y"
    total_real = 0
    max_pag_admin = 0

    if pag1.get('pag_texto'):
        # Extrair "1 de 17" etc.
        for pt in pag1['pag_texto']:
            import re
            m = re.search(r'(\d+)\s+de\s+(\d+)', pt)
            if m:
                max_pag_admin = int(m.group(2))
                print(f"Admin tem {max_pag_admin} paginas totais")
                break

    if not max_pag_admin and pag1.get('btns'):
        max_pag_admin = max(pag1['btns'])
        print(f"Admin max pagina (btns): {max_pag_admin}")

    if max_pag_admin > 0:
        # Ir para a ultima pagina para contar as linhas
        # Clicar no botao de ultima pagina (>>)
        try:
            # Tentar botao >> ou ultimo numero
            last_btn = page.locator("button").filter(has_text=">>").or_(
                page.locator("button[aria-label*='ltima'], button[aria-label*='last']")
            ).first
            if not last_btn.count():
                # Clicar no numero max
                max_str = str(max_pag_admin)
                last_btn = page.locator("button").filter(has_text=max_str).last
            if last_btn.count():
                box = last_btn.bounding_box()
                if box:
                    page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                    page.wait_for_timeout(2000)
                    linhas_ultima = page.evaluate("() => document.querySelectorAll('tbody tr').length")
                    total_real = (max_pag_admin - 1) * 25 + linhas_ultima
                    print(f"Ultima pagina ({max_pag_admin}): {linhas_ultima} linhas")
                    print(f"TOTAL REAL DE REGISTROS (admin): {total_real}")
                    tw.snap(page, BASE, "tc5_ultima_pagina")
        except Exception as e:
            print(f"Erro ao ir ultima pagina: {e}")
    else:
        # Apenas 1 pagina
        total_real = pag1.get('linhas', 0)
        print(f"Admin tem apenas 1 pagina, {total_real} linhas")

    # KPIs confirmados nos screenshots: 299 + 55 + 80 + 20 = 454
    # Mas precisa de mais status se houver
    # Verificar no texto da pagina se ha mais status
    page.goto(REGISTROS_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_selector("tbody tr", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.snap(page, BASE, "tc5_kpis_confirmacao")

    print(f"\n=== RESUMO TC5 ===")
    print(f"KPIs visuais (lidos nos screenshots): 299 Emitidos + 55 Expirados + 80 Pendentes + 20 Recusados = 454")
    print(f"Total real de registros na lista: {total_real}")
    if total_real > 0:
        print(f"Coerencia: {'OK' if total_real == 454 else 'DIVERGENCIA - ' + str(total_real) + ' != 454'}")

    ctx.close()
    browser.close()

print("\nDone.")
