#!/usr/bin/env python3
"""html_a_texto.py — Convierte HTML crudo del Gestor CRA a texto tipo web_fetch.

Uso: python3 html_a_texto.py <entrada.html> <salida.txt>

Motivacion: web_fetch trunca paginas grandes del gestor (~50-70 KB de texto).
Este conversor extrae el texto completo del HTML crudo (ISO-8859-1) con una
salida deliberadamente similar a la de web_fetch (enlaces como [texto](href),
imagenes como ![alt](src), un elemento de bloque por linea) para que el
limpiador de verificar_fuente.py se comporte igual en ambos lados.
"""
import html as html_mod
import re
import sys
from html.parser import HTMLParser

BLOCK = {"p", "div", "li", "tr", "td", "th", "table", "ul", "ol", "h1", "h2",
         "h3", "h4", "h5", "h6", "hr", "section", "article", "header", "footer",
         "nav", "blockquote", "pre", "form", "fieldset", "figcaption"}
SKIP = {"script", "style", "head", "noscript", "iframe", "svg"}
VOID = {"br", "img", "hr", "meta", "link", "base", "input", "col", "wbr",
        "embed", "source", "track", "area", "param"}


class GestorHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes = []        # fragmentos con marcas de newline
        self.stack = []         # pila de etiquetas abiertas
        self.saltar = 0         # profundidad dentro de bloques SKIP
        self.href_stack = []    # (etiqueta, href, img_alt) pendientes
        self.linkeando = None   # dict para el <a> abierto mas cercano
        self.img_alt = None

    def _nl(self, n=1):
        self.partes.append("\n" * n)

    def handle_startendtag(self, tag, attrs):
        # elementos void (<br/>, <img/>, <meta/>): sin pareja de cierre
        self.handle_starttag(tag, attrs)
        tag = tag.lower()
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = dict(attrs)
        if tag in VOID:
            if tag == "br":
                self._nl(1)
            elif tag == "img":
                src = a.get("src", "")
                alt = a.get("alt", "")
                if src:
                    self.partes.append(f"![{alt}]({src})")
            return
        if tag in SKIP:
            self.saltar += 1
            return
        if self.saltar:
            return
        if tag == "a":
            self.linkeando = {"href": a.get("href", ""), "buf": []}
        if tag == "b" or tag == "strong":
            self.partes.append("**")
        if tag == "i" or tag == "em":
            self.partes.append("*")
        if tag in BLOCK:
            self._nl(1)
        self.stack.append(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in SKIP:
            if self.saltar:
                self.saltar -= 1
            return
        if self.saltar:
            return
        if tag == "a" and self.linkeando is not None:
            texto = "".join(self.linkeando["buf"]).strip()
            href = self.linkeando["href"]
            if href and texto:
                self.partes.append(f"[{texto}]({href})")
            elif texto:
                self.partes.append(texto)
            self.linkeando = None
        if tag == "b" or tag == "strong":
            self.partes.append("**")
        if tag == "i" or tag == "em":
            self.partes.append("*")
        if tag in BLOCK:
            self._nl(1)
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_data(self, data):
        if self.saltar:
            return
        if self.linkeando is not None:
            self.linkeando["buf"].append(data)
        else:
            self.partes.append(data)


def main():
    entrada, salida = sys.argv[1], sys.argv[2]
    raw = open(entrada, "rb").read()
    for codec in ("iso-8859-1", "utf-8"):
        try:
            doc = raw.decode(codec)
            break
        except UnicodeDecodeError:
            continue
    else:
        doc = raw.decode("iso-8859-1", errors="replace")
    p = GestorHTML()
    p.feed(doc)
    p.close()
    texto = html_mod.unescape("".join(p.partes))
    # normalizar: colapsar espacios en blanco por linea, lineas vacias a una
    lineas = []
    for ln in texto.split("\n"):
        ln = re.sub(r"[ \t ]+", " ", ln).strip()
        lineas.append(ln)
    out, prev_vacia = [], False
    for ln in lineas:
        vacia = not ln
        if vacia and prev_vacia:
            continue
        out.append(ln)
        prev_vacia = vacia
    while out and not out[0]:
        out.pop(0)
    while out and not out[-1]:
        out.pop()
    open(salida, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(f"OK {entrada} -> {salida} ({len(out)} lineas)")


if __name__ == "__main__":
    main()
