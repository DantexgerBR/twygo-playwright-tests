"""UI Gradio para colar caso de teste e executá-lo."""
from __future__ import annotations

import json
import os
import queue
import threading
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

from ui.executor import Executor
from ui.generator import gerar_arquivo_teste, gerar_doc_caso
from ui.parser import parse_caso
from ui.reporter import render_bug_report

load_dotenv()


def _executar(
    texto_caso: str,
    base_url: str,
    admin_email: str,
    admin_password: str,
    aluno_email: str,
    aluno_password: str,
    anthropic_api_key: str,
    org_id: str,
    headless: bool,
):
    """Generator que faz yield de updates conforme o teste roda."""
    log_lines: list[str] = []
    log_q: queue.Queue[str | None] = queue.Queue()

    def emit(msg: str) -> None:
        log_q.put(msg)

    def render_log() -> str:
        return "\n".join(log_lines)

    # 1) Parse
    if not texto_caso.strip():
        yield "Cole um caso de teste antes de executar.", "", "", None
        return

    caso = parse_caso(texto_caso)
    if not caso.passos:
        yield (
            "Não consegui identificar passos no texto colado.\n"
            "Espero formato com tabela: `N\\tAção\\tEsperado\\t...`",
            "",
            json.dumps(caso.to_dict(), indent=2, ensure_ascii=False),
            None,
        )
        return

    log_lines.append(f"[parser] objetivo: {caso.objetivo[:80]}…")
    log_lines.append(f"[parser] {len(caso.passos)} passos, {len(caso.pre_condicoes)} pré-condições")
    yield render_log(), "", json.dumps(caso.to_dict(), indent=2, ensure_ascii=False), None

    # 2) Valida configs
    if not all([base_url, admin_email, admin_password, anthropic_api_key]):
        log_lines.append("[erro] Preencha BASE_URL, ADMIN_EMAIL, ADMIN_PASSWORD e ANTHROPIC_API_KEY")
        yield render_log(), "", json.dumps(caso.to_dict(), indent=2, ensure_ascii=False), None
        return

    # Aluno pode ser igual ao admin
    if not aluno_email:
        aluno_email = admin_email
        aluno_password = admin_password

    executor = Executor(
        base_url=base_url,
        admin_email=admin_email,
        admin_password=admin_password,
        aluno_email=aluno_email,
        aluno_password=aluno_password,
        api_key=anthropic_api_key,
        on_log=emit,
        headless=headless,
    )

    # Roda em thread pra poder fazer yield de logs.
    resultado_holder: dict = {}

    def run():
        try:
            resultado_holder["res"] = executor.executar(caso)
        except Exception as e:
            resultado_holder["err"] = str(e)
        finally:
            log_q.put(None)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    while True:
        msg = log_q.get()
        if msg is None:
            break
        log_lines.append(msg)
        yield render_log(), "", json.dumps(caso.to_dict(), indent=2, ensure_ascii=False), None

    thread.join()

    if "err" in resultado_holder:
        log_lines.append(f"[ERRO] {resultado_holder['err']}")
        yield render_log(), "", json.dumps(caso.to_dict(), indent=2, ensure_ascii=False), None
        return

    res = resultado_holder["res"]
    log_lines.append("")
    log_lines.append(f"[resultado] sucesso={res.sucesso}")
    log_lines.append(f"[usage] {res.usage_total}")

    # Gera arquivo pytest + doc
    arquivo_teste = gerar_arquivo_teste(caso, res, marker="gerado", area="gerado")
    arquivo_doc = gerar_doc_caso(caso)
    log_lines.append(f"[gerado] teste: {arquivo_teste}")
    log_lines.append(f"[gerado] doc:   {arquivo_doc}")

    # Bug report se falhou
    bug = render_bug_report(
        res,
        base_url=base_url,
        admin_email=admin_email,
        admin_password=admin_password,
        aluno_email=aluno_email,
        aluno_password=aluno_password,
        org_id=org_id or "-1",
    )
    bug_text = bug or "✅ Todos os passos passaram."

    # Screenshot da falha (se houver)
    img = None
    for pr in res.passos:
        if pr.screenshot_path and os.path.exists(pr.screenshot_path):
            img = pr.screenshot_path
            break

    yield render_log(), bug_text, json.dumps(caso.to_dict(), indent=2, ensure_ascii=False), img


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Twygo Test Runner") as demo:
        gr.Markdown("# Twygo Test Runner")
        gr.Markdown(
            "Cole um caso de teste no formato Twygo. O sistema parseia, executa "
            "cada passo dirigindo Playwright via Claude, e gera arquivo pytest + "
            "relatório de incidente se algo falhar."
        )

        with gr.Row():
            with gr.Column(scale=2):
                texto_caso = gr.Textbox(
                    label="Caso de teste",
                    placeholder="Cole aqui o caso (objetivo, pré-condições, tabela de passos)...",
                    lines=18,
                )
            with gr.Column(scale=1):
                base_url = gr.Textbox(
                    label="BASE_URL",
                    value=os.environ.get("BASE_URL", ""),
                )
                admin_email = gr.Textbox(
                    label="Admin e-mail",
                    value=os.environ.get("ADMIN_EMAIL", ""),
                )
                admin_password = gr.Textbox(
                    label="Admin senha",
                    type="password",
                    value=os.environ.get("ADMIN_PASSWORD", ""),
                )
                aluno_email = gr.Textbox(
                    label="Aluno e-mail (em branco usa admin)",
                    value=os.environ.get("ALUNO_EMAIL", ""),
                )
                aluno_password = gr.Textbox(
                    label="Aluno senha",
                    type="password",
                    value=os.environ.get("ALUNO_PASSWORD", ""),
                )
                anthropic_api_key = gr.Textbox(
                    label="ANTHROPIC_API_KEY",
                    type="password",
                    value=os.environ.get("ANTHROPIC_API_KEY", ""),
                )
                org_id = gr.Textbox(
                    label="ORG_ID",
                    value=os.environ.get("ORG_ID", "-1"),
                )
                headless = gr.Checkbox(label="Headless", value=True)
                btn = gr.Button("Executar", variant="primary")

        with gr.Row():
            log = gr.Textbox(label="Log de execução", lines=20, max_lines=40, interactive=False)
        with gr.Row():
            bug_out = gr.Textbox(label="Resultado / Bug report", lines=15, interactive=False)
        with gr.Row():
            caso_json = gr.Code(label="Caso parseado", language="json")
            img_falha = gr.Image(label="Screenshot da falha", height=400)

        btn.click(
            _executar,
            inputs=[
                texto_caso,
                base_url,
                admin_email,
                admin_password,
                aluno_email,
                aluno_password,
                anthropic_api_key,
                org_id,
                headless,
            ],
            outputs=[log, bug_out, caso_json, img_falha],
        )

    return demo


if __name__ == "__main__":
    build_ui().launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft(),
    )
