import hashlib
import json
import re
import unicodedata


def normalizar_identidade(valor):
    # Conservador: não apaga hífens, números, capacidades ou sufixos de modelos.
    valor = unicodedata.normalize('NFKC', str(valor or '')).casefold()
    return re.sub(r'\s+', ' ', valor.replace('®', '').replace('™', '')).strip()


def assinatura_peca(peca):
    return assinatura_campos(peca.__tablename__, peca.id, peca.fabricante, peca.modelo, peca.part_number)


def assinatura_campos(tabela, identificador, fabricante, modelo, part_number):
    campos = [tabela, identificador, fabricante, modelo, part_number]
    return hashlib.sha256(json.dumps(campos, ensure_ascii=False).encode()).hexdigest()


def assinatura_catalogo(produto):
    dados = {k: produto.get(k) for k in ('id', 'name', 'domain_id', 'attributes')}
    return hashlib.sha256(json.dumps(dados, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def assinatura_documento(dados):
    return hashlib.sha256(json.dumps(dados, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
