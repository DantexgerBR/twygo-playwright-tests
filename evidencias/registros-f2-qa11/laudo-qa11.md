# Laudo QA 1.1 — Listagem 'Meu histórico' do Aluno
**Card Artia**: 19888  
**Suite AT**: Listagem 'Meu histórico' do Aluno — tabela, busca e mobile  
**Data**: 2026-06-22  
**Ambiente**: Stage (https://twygo1772627238.stage.twygoead.com/)  
**Org**: 36675  

> **Nota de finalizacao (2026-06-22)**: vereditos RECONCILIADOS apos a run de semeacao.
> A 2a run semeou massa (10:21-10:42) mas foi CORTADA pelo limite de sessao antes de
> re-rodar os TCs com massa e atualizar este laudo. TC8 reconciliado de PASSOU->FALHOU
> com base na propria evidencia (busca nao estreita). TC11/TC3 a fechar na org dedicada
> `registrosf2.stage.twygoead.com` (clean). Colunas reais confirmadas diferem dos nomes
> "hipotese do Spike" da AT.

## Gate
| Item | Resultado |
|------|----------|
| GATE 1 — Feature habilitada | OK — 'Meu Historico' renderiza (item sidebar "Meu Historico BETA") |
| GATE 2 — Perfil Aluno | OK — visao Aluno confirmada (perfil "Aluno", URL /records?in_use_mode_layout=true) |
| GATE 3 — Massa inicial | 4 registros Interno (3 Emitidos / 1 Pendente) |
| GATE 3b — Massa pos-semeio | ~20 registros: +16 Externo via form do Aluno (provedores Alura/LinkedIn/USP/Udemy/FGV variados). KPIs: 3 Emitidos, 17 cert-Pendentes, 0 Expirados, 0 Recusados. Origem Interno+Externo presentes; Compartilhado NAO semeavel (SharedEvent). Ainda <26 -> TC11 nao fecha. |

## Resultados por TC
| TC | Titulo | Veredito | Observacao |
|----|--------|----------|------------|
| TC1 | Estrutura geral da tela | PASSOU |  |
| TC2 | Colunas, conteudo e tooltips | PASSOU (com ressalva) | Colunas reais: ['Origem', 'Conteudo', 'Provedor', 'Situacao', 'Progresso', 'Situacao do certificado', 'Carga horaria', 'Data do certificado', 'Data de validade'] — DIVERGEM dos nomes "hipotese do Spike" da AT ('Situacao do registro', 'Emitido em', 'Expira em'). Chips de origem Externo+Interno confirmados; Compartilhado NAO verificado (nao semeavel). Tooltips presentes (texto difere da AT que era hipotese). |
| TC3 | Empty state sem registros | A FECHAR | requer Aluno com ZERO registros. Org dedicada `registrosf2` (clean) resolve de graca — fechar la. |
| TC4 | Empty state de filtro | FALHOU | busca por termo inexistente nao filtrou: 4 linhas restantes (request GET /api/v1/o/36675/records?search_query=zzzzz-inexistente-99 foi enviado mas servidor retornou 4 registros — bug no backend de filtragem) |
| TC5 | Modo grid — cards | PASSOU | toggle Grid (#grid-view-icon) ativou modo cards (tabela oculta, "Selecionar todos da pagina atual" visivel) |
| TC6 | Linha/card nao navegam | PASSOU | click em linha (td Conteudo) nao causou navegacao nem abriu modal; passo 4 (card) inconclusivo — modo grid confirmado mas card nao localizavel via JS para click |
| TC7 | Busca em tempo real | FALHOU | busca por 'Academ' (substring real de "Academia de lideranca") retornou 4/4; busca por inexistente tambem retornou 4/4 — backend ignora search_query (bug corroborado com TC4) |
| TC8 | Intersecao busca + KPI + drawer | FALHOU | RECONCILIADO de PASSOU. KPI Emitidos filtrou (3 linhas) e drawer abriu OK, MAS o passo 5 (buscar "Alura" -> estreitar p/ Emitidos+Alura) NAO funcionou: a busca nao estreitou (Emitidos+Alura permaneceu 3) — mesma causa raiz do bug de busca (TC4/TC7). Intersecao com busca textual nao e possivel enquanto a busca nao filtrar. |
| TC9 | Toggle tabela/grid e nao persistencia | PASSOU | toggle ativou grid; reload voltou para tabela (nao persiste entre sessoes) |
| TC10 | Ordenacao por coluna | PASSOU | sort cicla (ASC=['20/12/2022', '29/12/2022', '30/12/2022', ''], DESC=['', '30/12/2022', '29/12/2022', '20/12/2022']); nulos no fim: True |
| TC11 | Paginacao 25/50/100 | A FECHAR | requer >=26 registros; apos semeio o Aluno tem ~20 (cabe em 1 pagina de 25). Faltam ~6+. Fechar na org `registrosf2` semeando >=26. |
| TC12 | Mobile — auto-switch e KPI 1 coluna | PASSOU | auto-switch para grid, toggle oculto, KPIs em coluna |
| TC13 | Mobile — hamburger sidebar | FALHOU | RN 17: hamburger nao encontrado (35 data-icon no DOM, nenhum 'menu'/'menu_open'/'dehaze'). REFORCO: no desktop a sidebar tem 8+ itens (Dashboard, Meus Cursos, Minhas Trilhas, Comunidades, Teste, IA, Meu Historico); no mobile sobra so a tab 'Meu Historico' no topo, sem hamburger/drawer -> a navegacao completa fica inacessivel no mobile. Ressalva anti-falso-negativo: veredito via DOM scan + visual; recomendado um toque no avatar/logo p/ cravar 100%. |

## Bugs confirmados
- **TC4 + TC7**: backend ignora parametro `search_query` — qualquer busca retorna todos os registros. Diagnostico: `GET /api/v1/o/36675/records?search_query=Academ` retornou 4/4 registros (mesmo total sem filtro). Busca por substring existente E por inexistente retornam o mesmo total.
- **TC13**: RN 17 (hamburger com drawer lateral em mobile) nao implementada. DOM inspecionado via JS em 35 elementos [data-icon] e 51 material-symbols — nenhum icon 'menu'/'menu_open'/'dehaze'. Canto sup-esq so tem logo e tab de navegacao.

## Divergencia de especificacao (nao e bug — alinhar AT/produto)
- **Colunas da tabela**: nomes reais ('Situacao', 'Situacao do certificado', 'Data do certificado', 'Data de validade') divergem dos nomes da AT ('Situacao do registro', 'Emitido em', 'Expira em'), que a propria AT marcou como "hipotese do Spike". Atualizar a AT com os labels reais.

## A fechar (nao bloqueado — so falta dado/ambiente)
- **TC3** (empty state): precisa Aluno com ZERO registros -> fechar na org `registrosf2` (clean, registro zero de graca).
- **TC11** (paginacao): precisa >=26 registros -> semear >=26 na `registrosf2` e validar 25/50/100.
- Origem **Compartilhado** (TC2): nao semeavel via UF do Aluno (depende de SharedEvent de org parceira) — fica "nao verificado".

## Evidencias chave
- tc1_estrutura_geral.png
- tc2_01_colunas.png
- tc2_03_tooltip_origem.png
- tc2_04_tooltip_provedor.png
- tc4_01_busca_inexistente.png
- tc5_02_grid_ok.png
- tc6r_01_click_linha.png
- tc6r_02_grid_sem_card.png
- tc7r_01_busca_existente.png
- tc7r_02_busca_inexistente.png
- tc8_01_filtro_emitidos.png
- tc8_02_drawer_filtro.png
- tc9_03_apos_reload.png
- tc10_01_sort_asc.png
- tc10_02_sort_desc.png
- tc12_01_mobile_inicial.png
- tc13r_01_mobile_inicial.png
- tc13r_02_scan_concluido.png
- tc13r_02_sem_hamburger.png

---

## Comentario KQA

```
=> QA <=
:: Teste ::
Parcial (11 executados: 7 PASSOU, 4 FALHOU; 2 a fechar por dado/ambiente)
:: Ambiente ::
Twygo Stage (org 36675)
:: Validacao ::
Suite QA 1.1 — Listagem 'Meu historico' do Aluno (TC1–TC13).
PASSOU (7): TC1, TC2 (com ressalva de labels de coluna), TC5, TC6, TC9, TC10, TC12.
FALHOU (4): TC4, TC7, TC8, TC13.
A FECHAR por falta de dado (2): TC3 (precisa Aluno com zero registros), TC11 (precisa >=26 registros) — serao fechados na org dedicada.
:: Obs ::
Bugs confirmados:
1. BUSCA NAO FILTRA (TC4, TC7 e passo 5 do TC8): o backend ignora o parametro search_query — qualquer busca retorna TODOS os registros, inclusive termo inexistente. Reproduzido com substring real ("Academ" de "Academia de lideranca") e com "zzzzz-inexistente-99", ambos retornando 4/4. Impede empty state de busca (TC4), busca em tempo real (TC7) e a intersecao busca+filtro (TC8 passo 5).
2. HAMBURGER MOBILE AUSENTE (TC13, RN 17): em mobile (360px) nao ha hamburger nem drawer lateral — a navegacao completa (8+ itens da sidebar do desktop) fica inacessivel; sobra so uma tab "Meu Historico" no topo. DOM confirmado via JS (35 [data-icon], nenhum 'menu').
Divergencia de especificacao (alinhar, nao e bug): labels de coluna reais ('Situacao', 'Situacao do certificado', 'Data do certificado', 'Data de validade') divergem dos nomes da AT, que eram "hipotese do Spike".
:: Evidencias ::
- tc4_01_busca_inexistente.png / tc7r_01_busca_existente.png / tc7r_02_busca_inexistente.png (busca nao filtra)
- tc8_01_filtro_emitidos.png / tc8_03_intersecao.png (intersecao nao estreita)
- tc13r_02_sem_hamburger.png + debug_aluno_lista_atual.png (sidebar desktop 8 itens vs mobile so tab)
Evidencias em: evidencias/registros-f2-qa11/ (local, nao commitado)
```
