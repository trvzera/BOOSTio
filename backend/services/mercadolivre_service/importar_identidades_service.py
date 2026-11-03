"""Importação de um manifesto revisado, sem inferência de códigos por nome."""
import json
from pathlib import Path
from urllib.parse import urlsplit

from models import IdentidadeFabricante
from services.peca_service.modelos_pecas import MODELOS_PECAS
from services.preco_service.validar_link_service import ValidarLinkService


class ImportarIdentidadesService:
    def executar(self, arquivo, *, simular=True):
        try:
            caminho = Path(arquivo)
            if caminho.stat().st_size > 2_000_000:
                raise ValueError('Manifesto excede 2 MB')
            dados = json.loads(caminho.read_text(encoding='utf-8'))
        except (OSError, UnicodeError, json.JSONDecodeError) as erro:
            raise ValueError('Não foi possível ler o manifesto de identidades') from erro
        if not isinstance(dados, list) or len(dados) > 5000:
            raise ValueError('Manifesto deve conter uma lista de até 5000 identidades')
        modelos = {m.__tablename__: m for m in MODELOS_PECAS}
        vistos = set()
        # Valida todo o formato e duplicatas antes da primeira gravação.
        for item in dados:
            if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k].strip() for k in
                    ('categoria', 'referencia', 'fabricante', 'modelo', 'mpn', 'fonte', 'url_peca')):
                raise ValueError('Identidade incompleta')
            if item['categoria'] not in modelos or len(item['mpn']) > 255:
                raise ValueError('Categoria ou MPN inválido')
            from .identidade_produto import gtin
            if item.get('gtin') is not None and gtin(item['gtin']) is None:
                raise ValueError('GTIN inválido; não foi inferido ou corrigido')
            url = urlsplit(item['fonte'])
            if url.scheme != 'https' or not url.hostname or url.username or url.password:
                raise ValueError('Fonte deve ser uma URL HTTPS pública')
            ValidarLinkService().codigo_produto(item['url_peca'])
            specs = item.get('especificacoes')
            if not isinstance(specs, dict) or not specs or any(k not in modelos[item['categoria']].__table__.columns for k in specs):
                raise ValueError('Especificações de conferência inválidas')
            chave = (item['categoria'], item['referencia'])
            if chave in vistos:
                raise ValueError('Referência duplicada no manifesto')
            vistos.add(chave)
        resumo = dict(simulacao=simular, propostas=0, cadastradas=0, inalteradas=0, revisao=0, detalhes=[])
        for item in dados:
            detalhe = {k: item[k] for k in ('categoria', 'referencia', 'mpn')}
            pecas = IdentidadeFabricante.localizar(modelos[item['categoria']], item['referencia'], item['fabricante'], item['modelo'])
            try:
                if len(pecas) != 1:
                    raise ValueError('Peça ausente ou ambígua no banco')
                peca = pecas[0]
                if ValidarLinkService().codigo_produto(peca.kabum_external) != ValidarLinkService().codigo_produto(item['url_peca']):
                    raise ValueError('Produto da loja diverge do registro revisado')
                acao = IdentidadeFabricante.registrar(peca, item['mpn'], item['fonte'], item['especificacoes'], simular=simular, gtin=item.get('gtin'))
                resumo[{'proposta': 'propostas', 'cadastrada': 'cadastradas', 'inalterada': 'inalteradas'}[acao]] += 1
                detalhe['status'] = acao
            except ValueError as erro:
                resumo['revisao'] += 1
                detalhe.update(status='revisao', motivo=str(erro))
            resumo['detalhes'].append(detalhe)
        return resumo
