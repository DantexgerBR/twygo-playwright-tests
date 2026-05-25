"""Valida que arquivos sensíveis estão cobertos pelo .gitignore.

Usado antes de qualquer escrita de credenciais para prevenir vazamento acidental.
"""
from __future__ import annotations

from pathlib import Path

REQUIRED_PATTERNS: list[str] = [
    ".env",
    ".env.*",
    "app/state.json",
    "docs/projetos/*/_credentials.json",
]


def patterns_no_gitignore(project_root: Path) -> set[str]:
    gitignore = project_root / ".gitignore"
    if not gitignore.exists():
        return set()
    linhas = gitignore.read_text(encoding="utf-8").splitlines()
    return {
        linha.strip()
        for linha in linhas
        if linha.strip() and not linha.strip().startswith("#")
    }


def faltando_no_gitignore(
    project_root: Path,
    padroes: list[str] | None = None,
) -> list[str]:
    padroes = padroes if padroes is not None else REQUIRED_PATTERNS
    existentes = patterns_no_gitignore(project_root)
    return [p for p in padroes if p not in existentes]


def gitignore_protege_credenciais(project_root: Path) -> tuple[bool, list[str]]:
    faltando = faltando_no_gitignore(project_root)
    return (len(faltando) == 0, faltando)
