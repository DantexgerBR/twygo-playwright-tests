# Retrabalhos Novos — QA 1.6 Registros F2

**Data**: 2026-06-23  
**Card de origem**: Artia 19893

---

## P1 [Registros F2] Erro 401 ao abrir "Vincular pessoas" para Gestor de turma (TC3)

**Prioridade**: P1  
**Perfil afetado**: Líder / Gestor de turma (qalider@teste.com)  
**Comportamento**: Ao clicar no campo "Pessoas*" no form de Adicionar registro, o modal "Vincular pessoas" abre mas retorna "Nenhum item encontrado" junto com toast de erro "Request failed with status code 401" (Unauthorized). O Gestor de turma não consegue selecionar nenhum liderado.  
**Esperado**: O modal deve listar os liderados diretos do líder (RN 93 — campo Pessoa restrito a liderados do Gestor de turma).  
**Impacto**: Gestor de turma está completamente bloqueado de criar registros de aprendizagem para seus liderados.  
**Evidências**: `tc3_03_dropdown_pessoas.png`, `tc3_04_opcoes_liderados.png`

---

## P2 [Registros F2] Provedores padrão não listados no dropdown para Aluno (TC7)

**Prioridade**: P2  
**Perfil afetado**: Aluno / Colaborador  
**Comportamento**: Ao clicar no campo "Provedor*" no form de Adicionar registro como Aluno, o dropdown exibe "Nenhum resultado encontrado". Os provedores padrão esperados (Alura, Coursera, Udemy etc.) não são retornados.  
**Esperado**: Lista de provedores padrão cadastrados para seleção; opção de criar provedor inline (RN 39.2).  
**Impacto**: Aluno não consegue criar registros de aprendizagem sem criar provedor manualmente; funcionalidade de adição de registro externa bloqueada para o perfil Colaborador.  
**Evidências**: `tc7_01_dropdown_provedor.png`, `tc7_02_opcoes.png`

---

## Obs: Divergências AT (não são bugs de produto — precisam de alinhamento)

Os itens abaixo são divergências entre a AT e a implementação atual. Não são bugs do produto — precisam de decisão de alinhamento entre QA e Dev:

1. **Título do form**: "Novo conteúdo externo" vs AT "Adicionar registro de aprendizagem" / "Adicionar registro"
2. **Campo Pessoas**: multi-select via modal "Vincular pessoas" vs AT dropdown "Pessoa" singular. Aluno também vê o campo (AT diz que é exclusivo Admin/Líder).
3. **Botões de rodapé**: "Salvar" (único) vs AT "Enviar para aprovação" (Aluno) / "Salvar e aprovar" (Admin)
4. **Renomeações de campo**: Nota→Desempenho, Anotações→Descrição, Comprovação→Evidência, Provedor de aprendizagem→Provedor, Descrição do conteúdo→Conteúdo
5. **Placeholders**: Website `https://exemplo.com` (AT: `http://website.com`); Carga horária `HH:MM:SS` (AT: `Ex: 40`)

Recomendação: atualizar test-analysis.md suíte 1.6 com os valores reais do produto.
