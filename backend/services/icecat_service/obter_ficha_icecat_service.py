import os
from pathlib import Path
import re
import tempfile
import time
import requests


class ErroConsultaIcecat(ValueError):
    def __init__(self, mensagem, status=None):
        self.status = status
        super().__init__(mensagem)


class ObterFichaIcecatService:
    def __init__(self, pasta, usuario=None, senha=None, intervalo=1.0, max_requisicoes=20):
        self.pasta = Path(pasta)
        self.usuario = usuario
        self.senha = senha
        self.intervalo = max(1.0, float(intervalo))
        self.max_requisicoes = max_requisicoes
        self.requisicoes = 0
        self.ultima = 0

    def executar(self, referencia):
        identificador = referencia['id']
        atualizado = referencia.get('atualizado', '')
        if not re.fullmatch(r'\d+', identificador) or not re.fullmatch(r'\d{14}', atualizado):
            raise ValueError('Referência Icecat inválida')
        caminho = self.pasta / f'{identificador}-{atualizado}.xml'
        if caminho.is_file():
            if caminho.stat().st_size > 2_000_000:
                raise ValueError('Ficha Icecat excede 2 MB')
            return caminho.read_bytes()
        if not self.usuario or not self.senha:
            raise ErroConsultaIcecat('Configure ICECAT_USUARIO e ICECAT_SENHA ou forneça a ficha local')
        if self.requisicoes >= self.max_requisicoes:
            raise ErroConsultaIcecat('Limite de consultas Icecat atingido; retome o lote depois')
        time.sleep(max(0, self.intervalo - (time.monotonic() - self.ultima)))
        self.ultima = time.monotonic()
        self.requisicoes += 1
        url = f'https://data.icecat.biz/export/freexml/EN/{identificador}.xml'
        try:
            with requests.get(url, auth=(self.usuario, self.senha), timeout=(10, 30),
                              stream=True, allow_redirects=False) as resposta:
                if resposta.status_code != 200:
                    raise ErroConsultaIcecat(f'Icecat HTTP {resposta.status_code}; consulta não concluída', resposta.status_code)
                if 'xml' not in resposta.headers.get('Content-Type', '').lower():
                    raise ValueError('Icecat retornou formato inesperado')
                corpo = bytearray()
                for bloco in resposta.iter_content(65536):
                    corpo.extend(bloco)
                    if len(corpo) > 2_000_000:
                        raise ValueError('Ficha Icecat excede 2 MB')
        except requests.RequestException:
            raise ErroConsultaIcecat('Falha de comunicação com Icecat') from None
        from defusedxml.ElementTree import fromstring
        from defusedxml.common import DefusedXmlException
        from xml.etree.ElementTree import ParseError
        try:
            raiz = fromstring(bytes(corpo))
        except (DefusedXmlException, ParseError):
            raise ValueError('XML Icecat inválido ou inseguro') from None
        produto = raiz.find('Product')
        if produto is None or produto.get('ID') != identificador:
            raise ValueError('Resposta Icecat sem ficha técnica')
        self.pasta.mkdir(parents=True, exist_ok=True)
        descriptor, temporario = tempfile.mkstemp(dir=self.pasta, prefix='.ficha-')
        try:
            with os.fdopen(descriptor, 'wb') as arquivo:
                arquivo.write(corpo)
            os.replace(temporario, caminho)
        finally:
            if os.path.exists(temporario):
                os.unlink(temporario)
        return bytes(corpo)
