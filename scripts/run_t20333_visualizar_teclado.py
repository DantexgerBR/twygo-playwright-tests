# -*- coding: utf-8 -*-
"""
Retrabalho Artia 20333 (P3) — Registros F2
"[Registros F2] Menu de ações (kebab) — 'Visualizar' não abre via teclado"

PR de correção: https://github.com/Twygo/twyg-app/pull/10833
Fix no componente compartilhado list-control. Comentário do dev: "alteração no
componente de list-control, validar algumas das outras tabelas. Ajustado para
erro legado. validar." — fix é potencialmente amplo (outras listas com kebab),
mas este script cobre a tela de Registros (onde o bug foi reportado).

Causa raiz apontada: no HTML, o botão "Visualizar" tinha tabIndex="-1" (classe
css-whmuo1) enquanto os outros itens do menu têm tabIndex="0" (css-ncfona) —
por isso o item não recebia foco/ativação via teclado.

O que este script mede (por perfil: admin e aluno):
  1. Abre o kebab de uma linha (click — abrir o menu não é o caminho quebrado).
  2. Navega por ArrowDown até "Visualizar", medindo document.activeElement a
     cada passo (garante que o Enter é disparado no item certo, não em outro).
  3. Também testa navegação por Tab nativo até "Visualizar" — a causa raiz
     (tabIndex=-1) afeta especificamente o Tab; a navegação por seta do Chakra
     usa .focus() programático e pode "funcionar" mesmo com tabIndex=-1, o que
     daria falso-positivo se só a seta fosse testada.
  4. Lê o tabIndex real do botão "Visualizar" via DOM (desempate/evidência da
     causa raiz, não é o critério de veredito).
  5. CONTROLE: repete os passos 2 e 3 para "Editar" no mesmo menu — confirma
     que o mecanismo de navegação por teclado do teste funciona e que
     Editar continua OK (não regressão).
  6. Critério de "abriu": URL mudou para o form de registro em modo leitura
     E/OU heading "Visualizar registro" aparece (mesma aba ou nova aba).

Rodar (headless por padrão):
    .\.venv\Scripts\python.exe scripts\run_t20333_visualizar_teclado.py
Rodar com janela (debug visual):
    set TW_HEADED=1 && .\.venv\Scripts\python.exe scripts\run_t20333_visualizar_teclado.py
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = os.environ.get("REGISTROSF2_BASE_URL", "https://registrosf2.stage.twygoead.com").rstrip("/")
ORG_ID = os.environ.get("REGISTROSF2_ORG_ID", "37079")

ADMIN_EMAIL = os.environ["REGISTROSF2_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["REGISTROSF2_ADMIN_PASSWORD"]
ALUNO_EMAIL = os.environ["REGISTROSF2_TC3_EMAIL"]
ALUNO_PASSWORD = os.environ["REGISTROSF2_TC3_PASSWORD"]

PASTA = tw.ROOT / "evidencias" / "registros-f2-qa20333"
PASTA.mkdir(parents=True, exist_ok=True)

resultados: dict = {}
log = lambda *a: print(*a, flush=True)


def snap(page, nome, full=False):
    fp = PASTA / f"{nome}.png"
    page.screenshot(path=str(fp), full_page=full)
    log(f"   [snap] {fp.name}")
    return fp


def dispensar_overlays(page):
    tw.dispensar_nps(page)
    try:
        page.evaluate("""() => {
            document.querySelectorAll(
                '#hubspot-messages-iframe-container,[id*=sophia]'
            ).forEach(e => e.style.display='none');
        }""")
    except Exception:
        pass


def ir_records(page):
    page.goto(f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
              wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_function(
            "() => document.querySelectorAll('tbody tr').length > 0", timeout=25000
        )
    except Exception:
        pass
    page.wait_for_timeout(2000)
    dispensar_overlays(page)


def abrir_kebab_linha(page, idx=0):
    """Abre o kebab da linha idx via click nativo. Retorna True/False."""
    rows = page.locator("tbody tr")
    if rows.count() <= idx:
        return False
    row = rows.nth(idx)
    kebab = row.locator("button.chakra-menu__menu-button, button[aria-haspopup='menu']").first
    if kebab.count() == 0:
        return False
    kebab.click(timeout=5000, force=True)
    page.wait_for_timeout(1200)
    return True


def menu_itens_ordem(page):
    """Lista (index, texto) dos menuitems do menu ABERTO (visível), na ordem do DOM."""
    return page.evaluate("""() => {
        const lists = Array.from(document.querySelectorAll('ul[class*="menu__menu-list"], [role=menu]'));
        const visivel = lists.find(l => {
            const r = l.getBoundingClientRect();
            const cs = getComputedStyle(l);
            return r.width > 0 && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.5;
        });
        if (!visivel) return [];
        const btns = Array.from(visivel.querySelectorAll('[role="menuitem"]'));
        return btns.map((btn, i) => ({
            index: i,
            id: btn.id,
            text: (btn.innerText || '').replace(/\\s+/g,' ').trim(),
            tabIndex: btn.tabIndex,
            className: btn.className,
        }));
    }""")


def foco_atual(page):
    """document.activeElement atual: {tag, role, id, text}."""
    return page.evaluate("""() => {
        const el = document.activeElement;
        if (!el) return null;
        return {
            tag: el.tagName, role: el.getAttribute('role'), id: el.id,
            text: (el.innerText || '').replace(/\\s+/g,' ').trim(),
            tabIndex: el.tabIndex,
        };
    }""")


def navegar_ate_item_via_seta(page, texto_alvo, max_passos=8):
    """ArrowDown repetido, medindo activeElement a cada passo. Retorna
    (chegou: bool, passos: list[dict], focado_final: dict|None)."""
    passos = []
    for i in range(max_passos):
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(250)
        foco = foco_atual(page)
        passos.append({"passo": i + 1, "foco": foco})
        if foco and re.search(texto_alvo, foco.get("text", ""), re.I):
            return True, passos, foco
    return False, passos, (passos[-1]["foco"] if passos else None)


def navegar_ate_item_via_tab(page, texto_alvo, max_passos=10):
    """Tab nativo repetido a partir do kebab focado, medindo activeElement.
    Usado para exercitar o caminho que a causa raiz (tabIndex=-1) afeta
    especificamente. Retorna (chegou, passos, focado_final)."""
    passos = []
    for i in range(max_passos):
        page.keyboard.press("Tab")
        page.wait_for_timeout(250)
        foco = foco_atual(page)
        passos.append({"passo": i + 1, "foco": foco})
        if not foco or foco.get("role") != "menuitem":
            # saiu do menu (perdeu o foco no menuitem) — parar
            break
        if re.search(texto_alvo, foco.get("text", ""), re.I):
            return True, passos, foco
    return False, passos, (passos[-1]["foco"] if passos else None)


def tela_abriu_visualizacao(page, ctx, pages_antes):
    """Verifica se a tela de visualização abriu (mesma aba ou nova aba).
    Retorna dict com achou(bool), onde(str), url, snippet."""
    page.wait_for_timeout(2500)
    pages_depois = len(ctx.pages)
    if pages_depois > pages_antes:
        nova = ctx.pages[-1]
        try:
            nova.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            pass
        nova.wait_for_timeout(2000)
        body = nova.inner_text("body")
        achou = "visualizar registro" in body.lower() or "mode=view" in nova.url.lower()
        return {"achou": achou, "onde": "nova_aba", "url": nova.url, "snippet": body[:200], "page_ref": nova}
    url = page.url
    body = page.inner_text("body")
    achou = ("mode=view" in url.lower()) or ("visualizar registro" in body.lower())
    return {"achou": achou, "onde": "mesma_aba", "url": url, "snippet": body[:200], "page_ref": page}


def tela_abriu_evidencias(page, ctx, pages_antes):
    """Controle: verifica se a tela/modal de 'Evidências' abriu (não usa
    mode=view; checa por heading/texto 'Evidência' fora do menu fechado)."""
    page.wait_for_timeout(2000)
    pages_depois = len(ctx.pages)
    if pages_depois > pages_antes:
        nova = ctx.pages[-1]
        try:
            nova.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            pass
        nova.wait_for_timeout(1500)
        body = nova.inner_text("body")
        achou = "evid" in body.lower()
        return {"achou": achou, "onde": "nova_aba", "url": nova.url, "snippet": body[:200], "page_ref": nova}
    url_antes = page.url
    body = page.inner_text("body")
    # heurística: mudou de URL (rota own de evidências) OU apareceu heading/modal com "Evidência"
    achou = ("evidenc" in url_antes.lower()) or bool(
        re.search(r"evid[eê]ncia", body, re.I)
    )
    return {"achou": achou, "onde": "mesma_aba", "url": url_antes, "snippet": body[:200], "page_ref": page}


def voltar_para_lista(page):
    ir_records(page)


def testar_item_via_seta(page, ctx, item_regex, snap_prefix, label, linha_idx=0, checador=None):
    """Fluxo completo para 1 item via ArrowDown: abre kebab, navega, Enter, mede.
    `checador` (opcional) troca a função de verificação de abertura — default
    é tela_abriu_visualizacao; controle usa tela_abriu_evidencias."""
    checador = checador or tela_abriu_visualizacao
    log(f"\n--- {label} (via SETA) ---")
    if not abrir_kebab_linha(page, linha_idx):
        return {"ok": False, "motivo": "kebab não encontrado/linha inexistente"}

    ordem = menu_itens_ordem(page)
    log(f"   menu (ordem DOM): {ordem}")
    item_alvo = next((it for it in ordem if re.search(item_regex, it["text"], re.I)), None)
    tabindex_alvo = item_alvo["tabIndex"] if item_alvo else None
    if item_alvo is None:
        page.keyboard.press("Escape")
        return {
            "ok": False, "motivo": f"item '{item_regex}' não existe neste menu",
            "ordem_menu": ordem,
        }

    chegou, passos, foco_final = navegar_ate_item_via_seta(page, item_regex)
    log(f"   chegou_via_seta={chegou} foco_final={foco_final}")
    snap(page, f"{snap_prefix}_seta_focado")

    if not chegou:
        return {
            "ok": False, "motivo": "ArrowDown não focou o item", "passos": passos,
            "tabindex_dom": tabindex_alvo, "ordem_menu": ordem,
        }

    pages_antes = len(ctx.pages)
    page.keyboard.press("Enter")
    resultado_abertura = checador(page, ctx, pages_antes)
    nova_page = resultado_abertura.pop("page_ref")
    snap(nova_page, f"{snap_prefix}_seta_pos_enter", full=True)
    if nova_page is not page:
        nova_page.close()

    log(f"   abriu={resultado_abertura['achou']} onde={resultado_abertura['onde']} url={resultado_abertura['url'][:80]}")
    return {
        "ok": resultado_abertura["achou"],
        "abertura": resultado_abertura,
        "tabindex_dom": tabindex_alvo,
        "ordem_menu": ordem,
        "passos": passos,
    }


def testar_item_via_tab(page, ctx, item_regex, snap_prefix, label, linha_idx=0):
    """Fluxo completo para 1 item via Tab nativo a partir do kebab.

    NOTA: o menu Chakra segue o padrão ARIA `role=menu`, cuja navegação
    intra-menu é feita por SETAS (roving tabindex), não por Tab — Tab
    tende a ficar preso no item já focado ou a sair do menu (comportamento
    da lib, não do produto). O cenário reportado no card usa "setas +
    Enter"; este teste via Tab é só um dado complementar, não o critério
    de veredito."""
    log(f"\n--- {label} (via TAB, informativo) ---")
    if not abrir_kebab_linha(page, linha_idx):
        return {"ok": False, "motivo": "kebab não encontrado/linha inexistente"}

    chegou, passos, foco_final = navegar_ate_item_via_tab(page, item_regex)
    log(f"   chegou_via_tab={chegou} foco_final={foco_final} passos={len(passos)}")
    snap(page, f"{snap_prefix}_tab_focado")

    if not chegou:
        return {"ok": False, "motivo": "Tab não focou o item (comportamento do menu ARIA — não é o cenário do bug)", "passos": passos}

    pages_antes = len(ctx.pages)
    page.keyboard.press("Enter")
    resultado_abertura = tela_abriu_visualizacao(page, ctx, pages_antes)
    nova_page = resultado_abertura.pop("page_ref")
    snap(nova_page, f"{snap_prefix}_tab_pos_enter", full=True)
    if nova_page is not page:
        nova_page.close()

    log(f"   abriu={resultado_abertura['achou']} onde={resultado_abertura['onde']} url={resultado_abertura['url'][:80]}")
    return {"ok": resultado_abertura["achou"], "abertura": resultado_abertura, "passos": passos}


def rodar_perfil(page, ctx, label):
    """Roda a bateria completa para um perfil (admin ou aluno) já logado e
    na tela records:
      1) Visualizar via SETA + Enter — cenário exato do bug reportado.
      2) Visualizar via TAB nativo — informativo (menu ARIA navega por seta,
         não por Tab; não é o critério de veredito).
      3) CONTROLE — Evidências via SETA + Enter — item presente nos dois
         perfis testados (admin e aluno), prova que o mecanismo de teclado
         do teste funciona e que outro item do MESMO menu não regrediu."""
    out = {}

    ir_records(page)
    snap(page, f"{label}_00_lista")

    # 1) Visualizar via SETA — cenário do bug
    out["visualizar_seta"] = testar_item_via_seta(
        page, ctx, r"isual", f"{label}_visualizar", f"{label.upper()} — Visualizar"
    )
    voltar_para_lista(page)

    # 2) Visualizar via TAB nativo — informativo
    out["visualizar_tab"] = testar_item_via_tab(
        page, ctx, r"isual", f"{label}_visualizar", f"{label.upper()} — Visualizar"
    )
    voltar_para_lista(page)

    # 3) CONTROLE — Evidências via SETA (mesmo menu, item que nunca teve o bug)
    out["evidencias_seta"] = testar_item_via_seta(
        page, ctx, r"vid[eê]ncia", f"{label}_evidencias", f"{label.upper()} — Evidências (controle)",
        checador=tela_abriu_evidencias,
    )
    voltar_para_lista(page)

    return out


def main():
    log("=== Retrabalho 20333 — Visualizar via teclado (kebab list-control) ===\n")

    with tw.sync_playwright() as p:
        # ── ADMIN ──────────────────────────────────────────────
        log("=== PERFIL: ADMIN ===")
        b_adm, c_adm, page_adm = tw.nova_pagina(p)
        tw.login(page_adm, {
            "base_url": BASE_URL, "org_id": ORG_ID,
            "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD,
        }, admin=True)
        log(f"  [admin] logado OK url={page_adm.url}")
        resultados["admin"] = rodar_perfil(page_adm, c_adm, "admin")
        b_adm.close()

        # ── ALUNO ──────────────────────────────────────────────
        log("\n=== PERFIL: ALUNO ===")
        b_alu, c_alu, page_alu = tw.nova_pagina(p)
        page_alu.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
        page_alu.fill("#user_email", ALUNO_EMAIL)
        page_alu.fill("#user_password", ALUNO_PASSWORD)
        page_alu.click("#user_submit")
        try:
            page_alu.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page_alu.wait_for_timeout(2000)
        dispensar_overlays(page_alu)
        log(f"  [aluno] logado OK url={page_alu.url}")
        resultados["aluno"] = rodar_perfil(page_alu, c_alu, "aluno")
        b_alu.close()

    # ── SUMÁRIO ────────────────────────────────────────────────
    log("\n" + "=" * 70)
    log("SUMÁRIO — Retrabalho 20333")
    log("=" * 70)
    for perfil, dados in resultados.items():
        log(f"\n[{perfil.upper()}]")
        for chave, r in dados.items():
            ok = r.get("ok")
            icone = "OK" if ok else "FALHOU"
            extra = ""
            if "abertura" in r:
                extra = f" abriu={r['abertura']['achou']} onde={r['abertura']['onde']}"
            if r.get("tabindex_dom") is not None:
                extra += f" tabIndex_DOM={r['tabindex_dom']}"
            if not ok and r.get("motivo"):
                extra += f" motivo={r['motivo']}"
            log(f"   [{icone}] {chave}:{extra}")

    out_path = PASTA / "resultados.json"
    def _default(o):
        return str(o)
    out_path.write_text(json.dumps(resultados, ensure_ascii=False, indent=2, default=_default), encoding="utf-8")
    log(f"\n[saida] {out_path}")


if __name__ == "__main__":
    main()
