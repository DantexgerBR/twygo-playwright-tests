"""Executor que dirige uma sessão Playwright a partir de um caso de teste parseado."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator

from playwright.sync_api import (
    BrowserContext,
    Locator,
    Page,
    Playwright,
    sync_playwright,
    expect,
)

from ui.discovery import snapshot_page
from ui.llm import LLMExecutor, LLMResposta
from ui.parser import Caso, Passo


@dataclass
class PassoResultado:
    n: int
    acao: str
    esperado: str
    status: str  # "ok" | "fail" | "error"
    mensagem: str = ""
    actions_executadas: list[dict[str, Any]] = field(default_factory=list)
    assertions: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    screenshot_path: str | None = None
    trace_path: str | None = None
    falha_em: str = ""  # "action" | "assertion" | "" se ok


@dataclass
class ExecucaoResultado:
    caso: Caso
    passos: list[PassoResultado] = field(default_factory=list)
    sucesso: bool = False
    usage_total: dict[str, int] = field(default_factory=dict)


class Executor:
    def __init__(
        self,
        base_url: str,
        admin_email: str,
        admin_password: str,
        aluno_email: str,
        aluno_password: str,
        api_key: str | None = None,
        output_dir: Path | None = None,
        on_log: Callable[[str], None] | None = None,
        headless: bool = True,
    ):
        self.base_url = base_url.rstrip("/") + "/"
        self.admin_email = admin_email
        self.admin_password = admin_password
        self.aluno_email = aluno_email
        self.aluno_password = aluno_password
        self.llm = LLMExecutor(api_key=api_key)
        self.output_dir = output_dir or Path("test-results/ui-runs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.on_log = on_log or (lambda msg: None)
        self.headless = headless
        self._usage_acc: dict[str, int] = {}

    def _log(self, msg: str) -> None:
        self.on_log(msg)

    def executar(self, caso: Caso) -> ExecucaoResultado:
        resultado = ExecucaoResultado(caso=caso)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self.headless)
            ctx_admin = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
            ctx_aluno = browser.new_context(viewport={"width": 1366, "height": 768}, locale="pt-BR")
            ctx_admin.tracing.start(screenshots=True, snapshots=True)
            ctx_aluno.tracing.start(screenshots=True, snapshots=True)

            try:
                # Logins iniciais conforme pré-condições.
                self._login(ctx_admin.new_page(), self.admin_email, self.admin_password, "admin")
                self._login(ctx_aluno.new_page(), self.aluno_email, self.aluno_password, "aluno")

                historico = []
                page = ctx_admin.pages[-1]  # começa pelo admin
                contexto_aluno_ativo = False

                for passo in caso.passos:
                    self._log(f"\n=== Passo {passo.n} — {passo.acao}")
                    self._log(f"    Esperado: {passo.esperado}")

                    # Heurística: passo que menciona "aluno" / "Aprender" → muda para context aluno
                    if re.search(r"\b(aluno|aprender)\b", passo.acao, re.I) and not contexto_aluno_ativo:
                        page = ctx_aluno.pages[-1]
                        contexto_aluno_ativo = True
                        self._log("    → Trocando para contexto do aluno")

                    pr = self._executar_passo(page, passo, historico)
                    resultado.passos.append(pr)
                    historico.append(f"Passo {passo.n}: {passo.acao} → {pr.status}")

                    if pr.status != "ok":
                        # Captura screenshot da falha.
                        slug = _slugify(caso.objetivo)
                        png = self.output_dir / f"{slug}-passo{passo.n}-falha.png"
                        try:
                            page.screenshot(path=str(png), full_page=True)
                            pr.screenshot_path = str(png)
                        except Exception:
                            pass
                        break

                resultado.sucesso = all(pr.status == "ok" for pr in resultado.passos)

                # Soma usage de todos os passos.
                total: dict[str, int] = {}
                for pr in resultado.passos:
                    pass  # usage é coletado em _executar_passo via self._usage_acc

                resultado.usage_total = self._usage_acc

            finally:
                slug = _slugify(caso.objetivo)
                trace_admin = self.output_dir / f"{slug}-admin-trace.zip"
                trace_aluno = self.output_dir / f"{slug}-aluno-trace.zip"
                try:
                    ctx_admin.tracing.stop(path=str(trace_admin))
                    ctx_aluno.tracing.stop(path=str(trace_aluno))
                except Exception:
                    pass
                for pr in resultado.passos:
                    if pr.status != "ok":
                        pr.trace_path = str(trace_admin if not contexto_aluno_ativo else trace_aluno)
                browser.close()

        return resultado

    def _login(self, page: Page, email: str, password: str, label: str) -> None:
        self._log(f"[login {label}] {email}")
        page.goto(self.base_url + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(email)
        page.locator("#user_password").fill(password)
        page.locator("#user_submit").click()
        page.wait_for_load_state("networkidle", timeout=20000)
        self._log(f"[login {label}] OK → {page.url}")

    def _executar_passo(self, page: Page, passo: Passo, historico: list[str]) -> PassoResultado:
        pr = PassoResultado(n=passo.n, acao=passo.acao, esperado=passo.esperado, status="error")

        # 1) Snapshot da página
        snap = snapshot_page(page)
        self._log(f"    [snapshot] {snap.url}")

        # 2) Pergunta ao LLM
        try:
            resposta: LLMResposta = self.llm.interpretar_passo(
                acao=passo.acao,
                esperado=passo.esperado,
                snapshot_render=snap.to_prompt(),
                base_url=self.base_url,
                historico_resumo="\n".join(historico[-3:]),
            )
        except Exception as e:
            pr.status = "error"
            pr.mensagem = f"LLM falhou: {e}"
            return pr

        # acumula usage
        for k, v in resposta.usage.items():
            self._usage_acc[k] = self._usage_acc.get(k, 0) + v

        pr.confidence = resposta.confidence
        pr.actions_executadas = resposta.actions
        pr.assertions = resposta.assertions
        self._log(f"    [llm] confidence={resposta.confidence:.2f} actions={len(resposta.actions)} assertions={len(resposta.assertions)}")
        if resposta.notes:
            self._log(f"    [llm notes] {resposta.notes}")

        # 3) Executa ações
        for act in resposta.actions:
            try:
                self._executar_acao(page, act)
            except Exception as e:
                pr.status = "fail"
                pr.falha_em = "action"
                pr.mensagem = f"Ação {act} falhou: {e}"
                return pr

        # 4) Verifica asserções
        for ass in resposta.assertions:
            try:
                self._verificar_assercao(page, ass)
            except AssertionError as e:
                pr.status = "fail"
                pr.falha_em = "assertion"
                pr.mensagem = f"Asserção {ass} falhou: {e}"
                return pr
            except Exception as e:
                pr.status = "error"
                pr.mensagem = f"Erro ao verificar {ass}: {e}"
                return pr

        pr.status = "ok"
        return pr

    def _executar_acao(self, page: Page, act: dict[str, Any]) -> None:
        op = act["op"]
        sel = act.get("selector", "")
        val = act.get("value", "")

        if op == "goto":
            url = act.get("url") or val
            if url and not url.startswith("http"):
                url = self.base_url + url.lstrip("/")
            page.goto(url, wait_until="networkidle", timeout=30000)
        elif op == "click":
            loc = page.locator(sel).first
            loc.scroll_into_view_if_needed(timeout=5000)
            loc.click(timeout=10000)
        elif op == "fill":
            page.locator(sel).first.fill(val)
        elif op == "check":
            page.locator(sel).first.check(timeout=5000)
        elif op == "uncheck":
            page.locator(sel).first.uncheck(timeout=5000)
        elif op == "select_option":
            page.locator(sel).first.select_option(val)
        elif op == "press":
            page.locator(sel).first.press(act.get("key", "Enter"))
        elif op == "wait_for_url":
            page.wait_for_url(act.get("url_glob", "**"), timeout=15000)
        elif op == "wait_for_selector":
            page.locator(sel).first.wait_for(state="visible", timeout=10000)
        elif op == "scroll_into_view":
            page.locator(sel).first.scroll_into_view_if_needed()
        else:
            raise ValueError(f"op desconhecido: {op}")

    def _verificar_assercao(self, page: Page, ass: dict[str, Any]) -> None:
        t = ass["type"]
        sel = ass.get("selector", "")
        val = ass.get("value", "")
        loc: Locator | None = page.locator(sel).first if sel else None

        if t == "to_be_visible":
            expect(loc).to_be_visible(timeout=10000)
        elif t == "to_be_hidden":
            expect(loc).to_be_hidden(timeout=10000)
        elif t == "to_be_checked":
            # Para Chakra label, verifica data-checked
            if loc and ".chakra-checkbox" in sel:
                assert loc.get_attribute("data-checked") is not None, "data-checked ausente"
            else:
                expect(loc).to_be_checked(timeout=5000)
        elif t == "not_to_be_checked":
            if loc and ".chakra-checkbox" in sel:
                assert loc.get_attribute("data-checked") is None, "data-checked presente (esperado ausente)"
            else:
                expect(loc).not_to_be_checked(timeout=5000)
        elif t == "to_have_text":
            expect(loc).to_contain_text(val, timeout=10000)
        elif t == "to_have_url":
            expect(page).to_have_url(re.compile(re.escape(val)), timeout=10000)
        elif t == "to_have_count":
            expect(page.locator(sel)).to_have_count(int(ass.get("count", 0)), timeout=10000)
        elif t == "custom":
            # Best-effort: o LLM deveria evitar isso, mas se vier, registra como warning
            raise AssertionError(f"verificação custom não implementada: {ass.get('description')}")
        else:
            raise ValueError(f"asserção desconhecida: {t}")


def _slugify(s: str, maxlen: int = 60) -> str:
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"\s+", "_", s).strip("_")
    return s[:maxlen] or "caso"
