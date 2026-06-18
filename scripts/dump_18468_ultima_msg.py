"""Dump da ULTIMA mensagem do assistente (ja no historico) — lista os blocos em
ORDEM com tag + amostra, e marca quais sao <table> vs texto-com-pipes. Decide se a
resposta e uma tabela limpa (fix) ou tem linhas viradas texto-com-pipes (bug).
Tambem salva o innerHTML e um screenshot full_page.
"""
import re
import _twygo as tw

c = tw.cfg("MIGR")
BASE, ORG = c["base_url"], c["org_id"]
PASTA = tw.ROOT / "evidencias" / "18468"

with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    page.goto(f"{BASE}/o/{ORG}/question_lists", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    page.get_by_role("button", name=re.compile(r"Importa.{0,4}o Inteligente", re.I)).first.click(force=True)
    page.wait_for_timeout(4000)

    info = page.evaluate(r"""()=>{
        const msgs=document.querySelectorAll('.aui-assistant-message-content');
        const m=msgs[msgs.length-1];
        if(!m) return {erro:'sem msg'};
        // percorre os filhos diretos relevantes em ordem
        const blocos=[];
        const walk=(el)=>{
            el.childNodes.forEach(n=>{
                if(n.nodeType!==1) return;
                const tag=n.tagName.toLowerCase();
                if(tag==='table'){
                    const rows=n.querySelectorAll('tr').length;
                    const head=(n.querySelector('th')?(n.querySelector('th').innerText||''):'');
                    blocos.push({tag:'TABLE', rows, head:head.slice(0,40)});
                } else if(['p','h1','h2','h3','h4','ul','ol','li'].includes(tag)){
                    const t=(n.innerText||'').replace(/\s+/g,' ').trim();
                    const pipes=(t.match(/\|/g)||[]).length;
                    blocos.push({tag:tag.toUpperCase(), pipes, txt:t.slice(0,60)});
                } else { walk(n); }
            });
        };
        walk(m);
        const tables=m.querySelectorAll('table').length;
        let pipePara=0;
        m.querySelectorAll('p,li,h1,h2,h3,h4').forEach(e=>{ if(e.closest('table'))return; if(((e.innerText||'').match(/\|/g)||[]).length>=2)pipePara++; });
        return {nMsgs:msgs.length, tables, pipePara, totalBlocos:blocos.length, blocos:blocos.slice(0,60)};
    }""")
    print(f"[nMsgs] {info.get('nMsgs')}  tables={info.get('tables')}  pipePara={info.get('pipePara')}  blocos={info.get('totalBlocos')}")
    print("[blocos em ordem]")
    for b in info.get("blocos", []):
        print("   ", b)

    # salvar innerHTML da ultima msg
    html = page.evaluate("()=>{const m=document.querySelectorAll('.aui-assistant-message-content');return m.length?m[m.length-1].innerHTML:'';}")
    (PASTA / "ultima_msg.html").write_text(html, encoding="utf-8")
    print(f"[html salvo] {(PASTA/'ultima_msg.html')} ({len(html)} chars)")

    # scroll pro topo da ultima msg e full_page snap
    page.evaluate("()=>{const m=document.querySelectorAll('.aui-assistant-message-content');if(m.length)m[m.length-1].scrollIntoView({block:'start'});}")
    page.wait_for_timeout(1000)
    tw.snap(page, PASTA, "dump-topo-ultima-msg")
    tw.snap(page, PASTA, "dump-fullpage", full=True)

    page.wait_for_timeout(1000)
    ctx.close(); browser.close()
