"""Testes do parser de retrabalho."""
from __future__ import annotations

from app.services.retrabalho_parser import (
    parece_retrabalho,
    parse_retrabalho,
)


TEXTO_EXEMPLO = """:: Incidente identificado ::
Em cards de atividade do tipo Página na aba de Design de um modelo, foi observado que não exibe o texto centralizado e corta parte do texto no card.

    :: Passo a passo para reprodução ::
» Editar modelo
» Design
» Editar Página
» Inserir texto
» Visualizar card em aba Design

    :: Comportamento esperado ::
Apresentar texto centralizado possibilitando a visualização sem cortar o texto"""


def test_parece_retrabalho_reconhece_texto_padrao():
    assert parece_retrabalho(TEXTO_EXEMPLO) is True


def test_parece_retrabalho_reconhece_so_passos_com_seta():
    assert parece_retrabalho("» Passo 1\n» Passo 2") is True


def test_parece_retrabalho_falso_para_caso_estruturado():
    assert parece_retrabalho("Objetivo: validar X\nPré-condições\n- foo") is False


def test_parse_retrabalho_extrai_incidente():
    caso = parse_retrabalho(TEXTO_EXEMPLO)
    assert "cards de atividade do tipo Página" in caso.objetivo
    assert "centralizado" in caso.objetivo


def test_parse_retrabalho_extrai_cinco_passos():
    caso = parse_retrabalho(TEXTO_EXEMPLO)
    assert len(caso.passos) == 5
    assert caso.passos[0]["acao"] == "Editar modelo"
    assert caso.passos[1]["acao"] == "Design"
    assert caso.passos[2]["acao"] == "Editar Página"
    assert caso.passos[3]["acao"] == "Inserir texto"
    assert caso.passos[4]["acao"] == "Visualizar card em aba Design"


def test_parse_retrabalho_esperado_no_ultimo_passo():
    caso = parse_retrabalho(TEXTO_EXEMPLO)
    # Comportamento esperado fica no último passo
    assert "centralizado" in caso.passos[-1]["esperado"]
    # Passos intermediários não têm esperado
    assert caso.passos[0]["esperado"] == ""


def test_parse_retrabalho_numera_sequencialmente():
    caso = parse_retrabalho(TEXTO_EXEMPLO)
    assert [p["n"] for p in caso.passos] == [1, 2, 3, 4, 5]


def test_parse_retrabalho_texto_bruto_preservado():
    caso = parse_retrabalho(TEXTO_EXEMPLO)
    assert caso.texto_bruto == TEXTO_EXEMPLO


def test_parse_retrabalho_so_passos_sem_secoes():
    texto = """» Passo A
» Passo B"""
    caso = parse_retrabalho(texto)
    assert len(caso.passos) == 2
    assert caso.passos[0]["acao"] == "Passo A"


def test_parse_retrabalho_sem_passos_retorna_lista_vazia():
    texto = ":: Incidente identificado ::\nBug X"
    caso = parse_retrabalho(texto)
    assert caso.passos == []
    assert "Bug X" in caso.objetivo


def test_parse_retrabalho_ambiente_default_stage():
    caso = parse_retrabalho(TEXTO_EXEMPLO)
    assert caso.ambiente == "stage"
