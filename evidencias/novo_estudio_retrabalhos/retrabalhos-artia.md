# ✅ CHECKLIST — Retrabalhos PENDENTES de criar no Artia (Novo Estúdio)

> **11 retrabalhos pra criar**, em ordem por card. Cada bloco está pronto: copiar → colar no Artia → marcar o checkbox.
> Já criados antes: mobile <1366 (33030233) e menu lateral (33030219) — não estão nesta lista.

- [ ] 1. [19705] Cards Trilha/Pacote abrem form de CURSO
- [ ] 2. [19705] Card Curso não vai pro Estúdio
- [ ] 3. [19705] "Criar curso com IA" bloqueado com IA ativa
- [ ] 4. [19706] Copiloto: abrir em 50% + botão expandir a 100%
- [ ] 5. [19706] Rota dedicada do Estúdio (404)
- [ ] 6. [19707] RN 3 ausente (drag de abas + persistência + última aba)
- [ ] 7. [19708] Sem section "Configurações de IA" com tooltip
- [ ] 8. [19708] Copiloto não aparece na aba Identificação
- [ ] 9. [19710] Lista do Estúdio não usa o nome customizado
- [ ] 10. [19710] Botão "Editar" do preview nunca habilita
- [ ] 11. [19710] Escolher tipo já cria a atividade (rascunho órfão)

Login de todos: `agents.qa@claude.com` / `123456` · org 37061

---

## 1. [19705] Cards Trilha/Pacote abrem o formulário de CURSO

```
:: Incidente identificado ::
Na página de seleção "O que você quer criar?", os cards "Trilha" e "Pacote" abrem o formulário de criação de CURSO ("Novo curso") em vez dos fluxos de Trilha e Pacote

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador na organização
» Passo 2: Acessar Aprendizagem » Conteúdos
» Passo 3: Clicar no botão "+ Adicionar" (abre a página "O que você quer criar?" com os 3 cards)
» Passo 4: Clicar no card "Trilha"
» Passo 5: Observar a página aberta: URL /o/37061/contents/new?kind=learning_path exibindo o formulário "Novo curso" (breadcrumb "Conteúdos > Adicionar curso")
» Passo 6: Voltar e repetir com o card "Pacote": URL /o/37061/contents/new?kind=package, mesmo formulário "Novo curso"

    :: Comportamento esperado ::
O card "Trilha" deve seguir o fluxo atual de criação de Trilha (formulário "Nova trilha", aberto hoje via kind=3) e o card "Pacote" o fluxo atual de Pacote (formulário "Novo pacote", kind=4). Causa provável: os cards enviam o parâmetro kind como texto (learning_path/package), que o backend não reconhece e cai no padrão Curso (kinds numéricos: 0=curso, 3=trilha, 4=pacote). Impacto: o usuário cria um CURSO achando que está criando Trilha/Pacote.

    :: Informações ::
url: https://novoestudio.stage.twygoead.com/o/37061/studio
login: agents.qa@claude.com
senha: 123456
org_id: 37061

    :: Evidência(s) ::
- Card Trilha abrindo "Novo curso": https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r01-card-trilha-abre-novo-curso.png
- Card Pacote abrindo "Novo curso": https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r01-card-pacote-abre-novo-curso.png
- Fluxo atual (org 36675) "Nova trilha" via kind=3: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_baseline_trilha_pacote/07-destino-trilha.png
- Fluxo atual (org 36675) "Novo pacote" via kind=4: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_baseline_trilha_pacote/08-destino-pacote.png
```

---

## 2. [19705] Card "Curso" não direciona ao Estúdio de Criação

```
:: Incidente identificado ::
Na página "O que você quer criar?", o card "Curso" abre o formulário legado de criação e, mesmo após salvar, direciona para a aba Identificação — o Estúdio de Criação não aparece em nenhum momento do fluxo

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador na organização
» Passo 2: Acessar Aprendizagem » Conteúdos e clicar no botão "+ Adicionar"
» Passo 3: Na página "O que você quer criar?", clicar no card "Curso"
» Passo 4: Observar: abre o formulário legado "Novo curso" (/o/37061/contents/new?kind=course), e não o Estúdio
» Passo 5: Preencher Nome, Tipo de experiência e Descrição e clicar em "Salvar"
» Passo 6: Observar o destino final: /o/37061/contents/{id}/edit na aba Identificação — sem redirect ao Estúdio de Criação

    :: Comportamento esperado ::
Selecionar o card "Curso" direciona para o Estúdio de Criação (tela única de atividades, aba "Atividades"/?tab=studio) com o curso vazio, conforme a RN do projeto.

    :: Informações ::
url: https://novoestudio.stage.twygoead.com/o/37061/studio
login: agents.qa@claude.com
senha: 123456
org_id: 37061

    :: Evidência(s) ::
- Card Curso abrindo o form legado: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r02-card-curso-form-legado.png
- Destino após salvar (aba Identificação, sem Estúdio): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r02-destino-pos-salvar-identificacao.png
```

---

## 3. [19705] "Criar curso com IA" bloqueado mesmo com IA ativa e saldo

```
:: Incidente identificado ::
Botão "Criar curso com IA" exibe o toast "Essa funcionalidade não foi habilitada para esse ambiente" mesmo com Controle de IA ativo e saldo de créditos — o assistente de 4 passos não abre (o clique não dispara nenhuma requisição ao servidor)

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador e conferir em Configurações » Controle de IA » aba Configurações: ambiente principal "novoestudio" com "Acesso de IA ativo" LIGADO
» Passo 2: Conferir na aba Extrato: saldo de créditos disponível
» Passo 3: Acessar Aprendizagem » Conteúdos
» Passo 4: Clicar no botão "Criar curso com IA"
» Passo 5: Observar o toast "Essa funcionalidade não foi habilitada para esse ambiente. Ative ou consulte o responsável..." — o assistente não abre

    :: Comportamento esperado ::
Com "Acesso de IA ativo" ligado e saldo disponível, o clique abre o assistente de criação de curso com IA (4 passos). Detalhe técnico: o clique não dispara nenhuma request — o bloqueio é uma checagem no front-end que não respeita a configuração ativa.

    :: Informações ::
url: https://novoestudio.stage.twygoead.com/o/37061/events?tab=events&profile=admin
login: agents.qa@claude.com
senha: 123456
org_id: 37061

    :: Evidência(s) ::
- Controle de IA com "Acesso de IA ativo" LIGADO: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r03-controle-ia-acesso-ativo.png
- Extrato com saldo de créditos: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r03-extrato-com-saldo.png
- Toast de bloqueio ao clicar: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r03-toast-bloqueio-ao-clicar.png
```

---

## 4. [19706] Drawer do copiloto fora do padrão: deve abrir em 50% com expandir até 100%

```
:: Incidente identificado ::
O drawer do copiloto no Estúdio abre ocupando ~66% da largura da tela, de forma fixa e sem botão de expandir — o padrão definido é abrir em 50% com botão para expandir até 100%

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador e abrir o Estúdio do curso 807533 (Editar » aba Atividades)
» Passo 2: Clicar no botão flutuante do copiloto (canto da tela)
» Passo 3: Observar a largura do drawer aberto: ~66% da tela (896px em viewport 1366), sobreposto ao conteúdo
» Passo 4: Procurar um botão de expandir no drawer → não existe (só o X de fechar e a lista de conversas)

    :: Comportamento esperado ::
Drawer do copiloto abre ocupando 50% da largura por padrão, com botão para expandir até 100% (comportamento confirmado com o time de desenvolvimento em 05/06).

    :: Informações ::
url: https://novoestudio.stage.twygoead.com/o/37061/contents/807533/edit?tab=studio
login: agents.qa@claude.com
senha: 123456
org_id: 37061

    :: Evidência(s) ::
- Drawer aberto em ~66% sem botão de expandir: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_recon/qa12-09-copiloto-aberto.png
```

---

## 5. [19706] Rota dedicada do Estúdio retorna 404

```
:: Incidente identificado ::
A rota dedicada do Estúdio prevista na documentação (/o/{org}/events/:id/edit/studio) retorna 404 — o Estúdio só abre pela rota /o/{org}/contents/{id}/edit?tab=studio

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador na organização
» Passo 2: Acessar a URL https://novoestudio.stage.twygoead.com/o/37061/events/807533/edit/studio
» Passo 3: Observar a página 404 ("The page you were looking for doesn't exist")
» Passo 4: Acessar https://novoestudio.stage.twygoead.com/o/37061/contents/807533/edit?tab=studio → o Estúdio abre normalmente

    :: Comportamento esperado ::
A rota deve seguir a documentação (/o/{org}/events/:id/edit/studio abrindo o Estúdio) — confirmado com o time de desenvolvimento em 05/06. Obs: o <title> da aba permanece genérico ("Domínio padrão"), mas é o padrão atual do admin — sem alteração por enquanto.

    :: Informações ::
url: https://novoestudio.stage.twygoead.com/o/37061/events/807533/edit/studio
login: agents.qa@claude.com
senha: 123456
org_id: 37061

    :: Evidência(s) ::
- Estúdio abrindo via ?tab=studio (rota da doc dá 404): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_recon/qa12-07-tab-studio-direto.png
```

---

## 6. [19707] Reordenação e persistência de abas não existem (RN 3)

```
:: Incidente identificado ::
RN 3 ausente: as abas do "Editar curso" não têm drag & drop (sem ícone no hover, arrastar não move e nada é persistido) e a última aba aberta não é restaurada ao reabrir o curso

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador e abrir o curso 807533 (Conteúdos » menu ⋮ » Editar)
» Passo 2: Passar o mouse sobre o título da aba "Modelo" → nenhum ícone de drag aparece
» Passo 3: Tentar arrastar a aba "Modelo" até a posição da aba "Banner" → a ordem não muda (e o DevTools/Network não registra nenhuma chamada de persistência)
» Passo 4: Clicar na aba "Banner", voltar para Conteúdos e abrir o curso novamente via "Editar"
» Passo 5: Observar: abre na aba "Identificação", não na última aba usada ("Banner")

    :: Comportamento esperado ::
Conforme RN 3: abas reordenáveis via drag & drop (com ícone no hover, exceto "Identificação" travada), ordem salva em banco POR USUÁRIO (user_course_preferences: tab_order/last_tab) e restauração da última aba aberta por usuário x curso. Observação: as RNs 2, 4 e 6 estão presentes e funcionais neste mesmo build/org — a ausência é específica da RN 3 (não parece problema de deploy/infra).

    :: Informações ::
url: https://novoestudio.stage.twygoead.com/o/37061/contents/807533/edit
login: agents.qa@claude.com
senha: 123456
org_id: 37061

    :: Evidência(s) ::
- Hover na aba "Modelo" sem ícone de drag: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r06-hover-modelo-sem-icone-drag.png
- Ordem inalterada após o drag: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r06-apos-drag-ordem-inalterada.png
- Retorno ao curso abrindo em Identificação: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r06-retorno-abre-identificacao.png
```

---

## 7. [19708] Sem section "Configurações de IA" com tooltip na Identificação

```
:: Incidente identificado ::
A aba Identificação não tem a section "Configurações de IA" com tooltip explicativo — os campos usados pela IA (Público alvo, Idade, Dificuldade, Tom de voz) estão na section "Público", sem indicação de uso por IA

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador e abrir o curso 807533 na aba Identificação
» Passo 2: Observar as sections existentes: Dados básicos, Público, Acesso e visibilidade, Conteúdo, Notificações, Chat
» Passo 3: Procurar a section "Configurações de IA" e o ícone de informação com o tooltip "Estes campos são usados pela IA na geração de conteúdo. Quanto mais preenchidos, melhor o resultado." → não existem

    :: Comportamento esperado ::
RN 4 prevê os campos de IA agrupados em section própria ("Configurações de IA") com tooltip explicativo do uso pela IA.

    :: Informações ::
url: https://novoestudio.stage.twygoead.com/o/37061/contents/807533/edit?tab=identification
login: agents.qa@claude.com
senha: 123456
org_id: 37061

    :: Evidência(s) ::
- Sections reais (topo do form): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r07-sections-reais-topo.png
- Campos de IA dentro da section "Público": https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r07-campos-ia-na-section-publico.png
```

---

## 8. [19708] Copiloto não aparece na aba Identificação

```
:: Incidente identificado ::
O botão flutuante do copiloto não renderiza na aba Identificação — só existe dentro da aba Atividades (Estúdio), impedindo o fluxo de sugestão de descrição via IA

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador e abrir o curso 807533 na aba Identificação
» Passo 2: Procurar o botão flutuante do copiloto → não existe nesta aba
» Passo 3: Clicar na aba "Atividades" → o botão do copiloto aparece

    :: Comportamento esperado ::
RN 4 prevê o copiloto acessível na Identificação em modo sugestão: responde no chat sem alterar os campos do formulário; o usuário copia e cola manualmente.

    :: Informações ::
url: https://novoestudio.stage.twygoead.com/o/37061/contents/807533/edit?tab=identification
login: agents.qa@claude.com
senha: 123456
org_id: 37061

    :: Evidência(s) ::
- Aba Identificação sem o botão do copiloto: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r08-identificacao-sem-copiloto.png
- Copiloto presente na aba Atividades (comparativo): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r08-copiloto-presente-na-aba-atividades.png
```

---

## 9. [19710] Lista do Estúdio não reflete o nome customizado do tipo

```
:: Incidente identificado ::
O nome customizado do tipo (display_label) salva e persiste no formulário da atividade, mas o card na lista de atividades do Estúdio continua exibindo o tipo original

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador e acessar o formulário da atividade "Material de apoio" pela URL: /o/37061/studio/activities/9288190/edit?type=pdf&eventId=807533
» Passo 2: Na seção de aparência, trocar o campo "Texto exibido para o aluno" de "PDF Estampado" para "Aula Customizada" e clicar em Salvar
» Passo 3: Recarregar o formulário e confirmar que "Aula Customizada" persistiu
» Passo 4: Abrir o Estúdio do curso (aba Atividades) e localizar o card da atividade 1.1
» Passo 5: Observar: o card ainda exibe "PDF Estampado" como tipo
» Passo 6 (restaurar): voltar o campo para "PDF Estampado" e salvar

    :: Comportamento esperado ::
A lista de atividades do Estúdio (visão do instrutor) exibe o display_label customizado no lugar do nome default do tipo, conforme RN 6. IMPORTANTE pro dev: o dado persiste corretamente e o PLAY DO ALUNO já consome e exibe "Aula Customizada" (validado em 05/06 com aluno inscrito) — o gap é exclusivamente a renderização da lista do Estúdio.

    :: Informações ::
url: https://novoestudio.stage.twygoead.com/o/37061/studio/activities/9288190/edit?type=pdf&eventId=807533
login: agents.qa@claude.com
senha: 123456
org_id: 37061

    :: Evidência(s) ::
- Lista exibindo "PDF Estampado" com "Aula Customizada" salvo no form: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r09-lista-nao-reflete-display-label.png
- Play do ALUNO exibindo "Aula Customizada" corretamente (contraste): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r09-play-aluno-exibe-display-label.png
```

---

## 10. [19710] Botão "Editar" do preview nunca habilita

```
:: Incidente identificado ::
No Estúdio, o botão "Editar" da área de preview permanece desabilitado mesmo com atividade selecionada — não há caminho pela interface para abrir o formulário de edição de uma atividade existente

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador e abrir o Estúdio do curso 807533 (aba Atividades)
» Passo 2: Clicar em qualquer atividade da lista (testado com atividade pai "Conteúdo 1" e sub-atividade "Material de apoio")
» Passo 3: Observar os botões no topo do preview: "Editar" continua desabilitado (cinza)
» Observação: o formulário existe e funciona acessando a URL direta /o/37061/studio/activities/{id}/edit?type={tipo}&eventId=807533

    :: Comportamento esperado ::
Selecionar uma atividade habilita o botão "Editar", abrindo o formulário de cadastro/edição da atividade (onde ficam os campos de nome customizado e ícone da RN 6).

    :: Informações ::
url: https://novoestudio.stage.twygoead.com/o/37061/contents/807533/edit?tab=studio
login: agents.qa@claude.com
senha: 123456
org_id: 37061

    :: Evidência(s) ::
- Atividade pai selecionada, "Editar" desabilitado: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r10-editar-desabilitado-atividade-pai.png
- Sub-atividade selecionada, "Editar" desabilitado: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r10-editar-desabilitado-atividade-folha.png
```

---

## 11. [19710] Escolher um tipo no "Adicionar" já cria a atividade (rascunho órfão)

```
:: Incidente identificado ::
Ao clicar em "Adicionar" na lista de atividades do Estúdio e escolher um tipo, a atividade É CRIADA imediatamente — se o usuário desistir sem salvar, fica um rascunho órfão na lista do curso

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador e abrir o Estúdio do curso 807533 (anotar o total da lista: "Atividades (12)")
» Passo 2: Clicar em "Adicionar" e escolher um tipo (ex: "Vídeo upload")
» Passo 3: Observar a URL do formulário: /o/37061/studio/activities/{novoId}/edit — a atividade já tem ID (foi criada no banco)
» Passo 4: Sair sem salvar (voltar para o Estúdio)
» Passo 5: Observar a lista: "Atividades (13)" — o rascunho ficou no curso
» Passo 6 (limpar): selecionar o rascunho na lista e excluir

    :: Comportamento esperado ::
A atividade só deve ser criada ao clicar em Salvar (ou o rascunho deve ser descartado automaticamente ao sair sem salvar).

    :: Informações ::
url: https://novoestudio.stage.twygoead.com/o/37061/contents/807533/edit?tab=studio
login: agents.qa@claude.com
senha: 123456
org_id: 37061

    :: Evidência(s) ::
- Seleção de tipos ("Adicionar conteúdo"): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r11-type-selector.png
- Formulário já com ID de atividade criada na URL: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r11-atividade-ja-criada-url-com-id.png
```

---

## (referência) Fora desta lista — nada a criar

- **Já criados**: mobile <1366 → [33030233](https://app2.artia.com/a/4874953/f/6386039/activities/33030233) · menu lateral → [33030219](https://app2.artia.com/a/4874953/f/6386039/activities/33030219)
- **Bug da DOC (corrigir análise de teste, não é retrabalho)**: aba "Certificado"; "Dificuldade" texto livre; campo "Idioma"
- **Stand-by pós-CBTD**: rótulo do SCORM ("Conteúdo SCORM" x "Conteúdo")
- **Menores/UX (avaliar depois)**: Salvar silencioso com "Tipo de experiência" vazio; sem toast no save do form de atividade
