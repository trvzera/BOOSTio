import hashlib
import json
import re
import unicodedata


def normalizar_identidade(valor):
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


def assinatura_tecnica(peca):
    ignorados = {'preco','esgotado','preco_atualizado_em','criado_em','atualizado_em','fontes_especificacoes'}
    return assinatura_documento({c.name:getattr(peca,c.name) for c in peca.__table__.columns if c.name not in ignorados})
