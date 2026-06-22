"""fechamento_qa11_pontos_finais.py — Fecha TC11 (pag2) e TC3 (empty state).

Focado nos 2 pontos inconclusivos da run anterior:
  - TC11: navegar pag1 -> pag2 (widget de chat suprimido via JS antes de clicar)
  - TC3:  criar usuario novo com todos os campos + listener HTTP para diagnosticar falha
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ADMIN_EMAIL = "dante.tavares@twygo.com"
ADMIN_SENHA = "123456"
ORG_ID = "37079"

SLUG = "registros-f2-qa11"
EVID = tw.ROOT / "evidencias" / SLUG
EVID.mkdir(parents=True, exist_ok=True)

RESULTADOS = {}


def log(msg):
    print(msg, flush=True)


def passou(tc_id, evidencias, obs=""):
    RESULTADOS[tc_id] = {"veredito": "PASSOU", "evidencias": evidencias, "obs": obs}
    log(f"  [TC{tc_id}] PASSOU{' — ' + obs if obs else ''}")


def falhou(tc_id, evidencias, motivo):
    RESULTADOS[tc_id] = {"veredito": "FALHOU", "evidencias": evidencias, "obs": motivo}
    log(f"  [TC{tc_id}] FALHOU — {motivo}")


def bloqueado(tc_id, evidencias, motivo):
    RESULTADOS[tc_id] = {"veredito": "BLOQUEADO", "evidencias": evidencias, "obs": motivo}
    log(f"  [TC{tc_id}] BLOQUEADO — {motivo}")


# ─── Login helpers ─────────────────────────────────────────────────────────────

def login_aluno(page):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", ADMIN_EMAIL)
    page.fill("#user_password", ADMIN_SENHA)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    if "/users/login" in page.url or "/login" in page.url:
        raise SystemExit("Login Aluno falhou — sessao caiu.")
    log(f"  Aluno logado: {page.url[:70]}")


def login_admin(page):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("#user_email", timeout=10000)
    page.fill("#user_email", ADMIN_EMAIL)
    page.fill("#user_password", ADMIN_SENHA)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    # Switch admin obrigatorio
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/events?tab=events&profile=admin",
        wait_until="domcontentloaded", timeout=60000,
    )
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    # Verificacao: se foi redirecionar para login, admin nao e desta org
    if "/users/login" in page.url or "/login" in page.url:
        raise SystemExit("Switch admin falhou — credencial pode nao ser dessa org.")
    log(f"  Admin logado: {page.url[:70]}")


def fechar_modal_confirmacao(page):
    """Fecha modal de confirmacao 'Continuar mesmo assim' ou 'OK' que aparece ao navegar."""
    for _ in range(3):
        fechou = False
        # Botao "OK" do modal confirm_go_to_administration
        for btn_id in [
            "confirm-modal-confirm_go_to_administration-cancel",
            "confirm-modal-confirm_go_to_administration-confirmed",
        ]:
            loc = page.locator(f"#{btn_id}").first
            if loc.count() > 0:
                try:
                    if loc.is_visible(timeout=1500):
                        loc.click(timeout=3000)
                        page.wait_for_timeout(1000)
                        fechou = True
                        log(f"  Modal confirmacao fechado via #{btn_id}")
                        break
                except Exception:
                    pass
        # Tambem tenta fechar qualquer modal generico
        tw.dispensar_nps(page)
        if not fechou:
            break


def ir_meu_historico(page):
    url = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2500)
    fechar_modal_confirmacao(page)
    tw.dispensar_nps(page)


# ─── Suprimir widget de chat (Sophia/Twygo) via JS ─────────────────────────────

def suprimir_chat_widget(page):
    """Remove/esconde o widget de chat do rodape para liberar cliques na paginacao."""
    resultado = page.evaluate("""() => {
        const seletores = [
            'iframe[src*="chat"]',
            'iframe[src*="sophia"]',
            'iframe[title*="Chat"]',
            'iframe[title*="chat"]',
            '[id*="chat-widget"]',
            '[class*="chat-widget"]',
            '[id*="sophia"]',
            '[class*="sophia"]',
            '[id*="intercom"]',
            '[class*="intercom"]',
            '[id*="crisp"]',
            '[class*="crisp"]',
            '[id*="hubspot"]',
            '[class*="hs-messages"]',
            '[data-testid*="chat"]',
        ];
        let removidos = 0;
        for (const sel of seletores) {
            document.querySelectorAll(sel).forEach(el => {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
                el.style.pointerEvents = 'none';
                removidos++;
            });
        }
        return removidos;
    }""")
    log(f"  Chat widget: {resultado} elemento(s) suprimido(s)")
    return resultado


# ─── TC11: Navegar para pagina 2 ───────────────────────────────────────────────

def run_tc11(page):
    log("\n=== TC11: Navegacao para pagina 2 ===")
    evids = []

    ir_meu_historico(page)
    rows_p1 = page.locator("table tbody tr").count()
    log(f"  Linhas vissiveis na pag 1: {rows_p1}")

    if rows_p1 < 25:
        falhou(11, evids,
               f"apenas {rows_p1} linha(s) na pag1 — precisa >= 26 registros para testar paginacao")
        return

    # Fecha modal de confirmacao que pode estar sobreposto antes de qualquer interacao
    fechar_modal_confirmacao(page)
    page.wait_for_timeout(500)

    # Rola ate o rodape e suprime widget de chat
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1500)
    suprimir_chat_widget(page)
    fechar_modal_confirmacao(page)
    page.wait_for_timeout(500)

    tw.snap(page, EVID, "fechamento_tc11_rodape")
    evids.append("fechamento_tc11_rodape.png")
    log("  Screenshot do rodape tirado.")

    # Garante 25/pagina antes de testar pag2
    log("  Garantindo 25 por pagina...")
    set25_ok = page.evaluate("""() => {
        const selects = Array.from(document.querySelectorAll('select'));
        for (const s of selects) {
            const opts = Array.from(s.options).map(o => o.value);
            if (opts.some(v => v === '25' || v === '50' || v === '100')) {
                if (s.value !== '25') {
                    s.value = '25';
                    s.dispatchEvent(new Event('change', {bubbles: true}));
                    return 'set';
                }
                return 'already25';
            }
        }
        return 'no_select';
    }""")
    log(f"  Select 25/pag: {set25_ok}")
    if set25_ok == "set":
        page.wait_for_timeout(2000)
        rows_p1 = page.locator("table tbody tr").count()
        log(f"  Linhas apos set 25: {rows_p1}")

    # Dump do DOM de TODOS os botoes (incluindo paginacao) — agora sem modal sobreposto
    dom_dump = page.evaluate("""() => {
        const candidates = [];
        // Todos os botoes visiveis da pagina
        document.querySelectorAll('button, a[role="button"]').forEach(el => {
            const rect = el.getBoundingClientRect();
            // Inclui botoes na metade inferior da tela (onde fica a paginacao)
            if (rect.bottom > window.innerHeight * 0.5 || rect.top > 600) {
                candidates.push({
                    tag: el.tagName,
                    text: el.innerText.trim().slice(0, 30),
                    aria: el.getAttribute('aria-label'),
                    cls: el.className.slice(0, 80),
                    disabled: el.disabled || el.getAttribute('aria-disabled') === 'true',
                    id: el.id,
                    top: Math.round(rect.top),
                    left: Math.round(rect.left),
                });
            }
        });
        return candidates;
    }""")
    log(f"  Botoes na metade inferior da pagina ({len(dom_dump)}):")
    for item in dom_dump:
        log(f"    {item}")

    # Identifica botao "proxima pagina" com varios criterios
    pag_next = None

    # Estrategia 1: IDs conhecidos (revelados pelo dump do DOM real)
    for id_str in ["#next-page-button", "#page-button-2"]:
        loc = page.locator(id_str).first
        if loc.count() > 0:
            try:
                if loc.is_visible(timeout=1500):
                    if not loc.is_disabled():
                        pag_next = loc
                        log(f"  Next encontrado via ID: {id_str}")
                        break
                    else:
                        log(f"  {id_str} encontrado mas desabilitado")
            except Exception:
                pass

    # Estrategia 2: aria-label
    if pag_next is None:
        for loc_str in [
            "[aria-label*='Próxima' i]",
            "[aria-label*='next' i]",
            "[aria-label*='seguinte' i]",
        ]:
            loc = page.locator(loc_str).first
            if loc.count() > 0:
                try:
                    if loc.is_visible(timeout=1500):
                        pag_next = loc
                        log(f"  Next encontrado via aria: {loc_str}")
                        break
                except Exception:
                    pass

    # Estrategia 3: texto do botao — incluindo icone material 'chevron_right'
    if pag_next is None:
        for txt in ["chevron_right", ">", "›", "→", "»"]:
            locs = page.get_by_role("button", name=re.compile(f"^{re.escape(txt)}$")).all()
            for loc in locs:
                try:
                    if loc.is_visible(timeout=1000) and not loc.is_disabled():
                        pag_next = loc
                        log(f"  Next encontrado via texto: '{txt}'")
                        break
                except Exception:
                    pass
            if pag_next:
                break

    # Estrategia 4: busca no dump por candidato nao-desabilitado
    if pag_next is None:
        for item in dom_dump:
            if item.get("disabled"):
                continue
            txt = item.get("text", "")
            aria = item.get("aria", "") or ""
            item_id = item.get("id", "")
            if (txt in ["chevron_right", ">", "›", "→", "»"]
                    or "next" in aria.lower() or "next" in item_id.lower()
                    or "prox" in aria.lower()):
                log(f"  Candidato via dump: {item}")
                if item_id:
                    loc = page.locator(f"#{item_id}").first
                elif aria:
                    loc = page.locator(f"[aria-label='{aria}']").first
                else:
                    loc = page.get_by_role("button", name=txt).first
                if loc.count() > 0:
                    try:
                        if loc.is_visible(timeout=1500) and not loc.is_disabled():
                            pag_next = loc
                            break
                    except Exception:
                        pass

    if pag_next is None:
        log("  AVISO: nao conseguiu localizar o botao 'proxima pagina' pelos seletores padrao.")
        log("  Tentando via JS click direto...")
        clicou_js = page.evaluate("""() => {
            // Tenta todos os navs em busca do botao de proxima pagina
            const navs = Array.from(document.querySelectorAll('nav, [class*="paginate"], [class*="Paginate"], [class*="pagination"], [class*="Pagination"]'));
            for (const nav of navs) {
                const btns = Array.from(nav.querySelectorAll('button')).filter(
                    b => !b.disabled && b.getAttribute('aria-disabled') !== 'true'
                );
                for (const b of btns) {
                    const t = b.innerText.trim();
                    const al = (b.getAttribute('aria-label') || '').toLowerCase();
                    if (t === '>' || t === '›' || t === '→' || al.includes('next') || al.includes('próxima') || al.includes('proxima')) {
                        b.scrollIntoView({block:'center'});
                        b.click();
                        return {clicked: true, text: t, aria: al};
                    }
                }
            }
            // Fallback: percorre todos os botoes do body
            const allBtns = Array.from(document.querySelectorAll('button')).filter(
                b => !b.disabled && b.getAttribute('aria-disabled') !== 'true'
            );
            for (const b of allBtns) {
                const t = b.innerText.trim();
                const al = (b.getAttribute('aria-label') || '').toLowerCase();
                if (t === '>' || t === '›' || t === '→' || al.includes('next') || al.includes('próxima') || al.includes('proxima')) {
                    b.scrollIntoView({block:'center'});
                    b.click();
                    return {clicked: true, text: t, aria: al};
                }
            }
            return {clicked: false};
        }""")
        log(f"  JS click resultado: {clicou_js}")
        if clicou_js and clicou_js.get("clicked"):
            page.wait_for_timeout(2500)
            rows_p2 = page.locator("table tbody tr").count()
            log(f"  Pag 2 (via JS): {rows_p2} linha(s)")
            tw.snap(page, EVID, "fechamento_tc11_pag2")
            evids.append("fechamento_tc11_pag2.png")
            if rows_p2 > 0 and rows_p2 < rows_p1:
                passou(11, evids, f"pag2 via JS: {rows_p2} linha(s) restante(s)")
            elif rows_p2 > 0:
                # Pode ser que ainda esta na pag1 (mesmo numero de linhas) — verifica URL/estado
                log(f"  AVISO: pag2 tem {rows_p2} linhas (igual pag1={rows_p1}) — pode nao ter mudado")
                # Tira screenshot e assume passou se havia mais de 25 registros
                tw.snap(page, EVID, "fechamento_tc11_pag2_check")
                evids.append("fechamento_tc11_pag2_check.png")
                # Verifica se ha indicador de pagina ativa
                pag_ativa = page.evaluate("""() => {
                    const navs = document.querySelectorAll('nav, [class*="paginate"], [class*="pagination"]');
                    for (const nav of navs) {
                        const ativo = nav.querySelector('[aria-current="page"], .active, [class*="active"]');
                        if (ativo) return ativo.innerText.trim();
                    }
                    return null;
                }""")
                log(f"  Pagina ativa indicada: {pag_ativa}")
                if pag_ativa == "2":
                    passou(11, evids, f"pag2 confirmada (aria-current=page=2); {rows_p2} linha(s)")
                else:
                    falhou(11, evids,
                           f"apos click JS, pag2 tem {rows_p2} linhas (igual pag1) — paginacao pode nao ter mudado; pagina_ativa={pag_ativa}")
            else:
                falhou(11, evids, "pag2 retornou 0 linhas apos click JS")
        else:
            # Nao conseguiu nem localizar o controle
            tw.snap(page, EVID, "fechamento_tc11_controle_nao_localizado")
            evids.append("fechamento_tc11_controle_nao_localizado.png")
            bloqueado(11, evids,
                      "controle de proxima pagina nao localizado — widget chat suprimido mas botao > nao encontrado no DOM")
        return

    # Clica no botao localizado por seletor
    log("  Clicando no botao de proxima pagina...")
    try:
        pag_next.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        suprimir_chat_widget(page)  # suprime novamente apos scroll
        page.wait_for_timeout(300)
        pag_next.click(timeout=5000)
        page.wait_for_timeout(2500)
        rows_p2 = page.locator("table tbody tr").count()
        log(f"  Pag 2: {rows_p2} linha(s)")
        tw.snap(page, EVID, "fechamento_tc11_pag2")
        evids.append("fechamento_tc11_pag2.png")
        if rows_p2 > 0 and rows_p2 < rows_p1:
            passou(11, evids, f"pag2 carregou com {rows_p2} linha(s) restante(s)")
        elif rows_p2 > 0:
            pag_ativa = page.evaluate("""() => {
                const navs = document.querySelectorAll('nav, [class*="paginate"], [class*="pagination"]');
                for (const nav of navs) {
                    const ativo = nav.querySelector('[aria-current="page"], .active, [class*="active"]');
                    if (ativo) return ativo.innerText.trim();
                }
                return null;
            }""")
            log(f"  Pagina ativa: {pag_ativa}")
            if pag_ativa == "2":
                passou(11, evids, f"pag2 (aria-current=2); {rows_p2} linha(s)")
            else:
                falhou(11, evids, f"pag2 tem {rows_p2} linhas (igual pag1={rows_p1}); pagina_ativa={pag_ativa}")
        else:
            falhou(11, evids, "pag2 retornou 0 linhas")
    except Exception as e:
        log(f"  Erro ao clicar next: {e}")
        tw.snap(page, EVID, "fechamento_tc11_erro_click")
        evids.append("fechamento_tc11_erro_click.png")
        falhou(11, evids, f"excecao ao clicar: {e}")


# ─── TC3: Usuario novo + empty state ───────────────────────────────────────────

def run_tc3(browser, page_admin):
    log("\n=== TC3: Criar usuario novo + empty state ===")
    evids = []
    novo_email = f"qa11tc3{os.getpid()}@twygotest.com"
    novo_senha = "123456"

    log(f"  Novo usuario: {novo_email}")

    # Navega para o form de criacao de usuario
    page_admin.goto(
        f"{BASE_URL}/o/{ORG_ID}/users/new",
        wait_until="domcontentloaded", timeout=30000,
    )
    try:
        page_admin.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page_admin.wait_for_timeout(2000)
    tw.dispensar_nps(page_admin)

    # Verifica se chegou no form (nao em 403)
    if "/users/login" in page_admin.url or "/login" in page_admin.url:
        bloqueado(3, evids, "admin nao autenticado — redirecionado para login ao acessar /users/new")
        return
    if "403" in page_admin.url or "forbidden" in page_admin.url.lower():
        bloqueado(3, evids, f"403 ao acessar /users/new — admin pode nao ter permissao nesta org")
        return

    log(f"  URL do form: {page_admin.url[:80]}")
    tw.snap(page_admin, EVID, "fechamento_tc3_form_novo_usuario")
    evids.append("fechamento_tc3_form_novo_usuario.png")

    # Inspeciona o DOM do form: campos obrigatorios, tipo, selects
    campos_dom = page_admin.evaluate("""() => {
        const inputs = Array.from(document.querySelectorAll('input, select, textarea'));
        return inputs.map(el => ({
            tag: el.tagName,
            type: el.type || null,
            id: el.id || null,
            name: el.name || null,
            placeholder: el.placeholder || null,
            required: el.required,
            value: el.value ? el.value.slice(0,30) : '',
        }));
    }""")
    log(f"  Campos no form ({len(campos_dom)}):")
    for c in campos_dom:
        log(f"    {c}")

    tem_senha = any(c.get("type") == "password" for c in campos_dom)
    log(f"  Tem campo senha: {tem_senha}")

    # Captura resposta HTTP do submit para diagnostico
    response_data = {}

    def capturar_resposta(response):
        url = response.url
        if "/users" in url and response.request.method in ("POST", "PUT", "PATCH"):
            try:
                body = response.text()
                response_data["status"] = response.status
                response_data["url"] = url
                response_data["body"] = body[:500]
                log(f"  HTTP {response.status} POST {url[:60]}")
                if response.status >= 400:
                    log(f"  Response body: {body[:300]}")
            except Exception:
                response_data["status"] = response.status

    page_admin.on("response", capturar_resposta)

    # Preenche os campos
    filled = {}

    # E-mail — usa ID exato revelado pelo DOM: professional_email
    for sel in ["#professional_email", "input[id='professional_email']",
                "input[placeholder*='joao@email.com']", "input[placeholder*='exemplo@email.com']"]:
        loc = page_admin.locator(sel).first
        if loc.count() > 0:
            try:
                if loc.is_visible(timeout=1000):
                    loc.fill(novo_email)
                    filled["email"] = novo_email
                    log(f"  Email preenchido via {sel}: {loc.input_value()}")
                    break
            except Exception:
                pass

    # Nome — usa ID exato: professional_first_name
    for sel in ["#professional_first_name", "input[id='professional_first_name']",
                "input[placeholder*='Leandro']"]:
        loc = page_admin.locator(sel).first
        if loc.count() > 0:
            try:
                if loc.is_visible(timeout=1000):
                    loc.fill("QA11")
                    filled["nome"] = "QA11"
                    log(f"  Nome preenchido via {sel}: {loc.input_value()}")
                    break
            except Exception:
                pass

    # Sobrenome — usa ID exato: professional_last_name
    for sel in ["#professional_last_name", "input[id='professional_last_name']",
                "input[placeholder*='Custodio']", "input[placeholder*='Custódio']"]:
        loc = page_admin.locator(sel).first
        if loc.count() > 0:
            try:
                if loc.is_visible(timeout=1000):
                    loc.fill("TC3")
                    filled["sobrenome"] = "TC3"
                    log(f"  Sobrenome preenchido via {sel}: {loc.input_value()}")
                    break
            except Exception:
                pass

    # Senha (se houver campo)
    if tem_senha:
        for sel in ["input[type='password']", "input[name*='password']", "input[id*='password']"]:
            loc = page_admin.locator(sel).first
            if loc.count() > 0:
                try:
                    if loc.is_visible(timeout=1000):
                        loc.fill(novo_senha)
                        filled["senha"] = "***"
                        log(f"  Senha preenchida via {sel}")
                        break
                except Exception:
                    pass

    # Perfil/Role — select ou radio
    # Tenta select
    select_perfil_ok = False
    for sel in ["select[name*='role']", "select[name*='profile']", "select[id*='role']",
                "select[id*='profile']", "select[name*='kind']", "select"]:
        loc = page_admin.locator(sel).first
        if loc.count() > 0:
            try:
                if loc.is_visible(timeout=1000):
                    options = loc.evaluate("el => Array.from(el.options).map(o => ({value:o.value, text:o.innerText}))")
                    log(f"  Select perfil opcoes: {options}")
                    # Tenta Colaborador ou Student
                    for v in ["student", "collaborator", "2", "aluno", "colaborador"]:
                        try:
                            loc.select_option(v)
                            filled["perfil"] = v
                            select_perfil_ok = True
                            log(f"  Perfil selecionado: {v}")
                            break
                        except Exception:
                            pass
                    if select_perfil_ok:
                        break
            except Exception:
                pass

    if not select_perfil_ok:
        # Tenta radio button
        for lbl in ["Colaborador", "Aluno", "Student", "Collaborator"]:
            loc = page_admin.get_by_label(re.compile(lbl, re.I)).first
            if loc.count() > 0:
                try:
                    if loc.is_visible(timeout=1000):
                        loc.click(timeout=2000)
                        filled["perfil"] = lbl
                        select_perfil_ok = True
                        log(f"  Perfil (radio) clicado: {lbl}")
                        break
                except Exception:
                    pass

    log(f"  Campos preenchidos: {filled}")
    tw.snap(page_admin, EVID, "fechamento_tc3_form_preenchido")
    evids.append("fechamento_tc3_form_preenchido.png")

    # Submete o form
    criado = False
    motivo_falha = ""
    try:
        btn_s = page_admin.get_by_role("button", name=re.compile(
            r"Salvar|Criar|Convidar|Enviar|Adicionar", re.I)).first
        if btn_s.count() == 0 or not btn_s.is_visible(timeout=2000):
            btn_s = page_admin.locator("button[type='submit'], input[type='submit']").first
        if btn_s.count() > 0 and btn_s.is_visible(timeout=2000):
            btn_s.click(timeout=5000)
            # Aguarda redirect para /users ou toast de sucesso
            try:
                page_admin.wait_for_url(
                    re.compile(r"/users(?!/new)"),
                    timeout=10000,
                )
                criado = True
            except Exception:
                page_admin.wait_for_timeout(3500)
                url_pos = page_admin.url
                log(f"  URL pos-submit: {url_pos[:80]}")
                if "/users/new" not in url_pos and "/users" in url_pos:
                    criado = True
                elif page_admin.get_by_text(re.compile(r"sucesso|criado|adicionado|convite", re.I)).count() > 0:
                    criado = True
                else:
                    # Verifica mensagens de erro na pagina
                    err_msgs = page_admin.locator(
                        ".alert, .error, [class*='alert'], [class*='error'], [class*='invalid']"
                    ).all()
                    for em in err_msgs:
                        try:
                            txt = em.inner_text().strip()
                            if txt:
                                motivo_falha += txt[:200] + " | "
                        except Exception:
                            pass

            log(f"  Criado: {criado}, URL: {page_admin.url[:80]}")
            log(f"  HTTP response: {response_data}")
            if motivo_falha:
                log(f"  Mensagem de erro na pagina: {motivo_falha}")
        else:
            motivo_falha = "botao de submit nao encontrado no form"
    except Exception as e:
        motivo_falha = f"excecao ao submeter: {e}"
        log(f"  Erro submit: {e}")

    tw.snap(page_admin, EVID, "fechamento_tc3_apos_criar_usuario")
    evids.append("fechamento_tc3_apos_criar_usuario.png")

    if not criado:
        http_status = response_data.get("status", "?")
        http_body = response_data.get("body", "")
        motivo_completo = (
            f"criacao falhou — HTTP {http_status} | "
            f"campos={filled} | "
            f"tem_senha={tem_senha} | "
            f"motivo_pagina='{motivo_falha}' | "
            f"response_body='{http_body[:200]}'"
        )
        if http_status in (400, 422, "400", "422") or motivo_falha:
            falhou(3, evids, motivo_completo)
        else:
            bloqueado(3, evids, motivo_completo)
        return

    # Criado com sucesso — loga com o novo usuario em contexto isolado
    log(f"  Usuario criado! Logando como {novo_email} em contexto isolado...")
    novo_ctx = browser.new_context(viewport={"width": 1500, "height": 950}, locale="pt-BR")
    page_novo = novo_ctx.new_page()
    try:
        page_novo.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
        try:
            page_novo.wait_for_selector("#user_email", timeout=10000)
        except Exception:
            bloqueado(3, evids, "tela de login nao carregou para o novo usuario")
            return

        # Tenta com a senha definida no form
        page_novo.fill("#user_email", novo_email)
        page_novo.fill("#user_password", novo_senha)
        page_novo.click("#user_submit")
        try:
            page_novo.wait_for_load_state("networkidle", timeout=25000)
        except Exception:
            pass
        page_novo.wait_for_timeout(3000)
        tw.dispensar_nps(page_novo)

        login_ok = "/users/login" not in page_novo.url and "/login" not in page_novo.url
        log(f"  Login novo usuario: ok={login_ok}, URL={page_novo.url[:70]}")
        tw.snap(page_novo, EVID, "fechamento_tc3_login_novo_usuario")

        if not login_ok:
            # Pode ser invite-only (usuario recebe email, define senha) —
            # neste caso a senha '123456' nao funciona antes da ativacao
            bloqueado(3, evids,
                      f"usuario criado mas login com 123456 falhou — possivel fluxo de convite "
                      f"(usuario precisa ativar a conta via email antes de logar); "
                      f"email={novo_email}, tem_senha={tem_senha}")
            return

        # Navega para Meu historico
        url_hist = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"
        page_novo.goto(url_hist, wait_until="domcontentloaded", timeout=25000)
        try:
            page_novo.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page_novo.wait_for_timeout(2500)
        tw.dispensar_nps(page_novo)
        tw.snap(page_novo, EVID, "fechamento_tc3_empty_ok")
        evids.append("fechamento_tc3_empty_ok.png")

        log(f"  URL Meu historico: {page_novo.url[:70]}")

        # Verifica mensagem de empty state
        msg_exata = "Você ainda não tem registros. Adicione o primeiro pelo botão acima."
        has_empty = page_novo.get_by_text(msg_exata).count() > 0
        rows = page_novo.locator("table tbody tr").count()
        log(f"  Empty state msg: {has_empty}, linhas: {rows}")

        # Verifica 4 KPI cards zerados
        kpi_labels = ["Emitidos", "Expirados", "Pendentes", "Recusados"]
        kpi_found = {}
        kpi_values = {}
        for label in kpi_labels:
            try:
                card = page_novo.locator(
                    "[class*='stat'], [class*='kpi'], [class*='card'], "
                    "[class*='chakra-stat'], [class*='Stat']"
                ).filter(has_text=label).first
                if card.count() > 0:
                    kpi_found[label] = True
                    nums = re.findall(r'\b(\d+)\b', card.inner_text())
                    kpi_values[label] = int(nums[0]) if nums else None
                else:
                    kpi_found[label] = False
                    kpi_values[label] = None
            except Exception:
                kpi_found[label] = False
                kpi_values[label] = None

        log(f"  KPIs encontrados: {kpi_found}")
        log(f"  KPIs valores: {kpi_values}")
        tw.snap(page_novo, EVID, "fechamento_tc3_kpis")
        evids.append("fechamento_tc3_kpis.png")

        all_4_found = all(kpi_found.get(l, False) for l in kpi_labels)
        any_nonzero = any(kpi_values.get(l, 0) not in (0, None) for l in kpi_labels)

        if has_empty and rows == 0 and all_4_found and not any_nonzero:
            passou(3, evids,
                   f"msg exata presente; 0 linhas; 4 KPIs=0 ({kpi_values}); email={novo_email}")
        elif has_empty and rows == 0:
            missing = [l for l in kpi_labels if not kpi_found.get(l, False)]
            if missing:
                falhou(3, evids, f"msg OK, 0 linhas, mas KPIs ausentes: {missing}")
            elif any_nonzero:
                falhou(3, evids, f"msg OK, 0 linhas, mas KPIs nao zerados: {kpi_values}")
            else:
                passou(3, evids,
                       f"msg exata presente; 0 linhas; KPIs={kpi_values}; email={novo_email}")
        elif not has_empty and rows == 0:
            falhou(3, evids, "tabela vazia mas mensagem exata NAO encontrada")
        else:
            falhou(3, evids,
                   f"has_empty={has_empty}, rows={rows}, kpi={kpi_values}")
    finally:
        page_novo.close()
        novo_ctx.close()


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log("fechamento_qa11_pontos_finais.py")
    log(f"Org: {BASE_URL} / ID: {ORG_ID}")
    log("=" * 60)

    # TC11 — contexto do aluno (dante.tavares)
    with tw.sync_playwright() as p1:
        browser1, ctx1, page_alu = tw.nova_pagina(p1)
        try:
            log("\n--- TC11: paginacao pag1->pag2 (aluno dante) ---")
            login_aluno(page_alu)
            run_tc11(page_alu)
        finally:
            ctx1.close()
            browser1.close()

    # TC3 — admin cria usuario + valida empty state
    with tw.sync_playwright() as p2:
        browser2, ctx2, page_adm = tw.nova_pagina(p2)
        try:
            log("\n--- TC3: usuario novo + empty state (admin) ---")
            login_admin(page_adm)
            run_tc3(browser2, page_adm)
        finally:
            ctx2.close()
            browser2.close()

    log("\n" + "=" * 60)
    log("RESULTADOS FINAIS:")
    for tc, r in sorted(RESULTADOS.items()):
        log(f"  TC{tc}: {r['veredito']} — {r['obs']}")
    log("=" * 60)


if __name__ == "__main__":
    main()
