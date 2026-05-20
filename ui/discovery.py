"""Snapshot da página Playwright para alimentar o LLM.

Captura URL/title + lista de elementos interagíveis (inputs, buttons, links,
selects, checkboxes) com seus atributos identificadores (id, name, label,
placeholder, role, texto visível). O snapshot é truncado para caber no contexto
sem inflar custo.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from playwright.sync_api import Page

_MAX_ELEMENTOS = 50
_MAX_TEXTO = 120


def _trunc(s: str | None, n: int = _MAX_TEXTO) -> str:
    if not s:
        return ""
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


@dataclass
class Snapshot:
    url: str
    title: str
    headings: list[str] = field(default_factory=list)
    inputs: list[dict[str, Any]] = field(default_factory=list)
    buttons: list[dict[str, Any]] = field(default_factory=list)
    links: list[dict[str, Any]] = field(default_factory=list)
    checkboxes: list[dict[str, Any]] = field(default_factory=list)
    iframes: list[dict[str, Any]] = field(default_factory=list)
    toasts_visiveis: list[str] = field(default_factory=list)

    def to_prompt(self) -> str:
        """Render compacto para enviar ao LLM."""
        out = [f"URL: {self.url}", f"TÍTULO: {self.title}"]
        if self.headings:
            out.append("HEADINGS: " + " | ".join(self.headings[:8]))
        if self.checkboxes:
            out.append("CHECKBOXES:")
            for c in self.checkboxes:
                out.append(f"  - {c}")
        if self.inputs:
            out.append("INPUTS:")
            for inp in self.inputs:
                out.append(f"  - {inp}")
        if self.buttons:
            out.append("BUTTONS:")
            for b in self.buttons:
                out.append(f"  - {b}")
        if self.links:
            out.append("LINKS:")
            for l in self.links[:20]:
                out.append(f"  - {l}")
        if self.iframes:
            out.append(f"IFRAMES: {len(self.iframes)}")
        if self.toasts_visiveis:
            out.append("TOASTS VISÍVEIS: " + " | ".join(self.toasts_visiveis))
        return "\n".join(out)


def snapshot_page(page: Page) -> Snapshot:
    page.wait_for_load_state("domcontentloaded")

    snap = Snapshot(url=page.url, title=page.title())

    # Headings (h1-h3)
    try:
        snap.headings = [
            _trunc(h)
            for h in page.locator("h1, h2, h3").all_inner_texts()[:10]
            if h.strip()
        ]
    except Exception:
        pass

    # Inputs (text, email, password, search, number, tel)
    try:
        inputs = page.locator(
            "input:not([type='hidden']):not([type='checkbox']):not([type='radio']):not([type='submit']):not([type='button'])"
        ).element_handles()[:_MAX_ELEMENTOS]
        for h in inputs:
            data = h.evaluate(
                """el => ({
                    id: el.id || null,
                    name: el.name || null,
                    type: el.type || 'text',
                    placeholder: el.placeholder || null,
                    value: (el.value || '').slice(0, 40) || null,
                    aria_label: el.getAttribute('aria-label'),
                    visible: !!(el.offsetWidth || el.offsetHeight),
                    label: (() => {
                      const l = el.id ? document.querySelector(`label[for='${el.id}']`) : null;
                      return l ? (l.innerText || '').trim().slice(0, 80) : null;
                    })(),
                })"""
            )
            snap.inputs.append(data)
    except Exception:
        pass

    # Checkboxes (input nativos + Chakra-style labels com role=checkbox)
    try:
        cbs = page.locator(
            "input[type='checkbox'], [role='checkbox'], label.chakra-checkbox"
        ).element_handles()[:_MAX_ELEMENTOS]
        for h in cbs:
            data = h.evaluate(
                """el => ({
                    tag: el.tagName.toLowerCase(),
                    id: el.id || null,
                    name: el.name || null,
                    checked: el.matches('[data-checked]') || el.checked || el.getAttribute('aria-checked') === 'true',
                    text: (el.innerText || el.textContent || '').trim().slice(0, 120),
                    aria_label: el.getAttribute('aria-label'),
                    visible: !!(el.offsetWidth || el.offsetHeight),
                })"""
            )
            snap.checkboxes.append(data)
    except Exception:
        pass

    # Buttons (incluindo input[type=submit])
    try:
        btns = page.locator(
            "button, input[type='submit'], input[type='button'], [role='button']"
        ).element_handles()[:_MAX_ELEMENTOS]
        for h in btns:
            data = h.evaluate(
                """el => ({
                    tag: el.tagName.toLowerCase(),
                    id: el.id || null,
                    name: el.name || null,
                    text: (el.innerText || el.value || '').trim().slice(0, 80),
                    aria_label: el.getAttribute('aria-label'),
                    type: el.type || null,
                    visible: !!(el.offsetWidth || el.offsetHeight),
                })"""
            )
            if data.get("text") or data.get("aria_label") or data.get("id"):
                snap.buttons.append(data)
    except Exception:
        pass

    # Links com texto
    try:
        links = page.locator("a[href]").element_handles()[:_MAX_ELEMENTOS]
        for h in links:
            data = h.evaluate(
                """el => ({
                    href: el.getAttribute('href'),
                    text: (el.innerText || '').trim().slice(0, 80),
                    aria_label: el.getAttribute('aria-label'),
                    visible: !!(el.offsetWidth || el.offsetHeight),
                })"""
            )
            if data.get("text") and data.get("visible"):
                snap.links.append(data)
    except Exception:
        pass

    # Iframes
    try:
        for fr in page.frames:
            if fr.parent_frame is not None:
                snap.iframes.append({"name": fr.name, "url": fr.url})
    except Exception:
        pass

    # Toasts comuns (Chakra usa role="status", muitos sistemas usam .toast)
    try:
        toasts = page.locator(
            "[role='status'], [role='alert'], .toast, .chakra-toast, .Toastify__toast"
        ).all_inner_texts()
        snap.toasts_visiveis = [_trunc(t) for t in toasts if t.strip()][:5]
    except Exception:
        pass

    return snap
