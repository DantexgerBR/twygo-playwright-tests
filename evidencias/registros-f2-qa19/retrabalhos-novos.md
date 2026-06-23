# Retrabalhos Novos — QA 1.9 Registros F2 (card 19896)

Data de abertura: 2026-06-23  
Suite: QA 1.9 — Avaliar registro pendente  
Ambiente: https://registrosf2.stage.twygoead.com/ (Org 37079)

---

## P2 [Registros F2] Kebab de registro Externo+Pendente exibe "Editar" e "Excluir" indevidamente (RN50)

**TC de origem**: TC1  
**Prioridade**: P2  

**Comportamento observado**: O kebab de um registro do tipo Externo com situacao de avaliacao pendente (situation=pending, cert_sit=pending) exibe tres opcoes: "Avaliar", "Editar" e "Excluir". Segundo a RN50, um registro nesse estado deveria exibir **apenas** a opcao "Avaliar" — as opcoes de edicao e exclusao nao devem estar disponiveis enquanto o registro aguarda avaliacao.

**Passos para reproduzir**:
1. Criar um registro do tipo Externo como aluno (via `/records/new?in_use_mode_layout=true`)
2. Confirmar que o registro esta com situation=pending, cert_sit=pending e criado pelo aluno
3. Acessar a lista de registros como admin: `/records`
4. Buscar o registro pelo conteudo
5. Abrir o menu kebab (tres pontos) do registro

**Resultado esperado** (RN50): Apenas "Avaliar" deve aparecer no kebab de registro Externo+Pendente.  
**Resultado obtido**: "Avaliar", "Editar" e "Excluir" aparecem simultaneamente no kebab.

**Evidencia**: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa19/tc1v6_01_menu_externo_pendente.png

---

## P2 [Registros F2] Aprovar registro sem preencher "Tipo de experiencia" nao exibe validacao

**TC de origem**: TC3  
**Prioridade**: P2  

**Comportamento observado**: No form de avaliacao de registro (`/records/ID/edit?mode=admin-avaliar`), o campo "Tipo de experiencia" e obrigatorio para aprovar. Ao deixar o campo vazio e clicar em "Aprovar", o sistema redireciona para a lista `/records` sem exibir nenhuma mensagem de erro ou validacao. O registro permanece pendente, mas o admin nao recebe feedback sobre o motivo da nao-aprovacao.

**Passos para reproduzir**:
1. Abrir o form de avaliacao de um registro Externo+Pendente: `/records/ID/edit?mode=admin-avaliar`
2. NAO preencher o campo "Tipo de experiencia" (deixar em branco)
3. Clicar no botao "Aprovar"

**Resultado esperado**: Exibir mensagem de validacao indicando que o campo "Tipo de experiencia" e obrigatorio antes de permitir a aprovacao.  
**Resultado obtido**: Sistema redireciona para a lista `/records` sem mensagem. A lista aparece vazia (sem registros na tela) imediatamente apos o redirecionamento.

**Evidencia**: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa19/tc3v6_02_pos_aprovar_sem_tipo.png

---

## P3 [Registros F2] Drawer de Historico nao abre ao clicar em "Historico" no kebab de registro Recusado

**TC de origem**: TC6  
**Prioridade**: P3  

**Comportamento observado**: Apos recusar um registro (status muda para "Recusado" na lista), ao abrir o kebab do registro recusado e clicar em "Historico", o sistema nao exibe o drawer/modal de historico. A pagina permanece na lista de registros sem nenhuma abertura de painel lateral ou modal.

**Passos para reproduzir**:
1. Recusar um registro via form de avaliacao (preencher justificativa e confirmar)
2. Verificar que o registro aparece com status "Recusado" na lista
3. Abrir o kebab (tres pontos) do registro recusado
4. Clicar em "Historico"

**Resultado esperado**: Um drawer ou modal deve abrir exibindo o historico de avaliacoes do registro, incluindo a justificativa da recusa.  
**Resultado obtido**: A tela permanece na lista de registros. O drawer de historico nao e renderizado. Nao e possivel ver a justificativa de recusa via UI.

**Nota**: A recusa em si funciona corretamente (status muda para "Recusado"). O problema e especifico na exibicao do historico.

**Evidencia**: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa19/tc6v6_07_historico.png  
**Evidencia complementar (recusa OK)**: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa19/tc6v6_05_lista_pos_recusa.png
