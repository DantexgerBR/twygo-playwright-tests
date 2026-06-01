r"""Retrabalho — cards de atividade tipo Página na aba Design cortam texto.

Bug original (do Artia):
    Em cards de atividade do tipo Página na aba de Design de um modelo, foi
    observado que não exibe o texto centralizado e corta parte do texto no card.

Reprodução:
» Editar modelo
» Design
» Editar Página
» Inserir texto
» Visualizar card em aba Design

Comportamento esperado:
    Apresentar texto centralizado possibilitando a visualização sem cortar o texto.

Como rodar:
    .\.venv\Scripts\python.exe scripts/retrabalho_cards_design.py

Saída:
    Vários screenshots em evidencias/retrabalho-cards-design/ pra análise.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

BASE_URL = (os.environ.get("BASE_URL", "") or "").rstrip("/")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
ORG_ID = os.environ.get("ORG_ID", "")

PASTA_EVIDENCIAS = ROOT / "evidencias" / "retrabalho-cards-design"
PASTA_EVIDENCIAS.mkdir(parents=True, exist_ok=True)


def snap(page, nome: str) -> Path:
    """Tira screenshot e devolve o path."""
    p = PASTA_EVIDENCIAS / f"{nome}.png"
    page.screenshot(path=str(p), full_page=False)
    print(f"  [snap] {p.name}")
    return p


def main() -> None:
    if not (BASE_URL and ADMIN_EMAIL and ADMIN_PASSWORD and ORG_ID):
        raise SystemExit("Faltam vars no .env: BASE_URL, ADMIN_EMAIL, ADMIN_PASSWORD, ORG_ID")

    print(f"BASE_URL={BASE_URL}")
    print(f"ORG_ID={ORG_ID}")
    print(f"Admin={ADMIN_EMAIL}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="pt-BR",
        )
        page = context.new_page()

        # 1. Login
        print("\n[1] Login…")
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
        page.fill("#user_email", ADMIN_EMAIL)
        page.fill("#user_password", ADMIN_PASSWORD)
        page.click("#user_submit")
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        print(f"  URL pos-login: {page.url}")
        snap(page, "01-pos-login")

        # 2. Trocar pra perfil admin
        print("\n[2] Mudando pra perfil admin…")
        admin_url = f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin"
        page.goto(admin_url, wait_until="domcontentloaded", timeout=30000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(3000)
        print(f"  URL admin: {page.url}")
        snap(page, "02-admin-dashboard")

        # 3. Procurar item "Modelos de conteúdo" na sidebar e navegar via href direto
        # (click tradicional trava por causa do widget de chat sobre o link).
        print("\n[3] Procurando link 'Modelos de conteudo' na sidebar...")
        encontrou_modelos = False
        href_modelos = page.evaluate(
            """() => {
                const links = Array.from(document.querySelectorAll('a'));
                const m = links.find(a => /modelos\\s+de\\s+conte[uú]do/i.test((a.innerText || '').trim()));
                return m ? m.href : null;
            }"""
        )
        if href_modelos:
            print(f"  href encontrado: {href_modelos}")
            page.goto(href_modelos, wait_until="domcontentloaded", timeout=30000)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(3000)
            encontrou_modelos = True
            print(f"  navegou OK. URL atual: {page.url}")
        else:
            print("  href de 'Modelos de conteudo' nao encontrado no DOM")

        if not encontrou_modelos:
            print("\n" + "=" * 60)
            print("FEATURE FLAG NÃO HABILITADA")
            print("=" * 60)
            print("O item 'Modelos' não aparece na sidebar do admin.")
            print("Isso significa que a feature flag de Modelos de Conteúdo")
            print("não está ativada nesta org (36675).")
            print()
            print("Próximos passos:")
            print("  1. Acesse o painel de admin manualmente")
            print("  2. Habilite a feature flag de Modelos de Conteúdo")
            print("  3. Avise pra rodar este script novamente")
            print("=" * 60)
            snap(page, "FAIL-feature-flag-modelos-desabilitada")
            page.wait_for_timeout(2000)
            context.close()
            browser.close()
            return

        if encontrou_modelos:
            # Espera até a listagem terminar de carregar — ou o texto "Não há dados"
            # aparece, ou itens de modelo aparecem. Sai do polling em até 15s.
            print("  Aguardando listagem carregar (sai do spinner)...")
            listagem_vazia = False
            tem_modelos = False
            for tentativa in range(30):  # 30 * 500ms = 15s
                page.wait_for_timeout(500)
                try:
                    body_txt = page.locator("body").inner_text(timeout=2000).lower()
                except Exception:
                    continue
                if "não há dados para exibir" in body_txt or "nao ha dados" in body_txt:
                    listagem_vazia = True
                    print(f"  [t={tentativa*0.5:.1f}s] listagem confirmada VAZIA")
                    break
                # Detecta se já tem cards/itens de modelo — procura links pra /content_models/<id>
                hrefs = page.evaluate(
                    "() => Array.from(document.querySelectorAll('a')).map(a => a.href)"
                    ".filter(h => /\\/content_models\\/\\d+/.test(h))"
                )
                if hrefs:
                    tem_modelos = True
                    print(f"  [t={tentativa*0.5:.1f}s] listagem tem {len(hrefs)} modelo(s)")
                    break
            else:
                print("  [aviso] listagem nao confirmou vazia nem com itens em 15s — assumindo vazia")
                listagem_vazia = True

            snap(page, "03-listagem-modelos")

            # 4. Se vazio, criar modelo de teste; se tem modelos, abrir o primeiro
            abriu_modelo = False
            if listagem_vazia:
                print("\n[4] Listagem vazia. Criando modelo de teste...")

                # Pega o próximo nome disponível (teste, teste1, teste2, ...)
                nome_modelo = "teste"
                print(f"  Nome do modelo a criar: '{nome_modelo}'")

                # Clica no botão "+ Adicionar"
                botao_add = page.locator("button:has-text('Adicionar'), a:has-text('Adicionar')").first
                botao_add.click(timeout=5000)
                page.wait_for_timeout(2000)
                snap(page, "04a-pos-clicar-adicionar")
                print(f"  Cliquei em '+ Adicionar'. URL: {page.url}")

                # Preenche Nome (usa placeholder pra evitar pegar input hidden do chat)
                print(f"  Preenchendo Nome='{nome_modelo}'...")
                preencheu_nome = False
                for sel in [
                    "input[placeholder*='Modelo padrão']",
                    "input[placeholder*='Modelo padrao']",
                    "input[name*='name']",
                    "input[name*='nome']",
                    "label:has-text('Nome') ~ * input",
                    "label:has-text('Nome') >> .. >> input",
                ]:
                    try:
                        loc = page.locator(sel).first
                        if loc.is_visible(timeout=1500):
                            loc.fill(nome_modelo, timeout=5000)
                            preencheu_nome = True
                            print(f"    Preencheu via: {sel}")
                            break
                    except Exception:
                        continue
                if not preencheu_nome:
                    print("    FAIL preencher Nome — capturando estado pra debug")
                    snap(page, "04-fail-preencher-nome")
                    raise SystemExit("Não consegui localizar o campo Nome")
                page.wait_for_timeout(800)

                # Tenta selecionar primeiro Kit de marca
                print("  Selecionando Kit de marca (primeira opcao disponivel)...")
                try:
                    dropdown_kit = page.locator("text=Selecione um kit de marca").first
                    dropdown_kit.click(timeout=5000)
                    page.wait_for_timeout(1500)
                    snap(page, "04b-dropdown-kit-aberto")
                    # Clica na primeira opção do dropdown
                    primeira_opcao = page.locator("[role='option'], li[data-value], .dropdown-item").first
                    primeira_opcao.click(timeout=5000)
                    page.wait_for_timeout(1000)
                    print("  Kit de marca selecionado.")
                except Exception as e:
                    print(f"  Falha no Kit de marca: {type(e).__name__}: {str(e)[:120]}")
                    snap(page, "04b-falha-kit-marca")

                # Rola pra baixo pra ver o resto do form (deve ter botão Salvar/Próximo)
                page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)
                snap(page, "04c-formulario-rolado")
                print(f"  Capturei formulario rolado. URL: {page.url}")
                print("  [PARANDO pra inspecionar antes de salvar]")
            else:
                print("\n[4] Abrindo o primeiro modelo da listagem...")
                for seletor in [
                    "[aria-label='Editar']",
                    "a[title='Editar']",
                    ".edit, .editar",
                    "button:has-text('Editar')",
                    "a:has-text('Editar')",
                ]:
                    try:
                        first = page.locator(seletor).first
                        if first.is_visible(timeout=2000):
                            first.click()
                            abriu_modelo = True
                            print(f"  cliquei via: {seletor}")
                            break
                    except Exception:
                        continue
                if not abriu_modelo:
                    try:
                        page.locator("table a, .list a, .card a, [role='link']").first.click(timeout=3000)
                        abriu_modelo = True
                        print("  cliquei via primeiro link da listagem")
                    except Exception:
                        print("  FAIL Não consegui abrir nenhum modelo")
        else:
            print("  FAIL Não achei 'Modelos' nem expandindo menus.")
            abriu_modelo = False

        if abriu_modelo:
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(3000)
            print(f"  URL modelo: {page.url}")
            snap(page, "04-editar-modelo")

            # 5. Clicar na aba "Design"
            print("\n[5] Clicando aba 'Design'…")
            try:
                page.locator("text=Design").first.click(timeout=5000)
                page.wait_for_timeout(3000)
                snap(page, "05-aba-design")
                print(f"  URL aba Design: {page.url}")
            except Exception as e:
                print(f"  FAIL Falhou clicar Design: {e}")

        print("\n[FIM] Screenshots salvos em:")
        print(f"  {PASTA_EVIDENCIAS}")
        for p in sorted(PASTA_EVIDENCIAS.glob("*.png")):
            print(f"    - {p.name}")

        page.wait_for_timeout(2000)
        context.close()
        browser.close()


if __name__ == "__main__":
    main()
