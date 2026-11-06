import json
import math
import re
from pathlib import Path
from services.peca_service.modelos_pecas import MODELOS_PECAS


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

