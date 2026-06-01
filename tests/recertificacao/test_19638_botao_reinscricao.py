"""CARD 19638 (P1) [Recertificação] — Botão "Iniciar reinscrição" deve aparecer
para TODOS os participantes na lista de Aprendizagem (habilitado p/ quem cumpre
critério; bloqueado + tooltip p/ quem não cumpre).

Env: EDUAPI (org 36912), conteúdo "Gestão para resultados" (798476) — o único com
"Habilitar reinscrição" ON na org. Pula (não falha) sem credencial/conteúdo/dados.

Referência: evidencias/19638_botao_reinscricao/LAUDO.md
"""
import pytest

from pages.admin.aprendizagem_page import AprendizagemPage

CONTEUDO_ID = "798476"


def _eh_elegivel(p: dict) -> bool:
    # critério de reinscrição: 100% de progresso OU aprovado OU certificado emitido
    return p.get("progresso") == "100%" or bool(p.get("aprovado")) or "Emitido" in (p.get("certificado") or "")


@pytest.mark.recertificacao
@pytest.mark.reinscricao
def test_iniciar_reinscricao_aparece_para_todos(admin_em):
    page, base = admin_em("EDUAPI")
    ap = AprendizagemPage(page)
    ap.abrir(base, CONTEUDO_ID)

    participantes = ap.participantes()
    if not participantes:
        pytest.skip("Conteúdo 798476 sem participantes na aba Aprendizagem (dados de stage mudaram?)")

    # --- Cláusula principal do card: o item aparece para TODOS os participantes ---
    ausentes = []
    estados = {}  # itemId -> (elegivel, bloqueado)
    for p in participantes:
        ap.abrir_kebab(p["itemId"])
        item = ap.item_reinscricao()
        if not item.get("achou"):
            ausentes.append(p["email"])
            continue
        estados[p["itemId"]] = (_eh_elegivel(p), ap.reinscricao_bloqueada(item.get("corIcone")))
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

    assert not ausentes, (
        f"'Iniciar reinscrição' AUSENTE no kebab de: {ausentes} — deve aparecer para todos."
    )

    # --- Cláusula secundária: elegível = habilitado; não-elegível = bloqueado ---
    elegiveis = [iid for iid, (eleg, _) in estados.items() if eleg]
    nao_elegiveis = [iid for iid, (eleg, _) in estados.items() if not eleg]
    if elegiveis:
        bloqueados_indevidos = [iid for iid in elegiveis if estados[iid][1]]
        assert not bloqueados_indevidos, (
            f"Inscrições elegíveis com reinscrição BLOQUEADA: {bloqueados_indevidos}"
        )
    if nao_elegiveis:
        habilitados_indevidos = [iid for iid in nao_elegiveis if not estados[iid][1]]
        assert not habilitados_indevidos, (
            f"Inscrições NÃO-elegíveis com reinscrição HABILITADA: {habilitados_indevidos}"
        )
    if not elegiveis or not nao_elegiveis:
        pytest.skip(
            "Sem par de contraste (elegível x não-elegível) nos dados atuais — "
            "presença para todos foi validada; enabled/blocked não pôde ser contrastado."
        )
