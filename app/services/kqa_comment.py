"""Gera comentário no padrão KQA (⇝ QA ⇜) pra colar de volta no Artia.

Padrão definido pelo usuário:

    ⇝ QA ⇜
    :: Teste ::
    ✅ Passou
    :: Ambiente ::
    🧪 Stage
    :: Validação ::
    <texto>
    :: Obs ::
    <texto opcional>
    :: Evidência(s) ::
    <lista>
    Evidência no link: <URL do commit ou link externo>
"""
from __future__ import annotations

from pathlib import Path

from app.state import Laudo


_TEXTO_LAUDO = {
    "corrigido": "✅ Passou",
    "ainda_quebrado": "❌ Falhou",
    "inconclusivo": "⚠️ Inconclusivo",
}


def gerar_comentario_kqa(
    laudo: Laudo,
    justificativa: str,
    evidencias: list[Path] | None = None,
    *,
    ambiente: str = "Stage",
    obs: str = "",
    commit_url: str = "",
) -> str:
    """Monta o texto pronto pra colar no Artia.

    Args:
        laudo: "corrigido" | "ainda_quebrado" | "inconclusivo"
        justificativa: o que o agente concluiu, em texto livre
        evidencias: lista de paths de prints/screenshots (mostra só o nome do arquivo)
        ambiente: nome do ambiente testado (default "Stage")
        obs: observações adicionais (omite a seção se vazio)
        commit_url: link público do commit das evidências (omite linha se vazio)
    """
    teste_str = _TEXTO_LAUDO.get(laudo, str(laudo))
    ev_str = _formatar_evidencias(evidencias or [])

    linhas = [
        "⇝ QA ⇜",
        ":: Teste ::",
        teste_str,
        ":: Ambiente ::",
        f"🧪 {ambiente}",
        ":: Validação ::",
        justificativa.strip() or "(sem detalhes)",
    ]
    if obs.strip():
        linhas.extend([":: Obs ::", obs.strip()])
    linhas.extend([":: Evidência(s) ::", ev_str])
    if commit_url.strip():
        linhas.append(f"Evidência no link: {commit_url.strip()}")

    return "\n".join(linhas)


def _formatar_evidencias(evidencias: list[Path]) -> str:
    if not evidencias:
        return "(sem evidências anexadas)"
    return "\n".join(f"- {Path(e).name}" for e in evidencias)
