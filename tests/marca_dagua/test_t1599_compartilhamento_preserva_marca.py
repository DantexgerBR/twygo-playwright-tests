"""
T-1599 v1 — Compartilhamento de conteúdo (cópia controlada/espelho) preserva marca d'água

CASO: Verificar que ao compartilhar um curso com atividade de vídeo com marca d'água
habilitada (modo Cópia controlada / espelho), a organização destinatária recebe a
atividade com as mesmas configurações de marca d'água.

PRÉ-CONDIÇÕES:
    - Usuário logado como Admin na organização origem
    - Feature flag de marca d'água habilitada em ambas as organizações
    - Curso com atividade de vídeo previamente cadastrada com marca d'água habilitada
    - Organização destinatária configurada e capaz de receber compartilhamentos

PERFIL TESTADO: Admin
PLATAFORMA: Desktop
AMBIENTE: Principal (stage)

Referência: docs/casos/T-1599.md

ESTADO: ⚠️ Bloqueado pelo ambiente — passos 1 e 2 (até marcar 'Controlado') automatizados.
Passo 2 (Salvar), 3 e 4 dependem de uma org destinatária disponível no dropdown 'Ambientes'.
Defina ORG_DESTINATARIA_NOME, ORG_DESTINATARIA_ID, ADMIN_DESTINATARIA_EMAIL/PASSWORD no .env
para destravar a execução completa.
"""
import os
from pathlib import Path

import pytest

from pages.admin.atividade_video_page import AtividadeVideoPage
from pages.admin.compartilhar_curso_page import CompartilharCursoPage

EVENTO_ORIGEM = os.environ.get("EVENTO_ID", "")
ATIVIDADE_ORIGEM = os.environ.get("ATIVIDADE_VIDEO_MARCA_DAGUA_ID", "")
ORG_DESTINATARIA_NOME = os.environ.get("ORG_DESTINATARIA_NOME", "")
OUTPUT_DIR = Path("test-results/t1599")


@pytest.mark.admin
@pytest.mark.marca_dagua
def test_compartilhamento_controlado_preserva_marca_dagua(admin_logado, base_url):
    """Automatiza passos 1 e 2 do T-1599.

    Passo 1: acessar curso na org origem.
    Passo 2: abrir 'Compartilhar' → Adicionar → marcar 'Controlado'. A escolha da
    org destinatária e o Salvar dependem de ORG_DESTINATARIA_NOME definido no .env.
    Se ausente, o teste registra a evidência da limitação do ambiente (lista de
    Ambientes vazia) e é marcado como xfail.
    """
    assert EVENTO_ORIGEM and ATIVIDADE_ORIGEM, (
        "Defina EVENTO_ID e ATIVIDADE_VIDEO_MARCA_DAGUA_ID no .env"
    )
    page = admin_logado
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ----- Pré: lê a config da atividade ORIGEM (será comparada com a destinatária no passo 4) -----
    edit_origem = AtividadeVideoPage(page)
    edit_origem.abrir_edicao(base_url, EVENTO_ORIGEM, ATIVIDADE_ORIGEM)
    page.wait_for_timeout(6000)
    config_origem = edit_origem.ler_config_marca_dagua()
    assert config_origem["enabled"], (
        "Pré-condição não satisfeita: marca d'água deve estar habilitada na atividade origem."
    )
    print(f"[T-1599] config origem (atividade {ATIVIDADE_ORIGEM}): {config_origem}")

    compartilhar = CompartilharCursoPage(page)

    # Passo 1 — Acessar o curso na organização origem
    # Esperado: Tela de edição do curso é exibida
    compartilhar.abrir_aba_share(base_url, EVENTO_ORIGEM)
    page.screenshot(path=str(OUTPUT_DIR / "passo1-edit-curso.png"))
    assert "tab=share" in page.url, f"Não entrou na aba Compartilhar. url={page.url}"

    page.screenshot(path=str(OUTPUT_DIR / "passo2a-aba-share.png"))

    # Passo 2 — Acionar 'Compartilhar' no modo 'Cópia controlada' (espelho)
    # Esperado: Toast de sucesso é exibido confirmando o compartilhamento
    compartilhar.clicar_adicionar()
    page.screenshot(path=str(OUTPUT_DIR / "passo2b-form-adicionar.png"))
    assert "/shared_events/new" in page.url, (
        f"Form 'Adicionar compartilhamento' não abriu. url={page.url}"
    )

    # Compartilhar com = Ambiente interno (default)
    compartilhar.escolher_consumer_type("interno")
    # Tipo de compartilhamento = Controlado (espelhado)
    compartilhar.escolher_shared_type("controlado")
    page.screenshot(path=str(OUTPUT_DIR / "passo2c-controlado-marcado.png"))

    estado = compartilhar.ler_estado_form()
    consumer_ok = any(r["name"] == "consumer_type" and r["value"] == "0" and r["checked"] for r in estado["radios"])
    shared_ok = any(r["name"] == "shared_type" and r["value"] == "1" and r["checked"] for r in estado["radios"])
    assert consumer_ok, f"Ambiente interno não está marcado: {estado['radios']}"
    assert shared_ok, f"Controlado (espelhado) não está marcado: {estado['radios']}"

    # Selecionar org destinatária no react-select Ambientes
    opcoes = compartilhar.listar_opcoes_ambientes()
    page.screenshot(path=str(OUTPUT_DIR / "passo2d-ambientes-vazio.png"))
    print(f"[T-1599] opcoes do dropdown Ambientes (Ambiente interno): {opcoes!r}")

    if not opcoes:
        pytest.xfail(
            "Ambiente bloqueado para automação completa: dropdown 'Ambientes' (consumer_type=Ambiente interno) "
            "retornou 0 opções para o admin desta org. Sem org destinatária disponível, os passos 2 (Salvar), 3 e 4 "
            "não podem ser executados. Configure outra org interna acessível a este admin OU defina "
            "ORG_DESTINATARIA_NOME no .env e use 'Ambiente externo'."
        )

    if not ORG_DESTINATARIA_NOME:
        pytest.xfail(
            f"Há {len(opcoes)} org(s) no dropdown ({opcoes!r}) mas ORG_DESTINATARIA_NOME não foi definido no .env. "
            "Defina o nome exato da org destinatária para continuar a execução."
        )

    selecionou = compartilhar.escolher_ambiente_destino(ORG_DESTINATARIA_NOME)
    assert selecionou, (
        f"Org destinatária {ORG_DESTINATARIA_NOME!r} não encontrada no dropdown. "
        f"Opções disponíveis: {opcoes!r}"
    )

    compartilhar.salvar()
    page.screenshot(path=str(OUTPUT_DIR / "passo2e-pos-salvar.png"))
    # toast de sucesso esperado — usar .first pois o Chakra empilha múltiplas instâncias
    from playwright.sync_api import expect
    expect(page.get_by_text("Conteúdo compartilhado com sucesso").first).to_be_visible(timeout=8000)

    # Passos 3 e 4 — requerem login na org destinatária (não implementado nesta fixture)
    # TODO: criar fixture admin_destinataria_logado quando ORG_DESTINATARIA_* estiver
    # configurado no .env, e replicar AtividadeVideoPage.ler_config_marca_dagua()
    # no curso espelhado para asserir igualdade com config_origem.
    pytest.xfail(
        "Passos 3 e 4 (validar atividade na org destinatária) ainda não implementados — "
        "requerem fixture admin_destinataria_logado e ATIVIDADE_DESTINO_ID conhecida."
    )
