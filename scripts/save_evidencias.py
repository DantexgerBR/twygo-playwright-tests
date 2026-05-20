"""Copia evidências de test-results/ para evidencias/T-XXXX/ e imprime URLs públicas.

Uso:
    python scripts/save_evidencias.py T-1596 test-results/t1596/*.png

Saída (stdout): cada linha "<nome arquivo>\t<URL raw.githubusercontent.com>"

Convenção:
- `evidencias/` é commitada no repo (links permanentes).
- `test-results/` permanece no .gitignore (artefatos voláteis).
- Nomes dos arquivos copiados ficam mais limpos: tira o prefixo "tXXXX-".

Pra trocar o slug repo/branch, ajuste GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

GITHUB_OWNER = "DantexgerBR"
GITHUB_REPO = "twygo-playwright-tests"
GITHUB_BRANCH = "main"


def url_publica(rel_path: Path) -> str:
    return (
        f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/"
        f"{GITHUB_BRANCH}/{rel_path.as_posix()}"
    )


def _nome_limpo(nome: str) -> str:
    # Remove prefixo "tXXXX-" se houver (ex: "t1596-passo3.png" → "passo3.png")
    if "-" in nome and nome[1:].split("-", 1)[0].isdigit():
        return nome.split("-", 1)[1]
    return nome


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Uso: python scripts/save_evidencias.py T-XXXX <arquivo.png> [...]", file=sys.stderr)
        return 2
    caso = argv[0]
    if not caso.startswith("T-"):
        print(f"Primeiro argumento deve ser T-XXXX, recebi: {caso}", file=sys.stderr)
        return 2

    destino = Path("evidencias") / caso
    destino.mkdir(parents=True, exist_ok=True)

    for arg in argv[1:]:
        p = Path(arg)
        if not p.exists():
            print(f"{p}\tERRO: arquivo não encontrado", file=sys.stderr)
            continue
        novo_nome = _nome_limpo(p.name)
        alvo = destino / novo_nome
        shutil.copy2(p, alvo)
        print(f"{p}\t{url_publica(alvo)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
