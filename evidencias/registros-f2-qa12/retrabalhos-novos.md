# Retrabalhos novos — QA 1.2 Registros F2 (card 19889)

Bugs reais confirmados no Discovery v02 (RN 9, 10, 11, 14). Texto pronto para abrir no Artia.

---

## 1. P2 [Registros] Listagem: colunas de seleção e ações não fixam ao rolar e tabela cresce sem scroll interno

**Onde:** Aprendizagem > Registros (visão Admin e Aluno) — https://registrosf2.stage.twygoead.com/

**Problema:** Ao rolar a tabela horizontalmente, a coluna de checkbox (esquerda) e a coluna de ações (direita) não permanecem fixas — estão com `position: static`. Além disso, o corpo da tabela não tem altura fixa: cresce com o conteúdo (tbody medido em 1425px), forçando o scroll da página inteira em vez de scroll interno.

**Esperado:** corpo da tabela com altura fixa (~660px) e scroll vertical interno; colunas de seleção e de ações fixas nas bordas (com dropshadow) ao rolar horizontalmente.

**Evidência:** tc5_01_antes_scroll.png, tc5_02_apos_scroll_horizontal.png, tc5_03_sticky_estado.png

---

## 2. P2 [Registros] Ordenação por coluna não limpa no 3º clique (afeta Admin e Aluno)

**Onde:** Aprendizagem > Registros (Admin) e Meu Histórico (Aluno).

**Problema:** O ciclo de ordenação ao clicar no cabeçalho de uma coluna é crescente → decrescente → crescente. Após o 3º clique o cabeçalho mantém a seta ativa e a lista segue ordenada, sem voltar à ordem padrão. Bug **global**: confirmado tanto na listagem do Admin quanto na do Aluno (reconciliar a QA 1.1 TC10, que havia saído PASSOU) — um único ajuste cobre as duas telas.

**Esperado:** ciclo crescente → decrescente → nenhum; o 3º clique remove o indicador de ordenação e retorna a lista à ordem padrão.

**Evidência:** tc6_01_sem_sort.png, tc6_02_asc.png, tc6_03_desc.png, tc6_04_none.png

---

## 3. P3 [Registros] Card selecionado no modo grade não recebe destaque de seleção

**Onde:** Aprendizagem > Registros, modo de visualização em grade (cards).

**Problema:** Ao marcar o checkbox de um card, a seleção funciona (checkbox marcado), mas o card não recebe a borda de destaque — permanece com a borda cinza padrão (`rgb(226,232,240)`) em vez da cor de seleção.

**Esperado:** card selecionado destacado visualmente com borda colorida (roxa).

**Evidência:** tc8final_01_grid.png, tc8final_02_card_marcado.png

---

## Pendências (não são retrabalho)

- **TC9 BLOQUEADO:** org 37079 sem organograma/líder com liderados. Criar líder + liderado direto para executar a visão Líder.
- **TC2 (alinhar AT, não bug):** colunas configuráveis (RN 7.2); labels reais "Situação", tooltip do Provedor e conjunto default ("Experiência"/"Website"/"Evidências"; "Progresso" fora do default) divergem da AT. Atualizar test-analysis.md.
- **Reconciliar QA 1.1 TC10:** veredito PASSOU deve virar FALHOU pelo mesmo bug do retrabalho #2 (sort não limpa).
