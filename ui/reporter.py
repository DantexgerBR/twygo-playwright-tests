"""Gera bug report no formato `:: Incidente identificado ::`."""
from __future__ import annotations

from ui.executor import ExecucaoResultado, PassoResultado
from ui.parser import Caso


def render_bug_report(
    resultado: ExecucaoResultado,
    base_url: str,
    admin_email: str,
    admin_password: str,
    aluno_email: str,
    aluno_password: str,
    org_id: str = "-1",
) -> str | None:
    """Se a execução falhou, retorna o relatório formatado. Senão None."""
    falha: PassoResultado | None = next((p for p in resultado.passos if p.status != "ok"), None)
    if not falha:
        return None

    caso = resultado.caso
    passos_str = []
    for p in caso.passos:
        if p.n < falha.n:
            passos_str.append(f"» Passo {p.n}: {p.acao}")
        elif p.n == falha.n:
            passos_str.append(f"» Passo {p.n} (FALHA): {p.acao}")
            break

    # decide login/senha do passo que falhou
    e_passo_aluno = "aluno" in falha.acao.lower() or "aprender" in falha.acao.lower()
    login = aluno_email if e_passo_aluno else admin_email
    senha = aluno_password if e_passo_aluno else admin_password

    evidencias = []
    if falha.screenshot_path:
        evidencias.append(("Screenshot do momento da falha", falha.screenshot_path))
    if falha.trace_path:
        evidencias.append(("Playwright trace (abra em https://trace.playwright.dev/)", falha.trace_path))

    if evidencias:
        evid_block = "\n".join(
            f"{desc}\nLink da evidência: {path}" for desc, path in evidencias
        )
    else:
        evid_block = "Sem evidência capturada\nLink da evidência: -"

    return (
        ":: Incidente identificado ::\n"
        f"{falha.mensagem or 'Passo falhou sem mensagem específica'}\n"
        "\n"
        "    :: Passo a passo para reprodução ::\n"
        + "\n".join(passos_str) + "\n"
        "\n"
        "    :: Comportamento esperado ::\n"
        f"{caso.passos[falha.n - 1].esperado}\n"
        "\n"
        "    :: Informações ::\n"
        f"url: {base_url}\n"
        f"login: {login}\n"
        f"senha: {senha}\n"
        f"org_id: {org_id}\n"
        f"Falha em: {falha.falha_em or 'ação'} | confidence LLM: {falha.confidence:.2f}\n"
        "\n"
        "    :: Evidência(s) ::\n"
        f"{evid_block}\n"
    )
