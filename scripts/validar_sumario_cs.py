# -*- coding: utf-8 -*-
"""Valida que o Sumário do docx gerado tem hyperlinks internos casando com bookmarks."""
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
with zipfile.ZipFile(r"D:\Trabalho\Twygo\Projetos\Continuidade e sucessão\Continuidade e sucessão - Usabilidade.docx") as z:
    xml = z.read("word/document.xml").decode("utf-8")

links = re.findall(r'<w:hyperlink [^>]*w:anchor="([^"]+)"', xml)
marks = re.findall(r'<w:bookmarkStart [^>]*w:name="([^"]+)"', xml)
print("links do sumário:", links)
print("bookmarks       :", marks)
faltando = set(links) - set(marks)
print("FALTANDO bookmark pra:", faltando if faltando else "nenhum — todos os links têm destino ✔")
