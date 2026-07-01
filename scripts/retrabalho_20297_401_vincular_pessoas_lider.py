# -*- coding: utf-8 -*-
"""Retrabalho Artia 20297 — validar fix do 401 no modal "Vincular pessoas"
para o perfil Gestor de turma (Líder), em /records/new.

Bug original (card 19893 / laudo QA1.6 TC3): líder abre /records/new, clica
"Adicionar pessoas", modal "Vincular pessoas" abre com "Nenhum item
encontrado" + toast 401. Endpoints 401 confirmados:
  - GET /api/v1/o/37079/professionals
  - GET /api/v1/o/37079/professionals/results_for_filter
  - GET /api/v1/o/37079/event_sources/get_provider_names

PR de correção: https://github.com/Twygo/twyg-app/pull/10868/

Critério: PASSOU somente se NENHUM dos 3 endpoints voltar 401 no clique real
do app E o modal listar liderados (RN 93). Testa 2 líderes conhecidos do
ambiente REGISTROSF2 para cobertura multiusuário (regra anti-falso-negativo).
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

# REGISTROSF2 no .env usa sufixo _ADMIN_EMAIL/_ADMIN_PASSWORD (não _EMAIL/_SENHA
# como o cfg() genérico espera) — lê direto do ambiente (dotenv já carregado por _twygo).
BASE_URL = os.environ["REGISTROSF2_BASE_URL"].rstrip("/")
ORG_ID = os.environ["REGISTROSF2_ORG_ID"]

# Líder da evidência original do bug (card 19893 / TC3) — hardcoded conforme
# instrução do card 20297 (não está no .env como var própria).
LIDERES = [
    {"nome": "qalider (evidência original do bug)", "email": "qalider@teste.com", "senha": "123456"},
    {"nome": "qaliderpuro (segundo líder, cobertura multiusuário)", "email": "qaliderpuro@teste.com", "senha": "123456"},
]

ENDPOINTS_ALVO = [
    re.compile(r"/api/v1/o/\d+/professionals/results_for_filter"),
    re.compile(r"/api/v1/o/\d+/professionals(?:\?|$)"),
    re.compile(r"/api/v1/o/\d+/event_sources/get_provider_names"),
]

PASTA = tw.ROOT / "evidencias" / "retrabalho-20297"
PASTA.mkdir(parents=True, exist_ok=True)
log = lambda *a: print(*a, flush=True)

resultados = {}


def nome_endpoint(url: str) -> str:
    for rgx, nome in [
        (ENDPOINTS_ALVO[0], "professionals/results_for_filter"),
        (ENDPOINTS_ALVO[1], "professionals"),
        (ENDPOINTS_ALVO[2], "event_sources/get_provider_names"),
    ]:
        if rgx.search(url):
            return nome
    return None


def testar_lider(p, lider: dict, slug: str):
    log("=" * 60)
    log(f"Testando lider: {lider['nome']} <{lider['email']}>")
    log("=" * 60)

    capturas = []

    browser, ctx, page = tw.nova_pagina(p, slow_mo=500)

    def on_response(resp):
        nome = nome_endpoint(resp.url)
        if nome:
            capturas.append({"endpoint": nome, "url": resp.url, "status": resp.status})
            log(f"  [network] {nome} -> HTTP {resp.status}  ({resp.url})")

    page.on("response", on_response)

    # Login SEM switch admin — precisa continuar como perfil "Gestor de turma".
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", lider["email"])
    page.fill("#user_password", lider["senha"])
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(1500)
    tw.dispensar_nps(page)

    if "/users/login" in page.url or page.url.rstrip("/").endswith("/login"):
        log(f"  [ERRO] login falhou para {lider['email']} — url atual: {page.url}")
        resultados[slug] = {"status": "LOGIN_FALHOU", "url": page.url}
        ctx.close(); browser.close()
        return

    log(f"  Login OK. URL pos-login: {page.url}")

    page.goto(f"{BASE_URL}/o/{ORG_ID}/records/new", wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    tw.snap(page, PASTA, f"{slug}_01_form")

    if "/records/new" not in page.url:
        log(f"  [AVISO] nao chegou em /records/new — url atual: {page.url}")
        resultados[slug] = {"status": "NAO_CHEGOU_NO_FORM", "url": page.url}
        ctx.close(); browser.close()
        return

    # Clicar em "Adicionar pessoas"
    campo = page.get_by_text("Adicionar pessoas", exact=False).first
    clicou = False
    try:
        campo.click(timeout=5000)
        clicou = True
    except Exception as e:
        log(f"  [AVISO] click direto falhou: {e}")
        try:
            page.evaluate(
                """() => {
                    const el = [...document.querySelectorAll('*')].find(e =>
                        e.children.length === 0 && (e.innerText || '').trim() === 'Adicionar pessoas');
                    if (el) { el.click(); return true; }
                    return false;
                }"""
            )
            clicou = True
        except Exception as e2:
            log(f"  [ERRO] click via JS tambem falhou: {e2}")

    page.wait_for_timeout(3000)
    tw.snap(page, PASTA, f"{slug}_02_modal_apos_click")

    # Ler conteúdo do modal
    modal_texto = page.evaluate(
        """() => {
            const dialog = document.querySelector('[role=dialog], .chakra-modal__content');
            return dialog ? dialog.innerText : '';
        }"""
    )
    nenhum_item = bool(modal_texto and re.search(r"nenhum item encontrado", modal_texto, re.I))
    log(f"  Modal contém 'Nenhum item encontrado': {nenhum_item}")

    # Tentar contar pessoas listadas (checkboxes/itens de lista dentro do modal)
    n_pessoas = page.evaluate(
        """() => {
            const dialog = document.querySelector('[role=dialog], .chakra-modal__content');
            if (!dialog) return -1;
            const checks = dialog.querySelectorAll('input[type=checkbox]');
            return checks.length;
        }"""
    )
    log(f"  Checkboxes de pessoas no modal: {n_pessoas}")

    resultados[slug] = {
        "status": "OK" if clicou else "CLICK_FALHOU",
        "clicou": clicou,
        "modal_nenhum_item": nenhum_item,
        "n_pessoas_checkbox": n_pessoas,
        "capturas_network": capturas,
        "modal_texto_preview": (modal_texto or "")[:300],
    }

    ctx.close(); browser.close()


with tw.sync_playwright() as p:
    for i, lider in enumerate(LIDERES):
        slug = f"lider{i+1}_{lider['email'].split('@')[0]}"
        try:
            testar_lider(p, lider, slug)
        except Exception as e:
            log(f"  [EXCEPTION] {lider['email']}: {e}")
            resultados[slug] = {"status": "EXCEPTION", "erro": str(e)}

log("\n" + "=" * 60)
log("RESUMO")
log("=" * 60)
log(json.dumps(resultados, ensure_ascii=False, indent=2))

with open(PASTA / "resultado.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)
log(f"\nResultado salvo em {PASTA / 'resultado.json'}")
