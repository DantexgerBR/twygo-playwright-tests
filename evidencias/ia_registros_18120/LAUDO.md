# Retrabalho 18120 — [UniTwygo][BUG] Registros externo (Preencher com IA)

**Org:** 36675 (stage principal — tem créditos de IA; goatwy/36676 está zerada)
**Tela:** Aprendizagem > Registros > Adicionar (Novo conteúdo externo) → "Preencher com IA"
**PRs:** Twygo/twyg-app#10262 e Twygo/twygo-ai-knowledge-agent#348 (ambos OPEN no GitHub,
mas o comportamento do PR 348 já está deployado no stage — ver cenário A).

## Veredito: ✅ Passou

> **Escopo (comentário do dev Gabriel Coelho no card, 19/05/2026):** o campo "Website" NÃO
> é feito para receber links de vídeo/YouTube — é um extrator de conteúdo de páginas. Fazer
> funcionar para o YouTube exigiria implementação nova, **fora do escopo** desta correção.
> Logo o cenário B não é defeito a corrigir aqui; o que estava no escopo (cenário A) passou.

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

### Cenário B — link do YouTube → FORA DO ESCOPO (não é defeito)
Link `https://www.youtube.com/watch?v=k_rYoyLEZKg` no campo Website → "Preencher com IA":
a IA só inferiu a modalidade "Online" (nome/descrição/carga vazios). Conforme o dev
esclareceu no card, o campo "Website" é extrator de páginas e não suporta YouTube — então
esse comportamento é esperado, não um defeito desta correção.

## Conclusão
O foco da correção (extração de **certificados/conteúdo de página** — itens críticos Nome e
Carga horária) está funcionando no stage, batendo com todos os casos do PR 348. O cenário do
YouTube está fora do escopo (campo Website não é para vídeos). Retrabalho **aprovado**.

## Repro
```
.\.venv\Scripts\python.exe scripts/retrabalho_ia_registros_18120.py
```
(headless por padrão; use TW_HEADED=1 pra ver a janela). Valores em `resultado_dom.txt`.
