# Mapa do admin Twygo (stage)

> Gerado automaticamente por `scripts/mapa_admin_twygo.py` em 2026-05-25.
> Use este mapa pra navegar direto ao item certo, sem ficar caçando seletor.

- **BASE_URL**: `https://twygo1772627238.stage.twygoead.com`
- **ORG_ID**: `36675`
- **Entrada admin**: `/o/{ORG_ID}/events?tab=events&profile=admin`
- **Itens reais**: 30 menus + 1 logo (notificações filtradas)
- **Screenshot do sidebar completo**: `mapa-admin-sidebar-completa.png`

---

## Como usar

Em um script Playwright, depois do login admin, pra ir direto a um item:

```python
page.goto(f"{BASE_URL}/o/{ORG_ID}/<path-da-tabela-abaixo>")
```

Se preferir clicar via sidebar (mais "humano"), use o texto da coluna **Label** com
o seletor JS já testado em `scripts/retrabalho_cards_design.py`:

```python
href = page.evaluate("""(label) => {
    const re = new RegExp(label, 'i');
    const links = Array.from(document.querySelectorAll('a'));
    const m = links.find(a => re.test((a.innerText || '').trim()));
    return m ? m.href : null;
}""", "Modelos de conte[uú]do")
```

---

## Conteúdo

| Label                  | Path                                      | Observação                                |
| ---------------------- | ----------------------------------------- | ----------------------------------------- |
| Dashboard              | `/dashboard`                              | landing do admin                          |
| Conteúdos              | `/events?tab=events`                      | mesma URL do `profile=admin`              |
| Compartilhamentos      | `/shared_events`                          |                                           |
| Registros              | `/records`                                | BETA                                      |
| Modelos de conteúdo    | `/content_models`                         | feature flag por org                      |
| Base de conhecimento   | `/knowledge_repositories`                 |                                           |
| Biblioteca             | `/events/?tab=libraries`                  | mesma rota de `events` com tab diferente  |

## Pessoas

| Label             | Path                |
| ----------------- | ------------------- |
| Usuários          | `/users`            |
| Empresas          | `/companies`        |
| Questionários     | `/question_lists`   |
| Comunidades       | `/feed`             |

## Estrutura organizacional

| Label                | Path                                       |
| -------------------- | ------------------------------------------ |
| Organograma          | `/organization_chart`                      |
| Funções de negócio   | `/roles`                                   |
| Competências         | `/organization_chart_competencies`         |

## Sucessão

| Label              | Path                                  |
| ------------------ | ------------------------------------- |
| Dashboard geral    | `/succession_dashboards`              |
| Análise individual | `/succession_people_analysis`         |
| Ações de resposta  | `/succession_actions`                 |
| Parâmetros         | `/succession_initiatives`             |
| PDI                | `/admin/pdis`                         |

## Configurações

| Label                  | Path                              | Observação |
| ---------------------- | --------------------------------- | ---------- |
| Organização            | `/edit`                           |            |
| Menu                   | `/use_modes`                      |            |
| Integrações            | `/integrations`                   |            |
| Piloto automático      | `/autopilots`                     |            |
| Regras do Jogo         | `/game_rules`                     |            |
| Comunicação            | `/communication`                  |            |
| Cobrança de inscrição  | `/payments`                       |            |
| Plano e assinatura     | `/subscription_plans`             |            |
| Segurança              | `/security`                       | NOVO       |
| Controle de IA         | `/ai_consumption_analysis`        | BETA       |
| Aparência              | `/appearance`                     |            |

## Outros

| Label  | Path         | Observação                                |
| ------ | ------------ | ----------------------------------------- |
| TWYGO  | `/dashboard` | logo no topo do sidebar, leva ao Dashboard|

---

## Observações pra automação futura

1. **Título da página HTML** é sempre **"Domínio padrão"** em todo o admin —
   não use `page.title()` como sinal de que chegou na rota certa.
2. **Material Icons no DOM**: os itens da sidebar têm um `<span>` com o nome do
   ícone (ex: `leaderboard`, `format_list_bulleted_add`) que aparece colado ao
   texto via `innerText`. Sempre faça regex tolerante a prefixos ou rode
   `text.split('\n').pop().trim()` pra pegar só o rótulo final.
3. **Itens "novos/promovidos"** (Segurança, Registros, Controle de IA) carregam
   sufixo `NOVO` ou `BETA` no texto — considere isso ao matchear.
4. **Notificações no sino** caem também como `<a>` na coleta — filtre por
   path com prefixo `/o/{ORG_ID}/` E padrão de rota reconhecido. Notificações
   de export pra download (`/data_exports/<id>/download`) explodem o
   `page.goto` porque viram download direto — pule.
5. **Logo TWYGO** aparece como menu (`#31` na coleta) mas é só o link de volta
   pro Dashboard. Pode ser ignorado em testes.
6. **Sucessão tem 5 itens** todos com prefixo `/succession_` (ou `/admin/pdis`
   no caso do PDI) — provavelmente compartilham um header de seção no sidebar.

---

## Arquivos relacionados

- `mapa-admin-twygo.json` — dump bruto da coleta (com URLs completas, ordem
  observada e screenshots de cada item visitado)
- `mapa-admin-twygo/` — pasta com PNGs `01-*.png` até `35-*.png`
- `mapa-admin-sidebar-completa.png` — screenshot da sidebar inteira no admin
- `scripts/mapa_admin_twygo.py` — script de regeneração (rodar de novo quando
  a Twygo adicionar/remover item da sidebar)
