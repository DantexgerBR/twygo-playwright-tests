"""Captura imagem da área de transferência do Windows.

Usa PIL.ImageGrab.grabclipboard() — funciona com prints do Win+Shift+S,
PrintScreen, ou qualquer copy-image de browser.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional


def pegar_imagem_da_clipboard(pasta_destino: Path, prefixo: str = "clip") -> Optional[Path]:
    """Cola imagem da clipboard como PNG numa pasta. Retorna o path, ou None se vazio."""
    from PIL import ImageGrab

    img = ImageGrab.grabclipboard()
    if img is None:
        return None

    # ImageGrab pode devolver uma Image ou uma lista (caminhos de arquivos copiados).
    if isinstance(img, list):
        # Usuário copiou arquivos no explorer, não uma imagem
        return None

    pasta_destino.mkdir(parents=True, exist_ok=True)
    nome = f"{prefixo}_{int(time.time())}.png"
    destino = pasta_destino / nome
    img.save(destino, "PNG")
    return destino
