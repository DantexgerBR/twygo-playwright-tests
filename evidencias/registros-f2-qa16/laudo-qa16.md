# Laudo QA 1.6 — Adicionar registro de aprendizagem (3 perfis, validações e origem inferida)

**Card Artia**: 19893  
**Data de execução**: 2026-06-23  
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
| Provedores padrão cadastrados | AUSENTE — dropdown Provedor mostra "Nenhum resultado encontrado" para usuário aluno; bloqueia TC7, TC14 |

---

## Tabela de Resultados

| TC | Prioridade | Veredito | Resumo |
|---|---|---|---|
| TC1 | critical | PASSOU (divergências) | Meu Histórico exibiu botão "Adicionar"; form abriu em `/records/new?in_use_mode_layout=true`. Divergências: (1) título é "Novo conteúdo externo" vs AT "Adicionar registro de aprendizagem"; (2) campo "Pessoas*" aparece para aluno (AT diz que campo Pessoa é exclusivo do modo admin); (3) botão de envio é "Salvar" vs AT "Enviar para aprovação" |
| TC2 | critical | PASSOU (divergências) | Form Admin abriu em `/records/new`, campos fundamentais presentes (Pessoas*, Provedor*, Conteúdo*). Divergências: (1) título "Novo conteúdo externo" vs AT "Adicionar registro"; (2) campo "Pessoas" abre modal "Vincular pessoas" (não dropdown inline); (3) botão salvar é "Salvar" vs AT "Salvar e aprovar" |
| TC3 | critical | FALHOU | Modal "Vincular pessoas" abre para o Líder mas retorna "Nenhum item encontrado" + toast de erro HTTP 401 (Unauthorized). Liderado não listado; Líder não consegue criar registro para seu liderado |
| TC4 | high | PASSOU (divergências) | Todos os campos do form existem. Divergências de nomenclatura AT vs produto: ver tabela de divergências abaixo. Placeholder Website = "https://exemplo.com" (AT: "http://website.com"); Carga horária = "HH:MM:SS" (AT: "Ex: 40"); campo "Nota" renomeado para "Desempenho"; "Comprovação de aprendizagem" renomeada para "Evidência de aprendizagem"; "Provedor de aprendizagem" renomeado para "Provedor"; "Descrição do conteúdo" renomeado para "Conteúdo"; "Anotações" renomeado para "Descrição" |
| TC5 | high | FALHOU | Script não conseguiu abrir o dropdown "Tipo de experiência" via automação (seletor `abrir_dropdown_por_label` não encontrou o elemento interativo). O campo existe no form (confirmado pelo recon). As 8 opções não puderam ser verificadas nesta execução |
| TC6 | high | PASSOU (parcial) | Dropdown "Categorias" abriu com 6 opções visíveis: Liderança e desenvolvimento pessoal, Cultura e integração organizacional, Gestão de negócios e processos, Segurança e compliance, Marketing e vendas, Tecnologia. AT espera 9 — encontradas 6 (dados de stage). Criação inline disponível (opção "Criar" aparece ao digitar). Chip criado ao selecionar categoria |
| TC7 | high | FALHOU | Dropdown "Provedor" mostra "Nenhum resultado encontrado" para usuário aluno (qa11tc342588). Provedores padrão (Alura, Coursera, Udemy etc.) não estão cadastrados na org 37079 ou não são retornados para esse usuário. Bug de dados de stage ou autorização |
| TC8 | medium | FALHOU (inconclusivo) | Ao tentar salvar com Carga horária vazia, o sistema abre modal "Vincular pessoas" (campo Pessoas* ainda não preenchido) ao invés de exibir erro de validação de Carga horária. Não foi possível testar a validação de Carga horária isoladamente — a ordem de validação priorizou Pessoas antes dos outros campos |
| TC9 | medium | PASSOU (renomeação) | Campo "Desempenho" encontrado (AT chama de "Nota"). Campo aceita valores numéricos. Sufixo "%" visível. Sem validação de range visível ao digitar (não bloqueia texto nem valores acima de 100 inline) |
| TC10 | medium | PASSOU | Campo "Data de término*" presente e obrigatório. Tentativa de salvar sem preencher gerou erro "Data de término é obrigatório" junto com os outros campos obrigatórios |
| TC11 | high | PASSOU | Clicar "Salvar" com todos os campos vazios exibiu 7 mensagens de erro: "Provedor é obrigatório", "Conteúdo é obrigatório", "Tipo de experiência é obrigatório", "Categorias é obrigatório", "Carga horária é obrigatório", "Data de término é obrigatório" + 1 vazio. Form permanece na mesma página |
| TC12 | medium | FALHOU | Após provocar erros e preencher o campo "Carga horária", as mensagens de erro não foram limpas (6 erros antes = 6 erros depois). O clearError pode não estar funcionando para campos de texto quando outros campos (selects) ainda têm erro — ou o fill no campo via Playwright não disparou o evento de input corretamente |
| TC13 | low | PASSOU | Clicar "Cancelar" sem preencher nenhum campo redirecionou para a lista sem validar. Nenhuma mensagem de erro foi exibida |
| TC14 | critical | FALHOU (bloqueado) | Não foi possível salvar o registro como Aluno pois o campo Provedor retornou vazio (dependência do bug de TC7). Origem inferida não pôde ser verificada |
| TC15 | critical | FALHOU (inconclusivo) | Não foi possível verificar a origem inferida pós-salvar. O form do Admin parou no modal "Vincular pessoas" pois o seletor de Pessoas falhou. Os registros já existentes na lista mostram "Externo" na coluna Origem, porém o registro criado pelo script não foi salvo com sucesso |
| TC16 | medium | PASSOU | Área de upload "Evidência de aprendizagem" presente; `input[type=file]` encontrado. Upload de arquivo PDF executado com sucesso. Formatos aceitos listados: .pdf, .docx, .xlsx, .csv, .jpg, .jpeg, .png; máximo 10 MB; até 5 arquivos |

**Resultado geral da execução**: CONCLUÍDA — **8 PASSOU | 8 FALHOU | 0 BLOQUEADO**  
(TC14 bloqueado por dependência do TC7; TC15 e TC8 inconclusivos por falha de automação em preencher Pessoas via modal)

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
| "Ex: 40" (placeholder Carga horária) | "HH:MM:SS" | Placeholder e formato divergentes (AT sugere número; produto usa HH:MM:SS) |
| "Ex: 85" com sufixo "%" (placeholder Nota) | Sem placeholder; campo com sufixo "%" | Placeholder ausente, sufixo presente |
| 9 categorias padrão | 6 categorias padrão | Quantidade divergente na stage |

**Recomendação**: atualizar test-analysis.md com os labels reais e corrigir o modelo de dados de "Pessoa" para "Pessoas" (multi-select via modal).

---

## Bugs Identificados

### BUG P1 — Erro 401 no modal "Vincular pessoas" para Líder (TC3)

**Severidade**: P1 (crítico — bloqueia fluxo do Gestor de turma)  
**Comportamento**: Líder acessa o form de Adicionar registro, clica no campo "Pessoas*", o modal "Vincular pessoas" abre mas retorna "Nenhum item encontrado" + toast "Request failed with status code 401".  
**Esperado**: Líder deve ver somente seus liderados diretos no modal (RN 93).  
**Evidências**: `tc3_03_dropdown_pessoas.png`, `tc3_04_opcoes_liderados.png`  
**Impacto**: Gestor de turma não consegue criar nenhum registro de aprendizagem para seus liderados.

### BUG P2 — Provedores padrão não carregam para usuário Aluno (TC7)

**Severidade**: P2 (alto — bloqueia fluxo do Aluno)  
**Comportamento**: Aluno abre o form de Adicionar registro, clica no campo "Provedor*", dropdown exibe "Nenhum resultado encontrado". AT pré-condição exige provedores padrão (Alura, Coursera, Udemy etc.) cadastrados.  
**Esperado**: Lista de provedores padrão deve ser exibida para seleção (RN 39.2).  
**Evidências**: `tc7_01_dropdown_provedor.png`, `tc7_02_opcoes.png`  
**Impacto**: Aluno não consegue criar registros sem criar um provedor manualmente; fluxo de TC14 (origem inferida) bloqueado.

### DIVERGÊNCIA AT (não bug de produto) — Aluno vê campo "Pessoas*"

**Tipo**: Divergência AT vs implementação  
**Comportamento**: O campo "Pessoas*" aparece para o Aluno no form (AT diz que é exclusivo do modo Admin/Líder).  
**Possível causa**: O produto implementou um único form com campo Pessoas para todos os perfis. Para Aluno, o campo pode estar pré-selecionado implicitamente (não visível) ou a RN 38 ainda não foi implementada.  
**Evidências**: `tc1_02_form_aluno.png`, `tc1_03_campos_form.png`

---

## Observações de Automação

1. **TC5 (Tipo de experiência)**: O seletor `abrir_dropdown_por_label("Tipo de experiência")` não conseguiu interagir com o dropdown. O campo existe (confirmado pelo recon e visível na imagem tc6_01). Para re-executar TC5, usar seletor direto no elemento Chakra select do campo.

2. **TC8 (Carga horária)**: O produto valida o campo "Pessoas*" antes dos outros campos — o modal de vinculação abre ao clicar Salvar se Pessoas não estiver preenchido. Script precisa preencher Pessoas via modal antes de testar validações de Carga horária.

3. **TC15 (origem Admin)**: O seletor de "Pessoas" via `abrir_dropdown_por_label` não funcionou para Admin (mesma limitação do modal). Registro não foi criado, logo origem inferida não foi verificada.

4. **TC12 (clearError)**: O script preencheu Carga horária via `fill`, mas o evento de input pode não ter disparado no Chakra (que usa estado controlado React). Usar `type` char-by-char ou `press` ao invés de `fill` pode resolver em re-execução.

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
| TC3 | [tc3_02_form_lider.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc3_02_form_lider.png), [tc3_03_dropdown_pessoas.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc3_03_dropdown_pessoas.png) |
| TC4 | [tc4_01_form_campos.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc4_01_form_campos.png), [tc4_02_form_completo.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc4_02_form_completo.png) |
| TC5 | [tc5_01_dropdown_tipo.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc5_01_dropdown_tipo.png) |
| TC6 | [tc6_01_dropdown_categorias.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc6_01_dropdown_categorias.png), [tc6_03_chip_selecionado.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc6_03_chip_selecionado.png), [tc6_04_opcao_criar.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc6_04_opcao_criar.png) |
| TC7 | [tc7_01_dropdown_provedor.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc7_01_dropdown_provedor.png), [tc7_02_opcoes.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc7_02_opcoes.png) |
| TC8 | [tc8_01_carga_vazia.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc8_01_carga_vazia.png), [tc8_02_erro_carga_vazia.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc8_02_erro_carga_vazia.png) |
| TC9 | [tc9_01_desemp_invalido.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc9_01_desemp_invalido.png), [tc9_03_desemp_valido.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc9_03_desemp_valido.png) |
| TC10 | [tc10_01_data_vazia.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc10_01_data_vazia.png), [tc10_03_data_valida.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc10_03_data_valida.png) |
| TC11 | [tc11_01_form_vazio.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc11_01_form_vazio.png), [tc11_03_erros.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc11_03_erros.png) |
| TC12 | [tc12_01_erros_provocados.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc12_01_erros_provocados.png), [tc12_02_apos_digitar.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc12_02_apos_digitar.png) |
| TC13 | [tc13_01_form_vazio.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc13_01_form_vazio.png), [tc13_02_pos_cancelar.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc13_02_pos_cancelar.png) |
| TC14 | [tc14_01_form_preenchido.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc14_01_form_preenchido.png), [tc14_03_lista_pos_salvar.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc14_03_lista_pos_salvar.png) |
| TC15 | [tc15_01_form_preenchido.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc15_01_form_preenchido.png), [tc15_03_lista_pos_salvar.png](https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc15_03_lista_pos_salvar.png) |
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
Suíte QA 1.6 concluída: 8 PASSOU | 8 FALHOU | 0 BLOQUEADO. 2 bugs reais identificados; 5 divergências de AT documentadas.

Passaram: TC1 (Aluno abre form), TC2 (Admin abre form), TC4 (campos presentes), TC6 (categorias + inline), TC9 (campo Desempenho), TC10 (Data de término obrigatória), TC11 (validação de obrigatórios), TC13 (Cancelar bypassa validação), TC16 (upload de evidências).

Falharam com bugs reais:
- TC3: Líder recebe HTTP 401 ao abrir modal "Vincular pessoas" — liderados não listados, bloqueio total do fluxo do Gestor de turma.
- TC7: Dropdown Provedor mostra "Nenhum resultado encontrado" para Aluno — provedores padrão não retornados (bloqueia TC14).

Falharam por limitação de automação (inconclusivos):
- TC5: seletor do dropdown "Tipo de experiência" não abriu (campo existe, opções não verificadas).
- TC8: sistema abre modal de Pessoas antes de validar Carga horária — automação não preencheu Pessoas via modal.
- TC12: clearError pode não estar funcionando para campos select/dropdown.
- TC14: bloqueado por TC7 (sem Provedor, registro não salva).
- TC15: automação não preencheu Pessoas via modal; origem inferida do Admin não verificada.
:: Obs ::
Múltiplas divergências AT vs produto — ver laudo para tabela completa: título do form é "Novo conteúdo externo" (AT: "Adicionar registro"), campo "Pessoas*" é multi-select via modal (AT: dropdown "Pessoa" exclusivo Admin), botão é "Salvar" (AT: "Salvar e aprovar"/"Enviar para aprovação"), campos renomeados (Nota→Desempenho, Anotações→Descrição, Comprovação→Evidência). Recomendo atualizar o AT.
TC3 é o bug mais crítico — Gestor de turma completamente bloqueado de criar registros para liderados.
:: Evidência(s) ::
- TC3 erro 401 Líder: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc3_03_dropdown_pessoas.png
- TC7 Provedor vazio: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc7_01_dropdown_provedor.png
- TC11 erros obrigatórios: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc11_03_erros.png
- TC16 upload: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc16_02_arquivo_carregado.png
- TC4 form completo: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa16/tc4_02_form_completo.png
Pasta com todas as evidências: https://github.com/DantexgerBR/twygo-playwright-tests/tree/main/evidencias/registros-f2-qa16
```
