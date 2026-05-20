"""Gera arquivo pytest a partir do caso executado, com as ações que funcionaram."""
from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ui.executor import ExecucaoResultado
from ui.parser import Caso

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _slug(s: str, maxlen: int = 60) -> str:
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"\s+", "_", s).strip("_")
    return s[:maxlen] or "caso"


def _render_action(act: dict) -> str:
    op = act.get("op", "")
    sel = act.get("selector", "")
    val = act.get("value", "")
    if op == "goto":
        url = act.get("url") or val
        if url.startswith("http"):
            return f'page.goto({url!r})'
        return f'page.goto(base_url + {url.lstrip("/")!r})'
    if op == "click":
        return f'page.locator({sel!r}).first.click()'
    if op == "fill":
        return f'page.locator({sel!r}).first.fill({val!r})'
    if op == "check":
        return f'page.locator({sel!r}).first.check()'
    if op == "uncheck":
        return f'page.locator({sel!r}).first.uncheck()'
    if op == "select_option":
        return f'page.locator({sel!r}).first.select_option({val!r})'
    if op == "press":
        return f'page.locator({sel!r}).first.press({act.get("key", "Enter")!r})'
    if op == "wait_for_url":
        return f'page.wait_for_url({act.get("url_glob", "**")!r}, timeout=15000)'
    if op == "wait_for_selector":
        return f'page.locator({sel!r}).first.wait_for(state="visible", timeout=10000)'
    if op == "scroll_into_view":
        return f'page.locator({sel!r}).first.scroll_into_view_if_needed()'
    return f'# op desconhecido: {op}'


def _render_assertion(ass: dict) -> str:
    t = ass.get("type", "")
    sel = ass.get("selector", "")
    val = ass.get("value", "")
    if t == "to_be_visible":
        return f'expect(page.locator({sel!r}).first).to_be_visible()'
    if t == "to_be_hidden":
        return f'expect(page.locator({sel!r}).first).to_be_hidden()'
    if t == "to_be_checked":
        if ".chakra-checkbox" in sel:
            return f'assert page.locator({sel!r}).first.get_attribute("data-checked") is not None'
        return f'expect(page.locator({sel!r}).first).to_be_checked()'
    if t == "not_to_be_checked":
        if ".chakra-checkbox" in sel:
            return f'assert page.locator({sel!r}).first.get_attribute("data-checked") is None'
        return f'expect(page.locator({sel!r}).first).not_to_be_checked()'
    if t == "to_have_text":
        return f'expect(page.locator({sel!r}).first).to_contain_text({val!r})'
    if t == "to_have_url":
        return f'expect(page).to_have_url(__import__("re").compile({val!r}))'
    if t == "to_have_count":
        return f'expect(page.locator({sel!r})).to_have_count({int(ass.get("count", 0))})'
    return f'# asserção custom: {ass.get("description", "")}'


def gerar_arquivo_teste(
    caso: Caso,
    resultado: ExecucaoResultado,
    pasta_destino: Path = Path("tests"),
    area: str = "gerado",
    marker: str = "gerado",
) -> Path:
    slug = _slug(caso.objetivo)
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("test_template.py.j2")

    passos_render = []
    for pr in resultado.passos:
        passos_render.append(
            {
                "n": pr.n,
                "acao": pr.acao,
                "esperado": pr.esperado,
                "actions_executadas": pr.actions_executadas,
                "assertions": pr.assertions,
            }
        )

    out = template.render(
        caso=caso,
        passos=passos_render,
        slug=slug,
        marker=marker,
        render_action=_render_action,
        render_assertion=_render_assertion,
    )

    destino = pasta_destino / area
    destino.mkdir(parents=True, exist_ok=True)
    arquivo = destino / f"test_{slug}.py"
    arquivo.write_text(out, encoding="utf-8")
    return arquivo


def gerar_doc_caso(caso: Caso, pasta_destino: Path = Path("docs/casos")) -> Path:
    slug = _slug(caso.objetivo)
    pasta_destino.mkdir(parents=True, exist_ok=True)
    arquivo = pasta_destino / f"{slug}.md"
    linhas = [
        f"# {caso.objetivo}",
        "",
        "## Pré-condições",
    ]
    for pre in caso.pre_condicoes:
        linhas.append(f"- {pre}")
    linhas += [
        "",
        f"**Perfil:** {caso.perfil or 'N/A'}",
        f"**Plataforma:** {caso.plataforma or 'Desktop'}",
        f"**Ambiente:** {caso.ambiente or 'Principal'}",
        "",
        "## Passos",
        "",
        "| # | Ação | Resultado esperado |",
        "|---|------|---------------------|",
    ]
    for p in caso.passos:
        linhas.append(f"| {p.n} | {p.acao} | {p.esperado} |")
    arquivo.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return arquivo
