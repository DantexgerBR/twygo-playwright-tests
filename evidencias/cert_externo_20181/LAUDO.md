# Retrabalho 20181 (P0) — Certificado externo não aparece na listagem após sucesso

**Org:** 36676 (goatwy.stage) · **Tela:** Registros → Adicionar (Novo conteúdo externo)
**Esperado:** ao salvar um conteúdo/certificado externo com sucesso, o item deve ser
persistido e exibido na listagem de Registros.

## Veredito: ✅ Passou

Bug **não reproduz** — o registro criado persiste e aparece na listagem imediatamente.

## Evidências (teste ao vivo)

Criado um conteúdo externo com nome único de rastreio **`QA20181-18132159`**:
- Pessoa: Vini Coelho (vini.coelho@dev.com)
- Provedor: QA Provider · Tipo: Treinamento · Categoria: Liderança e desenvolvimento pessoal
- Carga horária: 1h · Data de término: 30/06/2026

Ao salvar, o sistema redirecionou para a listagem (sucesso). Buscando/inspecionando a
listagem, o registro aparece como **1ª linha (mais recente)**:

```
Vini Coelho · vini.coelho@dev.com · QA20181-18132159 · Externo · criado por usuario dev
· Treinamento · QA Provider · 1h · Aprovado
```

Fonte de verdade = a própria listagem de Registros, que continha exatamente o item criado
com todos os dados informados. Logo, não há falha de persistência nem de renderização.

## Observação de acesso
A credencial do card (`devtestes@teste.com` / 123456) está **inválida** no stage
(testado: "Login ou senha inválidos"). Validação feita com `usuariodev@testes.com`
(admin da mesma org 36676).

## Evidências (arquivos)
- 02-form-adicionar.png / 03-form-preenchido.png — formulário preenchido
- 04-pos-salvar-toast.png — redireciona à listagem após salvar (sucesso)
- 06-verify-busca-token.png — registro presente na listagem (1ª linha)

## Repro
```
.\.venv\Scripts\python.exe scripts/retrabalho_cert_externo_20181.py
```
