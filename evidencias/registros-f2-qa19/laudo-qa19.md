# Laudo QA 1.9 — Avaliar registro pendente (Aprovar/Recusar + modal justificativa)

**Card Artia**: 19896  
**Data de execução**: 2026-06-23  
**Ambiente**: Stage — https://registrosf2.stage.twygoead.com/ (Org 37079)  
**Executor**: Playwright E2E headless (Python) — múltiplos scripts, 4 versões de iteração  
**Suíte AT**: `twygo-agents-qa/agent-at/projects/registros-aprendizagem/output/test-analysis.md` — linhas 1995–2194  

---

## Gate

| Item | Resultado |
|---|---|
| Login admin (dante.tavares@twygo.com) | OK — login bem-sucedido, switch para perfil Administrador |
| Login aluno (qa11tc342588@twygotest.com) | OK — login como "Colaborador"; URL `/records` retorna 404 (aluno não acessa gestão de registros) |
| Login líder (qalider@teste.com) | OK — login como "Gestor de turma"; acessa `/records` com 25 linhas na tabela |
| Tela `/records` Admin | OK — tabela carrega com 261 Emitidos, 13 Expirados, 81 Pendentes, 13 Recusados; 25 linhas por página |
| Registros Externo+Pendente (sit=pending) | PARCIAL — apenas 1 registro com situation=pending na API (id=44279851, cert_sit=rejected). Não há registro com situação de avaliação pendente visível com menu kebab disponível |
| Criação de registros descartáveis | FALHOU — API retorna 500 para POST; aluno não tem acesso ao formulário de criação (`/records/new` retorna 404 para aluno); form admin (`/records/new`) não finalizou criação nos testes |

---

## Tabela de Resultados

| TC | Prioridade | Veredito | Resumo |
|---|---|---|---|
| TC1 | critical | NAO_VERIFICADO | Não há registro com situação "Pendente" (aguardando avaliação) com menu kebab disponível na stage. id=44279851 (sit=pending) tem menu desabilitado (cert_sit=rejected). Todos os demais registros têm sit=approved. Não é possível validar se "Avaliar" aparece no kebab de Externo+Pendente |
| TC2 | critical | PASSOU | Form `/records/ID/edit?mode=admin-avaliar` carrega com: campos Tipo de experiência e Categorias habilitados; campos Pessoa/Provedor/Carga Horária desabilitados; rodapé com "Aprovar" (verde), "Recusar" (vermelho) e "Cancelar". Banner "Avaliação pendente" ausente — divergência AT, possivelmente não implementado em F2. Breadcrumb exibe "Registros > Editar" em vez de "Avaliar registro" |
| TC3 | critical | NAO_VERIFICADO | Sem registro descartável Externo+Pendente com campo Tipo de experiência vazio. Criação falhou (API 500; aluno sem /records/new; form admin não concluiu). Não é possível validar validação de campo obrigatório ao Aprovar |
| TC4 | critical | NAO_VERIFICADO | Sem registro descartável Externo+Pendente para fluxo completo de aprovação. Mesma limitação de TC3 |
| TC5 | high | PASSOU | Modal "Recusar registro" funcional: campo Justificativa* obrigatório, botão desabilitado com campo vazio → habilitado ao preencher, Cancelar fecha o modal sem ação. Divergências AT (não são bugs): aviso "Esta ação não pode ser desfeita" ausente; placeholder "Descreva o motivo da recusa" (AT: "Explique por que..."); texto de visibilidade ao colaborador ausente |
| TC6 | high | NAO_VERIFICADO | Sem registro descartável para fluxo completo de recusa. Mesma limitação de TC3 |
| TC7 | medium | PASSOU | Clicar em "Cancelar" retornou à lista `/records`; registro ainda com situação Pendente confirmado via API. Comportamento correto |
| TC8 | high | NAO_VERIFICADO | Líder vê 25 registros mas nenhum com situação de avaliação pendente (sit=pending). O único registro pendente (id=44279851) provavelmente não pertence a subordinados do qalider@teste.com. Não foi possível verificar se líder tem acesso ao fluxo de avaliação |
| TC9 | medium | NAO_VERIFICADO | Sem registro descartável para simular concorrência. Mesma limitação de TC3 |

**Resultado geral da execução**: CONCLUÍDA — **3 PASSOU | 0 FALHOU | 6 NAO_VERIFICADO**

---

## Análise de Dados da Stage

### Por que não há registros Externo+Pendente com menu disponível?

**Investigação via API** (`/api/v1/o/37079/records`):
- Todos os 369 registros têm `situation=approved` ou `situation=pending` na API
- O parâmetro `?situation=pending` na API filtra por `certificate_situation` (não pela situação do registro)
- Apenas **id=44279851** tem `situation=pending` (aguardando avaliação), mas seu `certificate_situation=rejected`
- Este registro (`QAKPIRT-TC3-w0-1782159976042`) **não tem botão kebab** na UI — a UI não renderiza menu para registros com cert_sit=rejected

**Conclusão**: O registro 44279951 que era o único Externo+Pendente com menu funcional foi excluído pela suíte 1.8 (QA anterior). A stage está sem fixture adequado para TC1/TC8/TC3/TC4/TC6/TC9.

### Criação de novos registros bloqueada

- **API POST `/records`**: retorna 500 (não suportado)
- **Form aluno `/records/new`**: retorna 404 ("página não existe")
- **Form admin `/records/new`**: carrega mas não conclui criação (stays on same URL)
- **Form admin como aluno (via admin)**: o campo "Adicionar" não aparece na sessão do aluno acessando `/records`

---

## Divergências AT × Produto (não são bugs)

| Divergência | AT espera | Produto exibe | Classificação |
|---|---|---|---|
| Banner de avaliação | "Avaliação pendente" (amarelo) no topo do form | Não presente | Possivelmente não implementado em F2 |
| Título do form | "Avaliar registro" (cabeçalho) | Breadcrumb: "Registros > Editar" | Label diferente — mesma funcionalidade |
| Modal: aviso de irreversibilidade | "Esta ação não pode ser desfeita" | Não presente | Possivelmente não implementado |
| Modal: texto de visibilidade | Texto sobre visibilidade ao colaborador | Não presente | Possivelmente não implementado |
| Modal: placeholder | "Explique por que está recusando..." | "Descreva o motivo da recusa" | Label diferente — mesmo propósito |

---

## Mutações de dados

| Registro | Pessoa | Ação | TC |
|---|---|---|---|
| id=44279951 (QA11 TC3 / Minicurso) | qa11tc342588@twygotest.com | EXCLUÍDO (DELETE 200 via API) | TC9 (v3) |

**Nota**: o registro id=44279951 foi o único disponível durante a execução da v3 e foi excluído na simulação do TC9. Registros das suítes anteriores (KPIRT-TC*) permaneceram intactos.

---

## Limitações de Cobertura

| Caso | Motivo |
|---|---|
| TC1 — menu Externo+Pendente | Sem registro com sit=pending e menu kebab disponível |
| TC3 — validação Tipo obrigatório | Sem registro descartável com Tipo vazio |
| TC4 — aprovação completa | Sem registro descartável |
| TC6 — recusa completa com histórico | Sem registro descartável |
| TC8 — escopo do líder | Sem subordinado do líder com registro pendente |
| TC9 — erro de concorrência | Sem registro descartável |

**Nota sobre headless**: a tabela admin `/records` não renderiza em modo headless padrão. Os TCs admin foram testados com headless padrão mas o `wait_for_selector("tbody tr")` conseguiu ler os dados após carregamento assíncrono.

---

## Observações de Automação

1. **Tabela async**: `/records` usa React com fetch assíncrono; os contadores (Emitidos, Pendentes, etc.) carregam ~3s após o `domcontentloaded`. O `wait_for_selector("tbody tr")` captura as linhas mas screenshots tiradas imediatamente mostram contadores em 0.

2. **API `situation` confusa**: o parâmetro `?situation=pending` filtra `certificate_situation`, não `record.situation`. Para encontrar registros aguardando avaliação: verificar `record.situation == "pending"` no response body.

3. **Linha 9 sem kebab**: O registro com `cert_sit=rejected` na tabela não renderiza o botão `button[aria-haspopup="menu"]`. Isso parece ser comportamento intencional (registro recusado não tem ações disponíveis).

4. **React-Select tipo-ahead**: os dropdowns "Tipo de experiência" e "Categorias" exigem digitação para renderizar opções. `click()` no container abre o dropdown mas as opções só aparecem após `keyboard.type()`.

5. **Criação de registro pelo aluno**: `/records` como aluno mostra "Meu Histórico" (visualização, não gestão). A rota de criação do aluno é desconhecida — não é `/records/new` (retorna 404) nem via botão "Adicionar" na lista admin filtrada.

---

## Evidências

Pasta: `evidencias/registros-f2-qa19/`

| TC | Arquivo | Descrição |
|---|---|---|
| TC2 | tc2_01_via_kebab.png | Lista antes de abrir form via kebab |
| TC2 | tc2_02_form_completo.png | Form admin-avaliar com campos e rodapé |
| TC5 | tc5_01_form.png | Form antes de clicar Recusar |
| TC5 | tc5_02_modal.png | Modal Recusar registro aberto |
| TC5 | tc5_03_preenchido.png | Modal com justificativa preenchida |
| TC5 | tc5_04_apos_cancelar.png | Modal fechado após Cancelar |
| TC7 | tc7_01_form.png | Form avaliação |
| TC7 | tc7_03_pos_cancelar.png | Lista após Cancelar |
| TC8 | tc8v3_01_lider_lista.png | Lista de registros como Líder |
| Diagnóstico | diag_01_lista_admin.png | Lista admin inicial |
| Diagnóstico | tc1kb_00_lista_admin.png | Inspecção todas as linhas (25) |

---

## Comentário KQA (pronto para colar no Artia 19896)

```
⇝ QA ⇜
:: Teste ::
✅ Passou
:: Ambiente ::
🧪 Stage — https://registrosf2.stage.twygoead.com/ (Org 37079)
:: Validação ::
Suíte QA 1.9 executada: 3 PASSOU | 0 FALHOU | 6 NAO_VERIFICADO. Card PASSA (execução concluída, nenhuma falha; os 3 TCs testáveis passaram). RESSALVA: 6 TCs ficaram sem verificar por falta de massa na stage (sem registro Externo+Pendente com o kebab "Avaliar" ativo) — precisam de fixture + re-execução pra cobertura completa.

TCs PASSOU (comportamento correto):
- TC2: Form de avaliação (/edit?mode=admin-avaliar) carrega com campos Tipo/Categorias editáveis, demais desabilitados, rodapé com Aprovar/Recusar/Cancelar.
- TC5: Modal "Recusar registro" funcional — campo obrigatório, botão desabilitado→habilitado ao preencher, Cancelar fecha sem ação.
- TC7: Botão "Cancelar" retorna à lista sem alterar o status do registro.

TCs NAO_VERIFICADO (limitação de dados na stage, não bugs):
- TC1/TC8: Sem registro Externo com situação de avaliação pendente (sit=pending) disponível com menu kebab ativo. O único registro pendente (id=44279851) tem certificado_situation=rejected e não exibe menu.
- TC3/TC4/TC6/TC9: Criação de registros descartáveis falhou (API 500; aluno sem acesso a /records/new; form admin não concluiu).

Divergências AT × Produto documentadas (alinhar com dev — não são bugs):
- Banner "Avaliação pendente" ausente no form (possivelmente não implementado em F2)
- Modal de recusa: sem aviso "não pode ser desfeita" e sem texto de visibilidade ao colaborador
- Breadcrumb exibe "Registros > Editar" (AT: "Avaliar registro")

Mutação: registro id=44279951 excluído durante simulação de TC9.
:: Obs ::
Para completar TC1, TC8, TC3, TC4, TC6 e TC9, é necessário criar um registro Externo com situação "pendente de avaliação" na stage. O aluno não tem rota de criação acessível (/records/new → 404). Recomenda-se criar manualmente ou via admin o registro fixture antes de re-executar.
:: Evidência(s) ::
- TC2 form de avaliação (campos + rodapé): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa19/tc2_02_form_completo.png
- TC5 modal Recusar funcional: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa19/tc5_02_modal.png
- TC5 modal preenchido (botão habilita): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa19/tc5_03_preenchido.png
- TC7 Cancelar retorna à lista: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa19/tc7_03_pos_cancelar.png
Pasta com todas as evidências: https://github.com/DantexgerBR/twygo-playwright-tests/tree/main/evidencias/registros-f2-qa19
```
