# Plano — Twygo QA App (Flet Desktop) — ❌ CANCELADO em 2026-05-25

> **STATUS: CANCELADO.** Trabalho preservado no código (commits 936b45b..08afb65) e nesse documento pra referência futura, mas **abandonado** como produto.
>
> **Motivo do cancelamento:** Custo/complexidade de manter um agente LLM (Gemini quota / Groq instabilidade / proxy corporativo da Twygo interrompendo conexões) ficaram acima do valor entregue. O agente conseguia logar como admin e navegar, mas:
> - Gemini grátis esgota cota rápido em uso real
> - Groq teve problemas de nome de modelo (`meta-llama/llama-4-maverick-17b-128e-instruct` retornou 404)
> - Rede corporativa derruba conexões com APIs externas
> - QA crítica precisa de mais confiabilidade que LLMs free oferecem hoje
>
> **Novo fluxo (em uso a partir de 2026-05-25):** o Dante manda o retrabalho (texto + print) direto no chat do Claude Code, que então:
> 1. Escreve/adapta um script Playwright em Python usando o conftest.py e pages/ existentes
> 2. Roda o script via venv local (sem API LLM externa)
> 3. Captura screenshot do estado pós-correção
> 4. Compara visualmente com o print do bug original (Dante anexa) ou analisa pelo DOM
> 5. Emite veredito e gera comentário no padrão KQA pro Dante colar no Artia
>
> **O que continua sendo útil do código deste plano (mesmo cancelado):**
> - `app/services/retrabalho_parser.py` — útil pra parsear retrabalhos do Artia
> - `app/services/jam_fetcher.py` — útil pra baixar prints do Jam.dev
> - `app/services/kqa_comment.py` — útil pra gerar comentário KQA
> - `app/services/git_committer.py` — útil pra commitar evidências
> - `app/services/stage_health.py` — útil pra verificar se stage tá no ar
> - `app/services/browser.py` — wrapper Playwright com login admin do Twygo
> - 112 testes unitários servindo de documentação executável dos componentes
>
> **O que NÃO usar mais:**
> - `app/main.py` e `app/views/*` — UI Flet, descontinuada
> - `app/agents/qa_agent.py` e `llm_client.py` — agente LLM, descontinuado
> - `run.cmd` — entry point da UI, descontinuado
>
> ---

> Roteiro original (preservado abaixo pra contexto):
> Transformar o projeto `twygo-playwright-tests` em um aplicativo desktop com UI em **Flet**, mantendo todo o backend (parser, executor, llm, generator, reporter) intacto.

## Objetivo

Entregar um `.exe` para Windows que:

- Tem **5 abas**: **📚 Documentação**, **📋 Caso**, **🖼️ Evidências**, **▶ Execução**, **📊 Resultado**
- Suporta **2 modos de operação** (selecionados no topo da janela): **🔁 Retrabalho** e **📐 Caso de teste T-XXXX**
- Carrega **documentação do projeto** (discovery, usabilidade, regras de negócio) que vira contexto persistente do agente
- Loga no **stage** com credenciais do `.env` (nunca no código)
- Reproduz os passos via Playwright dirigido pelo **Claude API** (agente QA especializado, com prompt caching das docs + system prompt)
- Salva evidências em `evidencias/T-XXXX/` e **commita** automaticamente no Git

Stack: **Python 3.12 + Flet + Playwright + Anthropic SDK + PyInstaller (fallback)**.

---

## Modos de operação

O app tem um **seletor de modo** no canto superior direito que altera o comportamento das abas Caso e Resultado. As abas Documentação, Evidências e Execução são compartilhadas entre os modos.

### 🔁 Modo Retrabalho

Para **validação rápida de correções de bug**. O agente reproduz um problema relatado e checa se ainda acontece.

**Entrada:**
- Descrição do retrabalho colada do Artia (formato `:: Incidente identificado :: ... :: Passo a passo para reprodução :: ... :: Comportamento esperado ::`)
- Evidência visual do bug original (print colado, arquivo anexado, link Jam)

**Saída:**
- **Laudo**: ✅ corrigido / ❌ ainda quebrado / ⚠️ inconclusivo
- **Comentário KQA** pronto pra colar no Artia (formato `⇝ QA ⇜ ...`)
- Detecção automática de links Jam no texto

**Quando usar:** "fui notificado que tem um retrabalho do bug X, preciso validar rápido se está corrigido pra fechar".

### 📐 Modo Caso de teste T-XXXX

Para **casos de teste estruturados** completos (muitos passos, formato Twygo). É o que o projeto atual já faz via Gradio.

**Entrada:**
- Caso colado no formato Twygo (Objetivo + Pré-condições + tabela `N | Ação | Resultado Esperado | Execução | Notas | Status`)
- OU seleção de um caso existente em `docs/casos/T-XXXX.md`

**Saída:**
- Arquivo **pytest persistente** em `tests/gerado/test_<slug>.py` (vira regressão futura)
- Doc Markdown em `docs/casos/<slug>.md`
- **Bug report** no formato Twygo (`:: Incidente identificado :: ...`) se algum passo falhar
- Screenshots passo a passo + trace.zip

**Quando usar:** "estou homologando uma feature nova, preciso passar pelo caso de teste completo e deixar a automação pronta pra regressão".

### Compartilhamento entre modos

| Componente | Compartilhado? |
|---|---|
| Aba 📚 Documentação | Sim — mesmas docs alimentam ambos os agentes |
| Aba 🖼️ Evidências | Sim, mas semântica diferente: em Retrabalho é "bug original"; em Caso de teste é "evidência de pré-condição já satisfeita" |
| Aba ▶ Execução | Sim — mesmas credenciais, mesma máquina de execução |
| Aba 📋 Caso | Adapta o formulário (Retrabalho = texto livre; Caso = formato estruturado) |
| Aba 📊 Resultado | Adapta a saída (Retrabalho = laudo + KQA; Caso = arquivo pytest + bug report) |
| `app/agents/qa_agent.py` | Mesmo agente, com **system prompts diferentes** por modo |

---

## Login e credenciais (componente transversal)

### Princípio de segurança

Credenciais **nunca** ficam no código, em commits, em README ou em logs. Toda persistência acontece em arquivos locais que estão (ou serão garantidos) no `.gitignore`. Cliente final é o único que vê os valores em texto puro.

### Onde a senha é guardada

| Camada | Local | Quando é usada |
|---|---|---|
| **Em uso (memória)** | `AppState.credenciais` | Durante a execução do app |
| **Disco — opção 1 (padrão)** | `.env` (já gitignored) | Quando você marca "Salvar credenciais" |
| **Disco — opção 2 (mais seguro)** | Windows Credential Manager via `keyring` | Quando você marca "Usar Credential Manager do Windows" |

> **Por que duas opções:** `.env` é simples mas armazena em texto puro. `keyring` usa criptografia do Windows. O usuário escolhe o trade-off entre comodidade e segurança.

### Tela de login (primeira execução)

Na **primeira vez** que o app abre (sem `.env` preenchido), aparece um dialog modal:

```
┌─ Configurar acesso ao Twygo ──────────────────────────┐
│                                                       │
│  URL da org de stage:                                 │
│  [https://twygo<sua-org>.stage.twygoead.com/      ]   │
│                                                       │
│  Admin                                                │
│  E-mail: [..............................]            │
│  Senha:  [••••••••••••••]  [👁]                       │
│                                                       │
│  Aluno (opcional — usa Admin se vazio)                │
│  E-mail: [..............................]            │
│  Senha:  [••••••••••••••]  [👁]                       │
│                                                       │
│  ANTHROPIC_API_KEY (pra rodar o agente Claude)        │
│  [sk-ant-..............]  [👁]                        │
│                                                       │
│  [✓] Salvar credenciais (em .env, gitignored)         │
│  [ ] Usar Credential Manager do Windows (mais seguro) │
│                                                       │
│  [Testar login]            [Cancelar]  [Salvar]       │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### Botão "Testar login"

Abre uma janela do Playwright (não-headless), navega para `BASE_URL`, tenta logar com admin. Resultado:
- ✅ Verde "Login OK" → habilita "Salvar"
- ❌ Vermelho "Falhou: senha incorreta / org não encontrada" → corrige

### Acessar configurações depois

- Ícone ⚙️ no canto superior direito da janela
- Abre o mesmo dialog com os valores atuais
- Botão extra: **🗑️ Esquecer credenciais salvas** — apaga do `.env` e do `keyring`

### Garantia de gitignore

Antes de **qualquer** escrita em disco com credenciais, o app valida que existe `.gitignore` com pelo menos:
```
.env
.env.*
state.json
docs/projetos/*/_credentials.json
```

Se não estiver, o app **se recusa a salvar** e mostra mensagem:
> ⚠️ `.gitignore` não cobre o arquivo de credenciais. Salvamento cancelado para evitar vazamento. Veja `app/services/gitignore_guard.py` para detalhes.

### Implementação (arquivos novos)

- [ ] `app/views/login_view.py` — dialog modal de login
- [ ] `app/services/credentials.py` — read/write em `.env` ou `keyring`
- [ ] `app/services/gitignore_guard.py` — valida que arquivos sensíveis estão cobertos
- [ ] `app/services/login_tester.py` — abre Playwright, testa login, fecha

---

## Etapa 0 — Pré-requisitos (uma vez)

- [ ] Confirmar `python --version` ≥ 3.10
- [ ] Ativar venv: `python -m venv .venv` e `.venv\Scripts\Activate.ps1`
- [ ] Instalar requirements existentes: `pip install -r requirements.txt`
- [ ] Adicionar e instalar novas deps: `pip install flet pillow pyperclip httpx pypdf keyring`
- [ ] `playwright install chromium` (se ainda não estiver instalado)
- [ ] Atualizar `requirements.txt` com as novas deps

> **Por quê cada uma:** Flet (UI), Pillow (clipboard de imagem), pyperclip (clipboard de texto), httpx (download HTTP), pypdf (ler PDFs), keyring (guardar senha no Credential Manager do Windows — alternativa segura ao .env).

---

## Etapa 1 — Estrutura inicial do app Flet

- [ ] Criar pasta `app/`
- [ ] Criar arquivos vazios:
  - `app/__init__.py`
  - `app/main.py` — entrada principal do Flet
  - `app/state.py` — estado compartilhado entre abas
  - `app/ui_kit.py` — componentes visuais reutilizáveis (cards, botões, status badge, laudo grande, empty states)
  - `app/theme.py` — tokens de design (cores, tipografia, espaçamentos) + alternância claro/escuro
  - `app/views/__init__.py`
  - `app/views/login_view.py` — dialog modal de login (componente transversal)
  - `app/views/documentacao_view.py`
  - `app/views/caso_view.py`
  - `app/views/evidencias_view.py`
  - `app/views/execucao_view.py`
  - `app/views/resultado_view.py`
  - `app/views/aprendizado_dialog.py` — dialog que pede aprovação de lições aprendidas
  - `app/services/__init__.py`
  - `app/services/credentials.py` — read/write em `.env` ou `keyring`
  - `app/services/gitignore_guard.py` — valida que arquivos sensíveis estão cobertos
  - `app/services/login_tester.py` — testa login via Playwright
  - `app/services/clipboard.py`
  - `app/services/jam_fetcher.py`
  - `app/services/comparador.py`
  - `app/services/git_committer.py`
  - `app/services/kqa_comment.py`
  - `app/services/doc_loader.py` — lê md/pdf/txt
  - `app/agents/__init__.py`
  - `app/agents/qa_agent.py`
- [ ] Atualizar `.gitignore` com:
  - `.env`
  - `.env.*`
  - `app/state.json`
  - `docs/projetos/*/_credentials.json`
  - `build/`
  - `dist/`
- [ ] Criar pasta para documentação por projeto: `docs/projetos/<nome>/`
  - Exemplo: `docs/projetos/modelos/` (projeto que você está trabalhando agora)

**Estado esperado:** rodar `python -m app.main` abre uma janela. Se for a primeira execução (sem `.env`), aparece o dialog de login antes da janela principal.

---

## Etapa 2 — Estado compartilhado (`app/state.py`)

- [ ] Classe `AppState` com atributos:
  - `projeto_ativo: str | None` (ex: "modelos")
  - `documentacao: list[Documento]` (cada um: path, tipo='md'|'pdf'|'txt'|'imagem', conteudo: str)
  - `caso: CasoTeste | None`
  - `evidencias: list[Evidencia]`
  - `execucao_em_progresso: bool`
  - `resultado: ResultadoExecucao | None`
  - `log_lines: list[str]`
- [ ] Padrão observer: views se inscrevem em eventos de estado
- [ ] Persistência local em `app/state.json` — ao abrir o app, restaura o projeto/docs do último uso

---

## Etapa 3 — Aba 📚 Documentação (`app/views/documentacao_view.py`)

> **Por que essa aba existe:** o agente QA precisa saber **as regras de negócio do projeto** que está testando, não só os passos do bug. Sem isso, ele não consegue distinguir "comportamento bugado" de "comportamento esperado de outra feature".

### Princípio fundamental — Documentação é persistente por projeto

A documentação fica **salva permanentemente no disco**, em `docs/projetos/<projeto>/`. Você anexa **uma vez** e nunca mais precisa reanexar. Da próxima vez que abrir o app e selecionar o mesmo projeto, todos os documentos aparecem automaticamente na lista.

Estrutura no disco:
```
docs/
└── projetos/
    ├── modelos/                  ← projeto que você está trabalhando agora
    │   ├── discovery.md          ← arquivos persistidos
    │   ├── regras-negocio.pdf
    │   ├── usabilidade-mockup.png
    │   └── _meta.json            ← metadados (tags, descrição, data de upload)
    ├── certificados/             ← outro projeto futuro
    │   └── ...
    └── aprender-mobile/
        └── ...
```

### Componentes da aba

- [ ] **Dropdown "Projeto ativo"** — lista pastas existentes em `docs/projetos/`. Selecionar carrega automaticamente todos os documentos.
- [ ] **Botão "+ Novo projeto"** — dialog pedindo nome → cria pasta `docs/projetos/<nome>/` e seleciona
- [ ] **Lista de documentos do projeto ativo** (carregada do disco ao selecionar projeto):
  - Cada item: nome do arquivo, tipo (md/pdf/txt/imagem), tamanho, tokens estimados
  - Botão 👁️ "ver" (abre o arquivo no visualizador padrão do Windows)
  - Botão 🗑️ "remover" (apaga do disco após confirmação)
  - Badge "✓ Carregado" se o conteúdo está no `AppState` pronto pra alimentar o agente
- [ ] **Barra de status**: "📚 Projeto **modelos**: 5 documentos persistidos (~12.4k tokens). Cache do agente: ativo."
- [ ] **Botões de adicionar** (cada um copia/salva o arquivo dentro de `docs/projetos/<projeto>/` e atualiza a lista):
  - `📂 Adicionar arquivo` — file picker (.md, .pdf, .txt, .png, .jpg)
  - `📋 Colar texto` — dialog com text area, salva como `colado_<timestamp>.md`
  - `📷 Colar imagem` — captura clipboard, salva como `imagem_<timestamp>.png`
  - `🔁 Reaproveitar de outro projeto` (stretch) — abre lista de docs de outros projetos, copia o selecionado pra o atual

### Tipos suportados

- `.md` e `.txt` → leitura direta como texto
- `.pdf` → extração via `pypdf.PdfReader`
- `.png` e `.jpg` → mantém path; enviados ao agente como vision content (não convertidos em texto)

### Indicador de cache

Como a documentação completa entra como bloco **cacheado** no Claude (`cache_control: {"type": "ephemeral", "ttl": "1h"}`), na primeira execução do projeto o sistema mostra:

> 🔄 Primeiro uso do projeto **modelos** hoje — vai construir o cache (custo cheio nessa rodada)

Nas execuções seguintes (dentro de 1 hora):

> ⚡ Cache ativo (~92% de economia) — ~3 horas restantes no TTL

---

## Etapa 4 — Aba 📋 Caso (`app/views/caso_view.py`)

- [ ] `ft.TextField` multiline, height 400, placeholder com exemplo de caso Twygo
- [ ] `ft.ElevatedButton` "Analisar" — chama `ui.parser.parse_caso(texto)`
- [ ] Área de resumo abaixo:
  - "✓ Parseado: N passos, M pré-condições"
  - "Objetivo: ..."
  - Lista de passos detectados
- [ ] Detectar URLs de jam.dev no texto e adicionar como evidência candidata
- [ ] Aviso amarelo se `AppState.documentacao` estiver vazia: "⚠ Você não carregou documentação do projeto na aba 📚. O agente pode errar regras de negócio."
- [ ] Persistir o caso no `AppState` ao analisar

---

## Etapa 5 — Aba 🖼️ Evidências (`app/views/evidencias_view.py`)

- [ ] Cabeçalho: "Evidências do bug original"
- [ ] Botões:
  - `📂 Anexar arquivo` (FilePicker, aceita PNG, JPG, MP4)
  - `📋 Colar da área de transferência` — usa `services/clipboard.py`
  - Drag-and-drop direto na janela
- [ ] Para cada evidência:
  - Miniatura
  - Nome do arquivo
  - Tipo: 🖼️ Print | 🎬 Vídeo | 🔗 Link Jam
  - Botão 🗑️ remover
- [ ] Se for vídeo: badge "Não consigo analisar conteúdo de vídeo — anexe um frame ou peça pra reabrir o retrabalho com print"
- [ ] Se for link Jam (detectado pela aba Caso): tenta baixar via `services/jam_fetcher.py`

**Verificação:** colar print do Win+Shift+S → aparece miniatura.

---

## Etapa 6 — Serviços de evidência e doc

### 6a. `app/services/clipboard.py`
- [ ] `get_image_from_clipboard() -> Path | None` usando `PIL.ImageGrab.grabclipboard()`
- [ ] Salva como `evidencias/_clipboard/clip_<timestamp>.png`

### 6b. `app/services/jam_fetcher.py`
- [ ] `fetch_jam_url(url: str) -> Path | None | "video"`
- [ ] httpx GET → procura `<meta property="og:image">` ou `<meta property="og:video">`
- [ ] Se imagem: baixa em `evidencias/_jam/jam_<id>.png`
- [ ] Se vídeo: retorna `"video"`
- [ ] Trata 404, timeout

### 6c. `app/services/doc_loader.py`
- [ ] `load_doc(path: Path) -> Documento` — detecta tipo pela extensão
- [ ] `.md`, `.txt`: lê como string
- [ ] `.pdf`: usa `pypdf.PdfReader`, junta todas as páginas em uma string
- [ ] `.png`, `.jpg`: marca como visual, não extrai texto
- [ ] Estima tokens (`len(texto) / 4` é aproximação grosseira do Claude)

---

## Etapa 7 — Aba ▶ Execução (`app/views/execucao_view.py`)

- [ ] Campos pré-carregados do `.env` (read-only com ícone de cadeado):
  - BASE_URL, ADMIN_EMAIL/PASSWORD, ALUNO_EMAIL/PASSWORD, ORG_ID
- [ ] `ft.Checkbox` "Headless" (padrão: desligado pra ver acontecer)
- [ ] `ft.Checkbox` "Slow motion" (500ms entre ações)
- [ ] Painel de **resumo do contexto** que será enviado ao agente:
  - "📚 N documentos do projeto X (~Y tokens cacheados)"
  - "📋 Caso de N passos"
  - "🖼️ M evidências"
- [ ] Botão grande "▶ Executar reprodução do retrabalho"
- [ ] Área de log abaixo (read-only, monospaced, auto-scroll)

**Fluxo ao clicar Executar:**
1. Valida: tem caso + tem ao menos uma evidência (docs são opcionais mas avisa se vazio)
2. Cria `QAAgent` (etapa 9) injetando docs + caso + evidências + credenciais
3. Roda em thread separada — emite logs no UI conforme avança
4. Ao terminar, popula a aba 📊 Resultado e auto-navega pra ela

---

## Etapa 8 — Aba 📊 Resultado (`app/views/resultado_view.py`)

- [ ] **Laudo grande no topo** (card colorido):
  - ✅ verde "Corrigido"
  - ❌ vermelho "Ainda quebrado"
  - ⚠️ amarelo "Inconclusivo"
- [ ] **Comparação visual lado a lado**:
  - Esquerda: evidência do bug original
  - Direita: screenshot do estado atual
- [ ] **Bug report** (se ainda quebrado) — formato Twygo do `ui.reporter`
- [ ] **Comentário KQA** (se passou) — gerado por `services/kqa_comment.py`:
  ```
  ⇝ QA ⇜
  :: Teste ::
  ✅ Passou
  :: Ambiente ::
  🧪 Stage
  :: Validação ::
  <descrição automática do que foi validado>
  :: Obs ::
  <opcional, vazio se nada>
  :: Evidência(s) ::
  <lista de paths das evidências geradas>
  Evidência no link: <URL do commit no GitHub>
  ```
  - Botão "📋 Copiar comentário" coloca na clipboard
- [ ] **Botão "💾 Commitar evidências"** — chama `services/git_committer.py`
- [ ] Após commit, mostra link do commit no GitHub e atualiza o comentário KQA com o link

---

## Aprendizado contínuo (cross-cutting)

> **Princípio:** o agente deve ficar **melhor** a cada execução, sem precisar de retreinamento. Não é fine-tuning — é acumular lições aprendidas em um arquivo que entra no contexto cacheado.

### Como funciona

A cada execução, o agente pode emitir **lições aprendidas** quando descobre algo útil (seletor flaky, atalho que funciona melhor, regra de negócio escondida). Essas lições são acumuladas em `docs/projetos/<projeto>/_aprendizado.md` — que vira parte do bloco cacheado do prompt.

Exemplo de entrada em `_aprendizado.md`:
```markdown
## 2026-05-25 — T-1603 cards-design

- **Lição:** No editor de modelo, a aba "Design" carrega de forma lazy.
  Sempre esperar `page.wait_for_selector('.card-grafico', state='attached')`
  antes de clicar nos cards.
- **Lição:** Cards de tipo "PÁGINA" e "AULA" têm seletores diferentes:
  `.card-pagina` × `.card-aula`. Filtrar por classe específica.
- **Anti-padrão:** Não usar `page.locator('text=Capa').click()` — existem
  múltiplos elementos com esse texto. Usar `.card-pagina[data-name="Capa"]`.
```

### Mecanismo de adição

- [ ] Após cada execução, o agente avalia: "aprendi algo que vale guardar?"
- [ ] Se sim, gera bloco em formato padrão e o app **mostra ao usuário** antes de salvar
- [ ] Usuário aprova/edita/descarta cada lição via dialog
- [ ] Lições aprovadas são apendadas em `_aprendizado.md` do projeto
- [ ] Na próxima execução, o arquivo inteiro vai no bloco cacheado (system + docs + aprendizado)

> **Por que o usuário aprova:** evita que o agente acumule lições erradas (alucinações que viram regras). Curadoria humana mantém o conhecimento limpo.

---

## Detecção de "stage down" (cross-cutting)

> **Princípio:** o stage da Twygo cai periodicamente quando os devs atualizam o banco de dados. O app deve **detectar** isso e **avisar de forma amigável**, em vez de tentar rodar testes que vão falhar com erro estranho ou travar o app.

### Como detectar

Antes de iniciar **qualquer execução** que dependa do stage:

1. Fazer um GET simples na `BASE_URL` com timeout de 5s
2. Se retornar 5xx, timeout, ou connection refused → considerar "stage down"
3. Se retornar 200 (ou redireciona pra login) → stage OK

Também detectar **durante** a execução: se Playwright pegar timeout/erro de rede em qualquer passo, classificar como "stage down possivelmente caiu".

### Como avisar o usuário

- Banner laranja no topo da janela:
  > 🟠 **Stage parece estar fora do ar.** Os devs costumam reiniciar o banco. Aguarde 2-5 minutos e tente de novo.
- Botão "Verificar de novo" pra retentar a checagem
- Bloqueia o botão "▶ Executar" enquanto o stage estiver down
- Polling automático opcional (a cada 30s) — quando voltar, banner some sozinho

### Onde implementar

- `app/services/stage_health.py` — função `verificar_stage(base_url: str) -> "ok" | "down" | "erro"`
- `app/views/execucao_view.py` — chama a verificação antes de habilitar o botão Executar
- `app/agents/qa_agent.py` — durante a execução, se pegar `TimeoutError` ou `ConnectionError` do Playwright, retorna laudo `INCONCLUSIVO` com justificativa "stage indisponível"

### Implementação prioritária

Fatia onde entra: **Fatia 4 (Execução + Agente)**. Não bloqueia as fatias anteriores.

---

## Reverificação (cross-cutting)

> **Princípio:** "uma execução bem-sucedida" não é suficiente para declarar passa. Reverificar reduz falsos positivos.

### Estratégia: double-check + consenso

Para cada passo crítico (e **sempre** para o "Comportamento esperado" final):

- [ ] Após executar o passo, o agente tira screenshot e classifica: PASSA / FALHA / INCONCLUSIVO
- [ ] Espera 500ms (deixa animações terminarem) e tira **segundo** screenshot
- [ ] Re-classifica com base no segundo screenshot
- [ ] Se as duas classificações concordam (PASSA × PASSA ou FALHA × FALHA) → mantém o laudo
- [ ] Se discordam → marca o passo como INCONCLUSIVO e logga: "primeira leitura: X; segunda: Y; precisa olho humano"
- [ ] Configurável: usuário pode aumentar pra 3 leituras (consenso 2-de-3) em casos mais delicados

### Onde implementar

- `app/agents/qa_agent.py` — método `_verificar_passo(passo, screenshots: list[Path]) -> Laudo`
- `app/services/comparador.py` — função `comparar_screenshots_consenso(prints: list[Path], esperado: str, n_leituras: int) -> Laudo`

### Custos

Cada reverificação é **uma chamada extra** ao Claude por passo crítico. Para um caso de teste com 10 passos e n=2, são 20 chamadas em vez de 10. Com prompt caching ativo, o overhead é ~10% (cache absorve a parte fixa).

---

## Design system (cross-cutting)

> **Princípio:** app desktop bonito ≠ Material Design genérico do Flet padrão. Tem que ter identidade visual coerente com o que profissionais entregam.

### Paleta (modo claro e escuro)

| Token | Claro | Escuro |
|---|---|---|
| `bg.primary` | `#FAFAFA` | `#0F1014` |
| `bg.surface` | `#FFFFFF` | `#1A1B22` |
| `bg.elevated` | `#F4F4F5` | `#23252E` |
| `text.primary` | `#0F1014` | `#F4F4F5` |
| `text.muted` | `#71717A` | `#A1A1AA` |
| `accent` | `#7C3AED` (Twygo roxo) | `#A78BFA` |
| `success` | `#16A34A` | `#22C55E` |
| `warning` | `#F59E0B` | `#FBBF24` |
| `error` | `#DC2626` | `#EF4444` |
| `border` | `#E4E4E7` | `#27272A` |

Inspiração: roxo da identidade Twygo (visto no print dos cards), neutros do Vercel/Linear, semânticos do Tailwind.

### Tipografia

- **Família**: Inter (fallback `system-ui`). Bundled no `.exe` via `assets/fonts/Inter-*.ttf`
- **Escala**: 12 / 14 / 16 / 20 / 24 / 32 (em px)
- **Pesos**: 400 (texto), 500 (UI), 600 (títulos), 700 (laudo grande)

### Grid e espaçamentos

- Múltiplos de **4px** (`4, 8, 12, 16, 24, 32, 48, 64`)
- Padding padrão dos cards: `24px`
- Gap entre cards: `16px`
- Border-radius padrão: `8px` (botões), `12px` (cards)

### Componentes derivados

Todos viram funções utilitárias em `app/ui_kit.py`:

```python
def card(content, *, elevated: bool = False, padding: int = 24) -> ft.Container: ...
def botao_primario(label: str, on_click, *, icon: str | None = None) -> ft.ElevatedButton: ...
def botao_secundario(label: str, on_click) -> ft.OutlinedButton: ...
def status_badge(tipo: Literal["ok", "warn", "error", "info"], texto: str) -> ft.Container: ...
def laudo_grande(estado: Literal["corrigido", "ainda_quebrado", "inconclusivo"]) -> ft.Container: ...
def empty_state(icone: str, titulo: str, descricao: str, acao: Optional[ft.Control] = None) -> ft.Column: ...
def loading(mensagem: str) -> ft.Row: ...
```

### Estados visuais

- **Empty state** em cada aba (quando o usuário ainda não fez nada): ícone grande + título amigável + CTA primário
- **Loading**: spinner + texto explicando o passo atual (não só "Carregando…")
- **Hover/Focus**: borda accent em botões e cards interativos
- **Disabled**: opacity 0.5, cursor not-allowed

### Acessibilidade

- Contraste mínimo AA (4.5:1) em texto normal
- Todos os botões com tooltip (visível em hover)
- Navegação por teclado: Tab funciona, atalhos pra abas (Ctrl+1..5)
- Tamanho mínimo de toque: 40×40px

### Tema escuro como default

O app inicia em tema escuro (Twygo Aprender costuma ser usado em sessões longas, escuro cansa menos). Botão na barra superior alterna pra claro. Preferência persiste em `state.json`.

---

## Etapa 9 — Agente QA especializado (`app/agents/qa_agent.py`)

- [ ] Classe `QAAgent(documentacao, caso, evidencias, credenciais, on_log, headless)`
- [ ] **System prompt cacheado** (cache_control=ephemeral, ttl 5 min):
  ```
  Você é um QA Engineer especialista na plataforma Twygo (Aprender e Admin).
  Sua tarefa: dado um retrabalho (descrição + evidência visual + documentação do
  projeto), reproduzir os passos no stage e emitir laudo objetivo sobre se o bug
  foi corrigido.

  REGRAS DE BASE:
  - Sempre executa um passo de cada vez. Espera a página estabilizar.
  - Após cada passo, tira screenshot e compara com o esperado.
  - Ao chegar ao "comportamento esperado", compara visualmente o estado atual
    com a evidência do bug original.
  - Usa a documentação do projeto como fonte da verdade sobre regras de negócio.
  - Emite laudo: CORRIGIDO / AINDA_QUEBRADO / INCONCLUSIVO.
  - Se INCONCLUSIVO, explica o porquê.
  - NUNCA inventa resultado positivo. Em dúvida → INCONCLUSIVO.

  Ferramentas: playwright_click, playwright_fill, playwright_screenshot,
  playwright_navigate, compare_with_evidence.
  ```
- [ ] **Bloco cacheado #2** (ttl 1h): a documentação do projeto inteira (regras, discovery, usabilidade)
- [ ] **Bloco não-cacheado**: caso específico + evidências + estado atual da página
- [ ] Loop de execução: pra cada passo, chama Claude, executa tool calls, registra resultado
- [ ] Devolve `ResultadoExecucao` com `laudo`, `justificativa`, `screenshots_por_passo`, `usage_total`

**Model:** `claude-opus-4-7`. **Visão:** evidências e screenshots como `image` blocks.

> **Economia esperada:** cache da documentação reduz custo em ~90% nas execuções consecutivas do mesmo projeto.

---

## Etapa 10 — Testes mínimos

- [ ] `tests/app/test_jam_fetcher.py`:
  - extrai ID de URL `https://jam.dev/c/abc123`
  - mock httpx: og:image válido → baixa
  - mock httpx: og:video → retorna `"video"`
  - mock httpx: 404 → `None`
- [ ] `tests/app/test_kqa_comment.py`:
  - gera comentário com todos os campos
  - omite "Obs" quando vazio
  - inclui link do commit
- [ ] `tests/app/test_doc_loader.py`:
  - lê `.md` corretamente
  - lê `.pdf` (com PDF de fixture pequeno)
  - rejeita extensão desconhecida
  - estima tokens (aproximado)
- [ ] `tests/app/test_state.py`:
  - observer pattern: subscrever, mudar estado, callback chamado
  - persistência: salvar/carregar `state.json`
- [ ] Rodar `pytest tests/app/ -v` → todos verdes

---

## Etapa 11 — Build e empacotamento

- [ ] `flet build windows`
  - Gera `build/windows/twygo-qa-app.exe`
- [ ] Testar: duplo-clique em pasta limpa
- [ ] Se Flet build falhar: `pyinstaller --onefile --windowed app/main.py`
- [ ] Adicionar `build/` ao `.gitignore`

**Tamanho esperado:** 80-120 MB (Python + Chromium do Playwright).

---

## Etapa 12 — Verificação manual

- [ ] Abrir o .exe → janela com 5 abas aparece
- [ ] Aba Documentação: selecionar projeto "modelos", anexar 1-2 docs de regras de negócio
- [ ] Aba Caso: colar o retrabalho dos cards de Design → parseia certo
- [ ] Aba Evidências: colar print do Win+Shift+S → miniatura aparece
- [ ] Aba Evidências: incluir URL jam.dev no caso → tenta baixar
- [ ] Aba Execução: ver resumo do contexto (📚 N docs, 📋 caso, 🖼️ evidências), clicar Executar
- [ ] Playwright abre Chrome, loga, reproduz os passos
- [ ] Aba Resultado: laudo aparece, comentário KQA gerado
- [ ] Clicar "Commitar" → commit em `git log`, evidências em `evidencias/T-XXXX/`
- [ ] Copiar comentário KQA → cola no Artia com link do commit

**Critério de pronto:** todos os itens marcados, sem mexer no código no meio.

---

## Etapa 13 — Stretch (depois do MVP)

- [ ] Pausar/retomar execução
- [ ] Histórico das últimas execuções (filtro por T-XXXX)
- [ ] Modo "regressão": rodar todos os pytest e mostrar dashboard
- [ ] Suporte a vídeo Jam: extrair frames e analisar (3-5 frames distribuídos no tempo)
- [ ] Atualização automática do .exe quando der push no repo
- [ ] Compartilhar documentação entre projetos (ex: regras gerais Twygo vs específicas de Modelos)

> Stretch fica pra outra conversa. Princípio YAGNI.
