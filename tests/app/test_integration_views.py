"""Testes de integração dos handlers das views.

Bypass Flet UI: monta a view com Page mockada, encontra os Containers
clicáveis no tree por tooltip, chama on_click direto. Asserta estado.

Não testa rendering visual — só lógica/estado.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import flet as ft
import pytest

from app.state import AppState, CasoParseado, Evidencia


# ---------------------------------------------------------------------------
# Helpers de inspeção
# ---------------------------------------------------------------------------


def walk(c, depth=0):
    """Walk Flet tree em profundidade, yielding cada controle."""
    if c is None:
        return
    yield c
    if hasattr(c, "content") and c.content is not None and c.content is not c:
        yield from walk(c.content, depth + 1)
    if hasattr(c, "controls") and c.controls:
        for sub in c.controls:
            yield from walk(sub, depth + 1)


def encontrar_botao_por_tooltip(root, tooltip: str):
    for ctrl in walk(root):
        tt = getattr(ctrl, "tooltip", None)
        oc = getattr(ctrl, "on_click", None)
        if tt == tooltip and oc is not None:
            return ctrl
    return None


def encontrar_icon_button_por_tooltip(root, tooltip: str):
    """IconButtons em vez de Containers clicáveis."""
    for ctrl in walk(root):
        if isinstance(ctrl, ft.IconButton):
            if getattr(ctrl, "tooltip", None) == tooltip:
                return ctrl
    return None


def mock_page():
    page = MagicMock()
    page.update = MagicMock()
    page.overlay = []
    page.controls = []
    page.show_dialog = MagicMock()
    page.pop_dialog = MagicMock()
    return page


# ---------------------------------------------------------------------------
# Boot test
# ---------------------------------------------------------------------------


def test_imports_modulos_principais():
    """Todos os módulos importam sem erro de sintaxe ou dependência."""
    import app.main  # noqa
    import app.state  # noqa
    import app.theme  # noqa
    import app.icons  # noqa
    import app.ui_kit  # noqa
    import app.views.login_view  # noqa
    import app.views.documentacao_view  # noqa
    import app.views.caso_view  # noqa
    import app.views.evidencias_view  # noqa
    import app.views.execucao_view  # noqa
    import app.views.resultado_view  # noqa
    import app.services.credentials  # noqa
    import app.services.clipboard  # noqa
    import app.services.file_dialog  # noqa
    import app.services.jam_fetcher  # noqa
    import app.services.doc_loader  # noqa
    import app.services.gitignore_guard  # noqa


def test_state_initialization():
    s = AppState(Path('.').resolve())
    assert s.modo == "retrabalho"
    assert s.evidencias == []
    assert s.caso is None
    assert s.projeto_ativo is None


# ---------------------------------------------------------------------------
# evidencias_view
# ---------------------------------------------------------------------------


def test_evidencias_view_constroi_sem_erro():
    from app.views import evidencias_view
    page = mock_page()
    state = AppState(Path('.').resolve())
    view = evidencias_view.construir(page, state)
    assert view is not None
    # Encontra os 4 botões principais
    assert encontrar_botao_por_tooltip(view, "Anexar arquivo") is not None
    assert encontrar_botao_por_tooltip(view, "Colar imagem") is not None
    assert encontrar_botao_por_tooltip(view, "Buscar links Jam") is not None
    assert encontrar_botao_por_tooltip(view, "Limpar tudo") is not None


def test_evidencias_view_paste_sem_imagem_na_clipboard(tmp_path):
    from app.views import evidencias_view
    page = mock_page()
    state = AppState(tmp_path)
    view = evidencias_view.construir(page, state)
    btn = encontrar_botao_por_tooltip(view, "Colar imagem")

    with patch("app.views.evidencias_view.pegar_imagem_da_clipboard", return_value=None):
        btn.on_click(None)

    # Estado não deve mudar (clipboard estava vazio)
    assert len(state.evidencias) == 0


def test_evidencias_view_paste_com_imagem_na_clipboard(tmp_path):
    from app.views import evidencias_view
    page = mock_page()
    state = AppState(tmp_path)
    view = evidencias_view.construir(page, state)
    btn = encontrar_botao_por_tooltip(view, "Colar imagem")

    fake_path = tmp_path / "evidencias" / "_sessao_atual" / "paste_fake.png"
    fake_path.parent.mkdir(parents=True, exist_ok=True)
    fake_path.write_bytes(b"fake")

    with patch("app.views.evidencias_view.pegar_imagem_da_clipboard", return_value=fake_path):
        btn.on_click(None)

    assert len(state.evidencias) == 1
    ev = state.evidencias[0]
    assert ev.origem == "paste"
    assert ev.tipo == "print"
    assert ev.path == fake_path


def test_evidencias_view_anexar_com_arquivos(tmp_path):
    from app.views import evidencias_view
    page = mock_page()
    state = AppState(tmp_path)
    view = evidencias_view.construir(page, state)
    btn = encontrar_botao_por_tooltip(view, "Anexar arquivo")

    fake_img = tmp_path / "foo.png"
    fake_img.write_bytes(b"img")
    fake_vid = tmp_path / "bar.mp4"
    fake_vid.write_bytes(b"vid")

    with patch("app.views.evidencias_view.escolher_arquivos", return_value=[fake_img, fake_vid]):
        btn.on_click(None)

    assert len(state.evidencias) == 2
    tipos = {ev.tipo for ev in state.evidencias}
    assert tipos == {"print", "video"}
    assert all(ev.origem == "upload" for ev in state.evidencias)


def test_evidencias_view_anexar_cancelado(tmp_path):
    from app.views import evidencias_view
    page = mock_page()
    state = AppState(tmp_path)
    view = evidencias_view.construir(page, state)
    btn = encontrar_botao_por_tooltip(view, "Anexar arquivo")

    with patch("app.views.evidencias_view.escolher_arquivos", return_value=[]):
        btn.on_click(None)

    assert len(state.evidencias) == 0


def test_evidencias_view_buscar_jam_sem_caso(tmp_path):
    from app.views import evidencias_view
    page = mock_page()
    state = AppState(tmp_path)
    view = evidencias_view.construir(page, state)
    btn = encontrar_botao_por_tooltip(view, "Buscar links Jam")

    btn.on_click(None)

    # Sem caso, não adiciona nada
    assert len(state.evidencias) == 0


def test_evidencias_view_buscar_jam_caso_sem_links(tmp_path):
    from app.views import evidencias_view
    page = mock_page()
    state = AppState(tmp_path)
    state.caso = CasoParseado(texto_bruto="só texto sem link nenhum")
    view = evidencias_view.construir(page, state)
    btn = encontrar_botao_por_tooltip(view, "Buscar links Jam")

    btn.on_click(None)

    assert len(state.evidencias) == 0


def test_evidencias_view_buscar_jam_com_link_print(tmp_path):
    from app.views import evidencias_view
    page = mock_page()
    state = AppState(tmp_path)
    state.caso = CasoParseado(
        texto_bruto="ver bug em https://jam.dev/c/abc123"
    )
    view = evidencias_view.construir(page, state)
    btn = encontrar_botao_por_tooltip(view, "Buscar links Jam")

    fake_jam_path = tmp_path / "evidencias" / "_sessao_atual" / "jam_abc123_1.png"
    fake_jam_path.parent.mkdir(parents=True, exist_ok=True)
    fake_jam_path.write_bytes(b"jam-img")

    with patch("app.views.evidencias_view.fetch_jam_url", return_value=fake_jam_path):
        btn.on_click(None)

    assert len(state.evidencias) == 1
    ev = state.evidencias[0]
    assert ev.origem == "jam"
    assert ev.tipo == "print"


def test_evidencias_view_buscar_jam_com_link_video(tmp_path):
    from app.views import evidencias_view
    page = mock_page()
    state = AppState(tmp_path)
    state.caso = CasoParseado(
        texto_bruto="bug em vídeo: https://jam.dev/c/vid456"
    )
    view = evidencias_view.construir(page, state)
    btn = encontrar_botao_por_tooltip(view, "Buscar links Jam")

    with patch("app.views.evidencias_view.fetch_jam_url", return_value="video"):
        btn.on_click(None)

    assert len(state.evidencias) == 1
    ev = state.evidencias[0]
    assert ev.origem == "jam"
    assert ev.tipo == "video"


def test_evidencias_view_limpar(tmp_path):
    from app.views import evidencias_view
    page = mock_page()
    state = AppState(tmp_path)
    # Adiciona evidências antes
    state.evidencias = [
        Evidencia(path=tmp_path / "a.png", nome="a.png", tipo="print", origem="upload"),
        Evidencia(path=tmp_path / "b.png", nome="b.png", tipo="print", origem="paste"),
    ]
    view = evidencias_view.construir(page, state)
    btn = encontrar_botao_por_tooltip(view, "Limpar tudo")

    btn.on_click(None)

    assert state.evidencias == []


# ---------------------------------------------------------------------------
# login_view (regressão)
# ---------------------------------------------------------------------------


def test_login_view_salvar_valido(tmp_path):
    """Reusa o teste antigo de salvar, agora estrutural."""
    from app.views.login_view import construir_tela_login

    # gitignore guard precisa do .gitignore com os patterns
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text(
        ".env\n.env.*\napp/state.json\ndocs/projetos/*/_credentials.json\n",
        encoding="utf-8",
    )

    page = mock_page()
    success_called = []

    def on_success(cred):
        success_called.append(cred)

    tela = construir_tela_login(page, tmp_path, on_success)

    # Procura botão Salvar
    btn_salvar = encontrar_botao_por_tooltip(tela, "Salvar")
    assert btn_salvar is not None

    # Encontra TextFields e preenche
    tfs = [c for c in walk(tela) if isinstance(c, ft.TextField)]
    # ordem: URL, admin_email, admin_password, aluno_email, aluno_password, anthropic, org_id
    assert len(tfs) >= 7
    tfs[0].value = "https://teste.stage.twygoead.com/"
    tfs[1].value = "admin@teste.com"
    tfs[2].value = "senha"
    tfs[5].value = "sk-ant-fake"

    btn_salvar.on_click(None)

    assert len(success_called) == 1
    assert (tmp_path / ".env").exists()


def test_login_view_apagar(tmp_path):
    from app.views.login_view import construir_tela_login

    # Cria .env com algum conteúdo
    env_path = tmp_path / ".env"
    env_path.write_text("BASE_URL=foo\nADMIN_EMAIL=bar\n", encoding="utf-8")
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text(
        ".env\n.env.*\napp/state.json\ndocs/projetos/*/_credentials.json\n",
        encoding="utf-8",
    )

    page = mock_page()
    tela = construir_tela_login(page, tmp_path, lambda _c: None)

    btn_apagar = encontrar_botao_por_tooltip(tela, "Esquecer credenciais")
    assert btn_apagar is not None
    btn_apagar.on_click(None)

    # .env não existe mais (ou está sem as chaves de credencial)
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        assert "BASE_URL=" not in content or "BASE_URL=\n" in content or "BASE_URL=" not in content


# ---------------------------------------------------------------------------
# documentacao_view
# ---------------------------------------------------------------------------


def test_documentacao_view_constroi_sem_erro(tmp_path):
    from app.views import documentacao_view
    page = mock_page()
    state = AppState(tmp_path)
    view = documentacao_view.construir(page, state)
    assert view is not None
    # Botão Anexar arquivo presente
    assert encontrar_botao_por_tooltip(view, "Anexar arquivo") is not None


def test_documentacao_view_criar_projeto_via_state(tmp_path):
    """Não testa o dialog (precisa UI), mas testa que criar via state funciona."""
    state = AppState(tmp_path)
    ok = state.criar_projeto("teste_projeto")
    assert ok is True
    projetos = state.listar_projetos()
    assert "teste_projeto" in projetos
    assert (tmp_path / "docs" / "projetos" / "teste_projeto").is_dir()


def test_documentacao_view_adicionar_doc_via_state(tmp_path):
    state = AppState(tmp_path)
    state.criar_projeto("p1")
    state.projeto_ativo = "p1"

    # Cria um .md fake fora do projeto
    fake = tmp_path / "fora.md"
    fake.write_text("# Regra de negocio\n", encoding="utf-8")

    doc = state.adicionar_doc(fake)
    assert doc is not None
    assert doc.tipo == "md"
    assert len(state.documentacao) == 1


# ---------------------------------------------------------------------------
# caso_view
# ---------------------------------------------------------------------------


def test_caso_view_constroi_sem_erro(tmp_path):
    from app.views import caso_view
    page = mock_page()
    state = AppState(tmp_path)
    view = caso_view.construir(page, state)
    assert view is not None
    assert encontrar_botao_por_tooltip(view, "Analisar") is not None
    assert encontrar_botao_por_tooltip(view, "Limpar") is not None


def test_caso_view_analisar_texto_vazio(tmp_path):
    from app.views import caso_view
    page = mock_page()
    state = AppState(tmp_path)
    view = caso_view.construir(page, state)
    btn = encontrar_botao_por_tooltip(view, "Analisar")

    btn.on_click(None)

    # Sem texto, caso continua None
    assert state.caso is None


def test_caso_view_analisar_retrabalho(tmp_path):
    from app.views import caso_view
    page = mock_page()
    state = AppState(tmp_path)
    view = caso_view.construir(page, state)

    # Preenche o textarea
    tfs = [c for c in walk(view) if isinstance(c, ft.TextField)]
    assert len(tfs) >= 1
    tfs[0].value = """:: Incidente identificado ::
Bug aleatorio

    :: Passo a passo para reprodução ::
» Passo 1
» Passo 2

    :: Comportamento esperado ::
Funcionar"""

    btn = encontrar_botao_por_tooltip(view, "Analisar")
    btn.on_click(None)

    # Caso deve ter sido parseado (mesmo se 0 passos detectados pelo parser, o state.caso é setado)
    assert state.caso is not None
    assert state.caso.texto_bruto != ""
