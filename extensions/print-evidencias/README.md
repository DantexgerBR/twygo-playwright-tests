# Print Evidências (Twygo)

Extensão de navegador que captura uma área da tela, sobe o print para o **Cloudinary**
e copia a **URL pública** para a área de transferência — pronta para colar no bug report.

A configuração é sempre **manual na máquina de quem usa**: nada de credencial vai no
código. A extensão guarda os dados no `chrome.storage.local` do navegador, então cada
pessoa preenche uma vez no perfil dela.

---

## Passo 0 — Escolha a conta Cloudinary (Opção A ou B)

Antes de configurar a extensão você precisa de dois valores: um **Cloud name** e um
**Upload preset não assinado (unsigned)**. De onde eles vêm depende da opção escolhida.

### Opção A — Todos usam a MESMA conta (compartilhada)

Mais simples para um time pequeno. As evidências de todos caem na mesma conta e
consomem a mesma quota.

1. O dono da conta abre o Cloudinary e cria (uma única vez) um upload preset unsigned:
   **Settings (⚙) → Upload → Upload presets → Add upload preset**
   - **Signing Mode:** `Unsigned`
   - **Folder** (opcional): `twygo-evidencias`
   - Salvar e anotar o **nome do preset**.
2. O dono compartilha com o time apenas estes dois valores:
   - **Cloud name** (fica no Dashboard)
   - **Upload preset** (o nome criado acima)
3. Cada pessoa usa esses mesmos dois valores na configuração da extensão (Passo 1).

> ⚠️ Como o preset é *unsigned*, qualquer pessoa com o `cloud name` + nome do preset
> consegue subir imagens nessa conta. Trate esses valores como semi-secretos: ok para
> um time de confiança, **não** exponha em repositório público.

### Opção B — Cada pessoa com a SUA conta (isolada)

Quota e evidências separadas por pessoa. Recomendado se você não quer dividir a sua conta.

1. Criar uma conta grátis em https://cloudinary.com
2. No Dashboard, anotar o **Cloud name**.
3. Criar um upload preset unsigned:
   **Settings (⚙) → Upload → Upload presets → Add upload preset**
   - **Signing Mode:** `Unsigned`
   - **Folder** (opcional): `twygo-evidencias`
   - Salvar e anotar o **nome do preset**.
4. Usar o **seu** Cloud name + Upload preset na configuração da extensão (Passo 1).

---

## Passo 1 — Instalar e configurar a extensão

### Instalar (carregar sem compactação)

1. Abrir `chrome://extensions` (ou `edge://extensions`).
2. Ativar o **Modo desenvolvedor** (canto superior direito).
3. Clicar em **Carregar sem compactação** e selecionar a pasta
   `extensions/print-evidencias`.

> Quando alterar arquivos da extensão, volte aqui e clique em **Atualizar/Recarregar**.

### Configurar as credenciais

1. Clicar no ícone da extensão (a mira) → no popup, clicar em **⚙ Configurações**.
2. Preencher:
   | Campo            | O que colocar                                                |
   |------------------|--------------------------------------------------------------|
   | **Cloud name**   | Cloud name da Opção A ou B (ex: `djkkooprl`)                  |
   | **Upload preset**| Nome do preset *unsigned* (ex: `twygo_evidencias`)           |
   | **Pasta**        | Opcional. Deixe **vazio** se o preset já define uma pasta.   |
3. Clicar em **Salvar**.

Se estiver tudo certo, o popup mostra o LED verde **"Cloudinary conectado"**.
Faltando algo, fica vermelho **"Não configurado"**.

---

## Passo 2 — Usar

1. Atalho **`Ctrl+Shift+E`** (ou abrir o popup e clicar em **Capturar área**).
2. Arrastar para selecionar a região (a leitura mostra as dimensões ao vivo; `ESC` cancela).
3. Ao soltar, o print sobe para o Cloudinary e a **URL pública é copiada automaticamente**
   para a área de transferência.
4. A última URL também fica no popup, com botão **Copiar URL** (fallback caso a cópia
   automática falhe em alguma página).

---

## Notas

- A extensão usa upload **unsigned** — ela **nunca** vê o seu *API Secret*.
- O *API Secret* só é necessário para o script `scripts/upload_evidencias.py` (via
  `CLOUDINARY_URL` no `.env`), que é outra ferramenta e independe desta extensão.
- Em páginas internas do navegador (`chrome://`, `edge://`, etc.) a captura não funciona —
  use em um site comum.
