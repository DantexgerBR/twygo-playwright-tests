"""
T-1602 v1 — Verificar a marca d'água nas outras atividades existente num curso

CASO: Garantir que a opção de marca d'água do VÍDEO (`#water-mark-video-enabled`)
NÃO seja exibida no form de edição quando o tipo de atividade for diferente de
vídeo interno. O caso lista 8 tipos: Texto, Página, Aula, PDF Estampado,
Vídeo Externo, Questionário, Scorm, Games.

PRÉ-CONDIÇÕES:
    - Admin logado
    - Feature flag de marca d'água habilitada
    - Atividades de cada tipo existem (ou podem ser simuladas pelo radio
      `media_type` do form de edição)

PERFIL TESTADO: Admin
PLATAFORMA: Desktop
AMBIENTE: Principal (stage)

Referência: docs/casos/T-1602.md

ESTRATÉGIA: o form de edição de qualquer atividade do tipo vídeo (9280032)
expõe todos os 9 radios `media_type`. Clicar em um radio diferente re-renderiza
o form mostrando os campos do novo tipo SEM persistir nada (até o Salvar). O
teste itera pelos 8 tipos do caso e valida a ausência do checkbox de marca
d'água. NÃO clica em Salvar — não altera estado da 9280032.

OBSERVAÇÃO: o tipo "PDF Estampado" (media_type=pdf) tem sua própria feature
"Habilitar marca d'água NO ARQUIVO" (checkbox distinto do #water-mark-video-enabled).
O teste valida especificamente a ausência da marca d'água DE VÍDEO; a marca de
PDF é uma feature paralela legítima.
"""
import os
from pathlib import Path

import pytest

EVENTO_ID = os.environ.get("EVENTO_ID", "")
ATIVIDADE_ID = os.environ.get("ATIVIDADE_VIDEO_MARCA_DAGUA_ID", "")
OUTPUT_DIR = Path("test-results/t1602")

# Mapeia rótulo do caso → media_type (radio name)
TIPOS_DO_CASO = [
    ("Texto", "text"),
    ("Página", "page"),
    ("Aula", "lesson"),
    ("PDF Estampado", "pdf"),
    ("Vídeo Externo", "external"),
    ("Questionário", "questions"),
    ("Scorm", "scorm"),
    ("Games", "games"),
]


def _ler_estado_marca_video(page) -> dict:
    """Retorna se o checkbox e o label de 'marca d'água no vídeo' estão visíveis."""
    return page.evaluate(r"""() => {
        const visible = (el) => {
            if (!el) return false;
            const r = el.getBoundingClientRect();
            const cs = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none';
        };
        const cb = document.querySelector('#water-mark-video-enabled');
        let cb_label_visible = false;
        if (cb) {
            const lbl = cb.closest('label.chakra-checkbox') || cb.parentElement;
            cb_label_visible = visible(lbl);
        }
        // Conta labels com texto exato 'Habilitar marca d'água no vídeo'
        const labels_video = Array.from(document.querySelectorAll('label, p, span, div'))
            .filter(el => /Habilitar marca d['']água no vídeo/i.test(el.innerText || ''))
            .filter(visible);
        // Conta labels com texto 'Habilitar marca d'água no arquivo' (feature distinta)
        const labels_arquivo = Array.from(document.querySelectorAll('label, p, span, div'))
            .filter(el => /Habilitar marca d['']água no arquivo/i.test(el.innerText || ''))
            .filter(visible);
        return {
            video_cb_exists: !!cb,
            video_cb_label_visible: cb_label_visible,
            video_label_count: labels_video.length,
            arquivo_label_count: labels_arquivo.length,
        };
    }""")


def _abrir_form_e_selecionar_tipo(page, base_url: str, tipo_radio_value: str):
    """Abre o form de edição e clica o radio media_type. Não salva."""
    page.goto(
        f"{base_url}e/{EVENTO_ID}/contents/{ATIVIDADE_ID}/edit",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    page.wait_for_timeout(6000)
    radio = page.locator(f"input[name='media_type'][value='{tipo_radio_value}']").first
    assert radio.count() > 0, f"radio media_type={tipo_radio_value} não encontrado no form"
    rid = radio.get_attribute("id")
    if rid:
        lbl = page.locator(f"label[for='{rid}']").first
        lbl.scroll_into_view_if_needed()
        lbl.click()
    else:
        radio.check(force=True, timeout=3000)
    page.wait_for_timeout(3000)


@pytest.mark.admin
@pytest.mark.marca_dagua
@pytest.mark.parametrize("rotulo,radio_value", TIPOS_DO_CASO, ids=[r[0] for r in TIPOS_DO_CASO])
def test_marca_dagua_video_oculta_em_tipo(admin_logado, base_url, rotulo, radio_value):
    """Para cada tipo do caso, ao selecionar o radio `media_type`, o form NÃO
    deve mostrar o checkbox `#water-mark-video-enabled` (marca d'água do vídeo).
    """
    EVENTO_ID and ATIVIDADE_ID or pytest.skip("Defina EVENTO_ID e ATIVIDADE_VIDEO_MARCA_DAGUA_ID")
    page = admin_logado
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    _abrir_form_e_selecionar_tipo(page, base_url, radio_value)
    safe = radio_value.replace("/", "_")
    page.screenshot(path=str(OUTPUT_DIR / f"tipo_{safe}.png"), full_page=True)
    estado = _ler_estado_marca_video(page)
    print(f"[T-1602] tipo={rotulo} ({radio_value}) → {estado}")

    assert not estado["video_cb_exists"], (
        f"Checkbox #water-mark-video-enabled estava presente para tipo {rotulo!r} "
        f"({radio_value}) — esperado AUSENTE. Estado: {estado}"
    )
    assert estado["video_label_count"] == 0, (
        f"Label 'Habilitar marca d'água no vídeo' visível para tipo {rotulo!r} "
        f"({radio_value}) — esperado 0. Estado: {estado}"
    )


@pytest.mark.admin
@pytest.mark.marca_dagua
def test_marca_dagua_video_presente_para_video_interno_referencia(admin_logado, base_url):
    """Sanity check: o checkbox DEVE existir para media_type=video (vídeo interno)."""
    if not (EVENTO_ID and ATIVIDADE_ID):
        pytest.skip("EVENTO_ID/ATIVIDADE_VIDEO_MARCA_DAGUA_ID não definidos no .env")
    page = admin_logado
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    _abrir_form_e_selecionar_tipo(page, base_url, "video")
    page.screenshot(path=str(OUTPUT_DIR / "tipo_video_referencia.png"), full_page=True)
    estado = _ler_estado_marca_video(page)
    print(f"[T-1602] tipo=Vídeo Interno (video) → {estado}")
    assert estado["video_cb_exists"], (
        f"Checkbox #water-mark-video-enabled NÃO encontrado para media_type=video — "
        f"feature de marca d'água do vídeo pode estar quebrada. Estado: {estado}"
    )
