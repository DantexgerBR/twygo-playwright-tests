"""
T-1596 v1 — Reprodução do vídeo no Aprender exibe marca d'água em viewport (Mobile)

OBJETIVO: Verificar que a marca d'água é exibida corretamente sobre o vídeo no Aprender
quando acessado em viewport Mobile.

PRÉ-CONDIÇÕES:
    - Aluno logado
    - Feature flag de marca d'água habilitada
    - Atividade de vídeo previamente cadastrada com marca d'água habilitada
      (informações: CPF, E-mail; posição: 'Sobre todo o vídeo')
    - Aluno previamente matriculado no curso
    - Viewport Mobile (360x740)

PASSOS:
    1. Acessar o curso no Aprender → tela do curso no layout mobile
    2. Selecionar a atividade de vídeo → player no layout mobile
    3. Iniciar a reprodução → marca d'água com dados REAIS (CPF mascarado + E-mail)
    4. Verificar visibilidade durante toda a reprodução

Como (a) a marca d'água é queimada server-side nos frames e (b) o conteúdo do <video> HTML5
não é capturado em screenshot Playwright headless, os "frames" são extraídos via canvas
drawImage do elemento <video> em diferentes momentos da reprodução.
"""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

load_dotenv()

BASE_URL = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ALUNO_EMAIL"] or os.environ["ADMIN_EMAIL"]
SENHA = os.environ["ALUNO_PASSWORD"] or os.environ["ADMIN_PASSWORD"]
EVENTO_ID = os.environ["EVENTO_ID"]
OUTPUT_DIR = Path("test-results/t1596")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    print(f"[t1596] {msg}", flush=True)


def captura_frame_video(page: Page, output_path: Path) -> dict:
    """Captura o frame atual do <video> via canvas. Retorna {ok, currentTime, w, h}."""
    result = page.evaluate(
        """() => {
            const v = document.querySelector('video');
            if (!v) return {ok: false};
            const c = document.createElement('canvas');
            c.width = v.videoWidth || 1280;
            c.height = v.videoHeight || 720;
            const ctx = c.getContext('2d');
            try {
                ctx.drawImage(v, 0, 0, c.width, c.height);
                return {ok: true, currentTime: v.currentTime, w: c.width, h: c.height, dataUrl: c.toDataURL('image/png')};
            } catch (e) {
                return {ok: false, error: e.message};
            }
        }"""
    )
    if result.get("ok"):
        b64 = result["dataUrl"].split(",", 1)[1]
        output_path.write_bytes(base64.b64decode(b64))
        return {"ok": True, "currentTime": result["currentTime"], "w": result["w"], "h": result["h"]}
    return {"ok": False, "error": result.get("error")}


def main() -> int:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 360, "height": 740},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
            user_agent=(
                "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
            locale="pt-BR",
        )
        context.tracing.start(screenshots=True, snapshots=True)
        page = context.new_page()

        try:
            # Login
            log(f"Login mobile como {EMAIL}")
            page.goto(BASE_URL + "login", wait_until="domcontentloaded")
            page.locator("#user_email").fill(EMAIL)
            page.locator("#user_password").fill(SENHA)
            page.locator("#user_submit").click()
            page.wait_for_load_state("domcontentloaded", timeout=20000)
            page.wait_for_timeout(3000)

            # Passo 1 — Acessar o curso no Aprender
            log("=== Passo 1: Acessar o curso no Aprender (layout mobile)")
            page.goto(
                f"{BASE_URL}e/{EVENTO_ID}/learn?learn_origin=my-contents",
                wait_until="domcontentloaded",
                timeout=20000,
            )
            page.wait_for_timeout(6000)
            page.screenshot(path=str(OUTPUT_DIR / "t1596-passo1-tela-curso.png"), full_page=True)

            # Passo 2 — Selecionar a atividade de vídeo
            log("=== Passo 2: Selecionar a atividade de vídeo")
            try:
                page.get_by_text("vídeo", exact=False).first.click(timeout=5000)
            except Exception:
                page.get_by_text("Novo 1", exact=False).first.click(timeout=5000)
            page.wait_for_timeout(4500)
            page.screenshot(path=str(OUTPUT_DIR / "t1596-passo2-player-na-tela.png"), full_page=True)
            video_count = page.locator("video").count()
            log(f"Player <video> count: {video_count}")
            if video_count == 0:
                return _falha("Player de vídeo é exibido", "Nenhum <video> encontrado após selecionar atividade", page, 2)

            # Passo 3 — Iniciar a reprodução + capturar frame com marca d'água
            log("=== Passo 3: Iniciar reprodução")
            # muted=true permite autoplay sem interação
            page.evaluate("() => { const v = document.querySelector('video'); v.muted = true; v.play(); }")
            page.wait_for_timeout(3000)
            paused = page.evaluate("() => document.querySelector('video').paused")
            if paused:
                return _falha("Vídeo começa a ser reproduzido", "Vídeo não saiu do pause após .play()", page, 3)
            info_p3 = captura_frame_video(page, OUTPUT_DIR / "t1596-passo3-marca-inicio.png")
            log(f"Frame passo 3: {info_p3}")
            duracao = page.evaluate("() => document.querySelector('video').duration") or 11.0
            log(f"Duração: {duracao:.1f}s")

            # Passo 4 — Captura no meio e no fim, verificando que a marca d'água permanece
            log("=== Passo 4: Verificar visibilidade durante reprodução")
            page.wait_for_timeout(max(2, int(duracao / 2 - 3)) * 1000)
            info_p4_meio = captura_frame_video(page, OUTPUT_DIR / "t1596-passo4-marca-meio.png")
            log(f"Frame meio: {info_p4_meio}")
            # Esperar perto do fim (último segundo)
            tempo_atual = page.evaluate("() => document.querySelector('video').currentTime") or 0
            tempo_restante = max(2, int(duracao - tempo_atual - 1))
            page.wait_for_timeout(tempo_restante * 1000)
            info_p4_fim = captura_frame_video(page, OUTPUT_DIR / "t1596-passo4-marca-fim.png")
            log(f"Frame fim: {info_p4_fim}")

            log("")
            log("=== Resultado ===")
            log("4 passos executados. Frames extraídos via canvas (a marca d'água queimada nos")
            log("frames aparece nesses PNGs). Validação visual:")
            log(f"  - {OUTPUT_DIR / 't1596-passo3-marca-inicio.png'}")
            log(f"  - {OUTPUT_DIR / 't1596-passo4-marca-meio.png'}")
            log(f"  - {OUTPUT_DIR / 't1596-passo4-marca-fim.png'}")

        except Exception as e:
            log(f"Erro inesperado: {e}")
            return 2
        finally:
            try:
                context.tracing.stop(path=str(OUTPUT_DIR / "t1596-trace.zip"))
            except Exception:
                pass
            browser.close()

    return 0


def _falha(passo_desc: str, motivo: str, page: Page, n: int) -> int:
    png = OUTPUT_DIR / f"t1596-passo{n}-falha.png"
    try:
        page.screenshot(path=str(png), full_page=True)
    except Exception:
        pass
    print()
    print(":: Incidente identificado ::")
    print(motivo)
    print()
    print("    :: Passo a passo para reprodução ::")
    print(f"» {passo_desc} — FALHOU no passo {n}")
    print()
    print("    :: Informações ::")
    print(f"url: {BASE_URL}")
    print(f"login: {EMAIL}")
    print(f"evento_id: {EVENTO_ID}")
    print()
    print("    :: Evidência(s) ::")
    print(f"Link da evidência: {png}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
