"""
T-1595 v1 — Reprodução do vídeo no Aprender exibe marca d'água em movimento (Desktop)

OBJETIVO: Verificar que ao reproduzir um vídeo cujo 'Tipo de exibição' está configurado
como 'Em movimento', a estampa se movimenta sobre o vídeo durante a reprodução.

PRÉ-CONDIÇÕES:
    - Aluno logado
    - Feature flag de marca d'água habilitada
    - Atividade de vídeo previamente cadastrada com marca d'água habilitada
      (tipo de exibição: 'Em movimento'; posição: 'Sobre todo o vídeo'; informações: 'CPF')
    - Aluno previamente matriculado no curso
    - Viewport Desktop (1920x1080)

PASSOS:
    1. Acessar o curso no Aprender → tela do curso é exibida com a lista de conteúdos
    2. Selecionar a atividade de vídeo → player de vídeo é exibido
    3. Iniciar a reprodução do vídeo → vídeo reproduz, marca d'água se move
    4. Aguardar (até metade do vídeo) → marca d'água continua se movendo
    5. Aguardar fim do vídeo → marca d'água continua se movendo

Como a marca d'água é queimada no vídeo server-side (não fica no DOM), a verificação de
"em movimento" é por screenshot — captura nos 3 momentos e o operador valida visualmente.
"""
from __future__ import annotations

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
OUTPUT_DIR = Path("test-results/t1595")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    print(f"[t1595] {msg}", flush=True)


def main() -> int:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="pt-BR")
        context.tracing.start(screenshots=True, snapshots=True)
        page = context.new_page()

        try:
            # Login
            log(f"Login como {EMAIL}")
            page.goto(BASE_URL + "login", wait_until="domcontentloaded")
            page.locator("#user_email").fill(EMAIL)
            page.locator("#user_password").fill(SENHA)
            page.locator("#user_submit").click()
            page.wait_for_load_state("domcontentloaded", timeout=20000)
            page.wait_for_timeout(3000)

            # Passo 1 — Acessar o curso no Aprender
            log("=== Passo 1: Acessar o curso no Aprender")
            page.goto(
                f"{BASE_URL}e/{EVENTO_ID}/learn?learn_origin=my-contents",
                wait_until="domcontentloaded",
                timeout=20000,
            )
            page.wait_for_timeout(6000)
            log(f"URL curso: {page.url}")

            # Passo 2 — Selecionar a atividade de vídeo (clica em texto "vídeo")
            log("=== Passo 2: Selecionar a atividade de vídeo")
            try:
                page.get_by_text("vídeo", exact=False).first.click(timeout=5000)
                page.wait_for_timeout(4000)
            except Exception as e:
                log(f"Não consegui clicar via texto: {e}")
                return _falha("Passo 2 — Player de vídeo é exibido", "Não foi possível clicar na atividade de vídeo", page, 2)

            if page.locator("video").count() == 0:
                return _falha("Passo 2 — Player de vídeo é exibido", "Player <video> não apareceu após selecionar a atividade", page, 2)

            # Passo 3 — Iniciar a reprodução
            log("=== Passo 3: Iniciar reprodução")
            video = page.locator("video").first
            video.evaluate("v => v.play()")
            page.wait_for_timeout(2000)
            duracao = video.evaluate("v => v.duration") or 11.0
            log(f"Duração do vídeo: {duracao:.1f}s")
            paused = video.evaluate("v => v.paused")
            if paused:
                return _falha("Passo 3 — Vídeo começa a ser reproduzido", "Vídeo não saiu do pause após .play()", page, 3)

            # Screenshot t=2s (já passou ~2s desde o play)
            png_t2 = OUTPUT_DIR / "t1595-passo3-marca-em-t2s.png"
            page.screenshot(path=str(png_t2), full_page=False)
            log(f"Screenshot t≈2s: {png_t2}")

            # Passo 4 — Aguardar até a metade (mid-point)
            log("=== Passo 4: Aguardar até a metade do vídeo")
            target_mid = max(4, duracao / 2)
            sleep_mid = max(2, int(target_mid - 2))
            page.wait_for_timeout(sleep_mid * 1000)
            png_mid = OUTPUT_DIR / "t1595-passo4-marca-no-meio.png"
            page.screenshot(path=str(png_mid), full_page=False)
            log(f"Screenshot t≈{2 + sleep_mid}s ({target_mid:.0f}s alvo): {png_mid}")

            # Passo 5 — Aguardar fim do vídeo
            log("=== Passo 5: Aguardar fim do vídeo")
            tempo_jah_passado = 2 + sleep_mid
            tempo_restante = max(2, int(duracao - tempo_jah_passado - 1))
            page.wait_for_timeout(tempo_restante * 1000)
            png_fim = OUTPUT_DIR / "t1595-passo5-marca-no-fim.png"
            page.screenshot(path=str(png_fim), full_page=False)
            log(f"Screenshot t≈{tempo_jah_passado + tempo_restante}s (próx do fim): {png_fim}")

            # Encerra sucesso (verificação visual é do operador)
            log("")
            log("=== Resultado ===")
            log("Os 5 passos do roteiro foram executados. A verificação 'em movimento' precisa")
            log("ser visual — compare a posição do 'CPF :' entre as 3 screenshots:")
            log(f"  - {png_t2}")
            log(f"  - {png_mid}")
            log(f"  - {png_fim}")

        except Exception as e:
            log(f"Erro inesperado: {e}")
            return 2
        finally:
            try:
                context.tracing.stop(path=str(OUTPUT_DIR / "t1595-trace.zip"))
            except Exception:
                pass
            browser.close()

    return 0


def _falha(passo_desc: str, motivo: str, page: Page, n: int) -> int:
    png = OUTPUT_DIR / f"t1595-passo{n}-falha.png"
    try:
        page.screenshot(path=str(png), full_page=True)
    except Exception:
        pass
    print()
    print(":: Incidente identificado ::")
    print(motivo)
    print()
    print("    :: Passo a passo para reprodução ::")
    print(f"» {passo_desc}")
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
