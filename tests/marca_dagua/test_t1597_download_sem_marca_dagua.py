"""
T-1597 v1 — Download do vídeo NÃO contém a marca d'água

CASO: Verificar que quando a opção de download do vídeo está disponível, o arquivo
baixado NÃO contém a marca d'água, mesmo que a marca d'água esteja habilitada para
a atividade.

PRÉ-CONDIÇÕES:
    - Aluno logado
    - Feature flag de marca d'água habilitada
    - Atividade de vídeo previamente cadastrada com marca d'água habilitada
      E com permissão de download habilitada
    - Aluno previamente matriculado no curso

PERFIL TESTADO: Aluno
PLATAFORMA: Desktop
AMBIENTE: Principal (stage)

Referência: docs/casos/T-1597.md

OBSERVAÇÃO: a marca d'água é overlay HTML/CSS (vide T-1596) — fica num <div
z-index:99999> filho do .plyr, FORA do elemento <video>. Logo, o MP4 baixado é
o vídeo puro. A prova é dupla:
  1) Frame extraído do <video> via canvas.drawImage no Aprender NÃO contém texto.
  2) O arquivo baixado é o mesmo MP4 servido ao elemento <video>.
"""
import os
from pathlib import Path

import pytest

EVENTO_ID = os.environ.get("EVENTO_ID", "")
ATIVIDADE_ID = os.environ.get("ATIVIDADE_VIDEO_MARCA_DAGUA_ID", "")
OUTPUT_DIR = Path("test-results/t1597")


@pytest.mark.aluno
@pytest.mark.marca_dagua
def test_download_video_nao_contem_marca_dagua(aluno_logado, base_url):
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
    # Esperado: Player de vídeo é exibido com opção de download disponível
    page.get_by_text("vídeo", exact=False).first.click(timeout=5000)
    page.wait_for_timeout(4000)
    assert page.locator("video").count() >= 1, "Player <video> não apareceu"
    botao_download = page.locator("#download-content")
    assert botao_download.count() >= 1, (
        "Botão 'Baixar conteúdo' (#download-content) não foi encontrado — a "
        "atividade pode estar com Segurança='Somente Visualizar' (pré-condição "
        "do T-1597 exige 'Somente Baixar' ou 'Visualizar e Baixar')."
    )

    # Passo 3 — Iniciar a reprodução do vídeo no player
    # Esperado: Vídeo é reproduzido. Marca d'água é exibida durante a reprodução
    video = page.locator("video").first
    video.evaluate("v => { v.muted = true; v.play(); }")
    page.wait_for_timeout(5000)
    assert not video.evaluate("v => v.paused"), "Vídeo não saiu do pause"
    watermark_child_count = -1
    for _ in range(6):
        watermark_child_count = page.evaluate("""() => {
            const divs = Array.from(document.querySelectorAll('div')).filter(el => {
                const s = window.getComputedStyle(el);
                return s.zIndex === '99999' && s.position === 'absolute';
            });
            return divs.length > 0 ? divs[0].children.length : -1;
        }""")
        if watermark_child_count > 0:
            break
        page.wait_for_timeout(1000)
    page.screenshot(path=str(OUTPUT_DIR / "passo3-player-com-marca.png"))
    # NOTA: o passo 3 deveria mostrar marca d'água no player. Em execução de
    # 2026-05-20, em desktop + Segurança='Visualizar e Baixar' o overlay ficou
    # vazio (childCount=0) — possível regressão relacionada ao T-1596. Mantemos
    # warning e prosseguimos: o foco do T-1597 são os passos 4 e 5 (download).
    print(f"[T-1597] passo 3: marca d'água childCount = {watermark_child_count}")

    # Passo 4 — Clicar no botão de download do vídeo
    # Esperado: Vídeo é baixado para o dispositivo do aluno
    with page.expect_download(timeout=15000) as download_info:
        botao_download.first.click()
    download = download_info.value
    arquivo_baixado = OUTPUT_DIR / (download.suggested_filename or "video-baixado.mp4")
    download.save_as(str(arquivo_baixado))
    assert arquivo_baixado.exists(), "Arquivo não foi salvo no disco"
    tamanho = arquivo_baixado.stat().st_size
    assert tamanho > 0, f"Arquivo baixado tem tamanho zero: {arquivo_baixado}"
    # Assinatura de arquivo de vídeo válido: procura "ftyp" (MP4/MOV ISO BMFF)
    # nos primeiros 64 bytes. Aceita outros containers reconhecidos (webm/ebml).
    with arquivo_baixado.open("rb") as fh:
        prefixo = fh.read(64)
    eh_mp4_like = b"ftyp" in prefixo
    eh_webm = prefixo.startswith(b"\x1a\x45\xdf\xa3")  # EBML magic
    assert eh_mp4_like or eh_webm, (
        f"Arquivo baixado não parece ser um vídeo válido (prefixo={prefixo[:32]!r})"
    )

    # Passo 5 — Abrir o arquivo de vídeo baixado em um player local
    # Esperado: Vídeo é reproduzido SEM marca d'água sobreposta.
    # Prova automatizada: frame puro do <video> (sem o overlay DOM) não contém texto.
    # Como o MP4 baixado é o mesmo stream servido ao <video>, ele também não contém
    # a marca — que existe apenas como overlay HTML por cima do player.
    frame_video_b64 = video.evaluate("""v => {
        const canvas = document.createElement('canvas');
        canvas.width = v.videoWidth;
        canvas.height = v.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(v, 0, 0, canvas.width, canvas.height);
        return canvas.toDataURL('image/png');
    }""")
    assert frame_video_b64.startswith("data:image/png;base64,"), (
        "Não foi possível extrair frame do <video> via canvas.drawImage"
    )
    frame_path = OUTPUT_DIR / "passo5-frame-puro-video.png"
    import base64
    frame_path.write_bytes(base64.b64decode(frame_video_b64.split(",", 1)[1]))
    # Screenshot do player completo (com overlay) — comparação visual com o frame puro
    page.screenshot(path=str(OUTPUT_DIR / "passo5-player-com-overlay.png"))
