"""Converte referências genéricas somente usando sua oferta original comprovada."""
import re
import json
from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace
from sqlalchemy.exc import SQLAlchemyError
from models import PlacaVideo, Oferta
from .aplicar_revisao_identidade_service import AplicarRevisaoIdentidadeService
from utils.identidade_peca import assinatura_tecnica
from services.catalogo_service.normalizar_produto import variante, nome
from services.catalogo_service.conferir_especificacoes_service import ConferirEspecificacoesService
from services.catalogo_service.enriquecer_peca_existente_service import EnriquecerPecaExistenteService
from .normalizar_ficha_kabum_service import NormalizarFichaKabumService


class ConverterReferenciasGpuService:
    @staticmethod
    def generica(peca):
        if peca.fabricante.casefold() not in {'nvidia','amd','intel'} or peca.modelo_referencia:
            return False
        texto = nome(peca.modelo)
        texto = re.sub(r'\b(?:geforce|radeon|nvidia|amd|intel)\b', '', texto)
        return bool(re.fullmatch(r'\s*(?:rtx|gtx|rx|arc)\s*[a-z]?\d{3,4}(?:\s*(?:ti|super|xt|xtx)){0,2}\s*', texto))

    def preparar(self, peca, produto):
        if not self.generica(peca):return dict(status='inalterada')
        if not Oferta.corresponde_origem(peca, produto.loja, produto.id_externo):
            return dict(status='revisao',motivo='Oferta original não comprovada')
        referencia = variante('placa_video', peca.modelo)
        remoto = variante('placa_video', produto.titulo)
        if not referencia or referencia != remoto:
            return dict(status='revisao',motivo='Chip ou sufixo diverge da referência')
        if bool(re.search(r'\b(?:notebook|laptop|mobile)\b',nome(peca.modelo))) != bool(re.search(r'\b(?:notebook|laptop|mobile)\b',nome(produto.titulo))):
            return dict(status='revisao',motivo='Desktop e notebook divergentes')
        proxy = SimpleNamespace(__tablename__='placa_video',__table__=peca.__table__,
            **{c.name:getattr(peca,c.name) for c in peca.__table__.columns})
        proxy.fabricante = produto.marca or ''
        memoria = ConferirEspecificacoesService().executar(proxy,produto)
        if not memoria['completa'] or memoria['conflitos']:
            return dict(status='revisao',motivo='Memória ou tipo de memória não comprovado',conflitos=memoria['conflitos'])
        preparo = EnriquecerPecaExistenteService().preparar(proxy,produto)
        codigo = preparo.get('dados',{}).get('codigo_modelo_fabricante')
        if preparo['status'] != 'proposta' or not codigo:
            return dict(status='revisao',motivo='Modelo comercial exato não comprovado na fonte original')
        modelo = f'{peca.modelo} {codigo}'
        if len(modelo)>120 or not produto.marca or len(produto.marca)>30:
            return dict(status='revisao',motivo='Identidade comercial excede o limite do cadastro')
        return dict(status='proposta',assinatura_tecnica=assinatura_tecnica(peca),
            dados=dict(fabricante=produto.marca,modelo=modelo,fabricante_chip=peca.fabricante,
                modelo_referencia=peca.modelo,codigo_modelo_fabricante=codigo),
            fontes={'codigo_modelo_fabricante':preparo['fontes']['codigo_modelo_fabricante']},
            sha256=preparo['sha256'],titulo_origem=produto.titulo,fonte=produto.fonte,
            evidencias=dict(chip=referencia,especificacoes_conferidas=memoria['conferidos'],oferta_original=produto.id_externo))

    def executar(self,pasta,*,simular=True):
        pasta=Path(pasta)
        if not pasta.is_dir():raise ValueError('Pasta de fichas inexistente')
        resumo=dict(simulacao=simular,propostas=0,convertidas=0,inalteradas=0,revisao=0,falhas=0,detalhes=[])
        cursor=0
        while True:
            lote=PlacaVideo.lote_para_identificadores(cursor,100)
            if not lote:break
            for p in lote:
                cursor=p.id
                try:
                    if not self.generica(p):resumo['inalteradas']+=1;continue
                    from models.medidas_fisicas import produto_kabum
                    ident=produto_kabum(p.kabum_external);arquivo=pasta/f'kabum-{ident}.json'
                    if not ident or not arquivo.is_file():
                        resultado=dict(status='revisao',motivo='Ficha original ausente')
                    else:
                        if arquivo.stat().st_size>4_000_000:raise ValueError('Arquivo excessivo')
                        dto=NormalizarFichaKabumService().executar(json.loads(arquivo.read_text()),'placa_video',codigo_esperado=ident)
                        dto=replace(dto,contexto={**dto.contexto,'origem_peca':f'placa_video:{p.id}'})
                        proposta=self.preparar(p,dto)
                        resultado=AplicarRevisaoIdentidadeService().executar(p,proposta,simular=simular) if proposta['status']=='proposta' else proposta
                    chave={'proposta':'propostas','convertida':'convertidas','inalterada':'inalteradas'}.get(resultado['status'],resultado['status'])
                    resumo[chave]+=1;resumo['detalhes'].append({'peca':f'placa_video:{cursor}',**resultado})
                except (ValueError,TypeError,OSError,SQLAlchemyError):
                    from models import db
                    db.session.rollback();resumo['revisao']+=1
                    resumo['detalhes'].append(dict(peca=f'placa_video:{cursor}',status='revisao',motivo='Conversão não confirmada; confira a identidade e os vínculos existentes'))
        return resumo
