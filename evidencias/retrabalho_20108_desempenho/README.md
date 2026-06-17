# 20108 (P0) — Avaliação de Desempenho não prossegue / autoavaliação

**Ambiente alvo:** stage 37048 (Desempenho/Gestão de Time). Org da evidência do card: 19830 (linkada — não usar).

## Status: BLOQUEADO para automação headless — precisa setup manual

### Bloqueio raiz
O 37048 **não tem nenhum modelo de Avaliação de Desempenho** cadastrado. Ao criar um
ciclo e marcar "Avaliação de Desempenho", o seletor de modelo abre o drawer
**"Modelos disponíveis" → "Nenhum modelo cadastrado nesta organização"**
(`modelo-aberto.png`). Sem modelo, a Avaliação de Desempenho não pode ser habilitada.

### Caminho completo mapeado (recon feito)
- Ciclo existente: **QA19948 Ciclo Calibracao** (id **139**, período 16/06–14/09/2026, situação Programado, 0 campanhas).
- Kebab do ciclo: Ver resumo / Editar / **Gerenciar campanhas** / **Ativar ciclo** / Duplicar / Excluir.
- Wizard de ciclo (`/cycles/new` ou `/cycles/139/edit`): abas **Identificação → Avaliações → Etapas → Configurações adicionais**.
  - Avaliações: checkboxes **Avaliação de Desempenho** (precisa modelo), **Avaliação de Competências**, **PDI** (marcada por padrão no 139).
- Campanhas (`/cycles/139/campaigns`): "+ Adicionar" → wizard **Identificação (nome) → Cronograma → Quem participa**.

### Reprodução MANUAL (≈5–10 min)
1. **Criar modelo**: Questionários/Avaliações → novo modelo "Avaliação de Desempenho" com seções (ex.: Potencial) e questões de escala — como na evidência do card (Seção 3 de 3).
2. **Novo ciclo**: Gestão de Time > Desenvolvimento > Novo ciclo → nome + datas (período incluindo hoje); aba **Avaliações** → marcar "Avaliação de Desempenho" → **Selecionar modelo** (o criado no passo 1); aba **Etapas** → configurar autoavaliação; **Salvar e programar**.
3. **Campanha**: kebab do ciclo → Gerenciar campanhas → + Adicionar → nome + Cronograma + **Quem participa** (adicionar o próprio usuário admin).
4. **Ativar ciclo** (kebab → Ativar ciclo).
5. **Responder**: logar como o participante → responder a Avaliação de Desempenho → **avançar até a última seção** e tentar concluir → verificar o bug P0 (não prossegue/autoavaliação não conclui).

### Por que não foi automatizado
Cada controle interativo do módulo (abas do wizard, menu kebab, react-select de
modelo/participante, drawer) não responde de forma confiável a cliques programáticos
em headless (mesma família de flakiness Chakra do 20033). Somado à necessidade de
criar um modelo do zero + responder múltiplas seções como participante, a automação
cega não produz resultado confiável. Recomenda-se validação manual ou em org que já
tenha modelo de Desempenho + ciclo ativo.

## Scripts de recon
`recon_20108_*.py`, `get_cycle_id.py`, `build_20108_*.py`.
