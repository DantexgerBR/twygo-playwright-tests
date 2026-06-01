# ⚠ Código LEGADO / CONGELADO — App Flet (cancelado)

Esta pasta (`app/`) é o **app desktop Flet de QA, cancelado** (e o agente LLM
descontinuado). Está **congelada**: não receber novas features nem ser usada pelo
fluxo de validação atual (que é 100% Playwright local, sem API LLM externa).

- Os testes em `tests/app/` (que exercitam este código) estão **ignorados** no
  `pytest.ini` (`--ignore=tests/app`).
- As dependências dele (`flet`, `anthropic`, `google-genai`, `groq`, `gradio`,
  `pillow`, `pyperclip`, `httpx`, `pypdf`, `keyring`) foram **removidas** do
  `requirements.txt`. Para rodar/manter o legado, instale-as à parte.

Fluxo atual de validação: ver `scripts/` (+ `scripts/_twygo.py`) e a skill
`validar-retrabalho-twygo`.
