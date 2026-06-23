# Retrabalhos Novos — QA 1.8 Registros F2

**Data**: 2026-06-23  
**Card de origem**: 19895 — Visualizar registro (standalone vs form viewing)

---

## P1 [Registros F2] "Visualizar" no menu kebab de registros não executa ação

**Prioridade**: P1  
**Contexto**: Suíte QA 1.8 — TC1, TC2, TC5, TC6, TC7

**Comportamento atual**:  
O item "Visualizar" no menu de 3 pontos (kebab) de qualquer registro nas telas "Registros" (admin) e "Meu Histórico" (aluno) está renderizado e habilitado, e o Chakra o processa normalmente (menu fecha ao pressionar Enter com o item focado), mas nenhuma ação é executada pelo handler React. A tela volta para a lista sem navegação, sem nova aba, sem form view.

**Reprodução**:
1. Acessar Aprendizagem > Registros como Admin (ou Meu Histórico como Aluno)
2. Clicar nos 3 pontos de qualquer registro para abrir o menu
3. Navegar com seta até "Visualizar" e pressionar Enter (ou clicar no item)
4. O menu fecha mas nenhuma ação ocorre — tela permanece na lista

**Comportamento esperado**:
- Registro Interno/Compartilhado Emitido: nova aba com tela standalone do certificado (URL com `?cert=TOKEN`)
- Registro Externo (qualquer status): form em modo leitura na mesma aba, cabeçalho "Visualizar registro", todos os campos desabilitados
- Registro "Em andamento": item "Visualizar" desabilitado com tooltip "Disponível após a conclusão"

**Diagnóstico**:  
O `<button role="menuitem" data-test-id="records-list-view-action">` existe no DOM com estrutura idêntica aos outros itens funcionais ("Editar", "Evidências"). O Chakra processa a seleção do item (menu fecha ao pressionar Enter), confirmando que a estrutura do componente está correta. O inner div usa `custom-element` como sufixo de ID (vs `edit-element` no Editar), sugerindo que o handler onClick React do item Visualizar não está conectado a nenhuma ação.

**Perfis afetados**: Admin e Aluno  
**Tipos de registro testados**: Interno, Externo Emitido, Externo Pendente, Externo Recusado  
**RNs afetadas**: RN 47, RN 48, RN 49  

**Evidências**:  
- Visualizar focado via teclado (foco real confirmado): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa18/kb4_01_focado.png
- Após Enter: menu fechou, lista sem ação (BUG): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa18/kb4_02_pos_enter.png
- Editar funciona no mesmo menu (controle/referência): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/registros-f2-qa18/dispatch_aluno_02_pos_editar.png
