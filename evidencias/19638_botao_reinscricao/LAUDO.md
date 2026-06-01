# Laudo — Retrabalho 19638 (P1) [Recertificação] Botão "Iniciar reinscrição" não aparece em todos participantes

- **Ambiente:** Stage — `https://eduapi.stage.twygoead.com/` (org **36912**, "EDU API")
- **Login:** `eduardo.schmidt@twygo.com` (Administrador)
- **Conteúdo de teste:** "Gestão para resultados" (id **798476**) — único conteúdo da org com **"Habilitar reinscrição" ON** (varri os 25; o switch existe em todos → flag `recertification` actored na 36912)
- **Caminho:** Lista de conteúdos → menu (⋮) da trilha/curso → Aprendizagem (`/e/798476/learning`) → kebab (⋮) de cada participante
- **Data:** 2026-06-01

## Veredito: ✅ Corrigido

### Bug original
O item "Iniciar reinscrição" não aparecia para todos os participantes da lista de Aprendizagem
(só para alguns), faltando para quem deveria poder reinscrever.

### Comportamento esperado (card)
- Deve exibir o botão para todos.
- Quando não deve permitir reinscrição, o botão fica **bloqueado** e ao **hover** apresenta
  **tooltip com o motivo**.

### Estado atual — lista "Gestão para resultados" (6 participantes)
| Participante | Progresso | Aprovação | Situação | Item "Iniciar reinscrição" | Observação |
|---|---|---|---|---|---|
| Edu API (eduardo) | 100% | Aprovado | Emitido | presente, **HABILITADO** (ícone azul) | **observado** |
| Danilo | 92% | — | Pendente | presente, **BLOQUEADO** (ícone cinza) + tooltip | **observado** |
| Julia | 100% | Aprovado | Emitido | presente, habilitado | inferido (mesmo estado do Edu) |
| Vanessa | 100% | Aprovado | Emitido | presente, habilitado | inferido (mesmo estado do Edu) |
| Carla | 100% | Aprovado | Emitido | presente, habilitado | inferido (mesmo estado do Edu) |
| Gabriel | 92% | — | Pendente | presente, bloqueado | inferido (mesmo estado do Danilo) |

O item (ícone `replay`, `data-index=7`) está no DOM no kebab de **todos os 6** participantes
(confirmado lendo o menu realmente aberto — o Chakra mantém os 6 menus montados; filtrei por
`visibility:visible`+`opacity:1`).

### Par de contraste — DIRETAMENTE OBSERVADO (prova das 2 cláusulas)
Discriminador objetivo = **cor do ícone do item**, lida do menu aberto correto:
- **Elegível (Edu, 100%+aprovado):** "Iniciar reinscrição" presente e **HABILITADO** —
  ícone **azul `rgb(27,47,186)`**, mesma cor/peso dos demais itens do menu, **sem tooltip de bloqueio**.
  → evidência `06-edu-ELEGIVEL-menu.png`.
- **Não-elegível (Danilo, 92% pendente):** "Iniciar reinscrição" presente porém **BLOQUEADO** —
  ícone **cinza `rgb(163,163,163)`** (contrasta com os itens escuros do mesmo menu), e ao hover
  exibe **tooltip com o motivo**:
  > "A reinscrição só é permitida quando o participante atingiu 100% de progresso, foi aprovado ou teve a inscrição expirada."

  → evidências `06-danilo-NAOELEG-menu.png` (bloqueado) e `04-danilo-NAOELEG-hover-tooltip.png` (tooltip).

### Conclusão
O botão "Iniciar reinscrição" agora **aparece para todos os participantes** da lista de Aprendizagem,
**habilitado** para quem cumpre o critério (100% / aprovado / expirado) e **bloqueado com tooltip
explicativo** para quem não cumpre. Bug corrigido e comportamento esperado (ambas as cláusulas) atendido.

### Evidências
- `01-acesso-switch-reinscricao.png` — switch "Habilitar reinscrição" ON no conteúdo 798476
- `02-lista-aprendizagem.png` — lista de participantes (estados variados)
- `06-edu-ELEGIVEL-menu.png` — elegível: "Iniciar reinscrição" HABILITADO (ícone azul)
- `06-danilo-NAOELEG-menu.png` — não-elegível: "Iniciar reinscrição" BLOQUEADO (ícone cinza)
- `04-danilo-NAOELEG-hover-tooltip.png` — não-elegível: tooltip com o motivo no hover
- `05-danilo-NAOELEG-item.png` — recorte do item bloqueado (cinza)
- `_scan_switches.json` — varredura: só o 798476 tem reinscrição ON (switch existe nos 25)
- `_relatorio_kebabs.json` — dump dos 6 kebabs
