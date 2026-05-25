"""Testes do git_committer: mockam subprocess pra simular git."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.git_committer import (
    CommitFalhou,
    _normalizar_remote_para_github,
    _construir_commit_url,
    commitar_evidencias,
)


def _proc(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    p = MagicMock()
    p.returncode = returncode
    p.stdout = stdout
    p.stderr = stderr
    return p


def test_normalizar_remote_https():
    assert (
        _normalizar_remote_para_github("https://github.com/DantexgerBR/repo.git")
        == "https://github.com/DantexgerBR/repo"
    )


def test_normalizar_remote_ssh():
    assert (
        _normalizar_remote_para_github("git@github.com:DantexgerBR/repo.git")
        == "https://github.com/DantexgerBR/repo"
    )


def test_normalizar_remote_sem_dotgit():
    assert (
        _normalizar_remote_para_github("https://github.com/DantexgerBR/repo")
        == "https://github.com/DantexgerBR/repo"
    )


def test_normalizar_remote_nao_github_retorna_none():
    assert _normalizar_remote_para_github("https://gitlab.com/foo/bar.git") is None


def test_construir_commit_url():
    url = _construir_commit_url("git@github.com:user/repo.git", "abc123")
    assert url == "https://github.com/user/repo/commit/abc123"


def test_construir_commit_url_sem_remote():
    assert _construir_commit_url(None, "abc") is None


def test_commitar_pasta_nao_existe(tmp_path):
    """Se a pasta de evidências não existe, retorna None silenciosamente."""
    result = commitar_evidencias(tmp_path, tmp_path / "inexistente", "msg")
    assert result is None


def test_commitar_sem_mudancas_no_index_retorna_none(tmp_path):
    """git add roda mas index continua vazio — não commita."""
    pasta = tmp_path / "evid"
    pasta.mkdir()
    (pasta / "x.txt").write_text("hi")

    def fake_run(cmd, **kwargs):
        if cmd[1] == "add":
            return _proc(0)
        if cmd[1] == "diff" and "--cached" in cmd:
            return _proc(0, stdout="")  # vazio = nada no index
        return _proc(0)

    with patch("subprocess.run", side_effect=fake_run):
        result = commitar_evidencias(tmp_path, pasta, "msg")

    assert result is None


def test_commitar_caminho_feliz_retorna_sha_e_url(tmp_path):
    pasta = tmp_path / "evid"
    pasta.mkdir()
    (pasta / "x.txt").write_text("hi")

    chamadas = []

    def fake_run(cmd, **kwargs):
        chamadas.append(cmd)
        if cmd[1] == "add":
            return _proc(0)
        if cmd[1] == "diff" and "--cached" in cmd:
            return _proc(0, stdout="evid/x.txt\n")
        if cmd[1] == "commit":
            return _proc(0, stdout="[main abc123] msg")
        if cmd[1] == "rev-parse":
            return _proc(0, stdout="abc123\n")
        if cmd[1] == "push":
            return _proc(0)
        if cmd[1] == "config":
            return _proc(0, stdout="git@github.com:DantexgerBR/twygo.git\n")
        if cmd[1] == "diff-tree":
            return _proc(0, stdout="evid/x.txt\n")
        return _proc(0)

    with patch("subprocess.run", side_effect=fake_run):
        result = commitar_evidencias(tmp_path, pasta, "test commit")

    assert result is not None
    assert result.sha == "abc123"
    assert result.url == "https://github.com/DantexgerBR/twygo/commit/abc123"
    assert result.arquivos == ["evid/x.txt"]
    # commit foi chamado, push foi chamado
    assert any(c[1] == "commit" for c in chamadas)
    assert any(c[1] == "push" for c in chamadas)


def test_commitar_push_falha_ainda_retorna_resultado_local(tmp_path):
    """Se push falha mas commit local funcionou, retorna sha mas url=None."""
    pasta = tmp_path / "evid"
    pasta.mkdir()
    (pasta / "x.txt").write_text("hi")

    def fake_run(cmd, **kwargs):
        if cmd[1] == "add":
            return _proc(0)
        if cmd[1] == "diff" and "--cached" in cmd:
            return _proc(0, stdout="x.txt")
        if cmd[1] == "commit":
            return _proc(0)
        if cmd[1] == "rev-parse":
            return _proc(0, stdout="def456")
        if cmd[1] == "push":
            return _proc(1, stderr="rejected")
        if cmd[1] == "diff-tree":
            return _proc(0, stdout="x.txt")
        return _proc(0)

    with patch("subprocess.run", side_effect=fake_run):
        result = commitar_evidencias(tmp_path, pasta, "msg")

    assert result is not None
    assert result.sha == "def456"
    assert result.url is None  # push falhou, sem URL


def test_commitar_push_desligado(tmp_path):
    """push=False pula a etapa de push e ainda retorna URL se remote conhecido."""
    pasta = tmp_path / "evid"
    pasta.mkdir()
    (pasta / "x.txt").write_text("hi")

    def fake_run(cmd, **kwargs):
        if cmd[1] == "add":
            return _proc(0)
        if cmd[1] == "diff" and "--cached" in cmd:
            return _proc(0, stdout="x.txt")
        if cmd[1] == "commit":
            return _proc(0)
        if cmd[1] == "rev-parse":
            return _proc(0, stdout="ghi789")
        if cmd[1] == "push":
            return _proc(1, stderr="should not be called")
        if cmd[1] == "config":
            return _proc(0, stdout="https://github.com/x/y.git")
        if cmd[1] == "diff-tree":
            return _proc(0)
        return _proc(0)

    with patch("subprocess.run", side_effect=fake_run):
        result = commitar_evidencias(tmp_path, pasta, "msg", push=False)

    assert result is not None
    assert result.sha == "ghi789"
    assert result.url == "https://github.com/x/y/commit/ghi789"


def test_commitar_add_falha_levanta(tmp_path):
    pasta = tmp_path / "evid"
    pasta.mkdir()

    def fake_run(cmd, **kwargs):
        if cmd[1] == "add":
            return _proc(1, stderr="path inválido")
        return _proc(0)

    with patch("subprocess.run", side_effect=fake_run):
        with pytest.raises(CommitFalhou, match="add"):
            commitar_evidencias(tmp_path, pasta, "msg")
