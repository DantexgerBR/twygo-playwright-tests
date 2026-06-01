# Laudo (parcial) — Retrabalho 19640 (P1) [Recertificação] Desempenho e pontuação da reinscrição atual propagado para todas as reinscrições

- **Ambiente:** Stage Recertificação — `https://recertificacao-testeqa.stage.twygoead.com/` (org **37048**)
- **Login:** `agents.claude@claude.com` (Administrador)
- **Trilha:** "Trilha para CASCADE" (id **807406**) — mesma do card 19602
- **Data:** 2026-06-01

## Veredito: ⚠ Inconclusivo (CORRIGIDO — o ❌ anterior era falso positivo)

> **Correção de veredito (2026-06-01):** eu havia emitido **❌ "dado sobrescrito/zerado"** olhando só a
> coluna Desempenho da aba Aprendizagem. Ao cruzar com a **fonte de verdade** (aba "Respostas de
> questionário"), o dado real está **PRESERVADO** → não houve perda de dado. Aquele ❌ era **falso
> positivo**. Veredito correto: **⚠ Inconclusivo** (há inconsistência de exibição a confirmar com o dev).

### O que está confirmado por evidência
- **Fonte de verdade (PRESERVADA):** na aba **"Respostas de questionário"**, `agents.claude` tem os
  quizzes **100% — Aprovado** (Prova 1ª/2ª tentativa, Questionário de Ciências). O desempenho real do
  usuário **existe e está intacto** — nada foi destruído. Evidência: `20-respostas-questionario.png`.
- **Inconsistência observada na aba Aprendizagem (a confirmar):** após a reinscrição, a coluna
  Desempenho/Pontuação por geração não bate com a performance real:
  - geração `44275175` (a que fez os quizzes a 100%): exibe **0,0% / 0**;
  - geração `44275236` (reinscrição fresca, 0% progresso): exibe **100,0% / 0**.

### Por que NÃO é ❌ (e não é ✅)
- **Não é ❌:** não consigo afirmar perda/sobrescrita de dado — o dado-fonte está preservado. O que vejo
  é a aba Aprendizagem exibindo desempenho/pontuação por geração de forma possivelmente incorreta.
- **Não é ✅:** o valor exibido na aba Aprendizagem realmente não está condizente com a performance real
  por geração; pode ser um defeito de exibição/cálculo — ou comportamento esperado pós-reinscrição que eu
  desconheço.
- **Falta pra fechar:** confirmação do **dev / banco** sobre qual desempenho/pontuação cada geração
  DEVERIA exibir após uma reinscrição. Sem isso, o honesto é **⚠ Inconclusivo**, não ❌.

---

## (Detalhe) Observação do antes/depois — NÃO interpretar como perda de dado

## (Detalhe) Reprodução ao vivo do antes/depois

### Prova definitiva — teste controlado (reinscrição pelo lado do ALUNO)
Fiz uma reinscrição na conta `agents.claude` (botão **"Reinscrever-se"** no banner da trilha, visão
aluno → "Confirmar") e comparei a **mesma inscrição** por `data-item-id`, antes e depois. Valores
lidos célula a célula (sem regex) — colunas Progresso / Desempenho / Pontuação / Certificado:

| Inscrição (data-item-id) | ANTES | DEPOIS |
|---|---|---|
| **44275175** (geração que já existia) | 100% / **100.0%** / **110** / Pendente | 0% / **0.0%** / **0** / Pendente |
| 44275236 (geração NOVA da reinscrição) | — (não existia) | 0% / 100.0% / 0 / Pendente |

A geração anterior `44275175` perdeu **desempenho 100.0% → 0.0%** e **pontuação 110 → 0**. Os valores
ganhos na geração anterior **não foram preservados** → `PRESERVADO=False`. Exatamente o bug 19640.
Evidências: `12-ANTES-admin.png` (linha 100% verde) × `16-DEPOIS-admin.png` / `17-DEPOIS-admin-full.png`
(mesma conta zerada); `_antes.json` / `_depois.json` / `_verificacao_colunas.json`.

**Argumento de identidade (por que 44275175 é a "anterior"):** o `data-item-id` é crescente; `44275236`
é a geração recém-criada pela reinscrição, logo `44275175` é a pré-existente. A aba Aprendizagem mostra
**uma linha por geração de inscrição** (há 2 linhas distintas pro agents.claude) — não é um valor único
recalculado; é o registro da geração anterior que foi sobrescrito.

**Rebatida ao "não estava finalizada" (era Pendente):** `44275175` estava **100% concluída e ELEGÍVEL
a reinscrição** — o botão "Iniciar reinscrição"/"Reinscrever-se" só habilita com 100% / aprovado /
expirado (ver card 19638). O sistema a trata como geração concluída; ao reinscrever, ela vira a geração
anterior, cujos valores ganhos deveriam ser imutáveis. Foram zerados.

**Histórico (tab):** tentei abrir "Histórico de aprendizagem"/"Histórico de certificado" da `44275175`
pra checagem extra; o item do kebab não abriu a view via automação → **não verificado**. Não altera o
veredito: o bug é reportado e reproduzido **na própria aba Aprendizagem** (onde cada geração tem sua linha).

Isso também **explica** o estado todo-zero e o red flag dos certificados "Emitido" a 0/0/0: eram
inscrições finalizadas cujos valores foram zerados por reinscrições anteriores.

> ⚠ Mutação de dados (autorizada pelo Dante): a conta `agents.claude` ficou reinscrita (nova geração
> 0% + a anterior zerada). Não revertido.

---

## (Histórico) Veredito anterior: ⚠ Inconclusivo por dados — superado pelo teste controlado acima

### Bug
Na aba Aprendizagem (visão admin) de uma trilha, o desempenho **e pontuação** da inscrição
atual estariam sobrescrevendo as inscrições **anteriores**. Esperado: desempenho/pontuação de
inscrições **já finalizadas** devem ser **imutáveis** (respeitar o histórico).

### O que foi observado (read-only)
Lista de Aprendizagem da trilha (14 inscrições) — agrupada por usuário:
- `agents.richard@claude.com`: **8 inscrições, TODAS 0% / 0.0% / 0** (1 "Emitido", 7 "Pendente").
- `agents.edu@claude.com`: **3 inscrições, TODAS 0% / 0.0% / 0** (1 "Emitido", 1 "Substituído", 1 "Pendente").
- `agents.claude@claude.com`: 1 inscrição, 100% / 100.0% / 110 (sem reinscrição).
- `richard.sebold@twygo.com`: 1 inscrição, 96% / 55.6% / 670 (sem reinscrição).
- `testeidnovo@teste.com`: 1 inscrição, 0/0/0.

### Por que está inconclusivo
O discriminador do bug = um registro **finalizado com valor não-zero** observado em um usuário que
**também tem reinscrição**, pra checar se o valor anterior foi preservado ou sobrescrito.
- As únicas contas com valores não-zero (`agents.claude`, `richard.sebold`) têm **uma só inscrição**
  (nada pra comparar).
- As contas com reinscrição (`agents.richard`, `agents.edu`) estão **todas zeradas** — inclusive as
  finalizadas (Emitido/Substituído). Estado "tudo zero" é compatível **tanto** com "corrigido (sempre
  foi zero)" **quanto** com "bug (foi zerado pela reinscrição atual a 0%)". Não distingue.

Portanto o read-only **não consegue** provar nem refutar o bug com os dados atuais.

### ⚠ Achado material pra reportar ao solicitante (Richard)
Na validação do card **19602** (mesma trilha, mesma manhã, 2026-06-01) o `agents.richard` tinha
inscrições com valores **distintos e não-zero** (ex.: 100%/30 pts, 55%/84.0%/2530 pts). Agora essas
inscrições **sumiram** e há 8 inscrições **todas zeradas** (contagem 4 → 8). Ou seja, **os dados da
trilha mudaram durante a validação** — alguém pode estar editando a trilha agora, **ou** valores
não-zero foram zerados (que seria justamente o bug). Isso é material pra um P1 e precisa de atenção.

### 🚩 Red flag concreto (sugere bug AINDA presente — confirmar)
Há inscrições com **certificado "Emitido"** exibindo **0% progresso / 0.0% desempenho / 0 pontuação**:
- `agents.richard@claude.com` — 1 linha Emitido a 0/0/0.
- `agents.edu@claude.com` — 1 linha Emitido a 0/0/0 e 1 "Substituído" a 0/0/0.

Isso é **contraditório**: um certificado emitido (inscrição finalizada/concluída) deveria ter sido
gerado com 100% de progresso e desempenho/pontuação de aprovação. Mostrar 0/0/0 é compatível com o
bug — os valores históricos da inscrição finalizada foram **sobrescritos** pela reinscrição atual
(a 0%). (Ressalva: não dá pra descartar 100% que o certificado tenha sido emitido manualmente pelo
admin; por isso o veredito fica como ⚠, não ❌.)

### Teste controlado — TENTADO, não concluído (automação)
Tentei disparar "Iniciar reinscrição" na conta `agents.claude` (100%/110, item HABILITADO/ícone azul)
para gerar o par antes/depois. O clique **registra** (menu fecha) mas **não produz efeito observável**:
sem modal de confirmação, sem diálogo nativo, sem nova inscrição criada, e a inscrição existente
permanece 100%/110. Ou seja, **não consegui atuar a reinscrição via Playwright** — nenhum dado foi
alterado no stage. O acionamento parece exigir interação que minha automação não reproduziu.

### Próximo passo (decisão do Dante)
Opções: (a) o Dante (ou o dev) faz a reinscrição manualmente na `agents.claude` e me chama pra
observar o antes/depois; (b) o dev confirma direto no banco se os valores históricos das inscrições
"Emitido"/"Substituído" foram sobrescritos; (c) entregar ⚠ Inconclusivo com o red flag acima.

### Evidências
- `01-lista-aprendizagem.png` — lista atual (todos os multi-inscrições zerados)
- `_inscricoes.txt` / `_inscricoes.json` — dump das 14 inscrições
