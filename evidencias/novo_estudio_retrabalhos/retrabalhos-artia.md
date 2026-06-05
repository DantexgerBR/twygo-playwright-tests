# Retrabalhos — Novo Estúdio de Criação (QA 1.1 a 1.6 · 05/06/2026)

> Copiar e colar cada bloco no Artia. Evidências com link do GitHub logo abaixo de cada bloco.
> Base das evidências: https://github.com/DantexgerBR/twygo-playwright-tests/tree/main/evidencias/novo_estudio_retrabalhos

---

## R1 — Cards Trilha/Pacote abrem o formulário de CURSO (card 19705)

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

## R2 — Card "Curso" não direciona ao Estúdio de Criação (card 19705)

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

## R3 — "Criar curso com IA" bloqueado mesmo com IA ativa e saldo (card 19705)

```
:: Incidente identificado ::
Botão "Criar curso com IA" exibe o toast "Essa funcionalidade não foi habilitada para esse ambiente" mesmo com Controle de IA ativo e saldo de créditos — o assistente de 4 passos não abre (o clique não dispara nenhuma requisição ao servidor)

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador e conferir em Configurações » Controle de IA » aba Configurações: ambiente principal "novoestudio" com "Acesso de IA ativo" LIGADO
» Passo 2: Conferir na aba Extrato: saldo de créditos disponível (renovação mensal +1, saldo final 1)
» Passo 3: Acessar Aprendizagem » Conteúdos
» Passo 4: Clicar no botão "Criar curso com IA"
» Passo 5: Observar o toast "Essa funcionalidade não foi habilitada para esse ambiente. Ative ou consulte o responsável..." — o assistente não abre

    :: Comportamento esperado ::
Com "Acesso de IA ativo" ligado e saldo disponível, o clique abre o assistente de criação de curso com IA (4 passos). Detalhe técnico: o clique não dispara nenhuma request — o bloqueio é uma checagem no front-end que não está respeitando a configuração ativa.

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

## R4 — Sem layout mobile abaixo de 1366px (card 19706)

```
:: Incidente identificado ::
Em resolução menor que 1366x720 o Estúdio mantém o layout desktop espremido com scroll horizontal — não aplica o layout mobile/tablet com 3 tabs no rodapé

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador e abrir o curso 807533 (Conteúdos » menu ⋮ » Editar)
» Passo 2: Clicar na aba "Atividades" (Estúdio de Criação)
» Passo 3: Redimensionar a janela para 1024x600 (ou usar o modo responsivo do DevTools — F12 + Ctrl+Shift+M)
» Passo 4: Observar: aparece scroll horizontal na página e nenhuma tab de navegação no rodapé

    :: Comportamento esperado ::
Abaixo de 1366px o Estúdio aplica o layout mobile/tablet com 3 tabs no rodapé (lista, preview, copiloto), sem scroll horizontal.

    :: Informações ::
url: https://novoestudio.stage.twygoead.com/o/37061/contents/807533/edit?tab=studio
login: agents.qa@claude.com
senha: 123456
org_id: 37061

    :: Evidência(s) ::
- Estúdio em 1024x600 com layout desktop e scroll: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r04-mobile-1024x600-scroll-horizontal.png
```

---

## R5 — Sem controles de colapsar/ocultar o menu lateral (card 19706)

```
:: Incidente identificado ::
Não existem os botões de recolher o menu lateral principal para ícones nem de ocultá-lo inteiramente dentro do Estúdio de Criação

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador e abrir o Estúdio do curso 807533 (Editar » aba Atividades)
» Passo 2: Procurar no menu lateral principal (Dashboard, Aprendizagem, Usuários...) qualquer controle de colapsar ou ocultar
» Passo 3: Observar: nenhum botão de colapso/ocultar existe

    :: Comportamento esperado ::
RN 2 prevê menu lateral colapsável para ícones E opção de ocultar inteiramente, liberando espaço horizontal para o Estúdio.

    :: Informações ::
url: https://novoestudio.stage.twygoead.com/o/37061/contents/807533/edit?tab=studio
login: agents.qa@claude.com
senha: 123456
org_id: 37061

    :: Evidência(s) ::
- Estúdio aberto sem controles no menu lateral: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r05-estudio-sem-controles-menu-lateral.png
```

---

## R6 — Reordenação e persistência de abas não existem (card 19707)

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
- Retorno ao curso abrindo em Identificação (last-tab não restaurada): https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r06-retorno-abre-identificacao.png
```

---

## R7 — Sem section "Configurações de IA" com tooltip na Identificação (card 19708)

```
:: Incidente identificado ::
A aba Identificação não tem a section "Configurações de IA" com tooltip explicativo — os campos usados pela IA (Público alvo, Idade, Dificuldade, Tom de voz) estão na section "Público", sem indicação de uso por IA

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador e abrir o curso 807533 na aba Identificação
» Passo 2: Observar as sections existentes: Dados básicos, Público, Acesso e visibilidade, Conteúdo, Notificações, Chat
» Passo 3: Procurar a section "Configurações de IA" e o ícone de informação com o tooltip "Estes campos são usados pela IA na geração de conteúdo. Quanto mais preenchidos, melhor o resultado." → não existem

    :: Comportamento esperado ::
RN 4 prevê sections "Básico", "Caracterização" e "Configurações de IA", com os campos de IA agrupados na section de IA com tooltip explicativo.

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

## R8 — Copiloto não aparece na aba Identificação (card 19708)

```
:: Incidente identificado ::
O botão flutuante do copiloto não renderiza na aba Identificação — só existe dentro da aba Atividades (Estúdio), impedindo o fluxo de sugestão de descrição via IA

    :: Passo a passo para reprodução ::
» Passo 1: Logar como administrador e abrir o curso 807533 na aba Identificação
» Passo 2: Procurar o botão flutuante roxo do copiloto → não existe nesta aba
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

## R9 — Lista do Estúdio não reflete o nome customizado do tipo (card 19710)

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
A lista de atividades do Estúdio (visão do instrutor) exibe o display_label customizado no lugar do nome default do tipo, conforme RN 6.

    :: Informações ::
url: https://novoestudio.stage.twygoead.com/o/37061/studio/activities/9288190/edit?type=pdf&eventId=807533
login: agents.qa@claude.com
senha: 123456
org_id: 37061

    :: Evidência(s) ::
- Lista exibindo "PDF Estampado" com "Aula Customizada" salvo no form: https://github.com/DantexgerBR/twygo-playwright-tests/blob/main/evidencias/novo_estudio_retrabalhos/r09-lista-nao-reflete-display-label.png
```

---

## R10 — Botão "Editar" do preview nunca habilita (card 19710)

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

## R11 — Escolher um tipo no "Adicionar" já cria a atividade (card 19710)

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

## Menores/UX (avaliar se viram retrabalho)

1. **Salvar silencioso na Identificação**: com "Tipo de experiência" (obrigatório) vazio, o Salvar falha sem nenhum toast de erro global — o usuário acha que salvou.
2. **Sem toast no save do form de atividade** do Estúdio (salva, mas sem feedback visual).
3. **SCORM com nome default "Conteúdo"** ao criar atividade (esperado: "SCORM"/"Conteúdo SCORM" pro instrutor).

## Confirmar com o solicitante antes de abrir (possível AT desatualizada)

- Copiloto: fechado por padrão via botão flutuante, abre ~70% sobreposto, sem botão "Expandir" (AT: coluna ~30% expansível a ~50%).
- Rota dedicada `/events/:id/edit/studio` retorna 404 (rota real: `?tab=studio`) e `<title>` da aba é genérico ("Domínio padrão").
- Aba "Certificado" não existe (nem no produto atual).
- "Dificuldade" é campo de texto livre (AT: dropdown); campo "Idioma" não existe.
- Rótulo do menu ⋮ é "Editar" (AT: "Editar curso"); "Gerenciar curso" não existe em lugar nenhum.
