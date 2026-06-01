"""19640 — CROSS-CHECK do desempenho: a aba 'Respostas de questionario' mostra o
desempenho REAL por questionario/participante. Compara com o que a aba Aprendizagem
exibe pro agents.claude (geracao anterior 44275175 vs nova 44275236), pra ver se a
lista de Aprendizagem esta mostrando desempenho NAO-condizente com as respostas reais.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://recertificacao-testeqa.stage.twygoead.com"
EMAIL, SENHA = "agents.claude@claude.com", "123456"
TRILHA_ID = "807406"
PASTA = ROOT / "evidencias" / "19640_pontuacao_reinscricao"


def dispensar_nps(page):
    for sel in ["button:has-text('Pergunte depois')", ".chakra-modal__close-btn", "[aria-label='Close']"]:
        try:
            b = page.locator(sel).first
            if b.count() and b.is_visible(): b.click(timeout=1500); page.wait_for_timeout(500)
        except Exception: pass


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=350)
    context = browser.new_context(viewport={"width": 1600, "height": 1000}, locale="pt-BR")
    page = context.new_page()
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded"); page.fill("#user_email", EMAIL)
    page.fill("#user_password", SENHA); page.click("#user_submit")
    try: page.wait_for_load_state("networkidle", timeout=20000)
    except Exception: pass
    page.goto(f"{BASE_URL}/e/{TRILHA_ID}/learning", wait_until="domcontentloaded", timeout=30000)
    try: page.wait_for_load_state("networkidle", timeout=15000)
    except Exception: pass
    page.wait_for_timeout(4000); dispensar_nps(page)

    # clicar aba 'Respostas de questionario'
    print("[aba] clicando 'Respostas de questionário' ...")
    try:
        page.get_by_text("Respostas de questionário", exact=False).first.click(timeout=8000)
        page.wait_for_timeout(4000); dispensar_nps(page)
    except Exception as e:
        print(f"   click aba falhou: {repr(e)[:120]}")
    print(f"   url={page.url}")
    page.screenshot(path=str(PASTA / "20-respostas-questionario.png"), full_page=True)
    print("   [snap] 20-respostas-questionario.png")

    # dump das linhas que tem agents.claude (e estrutura geral)
    dump = page.evaluate(
        r"""() => {
            const heads = Array.from(document.querySelectorAll('thead th, thead td')).map(h=>(h.innerText||'').replace(/\s+/g,' ').trim());
            const rows = [];
            document.querySelectorAll('tr').forEach(r => {
                const t = (r.innerText||'').replace(/\s+/g,' ').trim();
                if (/agents\.claude/i.test(t)) rows.push({itemId: r.getAttribute('data-item-id')||'', txt: t.slice(0,220)});
            });
            // tambem qualquer texto de desempenho/nota visivel
            return {heads, rows, totalTr: document.querySelectorAll('tr').length};
        }""")
    print(f"[heads] {dump['heads']}")
    print(f"[linhas agents.claude na aba Respostas] {len(dump['rows'])}:")
    for r in dump["rows"]:
        print(f"   itemId={r['itemId']} | {r['txt']}")
    (PASTA / "_respostas_questionario.json").write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")

    page.wait_for_timeout(1500)
    context.close(); browser.close()
