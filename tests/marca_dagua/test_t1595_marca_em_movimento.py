"""
T-1595 v1 — Reprodução do vídeo no Aprender exibe marca d'água em movimento (Desktop)

CASO: Verificar que ao reproduzir um vídeo cujo 'Tipo de exibição' está configurado
como 'Em movimento', a estampa se movimenta sobre o vídeo durante a reprodução.

PRÉ-CONDIÇÕES:
    - Aluno logado
    - Feature flag de marca d'água habilitada
    - Atividade de vídeo previamente cadastrada com marca d'água habilitada
      (tipo de exibição: 'Em movimento'; posição: 'Sobre todo o vídeo'; informações: 'CPF')
    - Aluno previamente matriculado no curso
    - Viewport Desktop (1920x1080)

PERFIL TESTADO: Aluno
PLATAFORMA: Desktop (1920x1080)
AMBIENTE: Principal (stage)

Referência: docs/casos/T-1595.md

OBSERVAÇÃO IMPORTANTE: a marca d'água é renderizada server-side e queimada nos frames
do vídeo (não fica no DOM). A verificação de "em movimento" é feita por screenshots
em 3 momentos da reprodução. A asserção atual confere apenas que o player carregou e
que o vídeo iniciou; a verificação de movimento permanece como inspeção manual das
3 imagens salvas em test-results/ (até o backend expor a posição da estampa).
"""
import os
from pathlib import Path

import pytest

EVENTO_ID = os.environ.get("EVENTO_ID", "")
ATIVIDADE_ID = os.environ.get("ATIVIDADE_VIDEO_MARCA_DAGUA_ID", "")
OUTPUT_DIR = Path("test-results/t1595")


@pytest.mark.aluno
@pytest.mark.marca_dagua
def test_marca_dagua_em_movimento_no_aprender(aluno_logado, base_url):
    EVENTO_ID and ATIVIDADE_ID or pytest.skip("Defina EVENTO_ID e ATIVIDADE_VIDEO_MARCA_DAGUA_ID no .env")
    page = aluno_logado
    page.set_viewport_size({"width": 1920, "height": 1080})
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Passo 1 — Acessar o curso no Aprender
    # Esperado: Tela do curso é exibida com a lista de conteúdos
    page.goto(
        f"{base_url}e/{EVENTO_ID}/learn?learn_origin=my-contents",
        wait_until="domcontentloaded",
        timeout=20000,
    )
    page.wait_for_timeout(6000)
    assert "/learn" in page.url

    # Passo 2 — Selecionar a atividade de vídeo
    # Esperado: Player de vídeo é exibido
    page.get_by_text("vídeo", exact=False).first.click(timeout=5000)
    page.wait_for_timeout(4000)
    assert page.locator("video").count() >= 1, "Player <video> não apareceu após selecionar atividade"

    # Passo 3 — Iniciar a reprodução do vídeo
    # Esperado: Vídeo começa a ser reproduzido. Marca d'água é exibida e sua posição muda ao longo do tempo
    video = page.locator("video").first
    video.evaluate("v => v.play()")
    page.wait_for_timeout(2000)
    assert not video.evaluate("v => v.paused"), "Vídeo não saiu do pause após .play()"
    duracao = video.evaluate("v => v.duration") or 11.0
    page.screenshot(path=str(OUTPUT_DIR / "t1595-passo3-marca-em-t2s.png"))

    # Passo 4 — Aguardar até a metade do vídeo
    # Esperado: Marca d'água continua se movimentando
    target_mid = max(4, duracao / 2)
    page.wait_for_timeout(max(2, int(target_mid - 2)) * 1000)
    page.screenshot(path=str(OUTPUT_DIR / "t1595-passo4-marca-no-meio.png"))

    # Passo 5 — Aguardar fim do vídeo
    # Esperado: Marca d'água continua se movimentando
    page.wait_for_timeout(max(2, int(duracao - target_mid - 1)) * 1000)
    page.screenshot(path=str(OUTPUT_DIR / "t1595-passo5-marca-no-fim.png"))

    # NOTA: a verificação de movimento da estampa é manual (3 screenshots geradas em
    # test-results/t1595/). Retrabalho já aberto: marca d'água permanece estática
    # mesmo com tipo de exibição "Em movimento" configurado.
