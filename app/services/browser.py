"""Wrapper de Playwright pro agente QA.

Encapsula browser, page e métodos de alto nível que o agente chama via tools.
Reusa `pages.login_page.LoginPage` para autenticar no Twygo.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional


class Browser:
    """Sessão de browser. Use como context manager OU chame start()/close()."""

    def __init__(self, *, headless: bool = False, slow_mo_ms: int = 0) -> None:
        self.headless = headless
        self.slow_mo_ms = slow_mo_ms
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self.page: Any = None

    # ---- Lifecycle ----

    def start(self) -> None:
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo_ms,
        )
        self._context = self._browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="pt-BR",
        )
        self.page = self._context.new_page()

    def close(self) -> None:
        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
        self._context = None
        self._browser = None
        self._playwright = None
        self.page = None

    def __enter__(self) -> "Browser":
        self.start()
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    # ---- Ações de alto nível ----

    def login_twygo(
        self,
        base_url: str,
        email: str,
        password: str,
        org_id: str = "",
    ) -> None:
        """Loga no Twygo e troca pro perfil Administrador.

        Twygo redireciona pra /dashboard_students por padrão após login.
        Pra entrar como admin, navega para /o/{org_id}/events?profile=admin.
        Se org_id não for fornecido, tenta detectar da URL atual após login.
        """
        if not self.page:
            raise RuntimeError("Browser não iniciado — chame start() antes.")
        url = base_url.rstrip("/") + "/login"
        self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        self.page.fill("#user_email", email)
        self.page.fill("#user_password", password)
        self.page.click("#user_submit")
        try:
            self.page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass

        # Detecta org_id da URL atual se não foi fornecido
        if not org_id:
            org_id = self._detectar_org_id_da_url()

        # Troca pro perfil admin
        if org_id and org_id != "-1":
            self._mudar_para_admin(base_url, org_id)

    def _detectar_org_id_da_url(self) -> str:
        """Tenta extrair o org_id da URL atual (formato /o/<id>/...)."""
        import re
        url_atual = self.current_url()
        m = re.search(r"/o/(\d+)/", url_atual)
        return m.group(1) if m else ""

    def _mudar_para_admin(self, base_url: str, org_id: str) -> None:
        """Navega para a área de admin do Twygo."""
        admin_url = (
            f"{base_url.rstrip('/')}/o/{org_id}/events?tab=events&profile=admin"
        )
        try:
            self.page.goto(admin_url, wait_until="domcontentloaded", timeout=30000)
        except Exception:
            pass
        # Aguarda pouco pra UI estabilizar (Twygo às vezes faz redirect interno)
        try:
            self.page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

    def goto(self, url: str, timeout_ms: int = 30000) -> None:
        if not self.page:
            raise RuntimeError("Browser não iniciado")
        self.page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

    def click(self, selector: str, timeout_ms: int = 5000) -> None:
        if not self.page:
            raise RuntimeError("Browser não iniciado")
        self.page.click(selector, timeout=timeout_ms)

    def fill(self, selector: str, value: str, timeout_ms: int = 5000) -> None:
        if not self.page:
            raise RuntimeError("Browser não iniciado")
        self.page.fill(selector, value, timeout=timeout_ms)

    def wait_for(self, selector: str, timeout_ms: int = 10000) -> None:
        if not self.page:
            raise RuntimeError("Browser não iniciado")
        self.page.wait_for_selector(selector, timeout=timeout_ms)

    def screenshot(self, destino: Path) -> Path:
        if not self.page:
            raise RuntimeError("Browser não iniciado")
        destino.parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(destino), full_page=False)
        return destino

    def current_url(self) -> str:
        if not self.page:
            return ""
        return self.page.url or ""

    # ---- Visão para o agente ----

    def get_dom_simplificado(self, max_chars: int = 8000) -> str:
        """Retorna uma representação textual dos elementos interativos visíveis.

        O agente usa isso pra entender a estrutura da página sem precisar processar
        screenshot pixel a pixel. Lista botões, links, inputs com texto/aria-label.
        """
        if not self.page:
            return ""
        js = """
        () => {
          const interativos = document.querySelectorAll(
            'button, a, input, select, textarea, [role="button"], [role="link"], [role="tab"]'
          );
          const linhas = [];
          interativos.forEach((el, i) => {
            if (i > 200) return;
            const rect = el.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) return;
            const tag = el.tagName.toLowerCase();
            const txt = (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim().slice(0, 80);
            const id = el.id ? `#${el.id}` : '';
            const cls = el.className && typeof el.className === 'string' ? '.' + el.className.split(' ').slice(0,2).join('.') : '';
            const tipo = el.type ? `[${el.type}]` : '';
            linhas.push(`<${tag}${tipo}${id}${cls}> ${txt}`);
          });
          return linhas.join('\\n');
        }
        """
        try:
            return (self.page.evaluate(js) or "")[:max_chars]
        except Exception as e:
            return f"(erro ao extrair DOM: {e})"
