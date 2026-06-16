# 20033 — Filtro "Aplicar e Salvar" inconsistente (Continuidade, PR #10712)

**Ambiente:** stage RECERT, org 37048, `/o/37048/succession_initiatives` (Parâmetros).

## O que foi PROVADO ao vivo (confiável)
- **1ª aplicação do filtro funciona corretamente** — ver `flow-02-aplicado-A.png`:
  filtro montado (valor *Iniciativa = Capacitar sucessor* + ocultar colunas *Impacto (%)*
  e *Cobertura (%)*) → **Aplicar** → tabela mostra **1 linha** correta e as 2 colunas
  ficam **ocultas**. Comportamento da 1ª aplicação = correto.
- **"Limpar filtro"** restaura o estado padrão (todas as colunas, 15 linhas) de forma consistente.
- O toggle **"Salvar na lista de filtros"** pode ser ligado e o Nome preenchido — ver `cols-01-builder.png`.

## O que NÃO foi possível validar de forma confiável (limite de automação headless)
- O **cerne do bug** (re-aplicar o filtro **salvo** em *Meus filtros* depois de limpar → filtragem
  errada / colunas reposicionam) não pôde ser reproduzido de forma estável via Playwright headless.
  O drawer Chakra ("Lista de filtros" / "Filtro rápido") + combobox em portal apresentam
  **flakiness run-a-run**: o mesmo script aplica o filtro num run e não aplica noutro; o
  seletor do dialog às vezes captura elemento solto. 8 abordagens tentadas
  (`run_20033_*.py`).
- **Não há evidência de defeito do produto** na reaplicação — a instabilidade observada é
  da automação, não comprovadamente do app. Por isso **não** se crava ❌ de produto
  (anti-falso-positivo) nem ✅ (não comprovado).

## Recomendação
Confirmação **manual** rápida (≈10s) da reaplicação: montar filtro → Salvar na lista →
Aplicar (conferir) → Limpar → reabrir Filtro → Meus filtros → reaplicar o salvo → conferir
se filtragem e ordem/visibilidade de colunas batem com a 1ª aplicação.

## Scripts
`scripts/run_20033_builder.py`, `run_20033_probe.py`, `run_20033_flow.py`,
`run_20033_reapply2.py`, `run_20033_cols.py`, `run_20033_linear.py`.
