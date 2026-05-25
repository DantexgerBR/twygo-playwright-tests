"""Detecta links do jam.dev em texto e tenta baixar a evidência.

Jam.dev compartilha bugs via URLs como https://jam.dev/c/<id>. Cada página
tem meta tags og:image (se a evidência é um print) ou og:video (se é gravação).
Para QA, baixamos só imagens; vídeos retornamos um marcador pra a UI avisar.
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Literal, Union

import httpx

JAM_URL_REGEX = re.compile(
    r"https?://(?:www\.)?jam\.dev/c/([a-zA-Z0-9_-]+)",
    re.IGNORECASE,
)
OG_IMAGE_REGEX = re.compile(
    r'<meta\s+[^>]*property=["\']og:image["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
OG_VIDEO_REGEX = re.compile(
    r'<meta\s+[^>]*property=["\']og:video["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

TIMEOUT_SEGUNDOS = 10


def extrair_id_jam(url: str) -> str | None:
    """Retorna o ID Jam se a URL casa com o padrão, senão None."""
    m = JAM_URL_REGEX.search(url)
    return m.group(1) if m else None


def encontrar_links_jam(texto: str) -> list[str]:
    """Devolve todas as URLs Jam.dev encontradas no texto."""
    return [m.group(0) for m in JAM_URL_REGEX.finditer(texto)]


def extrair_og_image(html: str) -> str | None:
    m = OG_IMAGE_REGEX.search(html)
    return m.group(1) if m else None


def extrair_og_video(html: str) -> str | None:
    m = OG_VIDEO_REGEX.search(html)
    return m.group(1) if m else None


def fetch_jam_url(url: str, pasta_destino: Path) -> Union[Path, Literal["video"], None]:
    """Tenta baixar a evidência da URL Jam.

    Retorna:
    - Path do arquivo PNG salvo se for um print
    - 'video' (string) se a página é um vídeo (UI deve avisar)
    - None se URL inválida, 404, ou sem og:image/og:video
    """
    jam_id = extrair_id_jam(url)
    if not jam_id:
        return None

    try:
        resp = httpx.get(url, timeout=TIMEOUT_SEGUNDOS, follow_redirects=True)
    except httpx.HTTPError:
        return None

    if resp.status_code != 200:
        return None

    if extrair_og_video(resp.text):
        return "video"

    img_url = extrair_og_image(resp.text)
    if not img_url:
        return None

    try:
        img_resp = httpx.get(img_url, timeout=TIMEOUT_SEGUNDOS, follow_redirects=True)
    except httpx.HTTPError:
        return None
    if img_resp.status_code != 200:
        return None

    pasta_destino.mkdir(parents=True, exist_ok=True)
    nome = f"jam_{jam_id}_{int(time.time())}.png"
    destino = pasta_destino / nome
    destino.write_bytes(img_resp.content)
    return destino
