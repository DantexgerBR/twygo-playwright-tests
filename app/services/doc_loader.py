"""Lê documentos do disco (md, txt, pdf, imagens) e devolve um `Documento` populado."""
from __future__ import annotations

from pathlib import Path

# Importação circular evitada: o tipo Documento vem de app.state, mas para
# evitar circular import, definimos aqui um helper que não precisa do tipo.


def _estimar_tokens(texto: str) -> int:
    """Aproximação grosseira: ~4 caracteres por token no Claude."""
    return max(1, len(texto) // 4)


def _ler_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pedacos: list[str] = []
    for pagina in reader.pages:
        try:
            texto = pagina.extract_text() or ""
        except Exception:
            texto = ""
        if texto.strip():
            pedacos.append(texto)
    return "\n\n".join(pedacos)


def _tipo_por_extensao(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".md", ".markdown"):
        return "md"
    if ext in (".txt", ".text"):
        return "txt"
    if ext == ".pdf":
        return "pdf"
    if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
        return "imagem"
    raise ValueError(f"Extensão não suportada: {ext}")


def load_doc(path: Path):
    """Carrega um doc do disco. Retorna um app.state.Documento.

    Importa Documento aqui dentro para evitar circular import com app.state.
    """
    from app.state import Documento  # local import para evitar ciclo

    tipo = _tipo_por_extensao(path)

    if tipo == "md" or tipo == "txt":
        conteudo = path.read_text(encoding="utf-8", errors="replace")
        tokens = _estimar_tokens(conteudo)
    elif tipo == "pdf":
        conteudo = _ler_pdf(path)
        tokens = _estimar_tokens(conteudo)
    else:  # imagem
        conteudo = ""
        tokens = 0  # imagem entra como vision content, não contamos pelo texto

    return Documento(
        path=path,
        nome=path.name,
        tipo=tipo,
        conteudo=conteudo,
        tokens_estimados=tokens,
    )
