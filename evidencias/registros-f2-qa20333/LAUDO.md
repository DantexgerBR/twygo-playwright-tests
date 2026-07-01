# Laudo — Retrabalho Artia 20333 (P3)

**Card**: [Registros F2] Menu de ações (kebab) — "Visualizar" não abre via teclado
**PR de correção**: https://github.com/Twygo/twyg-app/pull/10833 (componente compartilhado `list-control`)
**Ambiente**: Stage `https://registrosf2.stage.twygoead.com/` — org 37079
**Data**: 2026-07-01

## Causa raiz reportada
No HTML, o botão "Visualizar" tinha `tabIndex="-1"` (classe `css-whmuo1`)
enquanto os demais itens do menu tinham `tabIndex="0"` (classe `css-ncfona`),
impedindo foco/ativação via teclado especificamente nesse item.

## O que foi testado
Script: `scripts/run_t20333_visualizar_teclado.py`
Evidências: `evidencias/registros-f2-qa20333/*.png` + `resultados.json`

Para os perfis **Admin** e **Aluno** (login `REGISTROSF2_ADMIN_*` e
`REGISTROSF2_TC3_*`), na tela de Registros:

1. Abertura do kebab (click) de uma linha.
2. Navegação **por seta (ArrowDown) + Enter** até "Visualizar" — cenário
   exato reportado no bug — com leitura de `document.activeElement` a cada
   passo, garantindo que o Enter foi disparado sobre o item correto (não
   outro item do menu).
3. Navegação por **Tab nativo** até "Visualizar" — teste complementar
   /informativo. Observação: o menu segue o padrão ARIA `role=menu`
   (roving tabindex), cuja navegação é feita por SETAS — Tab tende a ficar
   preso no item já focado (Chakra intercepta), tanto no Visualizar quanto
   no controle. Isso é comportamento da biblioteca, não é o cenário
   reportado no card ("setas + Enter") e não afeta o veredito.
4. **Controle**: mesmo fluxo (seta + Enter) aplicado a "Evidências" — item
   presente nos dois menus/perfis testados — para provar que (a) o
   mecanismo de teclado do teste funciona e (b) outro item do MESMO menu
   segue funcionando (sem regressão).
5. Leitura do `tabIndex` real do botão "Visualizar" via DOM, como dado
   complementar de causa raiz (não como critério de veredito).

## Resultados

| Perfil | Item | Via seta+Enter | tabIndex após foco | Tela abriu? |
|---|---|---|---|---|
| Admin | Visualizar | Focou corretamente, Enter ativou | 0 (após foco; roving tabindex) | **Sim** — `/records/44279381/edit?mode=view`, form renderizado |
| Admin | Evidências (controle) | Focou corretamente, Enter ativou | 0 (após foco) | **Sim** — painel "Evidências do registro" abriu |
| Aluno | Visualizar | Focou corretamente, Enter ativou | 0 (após foco; roving tabindex) | **Sim** — `/records/44280004/edit?mode=view`, form renderizado |
| Aluno | Evidências (controle) | Focou corretamente, Enter ativou | 0 (após foco) | **Sim** — painel "Evidências do registro" abriu |

Nos dois perfis, o `activeElement` confirmou foco em "Visualizar"
(id/texto corretos) imediatamente antes do Enter — eliminando a
possibilidade de falso-positivo por Enter em item errado.

A tela de visualização abriu com o formulário completo renderizado
(campos Website, Pessoas, Provedor, Conteúdo, Descrição, Datas etc.), sem
erro nem tela em branco — mesma estrutura visual do form que antes só
abria via mouse.

## Comparação com evidência original do bug
- Bug original (`vf_a1_visualizar_02_apos_click.png`): item "Visualizar"
  aparece focado (destaque visual) mas o Enter não tinha efeito — tela
  não abria.
- Nesta validação: item "Visualizar" aparece focado com o MESMO padrão
  visual (`admin_visualizar_seta_focado.png` / `aluno_visualizar_seta_focado.png`),
  porém o Enter agora abre a tela de visualização
  (`admin_visualizar_seta_pos_enter.png` / `aluno_visualizar_seta_pos_enter.png`).
- Controle "Editar" do bug original (`vf_a1_editar_02_apos_click.png`,
  funcionando) foi substituído neste teste por "Evidências" — único item
  presente em ambos os menus testados (o menu do Admin nesta massa de
  dados de stage não tinha "Editar" disponível) — e também funcionou.

## Observação (não bloqueia veredito)
Ao abrir a tela de visualização como Aluno, apareceu um toast
`Request failed with status code 401` no canto da tela (visível em
`aluno_visualizar_seta_pos_enter.png`). Não impediu a renderização do
formulário nem é o objeto deste card — provavelmente uma chamada
secundária (permissão/analytics) sem relação com a navegação por teclado.
Registrado aqui para rastreabilidade; recomenda-se abrir card separado se
o dev quiser investigar.

## Cobertura de outras telas com list-control
O comentário do dev no PR pede validar "algumas outras tabelas" que usam
o componente compartilhado. Não foi possível identificar com segurança
outras listagens de admin que usem o mesmo `list-control` sem acesso ao
código-fonte/mapa de componentes — este laudo cobre apenas a tela de
Registros (onde o bug foi reportado). **Limitação de cobertura
declarada**: recomenda-se ao dev apontar explicitamente quais outras
tabelas usam o componente, para validação dedicada se necessário.

## Veredito
**PASSOU** — comportamento corrigido para os perfis Admin e Aluno na
tela de Registros: "Visualizar" agora abre corretamente via navegação
por teclado (seta + Enter), igual aos demais itens do mesmo menu.
