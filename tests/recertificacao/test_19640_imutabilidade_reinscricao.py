"""CARD 19640 (P1) [Recertificação] — Desempenho/pontuação de inscrições anteriores
ao reinscrever.

DELIBERADAMENTE `skip`: este caso NÃO vira um assert pass/fail automático porque:

1. **Muta dados no stage** — exige fazer uma reinscrição (botão "Reinscrever-se" do
   aluno), criando uma nova geração e alterando a anterior. Não é idempotente nem
   seguro rodar em CI / suíte compartilhada.
2. **Comportamento esperado em aberto** — na validação (2026-06-01) o dado-fonte
   (aba "Respostas de questionário") ficou PRESERVADO (quizzes 100% Aprovado), mas a
   aba Aprendizagem exibiu desempenho/pontuação não condizente por geração. Falta o
   dev/banco confirmar qual valor cada geração DEVE exibir. Sem esse esperado, um
   assert seria falso positivo/negativo (justamente o que evitamos).

Quando o esperado for definido, transformar em teste real:
    - admin_em("RECERT"); AprendizagemPage; abrir trilha 807406;
    - escolher participante com inscrição não-zero e elegível;
    - registrar (desempenho, pontuação) por data-item-id;
    - reinscrever pelo lado do aluno ("Reinscrever-se" + "Confirmar");
    - reabrir Aprendizagem e comparar por data-item-id;
    - cross-check OBRIGATÓRIO com `respostas_questionario()` (fonte de verdade).

Referência: evidencias/19640_pontuacao_reinscricao/LAUDO.md
"""
import pytest


@pytest.mark.recertificacao
@pytest.mark.reinscricao
@pytest.mark.skip(reason="muta stage + comportamento esperado pendente de confirmação do dev (ver docstring/LAUDO)")
def test_reinscricao_preserva_historico_da_inscricao_anterior():
    raise AssertionError("spec documentado — habilitar quando o esperado for definido")
