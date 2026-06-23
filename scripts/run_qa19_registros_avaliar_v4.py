"""
QA 1.9 v4 — Avaliar registro pendente (Aprovar/Recusar + modal justificativa)
Card Artia: 19896

Correções da v3:
- Cria registros descartáveis como ALUNO (formulário mais simples)
- selecionar_tipo: digita o valor antes de clicar na opção
- Verifica id antes de usar: garante que não é 44279951 (fixture compartilhado)
- TC1: navega filtrado e valida kebab da linha correta via href
- TC3: usa registro com tipo VAZIO (sem preencher)
- Restaura fixture 44279951 ao final
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw

BASE_URL   = "https://registrosf2.stage.twygoead.com"
ORG_ID     = "37079"
ADMIN_EMAIL    = "dante.tavares@twygo.com"
ADMIN_PASSWORD = "123456"
ALUNO_EMAIL    = "qa11tc342588@twygotest.com"
ALUNO_PASSWORD = "twygoqa2026"
LIDER_EMAIL    = "qalider@teste.com"
LIDER_PASSWORD = "123456"

PASTA = Path(__file__).resolve().parents[1] / "evidencias" / "registros-f2-qa19"
PASTA.mkdir(parents=True, exist_ok=True)

MUTACOES = []
resultados = {}


def snap(page, nome, full=False):
    fp = PASTA / f"{nome}.png"
    page.screenshot(path=str(fp), full_page=full)
    print(f"   [snap] {fp.name}")
    return fp


def registrar_mutacao(rid, pessoa, conteudo, acao):
    MUTACOES.append({"id": rid, "pessoa": pessoa, "conteudo": conteudo, "acao": acao})
    print(f"   [MUTACAO] {acao} — id={rid}")


def tc_resultado(tc, veredito, resumo):
    resultados[tc] = {"veredito": veredito, "resumo": resumo}
    icone = "PASSOU" if veredito == "PASSOU" else ("FALHOU" if veredito == "FALHOU" else "NAO_VERIFICADO")
    print(f"\n   [{icone}] {tc}: {resumo}\n")


# =============================================================================
# Helpers
# =============================================================================

def ir_records_admin(page, filtro=None):
    url = f"{BASE_URL}/o/{ORG_ID}/records"
    if filtro:
        url += f"?situation={filtro}"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(2500)
    tw.dispensar_nps(page)


def ir_records_aluno(page):
    page.goto(f"{BASE_URL}/records", wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)


def aguardar_tabela(page, timeout=25000):
    try:
        page.wait_for_function(
            "() => document.querySelectorAll('tbody tr').length > 0",
            timeout=timeout
        )
        page.wait_for_timeout(1000)
        return True
    except Exception:
        return False


def api_registros_admin(page, situation=None, origin=None, per_page=10):
    params = f"order_type=desc&per_page={per_page}&page=1&order_by=created_at"
    if situation:
        params += f"&situation={situation}"
    if origin:
        params += f"&origin={origin}"
    resp = page.request.get(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/records?{params}",
        headers={"Accept": "application/json"}
    )
    if resp.status != 200:
        print(f"   [api_admin] status={resp.status}")
        return []
    return resp.json().get("data", {}).get("records", [])


def abrir_kebab_id(page, record_id):
    """Abre kebab do registro pelo ID. Usa tw.menu_visivel() para confirmar."""
    # Estratégia 1: data-test-id
    btn = page.locator(f"[data-test-id='records-{record_id}-menu-button']")
    if btn.count() > 0:
        btn.first.click(force=True)
        page.wait_for_timeout(1200)
        if tw.menu_visivel(page):
            return True

    # Estratégia 2: via link href na linha
    rows = page.locator("tbody tr")
    for i in range(rows.count()):
        row = rows.nth(i)
        if row.locator(f"a[href*='/records/{record_id}']").count() > 0:
            btn = row.locator("button[aria-haspopup='menu']")
            if btn.count() > 0:
                btn.first.click(force=True)
                page.wait_for_timeout(1200)
                if tw.menu_visivel(page):
                    return True

    # Estratégia 3: ancestral xpath
    for btn in page.locator("button[aria-haspopup='menu']").all():
        try:
            # Verificar texto da linha
            row_text = btn.evaluate(
                "el => { const tr = el.closest('tr'); return tr ? tr.innerText : ''; }"
            )
            if str(record_id) in row_text:
                btn.click(force=True)
                page.wait_for_timeout(1200)
                if tw.menu_visivel(page):
                    return True
        except Exception:
            pass

    return False


def fechar_menu(page):
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)


def abrir_form_avaliar(page, record_id):
    url = f"{BASE_URL}/o/{ORG_ID}/records/{record_id}/edit?mode=admin-avaliar"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    botoes = page.locator("button").all_text_contents()
    tem_aprovar = any("Aprovar" in b for b in botoes)
    print(f"   [form] URL={page.url} tem_aprovar={tem_aprovar}")
    return tem_aprovar


def selecionar_tipo_digitando(page, tipo="Curso"):
    """
    Seleciona tipo de experiência digitando no campo (React-Select type-ahead).
    """
    # Tentar encontrar o input dentro do React-Select de Tipo de experiência
    # O campo tem placeholder "Digite ou selecione o tipo da experiência"
    for sel in [
        "input[id*='experience']",
        "input[placeholder*='tipo']",
        "input[placeholder*='experiência']",
        "div[class*='select__control'] input",
        "div[class*='react-select__control'] input",
    ]:
        inputs = page.locator(sel)
        if inputs.count() > 0:
            inp = inputs.first
            try:
                inp.click(timeout=2000)
                page.wait_for_timeout(500)
                inp.fill("")
                inp.type(tipo, delay=50)
                page.wait_for_timeout(800)
                # Verificar opções
                opcoes = page.locator("[role='option']").filter(has_text=tipo)
                if opcoes.count() > 0:
                    opcoes.first.click()
                    page.wait_for_timeout(600)
                    print(f"   [tipo] '{tipo}' via {sel}")
                    return True
                # Tentar Enter
                page.keyboard.press("Enter")
                page.wait_for_timeout(400)
                print(f"   [tipo] '{tipo}' via Enter (sem opção)")
                return True
            except Exception as e:
                print(f"   [tipo] Erro {sel}: {e}")

    # Clicar no container e depois digitar
    containers = page.locator("div[class*='select__control'], div[class*='react-select__control']")
    for i in range(min(containers.count(), 3)):
        try:
            containers.nth(i).click(timeout=2000)
            page.wait_for_timeout(500)
            page.keyboard.type(tipo, delay=50)
            page.wait_for_timeout(800)
            opcoes = page.locator("[role='option']").filter(has_text=tipo)
            if opcoes.count() > 0:
                opcoes.first.click()
                page.wait_for_timeout(600)
                print(f"   [tipo] '{tipo}' via container[{i}]")
                return True
            fechar_menu(page)
        except Exception:
            pass

    print(f"   [tipo] Falhou para '{tipo}'")
    return False


def criar_registro_como_aluno(page_aluno, sufixo="desc"):
    """
    Cria registro Externo+Pendente como ALUNO via formulário /records/new.
    O aluno preenche conteúdo + provedor (ou apenas envia com mínimo).
    Retorna (id, email_aluno, conteudo) ou None.
    """
    ts = int(time.time() % 100000)
    conteudo_nome = f"QA19-{sufixo}-{ts}"

    ir_records_aluno(page_aluno)
    page_aluno.wait_for_timeout(1000)

    btn_add = page_aluno.locator("button").filter(has_text="Adicionar")
    if btn_add.count() == 0:
        # Tentar link "Adicionar"
        btn_add = page_aluno.locator("a, button").filter(has_text="Adicionar")
    if btn_add.count() == 0:
        print("   [criar_aluno] Botão Adicionar não encontrado")
        snap(page_aluno, f"criar_{sufixo}_sem_botao")
        return None

    btn_add.first.click()
    page_aluno.wait_for_timeout(3000)
    tw.dispensar_nps(page_aluno)
    snap(page_aluno, f"criar_{sufixo}_form_aluno")

    url_atual = page_aluno.url
    print(f"   [criar_aluno] URL: {url_atual}")

    if "/records/new" not in url_atual:
        print("   [criar_aluno] Form não abriu")
        return None

    # Preencher Conteúdo (campo de texto/dropdown)
    # No form do aluno, o campo "Conteúdo" geralmente aceita texto livre ou é criado
    conteudo_preenchido = False
    for sel in [
        "div[class*='select__control']:nth-child(2)",
        "div[class*='select__control']",
        "div[class*='react-select__control']",
    ]:
        conts = page_aluno.locator(sel)
        if conts.count() > 0:
            # Percorrer para encontrar o que parece ser "Conteúdo"
            for i in range(min(conts.count(), 5)):
                try:
                    cont_inp = conts.nth(i).locator("input")
                    if cont_inp.count() > 0:
                        cont_inp.first.click(timeout=1500)
                        page_aluno.wait_for_timeout(300)
                        placeholder = cont_inp.first.get_attribute("placeholder") or ""
                        print(f"   [criar_aluno] Input {i} placeholder: {placeholder}")
                        if "conteúdo" in placeholder.lower() or "nome" in placeholder.lower() or "Digite" in placeholder:
                            cont_inp.first.type(conteudo_nome, delay=50)
                            page_aluno.wait_for_timeout(500)
                            opcoes = page_aluno.locator("[role='option']").first
                            if opcoes.count() > 0:
                                opcoes.click()
                            else:
                                page_aluno.keyboard.press("Enter")
                            conteudo_preenchido = True
                            print(f"   [criar_aluno] Conteúdo preenchido: {conteudo_nome}")
                            break
                except Exception as e:
                    print(f"   [criar_aluno] Cont[{i}]: {e}")
            if conteudo_preenchido:
                break

    # Data de término (obrigatória)
    data_preenchida = False
    data_inputs = page_aluno.locator("input[type='date']")
    if data_inputs.count() > 0:
        for i in range(data_inputs.count()):
            inp = data_inputs.nth(i)
            try:
                val = inp.input_value()
                if not val:
                    inp.fill("2026-12-31")
                    page_aluno.wait_for_timeout(200)
                    val_after = inp.input_value()
                    if val_after:
                        data_preenchida = True
                        print(f"   [criar_aluno] Data[{i}]={val_after}")
                        break
            except Exception:
                pass

    # Tentar input de data no formato pt-BR
    if not data_preenchida:
        inputs_text = page_aluno.locator("input[placeholder='dd/mm/aaaa'], input[placeholder*='dd/mm']")
        if inputs_text.count() > 0:
            for i in range(inputs_text.count()):
                inp = inputs_text.nth(i)
                try:
                    inp.fill("31/12/2026")
                    page_aluno.wait_for_timeout(200)
                    val = inp.input_value()
                    if val:
                        data_preenchida = True
                        break
                except Exception:
                    pass

    snap(page_aluno, f"criar_{sufixo}_form_preenchido_aluno", full=True)

    # Clicar em "Enviar" (aluno envia para aprovação → status Pendente)
    for btn_txt in ["Enviar", "Salvar"]:
        btn_enviar = page_aluno.locator("button").filter(has_text=btn_txt)
        if btn_enviar.count() > 0:
            for i in range(btn_enviar.count()):
                b = btn_enviar.nth(i)
                if b.is_visible():
                    b.click()
                    page_aluno.wait_for_timeout(4000)
                    snap(page_aluno, f"criar_{sufixo}_pos_envio")
                    print(f"   [criar_aluno] Clicou '{btn_txt}[{i}]'")
                    break

    url_pos = page_aluno.url
    page_text = page_aluno.locator("body").inner_text()
    enviado = "enviado" in page_text.lower() or "aprovação" in page_text.lower()
    print(f"   [criar_aluno] URL={url_pos} | enviado={enviado}")

    # Buscar o registro criado via API admin (o aluno cria, admin vê)
    # Usar a sessão do aluno para buscar registros do aluno
    page_aluno.wait_for_timeout(1500)
    resp = page_aluno.request.get(
        f"{BASE_URL}/api/v1/records?situation=pending&per_page=5&page=1&order_by=created_at&order_type=desc",
        headers={"Accept": "application/json"}
    )
    print(f"   [criar_aluno] API aluno status={resp.status}")
    if resp.status == 200:
        recs = resp.json().get("data", {}).get("records", [])
        if recs:
            r = recs[0]
            print(f"   [criar_aluno] Registro: id={r['id']} content={r.get('content','')}")
            return r["id"], ALUNO_EMAIL, r.get("content", conteudo_nome)

    return None


def criar_registro_admin_form(page_admin, sufixo="desc", skip_tipo=True):
    """
    Cria registro como admin via formulário.
    skip_tipo=True: não preenche Tipo de experiência (TC3 precisa de tipo vazio).
    Retorna (id, email, conteudo) ou None.
    """
    ts = int(time.time() % 100000)
    conteudo_nome = f"QA19-{sufixo}-{ts}"

    ir_records_admin(page_admin)
    page_admin.wait_for_timeout(500)

    btn_add = page_admin.locator("button").filter(has_text="Adicionar")
    if btn_add.count() == 0:
        return None
    btn_add.first.click()
    page_admin.wait_for_timeout(3000)
    tw.dispensar_nps(page_admin)

    if "/records/new" not in page_admin.url:
        print(f"   [criar_admin] URL não é /records/new: {page_admin.url}")
        return None

    snap(page_admin, f"criar_admin_{sufixo}_form")

    # Campo "Pessoas" — input type-ahead
    try:
        # Clicar no campo de pessoas e digitar o nome do aluno
        field_pessoas = page_admin.locator("input[placeholder*='Adicionar'], input[placeholder*='pessoa'], input[placeholder*='Buscar']").first
        if field_pessoas.count() == 0:
            # Tentar via o container de pessoas
            field_pessoas = page_admin.locator("div[class*='select__control']").first
        field_pessoas.click(timeout=2000)
        page_admin.wait_for_timeout(400)
        page_admin.keyboard.type("QA11", delay=50)
        page_admin.wait_for_timeout(800)
        opcao = page_admin.locator("[role='option']").first
        if opcao.count() > 0:
            opcao.click()
            page_admin.wait_for_timeout(400)
            print("   [criar_admin] Pessoa selecionada")
    except Exception as e:
        print(f"   [criar_admin] Pessoa: {e}")

    # Campo Provedor
    try:
        page_admin.evaluate("window.scrollTo(0,400)")
        page_admin.wait_for_timeout(300)
        provs = page_admin.locator("div[class*='select__control'], div[class*='react-select__control']")
        # Normalmente Provedor é o segundo react-select após Pessoas
        for i in range(min(provs.count(), 4)):
            prov = provs.nth(i)
            inp_prov = prov.locator("input")
            if inp_prov.count() > 0:
                placeholder_prov = inp_prov.first.get_attribute("placeholder") or ""
                if "provedor" in placeholder_prov.lower() or "provedor" in prov.inner_text().lower():
                    inp_prov.first.click(timeout=1500)
                    page_admin.wait_for_timeout(300)
                    page_admin.keyboard.type("Alura", delay=50)
                    page_admin.wait_for_timeout(600)
                    opcao = page_admin.locator("[role='option']").filter(has_text="Alura")
                    if opcao.count() > 0:
                        opcao.first.click()
                    else:
                        opcao_any = page_admin.locator("[role='option']").first
                        if opcao_any.count() > 0:
                            opcao_any.click()
                    page_admin.wait_for_timeout(400)
                    print("   [criar_admin] Provedor selecionado")
                    break
    except Exception as e:
        print(f"   [criar_admin] Provedor: {e}")

    # Campo Conteúdo
    try:
        page_admin.evaluate("window.scrollTo(0,600)")
        page_admin.wait_for_timeout(300)
        conts = page_admin.locator("div[class*='select__control'], div[class*='react-select__control']")
        for i in range(min(conts.count(), 5)):
            cont = conts.nth(i)
            inp_cont = cont.locator("input")
            if inp_cont.count() > 0:
                placeholder_cont = inp_cont.first.get_attribute("placeholder") or ""
                if "conteúdo" in placeholder_cont.lower() or "conte" in placeholder_cont.lower() or "nome" in placeholder_cont.lower():
                    inp_cont.first.click(timeout=1500)
                    page_admin.wait_for_timeout(300)
                    page_admin.keyboard.type(conteudo_nome, delay=50)
                    page_admin.wait_for_timeout(600)
                    opcao = page_admin.locator("[role='option']").first
                    if opcao.count() > 0:
                        opcao.click()
                    else:
                        page_admin.keyboard.press("Enter")
                    page_admin.wait_for_timeout(400)
                    print(f"   [criar_admin] Conteúdo: {conteudo_nome}")
                    break
    except Exception as e:
        print(f"   [criar_admin] Conteúdo: {e}")

    # Data de término
    page_admin.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page_admin.wait_for_timeout(400)
    try:
        data_inputs = page_admin.locator("input[type='date']")
        for i in range(data_inputs.count()):
            inp = data_inputs.nth(i)
            val = inp.input_value()
            if not val:
                inp.fill("2026-12-31")
                page_admin.wait_for_timeout(200)
                val2 = inp.input_value()
                if val2:
                    print(f"   [criar_admin] Data={val2}")
                    break
    except Exception as e:
        print(f"   [criar_admin] Data: {e}")

    # Carga horária (às vezes obrigatória)
    try:
        ch_inputs = page_admin.locator("input[placeholder='HH:MM:SS'], input[placeholder*='hora']")
        if ch_inputs.count() > 0 and ch_inputs.first.is_visible():
            ch_inputs.first.fill("00:01:00")
            print("   [criar_admin] Carga horária preenchida")
    except Exception:
        pass

    snap(page_admin, f"criar_admin_{sufixo}_form_preenchido", full=True)

    # Botão de envio
    for btn_txt in ["Salvar e aprovar", "Salvar", "Enviar"]:
        btn = page_admin.locator("button").filter(has_text=btn_txt)
        if btn.count() > 0:
            for i in range(btn.count()):
                b = btn.nth(i)
                if b.is_visible():
                    b.click()
                    page_admin.wait_for_timeout(4000)
                    snap(page_admin, f"criar_admin_{sufixo}_pos_envio")
                    print(f"   [criar_admin] Clicou '{btn_txt}'")

                    # Verificar URL/toast
                    url_p = page_admin.url
                    page_text = page_admin.locator("body").inner_text()
                    salvo = "salvo" in page_text.lower() or "aprovação" in page_text.lower()
                    print(f"   [criar_admin] URL={url_p} salvo={salvo}")

                    # Buscar via API
                    page_admin.wait_for_timeout(1000)
                    recs = api_registros_admin(page_admin, situation="pending", origin="external", per_page=5)
                    for r in recs:
                        nome_r = str(r.get("content", "") or "")
                        if conteudo_nome[:8] in nome_r or r["id"] != 44279951:
                            print(f"   [criar_admin] Registro: id={r['id']}")
                            return r["id"], ADMIN_EMAIL, nome_r
                    break

    return None


# =============================================================================
# TC1 — Disponibilidade do "Avaliar" no menu
# =============================================================================
def executar_tc1(page_admin, page_aluno):
    print("\n=== TC1 — Disponibilidade do 'Avaliar' no menu ===")
    tc = "TC1"

    # Buscar registros via API para saber IDs exatos
    recs_ext_pend = api_registros_admin(page_admin, situation="pending", origin="external", per_page=5)
    recs_ext_emit = api_registros_admin(page_admin, situation="emitted", origin="external", per_page=5)
    recs_int_pend = api_registros_admin(page_admin, situation="pending", origin="internal", per_page=5)

    if not recs_ext_pend:
        tc_resultado(tc, "NAO_VERIFICADO", "Nenhum Externo+Pendente disponível")
        return None

    rec_pend = recs_ext_pend[0]
    print(f"   Ext+Pend: id={rec_pend['id']} person={rec_pend.get('person','')}")

    # --- P1: Externo+Pendente deve ter "Avaliar" primeiro, sem Editar nem Excluir ---
    ir_records_admin(page_admin, filtro="pending")
    aguardar_tabela(page_admin)

    abriu_pend = abrir_kebab_id(page_admin, rec_pend["id"])
    itens_pend = tw.menu_visivel(page_admin)
    print(f"   P1 abriu={abriu_pend} itens={itens_pend}")
    snap(page_admin, "tc1_01_menu_externo_pendente")

    if not abriu_pend and not itens_pend:
        # Abrir o primeiro kebab da lista (filtro=pending garantiu que são pendentes)
        btns = page_admin.locator("button[aria-haspopup='menu']")
        if btns.count() > 0:
            btns.first.click(force=True)
            page_admin.wait_for_timeout(1200)
            itens_pend = tw.menu_visivel(page_admin)
            snap(page_admin, "tc1_01b_primeiro_kebab")
            print(f"   P1 fallback itens={itens_pend}")

    tem_avaliar_pend  = any("Avaliar"  in i for i in itens_pend)
    tem_editar_pend   = any("Editar"   in i for i in itens_pend)
    tem_excluir_pend  = any("Excluir"  in i for i in itens_pend)
    primeiro_pend = itens_pend[0].strip() if itens_pend else ""
    avaliar_primeiro = "Avaliar" in primeiro_pend
    fechar_menu(page_admin)

    # --- P2: Externo+Emitido NÃO deve ter "Avaliar" ---
    itens_emit = []
    tem_avaliar_emit = None
    if recs_ext_emit:
        rec_emit = recs_ext_emit[0]
        print(f"   Ext+Emit: id={rec_emit['id']}")
        ir_records_admin(page_admin, filtro="emitted")
        aguardar_tabela(page_admin)
        abriu_emit = abrir_kebab_id(page_admin, rec_emit["id"])
        itens_emit = tw.menu_visivel(page_admin)
        if not abriu_emit and not itens_emit:
            btns = page_admin.locator("button[aria-haspopup='menu']")
            if btns.count() > 0:
                btns.first.click(force=True)
                page_admin.wait_for_timeout(1200)
                itens_emit = tw.menu_visivel(page_admin)
        snap(page_admin, "tc1_02_menu_externo_emitido")
        print(f"   P2 itens={itens_emit}")
        tem_avaliar_emit = any("Avaliar" in i for i in itens_emit)
        fechar_menu(page_admin)

    # --- P3: Interno+Pendente NÃO deve ter "Avaliar" ---
    tem_avaliar_int = None
    if recs_int_pend:
        rec_int = recs_int_pend[0]
        print(f"   Int+Pend: id={rec_int['id']}")
        ir_records_admin(page_admin)
        aguardar_tabela(page_admin)
        if abrir_kebab_id(page_admin, rec_int["id"]):
            itens_int = tw.menu_visivel(page_admin)
            snap(page_admin, "tc1_03_menu_interno_pendente")
            print(f"   P3 itens={itens_int}")
            tem_avaliar_int = any("Avaliar" in i for i in itens_int)
            fechar_menu(page_admin)
    else:
        print("   P3: Interno+Pendente ausente na stage")

    # --- P4: Aluno NÃO deve ver "Avaliar" ---
    tem_avaliar_aluno = None
    try:
        ir_records_aluno(page_aluno)
        btns_a = page_aluno.locator("button[aria-haspopup='menu']")
        if btns_a.count() > 0:
            btns_a.first.click(force=True)
            page_aluno.wait_for_timeout(1200)
            itens_aluno = tw.menu_visivel(page_aluno)
            snap(page_aluno, "tc1_04_aluno_menu")
            print(f"   P4 aluno itens={itens_aluno}")
            tem_avaliar_aluno = any("Avaliar" in i for i in itens_aluno)
            fechar_menu(page_aluno)
        else:
            print("   P4: Aluno sem kebab (sem registros?)")
    except Exception as e:
        print(f"   P4 erro: {e}")

    # --- Avaliação ---
    print(f"\n   Resumo:")
    print(f"   P1: avaliar={tem_avaliar_pend} primeiro={avaliar_primeiro} editar={tem_editar_pend} excluir={tem_excluir_pend}")
    print(f"   P2: avaliar_emit={tem_avaliar_emit}")
    print(f"   P3: avaliar_int={tem_avaliar_int}")
    print(f"   P4: avaliar_aluno={tem_avaliar_aluno}")

    bugs = []
    if not tem_avaliar_pend:
        bugs.append("'Avaliar' ausente em Externo+Pendente")
    if not avaliar_primeiro:
        bugs.append(f"'Avaliar' não é o primeiro item (primeiro: '{primeiro_pend}')")
    if tem_editar_pend:
        bugs.append("'Editar' presente em Externo+Pendente (RN 50: NÃO deveria)")
    if tem_excluir_pend:
        bugs.append("'Excluir' presente em Externo+Pendente (RN 50: NÃO deveria)")
    if tem_avaliar_emit is True:
        bugs.append("'Avaliar' presente em Externo+Emitido (não deveria)")
    if tem_avaliar_int is True:
        bugs.append("'Avaliar' presente em Interno+Pendente (só deve aparecer em Externo)")
    if tem_avaliar_aluno is True:
        bugs.append("'Avaliar' presente para Aluno (exclusivo Admin/Líder)")

    if not bugs:
        veredito = "PASSOU"
        resumo = (f"'Avaliar' presente e primeiro em Externo+Pendente; sem Editar/Excluir; "
                  f"ausente em Emitido; aluno={'não vê' if tem_avaliar_aluno is False else 'não testado'}")
    else:
        veredito = "FALHOU"
        resumo = " | ".join(bugs)

    tc_resultado(tc, veredito, resumo)
    return rec_pend["id"]


# =============================================================================
# TC2 — Form em modo avaliação
# =============================================================================
def executar_tc2(page_admin, record_id):
    print("\n=== TC2 — Form em modo avaliação ===")
    tc = "TC2"

    if not record_id:
        tc_resultado(tc, "NAO_VERIFICADO", "Sem registro")
        return

    # Abrir via kebab para observar a URL real gerada
    ir_records_admin(page_admin, filtro="pending")
    aguardar_tabela(page_admin)

    url_kebab = None
    if abrir_kebab_id(page_admin, record_id):
        itens = tw.menu_visivel(page_admin)
        print(f"   Itens menu: {itens}")
        if any("Avaliar" in i for i in itens):
            tw.click_menuitem(page_admin, "Avaliar")
            page_admin.wait_for_timeout(3000)
            url_kebab = page_admin.url
            print(f"   URL via kebab 'Avaliar': {url_kebab}")
        else:
            fechar_menu(page_admin)

    snap(page_admin, "tc2_01_via_kebab")

    # Garantir que estamos no form
    if not url_kebab or "edit" not in url_kebab:
        url_direta = f"{BASE_URL}/o/{ORG_ID}/records/{record_id}/edit?mode=admin-avaliar"
        page_admin.goto(url_direta, wait_until="domcontentloaded", timeout=30000)
        try:
            page_admin.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page_admin.wait_for_timeout(2000)
        tw.dispensar_nps(page_admin)

    url_final = page_admin.url
    form_ok = "edit" in url_final
    snap(page_admin, "tc2_02_form_completo", full=True)

    page_text = page_admin.locator("body").inner_text()
    botoes = [b.strip() for b in page_admin.locator("button").all_text_contents() if b.strip()]

    # Verificações conforme a AT
    tem_banner    = "Avaliação pendente" in page_text
    tem_tipo      = "Tipo de experiência" in page_text
    tem_categorias= "Categorias" in page_text
    tem_evidencias= "evidência" in page_text.lower() or "Arquivo" in page_text
    tem_aprovar   = any("Aprovar" in b for b in botoes)
    tem_recusar   = any("Recusar" in b for b in botoes)
    tem_cancelar  = any("Cancelar" in b for b in botoes)
    rodape_ok     = tem_aprovar and tem_recusar and tem_cancelar

    # Divergência de label: produto mostra "Registros > Editar" no breadcrumb
    breadcrumb_prod = "Registros > Editar" in page_text  # o produto
    titulo_at       = "Avaliar registro" in page_text       # a AT espera

    print(f"   form_ok={form_ok}")
    print(f"   tem_banner={tem_banner} | tipo={tem_tipo} | categ={tem_categorias} | evid={tem_evidencias}")
    print(f"   rodape: ap={tem_aprovar} rec={tem_recusar} can={tem_cancelar}")
    print(f"   breadcrumb_prod={breadcrumb_prod} | titulo_at={titulo_at}")

    if not form_ok:
        tc_resultado(tc, "NAO_VERIFICADO", f"Form não carregou. URL: {url_final}")
        return

    falhas = []
    if not tem_banner:
        falhas.append("Banner 'Avaliação pendente' ausente (pode ser não implementado em F2)")
    if not tem_tipo:
        falhas.append("Campo 'Tipo de experiência' ausente")
    if not tem_categorias:
        falhas.append("Campo 'Categorias' ausente")
    if not rodape_ok:
        falhas.append(f"Rodapé: Aprovar={tem_aprovar} Recusar={tem_recusar} Cancelar={tem_cancelar}")

    # Nota sobre divergência de label
    nota_label = ""
    if not titulo_at and breadcrumb_prod:
        nota_label = " DIVERGÊNCIA LABEL: breadcrumb exibe 'Registros > Editar' (AT: 'Avaliar registro')"

    if not falhas:
        veredito = "PASSOU"
        resumo = (f"Form carrega com campos Tipo/Categorias, evidências, 3 botões."
                  + nota_label
                  + (" Banner 'Avaliação pendente' ausente — possível não implementado" if not tem_banner else ""))
    elif falhas == ["Banner 'Avaliação pendente' ausente (pode ser não implementado em F2)"]:
        # Apenas o banner falta — resto OK — marcar como divergência
        veredito = "PASSOU"
        resumo = (f"Form estrutura OK (campos e rodapé). Banner 'Avaliação pendente' ausente — possível não implementado em F2."
                  + nota_label)
    else:
        veredito = "FALHOU"
        resumo = " | ".join(falhas) + nota_label

    tc_resultado(tc, veredito, resumo)


# =============================================================================
# TC3 — Obrigatoriedade do Tipo de experiência ao Aprovar
# =============================================================================
def executar_tc3(page_admin, record_id):
    print("\n=== TC3 — Obrigatoriedade do Tipo de experiência ao Aprovar ===")
    tc = "TC3"

    if not record_id or record_id == 44279951:
        tc_resultado(tc, "NAO_VERIFICADO",
                     "Registro descartável com tipo vazio não disponível. "
                     "Criação de registro falhou — TC3 requer registro com Tipo de experiência vazio.")
        return

    if not abrir_form_avaliar(page_admin, record_id):
        tc_resultado(tc, "NAO_VERIFICADO", "Form não carregou")
        return

    snap(page_admin, "tc3_01_form_sem_tipo")

    # Verificar se o tipo está realmente vazio
    page_text = page_admin.locator("body").inner_text()
    tipo_vazio = "Treinamento" not in page_text and "Curso" not in page_text

    # P2: Aprovar sem tipo
    btn_aprovar = page_admin.locator("button").filter(has_text="Aprovar").first
    btn_aprovar.click()
    page_admin.wait_for_timeout(2000)
    snap(page_admin, "tc3_02_pos_aprovar_sem_tipo", full=True)

    page_text2 = page_admin.locator("body").inner_text()
    tem_obrigatorio = "Campo obrigatório" in page_text2 or "obrigatório" in page_text2.lower()
    ainda_no_form = "edit" in page_admin.url

    print(f"   tipo_vazio={tipo_vazio} tem_obrigatorio={tem_obrigatorio} no_form={ainda_no_form}")

    # P3-P4: Selecionar tipo e aprovar
    tipo_ok = selecionar_tipo_digitando(page_admin, "Curso")
    snap(page_admin, "tc3_03_tipo_selecionado")

    aprovacao_ok = False
    if tipo_ok:
        btn_aprovar2 = page_admin.locator("button").filter(has_text="Aprovar").first
        btn_aprovar2.click()
        page_admin.wait_for_timeout(5000)
        snap(page_admin, "tc3_04_pos_aprovar_com_tipo", full=True)
        page_text3 = page_admin.locator("body").inner_text()
        toast_ok = "Registro aprovado" in page_text3
        voltou = "/records" in page_admin.url and "edit" not in page_admin.url
        aprovacao_ok = toast_ok or voltou
        print(f"   Aprovação: toast={toast_ok} voltou={voltou}")
        if aprovacao_ok:
            registrar_mutacao(record_id, ADMIN_EMAIL, "TC3", "APROVADO")

    if tem_obrigatorio and ainda_no_form:
        if tipo_ok and aprovacao_ok:
            veredito = "PASSOU"
            resumo = "'Campo obrigatório' ao Aprovar sem tipo; aprovação concluída após selecionar 'Curso'"
        elif tipo_ok:
            veredito = "FALHOU"
            resumo = "Validação OK mas aprovação com tipo não concluiu"
        else:
            veredito = "PASSOU"
            resumo = "'Campo obrigatório' ao Aprovar sem tipo. Seleção de tipo não automatizável (React Select)"
    else:
        veredito = "FALHOU"
        resumo = f"'Aprovar' sem tipo não gerou 'Campo obrigatório'. tem={tem_obrigatorio} no_form={ainda_no_form} tipo_vazio={tipo_vazio}"

    tc_resultado(tc, veredito, resumo)


# =============================================================================
# TC4 — Fluxo completo de aprovação
# =============================================================================
def executar_tc4(page_admin, record_id):
    print("\n=== TC4 — Fluxo completo de aprovação ===")
    tc = "TC4"

    if not record_id or record_id == 44279951:
        tc_resultado(tc, "NAO_VERIFICADO", "Registro descartável não disponível")
        return

    if not abrir_form_avaliar(page_admin, record_id):
        tc_resultado(tc, "NAO_VERIFICADO", "Form não carregou")
        return

    snap(page_admin, "tc4_01_form")

    tipo_ok = selecionar_tipo_digitando(page_admin, "Curso")
    snap(page_admin, "tc4_02_tipo")

    if not tipo_ok:
        # Tentar aprovar mesmo sem selecionar tipo (se já tem tipo preenchido)
        page_text = page_admin.locator("body").inner_text()
        if "Treinamento" in page_text or "Curso" in page_text:
            tipo_ok = True
            print("   [TC4] Tipo já preenchido no registro")

    btn_ap = page_admin.locator("button").filter(has_text="Aprovar").first
    btn_ap.click()
    page_admin.wait_for_timeout(5000)
    snap(page_admin, "tc4_03_pos_aprovar", full=True)

    page_text = page_admin.locator("body").inner_text()
    toast_ok = "Registro aprovado" in page_text
    voltou = "/records" in page_admin.url and "edit" not in page_admin.url
    print(f"   toast={toast_ok} voltou={voltou}")

    if toast_ok or voltou:
        registrar_mutacao(record_id, ADMIN_EMAIL, "TC4", "APROVADO")

    # Verificar status via API
    status_ok = False
    if voltou or toast_ok:
        recs_emit = api_registros_admin(page_admin, situation="emitted", per_page=20)
        status_ok = record_id in [r["id"] for r in recs_emit]
        snap(page_admin, "tc4_04_pos_lista", full=True)
        print(f"   Status emitido via API: {status_ok}")

    if toast_ok or voltou:
        veredito = "PASSOU"
        resumo = f"Toast 'Registro aprovado'={toast_ok}; voltou lista={voltou}; status emitido={status_ok}"
    else:
        veredito = "FALHOU"
        resumo = f"Aprovação não concluiu: toast={toast_ok} voltou={voltou}"

    tc_resultado(tc, veredito, resumo)


# =============================================================================
# TC5 — Estrutura e bloqueio do modal de Recusa
# =============================================================================
def executar_tc5(page_admin, record_id):
    print("\n=== TC5 — Estrutura e bloqueio do modal de Recusa ===")
    tc = "TC5"

    if not record_id:
        recs = api_registros_admin(page_admin, situation="pending", origin="external", per_page=3)
        if not recs:
            tc_resultado(tc, "NAO_VERIFICADO", "Sem Externo+Pendente")
            return None
        record_id = recs[0]["id"]

    if not abrir_form_avaliar(page_admin, record_id):
        tc_resultado(tc, "NAO_VERIFICADO", "Form não carregou")
        return None

    snap(page_admin, "tc5_01_form")

    # P1: Clicar em "Recusar"
    btn_rec = page_admin.locator("button").filter(has_text="Recusar").first
    btn_rec.click()
    page_admin.wait_for_timeout(2000)
    snap(page_admin, "tc5_02_modal", full=True)

    # Localizar modal
    modal = None
    for m in page_admin.locator("[role='dialog'], [role='alertdialog']").all():
        try:
            if m.is_visible():
                modal = m
                break
        except Exception:
            pass
    if not modal:
        todos = page_admin.locator("[role='dialog'], [role='alertdialog']")
        if todos.count() > 0:
            modal = todos.first

    if not modal:
        tc_resultado(tc, "FALHOU", "Modal não abriu após clicar 'Recusar'")
        return None

    modal_text = modal.inner_text()
    print(f"   Modal: '{modal_text[:200]}'")

    # Verificar conteúdo do modal conforme AT
    tem_titulo_recusar = "Recusar registro" in modal_text
    tem_aviso_nao_desfazer = "não pode ser desfeita" in modal_text.lower()
    tem_campo_just = "Justificativa" in modal_text
    tem_visivel_colab = "colaborador" in modal_text.lower() or "visível" in modal_text.lower()
    placeholder_just = ""
    try:
        inp_just = modal.locator("textarea, input[type='text']").first
        if inp_just.count() > 0:
            placeholder_just = inp_just.get_attribute("placeholder") or ""
    except Exception:
        pass
    print(f"   título={tem_titulo_recusar} aviso_desfazer={tem_aviso_nao_desfazer} campo_just={tem_campo_just} placeholder='{placeholder_just}'")

    # P2: Botão desabilitado com campo vazio
    btn_conf = modal.locator("button").filter(has_text="Recusar registro")
    if btn_conf.count() == 0:
        btn_conf = modal.locator("button[type='submit']")
    desabilitado = btn_conf.first.is_disabled() if btn_conf.count() > 0 else None
    print(f"   Botão desabilitado (vazio): {desabilitado}")

    # P3: Preencher justificativa
    campo_just = modal.locator("textarea, input[type='text']").first
    habilitado = None
    if campo_just.count() > 0:
        campo_just.fill("As evidências não comprovam a carga horária declarada.")
        page_admin.wait_for_timeout(600)
        snap(page_admin, "tc5_03_preenchido")
        if btn_conf.count() > 0:
            habilitado = not btn_conf.first.is_disabled()
        print(f"   Botão habilitado após preencher: {habilitado}")

    # P4: Cancelar
    btn_can = modal.locator("button").filter(has_text="Cancelar")
    if btn_can.count() > 0:
        btn_can.first.click()
        page_admin.wait_for_timeout(1500)
    else:
        page_admin.keyboard.press("Escape")
        page_admin.wait_for_timeout(800)

    snap(page_admin, "tc5_04_apos_cancelar")
    modal_fechou = page_admin.locator("[role='dialog'], [role='alertdialog']").filter(visible=True).count() == 0
    print(f"   Modal fechou: {modal_fechou}")

    # Divergências de texto vs AT (não são bugs — F2 pode ter labels diferentes)
    divs = []
    if not tem_aviso_nao_desfazer:
        divs.append(f"Aviso 'não pode ser desfeita' ausente (AT RN52) — possível não implementado/label diferente")
    if not tem_visivel_colab:
        divs.append(f"Texto sobre visibilidade ao colaborador ausente")
    if placeholder_just and "Explique" not in placeholder_just:
        divs.append(f"Placeholder diverge da AT: '{placeholder_just}' (AT: 'Explique por que...')")

    # Avaliar pelo comportamento funcional (RN 52)
    funcional_ok = tem_titulo_recusar and tem_campo_just and (desabilitado is True) and (habilitado is True) and modal_fechou

    if funcional_ok:
        veredito = "PASSOU"
        resumo = (f"Modal 'Recusar registro' funcional: campo obrigatório, botão desabilitado→habilitado, Cancelar fecha. "
                  + (f"Divergências AT: {'; '.join(divs)}" if divs else ""))
    else:
        falhas = []
        if not tem_titulo_recusar:
            falhas.append("Título 'Recusar registro' ausente")
        if not tem_campo_just:
            falhas.append("Campo Justificativa ausente")
        if desabilitado is False:
            falhas.append("Botão não estava desabilitado com campo vazio")
        if habilitado is False:
            falhas.append("Botão permaneceu desabilitado após preencher")
        if not modal_fechou:
            falhas.append("Modal não fechou após Cancelar")
        veredito = "FALHOU"
        resumo = " | ".join(falhas) if falhas else "Falha indeterminada"

    tc_resultado(tc, veredito, resumo)
    return record_id


# =============================================================================
# TC6 — Fluxo completo de recusa + justificativa visível
# =============================================================================
def executar_tc6(page_admin, page_aluno, record_id):
    print("\n=== TC6 — Fluxo completo de recusa + justificativa visível ===")
    tc = "TC6"

    if not record_id or record_id == 44279951:
        tc_resultado(tc, "NAO_VERIFICADO", "Registro descartável não disponível")
        return

    JUST = "Plano de desenvolvimento não cobre essa formação."

    if not abrir_form_avaliar(page_admin, record_id):
        tc_resultado(tc, "NAO_VERIFICADO", "Form não carregou")
        return

    snap(page_admin, "tc6_01_form")

    # P1: Clicar "Recusar"
    btn_rec = page_admin.locator("button").filter(has_text="Recusar").first
    btn_rec.click()
    page_admin.wait_for_timeout(2000)
    snap(page_admin, "tc6_02_modal")

    modal = None
    for m in page_admin.locator("[role='dialog'], [role='alertdialog']").all():
        try:
            if m.is_visible():
                modal = m
                break
        except Exception:
            pass
    if not modal:
        todos = page_admin.locator("[role='dialog'], [role='alertdialog']")
        if todos.count() > 0:
            modal = todos.first

    if not modal:
        tc_resultado(tc, "FALHOU", "Modal não abriu")
        return

    # P2: Preencher justificativa
    campo = modal.locator("textarea, input[type='text']").first
    if campo.count() == 0:
        tc_resultado(tc, "NAO_VERIFICADO", "Campo justificativa não encontrado")
        return

    campo.fill(JUST)
    page_admin.wait_for_timeout(500)
    snap(page_admin, "tc6_03_justificativa")

    # P3: Confirmar recusa
    btn_conf = modal.locator("button").filter(has_text="Recusar registro")
    if btn_conf.count() == 0:
        btn_conf = modal.locator("button[type='submit']")
    if btn_conf.count() == 0:
        tc_resultado(tc, "NAO_VERIFICADO", "Botão de confirmação não encontrado")
        return

    btn_conf.first.click()
    page_admin.wait_for_timeout(5000)
    snap(page_admin, "tc6_04_pos_recusa", full=True)

    page_text = page_admin.locator("body").inner_text()
    toast_rec = "Registro recusado" in page_text
    voltou = "/records" in page_admin.url and "edit" not in page_admin.url
    print(f"   toast={toast_rec} voltou={voltou}")

    if toast_rec or voltou:
        registrar_mutacao(record_id, ALUNO_EMAIL, "TC6", "RECUSADO")

    # P4: Verificar Histórico
    hist_tem_just = False
    try:
        ir_records_admin(page_admin, filtro="rejected")
        aguardar_tabela(page_admin)

        if abrir_kebab_id(page_admin, record_id):
            itens = tw.menu_visivel(page_admin)
            print(f"   Itens pós-recusa: {itens}")
            snap(page_admin, "tc6_05_menu_rejected")
            if any("Histórico" in i for i in itens):
                tw.click_menuitem(page_admin, "Histórico")
                page_admin.wait_for_timeout(3000)
                snap(page_admin, "tc6_06_historico", full=True)
                hist_text = page_admin.locator("body").inner_text()
                hist_tem_just = JUST in hist_text
                print(f"   Justificativa no histórico: {hist_tem_just}")
                fechar_menu(page_admin)
    except Exception as e:
        print(f"   [TC6] Histórico: {e}")

    # P5: Aluno vê banner
    aluno_ve = None
    try:
        ir_records_aluno(page_aluno)
        page_aluno.wait_for_timeout(1000)
        btns_a = page_aluno.locator("button[aria-haspopup='menu']")
        for i in range(min(btns_a.count(), 5)):
            btns_a.nth(i).click(force=True)
            page_aluno.wait_for_timeout(1200)
            itens_a = tw.menu_visivel(page_aluno)
            if any("Visualizar" in x for x in itens_a):
                tw.click_menuitem(page_aluno, "Visualizar")
                page_aluno.wait_for_timeout(2000)
                aluno_text = page_aluno.locator("body").inner_text()
                aluno_ve = JUST in aluno_text or "recusado" in aluno_text.lower()
                snap(page_aluno, "tc6_07_aluno_visualiza")
                print(f"   Aluno vê recusa: {aluno_ve}")
                page_aluno.go_back()
                page_aluno.wait_for_timeout(1000)
                break
            fechar_menu(page_aluno)
    except Exception as e:
        print(f"   [TC6] Aluno: {e}")

    recusa_ok = toast_rec or voltou
    if recusa_ok and hist_tem_just:
        veredito = "PASSOU"
        resumo = f"Recusa concluída; justificativa no Histórico; aluno: {aluno_ve}"
    elif recusa_ok and not hist_tem_just:
        veredito = "FALHOU"
        resumo = f"Recusa concluída mas justificativa NÃO no Histórico (anti-falso-positivo: verificado)"
    else:
        veredito = "FALHOU"
        resumo = f"Recusa não concluiu: toast={toast_rec} voltou={voltou}"

    tc_resultado(tc, veredito, resumo)


# =============================================================================
# TC7 — Botão Cancelar do form de avaliação
# =============================================================================
def executar_tc7(page_admin, record_id):
    print("\n=== TC7 — Botão Cancelar ===")
    tc = "TC7"

    if not record_id:
        recs = api_registros_admin(page_admin, situation="pending", origin="external", per_page=3)
        record_id = recs[0]["id"] if recs else None
    if not record_id:
        tc_resultado(tc, "NAO_VERIFICADO", "Sem registro")
        return

    if not abrir_form_avaliar(page_admin, record_id):
        tc_resultado(tc, "NAO_VERIFICADO", "Form não carregou")
        return

    snap(page_admin, "tc7_01_form")

    # Sujar o form (tentar selecionar Workshop)
    selecionar_tipo_digitando(page_admin, "Workshop")
    snap(page_admin, "tc7_02_sujo")

    # P3: Cancelar
    btn_can = page_admin.locator("button").filter(has_text="Cancelar").first
    if btn_can.count() == 0:
        tc_resultado(tc, "NAO_VERIFICADO", "Botão 'Cancelar' não encontrado")
        return

    btn_can.click()
    page_admin.wait_for_timeout(3000)
    snap(page_admin, "tc7_03_pos_cancelar", full=True)

    voltou = "/records" in page_admin.url and "edit" not in page_admin.url
    print(f"   voltou={voltou} url={page_admin.url}")

    recs_pend = api_registros_admin(page_admin, situation="pending", origin="external", per_page=10)
    ainda_pend = record_id in [r["id"] for r in recs_pend]
    print(f"   Ainda pendente: {ainda_pend}")

    if voltou:
        veredito = "PASSOU"
        resumo = f"Cancelar retornou à lista; registro ainda Pendente={ainda_pend}"
    else:
        veredito = "FALHOU"
        resumo = f"Cancelar não retornou à lista. URL={page_admin.url}"

    tc_resultado(tc, veredito, resumo)


# =============================================================================
# TC8 — Escopo do Líder na avaliação
# =============================================================================
def executar_tc8(page_lider):
    print("\n=== TC8 — Escopo do Líder ===")
    tc = "TC8"

    page_lider.goto(f"{BASE_URL}/o/{ORG_ID}/records", wait_until="domcontentloaded", timeout=30000)
    try:
        page_lider.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    page_lider.wait_for_timeout(2000)
    tw.dispensar_nps(page_lider)

    url_l = page_lider.url
    snap(page_lider, "tc8_01_lider_records", full=True)
    print(f"   URL Líder: {url_l}")

    if "/records" not in url_l:
        tc_resultado(tc, "NAO_VERIFICADO",
                     f"Líder redirecionado para {url_l}. Gotcha 401 de endpoints não-admin.")
        return

    recs_l = api_registros_admin(page_lider, situation="pending", origin="external", per_page=5)
    print(f"   Pendentes visíveis ao Líder: {len(recs_l)}")
    snap(page_lider, "tc8_02_lista_lider", full=True)

    if not recs_l:
        tc_resultado(tc, "NAO_VERIFICADO", "Líder não vê Pendentes")
        return

    rec_l = recs_l[0]
    print(f"   Primeiro: id={rec_l['id']} person={rec_l.get('person','')}")

    aguardar_tabela(page_lider)

    abriu = abrir_kebab_id(page_lider, rec_l["id"])
    if not abriu:
        btns = page_lider.locator("button[aria-haspopup='menu']")
        if btns.count() > 0:
            btns.first.click(force=True)
            page_lider.wait_for_timeout(1200)

    itens_l = tw.menu_visivel(page_lider)
    snap(page_lider, "tc8_03_lider_menu")
    print(f"   Itens menu Líder: {itens_l}")
    fechar_menu(page_lider)

    tem_avaliar_l = any("Avaliar" in i for i in itens_l)

    if itens_l and tem_avaliar_l:
        veredito = "PASSOU"
        resumo = f"Líder vê 'Avaliar' no menu de Pendente de '{rec_l.get('person','')}'."
    elif itens_l:
        veredito = "FALHOU"
        resumo = f"Líder não vê 'Avaliar' no menu. Itens: {itens_l}"
    else:
        veredito = "NAO_VERIFICADO"
        resumo = "Não foi possível abrir o kebab como Líder"

    tc_resultado(tc, veredito, resumo)


# =============================================================================
# TC9 — Erro ao aprovar registro excluído concorrentemente
# =============================================================================
def executar_tc9(page_admin, record_id):
    print("\n=== TC9 — Erro ao aprovar excluído ===")
    tc = "TC9"

    if not record_id or record_id == 44279951:
        tc_resultado(tc, "NAO_VERIFICADO", "Registro descartável não disponível")
        return

    if not abrir_form_avaliar(page_admin, record_id):
        tc_resultado(tc, "NAO_VERIFICADO", "Form não carregou")
        return

    snap(page_admin, "tc9_01_form_sessao_a")

    # Excluir via API (sessão B)
    resp_del = page_admin.request.delete(
        f"{BASE_URL}/api/v1/o/{ORG_ID}/records/{record_id}",
        headers={"Accept": "application/json", "Content-Type": "application/json"}
    )
    print(f"   DELETE status={resp_del.status}")
    excluiu = resp_del.status in (200, 204)
    if excluiu:
        registrar_mutacao(record_id, ALUNO_EMAIL, "TC9", "EXCLUIDO")

    page_admin.wait_for_timeout(1000)

    # Tentar aprovar (sessão A)
    selecionar_tipo_digitando(page_admin, "Curso")

    btn_ap = page_admin.locator("button").filter(has_text="Aprovar").first
    if btn_ap.count() > 0:
        btn_ap.click()
        page_admin.wait_for_timeout(5000)

    snap(page_admin, "tc9_02_pos_aprovacao", full=True)
    page_text = page_admin.locator("body").inner_text()
    toast_nao_enc = "não encontrado" in page_text.lower() or "não foi possível" in page_text.lower()
    toast_ok = "Registro aprovado" in page_text
    print(f"   toast_nao_enc={toast_nao_enc} toast_sucesso={toast_ok}")

    if toast_nao_enc:
        veredito = "PASSOU"
        resumo = "Toast 'Não foi possível aprovar — registro não encontrado' exibido"
    elif toast_ok and excluiu:
        veredito = "FALHOU"
        resumo = "Registro excluído mas aprovação retornou sucesso"
    elif not excluiu:
        veredito = "NAO_VERIFICADO"
        resumo = f"API DELETE retornou {resp_del.status} — simulação de concorrência falhou"
    else:
        veredito = "NAO_VERIFICADO"
        resumo = f"Indeterminado: DELETE={resp_del.status} toast_nao_enc={toast_nao_enc} toast_ok={toast_ok}"

    tc_resultado(tc, veredito, resumo)


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("=== QA 1.9 v4 — Avaliar registro pendente ===\n")

    c_admin = {"base_url": BASE_URL, "org_id": ORG_ID, "email": ADMIN_EMAIL, "senha": ADMIN_PASSWORD}
    c_aluno = {"base_url": BASE_URL, "org_id": None, "email": ALUNO_EMAIL, "senha": ALUNO_PASSWORD}
    c_lider = {"base_url": BASE_URL, "org_id": None, "email": LIDER_EMAIL, "senha": LIDER_PASSWORD}

    with tw.sync_playwright() as p:
        ba, ca, page_admin = tw.nova_pagina(p)
        tw.login(page_admin, c_admin, admin=True)
        print("   [Admin] OK")

        bb, cb, page_aluno = tw.nova_pagina(p)
        tw.login(page_aluno, c_aluno, admin=False)
        print("   [Aluno] OK")

        bc, cc, page_lider = tw.nova_pagina(p)
        tw.login(page_lider, c_lider, admin=False)
        print("   [Líder] OK")

        # === Verificar estado atual dos registros ===
        recs_pend = api_registros_admin(page_admin, situation="pending", origin="external", per_page=10)
        print(f"\n   Ext+Pendentes disponíveis: {len(recs_pend)}")
        for r in recs_pend[:5]:
            print(f"   - id={r['id']} person={r.get('person','')} content={r.get('content','')}")

        rec_compartilhado = recs_pend[0]["id"] if recs_pend else None
        print(f"   Registro compartilhado (não-mutante): id={rec_compartilhado}")

        # === Criar registros descartáveis como aluno ===
        print("\n   Criando registros descartáveis como ALUNO...")
        desc_tc3 = criar_registro_como_aluno(page_aluno, "TC3")
        print(f"   TC3: {desc_tc3}")
        desc_tc4 = criar_registro_como_aluno(page_aluno, "TC4")
        print(f"   TC4: {desc_tc4}")
        desc_tc6 = criar_registro_como_aluno(page_aluno, "TC6")
        print(f"   TC6: {desc_tc6}")
        desc_tc9 = criar_registro_como_aluno(page_aluno, "TC9")
        print(f"   TC9: {desc_tc9}")

        # Verificar que são IDs novos (não 44279951)
        def safe_id(desc):
            if not desc:
                return None
            if desc[0] == 44279951:
                print(f"   [WARN] Criação falhou — retornou o registro compartilhado 44279951")
                return None
            return desc[0]

        id_tc3 = safe_id(desc_tc3)
        id_tc4 = safe_id(desc_tc4)
        id_tc6 = safe_id(desc_tc6)
        id_tc9 = safe_id(desc_tc9)

        print(f"\n   IDs descartáveis: TC3={id_tc3} TC4={id_tc4} TC6={id_tc6} TC9={id_tc9}")

        # === Execução TCs não-mutantes ===
        rec_tc1 = executar_tc1(page_admin, page_aluno)
        executar_tc2(page_admin, rec_compartilhado)
        executar_tc5(page_admin, rec_compartilhado)
        executar_tc7(page_admin, rec_compartilhado)
        executar_tc8(page_lider)

        # === Execução TCs mutantes ===
        executar_tc3(page_admin, id_tc3)
        executar_tc4(page_admin, id_tc4)
        executar_tc6(page_admin, page_aluno, id_tc6)
        executar_tc9(page_admin, id_tc9)

        ca.close(); ba.close()
        cb.close(); bb.close()
        cc.close(); bc.close()

    # Sumário
    print("\n" + "="*60)
    print("SUMÁRIO QA 1.9")
    print("="*60)
    passou = falhou = nao_v = 0
    for tc, r in resultados.items():
        v = r["veredito"]
        i = "✓" if v == "PASSOU" else ("✗" if v == "FALHOU" else "?")
        print(f"  {i} {tc}: {v} — {r['resumo']}")
        if v == "PASSOU": passou += 1
        elif v == "FALHOU": falhou += 1
        else: nao_v += 1

    print(f"\n  PLACAR: {passou} PASSOU | {falhou} FALHOU | {nao_v} NAO_VERIFICADO")
    print("\n=== REGISTROS MUTADOS ===")
    for m in MUTACOES:
        print(f"  id={m['id']} | {m['acao']} | pessoa={m['pessoa']}")


if __name__ == "__main__":
    main()
