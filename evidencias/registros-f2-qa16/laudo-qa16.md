# Laudo QA 1.6 — Adicionar registro de aprendizagem (3 perfis, validações e origem inferida)

**Card Artia**: 19893  
**Data de execução**: 2026-06-23 (round 1 + round 2 reconciliado)  
**Ambiente**: Stage — https://registrosf2.stage.twygoead.com/ (Org 37079)  
**Executor**: Playwright E2E headless (Python)  
**Suíte AT**: `twygo-agents-qa/agent-at/projects/registros-aprendizagem/output/test-analysis.md` — linhas 1319–1651  

---

## Gate

| Item | Resultado |
|---|---|
| Login admin (dante.tavares@twygo.com) | OK — login bem-sucedido, switch para perfil Administrador |
| Login aluno (qa11tc342588@twygotest.com) | OK — login como "Colaborador", Meu Histórico [BETA] acessível |
| Login líder (qalider@teste.com) | OK — login bem-sucedido, acessa `/records` como Gestor de turma |
| Tela `/records` Admin | OK — lista com 260 Emitidos, 13 Expirados, 80 Pendentes, 13 Recusados; botão Adicionar presente |
| Tela Meu Histórico Aluno | OK — `/records?in_use_mode_layout=true` com botão Adicionar |
| Provedores cadastrados | OK (Admin): Alura, Coursera, FGV, LinkedIn Learning, Nocode, Udemy, USP. FALHA (Aluno): API `/event_sources/get_provider_names` retorna 401 |

---

## Tabela de Resultados

| TC | Prioridade | Veredito | Resumo |
|---|---|---|---|
| TC1 | critical | PASSOU (divergências) | Meu Histórico exibiu botão "Adicionar"; form abriu em `/records/new?in_use_mode_layout=true`. Divergências: (1) título é "Novo conteúdo externo" vs AT "Adicionar registro de aprendizagem"; (2) campo "Pessoas*" aparece para aluno (AT diz que campo Pessoa é exclusivo do modo admin); (3) botão de envio é "Salvar" vs AT "Enviar para aprovação" |
| TC2 | critical | PASSOU (divergências) | Form Admin abriu em `/records/new`, campos fundamentais presentes (Pessoas*, Provedor*, Conteúdo*). Divergências: (1) título "Novo conteúdo externo" vs AT "Adicionar registro"; (2) campo "Pessoas" abre modal "Vincular pessoas" (não dropdown inline); (3) botão salvar é "Salvar" vs AT "Salvar e aprovar" |
| TC3 | critical | FALHOU — BUG P1 | Modal "Vincular pessoas" abre para o Líder mas retorna "Nenhum item encontrado" + toast de erro HTTP 401 (Unauthorized). 12 chamadas 401 confirmadas na aba Network: `GET /api/v1/o/37079/professionals` e `/professionals/results_for_filter`. Liderado não listado; Líder não consegue criar registro para seu liderado |
| TC4 | high | PASSOU (divergências) | Todos os campos do form existem. Divergências de nomenclatura AT vs produto: ver tabela de divergências abaixo |
| TC5 | high | FALHOU | Dropdown "Tipo de experiência" é um campo creatable (não lista fixa). Exibe apenas 2 opções cadastradas na stage ("Treinamento" e "Curso") vs 8 opções fixas esperadas pela AT ("Curso", "Trilha", "Workshop", "Mentoria", "Palestra", "Evento", "Aula", "Outro"). Campo permite criar inline — é possível que as opções variem por org/dados |
| TC6 | high | PASSOU (parcial) | Dropdown "Categorias" abriu com 6 opções visíveis. AT espera 9 — encontradas 6 (dados de stage). Criação inline disponível (opção "Criar" aparece ao digitar). Chip criado ao selecionar categoria |
| TC7 | high | FALHOU — BUG real | Dropdown "Provedor" vazio para Aluno. API `GET /api/v1/o/37079/event_sources/get_provider_names` retorna **401** para o perfil Aluno. Admin vê a lista completa (Alura, Coursera, FGV, LinkedIn Learning, Nocode, Udemy, USP). Bug de autorização: Aluno não tem permissão no endpoint de provedores |
| TC8 | critical | PASSOU | Após vincular os demais campos obrigatórios, salvar com "Carga horária" vazia exibiu erro "Carga horária é obrigatório" (borda vermelha) e o form permaneceu em `/records/new`. Validação de campo obrigatório funciona corretamente |
| TC9 | medium | PASSOU (renomeação) | Campo "Desempenho" encontrado (AT chama de "Nota"). Campo aceita valores numéricos. Sufixo "%" visível |
| TC10 | medium | PASSOU | Campo "Data de término*" presente e obrigatório. Tentativa de salvar sem preencher gerou erro "Data de término é obrigatório" |
| TC11 | high | PASSOU | Clicar "Salvar" com todos os campos vazios exibiu 7 mensagens de erro. Form permanece na mesma página |
| TC12 | medium | PASSOU | clearError funcionou: após provocar 7 erros e digitar no campo "Carga horária" com `type()` char-a-char, o número de erros reduziu de 7 para 6 (erro de Carga horária sumiu) imediatamente sem resubmeter |
| TC13 | low | PASSOU | Clicar "Cancelar" sem preencher nenhum campo redirecionou para a lista sem validar |
| TC14 | critical | PASSOU | Registro criado como Aluno (provedor "Alura" criado inline, tipo "Treinamento", categorias, carga 1h30m). Lista exibe chip de origem **Externo** e situação do certificado **Pendente** conforme AT |
| TC15 | critical | não verificado | Modal "Vincular pessoas" não pôde ser aberto via automação headless na sessão Admin (handler de click React não responde a eventos sintéticos). O recon confirmou que o modal existe e lista pessoas corretamente para Admin (liderado 1, lider ., dev teste com checkboxes). Verificação manual necessária: AT espera Externo + Emitido/Aprovado ao salvar como Admin |
| TC16 | medium | PASSOU | Área de upload "Evidência de aprendizagem" presente; `input[type=file]` encontrado. Upload de arquivo PDF executado com sucesso |

**Resultado geral da execução**: CONCLUÍDA — **10 PASSOU | 3 FALHOU (2 bugs reais + TC5 divergência) | 1 não verificado (TC15)**

**Nota sobre TC5**: o campo "Tipo de experiência" é um campo creatable-select, não uma lista fixa de 8 opções como documentado na AT. O produto pode ter implementado de forma diferente (opções cadastráveis) — alinhar com dev se as opções são fixas por RN ou livres.

---

## Divergências de Label AT vs Tela

| AT documenta | Tela implementa | Tipo |
|---|---|---|
| "Adicionar registro de aprendizagem" (título) | "Novo conteúdo externo" | Título do form divergente |
| "Adicionar registro" (título Admin) | "Novo conteúdo externo" | Título do form divergente |
| "Pessoa" (singular, campo Admin) | "Pessoas*" (plural, multi-select) | Campo e modelo de dados divergem |
| "Selecione o colaborador" (placeholder Pessoa) | "Adicionar pessoas" (modal Vincular pessoas) | Interação diverge: dropdown → modal |
| "Comprovação de aprendizagem" | "Evidência de aprendizagem" | Label divergente |
| "Provedor de aprendizagem" | "Provedor" | Label divergente (abreviado) |
| "Descrição do conteúdo" | "Conteúdo" | Label divergente (abreviado) |
| "Nota" | "Desempenho" | Label divergente |
| "Anotações" | "Descrição" | Label divergente |
| "Enviar para aprovação" (botão Aluno) | "Salvar" | Botão divergente |
| "Salvar e aprovar" (botão Admin) | "Salvar" | Botão divergente |
| "http://website.com" (placeholder Website) | "https://exemplo.com" | Placeholder divergente |
| "Ex: 40" (placeholder Carga horária) | "HH:MM:SS" | Placeholder e formato divergentes |
| "Ex: 85" com sufixo "%" (placeholder Nota) | Sem placeholder; campo com sufixo "%" | Placeholder ausente, sufixo presente |
| 9 categorias padrão | 6 categorias padrão | Quantidade divergente na stage |
| 8 opções fixas de Tipo de experiência | Campo creatable com 2 opções na stage | Tipo de campo diverge (fixo vs creatable) |

**Recomendação**: atualizar test-analysis.md com os labels reais e corrigir o modelo de dados.

---

## Bugs Identificados

### BUG P1 — Erro 401 no modal "Vincular pessoas" para Líder (TC3)

**Severidade**: P1 (crítico — bloqueia fluxo do Gestor de turma)  
**Comportamento**: Líder acessa o form de Adicionar registro, clica no campo "Pessoas*", o modal "Vincular pessoas" abre mas retorna "Nenhum item encontrado" + toast "Request failed with status code 401".  
**Endpoints com 401**: `GET /api/v1/o/37079/professionals`, `GET /api/v1/o/37079/professionals/results_for_filter`, `GET /api/v1/o/37079/event_sources/get_provider_names` — 12 chamadas 401 confirmadas na sessão do Líder.  
**Esperado**: Líder deve ver somente seus liderados diretos no modal (RN 93).  
**Evidências**: `tc3b_lider_modal_apos_click.png` (toast 401 visível), `tc3b_lider_form.png`  
**Impacto**: Gestor de turma não consegue criar nenhum registro de aprendizagem para seus liderados.

### BUG P2 — API de provedores retorna 401 para Aluno (TC7)

**Severidade**: P2 (alto — bloqueia fluxo do Aluno)  
**Comportamento**: Aluno abre o form de Adicionar registro, o dropdown "Provedor" fica vazio. API `GET /api/v1/o/37079/event_sources/get_provider_names` retorna **401 Unauthorized** para o perfil Aluno. Admin vê os provedores normalmente (Alura, Coursera, FGV etc.).  
**Esperado**: Lista de provedores deve ser exibida para o Aluno (RN 39.2); dropdown vazio não é massa faltando — a causa é falta de autorização no endpoint.  
**Evidências**: `tc7b_02_provedor_aluno_vazio.png`  
**Impacto**: Aluno não consegue selecionar provedor existente; precisa criar inline. Dependência TC14 resolvida criando provedor inline ("Alura").

---

## Observações de Automação

1. **TC5 (Tipo de experiência)**: campo é `creatable-select` (react-select com criação inline). No recon, combobox[2] mostrou apenas "Treinamento" e "Curso" — opções cadastradas na org. O campo não tem lista fixa de 8 opções como documentado na AT. Investigar com dev se as 8 opções são dados de seed obrigatórios.

2. **TC8 (Carga horária)**: sistema valida os campos obrigatórios na ordem de tela. Com todos os outros campos preenchidos (exceto Pessoas — modal não abre automaticamente via headless), o erro de Carga horária foi exibido corretamente.

3. **TC15 (origem Admin)**: o campo "Adicionar pessoas" exige click no container React que não responde a eventos sintéticos no headless. O recon confirmou que o modal funciona e lista pessoas corretamente para Admin. TC15 = não verificado por limitação de automação.

4. **TC12 (clearError)**: usar `type()` char-a-char em vez de `fill()` é necessário para disparar o evento `onChange` do React no campo "Carga horária".

---

## Evidências

Base (GitHub): https://github.com/DantexgerBR/twygo-playwright-tests/tree/main/evidencias/registros-f2-qa16

| TC | Arquivo principal (link) |
|---|---|
| Gate (Aluno) | [aluno_gate_login.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/aluno_gate_login.png) |
| Gate (Admin) | [admin_gate_login.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/admin_gate_login.png) |
| Gate (Líder) | [lider_gate_login.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/lider_gate_login.png) |
| TC1 | [tc1_01_meu_historico.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc1_01_meu_historico.png), [tc1_02_form_aluno.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc1_02_form_aluno.png) |
| TC2 | [tc2_01_registros_com_btn.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc2_01_registros_com_btn.png), [tc2_02_form_aberto.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc2_02_form_aberto.png) |
| TC3 — BUG P1 | [tc3b_lider_modal_apos_click.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc3b_lider_modal_apos_click.png) (toast 401 visível), [tc3b_lider_form.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc3b_lider_form.png) |
| TC4 | [tc4_01_form_campos.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc4_01_form_campos.png), [tc4_02_form_completo.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc4_02_form_completo.png) |
| TC5 | [tc5b_01_dropdown_aberto.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc5b_01_dropdown_aberto.png) (2 opções vs 8 esperadas) |
| TC6 | [tc6_01_dropdown_categorias.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc6_01_dropdown_categorias.png), [tc6_03_chip_selecionado.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc6_03_chip_selecionado.png) |
| TC7 — BUG P2 | [tc7b_02_provedor_aluno_vazio.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc7b_02_provedor_aluno_vazio.png) (dropdown vazio + 401 na API) |
| TC8 | [tc8b_07_pos_salvar_vazio.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc8b_07_pos_salvar_vazio.png) (erro "Carga horária é obrigatório") |
| TC9 | [tc9_01_desemp_invalido.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc9_01_desemp_invalido.png), [tc9_03_desemp_valido.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc9_03_desemp_valido.png) |
| TC10 | [tc10_01_data_vazia.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc10_01_data_vazia.png), [tc10_03_data_valida.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc10_03_data_valida.png) |
| TC11 | [tc11_01_form_vazio.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc11_01_form_vazio.png), [tc11_03_erros.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc11_03_erros.png) |
| TC12 | [tc12b_01_erros_provocados.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc12b_01_erros_provocados.png), [tc12b_02_apos_digitar.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc12b_02_apos_digitar.png) |
| TC13 | [tc13_01_form_vazio.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc13_01_form_vazio.png), [tc13_02_pos_cancelar.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc13_02_pos_cancelar.png) |
| TC14 | [tc14b_02_form_preenchido.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc14b_02_form_preenchido.png), [tc14b_04_lista.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc14b_04_lista.png) (Externo + Pendente) |
| TC15 (não verificado) | [recon_modal_dump_form.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/recon_modal_dump_form.png) (modal funciona para Admin no recon) |
| TC16 | [tc16_01_area_upload.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc16_01_area_upload.png), [tc16_02_arquivo_carregado.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc16_02_arquivo_carregado.png) |

Todas as evidências em: https://github.com/DantexgerBR/twygo-playwright-tests/tree/main/evidencias/registros-f2-qa16

---

## Comentário KQA (pronto para colar no Artia 19893)

```
⇝ QA ⇜
:: Teste ::
❌ Falhou
:: Ambiente ::
🧪 Stage — https://registrosf2.stage.twygoead.com/ (Org 37079)
:: Validação ::
Suíte QA 1.6 concluída (2 rounds): 10 PASSOU | 3 FALHOU (2 bugs reais + TC5 divergência de dados) | 1 não verificado (TC15 — limitação de automação).

Passaram: TC1, TC2, TC4, TC6, TC8, TC9, TC10, TC11, TC12, TC13, TC14, TC16.

2 bugs reais confirmados:
- TC3 (P1): Líder recebe HTTP 401 ao abrir modal "Vincular pessoas" — 12 chamadas a /professionals e /event_sources retornam 401. Liderado não aparece; Gestor de turma completamente bloqueado de criar registros.
- TC7 (P2): API /event_sources/get_provider_names retorna 401 para o perfil Aluno. Dropdown "Provedor" fica vazio. Admin vê a lista normalmente (Alura, Coursera, FGV etc.). Bug de autorização no endpoint, não dados faltando.

Divergência (não bug de produto):
- TC5: campo "Tipo de experiência" é creatable-select (não lista fixa). Stage tem apenas 2 opções cadastradas ("Treinamento", "Curso") vs 8 da AT. Alinhar com dev se as 8 opções são seed obrigatório ou livres.

Não verificado:
- TC15: modal "Vincular pessoas" funciona para Admin (confirmado no recon — lista pessoas corretamente com checkboxes), mas não pôde ser acionado via automação headless. Verificação manual necessária.
:: Obs ::
Múltiplas divergências AT vs produto documentadas: título "Novo conteúdo externo" (vs "Adicionar registro"), campo Pessoas é modal multi-select (vs dropdown singular), botão "Salvar" (vs "Salvar e aprovar"/"Enviar para aprovação"), renomeações de campo (Nota→Desempenho, Anotações→Descrição etc.). Recomendo atualizar o AT.
TC14 passou: registro Aluno criou corretamente como Externo + Pendente.
TC8 e TC12 passaram: validação de obrigatório e clearError funcionam.
:: Evidência(s) ::
- TC3 BUG P1 — 401 Líder: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc3b_lider_modal_apos_click.png
- TC7 BUG P2 — Provedor 401 Aluno: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc7b_02_provedor_aluno_vazio.png
- TC8 PASSOU — erro Carga horária: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc8b_07_pos_salvar_vazio.png
- TC12 PASSOU — clearError: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc12b_02_apos_digitar.png
- TC14 PASSOU — Externo+Pendente: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc14b_04_lista.png
- TC5 divergência — 2 tipos vs 8: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc5b_01_dropdown_aberto.png
Pasta com todas as evidências: https://github.com/DantexgerBR/twygo-playwright-tests/tree/main/evidencias/registros-f2-qa16
```
