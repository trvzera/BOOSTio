from services.catalogo_service.pendencias_montagem_service import pendencias_para_montagem
"""Recebe o contrato técnico interno; adaptadores externos não pertencem a este núcleo."""
import re
import json
from datetime import datetime
from models import db
from services.peca_service.modelos_pecas import MODELOS_PECAS
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.catalogo_service.validar_ficha_tecnica_service import ValidarFichaTecnicaService
from services.catalogo_service.conferir_especificacoes_service import converter
from services.catalogo_service.normalizar_produto import codigo, gtin
from repositories.catalogo_tecnico_repository import RepositorioCatalogoTecnico
from utils.codigos_peca import codigo_interno
from utils.identidade_peca import assinatura_tecnica

PROTEGIDOS={'id','criado_em','atualizado_em','preco','esgotado','preco_atualizado_em',
    'part_number','referencia_interna','codigo_modelo_fabricante','kabum_external','imagem_url',
    'status_validacao','validacao_motivo','validado_em','fontes_especificacoes','ficha_montagem_validada','fabricante','modelo'}


class ImportarBaseTecnicaService:
    def __init__(self, repositorio=None):self.repositorio=repositorio or RepositorioCatalogoTecnico()

    @staticmethod
    def normalizar(documento):
        from urllib.parse import urlsplit
        if not isinstance(documento,dict) or documento.get('versao')!=1:raise ValueError('Use o contrato técnico interno versão 1')
        try:
            tamanho=len(json.dumps(documento,allow_nan=False,ensure_ascii=False).encode('utf-8'))
        except (ValueError,TypeError):raise ValueError('Documento deve conter apenas valores JSON finitos') from None
        if tamanho>262144:raise ValueError('Documento técnico excede 256 KiB')
        permitidos={'versao','provedor','id_externo','categoria','identidade','especificacoes','fontes','atualizado_na_origem'}
        if set(documento)-permitidos:raise ValueError('Campo desconhecido no documento técnico')
        for campo,limite in [('provedor',60),('id_externo',120),('categoria',40)]:
            v=documento.get(campo)
            if not isinstance(v,str) or not v.strip() or len(v)>limite or any(ord(c)<32 for c in v):raise ValueError('Origem/categoria inválida')
        modelos={m.__tablename__:m for m in MODELOS_PECAS}
        if documento['categoria'] not in modelos:raise ValueError('Categoria desconhecida')
        identidade=documento.get('identidade',{});spec=documento.get('especificacoes',{});fontes=documento.get('fontes',{})
        if not all(isinstance(v,dict) for v in (identidade,spec,fontes)):raise ValueError('Identidade, especificações e fontes devem ser objetos')
        if set(identidade)-{'fabricante','modelo','mpn','gtin'}:raise ValueError('Campo de identidade desconhecido')
        if any(c in PROTEGIDOS or c.startswith('benchmark_') or c not in modelos[documento['categoria']].__table__.columns for c in spec):
            raise ValueError('Campo protegido ou desconhecido nas especificações')
        for origem in fontes.values():
            u=urlsplit(origem.get('url','')) if isinstance(origem,dict) else urlsplit('')
            if u.scheme!='https' or not u.hostname or u.username or u.password:raise ValueError('Fonte técnica precisa de URL HTTPS válida')
        data=documento.get('atualizado_na_origem')
        if data is not None:
            if not isinstance(data,str):raise ValueError('Data da fonte inválida')
            datetime.fromisoformat(data.replace('Z','+00:00'))
        return {**documento,'provedor':documento['provedor'].strip(),'id_externo':documento['id_externo'].strip(),
            'identidade':identidade,'especificacoes':spec,'fontes':fontes}

    def avaliar(self, documento):
        identidade=documento['identidade'];spec=documento['especificacoes'];fontes=documento['fontes']
        faltantes=[]
        mpn=identidade.get('mpn');ean=identidade.get('gtin')
        if not mpn and not ean:faltantes.append('identificador_fabricante_ou_gtin')
        conflitos=[]
        if mpn is not None and (not isinstance(mpn,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9./_-]{2,99}',mpn) or codigo_interno(mpn)):
            conflitos.append('mpn_invalido')
        if ean is not None and gtin(ean) is None:conflitos.append('gtin_invalido')
        for campo in ('mpn','gtin'):
            if identidade.get(campo) and campo not in fontes:faltantes.append('fonte:'+campo)
        for campo,valor in spec.items():
            if valor is not None and campo not in fontes:faltantes.append('fonte:'+campo)
        dados={k:v for k,v in identidade.items() if k in ('fabricante','modelo')};dados.update(spec)
        produto=ProdutoNormalizado(loja='fonte_tecnica',id_externo=documento['id_externo'],categoria=documento['categoria'],
            titulo=' '.join(str(identidade.get(c) or '') for c in ('fabricante','modelo')),marca=identidade.get('fabricante'),
            modelo=identidade.get('modelo'),especificacoes=spec,identificadores={k:identidade[k] for k in ('mpn','gtin') if identidade.get(k)},
            ativo=True,categoria_confirmada=True,contexto={'finalidade':'ficha_tecnica'})
        v=ValidarFichaTecnicaService().executar(documento['categoria'],dados,produto,identidade,fontes=fontes,finalidade='catalogo')
        faltantes+=v['campos_pendentes'];conflitos+=v['conflitos']
        return dict(pronto=v['pronto'] and not faltantes and not conflitos,dados=dados,produto=produto,
            campos_pendentes=sorted(set(faltantes)),conflitos=sorted(set(conflitos)))

    @staticmethod
    def conflitos_locais(peca, especificacoes):
        conflitos=[]
        for campo,valor in especificacoes.items():
            atual=getattr(peca,campo)
            if atual is None or atual=='':continue
            chave='formato_ram' if peca.__tablename__=='memoria_ram' and campo=='formato' else campo
            if converter(chave,atual)!=converter(chave,valor):conflitos.append('campo_local_divergente:'+campo)
        return conflitos

    def processar(self, documento, *, simular=True, responsavel='importador', assinatura_esperada=None):
        documento=self.normalizar(documento)
        with self.repositorio.transacao(simular=simular):
            if assinatura_esperada is not None:
                from models import FichaTecnicaCatalogo
                atual=FichaTecnicaCatalogo.buscar_origem(documento['provedor'],documento['id_externo'],bloquear=True)
                if atual is None or atual.assinatura_documento!=assinatura_esperada or atual.estado=='rejeitada':
                    raise ValueError('Ficha mudou durante a revisão; releia antes de aprovar')
            ficha,recepcao=self.repositorio.receber(documento)
            if recepcao=='rejeitada':return dict(acao='rejeitada',**ficha.resumo())
            modelos={m.__tablename__:m for m in MODELOS_PECAS};modelo=modelos[ficha.categoria]
            if recepcao=='igual' and ficha.estado=='importada':
                p=modelo.buscar_por_id(ficha.peca_id)
                if p and ficha.diagnostico.get('assinatura_tecnica')==assinatura_tecnica(p):
                    return dict(acao='inalterada',**ficha.resumo())
                ficha.transicionar('em_revisao',motivo='A peça mudou desde a importação',responsavel=responsavel)
                ficha.diagnostico={'conflitos':['peca_modificada']}
                return dict(acao='revisao',**ficha.resumo())
            avaliacao=self.avaliar(documento)
            ficha.campos_pendentes=avaliacao['campos_pendentes'];ficha.diagnostico={'conflitos':avaliacao['conflitos']}
            if not avaliacao['pronto']:
                estado='em_revisao' if avaliacao['conflitos'] else 'pendente_dados'
                ficha.transicionar(estado,motivo='Ficha incompleta ou conflitante',responsavel=responsavel)
                return dict(acao='revisao',**ficha.resumo())
            from services.catalogo_service.indice_candidatos_service import IndiceCandidatosService
            indice=IndiceCandidatosService.carregar(modelo)
            pool,identidades=indice.pecas,indice.identidades
            decisao=indice.avaliar(avaliacao['produto'])
            identidade=documento['identidade'];mpn=identidade.get('mpn');ean=identidade.get('gtin')
            existentes=[p for p in pool if (mpn and codigo(identidades.get(p.id,{}).get('mpn') or p.part_number or '')==codigo(mpn))
                or (ean and identidades.get(p.id,{}).get('gtin')==ean)]
            alvo=next((p for p in pool if f'{p.__tablename__}:{p.id}'==decisao.get('peca')),None)
            motivo=None
            if decisao['classificacao']=='ambigua':motivo='Candidatos ambíguos'
            elif existentes and (len(existentes)>1 or alvo not in existentes):motivo='Identificador existente com dados conflitantes; não duplicar'
            elif ficha.peca_id and (not alvo or alvo.id!=ficha.peca_id):motivo='Origem já vinculada a outra identidade; não substituir a peça'
            elif alvo and not alvo.publicavel:motivo='Peça local aguarda revisão; não liberar automaticamente'
            elif alvo:
                antes=assinatura_tecnica(alvo);db.session.refresh(alvo,with_for_update=True)
                if antes!=assinatura_tecnica(alvo):motivo='Peça mudou durante a validação'
                elif self.conflitos_locais(alvo,documento['especificacoes']):motivo='Especificações conhecidas divergem da fonte'
            if motivo:
                ficha.transicionar('em_revisao',motivo=motivo,responsavel=responsavel)
                ficha.diagnostico={'motivo':motivo,'associacao':{k:v for k,v in decisao.items() if k!='candidatos'}}
                return dict(acao='revisao',**ficha.resumo())
            ficha.transicionar('validada',motivo='Identidade e especificações confirmadas',responsavel=responsavel)
            nova=alvo is None
            if nova:
                alvo=self.repositorio.criar_peca(modelo,avaliacao['dados'],identidade,documento['fontes'],ficha)
            else:
                for campo,valor in documento['especificacoes'].items():
                    if getattr(alvo,campo) is None or getattr(alvo,campo)=='':setattr(alvo,campo,valor)
                db.session.flush();db.session.refresh(alvo)
                if alvo.ficha_montagem_validada is not None:alvo.ficha_montagem_validada=not pendencias_para_montagem(alvo)
                self.repositorio.registrar_fontes(alvo,documento['fontes'],identidade,ficha)
            ficha.peca_id=alvo.id
            ficha.diagnostico={'assinatura_tecnica':assinatura_tecnica(alvo),'pendencias_montagem':pendencias_para_montagem(alvo)}
            ficha.transicionar('importada',motivo='Componente cadastrado' if nova else 'Origem associada à peça existente',responsavel=responsavel)
            db.session.flush()
            return dict(acao='proposta' if simular else 'criada' if nova else 'associada',nova_peca=nova,
                situacao_catalogo=alvo.situacao_catalogo(),**ficha.resumo())
