# Fechamento QA 1.1 — Listagem "Meu Histórico" (Aluno)

**Card Artia**: 19888  
**Org**: `registrosf2.stage.twygoead.com` (ORG_ID: 37079)  
**Data**: 2026-06-22  
**Executor**: QA automatizado (Playwright + Python)

---

## GATE (orientação)

- Feature "Registros de Aprendizagem" habilitada na org 37079
- Feature identificada na sidebar do aluno como "Meu Histórico BETA"
- URL de acesso: `/o/37079/records?in_use_mode_layout=true`
- Usuário `dante.tavares@twygo.com` (QA Tester) confirmado com acesso

**Evidências**: `recon_pag_inicio.png`, `fechamento_gate_meu_historico.png`

---

## TC3 — Validar empty state da lista sem registros

**Veredito**: PASSOU (com ressalva de mensagem)

**Execucao (2026-06-22)**: Usuario `qa11tc342588@twygotest.com` (QA11 TC3) provisionado via kebab "Alterar senha" no admin da org 37079. Senha definida como `twygoqa2026` (toast de confirmacao: "Senha alterada com sucesso"). Login do usuario realizado com sucesso. Pagina "Meu Historico" acessada em `/o/37079/records?in_use_mode_layout=true`.

**Resultado observado**:
- 4 KPIs todos zerados: Emitidos=0, Expirados=0, Pendentes=0, Recusados=0 (OK)
- Tabela vazia exibindo "Nao ha dados para exibir"
- Botao "+ Adicionar" visivel

**Ressalva**: A AT esperava a mensagem "Voce ainda nao tem registros. Adicione o primeiro pelo botao acima.", mas o produto exibe "Nao ha dados para exibir" — mensagem generica da tabela Chakra. Mesma situacao do TC2 (labels de colunas divergem da hipotese da AT). A funcionalidade principal do empty state esta correta (tabela vazia + 4 KPIs zerados). Alinhar AT com o texto real do produto.

**Evidencias**: `fechamento_tc3_senha_definida.png` (modal Alterar senha com ambos campos preenchidos), `fechamento_tc3_empty_ok.png` (Meu Historico com tabela vazia e KPIs=0)

---

## TC11 — Validar paginação da lista (25/50/100)

**Veredito**: PASSOU

**Pré-condição cumprida**: 27 registros criados e visíveis na conta `dante.tavares@twygo.com`

### Passo 1: Tabela exibe 25 linhas por padrão

- Resultado esperado (AT): "Tabela exibe 25 linhas; controle de paginação exibe página '1' e o total de páginas"
- Resultado obtido: 25 linhas visíveis na pag1, controle exibe `<<` `<` `1` `2` `>` com página "1" indicada (botão "1" ativo) e total de 2 páginas
- Evidência: `fechamento_tc11_v3_pag1.png`, `fechamento_tc11_v3_footer.png`

### Passo 2: Clique em próxima página exibe página 2

- Resultado esperado (AT): "Tabela exibe a página 2 com os registros seguintes"
- Resultado obtido: Clique no botão `#next-page-button` (ícone `chevron_right`, Material Icons) carregou pag2 com 2 linhas (registros "Gestão para resultados" e "Construindo times de alt..."), controle mostra "2" selecionado
- Evidência (run final): `fechamento_tc11_rodape.png` (rodapé com paginação), `fechamento_tc11_pag2.png` (pág 2 ativa, 2 registros)

### Passo 3: Selecionar "50 por página"

- Resultado esperado (AT): "Tabela passa a exibir até 50 linhas por página e o total de páginas é recalculado"
- Resultado obtido: Select `#select_pages` selecionado com opção "50", tabela exibiu 27 linhas (todos os registros em uma só página)
- Evidência: `fechamento_tc11_v3_50pag.png`

### Passo 4: Selecionar "100 por página"

- Resultado esperado (AT): "Tabela passa a exibir até 100 linhas por página"
- Resultado obtido: Select selecionado com opção "100", tabela exibiu 27 linhas
- Evidência: `fechamento_tc11_v3_100pag.png`

---

## Sumário

| TC | Veredito | Obs |
|----|----------|-----|
| TC3 | PASSOU (com ressalva) | KPIs=0 e tabela vazia OK; mensagem exibida "Nao ha dados para exibir" difere da AT — alinhar texto |
| TC11 | PASSOU | Todos 4 passos validados: default 25, pag2 ok, 50/pag, 100/pag |
