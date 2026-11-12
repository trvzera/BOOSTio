"""Junta os @import de styles/style.css em um único arquivo (usado no build da imagem do frontend)."""
import posixpath
import re
import sys
from pathlib import Path

IMPORT = re.compile(r'@import\s+(?:url\()?["\']([^"\']+)["\']\)?\s*;')
URL = re.compile(r'url\(\s*(["\']?)([^)"\']+)\1\s*\)')


def ajustar_urls(css, pasta, raiz):
    def trocar(achado):
        caminho = achado.group(2)
        if caminho.startswith(("data:", "http", "/", "#")):
            return achado.group(0)
        destino = posixpath.relpath(posixpath.normpath(posixpath.join(pasta, caminho)), raiz)
        return f'url("{destino}")'
    return URL.sub(trocar, css)


def juntar(arquivo, raiz):
    pasta = posixpath.dirname(arquivo)
    css = Path(arquivo).read_text(encoding="utf-8")
    partes, fim = [], 0
    for achado in IMPORT.finditer(css):
        partes.append(ajustar_urls(css[fim:achado.start()], pasta, raiz))
        partes.append(juntar(posixpath.normpath(posixpath.join(pasta, achado.group(1))), raiz))
        fim = achado.end()
    partes.append(ajustar_urls(css[fim:], pasta, raiz))
    return "".join(partes)


if __name__ == "__main__":
    principal = sys.argv[1]
    resultado = juntar(principal, posixpath.dirname(principal))
    Path(principal).write_text(resultado, encoding="utf-8")
    print(f"{principal}: {len(resultado) // 1024} KB, {resultado.count('@import')} @import restantes")
