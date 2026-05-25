"""Faz git add/commit/push das evidências de uma execução.

Usado pelo botão 'Commitar evidências' na aba Resultado. Devolve um
CommitResult com SHA e URL pública (se o remote origin estiver configurado
pra GitHub).

NUNCA adiciona Co-Authored-By: Claude — só Dante de Oliveira Tavares.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CommitResult:
    sha: str  # short SHA
    url: Optional[str] = None  # link público (GitHub) ou None se sem remote
    arquivos: list[str] | None = None


class CommitFalhou(Exception):
    pass


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _short_sha(cwd: Path) -> str:
    res = _run(["git", "rev-parse", "--short", "HEAD"], cwd)
    if res.returncode != 0:
        raise CommitFalhou(f"git rev-parse falhou: {res.stderr.strip()}")
    return res.stdout.strip()


def _remote_url(cwd: Path) -> Optional[str]:
    """Retorna a URL do remote origin, ou None se não tiver."""
    res = _run(["git", "config", "--get", "remote.origin.url"], cwd)
    if res.returncode != 0:
        return None
    return res.stdout.strip() or None


def _normalizar_remote_para_github(remote_url: str) -> Optional[str]:
    """Converte git@github.com:user/repo.git e https://github.com/user/repo.git
    para https://github.com/user/repo (sem .git)."""
    if not remote_url:
        return None
    # SSH form: git@github.com:user/repo.git
    m = re.match(r"git@github\.com:([^/]+)/(.+?)(?:\.git)?$", remote_url)
    if m:
        return f"https://github.com/{m.group(1)}/{m.group(2)}"
    # HTTPS form: https://github.com/user/repo.git
    m = re.match(r"https?://github\.com/([^/]+)/(.+?)(?:\.git)?/?$", remote_url)
    if m:
        return f"https://github.com/{m.group(1)}/{m.group(2)}"
    return None


def _construir_commit_url(remote_url: Optional[str], sha: str) -> Optional[str]:
    if not remote_url:
        return None
    base = _normalizar_remote_para_github(remote_url)
    if not base:
        return None
    return f"{base}/commit/{sha}"


def _ha_mudancas_no_index(cwd: Path) -> bool:
    """Verifica se há algo no index pra commitar."""
    res = _run(["git", "diff", "--cached", "--name-only"], cwd)
    return res.returncode == 0 and bool(res.stdout.strip())


def commitar_evidencias(
    project_root: Path,
    pasta_evidencias: Path,
    mensagem: str,
    *,
    push: bool = True,
) -> Optional[CommitResult]:
    """Adiciona arquivos da pasta_evidencias, commita e faz push.

    Retorna None se não houve mudanças pra commitar.
    Lança CommitFalhou se algum passo do git falhou.
    """
    if not pasta_evidencias.exists():
        return None

    # 1. Add
    res = _run(["git", "add", "--", str(pasta_evidencias)], project_root)
    if res.returncode != 0:
        raise CommitFalhou(f"git add falhou: {res.stderr.strip()}")

    # 2. Verifica se tem algo a commitar (pasta pode estar gitignored)
    if not _ha_mudancas_no_index(project_root):
        return None

    # 3. Commit (sem Co-Authored-By Claude)
    res = _run(["git", "commit", "-m", mensagem], project_root)
    if res.returncode != 0:
        raise CommitFalhou(f"git commit falhou: {res.stderr.strip()}")

    sha = _short_sha(project_root)
    arquivos = _arquivos_do_commit(project_root, sha)

    # 4. Push (opcional)
    if push:
        res = _run(["git", "push", "origin", "HEAD"], project_root)
        if res.returncode != 0:
            # Push falhou mas o commit local foi feito — retornamos resultado sem URL
            return CommitResult(sha=sha, url=None, arquivos=arquivos)

    # 5. URL pública
    remote = _remote_url(project_root)
    url = _construir_commit_url(remote, sha)
    return CommitResult(sha=sha, url=url, arquivos=arquivos)


def _arquivos_do_commit(cwd: Path, sha: str) -> list[str]:
    res = _run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha], cwd)
    if res.returncode != 0:
        return []
    return [l.strip() for l in res.stdout.splitlines() if l.strip()]
