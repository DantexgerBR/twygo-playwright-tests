# Retrabalho 20177 — Filtros padrão da aba "Avaliações a preencher"

**PR:** https://github.com/Twygo/twyg-app/pull/10737 (OPEN, base `master`, não mergeado)
**Esperado:** na aba Desenvolvimento → "Avaliações a preencher", os filtros padrão
devem ser **Pendentes / Atrasadas / Desempenho** — o preset **"Concluídas" não deve aparecer**.

## Veredito: ✅ Passou

Fix confirmado **deployado e corretamente ligado** no JS servido pelo `cdn-stage.twygo.com`.

## Como foi validado

Validação feita inspecionando o **bundle que de fato roda no stage** (`cdn-stage.twygo.com`),
que para uma mudança de UI condicional é mais conclusivo que um print: o print mostra um
estado; o código mostra o gating exato — a aba passa a prop e a tabela remove o preset.

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

