# 18468 — Questionário com IA: tabela na importação inteligente

**Veredito: ✅ PASSOU** — Stage `testedemigracao` (org 19653), flag `analise_de_questionario_por_ia` ativa.

## O que o card pedia
Ao importar um documento na Importação Inteligente de questionários, a IA deve
apresentar as perguntas/respostas **em tabela desde o início**, não em texto
corrido com pipes (`| col | col |`). PR do fix: #10276 (token `__AGENT_HEARTBEAT__`
deixou de zerar o acumulador de texto no streaming).

## Como foi validado
Script `scripts/retrabalho_18468_tabela_importacao_ia.py`: abre o Agente de
importação, **inicia uma conversa nova** (fura o cache de resposta da sessão),
anexa um documento-tabela grande (~100 perguntas → gera pausas >5s do LLM, que
disparam o heartbeat) e **monitora o DOM da última mensagem durante o streaming**,
contando tabelas, blocos de texto-com-pipes e "tabelas quebradas" (um `<table>`
seguido de parágrafo-com-pipes).

## Resultado — 5 gerações independentes (docs únicos, ~54-67s cada)
| doc | tabelas | blocos-pipe | tabelas quebradas |
|-----|---------|-------------|-------------------|
| quiz_unico_102703 | 19 | 0 | 0 |
| quiz_unico_102939 | 19 | 0 | 0 |
| quiz_unico_103327 | 19 | 0 | 0 |
| quiz_unico_103519 | 19 | 0 | 0 |
| quiz_unico_103704 | 19 | 0 | 0 |

A tabela é construída progressivamente e **se mantém tabela até o fim**, mesmo nas
gerações longas onde o heartbeat dispara. Nenhuma degradação para texto-com-pipes.

## Screenshots
- `t1_99-final.png`, `t2_99-final.png`, `t3_99-final.png` — tabela limpa e alinhada
  (colunas NÚMERO/RESULTADO/LOTE/ESCOLHA e #/Pergunta/A/B/C/D/Resposta/Tipo).
- `t*_tab19-*.png` — tabela durante o streaming, já íntegra.
- `cache_pre_fix_tabela_quebrada.png` — **referência do bug** (resposta cacheada
  de uma conversa antiga, geração pré-fix): a tabela quebra e a linha
  `| C) | 1975 | | D) | 2001 |` aparece como texto. Foi o que motivou a investigação
  do cache; com geração fresca pós-fix o problema não ocorre.

## Observação importante
O Agente cacheia a resposta por conversa: reimportar na mesma conversa replica o
parse antigo. A validação só é fiel iniciando **conversa nova** a cada teste.
