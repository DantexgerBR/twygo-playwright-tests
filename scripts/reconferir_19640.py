"""19640 — RECONFERIR o desempenho (alguém olhou na org e não bateu).
Reabre a aba Aprendizagem fresca, extrai todas as inscrições (colunas pelo
cabeçalho) e tira screenshot. Usa os helpers de scripts/_twygo.py.
"""
import json

import _twygo as tw

TRILHA_ID = "807406"
PASTA = tw.ROOT / "evidencias" / "19640_pontuacao_reinscricao"


def main():
    c = tw.cfg("RECERT")
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p, width=1600)
        tw.login(page, c)
        tw.ir_learning(page, c, TRILHA_ID)
        print(f"[url] {page.url}")

        linhas = tw.extrair_tabela(page)
        print(f"\n[TODAS as inscrições — {len(linhas)}]:")
        for r in linhas:
            print(f"   {r['itemId']:>10} | {r['email']:30} | prog={r['progresso']:>6} | "
                  f"desemp={r['desempenho']:>8} | pont={r['pontuacao']:>5} | {r['certificado']}")
        print("\n[SÓ agents.claude]:")
        for r in tw.extrair_tabela(page, filtro_email="agents.claude@claude.com"):
            print(f"   {r['itemId']} -> prog={r['progresso']} desemp={r['desempenho']} "
                  f"pont={r['pontuacao']} cert={r['certificado']}")

        PASTA.mkdir(parents=True, exist_ok=True)
        (PASTA / "_reconferencia.json").write_text(
            json.dumps(linhas, ensure_ascii=False, indent=2), encoding="utf-8")
        tw.snap(page, PASTA, "19-reconferencia-full", full=True)

        # definição do '?' de Desempenho (tooltip), se houver
        try:
            page.get_by_text("Desempenho", exact=False).first.hover(timeout=3000)
            page.wait_for_timeout(1500)
            tip = page.evaluate(
                "()=>Array.from(document.querySelectorAll('[role=tooltip],.chakra-tooltip'))"
                ".filter(e=>e.offsetParent!==null).map(e=>(e.innerText||'').trim())")
            print(f"[tooltip desempenho] {tip}")
        except Exception as e:
            print(f"   tooltip err: {repr(e)[:80]}")

        page.wait_for_timeout(1000)
        ctx.close(); browser.close()


if __name__ == "__main__":
    main()
