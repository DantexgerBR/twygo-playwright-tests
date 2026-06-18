"""Retrabalho 20177 — aba "Avaliacoes a preencher" (Desenvolvimento / Desempenho).

Esperado: "Filtros padrao" deve listar apenas Pendentes, Atrasadas, Desempenho.
NAO deve mais exibir "Concluidas".
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

PASTA = tw.ROOT / "evidencias" / "filtro_avaliacoes_preencher"
c = tw.cfg("")  # org principal 36675 (dante tem acesso); valida flags do modulo


def listar_filtros_padrao(page):
    """Texto dos itens sob 'Filtros padrao' no painel 'Lista de filtros'."""
    return page.evaluate(
        r"""()=>{
            const heads=Array.from(document.querySelectorAll('*')).filter(e=>
                /^Filtros padr/i.test((e.textContent||'').trim()) && e.children.length===0);
            // pega o container do accordion de 'Filtros padrao' e lista os radios/labels
            const radios=Array.from(document.querySelectorAll('input[type=radio]'));
            const labels=radios.map(r=>{
                const lab=r.closest('label')||r.parentElement;
                return (lab&&lab.innerText||'').replace(/\s+/g,' ').trim();
            }).filter(Boolean);
            return {radios:labels};
        }"""
    )


def click_texto_js(page, texto, exato=True):
    """Clica por JS no 1o elemento (span/div/a) cujo texto == `texto` (bypassa viewport)."""
    return page.evaluate(
        """([t,ex])=>{
            const els=Array.from(document.querySelectorAll('span,div,a,button,li'));
            const el=els.find(e=>{const x=(e.innerText||'').trim();return ex?x===t:x.includes(t);});
            if(!el)return false; el.scrollIntoView({block:'center'});
            (el.closest('a,button,li,[role=menuitem]')||el).click(); return true;}""",
        [texto, exato],
    )


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p, height=1300)

    tw.login(page, c)  # loga + switch admin (org principal)
    print("[1] pos-login:", page.url)
    tw.snap(page, PASTA, "01-pos-login")

    # Trocar para o perfil de usuario/lider (a aba "Avaliacoes a preencher" so existe la)
    print("   abriu dropdown perfil:", click_texto_js(page, "Administrador", exato=False))
    page.wait_for_timeout(1500)
    tw.snap(page, PASTA, "01b-dropdown-perfil")
    # opcoes tipicas: "Estudante" / "Aluno" / "Usuario"
    for op in ["Estudante", "Aluno", "Usuário", "Líder", "Lider", "Colaborador"]:
        if click_texto_js(page, op, exato=True):
            print("   trocou perfil para:", op)
            break
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    print("[1c] pos-troca-perfil:", page.url)
    tw.snap(page, PASTA, "01c-perfil-usuario")

    # Expandir "Gestao de Time (BETA)" pra revelar o sub-item "Desenvolvimento"
    print("   expandiu Gestao de Time:", click_texto_js(page, "Gestão de Time", exato=False))
    page.wait_for_timeout(1500)
    print("   clicou Desenvolvimento:", click_texto_js(page, "Desenvolvimento", exato=True))
    page.wait_for_timeout(4000)
    tw.dispensar_nps(page)
    print("[2] desenvolvimento:", page.url)
    tw.snap(page, PASTA, "02-desenvolvimento")

    # Aba "Avaliacoes a preencher"
    print("   clicou aba Avaliacoes a preencher:", click_texto_js(page, "Avaliações a preencher", exato=False))
    page.wait_for_timeout(2500)
    tw.snap(page, PASTA, "03-aba-avaliacoes-preencher")

    # Abrir o painel de filtros (icone de filtro no topo da tabela)
    aberto = False
    for sel in [
        "button:has-text('Filtro')", "[aria-label*='iltro']",
        "button:has([data-icon='filter'])", "i:has-text('filter_list')",
        "[class*='filter']",
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                loc.click(timeout=4000)
                page.wait_for_timeout(2000)
                if page.get_by_text("Lista de filtros", exact=False).count():
                    aberto = True
                    break
        except Exception:
            pass
    if not aberto:
        # fallback: clicar qualquer icone material 'filter_list'
        try:
            page.get_by_text("filter_list", exact=False).first.click(timeout=4000)
            page.wait_for_timeout(2000)
            aberto = page.get_by_text("Lista de filtros", exact=False).count() > 0
        except Exception:
            pass
    print("[3] painel de filtros aberto:", aberto)
    tw.snap(page, PASTA, "04-lista-de-filtros")

    filtros = listar_filtros_padrao(page)
    print("[4] radios/labels no painel:", filtros)

    # texto bruto do painel pra conferir 'Filtros padrao'
    try:
        painel = page.get_by_text("Filtros padrão", exact=False).first
        print("[5] painel visivel:", painel.is_visible() if painel.count() else False)
    except Exception:
        pass

    tw.snap(page, PASTA, "05-final", full=True)
    ctx.close()
    browser.close()
print("OK")
