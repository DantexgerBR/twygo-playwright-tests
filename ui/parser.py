"""Parser do caso de teste no formato Twygo.

Aceita o texto que o usuário cola da plataforma de gestão de casos
(linhas livres com marcadores de seção) e devolve uma struct:

    {
      "objetivo": str,
      "pre_condicoes": [str, ...],
      "perfil": str | None,
      "plataforma": str | None,
      "ambiente": str | None,
      "passos": [{"n": int, "acao": str, "esperado": str}, ...],
    }

O formato do texto colado varia bastante. O parser é tolerante:
- Reconhece "Pré-condições" em qualquer caso.
- Os passos vêm como blocos separados começando por número, com colunas
  "Ações do Passo" e "Resultados Esperados" intercaladas com metadados
  de execução (Manual, datas, "Passou", anexos) que devem ser descartados.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Passo:
    n: int
    acao: str
    esperado: str


@dataclass
class Caso:
    objetivo: str
    pre_condicoes: list[str] = field(default_factory=list)
    perfil: Optional[str] = None
    plataforma: Optional[str] = None
    ambiente: Optional[str] = None
    passos: list[Passo] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


_LIXO = (
    "manual",
    "testado na org",
    "passou",
    "falhou",
    "bloqueado",
    "em suspenso",
    "arquivo:",
    "o tamanho máximo",
    "filename must verify",
    "allowed files",
    "no file chosen",
    "atenção:",
    "ao guardar passos",
    "tipo de execução",
    "estimação da duração",
    "perfil de usuário testado",
    "plataforma testada",
    "tipo ambiente testado",
    "tipo de ambiente",
    "perfil de usuário",
    "limpar todas as notas",
    "limpar todos os estados",
    "notas da execução",
    "status da execução",
    "execução",
    "ações do passo",
    "resultados esperados",
)


def _eh_lixo(linha: str) -> bool:
    low = linha.strip().lower()
    if not low:
        return True
    if re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", low):
        return True
    if low in {"#", "_", "—"}:
        return True
    return any(low.startswith(t) for t in _LIXO)


def _limpar_acao_esperado(texto: str) -> str:
    """Remove sufixos comuns de relato (ex: 'Testado na org...', anexos)."""
    if not texto:
        return ""
    linhas = []
    for ln in texto.splitlines():
        if _eh_lixo(ln):
            continue
        linhas.append(ln.strip())
    return " ".join(l for l in linhas if l).strip()


def parse_caso(texto: str) -> Caso:
    """Parse principal."""
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    linhas = texto.split("\n")

    # 1) Objetivo: primeira(s) linha(s) não vazias antes de "Pré-condições".
    objetivo_linhas: list[str] = []
    i = 0
    while i < len(linhas):
        ln = linhas[i].strip()
        if not ln:
            i += 1
            continue
        if re.match(r"^pr[eé]-?\s*condi[cç][oõ]es", ln, re.I):
            break
        objetivo_linhas.append(ln)
        i += 1
    objetivo = " ".join(objetivo_linhas).strip()

    caso = Caso(objetivo=objetivo)

    # 2) Pré-condições: bloco entre "Pré-condições" e a próxima seção
    # (Perfil / Tipo de ambiente / # / 1 ...).
    if i < len(linhas):
        i += 1  # pula a própria linha "Pré-condições"
        pre = []
        while i < len(linhas):
            ln = linhas[i].strip()
            if re.match(r"^perfil de usu[aá]rio\b", ln, re.I):
                break
            if re.match(r"^tipo de ambiente\b", ln, re.I):
                break
            if re.match(r"^#\s*ações?", ln, re.I):
                break
            # Primeiro passo: linha que começa com "1" sozinha ou "1\t..."
            if re.match(r"^1[\t\s]+\S", ln) and not re.match(r"^1\d", ln):
                break
            if ln:
                pre.append(ln)
            i += 1
        # Pré-condições podem vir tudo numa linha só, sem quebras: tenta dividir.
        if len(pre) == 1 and len(pre[0]) > 60:
            partes = re.split(
                r"\s+(?=Usu[aá]rio\b|Feature flag\b|Atividade\b|Aluno\b)", pre[0]
            )
            pre = [p.strip() for p in partes if p.strip()]
        caso.pre_condicoes = pre

    # 3) Perfil / Plataforma / Ambiente — captura onde aparecerem.
    for j, ln in enumerate(linhas):
        low = ln.lower()
        if "perfil de usuário testado" in low or low.startswith("perfil de usuário:"):
            valor = linhas[j + 1].strip() if j + 1 < len(linhas) else ""
            if valor and not _eh_lixo(valor):
                caso.perfil = valor
        if "plataforma testada" in low:
            valor = linhas[j + 1].strip() if j + 1 < len(linhas) else ""
            if valor and not _eh_lixo(valor):
                caso.plataforma = valor
        if "tipo ambiente testado" in low or "tipo de ambiente" in low:
            valor = linhas[j + 1].strip() if j + 1 < len(linhas) else ""
            if valor and not _eh_lixo(valor):
                caso.ambiente = valor

    # 4) Passos. Formatos suportados:
    #   (a) "N\tAção\tEsperado\tManual"  ← TestRail-like (texto colado da plataforma)
    #   (b) "N\tAção\tEsperado"
    #   (c) Linha "N" sozinha, com Ação e Esperado nas próximas linhas
    # Em todos, o "N" inicial deve estar no começo da linha.
    indices_passo = []
    for idx, ln in enumerate(linhas):
        m = re.match(r"^(\d{1,3})(\t|\s{2,}|$)", ln)
        if not m:
            continue
        n = int(m.group(1))
        if not (1 <= n <= 99):
            continue
        # Filtro: não pode ser uma linha que comece com um número grande (ano,
        # ID de atividade). 1-99 já filtra; mas evita falsos positivos quando
        # a linha começa com data tipo "19/05/2026" (regex acima exclui isso
        # porque o "/" não é tab/espaço duplo/fim).
        indices_passo.append((idx, n))

    for k, (idx, n) in enumerate(indices_passo):
        fim = indices_passo[k + 1][0] if k + 1 < len(indices_passo) else len(linhas)
        linha_inicial = linhas[idx]
        # Tenta extrair Ação e Esperado da própria linha (formato (a)/(b)).
        partes_tab = [p for p in re.split(r"\t+", linha_inicial) if p.strip()]
        acao = ""
        esperado = ""
        if len(partes_tab) >= 3:
            # partes_tab[0] é o "N", o resto é Ação/Esperado/(Execução)
            acao = partes_tab[1].strip()
            esperado = partes_tab[2].strip()
        elif len(partes_tab) == 2:
            acao = partes_tab[1].strip()
        else:
            # Formato (c): conteúdo nas próximas linhas.
            bloco_limpo = [
                ln.strip() for ln in linhas[idx + 1 : fim]
                if ln.strip() and not _eh_lixo(ln)
            ]
            if len(bloco_limpo) >= 2:
                acao, esperado = bloco_limpo[0], bloco_limpo[1]
            elif len(bloco_limpo) == 1:
                acao = bloco_limpo[0]

        if not acao:
            continue
        caso.passos.append(
            Passo(n=n, acao=_limpar_acao_esperado(acao), esperado=_limpar_acao_esperado(esperado))
        )

    return caso
