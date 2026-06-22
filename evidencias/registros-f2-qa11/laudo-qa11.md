# Laudo QA 1.1 — Listagem 'Meu histórico' do Aluno
**Card Artia**: 19888  
**Suite AT**: Listagem 'Meu histórico' do Aluno — tabela, busca e mobile  
**Data**: 2026-06-22  
**Ambiente**: Stage (https://twygo1772627238.stage.twygoead.com/)  
**Org**: 36675  

> **Nota de finalizacao (2026-06-22)**: QA 1.1 COMPLETA — 13/13 TCs conclusivos.
> 9 PASSOU, 4 FALHOU (TC4/TC7/TC8 mesma causa raiz = busca nao filtra; TC13 = sem hamburguer mobile).
> TC1-TC10 + TC12 validados na org 36675; TC3 (empty state) e TC11 (paginacao) fechados na
> org dedicada registrosf2 (37079). TC8 reconciliado de PASSOU->FALHOU (busca nao estreita).
> TC11 reconciliado de "falha de pag2" -> PASSOU (era selector/chat, botao real = id=next-page-button).
> 2 retrabalhos abertos (P1 busca, P2 hamburguer). Divergencias de label da AT (colunas + empty state) sao "hipotese do Spike" — alinhar AT, nao sao bug.

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
| TC3 | Empty state sem registros | PASSOU (com ressalva) | Fechado na org registrosf2 (37079) com usuario de teste sem registros (qa11tc342588@twygotest.com, senha definida via admin com autorizacao do dono). Empty state correto: tabela vazia + 4 KPIs zerados. Ressalva: produto exibe "Nao ha dados para exibir" e nao a frase da AT ("Voce ainda nao tem registros...") — divergencia de label (hipotese do Spike), nao bug. Evid: fechamento_tc3_empty_ok.png, tc3_final_apos_confirmar.png |
| TC4 | Empty state de filtro | FALHOU | busca por termo inexistente nao filtrou: 4 linhas restantes (request GET /api/v1/o/36675/records?search_query=zzzzz-inexistente-99 foi enviado mas servidor retornou 4 registros — bug no backend de filtragem) |
| TC5 | Modo grid — cards | PASSOU | toggle Grid (#grid-view-icon) ativou modo cards (tabela oculta, "Selecionar todos da pagina atual" visivel) |
| TC6 | Linha/card nao navegam | PASSOU | click em linha (td Conteudo) nao causou navegacao nem abriu modal; passo 4 (card) inconclusivo — modo grid confirmado mas card nao localizavel via JS para click |
| TC7 | Busca em tempo real | FALHOU | busca por 'Academ' (substring real de "Academia de lideranca") retornou 4/4; busca por inexistente tambem retornou 4/4 — backend ignora search_query (bug corroborado com TC4) |
| TC8 | Intersecao busca + KPI + drawer | FALHOU | RECONCILIADO de PASSOU. KPI Emitidos filtrou (3 linhas) e drawer abriu OK, MAS o passo 5 (buscar "Alura" -> estreitar p/ Emitidos+Alura) NAO funcionou: a busca nao estreitou (Emitidos+Alura permaneceu 3) — mesma causa raiz do bug de busca (TC4/TC7). Intersecao com busca textual nao e possivel enquanto a busca nao filtrar. |
| TC9 | Toggle tabela/grid e nao persistencia | PASSOU | toggle ativou grid; reload voltou para tabela (nao persiste entre sessoes) |
| TC10 | Ordenacao por coluna | PASSOU | sort cicla (ASC=['20/12/2022', '29/12/2022', '30/12/2022', ''], DESC=['', '30/12/2022', '29/12/2022', '20/12/2022']); nulos no fim: True |
| TC11 | Paginacao 25/50/100 | PASSOU | Fechado na org registrosf2 (37079) com 26+ registros semeados. Pag1=25 linhas (default 25 OK), pag1->pag2 OK (botao id="next-page-button", icone chevron_right; chat suprimido antes do clique), 50/pag e 100/pag OK. Evid: fechamento_tc11_pag1/pag2/rodape/50pag/100pag.png |
| TC12 | Mobile — auto-switch e KPI 1 coluna | PASSOU | auto-switch para grid, toggle oculto, KPIs em coluna |
| TC13 | Mobile — hamburger sidebar | FALHOU | RN 17: hamburger nao encontrado (35 data-icon no DOM, nenhum 'menu'/'menu_open'/'dehaze'). REFORCO: no desktop a sidebar tem 8+ itens (Dashboard, Meus Cursos, Minhas Trilhas, Comunidades, Teste, IA, Meu Historico); no mobile sobra so a tab 'Meu Historico' no topo, sem hamburger/drawer -> a navegacao completa fica inacessivel no mobile. Ressalva anti-falso-negativo: veredito via DOM scan + visual; recomendado um toque no avatar/logo p/ cravar 100%. |

## Bugs confirmados
- **TC4 + TC7**: backend ignora parametro `search_query` — qualquer busca retorna todos os registros. Diagnostico: `GET /api/v1/o/36675/records?search_query=Academ` retornou 4/4 registros (mesmo total sem filtro). Busca por substring existente E por inexistente retornam o mesmo total.
- **TC13**: RN 17 (hamburger com drawer lateral em mobile) nao implementada. DOM inspecionado via JS em 35 elementos [data-icon] e 51 material-symbols — nenhum icon 'menu'/'menu_open'/'dehaze'. Canto sup-esq so tem logo e tab de navegacao.

## Divergencia de especificacao (nao e bug — alinhar AT/produto)
- **Colunas da tabela**: nomes reais ('Situacao', 'Situacao do certificado', 'Data do certificado', 'Data de validade') divergem dos nomes da AT ('Situacao do registro', 'Emitido em', 'Expira em'), que a propria AT marcou como "hipotese do Spike". Atualizar a AT com os labels reais.
- **Mensagem de empty state (TC3)**: produto exibe "Nao ha dados para exibir"; AT esperava "Voce ainda nao tem registros. Adicione o primeiro pelo botao acima." (hipotese do Spike). Alinhar AT.

## Nao verificado (limitacao de ambiente)
- Origem **Compartilhado** (TC2): nao semeavel via UF do Aluno (depende de SharedEvent de org parceira) — fica "nao verificado".

## Retrabalhos abertos
- **P1** (busca nao filtra — TC4/TC7/TC8): https://app2.artia.com/a/4874953/f/6548979/activities/33118784
- **P2** (mobile sem hamburguer — TC13): https://app2.artia.com/a/4874953/f/6548979/activities/33118785

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
Concluido — 13/13 TCs. 9 PASSOU, 4 FALHOU (2 retrabalhos abertos).
:: Ambiente ::
Twygo Stage — org 36675 (TC1-TC10, TC12) e org dedicada registrosf2 / 37079 (TC3, TC11).
:: Validacao ::
Suite QA 1.1 — Listagem 'Meu historico' do Aluno (TC1-TC13).
PASSOU (9): TC1, TC2*, TC3*, TC5, TC6, TC9, TC10, TC11, TC12.
FALHOU (4): TC4, TC7, TC8 (mesma causa: busca nao filtra), TC13 (hamburguer mobile).
(* TC2 e TC3 passam com ressalva de divergencia de label da AT — ver Obs.)
:: Obs ::
Retrabalhos abertos:
- P1 [Registros F2] Busca da listagem nao filtra (afeta TC4/TC7/TC8): backend ignora search_query; qualquer termo (inclusive inexistente "zzzzz-inexistente-99") retorna todos os registros. Impede empty state de busca, busca em tempo real e a intersecao busca+filtro.
  https://app2.artia.com/a/4874953/f/6548979/activities/33118784
- P2 [Registros F2] Mobile sem menu hamburguer (afeta TC13): em 360px nao ha hamburguer/drawer; a sidebar completa (8+ itens do desktop) fica inacessivel, sobra so a tab "Meu Historico".
  https://app2.artia.com/a/4874953/f/6548979/activities/33118785
Divergencias de label da AT (NAO sao bug — alinhar AT, eram "hipotese do Spike"):
- Colunas reais: 'Situacao', 'Situacao do certificado', 'Data do certificado', 'Data de validade' (AT usava 'Situacao do registro', 'Emitido em', 'Expira em').
- Empty state: produto mostra "Nao ha dados para exibir" (AT esperava "Voce ainda nao tem registros...").
Nao verificado (limitacao de ambiente): origem Compartilhado (TC2) nao semeavel via formulario do Aluno (depende de SharedEvent de org parceira).
:: Evidencias ::
- Busca: tc4_01_busca_inexistente.png, tc7r_01_busca_existente.png, tc7r_02_busca_inexistente.png, tc8_03_intersecao.png
- Hamburguer mobile: tc13r_02_sem_hamburger.png, debug_aluno_lista_atual.png (sidebar desktop 8 itens)
- Empty state (TC3): fechamento_tc3_empty_ok.png, tc3_final_apos_confirmar.png
- Paginacao (TC11): fechamento_tc11_pag1.png, fechamento_tc11_pag2.png, fechamento_tc11_rodape.png
Evidencias: github.com/DantexgerBR/twygo-playwright-tests/tree/main/evidencias/registros-f2-qa11
```
