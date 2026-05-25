"""Cliente LLM agnóstico ao provedor.

Hoje só implementa Gemini (gemini-2.5-flash). A interface foi pensada
para no futuro plugar Claude/OpenAI sem mudar quem usa.

Mensagens, tools e resposta são structs Python simples (dataclasses) —
o cliente converte para o formato do provedor específico.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Protocol


# ---------------------------------------------------------------------------
# Tipos agnósticos ao provedor
# ---------------------------------------------------------------------------


@dataclass
class Mensagem:
    """Mensagem da conversa. `role` é 'user' ou 'model'.

    Cada mensagem pode ter texto e/ou referência a uma imagem (path no disco).
    """
    role: str  # "user" | "model"
    text: str = ""
    image_path: Optional[Path] = None


@dataclass
class Tool:
    """Ferramenta que o agente pode chamar.

    `parameters` segue jsonschema simples (type=object, properties, required).
    """
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    """Chamada de tool emitida pelo LLM."""
    name: str
    args: dict[str, Any]


@dataclass
class RespostaLLM:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    # Metadados crus do provedor pra debug
    raw: Any = None


# ---------------------------------------------------------------------------
# Interface (Protocol — duck-typed; não precisa herdar)
# ---------------------------------------------------------------------------


class LLMClient(Protocol):
    def gerar(
        self,
        system_instruction: str,
        mensagens: list[Mensagem],
        tools: list[Tool],
    ) -> RespostaLLM:
        ...


# ---------------------------------------------------------------------------
# Implementação Gemini
# ---------------------------------------------------------------------------


class GeminiClient:
    """Wrapper sobre google-genai (SDK novo: from google import genai)."""

    MODELO_PADRAO = "gemini-2.5-flash"

    def __init__(self, api_key: str, model: Optional[str] = None) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY ausente")
        # Import lazy para não exigir google-genai em testes que mockam isso
        from google import genai
        self._genai = genai
        self.client = genai.Client(api_key=api_key)
        self.model = model or self.MODELO_PADRAO

    def gerar(
        self,
        system_instruction: str,
        mensagens: list[Mensagem],
        tools: list[Tool],
    ) -> RespostaLLM:
        from google.genai import types

        # ---- Converte mensagens ----
        contents: list[Any] = []
        for msg in mensagens:
            parts: list[Any] = []
            if msg.text:
                parts.append(types.Part.from_text(text=msg.text))
            if msg.image_path is not None:
                img_path = Path(msg.image_path)
                if img_path.exists():
                    suffix = img_path.suffix.lower().lstrip(".")
                    mime = f"image/{suffix if suffix in ('png', 'jpeg', 'jpg', 'webp') else 'png'}"
                    if mime == "image/jpg":
                        mime = "image/jpeg"
                    parts.append(
                        types.Part.from_bytes(
                            data=img_path.read_bytes(),
                            mime_type=mime,
                        )
                    )
            if not parts:
                continue
            contents.append(types.Content(role=msg.role, parts=parts))

        # ---- Converte tools ----
        gemini_tools: list[Any] = []
        if tools:
            decls = []
            for t in tools:
                kwargs: dict[str, Any] = {
                    "name": t.name,
                    "description": t.description,
                }
                # Só envia parameters quando há props de verdade. Se a tool não
                # tem args, omite — alguns SDKs do Gemini falham com object vazio.
                props = (t.parameters or {}).get("properties") or {}
                if props:
                    kwargs["parameters"] = t.parameters
                decls.append(types.FunctionDeclaration(**kwargs))
            gemini_tools = [types.Tool(function_declarations=decls)]

        # ---- Chama API ----
        config = types.GenerateContentConfig(
            system_instruction=system_instruction or None,
            tools=gemini_tools or None,
        )
        print(
            f"[llm_client] generate_content: model={self.model}, "
            f"contents={len(contents)}, tools={len(gemini_tools)}",
            flush=True,
        )
        # Pequeno retry pra erros transitórios de rede (proxy corporativo,
        # conexão derrubada). Não tenta de novo se for erro de auth/quota.
        import time as _time
        ultima_exc: Exception | None = None
        for tentativa in range(1, 4):
            try:
                resp = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config,
                )
                break
            except Exception as e:
                msg = str(e).lower()
                # Não retentar em erros permanentes
                if any(k in msg for k in ("api_key", "unauthor", "permission", "quota", "billing", "404")):
                    print(f"[llm_client] erro permanente, não retenta: {type(e).__name__}: {e}", flush=True)
                    raise
                ultima_exc = e
                print(
                    f"[llm_client] tentativa {tentativa}/3 falhou: {type(e).__name__}: {e}",
                    flush=True,
                )
                if tentativa < 3:
                    _time.sleep(2 ** tentativa)  # 2s, 4s
        else:
            raise ultima_exc  # type: ignore[misc]

        # ---- Parseia resposta ----
        text = ""
        tool_calls: list[ToolCall] = []
        print(
            f"[llm_client] response candidates={len(getattr(resp, 'candidates', []) or [])}",
            flush=True,
        )
        if getattr(resp, "candidates", None):
            cand = resp.candidates[0]
            cand_content = getattr(cand, "content", None)
            for part in getattr(cand_content, "parts", []) or []:
                if getattr(part, "text", None):
                    text += part.text
                fc = getattr(part, "function_call", None)
                if fc:
                    tool_calls.append(
                        ToolCall(
                            name=fc.name,
                            args=dict(fc.args) if fc.args else {},
                        )
                    )

        return RespostaLLM(text=text, tool_calls=tool_calls, raw=resp)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def criar_cliente(provedor: str = "gemini", **kwargs: Any) -> LLMClient:
    """Cria um cliente LLM pelo nome do provedor. Por ora só 'gemini'."""
    provedor = provedor.lower()
    if provedor == "gemini":
        return GeminiClient(**kwargs)
    raise ValueError(f"Provedor LLM desconhecido: {provedor}")
