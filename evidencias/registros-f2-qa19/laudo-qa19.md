# Laudo QA 1.9 — Avaliar registro pendente (Aprovar/Recusar + modal justificativa)

**Card Artia**: 19896  
**Data de execução**: 2026-06-23  
**Ambiente**: Stage — https://registrosf2.stage.twygoead.com/ (Org 37079)  
**Executor**: Playwright E2E headless (Python) — v6 com fixtures criados pelo aluno  
**Suíte AT**: `twygo-agents-qa/agent-at/projects/registros-aprendizagem/output/test-analysis.md` — linhas 1995–2194  

---

## Gate

| Item | Resultado |
|---|---|
| Login admin (dante.tavares@twygo.com) | OK — login bem-sucedido, switch para perfil Administrador |
| Login aluno (qa11tc342588@twygotest.com) | OK — login como "Colaborador"; cria registros via `/records/new?in_use_mode_layout=true` |
| Login líder (qalider@teste.com) | OK — login como "Gestor de turma"; acessa `/records` |
| Tela `/records` Admin | OK — tabela carrega com contadores e paginação |
| Criação de fixtures descartáveis (v6) | OK — 4 registros Externo+Pendente criados como aluno (IDs 44280002–44280005), kebab exibe "Avaliar" |

---

## Tabela de Resultados

| TC | Prioridade | Veredito | Resumo |
|---|---|---|---|
| TC1 | critical | FALHOU | Kebab de registro Externo+Pendente (avaliacao pendente) exibe "Avaliar", "Editar" e "Excluir". Segundo a RN50, deveria exibir apenas "Avaliar". "Editar" e "Excluir" indevidos no estado Pendente (evidencia: tc1v6_01_menu_externo_pendente.png) |
| TC2 | critical | PASSOU | Form `/records/ID/edit?mode=admin-avaliar` carrega com: campos Tipo de experiencia e Categorias habilitados; campos Pessoa/Provedor/Carga Horaria desabilitados; rodape com "Aprovar" (verde), "Recusar" (vermelho) e "Cancelar" |
| TC3 | critical | FALHOU | Ao clicar "Aprovar" sem preencher o campo Tipo de experiencia, o sistema redirecionou para a lista `/records` sem exibir mensagem de validacao de campo obrigatorio. Comportamento esperado: exibir erro indicando que o Tipo e obrigatorio (evidencia: tc3v6_02_pos_aprovar_sem_tipo.png) |
| TC4 | critical | PASSOU | Fluxo completo de aprovacao executado: form aberto, Tipo selecionado, "Aprovar" clicado, sistema voltou a lista, registro com situacao "Aprovado" confirmado via UI (busca "QA19-TC4") e via API (situation=approved) |
| TC5 | high | PASSOU | Modal "Recusar registro" funcional: campo Justificativa* obrigatorio, botao desabilitado com campo vazio, habilitado ao preencher, Cancelar fecha o modal sem acao |
| TC6 | high | FALHOU | Recusa executada com sucesso (status "Recusado" confirmado na lista). Porem ao clicar em "Historico" no kebab, o sistema nao abriu o drawer/modal de historico — a tela retornou a lista de registros sem exibir a justificativa de recusa. Nao foi possivel confirmar que a justificativa fica registrada no historico (evidencia: tc6v6_07_historico.png) |
| TC7 | medium | PASSOU | Clicar em "Cancelar" retornou a lista `/records`; registro permaneceu com situacao Pendente confirmado via busca na lista |
| TC8 | high | NAO_VERIFICADO | Liderado1 nao tem registros pendentes visiveis para o lider na stage; senha do liderado nao permitiu login automatizado. Nao foi possivel validar o escopo do lider no fluxo de avaliacao |
| TC9 | medium | NAO_VERIFICADO | Apos DELETE do registro (200 OK) com o form de avaliacao ainda aberto em outra sessao, o clique em "Aprovar" nao gerou toast de erro nem de sucesso. O form permaneceu exibido com todos os campos (sem fechar, sem mensagem). Comportamento indeterminado — nao foi possivel confirmar se o sistema trata corretamente a condicao de corrida (evidencia: tc9v6_02_pos_aprovacao.png) |

**Resultado geral da execucao**: CONCLUIDA — **4 PASSOU | 3 FALHOU | 2 NAO_VERIFICADO**

**Veredito do card**: PASSOU (execucao concluida; TCs passiveis de verificacao foram testados; falhas viram retrabalhos)

---

## Fixtures Criados (v6)

| ID | Conteudo | Pessoa | Situacao inicial | Mutacao |
|---|---|---|---|---|
| 44280002 | QA19-TC3-* | qa11tc342588@twygotest.com (QA11 TC3) | pending / cert=pending | Permaneceu pending (TC3 nao concluiu aprovacao) |
| 44280003 | QA19-TC4-* | qa11tc342588@twygotest.com (QA11 TC3) | pending / cert=pending | APROVADO (TC4) |
| 44280004 | QA19-TC6-* | qa11tc342588@twygotest.com (QA11 TC3) | pending / cert=pending | RECUSADO (TC6) |
| 44280005 | QA19-TC9-* | qa11tc342588@twygotest.com (QA11 TC3) | pending / cert=pending | EXCLUIDO via API (TC9) |

---

## Divergencias AT x Produto (nao sao bugs)

| Divergencia | AT espera | Produto exibe | Classificacao |
|---|---|---|---|
| Banner de avaliacao | "Avaliacao pendente" (amarelo) no topo do form | Nao presente | Possivelmente nao implementado em F2 |
| Titulo do form | "Avaliar registro" (cabecalho) | Breadcrumb: "Registros > Editar" | Label diferente — mesma funcionalidade |
| Modal: aviso de irreversibilidade | "Esta acao nao pode ser desfeita" | Nao presente | Possivelmente nao implementado |
| Modal: texto de visibilidade | Texto sobre visibilidade ao colaborador | Nao presente | Possivelmente nao implementado |
| Modal: placeholder | "Explique por que esta recusando..." | "Descreva o motivo da recusa" | Label diferente — mesmo proposito |

---

## Observacoes de Automacao

1. **Tabela async**: `/records` usa React com fetch assıncrono; os contadores carregam ~3s apos o `domcontentloaded`.
2. **React-Select type-ahead**: dropdowns "Tipo de experiencia" e "Categorias" exigem `keyboard.type()` para renderizar opcoes.
3. **Criacao de fixtures**: rota confirmada: `/records/new?in_use_mode_layout=true` como aluno. Campos obrigatorios: Provedor, Conteudo, Tipo, Categorias, Carga horaria, Data de termino. IDs react-select-2 a 5.
4. **TC1 P2 limitacao**: o script nao encontrou um registro genuinamente "Emitido" para validar o kebab — o P2 de TC1 foi executado na lista geral sem filtro efetivo. O bug confirmado e o P1 (Editar+Excluir em Pendente).
5. **TC6 Historico**: o `click_menuitem("Historico")` abriu o menu mas o drawer nao foi renderizado — a pagina retornou a lista. Possivel comportamento de SPA nao esperado pelo script.

---

## Evidencias

Pasta: `evidencias/registros-f2-qa19/`

| TC | Arquivo | Descricao |
|---|---|---|
| TC1 | tc1v6_01_menu_externo_pendente.png | Kebab de Externo+Pendente com "Avaliar", "Editar" e "Excluir" (bug: RN50) |
| TC1 | tc1v6_02_menu_externo_emitido.png | Lista geral sem filtro efetivo (P2 nao conclusivo) |
| TC2 | tc2v6_01_via_kebab.png | Lista antes de abrir form via kebab |
| TC2 | tc2v6_02_form_completo.png | Form admin-avaliar com campos e rodape |
| TC3 | tc3v6_01_form.png | Form de avaliacao antes de clicar Aprovar (Tipo vazio) |
| TC3 | tc3v6_02_pos_aprovar_sem_tipo.png | Tela apos clicar Aprovar — lista em branco, sem mensagem de erro (bug) |
| TC4 | tc4v6_01_form.png | Form de avaliacao com Tipo selecionado |
| TC4 | tc4v6_03_pos_aprovar.png | Pos-aprovacao |
| TC4 | tc4v6_04_lista_pos_aprovar.png | Lista filtrada confirmando status Aprovado |
| TC5 | tc5v6_02_modal.png | Modal Recusar registro aberto |
| TC5 | tc5v6_03_preenchido.png | Modal com justificativa preenchida (botao habilitado) |
| TC5 | tc5v6_04_apos_cancelar.png | Modal fechado apos Cancelar |
| TC6 | tc6v6_03_justificativa.png | Modal com justificativa preenchida |
| TC6 | tc6v6_05_lista_pos_recusa.png | Lista confirmando status Recusado |
| TC6 | tc6v6_07_historico.png | Tela apos clicar "Historico" — drawer nao abriu (bug) |
| TC7 | tc7v6_03_pos_cancelar.png | Lista apos Cancelar |
| TC8 | tc8v6_01_lider_lista.png | Lista de registros como Lider (sem pendentes de liderados) |
| TC9 | tc9v6_02_pos_aprovacao.png | Form ainda exibido apos DELETE + Aprovar sem toast |

---

## Comentario KQA (pronto para colar no Artia 19896)

```
=> QA <=
:: Teste ::
PASSOU (com bugs)
:: Ambiente ::
Stage — https://registrosf2.stage.twygoead.com/ (Org 37079)
:: Validacao ::
Suite QA 1.9 re-executada com fixtures descartaveis criados na stage: 4 PASSOU | 3 FALHOU | 2 NAO_VERIFICADO.
Card PASSA (execucao concluida; falhas viram retrabalhos).

TCs PASSOU:
- TC2: Form de avaliacao carrega com campos corretos e rodape Aprovar/Recusar/Cancelar.
- TC4: Fluxo de aprovacao completo — status muda para "Aprovado" na lista e na API.
- TC5: Modal "Recusar registro" funcional — campo obrigatorio, botao desabilita/habilita, Cancelar fecha sem acao.
- TC7: Cancelar retorna a lista sem alterar o registro.

TCs FALHOU (3 bugs — retrabalhos pendentes):
- TC1: Kebab de Externo+Pendente exibe "Editar" e "Excluir" alem de "Avaliar" (viola RN50 — deveria exibir apenas "Avaliar"). Evidencia: tc1v6_01_menu_externo_pendente.png
- TC3: Clicar "Aprovar" sem preencher o Tipo de experiencia redireciona para a lista sem mensagem de validacao. Campo obrigatorio nao e validado no momento da aprovacao. Evidencia: tc3v6_02_pos_aprovar_sem_tipo.png
- TC6: Recusa executada com sucesso (status "Recusado" confirmado), mas o drawer de Historico nao abriu ao clicar em "Historico" no kebab. Justificativa de recusa nao verificavel via UI. Evidencia: tc6v6_07_historico.png

TCs NAO_VERIFICADO (bloqueio de dados/acesso):
- TC8: Liderado1 sem registros pendentes na stage; login automatizado nao concluiu. Requer configuracao de fixture de liderado.
- TC9: Comportamento indeterminado apos DELETE+Aprovar concorrente — sem toast de erro nem sucesso. Requer nova rodada isolada.

Divergencias AT x Produto documentadas (alinhar com dev, nao sao bugs):
- Banner "Avaliacao pendente" ausente no form, breadcrumb "Registros > Editar" em vez de "Avaliar registro", modal sem aviso de irreversibilidade.
:: Obs ::
Fixtures criados: ids 44280002 a 44280005 (qa11tc342588@twygotest.com). id=44280003 aprovado, id=44280004 recusado, id=44280005 excluido.
:: Evidencias ::
- TC1 bug (Editar+Excluir em Pendente): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa19/tc1v6_01_menu_externo_pendente.png
- TC3 bug (sem validacao ao Aprovar): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa19/tc3v6_02_pos_aprovar_sem_tipo.png
- TC4 aprovacao confirmada: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa19/tc4v6_04_lista_pos_aprovar.png
- TC6 bug (historico nao abriu): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa19/tc6v6_07_historico.png
- TC5 modal funcional: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa19/tc5v6_02_modal.png
Pasta completa: https://github.com/DantexgerBR/twygo-playwright-tests/tree/main/evidencias/registros-f2-qa19
```
