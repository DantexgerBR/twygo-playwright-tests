# -*- coding: utf-8 -*-
"""Gera UM curso pelo 'Assistente de criação' (org 37061) e espera a geração de
conteúdo concluir. Imprime o id do curso pra revisão de qualidade posterior.

Wizard de 6 passos (Dados, Questionário, Identificação, Atividades, Imagem, Áudio);
vários passos disparam sub-geração de IA e só habilitam 'Próximo' ao terminar.

Uso: editar SPEC abaixo (ou passar via env SPEC_IDX para escolher do lote)."""
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

CURSOS = [
    {"slug": "sql", "theme": "Fundamentos de SQL", "audience": "Iniciantes em banco de dados",
     "n": 3, "objective": "Capacitar iniciantes a escrever consultas SQL básicas (SELECT, WHERE, JOIN) e entender modelagem relacional."},
    {"slug": "git", "theme": "Boas práticas de Git", "audience": "Desenvolvedores iniciantes",
     "n": 3, "objective": "Ensinar o fluxo essencial de Git: commits, branches, merge, pull request e resolução de conflitos."},
    {"slug": "nr35", "theme": "NR-35 Trabalho em Altura", "audience": "Trabalhadores da construção civil",
     "n": 3, "objective": "Capacitar trabalhadores nos requisitos da NR-35 para execução segura de trabalho em altura."},
    {"slug": "atendimento", "theme": "Atendimento ao Cliente", "audience": "Equipe de atendimento",
     "n": 3, "objective": "Desenvolver habilidades de atendimento ao cliente com excelência, empatia e resolução de problemas."},
    {"slug": "lideranca", "theme": "Liderança de Equipes", "audience": "Novos gestores",
     "n": 3, "objective": "Preparar novos gestores para liderar equipes com comunicação, feedback e gestão de desempenho."},
]

import os
IDX = int(os.environ.get("SPEC_IDX", "0"))
SPEC = CURSOS[IDX]
PASTA = tw.ROOT / "evidencias" / f"qualidade_ia_{SPEC['slug']}"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'


def esperar_botao(page, padrao_regex, timeout_s=180):
    """Espera um button visível e habilitado cujo texto casa o regex. Retorna o locator ou None."""
    fim = time.time() + timeout_s
    while time.time() < fim:
        btns = page.get_by_role("button", name=re.compile(padrao_regex, re.I))
        for i in range(btns.count()):
            b = btns.nth(i)
            try:
                if b.is_visible() and b.is_enabled():
                    return b
            except Exception:
                pass
        page.wait_for_timeout(2000)
    return None


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    print(f"=== GERANDO CURSO: {SPEC['theme']} (slug={SPEC['slug']}) ===")
    page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/new_with_ai",
              wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)
    page.get_by_text(re.compile(r"Assistente de cria", re.I)).first.click(timeout=10000)
    page.wait_for_timeout(5000)
    tw.dispensar_nps(page)

    # ---- PASSO 1: Dados ----
    page.locator('input[name="theme"]').fill(SPEC["theme"])
    page.locator('input[name="targetAudience"]').fill(SPEC["audience"])
    n = page.locator('input[name="numberOfLessons"]'); n.click(); n.fill(""); n.fill(str(SPEC["n"]))
    for lbl in ["Página", "Aula"]:
        try:
            page.get_by_text(lbl, exact=True).first.click(timeout=2500)
        except Exception:
            pass
    page.locator('textarea[name="objective"]').fill(SPEC["objective"])
    page.wait_for_timeout(600)
    tw.snap(page, PASTA, "01-passo1")

    # ---- percorrer os passos até o disparo ----
    passo = 1
    while passo < 9:
        # botão de disparo final? (no passo Áudio o botão é só "Gerar")
        disparo = esperar_botao(page, r"^Gerar$|Gerar curso|Criar curso|Concluir e gerar|Finalizar", timeout_s=5)
        if disparo:
            print(f"[wizard] disparo final: {disparo.inner_text()!r}")
            tw.snap(page, PASTA, "09-antes-disparo", full=True)
            disparo.click(timeout=10000)
            break
        prox = esperar_botao(page, r"^(Próximo|Avançar|Continuar)$", timeout_s=180)
        if not prox:
            print(f"[wizard] passo {passo}: 'Próximo' não habilitou em 180s — abortando")
            tw.snap(page, PASTA, f"erro-passo{passo}", full=True)
            break
        passo += 1
        prox.click(timeout=8000)
        page.wait_for_timeout(3500)
        tw.dispensar_nps(page)
        tw.snap(page, PASTA, f"0{min(passo,8)}-passo{passo}")
        print(f"[wizard] avancei p/ passo {passo} | url={page.url}")

    # ---- aguardar a geração de conteúdo e capturar o id do curso ----
    print("[geração] aguardando criação do curso e redirecionamento...")
    curso_id = None
    fim = time.time() + 240
    while time.time() < fim:
        m = re.search(r"/contents/(\d+)/edit", page.url)
        if m:
            curso_id = m.group(1); break
        page.wait_for_timeout(3000)
    print(f"[geração] curso_id={curso_id} | url={page.url}")
    tw.snap(page, PASTA, "10-pos-disparo", full=True)

    if curso_id:
        url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{curso_id}/edit?tab=studio"
        # poll do estúdio até as atividades aparecerem renderizadas
        pronto = False
        fim = time.time() + 480
        while time.time() < fim:
            page.goto(url_studio, wait_until="domcontentloaded", timeout=30000)
            tw.dispensar_nps(page)
            try:
                page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(3000)
            corpo = page.evaluate("()=>document.body.innerText")
            renderizando = bool(re.search(r"Renderizando|Gerando|Processando|aguarde", corpo, re.I))
            n_cards = page.locator('[data-test-id^="creation-studio-activity-card-"]').count()
            print(f"[estúdio] cards={n_cards} | ainda renderizando? {renderizando}")
            if n_cards >= 1 and not renderizando:
                pronto = True; break
            page.wait_for_timeout(15000)
        tw.snap(page, PASTA, "11-estudio-final", full=True)
        print(f"[geração] CONCLUÍDO? {pronto} | curso {curso_id} | studio: {url_studio}")
        print(f"\n>>> CURSO_GERADO slug={SPEC['slug']} id={curso_id} pronto={pronto}")
    else:
        print("[geração] NÃO consegui capturar o id do curso — revisar manualmente")

    ctx.close(); browser.close()
