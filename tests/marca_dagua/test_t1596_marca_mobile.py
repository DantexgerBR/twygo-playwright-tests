"""
T-1596 v1 — Reprodução do vídeo no Aprender exibe marca d'água em viewport (Mobile)

CASO: Verificar que a marca d'água é exibida corretamente sobre o vídeo no Aprender
quando acessado em viewport Mobile.

PRÉ-CONDIÇÕES:
    - Aluno logado
    - Feature flag de marca d'água habilitada
    - Atividade de vídeo previamente cadastrada com marca d'água habilitada
      (informações: CPF, E-mail; posição: 'Sobre todo o vídeo')
    - Aluno previamente matriculado no curso
    - Viewport Mobile (360x740)

PERFIL TESTADO: Aluno
PLATAFORMA: Mobile (360x740)
AMBIENTE: Principal (stage)

Referência: docs/casos/T-1596.md

OBSERVAÇÃO: marca d'água é overlay HTML/CSS injetado no `<div z-index=99999>` filho do
container Plyr. No desktop é populado; no mobile permanece vazio (childCount == 0).
A asserção principal compara o childCount esperado (>0) com o atual.
"""
import os
from pathlib import Path

import pytest

EVENTO_ID = os.environ.get("EVENTO_ID", "")
ATIVIDADE_ID = os.environ.get("ATIVIDADE_VIDEO_MARCA_DAGUA_ID", "")
OUTPUT_DIR = Path("test-results/t1596")


@pytest.mark.aluno
@pytest.mark.marca_dagua
@pytest.mark.mobile
def test_marca_dagua_em_viewport_mobile(browser, aluno_credentials, base_url):
    EVENTO_ID and ATIVIDADE_ID or pytest.skip("Defina EVENTO_ID e ATIVIDADE_VIDEO_MARCA_DAGUA_ID no .env")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
    page = context.new_page()

    try:
        # Login (manual, pois precisa do context mobile dedicado)
        page.goto(base_url + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(aluno_credentials["email"])
        page.locator("#user_password").fill(aluno_credentials["password"])
        page.locator("#user_submit").click()
        page.wait_for_load_state("domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)

        # Passo 1 — Acessar o curso no Aprender
        # Esperado: Tela do curso é exibida no layout mobile
        page.goto(
            f"{base_url}e/{EVENTO_ID}/learn?learn_origin=my-contents",
            wait_until="domcontentloaded",
            timeout=20000,
        )
        page.wait_for_timeout(6000)
        assert "/learn" in page.url

        # Passo 2 — Selecionar a atividade de vídeo
        # Esperado: Player de vídeo é exibido no layout mobile
        page.get_by_text("vídeo", exact=False).first.click(timeout=5000)
        page.wait_for_timeout(4500)
        assert page.locator("video").count() >= 1, "Player <video> não apareceu em mobile"

        # Passo 3 — Iniciar a reprodução do vídeo
        # Esperado: Vídeo é reproduzido. Marca d'água exibida 'Sobre todo o vídeo' com CPF + E-mail
        page.evaluate("() => { const v = document.querySelector('video'); v.muted = true; v.play(); }")
        page.wait_for_timeout(3000)
        assert not page.evaluate("() => document.querySelector('video').paused"), \
            "Vídeo não saiu do pause"

        # Verifica o overlay de marca d'água
        watermark_child_count = page.evaluate("""() => {
            const divs = Array.from(document.querySelectorAll('div')).filter(el => {
                const s = window.getComputedStyle(el);
                return s.zIndex === '99999' && s.position === 'absolute';
            });
            return divs.length > 0 ? divs[0].children.length : -1;
        }""")
        # Aqui está o bug: em mobile o overlay fica vazio (childCount=0)
        assert watermark_child_count > 0, (
            f"Marca d'água ausente em viewport mobile — overlay vazio "
            f"(childCount={watermark_child_count}). Comparar com desktop "
            f"onde o mesmo overlay tem 6 children renderizados (CPF + E-mail)."
        )

        # Passo 4 — Verificar visibilidade durante toda a reprodução
        page.wait_for_timeout(4000)  # meio
        wm_meio = page.evaluate("""() => {
            const divs = Array.from(document.querySelectorAll('div')).filter(el => {
                const s = window.getComputedStyle(el);
                return s.zIndex === '99999' && s.position === 'absolute';
            });
            return divs.length > 0 ? divs[0].children.length : -1;
        }""")
        assert wm_meio > 0, f"Marca d'água ausente no meio da reprodução (childCount={wm_meio})"

        page.wait_for_timeout(4000)  # fim
        wm_fim = page.evaluate("""() => {
            const divs = Array.from(document.querySelectorAll('div')).filter(el => {
                const s = window.getComputedStyle(el);
                return s.zIndex === '99999' && s.position === 'absolute';
            });
            return divs.length > 0 ? divs[0].children.length : -1;
        }""")
        assert wm_fim > 0, f"Marca d'água ausente perto do fim (childCount={wm_fim})"
    finally:
        context.close()
