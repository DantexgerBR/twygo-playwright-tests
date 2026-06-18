"""Retrabalho 18468 — Importacao inteligente de questionario deve renderizar a
resposta da IA em TABELA desde o inicio e MANTER tabela durante todo o streaming.

Bug (PR #10276): o token __AGENT_HEARTBEAT__ (keepalive a cada 5s de silencio do
agente) era tratado como __AGENT_EXECUTOR__ -> zerava o acumulador e punha
'Processando...'. Em docs grandes o LLM pausa >5s; o heartbeat no meio de uma
tabela descartava o cabecalho GFM (| col |/| --- |) -> linhas restantes viravam
PARAGRAFO COM PIPES (texto corrido). Fix: heartbeat so faz 'continue'.

Validacao: subir um doc GRANDE (100 perguntas, forca pausas >5s) e monitorar o DOM
do chat durante o streaming. Frame com paragrafo-com-pipes OU 'Processando...'
apagando uma tabela ja montada = bug reproduzido (FALHOU). Tabela construida
progressivamente e mantida ate o fim, em N tentativas = fix OK (PASSOU).

Ambiente: MIGR (testedemigracao, org 19653, flag analise_de_questionario_por_ia).
"""
import re
import sys
from pathlib import Path
import _twygo as tw

N_TENTATIVAS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
PERFIL = sys.argv[2] if len(sys.argv) > 2 else "MIGR"   # ""=principal/36675, "MIGR"=testedemigracao
c = tw.cfg(PERFIL)
BASE, ORG = c["base_url"], c["org_id"]
SLUG = "18468" if PERFIL == "MIGR" else f"18468_{PERFIL or 'principal'}"
PASTA = tw.ROOT / "evidencias" / SLUG
DOC = Path(sys.argv[3]) if len(sys.argv) > 3 else (tw.ROOT / "evidencias" / "18468" / "quiz_grande.docx")
print(f"[perfil] {PERFIL or 'principal'}  org={ORG}  base={BASE}")
print(f"[doc] {DOC.name}")

# JS: classifica o estado renderizado SO no painel de importacao (exclui a tabela
# da lista de questionarios atras do overlay). nTables = tabelas renderizadas na
# resposta; pipePara = blocos de texto SEM tabela com >=2 pipes (sintoma do bug);
# processando = 'Processando...' presente.
PROBE = r"""()=>{
    // escopa SO na ultima mensagem do assistente (assistant-ui) -> ignora historico
    // de execucoes anteriores e a tabela da lista de questionarios atras do overlay.
    const msgs=document.querySelectorAll('.aui-assistant-message-content');
    const m=msgs[msgs.length-1];
    if(!m) return {nTables:0,pipePara:0,sample:'',processando:false,carregando:false,len:0,nMsgs:0};
    const tables=m.querySelectorAll('table');
    let pipePara=0, sample='';
    m.querySelectorAll('p,li,div,span').forEach(e=>{
        if(e.closest('table')) return;
        if(e.children.length>0) return;            // so folhas de texto
        const t=(e.textContent||'');
        if((t.match(/\|/g)||[]).length>=2){ pipePara++; if(!sample) sample=t.replace(/\s+/g,' ').trim().slice(0,90); }
    });
    const txt=m.innerText||'';
    return {nTables:tables.length, pipePara, sample,
            processando:/Processando\.\.\./.test(txt), carregando:/Carregando question/i.test(txt),
            len:txt.length, nMsgs:msgs.length};
}"""


# JS: estrutura da ultima mensagem em blocos ordenados (table vs texto-com-pipes).
# Detecta o sintoma do bug: P/H com >=2 pipes (linha de tabela virada texto), e
# 'tabela quebrada' = um <table> seguido imediatamente por um paragrafo-com-pipes.
STRUCT = r"""()=>{
    const msgs=document.querySelectorAll('.aui-assistant-message-content');
    const m=msgs[msgs.length-1];
    if(!m) return {erro:'sem msg'};
    const blocos=[];
    const walk=(el)=>{ el.childNodes.forEach(n=>{ if(n.nodeType!==1)return;
        const tag=n.tagName.toLowerCase();
        if(tag==='table'){ blocos.push({t:'TABLE', rows:n.querySelectorAll('tr').length}); }
        else if(['p','h1','h2','h3','h4','ul','ol','li'].includes(tag)){
            const txt=(n.innerText||'').replace(/\s+/g,' ').trim();
            const pipes=(txt.match(/\|/g)||[]).length;
            blocos.push({t:tag.toUpperCase(), pipes, txt:txt.slice(0,70)});
        } else { walk(n); } }); };
    walk(m);
    // quebras: paragrafo-com-pipes (>=2) que NAO esta em tabela
    const pipeBlocos=blocos.filter(b=>b.pipes>=2);
    // tabela-quebrada: TABLE imediatamente seguido por bloco com pipes
    let quebradas=0;
    for(let i=0;i<blocos.length-1;i++){ if(blocos[i].t==='TABLE' && (blocos[i+1].pipes||0)>=2) quebradas++; }
    return {nMsgs:msgs.length, totalBlocos:blocos.length,
            nTables:blocos.filter(b=>b.t==='TABLE').length,
            nPipeBlocos:pipeBlocos.length, nTabelasQuebradas:quebradas,
            amostraPipes:pipeBlocos.slice(0,5).map(b=>b.txt)};
}"""


def nova_conversa(page):
    """Abre o hamburguer (☰) do chat e clica '+ Nova conversa' pra furar o cache
    de resposta da sessao (todas as importacoes caem na mesma conversa por padrao)."""
    page.mouse.click(632, 90)   # hamburguer no topo-esq do overlay (viewport 1500x950)
    page.wait_for_timeout(1200)
    nc = page.get_by_text(re.compile(r"Nova conversa", re.I)).first
    if nc.count() and nc.is_visible():
        nc.click(timeout=4000); page.wait_for_timeout(2500)
        print("[nova conversa] iniciada")
        return True
    print("[nova conversa] NAO encontrei o botao")
    return False


def abrir_chat(page):
    page.goto(f"{BASE}/o/{ORG}/question_lists", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3500); tw.dispensar_nps(page)
    btn = page.get_by_role("button", name=re.compile(r"Importa.{0,4}o Inteligente", re.I))
    if not btn.count():
        print("[FLAG] botao 'Importacao Inteligente' AUSENTE -> flag analise_de_questionario_por_ia OFF nesta org")
        return False
    btn.first.click(force=True)
    for _ in range(12):
        page.wait_for_timeout(1000)
        if page.locator("textarea[placeholder*='Escreva']").count():
            nova_conversa(page)   # conversa fresca -> geracao nova (sem cache)
            return True
    return False


def tentativa(page, n):
    sub = f"t{n}"
    print(f"\n===== TENTATIVA {n} =====")
    if not abrir_chat(page):
        print("[erro] chat nao abriu"); return {"erro": "chat-nao-abriu"}
    tw.snap(page, PASTA, f"{sub}_00-chat-aberto")

    # anexar o doc pelo CLIPE (filechooser) — o input do chat de SUPORTE nao serve
    with page.expect_file_chooser(timeout=8000) as fc:
        page.get_by_text("attach_file").first.click(timeout=5000)
    fc.value.set_files(str(DOC))
    page.wait_for_timeout(2500)
    # confirmar o chip do arquivo antes de enviar
    tem_chip = page.evaluate("()=>/quiz_grande|\\.docx/i.test(document.body.innerText||'')")
    print(f"[anexo] chip presente={tem_chip}")
    # SEM prompt — como na evidencia (so o anexo -> a IA monta a tabela de preview)
    tw.snap(page, PASTA, f"{sub}_01-doc-anexado")
    # botao enviar: #thread-composer-send-btn so habilita quando o anexo termina de subir
    send = page.locator("#thread-composer-send-btn")
    enviado = False
    for _ in range(40):   # ate ~20s esperando habilitar
        if send.count() and send.is_enabled():
            send.click(timeout=4000); enviado = True; break
        page.wait_for_timeout(500)
    if not enviado:
        print("[aviso] send-btn nao habilitou; tentando Enter")
        page.locator("textarea[placeholder*='Escreva']").first.press("Enter")
    print("[enviado] aguardando streaming...")

    # monitorar
    estados = []
    pico_tabela = 0
    bug_pipe = None      # primeiro frame com paragrafo-com-pipes APOS ja ter visto conteudo
    bug_proc_apos_tabela = None
    viu_tabela = False
    estavel = 0
    last_len = -1
    ultimo_estado = None
    for i in range(420):  # ate ~7min (420 * 1s)
        page.wait_for_timeout(1000)
        st = page.evaluate(PROBE)
        chave = (st["nTables"], st["pipePara"], st["processando"], st["carregando"])
        if chave != ultimo_estado:
            ts = i
            estados.append({"t": ts, **st})
            print(f"  [t={ts:3}s] tables={st['nTables']} pipePara={st['pipePara']} proc={st['processando']} carreg={st['carregando']} len={st['len']} :: {st['sample']}")
            ultimo_estado = chave
            # snapshots de transicao relevantes
            if st["nTables"] > pico_tabela:
                pico_tabela = st["nTables"]
                tw.snap(page, PASTA, f"{sub}_tab{st['nTables']}-t{ts}")
            if st["nTables"] > 0:
                viu_tabela = True
            if st["pipePara"] > 0 and st["nTables"] == 0:
                # texto corrido com pipes SEM tabela = sintoma do bug
                if bug_pipe is None:
                    bug_pipe = {"t": ts, **st}
                    tw.snap(page, PASTA, f"{sub}_BUG-pipes-t{ts}")
            if st["processando"] and viu_tabela and st["nTables"] == 0:
                if bug_proc_apos_tabela is None:
                    bug_proc_apos_tabela = {"t": ts, **st}
                    tw.snap(page, PASTA, f"{sub}_BUG-proc-apos-tabela-t{ts}")
        # criterio de fim: NAO pode estar ocupado (Processando/Carregando questionario),
        # conteudo estavel e ja tem tabela montada (a resposta esperada e uma tabela).
        ocupado = st["processando"] or st["carregando"]
        if st["len"] == last_len and not ocupado:
            estavel += 1
        else:
            estavel = 0
        last_len = st["len"]
        if estavel >= 12 and not ocupado and st["nTables"] > 0:   # tabela pronta e ~12s estavel
            print(f"  [fim] tabela estavel em t={i}s")
            break
    tw.snap(page, PASTA, f"{sub}_99-final")

    # dump da estrutura da ultima mensagem (evidencia definitiva: tabela quebrada?)
    estrutura = page.evaluate(STRUCT)
    print(f"[estrutura t{n}] {estrutura}")

    res = {
        "tentativa": n,
        "viu_tabela": viu_tabela,
        "pico_tabela": pico_tabela,
        "bug_pipe": bug_pipe,
        "bug_proc_apos_tabela": bug_proc_apos_tabela,
        "estado_final": estados[-1] if estados else None,
        "n_transicoes": len(estados),
        "estrutura": estrutura,
    }
    print(f"[resultado t{n}] viu_tabela={viu_tabela} pico={pico_tabela}")
    return res


with tw.sync_playwright() as p:
    browser, ctx, page = tw.nova_pagina(p)
    tw.login(page, c)
    print(f"[login] {page.url}")

    resultados = []
    for n in range(1, N_TENTATIVAS + 1):
        try:
            resultados.append(tentativa(page, n))
        except Exception as e:
            print(f"[ERRO tentativa {n}] {e}")
            tw.snap(page, PASTA, f"t{n}_ERRO")
            resultados.append({"tentativa": n, "erro": str(e)})

    print("\n===================== RESUMO =====================")
    bug = False
    for r in resultados:
        est = r.get("estrutura") or {}
        quebr = est.get("nTabelasQuebradas", 0)
        pipes = est.get("nPipeBlocos", 0)
        rep = (quebr or pipes)   # tabela quebrada OU linha de tabela virada texto-com-pipes
        marca = "BUG REPRODUZIDO" if rep else ("OK (tabela limpa)" if est.get("nTables") else "SEM TABELA/INCONCLUSIVO")
        if rep:
            bug = True
        print(f"  t{r.get('tentativa')}: {marca} | tables={est.get('nTables')} pipeBlocos={pipes} tabelasQuebradas={quebr}")
        if est.get("amostraPipes"):
            print(f"      amostraPipes: {est.get('amostraPipes')}")
    print(f"\n[VEREDITO] {'FALHOU — bug reproduzido (tabela quebra em texto-com-pipes)' if bug else 'tabela integra em todas as tentativas'}")
    print(f"[evidencias] {PASTA}")
    page.wait_for_timeout(1500)
    ctx.close(); browser.close()
