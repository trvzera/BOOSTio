from html.parser import HTMLParser


class _ScriptsJson(HTMLParser):
    def __init__(self):
        super().__init__(); self.ler = False; self.partes = []; self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') in ('application/json', 'application/ld+json'):
            self.ler = True; self.partes = []

    def handle_data(self, texto):
        if self.ler:
            self.partes.append(texto)

    def handle_endtag(self, tag):
        if tag == 'script' and self.ler:
            self.scripts.append(''.join(self.partes)); self.ler = False
