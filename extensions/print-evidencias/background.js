// Service worker: orquestra captura -> recorte -> upload Cloudinary -> URL.

// Inicia o fluxo de captura na aba ativa.
async function iniciarCaptura() {
  const [aba] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!aba || !aba.id) {
    notificar("Erro", "Nenhuma aba ativa encontrada.");
    return;
  }
  // Páginas internas do navegador não permitem injeção.
  if (/^(chrome|edge|about|chrome-extension):/.test(aba.url || "")) {
    notificar("Não suportado", "Não é possível capturar páginas internas do navegador. Abra um site comum.");
    return;
  }
  try {
    await chrome.scripting.executeScript({
      target: { tabId: aba.id },
      files: ["content.js"]
    });
  } catch (e) {
    notificar("Erro", "Não foi possível iniciar a seleção: " + e.message);
  }
}

// Dispara pelo atalho de teclado.
chrome.commands.onCommand.addListener((comando) => {
  if (comando === "capturar-area") iniciarCaptura();
});

// Mensagens vindas do popup e do content script.
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.tipo === "iniciar-captura") {
    iniciarCaptura();
    return;
  }
  if (msg.tipo === "area-selecionada") {
    processarSelecao(msg.rect, sender.tab)
      .then((url) => sendResponse({ ok: true, url }))
      .catch((err) => sendResponse({ ok: false, erro: err.message }));
    return true; // resposta assíncrona
  }
});

async function processarSelecao(rect, aba) {
  if (!rect || rect.width < 2 || rect.height < 2) {
    throw new Error("Seleção muito pequena.");
  }

  const dataUrl = await chrome.tabs.captureVisibleTab(aba.windowId, {
    format: "png"
  });

  const blobRecortado = await recortar(dataUrl, rect);
  const url = await uploadCloudinary(blobRecortado);

  // Persiste a última URL e copia para a área de transferência.
  await chrome.storage.local.set({ ultimaUrl: url, ultimoEm: Date.now() });
  const copiou = await copiarParaClipboard(url, aba.id);

  notificar(
    "Print enviado ✓",
    url + (copiou ? "\n(URL copiada para a área de transferência)" : "\n(abra o popup para copiar a URL)")
  );
  return url;
}

// Recorta o dataURL na região selecionada, respeitando o devicePixelRatio.
async function recortar(dataUrl, rect) {
  const resp = await fetch(dataUrl);
  const blobOriginal = await resp.blob();
  const bitmap = await createImageBitmap(blobOriginal);

  const dpr = rect.dpr || 1;
  const sx = Math.round(rect.x * dpr);
  const sy = Math.round(rect.y * dpr);
  const sw = Math.round(rect.width * dpr);
  const sh = Math.round(rect.height * dpr);

  const canvas = new OffscreenCanvas(sw, sh);
  const ctx = canvas.getContext("2d");
  ctx.drawImage(bitmap, sx, sy, sw, sh, 0, 0, sw, sh);

  return await canvas.convertToBlob({ type: "image/png" });
}

async function uploadCloudinary(blob) {
  const { cloudName, uploadPreset, pasta } = await chrome.storage.local.get([
    "cloudName",
    "uploadPreset",
    "pasta"
  ]);
  if (!cloudName || !uploadPreset) {
    throw new Error("Cloudinary não configurado. Abra as opções da extensão.");
  }

  const form = new FormData();
  form.append("file", blob, "evidencia.png");
  form.append("upload_preset", uploadPreset);
  if (pasta) form.append("folder", pasta);

  const resp = await fetch(
    "https://api.cloudinary.com/v1_1/" + encodeURIComponent(cloudName) + "/image/upload",
    { method: "POST", body: form }
  );

  const json = await resp.json();
  if (!resp.ok || !json.secure_url) {
    const detalhe = json && json.error && json.error.message ? json.error.message : resp.status;
    throw new Error("Falha no upload Cloudinary: " + JSON.stringify(detalhe));
  }
  return json.secure_url;
}

// Copia a URL via content script (o service worker não tem acesso ao clipboard da página).
// Retorna true se a cópia foi confirmada.
async function copiarParaClipboard(texto, tabId) {
  try {
    const [res] = await chrome.scripting.executeScript({
      target: { tabId },
      func: async (t) => {
        try {
          await navigator.clipboard.writeText(t);
          return true;
        } catch (_) {
          // Fallback: textarea + execCommand (funciona mesmo sem foco em alguns casos).
          try {
            const ta = document.createElement("textarea");
            ta.value = t;
            ta.style.position = "fixed";
            ta.style.opacity = "0";
            document.body.appendChild(ta);
            ta.select();
            const ok = document.execCommand("copy");
            ta.remove();
            return ok;
          } catch (_) {
            return false;
          }
        }
      },
      args: [texto]
    });
    return Boolean(res && res.result);
  } catch (e) {
    // Ignora: o popup ainda mostra a URL e ela fica salva em storage.
    return false;
  }
}

function notificar(titulo, mensagem) {
  chrome.notifications.create({
    type: "basic",
    iconUrl: "icon.png",
    title: titulo,
    message: mensagem
  });
}
