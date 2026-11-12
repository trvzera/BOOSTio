from types import SimpleNamespace
from models.modelos_pecas import MODELOS_PECAS
from .associacao_inteligente_service import AssociacaoInteligenteService


class ValidarFichaTecnicaService:
    def executar(self,categoria,dados,produto,identidade=None,fontes=None,*,finalidade="comercial"):
        classe=next((m for m in MODELOS_PECAS if m.__tablename__==categoria),None)
        if classe is None:raise ValueError('Categoria inválida')
        ignorados={'id','criado_em','atualizado_em','status_validacao'}
        obrigatorios={c.name for c in classe.__table__.columns if not c.nullable and c.name not in ignorados}
        from utils.campos_tecnicos import CAMPOS_TECNICOS_OBRIGATORIOS
        obrigatorios.update(CAMPOS_TECNICOS_OBRIGATORIOS.get(categoria, ()))
        if finalidade not in ('comercial','catalogo'):raise ValueError('Finalidade inválida')
        if finalidade=='comercial':
            obrigatorios|={'preco','esgotado','consumo_energia'}
            if categoria=='processador':obrigatorios|={'videointegrado','cooler'}
        ausentes=sorted(k for k in obrigatorios if dados.get(k) is None)
        conflitos=[]
        if fontes is not None:
            from urllib.parse import urlsplit
            for campo in obrigatorios-set(ausentes):
                fonte=fontes.get(campo,{})
                url=urlsplit(fonte.get('url','')) if isinstance(fonte,dict) else urlsplit('')
                if url.scheme!='https' or not url.hostname or url.username or url.password:
                    ausentes.append('fonte:'+campo)
        from decimal import Decimal,InvalidOperation
        from sqlalchemy import Integer,Numeric,Float,Boolean,String
        protegidos={'id','criado_em','atualizado_em','status_validacao','validado_em','validacao_motivo','part_number','kabum_external','ficha_montagem_validada','fontes_especificacoes'}
        for campo,valor in dados.items():
            if campo in protegidos or campo.startswith('benchmark_'):
                conflitos.append('campo_protegido:'+campo)
                continue
            if campo in classe.CAMPOS_DA_OFERTA:
                if campo=='preco' and valor is not None and (type(valor) is bool or not isinstance(valor,(int,float,Decimal)) or not 0<valor<10**12):
                    conflitos.append('numero_invalido:'+campo)
                continue
            if campo not in classe.__table__.columns:raise ValueError('Campo técnico desconhecido: '+campo)
            tipo=classe.__table__.columns[campo].type
            if isinstance(tipo,Boolean) and valor is not None and type(valor) is not bool:
                conflitos.append('booleano_invalido:'+campo)
            elif isinstance(tipo,(Integer,Numeric,Float)) and valor is not None:
                try:
                    n=Decimal(str(valor))
                    if type(valor) is bool or not n.is_finite() or n<0 or (campo in {'preco','capacidade_gb','memoria_gb','nucleo','thread','clockbase','clockmax','frequencia_mhz','quantidade_pentes','potencia_w','dpi_max'} and n==0) or (isinstance(tipo,Integer) and n!=int(n)):
                        conflitos.append('numero_invalido:'+campo)
                except (InvalidOperation,ValueError,OverflowError):conflitos.append('numero_invalido:'+campo)
            if isinstance(tipo,String) and valor is not None and not isinstance(valor,str):conflitos.append('texto_invalido:'+campo)
            tam=getattr(tipo,'length',None)
            if isinstance(valor,str) and (not valor.strip() or (tam and len(valor)>tam)):conflitos.append('valor_invalido:'+campo)
        proxy=SimpleNamespace(__tablename__=categoria,id=0,part_number=(identidade or {}).get('mpn'),
            **{'fabricante':dados.get('fabricante',''),'modelo':dados.get('modelo',''),**dados})
        comparacao=AssociacaoInteligenteService().avaliar(proxy,produto,identidade=identidade)
        conflitos+=comparacao['conflitos']
        return dict(pronto=not ausentes and not conflitos and comparacao['percentual']>80,
                    campos_pendentes=ausentes,conflitos=sorted(set(conflitos)),comparacao=comparacao)
