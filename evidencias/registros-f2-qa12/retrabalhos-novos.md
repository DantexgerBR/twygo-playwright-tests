# Retrabalhos novos — QA 1.2 Registros F2 (card 19889)

Bugs reais confirmados na execução de 2026-06-22/23, alinhados às RNs do Discovery v02 (RN 6.2, 9, 10, 11, 14). Texto pronto para abrir no Artia.

> Base das evidências (GitHub): `https://github.com/DantexgerBR/twygo-playwright-tests/tree/main/evidencias/registros-f2-qa12`

---

## 1. P2 [Registros] Listagem: colunas de seleção e ações não fixam ao rolar e tabela cresce sem scroll interno

**Onde:** Aprendizagem > Registros (visão Admin e Aluno) — https://registrosf2.stage.twygoead.com/ (org 37079)

**Problema:** A listagem de Registros não segue o comportamento de tabela com bordas fixas e corpo rolável previsto nas RN 9 e RN 10:

1. **Colunas não sticky (RN 10):** a primeira coluna (checkbox de seleção) e a última (ações) deveriam permanecer fixas nas bordas enquanto o usuário rola a tabela horizontalmente, com dropshadow para indicar a fixação. Na implementação atual ambas têm `position: static` — ao rolar para a direita, o checkbox e os botões de ação saem da viewport junto com o resto das colunas. Em telas estreitas ou com muitas colunas habilitadas, o usuário perde a referência de qual linha está selecionando e fica sem acesso às ações sem rolar de volta.
2. **Tabela sem altura fixa / sem scroll interno (RN 9):** o corpo da tabela (`tbody`) deveria ter altura fixa de ~660px com scroll vertical próprio, mantendo cabeçalho, KPIs e toolbar visíveis. Em vez disso o `tbody` cresce com o conteúdo (medido em **1425px** com 25 linhas), empurrando o rodapé/paginação para baixo e forçando o scroll da página inteira — o cabeçalho da tabela some ao rolar.

**Impacto:** usabilidade da listagem degradada (perda de contexto de coluna/linha ao navegar), pior em listas longas e em telas menores. Não há perda de dado.

**Esperado:** corpo da tabela com altura fixa (~660px) e scroll vertical interno; colunas de checkbox (esquerda) e ações (direita) fixas nas bordas, com dropshadow, ao rolar horizontalmente.

**Reprodução:**
1. Abrir Aprendizagem > Registros como Admin.
2. Rolar a tabela horizontalmente → as colunas de checkbox e ações acompanham o scroll (não ficam fixas).
3. Observar a altura do `tbody` (cresce com o conteúdo) e o scroll ocorrendo na página, não dentro da tabela.

**Evidências:**
- Antes do scroll: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa12/tc5_01_antes_scroll.png
- Após scroll horizontal (colunas não fixas): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa12/tc5_02_apos_scroll_horizontal.png
- Estado do sticky / altura medida: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa12/tc5_03_sticky_estado.png

---

## 2. P2 [Registros] Ordenação por coluna não limpa no 3º clique (afeta listagem Admin e Aluno)

**Onde:** Aprendizagem > Registros (Admin) e Meu Histórico (Aluno) — https://registrosf2.stage.twygoead.com/

**Problema:** A RN 11 define o ciclo de ordenação ao clicar repetidamente no cabeçalho de uma coluna como **crescente → decrescente → nenhum** (o 3º clique limpa a ordenação e devolve a lista à ordem padrão). Na implementação atual o ciclo é **crescente → decrescente → crescente**: após o 3º clique o cabeçalho continua exibindo a seta de ordenação ativa e a lista permanece ordenada, sem nunca retornar ao estado neutro. O usuário não consegue "desligar" a ordenação que aplicou.

**Bug global (Admin + Aluno):** o mesmo comportamento foi observado na listagem do Aluno (Meu Histórico). Na QA 1.1 o TC10 (ordenação) havia saído PASSOU porque o sub-passo do 3º clique não foi conferido — a evidência do Aluno mostra o cabeçalho ainda com indicador de sort ativo após o 3º clique. **Um único ajuste cobre as duas telas**; a QA 1.1 TC10 deve ser reconciliada para FALHOU.

**Impacto:** funcional/UX — divergência do comportamento especificado; o usuário fica preso à ordenação aplicada. Sem perda de dado.

**Esperado:** ciclo crescente → decrescente → nenhum; no 3º clique o indicador de ordenação some do cabeçalho e a lista volta à ordem padrão.

**Reprodução:**
1. Abrir Aprendizagem > Registros (ou Meu Histórico no Aluno).
2. Clicar no cabeçalho "Pessoa" → ordena crescente.
3. Clicar de novo → ordena decrescente.
4. Clicar uma 3ª vez → esperado: limpa; observado: volta a crescente, com a seta ainda ativa.

**Evidências:**
- Sem ordenação (estado inicial): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa12/tc6_01_sem_sort.png
- 1º clique (crescente): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa12/tc6_02_asc.png
- 2º clique (decrescente): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa12/tc6_03_desc.png
- 3º clique (deveria limpar, mas mantém a seta): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa12/tc6_04_none.png

---

## 3. P3 [Registros] Card selecionado no modo grade não recebe destaque de seleção

**Onde:** Aprendizagem > Registros, modo de visualização em grade (cards) — https://registrosf2.stage.twygoead.com/

**Problema:** No modo grade, ao marcar o checkbox de um card a seleção é registrada corretamente (o checkbox fica marcado e o card entra na seleção em massa), mas o card **não recebe o destaque visual de borda** previsto na RN 14. A borda permanece na cor cinza padrão (`rgb(226,232,240)`) em vez da cor de seleção (roxa). Resultado: visualmente é difícil distinguir, num grid com vários cards, quais estão selecionados — só o estado do checkbox sinaliza.

**Impacto:** feedback visual de seleção ausente no modo grade; baixo risco (a seleção funciona), mas prejudica a leitura de quais itens estão marcados antes de uma ação em massa.

**Esperado:** card selecionado destacado com borda colorida (roxa), coerente com o estado do checkbox.

**Reprodução:**
1. Abrir Aprendizagem > Registros e alternar para o modo grade (cards).
2. Marcar o checkbox de um card.
3. Observar: checkbox marcado, mas a borda do card segue cinza (`rgb(226,232,240)`).

**Evidências:**
- Grid ativo: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa12/tc8final_01_grid.png
- Card marcado sem borda de destaque: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa12/tc8final_02_card_marcado.png

---

## 4. P1 [Registros] Visão do líder (Gestor de turma) não filtra por liderados diretos — exibe a organização inteira

**Onde:** Aprendizagem > Registros, perfil "Gestor de turma" — https://registrosf2.stage.twygoead.com/ (org 37079)

**Problema:** A RN 6.2 determina que o líder veja a **mesma tela do Admin** (tabs, KPIs, toolbar, colunas), porém listando **apenas os registros dos seus liderados diretos**, com os KPIs refletindo só o time. Na implementação atual o escopo do líder não é aplicado: o usuário com papel de Gestor de turma vê os registros da organização inteira, exatamente como o Admin.

Evidências do escopo não aplicado, testadas com o organograma `qalider@teste.com` (líder) → `liderado1@teste.com` (liderado direto, com 1 registro na org):
- **KPIs idênticos ao Admin:** 260 Emitidos / 13 Expirados / 80 Pendentes / 13 Recusados — os mesmos números da org inteira, quando deveriam refletir apenas o time (1 liderado, 1 registro).
- **Lista com pessoas fora do time:** sem busca, a listagem exibe `qa11tc342816@twygotest.com` (que **não** é liderado direto de qalider) em todas as 25 linhas visíveis.
- **Liderado direto não aparece:** o `liderado1@teste.com` não consta na lista sem busca; buscar por "liderado" retorna "Não há dados para exibir".

> Obs.: a busca por `qa11tc342816` também retorna "Não há dados", inconsistente com a lista sem busca — reflexo do bug P1 da busca (#33118784, TC4/TC7), que afeta também a visão Gestor.

O comportamento foi reproduzido em mais de um perfil candidato a "líder" (Gestor de turma e perfil de colaborador-líder), todos exibindo o escopo da org inteira.

**Impacto:** **vazamento de escopo** — um líder enxerga registros de aprendizagem de pessoas que não são seus liderados (org inteira), o que pode expor dados de toda a organização a quem deveria ver só o próprio time. Prioridade P1.

**Esperado (RN 6.2):** a tela de Registros no perfil de líder lista apenas os registros dos liderados diretos; os KPIs ("Emitidos", "Expirados", "Pendentes", "Recusados") contam apenas os registros do time (valores menores ou iguais aos da org inteira); pessoas que não são liderados diretos não aparecem.

**Reprodução:**
1. Login como `qalider@teste.com` (organograma: liderado direto = `liderado1@teste.com`).
2. Seletor de perfil → mudar para "Gestor de turma".
3. Acessar Aprendizagem > Registros.
4. Observado: KPIs 260/13/80/13 (org inteira); lista com `qa11tc342816@twygotest.com` (não-liderado); `liderado1` ausente.

**Evidências:**
- Registros na visão do líder (org inteira): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa12/tc9_step1_registros_lider.png
- KPIs do líder idênticos ao Admin: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa12/tc9_18_lider_kpis.png
- Cross-check — não-liderado listado: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa12/tc9_crosscheck_nao_liderado.png
- Cross-check — liderado direto ausente: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa12/tc9_crosscheck_liderado.png
- Seletor de perfil (Gestor de turma): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa12/tc9g_02_dropdown_perfil.png

---

## Pendências (não são retrabalho)

- **TC2 (alinhar AT, não bug):** colunas configuráveis (RN 7.2); labels reais "Situação", tooltip do Provedor e conjunto default ("Experiência"/"Website"/"Evidências"; "Progresso" fora do default) divergem da AT. Atualizar test-analysis.md.
- **Reconciliar QA 1.1 TC10:** veredito PASSOU deve virar FALHOU pelo mesmo bug do retrabalho #2 (sort não limpa no 3º clique).
