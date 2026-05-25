"""Verifica se o stage da Twygo está respondendo antes de tentar executar testes.

Stage cai periodicamente quando devs atualizam o banco. O agente precisa
detectar isso e avisar amigavelmente, em vez de tentar logar e travar.
"""
from __future__ import annotations

from typing import Literal

import httpx


StatusStage = Literal["ok", "down", "erro"]

TIMEOUT_PADRAO = 5.0


def verificar_stage(base_url: str, timeout: float = TIMEOUT_PADRAO) -> StatusStage:
    """Faz um GET simples no base_url e classifica o resultado.

    Retorna:
    - "ok": stage respondeu 2xx ou 3xx (login redirect conta como OK)
    - "down": status 5xx, timeout, ou connection refused (devs reiniciando)
    - "erro": URL inválida ou erro de rede genérico (problema do cliente)
    """
    if not base_url:
        return "erro"

    try:
        resp = httpx.get(
            base_url,
            timeout=timeout,
            follow_redirects=False,
        )
    except httpx.ConnectError:
        return "down"
    except httpx.TimeoutException:
        return "down"
    except httpx.HTTPError:
        return "erro"
    except Exception:
        return "erro"

    if 500 <= resp.status_code < 600:
        return "down"
    if 200 <= resp.status_code < 400:
        return "ok"
    # 4xx — provavelmente página existe mas pediu auth ou rota errada; OK pro nosso uso
    return "ok"
