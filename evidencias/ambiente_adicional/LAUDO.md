# Laudo — [Recertificação] QA x.x — Ambientes adicionais (Artia 19338)

**Data:** 2026-05-29
**Org/Ambiente:** 36675 — `https://twygo1772627238.stage.twygoead.com/`
**Escopo solicitado:** validar acesso/branding ponta a ponta do ambiente adicional já criado
**Perfil:** Administrador (login admin do .env)

## Veredito: ⚠️ Inconclusivo (bloqueado por permissão)

Não foi possível completar a validação ponta a ponta na org 36675 com a conta admin.

## O que foi verificado

| Rota | Status | Resultado |
|------|--------|-----------|
| `/o/36675/additional_environments/new` | 200 | Renderiza o formulário "Adicionar ambiente" (Nome do ambiente, E-mail, Cor primária, Cor do texto, Logo, Salvar/Cancelar) — **idêntico ao print do task**. Confirma que o print foi tirado aqui. |
| `/o/36675/additional_environments` (listagem) | 200 | **"Você não tem permissão para acessar esta página."** |
| `/o/36675/additional_environments?profile=admin` | 200 | Mesma negativa de permissão. |
| `/o/36675/appearance` | 200 | "Aparência > Kit de marca" — outra feature (kit de marca), não é "Ambientes adicionais". |
| `/o/36675/edit` | 200 | "Organização" (Dados/Customizações/...) — não é a feature. |

Nenhum link/botão com "ambiente" na sidebar/DOM do admin → a feature não tem entry point visível pra esse perfil.

## Por que está bloqueado

1. **Listagem negada:** sem acesso a `/additional_environments`, não dá pra confirmar que o `ambiente_adicional` (dante@adicional.com) foi de fato **salvo**, nem obter a **URL/subdomínio** do ambiente criado.
2. **Sem URL não há ponta a ponta:** a validação de branding (cor primária #ff0000ff + logo) e de isolamento depende de abrir a URL do ambiente adicional num contexto limpo do browser. Sem a listagem, não tenho essa URL.
3. **Possível inconsistência de permissão (achado):** o formulário de criação (`/new`) abre normalmente, mas o índice de gerenciamento nega permissão para o mesmo admin. Vale reportar ao time.

## Observação sobre o print

O print do task está em estado **pré-save** (botões Salvar/Cancelar visíveis) — não comprova que o ambiente foi salvo.

## Para destravar (precisa do Dante / time)

- Conta/perfil com permissão à listagem de ambientes adicionais, **ou**
- A **URL/subdomínio** do `ambiente_adicional` já criado (aí valido branding + isolamento abrindo direto), **ou**
- Credenciais do ambiente (dante@adicional.com + senha) caso a validação exija login dentro dele.

## Evidências (evidencias/ambiente_adicional/)
- `v2-additional_environments-new.png` — form de criação (= print do task)
- `v2-additional_environments.png` — listagem com "não tem permissão"
- `rota-appearance.png` — Aparência/Kit de marca (feature diferente)
- `rota-edit.png` — Organização (feature diferente)
