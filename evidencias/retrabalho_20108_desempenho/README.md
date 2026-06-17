# 20108 (P0) — Avaliação de Desempenho não prossegue / autoavaliação

**Ambiente:** stage 37048 (Desempenho/Gestão de Time). Org da evidência do card: 19830 (linkada — não usar).

## Resultado: infra montada do zero, mas BLOQUEADO por 500 no seletor de participantes

### O que foi construído (do zero, com sucesso)
1. **Modelo de avaliação** "QA20108 Modelo Desempenho" — criado em Questionários > Avaliações,
   marcado em **"Pode ser usado em: Avaliação de desempenho"** (POST /assessments → 200).
2. **Ciclo 166** "QA20108 Avaliacao Teste" — criado via Novo ciclo (POST /cycles → 201,
   "Ciclo criado com sucesso"): Identificação (16/06–15/09/2026) + Avaliações
   (Avaliação de Desempenho + modelo acima) + Etapas (Auto-avaliação + Resultado final
   "Cálculo automático ponderado").

### BLOQUEIO (impede campanha → autoavaliação)
Ao criar a campanha (`/cycles/166/campaigns/new` → aba "Quem participa" → "Definir
participantes"), o drawer **"Vincular pessoas" gira indefinidamente** porque a API que ele
consome retorna **500**:

```
GET /api/v1/o/37048/professionals/results_for_filter            -> 500 Internal Server Error
GET /api/v1/o/37048/professionals/results_for_filter?...page=1  -> 500
GET .../results_for_filter?search_field=name&search_value=a     -> 500
GET .../results_for_filter?cycle_id=166                         -> 500
(500 em TODAS as combinações de parâmetros)

# comparativo — o endpoint "plano" funciona:
GET /api/v1/o/37048/professionals?page=1                        -> 200 (lista profissionais)
```

Sem o `results_for_filter`, não há como selecionar participantes → não cria campanha →
não ativa autoavaliação → **não dá pra chegar na resposta da avaliação** (onde está o bug
P0 "não prossegue").

### Leitura (anti-falso-positivo)
- Esse **500 é reproduzível** e independe de parâmetros; é candidato a **bug próprio**
  (possível: o endpoint quebra com profissionais de dados incompletos — ex.: a lista plana
  trouxe "nova inscricao" com CPF vazio). NÃO é, por si só, o bug "não prossegue" do card
  20108 (que é na etapa de RESPOSTA), mas **bloqueia** a validação do 20108 no 37048.
- Para validar o 20108 de fato: usar org onde o seletor de participantes funcione (sem o 500),
  ou corrigir o 500, então criar campanha → ativar → responder a autoavaliação até a última
  seção → conferir se conclui/prossegue.

## Scripts
`recon_20108_*.py`, `build_20108_*.py`, `diag_20108_*.py`, `get_cycle_id.py`.
Artefatos criados no 37048: modelo "QA20108 Modelo Desempenho", ciclo 166 "QA20108 Avaliacao Teste".
