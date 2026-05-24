// Overlay de seleção por retângulo. Injetado sob demanda pelo background.
// Guarda contra dupla injeção.
(function () {
  if (window.__printEvidenciasAtivo) return;
  window.__printEvidenciasAtivo = true;

  const ACC = "#b6ff3c";
  const MONO = '"Cascadia Code","JetBrains Mono","SF Mono",ui-monospace,Consolas,monospace';

  const overlay = document.createElement("div");
  overlay.style.cssText = [
    "position:fixed",
    "inset:0",
    "z-index:2147483647",
    "cursor:crosshair",
    "background:rgba(8,10,14,0.45)",
    "backdrop-filter:saturate(0.7)"
  ].join(";");

  const caixa = document.createElement("div");
  caixa.style.cssText = [
    "position:fixed",
    "border:1.5px solid " + ACC,
    "background:rgba(182,255,60,0.08)",
    "box-shadow:0 0 0 100vmax rgba(8,10,14,0.35), 0 0 18px rgba(182,255,60,0.35)",
    "display:none",
    "pointer-events:none",
    "z-index:2147483647"
  ].join(";");

  // Leitura de dimensões (estilo instrumento), presa ao canto da seleção.
  const medida = document.createElement("div");
  medida.style.cssText = [
    "position:fixed",
    "display:none",
    "padding:2px 7px",
    "background:" + ACC,
    "color:#0a0c0f",
    "font:700 11px/1.4 " + MONO,
    "letter-spacing:0.08em",
    "border-radius:4px",
    "pointer-events:none",
    "z-index:2147483647",
    "white-space:nowrap"
  ].join(";");

  const dica = document.createElement("div");
  dica.innerHTML = "ARRASTE PARA SELECIONAR <span style='opacity:.55'>·</span> ESC PARA CANCELAR";
  dica.style.cssText = [
    "position:fixed",
    "top:16px",
    "left:50%",
    "transform:translateX(-50%)",
    "background:rgba(16,21,27,0.95)",
    "color:#e8eef5",
    "font:700 11px/1.4 " + MONO,
    "letter-spacing:0.16em",
    "padding:8px 14px",
    "border:1px solid #1d2530",
    "border-radius:8px",
    "box-shadow:0 8px 30px -10px rgba(0,0,0,0.8)",
    "z-index:2147483647",
    "pointer-events:none"
  ].join(";");

  document.documentElement.appendChild(overlay);
  document.documentElement.appendChild(caixa);
  document.documentElement.appendChild(medida);
  document.documentElement.appendChild(dica);

  let inicioX = 0;
  let inicioY = 0;
  let arrastando = false;

  function limpar() {
    overlay.remove();
    caixa.remove();
    medida.remove();
    dica.remove();
    window.__printEvidenciasAtivo = false;
    document.removeEventListener("keydown", onEsc, true);
  }

  function onEsc(e) {
    if (e.key === "Escape") {
      e.preventDefault();
      limpar();
    }
  }
  document.addEventListener("keydown", onEsc, true);

  overlay.addEventListener("mousedown", (e) => {
    arrastando = true;
    inicioX = e.clientX;
    inicioY = e.clientY;
    caixa.style.display = "block";
    caixa.style.left = inicioX + "px";
    caixa.style.top = inicioY + "px";
    caixa.style.width = "0px";
    caixa.style.height = "0px";
    medida.style.display = "block";
    dica.style.display = "none";
  });

  overlay.addEventListener("mousemove", (e) => {
    if (!arrastando) return;
    const x = Math.min(e.clientX, inicioX);
    const y = Math.min(e.clientY, inicioY);
    const w = Math.abs(e.clientX - inicioX);
    const h = Math.abs(e.clientY - inicioY);
    caixa.style.left = x + "px";
    caixa.style.top = y + "px";
    caixa.style.width = w + "px";
    caixa.style.height = h + "px";

    // Posiciona a leitura logo acima da seleção (ou abaixo, se colar no topo).
    medida.textContent = w + " × " + h;
    const acima = y - 26 > 0;
    medida.style.left = x + "px";
    medida.style.top = (acima ? y - 24 : y + h + 6) + "px";
  });

  overlay.addEventListener("mouseup", (e) => {
    if (!arrastando) return;
    arrastando = false;

    const x = Math.min(e.clientX, inicioX);
    const y = Math.min(e.clientY, inicioY);
    const width = Math.abs(e.clientX - inicioX);
    const height = Math.abs(e.clientY - inicioY);

    // Esconde o overlay ANTES da captura para não aparecer no print.
    limpar();

    if (width < 2 || height < 2) return;

    const rect = { x, y, width, height, dpr: window.devicePixelRatio || 1 };

    // Pequeno atraso garante que o overlay sumiu do frame capturado.
    setTimeout(() => {
      chrome.runtime.sendMessage({ tipo: "area-selecionada", rect }, (resp) => {
        if (chrome.runtime.lastError) return;
        // O background já notifica/copia; aqui não precisamos fazer nada.
      });
    }, 80);
  });
})();
