"""Testes do gerador de comentário KQA."""
from __future__ import annotations

from pathlib import Path

from app.services.kqa_comment import gerar_comentario_kqa


def test_laudo_corrigido_mostra_passou():
    txt = gerar_comentario_kqa("corrigido", "ok", [])
    assert "✅ Passou" in txt
    assert ":: Teste ::" in txt
    assert ":: Ambiente ::" in txt
    assert "🧪 Stage" in txt


def test_laudo_ainda_quebrado_mostra_falhou():
    txt = gerar_comentario_kqa("ainda_quebrado", "ainda corta", [])
    assert "❌ Falhou" in txt


def test_laudo_inconclusivo_mostra_inconclusivo():
    txt = gerar_comentario_kqa("inconclusivo", "sem certeza", [])
    assert "⚠️ Inconclusivo" in txt


def test_justificativa_aparece_na_validacao():
    txt = gerar_comentario_kqa("corrigido", "Texto centralizado, sem corte.", [])
    assert ":: Validação ::" in txt
    assert "Texto centralizado, sem corte." in txt


def test_justificativa_vazia_mostra_placeholder():
    txt = gerar_comentario_kqa("corrigido", "", [])
    assert "(sem detalhes)" in txt


def test_obs_aparece_quando_preenchida():
    txt = gerar_comentario_kqa("corrigido", "ok", [], obs="rodado no Chrome 120")
    assert ":: Obs ::" in txt
    assert "rodado no Chrome 120" in txt


def test_obs_vazia_omite_secao():
    txt = gerar_comentario_kqa("corrigido", "ok", [])
    assert ":: Obs ::" not in txt


def test_evidencias_lista_com_marcadores(tmp_path):
    e1 = tmp_path / "print1.png"
    e2 = tmp_path / "print2.png"
    txt = gerar_comentario_kqa("corrigido", "ok", [e1, e2])
    assert ":: Evidência(s) ::" in txt
    assert "- print1.png" in txt
    assert "- print2.png" in txt


def test_evidencias_vazia_mostra_placeholder():
    txt = gerar_comentario_kqa("corrigido", "ok", [])
    assert "(sem evidências anexadas)" in txt


def test_commit_url_aparece_quando_passado():
    txt = gerar_comentario_kqa(
        "corrigido",
        "ok",
        [],
        commit_url="https://github.com/DantexgerBR/twygo-playwright-tests/commit/abc123",
    )
    assert "Evidência no link:" in txt
    assert "github.com" in txt


def test_commit_url_vazia_omite_linha():
    txt = gerar_comentario_kqa("corrigido", "ok", [])
    assert "Evidência no link:" not in txt


def test_ambiente_customizavel():
    txt = gerar_comentario_kqa("corrigido", "ok", [], ambiente="Stage Acessibilidade")
    assert "🧪 Stage Acessibilidade" in txt


def test_estrutura_completa_em_ordem_certa():
    """Verifica que as seções aparecem na ordem definida pelo padrão."""
    txt = gerar_comentario_kqa(
        "ainda_quebrado",
        "bug X persiste",
        [Path("a.png")],
        obs="observação Y",
        commit_url="https://x/c/1",
    )
    pos_qa = txt.find("⇝ QA ⇜")
    pos_teste = txt.find(":: Teste ::")
    pos_ambiente = txt.find(":: Ambiente ::")
    pos_validacao = txt.find(":: Validação ::")
    pos_obs = txt.find(":: Obs ::")
    pos_ev = txt.find(":: Evidência(s) ::")
    pos_link = txt.find("Evidência no link:")

    assert 0 <= pos_qa < pos_teste < pos_ambiente < pos_validacao < pos_obs < pos_ev < pos_link
