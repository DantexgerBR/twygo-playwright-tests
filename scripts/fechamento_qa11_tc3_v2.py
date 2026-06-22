"""fechamento_qa11_tc3_v2.py — Fecha TC3 (empty state) da QA 1.1.

Fluxo:
1. Admin loga na org 37079 (registrosf2) com ADMIN_PASSWORD do .env
2. Abre kebab do usuario QA11TC3 e clica "Alterar senha" -> define twygoqa2026
3. Nova sessao: loga como qa11tc342588@twygotest.com / twygoqa2026
4. Acessa /records e valida empty state

Autorizacao explícita do dono: Dante de Oliveira Tavares (2026-06-22)
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ORG_ID = "37079"
TC3_EMAIL = "qa11tc342588@twygotest.com"
TC3_NOVA_SENHA = "twygoqa2026"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa11"
EVID.mkdir(parents=True, exist_ok=True)

PASSOU = []
FALHOU = []
BLOQUEIO = None


def log(msg):
    print(msg, flush=True)


def check(cond, label):
    if cond:
        PASSOU.append(label)
        log(f"  OK  {label}")
    else:
        FALHOU.append(label)
        log(f"  FAIL {label}")
    return cond


def admin_alterar_senha(page):
    """Admin altera senha do usuario QA11TC3 via kebab > Alterar senha."""
    global BLOQUEIO

    log("\n[ADMIN] Navegando para lista de usuarios...")
    page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    log(f"  URL: {page.url[:80]}")

    # Valida que chegou na pagina de usuarios (nao redirecionou pra login)
    if "/users" not in page.url:
        BLOQUEIO = f"Acesso negado a /users. URL atual: {page.url}"
        tw.snap(page, EVID, "tc3_v2_admin_bloqueado")
        return False

    # Pesquisa especificamente pelo email do usuario alvo
    try:
        busca = page.locator("input[placeholder='Pesquise aqui'], input[id*='search'], input[name*='search']").first
        if busca.count() > 0 and busca.is_visible(timeout=3000):
            busca.fill("qa11tc342588")
            page.wait_for_timeout(1500)
            log("  Pesquisado: qa11tc342588")
    except Exception as e:
        log(f"  Busca erro: {e}")

    tw.snap(page, EVID, "tc3_v2_lista_usuarios")

    # Localiza linha especifica do usuario qa11tc342588@twygotest.com
    row = page.locator("tr").filter(has_text="qa11tc342588@twygotest.com").first
    if row.count() == 0:
        # Fallback: usuario-situation-toggle do id 4298402 (id conhecido do usuario)
        toggle = page.locator("#user-situation-toggle-4298402")
        if toggle.count() > 0:
            row = toggle.locator("xpath=ancestor::tr").first
    if row.count() == 0:
        BLOQUEIO = "Linha do usuario qa11tc342588@twygotest.com nao encontrada"
        tw.snap(page, EVID, "tc3_v2_usuario_nao_encontrado")
        return False

    log("  Linha do usuario encontrada")
    row_text = ""
    try:
        row_text = row.inner_text()[:100]
        log(f"  Texto da linha: {row_text!r}")
    except Exception:
        pass

    # Captura erros de console e requisicoes de rede para diagnostico
    console_erros = []
    reqs_capturadas = []
    page.on("console", lambda msg: console_erros.append(f"{msg.type}: {msg.text[:200]}") if msg.type in ("error", "warning") else None)
    page.on("pageerror", lambda err: console_erros.append(f"PAGEERROR: {str(err)[:200]}"))
    page.on("request", lambda req: reqs_capturadas.append(f"{req.method} {req.url[:120]}") if req.method in ("POST", "PUT", "PATCH", "DELETE") else None)

    # DIAGNOSTICO: quantos menus passam o filtro de visibilidade?
    menus_visiveis_count = page.evaluate(
        "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
        "const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
    )
    log(f"  Menus visiveis antes do kebab: {menus_visiveis_count}")

    # Abre o kebab via click no ultimo botao da linha
    botoes = row.locator("button").all()
    log(f"  Botoes na linha: {len(botoes)}")
    if not botoes:
        BLOQUEIO = "Nenhum botao na linha do usuario (kebab ausente)"
        return False

    kebab = botoes[-1]
    kebab.scroll_into_view_if_needed()
    kebab.click(force=True)
    page.wait_for_timeout(1200)
    tw.snap(page, EVID, "tc3_v2_kebab_aberto")

    # DIAGNOSTICO: quantos menus visiveis apos abrir o kebab?
    menus_apos_kebab = page.evaluate(
        "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
        "const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
    )
    log(f"  Menus visiveis apos kebab: {menus_apos_kebab}")

    # DIAGNOSTICO: elemento topmost nas coordenadas onde vamos clicar
    id_alterar = page.evaluate(
        "(pal)=>{const ms=Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
        "const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;});"
        "const m=ms[ms.length-1];if(!m)return 'SEM MENU VISIVEL';"
        "const it=Array.from(m.querySelectorAll('[role=menuitem]'))"
        ".find(e=>new RegExp(pal,'i').test(e.innerText||''));return it?it.id:'SEM ITEM';}",
        "Alterar senha"
    )
    log(f"  ID do menuitem 'Alterar senha': {id_alterar!r}")

    if id_alterar and id_alterar not in ("SEM MENU VISIVEL", "SEM ITEM"):
        item_loc = page.locator(f'[id="{id_alterar}"]')
        bbox = item_loc.bounding_box()
        if bbox:
            cx = bbox["x"] + bbox["width"] / 2
            cy = bbox["y"] + bbox["height"] / 2
            # DIAGNOSTICO: elemento topmost nessa posicao
            topmost = page.evaluate(f"document.elementFromPoint({cx:.0f}, {cy:.0f})?.outerHTML?.slice(0, 200) || 'null'")
            log(f"  Elemento topmost em ({cx:.0f}, {cy:.0f}): {topmost}")

    # Usa click_menuitem do _twygo
    itens_visiveis = tw.menu_visivel(page)
    log(f"  Itens no menu visivel: {itens_visiveis}")

    ok_click = tw.click_menuitem(page, r"Alterar senha")
    log(f"  click_menuitem('Alterar senha'): {ok_click}")
    if not ok_click:
        BLOQUEIO = "click_menuitem nao encontrou 'Alterar senha' no menu visivel"
        tw.snap(page, EVID, "tc3_v2_kebab_sem_alterar_senha")
        return False

    page.wait_for_timeout(1000)
    menus_apos_click_v1 = page.evaluate(
        "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
        "const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
    )
    log(f"  Menus visiveis apos click_menuitem (1s): {menus_apos_click_v1}")

    # Se o menu ainda esta aberto, o click nao funcionou — tenta via React fiber
    if menus_apos_click_v1 > 0:
        log("  Menu ainda aberto — tentando via React fiber onClick...")
        resultado_fiber = page.evaluate(f"""(rid) => {{
            const el = document.getElementById(rid);
            if (!el) return 'elemento nao encontrado';
            // Encontra a fiber key do React
            const fiberKey = Object.keys(el).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
            if (!fiberKey) return 'sem fiber key: ' + Object.keys(el).filter(k=>k.startsWith('__')).join(',');
            let fiber = el[fiberKey];
            // Sobe ate encontrar onClick nas props
            while (fiber) {{
                const props = fiber.memoizedProps || fiber.pendingProps || {{}};
                if (props.onClick) {{
                    props.onClick({{
                        preventDefault: () => {{}},
                        stopPropagation: () => {{}},
                        target: el,
                        currentTarget: el,
                        nativeEvent: {{}}
                    }});
                    return 'ok - onClick chamado via fiber';
                }}
                fiber = fiber.return;
                if (!fiber || fiber.depth > 20) break;
            }}
            return 'onClick nao encontrado na fiber chain';
        }}""", id_alterar)
        log(f"  React fiber resultado: {resultado_fiber}")
        page.wait_for_timeout(2000)

    # Log de erros de console e reqs
    if console_erros:
        log(f"  Erros de console ({len(console_erros)}):")
        for e in console_erros[:10]:
            log(f"    {e}")
    if reqs_capturadas:
        log(f"  Requisicoes POST/PUT capturadas ({len(reqs_capturadas)}):")
        for r in reqs_capturadas[:10]:
            log(f"    {r}")

    menus_apos_click_imediato = page.evaluate(
        "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
        "const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
    )
    log(f"  Menus visiveis final: {menus_apos_click_imediato}")
    tw.snap(page, EVID, "tc3_v2_apos_click_alterar_senha")

    page.wait_for_timeout(1000)

    # Verifica DOM apos clique
    modal_info = page.evaluate("""() => {
        const candidates = [
            ...document.querySelectorAll('[class*="chakra-modal__content"]'),
            ...document.querySelectorAll('[data-focus-lock-disabled="false"]'),
            ...document.querySelectorAll('[aria-modal="true"]'),
            ...document.querySelectorAll('input[type="password"]')
        ];
        const visible = candidates.filter(el => {
            const s = getComputedStyle(el);
            return s.display !== 'none' && s.visibility !== 'hidden' && parseFloat(s.opacity) > 0.1;
        });
        return visible.map(el => ({
            tag: el.tagName,
            id: el.id,
            classes: el.className.slice(0, 80),
            textContent: el.textContent.slice(0, 100)
        }));
    }""")
    log(f"  Elementos modais/password visiveis: {len(modal_info)}")
    for m in modal_info:
        log(f"    {m['tag']} id={m['id']!r} {m['classes'][:50]!r}: {m['textContent'][:60]!r}")

    # Numero de menus depois do clique
    menus_apos_click = page.evaluate(
        "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
        "const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
    )
    log(f"  Menus visiveis apos click_menuitem: {menus_apos_click}")

    # PLAN B: Editar usuario — forma alternativa de definir senha
    # O form de Editar usuario pode ter campo de senha
    log("\n  [PLAN B] Tentando via Editar usuario...")
    try:
        # Reabre o kebab
        kebab.scroll_into_view_if_needed()
        kebab.click(force=True)
        page.wait_for_timeout(1200)

        menus_planb = page.evaluate(
            "Array.from(document.querySelectorAll('[role=menu]')).filter(m=>{"
            "const c=getComputedStyle(m);return c.visibility==='visible'&&parseFloat(c.opacity)>0.5;}).length"
        )
        log(f"  [PLAN B] Menus visiveis para Editar: {menus_planb}")

        ok_editar = tw.click_menuitem(page, r"Editar")
        log(f"  [PLAN B] click_menuitem('Editar'): {ok_editar}")
        page.wait_for_timeout(2000)
        tw.snap(page, EVID, "tc3_v2_planb_editar")

        # Verifica se abriu a pagina de editar ou um modal
        log(f"  [PLAN B] URL apos Editar: {page.url[:80]}")

        # Busca campo de senha no form de editar
        campos_senha = page.locator("input[type='password'], input[id*='password'], input[name*='password']").all()
        log(f"  [PLAN B] Campos de senha encontrados: {len(campos_senha)}")
        for c in campos_senha:
            try:
                if c.is_visible(timeout=500):
                    log(f"    visivel: type={c.get_attribute('type')!r} id={c.get_attribute('id')!r}")
            except Exception:
                pass
    except Exception as e:
        log(f"  [PLAN B] Erro: {e}")

    tw.snap(page, EVID, "tc3_v2_modal_alterar_senha")

    # Tenta preencher senha via input[type=password]
    preencheu = False
    try:
        campo_pw = page.locator("input[type='password']").first
        if campo_pw.count() > 0 and campo_pw.is_visible(timeout=3000):
            campo_pw.fill(TC3_NOVA_SENHA)
            preencheu = True
            log("  Senha preenchida via input[type=password]")
    except Exception as e:
        log(f"  Erro input[type=password]: {e}")

    if not preencheu:
        BLOQUEIO = "Nem 'Alterar senha' nem 'Editar' abriram campo de senha acessivel"
        return False

    tw.snap(page, EVID, "tc3_v2_senha_preenchida")

    # Clica em Salvar/Confirmar
    try:
        btn = page.locator("button[type='submit'], button").filter(
            has_text=re.compile(r"Salvar|Confirmar|Alterar|OK", re.I)
        ).last
        btn.click()
        page.wait_for_timeout(2000)
        log("  Botao salvar clicado")
    except Exception as e:
        log(f"  Erro ao clicar salvar: {e}")

    tw.snap(page, EVID, "fechamento_tc3_senha_definida")
    log("  Screenshot 'fechamento_tc3_senha_definida.png' capturado")
    return True


def run_tc3(page):
    """Loga como QA11TC3 e valida empty state."""
    global BLOQUEIO

    log("\n[TC3] Login como usuario sem registros...")
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("#user_email", timeout=15000)
    page.fill("#user_email", TC3_EMAIL)
    page.fill("#user_password", TC3_NOVA_SENHA)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    log(f"  URL pos-login: {page.url[:80]}")
    tw.snap(page, EVID, "tc3_v2_pos_login_aluno")

    # Verifica se login funcionou (nao ficou na pagina de login)
    if "/login" in page.url:
        # Captura mensagem de erro
        try:
            erro = page.locator("[class*='error'], [class*='alert'], [class*='flash'], .notice").first
            msg_erro = erro.inner_text() if erro.count() > 0 else "Sem mensagem de erro visivel"
        except Exception:
            msg_erro = "Nao foi possivel capturar mensagem de erro"
        BLOQUEIO = f"Login falhou para {TC3_EMAIL}. Mensagem: {msg_erro[:200]}"
        tw.snap(page, EVID, "tc3_v2_login_falhou")
        return

    log("  Login bem-sucedido")

    # Navega para Meu Historico
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true",
        wait_until="domcontentloaded", timeout=60000
    )
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    log(f"  URL Meu Historico: {page.url[:80]}")
    tw.snap(page, EVID, "tc3_v2_meu_historico")

    # PASSO 1: Mensagem de empty state
    msg_esperada = "Você ainda não tem registros. Adicione o primeiro pelo botão acima."
    msg_encontrada = False

    # Tenta localizar a mensagem exata
    try:
        loc_exato = page.locator(f"text={msg_esperada}").first
        msg_encontrada = loc_exato.is_visible(timeout=5000)
    except Exception:
        pass

    # Variacao sem pontuacao final / parcial
    if not msg_encontrada:
        try:
            loc_parcial = page.locator("text=Você ainda não tem registros").first
            msg_encontrada = loc_parcial.is_visible(timeout=2000)
            if msg_encontrada:
                log("  Mensagem encontrada (variacao parcial)")
        except Exception:
            pass

    # Log texto da pagina para debug
    if not msg_encontrada:
        try:
            corpo = page.locator("main, [class*='container'], [class*='content'], body").first
            texto_pagina = corpo.inner_text()[:600]
            log(f"  Texto pagina:\n{texto_pagina}")
        except Exception:
            pass

    check(msg_encontrada, "mensagem_empty_state_visivel")

    # PASSO 2: 4 KPI cards com valor 0
    tw.snap(page, EVID, "tc3_v2_kpis")
    kpi_labels = ["Emitidos", "Expirados", "Pendentes", "Recusados"]
    kpis_ok = 0
    for label in kpi_labels:
        try:
            # Localiza o card pelo label e sobe 2 niveis para achar o valor "0"
            container = page.locator(f"text={label}").locator("..").locator("..").first
            if container.count() == 0:
                container = page.locator(f"text={label}").locator("..").first
            texto = container.inner_text()
            tem_zero = "0" in texto
            log(f"  KPI {label!r}: {texto[:60].strip()!r} => zero={tem_zero}")
            if tem_zero:
                kpis_ok += 1
        except Exception as e:
            log(f"  KPI {label!r}: erro={e}")

    check(kpis_ok == 4, f"4_kpis_todos_zero ({kpis_ok}/4)")

    tw.snap(page, EVID, "fechamento_tc3_empty_ok")
    log("  Screenshot 'fechamento_tc3_empty_ok.png' capturado")


def main():
    log("=" * 60)
    log("fechamento_qa11_tc3_v2.py — TC3 empty state")
    log("=" * 60)

    global BLOQUEIO

    # Credenciais admin para org 37079 (registrosf2) — senha desta org e 123456
    admin_email = "dante.tavares@twygo.com"
    admin_senha = "123456"
    log(f"Admin email: {admin_email}")
    log(f"Admin org: {ORG_ID}")

    # SESSAO 1: Admin altera senha do QA11TC3
    log("\n--- SESSAO 1: Admin ---")
    ok_alterar = False
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            # Login admin
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("#user_email", timeout=15000)
            page.fill("#user_email", admin_email)
            page.fill("#user_password", admin_senha)
            page.click("#user_submit")
            try:
                page.wait_for_load_state("networkidle", timeout=25000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)
            log(f"  Pos-login: {page.url[:60]}")

            # Switch para admin na org 37079
            page.goto(
                f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
                wait_until="domcontentloaded", timeout=60000
            )
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
            tw.dispensar_nps(page)
            log(f"  Admin switch: {page.url[:60]}")
            tw.snap(page, EVID, "tc3_v2_admin_logado")

            # Aceita qualquer URL que nao seja o login page — o switch pode redirecionar
            # para /events ou para /dashboard_students mas ainda com sessao admin
            if "/login" in page.url:
                BLOQUEIO = f"Login admin falhou (credencial invalida). URL: {page.url}"
            else:
                ok_alterar = admin_alterar_senha(page)
        finally:
            ctx.close()
            browser.close()

    if BLOQUEIO:
        log(f"\nBLOQUEIO detectado: {BLOQUEIO}")
        log("TC3: BLOQUEADO")
        return

    if not ok_alterar:
        log("\nFalha ao alterar senha — abortando sessao 2")
        log("TC3: BLOQUEADO")
        return

    # SESSAO 2: Login como QA11TC3 e valida empty state
    log("\n--- SESSAO 2: Usuario QA11TC3 ---")
    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)
        try:
            run_tc3(page)
        finally:
            ctx.close()
            browser.close()

    # Resultado final
    log("\n" + "=" * 60)
    log("RESULTADO TC3:")
    if BLOQUEIO:
        log(f"  BLOQUEADO: {BLOQUEIO}")
        log("TC3: BLOQUEADO")
    elif not FALHOU:
        log(f"  PASSOU: {len(PASSOU)} checks")
        log("TC3: PASSOU")
    else:
        log(f"  PASSOU: {len(PASSOU)} checks")
        log(f"  FALHOU: {len(FALHOU)} checks")
        for f in FALHOU:
            log(f"    - {f}")
        log("TC3: FALHOU")
    log("=" * 60)


if __name__ == "__main__":
    main()
