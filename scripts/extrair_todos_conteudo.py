# -*- coding: utf-8 -*-
"""Extrai estrutura + conteúdo de PÁGINA de todos os cursos do lote (lê o arquivo
de ids). Para cada curso: lista atividades (estúdio), abre o sub-tab Conteúdo de
cada Página e extrai o texto rico. Salva dump por curso + screenshots.
(O conteúdo das Aulas é vídeo/canvas — avaliado à parte via player.)"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

IDS_FILE = tw.ROOT / "evidencias" / "qualidade_ia_ids.txt"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'

ids = {}
for ln in IDS_FILE.read_text(encoding="utf-8").splitlines():
    if "=" in ln:
        k, v = ln.split("=", 1)
        if v.strip() and v.strip() != "None":
            ids[k.strip()] = v.strip()

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=1000)
    tw.login(page, c)

    for slug, cid in ids.items():
        PASTA = tw.ROOT / "evidencias" / f"qualidade_ia_{slug}"
        print(f"\n========== CURSO {slug} ({cid}) ==========")
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{cid}/edit?tab=studio",
                  wait_until="domcontentloaded", timeout=45000)
        tw.dispensar_nps(page)
        try:
            page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=20000)
        except Exception:
            print("  [!] lista não carregou"); continue
        page.wait_for_timeout(2500)

        # título do curso
        titulo_curso = page.evaluate("()=>{const h=document.querySelector('h1,h2');return h?h.innerText.trim():''}")
        # atividades top-level
        ativs = page.evaluate(
            r"""()=>{const out=[];document.querySelectorAll('[data-test-id]').forEach(e=>{
                const m=(e.getAttribute('data-test-id')||'').match(/^creation-studio-activity-card-(\d+)$/);
                if(m)out.push({id:m[1],txt:(e.innerText||'').replace(/\s+/g,' ').trim().slice(0,90)});});return out;}"""
        )
        linhas = [f"CURSO: {titulo_curso}  (slug={slug}, id={cid})", "ESTRUTURA:"]
        for a in ativs:
            linhas.append(f"  - {a['txt']}")
        print(f"  curso='{titulo_curso}' | {len(ativs)} atividades")

        # conteúdo de cada atividade (Página = texto rico; Aula = chrome do editor)
        for a in ativs:
            aid = a["id"]
            for typ in ["page", "lesson"]:
                page.goto(f"{c['base_url']}/o/{c['org_id']}/studio/activities/{aid}/edit?type={typ}&eventId={cid}",
                          wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2500)
                tw.dispensar_nps(page)
                if page.get_by_text(re.compile(r"^Conteúdo$", re.I)).count():
                    break
            try:
                page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=5000, force=True)
                page.wait_for_timeout(3500)
            except Exception:
                pass
            txt = page.evaluate(
                """()=>{
                    // pega o conteúdo do editor de página (contenteditable) se houver
                    const eds=[...document.querySelectorAll('[contenteditable=true]')].filter(e=>e.offsetParent!==null);
                    if(eds.length) return eds.map(e=>(e.innerText||'').trim()).join('\\n');
                    // senão, o texto da área principal (tira o menu lateral)
                    const main=document.querySelector('main')||document.body;
                    return (main.innerText||'').replace(/\\n{3,}/g,'\\n').trim();
                }"""
            )
            tipo = "Aula" if "Aula" in a["txt"] else "Página"
            linhas.append(f"\n--- [{tipo}] {aid} ---\n{txt[:3500]}")
            print(f"    [{aid} {tipo}] {len(txt)} ch")

        (PASTA).mkdir(parents=True, exist_ok=True)
        (PASTA / "conteudo_completo.txt").write_text("\n".join(linhas), encoding="utf-8")
        print(f"  [dump] {PASTA / 'conteudo_completo.txt'}")

    ctx.close(); browser.close()
