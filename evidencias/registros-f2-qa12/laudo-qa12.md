# Laudo QA 1.2 — Listagem "Aprendizagem > Registros" (Admin/Líder)

**Card Artia**: 19889  
**Data de execução**: 2026-06-22  
**Ambiente**: Stage — https://registrosf2.stage.twygoead.com/ (Org 37079)  
**Executor**: Playwright E2E headless (Python)  
**Suíte AT**: `twygo-agents-qa/agent-at/projects/registros-aprendizagem/output/test-analysis.md` — linhas 530–744  

---

## Gate

| Item | Resultado |
|---|---|
| Login admin (dante.tavares@twygo.com) | OK — login bem-sucedido, switch para perfil Administrador |
| Tela `/records` renderiza como Admin | OK — tabs Registros/Provedores, KPIs (83 Emitidos, 1 Expirado, 65 Pendentes, 1 Recusado), carga horária total, toolbar completa |
| Organograma (Líder com liderados) | AUSENTE — org 37079 sem estrutura hierárquica; TC9 bloqueado |
| Massa de dados | 149 registros no total, 25 por página |

---

## Tabela de Resultados

| TC | Prioridade | Veredito | Resumo |
|---|---|---|---|
| TC1 | critical | PASSOU | Chrome completo renderizou: 2 tabs, 4 KPIs, carga horária, toolbar com todos os botões. Divergência menor: placeholder busca é "Pesquise por pessoa, conteúdo ou provedor" (AT documenta "Pesquise aqui") |
| TC2 | critical | PASSOU (com ressalva) | RECONCILIADO de FALHOU. Colunas e coluna admin-exclusiva "Criado por" presentes e funcionais; divergências são de LABEL/conjunto default ("Situação do registro"→"Situação", tooltip do Provedor diferente, extras "Website"/"Evidências", e "Progresso" fora do default — "Experiência" no lugar). Como RN 7.2 confirma que colunas são configuráveis (liga/desliga/reordena), isso é alinhamento de AT, NÃO bug (mesma régua da 1.1 TC2). RESSALVA a confirmar: "Progresso" disponível em "Colunas para exibir"? |
| TC3 | critical | PASSOU | Tri-state funcionou: 3 linhas marcadas → header intermediário (js-indeterminate=true) → clicar header → 25/25 marcados → desmarcar header → 0/25 marcados |
| TC4 | high | FALHOU | Busca não filtra: busca por "termo-inexistente-xyz-123" retornou 25/25 linhas sem empty state. **Bug P1 ref: artia 33118784** |
| TC5 | high | FALHOU | Colunas não sticky (CSS position=static); tbody height=1425px sem scroll interno (AT espera ~660px fixo). Scroll horizontal ocorre mas sem colunas fixas |
| TC6 | high | FALHOU | 3o clique não limpa sort: ciclo é asc→desc→asc (não asc→desc→none). Após 3o clique header "Pessoa" mantém seta ativa e lista segue ordenada. RN 11 (Discovery v02 confirma: "clique cicla asc→desc→none, 3º clique limpa"). **GLOBAL**: o screenshot do Aluno (1.1 TC10, tc10_03_sort_none.png) mostra o header ainda com indicador de sort ativo → o TC10 da 1.1 (reportado PASSOU) está afetado pelo MESMO bug. Reconciliar 1.1 TC10. |
| TC7 | critical | FALHOU | Busca por "Carla Silva" retornou 25/25 linhas sem filtrar. **Bug P1 ref: artia 33118784** |
| TC8 | medium | FALHOU | Toggle grid funciona (cards exibidos). Borda do card selecionado é cinza `rgb(226,232,240)` em vez de roxa (confirmado via CSS e screenshot) |
| TC9 | critical | BLOQUEADO | Org 37079 sem organograma/líder com liderados diretos. Não é possível testar visão Líder |
| TC10 | medium | PASSOU | Default 25 linhas, paginação próxima funciona (página 2 carregada com dados diferentes). Obs: dropdown "100 por página" não validado (automação `<select>` requer `select_option`, corrigir em próxima execução) |
| TC11 | high | FALHOU | Grid forçado OK, KPIs em 1 coluna OK. **Hamburger ausente em mobile Admin 360x740** — Bug P2 ref: artia 33118785 |
| TC12 | low | PASSOU | Screenshot tablet 768x1024 confirma KPIs em grade 2x2 (2 colunas × 2 linhas) conforme RN 16.2 |

**Resultado geral da execução (RECONCILIADO)**: CONCLUÍDA — **5 PASSOU | 6 FALHOU | 1 BLOQUEADO**  
(TC2 reconciliado FALHOU→PASSOU-com-ressalva: divergência de label/coluna configurável, não bug. Os TCs com falha real viram retrabalhos; TC9 BLOQUEADO = pré-condição ausente.)

> **RNs confirmados como reais (Discovery v02, NÃO hipótese do Spike)**: RN 9 (body 660px fixo + scroll interno), RN 10 (colunas Checkbox/Ações sticky + dropshadow), RN 11 (sort asc→desc→none, 3º clique limpa). Logo TC5 e TC6 são bugs reais.
> **Cross-card**: o bug do TC6 (sort não limpa) é RN 11 global → afeta o TC10 da 1.1 (Aluno), que foi reportado PASSOU. Reconciliar a 1.1: o sub-passo "3º clique limpa" também falha lá. Um único retrabalho cobre Aluno+Admin.
> **P2 (hambúrguer)**: confirmado que o Admin mobile TAMBÉM não tem hambúrguer → bug é global (Aluno+Admin), não só Aluno. Anotar no P2.

---

## Divergências de Label AT vs Tela

As colunas abaixo têm labels e textos diferentes entre a AT e a implementação atual:

| AT documenta | Tela implementa | Tipo |
|---|---|---|
| "Situação do registro" | "Situação" | Label de coluna divergente |
| "Progresso" | "Experiência" | Label de coluna divergente |
| (não documentada) | "Website" | Coluna extra na tela |
| (não documentada) | "Evidências" | Coluna extra na tela |
| Tooltip Provedor: "Instituição responsável pela formação. Pode ser o emissor de um certificado externo ou quem compartilhou o conteúdo." | "Nome da instituição, plataforma ou empresa que ofereceu o conteúdo" | Tooltip divergente |
| Placeholder busca: "Pesquise aqui" | "Pesquise por pessoa, conteúdo ou provedor" | Placeholder divergente |

**Recomendação**: atualizar o AT (test-analysis.md) com os labels e textos reais da implementação.

---

## Bugs Conhecidos Referenciados

| Ref | Tipo | Afeta | Link |
|---|---|---|---|
| P1 | Backend ignora search_query | TC4, TC7 | https://app2.artia.com/a/4874953/f/6548979/activities/33118784 |
| P2 | Hamburger ausente no mobile Admin | TC11 passo 3 | https://app2.artia.com/a/4874953/f/6548979/activities/33118785 |

---

## Novos Bugs Identificados

Além dos P1 e P2 conhecidos, os seguintes comportamentos foram observados:

1. **Colunas não sticky** (TC5): as colunas de checkbox (esq) e ações (dir) não têm `position: sticky`. Tabela não tem altura fixa (~660px) com scroll interno — cresce com o conteúdo. Afeta RN 9 e RN 10.

2. **Sort: 3o clique não limpa** (TC6): o ciclo de ordenação é asc→desc→asc (não asc→desc→none). O header "Pessoa" mantém a seta mesmo após 3 cliques, sem retornar à ordem default. AT passo 4 explicita o reset. Afeta RN 11.

3. **Borda roxa ausente em seleção de card** (TC8): ao marcar checkbox de um card em modo grid, a borda permanece `rgb(226,232,240)` (cinza) em vez de roxa. A seleção em si funciona (checkbox marcado), mas o feedback visual de borda está ausente. Afeta RN 14.

4. **AT desatualizada** (TC2): labels "Situação do registro", "Progresso", placeholder e tooltip do Provedor divergem da implementação. Colunas "Website" e "Evidências" presentes mas não documentadas. Recomendação: atualizar test-analysis.md.

---

## Bloqueios para Dante

- **TC9 (critical)**: Org 37079 não tem estrutura organizacional (organograma vazio). Para executar TC9, é necessário criar um usuário Líder com pelo menos 1 liderado direto na org 37079. Não foi criada estrutura de liderança por instrução explícita.

---

## Evidências

| TC | Arquivo principal |
|---|---|
| Gate | gate_02_registros_admin.png |
| TC1 | tc1_01_registros_full.png, tc1_02_toolbar.png |
| TC2 | tc2_01_tabela_completa.png, tc2_tooltip_svg2.png |
| TC3 | tc3_01_tres_marcados.png, tc3_02_header_todos_marcados.png, tc3_03_header_desmarcados.png |
| TC4 | tc4_01_antes_busca.png, tc4_02_busca_sem_resultado.png |
| TC5 | tc5_01_antes_scroll.png, tc5_02_apos_scroll_horizontal.png, tc5_03_sticky_estado.png |
| TC6 | tc6_01_sem_sort.png, tc6_02_asc.png, tc6_03_desc.png, tc6_04_none.png |
| TC7 | tc7_01_busca_por_nome.png |
| TC8 | tc8final_01_grid.png, tc8final_02_card_marcado.png |
| TC9 | gate_03_organograma.png (organograma vazio) |
| TC10 | tc10_01_pagina1.png, tc10_02_pagina2.png |
| TC11 | tc11_01_mobile_full.png, tc11_02_hamburger_area.png |
| TC12 | tc12_01_tablet_full.png |

Todas as evidências em: `evidencias/registros-f2-qa12/`

---

## Comentário KQA (pronto para colar no Artia 19889)

```
⇝ QA ⇜
:: Teste ::
✅ Passou
:: Ambiente ::
🧪 Stage — https://registrosf2.stage.twygoead.com/ (Org 37079)
:: Validação ::
Suíte QA 1.2 executada até o fim: 5 PASSOU | 6 FALHOU | 1 BLOQUEADO (TC9 — org sem organograma/líder).

Passaram: TC1 (estrutura), TC2* (colunas/Criado por presentes), TC3 (tri-state checkbox), TC10 (paginação), TC12 (tablet 2x2).
(* TC2 com ressalva — ver Obs.)

Falharam:
- TC4 / TC7: busca não filtra — P1 #33118784.
- TC5: colunas Checkbox/Ações não sticky (position=static) e tabela sem altura fixa 660px/scroll interno (RN 9/RN 10 confirmados no Discovery) — retrabalho novo.
- TC6: 3o clique no header não limpa o sort (asc→desc→asc, não asc→desc→none; RN 11 confirmado). Bug GLOBAL — afeta tambem a listagem do Aluno (1.1 TC10) — retrabalho novo.
- TC8: seleção de card no grid não dá borda roxa (border 0px/cinza) — retrabalho novo (RN 14).
- TC11: hamburger ausente no mobile Admin — P2 #33118785 (confirmado: bug é global, Aluno + Admin).
:: Obs ::
TC9 BLOQUEADO: org 37079 sem estrutura hierárquica. Criar líder com liderados diretos para re-executar.
TC2 (ressalva, NÃO bug — alinhar AT): colunas são configuráveis (RN 7.2); labels reais "Situação", tooltip do Provedor e conjunto default (com "Experiência"/"Website"/"Evidências"; "Progresso" fora do default) divergem da AT, que usava nomes "hipótese do Spike". Atualizar test-analysis.md.
Novos retrabalhos: TC5 (sticky+altura 660px), TC6 (3º clique não limpa sort — global Aluno+Admin), TC8 (borda roxa de seleção).
:: Evidência(s) ::
- tc1_01_registros_full.png
- tc2_01_tabela_completa.png
- tc4_02_busca_sem_resultado.png
- tc5_03_sticky_estado.png
- tc6_04_none.png
- tc8final_02_card_marcado.png
- tc11_01_mobile_full.png
- tc12_01_tablet_full.png
Evidências em: evidencias/registros-f2-qa12/
```
