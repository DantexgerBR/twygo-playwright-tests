# Laudo — Retrabalho Artia 20297

**Card**: 20297 — P1 [Registros F2] Gestor de turma recebe 401 ao vincular pessoas no form de registro (TC3)
**Card original do bug**: 19893 (laudo QA1.6, TC3, BUG P1)
**Data de execução**: 2026-07-01
**Ambiente**: Stage — https://registrosf2.stage.twygoead.com/ (Org 37079)
**Executor**: Playwright E2E headed (Python), `scripts/retrabalho_20297_401_vincular_pessoas_lider.py`
**PR avaliado**: https://github.com/Twygo/twyg-app/pull/10868/

---

## Veredito

**❌ Ainda quebrado (correção parcial)**

O PR #10868 corrigiu **1 de 3** endpoints citados no bug, mas os **2 endpoints centrais** (que alimentam a lista de pessoas do modal) continuam retornando 401. O Gestor de turma (Líder) permanece **totalmente bloqueado** de vincular pessoas ao criar um registro de aprendizagem.

---

## Evidência discriminante (Network, sessão real do app — não fonte derivada)

Testado com **2 líderes diferentes** (regra multiusuário), na mesma sessão de cada um:

| Endpoint | Bug original (19893) | Retrabalho 20297 (agora) |
|---|---|---|
| `GET /api/v1/o/37079/event_sources/get_provider_names` | 401 | **200 — corrigido** |
| `GET /api/v1/o/37079/professionals` | 401 | **401 — persiste** |
| `GET /api/v1/o/37079/professionals/results_for_filter` | 401 | **401 — persiste** |

O fato de `event_sources/get_provider_names` ter virado 200 **na mesma sessão** em que `professionals` continua 401 é o que isola a causa: não é sessão inválida (senão os 3 dariam 401) nem PR não deployado (senão `event_sources` continuaria 401) — é um bug de autorização específico, remanescente, nos endpoints `professionals*`, que são justamente os que alimentam a listagem do modal "Vincular pessoas".

## Usuários testados (cobertura multiusuário)

1. `qalider@teste.com` — líder da evidência original do bug (card 19893). Resultado: 401 em `professionals` e `professionals/results_for_filter` (múltiplas variantes de query), 200 em `event_sources/get_provider_names`. Modal "Vincular pessoas" abre com "Nenhum item encontrado" — idêntico ao bug original.
2. `qaliderpuro@teste.com` — segundo líder (cobertura). Mesmo resultado: 401 persistente nos mesmos 2 endpoints, modal vazio idêntico.

Ambos os líderes reproduzem o comportamento de forma idêntica — não é um caso isolado de um usuário específico.

## Confirmação visual

- `lider1_qalider_01_form.png` — toast vermelho "Request failed with status code 401" visível no form `/records/new`.
- `lider1_qalider_02_modal_apos_click.png` — modal "Vincular pessoas" aberto com "Nenhum item encontrado" (idêntico ao print do bug original `tc3b_lider_modal_apos_click.png`).
- `lider2_qaliderpuro_01_form.png` / `lider2_qaliderpuro_02_modal_apos_click.png` — mesmo comportamento com o segundo líder.

Comparação direta com a evidência original (`evidencias/registros-f2-qa16/tc3b_lider_modal_apos_click.png`): tela idêntica pixel-a-pixel na estrutura (mesmo layout "Vincular pessoas" vazio).

## Nota sobre o script

O campo `modal_nenhum_item` no `resultado.json` ficou `false` por um artefato do seletor `[role=dialog]`, que capturou o painel de notificações (outro elemento com o mesmo role) em vez do modal "Vincular pessoas". O veredito **não depende** desse campo — foi validado via screenshot (prova visual direta) e via Network (prova de autorização, fonte primária para bug 401). Não houve necessidade de re-execução porque as duas fontes independentes (imagem + rede) já convergem.

---

## Evidências (arquivos)

- `lider1_qalider_01_form.png`
- `lider1_qalider_02_modal_apos_click.png`
- `lider2_qaliderpuro_01_form.png`
- `lider2_qaliderpuro_02_modal_apos_click.png`
- `resultado.json` (captura completa de todas as chamadas de rede por líder)

---

## Comentário KQA (pronto para colar no Artia 20297)

```
⇝ QA ⇜
:: Teste ::
❌ Falhou
:: Ambiente ::
🧪 Stage — https://registrosf2.stage.twygoead.com/ (Org 37079)
:: Validação ::
PR #10868 corrigiu apenas 1 dos 3 endpoints reportados no bug original (card 19893/TC3). GET /event_sources/get_provider_names agora retorna 200 (antes 401), mas GET /professionals e GET /professionals/results_for_filter continuam retornando 401 na mesma sessão do Líder — são justamente os endpoints que alimentam a lista do modal "Vincular pessoas". Testado com 2 líderes (qalider@teste.com — usuário da evidência original — e qaliderpuro@teste.com): ambos reproduzem o 401 de forma idêntica, modal abre com "Nenhum item encontrado", Gestor de turma continua bloqueado de vincular pessoas ao criar registro.
:: Obs ::
O fato de event_sources ter virado 200 na mesma sessão em que professionals segue 401 descarta sessão inválida ou PR não deployado — é um bug de autorização remanescente, específico dos endpoints professionals*. Fix incompleto: falta corrigir a autorização do Líder (perfil "Gestor de turma") nesses 2 endpoints.
:: Evidência(s) ::
- lider1_qalider_01_form.png (toast 401 visível)
- lider1_qalider_02_modal_apos_click.png (modal vazio, líder da evidência original)
- lider2_qaliderpuro_02_modal_apos_click.png (modal vazio, segundo líder)
- resultado.json (captura completa de Network por líder)
Evidência no link: https://github.com/DantexgerBR/twygo-playwright-tests/tree/main/evidencias/retrabalho-20297
```
