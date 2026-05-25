"""Parser do formato Retrabalho (do Artia).

O formato típico:

    :: Incidente identificado ::
    <descrição do bug>

    :: Passo a passo para reprodução ::
    » Editar modelo
    » Design
    » ...

    :: Comportamento esperado ::
    <o que deveria acontecer>

Diferente do formato T-XXXX (tabela estruturada), retrabalho é texto livre
com seções delimitadas por `:: nome ::`.
"""
from __future__ import annotations

import re

from app.state import CasoParseado


_SECAO_RE = re.compile(
    r"::\s*(incidente identificado|passo a passo para reprodução|"
    r"comportamento esperado|informações|evidência\(?s?\)?)\s*::",
    re.IGNORECASE,
)


def _extrair_secoes(texto: str) -> dict[str, str]:
    """Quebra o texto em seções pelo marcador `:: nome ::`. Devolve dict por nome normalizado."""
    secoes: dict[str, str] = {}
    matches = list(_SECAO_RE.finditer(texto))
    if not matches:
        return secoes
    for i, m in enumerate(matches):
        nome = m.group(1).lower().strip()
        # Normaliza
        if "incidente" in nome:
            chave = "incidente"
        elif "passo" in nome:
            chave = "passos"
        elif "esperado" in nome:
            chave = "esperado"
        elif "informa" in nome:
            chave = "informacoes"
        elif "evid" in nome:
            chave = "evidencias"
        else:
            chave = nome
        inicio = m.end()
        fim = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
        conteudo = texto[inicio:fim].strip()
        secoes[chave] = conteudo
    return secoes


def _extrair_passos(secao_passos: str) -> list[str]:
    """Cada linha começando com » é um passo. Vazias e comentários são ignorados."""
    passos = []
    for linha in secao_passos.splitlines():
        s = linha.strip()
        if s.startswith("»"):
            texto_passo = s[1:].strip()
            if texto_passo:
                passos.append(texto_passo)
    return passos


def parece_retrabalho(texto: str) -> bool:
    """Heurística: tem marcador de seção típico de retrabalho?"""
    return ":: Incidente identificado ::" in texto or "» " in texto


def parse_retrabalho(texto: str) -> CasoParseado:
    """Converte um texto de retrabalho em CasoParseado.

    - `objetivo` = descrição do incidente
    - `passos` = passos de reprodução (n, ação). O 'esperado' fica no último passo,
      contendo o comportamento esperado declarado.
    - `texto_bruto` = texto original
    """
    secoes = _extrair_secoes(texto)
    incidente = secoes.get("incidente", "").strip()
    passos_raw = _extrair_passos(secoes.get("passos", ""))
    esperado = secoes.get("esperado", "").strip()

    # Se o parser não achou seções (texto sem :: marcadores ::), tenta passos só com » :
    if not passos_raw and "» " in texto:
        passos_raw = _extrair_passos(texto)

    passos = []
    for i, acao in enumerate(passos_raw, start=1):
        # Comportamento esperado fica no último passo (é a validação final)
        esperado_passo = esperado if i == len(passos_raw) else ""
        passos.append({"n": i, "acao": acao, "esperado": esperado_passo})

    return CasoParseado(
        objetivo=incidente or "(sem descrição do incidente)",
        pre_condicoes=[],
        passos=passos,
        perfil=None,
        plataforma=None,
        ambiente="stage",
        texto_bruto=texto,
    )
