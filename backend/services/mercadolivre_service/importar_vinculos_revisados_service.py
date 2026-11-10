"""Aplica decisões humanas versionadas, sem descoberta por semelhança."""
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from models import IdentidadeFabricante, VinculoMercadoLivre
from models.modelos_pecas import MODELOS_PECAS
from services.preco_service.validar_link_service import ValidarLinkService
from utils.identidade_peca import assinatura_peca, assinatura_catalogo

MANIFESTO = Path(__file__).resolve().parents[2] / 'data' / 'vinculos-mercadolivre-revisados.json'


class ImportarVinculosRevisadosService:
    def executar(self, arquivo=MANIFESTO, *, simular=True):
        try:
            caminho=Path(arquivo)
            if caminho.stat().st_size > 32_000_000:
                raise ValueError('Manifesto excede 32 MB')
            dados=json.loads(caminho.read_text(encoding='utf-8'))
        except (OSError, UnicodeError, json.JSONDecodeError):
            raise ValueError('Não foi possível ler o manifesto revisado') from None
        if not isinstance(dados,list) or len(dados)>5000:
            raise ValueError('Manifesto deve conter até 5000 vínculos')
        modelos={m.__tablename__:m for m in MODELOS_PECAS}
        vistos, catalogos=set(),set()
        # Validar todo o formato antes de gravar a primeira peça.
        for item in dados:
            self._validar(item, modelos)
            chave=(item['categoria'],item['referencia'])
            id=item['catalogo']['id']
            if chave in vistos or id in catalogos:
                raise ValueError('Peça ou catálogo duplicado no manifesto')
            vistos.add(chave);catalogos.add(id)
        resumo=dict(simulacao=simular,propostos=0,cadastrados=0,inalterados=0,revisao=0,detalhes=[])
        for item in dados:
            produto=item['catalogo']
            detalhe=dict(categoria=item['categoria'],referencia=item['referencia'],catalogo_id=produto['id'])
            try:
                pecas=IdentidadeFabricante.localizar(modelos[item['categoria']],item['referencia'],item['fabricante'],item['modelo'])
                if len(pecas)!=1:
                    raise ValueError('Peça ausente ou ambígua; nenhuma peça será criada')
                peca=pecas[0]
                if ValidarLinkService().codigo_produto(peca.kabum_external)!=ValidarLinkService().codigo_produto(item['url_peca']):
                    raise ValueError('Produto de origem difere da revisão')
                if not IdentidadeFabricante._conferem(peca,item['especificacoes']):
                    divergentes=[k for k,v in item['especificacoes'].items() if not IdentidadeFabricante._conferem(peca,{k:v})]
                    raise ValueError('Especificações divergentes: '+', '.join(divergentes))
                acao=VinculoMercadoLivre.aplicar_revisado(peca,produto['id'],assinatura_peca(peca),
                    assinatura_catalogo(produto),item['especificacoes'],simular=simular)
                resumo[{'proposto':'propostos','cadastrado':'cadastrados','inalterado':'inalterados'}[acao]]+=1
                detalhe['status']=acao
            except ValueError as erro:
                resumo['revisao']+=1;detalhe.update(status='revisao',motivo=str(erro))
            resumo['detalhes'].append(detalhe)
        return resumo

    @staticmethod
    def _validar(item,modelos):
        if not isinstance(item,dict) or not all(isinstance(item.get(k),str) and item[k].strip() for k in
                ('categoria','referencia','fabricante','modelo','url_peca','revisado_em','justificativa')):
            raise ValueError('Vínculo revisado incompleto')
        if item['categoria'] not in modelos:
            raise ValueError('Categoria inválida')
        from datetime import date
        try:date.fromisoformat(item['revisado_em'])
        except ValueError:raise ValueError('Data de revisão inválida') from None
        ValidarLinkService().codigo_produto(item['url_peca'])
        specs=item.get('especificacoes')
        if not isinstance(specs,dict) or not specs or any(k not in modelos[item['categoria']].__table__.columns for k in specs):
            raise ValueError('Especificações revisadas inválidas')
        produto=item.get('catalogo')
        if (not isinstance(produto,dict) or not isinstance(produto.get('id'),str) or not re.fullmatch(r'MLB[0-9]+',produto['id'])
                or not isinstance(produto.get('name'),str) or not produto['name'].strip()
                or not isinstance(produto.get('domain_id'),str) or not isinstance(produto.get('attributes'),list)):
            raise ValueError('Snapshot do catálogo inválido')
        evidencias=item.get('evidencias')
        if not isinstance(evidencias,list) or not evidencias:
            raise ValueError('Informe evidências da revisão')
        for fonte in evidencias:
            if not isinstance(fonte,str):raise ValueError('Fonte inválida')
            url=urlsplit(fonte)
            if url.scheme!='https' or not url.hostname or url.username or url.password:
                raise ValueError('Fonte deve usar HTTPS')
