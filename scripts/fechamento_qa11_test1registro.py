"""Test: criar 1 registro com debug detalhado para entender falha do seed."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ADMIN_EMAIL = "dante.tavares@twygo.com"
ADMIN_SENHA = "123456"
ORG_ID = "37079"

SLUG = "registros-f2-qa11"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg)


def preencher_creatable(page, input_id, valor):
    try:
        inp = page.locator(f"#{input_id}")
        if inp.count() == 0:
            log(f"  CAMPO NAO ENCONTRADO: #{input_id}")
            return False
        inp.scroll_into_view_if_needed()
        inp.click(timeout=3000)
        page.wait_for_timeout(400)
        inp.fill(valor)
        page.wait_for_timeout(1000)

        opcoes = page.locator("[class*='__option']").all()
        log(f"  #{input_id} '{valor}' — opcoes: {[op.inner_text()[:30] for op in opcoes[:5]]}")

        for op in opcoes:
            try:
                t = op.inner_text().strip()
                if valor.lower() in t.lower() and "Criar" not in t and "criar" not in t:
                    log(f"  Clicando opcao existente: {t!r}")
                    op.click(timeout=3000)
                    page.wait_for_timeout(400)
                    return True
            except Exception:
                pass

        for op in opcoes:
            try:
                t = op.inner_text().strip()
                if re.search(r"criar|create", t, re.I):
                    log(f"  Clicando 'Criar': {t!r}")
                    op.click(timeout=3000)
                    page.wait_for_timeout(400)
                    return True
            except Exception:
                pass

        log(f"  Nenhuma opcao encontrada — pressionando Enter")
        page.keyboard.press("Enter")
        page.wait_for_timeout(400)
        return True
    except Exception as e:
        log(f"  ERRO #{input_id}: {e}")
        return False


def main():
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            # Login como aluno
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("#user_email", timeout=10000)
            page.fill("#user_email", ADMIN_EMAIL)
            page.fill("#user_password", ADMIN_SENHA)
            page.click("#user_submit")
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)
            log(f"Logado: {page.url[:60]}")

            # Form de criacao
            page.goto(
                f"{BASE_URL}/o/{ORG_ID}/records/new?in_use_mode_layout=true",
                wait_until="domcontentloaded", timeout=25000
            )
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(2500)
            tw.dispensar_nps(page)
            log(f"Form carregado: {page.url[:60]}")
            tw.snap(page, EVID, "t1reg_01_inicial")

            # Provedor
            log("\n--- Provedor ---")
            ok_prov = preencher_creatable(page, "react-select-2-input", "Alura")
            tw.snap(page, EVID, "t1reg_02_apos_provedor")

            # Conteudo
            log("\n--- Conteudo ---")
            ok_cont = preencher_creatable(page, "react-select-3-input", "QA11-Debug-Test")
            tw.snap(page, EVID, "t1reg_03_apos_conteudo")

            # Tipo experiencia
            log("\n--- Tipo experiencia ---")
            # Tenta selecionar diretamente sem filtrar
            ok_tipo = False
            try:
                inp = page.locator("#react-select-4-input")
                inp.scroll_into_view_if_needed()
                inp.click(timeout=3000)
                page.wait_for_timeout(600)
                # Sem digitar nada — mostra todas as opcoes
                opcoes_tipo = page.locator("[class*='__option']").all()
                log(f"  Tipo opcoes (sem digitar): {[op.inner_text()[:30] for op in opcoes_tipo[:6]]}")
                if opcoes_tipo:
                    # Tenta achar "Curso"
                    for op in opcoes_tipo:
                        t = op.inner_text().strip()
                        if "curso" in t.lower() or "Curso" in t:
                            op.click(timeout=3000)
                            ok_tipo = True
                            log(f"  Selecionado: {t!r}")
                            break
                    if not ok_tipo:
                        # Digita "Curso" para criar
                        inp.fill("Curso")
                        page.wait_for_timeout(800)
                        opcoes_tipo2 = page.locator("[class*='__option']").all()
                        log(f"  Tipo opcoes (apos 'Curso'): {[op.inner_text()[:30] for op in opcoes_tipo2[:4]]}")
                        if opcoes_tipo2:
                            opcoes_tipo2[0].click(timeout=3000)
                            ok_tipo = True
                            log(f"  Selecionado primeira opcao")
                else:
                    # Cria "Curso"
                    inp.fill("Curso")
                    page.wait_for_timeout(800)
                    page.keyboard.press("Enter")
                    ok_tipo = True
                    log("  Enter para criar 'Curso'")
            except Exception as e:
                log(f"  ERRO tipo: {e}")
            page.wait_for_timeout(300)
            tw.snap(page, EVID, "t1reg_04_apos_tipo")

            # Categorias
            log("\n--- Categorias ---")
            ok_cat = False
            try:
                inp = page.locator("#react-select-5-input")
                inp.scroll_into_view_if_needed()
                inp.click(timeout=3000)
                page.wait_for_timeout(600)
                opcoes_cat = page.locator("[class*='__option']").all()
                log(f"  Cat opcoes: {[op.inner_text()[:40] for op in opcoes_cat[:5]]}")
                if opcoes_cat:
                    opcoes_cat[0].click(timeout=3000)
                    ok_cat = True
                    log(f"  Cat selecionada: primeira opcao")
            except Exception as e:
                log(f"  ERRO cat: {e}")
            page.wait_for_timeout(300)

            # Carga horaria
            log("\n--- Carga horaria ---")
            try:
                carga = page.locator("#workload_seconds")
                carga.scroll_into_view_if_needed()
                carga.fill("10:00:00")
            except Exception as e:
                log(f"  ERRO carga: {e}")

            # Data de termino
            log("\n--- Data de termino ---")
            try:
                dt = page.locator("#endDate")
                dt.scroll_into_view_if_needed()
                dt.fill("2025-01-15")
            except Exception as e:
                log(f"  ERRO data: {e}")

            tw.snap(page, EVID, "t1reg_05_antes_salvar")

            # Salva
            log("\n--- Salvar ---")
            try:
                btn = page.get_by_role("button", name=re.compile(r"^Salvar$|^Enviar para aprovação$", re.I)).first
                if btn.count() == 0:
                    btn = page.locator("button[type='submit']").first
                if btn.count() > 0:
                    log(f"  Botao encontrado: {btn.inner_text()[:30]!r}")
                    btn.scroll_into_view_if_needed()
                    btn.click(timeout=5000)
                    page.wait_for_timeout(3000)
                    tw.dispensar_nps(page)
                    log(f"  URL apos salvar: {page.url[:60]}")
                    tw.snap(page, EVID, "t1reg_06_apos_salvar")

                    # Verifica sucesso
                    if "/records/new" not in page.url and "/records" in page.url:
                        log("  SUCESSO — redirecionou para lista")
                    elif page.get_by_text(re.compile(r"sucesso|adicionado|enviado|criado", re.I)).count() > 0:
                        log("  SUCESSO — toast encontrado")
                    else:
                        log("  FALHOU — sem redirecionamento nem toast")
                        # Captura erros visiveis
                        erros = page.locator("[class*='error'], [class*='invalid'], [class*='alert']").all()
                        for er in erros[:5]:
                            try:
                                log(f"  Erro: {er.inner_text()[:60]!r}")
                            except Exception:
                                pass
                else:
                    log("  Botao salvar NAO encontrado")
                    btns = page.locator("button").all()
                    log(f"  Botoes na pagina: {[b.inner_text()[:20] for b in btns[:10] if b.is_visible()]}")
            except Exception as e:
                log(f"  ERRO salvar: {e}")
                tw.snap(page, EVID, "t1reg_07_erro_salvar")

        finally:
            ctx.close()
            browser.close()

    log("\nDone.")


if __name__ == "__main__":
    main()
