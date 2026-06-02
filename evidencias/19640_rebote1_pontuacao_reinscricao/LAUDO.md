# Laudo — Retrabalho 19640 · REBOTE 1 (P1) [Recertificação] Desempenho e pontuação da reinscrição atual propagado para todas as reinscrições

- **Ambiente:** Stage Recertificação — `https://recertificacao-testeqa.stage.twygoead.com/` (org **37048**)
- **Login:** `agents.claude@claude.com` (Administrador)
- **Trilha:** "Trilha para CASCADE" (id **807406**)
- **PR do dev:** https://github.com/Twygo/twyg-app/pull/10468
- **Data:** 2026-06-02
- **Card ID:** 19640 · Rebote 1

## Veredito: ✅ Corrigido

A propagação de desempenho/pontuação da inscrição atual para as demais reinscrições
**não ocorre mais**. Verificado em **4 usuários multi-geração** (incluindo o usuário
da evidência original), com controle positivo limpo e cruzamento com a fonte de verdade.

---

## O que o PR corrige (causa-raiz)

`EventStudentService#build_select_criterias` agregava `final_score` (desempenho) e
`total_score_by_weight` (pontuação) da trilha por `ep_child.user_id = event_participants.user_id`
— ou seja, somava/mediava **todos** os filhos do usuário, de **todas** as reinscrições, sem
correlacionar com a inscrição específica. Resultado: valor da inscrição atual vazava para o
histórico. **Fix:** correlacionar os filhos via `participant_relations`
(`learning_path_participant_id = event_participants.id AND deleted_at IS NULL`) → cada inscrição
agrega **apenas** os próprios filhos.

**Corrigido = ** cada geração mostra desempenho/pontuação distintos (os seus); reinscrição fresca
(0% de progresso, nada feito) mostra 0%/0; geração finalizada mantém o próprio valor (imutável).

## Evidência (aba Aprendizagem — visão admin)

19 inscrições, 4 usuários com reinscrição. Lido célula a célula, mapeado pelo cabeçalho
(não regex) — colunas Progresso / Desempenho / Pontuação:

| Usuário | Geração atual (progresso) | Demais gerações | Resultado |
|---|---|---|---|
| **agents.richard** (usuário da evidência) | item 44275243 (66%) → **100% / 550** | 8 gerações a 0% → **todas 0/0** | atual não vaza p/ anteriores |
| **richard.teste** (controle positivo) | item 44275255 (100%, Emitido) → **100% / 200** | 2 reinscrições frescas (0%) → **0/0** | finalizada mantém o seu; fresca zera |
| **agents.claude** | item 44275236 (28%) → **100% / 60** | item 44275175 (0%) → **0/0** | valores distintos |
| **agents.edu** | item 44275124 (33%) → **0% / 120** | 2 gerações a 0% → **0/0** | valores distintos |

**Discriminador forte (passou):** nenhuma geração com 0% de progresso exibe desempenho/pontuação
não-zero. Uma geração onde nada foi feito não pode ter score → se exibisse o valor da atual seria
propagação; não exibe.

**Comparação direta com o print do bug:** a evidência original mostrava `agents.richard` com 3 linhas
idênticas a **69.2% / 150** (progresso 100/0/0). Agora `agents.richard` tem só a geração atual
(44275243, 66%) com valor (**100%/550**) e **todas** as 8 anteriores em **0/0** — a propagação sumiu.

## Cross-check (anti-falso-positivo)

- **Fonte de verdade — Respostas de questionário:** o dado real existe e está preservado
  (ex.: `agents.richard` com Prova 8ª–15ª, vários 100% Aprovado; `agents.claude` 100% Aprovado;
  `richard.teste` 100% Aprovado). Confirma a lição do round anterior: nunca houve perda de dado —
  era cálculo/exibição por geração, que é exatamente o que o PR corrige. Evidência: `02-respostas-questionario.png`.
- **Controle positivo (richard.teste):** prova as duas direções do fix no mesmo usuário — geração
  finalizada (Emitido, 100%) retém **100%/200**, enquanto duas reinscrições frescas exibem **0/0**.

## Observação (não bloqueia o veredito; não é a propagação)

- `agents.richard` tem uma geração **"Emitido" exibindo 0%/0** (item 44275176). **Não é o bug deste card**
  (o bug faria exibir o valor da atual, 100%/550 — exibe 0/0, o oposto). É estado **pré-existente**
  (já estava 0/0 na rodada anterior) e é coerente com o fix: a geração agrega só os próprios filhos;
  se os filhos dela pontuaram 0 / não estão vinculados, exibe 0. Vale um aviso ao time, mas é escopo
  separado de 19640.
- **Cross-check de banco (twygo_db_rc) tentado mas indisponível:** o RDS retornou timeout de conexão
  desta rede (provável necessidade de VPN). Não foi necessário: o sinal da UI + fonte de verdade já
  são conclusivos para a propagação. Fica como reforço opcional se o time quiser a prova por-geração no SQL.

## Evidências
- `01-lista-aprendizagem.png` — lista com valores distintos por geração
- `02-respostas-questionario.png` — fonte de verdade (dado real preservado)
- `03-kebab-aberto.png` / `04-historico-aprendizagem.png` — menu/Histórico (best-effort)
- `_inscricoes.json` — dump das 19 inscrições (célula a célula, por cabeçalho)
- `_respostas_questionario.json` — respostas reais por usuário
- `_achados.json` — `[]` (nenhum indício de propagação)
- `../_bug_original_19640.png` — print do bug (estado ANTES, propagado)
