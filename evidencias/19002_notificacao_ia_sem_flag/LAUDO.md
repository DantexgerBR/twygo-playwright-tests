# Laudo — Bug 19002 (P2) [BUG] Disparo incorreto de notificação sobre análise de respostas por IA

- **Card:** 19002 · Tech - Bug Produção · Solicitante: Christofer Bastos
- **Ambiente do incidente:** PRODUÇÃO — `https://clararesorts.twygoead.com/` (cliente Clara Resorts)
- **PR do dev:** https://github.com/Twygo/twyg-app/pull/10181 (`fix/notificacao-analise-ia-sem-flag`)
- **Data da validação:** 2026-06-02

## Veredito: 🔁 RETRABALHO — a correção NÃO está em nenhum ambiente (não foi consertado)

A pedido do solicitante, o critério é binário: se não foi consertado, volta como retrabalho.
**Não foi consertado** — a correção do PR não está deployada em lugar nenhum (confirmado abaixo).
Não é ❌ "o fix do dev falhou" (não dá pra testar um código que não está rodando); é **retrabalho de
processo**: o PR precisa ser mergeado e deployado antes de qualquer validação fazer sentido.

### Bloqueio 1 (decisivo) — o PR #10181 está ABERTO e a correção NÃO está na branch default
- Verificado via API do GitHub: `state: OPEN`, `mergedAt: null`. A branch
  `fix/notificacao-analise-ia-sem-flag` **não está em nenhum ambiente** (nem stage, nem produção).
- **Cruzamento extra (descarta "entrou por outro PR"):** o histórico de commits da branch default nos
  DOIS arquivos que o fix altera não tem nenhum commit dessa correção. O commit mais recente em
  `create_question_list_attempt_ai_generated_report.rb` é de **2025-09-25 (#8198)** — meses ANTES do
  fix. Logo a correção não chegou por nenhum outro caminho.
- Testar o `clararesorts` agora exercita o **código antigo** — só reconfirmaria o bug, não a correção.
→ **Ação necessária antes de re-validar: mergear o PR #10181 e fazer o deploy.**

### Bloqueio 2 (independente) — a correção é backend (segmentação de notificação via SQS), não é card de UI/Playwright
Pelo próprio PR, o fix espelha as guards de feature flag em dois pontos do pipeline:
- `app/models/question_list_attempt.rb` → `ai_report_generation_allowed?` passa a checar
  `analise_creditos_ia_beta_test_enabled?(organization)` (bloqueia o disparo na origem — nada vai pro SQS).
- `app/application/use_cases/ai_generated_report/create_question_list_attempt_ai_generated_report.rb`
  → `create_ai_report_notification` valida a flag da org **e** `question_list.enable_ai_analysis`
  antes de despachar (defesa em profundidade para mensagens já enfileiradas).

Validar "a notificação **não** é mais disparada para orgs sem a flag" é provar um **negativo sobre um
evento backend** (pipeline assíncrono disparado por conclusão de questionário → fila SQS → notificação).
Isso **não é observável clicando na UI admin** — não é reproduzível via Playwright. É validação de
RSpec (dev) ou de banco/fila (agent-db), não de interface.

## Por que NÃO loguei no ambiente do cliente em produção
- O fix não está deployado → logar só reconfirmaria a pré-condição (a rota de relatório de IA
  retorna 403 "Administrador não possui permissão"), que o card já documenta.
- É a conta admin de um **cliente real, em produção**. Sem ganho de validação, não se justifica
  navegar/operar nesse ambiente. (Se o time quiser screenshots do estado atual para o ticket
  Movidesk, é uma ação read-only separada e explicitamente autorizada — não faz parte desta validação.)

## Confirmação de que é o PR certo
O corpo do PR bate 1:1 com o card: mesma mensagem de 403 ("Administrador não possui permissão para
acessar essa página"), mesma flag `analise_creditos_ia_beta_test`, mesma rota de relatório de IA
(`event_contents_controller#ai_generated_reports`), curso BIG FIVE. É o PR correto — só não foi mergeado.

## Plano de re-validação (quando desbloquear)
1. **Mergear o PR #10181 e deployar** (pré-requisito absoluto).
2. Validação correta (backend, não UI):
   - Org de stage **sem** a flag `analise_creditos_ia_beta_test` → concluir uma tentativa de
     questionário com análise por IA habilitada → **asserir que NENHUMA notificação é enfileirada/despachada**
     (RSpec do dev ou checagem de fila/banco via agent-db).
   - Complemento UI: confirmar que o clique na rota de relatório de IA **não cai mais em 403** para
     org habilitada (e segue bloqueado, sem notificação, para org não habilitada).
3. Este card provavelmente **não é validável pela infra Playwright** — encaminhar para validação de
   dev (RSpec) / agent-db.
