"""Uma etapa limitada por ciclo, com agenda, exclusão mútua e checkpoint no banco."""
import json
import math
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from threading import Event
from models import db, EstadoCatalogo, ProdutoPendente
from repositories.controle_catalogo_repository import RepositorioControleCatalogo
from services.peca_service.modelos_pecas import MODELOS_PECAS
from .controle_requisicoes_service import ControleRequisicoesService, OrcamentoRequisicoesEsgotado
from .descobrir_produtos_service import DescobrirProdutosService
from .classificar_pendencias_service import ClassificarPendenciasService
from .enriquecer_pendencias_service import EnriquecerPendenciasService
from .importar_produto_service import ImportarProdutoService

FASES=('descoberta','classificacao','enriquecimento','importacao')


class ControleRequisicoesCatalogo(ControleRequisicoesService):
    def __init__(self, limite, intervalo, verificar, parada):
        super().__init__(limite,intervalo)
        self.verificar=verificar;self.parada=parada

    def executar(self, chamada):
        def protegida():
            self.verificar()
            if self.parada.is_set():raise OrcamentoRequisicoesEsgotado('Parada solicitada')
            resultado=chamada();self.verificar()
            return resultado
        return super().executar(protegida)


class ProcessarCatalogoService:
    def __init__(self, repositorio=None, parada=None):
        self.repositorio=repositorio or RepositorioControleCatalogo()
        self.parada=parada or Event()

    @staticmethod
    def ler_plano(caminho):
        try:
            p=Path(caminho)
            if p.stat().st_size>524288:raise ValueError('Plano excede 512 KB')
            plano=json.loads(p.read_text())
        except (OSError,UnicodeError,json.JSONDecodeError):raise ValueError('Não foi possível ler o plano de catálogo') from None
        if not isinstance(plano,dict) or plano.get('versao')!=1 or not isinstance(plano.get('trabalhos'),list) or not 1<=len(plano['trabalhos'])<=1000:
            raise ValueError('Plano deve ter versão 1 e entre 1 e 1000 trabalhos')
        nomes=set();categorias={m.__tablename__ for m in MODELOS_PECAS}
        for trabalho in plano['trabalhos']:
            if not isinstance(trabalho,dict):raise ValueError('Trabalho inválido')
            permitidos={'nome','categoria','consulta','origem','categoria_ml','dominio','periodo_segundos','max_paginas','max_anuncios','limite_fila','max_requisicoes','intervalo','max_produtos','max_ofertas_por_produto','marca'}
            if set(trabalho)-permitidos:raise ValueError('Parâmetro desconhecido no plano')
            if not isinstance(trabalho.get('nome'),str) or not 1<=len(trabalho['nome'])<=80 or trabalho['nome'] in nomes:raise ValueError('Nome de trabalho ausente ou duplicado')
            if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}',trabalho['nome']):raise ValueError('Nome de trabalho deve usar letras minúsculas, números, hífen e sublinhado')
            nomes.add(trabalho['nome'])
            if trabalho.get('categoria') not in categorias or not isinstance(trabalho.get('consulta'),str) or not 2<=len(trabalho['consulta'].strip())<=150:raise ValueError('Categoria ou consulta inválida')
            if trabalho.get('origem','catalogo') not in ('catalogo','anuncios'):raise ValueError('Origem inválida')
            if any(ord(c)<32 for c in trabalho['consulta']):raise ValueError('Consulta contém caracteres inválidos')
            origem=trabalho.get('origem','catalogo')
            if trabalho.get('categoria_ml') is not None and (origem!='anuncios' or not isinstance(trabalho['categoria_ml'],str) or not re.fullmatch(r'MLB[0-9]+',trabalho['categoria_ml'])):raise ValueError('Categoria oficial inválida')
            if trabalho.get('dominio') is not None and (origem!='catalogo' or not isinstance(trabalho['dominio'],str) or not re.fullmatch(r'MLB-[A-Z0-9_]+',trabalho['dominio'])):raise ValueError('Domínio inválido')
            for campo,padrao,minimo,maximo in [('periodo_segundos',3600,300,86400),('max_paginas',3,1,20),('max_anuncios',50,1,500),('limite_fila',10,1,50),('max_requisicoes',30,1,200)]:
                valor=trabalho.get(campo,padrao)
                if type(valor) is not int or not minimo<=valor<=maximo:raise ValueError('Limite inválido no plano: '+campo)
                trabalho[campo]=valor
            marca = trabalho.get('marca')
            if marca is not None and (origem != 'catalogo' or not isinstance(marca, str) or not 1 <= len(marca.strip()) <= 80 or any(ord(c) < 32 for c in marca)):
                raise ValueError('Marca de pesquisa inválida')
            for campo in ('max_produtos', 'max_ofertas_por_produto'):
                valor = trabalho.get(campo)
                if valor is not None and (origem != 'catalogo' or type(valor) is not int or not 1 <= valor <= 1000):
                    raise ValueError('Limite de catálogo inválido: ' + campo)
            intervalo=trabalho.get('intervalo',1.0)
            if type(intervalo) not in (int,float) or not math.isfinite(intervalo) or intervalo<0.1:raise ValueError('Intervalo inválido')
            trabalho['intervalo']=intervalo
        return plano['trabalhos']

    def executar(self, trabalhos, *, simular=True, permitir_novos=False):
        with self.repositorio.bloquear() as adquirido:
            if not adquirido:return {'status':'ocupado'}
            self.repositorio.verificar()
            self.repositorio.verificar_esquema(trabalhos)
            agora=datetime.now(timezone.utc).replace(tzinfo=None)
            estados=[(EstadoCatalogo.obter(t,simular=simular),t) for t in trabalhos]
            agora=datetime.now(timezone.utc).replace(tzinfo=None)
            prontos=sorted(((e,t) for e,t in estados if e.proxima_execucao<=agora),key=lambda x:(x[0].proxima_execucao,x[0].nome))
            if not prontos:return {'status':'aguardando'}
            estado,trabalho=prontos[0];fase=estado.fase
            controle=ControleRequisicoesCatalogo(trabalho['max_requisicoes'],trabalho['intervalo'],self.repositorio.verificar,self.parada)
            campos={};resumo={};falhou=False
            try:
                if fase=='descoberta':
                    opcoes={k:trabalho[k] for k in ('categoria','consulta','origem','categoria_ml','dominio','max_paginas','max_anuncios','max_requisicoes','intervalo','max_produtos','max_ofertas_por_produto','marca') if k in trabalho}
                    resumo=DescobrirProdutosService(controle=controle).executar(**opcoes,simular=simular,cursor=estado.cursor_descoberta)
                    campos['cursor_descoberta']=resumo['cursor']
                    terminou=resumo['concluido']
                else:
                    ids=[p.id for p in ProdutoPendente.listar_para_revisao(estado.cursor_fila,trabalho['limite_fila'],trabalho['categoria'])]
                    opcoes=dict(limite=trabalho['limite_fila'],depois_id=estado.cursor_fila,categoria=trabalho['categoria'],simular=simular)
                    if fase=='classificacao':resumo=ClassificarPendenciasService().executar(**opcoes)
                    elif fase=='enriquecimento':resumo=EnriquecerPendenciasService(controle=controle).executar(**opcoes)
                    else:resumo=ImportarProdutoService(controle=controle,verificar_execucao=self.repositorio.verificar).executar_lote(**opcoes,permitir_novos=permitir_novos)
                    campos['cursor_fila']=max(ids) if ids else estado.cursor_fila
                    terminou=len(ids)<trabalho['limite_fila']
                falhou=bool(resumo.get('interrompido') or resumo.get('falhas'))
            except Exception as erro:
                db.session.rollback();falhou=True;terminou=False
                resumo={'falhas':1,'erro':'Etapa interrompida; confira esquema, acesso e evidências','tipo':type(erro).__name__}
            self.repositorio.verificar()
            agora=datetime.now(timezone.utc).replace(tzinfo=None)
            if falhou:
                tentativas=estado.tentativas+1
                espera=trabalho['periodo_segundos'] if tentativas>=3 else 60*(2**(tentativas-1))
                campos.pop('cursor_fila',None)
                campos.update(tentativas=min(tentativas,3),proxima_execucao=agora+timedelta(seconds=espera))
            else:
                campos.update(tentativas=0,proxima_execucao=agora+timedelta(seconds=1))
                if terminou:
                    if fase=='importacao':
                        campos.update(fase='descoberta',cursor_descoberta=None,cursor_fila=0,
                                      proxima_execucao=agora+timedelta(seconds=trabalho['periodo_segundos']))
                    else:campos.update(fase=FASES[FASES.index(fase)+1],cursor_fila=0)
            compacto={k:v for k,v in resumo.items() if k not in ('cursor','detalhes')}
            campos['ultimo_resumo']=compacto
            if not simular:estado.registrar_progresso(**campos)
            else:db.session.rollback()
            return dict(status='falha' if falhou else 'concluido',trabalho=trabalho['nome'],fase=fase,
                        proxima_fase=campos.get('fase',fase),resumo=compacto)
