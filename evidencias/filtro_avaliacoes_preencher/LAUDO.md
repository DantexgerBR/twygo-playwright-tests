# Retrabalho 20177 — Filtros padrão da aba "Avaliações a preencher"

**PR:** https://github.com/Twygo/twyg-app/pull/10737 (OPEN, base `master`, não mergeado)
**Esperado:** na aba Desenvolvimento → "Avaliações a preencher", os filtros padrão
devem ser **Pendentes / Atrasadas / Desempenho** — o preset **"Concluídas" não deve aparecer**.

## Veredito: ✅ Passou

Fix confirmado **deployado e corretamente ligado** no JS servido pelo `cdn-stage.twygo.com`.

## Por que não há screenshot do painel renderizado

A aba "Avaliações a preencher" é a **visão de colaborador/líder** (menu *Gestão de Time →
Desenvolvimento*, `relationshipKind: self_assessment`). Na org de teste **36675** esse menu
**não está habilitado** para o usuário (a sidebar do perfil Aluno só tem Dashboard, Meus
Cursos, Trilhas, Comunidades…). No perfil Administrador a tela Desenvolvimento mostra
"Todos os ciclos / Status dos times / Visão 9-box" — sem a aba alvo.
Criar um ciclo (lado admin) **não** adiciona o menu ao perfil colaborador — depende de uma
flag da experiência do colaborador na org. Por isso a validação foi feita inspecionando o
**bundle que de fato roda no stage**, que é mais conclusivo que um print para uma mudança de
UI condicional (o print mostra um estado; o código mostra o gating exato).

## Evidências (código servido pelo stage)

**Prova 1 — a aba passa a prop** (`development-page-QS4tkBiq.min.js`):
```js
"data-test-id":"development-evaluations-tab",
children: jsx(N,{ relationshipKind:"self_assessment", hideSearch:!0, hideCompletedDefaultFilter:!0 })
```

**Prova 2 — a tabela consome a prop** (`performance-evaluations-table-DZ2JRIM5.min.js`):
```js
c = useMemo(()=>$(u,p), ...)                                  // lista COMPLETA de filtros padrão
y = useMemo(()=> f ? c.filter(m=>m.model_default_enum!==j) : c, [c,f])  // f=true → remove "Concluídas"
v = useMemo(()=> ... s==="completed"?c[2]:... )              // currentFilter usa a lista completa (índices estáveis)
return jsx(T,{ defaultFilters:y, currentFilter:v, ... })
```
Bate 1:1 com o PR: com `hideCompletedDefaultFilter=true` o preset "Concluídas"
(`model_default_enum !== <enum>`) sai dos filtros padrão; sem a prop (ex.: hub "Meus
ciclos") a lista fica intacta; `currentFilter` segue na lista completa.

## Repro
```
.\.venv\Scripts\python.exe scripts/retrabalho_filtro_avaliacoes_preencher_bundlecheck.py
```
Saída completa em `bundlecheck_output.txt`.

## Para confirmação visual (se desejado)
- Acesso a um usuário **líder/colaborador da org 37064** (a do card, onde o menu existe e o
  bug foi reproduzido); ou
- Habilitar a experiência *Gestão de Time → Desenvolvimento* do colaborador na org 36675.
