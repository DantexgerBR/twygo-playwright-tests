# -*- coding: utf-8 -*-
"""Inspeciona hyperlinks internos e bookmarks do template Widgets - Usabilidade.docx."""
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
with zipfile.ZipFile(r"D:\Trabalho\Twygo\Projetos\Widgets\Widgets - Usabilidade.docx") as z:
    xml = z.read("word/document.xml").decode("utf-8")

print("hyperlinks w:anchor:")
for anchor, inner in re.findall(r'<w:hyperlink [^>]*w:anchor="([^"]+)"[^>]*>(.*?)</w:hyperlink>', xml, re.S)[:15]:
    txt = re.sub(r"<[^>]+>", "", inner)
    # estilo do run dentro do hyperlink
    estilo = re.findall(r'<w:rStyle w:val="([^"]+)"', inner)
    print(f"  anchor={anchor!r}  estilo={estilo}  texto={txt!r}")

print("\nbookmarks:")
for nome in re.findall(r'<w:bookmarkStart [^>]*w:name="([^"]+)"', xml)[:20]:
    print("  ", nome)
