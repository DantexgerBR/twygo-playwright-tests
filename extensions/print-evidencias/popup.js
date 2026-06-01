async function carregar() {
  const { ultimaUrl, cloudName, uploadPreset } = await chrome.storage.local.get([
    "ultimaUrl",
    "cloudName",
    "uploadPreset"
  ]);

  if (ultimaUrl) mostrarUrl(ultimaUrl);

  if (!cloudName || !uploadPreset) {
    document.getElementById("aviso").style.display = "block";
    document.getElementById("status-bar").classList.add("off");
    document.getElementById("status-txt").textContent = "Não configurado";
  }
}

// Exibe a URL no readout e libera o botão de copiar.
function mostrarUrl(url) {
  const alvo = document.getElementById("ultima");
  alvo.className = "readout";
  alvo.innerHTML = "";
  const a = document.createElement("a");
  a.href = url;
  a.target = "_blank";
  a.textContent = url;
  alvo.appendChild(a);

  document.getElementById("copiar").style.display = "block";
}

// Estado de processamento / erro logo abaixo dos botões.
function setProc(texto) {
  const el = document.getElementById("proc");
  if (texto) {
    el.textContent = texto;
    el.classList.remove("erro");
    el.style.display = "block";
  } else {
    el.style.display = "none";
  }
}
function setErro(texto) {
  const el = document.getElementById("proc");
  el.textContent = texto;
  el.classList.add("erro");
  el.style.display = "block";
}

function blobParaDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const fr = new FileReader();
    fr.onload = () => resolve(fr.result);
    fr.onerror = () => reject(new Error("Não foi possível ler a imagem."));
    fr.readAsDataURL(blob);
  });
}

// Sobe a imagem (colada ou de arquivo) via background -> Cloudinary.
async function enviarBlob(blob) {
  if (!blob || !blob.type || !blob.type.startsWith("image/")) {
    setErro("Isso não é uma imagem.");
    return;
  }
  try {
    setProc("enviando imagem…");
    const dataUrl = await blobParaDataUrl(blob);
    const resp = await chrome.runtime.sendMessage({ tipo: "upload-imagem", dataUrl });
    if (!resp || !resp.ok) {
      throw new Error(resp && resp.erro ? resp.erro : "Falha no upload.");
    }
    setProc(null);
    mostrarUrl(resp.url);
    // Copia automaticamente, como no fluxo de captura.
    try {
      await navigator.clipboard.writeText(resp.url);
    } catch (_) {
      /* o botão Copiar URL continua disponível */
    }
  } catch (e) {
    setErro(e.message);
  }
}

// ---- Captura de área (fluxo original) ----
document.getElementById("capturar").addEventListener("click", () => {
  chrome.runtime.sendMessage({ tipo: "iniciar-captura" });
  window.close(); // fecha o popup para liberar a tela para a seleção
});

// ---- Colar print da área de transferência ----
document.getElementById("colar").addEventListener("click", async () => {
  try {
    const itens = await navigator.clipboard.read();
    for (const item of itens) {
      const tipo = item.types.find((t) => t.startsWith("image/"));
      if (tipo) {
        const blob = await item.getType(tipo);
        enviarBlob(blob);
        return;
      }
    }
    setErro("Nenhuma imagem na área de transferência. Copie um print e tente de novo.");
  } catch (_) {
    // Alguns navegadores exigem o gesto de colar: oriente o Ctrl+V.
    setErro("Pressione Ctrl+V aqui para colar a imagem.");
  }
});

// Ctrl+V em qualquer lugar do popup também funciona.
document.addEventListener("paste", (e) => {
  const itens = e.clipboardData && e.clipboardData.items;
  if (!itens) return;
  for (const it of itens) {
    if (it.type && it.type.startsWith("image/")) {
      const blob = it.getAsFile();
      if (blob) {
        e.preventDefault();
        enviarBlob(blob);
        return;
      }
    }
  }
});

// ---- Escolher arquivo do computador ----
document.getElementById("arquivo").addEventListener("click", () => {
  document.getElementById("file-input").click();
});
document.getElementById("file-input").addEventListener("change", (e) => {
  const file = e.target.files && e.target.files[0];
  if (file) enviarBlob(file);
  e.target.value = ""; // permite reenviar o mesmo arquivo
});

// ---- Copiar URL ----
document.getElementById("copiar").addEventListener("click", async () => {
  const a = document.querySelector("#ultima a");
  if (!a) return;
  await navigator.clipboard.writeText(a.href);
  const btn = document.getElementById("copiar");
  btn.textContent = "Copiado ✓";
  setTimeout(() => (btn.textContent = "Copiar URL"), 1500);
});

// ---- Configurações ----
document.getElementById("opcoes").addEventListener("click", (e) => {
  e.preventDefault();
  chrome.runtime.openOptionsPage();
});

carregar();
