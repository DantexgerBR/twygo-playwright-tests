# Laudo — Retrabalho Artia 20297

**Card**: 20297 — P1 [Registros F2] Gestor de turma recebe 401 ao vincular pessoas no form de registro (TC3)
**Card original do bug**: 19893 (laudo QA1.6, TC3, BUG P1)
**Data de execução**: 2026-07-01
**Ambiente**: Stage — https://registrosf2.stage.twygoead.com/ (Org 37079)
**Executor**: Playwright E2E headed (Python), `scripts/retrabalho_20297_401_vincular_pessoas_lider.py`
**PR avaliado**: https://github.com/Twygo/twyg-app/pull/10868/

> **Veredito ajustado após alinhamento com o dev (01/07):** o PR #10868 ajustou o
> endpoint só para o fluxo do **Aluno** (retorna o próprio usuário). Para o
> **Gestor (Líder)**, o vínculo de liderados **não é feito por essa modal** —
> vai ganhar **tela própria**, já rastreada no card Artia **33126594**. Ou
> seja, o 401 remanescente em `professionals`/`professionals/results_for_filter`
> para o Líder **não é bug desta PR** — é escopo que nunca foi desta entrega.
> Execução deste retrabalho (20297) → **card ✅**; o bloqueio real do Gestor
> segue rastreado (e cobrado) no card 33126594, não aqui.

## Veredito

**✅ Passou (pós-alinhamento)** — ver nota acima. Achados técnicos originais (abaixo) permanecem válidos como evidência do estado atual do endpoint; a leitura de "bug" foi substituída por "fora de escopo, tratado em outro card".

<details>
<summary>Veredito original desta execução (pré-alinhamento, para histórico)</summary>

**❌ Ainda quebrado (correção parcial)** — O PR #10868 corrigiu **1 de 3** endpoints citados no bug, mas os **2 endpoints centrais** (que alimentam a lista de pessoas do modal) continuam retornando 401. Interpretação inicial: Gestor de turma (Líder) permanece bloqueado por falha da PR. Corrigido pela nota de alinhamento acima — o bloqueio é real, mas por escopo (tela ainda não construída), não por regressão desta PR.

</details>

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
✅ Passou
:: Ambiente ::
🧪 Stage — https://registrosf2.stage.twygoead.com/ (Org 37079)
:: Validação ::
PR #10868 ajustou o endpoint de vínculo de pessoas para o fluxo do Aluno (retorna o próprio usuário — antes 401 em event_sources/get_provider_names, agora 200). Confirmado ao vivo com 2 líderes (qalider@teste.com — usuário da evidência original do bug 19893/TC3 — e qaliderpuro@teste.com): GET /professionals e /professionals/results_for_filter continuam 401 na sessão do Líder, modal "Vincular pessoas" segue "Nenhum item encontrado".
:: Obs ::
Conforme alinhamento com o dev (01/07): o vínculo de liderados pelo Gestor de turma não é entregue por essa modal — terá tela própria, já rastreada no card 33126594. O 401 remanescente em professionals* para o Líder não é regressão desta PR; é escopo pendente daquele card, não deste retrabalho. Severidade P1 do bloqueio ao Gestor segue integralmente no card 33126594 — não foi "perdoada", só realocada para onde o trabalho de fato será feito.
Link da atividade que trata o Gestor: card Artia 33126594.
:: Evidência(s) ::
- lider1_qalider_01_form.png (toast 401 visível — estado atual do endpoint pro Líder)
- lider1_qalider_02_modal_apos_click.png (modal vazio, líder da evidência original)
- lider2_qaliderpuro_02_modal_apos_click.png (modal vazio, segundo líder)
- resultado.json (captura completa de Network por líder)
Evidência no link: https://github.com/DantexgerBR/twygo-playwright-tests/tree/main/evidencias/retrabalho-20297
```
