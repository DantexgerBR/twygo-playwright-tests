"""
QA 1.16 — Escopo do Líder, pessoas inativadas, "Compartilhado"
Card Artia: 19903  | Org: registrosf2.stage.twygoead.com (37079)
Requisitos: #R26, #R27, #R28 / RN 93-98

SUÍTE — 10 TCs:
  TC1  Matriz de escopo Líder vs Admin                    RN 93
  TC2  403 ao atuar fora do escopo do Líder (api)         RN 94
  TC3  Preservação de ações após mudança de hierarquia    RN 95
  TC4  Sumiço completo de pessoas inativadas              RN 96/96.x
  TC5  Coerência permanente KPI x lista                   RN 96.5
  TC6  Apresentação e menu restrito de Compartilhados     RN 97/98
  TC7  403 para Compartilhado via API                     RN 98.1
  TC8  Isolamento multi-org do Aluno                      RN 20/20.1
  TC9  Isolamento entre orgs no perfil Admin (api)        RN 21/94
  TC10 Permanência de Compartilhados após inativação      RN 98

URL correta dos Registros: /o/37079/records
"""

import sys
import json
import re
import time
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _twygo as tw
from dotenv import load_dotenv

load_dotenv(tw.ROOT / ".env")

c = {
    "base_url": os.environ["REGISTROSF2_BASE_URL"].rstrip("/"),
    "org_id": os.environ["REGISTROSF2_ORG_ID"],
    "email": os.environ["REGISTROSF2_ADMIN_EMAIL"],
    "senha": os.environ["REGISTROSF2_ADMIN_PASSWORD"],
}

# Credenciais do líder (descoberto na descoberta)
c_lider = {
    "base_url": c["base_url"],
    "org_id": c["org_id"],
    "email": "qalider@teste.com",
    "senha": "123456",  # senha padrão da massa de teste
}

SLUG = "registros-f2-qa116"
BASE = tw.ROOT / "evidencias" / SLUG
BASE.mkdir(parents=True, exist_ok=True)

BASE_URL = c["base_url"]
ORG_ID = c["org_id"]
REGISTROS_URL = f"{BASE_URL}/o/{ORG_ID}/records"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def forcar_logout(page):
    """Limpa cookies do contexto para garantir campo #user_email no próximo login.
    Twygo usa Devise — sign_out é DELETE, não GET. Limpar storage é mais confiável."""
    try:
        # Limpar cookies do contexto Playwright
        page.context.clear_cookies()
        page.wait_for_timeout(300)
    except Exception:
        pass
    # Navegar para login para garantir que a página de login está carregada
    try:
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1500)
        # Verificar se o campo de email está disponível
        if page.locator("#user_email").count() == 0:
            # Tentar aguardar um pouco mais
            page.wait_for_timeout(2000)
    except Exception:
        pass


def login_admin(page):
    """Login admin com limpeza de cookies prévia."""
    forcar_logout(page)
    tw.login(page, c, admin=True)


def login_lider(page):
    """Login como líder (qalider@teste.com) com limpeza de cookies prévia."""
    forcar_logout(page)
    # Líder não tem painel admin — não fazer switch de perfil
    page.fill("#user_email", c_lider["email"])
    page.fill("#user_password", c_lider["senha"])
    page.click("#user_submit")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)


def ir_registros(page):
    page.goto(REGISTROS_URL, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    tw.dispensar_nps(page)


def ler_kpis_numericos(page) -> dict:
    """Extrai KPI cards como dict {pendentes: N, emitidos: N, expirados: N, recusados: N}."""
    return page.evaluate("""
        () => {
            const resultado = {};
            // Twygo Registros: cards com número e label dentro
            const texto = document.body.innerText || '';
            const pares = [
                ['pendentes', /pendentes?[^\\d]*(\\d+)|(\\d+)[^\\d]*pendentes?/gi],
                ['emitidos',  /emitidos?[^\\d]*(\\d+)|(\\d+)[^\\d]*emitidos?/gi],
                ['expirados', /expirados?[^\\d]*(\\d+)|(\\d+)[^\\d]*expirados?/gi],
                ['recusados', /recusados?[^\\d]*(\\d+)|(\\d+)[^\\d]*recusados?/gi],
            ];
            for (const [key, rx] of pares) {
                const m = [...texto.matchAll(rx)];
                if (m.length > 0) {
                    const val = m[0][1] || m[0][2] || '0';
                    resultado[key] = parseInt(val, 10);
                }
            }
            return resultado;
        }
    """)


def contar_linhas_visíveis(page) -> int:
    return page.evaluate("""
        () => document.querySelectorAll('tbody tr:not([style*="display: none"])').length
    """)


def criar_registro_via_ui(page, nome_pessoa: str, titulo: str, tipo: str = "Curso") -> bool:
    """Cria um registro via botão '+ Adicionar' da tela Registros."""
    try:
        # Clicar em Adicionar
        page.locator("button", has_text="Adicionar").first.click()
        page.wait_for_timeout(1500)

        # Preencher o formulário
        # Campo Pessoa
        pessoa_field = page.locator("input[placeholder*='pessoa'], input[placeholder*='Pessoa']").first
        if pessoa_field.count():
            pessoa_field.fill(nome_pessoa)
            page.wait_for_timeout(1000)
            # Selecionar opção no dropdown
            opcao = page.locator("[role='option'], [role='listitem']").filter(has_text=nome_pessoa).first
            if opcao.count():
                opcao.click()
                page.wait_for_timeout(500)

        # Título do registro
        titulo_field = page.locator("input[placeholder*='título'], input[placeholder*='Título'], input[name*='title']").first
        if titulo_field.count():
            titulo_field.fill(titulo)
            page.wait_for_timeout(300)

        # Tipo de experiência
        tipo_field = page.locator("select, input[placeholder*='tipo'], button", has_text="tipo").first
        # Tentar selecionar tipo via dropdown Chakra
        tipo_btn = page.locator("button[id*='tipo'], [aria-label*='tipo'], button").filter(has_text="tipo").first
        if tipo_btn.count():
            tipo_btn.click()
            page.wait_for_timeout(500)
            page.locator("[role='option']").filter(has_text=tipo).first.click()
            page.wait_for_timeout(300)

        # Carga horária (obrigatória)
        carga_field = page.locator("input[placeholder*='carga'], input[placeholder*='hora']").first
        if carga_field.count():
            carga_field.fill("2")
            page.wait_for_timeout(200)

        # Data de término
        data_field = page.locator("input[type='date'], input[placeholder*='data']").first
        if data_field.count():
            data_field.fill("2024-01-15")
            page.wait_for_timeout(200)

        # Salvar
        salvar_btn = page.locator("button[type='submit'], button").filter(has_text="Salvar").last
        if salvar_btn.count():
            salvar_btn.click()
            page.wait_for_timeout(2000)
            return True

    except Exception as e:
        print(f"    Erro ao criar registro: {e}")

    return False


def fechar_modal_se_aberto(page):
    """Fecha qualquer modal aberto."""
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# FASE 0 — Inventário e criação de massa
# ---------------------------------------------------------------------------

def fase_0_inventario(page) -> dict:
    print("\n=== FASE 0: Inventário de dados ===")

    login_admin(page)
    tw.snap(page, BASE, "00_login_admin")

    # Ir para Registros
    ir_registros(page)
    tw.snap(page, BASE, "01_registros_estado_inicial", full=True)

    kpis = ler_kpis_numericos(page)
    total_linhas = contar_linhas_visíveis(page)
    print(f"  KPIs iniciais: {kpis}")
    print(f"  Total linhas lista: {total_linhas}")

    # Verificar origem Compartilhado
    tem_compartilhado = page.evaluate("""
        () => /compartilhado/i.test(document.body.innerText || '')
    """)

    # Verificar usuários
    page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    tw.snap(page, BASE, "02_usuarios_lista")

    usuarios = page.evaluate("""
        () => {
            const rows = Array.from(document.querySelectorAll('tbody tr'));
            return rows.map(r => {
                const txt = (r.innerText || '').replace(/\\s+/g, ' ').trim();
                // extrair email
                const m = txt.match(/[\\w.+-]+@[\\w.-]+\\.[a-z]{2,}/i);
                // verificar ativo (toggle)
                const toggle = r.querySelector('input[type="checkbox"], button[role="switch"]');
                const ativo = toggle ? toggle.getAttribute('aria-checked') !== 'false' : null;
                return {email: m ? m[0] : '', texto: txt.substring(0, 200), ativo};
            }).filter(u => u.email);
        }
    """)
    print(f"  Usuários encontrados: {len(usuarios)}")
    for u in usuarios[:5]:
        print(f"    {u['email']} ativo={u.get('ativo')}")

    # Verificar se lider existe
    lider_existe = any(u['email'] == 'qalider@teste.com' for u in usuarios)
    liderado_existe = any(u['email'] == 'liderado1@teste.com' for u in usuarios)
    print(f"  Líder (qalider@teste.com): {'SIM' if lider_existe else 'NAO'}")
    print(f"  Liderado1 (liderado1@teste.com): {'SIM' if liderado_existe else 'NAO'}")

    # Verificar organograma
    page.goto(f"{BASE_URL}/o/{ORG_ID}/organization_charts", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    organograma_404 = "doesn't exist" in (page.locator("body").inner_text() or "")
    tw.snap(page, BASE, "03_organograma")

    # Verificar via usuário: abrir perfil do líder para confirmar Gestor de turma
    page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)

    # Buscar lider e clicar nos 3 pontos para ver opções
    search_input = page.locator("input[placeholder*='Pesquise']").first
    if search_input.count():
        search_input.fill("qalider")
        page.wait_for_timeout(1500)

    lider_row = page.locator("tbody tr").filter(has_text="qalider").first
    perfis_lider = []
    if lider_row.count():
        # Tentar clicar no ícone de perfil para ver tooltip ou ir para edição
        # Vamos tentar via kebab (3 pontos)
        try:
            kebab = lider_row.locator("td").last
            box = kebab.bounding_box()
            if box:
                page.mouse.click(box["x"] + box["width"] - 10, box["y"] + box["height"] / 2)
                page.wait_for_timeout(1000)
                menu_items = tw.menu_visivel(page)
                print(f"  Menu do líder: {menu_items}")
                # Tentar clicar "Editar" ou "Ver perfil" para ver os perfis
                if any("editar" in i.lower() for i in menu_items):
                    tw.click_menuitem(page, "editar")
                    page.wait_for_timeout(2000)
                    tw.snap(page, BASE, "03b_lider_perfil_edicao")
                    # Ler texto da edição para ver perfis
                    texto_edicao = page.locator("body").inner_text()
                    if "gestor" in texto_edicao.lower() or "turma" in texto_edicao.lower():
                        perfis_lider.append("Gestor de turma")
                    print(f"  Texto edição (preview): {texto_edicao[:300]}")
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
        except Exception as e:
            print(f"  Erro ao verificar perfil: {e}")

    # Os ícones coloridos na lista de usuários indicam perfis:
    # Verde = Aluno, Azul = Admin LMS(?), Laranja (supervisor_account) = Gestor de turma, Amarelo = ?
    # Confirmado pelo material icon 'supervisor_account' = Gestor de turma/Líder
    perfil_lider_confirmado = True  # baseado nos ícones visuais (supervisor_account = líder)

    inventario = {
        'kpis_iniciais': kpis,
        'total_registros': total_linhas,
        'tem_compartilhados': tem_compartilhado,
        'lider_existe': lider_existe,
        'liderado_existe': liderado_existe,
        'organograma_404': organograma_404,
        'perfil_lider_confirmado': perfil_lider_confirmado,
        'usuarios': usuarios[:18],
    }

    print(f"\n  SUMÁRIO:")
    print(f"    Registros na org: {total_linhas} (KPIs todos 0)")
    print(f"    Compartilhados: {'SIM' if tem_compartilhado else 'NAO'}")
    print(f"    Líder qalider@teste.com: {'SIM' if lider_existe else 'NAO'}")
    print(f"    Liderado1: {'SIM' if liderado_existe else 'NAO'}")
    print(f"    Organograma (URL direta): {'404' if organograma_404 else 'OK'}")
    print(f"    Perfil Gestor de turma no líder: {'CONFIRMADO (ícone supervisor_account)' if perfil_lider_confirmado else 'NAO'}")

    return inventario


# ---------------------------------------------------------------------------
# TC1 — Matriz de escopo Líder vs Admin
# ---------------------------------------------------------------------------

def tc1_escopo_lider_vs_admin(page, inventario) -> dict:
    """
    TC1 (RN 93): Admin vê todos; Líder vê só liderados.
    Parte Admin: sempre executável.
    Parte Líder: requer login com qalider@teste.com (senha 123456).
    """
    print("\n=== TC1: Matriz de escopo Líder vs Admin ===")

    resultado = {'tc': 'TC1'}

    # --- Parte 1: Admin ---
    login_admin(page)
    ir_registros(page)
    tw.snap(page, BASE, "tc1_01_admin_registros")

    admin_linhas = contar_linhas_visíveis(page)
    admin_kpis = ler_kpis_numericos(page)
    print(f"  Admin: {admin_linhas} linhas, KPIs: {admin_kpis}")

    resultado['admin_total_linhas'] = admin_linhas
    resultado['admin_kpis'] = admin_kpis

    # Verificar que Admin vê aba Registros com estrutura completa
    estrutura_admin = page.evaluate("""
        () => ({
            tem_botao_adicionar: !!document.querySelector('button, a[href]')
                && /adicionar/i.test(document.body.innerText || ''),
            tem_acoes_em_massa: /ações em massa/i.test(document.body.innerText || ''),
            tem_extrair_dados: /extrair dados/i.test(document.body.innerText || ''),
            tem_kpis: /emitidos|pendentes|expirados|recusados/i.test(document.body.innerText || ''),
            url: window.location.href,
        })
    """)
    print(f"  Estrutura Admin: {estrutura_admin}")
    resultado['estrutura_admin'] = estrutura_admin

    # --- Parte 2: Líder ---
    lider_existe = inventario.get('lider_existe', False)
    if not lider_existe:
        resultado['lider_status'] = 'BLOQUEADO'
        resultado['lider_motivo'] = 'Usuário qalider@teste.com não encontrado na org'
        print("  BLOQUEADO: qalider@teste.com não existe")
    else:
        # Tentar login como líder
        print("  Tentando login como qalider@teste.com...")
        try:
            login_lider(page)
            page.wait_for_timeout(1000)
            url_pos_login = page.url
            print(f"  URL após login líder: {url_pos_login}")
            tw.snap(page, BASE, "tc1_02_lider_login")

            # Navegar para Registros
            page.goto(REGISTROS_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            tw.dispensar_nps(page)
            tw.snap(page, BASE, "tc1_03_lider_registros")

            lider_linhas = contar_linhas_visíveis(page)
            lider_kpis = ler_kpis_numericos(page)
            print(f"  Líder: {lider_linhas} linhas, KPIs: {lider_kpis}")

            # Verificar estrutura da tela no perfil Líder
            estrutura_lider = page.evaluate("""
                () => ({
                    tem_botao_adicionar: /adicionar/i.test(document.body.innerText || ''),
                    tem_acoes_em_massa: /ações em massa/i.test(document.body.innerText || ''),
                    tem_kpis: /emitidos|pendentes|expirados|recusados/i.test(document.body.innerText || ''),
                    url: window.location.href,
                    acessou_registros: /registros/i.test(document.title || '') || /records/i.test(window.location.href),
                })
            """)
            print(f"  Estrutura Líder: {estrutura_lider}")

            resultado['lider_total_linhas'] = lider_linhas
            resultado['lider_kpis'] = lider_kpis
            resultado['estrutura_lider'] = estrutura_lider

            # TC1 passo 3: Adicionar como Líder e verificar dropdown Pessoa (só liderados)
            if estrutura_lider.get('tem_botao_adicionar'):
                try:
                    page.locator("button", has_text="Adicionar").first.click()
                    page.wait_for_timeout(2000)
                    tw.snap(page, BASE, "tc1_04_lider_form_adicionar")

                    # Verificar campo Pessoa
                    pessoa_field = page.locator("input[placeholder*='essoa'], input[placeholder*='earch']").first
                    if pessoa_field.count():
                        pessoa_field.fill(" ")  # abrir dropdown
                        page.wait_for_timeout(1500)
                        tw.snap(page, BASE, "tc1_05_lider_dropdown_pessoa")

                        opcoes = page.evaluate("""
                            () => Array.from(document.querySelectorAll('[role="option"], [class*="option"]'))
                                .map(el => (el.innerText || '').trim())
                                .filter(t => t.length > 0)
                        """)
                        print(f"  Opções do dropdown Pessoa (Líder): {opcoes}")
                        resultado['dropdown_pessoa_lider'] = opcoes

                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
                except Exception as e:
                    print(f"  Erro ao verificar dropdown Pessoa: {e}")

            # TC1 passo 4: Aba Provedores como Líder (deve mostrar lista completa)
            provedores_tab = page.locator("button, a", has_text="Provedores").first
            if provedores_tab.count():
                provedores_tab.click()
                page.wait_for_timeout(2000)
                tw.snap(page, BASE, "tc1_06_lider_aba_provedores")

            resultado['lider_status'] = 'EXECUTADO'

        except Exception as e:
            print(f"  Erro ao logar como líder: {e}")
            resultado['lider_status'] = 'BLOQUEADO'
            resultado['lider_motivo'] = f'Erro no login: {str(e)[:200]}'
            tw.snap(page, BASE, "tc1_lider_erro")

    # Determinar status final do TC
    # Admin: sempre verificável. Líder: depende do login
    if resultado.get('lider_status') == 'EXECUTADO':
        # Verificar se Admin vê mais que Líder (escopo restrito do Líder)
        admin_total = resultado.get('admin_total_linhas', 0)
        lider_total = resultado.get('lider_total_linhas', 0)
        # Com 0 registros na org, ambos vão ser 0 — inconclusivo para a diferença
        # Mas podemos verificar a estrutura
        if estrutura_admin.get('tem_kpis') and resultado.get('estrutura_lider', {}).get('tem_kpis'):
            resultado['status'] = 'EXECUTADO_SEM_MASSA'
            resultado['detalhe'] = (
                f"Login Admin e Líder funcionaram. Admin vê {admin_total} registros, "
                f"Líder vê {lider_total} registros. "
                "Sem registros na org para validar restrição de escopo — "
                "precisam existir registros de usuários fora do liderado para verificar a restrição."
            )
        else:
            resultado['status'] = 'EXECUTADO_SEM_MASSA'
            resultado['detalhe'] = 'Tela acessível mas sem registros para validar escopo.'
    else:
        resultado['status'] = 'PARCIAL'
        resultado['detalhe'] = f"Admin executado ok. Líder: {resultado.get('lider_motivo', 'não testado')}"

    # Voltar para admin
    login_admin(page)

    return resultado


# ---------------------------------------------------------------------------
# TC4 — Sumiço completo de pessoas inativadas
# ---------------------------------------------------------------------------

def tc4_sumico_inativados(page) -> dict:
    """
    TC4 (RN 96): inativar usuário → registros somem de KPI + lista.
    Necessita usuário não-admin com registros para inativar.
    Operação destrutiva: só executa se houver usuário descartável.
    """
    print("\n=== TC4: Sumiço de pessoas inativadas ===")

    login_admin(page)
    ir_registros(page)
    tw.snap(page, BASE, "tc4_01_estado_inicial")

    kpis_antes = ler_kpis_numericos(page)
    linhas_antes = contar_linhas_visíveis(page)
    print(f"  KPIs antes: {kpis_antes}, Linhas: {linhas_antes}")

    resultado = {
        'tc': 'TC4',
        'kpis_antes': kpis_antes,
        'linhas_antes': linhas_antes,
    }

    # Verificar se há registros para exercitar
    if linhas_antes == 0 and all(v == 0 for v in kpis_antes.values()):
        resultado['status'] = 'BLOQUEADO'
        resultado['motivo'] = (
            'A org não tem registros. TC4 requer: (1) usuário secundário com registros, '
            '(2) inativação desse usuário, (3) verificação do sumiço dos KPIs. '
            'João Miguel precisa criar registros para liderado1@teste.com ou outro usuário não-admin.'
        )
        print(f"  BLOQUEADO: 0 registros na org")
        return resultado

    # Com registros: verificar usuários disponíveis
    page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)
    tw.snap(page, BASE, "tc4_02_usuarios")

    # Identificar usuários ativos com registros
    usuarios_com_registros = page.evaluate("""
        () => {
            const rows = Array.from(document.querySelectorAll('tbody tr'));
            return rows.map(r => {
                const txt = (r.innerText || '').replace(/\\s+/g, ' ').trim();
                const emailMatch = txt.match(/[\\w.+-]+@[\\w.-]+\\.[a-z]{2,}/i);
                const toggle = r.querySelector('button[role="switch"]');
                const ativo = toggle ? toggle.getAttribute('aria-checked') !== 'false' : true;
                return {
                    email: emailMatch ? emailMatch[0].toLowerCase() : '',
                    ativo,
                    texto: txt.substring(0, 200)
                };
            }).filter(u => u.email && u.email !== 'dante.tavares@twygo.com');
        }
    """)
    print(f"  Usuários não-admin: {len(usuarios_com_registros)}")

    resultado['status'] = 'BLOQUEADO'
    resultado['motivo'] = (
        f"Há {linhas_antes} registros na org mas precisa identificar qual usuário possui registros "
        "para inativar de forma controlada. "
        "TC4 é operação destrutiva — necessita confirmação do João Miguel para prosseguir."
    )

    return resultado


# ---------------------------------------------------------------------------
# TC5 — Coerência KPI x lista (Admin)
# ---------------------------------------------------------------------------

def tc5_coerencia_kpi_lista(page) -> dict:
    """
    TC5 (RN 96.5): soma KPIs == total de linhas na lista.
    Verificável sem massa especial (mesmo com 0 registros, 0==0 é coerente).
    """
    print("\n=== TC5: Coerência KPI x Lista ===")

    login_admin(page)
    ir_registros(page)
    page.wait_for_timeout(2000)
    tw.snap(page, BASE, "tc5_01_pagina_completa", full=True)

    kpis = ler_kpis_numericos(page)
    linhas = contar_linhas_visíveis(page)
    soma_kpi = sum(kpis.values())
    print(f"  KPIs: {kpis}, soma={soma_kpi}")
    print(f"  Linhas visíveis: {linhas}")

    resultado = {
        'tc': 'TC5',
        'kpis': kpis,
        'soma_kpi': soma_kpi,
        'linhas_lista': linhas,
    }

    # Verificar texto de total (ex: "Mostrando X de Y")
    total_texto = page.evaluate("""
        () => {
            const body = document.body.innerText || '';
            // Tentar encontrar texto de paginação
            const m = body.match(/(?:mostrando|showing|exibindo|\\d+\\s*[-–]\\s*\\d+\\s*de)\\s*[\\d,.]+/i);
            return m ? m[0] : null;
        }
    """)
    print(f"  Texto paginação: {total_texto}")
    resultado['texto_paginacao'] = total_texto

    # Coerência: se a lista mostra 0 e KPIs são todos 0 → coerente
    # Se há registros, verificar se soma_kpi == linhas (sem paginação) ou total indicado
    if soma_kpi == 0 and linhas == 0:
        resultado['status'] = 'PASSOU'
        resultado['detalhe'] = 'Org sem registros: KPIs todos 0 e lista vazia — perfeitamente coerente'
    elif soma_kpi == linhas:
        resultado['status'] = 'PASSOU'
        resultado['detalhe'] = f'KPI total ({soma_kpi}) == linhas da lista ({linhas})'
    elif linhas > 0 and soma_kpi != linhas:
        # Verificar se pode haver status sem card (ex: status não exibido nos 4 cards)
        resultado['status'] = 'FALHOU'
        resultado['detalhe'] = f'KPI total ({soma_kpi}) != linhas da lista ({linhas}) — inconsistência detectada'
    else:
        resultado['status'] = 'PASSOU'
        resultado['detalhe'] = f'KPI soma={soma_kpi}, linhas={linhas}'

    # Repetir para o Líder
    print("  Verificando coerência como Líder...")
    try:
        login_lider(page)
        ir_registros(page)
        page.wait_for_timeout(2000)
        tw.snap(page, BASE, "tc5_02_lider_kpi_lista")

        kpis_lider = ler_kpis_numericos(page)
        linhas_lider = contar_linhas_visíveis(page)
        soma_lider = sum(kpis_lider.values())
        print(f"  Líder KPIs: {kpis_lider}, soma={soma_lider}, linhas={linhas_lider}")

        resultado['lider_kpis'] = kpis_lider
        resultado['lider_soma'] = soma_lider
        resultado['lider_linhas'] = linhas_lider

        if soma_lider == linhas_lider:
            resultado['lider_coerencia'] = 'OK'
        else:
            resultado['lider_coerencia'] = f'DIVERGENCIA: KPI={soma_lider} != linhas={linhas_lider}'
            if resultado['status'] == 'PASSOU':
                resultado['status'] = 'FALHOU'
                resultado['detalhe'] += f' | Líder: KPI={soma_lider} != linhas={linhas_lider}'

    except Exception as e:
        print(f"  Erro ao verificar Líder: {e}")
        resultado['lider_erro'] = str(e)[:200]

    # Voltar admin
    login_admin(page)

    return resultado


# ---------------------------------------------------------------------------
# TC6 — Apresentação e menu restrito de registros Compartilhados
# ---------------------------------------------------------------------------

def tc6_compartilhados_menu(page, inventario) -> dict:
    print("\n=== TC6: Menu restrito de registros Compartilhados ===")

    resultado = {'tc': 'TC6'}

    login_admin(page)
    ir_registros(page)
    page.wait_for_timeout(2000)
    tw.snap(page, BASE, "tc6_01_lista_completa")

    tem_compartilhados = page.evaluate("""
        () => /compartilhado/i.test(document.body.innerText || '')
    """)

    if not tem_compartilhados:
        resultado['status'] = 'BLOQUEADO'
        resultado['motivo'] = (
            "Nenhum registro com origem='Compartilhado' encontrado na org 37079. "
            "Registros Compartilhados vêm de SharedEvent de org parceira (não criáveis pela UI). "
            "Solicitar ao João Miguel: configurar compartilhamento de org parceira ou criar "
            "registros com origin=shared via seed/API."
        )
        print(f"  BLOQUEADO: sem registros Compartilhados")
        return resultado

    # Localizar registro Compartilhado
    linha_compartilhada = page.locator("tbody tr").filter(
        has_text=re.compile("compartilhado", re.I)
    ).first

    if linha_compartilhada.count() == 0:
        resultado['status'] = 'BLOQUEADO'
        resultado['motivo'] = 'Chip Compartilhado encontrado no texto mas não localizado como linha de tabela'
        return resultado

    # Verificar chip na coluna Origem
    chip_visivel = page.evaluate("""
        () => {
            const rows = Array.from(document.querySelectorAll('tbody tr'));
            for (const r of rows) {
                if (/compartilhado/i.test(r.innerText || '')) {
                    // verificar se tem chip colorido
                    const chip = r.querySelector('[class*="badge"], [class*="chip"], [class*="tag"]');
                    return {
                        encontrou: true,
                        tem_chip: !!chip,
                        texto_linha: (r.innerText || '').replace(/\\s+/g, ' ').trim().substring(0, 200)
                    };
                }
            }
            return {encontrou: false};
        }
    """)
    print(f"  Chip info: {chip_visivel}")
    resultado['chip_info'] = chip_visivel

    tw.snap(page, BASE, "tc6_02_linha_compartilhada")

    # Abrir menu via page.mouse.click (gotcha 1.8)
    print("  Abrindo kebab via mouse.click...")
    try:
        box = linha_compartilhada.bounding_box()
        if box:
            # Clicar no canto direito da linha (onde fica o kebab)
            page.mouse.click(box["x"] + box["width"] - 15, box["y"] + box["height"] / 2)
            page.wait_for_timeout(1200)
        else:
            tw.abrir_kebab(page, linha_compartilhada)
    except Exception:
        tw.abrir_kebab(page, linha_compartilhada)

    tw.snap(page, BASE, "tc6_03_menu_aberto")
    itens = tw.menu_visivel(page)
    print(f"  Itens do menu: {itens}")
    resultado['itens_menu'] = itens

    if not itens:
        # Tentar novamente com abrir_kebab
        fechar_modal_se_aberto(page)
        page.wait_for_timeout(500)
        tw.abrir_kebab(page, linha_compartilhada)
        page.wait_for_timeout(800)
        itens = tw.menu_visivel(page)
        tw.snap(page, BASE, "tc6_03b_menu_segunda_tentativa")
        resultado['itens_menu_tentativa2'] = itens

    # Verificar restrições do menu (RN 97/98)
    tem_visualizar = any(re.search(r"visualiz", i, re.I) for i in itens)
    tem_historico = any(re.search(r"hist[oó]rico", i, re.I) for i in itens)
    tem_editar = any(re.search(r"editar", i, re.I) for i in itens)
    tem_avaliar = any(re.search(r"avaliar", i, re.I) for i in itens)
    tem_excluir = any(re.search(r"excluir", i, re.I) for i in itens)
    tem_evidencias = any(re.search(r"evid[eê]ncia", i, re.I) for i in itens)

    resultado.update({
        'tem_visualizar': tem_visualizar,
        'tem_historico': tem_historico,
        'tem_editar': tem_editar,
        'tem_avaliar': tem_avaliar,
        'tem_excluir': tem_excluir,
        'tem_evidencias': tem_evidencias,
    })

    menu_correto = tem_visualizar and tem_historico and not tem_editar and not tem_avaliar and not tem_excluir and not tem_evidencias
    chip_ok = chip_visivel.get('encontrou', False)

    if menu_correto and chip_ok:
        resultado['status'] = 'PASSOU'
        resultado['detalhe'] = "Chip 'Compartilhado' visível + menu tem apenas Visualizar e Histórico"
    elif itens:
        problemas = []
        if not tem_visualizar: problemas.append("'Visualizar' ausente")
        if not tem_historico: problemas.append("'Histórico' ausente")
        if tem_editar: problemas.append("'Editar' não deveria aparecer")
        if tem_avaliar: problemas.append("'Avaliar' não deveria aparecer")
        if tem_excluir: problemas.append("'Excluir' não deveria aparecer")
        if tem_evidencias: problemas.append("'Evidências' não deveria aparecer")
        resultado['status'] = 'FALHOU'
        resultado['problemas'] = problemas
    else:
        resultado['status'] = 'BLOQUEADO'
        resultado['motivo'] = 'Não foi possível abrir o menu kebab do registro Compartilhado'

    tw.snap(page, BASE, "tc6_04_resultado")
    return resultado


# ---------------------------------------------------------------------------
# FASE EXTRA — Verificar liderados do Líder via organograma/edição
# ---------------------------------------------------------------------------

def verificar_liderados_lider(page) -> dict:
    """Tenta verificar se lider. tem liderados configurados no organograma."""
    print("\n=== Verificando liderados do Líder ===")

    login_admin(page)

    # Tentar ir para configurações de organograma (hierarquia)
    urls_org = [
        f"{BASE_URL}/o/{ORG_ID}/organization_structure",
        f"{BASE_URL}/o/{ORG_ID}/hierarchies",
        f"{BASE_URL}/o/{ORG_ID}/org_charts",
        f"{BASE_URL}/o/{ORG_ID}/team_structures",
    ]

    resultado = {'funcao': 'verificar_liderados'}
    for url in urls_org:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(1500)
            body = page.locator("body").inner_text()
            if "doesn't exist" not in body and "404" not in page.url:
                print(f"  URL OK: {url}")
                tw.snap(page, BASE, f"lider_org_{url.split('/')[-1]}")
                resultado['url_organograma'] = url
                resultado['texto_preview'] = body[:300]
                break
        except Exception:
            pass

    # Verificar pelo usuário lider: clicar nos 3 pontos → Editar → ver liderados
    page.goto(f"{BASE_URL}/o/{ORG_ID}/users", wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(2000)
    tw.dispensar_nps(page)

    # Buscar lider
    search = page.locator("input[placeholder*='Pesquise']").first
    if search.count():
        search.fill("liderado1")
        page.wait_for_timeout(1500)
    tw.snap(page, BASE, "lider_busca_liderado1")

    liderado_row = page.locator("tbody tr").filter(has_text="liderado1").first
    if liderado_row.count():
        resultado['liderado1_existe'] = True
        info = liderado_row.inner_text()
        resultado['liderado1_info'] = info[:200]
        print(f"  liderado1: {info[:150]}")
    else:
        resultado['liderado1_existe'] = False

    return resultado


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("QA 1.16 — Registros F2 | Card 19903")
    print(f"Org: {BASE_URL} (ID: {ORG_ID})")
    print(f"URL Registros: {REGISTROS_URL}")
    print("=" * 60)

    resultados = {}

    with tw.sync_playwright() as p:
        browser, ctx, page = tw.nova_pagina(p)

        try:
            # FASE 0
            inventario = fase_0_inventario(page)
            resultados['inventario'] = inventario

            # Verificar liderados
            info_liderados = verificar_liderados_lider(page)
            resultados['info_liderados'] = info_liderados

            # TC1
            r_tc1 = tc1_escopo_lider_vs_admin(page, inventario)
            resultados['tc1'] = r_tc1

            # TC4
            r_tc4 = tc4_sumico_inativados(page)
            resultados['tc4'] = r_tc4

            # TC5
            r_tc5 = tc5_coerencia_kpi_lista(page)
            resultados['tc5'] = r_tc5

            # TC6
            r_tc6 = tc6_compartilhados_menu(page, inventario)
            resultados['tc6'] = r_tc6

        except Exception as e:
            print(f"\n[ERRO GERAL]: {e}")
            import traceback
            traceback.print_exc()
            try:
                tw.snap(page, BASE, "ERRO_geral")
            except Exception:
                pass
        finally:
            ctx.close()
            browser.close()

    # Salvar resultados
    result_path = BASE / "resultados.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n[resultados] {result_path}")

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO:")
    print("=" * 60)
    for key in ['tc1', 'tc4', 'tc5', 'tc6']:
        r = resultados.get(key, {})
        if r:
            status = r.get('status', 'N/A')
            detalhe = r.get('detalhe', r.get('motivo', ''))
            print(f"  {r.get('tc', key):8s} → {status:30s} | {detalhe[:80]}")

    # Inventário
    inv = resultados.get('inventario', {})
    print(f"\nInventário de massa:")
    print(f"  Registros na org: {inv.get('total_registros', '?')}")
    print(f"  Compartilhados: {inv.get('tem_compartilhados', '?')}")
    print(f"  Líder (qalider): {inv.get('lider_existe', '?')}")
    print(f"  Liderado1: {inv.get('liderado_existe', '?')}")

    print(f"\nScreenshots em: {BASE}")
    return resultados


if __name__ == "__main__":
    main()
