"""HTTP limitado aos fabricantes cadastrados, com cache e respeito ao robots.txt."""
import hashlib
import json
from pathlib import Path
import tempfile
import os
import time
from urllib.parse import urlsplit, urljoin
from urllib.robotparser import RobotFileParser
import requests

DOMINIOS = {'amd':'www.amd.com', 'corsair':'www.corsair.com',
            'crucial':'www.crucial.com', 'logitech':'www.logitechg.com'}


class ConsultarPaginasFabricanteService:
    def __init__(self, pasta, limite=48, intervalo=2.0):
        self.pasta = Path(pasta)
        self.limite = limite
        self.intervalo = max(1.0, intervalo)
        self.requisicoes = 0
        self.ultima = 0
        self.robos = {}

    @staticmethod
    def validar(url, fabricante):
        p = urlsplit(url)
        if p.scheme != 'https' or p.hostname != DOMINIOS.get(fabricante) or p.username or p.password or p.port not in (None,443):
            raise ValueError('URL fora do domínio oficial permitido')

    def executar(self, url, fabricante, *, robots=False):
        self.validar(url, fabricante)
        espera=self.intervalo
        if not robots:
            regras = self.regras(fabricante)
            if not regras.can_fetch('BOOSTioCatalogo', url):
                raise ValueError('Coleta recusada pelas regras do fabricante')
            espera=max(espera,regras.crawl_delay('BOOSTioCatalogo') or 0)
            taxa=regras.request_rate('BOOSTioCatalogo')
            if taxa and taxa.requests>0:espera=max(espera,taxa.seconds/taxa.requests)
            if espera>60:raise ValueError('Fabricante exige intervalo maior; reagendar consulta')
        chave = hashlib.sha256(url.encode()).hexdigest()
        caminho = self.pasta / (chave+'.json')
        if caminho.is_file() and time.time()-caminho.stat().st_mtime < 7*86400:
            cache = json.loads(caminho.read_text())
            if cache.get('url') == url:
                return cache['texto']
        if self.requisicoes >= self.limite:
            raise ValueError('Limite de consultas a fabricantes atingido')
        time.sleep(max(0,espera-(time.monotonic()-self.ultima)))
        self.ultima = time.monotonic()
        self.requisicoes += 1
        try:
            with requests.get(url,timeout=(5,15),stream=True,allow_redirects=False,
                              headers={'User-Agent':'BOOSTioCatalogo/1.0'}) as resposta:
                if resposta.status_code in (301,302,303,307,308):
                    destino=urljoin(url,resposta.headers.get('Location',''))
                    self.validar(destino,fabricante)
                    raise ValueError('Página oficial mudou de endereço; atualizar índice de descoberta')
                if resposta.status_code != 200:
                    raise ValueError(f'Fabricante HTTP {resposta.status_code}')
                tipo=resposta.headers.get('Content-Type','').lower()
                if not any(v in tipo for v in ('text/','xml','json')):
                    raise ValueError('Formato inesperado na fonte oficial')
                corpo=bytearray()
                for bloco in resposta.iter_content(65536):
                    corpo.extend(bloco)
                    if len(corpo)>16_000_000:
                        raise ValueError('Página ou sitemap excede 16 MB')
                texto=bytes(corpo).decode('utf-8',errors='replace')
        except requests.RequestException:
            raise ValueError('Falha de conexão com fabricante') from None
        if any(v in texto[:2000].lower() for v in ('request rejected','access denied','captcha')):
            raise ValueError('Fabricante bloqueou a consulta')
        self.pasta.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(dir=self.pasta,prefix='.pagina-')
        try:
            with os.fdopen(fd,'w') as f:json.dump({'url':url,'texto':texto},f)
            os.replace(tmp,caminho)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
        return texto

    def regras(self, fabricante):
        if fabricante not in self.robos:
            url='https://'+DOMINIOS[fabricante]+'/robots.txt'
            texto=self.executar(url,fabricante,robots=True)
            parser=RobotFileParser(url);parser.parse(texto.splitlines())
            self.robos[fabricante]=parser
        return self.robos[fabricante]
