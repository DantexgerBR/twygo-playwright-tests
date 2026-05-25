"""Dialogo nativo de selecao de arquivo via Tkinter.

Substitui ft.FilePicker que mudou drasticamente no Flet 0.85 e nao
aceita mais pick_files(). Tkinter ja vem com Python, sem dep extra.
"""
from __future__ import annotations

from pathlib import Path


def escolher_arquivos(
    titulo: str = "Selecione arquivos",
    extensoes: list[tuple[str, str]] | None = None,
    multiplo: bool = True,
) -> list[Path]:
    """Abre dialogo nativo do Windows. Retorna lista de paths selecionados.

    extensoes: lista de (descricao, pattern). Ex: [("Documentos", "*.md *.pdf")]
    """
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    filetypes = extensoes or [("Todos", "*.*")]

    if multiplo:
        resultado = filedialog.askopenfilenames(
            title=titulo,
            filetypes=filetypes,
            parent=root,
        )
    else:
        single = filedialog.askopenfilename(
            title=titulo,
            filetypes=filetypes,
            parent=root,
        )
        resultado = (single,) if single else ()

    root.destroy()

    return [Path(p) for p in resultado if p]
