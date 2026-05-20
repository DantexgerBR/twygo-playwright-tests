# Caso de Teste — Desmarcar marca d'água em atividade de vídeo

## Objetivo
Verificar que ao desmarcar o checkbox **"Habilitar marca d'água no vídeo"** em uma atividade previamente configurada e salvar, a marca d'água deixa de ser exibida no Aprender.

## Pré-condições
- Usuário logado como **Admin**
- Feature flag de marca d'água **habilitada**
- Atividade de vídeo previamente cadastrada **com marca d'água habilitada**
- Aluno previamente matriculado e capaz de acessar o conteúdo no Aprender

## Metadados
- **Perfil de usuário testado:** Administrador
- **Plataforma testada:** Desktop
- **Tipo ambiente testado:** Principal
- **Tipo de Execução:** Manual / Automatizado (Playwright)

## Passos

| # | Ações do Passo | Resultados Esperados |
|---|----------------|----------------------|
| 1 | Acessar a atividade de vídeo previamente cadastrada para editar | Formulário de edição é exibido com o checkbox 'Habilitar marca d'água no vídeo' marcado |
| 2 | Desmarcar o checkbox 'Habilitar marca d'água no vídeo' | Checkbox 'Habilitar marca d'água no vídeo' fica desmarcado. Todos os campos de configuração e preview são ocultados |
| 3 | Clicar no botão 'Salvar' | Toast de sucesso exibida com o texto 'Alterações salvas com sucesso.' |
| 4 | Logar como o aluno e acessar a atividade no Aprender | Vídeo é reproduzido. Marca d'água NÃO é exibida sobre o vídeo |

## Histórico de execuções manuais
- 19/05/2026 — Testado na org `https://twygo1772627238.stage.twygoead.com/` — **Passou** em todos os passos.

## Automação
- Arquivo: [`tests/marca_dagua/test_desmarcar_marca_dagua_video.py`](../../tests/marca_dagua/test_desmarcar_marca_dagua_video.py)
- Page Objects: `pages/admin/atividade_video_page.py`, `pages/aprender/conteudo_video_page.py`
