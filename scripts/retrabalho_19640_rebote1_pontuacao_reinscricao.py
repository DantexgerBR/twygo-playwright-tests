"""Retrabalho 19640 — REBOTE 1 (P1) [Recertificacao] Desempenho e pontuacao da
reinscricao atual propagado para todas as reinscricoes.

PR do dev: https://github.com/Twygo/twyg-app/pull/10468
Causa-raiz (PR): EventStudentService#build_select_criterias agregava final_score
(desempenho) e total_score_by_weight (pontuacao) por ep_child.user_id =
event_participants.user_id -> misturava TODOS os filhos do usuario de TODAS as
reinscricoes. Fix: correlacionar filhos por participant_relations
(learning_path_participant_id = event_participants.id) -> cada inscricao agrega
SO os proprios filhos.

CORRIGIDO = cada geracao (linha da aba Aprendizagem) mostra desempenho/pontuacao
DISTINTOS, refletindo so os proprios filhos. Em especial:
  - reinscricao fresca (progresso 0%, nada feito) DEVE exibir 0% / 0  (discriminador forte)
  - geracao finalizada DEVE manter o proprio valor (imutavel), nao o da atual.
QUEBRADO = geracao a 0% de progresso exibindo desempenho/pontuacao NAO-ZERO
(valor propagado da inscricao atual), ou todas as geracoes identicas apesar de
progresso/filhos diferentes.

Cross-check (anti-falso-positivo): aba "Respostas de questionario" prova que o
dado real existe (por usuario). A fonte de verdade POR GERACAO definitiva e o
banco (twygo_db_rc) — usar so se a UI ficar ambigua.

Env: RECERT (org 37048). Trilha "Trilha para CASCADE" (id 807406).
"""
import json
from collections import defaultdict
from pathlib import Path

import _twygo as tw

c = tw.cfg("RECERT")
TRILHA_ID = "807406"
PASTA = tw.ROOT / "evidencias" / "19640_rebote1_pontuacao_reinscricao"


def num(s):
    """'69.2%' / '150' / '0%' -> float (so digitos e ponto). '' -> None."""
    if s is None:
        return None
    t = "".join(ch for ch in str(s) if ch.isdigit() or ch == ".")
    try:
        return float(t) if t else None
    except ValueError:
        return None


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    print(f"[login] {page.url}")

    tw.ir_learning(page, c, TRILHA_ID)
    print(f"[learning] {page.url}")
    if "/login" in page.url:
        tw.snap(page, PASTA, "00-falha-login")
        raise SystemExit("FALHA: caiu no login")
    tw.snap(page, PASTA, "01-lista-aprendizagem")

    # ---- captura por CABECALHO (robusto) ----
    linhas = tw.extrair_tabela(page)
    print(f"\n[tabela] {len(linhas)} inscricoes (por cabecalho):")
    for i, l in enumerate(linhas):
        print(f"  [{i}] {l['email']:30} item={l['itemId']:>9} "
              f"prog={l['progresso']:>6} desemp={l['desempenho']:>7} "
              f"pont={l['pontuacao']:>6} cert={l['certificado'][:18]}")
    PASTA.mkdir(parents=True, exist_ok=True)
    (PASTA / "_inscricoes.json").write_text(
        json.dumps(linhas, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- analise por usuario (discriminador afiado) ----
    grupos = defaultdict(list)
    for l in linhas:
        grupos[l["email"]].append(l)

    achados = []  # (email, tipo, detalhe)
    print("\n===== ANALISE POR USUARIO =====")
    for email, regs in grupos.items():
        if len(regs) < 2:
            print(f"  {email}: 1 inscricao (sem reinscricao p/ comparar)")
            continue
        print(f"  {email}: {len(regs)} inscricoes")
        desemps, ponts, progs = set(), set(), set()
        for r in regs:
            d, pt, pr = num(r["desempenho"]), num(r["pontuacao"]), num(r["progresso"])
            desemps.add(d); ponts.add(pt); progs.add(pr)
            print(f"       item={r['itemId']:>9} prog={r['progresso']:>6} "
                  f"desemp={r['desempenho']:>7} pont={r['pontuacao']:>6} "
                  f"cert={r['certificado'][:18]}")
            # DISCRIMINADOR FORTE: 0% progresso com desemp OU pont nao-zero = propagacao
            if pr == 0 and ((d or 0) > 0 or (pt or 0) > 0):
                achados.append((email, "ZERO_PROG_NAOZERO", r["itemId"],
                                f"prog=0% mas desemp={r['desempenho']} pont={r['pontuacao']}"))
        # propagacao classica: progresso varia mas desemp+pont todos iguais (nao-zero)
        if len(progs) > 1 and len(desemps) == 1 and len(ponts) == 1 and (next(iter(desemps)) or 0) > 0:
            achados.append((email, "TODOS_IGUAIS", "-",
                            f"progresso varia mas desemp={desemps} pont={ponts} identicos"))
        distintos = len(desemps) > 1 or len(ponts) > 1
        print(f"       -> desemp distintos={len(desemps) > 1} | pont distintas={len(ponts) > 1} "
              f"| PRESERVA_HISTORICO(distinto)={distintos}")

    # ---- CROSS-CHECK fonte de verdade: aba Respostas de questionario ----
    print("\n===== CROSS-CHECK: Respostas de questionario =====")
    respostas = []
    try:
        page.get_by_role("tab", name=tw.re.compile("Respostas de question", tw.re.I)).first.click(timeout=6000)
        page.wait_for_timeout(3500)
        tw.dispensar_nps(page)
        tw.snap(page, PASTA, "02-respostas-questionario")
        respostas = page.evaluate(
            r"""() => {
                const out = [];
                document.querySelectorAll('tr').forEach(r => {
                    const t = (r.innerText||'').replace(/\s+/g,' ').trim();
                    if (/@/.test(t) && /(Aprovad|Reprovad|%)/i.test(t)) out.push(t.slice(0,160));
                });
                return out;
            }""")
        for r in respostas:
            print(f"   • {r}")
        (PASTA / "_respostas_questionario.json").write_text(
            json.dumps(respostas, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"   [aviso] nao consegui abrir/extrair Respostas de questionario: {e}")

    # ---- best-effort: Historico de aprendizagem do 1o usuario multi-geracao ----
    print("\n===== best-effort: Historico de aprendizagem (kebab) =====")
    try:
        page.get_by_role("tab", name=tw.re.compile("Aprendizagem", tw.re.I)).first.click(timeout=6000)
        page.wait_for_timeout(2500)
        multi = next((e for e, rs in grupos.items() if len(rs) > 1), None)
        if multi:
            row = page.locator(f'tr[data-item-id="{grupos[multi][0]["itemId"]}"]').first
            tw.abrir_kebab(page, row)
            tw.snap(page, PASTA, "03-kebab-aberto")
            itens = tw.menu_visivel(page)
            print(f"   itens do kebab: {itens}")
            if tw.click_menuitem(page, "Hist.*aprendiz"):
                page.wait_for_timeout(3000)
                tw.dispensar_nps(page)
                tw.snap(page, PASTA, "04-historico-aprendizagem")
                print("   [ok] abriu Historico de aprendizagem")
            else:
                print("   [aviso] item 'Historico de aprendizagem' nao encontrado/clicavel")
    except Exception as e:
        print(f"   [aviso] historico best-effort falhou: {e}")

    # ---- veredito preliminar ----
    print("\n===== RESUMO =====")
    multi_users = [e for e, rs in grupos.items() if len(rs) > 1]
    print(f"usuarios com reinscricao (multi-geracao) testados: {len(multi_users)} -> {multi_users}")
    if achados:
        print("BUG PRESENTE (indicios na aba Aprendizagem):")
        for a in achados:
            print(f"   ❌ {a[0]} [{a[1]}] item={a[2]} :: {a[3]}")
    else:
        print("OK na UI: nenhuma geracao 0% com valor nao-zero; valores por geracao distintos/coerentes.")
    (PASTA / "_achados.json").write_text(
        json.dumps([{"email": a[0], "tipo": a[1], "item": a[2], "detalhe": a[3]} for a in achados],
                   ensure_ascii=False, indent=2), encoding="utf-8")

    page.wait_for_timeout(1500)
    print(f"\n[FIM] evidencias em: {PASTA}")
    ctx.close(); browser.close()
