"""Testes do jam_fetcher: parser de URL, parser de HTML, fluxo end-to-end com mock."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.jam_fetcher import (
    extrair_id_jam,
    extrair_og_image,
    extrair_og_video,
    fetch_jam_url,
)


def test_extrair_id_jam_url_padrao():
    assert extrair_id_jam("https://jam.dev/c/abc123") == "abc123"


def test_extrair_id_jam_com_www():
    assert extrair_id_jam("https://www.jam.dev/c/xyz789") == "xyz789"


def test_extrair_id_jam_com_query():
    assert extrair_id_jam("https://jam.dev/c/abc123?ref=foo") == "abc123"


def test_extrair_id_jam_invalida_retorna_none():
    assert extrair_id_jam("https://google.com") is None
    assert extrair_id_jam("nao-uma-url") is None


def test_extrair_og_image_html_valido():
    html = '''
    <html><head>
    <meta property="og:image" content="https://cdn.jam.dev/abc.png" />
    </head></html>
    '''
    assert extrair_og_image(html) == "https://cdn.jam.dev/abc.png"


def test_extrair_og_image_html_sem_og():
    html = "<html><head><title>foo</title></head></html>"
    assert extrair_og_image(html) is None


def test_extrair_og_video_html_com_video():
    html = '<meta property="og:video" content="https://cdn.jam.dev/v.mp4" />'
    assert extrair_og_video(html) == "https://cdn.jam.dev/v.mp4"


def test_extrair_og_video_html_sem_video():
    html = '<meta property="og:image" content="foo.png" />'
    assert extrair_og_video(html) is None


def test_fetch_jam_url_imagem_baixa_e_retorna_path(tmp_path):
    html_resp = MagicMock()
    html_resp.status_code = 200
    html_resp.text = '<meta property="og:image" content="https://cdn.jam.dev/abc.png" />'

    img_resp = MagicMock()
    img_resp.status_code = 200
    img_resp.content = b"fake-png-bytes"

    with patch("httpx.get", side_effect=[html_resp, img_resp]):
        resultado = fetch_jam_url("https://jam.dev/c/abc123", tmp_path)

    assert isinstance(resultado, Path)
    assert resultado.exists()
    assert resultado.read_bytes() == b"fake-png-bytes"
    assert resultado.suffix == ".png"


def test_fetch_jam_url_video_retorna_string_video(tmp_path):
    html_resp = MagicMock()
    html_resp.status_code = 200
    html_resp.text = '<meta property="og:video" content="https://cdn.jam.dev/v.mp4" />'

    with patch("httpx.get", return_value=html_resp):
        resultado = fetch_jam_url("https://jam.dev/c/v123", tmp_path)

    assert resultado == "video"


def test_fetch_jam_url_404_retorna_none(tmp_path):
    resp = MagicMock()
    resp.status_code = 404
    resp.text = ""

    with patch("httpx.get", return_value=resp):
        assert fetch_jam_url("https://jam.dev/c/notfound", tmp_path) is None


def test_fetch_jam_url_invalida_retorna_none(tmp_path):
    assert fetch_jam_url("https://google.com", tmp_path) is None
