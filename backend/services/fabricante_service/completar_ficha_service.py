import os
import re
from types import SimpleNamespace
from services.catalogo_service.comparar_nomes_service import marca
from services.catalogo_service.normalizar_produto import nome
from services.catalogo_service.associacao_inteligente_service import AssociacaoInteligenteService
from services.catalogo_service.mesclar_ficha_tecnica_service import MesclarFichaTecnicaService
from .consultar_paginas_service import ConsultarPaginasFabricanteService
from .descobrir_ficha_service import DescobrirFichaFabricanteService
from .normalizar_ficha_service import NormalizarFichaFabricanteService


class CompletarFichaFabricanteService:
    def __init__(self,paginas):
        self.paginas=paginas

    @classmethod
    def configurado(cls):
        if os.getenv('FABRICANTES_HABILITADOS','').lower()!='true':return None
        return cls(ConsultarPaginasFabricanteService(os.getenv('FABRICANTES_CACHE','/tmp/boostio-fabricantes')))

    def executar(self,produto,ficha):
        fabricante=marca(produto.marca or '')
        if fabricante not in ('amd','corsair','crucial','logitech'):
            candidatos=[v for v in ('amd','corsair','crucial','logitech') if re.search(r'\b'+v+r'\b',nome(produto.titulo))]
            if len(candidatos)!=1:
                return produto,{**ficha,'fabricante_oficial':dict(status='revisao',motivo='fabricante_divergente_ou_nao_suportado',candidatos=candidatos)}
            fabricante=candidatos[0]
        try:
            urls=DescobrirFichaFabricanteService(self.paginas).executar(fabricante,produto)
            if not urls:
                return produto,{**ficha,'fabricante_oficial':dict(status='pendente',motivo='pagina_oficial_nao_localizada')}
            candidatas=[];diagnosticos=[]
            for url in urls:
                html=self.paginas.executar(url,fabricante)
                try:
                    tecnica=NormalizarFichaFabricanteService().executar(html,url,fabricante,produto)
                except ValueError:
                    diagnosticos.append(dict(url=url,classificacao='revisao',conflitos=['ficha_nao_confirmada']))
                    continue
                proxy=SimpleNamespace(__tablename__=produto.categoria,id=0,
                    part_number=tecnica['identidade']['mpn'],**tecnica['dados'])
                decisao=AssociacaoInteligenteService().avaliar(proxy,produto,identidade=tecnica['identidade'])
                diagnosticos.append(dict(url=url,classificacao=decisao['classificacao'],conflitos=decisao['conflitos']))
                if decisao['classificacao']=='confirmada':candidatas.append(tecnica)
            if len(candidatas)!=1 or any(d['classificacao'] in ('ambigua','revisao') for d in diagnosticos):
                return produto,{**ficha,'fabricante_oficial':dict(status='revisao',paginas=diagnosticos)}
            produto,nova=MesclarFichaTecnicaService().executar(produto,ficha,candidatas[0])
            nova['fabricante_oficial']=dict(status='encontrada',fabricante=fabricante,url=candidatas[0]['fonte_identidade'],paginas=diagnosticos,
                especificacoes_originais=candidatas[0].get('especificacoes_originais',{}))
            return produto,nova
        except (ValueError,OSError) as erro:
            return produto,{**ficha,'fabricante_oficial':dict(status='pendente',motivo=str(erro))}
