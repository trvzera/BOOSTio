import re
from difflib import SequenceMatcher
from itertools import permutations
from functools import lru_cache
from .normalizar_produto import nome


def marca(valor):
    s=nome(valor);return {'wd':'western digital', 'logitech g':'logitech', 'kingston fury':'kingston'}.get(s,s)


def cpu(texto):
    s=nome(texto)
    encontrados=re.findall(r'\b(ryzen\s*[3579]|(?:core\s*)?i[3579]|core\s*ultra\s*[3579])\s*-?\s*(pro\s*)?(\d{3,5}[a-z0-9]*)\b',s)
    if len(encontrados)!=1:return None
    familia,pro,modelo=(re.sub(r'\s+','',v) for v in encontrados[0])
    if re.fullmatch(r'corei[3579]',familia):familia=familia[4:]
    return familia,pro,modelo


@lru_cache(maxsize=8192)
def chave(valor,categoria,fabricante):
    s=nome(valor)
    for m in {nome(fabricante),marca(fabricante)}:
        if m:s=re.sub(r'(?<!\w)'+re.escape(m)+r'(?!\w)',' ',s)
    prefixos={'memoria_ram':r'\b(memoria|memory|ram|modulo|kit|de)\b',
      'placa_mae':r'\b(placa\s*mae|motherboard)\b','placa_video':r'\b(placa\s*de\s*video|placa\s*grafica)\b',
      'ssd':r'\b(disco|solido|solida|ssd|interno|interna|de)\b','hd':r'\b(disco|rigido|hd|hdd|interno|interno|de)\b',
      'fonte':r'\b(fonte|de|alimentacao|power supply)\b','mouse':r'\b(mouse)\b'}
    s=re.sub(r'\b(series|serie)\b',' ',s)
    if categoria in prefixos:s=re.sub(prefixos[categoria],' ',s)
    if categoria in ('memoria_ram','ssd','hd','placa_video'):
        s=re.sub(r'\b\d+\s*[x×]\s*\d+\s*gb\b',' ',s)
        s=re.sub(r'\b\d+(?:[.,]\d+)?\s*(?:gb|tb|mhz)\b',' ',s)
    if categoria=='memoria_ram':s=re.sub(r'\bddr\s*[345]\b|\bcl\s*\d+\b|\b(?:so[ -]?)?dimm\b|\bdesktop\b|\bnotebook\b',' ',s)
    if categoria=='placa_video':
        s=re.sub(r'\bgddr\s*[567]x?\b',' ',s)
        s=re.sub(r'\b(?:nvidia|amd|intel|geforce|radeon)\b',' ',s)
    if categoria=='fonte':s=re.sub(r'\b\d+\s*w\b',' ',s)
    return ''.join(re.findall(r'[a-z0-9]+|[+/]',s))


@lru_cache(maxsize=8192)
def chaves_remotas(categoria,fabricante,titulo,modelo,alternativos):
    valores={modelo,*alternativos};base=sorted(v for v in valores if v)[:10]
    valores.update(' '.join(v) for v in permutations(base,2));valores.add(titulo)
    return tuple(sorted({chave(v,categoria,fabricante) for v in valores if v}))


@lru_cache(maxsize=8192)
def similaridade_chaves(local,chaves):
    return max((SequenceMatcher(None,local,v).ratio() for v in chaves if local),default=0)


class CompararNomesService:
    def executar(self,peca,produto):
        categoria=peca.__tablename__;local=chave(peca.modelo,categoria,peca.fabricante)
        chaves=chaves_remotas(categoria,peca.fabricante,produto.titulo,produto.modelo or '',tuple(produto.modelos_alternativos))
        exato=bool(local and local in chaves)
        if categoria=='processador':
            lc=cpu(peca.modelo);rc=cpu(produto.titulo)
            exato=exato or bool(lc and lc==rc)
        if categoria=='placa_video':
            # Chip e VRAM não distinguem edições comerciais da mesma montadora.
            generico=re.fullmatch(r'(?:(?:geforce|radeon|nvidia|amd))*?(?:rtx|gtx|rx|arc)[a-z]?\d{3,4}(?:ti|super|xt|xtx)*',local)
            if generico:exato=False
        similaridade=similaridade_chaves(local,chaves)
        titulo_chave=chave(produto.titulo,categoria,peca.fabricante)
        titulo_exato=bool(local and local==titulo_chave) or bool(categoria=='processador' and cpu(peca.modelo) and cpu(peca.modelo)==cpu(produto.titulo))
        titulo_sim=similaridade_chaves(local,(titulo_chave,))
        return dict(exato=exato,pontos=35 if exato else round(35*min(similaridade,.7),2),
                    titulo=15 if titulo_exato else round(15*min(titulo_sim,.7),2),
                    chave_local=local,similaridade_revisao=round(similaridade,4))
