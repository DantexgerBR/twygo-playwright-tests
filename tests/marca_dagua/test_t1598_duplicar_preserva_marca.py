"""
T-1598 v1 — Duplicar atividade de vídeo preserva configurações da marca d'água

CASO: Verificar que ao duplicar uma atividade de vídeo com marca d'água habilitada,
a cópia mantém exatamente as mesmas configurações de marca d'água.

PRÉ-CONDIÇÕES:
    - Usuário logado como Admin
    - Feature flag de marca d'água habilitada
    - Atividade de vídeo previamente cadastrada com marca d'água habilitada
      e configurações específicas conhecidas

PERFIL TESTADO: Admin
PLATAFORMA: Desktop
AMBIENTE: Principal (stage)

Referência: docs/casos/T-1598.md

NOTA: na UI atual da Twygo, "Duplicar" é o botão "Copiar atividade" no topo da
listagem `/e/{evento}/contents`. O modal só lista OUTROS cursos como origem,
então o teste usa dois cursos:
    - ORIGEM: EVENTO_ID (curso com a atividade ATIVIDADE_VIDEO_MARCA_DAGUA_ID
      configurada com marca d'água).
    - DESTINO: EVENTO_DESTINO_ID (qualquer outro curso da org).
"""
import os
from pathlib import Path

import pytest

from pages.admin.atividade_video_page import AtividadeVideoPage
from pages.admin.listagem_atividades_page import ListagemAtividadesPage

EVENTO_ORIGEM = os.environ.get("EVENTO_ID", "")
ATIVIDADE_ORIGEM = os.environ.get("ATIVIDADE_VIDEO_MARCA_DAGUA_ID", "")
EVENTO_DESTINO = os.environ.get("EVENTO_DESTINO_ID", "787697")
OUTPUT_DIR = Path("test-results/t1598")


@pytest.mark.admin
@pytest.mark.marca_dagua
def test_duplicar_atividade_preserva_config_marca_dagua(admin_logado, base_url):
    assert EVENTO_ORIGEM and ATIVIDADE_ORIGEM, "Defina EVENTO_ID e ATIVIDADE_VIDEO_MARCA_DAGUA_ID no .env"
    page = admin_logado
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ----- Pré: lê a config da atividade ORIGEM -----
    edit_origem = AtividadeVideoPage(page)
    edit_origem.abrir_edicao(base_url, EVENTO_ORIGEM, ATIVIDADE_ORIGEM)
    page.wait_for_timeout(6000)
    config_origem = edit_origem.ler_config_marca_dagua()
    assert config_origem["enabled"], (
        "Pré-condição não satisfeita: marca d'água deve estar habilitada na atividade origem."
    )
    page.screenshot(path=str(OUTPUT_DIR / "config-origem.png"))

    # Passo 1 — Acessar o curso de destino
    # Esperado: Listagem de atividades do curso é exibida
    listagem = ListagemAtividadesPage(page)
    listagem.abrir(base_url, EVENTO_DESTINO)
    ids_antes = listagem.ids_atividades()
    page.screenshot(path=str(OUTPUT_DIR / "passo1-listagem-destino.png"))

    # Passo 2 — Acionar a opção 'Duplicar' (botão "Copiar atividade")
    # Esperado: Atividade duplicada é criada na listagem
    listagem.abrir_modal_copiar()
    page.screenshot(path=str(OUTPUT_DIR / "passo2a-modal-aberto.png"))
    listagem.selecionar_curso_origem(EVENTO_ORIGEM)
    page.screenshot(path=str(OUTPUT_DIR / "passo2b-curso-origem-selecionado.png"))
    listagem.selecionar_atividade_no_modal(ATIVIDADE_ORIGEM)
    page.screenshot(path=str(OUTPUT_DIR / "passo2c-atividade-selecionada.png"))
    listagem.salvar_copy()
    # após salvar, o JS pode recarregar a listagem; navegar de volta pra garantir estado limpo
    listagem.abrir(base_url, EVENTO_DESTINO)
    ids_depois = listagem.ids_atividades()
    page.screenshot(path=str(OUTPUT_DIR / "passo2d-listagem-pos-duplicacao.png"))
    novos_ids = [i for i in ids_depois if i not in ids_antes]
    assert novos_ids, (
        f"Nenhuma atividade nova surgiu na listagem do curso destino {EVENTO_DESTINO}. "
        f"ids antes={ids_antes}, ids depois={ids_depois}"
    )
    NOVO_ID = novos_ids[0]

    # Passo 3 — Abrir a atividade duplicada para edição
    # Esperado: Formulário de edição da atividade duplicada é exibido
    edit_duplicada = AtividadeVideoPage(page)
    edit_duplicada.abrir_edicao(base_url, EVENTO_DESTINO, NOVO_ID)
    page.wait_for_timeout(6000)
    page.screenshot(path=str(OUTPUT_DIR / "passo3-edicao-duplicada.png"))

    # Lê config da duplicada
    config_duplicada = edit_duplicada.ler_config_marca_dagua()

    # Passo 4 — Verificar o estado do checkbox 'Habilitar marca d'água no vídeo'
    # Esperado: Checkbox 'Habilitar marca d'água no vídeo' está marcado
    assert config_duplicada["enabled"] is True, (
        f"Checkbox de marca d'água NÃO está marcado na duplicada: {config_duplicada}"
    )

    # Passo 5 — Verificar as opções selecionadas em 'Informações', 'Posição', 'Tipo de exibição'
    # Esperado: Todas as opções selecionadas na atividade original também na duplicada
    assert sorted(config_duplicada["identificationFields"]) == sorted(
        config_origem["identificationFields"]
    ), (
        f"Informações divergem — origem={config_origem['identificationFields']!r}, "
        f"duplicada={config_duplicada['identificationFields']!r}"
    )
    assert config_duplicada["fontPosition"] == config_origem["fontPosition"], (
        f"Posição divergente — origem={config_origem['fontPosition']!r}, "
        f"duplicada={config_duplicada['fontPosition']!r}"
    )
    assert config_duplicada["fontMovement"] == config_origem["fontMovement"], (
        f"Tipo de exibição divergente — origem={config_origem['fontMovement']!r}, "
        f"duplicada={config_duplicada['fontMovement']!r}"
    )

    # Passo 6 — Verificar 'Tamanho da fonte' e 'Cor da fonte'
    # Esperado: Mesmos valores da atividade original estão definidos na duplicada
    assert config_duplicada["fontSize"] == config_origem["fontSize"], (
        f"Tamanho da fonte divergente — origem={config_origem['fontSize']!r}, "
        f"duplicada={config_duplicada['fontSize']!r}"
    )
    assert config_duplicada["fontColor"] == config_origem["fontColor"], (
        f"Cor da fonte divergente — origem={config_origem['fontColor']!r}, "
        f"duplicada={config_duplicada['fontColor']!r}"
    )

    print(f"[T-1598] config origem: {config_origem}")
    print(f"[T-1598] config duplicada (id={NOVO_ID}): {config_duplicada}")
