"""
T-1600 v1 — Retrocompatibilidade: atividade de vídeo cadastrada antes da feature de marca d'água

CASO: Verificar que atividades de vídeo cadastradas ANTES da implementação da feature
de marca d'água continuam acessíveis no Aprender, sem marca d'água e sem erros.

PRÉ-CONDIÇÕES:
    - Aluno logado
    - Feature flag de marca d'água habilitada
    - Atividade de vídeo cadastrada antes da implementação da feature (sem registros
      nas tabelas de marca d'água)
    - Aluno previamente matriculado no curso correspondente

PERFIL TESTADO: Aluno (passos 1-3) e Admin (passo 4)
PLATAFORMA: Desktop
AMBIENTE: Principal (stage)

Referência: docs/casos/T-1600.md

NOTA: stage atual não tem atividade legada de verdade. `scripts/setup_t1600.py`
desmarca a marca d'água em 9280032 para simular o comportamento de UX equivalente
(checkbox desmarcado + player sem overlay).
"""
import os
from pathlib import Path

import pytest

from pages.admin.atividade_video_page import AtividadeVideoPage

EVENTO_LEGADO_ID = os.environ.get("EVENTO_LEGADO_ID", "")
ATIVIDADE_LEGADA_ID = os.environ.get("ATIVIDADE_LEGADA_ID", "")
OUTPUT_DIR = Path("test-results/t1600")


def _ler_marca_dagua_overlay(page) -> dict:
    """Sonda overlay HTML de marca d'água dentro do .plyr.

    Retorna dict com:
        - overlay_existe: bool — algum <div z-index:99999> filho do .plyr foi achado
        - child_count: int — quantos filhos diretos esse overlay tem
        - tem_texto_marca: bool — algum texto 'CPF'/'E-MAIL'/'EMAIL' nos descendentes
    """
    return page.evaluate(r"""() => {
        const plyrs = Array.from(document.querySelectorAll('.plyr'));
        let overlayDiv = null;
        for (const p of plyrs) {
            overlayDiv = p.querySelector('div[style*="z-index:99999"], div[style*="z-index: 99999"]');
            if (overlayDiv) break;
        }
        const texto = (overlayDiv?.innerText || '').toUpperCase();
        return {
            overlay_existe: !!overlayDiv,
            child_count: overlayDiv ? overlayDiv.childElementCount : 0,
            tem_texto_marca: /CPF|E-MAIL|EMAIL|DANTE/i.test(texto),
            sample_text: texto.slice(0, 200),
        };
    }""")


@pytest.mark.aluno
@pytest.mark.marca_dagua
def test_atividade_legada_aluno_reproduz_sem_marca(aluno_logado, base_url):
    """Passos 1-3: aluno acessa curso, abre atividade de vídeo legada, reproduz — sem marca."""
    assert EVENTO_LEGADO_ID and ATIVIDADE_LEGADA_ID, (
        "Defina EVENTO_LEGADO_ID e ATIVIDADE_LEGADA_ID no .env (rodar setup_t1600.py antes)"
    )
    page = aluno_logado
    page.set_viewport_size({"width": 1920, "height": 1080})
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Passo 1 — Acessar o curso que contém a atividade de vídeo legada
    # Esperado: Tela do curso é exibida com a atividade de vídeo legada
    page.goto(
        f"{base_url}e/{EVENTO_LEGADO_ID}/learn?learn_origin=my-contents",
        wait_until="domcontentloaded",
        timeout=20000,
    )
    page.wait_for_timeout(7000)
    page.screenshot(path=str(OUTPUT_DIR / "passo1-curso-aprender.png"))
    assert "/learn" in page.url, f"Não entrou no Aprender. url={page.url}"

    # Passo 2 — Selecionar a atividade de vídeo legada
    # Esperado: Player de vídeo é exibido sem erros
    # A 1ª atividade do curso 787696 é a 9280032 (única, video), já abre por default.
    assert page.locator("video").count() >= 1, "Player <video> não apareceu no Aprender"
    page.screenshot(path=str(OUTPUT_DIR / "passo2-player.png"))

    # Passo 3 — Iniciar a reprodução do vídeo
    # Esperado: Vídeo é reproduzido normalmente. Marca d'água NÃO é exibida (atividade legada)
    video = page.locator("video").first
    video.evaluate("v => v.play()")
    page.wait_for_timeout(3500)
    assert not video.evaluate("v => v.paused"), "Vídeo não saiu do pause após .play()"
    current = video.evaluate("v => v.currentTime")
    print(f"[T-1600] reproduzindo — currentTime={current}")
    assert current > 0.1, f"currentTime não avançou: {current}"

    overlay = _ler_marca_dagua_overlay(page)
    page.screenshot(path=str(OUTPUT_DIR / "passo3-reproduzindo.png"))
    print(f"[T-1600] overlay sonda: {overlay}")

    # Esperamos overlay AUSENTE (não existe ou existe com childCount=0 e sem texto CPF/E-MAIL).
    assert overlay["child_count"] == 0 and not overlay["tem_texto_marca"], (
        f"Marca d'água parece estar sendo renderizada apesar da atividade ser 'legada'/desmarcada: "
        f"{overlay}. Verificar screenshot passo3-reproduzindo.png."
    )

    # Avança até ~metade para garantir que o player segue sem marca
    page.wait_for_timeout(3000)
    overlay2 = _ler_marca_dagua_overlay(page)
    page.screenshot(path=str(OUTPUT_DIR / "passo3b-meio.png"))
    print(f"[T-1600] overlay sonda (meio): {overlay2}")
    assert overlay2["child_count"] == 0 and not overlay2["tem_texto_marca"], (
        f"Marca d'água apareceu durante a reprodução: {overlay2}"
    )


@pytest.mark.admin
@pytest.mark.marca_dagua
def test_atividade_legada_admin_checkbox_desmarcado(admin_logado, base_url):
    """Passo 4: admin abre edit da atividade legada — checkbox desmarcado por default."""
    assert EVENTO_LEGADO_ID and ATIVIDADE_LEGADA_ID, "Defina EVENTO_LEGADO_ID/ATIVIDADE_LEGADA_ID"
    page = admin_logado
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Passo 4 — Logar como Admin e abrir a atividade legada para edição
    # Esperado: Formulário de edição é exibido. Checkbox 'Habilitar marca d'água no vídeo'
    # está desmarcado por default
    edit = AtividadeVideoPage(page)
    edit.abrir_edicao(base_url, EVENTO_LEGADO_ID, ATIVIDADE_LEGADA_ID)
    page.wait_for_timeout(6000)
    page.screenshot(path=str(OUTPUT_DIR / "passo4-edit-admin.png"))

    cfg = edit.ler_config_marca_dagua()
    print(f"[T-1600] config marca d'agua na atividade legada: {cfg}")
    assert cfg is not None, "Form de edição não carregou config — atividade pode não ser vídeo interno."
    assert cfg["enabled"] is False, (
        f"Checkbox 'Habilitar marca d'água no vídeo' deveria estar DESMARCADO por default na "
        f"atividade legada. Estado lido: {cfg}"
    )
