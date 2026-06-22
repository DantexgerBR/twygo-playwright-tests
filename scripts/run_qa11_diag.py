"""run_qa11_diag.py — Diagnóstico focado em 2 pontos:
1. Seletor do toggle Grid/Lista
2. Interação real com o campo de busca (keystrokes vs fill)

Roda headless.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

SLUG = "registros-f2-qa11"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)

BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")
ALUNO_EMAIL = os.environ.get("ALUNO_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
ORG_ID = os.environ.get("ORG_ID", "36675")
RECORDS_URL = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"


def login_como_aluno(page):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", ALUNO_EMAIL)
    page.fill("#user_password", ADMIN_PASSWORD)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)


def ir_para_meu_historico(page):
    page.goto(RECORDS_URL, wait_until="domcontentloaded", timeout=25000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    login_como_aluno(page)
    ir_para_meu_historico(page)

    # === DIAGNÓSTICO 1: Toggle Grid/Lista ===
    print("\n=== DIAGNÓSTICO 1: Toggle Grid/Lista ===")

    # Dump do HTML da toolbar inteira para identificar seletores
    toolbar_html = page.evaluate("""() => {
        // Tenta encontrar o container que tem o campo de busca e os botões de toggle
        const busca = document.querySelector('input[placeholder*="Pesquise"]');
        if (!busca) return 'busca não encontrada';
        // Sobe até achar o container que também contém os botões de toggle
        let el = busca.parentElement;
        for (let i = 0; i < 8; i++) {
            if (!el) break;
            const btns = el.querySelectorAll('button');
            if (btns.length >= 2) {
                // Encontrou um container com botões
                return el.outerHTML.substring(0, 3000);
            }
            el = el.parentElement;
        }
        return 'container com botões não encontrado';
    }""")
    print(f"Toolbar HTML (truncado):\n{toolbar_html[:2000]}")

    # Lista todos os botões visíveis na área de busca + toggle
    btns_info = page.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        const result = [];
        for (const btn of btns) {
            const rect = btn.getBoundingClientRect();
            // Só botões no range Y da toolbar (~320-380 pixels)
            if (rect.top > 320 && rect.top < 400 && rect.width < 60) {
                result.push({
                    text: btn.innerText?.trim() || '',
                    ariaLabel: btn.getAttribute('aria-label') || '',
                    title: btn.title || '',
                    className: btn.className?.substring(0, 100) || '',
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    w: Math.round(rect.width),
                    h: Math.round(rect.height),
                    svgContent: btn.querySelector('svg')?.innerHTML?.substring(0, 100) || ''
                });
            }
        }
        return result;
    }""")
    print(f"\nBotões na área da toolbar:")
    for b in btns_info:
        print(f"  text='{b['text']}' aria='{b['ariaLabel']}' title='{b['title']}' cls='{b['className'][:60]}' pos=({b['x']},{b['y']})")

    # Tenta identificar os botões de toggle especificamente
    # Na screenshot, são dois ícones de grid e lista logo antes do botão "Filtro"
    toggle_btns = page.evaluate("""() => {
        // Procura grupo de botões (role=group) perto do botão Filtro
        const filtroBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText?.includes('Filtro'));
        if (!filtroBtn) return 'botão Filtro não encontrado';
        // Vai até o elemento pai e pega botões irmãos
        let el = filtroBtn.parentElement;
        for (let i = 0; i < 5; i++) {
            if (!el) break;
            const btns = Array.from(el.querySelectorAll('button'));
            if (btns.includes(filtroBtn)) {
                return btns.map(b => ({
                    text: b.innerText?.trim() || '',
                    ariaLabel: b.getAttribute('aria-label') || '',
                    dataTestId: b.getAttribute('data-testid') || '',
                    className: b.className?.substring(0, 80) || ''
                }));
            }
            el = el.parentElement;
        }
        return 'não achou grupo';
    }""")
    print(f"\nBotões perto do 'Filtro': {toggle_btns}")

    tw.snap(page, EVID, "diag_01_toolbar_estado")

    # === DIAGNÓSTICO 2: Busca com keystrokes reais ===
    print("\n=== DIAGNÓSTICO 2: Busca com keystrokes ===")
    ir_para_meu_historico(page)
    row_count_antes = page.locator("table tbody tr").count()
    print(f"Linhas antes da busca: {row_count_antes}")

    busca = page.get_by_placeholder("Pesquise por conteúdo, origem ou provedor")
    busca.click()
    page.wait_for_timeout(300)

    # Registra requests de rede durante a busca
    requests_capturados = []
    def on_request(request):
        if "records" in request.url.lower() or "learning" in request.url.lower():
            requests_capturados.append({"url": request.url, "method": request.method})
    page.on("request", on_request)

    # Digita caractere a caractere
    termo = "zzzzz-inexistente-99"
    print(f"Digitando '{termo}' caractere a caractere...")
    busca.press_sequentially(termo, delay=60)
    page.wait_for_timeout(3000)  # aguarda debounce + request + render

    print(f"Requests capturados durante busca: {len(requests_capturados)}")
    for req in requests_capturados:
        print(f"  {req['method']} {req['url']}")

    row_count_depois = page.locator("table tbody tr").count()
    empty_msg = page.get_by_text("Nenhum registro encontrado").count() > 0
    print(f"Linhas após busca: {row_count_depois}, empty state: {empty_msg}")
    tw.snap(page, EVID, "diag_02_busca_keystrokes")

    # Tenta também com Enter
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)
    row_after_enter = page.locator("table tbody tr").count()
    empty_after_enter = page.get_by_text("Nenhum registro encontrado").count() > 0
    print(f"Após Enter: linhas={row_after_enter}, empty={empty_after_enter}")
    tw.snap(page, EVID, "diag_02_busca_apos_enter")

    # Limpa busca e verifica restauração
    busca.clear()
    page.wait_for_timeout(2000)
    row_after_clear = page.locator("table tbody tr").count()
    print(f"Após limpar: linhas={row_after_clear}")

    # === DIAGNÓSTICO 3: Colunas AT vs real ===
    print("\n=== DIAGNÓSTICO 3: Colunas reais ===")
    ir_para_meu_historico(page)
    headers = page.locator("table thead th").all_inner_texts()
    print(f"Headers reais: {headers}")
    print("AT esperava: ['Origem', 'Conteúdo', 'Provedor', 'Situação do registro', 'Progresso', 'Situação do certificado', 'Carga horária', 'Emitido em', 'Expira em']")
    print("Produto tem: (ver acima)")

    ctx.close()
    browser.close()
    print("\nDiagnóstico concluído.")
