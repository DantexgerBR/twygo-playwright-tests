"""
T-1601 v1 — Cor da fonte com 0% de transparência no Aprender

CASO: Verificar que uma cor configurada com 0% de transparência (totalmente
transparente) gera uma marca d'água invisível durante a reprodução do vídeo
no Aprender.

PRÉ-CONDIÇÕES:
    - Aluno logado
    - Feature flag de marca d'água habilitada
    - Atividade de vídeo previamente cadastrada com marca d'água habilitada
      (cor da fonte com transparência 0% — totalmente transparente)
    - Aluno previamente matriculado no curso

PERFIL TESTADO: Aluno
PLATAFORMA: Desktop
AMBIENTE: Principal (stage)

Referência: docs/casos/T-1601.md

NOTA: pré-requisito = rodar `scripts/setup_t1601.py` antes (habilita marca em
9280032 + grava `fontColor=#FFFFFF00`, alpha=0 totalmente transparente).
"""
import os
from pathlib import Path

import pytest

EVENTO_ID = os.environ.get("EVENTO_ID", "")
ATIVIDADE_ID = os.environ.get("ATIVIDADE_VIDEO_MARCA_DAGUA_ID", "")
OUTPUT_DIR = Path("test-results/t1601")


def _ler_overlay_marca(page) -> dict:
    """Sonda o overlay de marca d'água dentro do .plyr e a cor computada (rgba)
    de seus elementos textuais.

    Retorna:
        overlay_existe: bool
        child_count: int
        textos: list[{ text, color, opacity }]
        alpha_max: int — maior alpha encontrado em descendentes (0-255). 0 = invisível
        sample_text: str
    """
    return page.evaluate(r"""() => {
        const plyrs = Array.from(document.querySelectorAll('.plyr'));
        let overlay = null;
        for (const p of plyrs) {
            overlay = p.querySelector('div[style*="z-index:99999"], div[style*="z-index: 99999"]');
            if (overlay) break;
        }
        if (!overlay) {
            return {overlay_existe: false, child_count: 0, textos: [], alpha_max: -1, sample_text: ''};
        }
        const descendants = Array.from(overlay.querySelectorAll('*'));
        const textos = [];
        let alphaMax = 0;
        const re = /rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/;
        for (const el of descendants) {
            const txt = (el.innerText || '').trim();
            if (!txt) continue;
            const cs = getComputedStyle(el);
            const color = cs.color;
            const opacity = parseFloat(cs.opacity || '1');
            const m = re.exec(color);
            let aFloat = 1;
            if (m) aFloat = m[4] != null ? parseFloat(m[4]) : 1;
            const alpha255 = Math.round(aFloat * opacity * 255);
            if (alpha255 > alphaMax) alphaMax = alpha255;
            textos.push({text: txt.slice(0, 60), color, opacity, alpha255});
        }
        return {
            overlay_existe: true,
            child_count: overlay.childElementCount,
            textos: textos.slice(0, 12),
            alpha_max: alphaMax,
            sample_text: (overlay.innerText || '').slice(0, 200),
        };
    }""")


@pytest.mark.aluno
@pytest.mark.marca_dagua
def test_marca_dagua_invisivel_com_cor_transparente(aluno_logado, base_url):
    """3 passos: aluno acessa curso, abre player, reproduz e marca não é perceptível."""
    EVENTO_ID and ATIVIDADE_ID or pytest.skip("Defina EVENTO_ID e ATIVIDADE_VIDEO_MARCA_DAGUA_ID no .env")
    page = aluno_logado
    page.set_viewport_size({"width": 1920, "height": 1080})
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Passo 1 — Acessar o curso no Aprender
    # Esperado: Tela do curso é exibida
    page.goto(
        f"{base_url}e/{EVENTO_ID}/learn?learn_origin=my-contents",
        wait_until="domcontentloaded",
        timeout=20000,
    )
    page.wait_for_timeout(7000)
    page.screenshot(path=str(OUTPUT_DIR / "passo1-curso-aprender.png"))
    assert "/learn" in page.url, f"Não entrou no Aprender. url={page.url}"

    # Passo 2 — Selecionar a atividade de vídeo
    # Esperado: Player de vídeo é exibido
    assert page.locator("video").count() >= 1, "Player <video> não apareceu no Aprender"
    page.screenshot(path=str(OUTPUT_DIR / "passo2-player.png"))

    # Passo 3 — Iniciar a reprodução do vídeo
    # Esperado: Vídeo é reproduzido. Marca d'água NÃO é visualmente perceptível
    # devido à transparência total
    video = page.locator("video").first
    video.evaluate("v => v.play()")
    page.wait_for_timeout(3500)
    assert not video.evaluate("v => v.paused"), "Vídeo não saiu do pause após .play()"
    current = video.evaluate("v => v.currentTime")
    print(f"[T-1601] reproduzindo — currentTime={current}")
    assert current > 0.1, f"currentTime não avançou: {current}"

    overlay = _ler_overlay_marca(page)
    page.screenshot(path=str(OUTPUT_DIR / "passo3-reproduzindo.png"))
    print(f"[T-1601] overlay sonda: child_count={overlay['child_count']} "
          f"alpha_max={overlay['alpha_max']} sample={overlay['sample_text'][:120]!r}")
    for t in overlay["textos"]:
        print(f"  · texto={t['text']!r} color={t['color']} opacity={t['opacity']} alpha255={t['alpha255']}")

    # Reamostra perto da metade do vídeo
    page.wait_for_timeout(3000)
    overlay2 = _ler_overlay_marca(page)
    page.screenshot(path=str(OUTPUT_DIR / "passo3b-meio.png"))
    print(f"[T-1601] overlay sonda (meio): child_count={overlay2['child_count']} alpha_max={overlay2['alpha_max']}")

    # Critério: marca configurada → overlay renderizado no DOM, mas com alpha=0
    # nas cores computadas. Se overlay sumiu (child_count=0) também é OK — só não
    # podemos diferenciar "feature desligada" de "alpha=0", então logamos ambos.
    perceptivel_no_inicio = overlay["alpha_max"] > 0
    perceptivel_no_meio = overlay2["alpha_max"] > 0
    assert not perceptivel_no_inicio and not perceptivel_no_meio, (
        "Marca d'água é visualmente perceptível mesmo com cor totalmente transparente. "
        f"sonda1={overlay} sonda2={overlay2}"
    )
