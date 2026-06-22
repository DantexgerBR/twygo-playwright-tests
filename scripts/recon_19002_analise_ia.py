"""RECON (read-only-ish) p/ o card 19002 — entender a UI antes de automatizar o
fluxo do tech lead: questionario c/ switch de analise por IA -> atividade -> aluno
responde -> notificacao.

So navega e tira screenshots: (1) Controle de IA / creditos, (2) lista de
Questionarios, (3) form de novo questionario (achar o switch 'analise por IA'),
(4) area de notificacao (sino) do admin.
"""
import _twygo as tw

c = tw.cfg("")  # stage principal, org 36675
PASTA = tw.ROOT / "evidencias" / "19002_recon"


def dump_switches(page, label):
    """Lista switches/checkboxes visiveis com texto proximo — p/ achar 'analise por IA'."""
    info = page.evaluate(
        r"""() => {
            const out = [];
            document.querySelectorAll('input[type=checkbox], .chakra-switch, [role=switch]').forEach(el => {
                const box = el.closest('label,.chakra-switch,.chakra-form-control,div');
                const txt = (box ? box.innerText : '').replace(/\s+/g,' ').trim().slice(0,80);
                if (txt) out.push({txt, checked: el.checked ?? null, name: el.name || ''});
            });
            return out;
        }""")
    print(f"   [{label}] switches/checkboxes ({len(info)}):")
    for s in info[:25]:
        print(f"      checked={str(s['checked']):5} name={s['name'][:24]:24} :: {s['txt']}")
    return info


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    print(f"[login] {page.url}")
    BASE, ORG = c["base_url"], c["org_id"]

    # (1) Controle de IA (BETA) — creditos / flag
    page.goto(f"{BASE}/o/{ORG}/ai_consumption_analysis", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    print(f"[controle-ia] {page.url}")
    tw.snap(page, PASTA, "01-controle-ia")

    # (2) Lista de Questionarios
    page.goto(f"{BASE}/o/{ORG}/question_lists", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    print(f"[question_lists] {page.url}")
    tw.snap(page, PASTA, "02-lista-questionarios")
    # textos de botoes de criar
    botoes = page.evaluate(
        "()=>Array.from(document.querySelectorAll('button,a')).map(b=>(b.innerText||'').replace(/\\s+/g,' ').trim()).filter(t=>t&&t.length<40).slice(0,40)")
    print(f"   botoes/links: {botoes}")

    # (3) Form de novo questionario
    for url in [f"{BASE}/o/{ORG}/question_lists/new", f"{BASE}/o/{ORG}/question_lists/new?kind=0"]:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000); tw.dispensar_nps(page)
        print(f"[novo-questionario] {url} -> {page.url}")
        if "/new" in page.url and "404" not in page.url:
            break
    tw.snap(page, PASTA, "03-novo-questionario")
    dump_switches(page, "novo-questionario")
    # procurar texto 'IA' / 'analise' na pagina
    tem_ia = page.evaluate(
        "()=>{const t=document.body.innerText||'';const m=t.match(/.{0,40}(an[aá]lise|intelig|\\bIA\\b).{0,40}/gi)||[];return [...new Set(m)].slice(0,12);}")
    print(f"   trechos com IA/analise: {tem_ia}")

    # (4) Notificacao (sino) do admin
    page.goto(f"{BASE}/o/{ORG}/events?tab=events&profile=admin", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000); tw.dispensar_nps(page)
    # tentar achar sino de notificacao no topo
    sino = page.evaluate(
        r"""() => {
            const cands = Array.from(document.querySelectorAll('header *, nav *, [class*=notif] , [aria-label*=otific], .material-icons, [class*=icon]'));
            const hit = cands.find(e => /notif/i.test(e.className||'') || /notif/i.test(e.getAttribute&&e.getAttribute('aria-label')||'') || (e.innerText||'').trim()==='notifications');
            return hit ? {tag:hit.tagName, cls:(hit.className||'').toString().slice(0,60), aria:hit.getAttribute('aria-label'), txt:(hit.innerText||'').slice(0,30)} : null;
        }""")
    print(f"   candidato a sino de notificacao: {sino}")
    tw.snap(page, PASTA, "04-topbar-notificacao")

    print(f"\n[FIM recon] veja {PASTA}")
    page.wait_for_timeout(1000)
    ctx.close(); browser.close()
