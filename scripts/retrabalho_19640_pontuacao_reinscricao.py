"""Retrabalho 19640 — [Recertificação] Desempenho e pontuacao da reinscricao atual
esta sendo propagado para todas as reinscricoes.

Bug: na aba Aprendizagem (visao admin) de uma trilha, o desempenho E pontuacao da
inscricao atual sobrescreve as inscricoes anteriores. Anteriores ja finalizadas
deveriam ser IMUTAVEIS (respeitar historico).

Esperado: cada reinscricao do mesmo usuario mantem seu proprio desempenho+pontuacao.

Env: RECERTIFICACAO (org 37048). Trilha "Trilha para CASCADE" (id 807406).
Discriminador: as varias inscricoes do MESMO usuario devem ter pontuacao+desempenho
DISTINTOS (preservados), nao todos iguais ao valor da reinscricao atual.
"""
import re
import json
from pathlib import Path
from collections import defaultdict
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
import _twygo as tw
_c = tw.cfg("RECERT")
BASE_URL, ORG_ID, EMAIL, SENHA = _c["base_url"], _c["org_id"], _c["email"], _c["senha"]
TRILHA_ID = "807406"

PASTA = ROOT / "evidencias" / "19640_pontuacao_reinscricao"
PASTA.mkdir(parents=True, exist_ok=True)


def snap(page, nome):
    p = PASTA / f"{nome}.png"; page.screenshot(path=str(p), full_page=False)
    print(f"   [snap] {p.name}"); return p


def dispensar_nps(page):
    for sel in ["button:has-text('Pergunte depois')", "[aria-label='Close']", ".chakra-modal__close-btn"]:
        try:
            b = page.locator(sel).first
            if b.count() and b.is_visible(): b.click(timeout=2000); page.wait_for_timeout(600)
        except Exception: pass


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=350)
    context = browser.new_context(viewport={"width": 1500, "height": 950}, locale="pt-BR")
    page = context.new_page()

    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=30000)
    page.fill("#user_email", EMAIL); page.fill("#user_password", SENHA); page.click("#user_submit")
    try: page.wait_for_load_state("networkidle", timeout=20000)
    except Exception: pass
    print(f"[login] {page.url}")

    # ir direto pra Aprendizagem (learning) da trilha
    page.goto(f"{BASE_URL}/e/{TRILHA_ID}/learning", wait_until="domcontentloaded", timeout=30000)
    try: page.wait_for_load_state("networkidle", timeout=15000)
    except Exception: pass
    page.wait_for_timeout(4000); dispensar_nps(page)
    print(f"[learning] {page.url}")
    if "/users/login" in page.url or "/login" in page.url:
        print("FALHA: sessao/login"); snap(page, "00-falha"); raise SystemExit(1)
    snap(page, "01-lista-aprendizagem")

    # extrair linhas: participante(email) + progresso + desempenho + pontuacao + situacao/cert
    linhas = page.evaluate(
        r"""() => {
            const out = [];
            document.querySelectorAll('tr').forEach(r => {
                const txt = (r.innerText||'');
                if (!/@/.test(txt)) return;
                const email = (txt.match(/[\w.\-]+@[\w.\-]+/)||[''])[0];
                // numeros: progresso% , desempenho% , pontuacao
                const pcts = (txt.match(/(\d+(?:\.\d+)?)%/g)||[]);
                const progresso = pcts[0] || '';
                const desempenho = pcts[1] || '';
                // pontuacao = primeiro inteiro "solto" apos os %
                const semPct = txt.replace(/\d+(?:\.\d+)?%/g, '|');
                const pont = (semPct.match(/\|\s*\|?\s*(\d{1,6})\b/)||['',''])[1];
                const cert = /Emitido/.test(txt) ? 'Emitido' :
                             /Substitu/.test(txt) ? 'Substituido' :
                             /Pendente/.test(txt) ? 'Pendente' : '';
                out.push({email, progresso, desempenho, pontuacao: pont, cert,
                          resumo: txt.replace(/\n+/g,' | ').slice(0,180)});
            });
            return out;
        }""")
    print(f"[linhas] {len(linhas)} inscricoes:")
    for i, l in enumerate(linhas):
        print(f"   [{i}] {l['email']:32} prog={l['progresso']:>6} desemp={l['desempenho']:>7} pont={l['pontuacao']:>5} cert={l['cert']}")

    (PASTA / "_inscricoes.txt").write_text(
        "\n".join(f"[{i}] prog={l['progresso']} desemp={l['desempenho']} pont={l['pontuacao']} cert={l['cert']} | {l['resumo']}"
                  for i, l in enumerate(linhas)), encoding="utf-8")
    (PASTA / "_inscricoes.json").write_text(json.dumps(linhas, ensure_ascii=False, indent=2), encoding="utf-8")

    # agrupar por usuario p/ checar imutabilidade entre reinscricoes
    print("\n===== AGRUPADO POR USUARIO (reinscricoes) =====")
    grupos = defaultdict(list)
    for l in linhas:
        grupos[l["email"]].append(l)
    veredito_propagado = False
    for email, regs in grupos.items():
        if len(regs) < 2:
            print(f"   {email}: 1 inscricao (sem reinscricao p/ comparar)")
            continue
        pares = [(r["desempenho"], r["pontuacao"], r["progresso"]) for r in regs]
        desemps = {r["desempenho"] for r in regs}
        ponts = {r["pontuacao"] for r in regs}
        distintos = len(desemps) > 1 or len(ponts) > 1
        progs = {r["progresso"] for r in regs}
        # se PROGRESSO varia mas desemp+pont sao todos iguais => propagacao (bug)
        propagado = (len(progs) > 1) and (len(desemps) == 1) and (len(ponts) == 1)
        if propagado:
            veredito_propagado = True
        print(f"   {email}: {len(regs)} inscricoes")
        for r in regs:
            print(f"        prog={r['progresso']:>6} desemp={r['desempenho']:>7} pont={r['pontuacao']:>5} cert={r['cert']}")
        print(f"        -> desempenhos distintos={len(desemps)>1} | pontuacoes distintas={len(ponts)>1} "
              f"| PROPAGADO(bug)={propagado}")

    print("\n===== RESUMO =====")
    if veredito_propagado:
        print("BUG PRESENTE: ha usuario com progresso variando mas desemp+pont identicos (propagado).")
    else:
        print("OK: nenhum usuario com desemp+pont propagados; reinscricoes preservam valores distintos.")

    page.wait_for_timeout(1500)
    print("\n[FIM] veja evidencias/19640_pontuacao_reinscricao/")
    context.close(); browser.close()
