async function carregar() {
  const { cloudName, uploadPreset, pasta } = await chrome.storage.local.get([
    "cloudName",
    "uploadPreset",
    "pasta"
  ]);
  if (cloudName) document.getElementById("cloudName").value = cloudName;
  if (uploadPreset) document.getElementById("uploadPreset").value = uploadPreset;
  if (pasta) document.getElementById("pasta").value = pasta;
}

document.getElementById("salvar").addEventListener("click", async () => {
  const cloudName = document.getElementById("cloudName").value.trim();
  const uploadPreset = document.getElementById("uploadPreset").value.trim();
  const pasta = document.getElementById("pasta").value.trim();
  await chrome.storage.local.set({ cloudName, uploadPreset, pasta });
  const status = document.getElementById("status");
  status.textContent = "Salvo ✓";
  setTimeout(() => (status.textContent = ""), 2000);
});

carregar();
