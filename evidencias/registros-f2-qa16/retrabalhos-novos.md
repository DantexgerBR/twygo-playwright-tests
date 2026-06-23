# Retrabalhos Novos — QA 1.6 Registros F2

**Data**: 2026-06-23 (atualizado rounds 1+2)  
**Card de origem**: Artia 19893

---

## P1 [Registros F2] Gestor de turma recebe 401 ao vincular pessoas no form de registro (TC3)

**Prioridade**: P1  
**Perfil afetado**: Lider / Gestor de turma (qalider@teste.com)  
**Comportamento**: Ao abrir o form em `/records/new` como Lider e clicar no campo "Adicionar pessoas", o modal "Vincular pessoas" abre mas retorna "Nenhum item encontrado" e exibe toast de erro HTTP 401. Liderado nao aparece na lista.  
**Causa**: 12 requisicoes retornam 401 (Unauthorized): `GET /api/v1/o/37079/professionals`, `/professionals/results_for_filter`, `/event_sources/get_provider_names`. Lider nao tem autorizacao nesses endpoints.  
**Esperado**: RN 93 — modal deve listar liderados diretos do Gestor de turma.  
**Impacto**: Gestor de turma completamente bloqueado de criar registros para seus liderados.  
**Evidencias**: `tc3b_lider_modal_apos_click.png` (toast 401 visivel), `tc3b_lider_form.png`  
Link: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc3b_lider_modal_apos_click.png

---

## P2 [Registros F2] API de provedores retorna 401 para o perfil Aluno (TC7)

**Prioridade**: P2  
**Perfil afetado**: Aluno / Colaborador  
**Comportamento**: Ao abrir o form de Adicionar registro como Aluno, o dropdown "Provedor" fica completamente vazio. API `GET /api/v1/o/37079/event_sources/get_provider_names` retorna 401.  
**Causa**: Bug de autorizacao no endpoint — Aluno nao tem permissao para listar provedores. Admin ve a lista completa normalmente (Alura, Coursera, FGV, LinkedIn Learning, Nocode, Udemy, USP). Nao e massa de dados faltando.  
**Workaround**: Aluno pode criar provedor inline digitando o nome (opcao "Criar [nome]" aparece no dropdown). TC14 confirmou que o registro salva com provedor criado inline.  
**Esperado**: RN 39.2 — lista de provedores disponivel para o Aluno selecionar.  
**Evidencias**: `tc7b_02_provedor_aluno_vazio.png` (dropdown vazio, API 401)  
Link: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc7b_02_provedor_aluno_vazio.png

---

## Divergencia a alinhar (nao e bug de produto — necessita decisao)

### TC5 — "Tipo de experiencia" e creatable-select, nao lista fixa de 8 opcoes

**Tipo**: Divergencia AT vs implementacao  
**Observado**: Campo e `creatable-select` (opcoes cadastraveis). Stage 37079 tem apenas 2 opcoes ("Treinamento", "Curso") vs 8 fixas esperadas pela AT ("Curso", "Trilha", "Workshop", "Mentoria", "Palestra", "Evento", "Aula", "Outro").  
**Ponto de alinhamento**: As 8 opcoes sao seed obrigatorio (stage com dados incompletos) ou o campo e intencionalmente livre por org? Se seed, popular a stage 37079. Se livre, atualizar test-analysis.md.  
**Evidencia**: `tc5b_01_dropdown_aberto.png`  
Link: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc5b_01_dropdown_aberto.png

---

## Nao verificado (limitacao de automacao headless)

### TC15 — Origem Admin (Externo + Emitido/Aprovado)

**Motivo**: Campo "Adicionar pessoas" usa handler React que nao responde a eventos sinteticos do Playwright headless. Modal confirmado funcional no recon (lista pessoas com checkboxes). Verificacao manual necessaria.  
**Acao**: Admin abre form, clica "Adicionar pessoas" no browser real, seleciona liderado, preenche campos, salva. AT espera registro com chip **Externo** e situacao **Emitido** (ou Aprovado).

---

## TCs que PASSARAM (removidos dos retrabalhos)

- TC8 — Validacao "Carga horaria e obrigatorio" funciona
- TC12 — clearError funciona ao digitar no campo com erro
- TC14 — Registro Aluno salvo corretamente como Externo + Pendente

---

## Obs: Divergencias AT (nao sao bugs de produto)

1. Titulo do form: "Novo conteudo externo" vs AT "Adicionar registro de aprendizagem"
2. Campo Pessoas: multi-select via modal vs AT dropdown singular; Aluno tambem ve o campo
3. Botoes: "Salvar" vs AT "Enviar para aprovacao" (Aluno) / "Salvar e aprovar" (Admin)
4. Renomeacoes: Nota->Desempenho, Anotacoes->Descricao, Comprovacao->Evidencia
5. Placeholders: Carga horaria `HH:MM:SS` vs AT `Ex: 40`

Recomendacao: atualizar test-analysis.md suíte 1.6 com labels reais do produto.
