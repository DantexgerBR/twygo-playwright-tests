"""19640 — CROSS-CHECK do desempenho: a aba 'Respostas de questionário' mostra o
desempenho REAL por questionário/tentativa. Compara com a aba Aprendizagem pro
agents.claude (fonte de verdade vs valor exibido). Usa scripts/_twygo.py.
"""
import json

import _twygo as tw

TRILHA_ID = "807406"
ALVO = "agents.claude@claude.com"
PASTA = tw.ROOT / "evidencias" / "19640_pontuacao_reinscricao"


def main():
    c = tw.cfg("RECERT")
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p, width=1600, height=1000)
        tw.login(page, c)
        tw.ir_learning(page, c, TRILHA_ID)

        # aba Aprendizagem: o que está EXIBIDO pro alvo
        exibido = tw.extrair_tabela(page, filtro_email=ALVO)
        print(f"[Aprendizagem] {ALVO}:")
        for r in exibido:
            print(f"   {r['itemId']} prog={r['progresso']} desemp={r['desempenho']} pont={r['pontuacao']}")

        # aba Respostas de questionário: a FONTE DE VERDADE
        print("\n[Respostas de questionário] clicando aba ...")
        try:
            page.get_by_text("Respostas de questionário", exact=False).first.click(timeout=8000)
            page.wait_for_timeout(4000); tw.dispensar_nps(page)
        except Exception as e:
            print(f"   click aba falhou: {repr(e)[:100]}")
        tw.snap(page, PASTA, "20-respostas-questionario", full=True)
        reais = page.evaluate(
            r"""(filtro)=>{const out=[];document.querySelectorAll('tr').forEach(r=>{
                const t=(r.innerText||'').replace(/\s+/g,' ').trim();if(!/@/.test(t))return;
                const email=(t.match(/[\w.\-]+@[\w.\-]+/)||[''])[0];if(email!==filtro)return;
                out.push(t);});return out;}""", ALVO)
        print(f"[Respostas reais de {ALVO}] {len(reais)}:")
        for t in reais:
            print(f"   {t}")

        (PASTA / "_respostas_questionario.json").write_text(
            json.dumps({"exibido_aprendizagem": exibido, "respostas_reais": reais},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        page.wait_for_timeout(1000)
        ctx.close(); browser.close()


if __name__ == "__main__":
    main()
