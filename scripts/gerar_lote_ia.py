# -*- coding: utf-8 -*-
"""Gera o ESQUELETO (wizard + 'Gerar') dos cursos 1..4 do lote, em sequência,
sem esperar o render completo (o conteúdo renderiza async na fila do ambiente).
Registra os ids em evidencias/qualidade_ia_ids.txt para a fase de extração."""
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
import os as _os
ALVOS = [int(x) for x in _os.environ.get("ALVOS", "2,3,4").split(",")]
IDS_FILE = tw.ROOT / "evidencias" / "qualidade_ia_ids.txt"
c = tw.cfg("NOVOEST")


def esperar_botao(page, padrao_regex, timeout_s=180):
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


def gerar_um(page, spec):
    PASTA = tw.ROOT / "evidencias" / f"qualidade_ia_{spec['slug']}"
    # entrar no assistente com retry (a SPA às vezes não renderiza o card sob carga)
    entrou = False
    for tentativa in range(4):
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/new_with_ai",
                  wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(6000)
        tw.dispensar_nps(page)
        card = page.get_by_text(re.compile(r"Assistente de cria", re.I)).first
        if card.count() and card.is_visible():
            card.click(timeout=10000)
            page.wait_for_timeout(5000)
            tw.dispensar_nps(page)
            if page.locator('input[name="theme"]').count():
                entrou = True; break
        print(f"   [{spec['slug']}] retry entrar no assistente ({tentativa+1}/4)")
        page.wait_for_timeout(5000)
    if not entrou:
        raise RuntimeError("não consegui entrar no Assistente de criação")
    page.locator('input[name="theme"]').fill(spec["theme"])
    page.locator('input[name="targetAudience"]').fill(spec["audience"])
    n = page.locator('input[name="numberOfLessons"]'); n.click(); n.fill(""); n.fill(str(spec["n"]))
    for lbl in ["Página", "Aula"]:
        try:
            page.get_by_text(lbl, exact=True).first.click(timeout=2500)
        except Exception:
            pass
    page.locator('textarea[name="objective"]').fill(spec["objective"])
    page.wait_for_timeout(600)
    passo = 1
    while passo < 9:
        disparo = esperar_botao(page, r"^Gerar$|Gerar curso|Criar curso|Concluir e gerar|Finalizar", timeout_s=5)
        if disparo:
            tw.snap(page, PASTA, "09-antes-disparo")
            disparo.click(timeout=10000)
            break
        prox = esperar_botao(page, r"^(Próximo|Avançar|Continuar)$", timeout_s=180)
        if not prox:
            print(f"   [{spec['slug']}] passo {passo}: Próximo não habilitou — abortando este")
            return None
        passo += 1
        prox.click(timeout=8000)
        page.wait_for_timeout(3500)
        tw.dispensar_nps(page)
    # capturar id
    curso_id = None
    fim = time.time() + 180
    while time.time() < fim:
        m = re.search(r"/contents/(\d+)/edit", page.url)
        if m:
            curso_id = m.group(1); break
        page.wait_for_timeout(3000)
    tw.snap(page, PASTA, "10-pos-disparo")
    return curso_id


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)
    # merge: lê ids existentes e atualiza só os processados
    ids = {}
    if IDS_FILE.exists():
        for ln in IDS_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in ln:
                k, v = ln.split("=", 1)
                ids[k.strip()] = v.strip()
    ids.setdefault("sql", "807992"); ids.setdefault("git", "807993"); ids.setdefault("nr35", "807994")
    for idx in ALVOS:
        spec = CURSOS[idx]
        print(f"\n=== gerando esqueleto: {spec['theme']} (slug={spec['slug']}) ===")
        try:
            cid = gerar_um(page, spec)
        except Exception as e:
            print(f"   ERRO {e}"); cid = None
        print(f">>> {spec['slug']} id={cid}")
        if cid:
            ids[spec["slug"]] = cid
        IDS_FILE.write_text("\n".join(f"{k}={v}" for k, v in ids.items()) + "\n", encoding="utf-8")
    print(f"\n=== IDS em {IDS_FILE} ===")
    for k, v in ids.items():
        print(f"  {k}={v}")
    ctx.close(); browser.close()
