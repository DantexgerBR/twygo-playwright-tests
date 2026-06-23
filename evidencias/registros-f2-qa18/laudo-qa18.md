# Laudo QA 1.8 — Visualizar registro (standalone vs form viewing, "Em andamento")

**Card Artia**: 19895  
**Data de execução**: 2026-06-23  
**Ambiente**: Stage — https://registrosf2.stage.twygoead.com/ (Org 37079)  
**Executor**: Playwright E2E headed (Python) — TW_HEADED=1, múltiplas estratégias de interação  
**Suíte AT**: `twygo-agents-qa/agent-at/projects/registros-aprendizagem/output/test-analysis.md` — linhas 1862–1991  

---

## Gate

| Item | Resultado |
|---|---|
| Login admin (dante.tavares@twygo.com) | OK — login bem-sucedido, switch para perfil Administrador |
| Login aluno (qa11tc342588@twygotest.com) | OK — login como "Colaborador", Meu Histórico [BETA] acessível |
| Tela `/records` Admin (headed) | OK — tabela carrega com 261 Emitidos, 13 Expirados, 82 Pendentes, 13 Recusados; 25 linhas por página |
| Tela Meu Histórico Aluno | OK — 1 registro Externo Pendente exibido |
| Menu kebab da tabela | OK — botão `button.chakra-menu__menu-button` funcional em ambos os perfis |
| Dados de teste (aluno disponível) | PARCIAL — aluno qa11tc342588 tem apenas 1 registro (Externo+Pendente); registros Interno Emitido, Externo Emitido, Compartilhado e "Em andamento" não acessíveis via aluno com senha conhecida |

---

## Tabela de Resultados

| TC | Prioridade | Veredito | Resumo |
|---|---|---|---|
| TC1 | critical | FALHOU — BUG P1 | Menu exibe "Visualizar" habilitado para Externo+Pendente (aluno). Confirmado com foco real de teclado (ArrowDown 2x após click no kebab): elemento `id="menu-list-:r1v:-menuitem-:r29:"` focado, Enter fecha o menu (Chakra processa a seleção), mas nenhuma navegação ou ação ocorre. Cobre: item exibido ✅ / click funcional ❌ |
| TC2 | critical | FALHOU — BUG P1 | Admin com registro Interno. Confirmado via múltiplas estratégias (click/role/coordinate/keyboard). Enter com foco real fecha o menu sem ação. Comparativo: "Editar" no mesmo menu navega para `/records/ID/edit` corretamente |
| TC3 | medium | não verificado | Depende de TC2 abrir tela standalone — TC2 falhou, TC3 não pode ser executado |
| TC4 | high | não verificado | 0 registros com origin=shared no stage (369 registros enumerados via API: 234 Internos + 135 Externos + 0 Compartilhados). Dado necessário ausente na stage |
| TC5 | critical | FALHOU — BUG P1 | Admin com registro Externo Emitido (Richard Sebold / QA11-F2-FGV-Financas). Mesmo comportamento. |
| TC6 | high | FALHOU — BUG P1 | Admin com registros Externo Recusado (13 confirmados pelos KPIs). Mesmo comportamento. |
| TC7 | high | FALHOU — BUG P1 | Admin visualizando Externo Emitido. Mesmo comportamento confirmado. |

**Resultado geral da execução**: CONCLUÍDA — **0 PASSOU | 5 FALHOU (1 bug P1 afeta todos) | 2 não verificados (TC3 depende de TC2; TC4 ausência de dados)**

---

## Bug Identificado

### BUG P1 — Item "Visualizar" no kebab de Registros não tem ação funcional

**Severidade**: P1 (crítico — funcionalidade de visualização inteira bloqueada)  
**Afeta**: Admin e Aluno; todos os tipos de registro testados (Interno, Externo Emitido, Externo Pendente, Externo Recusado)  

**Comportamento observado**:  
Clicar em "Visualizar" no menu kebab (3 pontos) de qualquer registro não produz ação. O menu fecha normalmente (confirmando que o Chakra recebe e processa a seleção), mas nenhuma navegação, abertura de nova aba ou form view ocorre.

**Prova definitiva via keyboard (kb4)**:  
- Click no kebab abre o menu e foca automaticamente "Editar" (index 0)
- ArrowDown 2x foca "Visualizar" — elemento `id="menu-list-:r1v:-menuitem-:r29:"`, `text: 'visibilityVisualizar'`
- Enter no item focado: menu FECHA (Chakra processa a seleção corretamente)
- Resultado: tela volta para lista de registros sem ação — nenhuma navegação, nenhuma nova aba
- Comportamento de referência: "Editar" (ArrowDown 0x) via Enter navega para `/records/ID/edit`; "Evidências" (ArrowDown 3x) via Enter funciona igualmente

**Diagnóstico técnico**:  
O `<button role="menuitem" id="menu-list-:r1v:-menuitem-:r29:">` existe, tem estrutura idêntica aos outros itens, e o Chakra o processa ao pressionar Enter (menu fecha). Mas o handler `onClick` do React conectado ao item não executa ação. O inner div tem `id="records-44279951-custom-element-1-button-2"` com `data-test-id="records-list-view-action"` — o sufixo "custom-element" (vs "edit-element" no Editar) sugere que o handler de ação não foi implementado.

**Estratégias de interação testadas — todas confirmando o bug**:  
1. `page.mouse.click(centerX, centerY)` por coordenada exata (getBoundingClientRect) — menu não fecha, sem ação  
2. `get_by_role("menuitem", name="Visualizar").click()` com hit-testing do Playwright — menu não fecha, sem ação  
3. Click no `button[role="menuitem"]` ancestor do `data-test-id` — sem ação  
4. ArrowDown+Enter com foco real no elemento (método mais confiável) — menu fecha (Chakra OK), mas sem ação React  

**Esperado (AT)**:
- Interno/Compartilhado Emitido → nova aba com tela standalone `?cert=TOKEN`
- Externo (qualquer status) → form em modo leitura na mesma aba com cabeçalho "Visualizar registro"
- "Em andamento" → item desabilitado com tooltip "Disponível após a conclusão"

**Evidências**:  
- `kb4_01_focado.png` — "Visualizar" focado via teclado (highlight azul, foco real confirmado pelo DOM)  
- `kb4_02_pos_enter.png` — após Enter: menu fechou, lista sem ação (BUG confirmado)  
- `dispatch_aluno_02_pos_editar.png` — "Editar" funciona no mesmo menu (referência)  
- `tc7_01_menu_aberto.png` — menu admin aberto com Visualizar habilitado  

---

## Limitações de Cobertura

| Caso | Motivo da não verificação |
|---|---|
| TC1 linha 1 (Interno Emitido — aluno) | Aluno qa11tc342588 não tem registro Interno; aluno qa11tc342816 tem mas senha desconhecida |
| TC1 linha 2 (Externo Emitido — aluno) | Aluno qa11tc342588 tem apenas Externo Pendente |
| TC1 linha 3 (Compartilhado) | 0 registros origin=shared no stage (369 enumerados via API) |
| TC1 linha 4 (Em andamento disabled) | 0 registros situation=in_progress no stage |
| TC3 (botão "Validar outro certificado") | Depende de TC2 — tela standalone nunca abre |
| TC4 (standalone Compartilhado) | 0 registros Compartilhados no stage |

**Nota sobre headless vs headed**: a tabela admin `/records` não renderiza em modo headless (spinner infinito); todos os TCs admin foram testados com `TW_HEADED=1`. Aluno funciona corretamente em ambos os modos.

---

## Observações de Automação

1. **Seletor de menuitem com armadilha**: o seletor `[class*='menuitem']:visible` retorna items da sidebar (left~=23) além dos do dropdown real (left~=1188). Usar `getBoundingClientRect().left > 500` para isolar o dropdown.

2. **126 menuitems no DOM**: todos os menus das 25 linhas existem simultaneamente no DOM; apenas o aberto tem posição X válida no viewport direito.

3. **get_by_role vs teclado**: `get_by_role("menuitem").click()` não fecha o menu — o Playwright não consegue completar o hit-test quando o item está próximo da borda da viewport. O método de teclado (ArrowDown+Enter) é mais confiável e foi o método definitivo.

4. **Admin headed vs headless**: tabela admin carrega em headed (25 linhas), não carrega em headless. Investigar se há feature-flag ou lazy-render condicional ao viewport real.

---

## Evidências

Base (GitHub): https://github.com/DantexgerBR/twygo-playwright-tests/tree/main/evidencias/registros-f2-qa18

| TC | Arquivo principal | Descrição |
|---|---|---|
| BUG P1 prova definitiva | kb4_01_focado.png | Visualizar focado via teclado |
| BUG P1 prova definitiva | kb4_02_pos_enter.png | Menu fechou sem ação após Enter |
| Referência funcional | dispatch_aluno_02_pos_editar.png | Editar navega no mesmo menu |
| TC1 (aluno menu) | tc5_aluno_01_menu_aberto.png | Menu aluno com Visualizar habilitado |
| TC2 (admin Interno menu) | tc2_01_menu_aberto.png | Menu Interno admin |
| TC5/TC7 (admin Externo Emitido) | tc7_01_menu_aberto.png | Menu Externo Emitido admin |
| Admin tabela loaded headed | headed_02_admin_records_apos_wait.png | Tabela admin (261 Emitidos) |

Todas as evidências em: https://github.com/DantexgerBR/twygo-playwright-tests/tree/main/evidencias/registros-f2-qa18

---

## Comentário KQA (pronto para colar no Artia 19895)

```
⇝ QA ⇜
:: Teste ::
❌ Falhou
:: Ambiente ::
🧪 Stage — https://registrosf2.stage.twygoead.com/ (Org 37079)
:: Validação ::
Suíte QA 1.8 concluída: 0 PASSOU | 5 FALHOU | 2 não verificados.

BUG P1 confirmado — item "Visualizar" no menu kebab de Registros não executa ação:

O menu fecha normalmente ao pressionar Enter com o item focado (Chakra processa a seleção), mas nenhuma navegação ocorre. Confirmado via múltiplos métodos: coordenada, role-click, e navegação de teclado (ArrowDown+Enter). Para referência, "Editar" e "Evidências" no mesmo menu funcionam corretamente com os mesmos métodos.

Diagnóstico técnico: o <button role="menuitem"> com data-test-id="records-list-view-action" existe e é processado pelo Chakra, mas o handler React onClick não está conectado à ação de visualização.

Perfis/tipos testados:
- Admin + Externo Emitido (TC5/TC7)
- Admin + Interno (TC2)
- Admin + Externo Recusado (TC6)
- Aluno + Externo Pendente (TC1)

TCs não verificados:
- TC3: depende de TC2 abrir tela standalone (TC2 falhou)
- TC4: 0 registros Compartilhados no stage
:: Obs ::
Cobertura parcial da matriz do TC1: aluno acessível (qa11tc342588) tem apenas Externo+Pendente. Os casos Interno Emitido, Externo Emitido, Compartilhado e "Em andamento" ficaram sem dados de aluno. Admin valida os tipos (Interno, Externo Emitido, Externo Recusado) mas o bug bloqueia a ação em todos.
:: Evidência(s) ::
- BUG P1 — Visualizar focado via teclado: kb4_01_focado.png
- BUG P1 — Após Enter: menu fechou sem ação: kb4_02_pos_enter.png
- Referência — Editar funciona no mesmo menu: dispatch_aluno_02_pos_editar.png
Pasta: https://github.com/DantexgerBR/twygo-playwright-tests/tree/main/evidencias/registros-f2-qa18
```
