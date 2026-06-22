"""recon_qa11_paginacao.py — recon do footer de paginacao + criacao de usuario."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL = "https://registrosf2.stage.twygoead.com"
ADMIN_EMAIL = "dante.tavares@twygo.com"
ADMIN_SENHA = "123456"
ORG_ID = "37079"
EVID = tw.ROOT / "evidencias" / "registros-f2-qa11"
EVID.mkdir(parents=True, exist_ok=True)


def log(msg):
    print(msg, flush=True)


def login_aluno(page):
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("#user_email", timeout=15000)
    page.fill("#user_email", ADMIN_EMAIL)
    page.fill("#user_password", ADMIN_SENHA)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    log(f"Logado: {page.url[:60]}")


def ir_meu_historico(page):
    url = f"{BASE_URL}/o/{ORG_ID}/records?in_use_mode_layout=true"
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2500)
    tw.dispensar_nps(page)


def fechar_widget(page):
    """Fecha o chat widget da Sofia se estiver aberto."""
    try:
        fechar = page.locator("button").filter(has_text=re.compile(r"×|✕|fechar|close", re.I))
        visivel = [b for b in fechar.all() if b.is_visible(timeout=500)]
        if visivel:
            visivel[0].click(timeout=2000)
            page.wait_for_timeout(500)
            log("  Widget Sofia fechado")
        # Tambem tenta via data-testid ou aria
        try:
            page.locator("[data-dismiss='modal'], [aria-label*='fechar'], [aria-label*='close']").first.click(timeout=1000)
        except Exception:
            pass
    except Exception:
        pass


def recon_paginacao(page):
    log("\n=== RECON: Footer de paginacao ===")
    ir_meu_historico(page)

    rows = page.locator("table tbody tr").count()
    log(f"  Linhas visíveis: {rows}")
    tw.snap(page, EVID, "recon_pag_inicio")

    # Fecha widget da Sofia
    fechar_widget(page)
    page.wait_for_timeout(500)

    # Rola para o final da pagina para revelar paginacao
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1500)
    tw.snap(page, EVID, "recon_pag_footer_scroll")
    log("  Screenshot do footer capturado")

    # Dump do HTML proximo ao select de paginacao
    try:
        sel_element = page.locator("select").filter(
            has=page.locator("option[value='25']")
        ).first
        if sel_element.count() > 0:
            area = sel_element.evaluate("""el => {
                const parent = el.closest('[class*="pagination"], [class*="Pagination"], nav, div, section') || el.parentElement.parentElement;
                return parent ? parent.outerHTML.slice(0, 3000) : el.parentElement.outerHTML;
            }""")
            log(f"\n  HTML do container de paginacao:\n{area[:3000]}")
        else:
            log("  Nao achou select com opcao 25")
    except Exception as e:
        log(f"  Dump HTML erro: {e}")

    # Lista todos os botoes no footer
    try:
        todos_btns = page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            return btns
                .filter(b => {
                    const r = b.getBoundingClientRect();
                    return r.top > window.innerHeight * 0.5;
                })
                .map(b => ({
                    text: b.innerText?.trim()?.slice(0, 50),
                    ariaLabel: b.getAttribute('aria-label'),
                    disabled: b.disabled,
                    class: b.className?.slice(0, 80),
                    top: Math.round(b.getBoundingClientRect().top)
                }));
        }""")
        log(f"\n  Botoes na metade inferior da pagina: {len(todos_btns)}")
        for b in todos_btns:
            log(f"    top={b['top']:4d} | text={b['text']!r:20} | aria={b['ariaLabel']!r} | dis={b['disabled']} | cls={b['class'][:60]}")
    except Exception as e:
        log(f"  Lista botoes erro: {e}")

    # Dump do HTML completo abaixo da tabela
    try:
        after_table = page.evaluate("""() => {
            const table = document.querySelector('table');
            if (!table) return 'sem tabela';
            let el = table.nextElementSibling;
            let html = '';
            while (el) {
                html += el.outerHTML.slice(0, 1500);
                el = el.nextElementSibling;
            }
            return html || 'nada apos tabela';
        }""")
        log(f"\n  HTML apos tabela:\n{after_table[:3000]}")
    except Exception as e:
        log(f"  After-table dump erro: {e}")


def recon_criar_usuario(page):
    log("\n=== RECON: Criacao de usuario + reset senha ===")
    # Login admin
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("#user_email", timeout=15000)
    page.fill("#user_email", ADMIN_EMAIL)
    page.fill("#user_password", ADMIN_SENHA)
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    # Switch admin
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

    # Vai para form novo usuario
    page.goto(
        f"{BASE_URL}/o/{ORG_ID}/users/new",
        wait_until="domcontentloaded", timeout=60000
    )
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)

    # Dump do HTML do form
    try:
        form_html = page.evaluate("""() => {
            const form = document.querySelector('form');
            return form ? form.outerHTML.slice(0, 5000) : 'sem form';
        }""")
        log(f"\n  HTML do form de usuario:\n{form_html[:5000]}")
    except Exception as e:
        log(f"  Form HTML erro: {e}")

    # Lista todos os inputs e seus atributos
    try:
        inputs = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('input')).map(i => ({
                id: i.id,
                name: i.name,
                type: i.type,
                placeholder: i.placeholder,
                value: i.value,
                required: i.required,
                autocomplete: i.autocomplete
            }));
        }""")
        log(f"\n  Inputs no form: {len(inputs)}")
        for i in inputs:
            log(f"    id={i['id']!r} name={i['name']!r} type={i['type']!r} "
                f"placeholder={i['placeholder']!r} req={i['required']}")
    except Exception as e:
        log(f"  Inputs erro: {e}")

    # Preenche na ordem correta: Email primeiro
    import os
    novo_email = f"qa11tc3r{os.getpid()}@mailtest.example"
    log(f"\n  Email alvo: {novo_email}")

    # Abordagem: usa o primeiro input visivel para email (deve ter placeholder email)
    inputs_visiveis = page.locator("input:visible").all()
    log(f"  Inputs visíveis: {len(inputs_visiveis)}")
    for idx, inp in enumerate(inputs_visiveis):
        try:
            ph = inp.get_attribute("placeholder") or ""
            id_ = inp.get_attribute("id") or ""
            type_ = inp.get_attribute("type") or ""
            log(f"    [{idx}] id={id_!r} ph={ph!r} type={type_!r}")
        except Exception:
            pass

    tw.snap(page, EVID, "recon_form_usuario")

    # Preenche: input [0] = email, [1] = nome, [2] = sobrenome (ordem real do form)
    try:
        inputs_v = page.locator("input:visible").all()
        # Coleta infos
        phs = []
        for inp in inputs_v:
            try:
                phs.append(inp.get_attribute("placeholder") or "")
            except Exception:
                phs.append("")
        log(f"  Placeholders: {phs}")
    except Exception:
        pass

    # Preenche por placeholder EMAIL especificamente
    email_inp = None
    for placeholder_candidato in ["Ex: joao@email.com", "joao@email.com", "email", "e-mail"]:
        try:
            el = page.get_by_placeholder(placeholder_candidato, exact=False).first
            if el.count() > 0 and el.is_visible(timeout=1000):
                email_inp = el
                log(f"  Email input achado via placeholder {placeholder_candidato!r}")
                break
        except Exception:
            pass

    if email_inp is None:
        # Tenta pelo primeiro input type email
        try:
            el = page.locator("input[type='email']").first
            if el.count() > 0 and el.is_visible(timeout=1000):
                email_inp = el
                log("  Email input achado via type=email")
        except Exception:
            pass

    if email_inp is None:
        # Tenta pelo label E-mail
        try:
            el = page.get_by_label("E-mail", exact=True).first
            if el.count() > 0 and el.is_visible(timeout=1000):
                email_inp = el
                log("  Email input achado via label E-mail")
        except Exception:
            pass

    if email_inp:
        email_inp.click(timeout=3000)
        email_inp.fill(novo_email)
        page.wait_for_timeout(300)
        val = email_inp.input_value()
        log(f"  Email preenchido: {val!r}")
        tw.snap(page, EVID, "recon_form_email_preenchido")
    else:
        log("  ERRO: nao achou campo de email!")
        return None

    # Preenche Nome
    nome_inp = None
    for ph_cand in ["Ex: Leandro", "Leandro", "Nome", "First name"]:
        try:
            el = page.get_by_placeholder(ph_cand, exact=False).first
            if el.count() > 0 and el.is_visible(timeout=1000):
                nome_inp = el
                log(f"  Nome input achado via placeholder {ph_cand!r}")
                break
        except Exception:
            pass
    if nome_inp is None:
        try:
            el = page.get_by_label("Nome", exact=True).first
            if el.count() > 0 and el.is_visible(timeout=1000):
                nome_inp = el
                log("  Nome input achado via label")
        except Exception:
            pass

    if nome_inp:
        nome_inp.click(timeout=3000)
        nome_inp.fill("QA11TC3")
        page.wait_for_timeout(200)
        log(f"  Nome: {nome_inp.input_value()!r}")

    # Preenche Sobrenome
    sob_inp = None
    for ph_cand in ["Ex: Silva", "Silva", "Sobrenome", "Last name"]:
        try:
            el = page.get_by_placeholder(ph_cand, exact=False).first
            if el.count() > 0 and el.is_visible(timeout=1000):
                sob_inp = el
                log(f"  Sobrenome input achado via placeholder {ph_cand!r}")
                break
        except Exception:
            pass
    if sob_inp is None:
        try:
            el = page.get_by_label("Sobrenome", exact=True).first
            if el.count() > 0 and el.is_visible(timeout=1000):
                sob_inp = el
                log("  Sobrenome input achado via label")
        except Exception:
            pass

    if sob_inp:
        sob_inp.click(timeout=3000)
        sob_inp.fill("EmptyUser")
        page.wait_for_timeout(200)
        log(f"  Sobrenome: {sob_inp.input_value()!r}")

    tw.snap(page, EVID, "recon_form_completo")

    # Salva o usuario
    btn_salvar = None
    for name_cand in ["Salvar", "Criar", "Convidar", "Enviar"]:
        try:
            el = page.get_by_role("button", name=re.compile(name_cand, re.I)).first
            if el.count() > 0 and el.is_visible(timeout=1000):
                btn_salvar = el
                log(f"  Botao salvar achado: {name_cand!r}")
                break
        except Exception:
            pass

    if btn_salvar:
        btn_salvar.click(timeout=5000)
        try:
            page.wait_for_url(
                re.compile(r"/users(?:/\d+)?(?:\?|$)"),
                timeout=10000
            )
            log(f"  Redirect pos-salvar: {page.url[:60]}")
            criado = True
        except Exception:
            page.wait_for_timeout(3000)
            criado = "/users/new" not in page.url
            log(f"  Timeout redirect, URL: {page.url[:60]}, criado={criado}")
        tw.snap(page, EVID, "recon_pos_criar_usuario")
    else:
        log("  ERRO: nao achou botao salvar!")
        return None

    # Tenta reset de senha via admin (se criado)
    if criado and "/users" in page.url:
        # O novo usuario pode aparecer na URL ou redirecionar para lista
        user_url = page.url
        log(f"\n  Usuario criado. URL final: {user_url}")

        # Procura botao/link de reset de senha na pagina
        try:
            reset_btns = page.locator("a, button").filter(
                has_text=re.compile(r"senha|password|reset", re.I)
            ).all()
            log(f"  Botoes de reset: {len(reset_btns)}")
            for rb in reset_btns:
                try:
                    log(f"    - {rb.inner_text()!r} href={rb.get_attribute('href')!r}")
                except Exception:
                    pass
        except Exception as e:
            log(f"  Busca reset erro: {e}")

        # Verifica se o usuario aparece na lista e se tem acao de reset
        page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(2000)
        tw.dispensar_nps(page)
        tw.snap(page, EVID, "recon_lista_usuarios")
        log(f"  Lista de usuarios capturada")

        # Busca o usuario criado
        try:
            page.fill("input[type='search'], input[placeholder*='busca'], input[placeholder*='search']",
                      "QA11TC3")
            page.wait_for_timeout(1500)
            tw.snap(page, EVID, "recon_busca_usuario")
        except Exception as e:
            log(f"  Busca usuario erro: {e}")

        return novo_email
    return None


def main():
    log("=" * 60)
    log("recon_qa11_paginacao.py")
    log("=" * 60)

    # Parte 1: Recon paginacao (como aluno)
    with tw.sync_playwright() as p1:
        browser, ctx, page = tw.nova_pagina(p1)
        try:
            login_aluno(page)
            recon_paginacao(page)
        finally:
            ctx.close()
            browser.close()

    # Parte 2: Recon criacao de usuario (como admin)
    with tw.sync_playwright() as p2:
        browser, ctx, page = tw.nova_pagina(p2)
        try:
            email = recon_criar_usuario(page)
            log(f"\n  Email criado: {email}")
        finally:
            ctx.close()
            browser.close()

    log("\n" + "=" * 60)
    log("RECON CONCLUIDO")
    log("=" * 60)


if __name__ == "__main__":
    main()
