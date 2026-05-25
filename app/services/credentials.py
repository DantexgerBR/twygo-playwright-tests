"""Gerencia leitura e escrita de credenciais em .env.

Recusa salvar se o .gitignore não cobre os arquivos sensíveis.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

from app.services.gitignore_guard import gitignore_protege_credenciais


CHAVES_CREDENCIAIS = [
    "BASE_URL",
    "ADMIN_EMAIL",
    "ADMIN_PASSWORD",
    "ALUNO_EMAIL",
    "ALUNO_PASSWORD",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "ORG_ID",
]


@dataclass
class Credenciais:
    base_url: str = ""
    admin_email: str = ""
    admin_password: str = ""
    aluno_email: str = ""
    aluno_password: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    org_id: str = ""

    def completo_para_admin(self) -> bool:
        # Pelo menos uma das chaves de LLM precisa estar definida (Gemini é o default).
        tem_llm = bool(self.gemini_api_key) or bool(self.anthropic_api_key)
        return all([
            self.base_url,
            self.admin_email,
            self.admin_password,
            tem_llm,
        ])

    @classmethod
    def from_env(cls, env: dict) -> "Credenciais":
        return cls(
            base_url=env.get("BASE_URL", "") or "",
            admin_email=env.get("ADMIN_EMAIL", "") or "",
            admin_password=env.get("ADMIN_PASSWORD", "") or "",
            aluno_email=env.get("ALUNO_EMAIL", "") or "",
            aluno_password=env.get("ALUNO_PASSWORD", "") or "",
            anthropic_api_key=env.get("ANTHROPIC_API_KEY", "") or "",
            gemini_api_key=env.get("GEMINI_API_KEY", "") or "",
            org_id=env.get("ORG_ID", "") or "",
        )


def caminho_env(project_root: Path) -> Path:
    return project_root / ".env"


def carregar(project_root: Path) -> Credenciais:
    env_path = caminho_env(project_root)
    if not env_path.exists():
        return Credenciais()
    return Credenciais.from_env(dotenv_values(env_path))


class GitignoreNaoProteje(Exception):
    def __init__(self, faltando: list[str]) -> None:
        super().__init__(
            f"Padrões ausentes do .gitignore: {', '.join(faltando)}"
        )
        self.faltando = faltando


def salvar(project_root: Path, cred: Credenciais) -> None:
    ok, faltando = gitignore_protege_credenciais(project_root)
    if not ok:
        raise GitignoreNaoProteje(faltando)

    env_path = caminho_env(project_root)
    existing = dict(dotenv_values(env_path)) if env_path.exists() else {}
    existing.update({
        "BASE_URL": cred.base_url,
        "ADMIN_EMAIL": cred.admin_email,
        "ADMIN_PASSWORD": cred.admin_password,
        "ALUNO_EMAIL": cred.aluno_email,
        "ALUNO_PASSWORD": cred.aluno_password,
        "ANTHROPIC_API_KEY": cred.anthropic_api_key,
        "GEMINI_API_KEY": cred.gemini_api_key,
        "ORG_ID": cred.org_id,
    })
    linhas = [f"{chave}={valor}" for chave, valor in existing.items()]
    env_path.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def apagar_salvas(project_root: Path) -> None:
    env_path = caminho_env(project_root)
    if not env_path.exists():
        return
    existing = dict(dotenv_values(env_path))
    for chave in CHAVES_CREDENCIAIS:
        existing.pop(chave, None)
    if existing:
        linhas = [f"{chave}={valor}" for chave, valor in existing.items()]
        env_path.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    else:
        env_path.unlink()
