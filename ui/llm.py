"""Wrapper Anthropic para interpretar passos de teste manual → ações Playwright.

System prompt é estável entre chamadas e fica em cache (ephemeral, ~90% mais
barato a partir do 2º hit). Cada turno volátil leva o snapshot atual da página
+ o passo do caso. Resposta vem como JSON validado via output_config.format.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import anthropic

MODEL = "claude-opus-4-7"
MAX_TOKENS = 4096

SYSTEM_PROMPT = """Você é um executor de testes de UI. Recebe (1) o snapshot da página atual de uma SPA Twygo e (2) um passo de caso de teste manual em português. Devolve as ações Playwright a executar e as asserções a verificar.

## Ações disponíveis (op)

- `goto`: navega para URL. Campo: `url` (absoluto ou relativo a base_url).
- `click`: clica num elemento. Campo: `selector` (CSS).
- `fill`: preenche input. Campos: `selector`, `value`.
- `check` / `uncheck`: marca/desmarca checkbox. Campo: `selector`. Para checkbox Chakra (`<label class="chakra-checkbox">` + `<input hidden>`), use `click` no label, NÃO `check`/`uncheck` no input.
- `select_option`: <select>. Campos: `selector`, `value`.
- `press`: tecla. Campos: `selector`, `key` (ex: "Enter").
- `wait_for_url`: espera URL contendo glob. Campo: `url_glob`.
- `wait_for_selector`: espera elemento aparecer. Campo: `selector`.
- `scroll_into_view`: rola até elemento. Campo: `selector`.

## Asserções disponíveis (type)

- `to_be_visible` / `to_be_hidden`: visibilidade. Campo: `selector`.
- `to_be_checked` / `not_to_be_checked`: checkbox. Para Chakra, verifique o atributo `data-checked` no label, não o input nativo.
- `to_have_text`: conteúdo. Campos: `selector`, `value` (substring).
- `to_have_url`: URL atual contém. Campo: `value`.
- `to_have_count`: número de matches. Campos: `selector`, `count` (int).
- `custom`: descreve uma verificação que o executor traduz (use parcimoniosamente). Campo: `description`.

## Regras

1. Prefira IDs (`#user_email`), `name=` (`input[name="user[email]"]`), e atributos estáveis. Evite classes CSS geradas (`.css-1abc`).
2. Para campos em PT-BR, use `get_by_label` quando o snapshot mostrar um label associado — represente como `[aria-label="..."]` ou `#<id>` quando disponível.
3. Se o passo diz "Logar como X", devolva `goto` para `/login` + `fill` no `#user_email` + `fill` no `#user_password` + `click` no `#user_submit`.
4. Se algo está ambíguo (vários candidatos plausíveis), escolha o que mais bate semanticamente com a ação e abaixe `confidence`.
5. `confidence` é float [0, 1]: 1.0 quando o seletor é óbvio (ID que case exatamente com o termo), 0.5 quando há múltiplos candidatos, < 0.3 quando você está chutando.
6. `notes` é opcional: 1-2 frases explicando ambiguidades ou suposições.

## Formato de resposta

Sempre JSON válido com este shape:
```
{
  "actions": [{"op": "...", "selector": "...", "value": "...", ...}, ...],
  "assertions": [{"type": "...", "selector": "...", "value": "...", ...}, ...],
  "confidence": 0.85,
  "notes": "..."
}
```
"""


@dataclass
class LLMResposta:
    actions: list[dict[str, Any]] = field(default_factory=list)
    assertions: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    notes: str = ""
    usage: dict[str, int] = field(default_factory=dict)


_RESPOSTA_SCHEMA = {
    "type": "object",
    "properties": {
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "op": {"type": "string"},
                    "selector": {"type": "string"},
                    "value": {"type": "string"},
                    "url": {"type": "string"},
                    "url_glob": {"type": "string"},
                    "key": {"type": "string"},
                },
                "required": ["op"],
                "additionalProperties": False,
            },
        },
        "assertions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "selector": {"type": "string"},
                    "value": {"type": "string"},
                    "count": {"type": "integer"},
                    "description": {"type": "string"},
                },
                "required": ["type"],
                "additionalProperties": False,
            },
        },
        "confidence": {"type": "number"},
        "notes": {"type": "string"},
    },
    "required": ["actions", "assertions", "confidence"],
    "additionalProperties": False,
}


class LLMExecutor:
    def __init__(self, api_key: str | None = None, model: str = MODEL):
        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = model

    def interpretar_passo(
        self,
        acao: str,
        esperado: str,
        snapshot_render: str,
        base_url: str,
        historico_resumo: str = "",
    ) -> LLMResposta:
        """Pergunta ao Claude qual ação Playwright executar para o passo."""
        user_content = (
            f"BASE_URL: {base_url}\n\n"
            f"SNAPSHOT DA PÁGINA ATUAL:\n{snapshot_render}\n\n"
            f"HISTÓRICO RECENTE (passos já executados):\n{historico_resumo or '(início)'}\n\n"
            f"PASSO A EXECUTAR:\n"
            f"- Ação: {acao}\n"
            f"- Resultado esperado: {esperado}\n"
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            output_config={
                "format": {"type": "json_schema", "schema": _RESPOSTA_SCHEMA}
            },
            messages=[{"role": "user", "content": user_content}],
        )

        text = next((b.text for b in response.content if b.type == "text"), "")
        data = json.loads(text)
        return LLMResposta(
            actions=data.get("actions", []),
            assertions=data.get("assertions", []),
            confidence=float(data.get("confidence", 0.0)),
            notes=data.get("notes", ""),
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cache_creation_input_tokens": getattr(
                    response.usage, "cache_creation_input_tokens", 0
                ),
                "cache_read_input_tokens": getattr(
                    response.usage, "cache_read_input_tokens", 0
                ),
            },
        )
