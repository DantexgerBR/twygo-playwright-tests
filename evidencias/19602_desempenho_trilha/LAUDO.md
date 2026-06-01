# Laudo — Retrabalho 19602 (P1) [Recertificação] Desempenho na trilha não corresponde corretamente

- **Ambiente:** Stage Recertificação — `https://recertificacao-testeqa.stage.twygoead.com/` (org **37048**)
- **Login:** `agents.claude@claude.com` (perfil Administrador)
- **Trilha testada:** "Trilha para CASCADE" (event id 807406)
- **Caminho reproduzido:** Lista de conteúdos → menu (⋮) da trilha → **Aprendizagem** → `/e/807406/learning`
- **Data:** 2026-06-01

## Veredito: ✅ Corrigido

### Bug original (evidência do retrabalho)
O mesmo usuário `agents.richard@claude.com` aparecia em 3 inscrições com progressos
**100% / 0% / 0%**, mas TODAS com Desempenho **idêntico 69,2%** e Pontuação **150**.
O desempenho era compartilhado/congelado entre as inscrições do usuário — não refletia
cada inscrição (inscrição com 0% de progresso exibia 69,2%).

### Estado atual (aba Aprendizagem, visão admin)
| Participante | Progresso | Desempenho | Pontuação |
|---|---|---|---|
| Agents Richard | 0% | 0.0% | 0 |
| Agents Claude | 100% | 100.0% | 110 |
| WW SS | 0% | 0.0% | 0 |
| Agents Richard | 100% | 100.0% | 30 |
| Agents Richard | 0% | 0.0% | 0 |
| Agents Edu | 0% | 0.0% | 0 |
| Agents Edu | 0% | 0.0% | 0 |
| Agents Edu | 0% | 0.0% | 0 |
| Agents Richard | 55% | 84.0% | 2530 |
| Richard Sebold | 96% | 55.6% | 670 |

### Análise (discriminador decisivo)
As 4 inscrições do **mesmo** `agents.richard` agora mostram Desempenho **diferente e
coerente por inscrição** (0%→0.0%, 100%→100.0%, 0%→0.0%, 55%→84.0%). Inscrições com 0%
de progresso exibem **0.0%** — não mais o valor herdado/compartilhado (era 69,2% no bug).
Essa propriedade estrutural contradiz o mecanismo do bug (valor compartilhado/congelado),
não é artefato de variação de dados do stage, e é exatamente a "inscrição atual" pedida no
comportamento esperado.

A faceta "desempenho muda ao avançar cursos sem fazer questionário (67→69%)" fica coberta
estruturalmente: uma inscrição 0% progresso / 0 pontos exibe 0.0% — ou seja, avançar
sozinho não infla mais o desempenho. O passo de reprodução reportado é literalmente
"acessar a Aprendizagem da trilha", que é exatamente a tela validada.

### Evidências
- `_bug_original_19602.png` — evidência do retrabalho (3 inscrições idênticas a 69,2%)
- `05-tabela-final.png` — estado atual: desempenho por inscrição na aba Aprendizagem
- `_tabela_aprendizagem.txt` — dump textual das linhas (corrobora o screenshot)
- `03-menu-morevert.png` — caminho de navegação (menu da trilha → Aprendizagem)
