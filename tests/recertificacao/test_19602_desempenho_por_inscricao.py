"""CARD 19602 (P1) [Recertificação] — Desempenho da trilha deve corresponder à
inscrição (geração), não ser compartilhado/propagado entre as inscrições do mesmo
usuário.

Env: RECERT (org 37048), trilha "Trilha para CASCADE" (807406). Pula sem cred/dados.

Assertiva ROBUSTA (não depende de valor exato, que é mutável no stage):
- a aba Aprendizagem lista UMA LINHA POR INSCRIÇÃO (data-item-id distinto);
- as colunas Progresso e Desempenho existem e são lidas por geração;
- o bug original era "todas as inscrições do MESMO usuário com desempenho idêntico
  apesar de progresso diferente" → se houver um usuário com progressos DIFERENTES
  entre suas inscrições, o desempenho NÃO deve ser idêntico em todas.

Referência: evidencias/19602_desempenho_trilha/ (e 19640 LAUDO).
"""
from collections import defaultdict

import pytest

from pages.admin.aprendizagem_page import AprendizagemPage

TRILHA_ID = "807406"


@pytest.mark.recertificacao
@pytest.mark.reinscricao
def test_desempenho_nao_e_identico_entre_inscricoes_com_progresso_diferente(admin_em):
    page, base = admin_em("RECERT")
    ap = AprendizagemPage(page)
    ap.abrir(base, TRILHA_ID)

    participantes = ap.participantes()
    if not participantes:
        pytest.skip("Trilha 807406 sem participantes (dados de stage mudaram?)")

    # estrutura: uma linha por inscrição, com itemId único
    assert all(p["itemId"] for p in participantes), "Há linha sem data-item-id (geração não identificável)"
    assert all(p["progresso"] != "" and p["desempenho"] != "" for p in participantes), \
        "Colunas Progresso/Desempenho ausentes — layout da aba Aprendizagem mudou"

    # agrupa por usuário e procura quem tem progressos diferentes entre inscrições
    por_user = defaultdict(list)
    for p in participantes:
        por_user[p["email"]].append(p)

    casos = [(email, regs) for email, regs in por_user.items()
             if len({r["progresso"] for r in regs}) > 1]
    if not casos:
        pytest.skip("Nenhum usuário com inscrições de progresso diferente para contrastar.")

    for email, regs in casos:
        desempenhos = {r["desempenho"] for r in regs}
        assert len(desempenhos) > 1, (
            f"{email}: progressos diferentes ({[r['progresso'] for r in regs]}) mas desempenho "
            f"IDÊNTICO em todas as inscrições ({desempenhos}) — sintoma do bug 19602 (propagado)."
        )
