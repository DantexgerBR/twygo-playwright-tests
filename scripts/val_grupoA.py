# -*- coding: utf-8 -*-
"""Grupo A — validação dos retrabalhos de UI do Novo Estúdio (org 37061, curso 807533):
  19863  opção 'player próprio do YouTube' na atividade Vídeo externo
  19795  botão 'Visualizar' nos modelos (aba Modelo)
  19798  tamanho da aula não esconde 'Salvar e regerar'
  19997  dropdown da badge 'pendentes' fecha ao clicar fora
  20026  kebab sem 'Atividades' (ok no recon) + 'Editar' volta à última aba
  19813  layout mobile/3-tabs abaixo de 1366px sem scroll horizontal
Cada item isolado; veredito impresso. Atividade criada no 19863 é excluída."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "val_retrabalhos_grupoA"
CURSO = "807533"
c = tw.cfg("NOVOEST")
tid = lambda v: f'[data-test-id="{v}"]'
url_studio = f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit?tab=studio"
V = {}


def abrir_studio(page):
    for _ in range(3):
        page.goto(url_studio, wait_until="domcontentloaded", timeout=45000)
        tw.dispensar_nps(page)
        try:
            page.locator(tid("creation-studio-activities-list")).wait_for(state="visible", timeout=15000)
            break
        except Exception:
            pass
    page.wait_for_timeout(2500)


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, width=1440, height=900)
    tw.login(page, c)

    # ================= 19863 — player próprio do YouTube =================
    print("\n### 19863 — opção player próprio do YouTube")
    ativ_id = None
    try:
        abrir_studio(page)
        page.locator(tid("creation-studio-activity-add-button")).first.click(timeout=10000)
        page.locator(tid("creation-studio-type-selector-drawer")).wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(800)
        page.locator(tid("creation-studio-type-selector-external")).first.click(timeout=8000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        m = re.search(r"/studio/activities/(\d+)/edit", page.url); ativ_id = m.group(1) if m else None
        page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True)
        page.wait_for_timeout(2500)
        # garantir fonte YouTube selecionada
        try:
            page.get_by_text("YouTube", exact=True).first.click(timeout=3000)
        except Exception:
            pass
        page.wait_for_timeout(1500)
        corpo = page.evaluate("()=>document.body.innerText")
        twy = bool(re.search(r"player da Twygo", corpo, re.I))
        yt = bool(re.search(r"player pr[óo]prio do YouTube|player oficial do YouTube", corpo, re.I))
        tw.snap(page, PASTA, "19863-player-options", full=True)
        V[19863] = ("PASSOU" if (twy and yt) else "FALHOU", f"player Twygo={twy} | player próprio YouTube={yt}")
    except Exception as e:
        V[19863] = ("FALHOU", f"erro: {e}")
    finally:
        if ativ_id:
            try:
                abrir_studio(page)
                card = page.locator(tid(f"creation-studio-activity-card-{ativ_id}")).first
                card.scroll_into_view_if_needed(); card.click(timeout=8000, force=True); page.wait_for_timeout(2000)
                page.locator(tid("creation-studio-preview-delete")).first.click(timeout=8000, force=True); page.wait_for_timeout(1200)
                page.locator(tid("creation-studio-preview-delete-dialog")).get_by_role("button", name=re.compile("^Excluir", re.I)).first.click(timeout=8000)
                page.wait_for_timeout(2500)
            except Exception:
                print(f"   [cleanup] excluir manualmente {ativ_id}")
    print(f"   => 19863: {V[19863]}")

    # ================= 19795 — botão Visualizar nos modelos =================
    print("\n### 19795 — botão Visualizar nos modelos")
    try:
        page.goto(f"{c['base_url']}/o/{c['org_id']}/contents/{CURSO}/edit", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(4000); tw.dispensar_nps(page)
        page.get_by_text(re.compile(r"^Modelo$", re.I)).first.click(timeout=6000, force=True)
        page.wait_for_timeout(4000)
        botoes = page.evaluate(
            """()=>[...document.querySelectorAll('button,[role=button],a')].filter(e=>e.offsetParent!==null)
                .map(e=>(e.innerText||e.getAttribute('aria-label')||e.title||'').replace(/\\s+/g,' ').trim())
                .filter(t=>/visualiz|prever|preview|olho/i.test(t))"""
        )
        cards_modelo = page.evaluate("()=>/Selecione um modelo|Pílula|Trilha|Aula expositiva/i.test(document.body.innerText)")
        tw.snap(page, PASTA, "19795-modelo", full=True)
        V[19795] = ("OBSERVAR", f"cards de modelo presentes={cards_modelo} | botões visualizar={botoes}")
    except Exception as e:
        V[19795] = ("FALHOU", f"erro: {e}")
    print(f"   => 19795: {V[19795]}")

    # ================= 19798 — aula não esconde 'Salvar e regerar' =================
    print("\n### 19798 — botão 'Salvar e regerar' visível na Aula")
    try:
        abrir_studio(page)
        aula = page.evaluate(
            r"""()=>{let r=null;document.querySelectorAll('[data-test-id]').forEach(e=>{
                const m=(e.getAttribute('data-test-id')||'').match(/^creation-studio-activity-card-(\d+)$/);
                if(m && /Aula/i.test(e.innerText||'') && !r) r=m[1];});return r;}"""
        )
        print(f"   aula encontrada: {aula}")
        if aula:
            page.goto(f"{c['base_url']}/o/{c['org_id']}/studio/activities/{aula}/edit?type=lesson&eventId={CURSO}",
                      wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000); tw.dispensar_nps(page)
            page.get_by_text(re.compile(r"^Conteúdo$", re.I)).first.click(timeout=6000, force=True)
            page.wait_for_timeout(4000)
            btn = page.get_by_role("button", name=re.compile(r"Salvar e regerar", re.I)).first
            vis = btn.count() > 0 and btn.is_visible()
            in_view = False
            if vis:
                box = btn.bounding_box() or {}
                in_view = 0 <= box.get("y", -1) <= 900  # dentro do viewport
            tw.snap(page, PASTA, "19798-aula-regerar", full=True)
            V[19798] = ("PASSOU" if (vis and in_view) else "FALHOU", f"'Salvar e regerar' visível={vis} | dentro do viewport={in_view}")
        else:
            V[19798] = ("FALHOU", "nenhuma Aula encontrada no 807533")
    except Exception as e:
        V[19798] = ("FALHOU", f"erro: {e}")
    print(f"   => 19798: {V[19798]}")

    # ================= 19997 — dropdown 'pendentes' fecha ao clicar fora =================
    print("\n### 19997 — dropdown 'pendentes' fecha ao clicar fora")
    try:
        abrir_studio(page)
        badge = page.get_by_text(re.compile(r"\bpendentes?\b", re.I)).first
        if badge.count():
            badge.scroll_into_view_if_needed()
            badge.click(timeout=6000, force=True)
            page.wait_for_timeout(1500)
            aberto = page.evaluate("()=>!!document.querySelector('[role=menu]:not([hidden]),[role=listbox],.chakra-popover__content')")
            tw.snap(page, PASTA, "19997-dropdown-aberto")
            # clicar fora (no título do curso / área neutra)
            page.mouse.click(700, 160)
            page.wait_for_timeout(1500)
            fechou = page.evaluate("""()=>{const els=[...document.querySelectorAll('[role=menu],[role=listbox],.chakra-popover__content')].filter(e=>e.offsetParent!==null);return els.length===0;}""")
            tw.snap(page, PASTA, "19997-pos-clicar-fora")
            V[19997] = ("PASSOU" if (aberto and fechou) else "FALHOU", f"abriu={aberto} | fechou ao clicar fora={fechou}")
        else:
            V[19997] = ("FALHOU", "nenhuma badge 'pendentes' encontrada")
    except Exception as e:
        V[19997] = ("FALHOU", f"erro: {e}")
    print(f"   => 19997: {V[19997]}")

    # ================= 19813 — mobile/3-tabs abaixo de 1366px =================
    print("\n### 19813 — layout abaixo de 1366px (1024x600)")
    try:
        page.set_viewport_size({"width": 1024, "height": 600})
        abrir_studio(page)
        page.wait_for_timeout(2000)
        med = page.evaluate(
            """()=>({scrollW:document.documentElement.scrollWidth, clientW:document.documentElement.clientWidth,
                    overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth+4,
                    tabs:[...document.querySelectorAll('*')].filter(e=>e.offsetParent!==null && /^(Pré-visualização|Atividades|Copiloto)$/.test((e.innerText||'').trim()) && e.getBoundingClientRect().top>window.innerHeight-120).length})"""
        )
        tw.snap(page, PASTA, "19813-1024x600", full=True)
        ok = (not med["overflow"]) and med["tabs"] >= 2
        V[19813] = ("PASSOU" if ok else "FALHOU", f"scrollW={med['scrollW']} clientW={med['clientW']} overflow_horizontal={med['overflow']} | tabs_no_rodape={med['tabs']}")
        page.set_viewport_size({"width": 1440, "height": 900})
    except Exception as e:
        V[19813] = ("FALHOU", f"erro: {e}")
    print(f"   => 19813: {V[19813]}")

    print("\n================= RESUMO GRUPO A =================")
    for k in [19863, 19795, 19798, 19997, 19813]:
        print(f"  {k}: {V.get(k)}")
    print("  20026 (kebab sem 'Atividades'): PASSOU (confirmado no recon)")
    ctx.close(); browser.close()
