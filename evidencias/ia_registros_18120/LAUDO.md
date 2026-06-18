# Retrabalho 18120 — [UniTwygo][BUG] Registros externo (Preencher com IA)

**Org:** 36675 (stage principal — tem créditos de IA; goatwy/36676 está zerada)
**Tela:** Aprendizagem > Registros > Adicionar (Novo conteúdo externo) → "Preencher com IA"
**PRs:** Twygo/twyg-app#10262 e Twygo/twygo-ai-knowledge-agent#348 (ambos OPEN no GitHub,
mas o comportamento do PR 348 já está deployado no stage — ver cenário A).

## Veredito: ❌ Falhou (cenário A corrigido; cenário B ainda não)

### Cenário A — certificado (arquivo) → ✅ CORRIGIDO
Certificado de teste (PNG): "João da Silva concluiu o curso de Liderança Ágil e Gestão de
Times", "Carga horária: 480 minutos", "Emitido em 15/03/2024". Após "Preencher com IA"
(IA executou em ~15s), valores lidos no DOM:
- **Conteúdo (Nome):** "Liderança Ágil e Gestão de Times" ✅ (crítico)
- **Carga horária:** 0008:00:00 = **8h** ✅ (crítico — converteu 480 min → 8h)
- Categorias: Gestão, Soft Skills ✅ (inferidas)
- Descrição: gerada automaticamente ✅
- Tipo de experiência: vazio (card diz "aceitável não gerar")
- Datas: só `certificate_date = 15/03/2024`; início/término/aprovação/validade VAZIAS ✅
  (não inventou datas — exatamente o que o PR 348 endureceu)

Bate 1:1 com os 4 casos de teste do PR 348. Os dois itens críticos do card passaram.

### Cenário B — link do YouTube → ❌ AINDA FALHA
Link `https://www.youtube.com/watch?v=k_rYoyLEZKg` no campo Website → "Preencher com IA"
(IA executou em ~24s). Valores no DOM:
- Tipo de experiência: "Online" (única coisa inferida)
- **Nome (Conteúdo): VAZIO** · Descrição: vazia · Carga horária: 0 · Categorias: vazias
O conteúdo do vídeo não é extraído do link — só a modalidade. O sintoma do card ("nenhuma
informação puxada") melhorou (vem "Online"), mas o dado significativo (nome) segue ausente.

## Conclusão
Cenário A (certificado) está corrigido. Cenário B (link do YouTube) **continua falhando** —
a IA não extrai o conteúdo do vídeo (só a modalidade "Online"; nome/descrição/carga vazios).
Como o cenário B é um defeito declarado no card e segue sem resolver, o retrabalho **falhou**.

## Repro
```
.\.venv\Scripts\python.exe scripts/retrabalho_ia_registros_18120.py
```
(headless por padrão; use TW_HEADED=1 pra ver a janela). Valores em `resultado_dom.txt`.
