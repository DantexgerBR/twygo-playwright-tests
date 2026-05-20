# T-1595 — Reprodução do vídeo no Aprender exibe marca d'água em movimento (Desktop)

## Objetivo
Verificar que ao reproduzir um vídeo cujo "Tipo de exibição" está configurado como **Em movimento**, a estampa se movimenta sobre o vídeo durante a reprodução.

## Pré-condições
- Aluno logado
- Feature flag de marca d'água habilitada
- Atividade de vídeo previamente cadastrada com marca d'água habilitada (tipo: **Em movimento**; posição: **Sobre todo o vídeo**; informações: **CPF**)
- Aluno previamente matriculado no curso
- Viewport Desktop (1920×1080)

## Metadados
- **Perfil:** Aluno
- **Plataforma:** Desktop (1920×1080)
- **Ambiente:** Principal (stage)
- **Tipo de Execução:** Automatizada (Playwright) + validação visual

## Passos

| # | Ação | Resultado esperado |
|---|------|--------------------|
| 1 | Acessar o curso no Aprender | Tela do curso é exibida com a lista de conteúdos |
| 2 | Selecionar a atividade de vídeo | Player de vídeo é exibido |
| 3 | Iniciar a reprodução do vídeo | Vídeo começa a ser reproduzido. Marca d'água é exibida e sua posição sobre o vídeo muda ao longo do tempo (movimentação) |
| 4 | Aguardar até a metade da reprodução | Marca d'água continua se movimentando. Estampa não permanece fixa em uma posição |
| 5 | Aguardar a reprodução chegar ao final | Marca d'água continua se movimentando. Estampa não permanece fixa em uma posição |

## Particularidade técnica
A marca d'água é renderizada **server-side** e queimada nos frames do vídeo (não fica no DOM). Não é possível verificar movimento via seletor — só por inspeção visual de screenshots em diferentes momentos.

## Histórico

### Execução automatizada 2026-05-20 (stage `https://twygo1772627238.stage.twygoead.com/`, evento 787696, atividade 9280032)

- ✅ Passos 1-5 executados sem erro técnico
- ❌ Validação visual: **marca d'água permanece estática** nas mesmas 6 posições (grade 3×2 cobrindo o vídeo) nos 3 momentos capturados (t≈2s, t≈5s, t≈10s)
- 📌 **Status:** retrabalho já aberto para esse comportamento — bug confirmado pelo time
- ⚠️ Vídeo de teste tem apenas 11s. Repetir com vídeo de 60s+ se houver suspeita de que o ciclo de animação é maior que a duração

## Automação
- Teste: [`tests/marca_dagua/test_t1595_marca_em_movimento.py`](../../tests/marca_dagua/test_t1595_marca_em_movimento.py)
- Setup pré-requisito (habilita marca d'água + configura tipo): [`scripts/setup_t1595.py`](../../scripts/setup_t1595.py)
- Execução ad-hoc (sem pytest): [`scripts/run_t1595.py`](../../scripts/run_t1595.py)
