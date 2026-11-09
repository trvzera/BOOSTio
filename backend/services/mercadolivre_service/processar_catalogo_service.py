"""Uma etapa limitada por ciclo, com agenda, exclusão mútua e checkpoint no banco."""
from datetime import datetime, timezone, timedelta
from threading import Event
from models import db, EstadoCatalogo, ProdutoPendente
from repositories.controle_catalogo_repository import RepositorioControleCatalogo
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
