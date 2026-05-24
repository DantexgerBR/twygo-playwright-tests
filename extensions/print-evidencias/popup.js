async function carregar() {
  const { ultimaUrl, cloudName, uploadPreset } = await chrome.storage.local.get([
    "ultimaUrl",
    "cloudName",
    "uploadPreset"
  ]);

  const alvo = document.getElementById("ultima");
  if (ultimaUrl) {
    alvo.className = "readout";
    alvo.innerHTML = "";
    const a = document.createElement("a");
    a.href = ultimaUrl;
    a.target = "_blank";
    a.textContent = ultimaUrl;
    alvo.appendChild(a);

    const btn = document.getElementById("copiar");
    btn.style.display = "block";
    btn.addEventListener("click", async () => {
      await navigator.clipboard.writeText(ultimaUrl);
      btn.textContent = "Copiado ✓";
      setTimeout(() => (btn.textContent = "Copiar URL"), 1500);
    });
  }

  if (!cloudName || !uploadPreset) {
    document.getElementById("aviso").style.display = "block";
    document.getElementById("status-bar").classList.add("off");
    document.getElementById("status-txt").textContent = "Não configurado";
  }
}

document.getElementById("capturar").addEventListener("click", () => {
  chrome.runtime.sendMessage({ tipo: "iniciar-captura" });
  window.close(); // fecha o popup para liberar a tela para a seleção
});

document.getElementById("opcoes").addEventListener("click", (e) => {
  e.preventDefault();
  chrome.runtime.openOptionsPage();
});

carregar();
