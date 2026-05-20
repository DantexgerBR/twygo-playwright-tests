"""
CASO: Verificar que ao desmarcar o checkbox 'Habilitar marca d'água no vídeo'
em uma atividade previamente configurada e salvar, a marca d'água deixa de
ser exibida no Aprender.

PRÉ-CONDIÇÕES:
    - Usuário logado como Admin
    - Feature flag de marca d'água habilitada
    - Atividade de vídeo previamente cadastrada com marca d'água habilitada
    - Aluno previamente matriculado e capaz de acessar o conteúdo no Aprender

PERFIL TESTADO: Administrador
PLATAFORMA: Desktop
AMBIENTE: Principal (stage)

Referência: docs/casos/marca_dagua_video_desmarcar.md
"""
import os

import pytest
from playwright.sync_api import expect

from pages.admin.atividade_video_page import AtividadeVideoPage
from pages.aprender.conteudo_video_page import ConteudoVideoPage


EVENTO_ID = os.environ.get("EVENTO_ID", "")
ATIVIDADE_ID = os.environ.get("ATIVIDADE_VIDEO_MARCA_DAGUA_ID", "")


@pytest.mark.admin
@pytest.mark.marca_dagua
def test_desmarcar_marca_dagua_oculta_no_aprender(
    admin_logado,
    aluno_logado,
    base_url,
):
    assert EVENTO_ID and ATIVIDADE_ID, "Defina EVENTO_ID e ATIVIDADE_VIDEO_MARCA_DAGUA_ID no .env"

    admin_page = AtividadeVideoPage(admin_logado)

    # Passo 1 — Acessar a atividade de vídeo previamente cadastrada para editar
    # Esperado: Formulário de edição é exibido com o checkbox 'Habilitar marca d'água no vídeo' marcado
    admin_page.abrir_edicao(base_url, EVENTO_ID, ATIVIDADE_ID)
    assert admin_page.esta_marcado(), "Checkbox 'Habilitar marca d'água no vídeo' deveria estar marcado"

    # Passo 2 — Desmarcar o checkbox 'Habilitar marca d'água no vídeo'
    # Esperado: Checkbox desmarcado. Todos os campos de configuração e preview são ocultados
    admin_page.desmarcar_marca_dagua()
    assert not admin_page.esta_marcado(), "Checkbox deveria ter ficado desmarcado"
    expect(admin_page.painel_config_marca_dagua).to_be_hidden()
    expect(admin_page.preview_marca_dagua).to_be_hidden()

    # Passo 3 — Clicar no botão 'Salvar'
    # Esperado: Toast de sucesso exibida com o texto 'Alterações salvas com sucesso.'
    admin_page.salvar()
    admin_page.aguardar_toast_sucesso("Alterações salvas com sucesso.")

    # Passo 4 — Logar como o aluno e acessar a atividade no Aprender
    # Esperado: Vídeo é reproduzido. Marca d'água NÃO é exibida sobre o vídeo
    aprender = ConteudoVideoPage(aluno_logado)
    aprender.abrir_atividade(base_url, EVENTO_ID, ATIVIDADE_ID)
    assert aprender.video_esta_visivel(), "Vídeo não está visível no Aprender"
    assert not aprender.tem_marca_dagua(), "Marca d'água ainda está sendo exibida sobre o vídeo"
