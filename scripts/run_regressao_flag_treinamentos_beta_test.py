# -*- coding: utf-8 -*-
"""
Checagem exploratória de regressão — Registros F2 (org 37079)

Contexto: feature flag ANTIGA "treinamentos_beta_test" foi DESABILITADA na
org 37079 (a flag NOVA e vigente para Registros é "registros_de_avaliação").
Este script não valida um retrabalho específico — verifica se os fluxos
centrais de Registros continuam funcionando após o toggle.

Cobre (perfis admin e aluno):
  1. Listagem de Registros carrega (sem 404/tela branca/erro).
  2. Linhas/colunas da tabela renderizam com dados.
  3. Kebab (3 pontos) abre com os itens esperados.
  4. "Visualizar" (mouse) abre a tela de visualização.
  5. "Editar" (mouse) abre o formulário de edição.
  6. Botão de criar novo registro (se existir) abre o fluxo de criação.
  7. Captura de erros de Console e respostas HTTP 4xx/5xx via listeners de
     Network/Console durante toda a sessão (regra do monorepo: diagnosticar
     via Network+Console antes de concluir).
  8. Tenta localizar na UI (menu de configurações/organização) alguma
     referência a "registros_de_avaliação" — best-effort, não crítico.

Rodar (headless por padrão):
    .\.venv\Scripts\python.exe scripts\run_regressao_flag_treinamentos_beta_test.py
Rodar com janela (debug visual):
    set TW_HEADED=1 && .\.venv\Scripts\python.exe scripts\run_regressao_flag_treinamentos_beta_test.py
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = os.environ.get("REGISTROSF2_BASE_URL", "https://registrosf2.stage.twygoead.com").rstrip("/")
ORG_ID = os.environ.get("REGISTROSF2_ORG_ID", "37079")

ADMIN_EMAIL = os.environ["REGISTROSF2_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["REGISTROSF2_ADMIN_PASSWORD"]
ALUNO_EMAIL = os.environ.get("REGISTROSF2_ALUNO_EMAIL")
ALUNO_PASSWORD = os.environ.get("REGISTROSF2_ALUNO_PASSWORD")

PASTA = tw.ROOT / "evidencias" / "registros-f2-flag-treinamentos-beta-test"
PASTA.mkdir(parents=True, exist_ok=True)

resultados: dict = {}
log = lambda *a: print(*a, flush=True)


def snap(page, nome, full=False):
    fp = PASTA / f"{nome}.png"
    try:
        page.screenshot(path=str(fp), full_page=full)
        log(f"   [snap] {fp.name}")
    except Exception as e:
        log(f"   [snap] FALHOU {nome}: {e}")
    return fp


def instalar_listeners(page, bucket_key):
    """Registra listeners de console/network. Acumula em resultados[bucket_key]."""
    resultados.setdefault(bucket_key, {})
    erros_console = []
    erros_rede = []

    def on_console(msg):
        if msg.type in ("error", "warning"):
            erros_console.append({"type": msg.type, "text": msg.text[:300]})

    def on_response(resp):
        try:
            if resp.status >= 400:
                erros_rede.append({"status": resp.status, "url": resp.url[:200]})
        except Exception:
            pass

    page.on("console", on_console)
    page.on("response", on_response)
    resultados[bucket_key]["_erros_console"] = erros_console
    resultados[bucket_key]["_erros_rede"] = erros_rede
    return erros_console, erros_rede


def dispensar_overlays(page):
    tw.dispensar_nps(page)
    try:
        page.evaluate("""() => {
            document.querySelectorAll(
                '#hubspot-messages-iframe-container,[id*=sophia]'
            ).forEach(e => e.style.display='none');
        }""")
    except Exception:
        pass


def ir_records(page):
    """Visão do COLABORADOR ('Meu histórico') — usada no baseline t20333.
    Kebab aqui só tem Visualizar/Evidências (sem Editar/Adicionar de gestão)."""
    page.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
              wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_function(
            "() => document.querySelectorAll('tbody tr').length > 0", timeout=25000
        )
    except Exception:
        pass
    page.wait_for_timeout(2000)
    dispensar_overlays(page)


def ir_records_admin(page):
    """Visão de GESTÃO (Aprendizagem > Registros, sidebar admin) — onde vivem
    Editar e o fluxo de criação de registro. Rota sem in_use_mode_layout."""
    page.goto(f"{BASE_URL}/o/{ORG_ID}/records?tab=learning-records-tab",
              wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_function(
            "() => document.querySelectorAll('tbody tr').length > 0", timeout=25000
        )
    except Exception:
        pass
    page.wait_for_timeout(2000)
    dispensar_overlays(page)


def status_pagina(page):
    """Detecta 404/tela branca/erro genérico via texto visível + status implícito."""
    try:
        body = page.inner_text("body")
    except Exception:
        body = ""
    corpo_vazio = len(body.strip()) < 20
    tem_erro_texto = bool(re.search(r"\b404\b|p[aá]gina n[ãa]o encontrada|erro interno|something went wrong|internal server error", body, re.I))
    return {"corpo_vazio": corpo_vazio, "tem_erro_texto": tem_erro_texto, "snippet": body[:200]}


def abrir_kebab_linha(page, idx=0):
    rows = page.locator("tbody tr")
    if rows.count() <= idx:
        return False
    row = rows.nth(idx)
    kebab = row.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
    if kebab.count() == 0:
        return False
    kebab.click(timeout=5000, force=True)
    page.wait_for_timeout(1200)
    return True


def menu_itens_ordem(page):
    return page.evaluate("""() => {
        const lists = Array.from(document.querySelectorAll('ul[class*="menu__menu-list"], [role=menu]'));
        const visivel = lists.find(l => {
            const r = l.getBoundingClientRect();
            const cs = getComputedStyle(l);
            return r.width > 0 && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.5;
        });
        if (!visivel) return [];
        const btns = Array.from(visivel.querySelectorAll('[role="menuitem"]'));
        return btns.map((btn, i) => ({
            index: i,
            text: (btn.innerText || '').replace(/\\s+/g,' ').trim(),
        }));
    }""")


def clicar_item_menu(page, texto_regex):
    """Usa tw.click_menuitem (resolve pelo id do menu VISÍVEL) — evita acertar
    um menuitem de linha oculta/stale, já que o Chakra monta todos os menus
    da tabela no DOM simultaneamente."""
    itens = menu_itens_ordem(page)
    ok = tw.click_menuitem(page, texto_regex)
    return ok, itens


def testar_abertura(page, ctx, pages_antes, palavra_chave_regex, timeout_ms=3000):
    page.wait_for_timeout(timeout_ms)
    pages_depois = len(ctx.pages)
    if pages_depois > pages_antes:
        nova = ctx.pages[-1]
        try:
            nova.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            pass
        nova.wait_for_timeout(1500)
        body = nova.inner_text("body")
        achou = bool(re.search(palavra_chave_regex, body, re.I)) or bool(re.search(palavra_chave_regex, nova.url, re.I))
        return {"achou": achou, "onde": "nova_aba", "url": nova.url, "snippet": body[:200], "page_ref": nova}
    url = page.url
    body = page.inner_text("body")
    achou = bool(re.search(palavra_chave_regex, body, re.I)) or bool(re.search(palavra_chave_regex, url, re.I))
    return {"achou": achou, "onde": "mesma_aba", "url": url, "snippet": body[:200], "page_ref": page}


def rodar_perfil_admin(page, ctx, label):
    out = {}

    log(f"\n--- {label}: abrindo listagem de Registros ---")
    ir_records(page)
    status = status_pagina(page)
    out["listagem_status"] = status
    n_linhas = page.locator("tbody tr").count()
    out["n_linhas"] = n_linhas
    log(f"   corpo_vazio={status['corpo_vazio']} tem_erro_texto={status['tem_erro_texto']} n_linhas={n_linhas}")
    snap(page, f"{label}_00_lista", full=True)

    # Colunas do cabeçalho
    heads = page.evaluate("() => Array.from(document.querySelectorAll('thead th,thead td')).map(h=>(h.innerText||'').trim())")
    out["colunas"] = heads
    log(f"   colunas={heads}")

    # 1) kebab abre com itens esperados
    log(f"\n--- {label}: abrindo kebab da linha 0 ---")
    kebab_ok = abrir_kebab_linha(page, 0)
    itens = menu_itens_ordem(page) if kebab_ok else []
    out["kebab"] = {"abriu": kebab_ok, "itens": itens}
    log(f"   kebab_abriu={kebab_ok} itens={[it['text'] for it in itens]}")
    snap(page, f"{label}_01_kebab_aberto")

    # 2) Visualizar via mouse
    if kebab_ok:
        log(f"\n--- {label}: clicando 'Visualizar' ---")
        pages_antes = len(ctx.pages)
        clicou, _ = clicar_item_menu(page, r"isual")
        resultado = testar_abertura(page, ctx, pages_antes, r"visualizar registro|mode=view") if clicou else {"achou": False, "onde": None, "url": page.url, "page_ref": page}
        nova_page = resultado.pop("page_ref")
        out["visualizar"] = {"clicou": clicou, **resultado}
        log(f"   clicou={clicou} abriu={resultado['achou']} onde={resultado['onde']} url={resultado['url'][:100]}")
        snap(nova_page, f"{label}_02_visualizar", full=True)
        if nova_page is not page:
            nova_page.close()
        else:
            ir_records(page)
    else:
        out["visualizar"] = {"clicou": False, "motivo": "kebab não abriu"}

    # 3) Visão de GESTÃO (Aprendizagem > Registros) — onde vivem Editar e Adicionar
    log(f"\n--- {label}: abrindo visão de GESTÃO (Aprendizagem > Registros) ---")
    ir_records_admin(page)
    status_admin = status_pagina(page)
    n_linhas_admin = page.locator("tbody tr").count()
    out["listagem_admin_status"] = status_admin
    out["n_linhas_admin"] = n_linhas_admin
    log(f"   corpo_vazio={status_admin['corpo_vazio']} tem_erro_texto={status_admin['tem_erro_texto']} n_linhas={n_linhas_admin}")
    snap(page, f"{label}_03a_lista_gestao", full=True)

    # 3a) Editar via mouse (kebab da visão de gestão)
    log(f"\n--- {label}: abrindo kebab (gestão) p/ Editar ---")
    kebab_ok2 = abrir_kebab_linha(page, 0)
    itens_gestao = menu_itens_ordem(page) if kebab_ok2 else []
    out["kebab_gestao"] = {"abriu": kebab_ok2, "itens": itens_gestao}
    log(f"   kebab_abriu={kebab_ok2} itens={[it['text'] for it in itens_gestao]}")
    snap(page, f"{label}_03b_kebab_gestao_aberto")
    if kebab_ok2:
        pages_antes = len(ctx.pages)
        clicou, _ = clicar_item_menu(page, r"editar")
        resultado = testar_abertura(page, ctx, pages_antes, r"editar registro|mode=edit|formul[áa]rio") if clicou else {"achou": False, "onde": None, "url": page.url, "page_ref": page}
        nova_page = resultado.pop("page_ref")
        out["editar"] = {"clicou": clicou, **resultado}
        log(f"   clicou={clicou} abriu={resultado['achou']} onde={resultado['onde']} url={resultado['url'][:100]}")
        snap(nova_page, f"{label}_03c_editar", full=True)
        if nova_page is not page:
            nova_page.close()
        else:
            ir_records_admin(page)
    else:
        out["editar"] = {"clicou": False, "motivo": "kebab (gestão) não abriu"}

    # 4) Botão de criar novo registro ("+ Adicionar", visível na lista)
    log(f"\n--- {label}: procurando botão de criar novo registro ('Adicionar') ---")
    btn_novo = page.get_by_role("button", name=re.compile(r"\+?\s*adicionar", re.I)).first
    tem_botao = btn_novo.count() > 0
    out["criar_novo"] = {"tem_botao": tem_botao}
    if tem_botao:
        pages_antes = len(ctx.pages)
        try:
            btn_novo.click(timeout=4000)
            resultado = testar_abertura(page, ctx, pages_antes, r"novo registro|adicionar registro|mode=new|formul[áa]rio|records/new")
            nova_page = resultado.pop("page_ref")
            out["criar_novo"].update(resultado)
            log(f"   tem_botao=True abriu={resultado['achou']} onde={resultado['onde']} url={resultado['url'][:100]}")
            snap(nova_page, f"{label}_04_criar_novo", full=True)
            if nova_page is not page:
                nova_page.close()
            else:
                ir_records_admin(page)
        except Exception as e:
            out["criar_novo"]["erro"] = str(e)
            log(f"   tem_botao=True mas clique falhou: {e}")
    else:
        log("   botão 'Adicionar' NÃO encontrado nesta visão (gestão)")

    return out


def rodar_perfil_aluno(page, ctx, label):
    out = {}
    log(f"\n--- {label}: verificando acesso a Registros ---")
    page.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
              wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2500)
    dispensar_overlays(page)
    status = status_pagina(page)
    url_final = page.url
    out["status"] = status
    out["url_final"] = url_final
    log(f"   url_final={url_final} corpo_vazio={status['corpo_vazio']} tem_erro_texto={status['tem_erro_texto']}")
    snap(page, f"{label}_00_tentativa_acesso", full=True)
    return out


def buscar_referencia_flag_nova(page):
    """Best-effort: procura por 'registros_de_avaliação' em telas de config/org."""
    achados = []
    candidatos = [
        f"{BASE_URL}/o/{ORG_ID}/settings",
        f"{BASE_URL}/o/{ORG_ID}/organizations/edit",
    ]
    for url in candidatos:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(1500)
            body = page.inner_text("body")
            if re.search(r"registros?[\s_]*de[\s_]*avalia", body, re.I):
                achados.append({"url": url, "achou": True})
            else:
                achados.append({"url": url, "achou": False})
        except Exception as e:
            achados.append({"url": url, "erro": str(e)})
    return achados


def main():
    log("=== Regressão pós-toggle flag 'treinamentos_beta_test' (org 37079) ===\n")

    with tw.sync_playwright() as p:
        # ── ADMIN ──────────────────────────────────────────────
        log("=== PERFIL: ADMIN ===")
        b_adm, c_adm, page_adm = tw.nova_pagina(p)
        erros_console_adm, erros_rede_adm = instalar_listeners(page_adm, "admin")
        tw.login(page_adm, {
            "base_url": BASE_URL, "org_id": ORG_ID,
            "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD,
        }, admin=True)
        log(f"  [admin] logado OK url={page_adm.url}")
        resultados["admin"].update(rodar_perfil_admin(page_adm, c_adm, "admin"))

        # Snapshot dos erros de rede/console ATÉ AQUI — a busca best-effort da
        # flag nova abaixo usa URLs "chutadas" (/settings, /organizations/edit)
        # que podem 404 legitimamente sem relação com Registros. Não deixar
        # isso contaminar o sinal principal (regressão de Registros).
        resultados["admin"]["_erros_rede_core"] = list(resultados["admin"]["_erros_rede"])
        resultados["admin"]["_erros_console_core"] = list(resultados["admin"]["_erros_console"])

        log("\n--- ADMIN: procurando referência à flag nova 'registros_de_avaliação' (best-effort, página separada) ---")
        page_flag = c_adm.new_page()
        resultados["admin"]["busca_flag_nova"] = buscar_referencia_flag_nova(page_flag)
        page_flag.close()

        b_adm.close()

        # ── ALUNO ──────────────────────────────────────────────
        if ALUNO_EMAIL and ALUNO_PASSWORD:
            log("\n=== PERFIL: ALUNO ===")
            b_alu, c_alu, page_alu = tw.nova_pagina(p)
            erros_console_alu, erros_rede_alu = instalar_listeners(page_alu, "aluno")
            page_alu.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
            page_alu.fill("#user_email", ALUNO_EMAIL)
            page_alu.fill("#user_password", ALUNO_PASSWORD)
            page_alu.click("#user_submit")
            try:
                page_alu.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            page_alu.wait_for_timeout(2000)
            dispensar_overlays(page_alu)
            log(f"  [aluno] logado OK url={page_alu.url}")
            resultados["aluno"].update(rodar_perfil_aluno(page_alu, c_alu, "aluno"))
            b_alu.close()
        else:
            log("\n[aluno] REGISTROSF2_ALUNO_EMAIL/PASSWORD ausentes no .env — pulando perfil aluno")
            resultados["aluno_pulado"] = True

    # ── SUMÁRIO ────────────────────────────────────────────────
    log("\n" + "=" * 70)
    log("SUMÁRIO — Regressão flag treinamentos_beta_test (org 37079)")
    log("=" * 70)
    for perfil in ("admin", "aluno"):
        dados = resultados.get(perfil)
        if not dados:
            continue
        log(f"\n[{perfil.upper()}]")
        for chave, r in dados.items():
            if chave.startswith("_"):
                continue
            log(f"   {chave}: {r}")
        erros_rede = dados.get("_erros_rede_core", dados.get("_erros_rede", []))
        erros_console = dados.get("_erros_console_core", dados.get("_erros_console", []))
        log(f"   >> erros_rede CORE(4xx/5xx, so fluxos de Registros)={len(erros_rede)} {erros_rede if erros_rede else ''}")
        log(f"   >> erros_console CORE={len(erros_console)} {erros_console[:5] if erros_console else ''}")

    out_path = PASTA / "resultados.json"
    def _default(o):
        return str(o)
    out_path.write_text(json.dumps(resultados, ensure_ascii=False, indent=2, default=_default), encoding="utf-8")
    log(f"\n[saida] {out_path}")


if __name__ == "__main__":
    main()
