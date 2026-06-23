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

## 4. P1 [Registros] Visão do Gestor de turma não filtra por liderados diretos — exibe org inteira

**Onde:** Aprendizagem > Registros, perfil "Gestor de turma" — https://registrosf2.stage.twygoead.com/

**Problema:** O usuário com papel de Gestor de turma (líder no organograma) acessa Aprendizagem > Registros e visualiza os registros de toda a organização — KPIs idênticos ao Admin (260 Emitidos, 13 Expirados, 80 Pendentes, 13 Recusados) e lista com pessoas fora do seu time. O liderado direto (`liderado1@teste.com`) não aparece na lista sem filtro de busca.

**Esperado (RN 6.2):** a tela de Registros no perfil Gestor de turma deve listar apenas os registros dos liderados diretos do líder. KPIs devem refletir apenas o time (menores ou iguais à org inteira). Usuários que não são liderados diretos não devem aparecer.

**Reprodução:**
1. Login como `qalider@teste.com` (organograma: liderado direto = `liderado1@teste.com`)
2. Seletor de perfil → mudar para "Gestor de turma"
3. Aprendizagem > Registros
4. Resultado: 260 Emitidos (org inteira), lista com qa11tc342816@twygotest.com (não é liderado)

**Evidência:** tc9_step1_registros_lider.png, tc9_crosscheck_nao_liderado.png, tc9_crosscheck_liderado.png, tc9g_02_dropdown_perfil.png

---

## Pendências (não são retrabalho)

- **TC2 (alinhar AT, não bug):** colunas configuráveis (RN 7.2); labels reais "Situação", tooltip do Provedor e conjunto default ("Experiência"/"Website"/"Evidências"; "Progresso" fora do default) divergem da AT. Atualizar test-analysis.md.
- **Reconciliar QA 1.1 TC10:** veredito PASSOU deve virar FALHOU pelo mesmo bug do retrabalho #2 (sort não limpa).
