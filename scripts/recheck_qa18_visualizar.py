"""
Re-check QA 1.8 — Verifica se o bug 'Visualizar nao executa acao' foi corrigido.
Card Artia 19895 | Execucao inicial: 2026-06-23 | Re-check: 2026-06-24

Testa apenas o ponto central do bug P1:
- Aluno: clicar em Visualizar no registro Externo+Pendente
- Admin: clicar em Visualizar no registro Interno ou Externo Emitido

Estrategia: teclado (ArrowDown+Enter) que foi o metodo definitivo da execucao anterior.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
ADMIN_EMAIL = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
ALUNO_EMAIL = "qa11tc342588@twygotest.com"
ALUNO_PASSWORD = "twygoqa2026"

PASTA = Path(__file__).resolve().parents[1] / "evidencias" / "registros-f2-qa18"
PASTA.mkdir(parents=True, exist_ok=True)

c_admin = {"base_url": BASE_URL, "org_id": ORG_ID, "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}
c_aluno = {"base_url": BASE_URL, "org_id": ORG_ID, "email": ALUNO_EMAIL, "senha": ALUNO_PASSWORD}

results = {}


def snap(page, nome, full=False):
    fp = PASTA / f"recheck_{nome}.png"
    page.screenshot(path=str(fp), full_page=full)
    print(f"   [snap] {fp.name}")
    return fp


def testar_visualizar_via_teclado(page, perfil_label, snap_prefix):
    """
    Abre o kebab da primeira linha via teclado (ArrowDown ate Visualizar + Enter).
    Aguarda 4s e verifica se houve navegacao ou abertura de nova aba.
    Retorna (passou, descricao)
    """
    ctx = page.context

    # Garantir que a tabela esta carregada
    rows = page.locator("tbody tr")
    n = rows.count()
    print(f"   [{perfil_label}] Linhas na tabela: {n}")
    if n == 0:
        snap(page, f"{snap_prefix}_sem_tabela", full=True)
        return False, "Tabela sem linhas — ambiente nao renderizou"

    snap(page, f"{snap_prefix}_01_lista", full=True)

    # Abrir kebab da primeira linha
    kebab = rows.first.locator("button.chakra-menu__menu-button").first
    if kebab.count() == 0:
        kebab = rows.first.locator("button[aria-haspopup='menu']").first
    if kebab.count() == 0:
        return False, "Botao kebab nao encontrado na primeira linha"

    kebab.click()
    page.wait_for_timeout(1200)
    snap(page, f"{snap_prefix}_02_menu_aberto")

    # Identificar posicao do item Visualizar no menu via texto
    # O metodo: ArrowDown sequencial ate encontrar Visualizar
    # Tentativa: ate 5 ArrowDown para achar o item
    url_antes = page.url
    pages_antes = len(ctx.pages)

    # Pressionar Escape para fechar e reabrir para usar teclado limpo
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    kebab.click()
    page.wait_for_timeout(1200)

    # Navegar com teclado: o primeiro foco apos abrir e no primeiro item (Editar ou similar)
    # Usar ArrowDown ate chegar no Visualizar (max 5 tentativas)
    encontrou_visualizar = False
    for i in range(6):
        # Verificar texto do item focado atualmente
        focused_text = page.evaluate("""() => {
            const el = document.activeElement;
            return el ? el.innerText.trim() : '';
        }""")
        print(f"   Foco atual (step {i}): '{focused_text}'")
        if "visualizar" in focused_text.lower():
            encontrou_visualizar = True
            snap(page, f"{snap_prefix}_03_visualizar_focado")
            print(f"   'Visualizar' focado no step {i} — pressionando Enter")
            page.keyboard.press("Enter")
            break
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(300)

    if not encontrou_visualizar:
        snap(page, f"{snap_prefix}_03_sem_foco_visualizar")
        # Tentativa alternativa: clicar diretamente no item via texto
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        kebab.click()
        page.wait_for_timeout(1200)
        vis_item = page.get_by_role("menuitem", name="Visualizar")
        if vis_item.count() > 0:
            vis_item.first.click()
            print(f"   Clicou em Visualizar via role selector")
        else:
            snap(page, f"{snap_prefix}_03_item_nao_encontrado")
            return False, "Item Visualizar nao encontrado no menu via teclado nem role"

    page.wait_for_timeout(4000)
    url_depois = page.url
    pages_depois = len(ctx.pages)

    snap(page, f"{snap_prefix}_04_pos_visualizar", full=True)

    print(f"   URL antes: {url_antes}")
    print(f"   URL depois: {url_depois}")
    print(f"   Paginas antes: {pages_antes}, depois: {pages_depois}")

    if pages_depois > pages_antes:
        nova_aba = ctx.pages[-1]
        nova_aba.wait_for_load_state("domcontentloaded", timeout=15000)
        nova_aba.wait_for_timeout(2000)
        snap(nova_aba, f"{snap_prefix}_05_nova_aba", full=True)
        print(f"   NOVA ABA aberta! URL: {nova_aba.url}")
        return True, f"Visualizar abriu nova aba (standalone). URL={nova_aba.url}"
    elif url_depois != url_antes:
        texto = page.inner_text("body")
        tem_header_visualizar = "visualizar registro" in texto.lower()
        tem_inputs_disabled = page.evaluate(
            "() => document.querySelectorAll('input:disabled, textarea:disabled, select:disabled').length"
        )
        print(f"   Navegou para: {url_depois}")
        print(f"   header 'Visualizar registro': {tem_header_visualizar}")
        print(f"   inputs disabled: {tem_inputs_disabled}")
        if tem_header_visualizar or tem_inputs_disabled > 0:
            return True, f"Form visualizar abriu na mesma aba. URL={url_depois}, header={tem_header_visualizar}, disabled={tem_inputs_disabled}"
        else:
            return False, f"Navegou para URL inesperada sem form visualizar: {url_depois}"
    else:
        # URL igual, sem nova aba = bug ainda presente
        texto_curto = page.inner_text("body")[:200]
        print(f"   SEM ACAO — permaneceu na lista")
        return False, f"Bug ainda presente: Visualizar nao executou acao (URL={url_depois}, permaneceu na lista)"


def main():
    print("=== Re-check QA 1.8 — Bug Visualizar (2026-06-24) ===")
    print(f"Pasta evidencias: {PASTA}")

    with tw.sync_playwright() as p:
        # --- Teste como ALUNO (Externo+Pendente) ---
        print("\n=== ALUNO: Externo+Pendente ===")
        browser_a, ctx_a, page_a = tw.nova_pagina(p)
        page_a.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        page_a.fill("#user_email", ALUNO_EMAIL)
        page_a.fill("#user_password", ALUNO_PASSWORD)
        page_a.click("#user_submit")
        try:
            page_a.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass
        page_a.wait_for_timeout(2000)
        tw.dispensar_nps(page_a)
        page_a.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
                    wait_until="domcontentloaded", timeout=25000)
        page_a.wait_for_timeout(3000)

        passou_aluno, desc_aluno = testar_visualizar_via_teclado(page_a, "ALUNO", "aluno_ext_pend")
        results["aluno_ext_pend"] = (passou_aluno, desc_aluno)
        browser_a.close()

        # --- Teste como ADMIN (lista de registros) ---
        print("\n=== ADMIN: Tabela de Registros ===")
        browser_adm, ctx_adm, page_adm = tw.nova_pagina(p)
        tw.login(page_adm, c_admin, admin=True)

        # Admin: acessar registros com wait mais longo (headed nao necessario em recheck rapido)
        page_adm.goto(f"{BASE_URL}/o/{ORG_ID}/records",
                      wait_until="domcontentloaded", timeout=30000)
        print("   Aguardando tabela admin renderizar (max 35s)...")
        try:
            page_adm.wait_for_function(
                "() => document.querySelectorAll('tbody tr').length > 0",
                timeout=35000
            )
            page_adm.wait_for_timeout(2000)
        except Exception as e:
            print(f"   Tabela admin nao renderizou em 35s: {e}")
            snap(page_adm, "admin_sem_tabela", full=True)
            results["admin"] = (False, "Tabela admin nao renderizou em headless (gotcha conhecido)")
            browser_adm.close()
        else:
            passou_admin, desc_admin = testar_visualizar_via_teclado(page_adm, "ADMIN", "admin_reg")
            results["admin"] = (passou_admin, desc_admin)
            browser_adm.close()

    # --- Sumario ---
    print("\n\n=== SUMARIO RE-CHECK ===")
    for chave, (passou, desc) in results.items():
        emoji = "PASSOU" if passou else "FALHOU"
        print(f"   [{emoji}] {chave}: {desc}")

    # Verificar se o bug foi corrigido
    todos_passaram = all(passou for passou, _ in results.values())
    algum_passou = any(passou for passou, _ in results.values())

    if todos_passaram:
        print("\n   CONCLUSAO: Bug CORRIGIDO em todos os cenarios testados")
    elif algum_passou:
        print("\n   CONCLUSAO: Bug PARCIALMENTE corrigido (algum cenario passa, outro falha)")
    else:
        print("\n   CONCLUSAO: Bug AINDA PRESENTE em todos os cenarios testados")

    return results


if __name__ == "__main__":
    main()
