# 20048 (P0) — Competências: dashboard + filtros + drill-down + extração

**Ambiente:** stage. Dashboard de Competências em `/o/{org}/organization_chart_competencies`
(Skills > Competências; abas Dashboard / Matriz de versatilidade / Lista de competências).
Orgs: 37048 (sem dados) e 19653 (com organograma/funções).

## Requisitos do card
1. Filtrar por **área, gestor e função** em todos os dashboards.
2. **Drill-down**: clicar no indicador → ver registros/cálculo que originaram o valor.
3. **Exportar** dados/gráficos/relatórios (Excel/PDF/imagem).
> O card pede explicitamente "alinhar com o dono do projeto a possibilidade de criar ou não mais filtros".

## Veredito: ❌ PARCIAL (export OK; filtros/drill-down não comprovados)
- **Exportação ✓ IMPLEMENTADA**: cada widget do dashboard de Competências tem botão
  **"Extrair dados"** (Evolução organizacional, Cobertura por área, Radar, Funções mais/menos
  aderentes, Competências mais sólidas/deficitárias) — ver `01-dashboard.png` (37048).
- **Filtros área/gestor/função: NÃO localizados** no dashboard de Competências. A aba Dashboard
  (padrão no 37048) mostra título + abas + widgets, **sem barra de filtros** no topo; o corpo
  não menciona "por área/gestor/função". A aba "Lista de competências" tem um botão "Filtro"
  genérico (filtro da lista, não área/gestor/função do dashboard).
- **Drill-down: não confirmado** — 37048 sem dados ("Sem dados/Nenhuma área"), sem indicador
  clicável para testar.

## Limitação (anti-falso-positivo)
A ausência da barra de filtros foi aferida na aba **Dashboard do 37048 (sem dados)**; não
consegui abrir a aba Dashboard com dados no 19653 via automação (a página centrou na Lista).
Como o escopo de filtros é "alinhado com o PO", recomenda-se **conferir contra o PR/spec** se
os filtros área/gestor/função e o drill-down foram entregues nesta etapa ou ficaram pendentes.

## Scripts
`recon_20048_competencias.py`, `recon_20048_19653.py`, `recon_20048_dashtab.py`.
